"""Search results table with album art and like buttons."""

from __future__ import annotations

from datetime import timedelta
from functools import partial
from typing import cast

from rich.style import Style
from rich.text import Text
from textual.coordinate import Coordinate
from textual.events import Click, MouseMove, MouseScrollDown, MouseScrollUp
from textual.message import Message
from textual.widgets import DataTable
from textual.worker import Worker, WorkerState

from catalog.downscaler import downscale
from model.track import Track

_NULL_STYLE: Style = Style.null()


class SearchResults(DataTable):
    """DataTable subclass showing search results with album art in the first column."""

    class TrackSelected(Message):
        """Emitted when the user selects a track from the results."""

        bubble = True

        def __init__(self, sender: SearchResults, row: int) -> None:
            super().__init__()
            self.sender = sender
            self.row = row

    class LoadMore(Message):
        """Emitted when the user scrolls to the bottom of results."""

        bubble = True

    def __init__(
        self,
        widget_id: str = "search-results",
        like_callback: callable | None = None,
        track_selected_callback: callable | None = None,
    ) -> None:
        """Initialize the search results widget."""
        super().__init__(id=widget_id)
        self._row_count: int = 0
        self._max_rows: int = 0
        self.cursor_type = "cell"
        self.show_cursor: bool = True
        self.add_column("Art", width=16)
        self.add_columns("Title", "Artist", "Album", "Duration", "Like")
        self._render_generation: int = 0
        self._stripped_styles: dict[int, Style] = {}
        self._load_more_threshold: int = 5
        self._row_height: int = 8
        self._like_status: dict[str, bool] = {}
        self._like_callback = like_callback
        self._track_selected_callback = track_selected_callback

    def on_click(self, event: Click) -> None:
        """Handle clicks: determine cell from click coordinates."""
        try:
            coord = self.get_cell_coordinate(event.offset.x, event.offset.y)
            if coord is not None and coord.row is not None and coord.column is not None:
                row = int(coord.row)
                col = int(coord.column)
                if row >= 0:
                    self.call_next(lambda r=row, c=col: self._handle_cell_action(r, c))
                    return
        except Exception:  # noqa: BLE001, S110
            pass
        self._on_click(event)
        self.call_next(self._play_from_cursor)

    def _play_from_cursor(self) -> None:
        """Play the track at the current cursor position."""
        coord = self.cursor_coordinate
        if coord and coord.row is not None and coord.column is not None:
            row = int(coord.row)
            if 0 <= row < self._row_count:
                self._track_selected_callback(row)

    def _handle_cell_action(self, row: int, col: int) -> None:
        """Handle a cell click based on column index."""
        if col == 5 and self._like_callback is not None and row < self._row_count:
            track = self._get_track_at_row(row)
            if track:
                self._like_callback(self, row, track)
        elif col >= 1:
            if self._track_selected_callback is not None:
                self._track_selected_callback(row)

    def _get_track_at_row(self, row: int) -> Track | None:
        """Get the track at the given row index."""
        return None

    def on_mouse_move(self, event: MouseMove) -> None:
        """Handle mouse hover over cells."""
        try:
            coord = self.get_cell_coordinate(event.offset.x, event.offset.y)
            if coord is not None and coord.row is not None and coord.column is not None:
                row = int(coord.row)
                col = int(coord.column)
                if row >= 0:
                    self.call_next(lambda r=row, c=col: self._handle_cell_action(r, c))
                    return
        except Exception:  # noqa: BLE001, S110
            pass
        self._on_click(event)
        self.call_next(self._play_from_cursor)

    def on_scroll_down(self, event: MouseScrollDown) -> None:
        """Check for load-more when scrolling down."""
        self._check_load_more()

    def on_scroll_up(self, event: MouseScrollUp) -> None:
        """Check for load-more when scrolling up."""
        self._check_load_more()

    def _check_load_more(self) -> None:
        """Emit LoadMore if the user is near the bottom."""
        if self._row_count - self.cursor_row <= self._load_more_threshold:
            self.post_message(self.LoadMore())

    def show_loading(self) -> None:
        """Display a 'loading' row at the bottom."""
        current_rows = self._row_count
        self.add_row("", "Loading...", "", "", "", height=1, key=str(current_rows))

    def show_error(self, message: str) -> None:
        """Clear existing rows and display an error message."""
        self.clear()
        self._row_count = 0
        self.add_row("", message, "", "", "", height=1)

    def show_results(self, tracks: list[Track]) -> list[Track] | None:
        """Clear existing rows and display the given tracks."""
        self._render_generation += 1
        generation = self._render_generation
        self.clear()
        self._row_count = 0
        existing_ids: set[str] = set()
        for idx, track in enumerate(tracks):
            if track.provider_id:
                existing_ids.add(track.provider_id)
            liked = track.provider_id in self._like_status and self._like_status[track.provider_id]
            self.add_row("", track.title, track.artist, track.album,
                str(timedelta(milliseconds=track.duration_ms)),
                "❤️" if liked else "🤍", height=8)
            if track.image_path and not track.image_path.startswith("Unknown"):
                self.run_worker(partial(self._render_art, generation, idx, track.image_path),
                    name=f"artwork-{generation}-{idx}", group="artwork", thread=True)
            self._row_count += 1
        self._max_rows = self._row_count
        return existing_ids

    def append_results(self, tracks: list[Track]) -> list[Track] | None:
        """Append more results without clearing existing rows."""
        self._render_generation += 1
        generation = self._render_generation
        existing_ids: set[str] = set()
        start_row = self._row_count
        for idx, track in enumerate(tracks):
            if track.provider_id:
                existing_ids.add(track.provider_id)
            actual_row = start_row + idx
            liked = track.provider_id in self._like_status and self._like_status[track.provider_id]
            self.add_row("", track.title, track.artist, track.album,
                str(timedelta(milliseconds=track.duration_ms)),
                "❤️" if liked else "🤍", height=8)
            if track.image_path and not track.image_path.startswith("Unknown"):
                self.run_worker(partial(self._render_art, generation, actual_row, track.image_path),
                    name=f"artwork-{generation}-{actual_row}", group="artwork", thread=True)
            self._row_count += 1
        self._max_rows = self._row_count
        return existing_ids

    def show_loading_more(self) -> None:
        """Display a 'loading more' row at the bottom."""
        current_rows = self._row_count
        self.add_row("", "Loading more...", "", "", "", height=1, key=str(current_rows))

    def _render_art(self, generation: int, row: int, path: str) -> tuple[int, int, str] | None:
        """Render album art for a track in a background worker."""
        try:
            result: str = downscale(path, cols=16, cell_aspect=2.0)
            return (generation, row, result)
        except (OSError, ValueError):
            return None

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle completion of an artwork rendering worker."""
        if event.state != WorkerState.SUCCESS:
            return
        result = cast("tuple[int, int, str] | None", event.worker.result)
        if result is None:
            return
        generation, row, ansi = result
        if generation != self._render_generation or not ansi:
            return
        self.update_cell_at(Coordinate(row, 0), Text.from_ansi(ansi))
        self._max_rows = self._row_count

    def _on_click(self, event: Click) -> None:
        """Default click handler."""

    def _on_mouse_move(self, event: MouseMove) -> None:
        """Default mouse move handler."""
