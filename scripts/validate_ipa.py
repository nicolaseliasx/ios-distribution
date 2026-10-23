#!/usr/bin/env python3
"""Validate an unsigned iPhone IPA and emit public release metadata."""

import hashlib
import json
import plistlib
import sys
from pathlib import Path
from zipfile import ZipFile


def main(path: Path) -> None:
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        info_path = "Payload/ProxmoxAppTest.app/Info.plist"
        if info_path not in names:
            raise SystemExit("IPA is missing Info.plist")
        info = plistlib.loads(archive.read(info_path))
        executable = info.get("CFBundleExecutable")
        if not executable or f"Payload/ProxmoxAppTest.app/{executable}" not in names:
            raise SystemExit("IPA is missing its executable")
        if info.get("CFBundleIdentifier") != "cc.ncls.iosdist.proxmoxapptest":
            raise SystemExit("Unexpected bundle identifier")
        if info.get("CFBundleSupportedPlatforms") != ["iPhoneOS"]:
            raise SystemExit("IPA is not built for a physical iPhone")

    with path.open("rb") as ipa_file:
        digest = hashlib.file_digest(ipa_file, "sha256").hexdigest()

    metadata = {
        "bundleIdentifier": info["CFBundleIdentifier"],
        "version": info["CFBundleShortVersionString"],
        "build": info["CFBundleVersion"],
        "sizeBytes": path.stat().st_size,
        "sha256": digest,
    }
    output = path.with_suffix(".json")
    output.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_ipa.py <ipa>")
    main(Path(sys.argv[1]))
