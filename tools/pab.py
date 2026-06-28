#!/usr/bin/env python3
"""pab.py — Personal Agent Builder host-binding hook entrypoint (cross-platform STUB).

Called by Claude Code (.claude/settings.json) and Codex CLI (.codex/config.toml) hooks.
This is the CROSS-PLATFORM entrypoint — it needs only `python` on PATH, NOT `bash`. On native
Windows the older `bash "$(git rev-parse ...)/tools/pab"` form fails (no bash on PATH); this
script removes that dependency. Unix/macOS users may still call the `tools/pab` bash wrapper.

Both hosts pass a JSON event on stdin (session_id, transcript_path, cwd, hook_event_name;
turn-scoped events also add turn_id; model is not guaranteed on every event). One entrypoint,
many host triggers — the action substrate is meant to be MCP (OpenCrab). See
skills/14-host-binding.md and docs/hooks-setup.md.

THIS IS A STUB: it only logs what it WOULD do and ALWAYS exits 0 (never blocks a tool or turn).
It does NOT stage anything yet. To go LIVE, replace the no-op branches below with OpenCrab MCP
calls (ingest_text pack_visibility=draft / pack_update) per spec/09-triggers.md and
spec/10-dedup-and-merge.md. Invariants when live: capture/mine = STAGE ONLY (G3); promotion only
in the Stop review board after human confirm (G5).

Subcommands: compile-adapter | capture [--from prompt|tool] | boundary-check | mine-and-review
"""
import sys, os, tempfile, datetime


def main():
    argv = sys.argv[1:]
    sub = argv[0] if argv else ""
    rest = " ".join(argv[1:])

    # Hook JSON arrives on stdin (may be empty when run manually). Read non-blockingly.
    payload = ""
    try:
        if not sys.stdin.isatty():
            payload = sys.stdin.read()
    except Exception:
        payload = ""

    log = os.environ.get("PAB_LOG") or os.path.join(tempfile.gettempdir(), "pab-hooks.log")
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with open(log, "a", encoding="utf-8") as f:
            f.write("{}\tpab {} {}\n".format(ts, sub, rest).rstrip() + "\n")
    except Exception:
        pass  # logging must never break the hook

    # STUB dispatch — intent only. Wire real OpenCrab staging here to go live.
    if sub == "compile-adapter":
        pass        # SessionStart: compile confirmed+scoped slices -> runtime adapter (skills/10)
    elif sub == "capture":
        pass        # UserPromptSubmit/PostToolUse: stage EvidenceItem / detect corrections (draft, G3)
    elif sub == "boundary-check":
        pass        # PreToolUse: enforce boundary before external/irreversible action (G5). STUB allows all.
    elif sub == "mine-and-review":
        pass        # Stop: mine transcript -> candidates -> Korean review board. Promotion ONLY here.
    else:
        pass

    return 0        # never block a tool or turn


if __name__ == "__main__":
    sys.exit(main())
