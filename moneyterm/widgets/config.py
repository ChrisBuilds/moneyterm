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
from textual.validation import ValidationResult

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
from rich import box
from textual.containers import Horizontal, Grid, VerticalScroll, Vertical, HorizontalScroll
from textual.types import SelectType
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addlabelscreen import AddLabelScreen
from moneyterm.widgets.scopeselectbar import ScopeSelectBar
from moneyterm.widgets.transactiontable import TransactionTable
from moneyterm.screens.confirmscreen import ConfirmScreen
from moneyterm.widgets.labeler import LabelType


class Config(Widget):
    class ConfigUpdated(Message):
        """Message sent when labels are updated."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.config: dict[str, str | dict[str, str]] = {}
        self.directory_input = Input(
            id="import_directory_input",
            placeholder="Import Directory Path",
        )
        self.extension_input = Input(
            id="import_extension_input",
            placeholder=".QFX",
        )

        self.alias_account_select = Select(
            id="alias_account_select",
            options=((account, account) for account in self.ledger.accounts),
            prompt="Select Account",
        )

        self.alias_account_input = Input(id="alias_account_input", placeholder="Alias")
        self.save_config_button = Button(
            "Save Config",
            id="save_config_button",
        )

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        with Horizontal(id="import_horizontal"):
            yield Label("Import Directory", id="import_label")
            yield self.directory_input
            yield Label("Extension", id="extension_label")
            yield self.extension_input
        with Horizontal(id="alias_horizontal"):
            yield Label("Alias", id="alias_label")
            yield self.alias_account_select
            yield self.alias_account_input
        yield self.save_config_button

    def on_mount(self) -> None:
        # check for, and load, json data for config
        try:
            with open(Path("moneyterm/data/config.json"), "r") as f:
                self.config = json.load(f)
        except FileNotFoundError as e:
            self.config = {"import_directory": "", "import_extension": "", "account_aliases": {}}
        except json.decoder.JSONDecodeError as e:
            self.notify(
                f"Invalid config file. Exception: {e.msg}",
                severity="warning",
                timeout=7,
            )
            self.config = {"import_directory": "", "import_extension": "", "account_aliases": {}}
        if isinstance(self.config["import_directory"], str):
            self.directory_input.value = self.config["import_directory"]
        if isinstance(self.config["import_extension"], str):
            self.extension_input.value = self.config["import_extension"]

    def refresh_config(self) -> None:
        if isinstance(self.config["import_directory"], str):
            self.directory_input.value = self.config["import_directory"]
        if isinstance(self.config["import_extension"], str):
            self.extension_input.value = self.config["import_extension"]
        self.alias_account_select.set_options(((account, account) for account in self.ledger.accounts))
        self.alias_account_select.clear()
        self.alias_account_input.value = ""

    def write_config_json(self):
        with open(Path("moneyterm/data/config.json"), "w") as f:
            json.dump(self.config, f, indent=4)

    @on(Button.Pressed, "#save_config_button")
    def on_save_config_button_press(self, event: Button.Pressed) -> None:
        import_directory = self.directory_input.value
        import_extension = self.extension_input.value
        if import_directory and import_extension:
            self.config["import_directory"] = import_directory
            self.config["import_extension"] = import_extension
        if not self.alias_account_select.value is Select.BLANK:
            if (
                isinstance(self.config["account_aliases"], dict)
                and isinstance(self.alias_account_select.value, str)
                and isinstance(self.alias_account_input.value, str)
            ):
                self.config["account_aliases"][self.alias_account_select.value] = self.alias_account_input.value
        self.write_config_json()
        self.post_message(self.ConfigUpdated())
