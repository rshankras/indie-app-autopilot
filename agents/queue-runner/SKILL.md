---
name: queue-runner
description: The orchestrator. On a nightly schedule, checks the WIP limit and runs issue-worker on the next agent-ready issue if no agent PR is open. Produces a weekly digest of shipped / blocked / queue depth. Use as a scheduled agent, or when asked to "run the queue".
allowed-tools: [Read, Glob, Grep, Bash]
---

# Queue Runner

Keeps the pipeline moving at exactly the speed the human reviews. It adds **no new permissions** — it only decides *whether* to invoke issue-worker, which carries its own rules. Read `docs/SAFETY.md` as binding.

## Trigger

Nightly schedule (e.g., Claude Code scheduled agent / cron), or a human asks to "run the queue".

## Steps

1. **WIP check (the entire point of this agent):**
   ```bash
   gh pr list --label agent-pr --state open --json number,title,createdAt
   ```
   - One or more open → **do nothing** with the queue. If the oldest has waited > 3 days, post one gentle reminder comment on it (never re-ping more than once per PR).
2. **Blocked check:** list `agent-blocked` issues; include them in the report — they are waiting on the human, not the agent.
3. **Dispatch:** if WIP = 0 and an `agent-ready` issue exists, invoke the **issue-worker** skill on the oldest one. issue-worker's own rules apply unchanged.
4. **Report** (every run, even no-ops): did it dispatch and to which issue · open agent PR awaiting review · `agent-blocked` issues with their questions · queue depth.
5. **Weekly digest** (first run of the week, posted to the repo as a discussion/issue comment or written to the ops notes): issues shipped last week · average issue→merge time · blocked items aging · queue depth trend.

## Stop conditions

- WIP limit is absolute: never run issue-worker while any agent PR is open, and never run two issue-workers concurrently.
- Empty queue → report and exit. Never invent work, never promote `triage` or `needs-human` issues to fill the queue.
- Two consecutive failed dispatches on the same issue → relabel it `needs-human` with a failure summary and skip it thereafter.

## What this agent never does

Write code itself · merge · change labels except the failure path above · bypass any issue-worker rule.
