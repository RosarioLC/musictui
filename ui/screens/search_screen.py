"""Search screen for querying the music catalog."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input

from catalog.catalog_source import CatalogSource
from model.track import Track
from services.library_service import LibraryService
from services.playback_service import PlaybackService
from ui.mixins import Likeable, PlaylistActionable
from ui.widgets.next_track_card import NextTrackCard
from ui.widgets.now_playing_bar import NowPlayingBar
from ui.widgets.search_bar import SearchBar
from ui.widgets.search_input import SearchInput
from ui.widgets.track_list import TrackList


class SearchScreen(Screen, Likeable, PlaylistActionable):
    """Search screen for querying the music catalog and displaying results.

    Accepts text input from the user, sends it to the catalog source,
    and displays matching tracks in a :class:`~ui.widgets.track_list.TrackList`.
    Supports keyboard shortcuts for adding the currently playing track to
    a playlist.

    Keyboard bindings:
        ``a``: Add the currently playing track to a playlist.
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("a", "add_to_playlist", "Add to Playlist"),
    ]

    def __init__(
        self,
        catalog: CatalogSource,
        player: PlaybackService,
        playlists: LibraryService,
        initial_query: str = "",
        initial_tracks: list[Track] | None = None,
        on_results: Callable[[str, list[Track]], None] | None = None,
    ) -> None:
        """Initialize the search screen.

        Args:
            catalog: The catalog source used to perform searches.
            player: The playback service for controlling audio playback.
            playlists: The library service for playlist management.
            initial_query: Pre-filled search query text.
            initial_tracks: Pre-computed tracks to display before the user
                enters a query.
            on_results: Optional callback invoked with ``(query, tracks)``
                after each search completes.
        """
        super().__init__()
        self._catalog = catalog
        self._player = player
        self._playlists = playlists
        self._query: str = initial_query
        self._tracks: list[Track] = list(initial_tracks or [])
        self._on_results_callback: Callable[[str, list[Track]], None] | None = on_results
        self._search_box: SearchInput | None = None
        Likeable.library_service = playlists
        PlaylistActionable.library_service = playlists
        PlaylistActionable.playback_service = player

    def compose(self) -> ComposeResult:
        """Compose the search screen layout."""
        yield SearchBar()
        yield TrackList(
            widget_id="search-results",
            like_callback=self._on_toggle_like,
            track_selected_callback=self._on_track_selected_callback,
            like_status_callback=self._playlists.is_liked if self._playlists else None,
        )
        yield NextTrackCard()
        yield Footer()
        yield NowPlayingBar()

    def _on_track_selected_callback(self, row: int) -> None:
        """Handle a track selection from the search results.

        Sets the playback continuation to the remaining tracks after the
        selected one, then begins playback.  Also triggers search result
        preloading if the app supports it.

        Args:
            row: The zero-based index of the selected track.
        """
        if row >= len(self._tracks):
            return
        try:
            self._player.set_continuation(self._tracks[row + 1 :])
            self._player.play(self._tracks[row])
            if hasattr(self._player._player._app, "preload_search_results"):
                self._player._player._app.preload_search_results(self._tracks)
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")

    def on_mount(self) -> None:
        """Initialize the search box and display any pre-loaded tracks."""
        self._search_box = self.query_one(SearchInput)
        self._search_box.value = self._query
        if self._tracks:
            self.query_one(TrackList).show_results(self._tracks)
        elif self._query:
            self._search(self._query)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Perform a search when the user submits the input."""
        self._search(event.value.strip())

    def _search(self, query: str) -> None:
        """Execute a search and display the results.

        Args:
            query: The search query string.
        """
        self._query = query
        results_widget = self.query_one(TrackList)
        if not query:
            results_widget.show_error("Type an artist or song title to search")
            return
        results_widget.show_loading()
        try:
            results = self._catalog.search(query)
        except Exception as error:  # noqa: BLE001
            results_widget.show_error(str(error))
            return
        self._on_search_results(results)

    def _on_search_results(self, results: list[Track]) -> None:
        """Display search results and invoke the callback.

        Args:
            results: The list of matching tracks.
        """
        self._tracks = results
        if self._on_results_callback:
            self._on_results_callback(self._query, results)
        self.query_one(TrackList).show_results(results)
