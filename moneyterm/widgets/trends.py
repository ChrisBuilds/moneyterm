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
from moneyterm.widgets.labeler import LabelType

from datetime import datetime, timedelta


class TrendAnalysis(Widget):
    def __init__(
        self, ledger: Ledger, subject: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> None:
        super().__init__()
        self.ledger = ledger
        self.subject = subject
        self.start_date = start_date
        self.end_date = end_date
        self.stats_table_static = Static(id="stats_table_static")
        self.stats_by_month_table_static = Static(id="stats_by_month_table_static")
        self.bar_graph_static = Static(id="bar_graph_static")
        self.border_title = f"{self.subject} Analysis"

    def on_mount(self) -> None:
        self.analyse()

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        yield self.stats_table_static
        yield self.bar_graph_static
        with Horizontal(id="button_container"):
            yield Button("Remove", id="remove_analysis_button")
        with HorizontalScroll(id="table_horizontal_scroll"):
            yield self.stats_by_month_table_static

    def iterate_months(self, start_date: datetime, end_date: datetime):
        while start_date <= end_date:
            yield start_date
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                next_month = start_date.replace(month=start_date.month + 1, day=1)
            while next_month.day < start_date.day:
                next_month -= timedelta(days=1)
            start_date = next_month

    def make_chart(self, chart_data: list[float], height: int = 10, bar_width: int = 1) -> Text:
        rows: list[str] = []
        bar_character = "█"
        step_size = max(chart_data) / height
        for row in range(1, height + 2):
            row_string = ""
            for data in chart_data:
                if data <= 0 or data < (height - row) * step_size:
                    row_string += " " * bar_width
                else:
                    row_string += bar_character * bar_width
                row_string += " "
            rows.append(row_string)
        return Text("\n".join(rows), style="bold blue", no_wrap=True)

    def analyse(self) -> None:
        tx_with_label = self.ledger.get_all_tx_with_label(self.subject)
        if self.start_date:
            tx_with_label = [tx for tx in tx_with_label if tx.date >= self.start_date.date()]
        if self.end_date:
            tx_with_label = [tx for tx in tx_with_label if tx.date <= self.end_date.date()]

        if len(tx_with_label) == 0:
            self.notify("No transactions found.", title="No Transactions", severity="error")
            self.remove()
            return
        stats_table = Table(title="Stats Over Period", show_header=False, box=box.MINIMAL)
        stats_table.add_column("", justify="right")
        stats_table.add_column("")
        stats_table.add_row("Total", f"${abs((sum([tx.amount for tx in tx_with_label])))}")
        stats_table.add_row("Median", f"${abs(sorted([tx.amount for tx in tx_with_label])[len(tx_with_label) // 2])}")
        stats_table.add_row("Min", f"${min([abs(tx.amount) for tx in tx_with_label])}")
        stats_table.add_row("Max", f"${max([abs(tx.amount) for tx in tx_with_label])}")
        stats_table.add_row("Count", f"{len(tx_with_label)}")
        self.stats_table_static.update(stats_table)

        # make stats by month table for all months with transactions
        chart_data: list[float] = []
        stats_by_month_table = Table(box=box.MINIMAL)
        months_with_tx = [tx.date.replace(day=1) for tx in tx_with_label]
        start_month = min(months_with_tx)
        end_month = max(months_with_tx)
        row_data = []
        for month in self.iterate_months(start_month, end_month):
            month_tx = [tx for tx in tx_with_label if tx.date.month == month.month and tx.date.year == month.year]
            stats_by_month_table.add_column(month.strftime("%b %Y"))
            if len(month_tx) == 0:
                chart_data.append(0)
                row_data.append("$0")
                continue
            # make row with values for each month resulting in a horizontal table
            month_total = sum([abs(tx.amount) for tx in month_tx])
            chart_data.append(float(month_total))
            row_data.append(f"${month_total}")
        stats_by_month_table.add_row(*row_data)
        self.stats_by_month_table_static.update(stats_by_month_table)
        self.bar_graph_static.update(self.make_chart(chart_data, height=7, bar_width=max(1, 50 // len(row_data))))

    @on(Button.Pressed, "#remove_analysis_button")
    def on_remove_analysis_button_press(self, event: Button.Pressed) -> None:
        """Remove the selected analysis."""
        self.remove()


class TrendSelector(Widget):
    selected_type: reactive[str] = reactive("Bills")
    selected_label: reactive[str | NoSelection] = reactive(NoSelection())

    def __init__(self, ledger: Ledger) -> None:
        super().__init__()
        self.ledger = ledger
        self.labels: dict[str, LabelType] = {}
        self.trend_settings_vertical = Vertical(id="trend_settings_vertical")
        self.trend_settings_vertical.border_title = "Trend Selectors"
        self.selectors_horizontal = Horizontal(id="selectors_horizontal")
        self.dates_horizontal = Horizontal(id="dates_horizontal")
        self.type_selector_label = Label("Type: ")
        self.type_selector: Select[str] = Select(
            [("Bills", "Bills"), ("Categories", "Categories"), ("Incomes", "Incomes")],
            allow_blank=False,
            id="trend_type_select",
        )
        self.selector_label = Label("Label: ", id="trend_selector_label")
        self.label_selector: Select[str] = Select([], id="trend_selector_label_selector", prompt="Select a label")
        self.start_date_label = Label("Start date: ", id="trend_selector_start_date_label")
        self.start_date_input = Input(
            id="trend_selector_start_date_input",
            placeholder="mm/dd/yyyy",
            restrict=r"[0-9\/]*",
            validators=[Function(self.validate_date_format, "Date must be in the format mm/dd/yyyy.")],
            valid_empty=True,
            value=(datetime.now() - timedelta(days=180)).strftime("%m/%d/%Y"),
        )
        self.end_date_label = Label("End date: ", id="trend_selector_end_date_label")
        self.end_date_input = Input(
            id="trend_selector_end_date_input",
            placeholder="mm/dd/yyyy",
            restrict=r"[0-9\/]*",
            validators=[Function(self.validate_date_format, "Date must be in the format mm/dd/yyyy.")],
            valid_empty=True,
            value=datetime.now().strftime("%m/%d/%Y"),
        )
        self.add_analysis_button = Button("Add analysis", id="trend_selector_add_analysis_button")

        self.trend_analysis_vertical = VerticalScroll(id="trend_analysis_vertical")

    def on_mount(self) -> None:
        """Mount the widget."""
        try:
            with open(Path("moneyterm/data/labels.json"), "r") as f:
                self.labels = json.load(f)
        except FileNotFoundError:
            self.labels = {"Bills": {}, "Categories": {}, "Incomes": {}}
        self.update_label_selector()

    def compose(self) -> ComposeResult:
        """Compose the widgets."""
        with self.trend_settings_vertical:
            with self.selectors_horizontal:
                yield self.type_selector_label
                yield self.type_selector
                yield self.selector_label
                yield self.label_selector
            with self.dates_horizontal:
                yield self.start_date_label
                yield self.start_date_input
                yield self.end_date_label
                yield self.end_date_input
                yield self.add_analysis_button
        yield self.trend_analysis_vertical

    def validate_date_format(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except:
            return False

    def update_label_selector(self, set_selection: str | None = None) -> None:
        """Update the label select options based on the selected type.

        Args:
            set_selection (str | None, optional): String option to select after the update. Defaults to None.
        """
        label_options = [(label, label) for label in self.labels[self.selected_type]]
        label_options.sort(key=lambda x: x[0])
        self.label_selector.set_options(label_options)
        if set_selection:
            self.label_selector.value = set_selection
            self.selected_label = set_selection
        else:
            self.selected_label = NoSelection()

    @on(Select.Changed, "#trend_type_select")
    def on_type_selector_change(self, event: Select.Changed) -> None:
        self.selected_type = str(event.value)

    @on(Select.Changed, "#trend_selector_label_selector")
    def on_label_selector_change(self, event: Select.Changed) -> None:
        if self.label_selector.is_blank():
            self.selected_label = NoSelection()
        else:
            self.selected_label = str(event.value)

    def watch_selected_type(self) -> None:
        """Watch for changes to the selected type and update the label select."""
        self.update_label_selector()

    @on(Button.Pressed, "#trend_selector_add_analysis_button")
    def on_add_analysis_button_press(self, event: Button.Pressed) -> None:
        """Add a trend analysis to the vertical scroll."""
        if self.label_selector.is_blank():
            self.notify("No label selected.", title="Label Required", severity="error")
            return
        start_date_valid = self.start_date_input.validate(self.start_date_input.value)
        if start_date_valid and start_date_valid.is_valid is not True:
            self.notify("Start date must be in the format mm/dd/yyyy.", title="Invalid Date", severity="error")
            return
        end_date_valid = self.end_date_input.validate(self.end_date_input.value)
        if end_date_valid and end_date_valid.is_valid is not True:
            self.notify("End date must be in the format mm/dd/yyyy.", title="Invalid Date", severity="error")
            return

        start_date = datetime.strptime(self.start_date_input.value, "%m/%d/%Y") if self.start_date_input.value else None
        end_date = datetime.strptime(self.end_date_input.value, "%m/%d/%Y") if self.end_date_input.value else None
        if (start_date and end_date) and (start_date > end_date):
            self.notify("Start date must be before end date.", title="Invalid Date", severity="error")
            return

        new_analysis = TrendAnalysis(self.ledger, str(self.selected_label), start_date, end_date)
        self.trend_analysis_vertical.mount(new_analysis)
        new_analysis.scroll_visible()
