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
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen


class TransactionTable(DataTable):
    account: reactive[str | NoSelection] = reactive(NoSelection)
    year: reactive[int | NoSelection] = reactive(NoSelection)
    month: reactive[int | NoSelection] = reactive(NoSelection)

    class RowSent(Message):
        def __init__(self, row_key: str) -> None:
            super().__init__()
            self.account_number, self.txid = row_key.split(":")

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.zebra_stripes = True
        self.cursor_type = "row"
        self.account_aliases: dict[str, str] = {}
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
        self.load_config_json()
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

    def add_transaction_row(self, tx: Transaction) -> None:
        self.cursor_type = "row"
        labels = ",".join(sorted(tx.labels.bills + tx.labels.categories + tx.labels.incomes))
        account_alias = self.account_aliases.get(tx.account.number, tx.account.number)
        self.add_row(
            tx.date.strftime("%Y-%m-%d"),
            tx.alias if tx.alias else tx.payee,
            tx.tx_type,
            tx.amount,
            account_alias,
            labels,
            key=f"{tx.account.number}:{tx.txid}",
        )

    def load_config_json(self) -> None:
        try:
            with open(Path("moneyterm/data/config.json"), "r") as f:
                config = json.load(f)
        except FileNotFoundError as e:
            config = {"import_directory": "", "import_extension": "", "account_aliases": {}}
        except json.decoder.JSONDecodeError as e:
            config = {"import_directory": "", "import_extension": "", "account_aliases": {}}
        if "account_aliases" in config and isinstance(config["account_aliases"], dict):
            for account, alias in config["account_aliases"].items():
                self.account_aliases[account] = alias

    def on_mount(self) -> None:
        """Mount the datatable."""
        self.add_columns_from_labels()

    def on_key(self, key: events.Key) -> None:
        # def get_selected_category(category: str):
        #     if category:
        #         self.apply_category_to_selected_transaction(category)
        #         update_row_categories()

        # if key.key == "t":
        #     if self.selected_row_key:
        #         selected_transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
        #         self.app.push_screen(QuickCategoryScreen(self.ledger, selected_transaction), get_selected_category)
        if key.key == "i":
            if self.selected_row_key:
                self.log(f"Showing transaction details for {self.selected_row_key}")
                account_number, txid = self.selected_row_key.split(":")
                transaction = self.ledger.get_tx_by_txid(account_number, txid)
                self.app.push_screen(TransactionDetailScreen(self.ledger, transaction))

        elif key.key == "I":
            if self.selected_row_key:
                self.post_message(self.RowSent(self.selected_row_key))

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
