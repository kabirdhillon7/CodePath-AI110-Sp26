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
    target_valence: Optional[float] = None
    target_danceability: Optional[float] = None

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked = sorted(self.songs, key=lambda song: score_song(user, song)[0], reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = score_song(user, song)
        return ", ".join(reasons)

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

    Point budget (max 10.0) — two weight distributions:

    Basic (target_valence/target_danceability absent):
      mood match   → +4.0        (40%)
      genre match  → +2.5        (25%)
      energy fit   → up to +2.5  (25%)
      acoustic fit → up to +1.0  (10%)

    Extended (both target_valence and target_danceability present):
      mood match        → +3.0   (30%)
      genre match       → +2.0   (20%)
      energy fit        → up to +1.5  (15%)
      valence fit       → up to +1.5  (15%)
      danceability fit  → up to +1.0  (10%)
      acoustic fit      → up to +1.0  (10%)

    Energy, valence, and danceability use squared proximity to
    penalise distant songs more harshly than a linear gap would.

    Returns:
        score   — float in [0.0, 10.0]
        reasons — list of strings explaining each point contribution
    """
    score = 0.0
    reasons = []

    has_valence = user_prefs.target_valence is not None
    has_dance = user_prefs.target_danceability is not None
    extended = has_valence and has_dance

    if extended:
        mood_w, genre_w, energy_w, valence_w, dance_w, acoustic_w = 3.0, 2.0, 1.5, 1.5, 1.0, 1.0
    else:
        mood_w, genre_w, energy_w, valence_w, dance_w, acoustic_w = 4.0, 2.5, 2.5, 0.0, 0.0, 1.0

    # Mood match — categorical, all-or-nothing
    if song.mood == user_prefs.favorite_mood:
        score += mood_w
        reasons.append(f"mood match (+{mood_w})")

    # Genre match — categorical, all-or-nothing
    if song.genre == user_prefs.favorite_genre:
        score += genre_w
        reasons.append(f"genre match (+{genre_w})")

    # Energy fit — squared proximity penalises distant songs more than linear
    energy_proximity = (1.0 - abs(song.energy - user_prefs.target_energy)) ** 2
    energy_points = round(energy_w * energy_proximity, 2)
    score += energy_points
    reasons.append(f"energy fit (+{energy_points})")

    # Valence fit (only when target_valence is set)
    if has_valence:
        valence_proximity = (1.0 - abs(song.valence - user_prefs.target_valence)) ** 2
        valence_points = round(valence_w * valence_proximity, 2)
        score += valence_points
        reasons.append(f"valence fit (+{valence_points})")

    # Danceability fit (only when target_danceability is set)
    if has_dance:
        dance_proximity = (1.0 - abs(song.danceability - user_prefs.target_danceability)) ** 2
        dance_points = round(dance_w * dance_proximity, 2)
        score += dance_points
        reasons.append(f"danceability fit (+{dance_points})")

    # Acoustic fit — uses song.acousticness directly if user likes acoustic;
    # inverts it if they prefer electronic/produced sound
    acoustic_raw = song.acousticness if user_prefs.likes_acoustic else 1.0 - song.acousticness
    acoustic_points = round(acoustic_w * acoustic_raw, 2)
    score += acoustic_points
    reasons.append(f"acoustic fit (+{acoustic_points})")

    return round(score, 2), reasons


def detect_contradictions(user_prefs: Dict) -> List[str]:
    """
    Checks a raw user preferences dict for conflicting signals that the
    scoring system cannot reconcile, and returns human-readable warnings.
    """
    warnings = []
    energy = user_prefs.get("target_energy", 0.0)
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    danceability = user_prefs.get("target_danceability")
    tempo = user_prefs.get("target_tempo_bpm")

    if energy > 0.8 and likes_acoustic:
        warnings.append(
            f"High target_energy ({energy:.2f}) + likes_acoustic=True: "
            "high-energy songs are rarely acoustic. Recommendations will be a compromise."
        )
    if danceability is not None and tempo is not None:
        if danceability > 0.7 and tempo < 80:
            warnings.append(
                f"High target_danceability ({danceability:.2f}) + slow target_tempo_bpm ({tempo:.0f}): "
                "danceable songs are rarely slow. Recommendations may feel off."
            )
    return warnings


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, diversity_boost: bool = False) -> List[Tuple[Dict, float, List[str]]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Scores every song in the catalog using score_song, then returns the
    top k results sorted from highest to lowest score.

    Args:
        diversity_boost: When True, re-ranks the top results so that no
            mood appears more than twice in a row, broadening exposure.

    Return format: list of (song_dict, score, explanation) tuples.
    """
    user = UserProfile(
        favorite_genre=user_prefs["favorite_genre"],
        favorite_mood=user_prefs["favorite_mood"],
        target_energy=user_prefs["target_energy"],
        likes_acoustic=user_prefs["likes_acoustic"],
        target_valence=user_prefs.get("target_valence"),
        target_danceability=user_prefs.get("target_danceability"),
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
        return song_dict, points, reasons

    ranked = sorted((_score(s) for s in songs), key=lambda x: x[1], reverse=True)

    if not diversity_boost:
        return ranked[:k]

    # Diversity re-ranking: pick the highest-scoring song that doesn't repeat
    # the same mood more than once consecutively, then fill remaining slots.
    diverse: List[Tuple[Dict, float, List[str]]] = []
    pool = list(ranked)
    while len(diverse) < k and pool:
        last_mood = diverse[-1][0]["mood"] if diverse else None
        # Find the first candidate whose mood differs from the last pick
        for i, candidate in enumerate(pool):
            if candidate[0]["mood"] != last_mood:
                diverse.append(pool.pop(i))
                break
        else:
            # All remaining songs share the last mood — just take the top one
            diverse.append(pool.pop(0))
    return diverse
