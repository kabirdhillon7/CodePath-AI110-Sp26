"""
Shared data for the Mood Machine lab.

This file defines:
  - POSITIVE_WORDS: starter list of positive words
  - NEGATIVE_WORDS: starter list of negative words
  - SAMPLE_POSTS: short example posts for evaluation and training
  - TRUE_LABELS: human labels for each post in SAMPLE_POSTS
"""

# ---------------------------------------------------------------------
# Starter word lists
# ---------------------------------------------------------------------

POSITIVE_WORDS = [
    "happy",
    "great",
    "good",
    "love",
    "excited",
    "awesome",
    "fun",
    "chill",
    "relaxed",
    "amazing",
]

NEGATIVE_WORDS = [
    "sad",
    "bad",
    "terrible",
    "awful",
    "angry",
    "upset",
    "tired",
    "stressed",
    "hate",
    "boring",
]

# ---------------------------------------------------------------------
# Starter labeled dataset
# ---------------------------------------------------------------------

# Short example posts written as if they were social media updates or messages.
SAMPLE_POSTS = [
    "I love this class so much",
    "Today was a terrible day",
    "Feeling tired but kind of hopeful",
    "This is fine",
    "So excited for the weekend",
    "I am not happy about this",
    "Lowkey stressed but kind of proud of myself",
    "No cap this was the best meal I've ever had 😂",
    "I absolutely love getting stuck in traffic 💀",
    "Today is okay I guess",
    "Highkey obsessed with this new album 🥲",
    "Just woke up :) but already tired :(",
    "Everything is fine. Totally fine. Nothing is wrong.",
    "Meh",
    # --- Breaker sentences: designed to confuse the rule-based model ---
    "I love getting stuck in traffic",           # sarcasm: "love" fires positive
    "Wow amazing, my flight got cancelled",      # sarcasm: "amazing" fires positive
    "That movie was absolutely sick!",           # slang: "sick" = cool, not in word list
    "This beat is fire 🔥",                      # slang + emoji not in signal_scores
    "I'm fine 🙂",                               # passive-aggressive: 🙂 not scored
    "I hate that I love this show",              # cancel-out: hate(−2) + love(+2) = 0
    "I'm exhausted but proud of what I did today",  # vocab gap: neither word in lists
]

# Human labels for each post above.
# Allowed labels in the starter:
#   - "positive"
#   - "negative"
#   - "neutral"
#   - "mixed"
TRUE_LABELS = [
    "positive",  # "I love this class so much"
    "negative",  # "Today was a terrible day"
    "mixed",     # "Feeling tired but kind of hopeful"
    "neutral",   # "This is fine"
    "positive",  # "So excited for the weekend"
    "negative",  # "I am not happy about this"
    "mixed",     # "Lowkey stressed but kind of proud of myself"
    "positive",  # "No cap this was the best meal I've ever had 😂"
    "negative",  # "I absolutely love getting stuck in traffic 💀" (sarcasm)
    "neutral",   # "Today is okay I guess"
    "positive",  # "Highkey obsessed with this new album 🥲" (edge case: 🥲 is ambiguous)
    "mixed",     # "Just woke up :) but already tired :("
    "negative",  # "Everything is fine. Totally fine. Nothing is wrong." (sarcasm)
    "neutral",   # "Meh"
    # --- Breaker sentence labels ---
    "negative",  # "I love getting stuck in traffic"  (model predicts: positive)
    "negative",  # "Wow amazing, my flight got cancelled"  (model predicts: positive)
    "positive",  # "That movie was absolutely sick!"  (model predicts: neutral)
    "positive",  # "This beat is fire 🔥"  (model predicts: neutral)
    "negative",  # "I'm fine 🙂"  (model predicts: neutral)
    "mixed",     # "I hate that I love this show"  (model predicts: neutral)
    "mixed",     # "I'm exhausted but proud of what I did today"  (model predicts: neutral)
]

# TODO: Add 5-10 more posts and labels.
# NOTE: Added 8 posts above covering slang, emojis, sarcasm, and ambiguous feelings.
#
# Requirements:
#   - For every new post you add to SAMPLE_POSTS, you must add one
#     matching label to TRUE_LABELS.
#   - SAMPLE_POSTS and TRUE_LABELS must always have the same length.
#   - Include a variety of language styles, such as:
#       * Slang ("lowkey", "highkey", "no cap")
#       * Emojis (":)", ":(", "🥲", "😂", "💀")
#       * Sarcasm ("I absolutely love getting stuck in traffic")
#       * Ambiguous or mixed feelings
#
# Tips:
#   - Try to create some examples that are hard to label even for you.
#   - Make a note of any examples that you and a friend might disagree on.
#     Those "edge cases" are interesting to inspect for both the rule based
#     and ML models.
#
# Example of how you might extend the lists:
#
# SAMPLE_POSTS.append("Lowkey stressed but kind of proud of myself")
# TRUE_LABELS.append("mixed")
#
# Remember to keep them aligned:
#   len(SAMPLE_POSTS) == len(TRUE_LABELS)
