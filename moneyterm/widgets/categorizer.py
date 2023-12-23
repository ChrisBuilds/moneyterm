import json
from pathlib import Path
from typing import TypedDict
from textual import on
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.types import NoSelection
from textual.validation import Function
from textual.widgets.option_list import Option
from textual.widgets import (
    DataTable,
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
from moneyterm.screens.addgroupscreen import AddGroupScreen
from moneyterm.screens.confirmscreen import ConfirmScreen
from moneyterm.widgets.transactiontable import TransactionTable
from datetime import datetime


# create type alias for match field input dict
class MatchFields(TypedDict):
    start_date: str
    end_date: str
    memo: str
    memo_exact: bool
    payee: str
    payee_exact: bool
    amount: float
    type: str
    match_label: str
    color: str
    alias: str


MatchGroup = dict[str, MatchFields]
GroupType = dict[str, MatchGroup]


class Categorizer(Widget):
    selected_type: reactive[str] = reactive("Bills")
    selected_group: reactive[str | NoSelection] = reactive(NoSelection)
    selected_match_option: reactive[Option | None] = reactive(None)

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.groups: dict[str, GroupType]
        # widgets
        self.type_select_label = Label("Type")
        self.type_select = Select(
            [("Bills", "Bills"), ("Categories", "Categories"), ("Incomes", "Incomes")],
            allow_blank=False,
            id="manage_type_select",
        )
        self.group_select_label = Label("Group", id="group_select_label")
        self.group_select: Select[str] = Select([], allow_blank=True, id="group_select")
        self.create_new_group_button = Button("Create New", id="create_new_group_button")
        self.remove_group_button = Button("Remove", id="remove_group_button")
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
        self.matches_option_list = OptionList(*(str(i) for i in range(20)), id="matches_option_list")
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
        self.amount_input = Input(
            placeholder="Ex: 53.49",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_float_up_to_two_decimal_places,
                    "Amount must be number/decimal up to two places. Ex: 3, 3.01",
                )
            ],
            valid_empty=True,
            id="amount_input",
            classes="match_field_input",
        )
        self.type_label = Label("Type", id="type_label")
        self.type_input = Input(placeholder="Type", id="type_input", classes="match_field_input")
        self.remove_match_button = Button("Remove Match", id="remove_match_button")
        self.section_split_rule = Rule(id="section_split_rule")
        self.match_label = Label("Match Label", id="match_label")
        self.match_label_input = Input(placeholder="Match Label", id="match_label_input", valid_empty=False)
        self.color_label = Label("Color", id="color_label")
        self.color_input = Input(placeholder="Color", id="color_input")
        self.alias_label = Label("Alias", id="alias_label")
        self.alias_input = Input(placeholder="Alias", id="alias_input")
        self.save_button = Button("Save", id="save_button")
        self.save_button.disabled = True
        self.preview_button = Button("Show Matches", id="preview_button")
        self.show_all_tx_checkbox = Checkbox("Show All Transactions", id="show_all_tx_checkbox")
        # self.preview_table: DataTable = DataTable(id="preview_table", zebra_stripes=True, cursor_type="row")
        self.preview_table: TransactionTable = TransactionTable(self.ledger)
        self.preview_table.border_title = "Transactions Preview Results"

    def on_mount(self):
        # check for, and load, json data for groups
        try:
            with open(Path("moneyterm/data/identifiers.json"), "r") as f:
                self.groups = json.load(f)
        except FileNotFoundError:
            self.groups = {"Bills": {}, "Categories": {}, "Incomes": {}}
            self.write_groups_json()
        self.update_group_select()

        # self.preview_table.add_columns("Date", "Payee", "Type", "Amount", "Account", "Categories")

    def write_groups_json(self):
        with open(Path("moneyterm/data/identifiers.json"), "w") as f:
            json.dump(self.groups, f, indent=4)

    def compose(self) -> ComposeResult:
        with Horizontal(id="type_select_bar"):
            yield self.type_select_label
            yield self.type_select
        with Grid(id="manage_grid"):
            # row 1
            yield self.group_select_label
            yield self.group_select
            with Horizontal(id="group_create_remove_buttons"):
                yield self.create_new_group_button
                yield self.remove_group_button
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
            yield self.amount_input
            # row 8
            yield self.type_label
            yield self.type_input
            yield self.remove_match_button
            # row 9
            yield self.section_split_rule
            # row 10
            with Horizontal(id="match_label_row"):
                yield self.match_label
                yield self.match_label_input
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
        with Horizontal(id="preview_table_horizontal"):
            yield self.preview_table

    @on(Select.Changed, "#manage_type_select")
    def on_manage_type_select_change(self, event: Select.Changed) -> None:
        self.selected_type = str(event.value)

    @on(Select.Changed, "#group_select")
    def on_group_select_change(self, event: Select.Changed) -> None:
        if self.group_select.is_blank():
            self.selected_group = NoSelection()
        else:
            self.selected_group = str(event.value)

    @on(OptionList.OptionSelected, "#matches_option_list")
    def on_matches_option_list_select(self, event: OptionList.OptionSelected) -> None:
        self.selected_match_option = event.option

    @on(Button.Pressed, "#create_new_group_button")
    def on_create_new_group_button_press(self, event: Button.Pressed) -> None:
        self.app.push_screen(AddGroupScreen(list(self.groups[self.selected_type])), self.create_new_group)

    @on(Button.Pressed, "#remove_group_button")
    def on_remove_group_button_press(self, event: Button.Pressed) -> None:
        if isinstance(self.selected_group, NoSelection):
            return
        match_count = len(self.groups[self.selected_type][self.selected_group])
        message = f"Are you sure you want to remove group '{self.selected_group}' and its {match_count} matches?"
        self.app.push_screen(ConfirmScreen(message), self.remove_selected_group)

    def remove_selected_group(self, confirm: bool) -> None:
        if isinstance(self.selected_group, NoSelection):
            return
        if confirm:
            self.groups[self.selected_type].pop(self.selected_group)
            self.write_groups_json()
            self.update_group_select()

    @on(Button.Pressed, "#save_button")
    def on_save_button_press(self, event: Button.Pressed) -> None:
        if isinstance(self.selected_group, NoSelection):
            return
        if not self.validate_match_fields():
            return
        if self.amount_input.value:
            amount = float(self.amount_input.value)
        else:
            amount = 0.0
        self.groups[self.selected_type][self.selected_group][self.match_label_input.value] = {
            "start_date": self.start_date_input.value,
            "end_date": self.end_date_input.value,
            "memo": self.memo_input.value,
            "memo_exact": self.memo_exact_match_checkbox.value,
            "payee": self.payee_input.value,
            "payee_exact": self.payee_exact_match_checkbox.value,
            "amount": amount,
            "type": self.type_input.value,
            "match_label": self.match_label_input.value,
            "color": self.color_input.value,
            "alias": self.alias_input.value,
        }
        self.write_groups_json()
        self.update_match_options_list(set_selection=self.match_label_input.value)

    @on(Button.Pressed, "#remove_match_button")
    def on_remove_match_button_press(self, event: Button.Pressed) -> None:
        # verify valid group and match option are selected
        if (
            self.selected_match_option is None
            or self.selected_match_option.id is None
            or isinstance(self.selected_group, NoSelection)
        ):
            return
        message = f"Are you sure you want to remove match '{self.selected_match_option.id}'? Transactions with this match will no longer be categorized."
        self.app.push_screen(ConfirmScreen(message), self.remove_selected_match)

    def remove_selected_match(self, confirm: bool) -> None:
        if (
            self.selected_match_option is None
            or self.selected_match_option.id is None
            or isinstance(self.selected_group, NoSelection)
        ):
            return
        if confirm:
            self.groups[self.selected_type][self.selected_group].pop(self.selected_match_option.id)
            self.write_groups_json()
            self.update_match_options_list()

    @on(Button.Pressed, "#preview_button")
    def on_preview_button_press(self, event: Button.Pressed) -> None:
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
                self.preview_table.add_transaction_row(tx, payee_alias=match_fields["alias"])
            else:
                if self.show_all_tx_checkbox.value:
                    self.preview_table.add_transaction_row(tx)

    def on_transaction_table_row_sent(self, message: TransactionTable.RowSent) -> None:
        transaction = self.ledger.get_tx_by_txid(message.tx_id)
        self.start_date_input.value = transaction.date.strftime("%m/%d/%Y")
        self.end_date_input.value = transaction.date.strftime("%m/%d/%Y")
        self.memo_input.value = transaction.memo
        self.memo_exact_match_checkbox.value = False
        self.payee_input.value = transaction.payee
        self.payee_exact_match_checkbox.value = False
        self.amount_input.value = str(transaction.amount)
        self.type_input.value = transaction.tx_type

    def get_match_fields(self) -> MatchFields:
        return {
            "start_date": self.start_date_input.value,
            "end_date": self.end_date_input.value,
            "memo": self.memo_input.value,
            "memo_exact": self.memo_exact_match_checkbox.value,
            "payee": self.payee_input.value,
            "payee_exact": self.payee_exact_match_checkbox.value,
            "amount": float(self.amount_input.value) if self.amount_input.value else 0.0,
            "type": self.type_input.value,
            "match_label": self.match_label_input.value,
            "color": self.color_input.value,
            "alias": self.alias_input.value,
        }

    def validate_date_format(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except:
            return False

    def validate_end_date_after_start_date(self, end_date: str) -> bool:
        if not self.start_date_input.value:
            return True
        try:
            start_date_obj = datetime.strptime(self.start_date_input.value, "%m/%d/%Y")
            end_date_obj = datetime.strptime(end_date, "%m/%d/%Y")
            return start_date_obj <= end_date_obj
        except:
            return False

    def validate_amount_is_float_up_to_two_decimal_places(self, amount: str) -> bool:
        try:
            float(amount)
            if "." in amount:
                return len(amount.split(".")[1]) <= 2
            return True
        except:
            return False

    def validate_match_fields(self) -> bool:
        # require a match label
        validated = True
        if not self.match_label_input.value:
            self.notify("Match label cannot be empty!", title="Error", severity="error", timeout=7)
            validated = False
        # check match field valid states
        for match_field in (
            self.start_date_input,
            self.end_date_input,
            self.amount_input,
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
                not self.amount_input.value,
            ]
        ):
            self.notify(
                "At least one of (Memo, Payee, Amount) must be specified!", title="Error", severity="error", timeout=7
            )
            validated = False
        return validated

    def create_new_group(self, new_group_name: str) -> None:
        if self.selected_type == "Categories":
            self.log("Adding new category to ledger.")
            self.ledger.add_category(new_group_name)
        self.groups[self.selected_type][new_group_name] = {}
        self.write_groups_json()
        self.update_group_select(set_selection=new_group_name)

    def update_group_select(self, set_selection: str | None = None) -> None:
        """Update the group select options based on the selected type.

        Args:
            set_selection (str | None, optional): String option to select after the update. Defaults to None.
        """
        group_options = [(group, group) for group in self.groups[self.selected_type]]
        group_options.sort(key=lambda x: x[0])
        self.group_select.set_options(group_options)
        if set_selection:
            self.group_select.value = set_selection
            self.selected_group = set_selection
        else:
            self.selected_group = NoSelection()

    def update_match_options_list(self, set_selection: str | None = None) -> None:
        """Update the match options list based on the selected group.

        Args:
            set_selection (str | None, optional): String to set as the active option after the update. Defaults to None.
        """
        self.matches_option_list.clear_options()
        self.selected_match_option = None
        if isinstance(self.selected_group, NoSelection):
            return
        for match_label in self.groups[self.selected_type][self.selected_group].keys():
            new_option = Option(match_label, id=match_label)
            self.matches_option_list.add_option(new_option)
        if set_selection and set_selection in self.groups[self.selected_type][self.selected_group]:
            self.matches_option_list.highlighted = self.matches_option_list.get_option_index(set_selection)
            self.matches_option_list.action_select()

    def watch_selected_type(self) -> None:
        """Watch for changes to the selected type and update the group select."""
        self.update_group_select()

    def watch_selected_group(self) -> None:
        """Watch for changes to the selected group and update the match options list."""
        self.update_match_options_list()
        if isinstance(self.selected_group, NoSelection):
            self.remove_group_button.disabled = True
            self.save_button.disabled = True
        else:
            self.remove_group_button.disabled = False
            self.save_button.disabled = False

    def watch_selected_match_option(self) -> None:
        if self.selected_match_option is None or isinstance(self.selected_group, NoSelection):
            self.remove_match_button.disabled = True
            self.start_date_input.clear()
            self.end_date_input.clear()
            self.memo_input.clear()
            self.memo_exact_match_checkbox.value = False
            self.payee_input.clear()
            self.payee_exact_match_checkbox.value = False
            self.amount_input.clear()
            self.type_input.clear()
            self.match_label_input.clear()
            self.color_input.clear()
            self.alias_input.clear()
            self.preview_table.update_data()
            return
        self.remove_match_button.disabled = False
        match = self.groups[self.selected_type][self.selected_group][str(self.selected_match_option.id)]
        self.start_date_input.value = match["start_date"]
        self.end_date_input.value = match["end_date"]
        self.memo_input.value = match["memo"]
        self.memo_exact_match_checkbox.value = match["memo_exact"]
        self.payee_input.value = match["payee"]
        self.payee_exact_match_checkbox.value = match["payee_exact"]
        self.amount_input.value = str(match["amount"])
        self.type_input.value = match["type"]
        self.match_label_input.value = match["match_label"]
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
            start_date_obj = datetime.strptime(match_fields["start_date"], "%m/%d/%Y")
            if transaction.date < start_date_obj:
                return False
        # check end date
        if match_fields["end_date"]:
            end_date_obj = datetime.strptime(match_fields["end_date"], "%m/%d/%Y")
            if transaction.date > end_date_obj:
                return False
        # check memo
        if match_fields["memo"]:
            if match_fields["memo_exact"]:
                if match_fields["memo"] != transaction.memo:
                    return False
            else:
                if match_fields["memo"] not in transaction.memo:
                    return False
        # check payee
        if match_fields["payee"]:
            if match_fields["payee_exact"]:
                if match_fields["payee"] != transaction.payee:
                    return False
            else:
                if match_fields["payee"] not in transaction.payee:
                    return False
        # check amount
        if match_fields["amount"]:
            if match_fields["amount"] != transaction.amount:
                return False
        # check type
        if match_fields["type"]:
            if match_fields["type"] != transaction.tx_type:
                return False
        return True
