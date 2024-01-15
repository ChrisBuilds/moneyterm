from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Label,
    Rule,
    OptionList,
    Input,
)
from textual.containers import VerticalScroll
from moneyterm.utils.ledger import Ledger, Transaction
from pathlib import Path
import json


class QuickLabelScreen(ModalScreen):
    """Screen for selecting a label from a list of all labels in the ledger. Labels are filtered by the input field.

    Args:
        Screen (textual.screen.Screen): Screen class

    Attributes:
        CSS_PATH (str): The path to the CSS file for styling the screen.
        ledger (Ledger): The Ledger object.
        labels (list[str]): The list of all labels in the ledger.
        label_types_map (dict[str, str]): A mapping of labels to their corresponding types.
        transaction (Transaction): The Transaction object.
        vertical_scroll (VerticalScroll): The vertical scroll widget for the screen.
        label_list (OptionList): The option list widget for displaying the available labels.
    """

    CSS_PATH = "../tcss/quicklabelscreen.tcss"

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            ledger (Ledger): Ledger object
            transaction (Transaction): Transaction object
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
        """Compose the screen layout.

        Yields:
            Composeable: The composeable elements of the screen.
        """
        self.label_list: OptionList = OptionList(id="label_list")
        with self.vertical_scroll:
            yield Input(placeholder="Search Labels", id="labels_search_input")
            yield Rule()
            yield Label("Available Labels", id="available_labels_label")
            yield self.label_list

    def on_mount(self) -> None:
        """Event handler called when the screen is mounted."""
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
        """Event handler called when a key is pressed.

        Args:
            key (events.Key): The key event.
        """
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.label_list.action_select()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Event handler called when the input field value is changed.

        Args:
            event (Input.Changed): The input changed event.
        """
        self.label_list.clear_options()
        self.label_list.add_options([label for label in self.labels if event.value.lower() in label.lower()])
        self.label_list.action_first()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Event handler called when an option is selected from the option list.

        Args:
            event (OptionList.OptionSelected): The option selected event.
        """
        selected_label = str(event.option.prompt)
        selected_label_type = self.label_types_map[selected_label]
        self.dismiss((selected_label, selected_label_type))
