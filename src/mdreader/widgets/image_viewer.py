"""High-performance terminal TrueColor image viewer widget using Pillow and ANSI half-blocks."""
from __future__ import annotations
import os
import sys
import subprocess
from pathlib import Path
from typing import Sequence
from textual.scroll_view import ScrollView
from textual.geometry import Size
from textual.strip import Strip
from textual.binding import Binding
from rich.segment import Segment
from rich.style import Style
from rich.color import Color
from PIL import Image

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".ico",
    ".tiff",
    ".tif",
}


def is_image_file(filepath_or_name: Path | str | None) -> bool:
    """Check if the given path or filename has a supported image extension."""
    if not filepath_or_name:
        return False
    path = Path(filepath_or_name)
    return path.suffix.lower() in IMAGE_EXTENSIONS


def format_file_size(size_bytes: int) -> str:
    """Format byte size into human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


class ImageViewerWidget(ScrollView):
    """Integrated TrueColor Half-block image viewer widget for terminal displays."""

    DEFAULT_CSS = """
    ImageViewerWidget {
        width: 100%;
        height: 100%;
        background: $surface;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("plus", "zoom_in", "Zoom In (+)", show=False),
        Binding("equals", "zoom_in", "Zoom In (=)", show=False),
        Binding("minus", "zoom_out", "Zoom Out (-)", show=False),
        Binding("zero", "reset_zoom", "Reset Zoom (0)", show=False),
        Binding("v", "open_external", "Open with default app (v)", show=False),
        Binding("f4", "open_external", "Open with default app (F4)", show=False),
        Binding("enter", "open_external", "Open with default app", show=False),
    ]

    def __init__(
        self,
        filepath: Path | str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.filepath = Path(filepath)
        self.zoom: float = 1.0
        self._strips: list[Strip] = []
        self._img_orig_size: tuple[int, int] = (0, 0)
        self._img_format: str = ""
        self._img_mode: str = ""
        self._last_render_width: int = 0
        self._load_and_render()

    def _load_and_render(self, target_width: int | None = None) -> None:
        """Load image file and generate TrueColor half-block terminal strips."""
        if not self.filepath.exists() or not self.filepath.is_file():
            self._render_error(f"File not found: {self.filepath}")
            return

        try:
            with Image.open(self.filepath) as raw_img:
                self._img_orig_size = raw_img.size
                self._img_format = raw_img.format or self.filepath.suffix.lstrip(".").upper()
                self._img_mode = raw_img.mode

                # Composite RGBA or paletted images with transparency onto neutral dark background
                if raw_img.mode in ("RGBA", "LA") or (raw_img.mode == "P" and "transparency" in raw_img.info):
                    bg = Image.new("RGBA", raw_img.size, (20, 24, 30, 255))
                    img = Image.alpha_composite(bg, raw_img.convert("RGBA")).convert("RGB")
                else:
                    img = raw_img.convert("RGB")

                orig_w, orig_h = self._img_orig_size
                if orig_w <= 0 or orig_h <= 0:
                    self._render_error("Invalid image dimensions (0x0)")
                    return

                # Calculate render width based on viewport and zoom
                available_w = target_width or (self.size.width if self.size.width > 10 else 80)
                # Cap base width to available width with zoom multiplier
                base_w = max(20, min(orig_w, available_w - 4))
                render_w = max(10, int(base_w * self.zoom))
                
                # Each terminal character cell is roughly 1:2 aspect ratio (width : height)
                # So 1 row of characters = 2 rows of pixels (upper half block and lower half block)
                render_h_pixels = max(2, int(orig_h * (render_w / orig_w) * 0.5) * 2)

                resized = img.resize((render_w, render_h_pixels), Image.Resampling.BILINEAR)

                strips: list[Strip] = []
                file_size_str = format_file_size(self.filepath.stat().st_size)
                zoom_pct = int(self.zoom * 100)

                # 1. Header Information Banner
                banner_text = f"🖼️  {self.filepath.name} │ {orig_w}x{orig_h} px │ {self._img_format} ({self._img_mode}) │ {file_size_str} │ Zoom: {zoom_pct}%"
                strips.append(Strip([Segment(banner_text, Style(color="bright_cyan", bold=True))]))
                strips.append(Strip([Segment("─" * min(len(banner_text) + 2, 120), Style(color="bright_black"))]))
                strips.append(Strip.blank(1))

                # 2. Image TrueColor Half-Block Pixel Matrix
                for y in range(0, render_h_pixels, 2):
                    segments: list[Segment] = []
                    # Left padding for centering if table/image is smaller than viewport
                    left_pad = max(0, (available_w - render_w) // 2) if self.zoom <= 1.0 else 0
                    if left_pad > 0:
                        segments.append(Segment(" " * left_pad))

                    for x in range(render_w):
                        p1 = resized.getpixel((x, y))
                        p2 = resized.getpixel((x, y + 1)) if y + 1 < render_h_pixels else (0, 0, 0)
                        c1 = Color.from_rgb(p1[0], p1[1], p1[2])
                        c2 = Color.from_rgb(p2[0], p2[1], p2[2])
                        # Upper half block: Foreground = top pixel, Background = bottom pixel
                        segments.append(Segment("▀", Style.from_color(color=c1, bgcolor=c2)))
                    
                    strips.append(Strip(segments))

                # 3. Footer Instruction Bar
                strips.append(Strip.blank(1))
                hints = "[v/Enter]: Open with System Viewer  │  [+/-/0]: Zoom In/Out/Reset  │  [↑↓←→ / jkdf]: Pan Image"
                strips.append(Strip([Segment(hints, Style(color="bright_black", italic=True))]))

                self._strips = strips
                max_w = max((s.cell_length for s in strips), default=render_w)
                self.virtual_size = Size(max_w + 2, len(strips) + 1)
                self._last_render_width = available_w
                self.refresh()

        except Exception as e:
            self._render_error(f"Failed to decode image '{self.filepath.name}': {e}")

    def _render_error(self, err_msg: str) -> None:
        """Render a clean error fallback screen."""
        strips = [
            Strip([Segment("⚠️ Image Preview Error", Style(color="red", bold=True))]),
            Strip([Segment("─" * 40, Style(color="bright_black"))]),
            Strip([Segment(err_msg, Style(color="yellow"))]),
            Strip.blank(1),
            Strip([Segment("Press [v] or [Enter] to try opening with system viewer.", Style(color="cyan"))]),
        ]
        self._strips = strips
        self.virtual_size = Size(80, len(strips))
        self.refresh()

    def on_resize(self, event) -> None:
        """Dynamically re-fit image when terminal window is resized (only when at standard 1.0 zoom)."""
        if self.zoom == 1.0 and abs(event.size.width - self._last_render_width) > 3:
            self._load_and_render(target_width=event.size.width)

    def render_line(self, y: int) -> Strip:
        """Render visible viewport line with virtual scrolling support."""
        scroll_x, scroll_y = self.scroll_offset
        line_idx = y + scroll_y
        if 0 <= line_idx < len(self._strips):
            strip = self._strips[line_idx]
            return strip.crop(scroll_x, scroll_x + self.size.width)
        return Strip.blank(self.size.width)

    def update_content(self, filepath: Path | str) -> None:
        """Update and reload image from a new filepath."""
        self.filepath = Path(filepath)
        self.zoom = 1.0
        self._load_and_render()

    def action_zoom_in(self) -> None:
        """Zoom in image preview (+20%)."""
        if self.zoom < 4.0:
            self.zoom = round(self.zoom + 0.2, 1)
            self._load_and_render()

    def action_zoom_out(self) -> None:
        """Zoom out image preview (-20%)."""
        if self.zoom > 0.3:
            self.zoom = round(self.zoom - 0.2, 1)
            self._load_and_render()

    def action_reset_zoom(self) -> None:
        """Reset zoom to standard 100%."""
        self.zoom = 1.0
        self._load_and_render()

    def action_open_external(self) -> None:
        """Open the image with the operating system default image viewer."""
        if not self.filepath.exists():
            return
        target = str(self.filepath.resolve())
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", target])
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", target])
            elif sys.platform == "win32":
                os.startfile(target)
        except Exception:
            pass

    # Duck-typing methods for compatibility with MDReaderApp actions
    def get_headings(self) -> list:
        return []

    def scroll_to_heading_id(self, target_id: str) -> None:
        pass

    def search_text(self, query: str) -> list:
        return []

    def set_soft_wrap(self, wrap: bool) -> None:
        pass

    def toggle_line_numbers(self) -> None:
        pass
