import json
from pathlib import Path
from typing import TypedDict
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.types import NoSelection
from textual.validation import Function
from textual.widgets.option_list import Option
from textual.widgets import (
    Label,
    Select,
    Button,
    Input,
    OptionList,
    Rule,
    Checkbox,
)
from textual.containers import Horizontal, Grid
from moneyterm.utils.ledger import Ledger, Transaction
from moneyterm.screens.addlabelscreen import AddLabelScreen
from moneyterm.screens.renamelabelscreen import RenameLabelScreen
from moneyterm.screens.confirmscreen import ConfirmScreen
from moneyterm.widgets.transactiontable import TransactionTable
from datetime import datetime
from decimal import Decimal


# create type alias for match field input dict
class MatchFields(TypedDict):
    start_date: str
    end_date: str
    memo: str
    memo_exact: bool
    payee: str
    payee_exact: bool
    amount_min: str
    amount_max: str
    type: str
    match_name: str
    color: str
    alias: str


MatchLabel = dict[str, MatchFields]
LabelType = dict[str, MatchLabel]


class Labeler(Widget):
    """
    A widget for managing labels in the MoneyTerm application.

    This widget allows the user to create, rename, remove, and select labels for categorizing transactions.
    It also provides options for filtering transactions based on various criteria such as date, memo, payee, and amount.

    Attributes:
        selected_type (reactive[str]): The currently selected label type.
        selected_label (reactive[str | NoSelection]): The currently selected label.
        selected_match_option (reactive[Option | None]): The currently selected match option.
        BINDINGS (List[Tuple[str, str, str]]): A list of key bindings for the widget.
        ledger (Ledger): The ledger object used for managing transactions.
        labels (Dict[str, LabelType]): A dictionary containing the labels for different types.

    Methods:
        write_labels_json(self): Writes the labels dictionary to a JSON file.
        action_clear_input(self) -> None: Clears the input field if it is currently focused.
        on_manage_type_select_change(self, event: Select.Changed) -> None: Handles the change event of the manage type select widget.
        on_label_select_change(self, event: Select.Changed) -> None: Handles the event when the label selection changes.
        on_matches_option_list_select(self, event: OptionList.OptionSelected) -> None: Handles the event when an option is selected from the matches option list.
        on_create_new_label_button_press(self, event: Button.Pressed) -> None: Event handler for the 'create new label' button press.
    """

    class LabelsUpdated(Message):
        """Message sent when labels are updated."""

        def __init__(self) -> None:
            super().__init__()

    class LabelRenamed(Message):
        """Message sent when a label is renamed."""

        def __init__(self, old_label: str, new_label: str) -> None:
            super().__init__()
            self.old_label = old_label
            self.new_label = new_label

    class LabelRemoved(Message):
        """Message sent when a label is removed."""

        def __init__(self, removed_label: str) -> None:
            super().__init__()
            self.removed_label = removed_label

    class LabelAdded(Message):
        """Message sent when a label is added."""

        def __init__(self, added_label: str) -> None:
            super().__init__()
            self.added_label = added_label

    selected_type: reactive[str] = reactive("Bills")
    selected_label: reactive[str | NoSelection] = reactive(NoSelection)
    selected_match_option: reactive[Option | None] = reactive(None)

    BINDINGS = [("ctrl+x", "clear_input", "Clear Input")]

    def __init__(self, ledger: Ledger) -> None:
        super().__init__(id="labeler")
        self.ledger = ledger
        self.labels: dict[str, LabelType]
        # widgets
        self.type_select_label = Label("Type")
        self.type_select = Select(
            [("Bills", "Bills"), ("Expenses", "Expenses"), ("Incomes", "Incomes")],
            allow_blank=False,
            id="manage_type_select",
        )
        self.label_select_label = Label("Label", id="label_select_label")
        self.label_select: Select[str] = Select([], allow_blank=True, id="label_select")
        self.create_new_label_button = Button("Create New", id="create_new_label_button")
        self.remove_label_button = Button("Remove", id="remove_label_button")
        self.rename_label_button = Button("Rename", id="rename_label_button")
        self.match_fields_label = Label("Match Fields", id="match_fields_label")
        self.matches_label = Label("Matches", id="matches_label")
        self.start_date_label = Label("Start Date", id="start_date_label")
        self.start_date_input = Input(
            placeholder="mm/dd/yyyy",
            restrict=r"[0-9\/]*",
            validators=[Function(self.validate_date_format, "Date must be in the format mm/dd/yyyy.")],
            valid_empty=True,
            id="start_date_input",
            classes="match_field_input",
        )
        self.matches_option_list = OptionList(id="matches_option_list")
        self.end_date_label = Label("End Date", id="end_date_label")
        self.end_date_input = Input(
            placeholder="mm/dd/yyyy",
            restrict=r"[0-9\/]*",
            validators=[
                Function(self.validate_date_format, "Date must be in the format mm/dd/yyyy."),
                Function(self.validate_end_date_after_start_date, "End date must be after start date."),
            ],
            valid_empty=True,
            id="end_date_input",
            classes="match_field_input",
        )
        self.memo_label = Label("Memo", id="memo_label")
        self.memo_input = Input(placeholder="Memo", id="memo_input", classes="match_field_input")
        self.memo_exact_match_checkbox = Checkbox("Exact", id="memo_exact_match_checkbox")
        self.payee_label = Label("Payee", id="payee_label")
        self.payee_input = Input(placeholder="Payee", id="payee_input", classes="match_field_input")
        self.payee_exact_match_checkbox = Checkbox("Exact", id="payee_exact_match_checkbox")
        self.amount_label = Label("Amount", id="amount_label")
        self.amount_lower_bound_input = Input(
            placeholder="min Ex: 53.49",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_decimal,
                    "Amount must be number/decimal. Ex: 3, 3.01",
                )
            ],
            valid_empty=True,
            id="amount_lower_bound_input",
            classes="match_field_input",
        )
        self.amount_upper_bound_input = Input(
            placeholder="max Ex: 53.49",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_decimal,
                    "Amount must be number/decimal. Ex: 3, 3.01",
                )
            ],
            valid_empty=True,
            id="amount_upper_bound_input",
            classes="match_field_input",
        )
        self.type_label = Label("Type", id="type_label")
        self.type_input = Input(placeholder="Type", id="type_input", classes="match_field_input")
        self.remove_match_button = Button("Remove Match", id="remove_match_button")
        self.section_split_rule = Rule(id="section_split_rule")
        self.match_name = Label("Match Name", id="match_name")
        self.match_name_input = Input(placeholder="Match Name", id="match_name_input", valid_empty=False)
        self.color_label = Label("Color", id="color_label")
        self.color_input = Input(placeholder="Color", id="color_input")
        self.alias_label = Label("Alias", id="alias_label")
        self.alias_input = Input(placeholder="Alias", id="alias_input")
        self.save_button = Button("Save", id="save_button")
        self.save_button.disabled = True
        self.preview_button = Button("Show Matches", id="preview_button")
        self.show_all_tx_checkbox = Checkbox("Show All Transactions", id="show_all_tx_checkbox")
        self.scan_and_update_button = Button("Scan and Update", id="scan_and_update_button")
        self.preview_table: TransactionTable = TransactionTable(self.ledger)
        self.preview_table.border_title = "Transactions Preview Results"

    def on_mount(self):
        # check for, and load, json data for labels
        try:
            with open(Path("moneyterm/data/labels.json"), "r") as f:
                self.labels = json.load(f)
        except FileNotFoundError:
            self.labels = {"Bills": {}, "Expenses": {}, "Incomes": {}}
            self.write_labels_json()
        self.update_label_select()

    def write_labels_json(self):
        """
        Writes the labels dictionary to a JSON file.

        """
        with open(Path("moneyterm/data/labels.json"), "w") as f:
            json.dump(self.labels, f, indent=4)

    def compose(self) -> ComposeResult:
        with Horizontal(id="type_select_bar"):
            yield self.type_select_label
            yield self.type_select
        with Grid(id="labeler_grid"):
            # row 1
            yield self.label_select_label
            yield self.label_select
            with Horizontal(id="label_create_remove_buttons"):
                yield self.create_new_label_button
                yield self.remove_label_button
                yield self.rename_label_button
            # row 2
            yield self.match_fields_label
            yield self.matches_label
            # row 3
            yield self.start_date_label
            yield self.start_date_input
            yield self.matches_option_list
            # row 4
            yield self.end_date_label
            yield self.end_date_input
            # row 5
            yield self.memo_label
            with Horizontal(id="memo_field_bar"):
                yield self.memo_input
                yield self.memo_exact_match_checkbox
            # row 6
            yield self.payee_label
            with Horizontal(id="payee_field_bar"):
                yield self.payee_input
                yield self.payee_exact_match_checkbox

            # row 7
            yield self.amount_label
            with Horizontal(id="amount_field_bar"):
                yield self.amount_lower_bound_input
                yield self.amount_upper_bound_input
            # row 8
            yield self.type_label
            yield self.type_input
            yield self.remove_match_button
            # row 9
            yield self.section_split_rule
            # row 10
            with Horizontal(id="match_name_row"):
                yield self.match_name
                yield self.match_name_input
                # row 11
                yield self.color_label
                yield self.color_input
                # row 12
                yield self.alias_label
                yield self.alias_input
                # row 13
            with Horizontal(id="save_preview_buttons"):
                yield self.save_button
                yield self.preview_button
                yield self.show_all_tx_checkbox
                yield self.scan_and_update_button
        with Horizontal(id="preview_table_horizontal"):
            yield self.preview_table

    def action_clear_input(self) -> None:
        """
        Clears the input field if it is currently focused.

        This method checks if the currently focused widget is an instance of the Input class,
        and if so, it clears the input field.
        """
        focused = self.app.focused
        if isinstance(focused, Input):
            focused.clear()

    @on(Select.Changed, "#manage_type_select")
    def on_manage_type_select_change(self, event: Select.Changed) -> None:
        """
        Handle the change event of the manage type select widget.

        Args:
            event (Select.Changed): The event object containing the new selected value.
        """
        self.selected_type = str(event.value)

    @on(Select.Changed, "#label_select")
    def on_label_select_change(self, event: Select.Changed) -> None:
        """
        Handles the event when the label selection changes.

        Args:
            event (Select.Changed): The event object containing the changed value.

        Returns:
            None
        """
        if self.label_select.is_blank():
            self.selected_label = NoSelection()
        else:
            self.selected_label = str(event.value)

    @on(OptionList.OptionSelected, "#matches_option_list")
    def on_matches_option_list_select(self, event: OptionList.OptionSelected) -> None:
        """
        Handles the event when an option is selected from the matches option list.

        Args:
            event (OptionList.OptionSelected): The event object containing the selected option.
        """
        self.selected_match_option = event.option

    @on(Button.Pressed, "#create_new_label_button")
    def on_create_new_label_button_press(self, event: Button.Pressed) -> None:
        """
        Event handler for the 'create new label' button press.

        Retrieves all existing labels and pushes the 'AddLabelScreen' with the list of labels
        to allow the user to create a new label.
        """
        all_labels = []
        for label_type in self.labels:
            all_labels.extend(list(self.labels[label_type]))
        self.app.push_screen(AddLabelScreen(list(all_labels)), self.create_new_label)

    def create_new_label(self, new_label_name: str) -> None:
        """
        Creates a new label with the given name and adds it to the labels dictionary.

        Args:
            new_label_name (str): The name of the new label.

        Returns:
            None
        """
        self.labels[self.selected_type][new_label_name] = {}
        self.write_labels_json()
        self.update_label_select(set_selection=new_label_name)
        self.post_message(self.LabelAdded(added_label=new_label_name))

    @on(Button.Pressed, "#remove_label_button")
    def on_remove_label_button_press(self, event: Button.Pressed) -> None:
        """
        Handles the button press event for removing a label.

        If the selected label is of type NoSelection, the method returns without performing any action.
        Otherwise, it prompts the user with a confirmation message, including the number of matches associated with the label.
        If the user confirms the removal, the selected label and its matches are removed from the application.
        If the label is manually applied to a transaction or used in a transaction split, the split/label will also be removed.

        Args:
            event (Button.Pressed): The button press event.

        Returns:
            None
        """
        if isinstance(self.selected_label, NoSelection):
            return
        match_count = len(self.labels[self.selected_type][self.selected_label])
        message = f"Are you sure you want to remove label '{self.selected_label}' and its {match_count} matches? If this label has been manually applied to a transaction or is used in a transaction split, the split/label will be removed."
        self.app.push_screen(ConfirmScreen(message), self.remove_selected_label)

    def remove_selected_label(self, confirm: bool) -> None:
        """
        Removes the selected label from the labeler.

        Args:
            confirm (bool): Flag indicating whether to confirm the removal.

        Returns:
            None
        """
        if isinstance(self.selected_label, NoSelection):
            return
        if confirm:
            removed_label = self.selected_label
            self.labels[self.selected_type].pop(self.selected_label)
            self.ledger.remove_label_from_all_tx(self.selected_label)
            self.write_labels_json()
            self.update_label_select()
            self.scan_and_update_transactions()
            self.post_message(self.LabelRemoved(removed_label=removed_label))

    @on(Button.Pressed, "#rename_label_button")
    def on_rename_label_button_press(self, event: Button.Pressed) -> None:
        """
        Handles the button press event for renaming a label.

        Args:
            event (Button.Pressed): The button press event.

        Returns:
            None
        """
        if isinstance(self.selected_label, NoSelection):
            return
        self.app.push_screen(
            RenameLabelScreen(self.selected_label, list(self.labels[self.selected_type])), self.rename_label
        )

    def rename_label(self, new_label_name: str) -> None:
        """
        Renames the selected label to the specified new label name.

        Args:
            new_label_name (str): The new name for the label.

        Returns:
            None
        """
        if isinstance(self.selected_label, NoSelection):
            return
        old_label = self.selected_label
        self.labels[self.selected_type][new_label_name] = self.labels[self.selected_type].pop(self.selected_label)
        self.write_labels_json()
        self.update_label_select(set_selection=new_label_name)
        self.ledger.rename_label(old_label, new_label_name)
        self.post_message(self.LabelRenamed(old_label=old_label, new_label=new_label_name))

    @on(Button.Pressed, "#save_button")
    def on_save_button_press(self, event: Button.Pressed) -> None:
        """
        Handles the event when the save button is pressed.

        Saves the selected label with the specified match fields and their values to the labels dictionary.
        Writes the updated labels dictionary to a JSON file.
        Updates the match options list and selects the saved match name.
        Scans and updates the transactions based on the updated labels.
        """
        if isinstance(self.selected_label, NoSelection):
            return
        if not self.validate_match_fields():
            return
        self.labels[self.selected_type][self.selected_label][self.match_name_input.value] = {
            "start_date": self.start_date_input.value,
            "end_date": self.end_date_input.value,
            "memo": self.memo_input.value,
            "memo_exact": self.memo_exact_match_checkbox.value,
            "payee": self.payee_input.value,
            "payee_exact": self.payee_exact_match_checkbox.value,
            "amount_min": self.amount_lower_bound_input.value,
            "amount_max": self.amount_upper_bound_input.value,
            "type": self.type_input.value,
            "match_name": self.match_name_input.value,
            "color": self.color_input.value,
            "alias": self.alias_input.value,
        }
        self.write_labels_json()
        self.update_match_options_list(set_selection=self.match_name_input.value)
        self.scan_and_update_transactions()

    @on(Button.Pressed, "#remove_match_button")
    def on_remove_match_button_press(self, event: Button.Pressed) -> None:
        """
        Handles the button press event for removing a match.

        Args:
            event (Button.Pressed): The button press event.

        Returns:
            None
        """
        # verify valid label and match option are selected
        if (
            self.selected_match_option is None
            or self.selected_match_option.id is None
            or isinstance(self.selected_label, NoSelection)
        ):
            return
        message = f"Are you sure you want to remove match '{self.selected_match_option.id}'? Transactions with this match will no longer be labeled."
        self.app.push_screen(ConfirmScreen(message), self.remove_selected_match)

    def remove_selected_match(self, confirm: bool) -> None:
        """
        Removes the selected match option from the labels dictionary and performs necessary updates.

        Args:
            confirm (bool): Indicates whether to confirm the removal.

        Returns:
            None
        """
        if (
            self.selected_match_option is None
            or self.selected_match_option.id is None
            or isinstance(self.selected_label, NoSelection)
        ):
            return
        if confirm:
            self.labels[self.selected_type][self.selected_label].pop(self.selected_match_option.id)
            self.write_labels_json()
            self.update_match_options_list()
            self.scan_and_update_transactions()

    @on(Button.Pressed, "#preview_button")
    def on_preview_button_press(self, event: Button.Pressed) -> None:
        """
        Handle the button press event for the preview button.

        This method is called when the preview button is pressed. It retrieves the selected account, year, and month
        from the corresponding select widgets. If any of these values are not selected, it displays an error notification
        and returns.

        It then retrieves the transactions for the selected account, year, and month from the ledger. If the match fields
        are not valid, it returns without adding any transaction rows to the preview table.

        For each transaction, it checks if it matches the specified match fields. If it does, it adds the transaction row
        to the preview table. If the 'show_all_tx_checkbox' is checked, it adds all transactions to the preview table,
        regardless of whether they match the specified match fields.

        Args:
            event (Button.Pressed): The button press event.

        Returns:
            None
        """
        account_select: Select = self.app.query_one("#account_select", expect_type=Select)
        year_select: Select = self.app.query_one("#year_select", expect_type=Select)
        month_select: Select = self.app.query_one("#month_select", expect_type=Select)
        if any(
            isinstance(scope_select.value, NoSelection) for scope_select in (account_select, year_select, month_select)
        ):
            self.notify("Account, year, and month must be selected!", title="Error", severity="error", timeout=7)
            return
        transactions = self.ledger.get_tx_by_month(
            str(account_select.value), int(year_select.value), int(month_select.value)  # type: ignore
        )
        self.preview_table.clear()
        if not self.validate_match_fields():
            return
        match_fields = self.get_match_fields()
        for tx in transactions:
            if self.check_transaction_match(tx, match_fields):
                self.preview_table.add_transaction_row(tx)
            else:
                if self.show_all_tx_checkbox.value:
                    self.preview_table.add_transaction_row(tx)

    @on(Button.Pressed, "#scan_and_update_button")
    def on_scan_and_update_button_press(self, event: Button.Pressed) -> None:
        self.scan_and_update_transactions()

    def scan_and_update_transactions(self) -> None:
        """Scan all transactions and update their labels."""
        for transaction in self.ledger.get_all_tx():
            transaction.auto_labels.bills.clear()
            transaction.auto_labels.expenses.clear()
            transaction.auto_labels.incomes.clear()
            for label_type in self.labels:
                for label in self.labels[label_type]:
                    for match in self.labels[label_type][label]:
                        match_fields = self.labels[label_type][label][match]
                        if self.check_transaction_match(transaction, match_fields):
                            self.ledger.add_label_to_tx(transaction.account.number, transaction.txid, label, label_type)
                            if match_fields["alias"]:
                                transaction.alias = match_fields["alias"]
            self.ledger.validate_split_labels(transaction.account.number, transaction.txid)

        self.notify(f"All transaction labels updated.", title="Scan and Update Complete", timeout=7)
        self.ledger.save_ledger_pkl()
        self.post_message(self.LabelsUpdated())

    def on_transaction_table_row_sent(self, message: TransactionTable.RowSent) -> None:
        """
        Handles the event when a row is sent from the transaction table.

        Args:
            message (TransactionTable.RowSent): The message containing the account number and transaction ID.

        Returns:
            None
        """
        transaction = self.ledger.get_tx_by_txid(message.account_number, message.txid)
        self.start_date_input.value = transaction.date.strftime("%m/%d/%Y")
        self.end_date_input.value = transaction.date.strftime("%m/%d/%Y")
        self.memo_input.value = transaction.memo
        self.memo_exact_match_checkbox.value = False
        self.payee_input.value = transaction.payee
        self.payee_exact_match_checkbox.value = False
        self.amount_lower_bound_input.value = str(transaction.amount)
        self.amount_upper_bound_input.value = str(transaction.amount)
        self.type_input.value = transaction.tx_type

    def get_match_fields(self) -> MatchFields:
        """
        Returns a dictionary containing the match fields and their corresponding values.

        Returns:
            MatchFields: A dictionary containing the match fields and their values.
        """
        return {
            "start_date": self.start_date_input.value,
            "end_date": self.end_date_input.value,
            "memo": self.memo_input.value,
            "memo_exact": self.memo_exact_match_checkbox.value,
            "payee": self.payee_input.value,
            "payee_exact": self.payee_exact_match_checkbox.value,
            "amount_min": self.amount_lower_bound_input.value,
            "amount_max": self.amount_upper_bound_input.value,
            "type": self.type_input.value,
            "match_name": self.match_name_input.value,
            "color": self.color_input.value,
            "alias": self.alias_input.value,
        }

    def validate_date_format(self, date_str: str) -> bool:
        """
        Validates the format of a date string.

        Args:
            date_str (str): The date string to be validated.

        Returns:
            bool: True if the date string is in the format "%m/%d/%Y", False otherwise.
        """
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except:
            return False

    def validate_end_date_after_start_date(self, end_date: str) -> bool:
        """
        Validates if the end date is after the start date.

        Args:
            end_date (str): The end date to be validated.

        Returns:
            bool: True if the end date is after the start date, False otherwise.
        """
        if not self.start_date_input.value:
            return True
        try:
            start_date_obj = datetime.strptime(self.start_date_input.value, "%m/%d/%Y")
            end_date_obj = datetime.strptime(end_date, "%m/%d/%Y")
            return start_date_obj <= end_date_obj
        except:
            return False

    def validate_amount_is_decimal(self, amount: str) -> bool:
        """
        Validates if the given amount is a decimal number.

        Args:
            amount (str): The amount to be validated.

        Returns:
            bool: True if the amount is a decimal number, False otherwise.
        """
        try:
            Decimal(amount)
            return True
        except:
            return False

    def validate_match_fields(self) -> bool:
        """
        Validates the match fields and returns True if all fields are valid, False otherwise.

        Returns:
            bool: True if all fields are valid, False otherwise.
        """
        # require a Match Name
        validated = True
        if not self.match_name_input.value:
            self.notify("Match Name cannot be empty!", title="Error", severity="error", timeout=7)
            validated = False
        # check match field valid states
        for match_field in (
            self.start_date_input,
            self.end_date_input,
            self.amount_lower_bound_input,
        ):
            validation_result = match_field.validate(match_field.value)
            if validation_result is None or validation_result.is_valid:
                continue
            else:
                for failure_reason in validation_result.failure_descriptions:
                    self.notify(failure_reason, title="Error", severity="error", timeout=7)
                validated = False

        # require at least one of memo, payee or amount
        if all(
            [
                not self.memo_input.value,
                not self.payee_input.value,
                not self.amount_lower_bound_input.value,
                not self.amount_upper_bound_input.value,
            ]
        ):
            self.notify(
                "At least one of (Memo, Payee, Amount) must be specified!", title="Error", severity="error", timeout=7
            )
            validated = False
        return validated

    def update_label_select(self, set_selection: str | None = None) -> None:
        """Update the label select options based on the selected type.

        Args:
            set_selection (str | None, optional): String option to select after the update. Defaults to None.
        """
        label_options = [(label, label) for label in self.labels[self.selected_type]]
        label_options.sort(key=lambda x: x[0])
        self.label_select.set_options(label_options)
        if set_selection:
            self.label_select.value = set_selection
            self.selected_label = set_selection
        else:
            self.selected_label = NoSelection()

    def update_match_options_list(self, set_selection: str | None = None) -> None:
        """Update the match options list based on the selected label.

        Args:
            set_selection (str | None, optional): String to set as the active option after the update. Defaults to None.
        """
        self.matches_option_list.clear_options()
        self.selected_match_option = None
        if isinstance(self.selected_label, NoSelection):
            return
        for match_name in sorted(
            list(self.labels[self.selected_type][self.selected_label].keys()), key=lambda x: x.lower()
        ):
            new_option = Option(match_name, id=match_name)
            self.matches_option_list.add_option(new_option)
        if set_selection and set_selection in self.labels[self.selected_type][self.selected_label]:
            self.matches_option_list.highlighted = self.matches_option_list.get_option_index(set_selection)
            self.matches_option_list.action_select()

    def watch_selected_type(self) -> None:
        """Watch for changes to the selected type and update the label select."""
        self.update_label_select()

    def watch_selected_label(self) -> None:
        """Watch for changes to the selected label and update the match options list."""
        self.update_match_options_list()
        if isinstance(self.selected_label, NoSelection):
            self.remove_label_button.disabled = True
            self.save_button.disabled = True
            self.rename_label_button.disabled = True
        else:
            self.remove_label_button.disabled = False
            self.save_button.disabled = False
            self.rename_label_button.disabled = False

    def watch_selected_match_option(self) -> None:
        """
        Updates the widget's input fields with the values of the selected match option.
        If no match option is selected or the selected label is a NoSelection, clears all input fields.
        """
        if self.selected_match_option is None or isinstance(self.selected_label, NoSelection):
            self.remove_match_button.disabled = True
            self.start_date_input.clear()
            self.end_date_input.clear()
            self.memo_input.clear()
            self.memo_exact_match_checkbox.value = False
            self.payee_input.clear()
            self.payee_exact_match_checkbox.value = False
            self.amount_lower_bound_input.clear()
            self.amount_upper_bound_input.clear()
            self.type_input.clear()
            self.match_name_input.clear()
            self.color_input.clear()
            self.alias_input.clear()
            return
        self.remove_match_button.disabled = False
        match = self.labels[self.selected_type][self.selected_label][str(self.selected_match_option.id)]
        self.start_date_input.value = match["start_date"]
        self.end_date_input.value = match["end_date"]
        self.memo_input.value = match["memo"]
        self.memo_exact_match_checkbox.value = match["memo_exact"]
        self.payee_input.value = match["payee"]
        self.payee_exact_match_checkbox.value = match["payee_exact"]
        self.amount_lower_bound_input.value = str(match["amount_min"])
        self.amount_upper_bound_input.value = str(match["amount_max"])
        self.type_input.value = match["type"]
        self.match_name_input.value = match["match_name"]
        self.color_input.value = match["color"]
        self.alias_input.value = match["alias"]

    def check_transaction_match(self, transaction: Transaction, match_fields: MatchFields) -> bool:
        """Check if a transaction matches the match fields.

        Args:
            transaction (Transaction): Transaction object
            match_fields (MatchFields): Match fields dict

        Returns:
            bool: True if the transaction matches the match fields, False otherwise
        """
        # check start date
        if match_fields["start_date"]:
            start_date_obj = datetime.strptime(match_fields["start_date"], "%m/%d/%Y").date()
            if transaction.date < start_date_obj:
                return False
        # check end date
        if match_fields["end_date"]:
            end_date_obj = datetime.strptime(match_fields["end_date"], "%m/%d/%Y").date()
            if transaction.date > end_date_obj:
                return False
        # check memo
        if match_fields["memo"]:
            if match_fields["memo_exact"]:
                if match_fields["memo"].casefold() != transaction.memo.casefold():
                    return False
            else:
                if match_fields["memo"].casefold() not in transaction.memo.casefold():
                    return False
        # check payee
        if match_fields["payee"]:
            if match_fields["payee_exact"]:
                if match_fields["payee"].casefold() != transaction.payee.casefold():
                    return False
            else:
                if match_fields["payee"].casefold() not in transaction.payee.casefold():
                    return False
        # check amount
        if match_fields["amount_min"]:
            if transaction.amount < Decimal(match_fields["amount_min"]):
                return False
        if match_fields["amount_max"]:
            if transaction.amount > Decimal(match_fields["amount_max"]):
                return False
        # check type
        if match_fields["type"]:
            if match_fields["type"] != transaction.tx_type:
                return False
        return True

    def get_labels(self) -> dict[str, LabelType]:
        """
        Returns the labels dictionary.

        Returns:
            dict[str, LabelType]: The labels dictionary.
        """
        return self.labels
