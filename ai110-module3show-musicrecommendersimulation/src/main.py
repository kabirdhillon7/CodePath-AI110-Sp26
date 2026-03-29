"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 
    print(f"Loaded {len(songs)} songs from the dataset."
          )
    # Taste profiles: three distinct listener personas
    profiles = {
        "High-Energy Pop": {
            "favorite_genre": "pop",
            "favorite_mood": "happy",
            "target_energy": 0.9,
            "target_valence": 0.85,
            "target_danceability": 0.85,
            "target_tempo_bpm": 128.0,
            "likes_acoustic": False,
        },
        "Chill Lofi": {
            "favorite_genre": "lo-fi",
            "favorite_mood": "calm",
            "target_energy": 0.25,
            "target_valence": 0.5,
            "target_danceability": 0.3,
            "target_tempo_bpm": 75.0,
            "likes_acoustic": True,
        },
        "Deep Intense Rock": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 0.95,
            "target_valence": 0.3,
            "target_danceability": 0.4,
            "target_tempo_bpm": 150.0,
            "likes_acoustic": False,
        },
        # Edge case: contradictory signals — maximum energy but also prefers acoustic.
        # High-energy songs are rarely acoustic, so this tests how the scorer
        # balances two opposing preferences with no clear winner.
        "Acoustic Headbanger": {
            "favorite_genre": "rock",
            "favorite_mood": "intense",
            "target_energy": 1.0,
            "target_valence": 0.4,
            "target_danceability": 0.5,
            "target_tempo_bpm": 160.0,
            "likes_acoustic": True,
        },
    }

    divider = "=" * 44
    for profile_name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print(f"\n{'#' * 44}")
        print(f"  Profile: {profile_name}")
        print(f"{'#' * 44}")
        print("\nTop recommendations:\n")
        for rank, (song, score, reasons) in enumerate(recommendations, start=1):
            print(divider)
            print(f"  #{rank}  {song['title']}")
            print(f"       Score: {score:.2f} / 10.00")
            print("  " + "-" * 40)
            for reason in reasons:
                print(f"    * {reason}")
        print(divider)


if __name__ == "__main__":
    main()
