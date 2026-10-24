from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.events import Click
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget


class Slider(Widget):
    """Interactive horizontal slider used by the playback controls.

    Renders a two-line visual indicator (filled/empty blocks) and
    responds to clicks to set the value.
    """

    can_focus: bool = True
    value: reactive[float] = reactive(0.0)
    maximum: reactive[float] = reactive(100.0)

    class Updated(Message):
        """Sent when the user changes the slider value via click or other means.

        Attributes:
            slider: The :class:`Slider` that emitted this message.
            value: The new slider value.
        """

        def __init__(self, slider: Slider, value: float) -> None:
            super().__init__()
            self.slider = slider
            self.value = value

    def __init__(
        self,
        *,
        value: float = 0.0,
        maximum: float = 100.0,
        **kwargs: Any,
    ) -> None:
        """Initialize the slider.

        Args:
            value: Initial value.
            maximum: Maximum value (the range is 0..maximum).
            kwargs: Additional keyword arguments passed to :class:`Widget`.
        """
        super().__init__(**kwargs)
        self.value = value
        self.maximum = maximum

    def render(self) -> Text:
        """Render the slider as two lines of block characters."""
        width: int = max(self.size.width, 1)
        maximum: float = max(float(self.maximum), 1.0)
        filled: int = round(min(max(float(self.value) / maximum, 0.0), 1.0) * width)
        remainder: int = width - filled
        line: Text = Text.assemble(
            ("█" * filled, "#1ed760 bold"),
            ("░" * remainder, "#535353"),
        )
        return line

    def on_click(self, event: Click) -> None:
        """Set the slider value based on click position."""
        if self.size.width <= 0:
            return
        ratio: float = min(max(event.x / self.size.width, 0.0), 1.0)
        self.value = ratio * float(self.maximum)
        self.post_message(self.Updated(self, self.value))
