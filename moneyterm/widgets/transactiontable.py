from datetime import datetime
from pathlib import Path
import json
from decimal import Decimal
from textual import events
from textual.reactive import reactive
from textual.types import NoSelection
from textual.message import Message

from textual.widgets import (
    DataTable,
)
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.screens.quickcategoryscreen import QuickLabelScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen


class TransactionTable(DataTable):
    class RowSent(Message):
        def __init__(self, row_key: str) -> None:
            super().__init__()
            self.account_number, self.txid = row_key.split(":")

    class QuickLabelChanged(Message):
        def __init__(self) -> None:
            super().__init__()

    account: reactive[str | NoSelection] = reactive(NoSelection)
    year: reactive[int | NoSelection] = reactive(NoSelection)
    month: reactive[int | NoSelection] = reactive(NoSelection)

    BINDINGS = [
        ("c", "quick_label", "Quick Label"),
        ("i", "transaction_details", "Transaction Details"),
        ("ctrl+l", "send_to_labeler", "Send to Labeler"),
    ]

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.zebra_stripes = True
        self.cursor_type = "row"
        self.id = "transactions_table"
        self.selected_row_key: str | None = None
        self.column_labels = ["Date", "Payee", "Type", "Amount", "Account", "Labels"]
        self.last_sort_label: str = ""
        self.reversed_sort: bool = False

    def add_columns_from_labels(self) -> None:
        """Add columns from column keys."""
        for label in self.column_labels:
            self.add_column(label, key=label)

    def update_data(self) -> None:
        """Update the datatable when month selection changed."""
        self.clear(columns=True)
        self.add_columns_from_labels()
        if (
            isinstance(self.account, NoSelection)
            or isinstance(self.year, NoSelection)
            or isinstance(self.month, NoSelection)
        ):
            self.selected_row_key = None
            self.add_row("No account/dates selected.", "", "", "", "", "")
            self.cursor_type = "none"
            return
        for tx in self.ledger.get_tx_by_month(self.account, self.year, self.month):
            self.add_transaction_row(tx)
        if self.selected_row_key:
            try:
                self.move_cursor(row=self.get_row_index(self.selected_row_key))
            except:
                pass

    def add_transaction_row(self, tx: Transaction) -> None:
        self.cursor_type = "row"
        labels = ",".join(
            sorted(
                tx.auto_labels.bills
                + tx.auto_labels.categories
                + tx.auto_labels.incomes
                + tx.manual_labels.bills
                + tx.manual_labels.categories
                + tx.manual_labels.incomes
            )
        )
        self.add_row(
            tx.date.strftime("%Y-%m-%d"),
            tx.alias if tx.alias else tx.payee,
            tx.tx_type,
            tx.amount,
            tx.account.alias if tx.account.alias else tx.account.number,
            labels,
            key=f"{tx.account.number}:{tx.txid}",
        )

    def on_mount(self) -> None:
        """Mount the datatable."""
        self.add_columns_from_labels()

    def action_send_to_labeler(self) -> None:
        if self.selected_row_key:
            self.post_message(self.RowSent(self.selected_row_key))

    def action_transaction_details(self) -> None:
        if self.selected_row_key:
            self.log(f"Showing transaction details for {self.selected_row_key}")
            account_number, txid = self.selected_row_key.split(":")
            transaction = self.ledger.get_tx_by_txid(account_number, txid)
            self.app.push_screen(
                TransactionDetailScreen(self.ledger, transaction),
                self.label_removed,
            )

    def action_quick_label(self) -> None:
        if self.selected_row_key:
            account_number, txid = self.selected_row_key.split(":")
            transaction = self.ledger.get_tx_by_txid(account_number, txid)
            self.app.push_screen(QuickLabelScreen(self.ledger, transaction), self.quick_add_label)

    def label_removed(self, label_removed: bool) -> None:
        if label_removed:
            self.update_data()
            self.post_message(self.QuickLabelChanged())

    def quick_add_label(self, label_info: tuple[str, str]) -> None:
        if self.selected_row_key:
            label, label_type = label_info
            account_number, txid = self.selected_row_key.split(":")
            self.ledger.add_label_to_tx(account_number, txid, label, label_type, auto=False)
            self.ledger.save_ledger_pkl()
            self.update_data()
            self.post_message(self.QuickLabelChanged())

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_row_key = event.row_key.value

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.selected_row_key = event.row_key.value

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """
        Sorts the transaction table based on the selected header label.

        Args:
            event (DataTable.HeaderSelected): The event object containing the selected header label.

        Returns:
            None
        """
        if str(event.label) == self.last_sort_label:
            self.reversed_sort = not self.reversed_sort
        else:
            self.reversed_sort = False
        self.last_sort_label = str(event.label)
        if str(event.label) == "Labels":
            self.log("Sorting by labels")
            self.sort("Labels", key=lambda label: label.lower(), reverse=self.reversed_sort)
        elif str(event.label) == "Date":
            self.log("Sorting by date")
            self.sort("Date", key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=self.reversed_sort)
        elif str(event.label) == "Payee":
            self.log("Sorting by payee")
            self.sort("Payee", key=lambda payee: payee.lower(), reverse=self.reversed_sort)
        elif str(event.label) == "Type":
            self.log("Sorting by type")
            self.sort("Type", key=lambda tx_type: tx_type.lower(), reverse=self.reversed_sort)
        elif str(event.label) == "Amount":
            self.log("Sorting by amount")
            self.sort("Amount", key=lambda amount: Decimal(amount), reverse=self.reversed_sort)
        elif str(event.label) == "Account":
            self.log("Sorting by account")
            self.sort("Account", reverse=self.reversed_sort)

    def watch_account(self) -> None:
        """Watch for account selection changes."""
        self.update_data()

    def watch_year(self) -> None:
        """Watch for year selection changes."""
        self.update_data()

    def watch_month(self) -> None:
        """Watch for month selection changes."""
        self.update_data()
