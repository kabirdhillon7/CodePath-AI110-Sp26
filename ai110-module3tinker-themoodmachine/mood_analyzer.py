# mood_analyzer.py
"""
Rule based mood analyzer for short text snippets.

This class starts with very simple logic:
  - Preprocess the text
  - Look for positive and negative words
  - Compute a numeric score
  - Convert that score into a mood label
"""

import re
from typing import List, Dict, Tuple, Optional

from dataset import POSITIVE_WORDS, NEGATIVE_WORDS


class MoodAnalyzer:
    """
    A very simple, rule based mood classifier.
    """

    def __init__(
        self,
        positive_words: Optional[List[str]] = None,
        negative_words: Optional[List[str]] = None,
    ) -> None:
        # Use the default lists from dataset.py if none are provided.
        positive_words = positive_words if positive_words is not None else POSITIVE_WORDS
        negative_words = negative_words if negative_words is not None else NEGATIVE_WORDS

        # Store as sets for faster lookup.
        self.positive_words = set(w.lower() for w in positive_words)
        self.negative_words = set(w.lower() for w in negative_words)

        # Words that carry stronger sentiment get a weight of 2; others default to 1.
        self.positive_weights = {"love": 2, "amazing": 2, "awesome": 2, "excited": 2}
        self.negative_weights = {"hate": 2, "terrible": 2, "awful": 2, "angry": 2}

        # Emoji and slang tokens mapped directly to score deltas.
        self.signal_scores = {
            ":)": 2,  ":d": 2,  ":p": 1,
            ":(": -2, ":-(": -2,
            "😂": 1,  "🥲": -1, "💀": -2,
            "lol": 1,
            "sick": 2, "fire": 2, "lit": 1,  # slang positives
            "🔥": 2,                           # fire emoji
        }

    # ---------------------------------------------------------------------
    # Preprocessing
    # ---------------------------------------------------------------------

    def preprocess(self, text: str) -> List[str]:
        """
        Convert raw text into a list of tokens the model can work with.

        TODO: Improve this method.

        Right now, it does the minimum:
          - Strips leading and trailing whitespace
          - Converts everything to lowercase
          - Splits on spaces

        Ideas to improve:
          - Remove punctuation
          - Handle simple emojis separately (":)", ":-(", "🥲", "😂")
          - Normalize repeated characters ("soooo" -> "soo")
        """
        text = text.strip().lower()

        # 1. Extract text emoticons before punctuation removal (e.g. ":)", ":-(")
        emoticon_pattern = r'[:;=8][-o*]?[)\](\[dDpP/\\:}{@|]'
        emoticons = re.findall(emoticon_pattern, text)
        text = re.sub(emoticon_pattern, ' ', text)

        # 2. Remove remaining punctuation so "love," matches "love"
        text = re.sub(r'[^\w\s]', ' ', text)

        # 3. Split and normalize repeated characters ("soooo" -> "soo")
        tokens = text.split()
        tokens = [re.sub(r'(.)\1{2,}', r'\1\1', t) for t in tokens]

        # 4. Re-add emoticons as their own tokens
        tokens += emoticons

        print(f"[preprocess] tokens: {tokens}")
        return tokens

    # ---------------------------------------------------------------------
    # Scoring logic
    # ---------------------------------------------------------------------

    def _compute_score(self, tokens: List[str]) -> Tuple[int, bool, bool]:
        """
        Core scoring logic shared by score_text and predict_label.

        Returns (score, has_positive, has_negative) so callers can detect
        conflicting signals (both positive and negative fired) even when
        they cancel out to a net score of zero.
        """
        score = 0
        has_positive = False
        has_negative = False
        negation_words = {"not", "never", "no"}
        negated = False

        for token in tokens:
            # Emoji/slang — strong fixed signals, not affected by negation
            if token in self.signal_scores:
                delta = self.signal_scores[token]
                score += delta
                if delta > 0:
                    has_positive = True
                if delta < 0:
                    has_negative = True
                negated = False
                continue

            # Negation — set flag, consume on next sentiment word
            if token in negation_words:
                negated = True
                continue

            # Word weights — strong words count more than weak ones
            weight = 0
            if token in self.positive_words:
                weight += self.positive_weights.get(token, 1)
            if token in self.negative_words:
                weight -= self.negative_weights.get(token, 1)

            # Flip contribution if negated
            if negated and weight != 0:
                weight = -weight
                negated = False  # consume negation after first sentiment word

            # Frequency — each occurrence of a word is counted
            if weight > 0:
                has_positive = True
            if weight < 0:
                has_negative = True
            score += weight

        return score, has_positive, has_negative

    def score_text(self, text: str) -> int:
        """
        Compute a numeric "mood score" for the given text.

        Positive words increase the score.
        Negative words decrease the score.
        """
        tokens = self.preprocess(text)
        score, _, _ = self._compute_score(tokens)
        return score

    # ---------------------------------------------------------------------
    # Label prediction
    # ---------------------------------------------------------------------

    def predict_label(self, text: str) -> str:
        """
        Turn the numeric score for a piece of text into a mood label.

        The default mapping is:
          - score > 0  -> "positive"
          - score < 0  -> "negative"
          - score == 0 -> "neutral"

        TODO: You can adjust this mapping if it makes sense for your model.
        For example:
          - Use different thresholds (for example score >= 2 to be "positive")
          - Add a "mixed" label for scores close to zero
        Just remember that whatever labels you return should match the labels
        you use in TRUE_LABELS in dataset.py if you care about accuracy.
        """
        tokens = self.preprocess(text)
        score, has_positive, has_negative = self._compute_score(tokens)

        if score >= 2:
            return "positive"
        if score <= -2:
            return "negative"
        if score == 0:
            # Both sides fired and cancelled out → conflicting sentiment, not neutral
            if has_positive and has_negative:
                return "mixed"
            return "neutral"
        return "mixed"  # score == +1 or -1: weak or conflicting signals

    # ---------------------------------------------------------------------
    # Explanations (optional but recommended)
    # ---------------------------------------------------------------------

    def explain(self, text: str) -> str:
        """
        Return a short string explaining WHY the model chose its label.

        TODO:
          - Look at the tokens and identify which ones counted as positive
            and which ones counted as negative.
          - Show the final score.
          - Return a short human readable explanation.

        Example explanation (your exact wording can be different):
          'Score = 2 (positive words: ["love", "great"]; negative words: [])'

        The current implementation is a placeholder so the code runs even
        before you implement it.
        """
        tokens = self.preprocess(text)

        positive_hits: List[str] = []
        negative_hits: List[str] = []
        score = 0

        for token in tokens:
            if token in self.positive_words:
                positive_hits.append(token)
                score += 1
            if token in self.negative_words:
                negative_hits.append(token)
                score -= 1

        return (
            f"Score = {score} "
            f"(positive: {positive_hits or '[]'}, "
            f"negative: {negative_hits or '[]'})"
        )
