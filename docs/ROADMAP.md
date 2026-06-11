# Roadmap

Where this is heading: from a single-app pipeline to a portfolio autopilot. The current five agents cover the **shipping loop** (issue → PR → TestFlight → release). The next wave covers **portfolio operations** — the recurring per-app work that quietly stops happening once you maintain more than a few apps.

Status: the shipping loop is being piloted against a real 16-app portfolio during the iOS 27 beta cycle (summer 2026). Portfolio agents land after the pilot proves the safety model.

## Planned agents

| Agent | Trigger | What it does | Human gate |
|---|---|---|---|
| `portfolio-health-monitor` | weekly | Pulls sales, analytics, perf metrics, and crash diagnostics for every app; compares to baseline; writes one digest with anomalies on top ("downloads −40% WoW", "crash spike after 2.3.1") | read-only |
| `review-concierge` | daily | Fetches new App Store reviews across all apps, drafts responses, files crash complaints as `triage` issues | you approve each reply before it posts |
| `aso-experimenter` | monthly | Checks keyword performance, proposes metadata changes, runs them as Product Page Optimization experiments, reads results, iterates | you approve each experiment |
| `overnight-qa` | nightly | Build, full test suite, launch in simulator, screenshot key flows, snapshot + accessibility checks; morning report | read-only |

Already shipped from the original brainstorm: `beta-break-bot` (in `agents/` now — rebuild the portfolio on every Xcode beta drop and report breakage).

## Design rules for new agents

Every new agent must declare, in its SKILL.md: **Trigger · Preconditions · numbered Steps with copy-runnable commands · Stop conditions · "What this agent never does."** Read-only agents (monitors, reporters) may run fully autonomous; anything that changes state visible to users (reviews, metadata, releases) gets a human approval gate. The [safety contract](SAFETY.md) is non-negotiable and applies to all of them.

## Infrastructure ideas

- **Portfolio registry format** — a config file mapping app ⇄ repo ⇄ scheme ⇄ App Store Connect app ID, so portfolio agents iterate without hardcoding. (Keep the *filled-in* registry private; only the format lives here.)
- **Plugin packaging** — `.claude-plugin/plugin.json` is staged; publish to a marketplace so installation is one command.
- **Metrics** — issues shipped/week, issue→merge time, PR rejection rate: the numbers that say whether the pipeline is actually faster than working by hand.

## Contributions

The most useful contributions right now: run the pipeline on your own app and report where the agent instructions were ambiguous or wrong. The agents are operating procedures — they improve the way checklists improve: from incident reports.
