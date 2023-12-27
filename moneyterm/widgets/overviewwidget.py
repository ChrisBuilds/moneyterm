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
from textual.containers import Horizontal, Grid, VerticalScroll
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addlabelscreen import AddLabelScreen
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.widgets.categorizer import Categorizer
from datetime import datetime


class TransactionMarkdownTable(Markdown):
    def __init__(self, ledger: Ledger, subject: str) -> None:
        super().__init__()
        self.ledger = ledger
        self.subject = subject
        self.transactions: list[Transaction] = []

    def on_mount(self) -> None:
        """Mount the widget."""
        pass

    def compose(self) -> ComposeResult:
        yield Markdown("")

    def generate_table(self, transactions_by_source: dict[str, list[Transaction]]) -> str:
        table = ""
        table_heading = """| Source | Date | Amount |
| ------ | ---- | ------ |"""
        table += table_heading

        if not transactions_by_source:
            table += f"\nNo {self.subject} transactions found."
            return table

        total_transaction_amount = Decimal(0)
        for source_label in transactions_by_source:
            source_heading = f"\n| {source_label} | | |"
            table += source_heading
            source_total = Decimal(0)
            for transaction in transactions_by_source[source_label]:
                total_transaction_amount += transaction.amount
                source_total += transaction.amount
                source_transaction_row = f"\n| | {transaction.date} | ${transaction.amount} |"
                table += source_transaction_row
            source_total_row = f"\n| | **Total {source_label.capitalize()}** | **${source_total}** |"
            table += source_total_row
            table += "\n| | | |"
        table += f"\n| | **Total {self.subject.capitalize()}(s)** | **${total_transaction_amount}** |"
        return table

    def update_markdown(self, transactions_by_source: dict[str, list[Transaction]]) -> None:
        """Update the markdown table when month selection changed."""
        self.update(self.generate_table(transactions_by_source))


class OverviewWidget(Widget):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.vertical_scroll = VerticalScroll(id="overview_vertical_scroll")
        self.account: str | NoSelection = NoSelection()
        self.year: int | NoSelection = NoSelection()
        self.month: int | NoSelection = NoSelection()
        self.income_table = TransactionMarkdownTable(self.ledger, "income")
        self.bill_table = TransactionMarkdownTable(self.ledger, "bill")

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
            for source_label in transaction.labels.incomes:
                if source_label not in income_tx_by_source:
                    income_tx_by_source[source_label] = list()
                income_tx_by_source[source_label].append(transaction)
            for source_label in transaction.labels.bills:
                if source_label not in bill_tx_by_source:
                    bill_tx_by_source[source_label] = list()
                bill_tx_by_source[source_label].append(transaction)

        self.income_table.update_markdown(income_tx_by_source)
        self.bill_table.update_markdown(bill_tx_by_source)

    def refresh_tables(self) -> None:
        """Refresh the tables with the same scope."""
        self.update_tables(self.account, self.year, self.month)
