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
    # Taste profile: target values for all song features
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.75,
        "target_danceability": 0.7,
        "target_tempo_bpm": 120.0,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    divider = "=" * 44
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
