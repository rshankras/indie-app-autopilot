# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Indie App Autopilot is the **action layer** for issue-driven iOS app development: agent operating procedures (SKILL.md format), CI templates, and an app-onboarding script. The companion **knowledge layer** is [claude-code-apple-skills](https://github.com/rshankras/claude-code-apple-skills).

This repo contains agent definitions, templates, shell scripts, and docs — no app code.

## Architecture

| Directory | Consumer | Rule |
|---|---|---|
| `agents/` | Claude (reads SKILL.md at runtime) | One folder per agent. SKILL.md + YAML frontmatter (`name`, `description`, `allowed-tools`). Same conventions as claude-code-apple-skills. |
| `templates/` | App repos (copied by setup script) | Never read by agents at runtime. Placeholders use `{{PLACEHOLDER}}` syntax. |
| `scripts/` | Humans (one-time bootstrap) | Bash, no dependencies beyond `gh`, `git`, `python3`. |
| `docs/` | Humans | PIPELINE.md (build plan), SETUP.md (onboarding), SAFETY.md (contract). |

## Conventions

- Agent names and folders: `kebab-case`.
- Every agent SKILL.md must specify: **Trigger**, **Preconditions**, **Steps** (numbered), **Stop conditions**, **What this agent never does**.
- The safety rules in `docs/SAFETY.md` are load-bearing. Never edit SAFETY.md, or weaken stop conditions in any agent, without the maintainer explicitly asking for that change.
- Shell snippets in agent steps must be copy-runnable (`gh`, `xcodebuild`, `git` — exact flags, no pseudo-commands).
- Templates must stay generic: no app names, bundle IDs, team IDs, or personal data. Those arrive via setup-app.sh arguments or CI secrets.

## Testing changes

- `bash -n scripts/setup-app.sh` for syntax; run against a scratch repo for behavior.
- Validate YAML templates (`templates/github/**/*.yml`) parse before committing.
- Agent SKILL.md changes: dry-run the agent on a test app (e.g., CalculatorAppWithTests) before relying on it against a live app.
