from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label

from model.track import Track
from ui.widgets.album_art import AlbumArt
from ui.widgets.now_playing_bar import NowPlayingBar


class FullscreenScreen(Screen):
    """Overlay screen displaying a large album-art rendering."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "close", "Close")]

    def __init__(self, track: Track, art_cols: int | None = None) -> None:
        """Initialize the fullscreen screen.

        Args:
            track: The track whose art to display.
            art_cols: Optional fixed column count for the art rendering.
        """
        super().__init__(id="fullscreen-screen")
        self._track = track
        self._art_cols = art_cols

    def compose(self) -> ComposeResult:
        """Compose the fullscreen layout."""
        art = AlbumArt(art_cols=70, id="fullscreen-art")
        art.styles.width = "100%"
        art.styles.height = "100%"
        yield art
        yield Label(
            f"{self._track.title}  /  {self._track.artist}",
            id="fullscreen-caption",
        )
        yield Footer()
        yield NowPlayingBar(show_art=False)

    def on_mount(self) -> None:
        """Set the album art source when the screen is mounted."""
        self.query_one(AlbumArt).set_source(self._track.image_path)

    def action_close(self) -> None:
        """Dismiss the fullscreen overlay."""
        self.app.pop_screen()
