from __future__ import annotations

from functools import partial
from typing import Any, cast

from rich.text import Text
from textual.events import Resize
from textual.widgets import Static
from textual.worker import Worker, WorkerState

from catalog.downscaler import CELL_ASPECT, downscale

# Default placeholder text (empty ANSI render).
_DEFAULT_TEXT: str = ""


class AlbumArt(Static):
    """Render album art as ANSI half-block colour text in the terminal."""

    DEFAULT_TEXT: str = _DEFAULT_TEXT

    def __init__(self, art_cols: int | None = None, **kwargs: Any) -> None:
        """Initialize the album art widget.

        Args:
            art_cols: Fixed column count for the rendering.
                If ``None``, the widget adapts to its container size.
            kwargs: Additional keyword arguments passed to :class:`Static`.
        """
        super().__init__(self.DEFAULT_TEXT, **kwargs)
        self._art_cols: int | None = art_cols
        self._source: str | None = None
        self._render_generation: int = 0

    def set_source(self, source: str | None) -> None:
        """Set the image source and schedule a render.

        Args:
            source: File path or URL of the image, or ``None`` to clear.
        """
        if not source or source.startswith("Unknown"):
            self.update(self.DEFAULT_TEXT)
            return
        self._source = source
        self.call_after_refresh(self._render_artwork)

    def _render_artwork(self) -> None:
        """Render the current source image in a background worker."""
        if not self._source or self.size.width <= 0 or self.size.height <= 0:
            return
        self._render_generation += 1
        if self._art_cols is not None:
            cols = self._art_cols
        else:
            # For square rendering: cols = height * CELL_ASPECT
            cols = round(self.size.height * CELL_ASPECT)
        cell_aspect: float = CELL_ASPECT
        self.run_worker(
            partial(downscale, self._source, cols=cols, cell_aspect=cell_aspect),
            name="album-art-render",
            group="album-art",
            exit_on_error=False,
            thread=True,
        )

    def on_resize(self, event: Resize) -> None:
        """Re-render when the widget is resized (adaptive mode only)."""
        if self._source and self._art_cols is None:
            self.call_after_refresh(self._render_artwork)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle the result of the artwork rendering worker."""
        if event.worker.name != "album-art-render":
            return
        if event.state == WorkerState.SUCCESS:
            result = cast(str, event.worker.result)
            self.update(Text.from_ansi(result))
        elif event.state == WorkerState.ERROR:
            self.update(self.DEFAULT_TEXT)
