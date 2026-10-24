"""Screen showing a single playlist's tracks."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label

from model.playlist import Playlist
from services.library_service import LibraryService
from services.playback_service import PlaybackService
from ui.mixins import Likeable, PlaylistActionable
from ui.widgets.next_track_card import NextTrackCard
from ui.widgets.now_playing_bar import NowPlayingBar
from ui.widgets.track_list import TrackList
from ui.messages import PlaylistChanged


class PlaylistScreen(Screen, Likeable, PlaylistActionable):
    """Screen displaying a single playlist's tracks with playback controls.

    Shows the playlist name and a list of all tracks within it.  Supports
    playing individual tracks, navigating between tracks, and removing
    songs from the playlist.

    Keyboard bindings:
        ``d``: Remove the first track from the playlist.
        ``Escape``: Navigate back to the previous screen.
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("d", "remove_song", "Remove Song"),
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(
        self,
        player: PlaybackService,
        playlist: Playlist,
        playlists: LibraryService,
    ) -> None:
        """Initialize the playlist screen.

        Args:
            player: The playback service for controlling audio playback.
            playlist: The playlist to display.
            playlists: The library service for playlist management.
        """
        super().__init__()
        self._player = player
        self._playlist = playlist
        self._playlists = playlists
        self._current_row: int = 0
        Likeable.library_service = playlists
        PlaylistActionable.library_service = playlists
        PlaylistActionable.playback_service = player

    def compose(self) -> ComposeResult:
        """Compose the playlist screen layout."""
        yield Label(f"Playlist: {self._playlist.name}", id="playlist-name")
        yield TrackList(
            widget_id="playlist-tracks",
            like_callback=self._on_toggle_like,
            track_selected_callback=self._on_track_selected,
            like_status_callback=self._playlists.is_liked,
        )
        yield NextTrackCard()
        yield Footer()
        yield NowPlayingBar()

    def on_mount(self) -> None:
        """Set playlist context and display the tracks."""
        self._player.set_playlist_context(True)
        tracks_widget = self.query_one("#playlist-tracks", TrackList)
        tracks_widget.show_results(list(self._playlist.songs))

    def _on_track_selected(self, row: int) -> None:
        """Handle a track selection from the playlist.

        Sets the queue to the remaining tracks after the selected one,
        then begins playback.

        Args:
            row: The zero-based index of the selected track.
        """
        if row >= len(self._playlist.songs):
            return
        try:
            self._current_row = row
            queue = self._player._player._queue
            playlist_tracks = list(self._playlist.songs)
            queue._tracks = playlist_tracks[row + 1 :]
            queue._track_ids = {t.id for t in queue._tracks}
            queue._history = []
            queue._current = None
            self._player._player._continuation = []
            self._player.play(self._playlist.songs[row])
        except Exception as exc:  # noqa: BLE001
            self.notify(f"ERROR: {exc}", severity="error")

    def _on_track_select(self, row: int) -> None:
        """Handle track selection from the TrackList."""
        self._on_track_selected(row)

    def action_next(self) -> None:
        """Go to the next track in the playlist."""
        if self._current_row + 1 < len(self._playlist.songs):
            self._current_row += 1
            self._player.play(self._playlist.songs[self._current_row])

    def action_previous(self) -> None:
        """Go to the previous track in the playlist."""
        if self._current_row > 0:
            self._current_row -= 1
            queue = self._player._player._queue
            queue._tracks = self._playlist.songs[self._current_row + 1 :]
            queue._track_ids = {t.id for t in queue._tracks}
            queue._history = []
            queue._current = None
            self._player._player._continuation = []
            self._player.play(self._playlist.songs[self._current_row])

    def action_remove_song(self) -> None:
        """Remove the first song from the playlist."""
        self.query_one("#playlist-tracks", TrackList)
        songs = self._playlist.songs
        if not songs:
            self.notify("No songs in playlist", severity="warning")
            return
        track = songs[0]
        try:
            if self._playlist.id == LibraryService.LIKED_SONGS_ID:
                self._playlists.remove_from_liked_songs(track)
            else:
                self._playlists.remove_song(self._playlist.id, track)
                self._playlist.remove_song(track)
            self._refresh_table()
            self.notify(f'Removed "{track.title}"')
        except ValueError as exc:
            self.notify(str(exc), severity="error")

    def action_go_back(self) -> None:
        """Navigate back to the previous screen."""
        if self.app and len(self.app.screen_stack) > 1:
            self.app.pop_screen()

    def _refresh_table(self) -> None:
        """Refresh the track list display after modifications."""
        tracks_widget = self.query_one("#playlist-tracks", TrackList)
        tracks_widget.show_results(list(self._playlist.songs))

    def on_playlist_changed(self, event: PlaylistChanged) -> None:
        """Refresh when the current playlist is modified."""
        self._refresh_table()

