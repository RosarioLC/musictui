from typing import ClassVar

from textual.binding import Binding
from textual.widgets import Input


class SearchInput(Input):
    """Text input that emits Submitted when user presses Enter.

    Keyboard bindings:
        Escape: Clear the input field.
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "clear", "Clear"),
    ]

    def __init__(self) -> None:
        """Initialize the search input widget."""
        super().__init__(
            placeholder="What do you want to play?",
            id="search-box",
        )

    def action_clear(self) -> None:
        """Clear the input field."""
        self.value = ""
