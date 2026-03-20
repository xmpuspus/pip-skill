"""Interactive TUI builder for pip-skill using Textual."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Markdown,
    OptionList,
    Static,
)
from textual.widgets.option_list import Option

from pip_skill.introspect import CallableInfo, PackageInfo
from pip_skill.utils import normalize_skill_name


@dataclass
class FunctionRow:
    """A scored function with selection state."""

    callable_info: CallableInfo
    score: int
    selected: bool = False
    module: str = ""

    def __post_init__(self):
        self.module = self.callable_info.module


# ---------------------------------------------------------------------------
# Module filter modal
# ---------------------------------------------------------------------------


class ModuleFilterScreen(ModalScreen[str | None]):
    """Modal screen for filtering functions by module."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close"),
    ]

    CSS = """
    ModuleFilterScreen {
        align: center middle;
    }
    #module-filter-container {
        width: 60;
        max-height: 24;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    #module-filter-container Static {
        width: 100%;
        content-align: center middle;
        margin-bottom: 1;
    }
    #module-list {
        height: 1fr;
    }
    """

    def __init__(self, modules: list[str]) -> None:
        super().__init__()
        self.modules = sorted(modules)

    def compose(self) -> ComposeResult:
        with Vertical(id="module-filter-container"):
            yield Static("Filter by Module")
            yield OptionList(
                Option("(all modules)", id="__all__"),
                *[Option(m, id=m) for m in self.modules],
                id="module-list",
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        value = None if event.option.id == "__all__" else str(event.option.id)
        self.dismiss(value)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Main TUI app
# ---------------------------------------------------------------------------

SORT_MODES = ["score", "name", "module"]

EMPTY_PREVIEW = """\
# SKILL.md Preview

Select functions from the left panel to see a live preview here.

**Keybindings:**
- `Space` — toggle function selection
- `/` — search functions
- `s` — cycle sort mode
- `f` — filter by module
- `Enter` — generate skill files
- `q` — quit
"""


class PipSkillBuilder(App[int]):
    """Interactive TUI for building pip-skill plugins."""

    CSS = """
    #main-container {
        height: 1fr;
    }
    #left-pane {
        width: 1fr;
        min-width: 40;
    }
    #right-pane {
        width: 1fr;
        min-width: 40;
        border-left: tall $accent;
    }
    #function-table {
        height: 1fr;
    }
    #search-input {
        dock: bottom;
        display: none;
    }
    #preview {
        height: 1fr;
        padding: 0 1;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit_app", "Quit", priority=True),
        Binding("space", "toggle_row", "Toggle", show=False),
        Binding("slash", "search", "Search"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("f", "filter_module", "Filter"),
        Binding("a", "select_all", "All"),
        Binding("n", "select_none", "None"),
        Binding("enter", "generate", "Generate"),
    ]

    def __init__(
        self,
        package_name: str,
        output_dir: Path | None = None,
        max_tools: int = 20,
        mcp: bool = False,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.package_name = package_name
        self.output_dir = output_dir
        self.max_tools = max_tools
        self.mcp = mcp
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

        self.rows: list[FunctionRow] = []
        self.package_info: PackageInfo | None = None
        self.sort_mode = "score"
        self.module_filter: str | None = None
        self.search_query = ""
        self._generated = False

    # -- Layout ---------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield DataTable(id="function-table", cursor_type="row")
                yield Input(
                    placeholder="Type to filter, Escape to close",
                    id="search-input",
                )
            with Vertical(id="right-pane"):
                yield Markdown(EMPTY_PREVIEW, id="preview")
        yield Static("Loading...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#function-table", DataTable)
        table.add_columns(" ", "Score", "Function", "Module")
        table.loading = True
        self.title = f"pip-skill build {self.package_name}"
        self._load_package()

    # -- Async loading --------------------------------------------------------

    @work(thread=True)
    def _load_package(self) -> None:
        from pip_skill.introspect import introspect_package
        from pip_skill.selector import select_functions

        try:
            info = introspect_package(self.package_name)
        except ValueError as e:
            self.call_from_thread(self.notify, f"Error: {e}", severity="error")
            self.call_from_thread(self._set_exit_code, 1)
            return

        selected = select_functions(
            info,
            max_tools=999,
            threshold=0,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
        )

        rows = []
        for i, (fn, score) in enumerate(selected):
            pre_selected = i < self.max_tools and score >= 20
            rows.append(
                FunctionRow(
                    callable_info=fn,
                    score=score,
                    selected=pre_selected,
                )
            )

        self.call_from_thread(self._populate, info, rows)

    def _set_exit_code(self, code: int) -> None:
        self.exit(code)

    def _populate(self, info: PackageInfo, rows: list[FunctionRow]) -> None:
        self.package_info = info
        self.rows = rows
        self._refresh_table()
        table = self.query_one("#function-table", DataTable)
        table.loading = False
        self._update_status()
        self._update_preview()

    # -- Table management -----------------------------------------------------

    def _visible_rows(self) -> list[FunctionRow]:
        """Return rows matching current filter and search."""
        result = self.rows
        if self.module_filter:
            result = [r for r in result if r.module == self.module_filter]
        if self.search_query:
            q = self.search_query.lower()
            result = [
                r
                for r in result
                if q in r.callable_info.name.lower() or q in r.callable_info.qualname.lower()
            ]
        if self.sort_mode == "score":
            result.sort(key=lambda r: (-r.score, r.callable_info.name))
        elif self.sort_mode == "name":
            result.sort(key=lambda r: r.callable_info.name.lower())
        elif self.sort_mode == "module":
            result.sort(key=lambda r: (r.module, -r.score))
        return result

    def _refresh_table(self) -> None:
        table = self.query_one("#function-table", DataTable)
        table.clear()
        for row in self._visible_rows():
            check = "[x]" if row.selected else "[ ]"
            table.add_row(
                check,
                str(row.score),
                row.callable_info.qualname,
                row.module,
                key=row.callable_info.qualname,
            )

    def _update_status(self) -> None:
        if not self.package_info:
            return
        selected_count = sum(1 for r in self.rows if r.selected)
        total = len(self.rows)
        tier_labels = {1: "T1", 2: "T2", 3: "T3"}
        tier = tier_labels.get(self.package_info.tier, "?")

        parts = [
            f"{self.package_info.name} v{self.package_info.version}",
            f"[{tier}]",
            f"{selected_count}/{total} selected",
            f"sort:{self.sort_mode}",
        ]
        if self.module_filter:
            parts.append(f"filter:{self.module_filter}")
        if self.search_query:
            parts.append(f"search:{self.search_query}")

        status = self.query_one("#status-bar", Static)
        status.update("  |  ".join(parts))

    # -- Preview --------------------------------------------------------------

    def _update_preview(self) -> None:
        if not self.package_info:
            return
        selected_fns = [r.callable_info for r in self.rows if r.selected]
        if not selected_fns:
            preview = self.query_one("#preview", Markdown)
            preview.update(EMPTY_PREVIEW)
            return

        from pip_skill.generator import render_skill_md_string
        from pip_skill.schema import build_tool_schemas

        schemas = build_tool_schemas(selected_fns)
        content = render_skill_md_string(
            self.package_info,
            schemas,
            {"mcp": self.mcp},
        )
        preview = self.query_one("#preview", Markdown)
        preview.update(content)

    # -- Actions --------------------------------------------------------------

    def action_toggle_row(self) -> None:
        table = self.query_one("#function-table", DataTable)
        if table.row_count == 0:
            return
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        qualname = str(row_key.value)
        for row in self.rows:
            if row.callable_info.qualname == qualname:
                row.selected = not row.selected
                break
        self._refresh_table()
        self._update_status()
        self._update_preview()

    def action_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        if search_input.display:
            search_input.display = False
            self.search_query = ""
            self._refresh_table()
            self._update_status()
        else:
            search_input.display = True
            search_input.value = self.search_query
            search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-input":
            self.search_query = event.value
            self._refresh_table()
            self._update_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            event.input.display = False
            self.query_one("#function-table", DataTable).focus()

    def on_key(self, event) -> None:
        if event.key == "escape":
            search_input = self.query_one("#search-input", Input)
            if search_input.display:
                search_input.display = False
                self.search_query = ""
                self._refresh_table()
                self._update_status()
                self.query_one("#function-table", DataTable).focus()
                event.prevent_default()

    def action_cycle_sort(self) -> None:
        idx = SORT_MODES.index(self.sort_mode)
        self.sort_mode = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        self._refresh_table()
        self._update_status()
        self.notify(f"Sort: {self.sort_mode}")

    def action_filter_module(self) -> None:
        modules = sorted({r.module for r in self.rows})
        self.push_screen(ModuleFilterScreen(modules), self._on_module_filter)

    def _on_module_filter(self, module: str | None) -> None:
        self.module_filter = module
        self._refresh_table()
        self._update_status()
        if module:
            self.notify(f"Filtered: {module}")
        else:
            self.notify("Filter cleared")

    def action_select_all(self) -> None:
        for row in self._visible_rows():
            row.selected = True
        self._refresh_table()
        self._update_status()
        self._update_preview()
        self.notify("Selected all visible")

    def action_select_none(self) -> None:
        for row in self._visible_rows():
            row.selected = False
        self._refresh_table()
        self._update_status()
        self._update_preview()
        self.notify("Deselected all visible")

    def action_generate(self) -> None:
        if not self.package_info:
            return
        selected_fns = [r.callable_info for r in self.rows if r.selected]
        if not selected_fns:
            self.notify("No functions selected", severity="warning")
            return
        self._do_generate(selected_fns)

    @work(thread=True)
    def _do_generate(self, selected_fns: list[CallableInfo]) -> None:
        from pip_skill.generator import render_templates
        from pip_skill.schema import build_tool_schemas

        schemas = build_tool_schemas(selected_fns)
        skill_name = normalize_skill_name(self.package_info.name)
        output_dir = self.output_dir or Path(skill_name)

        options = {"mcp": self.mcp}
        written = render_templates(self.package_info, schemas, options, output_dir)

        self.call_from_thread(
            self.notify,
            f"Generated {len(written)} files in {output_dir}/",
            severity="information",
        )
        self.call_from_thread(self._mark_generated, output_dir, len(written))

    def _mark_generated(self, output_dir: Path, count: int) -> None:
        self._generated = True
        self._update_status()

    def action_quit_app(self) -> None:
        self.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_tui(args) -> int:
    """Launch the TUI builder from CLI args."""
    app = PipSkillBuilder(
        package_name=args.package,
        output_dir=getattr(args, "output", None),
        max_tools=getattr(args, "max_tools", 20),
        mcp=getattr(args, "mcp", False),
        include_patterns=getattr(args, "include", None),
        exclude_patterns=getattr(args, "exclude", None),
    )
    result = app.run()
    return result if isinstance(result, int) else 0
