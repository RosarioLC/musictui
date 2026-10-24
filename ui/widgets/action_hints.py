from textual.widgets import Static

# Default action hint template.
_DEFAULT_HINTS: str = ""


class ActionHints(Static):
    """Compact scene-aware keyboard hint row."""

    def __init__(self, actions: str = _DEFAULT_HINTS) -> None:
        """Initialize the action hints widget.

        Args:
            actions: Hint text to display (e.g. ``"q:Quit  h:Home"``).
        """
        super().__init__(actions, id="action-hints")
