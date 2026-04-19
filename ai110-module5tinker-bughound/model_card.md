# BugHound Mini Model Card (Reflection)

---

## 1) What is this system?

**Name:** BugHound
**Purpose:** Analyze a Python snippet, propose a fix, and run reliability checks before suggesting whether the fix should be auto-applied.

**Intended users:** Students learning agentic workflows and AI reliability concepts. The system is also useful as a lightweight offline code-review assistant for developers who want a fast first pass over a snippet before committing it.

---

## 2) How does it work?

BugHound runs a five-step agentic loop on every code snippet:

1. **PLAN** — The agent logs its intent: it will scan the code and attempt a fix. No real decision-making happens here; it is a trace anchor for the log output.

2. **ANALYZE** — The agent detects issues. If a Gemini client is available (`_can_call_llm()` returns `True`), it sends the code to Gemini with a system prompt instructing it to return a JSON array of issue objects (`type`, `severity`, `msg`). If the API call fails, the response is not parseable JSON, or no client is configured, the agent falls back to `_heuristic_analyze`, which runs three regex/string checks: presence of `print(`, bare `except:`, and `TODO` comments.

3. **ACT** — The agent proposes a fix. Again, Gemini is preferred. The full original code and the JSON issue list are passed together in a single prompt asking for a minimal rewrite. If Gemini is unavailable or returns empty output, `_heuristic_fix` applies targeted regex patches: replacing `except:` with `except Exception as e:`, and replacing `print(` with `logging.info(` (adding `import logging` if missing).

4. **TEST** — `assess_risk` in `reliability/risk_assessor.py` compares the original and fixed code. It deducts points from a starting score of 100 based on issue severity, structural changes (line count, missing `return`, bare `except` removal, risky additions, and non-Python output), then assigns a risk level (low / medium / high).

5. **REFLECT** — If the risk level is "low" and the score is ≥ 85 with no high-severity issues, the agent sets `should_autofix: True`. Otherwise it recommends human review.

**Heuristics vs. Gemini:**
- Heuristics are deterministic, fast, and offline. They catch only the three patterns they were written for, and their fixes are mechanical string substitutions.
- Gemini can detect semantic issues (logic errors, missing edge-case handling, type mismatches) that heuristics cannot. Its fixes can also span multiple changes at once. However, Gemini's output format is less predictable, which is why `_strip_code_fences` and `_parse_json_array_of_issues` exist as defensive wrappers.

---

## 3) Inputs and outputs

**Inputs tested:**

| File | Shape | Notable features |
|------|-------|-----------------|
| `sample_code/cleanish.py` | 5-line module with one function | Uses `logging`, no anti-patterns |
| `sample_code/mixed_issues.py` | 9-line function with `try/except` | Contains `print`, bare `except:`, and a `TODO` comment |
| `sample_code/print_spam.py` | 8-line function | Three `print` calls, one `return True` |
| Inline: `"print('hello')\nprint('world')\n"` | 2-line script | No function definition, no `return` — used to expose format failure |
| Inline: `"# just a comment\n# nothing here\n"` | Comments only | No executable code — "weird" case |

**Outputs:**

- `cleanish.py`: no issues detected; fixed code identical to original; score 100; `should_autofix: True`.
- `mixed_issues.py`: three issues (Code Quality/Low, Reliability/High, Maintainability/Medium); heuristic fixer replaced bare `except:` and `print(`; score 20 (high risk); `should_autofix: False`.
- `print_spam.py` (heuristic mode): one Code Quality/Low issue; fixer prepended `import logging` and replaced all `print(` calls; score 75; `should_autofix: False` (score below 85 threshold).
- Comments-only input: no issues; original returned unchanged; score 100; `should_autofix: True`.
- Prose-fixer simulation: one Code Quality/Low issue; LLM "returned" English prose; score 55 after format-failure deduction (−40); `should_autofix: False`.

---

## 4) Reliability and safety rules

**Rule 1: Missing `return` penalty (−30)**

`assess_risk` checks whether `"return"` appears in the original but not in the fixed code, and deducts 30 points if so.

- *Why it matters:* A function that loses its `return` statement changes behavior silently — callers receive `None` instead of the expected value. This is one of the most dangerous silent mutations a code rewriter can make.
- *False positive:* A fix that correctly refactors a function to use an early-return pattern, or moves a `return` inside a new helper, could cause `"return"` to disappear from the top-level scope. The check is purely lexical, not structural.
- *False negative:* If the fix changes `return x` to `return None` or `return 0`, the check passes even though the return value semantics are broken.

**Rule 2: Format failure penalty (−40)**

If `ast.parse(original_code)` succeeds but `ast.parse(fixed_code)` raises `SyntaxError`, the assessor deducts 40 points and flags a possible format failure.

- *Why it matters:* A language model can return prose, markdown, or malformed code instead of valid Python. Without this check, a short snippet with only low-severity issues could receive a score of 95 and be auto-applied — replacing working code with English sentences.
- *False positive:* A deliberately broken snippet used for testing (e.g., a snippet that is itself invalid Python) would have `_is_valid_python(original_code) = False`, so the guardrail would not fire even if the fix is also invalid. The rule only applies when the original is valid.
- *False negative:* A fix that is syntactically valid Python but semantically nonsensical (e.g., a single `pass` statement replacing a 50-line module) would pass `ast.parse()` and not trigger this rule.

---

## 5) Observed failure modes

**Failure 1: Prose returned as fixed code (format failure / unsafe confidence)**

Input: `"print('hello')\nprint('world')\n"`
Client: A `ProseFixer` mock that returns `"The code looks fine.\nMinor style note: remove print statements."` for the fixer prompt.

Before the format-failure guardrail was added, `assess_risk` scored this 95 and set `should_autofix: True`. The agent would have written an English sentence to disk as the "fixed" Python file. The risk assessor had no way to distinguish valid code from prose — it only checked for length changes and missing `return`, neither of which applied here.

**Failure 2: Heuristic over-editing on cleanish code (false positive)**

Input: `sample_code/cleanish.py` (already uses `logging`).
Mode: Heuristic only.

Because `cleanish.py` contains no `print(`, bare `except:`, or `TODO`, the heuristic analyzer correctly returns no issues and the fixer returns the original unchanged. However, if the snippet had contained a single `print(` for legitimate debug output inside a test or script entrypoint, the heuristic would prepend `import logging` and replace `print(` with `logging.info(` regardless of context. The heuristic has no concept of "is this a production module or a one-off script?" — it treats all `print(` calls as problems.

---

## 6) Heuristic vs. Gemini comparison

| Dimension | Heuristic mode | Gemini mode |
|-----------|---------------|-------------|
| Issue detection | Catches only `print(`, bare `except:`, `TODO` — nothing else | Can detect semantic bugs, missing edge cases, type issues, unreachable code |
| Fix quality | Mechanical substitution; always produces the same output for the same input | Context-aware rewrite; can restructure logic, rename variables, add type hints |
| Output reliability | 100% predictable; never produces prose or markdown | Occasionally wraps output in backticks or adds explanation text; requires `_strip_code_fences` |
| Risk scorer agreement | Scores aligned with intuition: `mixed_issues.py` scored high, `cleanish.py` scored 100 | Scores can diverge if Gemini makes many small changes that individually seem minor but collectively alter behavior |
| Speed | Instantaneous | Subject to API latency and rate limits |
| Offline availability | Always available | Requires `GEMINI_API_KEY` and network access |

The most significant discrepancy: heuristics cannot distinguish a `TODO` comment that marks genuinely unfinished code from one used as a documentation convention. Gemini can read the surrounding context and judge whether the TODO represents a real risk.

---

## 7) Human-in-the-loop decision

**Scenario:** The agent detects a high-severity bare `except:` in a production database transaction handler. The heuristic fixer replaces it with `except Exception as e:` and the risk score drops to 85 — technically clearing the auto-fix threshold if no other deductions apply.

In this case the agent should refuse to auto-apply, because:
- Exception handling in transaction code is load-bearing; a wrong change can silently swallow database errors or prevent rollbacks.
- The fix is syntactically valid but the *correct* exception type (`psycopg2.DatabaseError`, `sqlalchemy.exc.SQLAlchemyError`, etc.) is domain-specific and unknowable without project context.

**Trigger to add:** A hard block on auto-fix whenever the issue type is `"Reliability"` and the fix touches exception handling — regardless of score. This is best implemented in `risk_assessor.py` alongside the existing `has_high_severity` block, since it is a policy decision about what categories of change are safe to automate.

**Message to show the user:**
```
[BugHound] Auto-fix blocked: this change modifies exception handling in reliability-critical code.
Proposed fix shown below for review. Apply manually if correct.
```

---

## 8) Improvement idea

**Improvement: validate that the fix is a strict superset of the original's public interface**

The current assessor checks for missing `return` statements lexically, but it misses cases where a function signature changes (parameter removed, default value altered) or a public function is deleted entirely. A low-complexity addition to `assess_risk` would use `ast.parse()` — already imported for the format-failure check — to extract the set of top-level function names and their argument counts from both the original and fixed code, then deduct points if any name disappears or any arity changes.

```python
def _extract_signatures(code: str) -> dict:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    return {
        node.name: len(node.args.args)
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
```

If any function present in the original is missing or has a different arity in the fixed code, deduct 30 points. This catches over-editing (a fix that deletes a function entirely) and interface-breaking changes (a fix that removes a required parameter), both of which the current rules miss completely. It reuses the `ast` import already in place, requires no new dependencies, and adds roughly 10 lines of code.
