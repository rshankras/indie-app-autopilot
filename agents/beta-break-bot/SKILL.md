---
name: beta-break-bot
description: When a new Xcode or OS beta drops, rebuilds every app in the portfolio against the new SDK and reports compile errors, new deprecations, and new warnings per app. Use when a beta is released or when asked "what does beta N break". Read-only toward the apps — it reports, it never fixes.
allowed-tools: [Read, Glob, Grep, Bash]
---

# Beta-Break Bot

Answers one question after every beta drop: **which of my apps does this beta break, and how badly?** Output feeds the issue queue; fixes go through issue-worker like any other change.

## Trigger

A new Xcode/iOS beta is installed (human says "Xcode beta N is out, run the sweep"), or a schedule that checks `xcodebuild -version` against the last recorded sweep.

## Preconditions

- The beta Xcode is installed. Confirm which is active: `xcode-select -p` and `xcodebuild -version`. If both release and beta are installed, use `DEVELOPER_DIR` to target the beta explicitly — never silently build with the wrong toolchain.
- A portfolio list exists (repo paths + schemes), provided by the human or an ops config file. No list → ask, don't guess.

## Steps

1. **Record the environment:** Xcode version/build, SDK versions, date.
2. **Per app, in sequence:**
   ```bash
   DEVELOPER_DIR=/Applications/Xcode-beta.app xcodebuild build \
     -scheme <Scheme> -destination 'generic/platform=iOS' \
     2>&1 | tee /tmp/beta-sweep-<app>.log
   ```
   Classify the result: ❌ fails to compile · ⚠️ new deprecations/warnings vs the previous sweep's log · ✅ clean. If the build succeeds, also run the test suite and record failures separately.
3. **Diff against the previous sweep** (keep logs per Xcode build): only *new* warnings count — longstanding ones are noise.
4. **Report:** one table — app · status · error/warning count · the most severe finding verbatim. Order worst-first.
5. **File issues (optional, on request):** for each ❌, file an issue in that app's repo using the agent-task template with the compiler output as context, labeled `needs-human` (a human scopes it before it becomes `agent-ready`).

## Stop conditions

- An app missing locally or failing to `git pull` cleanly → skip it, note it in the report, continue with the rest.
- Never modify app code, project settings, or dependencies — this agent reports; issue-worker fixes.

## What this agent never does

Fix code · bump deployment targets or dependencies · commit anything to app repos · run against a dirty working tree without flagging it in the report.
