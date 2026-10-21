# ui/widgets/modal.py
"""Modal dialog widgets for the application."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class NewPlaylistScreen(Screen):
    """Modal dialog for creating a new playlist."""

    CSS = """
    Screen {
        background: rgba(0, 0, 0, 0.7);
    }

    #dialog {
        background: #181818;
        border: solid #1ed760;
        width: 50;
        height: auto;
        padding: 2 4;
        margin: 1;
        layout: vertical;
        align: center middle;
    }

    #title {
        text-style: bold;
        color: #ffffff;
        height: 3;
        content-align: center middle;
    }

    Input {
        width: 100%;
        margin-top: 1;
        margin-bottom: 1;
        padding: 0 1;
        height: 3;
        color: #ffffff;
        background: #242424;
        border: round #535353;
    }

    Input:focus {
        border: round #1ed760;
    }

    #buttons {
        dock: bottom;
        width: 100%;
        layout: horizontal;
    }

    #buttons Button {
        width: 50%;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self) -> None:
        """Initialize the new playlist dialog."""
        super().__init__()
        self._result: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        yield Label("Enter playlist name:", id="title")
        yield Input(placeholder="My Playlist", id="name-input")
        with Horizontal(id="buttons"):
            yield Button("Create", variant="primary", id="create-button")
            yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-button":
            name = self.query_one(Input).value.strip()
            if name:
                self._result = name
                self.dismiss(self._result)
            else:
                self.notify("Please enter a playlist name", severity="error")
        elif event.button.id == "cancel-button":
            self._result = None
            self.dismiss(self._result)

    def on_mount(self) -> None:
        """Focus the input field after mount."""
        self.call_later(self._focus_input)

    def _focus_input(self) -> None:
        """Focus the input field."""
        input_widget = self.query_one(Input)
        input_widget.focus()
        self.log(f"Input focused: {input_widget.has_focus}")

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)


class PlaylistPickerScreen(Screen):
    """Modal dialog for choosing which playlist to add a track to."""

    CSS = """
    Screen {
        background: rgba(0, 0, 0, 0.7);
    }

    #dialog {
        background: #181818;
        border: solid #1ed760;
        width: 50;
        height: auto;
        padding: 2 4;
        margin: 1;
        layout: vertical;
        align: center middle;
    }

    #title {
        text-style: bold;
        color: #ffffff;
        height: 3;
        content-align: center middle;
    }

    #buttons {
        dock: bottom;
        width: 100%;
        layout: horizontal;
    }

    #buttons Button {
        width: 50%;
    }

    #empty-message {
        height: 3;
        color: #a0a0a0;
        content-align: center middle;
    }
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, playlists: list) -> None:
        """Initialize the playlist picker.

        Args:
            playlists: List of playlist objects with 'id' and 'name' attributes.
        """
        super().__init__()
        self._playlists = playlists
        self._result: int | None = None

    def compose(self) -> ComposeResult:
        """Compose the picker layout."""
        yield Label("Add to playlist:", id="title")
        if self._playlists:
            for playlist in self._playlists:
                yield Button(
                    playlist.name,
                    variant="primary",
                    id=f"playlist-{playlist.id}",
                )
        else:
            yield Static("No playlists yet.", id="empty-message")
        with Horizontal(id="buttons"):
            yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-button":
            self._result = None
            self.dismiss(self._result)
        elif event.button.id and event.button.id.startswith("playlist-"):
            playlist_id = int(event.button.id.removeprefix("playlist-"))
            self._result = playlist_id
            self.dismiss(self._result)

    def on_mount(self) -> None:
        """Focus the first playlist button if available."""
        if self._playlists:
            first_btn = self.query_one("#playlist-0", Button)
            if first_btn:
                first_btn.focus()

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
