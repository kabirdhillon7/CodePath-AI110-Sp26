import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            songs.append(row)
    return songs

def score_song(user_prefs: UserProfile, song: Song) -> Tuple[float, List[str]]:
    """
    Scores a single song against a user's preferences.

    Point budget (max 10.0):
      mood match   → +4.0        (40% — primary intent signal)
      genre match  → +2.5        (25% — taste identity)
      energy fit   → up to +2.5  (25% — proximity to target_energy)
      acoustic fit → up to +1.0  (10% — tiebreaker)

    Returns:
        score   — float in [0.0, 10.0]
        reasons — list of strings explaining each point contribution
    """
    score = 0.0
    reasons = []

    # Mood match (+4.0) — categorical, all-or-nothing
    if song.mood == user_prefs.favorite_mood:
        score += 4.0
        reasons.append("mood match (+4.0)")

    # Genre match (+2.5) — categorical, all-or-nothing
    if song.genre == user_prefs.favorite_genre:
        score += 2.5
        reasons.append("genre match (+2.5)")

    # Energy fit (up to +2.5) — rewards closeness to target_energy
    # proximity = 1.0 when perfect match, 0.0 when furthest away
    energy_proximity = 1.0 - abs(song.energy - user_prefs.target_energy)
    energy_points = round(2.5 * energy_proximity, 2)
    score += energy_points
    reasons.append(f"energy fit (+{energy_points})")

    # Acoustic fit (up to +1.0) — uses song.acousticness directly if user
    # likes acoustic; inverts it if they prefer electronic/produced sound
    acoustic_raw = song.acousticness if user_prefs.likes_acoustic else 1.0 - song.acousticness
    acoustic_points = round(1.0 * acoustic_raw, 2)
    score += acoustic_points
    reasons.append(f"acoustic fit (+{acoustic_points})")

    return round(score, 2), reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Scores every song in the catalog using score_song, then returns the
    top k results sorted from highest to lowest score.

    Return format: list of (song_dict, score, explanation) tuples.
    """
    user = UserProfile(
        favorite_genre=user_prefs["favorite_genre"],
        favorite_mood=user_prefs["favorite_mood"],
        target_energy=user_prefs["target_energy"],
        likes_acoustic=user_prefs["likes_acoustic"],
    )

    def _score(song_dict: Dict) -> Tuple[Dict, float, str]:
        song = Song(
            id=song_dict["id"],
            title=song_dict["title"],
            artist=song_dict["artist"],
            genre=song_dict["genre"],
            mood=song_dict["mood"],
            energy=song_dict["energy"],
            tempo_bpm=song_dict["tempo_bpm"],
            valence=song_dict["valence"],
            danceability=song_dict["danceability"],
            acousticness=song_dict["acousticness"],
        )
        points, reasons = score_song(user, song)
        return song_dict, points, ", ".join(reasons)

    ranked = sorted((_score(s) for s in songs), key=lambda x: x[1], reverse=True)
    return ranked[:k]
