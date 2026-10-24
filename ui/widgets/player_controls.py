from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static

_BTN_PREV: str = "<< "
_BTN_PLAY: str = "\u25b6 "
_BTN_NEXT: str = " >>"


class PlayerControls(Static):
    """Transport controls: previous, play/pause, and next."""

    def __init__(self) -> None:
        super().__init__(id="player-controls")

    def compose(self) -> ComposeResult:
        yield Static("", classes="control-spacer")
        yield Button(_BTN_PREV, id="prev")
        yield Button(_BTN_PLAY, id="play-pause")
        yield Button(_BTN_NEXT, id="next")
        yield Static("", classes="control-spacer")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if not hasattr(self.app, "_playback_service"):
            return
        player = self.app._playback_service
        if player is None:
            return
        # Find the screen that owns this widget (the one with the now-playing bar).
        current = self
        while current is not None:
            if isinstance(current, Screen):
                break
            current = current.parent
        if current is None:
            player.play_next()
            return
        match event.button.id:
            case "prev":
                if hasattr(current, "action_previous"):
                    current.action_previous()
                else:
                    player.play_previous()
            case "play-pause":
                player.toggle_play_pause()
            case "next":
                if hasattr(current, "action_next"):
                    current.action_next()
                else:
                    player.play_next()
            case _:
                pass
