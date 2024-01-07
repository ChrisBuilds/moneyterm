from textual import log, on, events
from textual.message import Message
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    TabbedContent,
    Placeholder,
    TabPane,
    Static,
    Button,
    ListItem,
    ListView,
    Label,
    Select,
    Rule,
    OptionList,
    Input,
    Markdown,
)
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.utils.financedb import FinanceDB
from pathlib import Path
import json


class QuickCategoryScreen(ModalScreen):
    """Screen for selecting a category from a list of all categories in the ledger. Categories are filtered by the input field.

    Args:
        Screen (textual.screen.Screen): Screen class
    """

    CSS_PATH = "../tcss/quickcategoryscreen.tcss"

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            ledger (Ledger): Ledger object
        """
        super().__init__()
        self.ledger = ledger
        self.categories: list[str] = []
        self.transaction = transaction
        self.vertical_scroll = VerticalScroll()
        self.vertical_scroll.can_focus = False
        self.vertical_scroll.border_title = "Quick Category"

    def compose(self) -> ComposeResult:
        self.category_list: OptionList = OptionList(id="category_list")
        with self.vertical_scroll:
            yield Input(placeholder="Search Categories", id="category_search_input")
            yield Rule()
            yield Label("Available Categories")
            yield self.category_list

    def on_mount(self) -> None:
        try:
            with open(Path("moneyterm/data/labels.json"), "r") as f:
                self.categories.extend(sorted(json.load(f)["Categories"], key=str.lower))
        except FileNotFoundError:
            pass
        if not self.categories:
            self.category_list.add_options(["No categories found."])
            self.category_list.disabled = True
        else:
            self.category_list.add_options(self.categories)
        self.query_one("#category_search_input").focus()

    def on_key(self, key: events.Key) -> None:
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.category_list.action_select()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.category_list.clear_options()
        self.category_list.add_options(
            [category for category in self.categories if event.value.lower() in category.lower()]
        )
        self.category_list.action_first()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Dismiss the screen and return the selected category via the callback.

        Args:
            event (OptionList.OptionSelected): Event containing the selected category.
        """
        self.dismiss(event.option.prompt)
