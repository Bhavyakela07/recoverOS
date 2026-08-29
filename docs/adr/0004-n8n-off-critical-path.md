# ADR-0004: n8n Off Critical Path

## Status
Accepted

## Date
2026-08-29

## Context
Track 03 does not require, reward, or mention n8n.

**Problem**: n8n is the one part of the stack Claude Code cannot write, run, or debug for us — it is a GUI canvas, so every hour in it is an hour our biggest advantage (AI-assisted coding) is switched off.

## Decision
**n8n is NOT on the critical path.** The scheduled abandonment / overdue sweep is ~20 lines of Python (APScheduler or a FastAPI startup task). Escalation notification is a function call.

If, and only if, MUST is fully green with time to spare on Day 5, n8n may be added as a thin, decorative wrapper for:
(a) the escalation fan-out to Slack/email
(b) a visual workflow slide

Nothing may depend on it.

## Consequences

### Positive
- **Preserves AI-coding advantage**: Every hour stays in Python where Claude can help
- **Cleaner repo**: No JSON workflow blobs to diff in git (they fight "repo is the source of truth")
- **Thin orchestration**: Detection, verification, idempotency, policy, stopping rules, and execution stay in tested backend code
- **Swappable**: A workflow engine for notifications is a config change, not an architecture change

### Negative
- **No workflow UI**: The demo won't show a fancy orchestration canvas
- **Manual fan-out**: Escalation notifications are a function call, not a workflow

## Rationale

Orchestration is deliberately decoupled and thin. Correctness lives in tested backend code — detection, verification, idempotency, policy, stopping rules, and execution. Swapping in a workflow engine for notifications later is a config change, not an architecture change.

**Alternative considered and rejected**: Building orchestration with n8n from the start. Rejected because it's a GUI tool that fights our AI-assisted workflow and doesn't fit the "repo is the source of truth" rule.

**Trade-off**: We accept a simpler orchestration story in exchange for speed, testability, and the ability to keep the critical path entirely in code that our AI can write, run, and debug.

## Notes
- APScheduler for scheduled sweeps
- FastAPI startup task for recurring work
- Function calls for notification fan-out
- If asked why orchestration is thin, use this exact line:
  "Orchestration is deliberately decoupled and thin. Detection, verification, idempotency, policy, stopping rules, and execution live in tested backend code, because that's where correctness has to live. Swapping in a workflow engine for notifications is a config change, not an architecture change."