from appdirs import AppDirs  # type: ignore
from pathlib import Path
import json
import pickle

user_data_dir = Path(AppDirs("moneyterm", "chrisbuilds").user_data_dir)
LABELS_JSON = user_data_dir / Path("labels.json")
CONFIG_JSON = user_data_dir / Path("config.json")
LEDGER_PKL = user_data_dir / Path("ledger.pkl")
BUDGETS_JSON = user_data_dir / Path("budgets.json")

DEFAULT_CONFIG = {
    "import_directory": "",
    "import_extension": "",
    "account_aliases": {},
    "default_account": "",
}
DEFAULT_LABELS: dict[str, dict[str, str]] = {"Bills": {}, "Expenses": {}, "Incomes": {}}


def check_user_data_dir() -> None:
    """Check if the user data directory exists and create it if it doesn't."""
    user_data_dir.mkdir(parents=True, exist_ok=True)


def check_labels_json() -> None:
    """Check if the labels JSON file exists and create it if it doesn't."""
    check_user_data_dir()
    if not LABELS_JSON.exists():
        with LABELS_JSON.open("w") as f:
            json.dump(DEFAULT_LABELS, f)


def check_config_json() -> None:
    """Check if the config JSON file exists and create it if it doesn't."""
    check_user_data_dir()
    if not CONFIG_JSON.exists():
        with CONFIG_JSON.open("w") as f:
            json.dump(DEFAULT_CONFIG, f)


def check_budgets_json() -> None:
    """Check if the budgets JSON file exists and create it if it doesn't."""
    check_user_data_dir()
    if not BUDGETS_JSON.exists():
        with BUDGETS_JSON.open("w") as f:
            json.dump({}, f)


def check_ledger_pkl() -> None:
    """Check if the ledger pickle file exists and create it if it doesn't."""
    check_user_data_dir()
    if not LEDGER_PKL.exists():
        with LEDGER_PKL.open("wb") as f:
            pickle.dump(({}, {}), f)
