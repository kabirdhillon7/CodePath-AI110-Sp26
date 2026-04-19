from bughound_agent import BugHoundAgent
from llm_client import MockClient


def test_workflow_runs_in_offline_mode_and_returns_shape():
    agent = BugHoundAgent(client=None)  # heuristic-only
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert isinstance(result, dict)
    assert "issues" in result
    assert "fixed_code" in result
    assert "risk" in result
    assert "logs" in result

    assert isinstance(result["issues"], list)
    assert isinstance(result["fixed_code"], str)
    assert isinstance(result["risk"], dict)
    assert isinstance(result["logs"], list)
    assert len(result["logs"]) > 0


def test_offline_mode_detects_print_issue():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])


def test_offline_mode_proposes_logging_fix_for_print():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    fixed = result["fixed_code"]
    assert "logging" in fixed
    assert "logging.info(" in fixed


def test_mock_client_forces_llm_fallback_to_heuristics_for_analysis():
    # MockClient returns non-JSON for analyzer prompts, so agent should fall back.
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])
    # Ensure we logged the fallback path
    assert any("Falling back to heuristics" in entry.get("message", "") for entry in result["logs"])


class ProseFixer(MockClient):
    """MockClient variant whose fixer returns English prose instead of Python code."""

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if "Return ONLY valid JSON" in system_prompt:
            return super().complete(system_prompt, user_prompt)
        return "The code looks fine.\nMinor style note: remove print statements."


def test_prose_fix_is_blocked_by_format_guardrail():
    # Failure mode: LLM returns English prose instead of Python code.
    # With only a low-severity issue and same-length prose output, the old assessor
    # scored this 95 and set should_autofix=True — applying a sentence as code.
    # The format guardrail (-40 for no Python syntax in fixed code) must block it.
    agent = BugHoundAgent(client=ProseFixer())
    code = "print('hello')\nprint('world')\n"

    result = agent.run(code)

    assert result["risk"]["should_autofix"] is False
    assert result["risk"]["level"] != "low"
    assert any("format failure" in r.lower() for r in result["risk"]["reasons"])
