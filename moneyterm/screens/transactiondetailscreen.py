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
from moneyterm.screens.tagselectorscreen import TransactionTaggerScreen
from pathlib import Path


class TagButtons(Widget):
    """Widget for displaying the tags of a transaction."""

    def __init__(self, tags: list[str]) -> None:
        """Initialize the widget.

        Args:
            tags (list[str]): List of tags
        """

        super().__init__()
        self.tags = tags
        self.id = "tag_buttons"

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        for tag in self.tags:
            button = Button(f"{tag}", id=f"tag_button_{tag}", name=tag)
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
        self.id = "transaction_detail_screen"
        self.vertical = Vertical()
        self.markdown = f"""**Transaction ID** : {self.transaction.txid}
        
**Date** : {self.transaction.date}

**Memo** : {self.transaction.memo}

**Payee** : {self.transaction.payee}

**Type** : {self.transaction.tx_type}

**Amount** : {self.transaction.amount}

**Account Number** : {self.transaction.account_number}

**Categories** : {','.join(self.transaction.categories)}

"""
        self.markdown_widget = Markdown(self.markdown, id="transaction_detail_markdown")
        self.markdown_widget.styles.width = max(len(line) for line in self.markdown.splitlines())
        self.vertical.border_title = "Transaction Details"

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        with self.vertical:
            yield self.markdown_widget
            yield Label("Tags (click to remove)")
            yield TagButtons(sorted(self.transaction.tags))

    def on_key(self, key: events.Key) -> None:
        """Handle keypress events."""
        close_screen_keys = ("escape", "q", "i")
        if key.key in close_screen_keys:
            self.dismiss(None)

    def on_button_pressed(self, pressed: Button.Pressed) -> None:
        """Remove the tag corresponding to the pressed button."""
        tag_to_remove = pressed.button.name
        if tag_to_remove:
            self.ledger.remove_tag_from_tx(self.transaction, tag_to_remove)
        pressed.button.remove()
