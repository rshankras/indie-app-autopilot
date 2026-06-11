# The Pipeline: GitHub Issues → App Store

The build plan for the full issue-driven pipeline. Each phase is useful on its own even if you never build the next one. **Do not build the orchestrator first** — build issue→PR, live with it for two weeks, and let what annoys you decide what gets automated next.

Timeline: ~6 weeks to the full loop, useful from day 3.

---

## Phase 0 — Foundations (Day 1, ~2 hours, no agents)

Agents are only as good as the queue you feed them. This phase builds the queue.

1. **Prepare the pilot repo.** Pick one small live app. Confirm it builds and tests headlessly:
   ```bash
   xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16'
   ```
   No test target → create one first. *The whole pipeline rests on tests as the pass/fail contract.*
2. **Add the CLAUDE.md block** (`templates/CLAUDE.md.snippet`) to the app repo: exact build command, exact test command, scheme/destination, conventions. The agent reads this every run.
3. **Create the labels** (done by `scripts/setup-app.sh`):

   | Label | Meaning |
   |---|---|
   | `agent-ready` | Spec complete, agent may pick it up |
   | `agent-in-progress` | An agent run owns this issue |
   | `agent-blocked` | Agent hit a question only a human can answer |
   | `needs-human` | Too ambiguous/risky for an agent |
   | `triage` | Filed by feedback-triage, awaiting human promotion |

4. **Install the issue template** (`templates/github/ISSUE_TEMPLATE/agent-task.yml`): Goal (one sentence), Acceptance criteria (checkboxes — these become the tests), Out of scope, UI involved y/n. **Rule: no acceptance criteria → no `agent-ready` label.**
5. **Fill the queue** with 5–10 small issues (one screen / one behavior each).

## Phase 1 — Issue Worker (Weekend 1) — the core

Install [`agents/issue-worker`](../agents/issue-worker/SKILL.md). Run it manually: open Claude Code in the app repo and ask it to *"work the next issue"*.

Your job per cycle: review the PR (screenshots make it fast), merge or request changes. Change requests go as PR comments; the next run addresses them on the same branch.

**Exit criterion: 5 issues shipped through it. Live here for two weeks before continuing.**

## Phase 2 — Merge → TestFlight (Weekend 2, deterministic CI, zero AI)

1. Set up Fastlane (`templates/fastlane/`) with an **App Store Connect API key** (no 2FA pain in CI).
2. Pick a runner — for an indie: **your own Mac as a self-hosted GitHub Actions runner** (free, signing already works) or **Xcode Cloud** (25 free hrs/month). Avoid paid GitHub macOS runners.
3. Install `templates/github/workflows/testflight.yml`: push to `main` → bump build number → `fastlane beta` → TestFlight internal group.

This is plain CI on purpose: uploads should be boring and identical every time.

**Exit criterion: merging a PR puts a build on your phone in ~20 minutes, hands-free.**

## Phase 3 — Release agent (Weeks 3–4)

Install [`agents/release-agent`](../agents/release-agent/SKILL.md). Triggered only when you say *"prepare release X.Y"*. It drafts release notes from merged PRs, updates App Store Connect metadata, promotes the build to external testers, runs the submission checklist — and stops at the Submit button. After approval it sets up a phased release and watches crash diagnostics, pausing the rollout if crashes spike.

## Phase 4 — Orchestrator + feedback loop (Month 2)

- **[`queue-runner`](../agents/queue-runner/SKILL.md)** — scheduled nightly. If an agent-authored PR is already open, it does nothing (**WIP limit = 1**; the queue moves at your review speed — that's the design, not a bug). Otherwise it runs issue-worker on the next issue. Weekly digest: shipped / blocked / queue depth.
- **[`feedback-triage`](../agents/feedback-triage/SKILL.md)** — scheduled daily. Pulls TestFlight crash feedback and beta screenshots, clusters duplicates, files `triage` issues with repro details. **It never labels its own issues `agent-ready`** — you promote them.

The loop is now closed: you only triage and review; the system feeds itself.

---

## Recommendations

- **Start with an *update* to an existing app, not a new app.** Existing test suite + known architecture + small well-scoped issues = ideal agent food. For a new app: generate the architecture spec and issue backlog first (see the `product/` skills in [claude-code-apple-skills](https://github.com/rshankras/claude-code-apple-skills)), then feed the same pipeline.
- **Use real, deadline-driven work as the pilot cargo** (e.g., an OS-version readiness sweep) so the pipeline gets built by doing work you already need to do.
- Read [SAFETY.md](SAFETY.md) before turning anything on. The two human gates (merge, submit) are permanent.
