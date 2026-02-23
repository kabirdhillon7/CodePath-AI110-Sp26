import random
from collections import Counter
from typing import Dict, List, Optional, Tuple

Song = Dict[str, object]
PlaylistMap = Dict[str, List[Song]]

# Playlist keys
PLAYLIST_HYPE = "Hype"
PLAYLIST_CHILL = "Chill"
PLAYLIST_MIXED = "Mixed"

# Lucky pick modes
MODE_HYPE = "hype"
MODE_CHILL = "chill"
MODE_ANY = "any"

DEFAULT_PROFILE = {
    "name": "Default",
    "hype_min_energy": 7,
    "chill_max_energy": 3,
    "favorite_genre": "rock",
    "include_mixed": True,
}


def normalize_text(value: str) -> str:
    """Normalize a text field by stripping whitespace."""
    if not value:
        return ""
    return value.strip()


def normalize_title(title: str) -> str:
    """Normalize a song title for comparisons."""
    return normalize_text(title)


def normalize_artist(artist: str) -> str:
    """Normalize an artist name for comparisons."""
    return normalize_text(artist)


def normalize_genre(genre: str) -> str:
    """Normalize a genre name for comparisons."""
    return genre.lower().strip()


def normalize_song(raw: Song) -> Song:
    """Return a normalized song dict with expected keys."""
    title = normalize_title(str(raw.get("title", "")))
    artist = normalize_artist(str(raw.get("artist", "")))
    genre = normalize_genre(str(raw.get("genre", "")))
    energy = raw.get("energy", 0)

    if isinstance(energy, str):
        try:
            energy = int(energy)
        except ValueError:
            energy = 0

    tags = raw.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "title": title,
        "artist": artist,
        "genre": genre,
        "energy": energy,
        "tags": tags,
    }


def classify_song(song: Song, profile: Dict[str, object]) -> str:
    """Return a mood label given a song and user profile."""
    energy = song.get("energy", 0)
    genre = song.get("genre", "")

    hype_min_energy = profile.get("hype_min_energy", 7)
    chill_max_energy = profile.get("chill_max_energy", 3)
    favorite_genre = profile.get("favorite_genre", "")

    hype_keywords = ["rock", "punk", "party"]
    chill_keywords = ["lofi", "ambient", "sleep"]

    is_hype_keyword = any(k in genre for k in hype_keywords)
    is_chill_keyword = any(k in genre for k in chill_keywords)

    if genre == str(favorite_genre).lower() or energy >= hype_min_energy or is_hype_keyword:
        return PLAYLIST_HYPE
    if energy <= chill_max_energy or is_chill_keyword:
        return PLAYLIST_CHILL
    return PLAYLIST_MIXED


def build_playlists(songs: List[Song], profile: Dict[str, object]) -> PlaylistMap:
    """Group songs into playlists based on mood and profile."""
    playlists: PlaylistMap = {
        PLAYLIST_HYPE: [],
        PLAYLIST_CHILL: [],
        PLAYLIST_MIXED: [],
    }

    for song in songs:
        normalized = normalize_song(song)
        mood = classify_song(normalized, profile)
        normalized["mood"] = mood
        playlists[mood].append(normalized)

    return playlists


def merge_playlists(a: PlaylistMap, b: PlaylistMap) -> PlaylistMap:
    """Merge two playlist maps into a new map."""
    merged: PlaylistMap = {}
    for key in set(list(a.keys()) + list(b.keys())):
        merged[key] = a.get(key, []) + b.get(key, [])
    return merged


def compute_playlist_stats(playlists: PlaylistMap) -> Dict[str, object]:
    """Compute statistics across all playlists."""
    all_songs: List[Song] = []
    for songs in playlists.values():
        all_songs.extend(songs)

    hype = playlists.get(PLAYLIST_HYPE, [])
    chill = playlists.get(PLAYLIST_CHILL, [])
    mixed = playlists.get(PLAYLIST_MIXED, [])

    total = len(all_songs)
    hype_ratio = len(hype) / total if total > 0 else 0.0

    avg_energy = 0.0
    if all_songs:
        total_energy = sum(song.get("energy", 0) for song in all_songs)
        avg_energy = total_energy / total

    top_artist, top_count = most_common_artist(all_songs)

    return {
        "total_songs": total,
        "hype_count": len(hype),
        "chill_count": len(chill),
        "mixed_count": len(mixed),
        "hype_ratio": hype_ratio,
        "avg_energy": avg_energy,
        "top_artist": top_artist,
        "top_artist_count": top_count,
    }


def most_common_artist(songs: List[Song]) -> Tuple[str, int]:
    """Return the most common artist and count."""
    artists = [str(song.get("artist", "")) for song in songs if song.get("artist", "")]
    if not artists:
        return "", 0
    return Counter(artists).most_common(1)[0]


def search_songs(
    songs: List[Song],
    query: str,
    field: str = "artist",
) -> List[Song]:
    """Return songs matching the query on a given field."""
    if not query:
        return songs

    q = query.lower().strip()
    filtered: List[Song] = []

    for song in songs:
        value = str(song.get(field, "")).lower()
        if value and q in value:
            filtered.append(song)

    return filtered


def lucky_pick(
    playlists: PlaylistMap,
    mode: str = MODE_ANY,
) -> Optional[Song]:
    """Pick a song from the playlists according to mode."""
    if mode == MODE_HYPE:
        songs = playlists.get(PLAYLIST_HYPE, [])
    elif mode == MODE_CHILL:
        songs = playlists.get(PLAYLIST_CHILL, [])
    else:
        songs = playlists.get(PLAYLIST_HYPE, []) + playlists.get(PLAYLIST_CHILL, [])

    return random_choice_or_none(songs)


def random_choice_or_none(songs: List[Song]) -> Optional[Song]:
    """Return a random song or None."""
    return random.choice(songs) if songs else None


def history_summary(history: List[Song]) -> Dict[str, int]:
    """Return a summary of moods seen in the history."""
    counts = {PLAYLIST_HYPE: 0, PLAYLIST_CHILL: 0, PLAYLIST_MIXED: 0}
    for song in history:
        mood = song.get("mood", PLAYLIST_MIXED)
        if mood not in counts:
            counts[PLAYLIST_MIXED] += 1
        else:
            counts[mood] += 1
    return counts
