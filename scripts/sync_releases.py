#!/usr/bin/env python3
"""Mirror validated public GitHub IPA releases into a static AltSource."""

import argparse
import hashlib
import json
import os
import plistlib
import shutil
import tempfile
import urllib.request
from pathlib import Path
from zipfile import ZipFile

USER_AGENT = "ncls-ios-distribution/1.0"


def read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def load_json_url(url: str):
    return json.loads(read_url(url))


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as temp:
        json.dump(value, temp, indent=2, ensure_ascii=False)
        temp.write("\n")
        temp_path = Path(temp.name)
    os.replace(temp_path, path)


def ipa_info(path: Path) -> dict:
    with ZipFile(path) as archive:
        info_files = [
            name for name in archive.namelist()
            if name.startswith("Payload/") and name.endswith(".app/Info.plist")
            and name.count("/") == 2
        ]
        if len(info_files) != 1:
            raise ValueError("IPA must contain exactly one app Info.plist")
        info = plistlib.loads(archive.read(info_files[0]))
        executable = info.get("CFBundleExecutable")
        app_prefix = info_files[0].removesuffix("Info.plist")
        if not executable or f"{app_prefix}{executable}" not in archive.namelist():
            raise ValueError("IPA has no app executable")
        if "iPhoneOS" not in info.get("CFBundleSupportedPlatforms", []):
            raise ValueError("IPA is not for an iPhone")
        privacy = {
            key: value for key, value in info.items()
            if key.endswith("UsageDescription") and isinstance(value, str)
        }
        return {
            "bundleIdentifier": info["CFBundleIdentifier"],
            "version": info["CFBundleShortVersionString"],
            "build": info["CFBundleVersion"],
            "privacy": privacy,
        }


def release_pair(release: dict):
    assets = release.get("assets", [])
    ipas = [asset for asset in assets if asset["name"].endswith(".ipa")]
    for ipa in ipas:
        stem = ipa["name"][:-4]
        metadata = next((asset for asset in assets if asset["name"] == stem + ".json"), None)
        if metadata:
            yield ipa, metadata


def publish_one(app: dict, release: dict, ipa_asset: dict, metadata_asset: dict,
                public: Path) -> bool:
    metadata = load_json_url(metadata_asset["browser_download_url"])
    if metadata.get("bundleIdentifier") != app["bundleIdentifier"]:
        return False
    version = str(metadata["version"])
    build = str(metadata["build"])
    if not version.replace(".", "").isdigit() or not build.isdigit():
        raise ValueError("Invalid version or build in release metadata")
    directory = public / "releases" / app["slug"] / f"{version}-{build}"
    manifest = directory / "release.json"
    if manifest.exists():
        existing = json.loads(manifest.read_text())
        if existing["sha256"] != metadata["sha256"]:
            raise ValueError(f"Published release changed: {directory}")
        return False

    directory.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".release-", dir=directory.parent))
    try:
        ipa_path = staging / "app.ipa"
        ipa_path.write_bytes(read_url(ipa_asset["browser_download_url"]))
        digest = hashlib.sha256(ipa_path.read_bytes()).hexdigest()
        if digest != metadata["sha256"] or ipa_path.stat().st_size != metadata["sizeBytes"]:
            raise ValueError("Release checksum or size mismatch")
        info = ipa_info(ipa_path)
        if any(info[key] != metadata[key] for key in ("bundleIdentifier", "version", "build")):
            raise ValueError("IPA Info.plist does not match release metadata")
        published_at = release["published_at"]
        release_manifest = {
            "bundleIdentifier": info["bundleIdentifier"],
            "version": version,
            "build": build,
            "publishedAt": published_at,
            "sizeBytes": ipa_path.stat().st_size,
            "sha256": digest,
            "privacy": info["privacy"],
        }
        (staging / "release.json").write_text(json.dumps(release_manifest, indent=2) + "\n")
        os.replace(staging, directory)
        print(f"Published {app['slug']} {version} ({build})")
        return True
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def rebuild_catalog(config: dict, public: Path, base_url: str) -> None:
    apps = []
    latest = {}
    for app in config["apps"]:
        versions = []
        for manifest in (public / "releases" / app["slug"]).glob("*/release.json"):
            item = json.loads(manifest.read_text())
            if item["bundleIdentifier"] != app["bundleIdentifier"]:
                raise ValueError(f"Unexpected bundle ID in {manifest}")
            version_dir = manifest.parent.name
            versions.append({
                "version": item["version"],
                "buildVersion": item["build"],
                "date": item["publishedAt"],
                "localizedDescription": "Versão distribuída pelo SideStore.",
                "downloadURL": f"{base_url}/releases/{app['slug']}/{version_dir}/app.ipa",
                "size": item["sizeBytes"],
                "minOSVersion": app.get("minOSVersion", "17.0"),
            })
        if not versions:
            continue
        versions.sort(key=lambda item: item["date"], reverse=True)
        newest = versions[0]
        newest_manifest = public / "releases" / app["slug"] / f"{newest['version']}-{newest['buildVersion']}" / "release.json"
        permissions = json.loads(newest_manifest.read_text())
        apps.append({
            "name": app["name"],
            "bundleIdentifier": app["bundleIdentifier"],
            "developerName": app["developerName"],
            "subtitle": app["subtitle"],
            "localizedDescription": app["localizedDescription"],
            "iconURL": f"{base_url}/{app['icon']}",
            "category": app["category"],
            "versions": versions,
            "appPermissions": {"entitlements": [], "privacy": permissions["privacy"]},
        })
        latest[app["slug"]] = newest
    if not apps:
        raise ValueError("No validated app releases to publish")
    source = {
        "name": config["name"],
        "subtitle": config["subtitle"],
        "description": config["description"],
        "website": config["website"],
        "apps": apps,
        "news": [],
    }
    atomic_json(public / "latest.json", latest)
    atomic_json(public / "source.json", source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", type=Path, default=Path(__file__).resolve().parents[1] / "public")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/apps.json")
    parser.add_argument("--base-url", default="https://ios.ncls.cc")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    args.public.mkdir(parents=True, exist_ok=True)
    for app in config["apps"]:
        api = f"https://api.github.com/repos/{app['githubRepo']}/releases?per_page=100"
        for release in load_json_url(api):
            if release.get("draft") or release.get("prerelease"):
                continue
            for ipa, metadata in release_pair(release):
                publish_one(app, release, ipa, metadata, args.public)
    rebuild_catalog(config, args.public, args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
