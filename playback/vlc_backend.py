"""VLC-based audio playback backend."""

from typing import Any

import vlc

# Volume range supported by VLC.
_VOLUME_MAX: int = 100


class VLCAudioBackend:
    """Audio playback backend using the VLC media library.

    Creates a single :class:`vlc.MediaPlayer` instance on first use
    and reuses it for all playback operations.
    """

    # Cached VLC state enum for fast is_paused check.
    _PAUSED_STATE = getattr(vlc.State, "Paused", None)

    def __init__(self) -> None:
        """Initialize the VLC instance with sensible defaults.

        Args:
            _: Unused; retained for backward compatibility.
        """
        self._instance: Any = vlc.Instance(
            "--quiet",
            "--no-video-title-show",
        )
        self._player: Any = None

    def _ensure_player(self) -> Any:
        """Create and return a :class:`vlc.MediaPlayer` if one doesn't exist."""
        if self._player is None or not hasattr(self._player, "play"):
            self._player = self._instance.media_player_new()
        return self._player  # type: ignore[return-value]

    def play(self, url: str) -> None:
        """Start playback of the media at *url*.

        Args:
            url: Media URL or file path.
        """
        player = self._ensure_player()
        media = self._instance.media_new(url)
        player.set_media(media)
        player.play()

    def pause(self) -> None:
        """Toggle pause on the current media."""
        if self._player:
            self._player.pause()

    def resume(self) -> None:
        """Resume playback (equivalent to :meth:`play` when paused)."""
        if self._player:
            self._player.play()

    def stop(self) -> None:
        """Stop playback and release the player."""
        if self._player:
            self._player.stop()

    def seek(self, position_ms: int) -> None:
        """Seek to *position_ms* within the current media.

        Args:
            position_ms: Target position in milliseconds.
        """
        if self._player:
            self._player.set_time(position_ms)

    def get_position(self) -> int:
        """Return the current playback position in milliseconds."""
        return self._player.get_time() if self._player else 0

    def get_duration(self) -> int:
        """Return the total duration of the current media in milliseconds."""
        return self._player.get_length() if self._player else 0

    def set_volume(self, volume: int) -> None:
        """Set the playback volume (0–100).

        Args:
            volume: Volume level.  Clamped to [0, 100].
        """
        if self._player:
            clamped = max(0, min(volume, _VOLUME_MAX))
            self._player.audio_set_volume(clamped)

    def get_volume(self) -> int:
        """Return the current volume (0–100)."""
        return self._player.audio_get_volume() if self._player else 0

    @property
    def is_playing(self) -> bool:
        """``True`` if playback is currently active."""
        player = self._player
        if not player:
            return False
        val = player.is_playing()
        return bool(val) if val is not None else False

    @property
    def is_paused(self) -> bool:
        """``True`` if playback is paused."""
        player = self._player
        if not player:
            return False
        paused_state = self._PAUSED_STATE
        return player.get_state() == paused_state if paused_state else False
