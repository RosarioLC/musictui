from textual.app import ComposeResult
from textual.widgets import Button, Static

from ui.widgets.volume_control import VolumeControl

# Button labels for utility controls.
_BTN_LYRICS: str = "♫"
_BTN_FULLSCREEN: str = "⛶"


class PlayerUtilities(Static):
    """Lyrics, volume, and fullscreen controls for the now-playing bar."""

    def __init__(self) -> None:
        """Initialize the player utilities."""
        super().__init__(id="player-utilities")

    def compose(self) -> ComposeResult:
        """Compose the utility buttons and volume control."""
        yield Button(_BTN_LYRICS, id="lyrics")
        yield VolumeControl()
        yield Button(_BTN_FULLSCREEN, id="fullscreen")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route button presses to the app actions."""
        if self.app is None:
            return
        if event.button.id == "lyrics":
            await self.app.run_action("show_lyrics")
        elif event.button.id == "fullscreen":
            await self.app.run_action("toggle_fullscreen")
