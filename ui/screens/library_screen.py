"""Library screen with playlists and liked songs tables."""

from __future__ import annotations

from functools import partial
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label

from catalog.catalog_source import CatalogSource
from model.track import Track
from services.library_service import LibraryService
from services.playback_service import PlaybackService
from ui.mixins import Likeable, PlaylistActionable
from ui.widgets.modal import (
    NewPlaylistScreen,
    PlaylistPickerScreen,
    RenamePlaylistScreen,
)
from ui.widgets.next_track_card import NextTrackCard
from ui.widgets.now_playing_bar import NowPlayingBar
from ui.widgets.track_list import TrackList
from ui.messages import PlaylistChanged


class LibraryScreen(Screen, Likeable, PlaylistActionable):
    """Library screen with playlists and liked songs tables."""

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("n", "new_playlist", "New Playlist"),
        Binding("d", "delete_playlist", "Delete Playlist"),
        Binding("r", "rename_playlist", "Rename Playlist"),
        Binding("a", "add_selected_to_playlist", "Add to Playlist"),
    ]

    def __init__(
        self,
        player: PlaybackService,
        catalog: CatalogSource,
        playlists: LibraryService,
    ) -> None:
        """Initialize the library screen."""
        super().__init__()
        self._player = player
        self._catalog = catalog
        self._playlists = playlists
        self._current_playlist_id: int | None = None
        self._current_playlist_songs: list[Track] = []
        self._current_row: int = 0
        Likeable.library_service = playlists
        PlaylistActionable.library_service = playlists
        PlaylistActionable.playback_service = player

    def compose(self) -> ComposeResult:
        """Compose the library screen layout."""
        yield Label("Playlists", id="library-title")
        with Horizontal(id="library-content"):
            yield DataTable(id="playlists")
            yield TrackList(
                widget_id="playlist-songs",
                like_callback=self._on_toggle_like,
                track_selected_callback=self._on_track_selected,
                like_status_callback=self._playlists.is_liked,
            )
        yield NextTrackCard()
        yield Footer()
        yield NowPlayingBar()

    def on_mount(self) -> None:
        """Initialize the playlist table and show liked songs."""
        playlists_table = self.query_one("#playlists", DataTable)
        playlists_table.add_columns("Name")
        for playlist in self._playlists.list_playlists():
            playlists_table.add_row(playlist.name, key=str(playlist.id))
        self._show_playlist_songs(LibraryService.LIKED_SONGS_ID)
        self._refresh_playlists()

    def action_new_playlist(self) -> None:
        """Show the new playlist creation dialog."""
        self.call_after_refresh(self._show_new_playlist_dialog)

    def _show_new_playlist_dialog(self) -> None:
        """Push the new playlist dialog screen."""
        self.app.push_screen(
            NewPlaylistScreen(),
            callback=self._on_new_playlist_result,
        )

    def _on_new_playlist_result(self, name: str | None) -> None:
        """Handle the new playlist dialog result."""
        if name:
            try:
                self._playlists.create_playlist(name)
                self._refresh_playlists()
                self.notify(f'Playlist "{name}" created')
            except Exception as exc:  # noqa: BLE001
                self.notify(str(exc), severity="error")

    def action_delete_playlist(self) -> None:
        """Delete the currently selected playlist."""
        table = self.query_one("#playlists", DataTable)
        if table.cursor_row is None:
            return
        playlists = self._playlists.list_playlists()
        if table.cursor_row >= len(playlists):
            return
        playlist = playlists[table.cursor_row]
        if playlist.id == LibraryService.LIKED_SONGS_ID:
            self.notify("Cannot delete Liked Songs", severity="warning")
            return
        self._playlists.delete_playlist(playlist.id)
        self._refresh_playlists()
        self._show_playlist_songs(LibraryService.LIKED_SONGS_ID)

    def action_rename_playlist(self) -> None:
        """Show the rename dialog for the currently selected playlist."""
        table = self.query_one("#playlists", DataTable)
        if table.cursor_row is None:
            return
        playlists = self._playlists.list_playlists()
        if table.cursor_row >= len(playlists):
            return
        playlist = playlists[table.cursor_row]
        if playlist.id == LibraryService.LIKED_SONGS_ID:
            self.notify("Cannot rename Liked Songs", severity="warning")
            return
        self.call_after_refresh(
            lambda: self.app.push_screen(
                RenamePlaylistScreen(playlist.name),
                callback=partial(self._on_rename_result, playlist.id),
            )
        )

    def _on_rename_result(self, playlist_id: int, name: str | None) -> None:
        """Handle the rename dialog result."""
        if name:
            try:
                self._playlists.rename_playlist(playlist_id, name)
                self._refresh_playlists()
                self.notify(f'Playlist renamed to "{name}"')
            except Exception as exc:  # noqa: BLE001
                self.notify(str(exc), severity="error")

    def action_add_selected_to_playlist(self) -> None:
        """Show the playlist picker for the currently playing track."""
        player = self._player
        library = self._playlists
        if player is None or library is None:
            return
        current = player.current_track
        if current is None:
            self.notify("Nothing is playing", severity="warning")
            return
        playlists = library.list_playlists()
        non_liked = [p for p in playlists if p.id != -1]
        if not non_liked:
            self.notify("Create a playlist first", severity="warning")
            return
        self.call_after_refresh(
            lambda: self.app.push_screen(
                PlaylistPickerScreen(non_liked),
                callback=self._on_add_selected_to_playlist_result,
            )
        )

    def _on_add_selected_to_playlist_result(self, playlist_id: int | None) -> None:
        """Handle the add-to-playlist picker result."""
        if playlist_id is None:
            return
        current = self._player.current_track
        if current is None:
            return
        try:
            self._playlists.add_song(playlist_id, current)
            self.notify("Added to playlist")
            self._refresh_playlists()
            # If the current playlist view is the one we just added to, refresh it
            if self._current_playlist_id == playlist_id:
                self._show_playlist_songs(playlist_id)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")

    def _refresh_playlists(self) -> None:
        """Refresh the playlist table display."""
        table = self.query_one("#playlists", DataTable)
        table.clear()
        for playlist in self._playlists.list_playlists():
            table.add_row(playlist.name, key=str(playlist.id))

    def _show_playlist_songs(self, playlist_id: int) -> None:
        """Display the songs of the given playlist."""
        self._current_playlist_id = playlist_id
        tracks_widget = self.query_one("#playlist-songs", TrackList)
        if playlist_id == LibraryService.LIKED_SONGS_ID:
            self._current_playlist_songs = self._playlists.get_liked_songs()
        else:
            playlists = self._playlists.list_playlists()
            playlist = next((p for p in playlists if p.id == playlist_id), None)
            if playlist is None:
                return
            self._current_playlist_songs = list(playlist.songs)
        tracks_widget.show_results(self._current_playlist_songs)

    def _on_track_selected(self, row: int) -> None:
        """Handle a track selection from the playlist songs list."""
        if row >= len(self._current_playlist_songs):
            return
        try:
            self._current_row = row
            queue = self._player._player._queue
            queue._tracks = self._current_playlist_songs[row + 1 :]
            queue._track_ids = {t.id for t in queue._tracks}
            queue._history = []
            queue._current = None
            self._player._player._continuation = []
            self._player.play(self._current_playlist_songs[row])
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")

    def action_next(self) -> None:
        """Go to next track in the current playlist."""
        if self._current_row + 1 < len(self._current_playlist_songs):
            self._current_row += 1
            self._player.play(self._current_playlist_songs[self._current_row])

    def action_previous(self) -> None:
        """Go to previous track in the current playlist."""
        if self._current_row > 0:
            self._current_row -= 1
            queue = self._player._player._queue
            queue._tracks = self._current_playlist_songs[self._current_row + 1 :]
            queue._track_ids = {t.id for t in queue._tracks}
            queue._history = []
            queue._current = None
            self._player._player._continuation = []
            self._player.play(self._current_playlist_songs[self._current_row])

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle playlist selection from the playlist table."""
        if event.data_table.id != "playlists":
            return
        row = event.coordinate.row
        playlists = self._playlists.list_playlists()
        if row >= len(playlists):
            return
        playlist_id = playlists[row].id
        self._show_playlist_songs(playlist_id)

    def on_playlist_changed(self, event: PlaylistChanged) -> None:
        """Refresh the library when any playlist is modified."""
        self._refresh_playlists()
        if self._current_playlist_id is not None:
            self._show_playlist_songs(self._current_playlist_id)
