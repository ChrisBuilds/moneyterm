from textual import on, events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
)
from textual.containers import Horizontal, Vertical


class ConfirmScreen(ModalScreen):
    """Confirmation screen. On self.dismiss, returns a bool indicating whether the user confirmed or not.

    Args:
        ModalScreen (ModalScreen): textual.screen.ModalScreen

    """

    CSS_PATH = "../tcss/confirmscreen.tcss"

    def __init__(self, message: str) -> None:
        """Initialize the screen.

        Args:
            message (str): Message to display

        """
        super().__init__()
        self.message = message
        self.buttons_horizontal = Horizontal(id="confirm_buttons_horizontal")
        self.screen_vertical = Vertical(id="screen_vertical")
        self.screen_vertical.border_title = "Confirm"

    def compose(self) -> ComposeResult:
        with self.screen_vertical:
            yield Label(
                self.message,
                id="confirm_label",
            )
            with self.buttons_horizontal:
                yield Button("Yes", id="confirm_yes_button")
                yield Button("No", id="confirm_no_button")

    def on_key(self, key: events.Key) -> None:
        """Handle key presses."""
        if key.key == "escape":
            self.dismiss(False)

    @on(Button.Pressed, "#confirm_yes_button")
    def confirm_yes_button(self) -> None:
        """Return True when user confirms."""
        self.dismiss(True)

    @on(Button.Pressed, "#confirm_no_button")
    def confirm_no_button(self) -> None:
        """Return False when user cancels."""
        self.dismiss(False)
