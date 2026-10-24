from functools import partial
from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Label
from textual.worker import WorkerState

from catalog.catalog_source import CatalogSource
from model.track import Track
from services.playback_service import PlaybackService
from ui.widgets.lyrics_panel import LyricsPanel
from ui.widgets.now_playing_bar import NowPlayingBar

_INTERVAL: float = 0.25


class LyricsScreen(Screen):
    """Overlay screen displaying synced lyrics for the current track."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "close", "Close")]

    def __init__(self, player: PlaybackService, catalog: CatalogSource) -> None:
        super().__init__(id="lyrics-screen")
        self._player = player
        self._catalog = catalog
        self._lyrics_panel: LyricsPanel | None = None
        self._lyrics_title: Label | None = None

    def compose(self) -> ComposeResult:
        yield Label("Lyrics", id="lyrics-title")
        yield LyricsPanel()
        yield Label("Press Escape to close", id="lyrics-help")
        yield Footer()
        yield NowPlayingBar(show_art=True)

    def on_mount(self) -> None:
        self._lyrics_panel = self.query_one(LyricsPanel)
        self._lyrics_title = self.query_one("#lyrics-title", Label)
        self.set_interval(_INTERVAL, self._refresh_highlight)
        track = self._player.current_track
        if track is None:
            self._lyrics_panel.set_message("Nothing is playing")
            return
        self._lyrics_title.update(f"{track.title}  /  {track.artist}")
        self.run_worker(
            partial(self._load_lyrics, track),
            name="lyrics-load",
            group="lyrics",
            thread=True,
        )

    def _refresh_highlight(self) -> None:
        self._lyrics_panel.update_highlight(self._player.position_ms)

    def _load_lyrics(self, track: Track) -> list:
        return self._catalog.get_lyrics(track)

    def on_worker_state_changed(self, event: object) -> None:
        if event.worker.name != "lyrics-load":
            return
        panel = self.query_one(LyricsPanel)
        if event.worker.state == WorkerState.SUCCESS:
            lines = event.worker.result
            if lines:
                panel.set_lyrics(lines)
            else:
                panel.set_message("Lyrics are not available for this track")
        elif event.worker.state == WorkerState.ERROR:
            panel.set_message("Unable to load lyrics")

    def action_close(self) -> None:
        self.app.pop_screen()
