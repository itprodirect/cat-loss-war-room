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

## Intake schema

Each intake should mirror `CaseIntake` in `src/war_room/query_plan.py`.

Required fields:

- `event_name` (string)
- `event_date` (YYYY-MM-DD string)
- `state` (string)
- `county` (string)
- `carrier` (string)
- `policy_type` (string)

Optional fields:

- `posture` (list of strings)
- `key_facts` (list of strings)
- `coverage_issues` (list of strings)

See `_template_case_intake.json` for a clean starting point.
