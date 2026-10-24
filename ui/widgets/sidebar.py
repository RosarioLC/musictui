from textual.app import ComposeResult
from textual.widgets import Static

from ui.widgets.nav_items import NavItem

# Brand text and section headings.
_BRAND_TEXT: str = "♫  MUSIC"
_MAIN_HEADING: str = "MAIN"
_LIBRARY_HEADING: str = "YOUR LIBRARY"


class Sidebar(Static):
    """Left sidebar with navigation menu."""

    def __init__(self) -> None:
        """Initialize the sidebar."""
        super().__init__(id="sidebar")

    def compose(self) -> ComposeResult:
        """Compose the sidebar layout."""
        yield Static(_BRAND_TEXT, id="brand")
        yield Static(_MAIN_HEADING, classes="sidebar-heading")
        yield NavItem(label="Home", binding="h")
        yield NavItem(label="Search", binding="s")
        yield NavItem(label="Library", binding="l")
        yield Static(_LIBRARY_HEADING, classes="sidebar-heading")
        yield Static("Playlists", classes="sidebar-link")
        yield Static("Liked Songs", classes="sidebar-link")
