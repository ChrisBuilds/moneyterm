from textual import log, on, events
from textual.events import Mount
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
from textual.validation import Function
from rich.text import Text
from rich.table import Table
from rich import box

from textual.widget import Widget
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.utils.financedb import FinanceDB
from moneyterm.screens.confirmscreen import ConfirmScreen
from pathlib import Path
from decimal import Decimal
import json


class LabelValue(Widget):
    """Widget for displaying a label and value input widget."""

    def __init__(self, label: str, value: str) -> None:
        super().__init__()
        self.label = label
        self.value = value
        self.id = f"label_value_{label}"
        self.input = Input(
            value=self.value,
            placeholder="0.00",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_decimal,
                    "Amount must be number/decimal. Ex: 3, 3.01",
                )
            ],
            valid_empty=True,
            id=f"{self.label}_input",
        )

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self.label)
            yield self.input

    def validate_amount_is_decimal(self, amount: str) -> bool:
        try:
            Decimal(amount)
            return True
        except:
            return False


class TransactionSplitScreen(ModalScreen):
    """Screen for splitting transaction value across multiple labels.

    Args:
        Screen (textual.screen.Screen): Screen class
    """

    CSS_PATH = "../tcss/transactionsplitscreen.tcss"

    BINDINGS = [
        ("escape", "close_screen", "Close Screen"),
    ]

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            ledger (Ledger): Ledger object
        """
        super().__init__()
        self.ledger = ledger
        self.label_types_map: dict[str, str] = {}
        self.transaction = transaction
        self.vertical_scroll = VerticalScroll()
        self.vertical_scroll.border_title = "Split Transaction"
        self.breakdown_static = Static(id="table")
        self.remaining_amount = Decimal(abs(self.transaction.amount))

    def compose(self) -> ComposeResult:
        with self.vertical_scroll:
            yield self.breakdown_static
            yield Rule()
            for label in (
                self.transaction.auto_labels.bills
                + self.transaction.auto_labels.categories
                + self.transaction.auto_labels.incomes
                + self.transaction.manual_labels.bills
                + self.transaction.manual_labels.categories
                + self.transaction.manual_labels.incomes
            ):
                yield LabelValue(label, "")
            yield Rule()
            yield Button("Save and Close", id="save_button")

    def on_mount(self) -> None:
        self.breakdown_static.update(self.update_breakdown())
        if self.transaction.splits:
            for label_value_widget in self.query("LabelValue").results(LabelValue):
                label = label_value_widget.label
                if label in self.transaction.splits:
                    label_value_widget.input.value = str(self.transaction.splits[label])

    def get_value(self, label_value: LabelValue, label: str, input_changed_event: Input.Changed | None = None):
        if input_changed_event and input_changed_event.control.id == f"{label}_input":
            return abs(Decimal(input_changed_event.value)) if input_changed_event.value else Decimal(0)
        elif label_value.input.value:
            return abs(Decimal(label_value.input.value))
        else:
            return Decimal(0)

    def update_breakdown(self, input_changed_event: Input.Changed | None = None) -> Table:
        apportioned_amounts = []
        breakdown_table = Table(show_header=False, box=box.SIMPLE)
        breakdown_table.add_row("Transaction Total", f"${abs(self.transaction.amount)}")
        for label_value_widget in self.query("LabelValue").results(LabelValue):
            label = label_value_widget.label
            value = self.get_value(label_value_widget, label, input_changed_event)
            breakdown_table.add_row(label, f"${value:.2f}")
            apportioned_amounts.append(value)
        if apportioned_amounts:
            self.remaining_amount = Decimal(abs(self.transaction.amount)) - Decimal(sum(apportioned_amounts))
            remaining_amount_text = Text(f"${self.remaining_amount:.2f}")
            if self.remaining_amount < 0:
                remaining_amount_text.stylize("bold red")
            breakdown_table.add_section()
            breakdown_table.add_row("Remaining", remaining_amount_text)
        self.query_one("#save_button").disabled = self.remaining_amount < 0
        return breakdown_table

    @on(Input.Changed)
    def on_input_changed_update_breakdown(self, event: Input.Changed) -> None:
        if event.validation_result and event.validation_result.is_valid or not event.validation_result:
            self.breakdown_static.update(self.update_breakdown(event))

    @on(Button.Pressed, "#save_button")
    def on_save_button_button_press(self, event: events.Event) -> None:
        if self.remaining_amount > 0:
            message = f"Are you sure you want to save with ${self.remaining_amount:.2f} remaining? Remaining amount will not be tracked under any label."
            self.app.push_screen(ConfirmScreen(message), self.save_transaction_splits)
        else:
            self.save_transaction_splits(True)

    def save_transaction_splits(self, confirm: bool) -> None:
        if not confirm:
            return
        for label_value_widget in self.query("LabelValue").results(LabelValue):
            label = label_value_widget.label
            value = self.get_value(label_value_widget, label)
            self.ledger.split_transaction(self.transaction.account.number, self.transaction.txid, label, value)
        self.ledger.save_ledger_pkl()
        self.notify("Transaction splits saved.", timeout=3)
        self.dismiss(True)

    def action_close_screen(self) -> None:
        self.dismiss(False)
