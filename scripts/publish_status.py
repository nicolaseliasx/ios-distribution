#!/usr/bin/env python3
"""Publish a small, credential-free Codex status file for the iPhone widget."""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def percent(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(max(0.0, min(100.0, float(value))), 1) if math.isfinite(value) else None


def profile_summary(value: object) -> dict:
    profile = value if isinstance(value, dict) else {}
    windows = profile.get("windows")
    windows = windows if isinstance(windows, list) else []
    named = {
        item.get("name"): item for item in windows
        if isinstance(item, dict) and item.get("name") in ("primary", "secondary")
    }
    state = profile.get("state")
    sessions = profile.get("activeSessions")
    return {
        "state": state if state in ("available", "limited") else "unknown",
        "remainingPercent": percent(profile.get("remainingPercent")),
        "shortRemainingPercent": percent(named.get("primary", {}).get("remainingPercent")),
        "longRemainingPercent": percent(named.get("secondary", {}).get("remainingPercent")),
        "activeSessionCount": len(sessions) if isinstance(sessions, list) else 0,
    }


def public_status(value: dict) -> dict:
    checked_at = value.get("checkedAt")
    if not isinstance(checked_at, str):
        raise ValueError("Missing status timestamp")
    checked_ms = round(datetime.fromisoformat(checked_at.replace("Z", "+00:00")).timestamp() * 1000)
    profiles = value.get("profiles")
    profiles = profiles if isinstance(profiles, dict) else {}
    return {
        "checkedAt": checked_ms,
        "codex": profile_summary(profiles.get("codex")),
        "codex2": profile_summary(profiles.get("codex2")),
    }


def publish(path: Path, status: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        json.dump(status, temp, ensure_ascii=False, separators=(",", ":"))
        temp.write("\n")
        temp_path = Path(temp.name)
    os.chmod(temp_path, 0o644)
    os.replace(temp_path, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "public/status.json")
    args = parser.parse_args()
    helper = Path(__file__).with_name("codex_status.py")
    result = subprocess.run(
        [sys.executable, str(helper)], capture_output=True, text=True,
        timeout=45, check=True,
    )
    publish(args.output, public_status(json.loads(result.stdout)))


if __name__ == "__main__":
    main()
