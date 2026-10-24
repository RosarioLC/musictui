from textual.app import ComposeResult
from textual.widgets import DataTable, Label, Static

from model.track import Track
from ui.messages import QueueUpdated


class QueuePanel(Static):
    """Displays the upcoming tracks in the queue as a data table.

    Listens for :class:`~ui.messages.QueueUpdated` events and refreshes
    the table whenever the queue changes.

    The table has two columns: "Title" and "Artist".
    """

    def __init__(self) -> None:
        """Initialize the queue panel widget."""
        super().__init__(id="queue-panel")
        self._table_ref: DataTable | None = None

    def compose(self) -> ComposeResult:
        """Compose the queue panel layout."""
        yield Label("Up Next")
        yield DataTable(id="queue-tracks")

    def on_mount(self) -> None:
        """Cache the table reference for fast access."""
        try:
            self._table_ref = self.query_one("#queue-tracks", DataTable)
        except Exception:  # noqa: BLE001, S110
            pass

    def on_queue_updated(self, event: QueueUpdated) -> None:
        """Refresh the table when the queue changes."""
        self.update_tracks(event.upcoming)

    def update_tracks(self, tracks: list[Track]) -> None:
        """Populate the table with the given tracks.

        Args:
            tracks: The upcoming tracks to display.
        """
        table = self._table_ref
        if table is None:
            return
        table.clear(columns=False)
        if not table.columns:
            table.add_columns("Title", "Artist")
        for track in tracks:
            table.add_row(track.title, track.artist)
