from textual.app import App, ComposeResult
from moneyterm.utils.ledger import Ledger
from moneyterm.utils.financedb import FinanceDB
from moneyterm.screens.transactionstablescreen import TransactionsTableScreen


class DashboardApp(App):
    """Finance dashboard TUI."""

    DB = FinanceDB()
    LEDGER = Ledger(DB)
    CSS_PATH = "dashboard.tcss"
    BINDINGS = []
    SCREENS = {"transactions_table": TransactionsTableScreen(LEDGER)}

    def on_mount(self) -> None:
        """Mount the app."""
        self.push_screen("transactions_table")


if __name__ == "__main__":
    app = DashboardApp()
    app.run()
