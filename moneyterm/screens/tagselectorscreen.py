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
from textual.containers import Vertical, Horizontal, VerticalScroll
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.utils.financedb import FinanceDB
from pathlib import Path


class TagSelectorScreen(Screen):
    """Screen for selecting a tag from a list of all tags in the ledger. Tags are filtered by the input field.

    Args:
        Screen (textual.screen.Screen): Screen class
    """

    def __init__(self, ledger: Ledger) -> None:
        """Initialize the screen.

        Args:
            ledger (Ledger): Ledger object
        """
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        self.tag_list: OptionList = OptionList(id="tag_list")

        with Vertical():
            yield Input(placeholder="Search Tags")
            yield Label("Select Tag")
            yield self.tag_list

    def on_mount(self) -> None:
        self.all_tags = self.ledger.get_all_tags()
        self.tag_list.add_options(self.all_tags)

    def on_key(self, key: events.Key) -> None:
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.tag_list.action_select()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.tag_list.clear_options()
        self.tag_list.add_options([tag for tag in self.all_tags if event.value.lower() in tag.lower()])
        self.tag_list.action_first()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Dismiss the screen and return the selected tag via the callback.

        Args:
            event (OptionList.OptionSelected): Event containing the selected tag.
        """
        self.dismiss(event.option.prompt)
