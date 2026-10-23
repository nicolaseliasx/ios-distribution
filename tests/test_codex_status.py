import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "codex_status.py"
spec = importlib.util.spec_from_file_location("codex_status", SCRIPT)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)


class CodexStatusTests(unittest.TestCase):
    def test_remaining_quota_and_no_credential_fields(self):
        class Router:
            @staticmethod
            def read_limits(*_args):
                return {
                    "primary": {"usedPercent": 25, "resetsAt": 123, "token": "secret"},
                    "secondary": {"usedPercent": 80, "resetsAt": 456, "email": "private"},
                }

        result = status.profile_status(Router(), Path("/tmp/profile"), ["work"])
        self.assertEqual(result["remainingPercent"], 20)
        self.assertEqual(result["state"], "available")
        self.assertEqual(result["activeSessions"], ["work"])
        self.assertEqual(set(result), {"state", "remainingPercent", "windows", "activeSessions"})
        self.assertEqual(set(result["windows"][0]), {"name", "remainingPercent", "resetsAt"})

    def test_failed_quota_read_is_unknown(self):
        class Router:
            @staticmethod
            def read_limits(*_args):
                raise RuntimeError("secret details")

        result = status.profile_status(Router(), Path("/tmp/profile"), [])
        self.assertEqual(result["state"], "unknown")
        self.assertEqual(result["windows"], [])


if __name__ == "__main__":
    unittest.main()
