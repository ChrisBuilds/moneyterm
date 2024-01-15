import json
from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    Label,
    Select,
    Button,
    Input,
)
from textual.widgets.select import InvalidSelectValueError
from textual.containers import Horizontal
from moneyterm.utils.ledger import Ledger

DEFAULT_CONFIG = {"import_directory": "", "import_extension": "", "account_aliases": {}, "default_account": ""}


class Config(Widget):
    """Widget for configuring settings.

    This widget provides a user interface for configuring various settings, such as import directory, extension,
    account aliases, and default account. It allows the user to input values and save the configuration to a JSON file.
    The widget also provides functionality for importing transactions and sending messages when the configuration is updated.
    """

    class ConfigUpdated(Message):
        """Message sent when labels are updated."""

        def __init__(self) -> None:
            super().__init__()

    class ImportTransactions(Message):
        """Message sent when transactions are imported."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, ledger: Ledger) -> None:
        """
        Initialize the Config widget.

        Args:
            ledger (Ledger): The ledger object.

        Attributes:
            ledger (Ledger): The ledger object.
            config (dict): The configuration settings.
            directory_input (Input): The input field for the import directory path.
            extension_input (Input): The input field for the import file extension.
            alias_account_select (Select): The select field for choosing an account for aliasing.
            alias_account_input (Input): The input field for entering an alias for the selected account.
            save_config_button (Button): The button for saving the configuration.
            default_account_select (Select): The select field for choosing a default account.
            import_transactions_button (Button): The button for importing transactions.
        """
        super().__init__()
        self.ledger = ledger
        self.config = DEFAULT_CONFIG
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
        self.save_config_button = Button("Save Config", id="save_config_button")

        self.default_account_select = Select(
            id="default_account_select",
            options=((account, account) for account in self.ledger.accounts),
            prompt="Select Account",
        )

        self.import_transactions_button = Button("Import Transactions", id="import_transactions_button")

    def compose(self) -> ComposeResult:
        """
        Compose the widgets.

        Returns:
            ComposeResult: The composed widgets.
        """
        with Horizontal(id="import_horizontal"):
            yield Label("Import Directory", id="import_label")
            yield self.directory_input
            yield Label("Extension", id="extension_label")
            yield self.extension_input
        with Horizontal(id="alias_horizontal"):
            yield Label("Account", id="alias_label")
            yield self.alias_account_select
            yield self.alias_account_input
        with Horizontal(id="default_account_horizontal"):
            yield Label("Default Account", id="default_label")
            yield self.default_account_select
        with Horizontal(id="button_horizontal"):
            yield self.save_config_button
            yield self.import_transactions_button

    def on_mount(self) -> None:
        """
        Perform actions when the widget is mounted.

        This method is called when the widget is mounted and performs the following actions:
        1. Loads the configuration from a JSON file.
        2. Sets the values of the directory_input and extension_input widgets based on the loaded configuration.
        3. Sets the value of the default_account_select widget based on the loaded configuration, if it is a string.
        4. Clears the default_account_select widget if the loaded configuration does not have a valid default account.

        """
        self.load_config_json()
        if isinstance(self.config["import_directory"], str):
            self.directory_input.value = self.config["import_directory"]
        if isinstance(self.config["import_extension"], str):
            self.extension_input.value = self.config["import_extension"]
        if self.config["default_account"] and isinstance(self.config["default_account"], str):
            try:
                self.default_account_select.value = self.config["default_account"]
            except InvalidSelectValueError:
                self.default_account_select.clear()
        else:
            self.default_account_select.clear()

    def refresh_config(self) -> None:
        """
        Refresh the configuration.

        This method updates the widget's configuration based on the values stored in the `config` attribute.
        It sets the values of the `directory_input` and `extension_input` widgets based on the `import_directory`
        and `import_extension` values in the `config` dictionary, respectively.

        It also updates the options of the `alias_account_select` and `default_account_select` widgets based on
        the accounts stored in the `ledger` attribute. If a `default_account` is specified in the `config` dictionary,
        it sets the value of the `default_account_select` widget to that account, if it exists in the ledger.

        If the `default_account` value is invalid or not specified, it clears the `default_account_select` widget.

        Note: This method assumes that the `config` attribute is a dictionary containing the necessary configuration values,
        and that the `ledger` attribute is an object with an `accounts` attribute representing a collection of accounts.
        """
        if isinstance(self.config["import_directory"], str):
            self.directory_input.value = self.config["import_directory"]
        if isinstance(self.config["import_extension"], str):
            self.extension_input.value = self.config["import_extension"]
        self.alias_account_select.set_options(((account, account) for account in self.ledger.accounts))
        self.alias_account_select.clear()
        self.alias_account_input.value = ""
        self.default_account_select.set_options(((account, account) for account in self.ledger.accounts))
        if self.config["default_account"] and isinstance(self.config["default_account"], str):
            try:
                self.default_account_select.value = self.config["default_account"]
            except InvalidSelectValueError:
                self.default_account_select.clear()
        else:
            self.default_account_select.clear()

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

    def write_config_json(self):
        """
        Write the configuration to a JSON file.
        """
        with Path("moneyterm/data/config.json").open("w") as config_file:
            json.dump(self.config, config_file, indent=4)

    @on(Button.Pressed, "#save_config_button")
    def on_save_config_button_press(self, event: Button.Pressed) -> None:
        """
        Handle the button press event for saving the configuration.

        Args:
            event (Button.Pressed): The button press event.
        """
        import_directory = self.directory_input.value
        import_extension = self.extension_input.value
        self.config["import_directory"] = import_directory
        self.config["import_extension"] = import_extension
        if not self.alias_account_select.value is Select.BLANK:
            if (
                isinstance(self.config["account_aliases"], dict)
                and isinstance(self.alias_account_select.value, str)
                and isinstance(self.alias_account_input.value, str)
            ):
                self.config["account_aliases"][self.alias_account_select.value] = f"{self.alias_account_input.value}"
        if not self.default_account_select.value is Select.BLANK:
            if isinstance(self.default_account_select.value, str):
                self.config["default_account"] = self.default_account_select.value
        self.write_config_json()
        self.notify("Config saved.", severity="information", timeout=5, title="Config Saved")
        for account in self.config["account_aliases"]:
            self.ledger.add_account_alias(account, self.config["account_aliases"].get(account, ""))  # type: ignore
        self.post_message(self.ConfigUpdated())
        self.ledger.save_ledger_pkl()

    @on(Select.Changed, "#alias_account_select")
    def on_alias_account_select_change(self, event: Select.Changed) -> None:
        """
        Handle the select change event for the alias account.

        Args:
            event (Select.Changed): The select change event.
        """
        if isinstance(self.config["account_aliases"], dict) and isinstance(event.value, str):
            if event.value in self.config["account_aliases"]:
                self.alias_account_input.value = self.config["account_aliases"][event.value]
            else:
                self.alias_account_input.value = ""

    @on(Button.Pressed, "#import_transactions_button")
    def on_import_transactions_button_press(self, event: Button.Pressed) -> None:
        """
        Handle the button press event for importing transactions.

        Args:
            event (Button.Pressed): The button press event.
        """
        if isinstance(self.config["import_directory"], str) and isinstance(self.config["import_extension"], str):
            if self.config["import_directory"] and self.config["import_extension"]:
                self.post_message(self.ImportTransactions())
            else:
                self.notify(
                    "Cannot Import: Import directory and extension must be set.",
                    severity="warning",
                    timeout=5,
                    title="Import Error",
                )
