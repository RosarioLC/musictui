from textual.app import ComposeResult
from textual.widgets import Static

from ui.widgets.player_controls import PlayerControls
from ui.widgets.progress_row import ProgressRow


class PlaybackCenter(Static):
    """Vertically stacked transport controls and seek bar."""

    def __init__(self) -> None:
        """Initialize the playback center."""
        super().__init__(id="playback-center")

    def compose(self) -> ComposeResult:
        """Compose the playback center layout."""
        yield PlayerControls()
        yield ProgressRow()
