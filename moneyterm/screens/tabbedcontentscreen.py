from textual import on, events
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    TabbedContent,
    TabPane,
    Label,
    Select,
    Static,
    Button,
    Input,
    OptionList,
    Rule,
)
from rich.table import Table
from textual.containers import Horizontal, Grid
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen


class TagsSummaryTable(Static):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def generate(self, account: str, year: int, month: int) -> None:
        """Update the datatable when month selection changed."""
        tags_table = Table(show_header=True)
        for label in ["Tag", "Total"]:
            tags_table.add_column(label)
        transactions = self.ledger.get_tx_by_month(account, year, month)
        for tag in self.ledger.get_all_tags():
            transactions = self.ledger.get_tx_by_month(account, year, month)
            total = sum([tx.amount for tx in transactions if tag in tx.tags])
            tags_table.add_row(tag, str(total))
        self.update(tags_table)


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
                key=tx.txid,
            )

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


class TabbedContentScreen(Screen):
    CSS_PATH = "../tcss/tabbedcontentscreen.tcss"

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
        self.tag_summary_table: TagsSummaryTable = TagsSummaryTable(self.ledger)

        yield Header()
        yield Footer()
        with Horizontal(id="selectors_bar"):
            yield Label("Account")
            yield self.account_select
            yield Label("Year")
            yield self.year_select
            yield Label("Month")
            yield self.month_select
        with TabbedContent(initial="transactions_tab", id="tabbed_content"):
            with TabPane("Overview", id="overview_tab"):
                yield self.tag_summary_table
            with TabPane("Transactions", id="transactions_tab"):
                yield self.transactions_table
            with TabPane("Manage", id="manage_tab"):
                with Horizontal(id="type_select"):
                    yield Label("Type")
                    yield Select([("Bill", "Bill"), ("Category", "Category")], allow_blank=True, id="type_select")
                with Grid(id="manage_grid"):
                    # row 1
                    yield Label("Group")
                    yield Select([], allow_blank=True, id="group_select")
                    yield Button("Add New", id="add_new_button")
                    # row 2
                    yield Label("Match Fields", id="match_fields_label")
                    yield Label("Matches", id="matches_label")
                    # row 3
                    yield Label("Start Date", id="start_date_label")
                    yield Input(placeholder="mm/dd/yyyy", id="start_date_input", classes="match_field_input")
                    yield OptionList(*(str(i) for i in range(20)), id="matches_option_list")
                    # row 4
                    yield Label("End Date", id="end_date_label")
                    yield Input(placeholder="mm/dd/yyyy", id="end_date_input", classes="match_field_input")
                    # row 5
                    yield Label("Memo", id="memo_label")
                    yield Input(placeholder="Memo", id="memo_input", classes="match_field_input")
                    # row 6
                    yield Label("Payee", id="payee_label")
                    yield Input(placeholder="Payee", id="payee_input", classes="match_field_input")
                    # row 7
                    yield Label("Amount", id="amount_label")
                    yield Input(placeholder="Amount", id="amount_input", classes="match_field_input")
                    # row 8
                    yield Label("Type", id="type_label")
                    yield Input(placeholder="Type", id="type_input", classes="match_field_input")
                    # row 9
                    yield Rule(id="section_split_rule")
                    # row 10
                    yield Label("Match Label", id="match_label")
                    yield Input(placeholder="Match Label", id="match_label_input")
                    # row 11
                    yield Label("Color", id="color_label")
                    yield Input(placeholder="Color", id="color_input")
                    # row 12
                    yield Label("Alias", id="alias_label")
                    yield Input(placeholder="Alias", id="alias_input")
                    # row 13
                    yield Button("Save", id="save_button")

    def on_mount(self) -> None:
        """Mount the widgets."""

        for label in ("Date", "PAYEE", "TYPE", "AMOUNT", "ACCOUNT", "CATEGORIES"):
            self.transactions_table.add_column(label, key=label)
        account_select_options = [(account, account) for account in self.ledger.accounts]
        self.account_select.set_options(account_select_options)
        self.update_year_month_selects()
        self.update_all()

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
    def update_all(self) -> None:
        """Update all relevant widgets when account/year/month selections are changed."""
        account_number = str(self.account_select.value)
        month = int(self.month_select.value)  # type: ignore
        year = int(self.year_select.value)  # type: ignore
        self.transactions_table.update_data(account_number, month, year)
        self.tag_summary_table.generate(account_number, year, month)

    def on_tabbed_content_tab_activated(self, tabbed_content: TabbedContent.TabActivated) -> None:
        if tabbed_content.tab.id == "overview_tab":
            self.update_all()
