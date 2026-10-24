# ui/widgets/modal.py
"""Modal dialog widgets for the application."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static


class NewPlaylistScreen(Screen):
    """Modal dialog for creating a new playlist."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "cancel", "Cancel")]

    def __init__(self) -> None:
        """Initialize the new playlist dialog."""
        super().__init__()
        self._result: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Vertical(id="dialog"):
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

    def on_key(self, event) -> None:
        """Handle Enter key to submit."""
        if event.key == "enter":
            self.on_button_pressed(
                Button.Pressed(self.query_one("#create-button", Button))
            )

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)


class RenamePlaylistScreen(Screen):
    """Modal dialog for renaming a playlist."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, old_name: str) -> None:
        """Initialize the rename dialog.

        Args:
            old_name: The current playlist name.
        """
        super().__init__()
        self._old_name = old_name
        self._result: str | None = None

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Vertical(id="dialog"):
            yield Label("Rename playlist:", id="title")
            yield Input(placeholder=self._old_name, id="name-input")
            with Horizontal(id="buttons"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            name = self.query_one("#name-input", Input).value.strip()
            if name and name != self._old_name:
                self._result = name
                self.dismiss(self._result)
            else:
                self.notify("Please enter a new name", severity="error")
        elif event.button.id == "cancel-button":
            self._result = None
            self.dismiss(self._result)

    def on_mount(self) -> None:
        """Focus the input field after mount."""
        self.call_later(self._focus_input)

    def _focus_input(self) -> None:
        """Focus the input field."""
        input_widget = self.query_one("#name-input", Input)
        input_widget.focus()

    def on_key(self, event) -> None:
        """Handle Enter key to submit."""
        if event.key == "enter":
            self.on_button_pressed(
                Button.Pressed(self.query_one("#save-button", Button))
            )

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)


class PlaylistPickerScreen(Screen):
    """Modal dialog for choosing which playlist to add a track to."""

    BINDINGS: ClassVar[list[Binding]] = [Binding("escape", "cancel", "Cancel")]

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
        with Vertical(id="dialog"):
            yield Label("Add to playlist:")
            if self._playlists:
                for playlist in self._playlists:
                    yield Button(
                        playlist.name,
                        variant="primary",
                        id=f"playlist-{playlist.id}",
                    )
            else:
                yield Static("No playlists yet.")
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
        self.call_later(self._focus_first_button)

    def _focus_first_button(self) -> None:
        """Focus the first playlist button."""
        if not self._playlists:
            return
        buttons = self.query(Button)
        if buttons:
            buttons.first().focus()

    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)
