"""Protocol defining the contract for all music catalog providers.

Any class implementing this protocol can serve as a source of music
tracks, whether from online APIs (YouTube Music) or local storage.
"""

from typing import Protocol

from model.track import Track


class CatalogSource(Protocol):
    """Interface for music catalog providers (YouTube Music, etc.).

    Implementations must provide a :meth:`search` method that returns
    a list of :class:`~model.track.Track` objects matching the query.
    """

    def search(self, query: str) -> list[Track]:
        """Search the catalog and return matching tracks.

        Args:
            query: The search query string.

        Returns:
            A list of tracks matching the query. May be empty.
        """
        ...

    def get_track(self, track_id: int) -> Track | None:
        """Get a track by its catalog ID (provider_id).

        Args:
            track_id: The YouTube video ID (provider_id) of the track.

        Returns:
            A :class:`~model.track.Track` object if found, ``None`` otherwise.
        """
        ...

    def get_track_stream_url(self, track: Track) -> str:
        """Resolve a playable stream URL for *track*.

        Args:
            track: The track to resolve.

        Returns:
            A stream URL, or the original :attr:`~model.track.Track.url`
            as a fallback when resolution fails.
        """
        ...
