"""Immutable playback state used by the UI and player."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PlayState:
    """Immutable snapshot of the current playback state.

    This dataclass captures whether the player is actively playing or
    paused at a point in time.  Because it is frozen, instances can be
    safely shared across threads and UI components without locking.
    The :meth:`replace` method supports functional-style updates by
    producing a new :class:`PlayState` with selected fields changed.

    Attributes:
        is_playing: Whether audio is currently being output to the device.
        is_paused: Whether playback has been temporarily suspended.
    """

    is_playing: bool = False
    is_paused: bool = False

    def replace(self, **changes: object) -> "PlayState":
        """Return a new :class:`PlayState` with the specified fields updated.

        This method follows the functional-update pattern common with frozen
        dataclasses: it does not mutate the current instance but instead
        produces a new one with the requested changes applied.

        Args:
            **changes: Field names and their new values to replace.
                Valid keys are ``is_playing`` and ``is_paused``.

        Returns:
            A new :class:`PlayState` instance reflecting the changes.
        """
        from dataclasses import replace as _dc_replace

        return _dc_replace(self, **changes)  # type: ignore[call-overload]
