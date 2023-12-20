import json
from pathlib import Path
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
)
from rich.table import Table
from textual.containers import Horizontal, Grid, VerticalScroll
from moneyterm.utils.ledger import Ledger
from moneyterm.screens.quickcategoryscreen import QuickCategoryScreen
from moneyterm.screens.transactiondetailscreen import TransactionDetailScreen
from moneyterm.screens.addgroupscreen import AddGroupScreen
from datetime import datetime


class TagsSummaryTable(Static):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def generate(self, account: str, year: int, month: int) -> None:
        """Update the datatable when month selection changed."""
        tags_table = Table(show_header=True)
        for label in ["Tag", "Total"]:
            tags_table.add_column(label)
        transactions = self.ledger.get_tx_by_month(account, year, month)
        for tag in self.ledger.get_all_tags():
            transactions = self.ledger.get_tx_by_month(account, year, month)
            total = sum([tx.amount for tx in transactions if tag in tx.tags])
            tags_table.add_row(tag, str(total))
        self.update(tags_table)


class TransactionTable(DataTable):
    account: reactive[str | NoSelection] = reactive(NoSelection)
    year: reactive[int | NoSelection] = reactive(NoSelection)
    month: reactive[int | NoSelection] = reactive(NoSelection)

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.zebra_stripes = True
        self.cursor_type = "row"
        self.id = "transactions_table"
        self.selected_row_key: str | None = None

    def update_data(self) -> None:
        """Update the datatable when month selection changed."""
        self.clear(columns=False)
        if (
            isinstance(self.account, NoSelection)
            or isinstance(self.year, NoSelection)
            or isinstance(self.month, NoSelection)
        ):
            self.selected_row_key = None
            self.add_row("No data", "No data", "No data", "No data", "No data", "No data")
            self.cursor_type = "none"
            return
        for tx in self.ledger.get_tx_by_month(self.account, self.year, self.month):
            self.cursor_type = "row"
            self.add_row(
                tx.date.strftime("%Y-%m-%d"),
                tx.payee,
                tx.tx_type,
                tx.amount,
                tx.account_number,
                ",".join(tx.categories),
                key=tx.txid,
            )

    def on_mount(self) -> None:
        """Mount the datatable."""
        self.add_columns("Date", "Payee", "Type", "Amount", "Account", "Categories")

    def on_key(self, key: events.Key) -> None:
        def update_row_categories(*args):
            if self.selected_row_key is None:
                return
            self.update_cell(
                self.selected_row_key,
                "CATEGORIES",
                ",".join(sorted(self.ledger.get_tx_by_txid(self.selected_row_key).categories)),
            )

        def get_selected_category(category: str):
            if category:
                self.apply_category_to_selected_transaction(category)
                update_row_categories()

        if key.key == "c":
            if self.selected_row_key:
                selected_transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
                self.app.push_screen(QuickCategoryScreen(self.ledger, selected_transaction), get_selected_category)
        elif key.key == "i":
            if self.selected_row_key:
                transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
                self.app.push_screen(TransactionDetailScreen(self.ledger, transaction), update_row_categories)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_row_key = event.row_key.value

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.selected_row_key = event.row_key.value

    def apply_category_to_selected_transaction(self, category: str) -> None:
        """Apply a category to the selected transaction."""
        if self.selected_row_key is None:
            return
        self.log(f"Applying category {category} to transaction {self.ledger.get_tx_by_txid(self.selected_row_key)}")
        selected_transaction = self.ledger.get_tx_by_txid(self.selected_row_key)
        self.ledger.add_category_to_tx(selected_transaction, category)

    def watch_account(self) -> None:
        """Watch for account selection changes."""
        self.update_data()

    def watch_year(self) -> None:
        """Watch for year selection changes."""
        self.update_data()

    def watch_month(self) -> None:
        """Watch for month selection changes."""
        self.update_data()


class ScopeSelectBar(Widget):
    "Selection bar for account, year, and month selection."

    class ScopeChanged(Message):
        """Message sent when account, year, or month selection changed."""

        def __init__(self, account: str | NoSelection, year: int | NoSelection, month: int | NoSelection) -> None:
            super().__init__()
            self.account = account
            self.year = year
            self.month = month

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.account_select: Select[str] = Select([], id="account_select")
        self.year_select: Select[int] = Select([], id="year_select")
        self.month_select: Select[int] = Select([], id="month_select")

    def compose(self) -> ComposeResult:
        with Horizontal(id="scope_select_bar"):
            yield Label("Account")
            yield self.account_select
            yield Label("Year")
            yield self.year_select
            yield Label("Month")
            yield self.month_select

    def on_mount(self) -> None:
        self.refresh_all_selects()

    def refresh_all_selects(self) -> None:
        """Reload all selects."""
        accounts = self.ledger.accounts
        if accounts:
            account_options = sorted([(account, account) for account in accounts.keys()], key=lambda x: x[0])
            self.account_select.set_options(account_options)
            self.refresh_year_month_selects()
        else:
            self.account_select.set_options([])

    def refresh_year_month_selects(self) -> None:
        """
        Refreshes the year and month selection options based on the selected account.
        If no account is selected, clears the options for year and month.
        If there is activity for the selected account, populates the year and month options based on the activity dates.
        Tries to preserve the previously selected year and month if possible.
        """
        selected_account = self.account_select.value
        if isinstance(selected_account, NoSelection):
            self.year_select.set_options([])
            self.month_select.set_options([])
            return
        else:
            self.selected_year = self.year_select.value
            self.selected_month = self.month_select.value
            activity_dates = self.ledger.find_dates_with_tx_activity(account_number=selected_account)
            if activity_dates:
                year_options = sorted([(str(year), year) for year in activity_dates.keys()], key=lambda x: x[1])
                self.year_select.set_options(year_options)
                # try to preserve previously selected year
                try:
                    self.year_select.value = self.selected_year
                except InvalidSelectValueError:
                    self.year_select.clear()

                if isinstance(self.year_select.value, int):
                    month_options = sorted(
                        [(month_name, month_int) for month_int, month_name in activity_dates[self.year_select.value]],
                        key=lambda x: x[1],
                    )
                    self.month_select.set_options(month_options)
                    # try to preserve previously selected month
                    try:
                        self.month_select.value = self.selected_month
                    except InvalidSelectValueError:
                        self.month_select.clear()
            else:
                self.year_select.set_options([])
                self.month_select.set_options([])

    @on(Select.Changed, "#account_select")
    def on_account_select_change(self, event: Select.Changed) -> None:
        self.refresh_year_month_selects()
        self.post_message(self.ScopeChanged(self.account_select.value, self.year_select.value, self.month_select.value))

    @on(Select.Changed, "#year_select")
    def on_year_select_change(self, event: Select.Changed) -> None:
        if isinstance(self.year_select.value, NoSelection) or isinstance(self.account_select.value, NoSelection):
            self.month_select.set_options([])
        else:
            activity_dates = self.ledger.find_dates_with_tx_activity(account_number=self.account_select.value)
            month_options = sorted(
                [(month_name, month_int) for month_int, month_name in activity_dates[self.year_select.value]],
                key=lambda x: x[1],
            )
            previous_month = self.month_select.value
            self.month_select.set_options(month_options)
            # try to preserve previously selected month
            try:
                self.month_select.value = previous_month
            except InvalidSelectValueError:
                self.month_select.clear()
        self.post_message(self.ScopeChanged(self.account_select.value, self.year_select.value, self.month_select.value))

    @on(Select.Changed, "#month_select")
    def on_month_select_change(self, event: Select.Changed) -> None:
        self.post_message(self.ScopeChanged(self.account_select.value, self.year_select.value, self.month_select.value))


# create type alias for match field input dict
MatchFields = dict[str, str]
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
            validators=[Function(self.validate_date, "Date must be in the format mm/dd/yyyy.")],
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
                Function(self.validate_date, "Date must be in the format mm/dd/yyyy."),
                Function(self.validate_end_date_after_start_date, "End date must be after start date."),
            ],
            valid_empty=True,
            id="end_date_input",
            classes="match_field_input",
        )
        self.memo_label = Label("Memo", id="memo_label")
        self.memo_input = Input(placeholder="Memo", id="memo_input", classes="match_field_input")
        self.payee_label = Label("Payee", id="payee_label")
        self.payee_input = Input(placeholder="Payee", id="payee_input", classes="match_field_input")
        self.amount_label = Label("Amount", id="amount_label")
        self.amount_input = Input(
            placeholder="Ex: 53.49",
            restrict=r"[0-9\.]*",
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

    def on_mount(self):
        # check for, and load, json data for groups
        try:
            with open(Path("moneyterm/data/groups.json"), "r") as f:
                self.groups = json.load(f)
        except FileNotFoundError:
            self.groups = {"Bills": {}, "Categories": {}, "Incomes": {}}
            self.write_groups_json()
        self.update_group_select()

    def write_groups_json(self):
        with open(Path("moneyterm/data/groups.json"), "w") as f:
            json.dump(self.groups, f, indent=4)

    def compose(self) -> ComposeResult:
        with Horizontal(id="type_select_bar"):
            yield self.type_select_label
            yield self.type_select
        with Grid(id="manage_grid"):
            # row 1
            yield self.group_select_label
            yield self.group_select
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
            yield self.memo_input
            # row 6
            yield self.payee_label
            yield self.payee_input
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
            yield self.match_label
            yield self.match_label_input
            # row 11
            yield self.color_label
            yield self.color_input
            # row 12
            yield self.alias_label
            yield self.alias_input
            # row 13
            yield self.save_button

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
        self.groups[self.selected_type].pop(self.selected_group)
        self.write_groups_json()
        self.update_group_select()

    @on(Button.Pressed, "#save_button")
    def on_save_button_press(self, event: Button.Pressed) -> None:
        if isinstance(self.selected_group, NoSelection):
            return
        if not self.validate_match_fields():
            return
        self.groups[self.selected_type][self.selected_group][self.match_label_input.value] = {
            "start_date": self.start_date_input.value,
            "end_date": self.end_date_input.value,
            "memo": self.memo_input.value,
            "payee": self.payee_input.value,
            "amount": self.amount_input.value,
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
        self.groups[self.selected_type][self.selected_group].pop(self.selected_match_option.id)
        self.write_groups_json()
        self.update_match_options_list()

    def validate_date(self, date_str: str) -> bool:
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

    def create_new_group(self, new_group_name) -> None:
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
        else:
            self.remove_group_button.disabled = False

    def watch_selected_match_option(self) -> None:
        if self.selected_match_option is None or isinstance(self.selected_group, NoSelection):
            self.remove_match_button.disabled = True
            self.start_date_input.clear()
            self.end_date_input.clear()
            self.memo_input.clear()
            self.payee_input.clear()
            self.amount_input.clear()
            self.type_input.clear()
            self.match_label_input.clear()
            self.color_input.clear()
            self.alias_input.clear()
            return
        self.remove_match_button.disabled = False
        match = self.groups[self.selected_type][self.selected_group][str(self.selected_match_option.id)]
        self.start_date_input.value = match["start_date"]
        self.end_date_input.value = match["end_date"]
        self.memo_input.value = match["memo"]
        self.payee_input.value = match["payee"]
        self.amount_input.value = match["amount"]
        self.type_input.value = match["type"]
        self.match_label_input.value = match["match_label"]
        self.color_input.value = match["color"]
        self.alias_input.value = match["alias"]


class TabbedContentScreen(Screen):
    CSS_PATH = "../tcss/tabbedcontentscreen.tcss"

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        self.transactions_table: TransactionTable = TransactionTable(self.ledger)
        self.tag_summary_table: TagsSummaryTable = TagsSummaryTable(self.ledger)

        yield Header()
        yield Footer()
        yield ScopeSelectBar(self.ledger)
        with TabbedContent(initial="transactions_tab", id="tabbed_content"):
            with TabPane("Overview", id="overview_tab"):
                yield Label("Overview")
            with TabPane("Transactions", id="transactions_tab"):
                yield self.transactions_table
            with TabPane("Manage", id="manage_tab"):
                yield Categorizer(self.ledger)

    def on_scope_select_bar_scope_changed(self, message: ScopeSelectBar.ScopeChanged) -> None:
        """Update the tag summary table and transaction table when scope selection changed."""
        self.log(f"Scope changed: {message.account}, {message.year}, {message.month}")
        self.transactions_table.account = message.account
        self.transactions_table.year = message.year
        self.transactions_table.month = message.month
