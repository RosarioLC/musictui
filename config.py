"""Application-wide constants and configuration."""

from __future__ import annotations

# ── Pagination ────────────────────────────────────────────────────────
PAGE_SIZE: int = 12

# ── Cache ─────────────────────────────────────────────────────────────
CACHE_MAX_SIZE: int = 50

# ── Refresh / timing intervals (seconds) ──────────────────────────────
REFRESH_INTERVAL: float = 0.5
HIGHLIGHT_INTERVAL: float = 0.25

# ── Volume ────────────────────────────────────────────────────────────
VOLUME_MAX: int = 100

# ── Playlist IDs ──────────────────────────────────────────────────────
LIKED_SONGS_ID: int = -1

# ── Branding ──────────────────────────────────────────────────────────
BRAND_TEXT: str = "\u266b  MUSIC"

# ── Section headings ──────────────────────────────────────────────────
MAIN_HEADING: str = "MAIN"
LIBRARY_HEADING: str = "YOUR LIBRARY"

# ── Navigation labels ─────────────────────────────────────────────────
NAV_HOME: str = "Home"
NAV_SEARCH: str = "Search"
NAV_LIBRARY: str = "Library"

# ── Player control labels ─────────────────────────────────────────────
BTN_PREV: str = "\u00ab\u00ab"
BTN_PLAY: str = "\u25b6"
BTN_NEXT: str = "\u00bb\u00bb"

# ── Player transport actions ──────────────────────────────────────────
ACTION_PREV: str = "prev"
ACTION_PLAY_PAUSE: str = "play-pause"
ACTION_NEXT: str = "next"

# ── Navigation bindings ───────────────────────────────────────────────
NAV_BINDING_HOME: str = "h"
NAV_BINDING_SEARCH: str = "s"
NAV_BINDING_LIBRARY: str = "l"

# ── Navigation action map ─────────────────────────────────────────────
NAV_ACTION_MAP: dict[str, str] = {
    "h": "home",
    "s": "search",
    "l": "library",
}

# ── YouTube Music URLs ────────────────────────────────────────────────
YOUTUBE_BASE_URL: str = "https://music.youtube.com/watch?v="

# ── Search result keys ────────────────────────────────────────────────
KEY_ARTIST_NAME: str = "name"
KEY_ALBUM_NAME: str = "name"
KEY_THUMBNAIL_URL: str = "url"
KEY_VIDEO_ID: str = "videoId"
KEY_TITLE: str = "title"
KEY_ARTISTS: str = "artists"
KEY_THUMBNAILS: str = "thumbnails"
KEY_ALBUM: str = "album"
KEY_DURATION: str = "duration"

# ── Database table names ──────────────────────────────────────────────
DB_TABLE_LIKED_SONGS: str = "liked_songs"
DB_TABLE_TRACKS: str = "tracks"
DB_TABLE_PLAYLISTS: str = "playlists"
DB_TABLE_PLAYLIST_SONGS: str = "playlist_songs"
