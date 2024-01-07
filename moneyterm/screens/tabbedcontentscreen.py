from pathlib import Path
import json
from textual.app import ComposeResult
from textual.types import NoSelection
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


DEFAULT_CONFIG = {"import_directory": "", "import_extension": "", "account_aliases": {}}


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
        self.selected_account: str | NoSelection = NoSelection()
        self.selected_year: int | NoSelection = NoSelection()
        self.selected_month: int | NoSelection = NoSelection()

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

    def on_mount(self) -> None:
        """
        Mount the screen.

        Returns:
            None

        """
        self.load_config_json()
        self.import_transactions()

    def load_config_json(self) -> None:
        """
        Load the configuration from a JSON file.
        """
        try:
            self.config = self.read_config_file()
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            self.notify(
                f"Failed to load config file. Exception: {str(e)}",
                severity="warning",
                timeout=7,
            )
            self.config = DEFAULT_CONFIG

    def read_config_file(self):
        """
        Reads the configuration file and returns its contents as a dictionary.

        Returns:
            dict: The contents of the configuration file.
        """
        with Path("moneyterm/data/config.json").open("r") as config_file:
            return json.load(config_file)

    def import_transactions(self) -> None:
        """
        Import transactions from a directory.

        Returns:
            None

        """
        self.log("Importing transactions.")
        self.load_config_json()
        if not self.config["import_directory"]:
            self.notify(
                "Import directory not set. Please set it in the config tab.",
                severity="warning",
                timeout=7,
                title="Import Error",
            )
            return
        import_dir = Path(self.config["import_directory"])
        if not import_dir.exists():
            self.notify(
                f"Import directory ({import_dir}) does not exist. Correct this in the config tab.",
                severity="warning",
                timeout=7,
                title="Import Error",
            )
            return
        if not import_dir.is_dir():
            self.notify(
                f"Import directory ({import_dir}) is not a directory. Correct this in the config tab.",
                severity="warning",
                timeout=7,
                title="Import Error",
            )
            return
        # iterate over files in import directory for files with the import_extension extension
        overall_load_results: dict[str, int] = {
            "source_files": 0,
            "accounts_added": 0,
            "transactions_added": 0,
            "transactions_ignored": 0,
        }
        for file in import_dir.iterdir():
            if file.suffix == self.config["import_extension"]:
                load_results = self.ledger.load_ofx_data(file)
                if any(load_results.values()):
                    overall_load_results["source_files"] += 1
                    overall_load_results["accounts_added"] += load_results["accounts_added"]
                    overall_load_results["transactions_added"] += load_results["transactions_added"]
                    overall_load_results["transactions_ignored"] += load_results["transactions_ignored"]
        self.notify(
            f"Import complete. {overall_load_results['source_files']} source files processed. "
            f"{overall_load_results['accounts_added']} accounts added. "
            f"{overall_load_results['transactions_added']} transactions added. "
            f"{overall_load_results['transactions_ignored']} transactions ignored.",
            title="Import Complete",
            timeout=7,
        )
        self.ledger.save_ledger_pkl()
        self.query_one(ScopeSelectBar).refresh_all_selects()
        for transaction_table in self.query(TransactionTable):
            transaction_table.update_data()
        self.query_one(OverviewWidget).refresh_tables()
        self.query_one(Budgeter).update_budgets_table()
        self.query_one(TrendSelector).handle_labels_updated()
        self.query_one(Config).refresh_config()
        self.query_one(Labeler).scan_and_update_transactions()

    def on_scope_select_bar_scope_changed(self, message: ScopeSelectBar.ScopeChanged) -> None:
        """
        Update the tag summary table and transaction table when scope selection changed.

        Args:
            message (ScopeSelectBar.ScopeChanged): The message containing the updated scope information.

        Returns:
            None

        """
        self.log(f"Scope changed: {message.account}, {message.year}, {message.month}")
        self.selected_account = message.account
        self.selected_year = message.year
        self.selected_month = message.month
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
        for transaction_table in self.query(TransactionTable):
            transaction_table.update_data()

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
        for transaction_table in self.query(TransactionTable):
            transaction_table.update_data()

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

    def on_config_import_transactions(self, event: Config.ImportTransactions) -> None:
        """
        Event handler for when transactions are imported.

        Args:
            event (Config.ImportTransactions): The event object.

        Returns:
            None

        """
        self.import_transactions()
        self.log("Transactions imported.")

    def on_transaction_table_quick_label_changed(self, event: TransactionTable.QuickLabelChanged) -> None:
        """
        Event handler for when a transaction label is added or removed via the quick label screen/transaction details screen.

        Args:
            event (TransactionTable.QuickCategoryChanged): The event object.

        Returns:
            None

        """
        self.query_one(Budgeter).update_budgets_table()
        self.overview_widget.update_tables(self.selected_account, self.selected_year, self.selected_month)
