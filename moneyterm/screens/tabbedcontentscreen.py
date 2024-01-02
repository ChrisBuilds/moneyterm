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
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addlabelscreen import AddLabelScreen
from moneyterm.widgets.overviewwidget import OverviewWidget
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.widgets.labeler import Labeler
from moneyterm.widgets.trends import TrendSelector
from moneyterm.widgets.budgeter import Budgeter
from moneyterm.widgets.config import Config
from datetime import datetime


class TabbedContentScreen(Screen):
    CSS_PATH = "../tcss/tabbedcontentscreen.tcss"

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        self.transactions_table: TransactionTable = TransactionTable(self.ledger)
        self.overview_widget: OverviewWidget = OverviewWidget(self.ledger)

        yield Header()
        yield Footer()
        yield ScopeSelectBar(self.ledger)
        with TabbedContent(initial="transactions_tab", id="tabbed_content"):
            with TabPane("Overview", id="overview_tab"):
                yield self.overview_widget
            with TabPane("Transactions", id="transactions_tab"):
                yield self.transactions_table
            with TabPane("Labeler", id="labeler_tab"):
                yield Labeler(self.ledger)
            with TabPane("Trends", id="trends_tab"):
                yield TrendSelector(self.ledger)
            with TabPane("Budget", id="budget_tab"):
                yield Budgeter(self.ledger)
            with TabPane("Config", id="config_tab"):
                yield Config(self.ledger)

    def on_scope_select_bar_scope_changed(self, message: ScopeSelectBar.ScopeChanged) -> None:
        """Update the tag summary table and transaction table when scope selection changed."""
        self.log(f"Scope changed: {message.account}, {message.year}, {message.month}")
        for transaction_table in self.query("TransactionTable"):
            if isinstance(transaction_table, TransactionTable):
                transaction_table.account = message.account
                transaction_table.year = message.year
                transaction_table.month = message.month
        self.overview_widget.update_tables(message.account, message.year, message.month)

    def on_labeler_labels_updated(self, event: Labeler.LabelsUpdated) -> None:
        self.log("Labels updated.")
        self.overview_widget.refresh_tables()
        self.query_one(Budgeter).update_budgets_table()

    def on_labeler_label_removed(self, event: Labeler.LabelRemoved) -> None:
        self.log("Label removed.")
        self.query_one(Budgeter).handle_category_removed(event.removed_label)
        self.query_one(TrendSelector).handle_labels_updated()

    def on_labeler_label_renamed(self, event: Labeler.LabelRenamed) -> None:
        self.log("Label renamed.")
        self.query_one(Budgeter).handle_category_renamed(event.old_label, event.new_label)
        self.query_one(TrendSelector).handle_labels_updated()

    def on_labeler_label_added(self, event: Labeler.LabelAdded) -> None:
        self.log("Label added.")
        self.query_one(Budgeter).handle_category_added()
        self.query_one(TrendSelector).handle_labels_updated()
