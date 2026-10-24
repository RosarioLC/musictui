from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Button, Static

from ui.widgets.slider import Slider

# Default volume level.
_DEFAULT_VOLUME: int = 75


class VolumeControl(Static):
    """Volume slider with a mute/unmute toggle button."""

    volume: reactive[int] = reactive(_DEFAULT_VOLUME)

    def __init__(self) -> None:
        """Initialize the volume control widget."""
        super().__init__(id="volume-control")
        self._volume_before_mute: int = _DEFAULT_VOLUME
        self._player_ref: object | None = None

    def compose(self) -> ComposeResult:
        """Compose the mute button and volume slider."""
        yield Button("🔊", id="mute")
        yield Slider(id="volume", value=_DEFAULT_VOLUME, maximum=100)

    def on_mount(self) -> None:
        """Cache the player reference once."""
        if self.app and hasattr(self.app, "_player"):
            self._player_ref = self.app._player

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Toggle mute/unmute."""
        if event.button.id != "mute":
            return
        if self.volume > 0:
            self._volume_before_mute = self.volume
            self.volume = 0
        else:
            self.volume = self._volume_before_mute
        player = self._player_ref
        if player is not None:
            player.set_volume(self.volume)

    def on_slider_updated(self, event: Slider.Updated) -> None:
        """Update volume when the slider is changed."""
        self.volume = int(event.value)
        player = self._player_ref
        if player is not None:
            player.set_volume(int(event.value))

    def watch_volume(self, volume: int) -> None:
        """React to volume changes: sync slider and mute button icon."""
        if self.is_mounted:
            self.query_one(Slider).value = volume
            mute_btn = self.query_one("#mute", Button)
            mute_btn.label = "🔇" if volume == 0 else "🔊"
