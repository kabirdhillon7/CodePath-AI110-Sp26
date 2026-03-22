# Model Card: Mood Machine

This model card is for the Mood Machine project, which includes **two** versions of a mood classifier:

1. A **rule based model** implemented in `mood_analyzer.py`
2. A **machine learning model** implemented in `ml_experiments.py` using scikit learn

---

## 1. Model Overview

**Model type:**
Both models were built and compared. The rule-based model was developed first and used as a baseline. The ML model was then trained on the same dataset to see how the two approaches differ.

**Intended purpose:**
Classify short social media-style text messages into one of four mood labels: `positive`, `negative`, `neutral`, or `mixed`. The input is a single sentence or short post; the output is a single label.

**How it works (brief):**
- *Rule-based:* Text is preprocessed (lowercased, punctuation stripped, text emoticons extracted, repeated characters normalized), then scored by looking up tokens against positive and negative word lists. Words carry weights (1 or 2), negation words flip the next word's contribution, and emoji/slang tokens map to fixed score deltas. The final score is mapped to a label using thresholds, with a special case that detects conflicting signals (both positive and negative fired) to return "mixed" even when they cancel to zero.
- *ML model:* Each post is converted to a bag-of-words vector using `CountVectorizer`, then a `LogisticRegression` classifier is trained to predict the label directly from word frequencies, with no hand-crafted rules.

---

## 2. Data

**Dataset description:**
The dataset (`SAMPLE_POSTS` and `TRUE_LABELS` in `dataset.py`) contains 21 labeled posts built in three stages:
- 6 starter examples provided with the lab
- 8 extended examples added to cover a range of language styles (slang, emojis, sarcasm, mixed feelings)
- 7 "breaker" sentences specifically designed to expose model weaknesses (sarcasm with positive words, slang, ambiguous emoji, cancel-out sentiment)

**Labeling process:**
Labels were assigned by human judgment using the four allowed categories. Several posts were genuinely difficult to label:
- `"Highkey obsessed with this new album 🥲"` — labeled `positive` (enthusiasm outweighs the ambiguous emoji), but a case could be made for `mixed`
- `"I'm fine 🙂"` — labeled `negative` in context (passive-aggressive tone) but could reasonably be `neutral`
- `"I hate that I love this show"` — labeled `mixed`; both emotions are genuinely present

**Important characteristics of your dataset:**
- Contains internet slang ("lowkey", "highkey", "no cap", "sick", "fire", "lit")
- Includes unicode emoji (😂, 💀, 🥲, 🔥) and text emoticons (:), :()
- Includes sarcasm ("I love getting stuck in traffic", "Everything is fine. Totally fine.")
- Several posts express mixed or conflicting feelings
- Includes very short/minimal posts ("Meh", "This is fine")

**Possible issues with the dataset:**
- Only 21 examples — far too small for reliable generalization
- Label distribution is uneven: more `negative` and `mixed` than `positive` or `neutral`
- Sarcasm requires knowing the author's intent; labels reflect one interpretation
- All posts are in English; the model will perform poorly on other languages

---

## 3. How the Rule Based Model Works (if used)

**Your scoring rules:**
- **Word lists:** Tokens are matched against `POSITIVE_WORDS` and `NEGATIVE_WORDS` sets. Matches add or subtract from a running score.
- **Word weights:** Stronger words ("love", "hate", "amazing", "terrible") carry a weight of 2; all other words carry a weight of 1.
- **Negation:** The words "not", "never", and "no" set a negation flag that flips the contribution of the next sentiment word (e.g., "not happy" scores −1 instead of +1).
- **Emoji and slang signals:** Tokens like `:)`, `:(`, `😂`, `💀`, `🔥`, `sick`, and `fire` map directly to fixed score deltas (ranging from −2 to +2), bypassing the word list lookup.
- **Frequency:** Every occurrence of a sentiment word is counted, so "hate hate hate" scores −6.
- **Label thresholds:** `score ≥ 2` → `"positive"`, `score ≤ −2` → `"negative"`, `score == 0` with both positive and negative signals → `"mixed"`, `score == 0` with no signals → `"neutral"`, `score == ±1` → `"mixed"`.

**Strengths of this approach:**
- Fully transparent — every prediction can be explained by tracing which tokens fired
- Fast and requires no training data
- Handles repeated emphasis ("soooo good") through character normalization
- Correctly catches simple negation ("not bad" → positive)

**Weaknesses of this approach:**
- Cannot detect sarcasm ("I love getting stuck in traffic" still scores positive from "love")
- Relies entirely on vocabulary coverage — unknown slang scores as neutral until manually added
- Negation only applies to the immediately following sentiment word; multi-word negation fails
- Passive-aggressive or context-dependent emoji ("🙂" as dismissive) are indistinguishable from genuine positivity

---

## 4. How the ML Model Works (if used)

**Features used:**
Bag-of-words vectors produced by `CountVectorizer`. Each post is represented as a vector of word counts across the full vocabulary of the training set. No special handling for emoji, slang, or word order.

**Training data:**
The model trains on all 21 entries in `SAMPLE_POSTS` and `TRUE_LABELS` from `dataset.py`.

**Training behavior:**
The model achieved 100% accuracy on the training set. This is expected — with only 21 examples and a flexible logistic regression classifier, the model can memorize each post without learning generalizable patterns. Adding more labeled examples would increase the chance that it learns real signals rather than memorizing specific posts.

**Strengths and weaknesses:**
- *Strengths:* Learns patterns automatically from labels without hand-crafted rules. Correctly classifies sarcasm examples because it saw them labeled during training. Can pick up multi-word patterns that word-list models miss.
- *Weaknesses:* 100% training accuracy is a sign of overfitting — the model has essentially memorized the 21 posts rather than learned transferable mood signals. It will likely fail on novel phrasing not seen during training. The bag-of-words representation loses word order and context, so "I hate that I love this show" and "I love that I hate this show" would be treated identically.

---

## 5. Evaluation

**How you evaluated the model:**
Both models were evaluated on the same 21 labeled posts in `dataset.py`. This is training-set evaluation only — there is no held-out test set.

- Rule-based accuracy: **9 / 21 (43%)**
- ML model accuracy: **21 / 21 (100%)** — but this is training accuracy and reflects memorization

**Examples of correct predictions (rule-based):**
- `"I love this class so much"` → `positive` — "love" has weight 2, clear positive signal, no conflicting words
- `"Today was a terrible day"` → `negative` — "terrible" has weight 2, no conflicting signal
- `"Just woke up :) but already tired :("` → `mixed` — `:)` scores +2, `:(` scores −2, both signals fired → conflict detected as mixed

**Examples of incorrect predictions (rule-based):**
- `"I love getting stuck in traffic"` → predicted `mixed`, true `negative` — sarcasm is undetectable; "love" fires positive and "stuck" fires negative, so the model at least hedges with "mixed" rather than confidently saying "positive"
- `"No cap this was the best meal I've ever had 😂"` → predicted `neutral`, true `positive` — "no" triggers negation, then "cap" is not a sentiment word so the negation is wasted; 😂 adds +1 but "best" is not in the word list, leaving only a score of +1 → "mixed" rather than "positive"
- `"I'm fine 🙂"` → predicted `neutral`, true `negative` — passive-aggressive tone is invisible to the rule system; neither "fine" nor 🙂 triggers any signal

---

## 6. Limitations

- **Tiny dataset:** 21 examples is far too small to train or validate a reliable sentiment classifier. The ML model's 100% accuracy reflects memorization, not generalization.
- **No test set:** Both models are evaluated on the same data they were developed on (or trained on). Real accuracy on unseen text is unknown.
- **Sarcasm blindspot:** Neither model reliably handles sarcasm. The rule-based model improved from predicting "positive" to "mixed" for sarcastic sentences after adding context words, but cannot reach the correct "negative" label without sentence-level understanding.
- **Vocabulary coverage:** The rule-based model only recognizes sentiment in words that were manually added to the word lists or signal map. Any slang, dialect, or domain-specific vocabulary not in those lists is ignored.
- **Language and demographic bias:** All posts are in informal American English. The model has not been tested on formal writing, other dialects, or other languages.
- **Short-text only:** The scoring and vectorization approaches used here are not designed for longer documents where sentiment may shift across paragraphs.

---

## 7. Ethical Considerations

- **Misclassifying distress:** A message expressing genuine distress in understated language ("I'm fine 🙂", "everything is fine") may be labeled neutral or positive. In any application where mood detection is used to identify users who need support, this false negative could have serious consequences.
- **Slang and dialect bias:** The word lists and signal scores were built with a specific set of slang in mind. Language communities using different slang, code-switching, or non-standard spelling may be systematically misclassified — their positive expressions might score neutral, or vice versa.
- **Overfitting to labeled assumptions:** The human labels in this dataset reflect one person's interpretation of ambiguous posts (e.g., "I'm fine 🙂" as passive-aggressive). Deploying a model trained on these labels encodes those interpretations as ground truth, which may not match how the author intended the message.
- **Privacy:** Mood classification inherently involves analyzing personal communications. If applied at scale to real messages, users may not be aware their words are being analyzed and categorized.

---

## 8. Ideas for Improvement

- **More labeled data:** Even 200–500 diverse labeled examples would significantly improve the ML model's generalization and make training/test splits feasible.
- **Real train/test split:** Hold out 20–30% of the dataset for testing so accuracy reflects performance on unseen examples rather than training memorization.
- **TF-IDF instead of CountVectorizer:** Down-weighting common words (like "I", "the") and up-weighting rare but informative words would give the ML model better features.
- **Better slang and emoji coverage:** Expand the signal dictionary in `mood_analyzer.py` and consider pulling from an existing sentiment lexicon (e.g., VADER) rather than maintaining the list manually.
- **Sarcasm detection:** A simple heuristic could flag sentences where a strong positive word appears alongside a clearly negative outcome phrase ("love + cancelled", "amazing + stuck"). A more robust approach would use a pre-trained language model fine-tuned on sarcasm data.
- **Small neural network or transformer:** A model like a fine-tuned DistilBERT can capture context, word order, and tone in ways that bag-of-words and rule-based systems cannot, and has been pre-trained on billions of examples of natural language.
- **Confidence scores:** Instead of a single label, outputting a probability distribution over labels would let downstream systems handle uncertainty more gracefully (e.g., flagging "mixed" predictions for human review).
