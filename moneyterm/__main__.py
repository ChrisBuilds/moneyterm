from textual.app import App
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.tabbedcontentscreen import TabbedContentScreen
from moneyterm.utils import config


class MoneyTerm(App):
    """Finance dashboard TUI."""

    LEDGER: Ledger = Ledger()
    CSS_PATH = "tcss/moneyterm.tcss"
    BINDINGS = [("ctrl+c", "quit", "Quit")]
    SCREENS = {"tabbedcontent": TabbedContentScreen(LEDGER)}

    def __init__(self) -> None:
        super().__init__()
        config.check_user_data_dir()
        config.check_config_json()
        config.check_labels_json()
        config.check_budgets_json()
        config.check_ledger_pkl()
        self.LEDGER.read_ledger_pkl()

    def on_mount(self) -> None:
        """Mount the app."""
        self.push_screen("tabbedcontent")


def main() -> None:
    """Run the app."""
    app = MoneyTerm()
    app.run()


if __name__ == "__main__":
    main()
