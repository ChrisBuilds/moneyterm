from decimal import Decimal
import json
from textual import on
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.message import Message
from textual.widget import Widget
from textual.types import NoSelection
from textual.validation import Function

from textual.widgets import (
    Label,
    Select,
    Static,
    Button,
    Input,
)
from rich.table import Table
from rich.text import Text
from rich import box
from textual.containers import Horizontal, VerticalScroll, Vertical
from moneyterm.utils.ledger import Ledger
from moneyterm.utils import config
from moneyterm.widgets.labeler import LabelType

from datetime import datetime
from dateutil.relativedelta import relativedelta  # type: ignore


class BudgetBuilder(Widget):
    """
    A class representing a budget builder widget.

    Attributes:
        selected_expense (reactive[str | NoSelection]): The selected expense.
        ledger (Ledger): The ledger object.
        budgets (dict[str, dict[str, str]]): The budgets dictionary.

    Methods:
        __init__(self, ledger: Ledger, budgets: dict[str, dict[str, str]]) -> None:
            Initializes the BudgetBuilder object.
        compose(self) -> ComposeResult:
            Composes the widget.
        validate_amount_is_decimal_or_blank(self, amount: str) -> bool:
            Validates if the amount is a decimal or blank.
        on_expense_select_change(self, event: Select.Changed):
            Event handler for expense select change.
        on_monthly_budget_input_change(self, event: Input.Changed):
            Event handler for monthly budget input change.
        on_save_budgets_button_press(self, event: Button.Pressed):
            Event handler for save budgets button press.
        watch_selected_expense(self) -> None:
            Watches the selected expense.
        update_expense_select(self, labels: dict[str, LabelType]):
            Updates the expense select options.
    """

    selected_expense: reactive[str | NoSelection] = reactive(NoSelection)

    class BudgetAdded(Message):
        """Message sent when a budget is added/modified."""

        def __init__(self) -> None:
            super().__init__()

    def __init__(self, ledger: Ledger, budgets: dict[str, dict[str, str]]) -> None:
        """
        Initializes the BudgetBuilder object.

        Args:
            ledger (Ledger): The ledger object.
            budgets (dict[str, dict[str, str]]): The budgets dictionary.
        """
        super().__init__()
        self.border_title = "Budget Builder"
        self.ledger = ledger
        self.budgets = budgets
        self.expense_select_label = Label("Expense", id="expense_select_label")
        self.expense_select: Select[str] = Select([("a", "a")], id="expense_select", prompt="Select a expense")
        self.monthly_budget_input = self.amount_input = Input(
            placeholder="Ex: 150.00",
            restrict=r"[0-9\.\-]*",
            validators=[
                Function(
                    self.validate_amount_is_decimal_or_blank,
                    "Amount must be number/decimal. Ex: 3, 3.01",
                )
            ],
            id="monthly_budget_input",
        )
        self.save_budgets_button = Button("Save Budgets", id="save_budgets_button")

    def compose(self) -> ComposeResult:
        """
        Composes the widget.

        Yields:
            Composeable: The composed widget elements.
        """
        with Horizontal(id="builder_hz"):
            yield self.expense_select_label
            yield self.expense_select
            yield self.monthly_budget_input
            yield self.save_budgets_button

    def validate_amount_is_decimal_or_blank(self, amount: str) -> bool:
        """
        Validates if the given amount is a decimal number or blank.

        This method checks if the provided amount is a valid decimal number or if it is blank.
        A valid decimal number is a number greater than zero with optional decimal places.

        Args:
            amount (str): The amount to be validated.

        Returns:
            bool: True if the amount is a decimal number or blank, False otherwise.
        """
        if not amount:
            return True
        try:
            decimal_amount = Decimal(amount)
            assert decimal_amount >= 0
            return True
        except:
            return False

    @on(Select.Changed, "#expense_select")
    def on_expense_select_change(self, event: Select.Changed) -> None:
        """
        Event handler for expense select change.

        Args:
            event (Select.Changed): The event object.
        """
        if event.value == Select.BLANK:
            self.selected_expense = NoSelection()
        else:
            self.selected_expense = str(event.value)

    @on(Input.Changed, "#monthly_budget_input")
    def on_monthly_budget_input_change(self, event: Input.Changed) -> None:
        """
        Event handler for monthly budget input change.

        This method is called when the value of the monthly budget input field changes.
        It checks if the input value is valid based on the event's validation result.
        If the input is not valid, it disables the save_budgets_button.
        Otherwise, it enables the save_budgets_button.

        Args:
            event (Input.Changed): The event object.
        """
        if event.validation_result and not event.validation_result.is_valid:
            self.save_budgets_button.disabled = True
        else:
            self.save_budgets_button.disabled = False

    @on(Button.Pressed, "#save_budgets_button")
    def on_save_budgets_button_press(self, event: Button.Pressed) -> None:
        """
        Event handler for save budgets button press.

        This method is responsible for handling the event when the save budgets button is pressed.
        It checks if an expense is selected, and if not, it displays an error message.
        If an expense is selected, it updates the budgets dictionary with the monthly budget value.
        Finally, it posts a message to indicate that the budget has been added.

        Args:
            event (Button.Pressed): The event object.
        """
        if isinstance(self.selected_expense, NoSelection):
            self.notify("A expense must be selected to add a budget", severity="error", title="No Expense Selected")
            return

        self.budgets[self.selected_expense] = {"monthly_budget": self.monthly_budget_input.value}
        self.post_message(self.BudgetAdded())

    def watch_selected_expense(self) -> None:
        """
        Watches the selected expense and updates the monthly budget input accordingly.

        If the selected expense is of type NoSelection, the monthly budget input is cleared.
        Otherwise, if the selected expense exists in the budgets dictionary, the monthly budget input is set to the corresponding monthly budget value.

        Returns:
            None
        """
        if isinstance(self.selected_expense, NoSelection):
            self.monthly_budget_input.value = ""
        else:
            if self.selected_expense in self.budgets:
                self.monthly_budget_input.value = self.budgets[self.selected_expense]["monthly_budget"]

    def update_expense_select(self, labels: dict[str, LabelType]) -> None:
        """
        Updates the expense select options.

        This method takes a dictionary of labels as input and updates the options available in the expense select widget.
        The labels dictionary should have a key "Expenses" which contains a list of expenses.

        Args:
            labels (dict[str, LabelType]): The labels dictionary.

        Returns:
            None
        """
        if "Expenses" in labels:
            options = [(expense, expense) for expense in labels["Expenses"]]
            options.sort(key=lambda x: x[0].lower())
            self.expense_select.set_options(options)


class Budgeter(Widget):
    """
    A class representing a budgeter widget.

    Attributes:
    - ledger (Ledger): The ledger object used for managing financial transactions.
    - budgets (dict[str, dict[str, str]]): A dictionary containing budget information.
    - labels (dict[str, LabelType]): A dictionary containing label information.
    - builder (BudgetBuilder): The budget builder object used for creating and modifying budgets.
    - budgets_table_static (Static): The static widget used for displaying the budgets table.

    Methods:
    - compose(): Composes the widget by yielding the child components.
    - on_mount(): Called when the widget is mounted. Loads budgets and labels from JSON files and updates the UI.
    - load_labels_from_json(): Loads labels from the labels JSON file.
    - on_budget_builder_budget_added(message: BudgetBuilder.BudgetAdded): Handles the event when a budget is added in the budget builder.
    - write_budgets_json(): Writes the budgets dictionary to the budgets JSON file.
    - update_budgets_table(): Updates the budgets table with the latest budget information.
    - get_budget_stats_for_month(month: int, year: int, budget_expense: str) -> tuple[Decimal, Decimal]: Calculates the total transactions amount and remaining budget for a given month and budget expense.
    - handle_expense_renamed(old_expense: str, new_expense: str): Handles the event when an expense is renamed.
    - handle_expense_removed(expense: str): Handles the event when an expense is removed.
    - handle_expense_added(): Handles the event when an expense is added.
    """

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.budgets: dict[str, dict[str, str]] = dict()
        self.labels: dict[str, LabelType] = dict()
        self.builder = BudgetBuilder(ledger, self.budgets)
        self.budgets_table_static = Static(id="budgets_table_static")

    def compose(self) -> ComposeResult:
        """
        Composes the widget by yielding the child components.

        Yields:
        - builder (BudgetBuilder): The budget builder component.
        - budgets_table_static (Static): The static component for displaying the budgets table.
        """
        with Vertical(id="budgeter_vertical"):
            yield self.builder
        with VerticalScroll(id="budget_tables_vertical_scroll"):
            yield self.budgets_table_static

    def on_mount(self):
        """
        Called when the widget is mounted. Loads budgets and labels from JSON files and updates the UI.
        """
        # check for, and load, json data for budgets
        try:
            with config.BUDGETS_JSON.open() as f:
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
        self.update_budgets_table()

        # load labels from labels json
        self.load_labels_from_json()
        self.builder.update_expense_select(self.labels)

    def load_labels_from_json(self) -> None:
        """
        Loads labels from the labels JSON file.

        This method reads the labels JSON file and loads the labels into the `self.labels` attribute.
        If the file is not found, it silently ignores the exception and continues execution.

        Returns:
            None
        """
        try:
            with config.LABELS_JSON.open() as f:
                self.labels = json.load(f)
        except FileNotFoundError:
            pass

    def on_budget_builder_budget_added(self, message: BudgetBuilder.BudgetAdded):
        """
        Handles the event when a budget is added in the budget builder.

        Args:
        - message (BudgetBuilder.BudgetAdded): The event message containing the added budget information.
        """
        self.budgets = self.builder.budgets
        self.write_budgets_json()
        self.update_budgets_table()

    def write_budgets_json(self):
        """
        Writes the budgets dictionary to the budgets JSON file.
        """
        with config.BUDGETS_JSON.open("w") as f:
            json.dump(self.budgets, f, indent=4)

    def update_budgets_table(self) -> None:
        """
        Updates the budgets table with the latest budget information.
        """

        def get_budget_stats_for_month(month: int, year: int, budget_expense: str) -> tuple[Decimal, Decimal]:
            """
            Calculates the total transactions amount and remaining budget for a given month and budget expense.

            Args:
            - month (int): The month for which to calculate the budget stats.
            - year (int): The year for which to calculate the budget stats.
            - budget_expense (str): The budget expense for which to calculate the budget stats.

            Returns:
            - tuple[Decimal, Decimal]: A tuple containing the total transactions amount and remaining budget.
            """
            # get transactions with the expense
            transactions = self.ledger.get_all_tx_with_label(budget_expense)
            # get transactions for the current month
            current_month_transactions = [tx for tx in transactions if tx.date.month == month and tx.date.year == year]
            # total transactions amount (abs value)
            total_transactions_amount = Decimal(0)
            for transaction in current_month_transactions:
                if budget_expense in transaction.splits:
                    total_transactions_amount += transaction.splits[budget_expense]
                else:
                    total_transactions_amount += abs(transaction.amount)
            # remaining budget
            remaining_budget = decimal_budget_amount - total_transactions_amount
            return (total_transactions_amount, remaining_budget)

        budgets_table = Table(title=f"Budgets {datetime.strftime(datetime.now(), '%B %Y')}", box=box.SIMPLE)
        budgets_table.add_column("Expense", justify="center")
        budgets_table.add_column("Monthly Budget", justify="center")
        budgets_table.add_column("Spent", justify="center")
        budgets_table.add_column("Remaining", justify="center")
        budgets_table.add_column("Last Month Spent", justify="center")
        budgets_table.add_column("Last Month Remaining", justify="center")

        if not self.budgets:
            self.budgets_table_static.update("No budgets set.")
            return
        row_added = False
        last_month = datetime.now() - relativedelta(months=1)
        for budget_expense in sorted(list(self.budgets)):
            for _, budget_amount in self.budgets[budget_expense].items():
                if not budget_amount:
                    continue
                decimal_budget_amount = Decimal(budget_amount)
                last_month_spent, last_month_remaining = get_budget_stats_for_month(
                    last_month.month, last_month.year, budget_expense
                )
                total_transactions_amount, remaining_budget = get_budget_stats_for_month(
                    datetime.now().month, datetime.now().year, budget_expense
                )
                remaining_budget_colored = Text(f"${remaining_budget}")
                if remaining_budget > 0:
                    remaining_budget_colored.stylize("bold green")
                else:
                    remaining_budget_colored.stylize("bold red")
                last_month_remaining_colored = Text(f"${last_month_remaining}")
                if last_month_remaining > 0:
                    last_month_remaining_colored.stylize("bold green")
                else:
                    last_month_remaining_colored.stylize("bold red")
                budgets_table.add_row(
                    budget_expense,
                    f"${decimal_budget_amount}",
                    f"${total_transactions_amount}",
                    remaining_budget_colored,
                    f"${last_month_spent}",
                    last_month_remaining_colored,
                )
                row_added = True
        if not row_added:
            self.budgets_table_static.update("No budgets set.")
            return
        self.budgets_table_static.update(budgets_table)

    def handle_expense_renamed(self, old_expense: str, new_expense: str):
        """
        Handles the event when an expense is renamed.

        This method updates the budgets dictionary by replacing the old expense name
        with the new expense name. It then writes the updated budgets to a JSON file,
        updates the budgets table, and reloads the labels from the JSON file. Finally,
        it updates the expense select in the builder.

        Args:
        - old_expense (str): The old expense name.
        - new_expense (str): The new expense name.
        """
        if old_expense in self.budgets:
            self.budgets[new_expense] = self.budgets.pop(old_expense)
            self.write_budgets_json()
            self.update_budgets_table()
        self.load_labels_from_json()
        self.builder.update_expense_select(self.labels)

    def handle_expense_removed(self, expense: str):
        """
        Handles the event when an expense is removed.

        This method removes the specified expense from the budgets dictionary,
        updates the budgets JSON file, and updates the budgets table in the UI.
        Additionally, it reloads the labels from the JSON file and updates the
        expense select widget in the UI.

        Args:
        - expense (str): The expense to be removed.
        """
        if expense in self.budgets:
            del self.budgets[expense]
            self.write_budgets_json()
            self.update_budgets_table()
        self.load_labels_from_json()
        self.builder.update_expense_select(self.labels)

    def handle_expense_added(self):
        """
        Handles the event when an expense is added.

        This method is called when a new expense is added to the budgeter. It performs the following steps:
        1. Loads the labels from a JSON file.
        2. Updates the expense select widget with the new labels.

        This method does not return any value.
        """
        self.load_labels_from_json()
        self.builder.update_expense_select(self.labels)
