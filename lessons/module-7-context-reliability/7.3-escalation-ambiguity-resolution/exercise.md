# Escalation and ambiguity resolution — exercise

## What you're building

Implement the triage gate from the lesson in `escalation.py`. A support agent
emits a structured `signal` describing what it knows about a request; your code
decides whether to **answer**, **clarify**, or **escalate** — deterministically,
in code, never by trusting a prompt instruction.

## Function signatures

```python
def route(signal, policy):
    """Deterministic triage gate. Return 'answer', 'clarify', or 'escalate'."""

def clarifying_question(missing_required):
    """Build a TARGETED clarifying question naming the specific missing fields."""
```

A `signal` is a dict: `confidence` (float 0–1), `missing_required` (list[str]),
`ambiguous` (bool), `stakes` (`"low"` | `"high"`). A `policy` is a dict:
`confidence_threshold` and `high_stakes_threshold`. Use `DEFAULT_POLICY` and the
sample signals from `fixtures.py` — they ship implemented.

## Requirements

You must:

1. **Implement `route` as an ordered gate, in this exact order:**
   - `missing_required` non-empty → `'clarify'`
   - else `ambiguous` → `'clarify'`
   - else `stakes == 'high'` and `confidence < high_stakes_threshold` → `'escalate'`
   - else `confidence < confidence_threshold` → `'escalate'`
   - else → `'answer'`
2. **Make `clarifying_question` targeted** — it must name each field in
   `missing_required` by name (e.g. `"To proceed I need: order_id, email."`),
   not return a vague `"Can you clarify?"`.
3. **Keep the decision a pure function of the typed signal fields.** No string
   matching on model prose, no reading the assistant's text to decide.
4. **Pass every test in `test_escalation.py`.**

You must NOT:

5. **Answer or guess when a required field is missing.** If `missing_required`
   is non-empty, the only correct route is `'clarify'` — never `'answer'`, and
   never fabricate the missing value. An agent that fills the gap with a guess
   is the hallucination the guardrail exists to prevent.
6. **Make the escalation decision anything other than a programmatic gate.** The
   high-stakes-low-confidence path must be decided by `route`'s code, not
   deferred to a prompt instruction like "escalate if unsure." A prompt is a
   suggestion; this gate is the control.

Requirements 5 and 6 are graded directly by the rubric (`check: anti_pattern`).
The verifier reads your code looking for them; they fail the rubric whether or
not your tests pass.

## How to run it

```bash
cd ~/learn-claude-work/7.3
pip install -r requirements.txt          # use a venv if you like
pytest -v
```

The tests are pure logic — no `ANTHROPIC_API_KEY`, no network, no API credits.

When you're ready (or stuck), run `/verify 7.3` and I'll grade you.

## References

- Lesson: `lesson.md` (in this directory) — read it first if you haven't.
- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — allow "I don't know" and ask for clarification when info is missing.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — why the signal your gate reads is typed data, not parsed prose.
