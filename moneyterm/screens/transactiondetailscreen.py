from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import (
    Button,
    Label,
    Markdown,
    Button,
)
from textual.containers import Vertical
from moneyterm.utils.ledger import Ledger, Transaction


class ManualLabelButtons(Widget):
    """Widget for displaying the manual labels of a transaction.

    This widget is responsible for displaying the manual labels of a transaction.

    Attributes:
        manual_labels (list[str]): A list of manual labels of the transaction.
        id (str): The ID of the widget.

    """

    def __init__(self, tx: Transaction) -> None:
        """Initialize the widget.

        Args:
            tx (Transaction): Transaction object

        """
        super().__init__()
        self.manual_labels = tx.manual_labels.bills + tx.manual_labels.expenses + tx.manual_labels.incomes
        self.id = "manual_label_buttons"

    def compose(self) -> ComposeResult:
        """Compose the widget.

        Yields:
            button (Button): A button representing a manual label.

        """
        for label in self.manual_labels:
            button = Button(f"{label}", id=f"manual_label_button_{label}", name=label)
            button.can_focus = False
            yield button


class TransactionDetailScreen(ModalScreen):
    """Screen for displaying the details of a transaction.

    Attributes:
        CSS_PATH (str): The path to the CSS file for styling the screen.

    Args:
        ledger (Ledger): The ledger object.
        transaction (Transaction): The transaction object.
    """

    CSS_PATH = "../tcss/transactiondetailscreen.tcss"

    def __init__(self, ledger: Ledger, transaction: Transaction) -> None:
        """Initialize the TransactionDetailScreen.

        Args:
            ledger (Ledger): The ledger object.
            transaction (Transaction): The transaction object.
        """
        super().__init__()
        self.ledger = ledger
        self.transaction = transaction
        self.label_removed = False
        self.id = "transaction_detail_screen"
        self.vertical = Vertical()
        if self.transaction.splits:
            untracked = abs(self.transaction.amount) - sum(self.transaction.splits.values())
            splits_string = ""
            for label, amount in self.transaction.splits.items():
                splits_string += f"{label} (${amount:.2f}) | "
            if untracked:
                splits_string += f"Untracked (${untracked:.2f})"
            else:
                splits_string = splits_string[:-3]
        else:
            splits_string = "None"
        self.markdown = f"""**Transaction ID** : {self.transaction.txid}
        
**Date** : {self.transaction.date}

**Memo** : {self.transaction.memo}

**Payee** : {self.transaction.payee}

**Transaction Alias** : {self.transaction.alias}

**Type** : {self.transaction.tx_type}

**Amount** : ${self.transaction.amount:.2f}

**Splits**: {splits_string}

**Account Number** : {self.transaction.account.number}

**Account Institution** : {self.transaction.account.institution}

**Account Alias** : {self.transaction.account.alias}

**Bills Auto-Labels** : {','.join(self.transaction.auto_labels.bills)}

**Expenses Auto-Labels** : {','.join(self.transaction.auto_labels.expenses)}

**Incomes Auto-Labels** : {','.join(self.transaction.auto_labels.incomes)}
"""
        self.markdown_widget = Markdown(self.markdown, id="transaction_detail_markdown")
        self.markdown_widget.styles.width = max(len(line) for line in self.markdown.splitlines())
        self.vertical.border_title = "Transaction Details"

    def compose(self) -> ComposeResult:
        """Compose the widgets.

        Yields:
            Widget: The widgets to be displayed on the screen.
        """
        with self.vertical:
            yield self.markdown_widget
            yield Label("Manual Labels (click to remove)")
            yield ManualLabelButtons(self.transaction)

    def on_key(self, key: events.Key) -> None:
        """Handle keypress events.

        Args:
            key (events.Key): The key that was pressed.
        """
        close_screen_keys = ("escape", "q", "i")
        if key.key in close_screen_keys:
            self.dismiss(self.label_removed)

    def on_button_pressed(self, pressed: Button.Pressed) -> None:
        """Remove the manual label corresponding to the pressed button.

        Args:
            pressed (Button.Pressed): The pressed button object.
        """
        label_to_remove = pressed.button.name
        if label_to_remove:
            self.ledger.remove_label_from_tx(self.transaction.account.number, self.transaction.txid, label_to_remove)
            self.label_removed = True
        pressed.button.remove()
        self.ledger.save_ledger_pkl()
