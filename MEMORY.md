# Memory

This file is the front door to the repo's existing memory stack. It points to the current operating docs and session history; it does not replace them.

## Read order

1. [README.md](./README.md)
2. [AGENTS.md](./AGENTS.md)
3. [docs/repo-brief.md](./docs/repo-brief.md)
4. [docs/heartbeat.md](./docs/heartbeat.md)
5. [docs/SESSION_LOG.md](./docs/SESSION_LOG.md) for the current build-session memory and validation trail
6. Latest file in [`logs/`](./logs/) for older dated closeout notes when relevant
7. [docs/DECISION_LOG.md](./docs/DECISION_LOG.md) if the task touches a durable naming, scope, or architecture decision

## Current operational memory files

- [AGENTS.md](./AGENTS.md)
- [docs/repo-brief.md](./docs/repo-brief.md)
- [docs/heartbeat.md](./docs/heartbeat.md)
- [docs/SESSION_LOG.md](./docs/SESSION_LOG.md)
- [`logs/`](./logs/)
- [docs/DECISION_LOG.md](./docs/DECISION_LOG.md)

## Update rules

- Update [docs/heartbeat.md](./docs/heartbeat.md) when current-state status changes.
- Append to [docs/SESSION_LOG.md](./docs/SESSION_LOG.md) for real work sessions worth resuming later.
- Add a file in [`logs/`](./logs/) only for separate dated closeout notes when explicitly useful.
- Update [docs/repo-brief.md](./docs/repo-brief.md) when repo purpose, buyer/user, or current milestone changes.
- Update [docs/DECISION_LOG.md](./docs/DECISION_LOG.md) only for durable naming, scope, or architecture decisions.
