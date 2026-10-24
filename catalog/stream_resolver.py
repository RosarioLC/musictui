"""Resolve track metadata into playable stream URLs."""

from model.track import Track


class StreamResolver:
    """Simple stream resolver that returns the track's URL as-is.

    This is the default / fallback resolver.  More sophisticated
    implementations (e.g. using yt_dlp to extract direct audio URLs)
    can replace this class via dependency injection.
    """

    def resolve(self, track: Track) -> str:
        """Return the track's URL as the stream URL.

        This is a pass-through resolver: it does not perform any network
        requests or URL transformation.

        Args:
            track: The track whose URL to return.

        Returns:
            The value of :attr:`~model.track.Track.url`.  Returns an empty
            string if the track has no URL set.
        """
        return track.url
