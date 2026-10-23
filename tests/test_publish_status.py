import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_status.py"
spec = importlib.util.spec_from_file_location("publish_status", SCRIPT)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class PublicStatusTests(unittest.TestCase):
    def test_redacts_credentials_names_and_window_metadata(self):
        private = {
            "checkedAt": "2026-10-23T18:54:02Z",
            "token": "SECRET",
            "profiles": {
                "codex": {
                    "state": "available", "remainingPercent": 18,
                    "activeSessions": ["PRIVATE-SESSION"],
                    "windows": [
                        {"name": "primary", "remainingPercent": 52, "resetsAt": 123, "email": "PRIVATE-EMAIL"},
                        {"name": "secondary", "remainingPercent": 18, "resetsAt": 456},
                    ],
                },
                "codex2": {"state": "limited", "remainingPercent": 0, "activeSessions": []},
            },
        }
        public = status.public_status(private)
        self.assertEqual(public["codex"]["activeSessionCount"], 1)
        self.assertEqual(public["codex"]["shortRemainingPercent"], 52)
        self.assertEqual(public["codex2"]["state"], "limited")
        payload = json.dumps(public)
        for secret in ("SECRET", "PRIVATE-SESSION", "PRIVATE-EMAIL", "resetsAt"):
            self.assertNotIn(secret, payload)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "status.json"
            status.publish(target, public)
            self.assertEqual(json.loads(target.read_text()), public)

    def test_invalid_profile_is_unknown(self):
        public = status.public_status({"checkedAt": "2026-10-23T18:54:02+00:00", "profiles": {}})
        self.assertEqual(public["codex"]["state"], "unknown")
        self.assertIsNone(public["codex"]["remainingPercent"])
        self.assertEqual(public["codex2"]["activeSessionCount"], 0)


if __name__ == "__main__":
    unittest.main()
