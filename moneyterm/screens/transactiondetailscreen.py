from textual import log, on, events
from textual.message import Message
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widget import Widget
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
    Button,
)
from textual.containers import Vertical, Horizontal, VerticalScroll
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.utils.financedb import FinanceDB
from moneyterm.screens.quickcategoryscreen import QuickLabelScreen
from pathlib import Path


class ManualLabelButtons(Widget):
    """Widget for displaying the manual labels of a transaction."""

    def __init__(self, tx: Transaction) -> None:
        """Initialize the widget.

        Args:
            tx (Transaction): Transaction object
        """

        super().__init__()
        self.manual_labels = tx.manual_labels.bills + tx.manual_labels.categories + tx.manual_labels.incomes
        self.id = "manual_label_buttons"

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        for label in self.manual_labels:
            button = Button(f"{label}", id=f"manual_label_button_{label}", name=label)
            button.can_focus = False
            yield button


class TransactionDetailScreen(ModalScreen):
    """Screen for displaying the details of a transaction."""

    CSS_PATH = "../tcss/transactiondetailscreen.tcss"

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            transaction (str): Transaction ID
        """
        super().__init__()
        self.ledger = ledger
        self.transaction = transaction
        self.label_removed = False
        self.id = "transaction_detail_screen"
        self.vertical = Vertical()
        self.markdown = f"""**Transaction ID** : {self.transaction.txid}
        
**Date** : {self.transaction.date}

**Memo** : {self.transaction.memo}

**Payee** : {self.transaction.payee}

**Transaction Alias** : {self.transaction.alias}

**Type** : {self.transaction.tx_type}

**Amount** : {self.transaction.amount}

**Account Number** : {self.transaction.account.number}

**Account Institution** : {self.transaction.account.institution}

**Account Alias** : {self.transaction.account.alias}

**Bills Auto-Labels** : {','.join(self.transaction.auto_labels.bills)}

**Categories Auto-Labels** : {','.join(self.transaction.auto_labels.categories)}

**Incomes Auto-Labels** : {','.join(self.transaction.auto_labels.incomes)}
"""
        self.markdown_widget = Markdown(self.markdown, id="transaction_detail_markdown")
        self.markdown_widget.styles.width = max(len(line) for line in self.markdown.splitlines())
        self.vertical.border_title = "Transaction Details"

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        with self.vertical:
            yield self.markdown_widget
            yield Label("Manual Labels (click to remove)")
            yield ManualLabelButtons(self.transaction)

    def on_key(self, key: events.Key) -> None:
        """Handle keypress events."""
        close_screen_keys = ("escape", "q", "i")
        if key.key in close_screen_keys:
            self.dismiss(self.label_removed)

    def on_button_pressed(self, pressed: Button.Pressed) -> None:
        """Remove the manual label corresponding to the pressed button."""
        label_to_remove = pressed.button.name
        if label_to_remove:
            self.ledger.remove_label_from_tx(self.transaction.account.number, self.transaction.txid, label_to_remove)
            self.label_removed = True
        pressed.button.remove()
        self.ledger.save_ledger_pkl()
