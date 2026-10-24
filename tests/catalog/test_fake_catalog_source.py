"""Tests for the FakeCatalogSource mock."""

from tests.catalog.fake_catalog_source import FakeCatalogSource
from model.track import Track


class TestFakeCatalogSource:
    """Tests for the in-memory catalog mock."""

    def test_search_by_title(self):
        source = FakeCatalogSource(
            tracks=[
                Track(id=1, title="Bohemian Rhapsody", artist="Queen"),
                Track(id=2, title="Hotel California", artist="Eagles"),
            ]
        )
        results = source.search("Bohemian")
        assert len(results) == 1
        assert results[0].title == "Bohemian Rhapsody"

    def test_search_by_artist(self):
        source = FakeCatalogSource(
            tracks=[
                Track(id=1, title="Bohemian Rhapsody", artist="Queen"),
                Track(id=2, title="Hotel California", artist="Eagles"),
            ]
        )
        results = source.search("Queen")
        assert len(results) == 1
        assert results[0].artist == "Queen"

    def test_search_by_album(self):
        source = FakeCatalogSource(
            tracks=[
                Track(id=1, title="Bohemian Rhapsody", artist="Queen", album="A Night at the Opera"),
                Track(id=2, title="Hotel California", artist="Eagles", album="Hotel California"),
            ]
        )
        results = source.search("Opera")
        assert len(results) == 1

    def test_search_case_insensitive(self):
        source = FakeCatalogSource(
            tracks=[Track(id=1, title="Bohemian Rhapsody", artist="Queen")]
        )
        assert len(source.search("bohemian")) == 1
        assert len(source.search("BOHEMIAN")) == 1

    def test_search_no_match(self):
        source = FakeCatalogSource(
            tracks=[Track(id=1, title="Bohemian Rhapsody", artist="Queen")]
        )
        assert source.search("nonexistent") == []

    def test_search_empty_catalog(self):
        source = FakeCatalogSource()
        assert source.search("anything") == []

    def test_search_multiple_matches(self):
        source = FakeCatalogSource(
            tracks=[
                Track(id=1, title="Hello", artist="Artist A"),
                Track(id=2, title="Hello Again", artist="Artist B"),
                Track(id=3, title="Goodbye", artist="Artist C"),
            ]
        )
        results = source.search("Hello")
        assert len(results) == 2
