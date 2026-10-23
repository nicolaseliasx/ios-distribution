import hashlib
import io
import json
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from scripts import sync_releases


APP = {
    "slug": "proxmox-app-test",
    "name": "ProxmoxAppTest",
    "bundleIdentifier": "cc.ncls.iosdist.proxmoxapptest",
    "developerName": "nicolas",
    "subtitle": "Test",
    "localizedDescription": "Test app",
    "icon": "icons/proxmox-app-test.png",
    "category": "utilities",
}
RELEASE = {"published_at": "2026-10-23T17:24:23Z"}
IPA_ASSET = {"browser_download_url": "https://example.test/app.ipa"}
META_ASSET = {"browser_download_url": "https://example.test/app.json"}


def make_ipa() -> bytes:
    output = io.BytesIO()
    info = {
        "CFBundleIdentifier": APP["bundleIdentifier"],
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "CFBundleExecutable": "ProxmoxAppTest",
        "CFBundleSupportedPlatforms": ["iPhoneOS"],
    }
    with ZipFile(output, "w") as archive:
        archive.writestr("Payload/ProxmoxAppTest.app/Info.plist", plistlib.dumps(info))
        archive.writestr("Payload/ProxmoxAppTest.app/ProxmoxAppTest", b"binary")
    return output.getvalue()


class SyncReleasesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.public = Path(self.temp.name)
        self.ipa = make_ipa()
        self.metadata = {
            "bundleIdentifier": APP["bundleIdentifier"],
            "version": "0.1.0",
            "build": "1",
            "sha256": hashlib.sha256(self.ipa).hexdigest(),
            "sizeBytes": len(self.ipa),
        }

    def tearDown(self):
        self.temp.cleanup()

    def publish(self):
        with patch.object(sync_releases, "load_json_url", return_value=self.metadata), \
                patch.object(sync_releases, "read_url", return_value=self.ipa):
            return sync_releases.publish_one(
                APP, RELEASE, IPA_ASSET, META_ASSET, self.public
            )

    def test_verified_release_enters_catalog_and_is_idempotent(self):
        self.assertTrue(self.publish())
        self.assertFalse(self.publish())
        config = {"name": "NCLS iOS", "subtitle": "Test", "description": "Test",
                  "website": "https://ios.ncls.cc", "apps": [APP]}
        sync_releases.rebuild_catalog(config, self.public, "https://ios.ncls.cc")
        source = json.loads((self.public / "source.json").read_text())
        item = source["apps"][0]["versions"][0]
        self.assertEqual(item["version"], "0.1.0")
        self.assertEqual(item["buildVersion"], "1")
        self.assertEqual(item["size"], len(self.ipa))
        self.assertEqual(item["downloadURL"],
                         "https://ios.ncls.cc/releases/proxmox-app-test/0.1.0-1/app.ipa")

    def test_bad_checksum_is_not_published(self):
        self.metadata["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.publish()
        self.assertFalse((self.public / "releases" / APP["slug"] / "0.1.0-1").exists())


if __name__ == "__main__":
    unittest.main()
