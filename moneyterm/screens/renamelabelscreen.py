from textual import log, on, events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal


class RenameLabelScreen(ModalScreen):
    """
    A screen for renaming a label.

    Args:
        selected_label (str): The label to be renamed.
        existing_labels (list[str]): List of existing labels.

    Attributes:
        CSS_PATH (str): The path to the CSS file for styling the screen.
        existing_labels (list[str]): List of existing labels.
        instructions_label (Label): The label displaying instructions for renaming the label.
        new_label_input (Input): The input field for entering the new label name.
        container_vertical (Vertical): The vertical container for organizing the screen elements.
    """

    CSS_PATH = "../tcss/renamelabelscreen.tcss"

    def __init__(self, selected_label, existing_labels: list[str]) -> None:
        """Initialize the screen.

        Args:
            existing_labels (list[str]): List of existing labels
        """
        super().__init__()
        self.existing_labels = existing_labels
        self.instructions_label = Label(f"Enter new name for '{selected_label}'")
        self.new_label_input = Input(id="new_label_name_input", placeholder="New Label Name")
        self.container_vertical = Vertical(id="rename_label_vertical")
        self.container_vertical.border_title = "Rename Label"

    def compose(self) -> ComposeResult:
        with self.container_vertical:
            yield self.instructions_label
            with Horizontal(id="rename_label_horizontal"):
                yield self.new_label_input
            yield Button("Rename Label", id="rename_label_button")

    def on_key(self, key: events.Key) -> None:
        """Handle key presses."""
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.rename_label_button()

    @on(Button.Pressed, "#rename_label_button")
    def rename_label_button(self) -> None:
        """
        Add a new label to the list of existing labels.

        This function checks if the new label name already exists in the list of existing labels.
        If it does, an error notification is displayed.
        If the new label name is empty, an error notification is displayed.
        Otherwise, the function dismisses the screen with the new label name.
        """
        new_label_name = self.new_label_input.value
        if new_label_name in self.existing_labels:
            self.notify("Label already exists!", title="Error", severity="error")
        elif not new_label_name:
            self.notify("Label name cannot be empty!", title="Error", severity="error")
        else:
            self.dismiss(new_label_name)
