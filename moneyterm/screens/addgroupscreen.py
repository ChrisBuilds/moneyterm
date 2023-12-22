from textual import log, on, events
from textual.message import Message
from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    TabbedContent,
    Placeholder,
    TabPane,
    Static,
    Button,
    ListItem,
    ListView,
    Label,
    Select,
    Rule,
    OptionList,
    Input,
    Markdown,
)
from textual.containers import Vertical, Horizontal, VerticalScroll, Middle


class AddGroupScreen(ModalScreen):
    CSS_PATH = "../tcss/addgroupscreen.tcss"

    def __init__(self, existing_groups: list[str]) -> None:
        """Initialize the screen.

        Args:
            existing_groups (list[str]): List of existing groups
        """
        super().__init__()
        self.existing_groups = existing_groups
        self.new_group_input = Input(id="new_group_name_input", placeholder="New Group Name")
        self.container_vertical = Vertical(id="add_group_vertical")
        self.container_vertical.border_title = "Add Group"

    def compose(self) -> ComposeResult:
        with self.container_vertical:
            with Horizontal(id="add_group_horizontal"):
                yield self.new_group_input
            yield Button("Add Group", id="add_group_button")

    def on_key(self, key: events.Key) -> None:
        """Handle key presses."""
        if key.key == "escape":
            self.app.pop_screen()
        elif key.key == "enter":
            self.add_group_button()

    @on(Button.Pressed, "#add_group_button")
    def add_group_button(self) -> None:
        """Add a new group to the list of existing groups."""
        new_group_name = self.new_group_input.value
        if new_group_name in self.existing_groups:
            self.notify("Group already exists!", title="Error", severity="error")
        elif not new_group_name:
            self.notify("Group name cannot be empty!", title="Error", severity="error")
        else:
            self.dismiss(new_group_name)
