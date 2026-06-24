# Indie App Autopilot

Agents that take an indie iOS app from **GitHub issue → tested PR → TestFlight → App Store**, with a human in exactly two places: merging the PR and pressing Submit.

[![Claude Code](https://img.shields.io/badge/Claude_Code-skills-blueviolet)](https://claude.ai/code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Xcode_27-Agent_Skills-blue)](https://developer.apple.com)

```
GitHub issue (spec) ──► issue-worker ──► PR ──► [HUMAN: merge]
                                                    │
                                              CI: fastlane beta
                                                    │
                                              TestFlight build
                                                    │
       feedback-triage ◄── beta feedback ◄──── testers
            │
        new issues ──► [HUMAN: promote to agent-ready] ──► queue
                                                    │
"prepare release X.Y" ──► release-agent ──► [HUMAN: Submit for Review]
                                                    │
                                          phased release + crash watch
```

## The stack

Three repos, three layers — use one or all:

| Layer | Repo | What it is |
|---|---|---|
| Knowledge | [claude-code-apple-skills](https://github.com/rshankras/claude-code-apple-skills) | 139 skills — how to build right |
| Action | **indie-app-autopilot** ← you are here | 7 agents — who ships it |
| Integration | [asc-metadata-mcp](https://github.com/rshankras/asc-metadata-mcp) | 65+ MCP tools — live ASC API wire |

`release-agent` and `portfolio-health-monitor` use `asc-metadata-mcp` to read and write App Store Connect directly. Install it alongside this repo for the full pipeline.

## Why this exists

Born June 2026, during WWDC26 week, from three observations:

1. **Solo developers don't scale; queues + agents do.** With a portfolio of apps, anything you do per-app you effectively don't do. Defining all work as GitHub issues and letting an agent work them one at a time — tests first, screenshots attached, human merging — turns "I should update that app" into a queue that drains itself.
2. **The autonomy boundary is the design problem, not the AI.** A pipeline you can trust is one with exactly two human gates (PR merge, App Store submit), a WIP limit of 1, and agents that ask instead of guess. This repo is mostly an encoding of that boundary — see [docs/SAFETY.md](docs/SAFETY.md).
3. **Agent skills became an open standard.** Xcode 27 ships Apple's own Agent Skills in the same `SKILL.md` format used here and in claude-code-apple-skills. Operating procedures for agents are now portable, shareable artifacts — so a pipeline like this can be open source instead of every indie rebuilding it privately.

The build philosophy is deliberately incremental ([docs/PIPELINE.md](docs/PIPELINE.md)): issue→PR first, live with it two weeks, then TestFlight CI, then the release agent, then the orchestrator. Each phase is useful even if you stop there. **Don't build the orchestrator first.**

## What this is (and isn't)

This is the **action layer**: agent operating procedures, CI wiring, and per-app templates for running an issue-driven development pipeline with [Claude Code](https://claude.com/claude-code).

It is not a knowledge library. Platform knowledge (SwiftUI patterns, HIG review, App Store optimization, code generators) lives in **[claude-code-apple-skills](https://github.com/rshankras/claude-code-apple-skills)** — the knowledge layer. App Store Connect reads and writes go through **[asc-metadata-mcp](https://github.com/rshankras/asc-metadata-mcp)** — the integration layer. This repo is the action layer. They are cross-linked, never merged.

## The agents

| Agent | Trigger | What it does | Uses asc-metadata-mcp | Human gate |
|---|---|---|---|---|
| [`issue-worker`](agents/issue-worker/SKILL.md) | manual or queue-runner | Oldest `agent-ready` issue → TDD implementation → simulator screenshots → PR | — | You merge |
| [`release-agent`](agents/release-agent/SKILL.md) | you say "prepare release X.Y" | Release notes, App Store Connect metadata, submission checklist | Yes | You submit |
| [`feedback-triage`](agents/feedback-triage/SKILL.md) | daily schedule | TestFlight crashes + feedback → deduplicated GitHub issues (`triage`) | — | You promote to `agent-ready` |
| [`queue-runner`](agents/queue-runner/SKILL.md) | nightly schedule | Runs issue-worker when no agent PR is open (WIP = 1); weekly digest | — | — |
| [`beta-break-bot`](agents/beta-break-bot/SKILL.md) | new Xcode beta drops | Rebuilds every portfolio app against the new SDK, reports breakage | — | — |
| [`portfolio-health-monitor`](agents/portfolio-health-monitor/SKILL.md) | weekly schedule | Sales, downloads, sessions, crashes, perf, rating deltas, new/unanswered reviews → week-over-week digest, anomalies on top | Yes | — (read-only) |
| [`daily-sales-pulse`](agents/daily-sales-pulse/SKILL.md) | daily (launchd runs [`scripts/daily-sales-pulse.py`](scripts/daily-sales-pulse.py)) | Yesterday's downloads/proceeds per app vs trailing 7-day average → a macOS notification + email | Yes | — (read-only) |

Agents use the open Agent Skills format (`SKILL.md` + YAML frontmatter) — the same format as Xcode 27's built-in Agent Skills.

## Quick start

```bash
# 1. Clone
git clone https://github.com/rshankras/indie-app-autopilot.git

# 2. Install the agents globally (or per-project into .claude/skills/)
cp -r indie-app-autopilot/agents/* ~/.claude/skills/

# 3. (Optional but recommended) Install asc-metadata-mcp for App Store Connect access
#    https://github.com/rshankras/asc-metadata-mcp

# 4. Onboard one app (labels, issue template, TestFlight workflow, Fastlane)
./scripts/setup-app.sh /path/to/your-app-repo YourScheme

# 5. Read docs/SETUP.md for the one-time signing/CI setup, then:
#    file issues → label one `agent-ready` → ask Claude Code to "work the next issue"
```

## Documentation

| Doc | Contents |
|---|---|
| [docs/PIPELINE.md](docs/PIPELINE.md) | The full Phase 0–4 build plan and rollout order |
| [docs/SETUP.md](docs/SETUP.md) | Onboarding one app, step by step (signing, CI runner, secrets) |
| [docs/SAFETY.md](docs/SAFETY.md) | The operating contract: two human gates, WIP limit, hard rules |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Where this is heading: portfolio-operations agents (review concierge, ASO experimenter, overnight QA) |

## Repository structure

```
agents/        Agent operating procedures (SKILL.md format) — read by Claude
templates/     Files COPIED into each app repo by scripts/setup-app.sh
scripts/       setup-app.sh — bootstrap an app repo (labels, templates, Fastlane)
docs/          Pipeline plan, setup guide, safety contract
```

Agent logic lives only here. App repos get wiring (labels, workflows, Fastlane) — so improving an agent improves it for every app at once.

## The safety contract (summary)

- Two human gates, forever: **PR merge** and **App Store submit**.
- One issue = one branch = one PR = one agent run. WIP limit = 1.
- Agents never touch `main`, never expand scope, never weaken a test, and prefer asking (`agent-blocked`) over guessing.
- Secrets (App Store Connect API keys) live in CI secrets — never in any repo.

Full contract: [docs/SAFETY.md](docs/SAFETY.md).

## Status

Early. Built in public against a real 16-app portfolio during the iOS 27 beta cycle (summer 2026). Expect sharp edges; issues and PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
