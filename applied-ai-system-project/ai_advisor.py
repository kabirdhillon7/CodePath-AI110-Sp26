import os
import json
import logging
import time
from typing import TYPE_CHECKING

from google import genai
from google.genai import types
from google.genai.errors import ClientError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; key can be set via shell export

if TYPE_CHECKING:
    from pawpal_system import Owner, Task

# ── Logging setup ─────────────────────────────────────────────────────────────
_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_file_handler = logging.FileHandler("pawpal_ai.log")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_formatter)

_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(logging.WARNING)
_stream_handler.setFormatter(_formatter)

logger = logging.getLogger("ai_advisor")
logger.setLevel(logging.DEBUG)
logger.addHandler(_file_handler)
logger.addHandler(_stream_handler)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL = "gemini-2.5-flash"

_TASK_REQUIRED_KEYS = {"description", "duration_minutes", "priority", "frequency", "category", "notes"}
_VALID_PRIORITIES = {"high", "medium", "low"}
_VALID_FREQUENCIES = {"daily", "weekly", "as_needed"}
_VALID_CATEGORIES = {"walk", "feeding", "grooming", "enrichment", "meds", "other"}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_client() -> genai.Client:
    """Return a configured Gemini client. Raises EnvironmentError if key is missing."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    logger.debug("Gemini client initialized")
    return genai.Client(api_key=key)


def _build_owner_context(owner) -> str:
    """Serialize the full owner state into a compact text block for prompt injection."""
    lines = [f"Owner: {owner.name} | Daily time budget: {owner.available_minutes} min"]
    for pet in owner.pets:
        lines.append(f"\nPet: {pet.name} ({pet.species}, age {pet.age})")
        if pet.tasks:
            for t in pet.tasks:
                status = "done" if t.completed else "pending"
                note = f" — {t.notes}" if t.notes else ""
                lines.append(
                    f"  - {t.description} [{t.priority}, {t.frequency}, "
                    f"{t.duration_minutes} min, {status}]{note}"
                )
        else:
            lines.append("  - No tasks yet.")
    return "\n".join(lines)


def _validate_suggestion(item: dict) -> bool:
    """Return True if a suggestion dict has all required keys and valid enum values."""
    if not _TASK_REQUIRED_KEYS.issubset(item.keys()):
        return False
    if item["priority"] not in _VALID_PRIORITIES:
        return False
    if item["frequency"] not in _VALID_FREQUENCIES:
        return False
    if item["category"] not in _VALID_CATEGORIES:
        return False
    if not isinstance(item["duration_minutes"], int) or not (1 <= item["duration_minutes"] <= 240):
        return False
    return True


# ── Public API ────────────────────────────────────────────────────────────────

def suggest_tasks_for_pet(pet_name: str, species: str, age: int) -> list:
    """
    Ask Gemini to suggest 3-5 care tasks for a pet.

    Returns a list of dicts matching Task constructor fields, or [] on any error.
    """
    logger.info("suggest_tasks_for_pet called: pet=%s species=%s age=%d", pet_name, species, age)
    start = time.time()
    raw = ""
    try:
        client = _get_client()
        prompt = (
            f"Suggest 3-5 daily care tasks for {pet_name}, a {age}-year-old {species}. "
            "Return a JSON array where each element has exactly these keys:\n"
            "  description (string),\n"
            "  duration_minutes (integer between 5 and 240),\n"
            "  priority (one of: high, medium, low),\n"
            "  frequency (one of: daily, weekly, as_needed),\n"
            "  category (one of: walk, feeding, grooming, enrichment, meds, other),\n"
            "  notes (string, can be empty string).\n"
            "Ensure all values are realistic for home pet care."
        )
        response = client.models.generate_content(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a veterinary care assistant. "
                    "Always respond with valid JSON only — no markdown, no code fences, no explanation. "
                    "Your response must be a raw JSON array and nothing else."
                )
            ),
            contents=prompt,
        )
        raw = response.text.strip()

        # Strip accidental markdown fences if the model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0].strip()

        suggestions = json.loads(raw)
        if not isinstance(suggestions, list):
            logger.error("suggest_tasks_for_pet: expected JSON array, got %s", type(suggestions))
            return []

        valid = []
        for item in suggestions:
            if _validate_suggestion(item):
                valid.append(item)
            else:
                logger.warning("Dropping malformed suggestion: %s", item)

        logger.info(
            "suggest_tasks_for_pet returned %d suggestions in %.2fs",
            len(valid), time.time() - start,
        )
        return valid

    except EnvironmentError as e:
        logger.error("suggest_tasks_for_pet: API key error — %s", e)
        return []
    except json.JSONDecodeError:
        logger.error("suggest_tasks_for_pet: JSON parse failed. Raw (truncated): %.500s", raw)
        return []
    except ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            logger.warning("suggest_tasks_for_pet: quota exhausted (429)")
            return "QUOTA_EXHAUSTED"
        logger.exception("suggest_tasks_for_pet: API client error — %s", e)
        return []
    except Exception as e:
        logger.exception("suggest_tasks_for_pet: unexpected error — %s", e)
        return []


def analyze_schedule(owner, scheduled_tasks: list, excluded_tasks: list) -> str:
    """
    Ask Gemini to analyze today's schedule and identify care gaps.

    Returns a markdown string, or an error message string on failure.
    """
    logger.info(
        "analyze_schedule called: %d scheduled, %d excluded",
        len(scheduled_tasks), len(excluded_tasks),
    )
    start = time.time()
    try:
        client = _get_client()
        context = _build_owner_context(owner)
        scheduled_str = "\n".join(
            f"  - {t.description} ({t.duration_minutes} min, {t.priority}, {t.category})"
            for t in scheduled_tasks
        ) or "  None"
        excluded_str = "\n".join(
            f"  - {t.description} ({t.duration_minutes} min, {t.priority}, {t.category})"
            for t in excluded_tasks
        ) or "  None"

        prompt = (
            f"{context}\n\n"
            f"Scheduled tasks for today:\n{scheduled_str}\n\n"
            f"Excluded tasks (did not fit in time budget):\n{excluded_str}\n\n"
            "Analyze this schedule. Identify care gaps, highlight any high-priority excluded tasks, "
            "and give concrete, budget-aware recommendations."
        )
        response = client.models.generate_content(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a pet care advisor. Respond in markdown. "
                    "Be concise — 3-5 bullet points plus one brief summary sentence. "
                    "Before making any recommendations, verify they fit within the owner's available "
                    "time budget. Do not recommend adding tasks if the budget is already fully utilized."
                )
            ),
            contents=prompt,
        )
        logger.info("analyze_schedule completed in %.2fs", time.time() - start)
        return response.text

    except EnvironmentError as e:
        logger.error("analyze_schedule: API key error — %s", e)
        return "Analysis unavailable: GEMINI_API_KEY is not configured."
    except ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            logger.warning("analyze_schedule: quota exhausted (429)")
            return "QUOTA_EXHAUSTED"
        logger.exception("analyze_schedule: API client error — %s", e)
        return f"Analysis unavailable: {e}"
    except Exception as e:
        logger.exception("analyze_schedule: unexpected error — %s", e)
        return f"Analysis unavailable: {e}"


def chat_with_advisor(owner, conversation_history: list, user_message: str) -> str:
    """
    One turn of the pet care chat with full owner context injected.

    conversation_history is a list of {"role": "user"|"assistant", "content": str}.
    The caller should append the new user message BEFORE calling this function.
    Returns Gemini's reply string, or a fallback message on error.
    """
    logger.info("chat_with_advisor called, history length: %d", len(conversation_history))
    start = time.time()
    try:
        client = _get_client()
        context = _build_owner_context(owner)

        # Build Gemini history from all messages except the last (current user message)
        history = conversation_history[:-1]
        if len(history) > 20:
            logger.debug("Chat history truncated from %d to 20 messages", len(history))
            history = history[-20:]

        # Gemini uses "model" for the assistant role
        gemini_history = [
            types.Content(
                role="model" if msg["role"] == "assistant" else "user",
                parts=[types.Part(text=msg["content"])],
            )
            for msg in history
        ]

        chat = client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a knowledgeable, friendly pet care advisor. "
                    "You have access to the owner's current pet care setup below. "
                    "Always answer based on this specific context rather than giving generic advice. "
                    "Keep responses concise and actionable.\n\n"
                    f"Current owner context:\n{context}"
                )
            ),
            history=gemini_history,
        )
        response = chat.send_message(user_message)
        logger.info("chat_with_advisor completed in %.2fs", time.time() - start)
        return response.text

    except EnvironmentError as e:
        logger.error("chat_with_advisor: API key error — %s", e)
        return "I'm having trouble connecting — GEMINI_API_KEY is not configured."
    except ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            logger.warning("chat_with_advisor: quota exhausted (429)")
            return "QUOTA_EXHAUSTED"
        logger.exception("chat_with_advisor: API client error — %s", e)
        return "I'm having trouble connecting right now. Please try again."
    except Exception as e:
        logger.exception("chat_with_advisor: unexpected error — %s", e)
        return "I'm having trouble connecting right now. Please try again."
