from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    TabPane,
)
from moneyterm.utils.ledger import Ledger
from moneyterm.widgets.overviewwidget import OverviewWidget
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.widgets.labeler import Labeler
from moneyterm.widgets.trends import TrendSelector
from moneyterm.widgets.budgeter import Budgeter
from moneyterm.widgets.config import Config


class TabbedContentScreen(Screen):
    """
    A screen that displays a tabbed content interface for managing financial data.

    Args:
        ledger (Ledger): The ledger object containing financial data.

    Attributes:
        ledger (Ledger): The ledger object containing financial data.

    """

    CSS_PATH = "../tcss/tabbedcontentscreen.tcss"

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        """
        Compose the widgets for the screen.

        Yields:
            ComposeResult: The composed widgets.

        """
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
        """
        Update the tag summary table and transaction table when scope selection changed.

        Args:
            message (ScopeSelectBar.ScopeChanged): The message containing the updated scope information.

        Returns:
            None

        """
        self.log(f"Scope changed: {message.account}, {message.year}, {message.month}")
        for transaction_table in self.query(TransactionTable):
            transaction_table.account = message.account
            transaction_table.year = message.year
            transaction_table.month = message.month
        self.overview_widget.update_tables(message.account, message.year, message.month)

    def on_labeler_labels_updated(self, event: Labeler.LabelsUpdated) -> None:
        """
        Event handler for when the labels are updated in the labeler.

        Args:
            event (Labeler.LabelsUpdated): The event object.

        Returns:
            None

        """
        self.log("Labels updated.")
        self.overview_widget.refresh_tables()
        self.query_one(Budgeter).update_budgets_table()

    def on_labeler_label_removed(self, event: Labeler.LabelRemoved) -> None:
        """
        Handles the event when a label is removed from the labeler.

        Args:
            event (Labeler.LabelRemoved): The event object containing information about the removed label.

        Returns:
            None

        """
        self.log("Label removed.")
        self.query_one(Budgeter).handle_category_removed(event.removed_label)
        self.query_one(TrendSelector).handle_labels_updated()

    def on_labeler_label_renamed(self, event: Labeler.LabelRenamed) -> None:
        """
        Handles the event when a label is renamed.

        Args:
            event (Labeler.LabelRenamed): The event object containing the old and new label names.

        Returns:
            None

        """
        self.log("Label renamed.")
        self.query_one(Budgeter).handle_category_renamed(event.old_label, event.new_label)
        self.query_one(TrendSelector).handle_labels_updated()

    def on_labeler_label_added(self, event: Labeler.LabelAdded) -> None:
        """
        Event handler for when a label is added by the labeler.

        Args:
            event (Labeler.LabelAdded): The event object containing information about the added label.

        Returns:
            None

        """
        self.log("Label added.")
        self.query_one(Budgeter).handle_category_added()
        self.query_one(TrendSelector).handle_labels_updated()

    def on_config_config_updated(self, event: Config.ConfigUpdated) -> None:
        """
        Event handler for when the configuration is updated.

        Args:
            event (Config.ConfigUpdated): The event object containing the updated configuration.

        Returns:
            None

        """
        self.log("Config updated.")
        self.query_one(ScopeSelectBar).refresh_all_selects()
        for transaction_table in self.query(TransactionTable):
            transaction_table.update_data()
