"""Home screen showing recommended tracks and the now-playing bar."""

from __future__ import annotations

from functools import partial
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Input, Label
from textual.worker import Worker, WorkerState

from catalog.catalog_source import CatalogSource
from model.track import Track
from services.library_service import LibraryService
from services.playback_service import PlaybackService
from ui.mixins import Likeable, PlaylistActionable
from ui.widgets.next_track_card import NextTrackCard
from ui.widgets.now_playing_bar import NowPlayingBar
from ui.widgets.search_bar import SearchBar
from ui.widgets.track_list import TrackList


class HomeScreen(Screen, Likeable, PlaylistActionable):
    """Home screen displaying recommended tracks and the now-playing bar.

    On mount, this screen loads recommended tracks from the catalog in a
    background worker and displays them in a :class:`~ui.widgets.track_list.TrackList`.
    It supports infinite scrolling (loading more recommendations) and
    provides keyboard shortcuts for adding tracks to playlists.
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("a", "add_to_playlist", "Add to Playlist"),
    ]

    _PAGE_SIZE: int = 12

    def __init__(
        self,
        catalog: CatalogSource,
        player: PlaybackService,
        playlists: LibraryService,
    ) -> None:
        """Initialize the home screen with its services.

        Args:
            catalog: The catalog source used to fetch recommended tracks.
            player: The playback service for controlling audio playback.
            playlists: The library service for playlist management.
        """
        super().__init__()
        self._catalog = catalog
        self._player = player
        self._playlists = playlists
        self._recommended: list[Track] = []
        self._shown_count: int = 0
        self._seen_ids: set[str] = set()
        Likeable.library_service = playlists
        PlaylistActionable.library_service = playlists
        PlaylistActionable.playback_service = player

    def compose(self) -> ComposeResult:
        """Compose the home screen layout.

        Returns:
            A sequence of widgets: search bar, home title, recommended
            tracks list, next-track card, footer, and now-playing bar.
        """
        yield SearchBar()
        yield Label("HOME", id="home-title")
        yield TrackList(
            widget_id="recommended",
            like_callback=self._on_toggle_like,
            track_selected_callback=self._on_track_selected_callback,
            like_status_callback=self._playlists.is_liked if self._playlists else None,
        )
        yield NextTrackCard()
        yield Footer()
        yield NowPlayingBar()

    def _on_track_selected_callback(self, row: int) -> None:
        """Handle a track selection from the recommended tracks list.

        Sets the playback continuation to the remaining tracks after the
        selected one, then begins playback of the selected track.

        Args:
            row: The zero-based index of the selected track in
                :attr:`_recommended`.
        """
        if row >= len(self._recommended):
            return
        try:
            self._player.set_continuation(self._recommended[row + 1 :])
            self._player.play(self._recommended[row])
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")

    def on_mount(self) -> None:
        """Start loading recommended tracks in a background worker."""
        self.run_worker(
            partial(self._catalog.get_recommended_tracks, self._PAGE_SIZE),
            name="home-recommendations",
            group="home",
            thread=True,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle completion of a recommendations worker.

        On success, updates the track list and seen-ID set.  For the
        initial load, the results replace any existing display; for
        subsequent loads, they are appended.

        Args:
            event: The worker state-change event.
        """
        if (
            event.worker.name == "home-recommendations"
            and event.state == WorkerState.SUCCESS
        ):
            tracks: list[Track] = event.worker.result or []
            tracks = [t for t in tracks if t.provider_id not in self._seen_ids]
            if tracks:
                self._seen_ids.update(t.provider_id for t in tracks if t.provider_id)
                self._recommended = tracks
                self.query_one("#recommended", TrackList).show_results(tracks)
                self._shown_count += len(tracks)
        elif (
            event.worker.name == "home-recommendations-next"
            and event.state == WorkerState.SUCCESS
        ):
            tracks: list[Track] = event.worker.result or []
            tracks = [t for t in tracks if t.provider_id not in self._seen_ids]
            if tracks:
                self._seen_ids.update(t.provider_id for t in tracks if t.provider_id)
                self._recommended.extend(tracks)
                self.query_one("#recommended", TrackList).append_results(tracks)
                self._shown_count += len(tracks)

    def _load_more_if_needed(self) -> None:
        """Load additional recommendations if the user scrolls to the bottom."""
        if self._shown_count == 0:
            return
        self.query_one("#recommended", TrackList).show_loading_more()
        self.run_worker(
            partial(self._catalog.get_recommended_tracks, self._PAGE_SIZE),
            name="home-recommendations-next",
            group="home",
            thread=True,
        )

    def on_track_list_load_more(self, event: TrackList.LoadMore) -> None:
        """Handle a load-more request from the track list widget."""
        self._load_more_if_needed()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission by navigating to the search screen.

        Stores the query in the app pending-search state so that the
        search screen can pick it up on mount.

        Args:
            event: The input submission event containing the search text.
        """
        self.app._pending_search_query = event.value.strip()
        await self.app.run_action("go_search")
