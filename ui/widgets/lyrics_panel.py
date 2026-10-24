import bisect
from typing import ClassVar

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView, Static

from model import LyricLine

# Maximum number of lyric lines to keep in memory.
_MAX_LINES: int = 500


class LyricsPanel(Static):
    """Shows synced LRC lyrics, highlighting the current line."""

    # -- internal state
    _lines: ClassVar[list[LyricLine]] = []
    _timed: bool = False
    _active_line: int = -1
    _list_view_ref: ListView | None = None

    def compose(self) -> ComposeResult:
        """Compose the lyrics list view."""
        list_view = ListView(id="lyrics-list")
        list_view.can_focus = False
        yield list_view

    def on_mount(self) -> None:
        """Cache the list view reference."""
        try:
            self._list_view_ref = self.query_one("#lyrics-list", ListView)
        except Exception:  # noqa: BLE001, S110
            pass

    def set_lyrics(self, lines: list[LyricLine]) -> None:
        """Set the lyrics to display.

        Args:
            lines: List of :class:`~model.lyric_line.LyricLine` objects.
        """
        self._lines = lines[:_MAX_LINES]
        self._timed = any(line.timestamp_ms > 0 for line in self._lines)
        self._active_line = -1

        list_view = self._list_view_ref
        if list_view is None:
            return
        list_view.clear()
        for line in self._lines:
            item = ListItem(Label(line.text))
            item.selectable = False
            list_view.append(item)
        self.call_after_refresh(self._enlarge_lyrics_font)

    def set_message(self, message: str) -> None:
        """Display a plain message instead of lyrics.

        Args:
            message: Message text to show.
        """
        list_view = self._list_view_ref
        if list_view is None:
            return
        list_view.clear()
        item = ListItem(Label(message, id="lyrics-message"))
        item.selectable = False
        list_view.append(item)

    def _enlarge_lyrics_font(self) -> None:
        """Apply larger font size to all lyric labels."""
        list_view = self._list_view_ref
        if list_view is None:
            return
        for item in list_view.children:
            label = item.query_one(Label)
            label.set_class("lyrics-line")
            label.styles.font_size = 14

    def update_highlight(self, position_ms: int) -> None:
        """Highlight the active lyric line based on current playback position.

        Uses binary search for O(log n) lookup instead of linear scan.

        Args:
            position_ms: Current playback position in milliseconds.
        """
        if not getattr(self, "_timed", False):
            return

        lines = getattr(self, "_lines", [])
        if not lines:
            return

        timestamps = [line.timestamp_ms for line in lines]
        active_index = bisect.bisect_right(timestamps, position_ms) - 1

        if active_index < 0:
            list_view = self._list_view_ref
            if list_view is None:
                return
            for item in list_view.children:
                item.remove_class("lyrics-active")
            self._active_line = -1
            return

        if active_index == self._active_line:
            return

        list_view = self._list_view_ref
        if list_view is None:
            return
        if 0 <= self._active_line < len(list_view.children):
            list_view.children[self._active_line].set_class(False, "lyrics-active")
        if 0 <= active_index < len(list_view.children):
            list_view.children[active_index].set_class(True, "lyrics-active")
        self._active_line = active_index
