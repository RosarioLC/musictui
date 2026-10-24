"""YouTube Music catalog source."""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
import zlib
from importlib import import_module
from typing import Any

from catalog.catalog_source import CatalogSource
from catalog.lyrics_parser import LyricsParser
from model.lyric_line import LyricLine
from model.track import Track

logger = logging.getLogger(__name__)


class YTMusicSource(CatalogSource):
    _VIDEO_ID_KEY: str = "videoId"
    _TITLE_KEY: str = "title"
    _ARTISTS_KEY: str = "artists"
    _THUMBNAILS_KEY: str = "thumbnails"
    _ALBUM_KEY: str = "album"
    _DURATION_KEY: str = "duration"

    def __init__(self) -> None:
        self._client: Any = None
        self._yt_dlp_dl: Any = None

    def _get_yt_dlp_dl(self) -> Any:
        if self._yt_dlp_dl is not None:
            return self._yt_dlp_dl
        try:
            yt_dlp: Any = import_module("yt_dlp")
            options: dict[str, Any] = {
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "cachedir": True,
            }
            self._yt_dlp_dl = yt_dlp.YoutubeDL(options)
        except ImportError:
            self._yt_dlp_dl = None
        return self._yt_dlp_dl

    def _try_lrclib(self, track: Track) -> list[LyricLine] | None:
        try:
            query = f"{track.artist} {track.title}"
            url = (
                f"https://lrclib.net/api/search"
                f"?q={urllib.parse.quote(query)}"
                f"&track_name={urllib.parse.quote(track.title)}"
                f"&artist_name={urllib.parse.quote(track.artist)}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "MusicTUI/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status != 200:
                    return None
                data = json.loads(resp.read())
                if isinstance(data, list) and data:
                    item = data[0]
                elif isinstance(data, dict):
                    item = data
                else:
                    return None
                lyrics_text = item.get("syncedLyrics") or item.get("plainLyrics", "")
                if not lyrics_text:
                    return None
                parsed = LyricsParser.parse(lyrics_text)
                if parsed:
                    return parsed
                return [
                    LyricLine(timestamp_ms=0, text=line.strip())
                    for line in lyrics_text.splitlines()
                    if line.strip()
                ]
        except Exception:
            return None

    def _get_client(self) -> Any | None:
        if self._client is None:
            try:
                ytmusicapi: Any = import_module("ytmusicapi")
                self._client = ytmusicapi.YTMusic()
            except ImportError:
                self._client = None
        return self._client

    def search(self, query: str) -> list[Track]:
        client = self._get_client()
        if client is None:
            return []
        results = client.search(query, filter="songs")
        tracks: list[Track] = []
        seen: set[str] = set()
        for result in results:
            if not result.get("videoId"):
                continue
            video_id = result[self._VIDEO_ID_KEY]
            if video_id in seen:
                continue
            seen.add(video_id)
            tracks.append(self._make_track(result))
            if len(tracks) >= 20:
                break
        return tracks

    def get_track(self, track_id: int) -> Track | None:
        client = self._get_client()
        if client is None:
            return None
        try:
            wp = client.get_watch_playlist(track_id)
            songs = wp.get("songs", [])
            if songs:
                return self._make_track(songs[0])
        except Exception:
            pass
        return None

    def get_recommended_tracks(self, limit: int = 12) -> list[Track]:
        client = self._get_client()
        if client is None:
            return []
        try:
            sections = client.get_home()
        except Exception:
            return []
        tracks: list[Track] = []
        seen: set[str] = set()
        for section in sections:
            for result in section.get("contents", []):
                if self._skip_rec(result, seen, limit, tracks):
                    return tracks
        return tracks

    def get_track_stream_url(self, track: Track) -> str:
        if not track.url:
            return ""
        dl = self._get_yt_dlp_dl()
        if dl is None:
            return track.url
        try:
            info = dl.extract_info(track.url, download=False)
            return str(info.get("url") or track.url)
        except Exception:
            return track.url

    def get_lyrics(self, track: Track) -> list[LyricLine]:
        tl = self._try_lrclib(track)
        if tl:
            return tl
        tl = self._try_syncedlyrics("", track)
        if tl:
            return tl
        client = self._get_client()
        if client is None or not track.provider_id:
            return []
        lt = self._fetch_yt_lyrics(client, track)
        if lt is None:
            return []
        return self._format_lyrics(lt, track)

    @staticmethod
    def _make_track(result: dict[str, Any]) -> Track:
        vid = result["videoId"]
        artists = result.get("artists") or []
        thumbs = result.get("thumbnails") or []
        dur = _duration_to_ms(result.get("duration"))
        return Track(
            id=zlib.crc32(vid.encode("utf-8")) & 0xFFFFFFFF,
            provider_id=vid,
            title=result.get("title", "Unknown Title"),
            artist=(
                artists[0].get("name", "Unknown Artist")
                if artists
                else "Unknown Artist"
            ),
            album=(result.get("album") or {}).get("name", "Unknown Album"),
            duration_ms=dur,
            image_path=thumbs[-1].get("url", "") if thumbs else "",
            url=f"https://music.youtube.com/watch?v={vid}",
        )

    def _skip_rec(self, result, seen, limit, tracks):
        if "videoId" not in result:
            return False
        vid = result["videoId"]
        if vid in seen:
            return False
        seen.add(vid)
        artists = result.get("artists") or []
        thumbs = result.get("thumbnails") or []
        tracks.append(
            Track(
                id=zlib.crc32(vid.encode("utf-8")) & 0xFFFFFFFF,
                provider_id=vid,
                title=result.get("title", "Unknown Title"),
                artist=(
                    artists[0].get("name", "Unknown Artist")
                    if artists
                    else "Unknown Artist"
                ),
                album=(result.get("album") or {}).get("name", "Unknown Album"),
                image_path=thumbs[-1].get("url", "") if thumbs else "",
                url=f"https://music.youtube.com/watch?v={vid}",
            )
        )
        return len(tracks) >= limit

    def _fetch_yt_lyrics(self, client, track):
        try:
            wp = client.get_watch_playlist(track.provider_id)
            bid = wp.get("lyrics")
            if not bid:
                return None
            r = client.get_lyrics(bid)
            lyrics = r.get("lyrics", "")
        except Exception:
            return None
        return lyrics if lyrics else None

    def _format_lyrics(self, lyrics, track):
        tl = self._try_syncedlyrics(lyrics, track)
        if tl:
            return tl
        return self._distribute_lyrics_linearly(lyrics, track)

    def _try_syncedlyrics(self, lyrics, track):
        try:
            syncedlyrics = import_module("syncedlyrics")
            synced = syncedlyrics.search(f"{track.artist} {track.title}", enhanced=True)
            if synced:
                tl = LyricsParser.parse(synced)
                if tl:
                    return tl
        except (ImportError, Exception):
            pass
        return None

    @staticmethod
    def _distribute_lyrics_linearly(lyrics, track):
        pl = [l for l in lyrics.splitlines() if l.strip()]
        li = len(pl) - 1
        if li < 0 or track.duration_ms <= 0:
            return [LyricLine(timestamp_ms=0, text=l) for l in pl]
        step = track.duration_ms / li
        return [
            LyricLine(timestamp_ms=int(i * step), text=pl[i]) for i in range(len(pl))
        ]


def _duration_to_ms(duration):
    if not duration:
        return 0
    try:
        m, s = (int(p) for p in duration.split(":", 1))
        return (m * 60 + s) * 1000
    except ValueError:
        return 0
