# Memory

This file is the front door to the repo's existing memory stack. It points to the current operating docs and session history; it does not replace them.

## Read order

1. [README.md](./README.md)
2. [AGENTS.md](./AGENTS.md)
3. [docs/repo-brief.md](./docs/repo-brief.md)
4. [docs/heartbeat.md](./docs/heartbeat.md)
5. Latest file in [`logs/`](./logs/) (currently [`logs/2026-03-27-session.md`](./logs/2026-03-27-session.md))
6. [docs/DECISION_LOG.md](./docs/DECISION_LOG.md) if the task touches a durable naming, scope, or architecture decision

## Current operational memory files

- [AGENTS.md](./AGENTS.md)
- [docs/repo-brief.md](./docs/repo-brief.md)
- [docs/heartbeat.md](./docs/heartbeat.md)
- [`logs/`](./logs/)
- [docs/DECISION_LOG.md](./docs/DECISION_LOG.md)

## Update rules

- Update [docs/heartbeat.md](./docs/heartbeat.md) when current-state status changes.
- Add a file in [`logs/`](./logs/) for real work sessions worth resuming later.
- Update [docs/repo-brief.md](./docs/repo-brief.md) when repo purpose, buyer/user, or current milestone changes.
- Update [docs/DECISION_LOG.md](./docs/DECISION_LOG.md) only for durable naming, scope, or architecture decisions.
