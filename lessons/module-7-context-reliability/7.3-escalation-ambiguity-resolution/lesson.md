---
chapter: "7.3"
slug: "escalation-ambiguity-resolution"
title: "Escalation and ambiguity resolution"
module: "module-7-context-reliability"
sequence: 30
references:
  - title: "Reduce hallucinations"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations"
    type: official_docs
    covers: "Allow 'I don't know'; ask for clarification when required info is missing"
  - title: "Increase output consistency"
    url: "https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency"
    type: official_docs
    covers: "'If unsure, ask for clarification before proceeding'; grounding and format constraints"
  - title: "Handle tool calls"
    url: "https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls"
    type: official_docs
    covers: "Surfacing failures with is_error and instructive messages; programmatic handling around the model"
  - title: "Structured outputs"
    url: "https://platform.claude.com/docs/en/build-with-claude/structured-outputs"
    type: official_docs
    covers: "Schema-guaranteed JSON for a parseable confidence/decision signal a gate can read"
---

# Escalation and ambiguity resolution

## Overview

An agent that always answers is a liability. Real production tasks arrive underspecified ("cancel my order" — which order?), ambiguous ("the blue one" — there are three), or high-stakes (issue a refund, delete a record, send a wire). A reliable agent has to do three things the naïve "just answer" loop never does: **detect** when it lacks what it needs, **ask** a targeted clarifying question instead of guessing, and **escalate** to a human when confidence is low on an action that's expensive to get wrong. This is Domain 5, Task Statement 5.2: **design effective escalation and ambiguity resolution patterns.**

The trap the exam sets is binary thinking. One failure mode is the over-eager agent that fills every gap with a plausible guess — it hallucinates an order ID, refunds the wrong customer, and is confidently wrong. The opposite failure mode is the agent that escalates everything, which is just a slow, expensive human queue with extra steps. The skill the exam tests is **triage**: a deterministic policy that routes most requests to an answer, sends genuinely under-specified ones back for clarification, and reserves human escalation for the narrow band where the action is high-stakes *and* the agent isn't confident.

The two pieces — knowing when to ask, and knowing when to escalate — come from two different official guardrails. Asking before guessing is a hallucination control ([reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). Escalating high-stakes low-confidence actions is a *control-plane* decision that, the Anthropic way, must be enforced programmatically — not left to a sentence in the prompt.

## How it works

### Detect missing information and ask, don't guess

The first guardrail is permission to be uncertain. The official guidance is blunt: **"Allow Claude to say 'I don't know'"** — explicitly give the model an out so it doesn't feel compelled to fabricate an answer ([reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). A model that has been told it *must* produce an answer will invent the missing order ID rather than admit it doesn't have one — the reduce-hallucinations page is about giving the model that out to admit it lacks the information. The active half — turning that admission into a question rather than proceeding on an assumption — comes from the consistency guide, which states the rule as a single sentence you can hand the model: **"If unsure, ask for clarification before proceeding."** ([increase consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency)).

But a clarifying question only helps if it's *targeted*. "Can you clarify?" pushes the work back onto the user and usually earns a second vague reply. A good clarifying question names exactly what's missing: *"To cancel an order I need the order_id and the email on the account."* The user can answer it in one turn. The difference between a vague and a targeted question is the difference between one extra round-trip and three.

### Make the missing-info and confidence signals machine-readable

A clarifying question is only as good as your ability to *detect* that one is needed, and a gate is only as good as the signal it reads. That signal should be structured data, not prose you regex out of a sentence. **Structured Outputs** give you schema-guaranteed JSON via constrained decoding — "Always valid: No more JSON.parse() errors" ([structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)). Have the model emit something like `{"missing_required": ["order_id"], "ambiguous": false, "confidence": 0.42, "stakes": "high"}` against a JSON schema, and your routing code reads typed fields instead of guessing whether the prose "I'm not totally sure…" means confidence is low. Strict tool use applies the same parameter validation when the signal arrives as a tool call. The point: the *decision input* is data, so the *decision* can be code.

### Escalate high-stakes low-confidence actions through a programmatic gate

Here is the load-bearing exam position. When an action is high-stakes — a refund, an account deletion, anything expensive or irreversible — and the agent's confidence is below a threshold, the request must go to a human. **The escalation must be enforced programmatically, not by a prompt instruction.** A system prompt that says "escalate to a human if you are unsure" is *not a control*: it's a request the model can ignore, misjudge, or be talked out of. It will hold most of the time and fail exactly when it matters — under an adversarial input or an edge case — which is the worst possible failure profile for a high-stakes action.

The Anthropic-prescribed pattern is the same one this module teaches for every business rule that needs deterministic compliance: **programmatic enforcement over prompt instructions.** You let the model *propose* (and produce the structured confidence/stakes signal above), and you let *code* dispose. The tool-use lifecycle is built for exactly this — your code sits between the model and the side-effecting action, and it can refuse to execute. When it refuses, you surface that back to the model honestly: return the tool result with **`is_error: true`** and an instructive message so the model incorporates the outcome ("This action requires human approval; the request has been escalated.") rather than silently retrying ([handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)). The gate is a function with a fixed decision order; the model never gets to overrule it.

### Triage: the deterministic routing order

Put it together as one ordered decision. Order matters because the categories overlap — a request can be both missing fields *and* low-confidence, and you want the cheaper, more recoverable action (ask the user) to win over the more expensive one (page a human):

1. **Missing required info → clarify.** If a required field is absent, no confidence score matters; you literally cannot proceed. Ask for the specific fields.
2. **Ambiguous → clarify.** All fields present but the request resolves to more than one thing ("the blue one"). Ask which.
3. **High-stakes and low confidence → escalate.** Everything's present and unambiguous, but the action is expensive and the model isn't sure enough. A human decides.
4. **Low confidence (any stakes) → escalate.** Even low-stakes, if the model is below the general confidence floor, don't ship a likely-wrong answer.
5. **Otherwise → answer.** Confident, unambiguous, complete: proceed.

Two thresholds tune the bands: a general `confidence_threshold` and a stricter `high_stakes_threshold` (higher, because the bar for acting on something expensive is higher). This is the function you'll implement.

```python
def route(signal, policy):
    if signal["missing_required"]:
        return "clarify"
    if signal["ambiguous"]:
        return "clarify"
    if signal["stakes"] == "high" and signal["confidence"] < policy["high_stakes_threshold"]:
        return "escalate"
    if signal["confidence"] < policy["confidence_threshold"]:
        return "escalate"
    return "answer"
```

Notice what's *not* here: no string-matching on the model's prose, no "the model said it would escalate so we trust it." The decision is a pure function of typed inputs.

## Worked example

A support agent handles "I want to cancel my order and get a refund." The model emits a structured signal; your gate routes it. Here's the complete shape the exercise grades.

```python
DEFAULT_POLICY = {"confidence_threshold": 0.6, "high_stakes_threshold": 0.85}


def route(signal, policy):
    """Deterministic triage gate. Returns 'answer' | 'clarify' | 'escalate'."""
    if signal["missing_required"]:
        return "clarify"
    if signal["ambiguous"]:
        return "clarify"
    if signal["stakes"] == "high" and signal["confidence"] < policy["high_stakes_threshold"]:
        return "escalate"
    if signal["confidence"] < policy["confidence_threshold"]:
        return "escalate"
    return "answer"


def clarifying_question(missing_required):
    """Name the specific missing fields, not a vague 'can you clarify?'."""
    fields = ", ".join(missing_required)
    return "To proceed I need: " + fields + "."
```

Walk through four signals against `DEFAULT_POLICY`:

```python
# 1. Refund requested but no order id -> can't proceed, ask for it.
s1 = {"confidence": 0.9, "missing_required": ["order_id"], "ambiguous": False, "stakes": "high"}
route(s1, DEFAULT_POLICY)              # 'clarify'
clarifying_question(s1["missing_required"])   # 'To proceed I need: order_id.'

# 2. All fields present, but "the recent order" matches three -> ambiguous.
s2 = {"confidence": 0.8, "missing_required": [], "ambiguous": True, "stakes": "low"}
route(s2, DEFAULT_POLICY)              # 'clarify'

# 3. Refund is high-stakes; model is only 0.7 confident -> human decides.
s3 = {"confidence": 0.7, "missing_required": [], "ambiguous": False, "stakes": "high"}
route(s3, DEFAULT_POLICY)              # 'escalate'  (0.7 < 0.85)

# 4. Complete, unambiguous, confident, low-stakes lookup -> just answer.
s4 = {"confidence": 0.95, "missing_required": [], "ambiguous": False, "stakes": "low"}
route(s4, DEFAULT_POLICY)              # 'answer'
```

The same 0.7 confidence that escalates a high-stakes refund (signal 3) would *answer* a low-stakes question — the high-stakes band's stricter 0.85 threshold is doing the work. That asymmetry is the whole point: the cost of being wrong sets the bar. And the clarifying question for signal 1 names `order_id` outright, so the user can resolve it in one reply rather than guessing what you wanted.

In a live agent, `route` runs *before* the side-effecting refund tool executes. `'answer'` lets the tool fire; `'clarify'` returns a question to the user; `'escalate'` returns the tool result with `is_error: true` and an instructive message so the model reports the escalation instead of retrying ([handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)).

## Anti-patterns & pitfalls

- **Guessing to fill a required gap.** The model invents an order ID or assumes "the blue one" means the first match. This is the canonical hallucination the guardrail exists to prevent: the fix is to **allow "I don't know"** and **ask for clarification when info is missing** ([reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations)). An agent that never asks is an agent that will confidently act on fabricated inputs.

- **A prompt instruction as the escalation control.** "Escalate to a human if you're not confident" in the system prompt *feels* like a safeguard, but it is not a control — it's a suggestion the model can misjudge or be argued out of, and it fails precisely on the adversarial inputs where high-stakes escalation matters most. The Anthropic way is unambiguous: **programmatic enforcement over prompt instructions** for any rule requiring deterministic compliance. The model proposes; a code gate disposes. Anyone who answers "put it in the prompt" on this exam is choosing the wrong pattern.

- **A vague clarifying question.** "Can you clarify?" or "I need more information" technically asks, but it puts the work on the user and burns round-trips. Name the missing fields: *"To proceed I need: order_id, email."* A targeted question resolves in one turn.

- **Routing on the model's prose.** Reading the assistant's text for "I'm not sure" or "I would escalate this" to drive the decision. Like text-based loop termination, this is brittle string-matching that misses paraphrases and false-fires on asides. Drive the gate from a **structured, schema-guaranteed signal** instead ([structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)) — typed `confidence`, `missing_required`, `stakes` fields your code reads directly.

- **The all-or-nothing extremes.** Escalating every request makes the agent a slow human queue; escalating nothing makes it dangerous. Neither is triage. The correct design routes the *majority* to an answer and reserves clarification and escalation for the cases that genuinely need them — tuned by the two thresholds, not by a single on/off switch.

## Exam focus

Task Statement 5.2 powers the reliability questions in the customer-facing scenarios — most directly **Scenario 1 (Customer Support Resolution Agent)**, where the agent must cancel orders, issue refunds, and look up accounts, each with a different stakes and missing-info profile. Expect distractors that:

- offer a **system-prompt instruction** ("tell the model to escalate when unsure") as the escalation mechanism — wrong, because escalation of a high-stakes action needs a programmatic gate;
- offer **guessing or assuming** the missing value as a way to "keep the conversation flowing" — wrong, it's a hallucination;
- offer a **vague "ask the user to clarify"** without naming the fields, or **escalate-everything / answer-everything** as the policy — wrong, neither is triage.

The correct answer is consistently: detect the gap from a structured signal, ask a *targeted* question when info is missing or ambiguous, and enforce high-stakes escalation in *code*.

## References & further reading

- [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) — allow Claude to say "I don't know" and ask for clarification when information is missing; the foundation for not-guessing.
- [Increase output consistency](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency) — the prescribed instruction "If unsure, ask for clarification before proceeding," plus grounding and format constraints.
- [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) — using `is_error: true` and instructive messages to surface a refused/escalated action to the model; the programmatic layer that sits between the model and a side-effecting tool.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — schema-guaranteed JSON (and strict tool use) so the confidence/stakes/missing-info signal your gate reads is typed data, not parsed prose.

## Exam coverage

- **CCAF** — Domain 5 (Context Management & Reliability), Task Statement 5.2: Design effective escalation and ambiguity resolution patterns.

The authoritative exam → lesson map for the whole project is [`docs/exam-mapping.md`](../../../docs/exam-mapping.md).
