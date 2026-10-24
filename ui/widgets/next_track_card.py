from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.widgets import Label, Static

from ui.messages import PlaybackStarted
from ui.widgets.album_art import AlbumArt

_REFRESH_INTERVAL: float = 0.5


class NextTrackDetails(Static):
    """Container for next-track album art and metadata."""

    def __init__(self) -> None:
        super().__init__(id="next-track-details")

    def compose(self) -> ComposeResult:
        yield AlbumArt(art_cols=16, id="next-art")
        yield NextTrackText()


class NextTrackText(Static):
    """Vertical container for NEXT label and metadata."""

    def __init__(self) -> None:
        super().__init__(id="next-text")

    def compose(self) -> ComposeResult:
        yield Label("NEXT", id="next-label")
        yield Static("", id="next-metadata")


class NextTrackCard(Static):
    """Compact next-track preview for the Home screen."""

    def __init__(self) -> None:
        super().__init__(id="next-track")

    def compose(self) -> ComposeResult:
        yield NextTrackDetails()

    def on_mount(self) -> None:
        self.set_interval(_REFRESH_INTERVAL, self._refresh)

    def on_playback_started(self, event: PlaybackStarted) -> None:
        self._refresh()

    def _refresh(self) -> None:
        if not hasattr(self.app, "_playback_service"):
            return
        player = self.app._playback_service
        if player is None:
            return
        try:
            metadata = self.query_one("#next-metadata", Static)
            art = self.query_one("#next-art", AlbumArt)
        except NoMatches:
            return
        track = player.upcoming_track
        if track is None:
            self.display = False
            return
        self.display = True
        metadata.update(f"{track.title}\n{track.artist}")
        art.set_source(track.image_path)
