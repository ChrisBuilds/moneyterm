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


class QuickLabelScreen(ModalScreen):
    """Screen for selecting a label from a list of all labels in the ledger. Labels are filtered by the input field.

    Args:
        Screen (textual.screen.Screen): Screen class
    """

    CSS_PATH = "../tcss/quicklabelscreen.tcss"

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            ledger (Ledger): Ledger object
        """
        super().__init__()
        self.ledger = ledger
        self.labels: list[str] = []
        self.label_types_map: dict[str, str] = {}
        self.transaction = transaction
        self.vertical_scroll = VerticalScroll()
        self.vertical_scroll.can_focus = False
        self.vertical_scroll.border_title = "Quick Label"

    def compose(self) -> ComposeResult:
        self.label_list: OptionList = OptionList(id="label_list")
        with self.vertical_scroll:
            yield Input(placeholder="Search Labels", id="labels_search_input")
            yield Rule()
            yield Label("Available Labels", id="available_labels_label")
            yield self.label_list

    def on_mount(self) -> None:
        try:
            with open(Path("moneyterm/data/labels.json"), "r") as f:
                labels = json.load(f)
                for label_type in ("Bills", "Expenses", "Incomes"):
                    for label in labels[label_type]:
                        self.label_types_map[label] = label_type
                self.labels.extend(labels["Bills"])
                self.labels.extend(labels["Expenses"])
                self.labels.extend(labels["Incomes"])
                self.labels.sort(key=lambda x: x.lower())

        except FileNotFoundError:
            pass
        if not self.labels:
            self.label_list.add_options(["No labels found."])
            self.label_list.disabled = True
        else:
            self.label_list.add_options(self.labels)
        self.query_one("#labels_search_input").focus()

    def on_key(self, key: events.Key) -> None:
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.label_list.action_select()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.label_list.clear_options()
        self.label_list.add_options([label for label in self.labels if event.value.lower() in label.lower()])
        self.label_list.action_first()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Dismiss the screen and return the selected label via the callback.

        Args:
            event (OptionList.OptionSelected): Event containing the selected label.
        """
        selected_label = str(event.option.prompt)
        selected_label_type = self.label_types_map[selected_label]
        self.dismiss((selected_label, selected_label_type))
