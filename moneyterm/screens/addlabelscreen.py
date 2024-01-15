from textual import log, on, events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
)
from textual.containers import Vertical, Horizontal


class AddLabelScreen(ModalScreen):
    """
    Represents a screen for adding a new label.

    Attributes:
        CSS_PATH (str): The path to the CSS file for styling the screen.
        existing_labels (list[str]): List of existing labels.
        new_label_input (Input): Input field for entering the new label name.
        container_vertical (Vertical): Vertical container for organizing the screen elements.
    """

    CSS_PATH = "../tcss/addlabelscreen.tcss"

    def __init__(self, existing_labels: list[str]) -> None:
        """Initialize the screen.

        Args:
            existing_labels (list[str]): List of existing labels
        """
        super().__init__()
        self.existing_labels = existing_labels
        self.new_label_input = Input(id="new_label_name_input", placeholder="New Label Name")
        self.container_vertical = Vertical(id="add_label_vertical")
        self.container_vertical.border_title = "Add Label"

    def compose(self) -> ComposeResult:
        """
        Compose the screen by defining the layout and components.

        Yields:
            Composeable: The components to be rendered on the screen.
        """
        with self.container_vertical:
            with Horizontal(id="add_label_horizontal"):
                yield self.new_label_input
            yield Button("Add Label", id="add_label_button")

    def on_key(self, key: events.Key) -> None:
        """Handle key presses."""
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.add_label_button()

    @on(Button.Pressed, "#add_label_button")
    def add_label_button(self) -> None:
        """
        Add a new label to the list of existing labels.

        This function takes the value from the `new_label_input` and checks if it already exists in the `existing_labels` list.
        If the label already exists, an error notification is displayed.
        If the label name is empty, an error notification is displayed.
        Otherwise, the function dismisses the screen and returns the new label name.
        """
        new_label_name = self.new_label_input.value
        if new_label_name in self.existing_labels:
            self.notify(
                "Label already exists! Labels must be unique across all types.", title="Error", severity="error"
            )
        elif not new_label_name:
            self.notify("Label name cannot be empty!", title="Error", severity="error")
        else:
            self.dismiss(new_label_name)
