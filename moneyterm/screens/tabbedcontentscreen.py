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
)
from rich.table import Table
from textual.containers import Horizontal, Grid, VerticalScroll
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addgroupscreen import AddGroupScreen
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.widgets.categorizer import Categorizer
from datetime import datetime


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


class TabbedContentScreen(Screen):
    CSS_PATH = "../tcss/tabbedcontentscreen.tcss"

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        self.transactions_table: TransactionTable = TransactionTable(self.ledger)
        self.tag_summary_table: TagsSummaryTable = TagsSummaryTable(self.ledger)

        yield Header()
        yield Footer()
        yield ScopeSelectBar(self.ledger)
        with TabbedContent(initial="transactions_tab", id="tabbed_content"):
            with TabPane("Overview", id="overview_tab"):
                yield Label("Overview")
            with TabPane("Transactions", id="transactions_tab"):
                yield self.transactions_table
            with TabPane("Manage", id="manage_tab"):
                yield Categorizer(self.ledger)

    def on_scope_select_bar_scope_changed(self, message: ScopeSelectBar.ScopeChanged) -> None:
        """Update the tag summary table and transaction table when scope selection changed."""
        self.log(f"Scope changed: {message.account}, {message.year}, {message.month}")
        self.transactions_table.account = message.account
        self.transactions_table.year = message.year
        self.transactions_table.month = message.month
