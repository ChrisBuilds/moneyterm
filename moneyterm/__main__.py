from textual.app import App, ComposeResult
from moneyterm.utils.ledger import Ledger
from moneyterm.utils.financedb import FinanceDB
from moneyterm.screens.tabbedcontentscreen import TabbedContentScreen


class MoneyTerm(App):
    """Finance dashboard TUI."""

    DB: FinanceDB = FinanceDB()
    LEDGER: Ledger = Ledger(DB)
    CSS_PATH = "tcss/moneyterm.tcss"
    BINDINGS = []
    SCREENS = {"tabbedcontent": TabbedContentScreen(LEDGER)}

    def on_mount(self) -> None:
        """Mount the app."""
        self.push_screen("tabbedcontent")


if __name__ == "__main__":
    app = MoneyTerm()
    app.run()
