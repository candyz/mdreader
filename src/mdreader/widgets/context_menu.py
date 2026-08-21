"""Right-click context menu modal screen for mdreader."""
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import OptionList
from textual.binding import Binding


class ContextMenuModal(ModalScreen[str | None]):
    """Floating context menu on mouse right-click."""

    DEFAULT_CSS = """
    ContextMenuModal {
        background: transparent;
        align: left top;
    }
    #context-menu-list {
        width: 32;
        height: auto;
        border: heavy $accent;
        background: $panel;
        padding: 0;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_menu", "Cancel", show=False),
        Binding("q", "dismiss_menu", "Cancel", show=False),
    ]

    def __init__(self, x: int, y: int, has_selection: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.menu_x = max(0, x)
        self.menu_y = max(0, y)
        self.has_selection = has_selection

    def compose(self) -> ComposeResult:
        if self.has_selection:
            options = [
                "📋 Copy (複製選取文字)",
                "🔍 Search (搜尋此文字)",
                "❌ Cancel (取消)",
            ]
        else:
            options = [
                "📄 Select All (全選文字)",
                "🔍 Search (開啟搜尋)",
                "❌ Cancel (取消)",
            ]
        yield OptionList(*options, id="context-menu-list")

    def on_mount(self) -> None:
        menu = self.query_one("#context-menu-list", OptionList)
        screen_w = self.app.size.width
        screen_h = self.app.size.height
        
        # Keep context menu within viewport bounds
        menu_w = 32
        menu_h = 6
        target_x = min(self.menu_x, max(0, screen_w - menu_w - 2))
        target_y = min(self.menu_y, max(0, screen_h - menu_h - 2))
        menu.styles.offset = (target_x, target_y)
        menu.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        selected = str(event.option.prompt)
        self.dismiss(selected)

    def action_dismiss_menu(self) -> None:
        self.dismiss(None)

    def on_mouse_down(self, event) -> None:
        """Clicking outside the menu closes it."""
        menu = self.query_one("#context-menu-list", OptionList)
        if not menu.region.contains(event.screen_x, event.screen_y):
            self.dismiss(None)
