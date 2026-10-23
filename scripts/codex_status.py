#!/usr/bin/env python3
"""Print a redacted, read-only status for the two local Codex profiles."""

import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ROUTER_PATH = HOME / "codex2-router/packages/codex2-router/router.py"
CODEX_BIN = HOME / ".local/bin/codex"
PROFILES = {"codex": HOME / ".codex-personal", "codex2": HOME / ".codex"}


def load_router():
    spec = importlib.util.spec_from_file_location("codex2_router_local", ROUTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Codex router is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def session_processes() -> dict[str, list[str]]:
    """Map only process profiles and tmux names; never return commands or env."""
    try:
        panes = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{session_name}|#{pane_pid}"],
            text=True, capture_output=True, timeout=3, check=True,
        ).stdout.splitlines()
        processes = subprocess.run(
            ["ps", "-eo", "pid=,ppid=,comm="], text=True,
            capture_output=True, timeout=3, check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return {name: [] for name in PROFILES}

    panes_by_pid = {}
    for row in panes:
        name, _, pid_text = row.partition("|")
        if pid_text.isdigit():
            panes_by_pid[int(pid_text)] = name
    parent = {}
    codex_pids = []
    for row in processes:
        parts = row.split(None, 2)
        if len(parts) != 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        pid, ppid = int(parts[0]), int(parts[1])
        parent[pid] = ppid
        if parts[2].startswith("codex"):
            codex_pids.append(pid)

    sessions = {name: set() for name in PROFILES}
    for pid in codex_pids:
        try:
            entries = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        profile = next((name for name, home in PROFILES.items()
                        if b"CODEX_HOME=" + os.fsencode(home) in entries), None)
        if profile is None:
            continue
        seen = set()
        ancestor = pid
        while ancestor in parent and ancestor not in seen:
            if ancestor in panes_by_pid:
                sessions[profile].add(panes_by_pid[ancestor])
                break
            seen.add(ancestor)
            ancestor = parent[ancestor]
    return {name: sorted(values) for name, values in sessions.items()}


def profile_status(router, home: Path, active_sessions: list[str]) -> dict:
    try:
        limits = router.read_limits(str(CODEX_BIN), home, 12)
        windows = []
        for key in ("primary", "secondary"):
            window = limits.get(key)
            if not isinstance(window, dict):
                continue
            used = window.get("usedPercent")
            if not isinstance(used, (int, float)) or isinstance(used, bool) or not 0 <= used <= 100:
                continue
            windows.append({
                "name": key,
                "remainingPercent": round(100 - used, 1),
                "resetsAt": window.get("resetsAt") if isinstance(window.get("resetsAt"), int) else None,
            })
        if not windows:
            raise ValueError("No rate-limit windows")
        remaining = min(window["remainingPercent"] for window in windows)
        return {
            "state": "limited" if remaining <= 0 else "available",
            "remainingPercent": remaining,
            "windows": windows,
            "activeSessions": active_sessions,
        }
    except Exception:
        return {
            "state": "unknown",
            "remainingPercent": None,
            "windows": [],
            "activeSessions": active_sessions,
        }


def main():
    sessions = session_processes()
    try:
        router = load_router()
    except Exception:
        router = None
    profiles = {
        name: profile_status(router, home, sessions[name]) if router else {
            "state": "unknown", "remainingPercent": None,
            "windows": [], "activeSessions": sessions[name],
        }
        for name, home in PROFILES.items()
    }
    print(json.dumps({
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "profiles": profiles,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
