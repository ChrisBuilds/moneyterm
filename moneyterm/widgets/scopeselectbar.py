from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.types import NoSelection
from textual.widgets.select import InvalidSelectValueError
from textual.widgets import (
    Label,
    Select,
)
from textual.containers import Horizontal
from moneyterm.utils.ledger import Ledger


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
        self.accounts: list[str] = []

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
            account_options = []
            for account in accounts.values():
                if account.alias:
                    account_options.append((account.alias, account.number))
                else:
                    account_options.append((account.number, account.number))
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

    def show_latest(self, default_account: str) -> None:
        """
        Selects the latest account, year, and month.
        """
        # TODO: fix this multiple refresh nonsense
        if not self.ledger.accounts:
            return
        if default_account and default_account in self.ledger.accounts:
            self.account_select.value = default_account
        else:
            self.account_select.value = list(self.ledger.accounts)[0]
        year, month = self.ledger.get_most_recent_year_month(self.account_select.value)
        self.refresh_year_month_selects()
        self.year_select.value = year
        self.refresh_year_month_selects()
        self.month_select.value = month
        self.post_message(self.ScopeChanged(self.account_select.value, self.year_select.value, self.month_select.value))

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
