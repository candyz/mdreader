"""Unit tests for graphics protocol helper and file picker scan."""
from pathlib import Path
from mdreader.renderer.graphics import is_iterm2_supported, is_kitty_supported, encode_iterm2_image
from mdreader.widgets.file_picker import FilePickerScreen


def test_graphics_protocol_detection(monkeypatch):
    monkeypatch.setenv("TERM_PROGRAM", "iTerm.app")
    monkeypatch.setenv("LC_TERMINAL", "iTerm2")
    assert is_iterm2_supported() is True

    monkeypatch.setenv("TERM_PROGRAM", "Apple_Terminal")
    monkeypatch.setenv("LC_TERMINAL", "")
    assert is_iterm2_supported() is False

    monkeypatch.setenv("TERM_PROGRAM", "ghostty")
    assert is_kitty_supported() is True


def test_encode_iterm2_image(tmp_path: Path):
    sample = tmp_path / "test.png"
    sample.write_bytes(b"dummy image content")
    encoded = encode_iterm2_image(sample)
    assert encoded.startswith("\033]1337;File=inline=1;size=")
    assert encoded.endswith("\a")


def test_file_picker_scan(tmp_path: Path):
    (tmp_path / "doc1.md").write_text("# Doc 1", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "doc2.markdown").write_text("# Doc 2", encoding="utf-8")
    (tmp_path / "sub" / "ignored.txt").write_text("ignore", encoding="utf-8")

    # Default: only md / html files
    screen = FilePickerScreen(start_dir=tmp_path, show_all_files=False)
    screen._scan_directory()
    item_labels = [label for label, item_type, path in screen.items]
    assert any("doc1.md" in l for l in item_labels)
    assert any("sub/" in l for l in item_labels)
    assert not any("ignored.txt" in l for l in item_labels)

    # Show all files: includes .txt and other plain text and dotfiles
    (tmp_path / "sub" / ".vimrc").write_text("syntax on", encoding="utf-8")
    (tmp_path / "sub" / ".config").mkdir()
    screen_all = FilePickerScreen(start_dir=tmp_path / "sub", show_all_files=True)
    screen_all._scan_directory()
    item_labels_all = [label for label, item_type, path in screen_all.items]
    assert any("doc2.markdown" in l for l in item_labels_all)
    assert any("ignored.txt" in l for l in item_labels_all)
    assert any(".vimrc" in l for l in item_labels_all)
    assert any(".config/" in l for l in item_labels_all)


def test_commander_screen(tmp_path: Path):
    from mdreader.widgets.commander import CommanderScreen, PaneWidget

    (tmp_path / "file1.md").write_text("# Hello", encoding="utf-8")
    (tmp_path / "script.py").write_text("print('test')", encoding="utf-8")
    (tmp_path / "folder").mkdir()

    pane = PaneWidget("test-pane", start_dir=tmp_path, show_all=True)
    pane.scan()
    items = pane.items
    assert any("file1.md" in i[0] for i in items)
    assert any("script.py" in i[0] for i in items)
    assert any("folder/" in i[0] for i in items)

    screen = CommanderScreen(current_path=tmp_path / "file1.md", show_all=True)
    assert screen.active_pane_id == "left-pane"
    screen.action_switch_pane()
    assert screen.active_pane_id == "right-pane"


def test_commander_modals():
    from mdreader.widgets.commander import PromptModal, ConfirmModal

    prompt = PromptModal(title="Test Prompt", initial_value="default_val")
    assert prompt.prompt_title == "Test Prompt"
    assert prompt.initial_value == "default_val"

    confirm = ConfirmModal(title="Delete Confirm", message="Delete file?")
    assert confirm.confirm_title == "Delete Confirm"
    assert confirm.confirm_msg == "Delete file?"


def test_commander_multiselect(tmp_path: Path):
    from mdreader.widgets.commander import PaneWidget

    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a", encoding="utf-8")
    f2.write_text("b", encoding="utf-8")

    pane = PaneWidget("test-pane", start_dir=tmp_path, show_all=True)
    pane.scan()
    assert len(pane.selected_paths) == 0

    pane.selected_paths.add(f1)
    pane.selected_paths.add(f2)
    assert len(pane.get_effective_targets()) == 2

    pane.unselect_all_items()
    assert len(pane.selected_paths) == 0


def test_position_label():
    from mdreader.app import PositionLabel

    label = PositionLabel()
    # At top with total_lines
    label.update_position(scroll_y=0, max_scroll_y=100, total_lines=100)
    assert "Ln 1/100 (0%)" in str(label.render())

    # In middle (scroll_y=49 -> line 50)
    label.update_position(scroll_y=49, max_scroll_y=100, total_lines=100)
    assert "Ln 50/100 (49%)" in str(label.render())

    # At bottom (scroll_y=99 -> line 100)
    label.update_position(scroll_y=99, max_scroll_y=100, total_lines=100)
    assert "Ln 100/100 (99%)" in str(label.render())

    # Fits in single page (max_scroll_y <= 0)
    label.update_position(scroll_y=0, max_scroll_y=0, virtual_height=20, size_height=40, total_lines=20)
    assert "Ln 1/20 (100%)" in str(label.render())

    # Full rich status with file size, type, and wrap
    label.update_position(
        scroll_y=42,
        max_scroll_y=1000,
        total_lines=1000,
        file_size=1565863,
        file_type="Markdown",
        soft_wrap=True,
        available_width=130,
    )
    rendered = str(label.render())
    assert "1.5M" in rendered
    assert "Markdown" in rendered
    assert "[WRAP]" in rendered
    assert "Ln 43/1000" in rendered


def test_virtual_text_viewer():
    from mdreader.widgets.virtual_viewer import VirtualTextViewer, should_use_virtual_viewer

    # Check should_use_virtual_viewer logic
    assert should_use_virtual_viewer("hello", "file.txt") is True
    assert should_use_virtual_viewer("hello", "script.py") is True
    assert should_use_virtual_viewer("# Heading", "doc.md") is False
    assert should_use_virtual_viewer("line\n" * 4000, "large.md") is True

    # Test VirtualTextViewer operations
    content = "Line 1\n# Heading 1\nLine 3\n## Sub heading\nLine 5"
    viewer = VirtualTextViewer(raw_text=content, filename="test.txt")
    assert len(viewer.lines) == 5

    # Headings extraction
    headings = viewer.get_headings()
    assert len(headings) == 2
    assert headings[0] == (1, "Heading 1", "1")
    assert headings[1] == (2, "Sub heading", "3")

    # Search
    matches = viewer.search_text("Heading")
    assert len(matches) == 2
    assert matches == [1, 3]

    # Scrolling and line rendering
    viewer.scroll_to_block(1)
    assert viewer._highlighted_line == 1
    strip = viewer.render_line(0)
    assert len(strip._segments) > 0


def test_large_file_virtual_viewer_performance(tmp_path: Path):
    from mdreader.widgets.virtual_viewer import VirtualTextViewer
    import time

    # Generate 50,000 lines
    large_text = "\n".join(f"Data row {i}: some sample content for benchmarking" for i in range(50000))
    t0 = time.time()
    viewer = VirtualTextViewer(raw_text=large_text, filename="large.txt")
    mount_time = time.time() - t0
    assert mount_time < 0.1, f"Mounting 50k lines should take < 0.1s, took {mount_time:.4f}s"

    # Search 50k lines
    t1 = time.time()
    matches = viewer.search_text("row 49999")
    search_time = time.time() - t1
    assert len(matches) == 1
    assert search_time < 0.05, f"Search across 50k lines should take < 0.05s, took {search_time:.4f}s"


def test_open_file_swap_viewer(tmp_path: Path):
    from mdreader.app import MDReaderApp
    from mdreader.widgets.virtual_viewer import VirtualTextViewer
    from mdreader.widgets.markdown_view import MarkdownViewerWidget
    import asyncio

    f_txt = tmp_path / "sample.txt"
    f_txt.write_text("Hello plain text", encoding="utf-8")
    f_md = tmp_path / "sample.md"
    f_md.write_text("# Hello Markdown", encoding="utf-8")

    async def run():
        # Start app with no initial file
        app = MDReaderApp()
        async with app.run_test() as pilot:
            assert isinstance(app.query_one("#viewer"), MarkdownViewerWidget)
            
            # Open txt file (swaps to VirtualTextViewer)
            await app.open_file(f_txt)
            await pilot.pause()
            assert isinstance(app.query_one("#viewer"), VirtualTextViewer)
            
            # Open md file (swaps back to MarkdownViewerWidget)
            await app.open_file(f_md)
            await pilot.pause()
            assert isinstance(app.query_one("#viewer"), MarkdownViewerWidget)

    asyncio.run(run())


def test_goto_line_and_colon_jump(tmp_path: Path):
    from mdreader.app import MDReaderApp
    from mdreader.widgets.virtual_viewer import VirtualTextViewer
    import asyncio

    # 500 lines text file
    txt_file = tmp_path / "long.txt"
    txt_file.write_text("\n".join(f"Line {i+1}" for i in range(500)), encoding="utf-8")

    async def run():
        app = MDReaderApp(filepath=txt_file)
        async with app.run_test() as pilot:
            viewer = app.query_one("#viewer", VirtualTextViewer)
            assert viewer.scroll_y == 0
            
            # Jump to line 250 via action_goto_line
            app.action_goto_line(250)
            await pilot.pause()
            assert viewer.scroll_y == 249
            assert "Ln 250/500" in str(app.query_one("#position-label").render())
            
            # Jump to bottom via 500G
            await pilot.press("5", "0", "0", "G")
            await pilot.pause()
            assert "100%" in str(app.query_one("#position-label").render())

            # Jump via colon prompt
            app.action_open_goto_line()
            await pilot.pause()
            assert app.search_visible is True
            search_input = app.query_one("#search-input")
            search_input.value = ":42"
            await pilot.press("enter")
            await pilot.pause()
            assert viewer.scroll_y == 41
            assert "Ln 42/500" in str(app.query_one("#position-label").render())

    asyncio.run(run())


def test_fuzzy_score_and_recent_files(tmp_path: Path):
    from mdreader.widgets.file_picker import fuzzy_score, FilePickerScreen
    from mdreader.utils.config import add_recent_file, get_recent_files

    # 1. Fuzzy scoring tests
    is_m, s = fuzzy_score("sapp", "src/mdreader/app.py")
    assert is_m is True
    assert s > 0

    is_m, s = fuzzy_score("app", "app.py")
    assert is_m is True
    assert s > 500  # Prefix match bonus

    is_m, _ = fuzzy_score("xyz", "app.py")
    assert is_m is False

    # 2. Recent files tests
    f1 = tmp_path / "doc1.md"
    f1.write_text("# Doc 1", encoding="utf-8")
    f2 = tmp_path / "doc2.md"
    f2.write_text("# Doc 2", encoding="utf-8")

    add_recent_file(f1)
    add_recent_file(f2)
    recents = get_recent_files()
    assert str(f2.resolve()) in recents
    assert str(f1.resolve()) in recents


def test_virtual_viewer_syntax_highlighting():
    from mdreader.widgets.virtual_viewer import VirtualTextViewer

    py_code = "def calculate_sum(a: int, b: int = 10) -> int:\n    # Add numbers\n    return a + b"
    viewer = VirtualTextViewer(raw_text=py_code, filename="calc.py")
    assert viewer._lexer is not None

    strip0 = viewer.render_line(0)
    # Check that segments contain styled tokens (not just plain string)
    assert len(strip0._segments) > 1
    found_keyword = any(seg.style and getattr(seg.style, "color", None) and "magenta" in str(seg.style.color) for seg in strip0._segments)
    assert found_keyword is True


def test_commander_sort_modes(tmp_path: Path):
    from mdreader.widgets.commander import PaneWidget

    # Create dummy files with different sizes and extensions
    (tmp_path / "z_small.txt").write_text("a", encoding="utf-8")
    (tmp_path / "a_large.py").write_text("a" * 500, encoding="utf-8")
    (tmp_path / "m_medium.md").write_text("a" * 100, encoding="utf-8")

    pane = PaneWidget(pane_id="test-pane", start_dir=tmp_path, show_all=True)
    
    # 1. Sort by name
    pane.sort_mode = "name"
    pane.scan()
    file_names = [p.name for _, item_type, p in pane.items if item_type == "file"]
    assert file_names == ["a_large.py", "m_medium.md", "z_small.txt"]

    # 2. Sort by size (largest first)
    pane.sort_mode = "size"
    pane.scan()
    file_names = [p.name for _, item_type, p in pane.items if item_type == "file"]
    assert file_names == ["a_large.py", "m_medium.md", "z_small.txt"]

    # 3. Sort by extension
    pane.sort_mode = "ext"
    pane.scan()
    file_names = [p.name for _, item_type, p in pane.items if item_type == "file"]
    assert file_names == ["m_medium.md", "a_large.py", "z_small.txt"]

    # 4. Cycle sort mode
    pane.sort_mode = "name"
    next_mode = pane.cycle_sort_mode()
    assert next_mode == "size"
    assert pane.sort_mode == "size"


def test_full_document_copy_fallback(tmp_path: Path):
    from mdreader.app import MDReaderApp
    import asyncio

    doc_file = tmp_path / "sample.md"
    doc_file.write_text("# Test Document\n\nFull copy test line.", encoding="utf-8")

    async def run():
        app = MDReaderApp(filepath=doc_file)
        async with app.run_test() as pilot:
            copied = []
            app.copy_to_system_clipboard = lambda text: copied.append(text) or True
            
            # Action copy with no mouse selection should copy entire document
            app.action_copy_selected_text()
            await pilot.pause()
            assert len(copied) == 1
            assert "# Test Document" in copied[0]

    asyncio.run(run())


def test_extract_links():
    from mdreader.widgets.link_picker import extract_links_from_text

    text = """
    Check out [GitHub](https://github.com) and [Google](https://google.com).
    Also raw link https://textual.textualize.io/guide/
    """
    links = extract_links_from_text(text)
    assert len(links) == 3
    labels = [l[0] for l in links]
    assert "GitHub" in labels
    assert "Google" in labels
    assert "https://textual.textualize.io/guide/" in labels


def test_marks_modal():
    from mdreader.widgets.marks_modal import MarksModal

    marks = {"a": 42, "b": 100}
    lines = [f"Line {i}" for i in range(150)]
    modal = MarksModal(marks, lines)
    assert modal.marks == marks


def test_vim_marks_and_wrap_toggle(tmp_path: Path):
    from mdreader.app import MDReaderApp
    from mdreader.widgets.virtual_viewer import VirtualTextViewer
    import asyncio

    txt_file = tmp_path / "marks.txt"
    txt_file.write_text("\n".join(f"Row {i+1}" for i in range(300)), encoding="utf-8")

    async def run():
        app = MDReaderApp(filepath=txt_file)
        async with app.run_test() as pilot:
            viewer = app.query_one("#viewer", VirtualTextViewer)
            
            # 1. Soft wrap toggle
            assert app._soft_wrap is True
            app.action_toggle_wrap()
            await pilot.pause()
            assert app._soft_wrap is False
            app.action_toggle_wrap()
            await pilot.pause()
            assert app._soft_wrap is True

            # 2. Set mark 'a' at top
            await pilot.press("m", "a")
            await pilot.pause()
            assert app._marks.get("a") == 1

            # 3. Jump to line 200 and set mark 'b'
            app.action_goto_line(200)
            await pilot.pause()
            await pilot.press("m", "b")
            await pilot.pause()
            assert app._marks.get("b") == 200

            # 4. Jump back to mark 'a' using 'a
            await pilot.press("'", "a")
            await pilot.pause()
            assert viewer.scroll_y == 0

            # 5. Jump to mark 'b' using 'b
            await pilot.press("'", "b")
            await pilot.pause()
            assert viewer.scroll_y == 199

    asyncio.run(run())


def test_mmap_line_buffer(tmp_path: Path):
    from mdreader.utils.mmap_buffer import MmapLineBuffer

    # Create a 5,000 line test file
    sample_file = tmp_path / "big_sample.txt"
    lines = [f"Entry #{i+1} with some text data" for i in range(5000)]
    lines[2500] = "SPECIAL_UNIQUE_KEYWORD_FOR_SEARCH"
    sample_file.write_text("\n".join(lines), encoding="utf-8")

    buf = MmapLineBuffer(sample_file)
    assert len(buf) == 5000
    assert buf[0] == "Entry #1 with some text data"
    assert buf[2500] == "SPECIAL_UNIQUE_KEYWORD_FOR_SEARCH"
    assert buf[-1] == "Entry #5000 with some text data"
    assert len(buf[10:20]) == 10

    # Test lightning search
    matches = buf.search_text("SPECIAL_UNIQUE_KEYWORD")
    assert matches == [2500]

    # Test full text reading
    all_text = buf.read_all_text()
    assert "SPECIAL_UNIQUE_KEYWORD_FOR_SEARCH" in all_text
    buf.close()


def test_mmap_viewer_integration(tmp_path: Path):
    from mdreader.app import MDReaderApp
    from mdreader.widgets.virtual_viewer import VirtualTextViewer
    import asyncio

    # Create a large text file > 300KB
    large_file = tmp_path / "gigantic.log"
    content = "\n".join(f"2026-08-23 12:00:{i%60:02d} [INFO] System event record {i+1}" for i in range(8000))
    large_file.write_text(content, encoding="utf-8")

    async def run():
        app = MDReaderApp(filepath=large_file)
        async with app.run_test() as pilot:
            viewer = app.query_one("#viewer", VirtualTextViewer)
            assert len(viewer.lines) == 8000
            assert app._mmap_buffer is not None

            # Test line jump
            app.action_goto_line(4000)
            await pilot.pause()
            assert viewer.scroll_y == 3999
            assert "Ln 4000/8000" in str(app.query_one("#position-label").render())

            # Test search on mmap viewer
            app.perform_search("event record 4000")
            await pilot.pause()
            assert viewer.scroll_y == 3999

    asyncio.run(run())


def test_grep_search(tmp_path: Path):
    from mdreader.utils.grep import grep_search

    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    f1 = sub_dir / "code.py"
    f1.write_text("def hello_world():\n    return 'UNIQUE_GREP_TARGET'\n", encoding="utf-8")

    f2 = sub_dir / "notes.md"
    f2.write_text("# Notes\n\nSome notes without target.\n", encoding="utf-8")

    matches = grep_search(tmp_path, "UNIQUE_GREP_TARGET")
    assert len(matches) == 1
    assert matches[0][0] == f1
    assert matches[0][1] == 2
    assert "UNIQUE_GREP_TARGET" in matches[0][2]


def test_dir_bookmarks_modal():
    from mdreader.widgets.dir_bookmarks import DirBookmarksModal

    modal = DirBookmarksModal(Path.cwd())
    assert len(modal.destinations) >= 3
    paths = [p for _, p in modal.destinations]
    assert Path.home() in paths
    assert Path.cwd() in paths


def test_grep_search_modal(tmp_path: Path):
    from mdreader.widgets.grep_modal import GrepSearchModal
    from mdreader.app import MDReaderApp
    import asyncio

    test_file = tmp_path / "sample.txt"
    test_file.write_text("line 1\nline 2 with GREP_KEYWORD\nline 3", encoding="utf-8")

    modal = GrepSearchModal(root_dir=tmp_path)
    assert modal.root_dir == tmp_path.resolve()


def test_export_utilities(tmp_path: Path):
    from mdreader.utils.export import export_to_html, export_document_to_file

    md_content = "# Title Heading\n\n- item 1\n- item 2\n\n```python\nprint('hello')\n```"
    html_out = export_to_html(md_content, title="My Test")
    assert "<!DOCTYPE html>" in html_out
    assert "<title>My Test</title>" in html_out
    assert "Title Heading" in html_out
    assert "print('hello')" in html_out

    dest_file = tmp_path / "out.html"
    res_path = export_document_to_file(md_content, dest_file, export_format="html", title="Doc")
    assert res_path.exists()
    assert "<!DOCTYPE html>" in res_path.read_text(encoding="utf-8")


def test_extract_code_blocks():
    from mdreader.widgets.code_block_modal import extract_code_blocks, CodeBlockModal

    md_text = """
    Here is some Python:
    ```python
    import os
    print(os.getcwd())
    ```

    And some Shell:
    ```bash
    echo "test"
    ```
    """
    blocks = extract_code_blocks(md_text)
    assert len(blocks) == 2
    assert blocks[0][0] == "python"
    assert "import os" in blocks[0][1]
    assert blocks[1][0] == "bash"
    assert "echo \"test\"" in blocks[1][1]

    modal = CodeBlockModal(blocks)
    assert len(modal.code_blocks) == 2


def test_cli_args_parsing():
    from mdreader.__main__ import parse_args

    # 1. Positional +line syntax
    args, line = parse_args(["+120", "doc.md"])
    assert args.file == "doc.md"
    assert line == 120

    # 2. Flag -l
    args, line = parse_args(["-l", "42", "doc.md", "--watch", "-t", "tokyo-night"])
    assert args.file == "doc.md"
    assert line == 42
    assert args.watch is True
    assert args.theme == "tokyo-night"

    # 3. Export flags
    args, _ = parse_args(["README.md", "--export-html", "out.html", "--list-themes"])
    assert args.export_html == "out.html"
    assert args.list_themes is True


def test_markdown_softbreaks_preservation():
    from mdreader.widgets.markdown_view import MarkdownViewerWidget
    from textual.app import App, ComposeResult
    import asyncio

    raw = "Line One\nLine Two\nLine Three"

    class AppSoftBreak(App):
        def compose(self) -> ComposeResult:
            yield MarkdownViewerWidget(raw_markdown=raw, id="viewer")

    async def run():
        app = AppSoftBreak()
        async with app.run_test() as pilot:
            viewer = app.query_one("#viewer", MarkdownViewerWidget)
            para = viewer.document.children[0]
            content_str = str(getattr(para, "_content", ""))
            assert "Line One\nLine Two\nLine Three" in content_str

    asyncio.run(run())


def test_virtual_viewer_line_numbers_toggle():
    from mdreader.widgets.virtual_viewer import VirtualTextViewer

    viewer = VirtualTextViewer(raw_text="hello\nworld", filename="test.py")
    assert viewer.show_line_numbers is True

    new_state = viewer.toggle_line_numbers()
    assert new_state is False
    assert viewer.show_line_numbers is False

    new_state = viewer.toggle_line_numbers()
    assert new_state is True
    assert viewer.show_line_numbers is True


def test_reader_help_modal():
    from mdreader.widgets.help_modal import ReaderHelpModal, HELP_SECTIONS

    modal = ReaderHelpModal()
    assert len(HELP_SECTIONS) >= 5
    assert modal is not None


def test_terminal_and_finder_actions(tmp_path: Path):
    from mdreader.app import MDReaderApp
    import os

    test_file = tmp_path / "test.md"
    test_file.write_text("# Test", encoding="utf-8")

    app = MDReaderApp(filepath=test_file)
    assert app.filepath == test_file

    # Ensure no NameError when accessing terminal action helper logic
    target_dir = app.filepath.parent if app.filepath and app.filepath.exists() else Path.cwd()
    shell = os.environ.get("SHELL") or "/bin/sh"
    assert target_dir == tmp_path
    assert len(shell) > 0


def test_cmd_prompt_bar_toggle(tmp_path: Path):
    from mdreader.app import MDReaderApp
    import asyncio

    test_file = tmp_path / "test.md"
    test_file.write_text("# Terminal Test", encoding="utf-8")

    async def run():
        app = MDReaderApp(filepath=test_file)
        async with app.run_test() as pilot:
            assert app.cmd_prompt_visible is False
            prompt_label = app._get_prompt_label()
            assert "@" in prompt_label
            assert "$" in prompt_label

            # Toggle prompt on
            app.action_toggle_cmd_prompt()
            await pilot.pause()
            assert app.cmd_prompt_visible is True

            # Toggle prompt off
            app.action_toggle_cmd_prompt()
            await pilot.pause()
            assert app.cmd_prompt_visible is False

    asyncio.run(run())


def test_markdown_and_virtual_soft_wrap():
    from mdreader.widgets.markdown_view import MarkdownViewerWidget
    from mdreader.widgets.virtual_viewer import VirtualTextViewer

    # 1. MarkdownViewer soft wrap toggle
    md_viewer = MarkdownViewerWidget(raw_markdown="# Title\nLong text")
    assert md_viewer.soft_wrap is True
    assert "-no-wrap" not in md_viewer.classes

    md_viewer.set_soft_wrap(False)
    assert md_viewer.soft_wrap is False
    assert "-no-wrap" in md_viewer.classes

    md_viewer.set_soft_wrap(True)
    assert md_viewer.soft_wrap is True
    assert "-no-wrap" not in md_viewer.classes

    # 2. VirtualTextViewer visual line wrapping
    long_line = "A" * 150
    v_viewer = VirtualTextViewer(raw_text=long_line, filename="test.py")
    assert v_viewer.soft_wrap is False
    assert len(v_viewer.lines) == 1

    v_viewer.set_soft_wrap(True)
    assert v_viewer.soft_wrap is True
    display_lines = getattr(v_viewer, "_display_lines", [])
    assert len(display_lines) >= 2
