from __future__ import annotations

import logging
from datetime import timedelta
from functools import partial
from typing import cast

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.coordinate import Coordinate
from textual.events import Click
from textual.message import Message
from textual.widgets import Static
from textual.worker import Worker, WorkerState

from catalog.downscaler import downscale
from model.track import Track

logger = logging.getLogger(__name__)


class HeartButton(Static):
    """A static widget that shows a heart icon and handles clicks."""

    def __init__(
        self,
        track: Track,
        liked: bool = False,
        on_like: callable | None = None,
    ) -> None:
        super().__init__("\u2665", id=f"heart-{track.provider_id}")
        self.track = track
        self.liked = liked
        self._on_like = on_like
        self.add_class("heart-button")
        self.set_class(liked, "heart-liked")
        self.styles.padding = (0, 0, 0, 0)
        self.styles.margin = (0, 0, 0, 0)
        self.styles.height = 1
        self.styles.content_align_vertical = "middle"
        self.styles.width = 4
        self.styles.min_width = 4
        self.styles.max_width = 4

    def on_click(self, event: Click) -> None:
        """Toggle like status."""
        self.liked = not self.liked
        self.set_class(self.liked, "heart-liked")
        if self._on_like:
            self._on_like(self.track)
        event.stop()

    def set_liked(self, liked: bool) -> None:
        """Set the like status."""
        if self.liked != liked:
            self.liked = liked
            self.set_class(liked, "heart-liked")


class TrackRow(Static):
    """A single track row with album art, info, and a heart button."""

    def __init__(
        self,
        track: Track,
        row_index: int,
        liked: bool,
        on_select: callable | None = None,
        on_like: callable | None = None,
    ) -> None:
        super().__init__()
        self.track = track
        self.row_index = row_index
        self._on_select = on_select
        self._on_like = on_like
        self.liked = liked
        self._art_label = Static("", classes="track-art", id=f"art-{row_index}")
        self._title_label = Static(
            track.title, classes="track-title", id=f"title-{row_index}"
        )
        self._artist_label = Static(
            track.artist, classes="track-artist", id=f"artist-{row_index}"
        )
        self._album_label = Static(
            track.album or "", classes="track-album", id=f"album-{row_index}"
        )
        duration_str = str(timedelta(milliseconds=track.duration_ms))
        self._duration_label = Static(
            duration_str, classes="track-duration", id=f"duration-{row_index}"
        )
        self._heart_button = HeartButton(
            track=track,
            liked=liked,
            on_like=on_like,
        )

    def compose(self) -> ComposeResult:
        yield self._art_label
        yield self._title_label
        yield self._artist_label
        yield self._album_label
        yield self._duration_label
        yield self._heart_button

    def on_click(self, event: Click) -> None:
        """Handle clicks on the row (not the button)."""
        if event.button == 1 and self._on_select:
            self._on_select(self.row_index)
            event.stop()

    def set_liked(self, liked: bool) -> None:
        """Update the like status."""
        self.liked = liked
        self._heart_button.set_liked(liked)

    def render_art(self, ansi: str) -> None:
        """Render album art."""
        self._art_label.update(Text.from_ansi(ansi))


class TrackList(Static):
    """A scrollable list of track rows with heart buttons."""

    class TrackSelected(Message):
        bubble = True

        def __init__(self, sender: TrackList, row: int) -> None:
            super().__init__()
            self.sender = sender
            self.row = row

    class LoadMore(Message):
        bubble = True

    def __init__(
        self,
        widget_id: str = "track-list",
        like_callback: callable | None = None,
        track_selected_callback: callable | None = None,
        like_status_callback: callable | None = None,
    ) -> None:
        super().__init__(id=widget_id)
        self._row_count: int = 0
        self._render_generation: int = 0
        self._like_status: dict[str, bool] = {}
        self._like_callback = like_callback
        self._track_selected_callback = track_selected_callback
        self._like_status_callback = like_status_callback
        self._tracks: list[Track] = []
        self._track_container: Static | None = None
        self._loading_label: Static | None = None
        self._error_label: Static | None = None

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="track-list-scroll")

    def _get_scroll(self) -> VerticalScroll:
        return self.query_one("#track-list-scroll", VerticalScroll)

    def show_results(self, tracks: list[Track]) -> list[Track] | None:
        self._tracks = list(tracks)
        self._render_generation += 1
        generation = self._render_generation
        self._row_count = 0
        scroll = self._get_scroll()
        for w in scroll.query(
            "TrackRow, #loading-label, #error-label, #loading-more-label, #track-container"
        ):
            w.remove()
        self._track_container = Static(id="track-container")
        for idx, track in enumerate(tracks):
            if self._like_status_callback:
                liked = self._like_status_callback(track)
            else:
                liked = (
                    track.provider_id in self._like_status
                    and self._like_status[track.provider_id]
                )
            row = TrackRow(
                track=track,
                row_index=idx,
                liked=liked,
                on_select=self._on_track_select,
                on_like=partial(self._on_toggle_like),
            )
            self._track_container.mount(row)
            if track.image_path and not track.image_path.startswith("Unknown"):
                self.run_worker(
                    partial(self._render_art, generation, idx, track.image_path),
                    name=f"artwork-{generation}-{idx}",
                    group="artwork",
                    thread=True,
                )
        scroll.mount(self._track_container)
        self._max_rows = self._row_count
        return None

    def append_results(self, tracks: list[Track]) -> list[Track] | None:
        self._render_generation += 1
        generation = self._render_generation
        start_row = self._row_count
        self._tracks.extend(tracks)
        if not self._track_container:
            self._track_container = Static(id="track-container")
            self._get_scroll().mount(self._track_container)
        for idx, track in enumerate(tracks):
            actual_row = start_row + idx
            liked = (
                track.provider_id in self._like_status
                and self._like_status[track.provider_id]
            )
            row = TrackRow(
                track=track,
                row_index=actual_row,
                liked=liked,
                on_select=self._on_track_select,
                on_like=partial(self._on_toggle_like),
            )
            self._track_container.mount(row)
            if track.image_path and not track.image_path.startswith("Unknown"):
                self.run_worker(
                    partial(self._render_art, generation, actual_row, track.image_path),
                    name=f"artwork-{generation}-{actual_row}",
                    group="artwork",
                    thread=True,
                )
        self._row_count += len(tracks)
        self._max_rows = self._row_count
        return None

    def show_loading(self) -> None:
        scroll = self._get_scroll()
        if self._track_container:
            self._track_container.remove()
            self._track_container = None
        if self._error_label:
            self._error_label.remove()
            self._error_label = None
        self._loading_label = Static("Loading...", id="loading-label")
        scroll.mount(self._loading_label)

    def show_loading_more(self) -> None:
        scroll = self._get_scroll()
        if not self._track_container:
            self._track_container = Static(id="track-container")
            scroll.mount(self._track_container)
        loading_label = Static("Loading more...", id="loading-more-label")
        loading_label.styles.width = 40
        self._track_container.mount(loading_label)

    def show_error(self, message: str) -> None:
        scroll = self._get_scroll()
        if self._track_container:
            self._track_container.remove()
            self._track_container = None
        if self._loading_label:
            self._loading_label.remove()
            self._loading_label = None
        self._error_label = Static(message, id="error-label")
        scroll.mount(self._error_label)

    def update_like_status(self, provider_id: str, liked: bool) -> None:
        self._like_status[provider_id] = liked
        if self._track_container:
            for row in self._track_container.query("TrackRow"):
                if isinstance(row, TrackRow) and row.track.provider_id == provider_id:
                    row.set_liked(liked)
                    break

    def _on_track_select(self, row_index: int) -> None:
        if self._track_selected_callback and 0 <= row_index < len(self._tracks):
            self._track_selected_callback(row_index)

    def _on_toggle_like(self, track: Track) -> None:
        if self._like_callback:
            row_index = -1
            for idx, t in enumerate(self._tracks):
                if t.provider_id == track.provider_id:
                    row_index = idx
                    break
            if row_index >= 0:
                self._like_callback(self, row_index, track)

    def _render_art(
        self, generation: int, row: int, path: str
    ) -> tuple[int, int, str] | None:
        try:
            result: str = downscale(path, cols=16, cell_aspect=2.0)
            return (generation, row, result)
        except (OSError, ValueError):
            return None

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS:
            return
        result = cast("tuple[int, int, str] | None", event.worker.result)
        if result is None:
            return
        generation, row, ansi = result
        if generation != self._render_generation or not ansi:
            return
        if self._track_container:
            for track_row in self._track_container.query("TrackRow"):
                if isinstance(track_row, TrackRow) and track_row.row_index == row:
                    track_row.render_art(ansi)
                    break
        self._max_rows = self._row_count

    @property
    def cursor_coordinate(self) -> Coordinate | None:
        return None

    @property
    def cursor_type(self) -> str | None:
        return None

    @cursor_type.setter
    def cursor_type(self, value: str | None) -> None:
        pass

    @property
    def show_cursor(self) -> bool:
        return False

    @show_cursor.setter
    def show_cursor(self, value: bool) -> None:
        pass
