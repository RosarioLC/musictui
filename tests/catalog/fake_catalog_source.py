from catalog.catalog_source import CatalogSource
from model.track import Track


class FakeCatalogSource(CatalogSource):
    def __init__(self, tracks=None):
        self._tracks = tracks or []

    def search(self, query: str) -> list[Track]:
        query_lower = query.lower()
        return [
            t
            for t in self._tracks
            if query_lower in t.title.lower()
            or query_lower in t.artist.lower()
            or query_lower in t.album.lower()
        ]
