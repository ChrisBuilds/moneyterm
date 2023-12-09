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
from moneyterm.screens.tagselectorscreen import TagSelectorScreen
from pathlib import Path


class TransactionDetailScreen(ModalScreen):
    """Screen for displaying the details of a transaction."""

    def __init__(self, transaction: Transaction) -> None:
        """Initialize the screen.

        Args:
            transaction (str): Transaction ID
        """
        super().__init__()
        self.transaction = transaction
        self.id = "transaction_detail_screen"
        self.markdown = f"""**Transaction ID** : {self.transaction.txid}
        
**Date** : {self.transaction.date}

**Memo** : {self.transaction.memo}

**Payee** : {self.transaction.payee}

**Type** : {self.transaction.tx_type}

**Amount** : {self.transaction.amount}

**Account Number** : {self.transaction.account_number}

**Categories** : {','.join(self.transaction.categories)}

**Tags** : {','.join(self.transaction.tags)}
"""
        self.markdown_widget = Markdown(self.markdown, id="transaction_detail_markdown")
        self.markdown_widget.styles.border = ("heavy", "white")
        self.markdown_widget.styles.border_title_align = "center"
        self.markdown_widget.border_title = "Transaction Details"

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        yield self.markdown_widget

    def on_key(self, key: events.Key) -> None:
        """Handle keypress events."""
        if key.key == "escape":
            self.app.pop_screen()
