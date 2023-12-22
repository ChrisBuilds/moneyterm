from textual import events
from textual.reactive import reactive
from textual.types import NoSelection
from textual.widgets import (
    DataTable,
)
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen


class TransactionTable(DataTable):
    account: reactive[str | NoSelection] = reactive(NoSelection)
    year: reactive[int | NoSelection] = reactive(NoSelection)
    month: reactive[int | NoSelection] = reactive(NoSelection)

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.zebra_stripes = True
        self.cursor_type = "row"
        self.id = "transactions_table"
        self.selected_row_key: str | None = None

    def update_data(self) -> None:
        """Update the datatable when month selection changed."""
        self.clear(columns=False)
        if (
            isinstance(self.account, NoSelection)
            or isinstance(self.year, NoSelection)
            or isinstance(self.month, NoSelection)
        ):
            self.selected_row_key = None
            self.add_row("No data", "No data", "No data", "No data", "No data", "No data")
            self.cursor_type = "none"
            return
        for tx in self.ledger.get_tx_by_month(self.account, self.year, self.month):
            self.cursor_type = "row"
            self.add_row(
                tx.date.strftime("%Y-%m-%d"),
                tx.payee,
                tx.tx_type,
                tx.amount,
                tx.account_number,
                ",".join(tx.categories),
                key=tx.txid,
            )

    def on_mount(self) -> None:
        """Mount the datatable."""
        self.add_columns("Date", "Payee", "Type", "Amount", "Account", "Categories")

    def on_key(self, key: events.Key) -> None:
        def update_row_categories(*args):
            if self.selected_row_key is None:
                return
            self.update_cell(
                self.selected_row_key,
                "CATEGORIES",
                ",".join(sorted(self.ledger.get_tx_by_txid(self.selected_row_key).categories)),
            )

        def get_selected_category(category: str):
            if category:
                self.apply_category_to_selected_transaction(category)
                update_row_categories()

        if key.key == "c":
            if self.selected_row_key:
                selected_transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
                self.app.push_screen(QuickCategoryScreen(self.ledger, selected_transaction), get_selected_category)
        elif key.key == "i":
            if self.selected_row_key:
                transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
                self.app.push_screen(TransactionDetailScreen(self.ledger, transaction), update_row_categories)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_row_key = event.row_key.value

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.selected_row_key = event.row_key.value

    def apply_category_to_selected_transaction(self, category: str) -> None:
        """Apply a category to the selected transaction."""
        if self.selected_row_key is None:
            return
        self.log(f"Applying category {category} to transaction {self.ledger.get_tx_by_txid(self.selected_row_key)}")
        selected_transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
        self.ledger.add_category_to_tx(selected_transaction, category)

    def watch_account(self) -> None:
        """Watch for account selection changes."""
        self.update_data()

    def watch_year(self) -> None:
        """Watch for year selection changes."""
        self.update_data()

    def watch_month(self) -> None:
        """Watch for month selection changes."""
        self.update_data()
