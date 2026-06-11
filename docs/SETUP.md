# Setup: Onboarding One App

One-time setup to put a single app repo on the pipeline. Budget ~2 hours for Phase 0 + 1, plus a weekend for TestFlight CI.

## Prerequisites

- macOS with Xcode installed; app builds locally
- `gh` CLI authenticated (`gh auth status`)
- [Claude Code](https://claude.com/claude-code) installed
- The app repo is on GitHub
- **A test target that runs headlessly** — verify before anything else:
  ```bash
  xcodebuild test -scheme <Scheme> -destination 'platform=iOS Simulator,name=iPhone 16'
  ```

## Step 1 — Install the agents

```bash
# Globally (all projects):
cp -r agents/* ~/.claude/skills/

# Or per-project:
cp -r agents/* /path/to/app-repo/.claude/skills/
```

## Step 2 — Bootstrap the app repo

```bash
./scripts/setup-app.sh /path/to/app-repo <Scheme>
```

This copies the issue template + TestFlight workflow + Fastlane templates into the app repo and creates the five pipeline labels on its GitHub repo.

## Step 3 — Fill in the placeholders

1. **`CLAUDE.md`** — the script appends `templates/CLAUDE.md.snippet`; replace `{{...}}` placeholders with the real build/test commands. The issue-worker reads this file every run; wrong commands = broken agent.
2. **`fastlane/Appfile`** — bundle ID, Apple ID, team ID.

## Step 4 — App Store Connect API key (for CI)

1. App Store Connect → Users and Access → Integrations → App Store Connect API → generate a **Team key** with App Manager role.
2. Store as GitHub Actions secrets on the app repo (never commit the .p8):
   ```bash
   gh secret set ASC_KEY_ID --body "<key id>"
   gh secret set ASC_ISSUER_ID --body "<issuer id>"
   gh secret set ASC_KEY_CONTENT --body "$(base64 -i AuthKey_XXXX.p8)"
   gh variable set APP_SCHEME --body "<Scheme>"
   ```

## Step 5 — CI runner (choose one)

**Option A — self-hosted runner on your own Mac (recommended for indies).** Free, and code signing already works on your machine. App repo → Settings → Actions → Runners → New self-hosted runner, follow the macOS instructions. The provided workflow targets `runs-on: self-hosted`.

**Option B — Xcode Cloud.** 25 free compute hrs/month, Apple-managed signing. Skip the workflow file and configure an Xcode Cloud workflow (branch `main` → TestFlight internal) instead.

## Step 6 — File the first issues

Use the "Agent task" issue template. Every issue needs: Goal (one sentence), Acceptance criteria (checkboxes), Out of scope, UI involved y/n. Start with 5–10 small ones (one screen / one behavior each).

Issues are born `needs-human`. Review each; when the spec is complete, relabel to `agent-ready`:

```bash
gh issue edit <n> --remove-label needs-human --add-label agent-ready
```

## Step 7 — First run

```bash
cd /path/to/app-repo
claude   # then: "work the next issue"
```

Review the PR it opens. Merge when satisfied. That's the loop.

## Troubleshooting

- **Agent can't build** → the build/test commands in the app repo's CLAUDE.md are wrong or incomplete. Fix there.
- **Agent goes `agent-blocked`** → it asked a question on the issue. Answer in a comment, relabel `agent-ready`.
- **TestFlight upload fails on signing** → run `fastlane beta` manually on the runner machine once; resolve signing interactively, then CI will work.
- **Simulator steps fail** → check the destination device name exists: `xcrun simctl list devices available`.
