# Live Eval Lane

This folder is for public or fully redacted evaluation scenarios.

## Purpose

Use live eval runs to measure quality and reliability without changing the
canonical demo notebook flow.

## Rules

- No client PII.
- No policy numbers or claim numbers.
- No privileged/confidential case facts.
- Public sources only, or synthetic/redacted scenarios.

## Folder layout

- `eval/intakes/`: committed intake files for eval runs.
- `eval/results/`: local metrics/output summaries (gitignored except README).

## Intake contract (canonical)

All intake payloads in both lanes (demo and live eval) use the same canonical
`CaseIntake` schema in `src/war_room/query_plan.py`.

Required fields (demo + live eval):

- `event_name` (string)
- `event_date` (YYYY-MM-DD string)
- `state` (string)
- `county` (string)
- `carrier` (string)
- `policy_type` (string)

Optional fields (demo + live eval):

- `posture` (list of snake_case strings, defaults to `["denial"]`)
- `key_facts` (list of strings)
- `coverage_issues` (list of strings)

Strict validation rules:

- Unknown fields are rejected.
- Missing required fields fail fast.
- Field types are not coerced.
- `event_date` must be a valid ISO date (`YYYY-MM-DD`).

## Validation entrypoints

- `validate_case_intake_payload(payload)` validates JSON-like payloads.
- `load_case_intake(path)` loads JSON from disk and validates strictly.

Example:

```python
from war_room.query_plan import load_case_intake

intake = load_case_intake("eval/intakes/_template_case_intake.json")
```

See `_template_case_intake.json` for a clean starting point.
