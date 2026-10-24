from textual.app import ComposeResult
from textual.widgets import Static

from model.track import Track
from ui.widgets.album_art import AlbumArt


class TrackMetadata(Static):
    """Container for track title and artist labels."""

    def __init__(self) -> None:
        """Initialize the metadata container."""
        super().__init__(id="track-metadata")

    def compose(self) -> ComposeResult:
        """Compose the title and artist labels."""
        yield Static("", id="track-title")
        yield Static("", id="track-artist")


class TrackInfo(Static):
    """Track info widget showing album art, title, and artist.

    Displays the current track's album art (optional), title, and artist
    name.  Album art is rendered as ANSI half-block colour text via the
    :class:`~ui.widgets.album_art.AlbumArt` widget.
    """

    def __init__(self, show_art: bool = True) -> None:
        """Initialize the track info widget.

        Args:
            show_art: Whether to display album art alongside the metadata.
        """
        super().__init__(id="track-info")
        self._show_art: bool = show_art
        self._album_art: AlbumArt | None = None
        self._title: Static | None = None
        self._artist: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the album art and metadata widgets."""
        if self._show_art:
            yield AlbumArt(art_cols=20, id="album-art")
        yield TrackMetadata()

    def on_mount(self) -> None:
        """Cache references to child widgets for fast access."""
        if self._show_art:
            try:
                self._album_art = self.query_one("#album-art", AlbumArt)
            except Exception:  # noqa: BLE001
                self._album_art = None
        else:
            self._album_art = None
        try:
            self._title = self.query_one("#track-title", Static)
            self._artist = self.query_one("#track-artist", Static)
        except Exception:  # noqa: BLE001
            self._title = None
            self._artist = None

    def update_track(self, track: Track | None) -> None:
        """Update the displayed track info.

        Args:
            track: The track to display, or ``None`` to clear.
        """
        if track is None:
            if self._title is not None:
                self._title.update("")
            if self._artist is not None:
                self._artist.update("")
            return
        if self._title is not None:
            self._title.update(track.title)
        if self._artist is not None:
            self._artist.update(track.artist)
        if self._album_art is not None:
            self._album_art.set_source(track.image_path)
