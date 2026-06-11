#!/usr/bin/env bash
# setup-app.sh — bootstrap an app repo onto the indie-app-autopilot pipeline.
# Usage: ./scripts/setup-app.sh /path/to/app-repo <Scheme>
#
# Copies the issue template, TestFlight workflow, and Fastlane templates into
# the app repo, appends the CLAUDE.md snippet, and creates the pipeline labels
# on its GitHub repo. Idempotent: safe to re-run (skips files that exist).

set -euo pipefail

AUTOPILOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${1:?Usage: setup-app.sh /path/to/app-repo <Scheme>}"
SCHEME="${2:?Usage: setup-app.sh /path/to/app-repo <Scheme>}"

[ -d "$APP_DIR/.git" ] || { echo "✗ $APP_DIR is not a git repository"; exit 1; }
command -v gh >/dev/null || { echo "✗ gh CLI is required (brew install gh)"; exit 1; }

echo "→ Onboarding $(basename "$APP_DIR") (scheme: $SCHEME)"

copy_if_absent() {  # $1 = source, $2 = destination
  if [ -e "$2" ]; then
    echo "  · skip (exists): ${2#"$APP_DIR"/}"
  else
    mkdir -p "$(dirname "$2")"
    cp "$1" "$2"
    echo "  ✓ added: ${2#"$APP_DIR"/}"
  fi
}

# 1. GitHub issue template + workflow
copy_if_absent "$AUTOPILOT_DIR/templates/github/ISSUE_TEMPLATE/agent-task.yml" \
               "$APP_DIR/.github/ISSUE_TEMPLATE/agent-task.yml"
copy_if_absent "$AUTOPILOT_DIR/templates/github/workflows/testflight.yml" \
               "$APP_DIR/.github/workflows/testflight.yml"

# 2. Fastlane
copy_if_absent "$AUTOPILOT_DIR/templates/fastlane/Fastfile" "$APP_DIR/fastlane/Fastfile"
copy_if_absent "$AUTOPILOT_DIR/templates/fastlane/Appfile.template" "$APP_DIR/fastlane/Appfile"

# 3. CLAUDE.md snippet (append once, with scheme pre-filled)
if grep -q "indie-app-autopilot" "$APP_DIR/CLAUDE.md" 2>/dev/null; then
  echo "  · skip (already onboarded): CLAUDE.md"
else
  { [ -f "$APP_DIR/CLAUDE.md" ] && printf "\n"; \
    sed "s/{{SCHEME}}/$SCHEME/g" "$AUTOPILOT_DIR/templates/CLAUDE.md.snippet"; } >> "$APP_DIR/CLAUDE.md"
  echo "  ✓ appended snippet to CLAUDE.md (fill remaining {{...}} placeholders)"
fi

# 4. Labels on the GitHub repo
echo "→ Creating labels"
REPO=$(git -C "$APP_DIR" remote get-url origin 2>/dev/null | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##') \
  || { echo "✗ no GitHub origin remote"; exit 1; }
python3 - "$AUTOPILOT_DIR/templates/github/labels.json" <<'PY' | while IFS=$'\t' read -r name color desc; do
import json, sys
for l in json.load(open(sys.argv[1])):
    print(f"{l['name']}\t{l['color']}\t{l['description']}")
PY
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null \
    && echo "  ✓ label: $name"
done

cat <<NEXT

Done. Next steps (docs/SETUP.md has details):
  1. Fill the {{...}} placeholders in CLAUDE.md and fastlane/Appfile
  2. Set CI secrets:  gh secret set ASC_KEY_ID / ASC_ISSUER_ID / ASC_KEY_CONTENT
                      gh variable set APP_SCHEME --body "$SCHEME"
  3. Register a self-hosted runner (or use Xcode Cloud) for the TestFlight workflow
  4. Verify tests run:  xcodebuild test -scheme $SCHEME -destination 'platform=iOS Simulator,name=iPhone 16'
  5. File 5-10 issues with the 'Agent task' template, promote one to agent-ready
  6. In the app repo, ask Claude Code to: "work the next issue"
NEXT
