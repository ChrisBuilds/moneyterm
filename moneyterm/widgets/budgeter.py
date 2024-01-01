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

from datetime import datetime
from dateutil.relativedelta import relativedelta  # type: ignore


class BudgetBuilder(Widget):
    selected_category: reactive[str | NoSelection] = reactive(NoSelection)
    selected_budget_option: reactive[Option | None] = reactive(None)

    class BudgetAdded(Message):
        """Message sent when a budget is added/modified."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, ledger: Ledger, budgets: dict[str, dict[str, str]]) -> None:
        super().__init__()
        self.border_title = "Budget Builder"
        self.ledger = ledger
        self.budgets = budgets
        self.category_select_label = Label("Category", id="category_select_label")
        self.category_select: Select[str] = Select([("a", "a")], id="category_select", prompt="Select a category")
        self.monthly_budget_label = Label("Monthly Budget", id="monthly_budget_label")
        self.monthly_budget_input = self.amount_input = Input(
            placeholder="Ex: 150.00",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_decimal,
                    "Amount must be number/decimal. Ex: 3, 3.01",
                )
            ],
            id="monthly_budget_input",
        )
        self.budgets_option_list = OptionList(id="budgets_option_list")
        self.add_to_budget_button = Button("Add to Budget", id="add_to_budget_button")
        self.delete_budget_button = Button("Delete Budget", id="delete_budget_button")

    def compose(self) -> ComposeResult:
        with Horizontal(id="category_hz"):
            yield self.category_select_label
            yield self.category_select
        yield self.budgets_option_list
        with Horizontal(id="budget_input_hz"):
            yield self.monthly_budget_label
            yield self.monthly_budget_input
        with Horizontal(id="add_to_budget_button_hz"):
            yield self.add_to_budget_button
        yield self.delete_budget_button

    def validate_amount_is_decimal(self, amount: str) -> bool:
        try:
            Decimal(amount)
            return True
        except:
            return False

    @on(Select.Changed, "#category_select")
    def on_category_select_change(self, event: Select.Changed):
        if self.category_select.is_blank():
            self.selected_category = NoSelection()
        else:
            self.selected_category = str(event.value)

    @on(OptionList.OptionSelected, "#budgets_option_list")
    def on_budgets_option_list_select(self, event: OptionList.OptionSelected):
        self.selected_budget_option = event.option
        selected_option_budget = self.budgets[str(self.selected_budget_option.id)]["monthly_budget"]
        self.monthly_budget_input.value = f"{selected_option_budget}"

    @on(Button.Pressed, "#add_to_budget_button")
    def on_add_to_budget_button_press(self, event: Button.Pressed):
        if isinstance(self.selected_category, NoSelection):
            self.notify("A category must be selected to add a budget", severity="error", title="No Category Selected")
            return
        if self.monthly_budget_input.value == "":
            self.notify("A budget amount must be entered", severity="error", title="No Budget Amount Entered")
            return

        self.budgets[self.selected_category] = {"monthly_budget": self.monthly_budget_input.value}
        self.post_message(self.BudgetAdded())

    @on(Button.Pressed, "#delete_budget_button")
    def on_delete_budget_button_press(self, event: Button.Pressed):
        if self.selected_budget_option:
            message = f"Are you sure you want to delete the budget for {self.selected_budget_option.id}?"
            self.app.push_screen(ConfirmScreen(message), self.remove_selected_budget)

    def watch_selected_category(self) -> None:
        self.monthly_budget_input.value = ""

    def watch_selected_budget_option(self) -> None:
        pass

    def update_budget_options(self):
        self.budgets_option_list.clear_options()
        for category in sorted(list(self.budgets)):
            self.budgets_option_list.add_option(
                Option(
                    category,
                    category,
                )
            )

    def update_category_select(self, labels: dict[str, LabelType]):
        if "Categories" in labels:
            options = [(category, category) for category in labels["Categories"]]
            options.sort(key=lambda x: x[0])
            self.category_select.set_options(options)

    def remove_selected_budget(self, confirm: bool):
        if confirm and self.selected_budget_option:
            del self.budgets[str(self.selected_budget_option.id)]
            self.post_message(self.BudgetAdded())


class Budgeter(Widget):
    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.budgets: dict[str, dict[str, str]] = dict()
        self.labels: dict[str, LabelType] = dict()
        self.builder = BudgetBuilder(ledger, self.budgets)
        self.budgets_table_static = Static(id="budgets_table_static")

    def compose(self) -> ComposeResult:
        with Vertical(id="budgeter_vertical"):
            yield self.builder
        with VerticalScroll(id="budget_tables_vertical_scroll"):
            yield self.budgets_table_static

    def on_mount(self):
        # check for, and load, json data for budgets
        try:
            with open(Path("moneyterm/data/budgets.json"), "r") as f:
                self.budgets = json.load(f)
        except FileNotFoundError as e:
            self.budgets = {}
        except json.decoder.JSONDecodeError as e:
            self.notify(
                f"Invalid budgets file. Exception: {e.msg}",
                severity="warning",
                timeout=7,
            )
            self.budgets = {}

        self.builder.budgets = self.budgets
        self.builder.update_budget_options()
        self.update_budgets_table()

        # load labels from labels json
        try:
            with open(Path("moneyterm/data/labels.json"), "r") as f:
                self.labels = json.load(f)
                self.builder.update_category_select(self.labels)
        except FileNotFoundError:
            pass

    def on_budget_builder_budget_added(self, message: BudgetBuilder.BudgetAdded):
        self.budgets = self.builder.budgets
        self.write_budgets_json()
        self.builder.update_budget_options()
        self.update_budgets_table()

    def write_budgets_json(self):
        with open(Path("moneyterm/data/budgets.json"), "w") as f:
            json.dump(self.budgets, f, indent=4)

    def update_budgets_table(self) -> None:
        def get_budget_stats_for_month(month: int, year: int, budget_category: str) -> tuple[Decimal, Decimal]:
            # get transactions with the category
            transactions = self.ledger.get_all_tx_with_label(budget_category)
            # get transactions for the current month
            current_month_transactions = [tx for tx in transactions if tx.date.month == month and tx.date.year == year]
            # total transactions amount (abs value)
            total_transactions_amount = sum([abs(tx.amount) for tx in current_month_transactions], Decimal(0))
            # remaining budget
            remaining_budget = decimal_budget_amount - total_transactions_amount
            return (total_transactions_amount, remaining_budget)

        budgets_table = Table(title=f"Budgets {datetime.strftime(datetime.now(), '%B %Y')}", box=box.SIMPLE)
        budgets_table.add_column("Category")
        budgets_table.add_column("Monthly Budget")
        budgets_table.add_column("Spent")
        budgets_table.add_column("Remaining")
        budgets_table.add_column("Last Month Remaining")

        if not self.budgets:
            self.budgets_table_static.update("No budgets set.")
            return
        last_month = datetime.now() - relativedelta(months=1)
        for budget_category in sorted(list(self.budgets)):
            for _, budget_amount in self.budgets[budget_category].items():
                decimal_budget_amount = Decimal(budget_amount)
                last_month_spent, last_month_remaining = get_budget_stats_for_month(
                    last_month.month, last_month.year, budget_category
                )
                total_transactions_amount, remaining_budget = get_budget_stats_for_month(
                    datetime.now().month, datetime.now().year, budget_category
                )
                budgets_table.add_row(
                    budget_category,
                    f"${decimal_budget_amount}",
                    f"${total_transactions_amount}",
                    f"${remaining_budget}",
                    f"${last_month_remaining}",
                )
        self.budgets_table_static.update(budgets_table)
