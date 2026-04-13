"""
Tests for ai_advisor.py.

All Gemini API calls are mocked — no real network requests are made.
The FakeQuotaError subclasses ClientError so it is caught by the
`except ClientError` blocks in ai_advisor.py and triggers the
"QUOTA_EXHAUSTED" sentinel path.
"""
import json
import os
from unittest.mock import patch, MagicMock

import pytest
from google.genai.errors import ClientError

from ai_advisor import (
    _validate_suggestion,
    _build_owner_context,
    suggest_tasks_for_pet,
    analyze_schedule,
    chat_with_advisor,
)
from pawpal_system import Owner, Pet, Task


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_owner_with_pet():
    owner = Owner(name="Kabir", available_minutes=60, preferences=[])
    luna = Pet(name="Luna", species="Dog", age=3, needs=[])
    luna.add_task(Task("Morning walk", 30, "high", "daily", "walk", ""))
    owner.add_pet(luna)
    return owner


def valid_task_dict(**overrides):
    base = {
        "description": "Morning walk",
        "duration_minutes": 30,
        "priority": "high",
        "frequency": "daily",
        "category": "walk",
        "notes": "",
    }
    base.update(overrides)
    return base


class FakeQuotaError(ClientError):
    """Simulates a 429 RESOURCE_EXHAUSTED ClientError without hitting the API."""
    def __init__(self):
        pass  # skip parent __init__; we only need isinstance + __str__

    def __str__(self):
        return "429 RESOURCE_EXHAUSTED. quota exceeded for free tier"


# ── _validate_suggestion ──────────────────────────────────────────────────────

def test_validate_suggestion_valid():
    assert _validate_suggestion(valid_task_dict()) is True


def test_validate_suggestion_missing_key():
    d = valid_task_dict()
    del d["notes"]
    assert _validate_suggestion(d) is False


def test_validate_suggestion_invalid_priority():
    assert _validate_suggestion(valid_task_dict(priority="urgent")) is False


def test_validate_suggestion_invalid_frequency():
    assert _validate_suggestion(valid_task_dict(frequency="hourly")) is False


def test_validate_suggestion_invalid_category():
    assert _validate_suggestion(valid_task_dict(category="general")) is False


def test_validate_suggestion_duration_too_short():
    assert _validate_suggestion(valid_task_dict(duration_minutes=0)) is False


def test_validate_suggestion_duration_too_long():
    assert _validate_suggestion(valid_task_dict(duration_minutes=300)) is False


# ── _build_owner_context ──────────────────────────────────────────────────────

def test_build_context_includes_pet_name_and_species():
    ctx = _build_owner_context(make_owner_with_pet())
    assert "Luna" in ctx
    assert "Dog" in ctx


def test_build_context_includes_task_description():
    ctx = _build_owner_context(make_owner_with_pet())
    assert "Morning walk" in ctx


def test_build_context_no_tasks_message():
    owner = Owner(name="Test", available_minutes=30, preferences=[])
    owner.add_pet(Pet(name="Mochi", species="Cat", age=2, needs=[]))
    ctx = _build_owner_context(owner)
    assert "No tasks yet" in ctx


def test_build_context_includes_time_budget():
    ctx = _build_owner_context(make_owner_with_pet())
    assert "60 min" in ctx


# ── suggest_tasks_for_pet ─────────────────────────────────────────────────────

@patch("ai_advisor.genai.Client")
def test_suggest_tasks_returns_valid_list(mock_cls):
    mock_cls.return_value.models.generate_content.return_value = MagicMock(
        text=json.dumps([valid_task_dict()])
    )
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert len(result) == 1
    assert result[0]["description"] == "Morning walk"


@patch("ai_advisor.genai.Client")
def test_suggest_tasks_strips_markdown_fences(mock_cls):
    fenced = "```json\n" + json.dumps([valid_task_dict()]) + "\n```"
    mock_cls.return_value.models.generate_content.return_value = MagicMock(text=fenced)
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert len(result) == 1


@patch("ai_advisor.genai.Client")
def test_suggest_tasks_drops_invalid_entries(mock_cls):
    good = valid_task_dict()
    bad = valid_task_dict(priority="urgent")  # invalid
    mock_cls.return_value.models.generate_content.return_value = MagicMock(
        text=json.dumps([good, bad])
    )
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert len(result) == 1


@patch("ai_advisor.genai.Client")
def test_suggest_tasks_malformed_json_returns_empty(mock_cls):
    mock_cls.return_value.models.generate_content.return_value = MagicMock(
        text="not valid json {"
    )
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert result == []


@patch("ai_advisor.genai.Client")
def test_suggest_tasks_quota_exhausted_returns_sentinel(mock_cls):
    mock_cls.return_value.models.generate_content.side_effect = FakeQuotaError()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert result == "QUOTA_EXHAUSTED"


def test_suggest_tasks_missing_api_key_returns_empty():
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        result = suggest_tasks_for_pet("Luna", "dog", 3)
    assert result == []


# ── analyze_schedule ──────────────────────────────────────────────────────────

@patch("ai_advisor.genai.Client")
def test_analyze_schedule_returns_markdown_string(mock_cls):
    mock_cls.return_value.models.generate_content.return_value = MagicMock(
        text="## Analysis\n- Good coverage overall."
    )
    owner = make_owner_with_pet()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = analyze_schedule(owner, owner.get_all_tasks(), [])
    assert isinstance(result, str)
    assert "Analysis" in result


@patch("ai_advisor.genai.Client")
def test_analyze_schedule_quota_exhausted(mock_cls):
    mock_cls.return_value.models.generate_content.side_effect = FakeQuotaError()
    owner = make_owner_with_pet()
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = analyze_schedule(owner, [], [])
    assert result == "QUOTA_EXHAUSTED"


def test_analyze_schedule_missing_api_key():
    owner = make_owner_with_pet()
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        result = analyze_schedule(owner, [], [])
    assert "unavailable" in result.lower()


# ── chat_with_advisor ─────────────────────────────────────────────────────────

@patch("ai_advisor.genai.Client")
def test_chat_returns_reply_string(mock_cls):
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = MagicMock(text="Luna needs more enrichment.")
    mock_cls.return_value.chats.create.return_value = mock_chat

    owner = make_owner_with_pet()
    history = [{"role": "user", "content": "What does Luna need?"}]
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = chat_with_advisor(owner, history, "What does Luna need?")
    assert "Luna" in result


@patch("ai_advisor.genai.Client")
def test_chat_quota_exhausted_returns_sentinel(mock_cls):
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = FakeQuotaError()
    mock_cls.return_value.chats.create.return_value = mock_chat

    owner = make_owner_with_pet()
    history = [{"role": "user", "content": "Hello"}]
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        result = chat_with_advisor(owner, history, "Hello")
    assert result == "QUOTA_EXHAUSTED"


@patch("ai_advisor.genai.Client")
def test_chat_truncates_history_over_20(mock_cls):
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = MagicMock(text="OK")
    mock_cls.return_value.chats.create.return_value = mock_chat

    owner = make_owner_with_pet()
    # 26 messages total (25 prior + 1 current user message at end)
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
        for i in range(26)
    ]
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        chat_with_advisor(owner, history, "new message")

    passed_history = mock_cls.return_value.chats.create.call_args.kwargs["history"]
    assert len(passed_history) <= 20


def test_chat_missing_api_key_returns_fallback():
    owner = make_owner_with_pet()
    history = [{"role": "user", "content": "Hello"}]
    with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
        result = chat_with_advisor(owner, history, "Hello")
    assert "GEMINI_API_KEY" in result
