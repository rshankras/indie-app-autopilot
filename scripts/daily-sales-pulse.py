#!/usr/bin/env python3
"""Daily sales pulse: fetch yesterday's App Store daily sales report via the
asc-metadata MCP server, append to local history, compare to the trailing
7-day average, and post a macOS notification.

Deterministic companion to agents/daily-sales-pulse/SKILL.md — this script is
the unattended daily run (launchd/cron); the agent skill is for interactive
follow-ups. Zero dependencies beyond python3 and a configured asc-metadata MCP
server (binary path read from ~/.claude.json, vendor number from the server's
own config).
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta

STATE_DIR = os.path.join(
    os.environ.get("AUTOPILOT_DATA_DIR", os.path.expanduser("~/.indie-app-autopilot")),
    "daily-pulse",
)
HISTORY_PATH = os.path.join(STATE_DIR, "history.json")
LATEST_PATH = os.path.join(STATE_DIR, "latest.md")
HISTORY_KEEP_DAYS = 90
TRAILING_DAYS = 7


def mcp_binary():
    cfg = json.load(open(os.path.expanduser("~/.claude.json")))
    server = (cfg.get("mcpServers") or {}).get("asc-metadata")
    if not server or "command" not in server:
        sys.exit("asc-metadata MCP server not found in ~/.claude.json")
    return server["command"]


def fetch_daily_report(binary, report_date):
    """One JSON-RPC round-trip over stdio. Returns parsed report dict,
    'NOT_PUBLISHED' on HTTP 404, or raises on anything else."""
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "daily-sales-pulse", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "get_sales_report",
                    "arguments": {"frequency": "DAILY", "aggregateBy": "APP",
                                  "reportDate": report_date}}},
    ]
    proc = subprocess.Popen([binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)
    try:
        proc.stdin.write("".join(json.dumps(r) + "\n" for r in requests))
        proc.stdin.flush()
        deadline = datetime.now() + timedelta(seconds=45)
        while datetime.now() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == 2:
                result = msg.get("result", {})
                text = (result.get("content") or [{}])[0].get("text", "")
                if result.get("isError"):
                    if "404" in text:
                        return "NOT_PUBLISHED"
                    raise RuntimeError(f"get_sales_report failed: {text[:200]}")
                return json.loads(text)
        raise RuntimeError("timed out waiting for MCP response")
    finally:
        proc.kill()


def load_history():
    if os.path.exists(HISTORY_PATH):
        return json.load(open(HISTORY_PATH))
    return {"days": {}}


def save_history(history):
    cutoff = (date.today() - timedelta(days=HISTORY_KEEP_DAYS)).isoformat()
    history["days"] = {d: v for d, v in history["days"].items() if d >= cutoff}
    os.makedirs(STATE_DIR, exist_ok=True)
    json.dump(history, open(HISTORY_PATH, "w"), indent=2, sort_keys=True)


def to_day_entry(report):
    apps = {}
    for app in report.get("apps", []):
        apps[app["appleIdentifier"]] = {
            "title": (app.get("titles") or ["?"])[-1],
            "downloads": app.get("downloads", 0),
            "redownloads": app.get("redownloads", 0),
            "updates": app.get("updates", 0),
            "iapUnits": app.get("iapUnits", 0),
            "proceeds": app.get("proceeds", {}),
        }
    t = report.get("totals", {})
    return {"apps": apps,
            "totals": {"downloads": t.get("downloads", 0),
                       "redownloads": t.get("redownloads", 0),
                       "updates": t.get("updates", 0),
                       "iapUnits": t.get("iapUnits", 0),
                       "proceeds": t.get("proceeds", {})}}


def trailing_average(history, before_date, key="downloads"):
    days = sorted(d for d in history["days"] if d < before_date)[-TRAILING_DAYS:]
    if not days:
        return None, 0
    vals = [history["days"][d]["totals"][key] for d in days]
    return sum(vals) / len(vals), len(days)


def fmt_proceeds(proceeds):
    return " + ".join(f"{cur} {amt:.2f}" for cur, amt in sorted(proceeds.items()))


def compose(history, day, entry):
    avg, n = trailing_average(history, day)
    total = entry["totals"]["downloads"]
    if avg is None:
        vs = ""
    else:
        direction = "↑" if total > avg * 1.15 else "↓" if total < avg * 0.85 else "≈"
        vs = f" ({direction} {n}d avg {avg:.1f})"
    headline = f"Portfolio: {total} downloads{vs}"
    proceeds = entry["totals"]["proceeds"]
    if proceeds:
        headline += f" · {fmt_proceeds(proceeds)}"

    lines = []
    active = sorted(entry["apps"].values(), key=lambda a: -a["downloads"])
    for app in active:
        if not any([app["downloads"], app["redownloads"], app["updates"], app["iapUnits"]]):
            continue
        bits = [f"{app['downloads']} dl"]
        if app["redownloads"]:
            bits.append(f"{app['redownloads']} redl")
        if app["updates"]:
            bits.append(f"{app['updates']} upd")
        if app["iapUnits"]:
            bits.append(f"{app['iapUnits']} IAP ({fmt_proceeds(app['proceeds'])})")
        lines.append(f"- {app['title']}: {', '.join(bits)}")
    if not lines:
        lines = ["- no activity recorded — that's a complete pulse, not an error"]
    return headline, lines


def notify(title, message):
    safe_t = title.replace('"', "'")
    safe_m = message.replace('"', "'")
    subprocess.run(["osascript", "-e",
                    f'display notification "{safe_m}" with title "{safe_t}"'],
                   check=False)


def main():
    binary = mcp_binary()
    history = load_history()

    # Yesterday first; Apple publishes ~5-8am Pacific next day. Fall back one more day.
    report, day = None, None
    for offset in (1, 2):
        candidate = (date.today() - timedelta(days=offset)).isoformat()
        if candidate in history["days"]:
            print(f"{candidate} already in history; nothing new.")
            return
        fetched = fetch_daily_report(binary, candidate)
        if fetched != "NOT_PUBLISHED":
            report, day = fetched, candidate
            break
        print(f"{candidate}: not published yet")
    if report is None:
        notify("Sales Pulse", "No new daily report available yet (Apple delay)")
        return

    entry = to_day_entry(report)
    headline, lines = compose(history, day, entry)
    history["days"][day] = entry
    save_history(history)

    pretty = datetime.strptime(day, "%Y-%m-%d").strftime("%b %-d")
    body = f"# Sales Pulse — {pretty}\n\n{headline}\n\n" + "\n".join(lines) + "\n"
    with open(LATEST_PATH, "w") as f:
        f.write(body)
    print(body)
    notify(f"Sales Pulse — {pretty}", headline)


if __name__ == "__main__":
    main()
