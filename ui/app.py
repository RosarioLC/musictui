from __future__ import annotations

from functools import partial
from typing import ClassVar

from textual.app import App
from textual.binding import Binding

from catalog.track_cache import TrackCache
from catalog.ytmusic_source import YTMusicSource
from model.track import Track
from playback.music_queue import MusicQueue
from playback.player import Player
from playback.vlc_backend import VLCAudioBackend
from services.catalog_service import CatalogService
from services.library_service import LibraryService
from services.playback_service import PlaybackService
from store.database import Database
from store.playlist_store import PlaylistStore
from ui.messages import EventBus
from ui.screens.fullscreen_screen import FullscreenScreen
from ui.screens.home_screen import HomeScreen
from ui.screens.library_screen import LibraryScreen
from ui.screens.lyrics_screen import LyricsScreen
from ui.screens.search_screen import SearchScreen


class MusicTUI(App):
    """Main application for the MusicTUI music player.

    Manages screen navigation, stream resolution, asset preloading,
    and delegates playback to a :class:`~playback.player.Player` instance.
    """

    CSS_PATH: str = "style.tcss"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit", show=True),
        Binding("h", "go_home", "Home", show=True),
        Binding("s", "go_search", "Search", show=True),
        Binding("l", "go_library", "Library", show=True),
        Binding("f", "toggle_fullscreen", "Fullscreen", show=True),
    ]

    def on_mount(self) -> None:
        """Initialize services and push the home screen."""
        import sys

        sys.stdout.write("MUSIC_APP_MOUNTED\n")
        sys.stdout.flush()

        # Core infrastructure.
        self._event_bus = EventBus(self)

        # Services.
        self._catalog_source = YTMusicSource()
        self._store = Database("store.db")
        self._track_cache = TrackCache(max_size=50)
        self._playlist_store = PlaylistStore(self._store, self._catalog_source)

        self._catalog_service = CatalogService(self._catalog_source, self._track_cache)
        self._library_service = LibraryService(self._playlist_store)

        self._player = Player(
            backend=VLCAudioBackend(),
            queue=MusicQueue(),
            stream_resolver=lambda t: self._catalog_service.get_stream(t),
        )
        self._player.set_textual_app(self)
        self._playback_service = PlaybackService(self._player, self._event_bus)

        # Search state.
        self._last_search_query: str = ""
        self._last_search_tracks: list[Track] = []
        self._pending_search_query: str = ""
        self._asset_workers: set[int] = set()

        self.push_screen(
            HomeScreen(
                self._catalog_service, self._playback_service, self._library_service
            )
        )

    def on_unmount(self) -> None:
        """Close the database connection on shutdown."""
        if hasattr(self, "_store"):
            self._store.close()

    def action_go_home(self) -> None:
        """Navigate to the home screen."""
        self.switch_screen(
            HomeScreen(
                self._catalog_service, self._playback_service, self._library_service
            )
        )

    def action_go_search(self) -> None:
        """Navigate to the search screen, preserving the last query."""
        self._playback_service.set_playlist_context(False)
        query = self._pending_search_query or self._last_search_query
        self._pending_search_query = ""
        self.switch_screen(
            SearchScreen(
                catalog=self._catalog_service,
                player=self._playback_service,
                playlists=self._library_service,
                initial_query=query,
                initial_tracks=self._last_search_tracks,
                on_results=self._remember_search,
            )
        )

    def action_go_library(self) -> None:
        """Navigate to the library screen."""
        self._playback_service.set_playlist_context(False)
        self.switch_screen(
            LibraryScreen(
                player=self._playback_service,
                catalog=self._catalog_service,
                playlists=self._library_service,
            )
        )

    def _remember_search(self, query: str, tracks: list[Track]) -> None:
        """Callback invoked by the search screen when results are returned."""
        self._last_search_query = query
        self._last_search_tracks = list(tracks)

    def _resolve_stream(self, track: Track) -> str:
        """Resolve a playable stream URL for *track*, using the cache."""
        cached = self._track_cache.get_stream(track)
        if cached is not None:
            return cached
        stream = self._catalog.get_track_stream_url(track)
        if stream:
            self._track_cache.put_stream(track, stream)
        return stream

    def preload_track(self, track: Track) -> None:
        """Preload stream URL for *track* in the background.

        Skips tracks that are already being loaded.
        """
        if track.id in self._asset_workers:
            return

        self._asset_workers.add(track.id)
        self.run_worker(
            partial(self._load_track_assets, track),
            name=f"track-assets-{track.id}",
            thread=True,
            group="track-assets",
            exit_on_error=False,
        )

    def preload_search_results(self, tracks: list[Track]) -> None:
        """Preload assets for the top 20 search result tracks."""
        for track in tracks[:20]:
            self.preload_track(track)

    def preload_from_search(self, tracks: list[Track]) -> None:
        """Preload assets for the first 10 tracks in the result list."""
        for track in tracks[:10]:
            self.preload_track(track)

    def preload_next_tracks(self, current: Track) -> None:
        """Preload the next 3 tracks in the queue after *current*."""
        for index, track in enumerate(self._player.queue):
            if index >= 3:
                break
            if track.id != current.id:
                self.preload_track(track)

    def _load_track_assets(self, track: Track) -> None:
        """Background worker: resolve stream URL only (lyrics loaded on demand)."""
        self._resolve_stream(track)

    def on_worker_state_changed(self, event: object) -> None:
        """When a track-asset worker finishes, preload the next tracks."""
        worker_name = getattr(event, "worker", None)
        name = worker_name.name if worker_name else ""
        if not name.startswith("track-assets-"):
            return

        track_id = int(name.removeprefix("track-assets-"))
        self._asset_workers.discard(track_id)

        cache = self._track_cache.get(track_id)
        if cache and self._player.is_playing:
            self.preload_next_tracks(cache)

    async def action_show_lyrics(self) -> None:
        """Toggle the lyrics overlay screen."""
        if isinstance(self.screen, LyricsScreen):
            self.pop_screen()
            return

        existing = next(
            (
                screen
                for screen in self.screen_stack
                if isinstance(screen, LyricsScreen)
            ),
            None,
        )
        if existing is not None:
            while self.screen is not existing:
                self.pop_screen()
            return

        if self._player.current_track is None:
            self.notify("Nothing is playing")
            return
        self.push_screen(LyricsScreen(self._playback_service, self._catalog_service))

    async def action_toggle_fullscreen(self) -> None:
        """Toggle the fullscreen album-art overlay screen."""
        if isinstance(self.screen, FullscreenScreen):
            self.pop_screen()
            return

        existing = next(
            (
                screen
                for screen in self.screen_stack
                if isinstance(screen, FullscreenScreen)
            ),
            None,
        )
        if existing is not None:
            while self.screen is not existing:
                self.pop_screen()
            return

        track = self._player.current_track
        if track is None:
            self.notify("Nothing is playing")
            return
        self.push_screen(FullscreenScreen(track))
