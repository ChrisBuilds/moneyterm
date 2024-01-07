from decimal import Decimal
import json
from pathlib import Path
from typing import TypedDict
from textual import on, events
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import Screen
from textual.message import Message
from textual.widget import Widget
from textual.types import NoSelection
from textual.widgets.select import InvalidSelectValueError
from textual.validation import Function
from textual.widgets.option_list import Option
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
    Checkbox,
    Markdown,
)
from rich.table import Table
from rich.text import Text
from textual.containers import Horizontal, Grid, VerticalScroll
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addlabelscreen import AddLabelScreen
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.widgets.labeler import Labeler
from datetime import datetime


class OverviewWidget(Widget):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.vertical_scroll = VerticalScroll(id="overview_vertical_scroll")
        self.account: str | NoSelection = NoSelection()
        self.year: int | NoSelection = NoSelection()
        self.month: int | NoSelection = NoSelection()
        self.income_table = Static()
        self.bill_table = Static()

    def compose(self) -> ComposeResult:
        """Compose the widgets."""

        with self.vertical_scroll:
            with Horizontal(id="overview_horizontal"):
                yield self.income_table
                yield self.bill_table

    def on_mount(self) -> None:
        """Mount the widget."""
        self.update_tables(NoSelection(), NoSelection(), NoSelection())

    def update_tables(self, account: str | NoSelection, year: int | NoSelection, month: int | NoSelection) -> None:
        self.account = account
        self.year = year
        self.month = month
        transactions: list[Transaction] = []
        if isinstance(account, NoSelection):
            transactions = self.ledger.get_all_tx()
        elif isinstance(year, NoSelection):
            transactions = self.ledger.get_tx_by_account(account)
        elif isinstance(month, NoSelection):
            transactions = self.ledger.get_tx_by_year(account, year)
        else:
            transactions = self.ledger.get_tx_by_month(account, year, month)
        income_tx_by_source: dict[str, list[Transaction]] = {}
        bill_tx_by_source: dict[str, list[Transaction]] = {}
        for transaction in transactions:
            for source_label in transaction.auto_labels.incomes:
                if source_label not in income_tx_by_source:
                    income_tx_by_source[source_label] = list()
                income_tx_by_source[source_label].append(transaction)
            for source_label in transaction.auto_labels.bills:
                if source_label not in bill_tx_by_source:
                    bill_tx_by_source[source_label] = list()
                bill_tx_by_source[source_label].append(transaction)
        self.income_table.update(self.make_table("income", income_tx_by_source))
        self.bill_table.update(self.make_table("bill", bill_tx_by_source))

    def make_table(self, source: str, transactions_by_source: dict[str, list[Transaction]]) -> Table:
        """Make a table from the given transactions."""
        table = Table(title=f"{source.capitalize()} Transactions")
        table.add_column("Source")
        table.add_column("Date", justify="right")
        table.add_column("Amount")

        if not transactions_by_source:
            table.add_row("None", "", "")
            return table

        total_transaction_amount = Decimal(0)
        for source_label in transactions_by_source:
            source_total = Decimal(0)
            for i, transaction in enumerate(transactions_by_source[source_label]):
                total_transaction_amount += transaction.amount
                source_total += transaction.amount
                formatted_date = transaction.date.strftime("%m/%d/%Y")
                table.add_row(
                    f"{source_label if i == 0 else ''}",
                    formatted_date,
                    f"${transaction.amount}",
                    end_section=len(transactions_by_source[source_label]) == 1,
                )
            if len(transactions_by_source[source_label]) > 1:
                table.add_row("", f"Total {source_label}", f"${source_total}", end_section=True, style="bold")

        table.add_row("", "Total", f"${total_transaction_amount}", style="bold")

        return table

    def refresh_tables(self) -> None:
        """Refresh the tables with the same scope."""
        self.update_tables(self.account, self.year, self.month)
