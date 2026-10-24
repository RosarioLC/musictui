"""Mixin classes for shared screen behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Static

from model.track import Track
from ui.widgets.modal import PlaylistPickerScreen

if TYPE_CHECKING:
    from services.library_service import LibraryService
    from services.playback_service import PlaybackService


class Likeable:
    """Mixin that provides like/unlike functionality for screens."""

    library_service: LibraryService | None = None

    def _on_toggle_like(self, sender: Static, row: int, track: Track) -> None:
        """Toggle the like status of *track* in the liked-songs collection."""
        library = self.library_service
        if library is None:
            return
        try:
            if library.is_liked(track):
                library.remove_from_liked_songs(track)
                self.notify("Removed from Liked Songs")
            else:
                library.add_to_liked_songs(track)
                self.notify("Added to Liked Songs")
            if track.provider_id:
                liked = library.is_liked(track)
                sender.update_like_status(track.provider_id, liked)
            if self.app:
                from ui.messages import LikedSongsChanged

                self.app.post_message(LikedSongsChanged())
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")


class PlaylistActionable:
    """Mixin that provides add-to-playlist functionality for screens."""

    library_service: LibraryService | None = None
    playback_service: PlaybackService | None = None

    def action_add_to_playlist(self) -> None:
        """Show the playlist picker for the currently playing track."""
        player = self.playback_service
        library = self.library_service
        if player is None or library is None:
            return
        current = player.current_track
        if current is None:
            self.notify("Nothing is playing", severity="warning")
            return
        playlists = library.list_playlists()
        non_liked = [p for p in playlists if p.id != -1]
        if not non_liked:
            self.notify(
                "Create a playlist first (go to Library -> N)", severity="warning"
            )
            return
        self.call_after_refresh(
            lambda: self.app.push_screen(
                PlaylistPickerScreen(non_liked),
                callback=self._on_add_to_playlist_result,
            )
        )

    def _on_add_to_playlist_result(self, playlist_id: int | None) -> None:
        """Handle the playlist picker result and add the track."""
        library = self.library_service
        player = self.playback_service
        if library is None or player is None:
            return
        if playlist_id is None:
            return
        current = player.current_track
        if current is None:
            return
        try:
            library.add_song(playlist_id, current)
            self.notify("Added to playlist")
            if self.app:
                from ui.messages import PlaylistChanged
                self.app.post_message(PlaylistChanged())
        except ValueError as exc:
            self.notify(str(exc), severity="error")
        except Exception as exc:  # noqa: BLE001
            self.notify(str(exc), severity="error")
