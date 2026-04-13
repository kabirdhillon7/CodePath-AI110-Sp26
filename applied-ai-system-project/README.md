# PawPal+ — AI-Powered Pet Care Scheduler

**Original project:** PawPal+ (CodePath AI110 Modules 1–3)
PawPal+ was originally built as a deterministic pet care task scheduler. Given an owner's daily time budget and a list of pets with tasks (walks, feeding, grooming, enrichment, medications), the system uses a two-phase priority algorithm to generate a fair daily schedule — guaranteeing every pet gets at least one task — and explains why each task was included or excluded. It was implemented in Python with a Streamlit UI and full JSON-based state persistence.

---

## Title and Summary

**PawPal+** is a smart pet care assistant that helps busy pet owners plan daily care routines for multiple pets. It combines a rule-based scheduler with an AI Care Advisor powered by the Gemini API, so owners can get personalized task suggestions, schedule gap analysis, and natural-language answers about their pets' care — all in one place.

**Why it matters:** Most pet care apps are generic. PawPal+ knows your specific pets, their tasks, and how much time you actually have. The AI layer makes recommendations grounded in your real data, not boilerplate advice.

---

## Architecture Overview

See [`system_diagram.mmd`](system_diagram.mmd) for the full Mermaid diagram.

The system has four main layers:

1. **Streamlit UI (`app.py`)** — Two tabs: *Schedule & Tasks* (core scheduling + AI features) and *AI Care Chat* (conversational advisor).
2. **PawPal Core (`pawpal_system.py`)** — Data models (Owner, Pet, Task) and the Scheduler, which generates and explains daily plans. Fully deterministic; no AI dependency.
3. **AI Advisor (`ai_advisor.py`)** — Three AI-powered functions that call the Gemini API: task suggestion, schedule analysis, and freeform chat. All calls are logged to `pawpal_ai.log`.
4. **Persistence** — Owner/pet/task state is saved to `pawpal_state.json` on every change. AI suggestions are ephemeral (session only) until the user approves and saves them.

**Human-in-the-loop:** AI-suggested tasks are shown as checkboxes — nothing is added to the system without explicit user approval. The AI advises; the owner decides.

---

## Setup Instructions

### Prerequisites
- Python 3.9+ (3.11+ recommended to avoid deprecation warnings)
- A [Google AI Studio](https://aistudio.google.com/) API key (free tier works)

### Steps

```bash
# 1. Clone the repo and enter the project directory
git clone <repo-url>
cd applied-ai-system-project

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
cp .env.example .env
# Open .env and replace "your_key_here" with your Gemini API key

# 5. Run the app
streamlit run app.py
```

### Running tests

```bash
pytest tests/
```

> **Note on free-tier quota:** The Gemini free tier has a daily request limit. If you see a "quota exhausted" message in the app, the AI features will resume after midnight Pacific Time. The scheduler works fully without an API key.

---

## Sample Interactions

### 1. AI Task Suggester

**Input:** User adds a pet — Luna, Dog, age 3 — and clicks "Get AI Suggestions."

**AI Output (structured JSON, rendered as checkboxes):**
```
☐ Morning walk            30 min  [high, daily]     Around the neighborhood
☐ Breakfast feeding       10 min  [high, daily]     1 cup dry kibble
☐ Brush coat              20 min  [medium, weekly]  Focus on shedding areas
☐ Dental chew              5 min  [low, daily]      One chew after dinner
☐ Socialization/play      15 min  [medium, daily]   Fetch or tug-of-war
```

User checks three items and clicks "Add Selected Tasks" — only those three are saved.

---

### 2. AI Schedule Analyzer

**Input:** Owner has 60 minutes available. Schedule is generated — Luna's walk (30 min) and Mochi's wet food feeding (5 min) are scheduled. Luna's grooming (20 min) and Mochi's litter box (10 min) are excluded.

**AI Output (markdown, shown in-app):**

> **Schedule Analysis**
>
> - Both pets have at least one task scheduled — good baseline coverage.
> - **Gap:** Luna's grooming is excluded. For a 3-year-old dog, weekly grooming prevents matting; consider scheduling it tomorrow or splitting into a 10-min quick-brush today.
> - **Gap:** Mochi's litter box (10 min) was excluded despite being a daily hygiene task. Increasing the budget by 10 min would fit all tasks.
> - **Recommendation:** Raise available time to 70 min, or mark the litter box as high priority to guarantee it schedules first.

---

### 3. AI Care Chat

**Input:** User types in the chat tab: *"Is Luna's current schedule missing anything for a 3-year-old dog?"*

**AI Output:**

> Based on Luna's current tasks — morning walk, breakfast feeding, and weekly grooming — she has good coverage for exercise, nutrition, and coat care. For a 3-year-old dog, I'd also suggest:
>
> - **Dental hygiene**: Daily dental chews or a 5-minute brush session reduces tartar buildup.
> - **Mental enrichment**: Puzzle feeders or training sessions (10–15 min a few times a week) help prevent boredom behaviors in active breeds.
> - **Annual vet check**: Not a daily task, but worth adding as an `as_needed` reminder so it doesn't slip.
>
> Want me to suggest specific tasks to add for any of these?

---

## Design Decisions

**Why Gemini API?**
Gemini's free tier works without a credit card, which matters for a student project that makes many API calls during development and testing. We use the `google-genai` SDK (the current recommended package — `google-generativeai` is deprecated as of early 2025).

**Why keep the scheduler deterministic?**
The two-phase scheduling algorithm is predictable and testable — 23 unit tests cover its behavior precisely. Replacing it with AI-generated schedules would make the system less reliable and harder to debug. AI advises on top of a trustworthy base; this separation also means the app works fully without an API key.

**Why a human approval step for task suggestions?**
AI suggestions are sometimes generic or inappropriate for a specific animal. Requiring explicit checkbox selection before any task is saved keeps the owner in control and builds trust. The AI is an assistant, not an autopilot.

**Why log to a file (`pawpal_ai.log`) instead of just printing?**
Streamlit reruns the entire script on every interaction. `print()` output is ephemeral and hard to correlate across calls. A persistent log file captures every API call, response time, and error for after-the-fact debugging.

**How quota exhaustion is handled:**
Rather than crashing with a raw traceback, `ai_advisor.py` catches `ClientError` with `"RESOURCE_EXHAUSTED"` in the message and returns a sentinel value (`"QUOTA_EXHAUSTED"`). The UI checks for this sentinel and shows a human-readable message with a link to the usage dashboard — the rest of the app keeps working normally.

**Trade-off — chat history is not persisted:**
Conversation history lives in `st.session_state` and resets on page refresh. Persisting it to `pawpal_state.json` would couple unrelated concerns. Ephemeral history is the right call for a v1.

---

## Testing Summary

**Results: 43/43 tests pass** (`pytest tests/`)

| Suite | Tests | Coverage |
|---|---|---|
| `test_pawpal.py` | 23 | Scheduler, Task recurrence, Pet management, serialization |
| `test_ai_advisor.py` | 24 | Validation logic, context building, API mocking, error paths |

The AI tests use `unittest.mock` to patch `genai.Client` — no real API calls are made, so the suite runs without a key and completes in under 1 second.

**What the AI tests cover:**
- `_validate_suggestion`: 7 cases — valid input, missing key, invalid priority/frequency/category, duration out of range
- `_build_owner_context`: 4 cases — pet name/species, task description, empty pet, time budget
- `suggest_tasks_for_pet`: 6 cases — valid JSON, markdown fence stripping, dropped invalid entries, malformed JSON, quota exhaustion sentinel, missing key
- `analyze_schedule`: 3 cases — valid response, quota exhaustion, missing key
- `chat_with_advisor`: 4 cases — valid response, quota exhaustion, history truncation at 20 messages, missing key

**What didn't (and how it was fixed):**
- `google-generativeai` raised a `FutureWarning` on import — it's fully deprecated. Switched to `google-genai`, which has a different client-based API (`genai.Client`, `types.GenerateContentConfig`).
- `gemini-2.0-flash` hit the free-tier daily quota immediately. `gemini-1.5-flash` returned a 404 (not available in the v1beta API). Settled on `gemini-2.0-flash-lite`, which has its own quota bucket.
- `ClientError` has no `status_code` attribute — checking `"RESOURCE_EXHAUSTED" in str(e)` is the correct approach for this SDK version.
- Early prompts for task suggestion returned markdown-wrapped JSON (` ```json ` fences), which broke `json.loads()`. Added a fence-stripping step and tightened the system prompt.

**What I learned:**
- LLM outputs need a validation layer even when the prompt is careful. Defensive parsing makes the system resilient without being brittle.
- SDK deprecations move fast — always check the package's README before starting, not just the tutorial you find on the first search result.
- Separating AI logic into its own module (`ai_advisor.py`) made it straightforward to test the scheduler independently and keep `app.py` focused on UI.

---

## Reflection

This project changed how I think about the role of AI in software systems. The most useful thing I built wasn't the AI features themselves — it was the structure around them: the logging, the error handling, the human approval step, and the deterministic fallback. An AI feature that crashes silently or adds tasks without user consent would be worse than no AI at all.

I also learned that prompt engineering is iterative. The first version of every prompt produced output I didn't expect. Refining prompts — adding constraints, specifying output format, telling the model what *not* to do — felt a lot like writing unit tests: you're encoding your assumptions about correct behavior and checking whether the system meets them.

The biggest open question this project left me with: how do you evaluate an AI advisor's quality over time? The schedule analyzer might give subtly wrong advice that a user follows without realizing it. Building a feedback loop — even just a thumbs up/down on each analysis — would be a meaningful next step.
