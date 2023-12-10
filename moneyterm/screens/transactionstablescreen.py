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
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from pathlib import Path


class TransactionTable(DataTable):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.zebra_stripes = True
        self.cursor_type = "row"
        self.id = "transactions_table"
        self.selected_row_key: str | None = None

    def update_data(self, account: str, month: int, year: int) -> None:
        """Update the datatable when month selection changed."""
        self.clear(columns=False)
        for tx in self.ledger.get_tx_by_month(account, year, month):
            self.add_row(
                tx.date.strftime("%Y-%m-%d"),
                tx.payee,
                tx.tx_type,
                tx.amount,
                tx.account_number,
                ",".join(tx.categories),
                ",".join(tx.tags),
                key=tx.txid,
            )

    def on_key(self, key: events.Key) -> None:
        def get_selected_tag(tag: str):
            if tag:
                self.apply_tag_to_selected_transaction(tag)

        if key.key == "t":
            self.app.push_screen(TagSelectorScreen(self.ledger), get_selected_tag)
        elif key.key == "i":
            if self.selected_row_key:
                transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
                self.app.push_screen(TransactionDetailScreen(transaction))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_row_key = event.row_key.value

    def apply_tag_to_selected_transaction(self, tag: str) -> None:
        """Apply a tag to the selected transaction."""
        if self.selected_row_key is None:
            return
        self.log(f"Applying tag {tag} to transaction {self.ledger.get_tx_by_txid(self.selected_row_key)}")


class TransactionsTableScreen(Screen):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        self.account_select: Select[str] = Select(
            (("one", "one"), ("two", "two")), id="account_select", allow_blank=False, name="Account"
        )
        self.year_select: Select[str] = Select((("one", "one"), ("two", "two")), id="year_select", allow_blank=False)
        self.month_select: Select[str] = Select((("one", "one"), ("two", "two")), id="month_select", allow_blank=False)
        self.transactions_table: TransactionTable = TransactionTable(self.ledger)

        yield Header()
        yield Footer()
        with Horizontal():
            yield Label("Account")
            yield self.account_select
            yield Label("Year")
            yield self.year_select
            yield Label("Month")
            yield self.month_select
        with TabbedContent(initial="transactions", id="tabbed_content"):
            with TabPane("Transactions", id="transactions"):
                yield self.transactions_table

    def on_mount(self) -> None:
        """Mount the widgets."""

        for label in ("Date", "PAYEE", "TYPE", "AMOUNT", "ACCOUNT", "CATEGORIES", "TAGS"):
            self.transactions_table.add_column(label)
        account_select = self.query_one("#account_select", Select)
        account_select_options = [(account, account) for account in self.ledger.accounts]
        account_select.set_options(account_select_options)
        self.update_year_month_selects()
        self.update_transactions_table()

    @on(Select.Changed, "#account_select")
    def update_year_month_selects(self) -> None:
        """Update the year and month select widgets when account selection changed. Attempt to maintain the currently
        selected year and month if possible."""
        currently_selected_year = self.year_select.value
        currently_selected_month = self.month_select.value
        account_number = self.account_select.value
        tx_dates = self.ledger.find_dates_with_tx_activity(account_number=str(account_number))

        year_select_options = [(str(year), str(year)) for year in tx_dates]
        year_select_options.sort(key=lambda years: int(years[0]))
        self.year_select.set_options(year_select_options)

        if currently_selected_year in [year[0] for year in year_select_options]:
            self.year_select.value = currently_selected_year

        if isinstance(self.year_select.value, str):
            month_select_options = [
                (str(month_name), str(month)) for month, month_name in tx_dates[int(self.year_select.value)]
            ]
            month_select_options.sort(key=lambda months: int(months[1]))
            self.month_select.set_options(month_select_options)
            if currently_selected_month in [month[1] for month in month_select_options]:
                self.month_select.value = currently_selected_month

    @on(Select.Changed)
    def update_transactions_table(self) -> None:
        """Update the datatable when month selection changed."""
        account_number = str(self.account_select.value)
        month = int(self.month_select.value)  # type: ignore
        year = int(self.year_select.value)  # type: ignore
        self.transactions_table.update_data(account_number, month, year)