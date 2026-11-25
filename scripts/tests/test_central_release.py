import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("central_release", Path(__file__).resolve().parents[1] / "central_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class CentralReleaseTest(unittest.TestCase):
    def test_guard_rejects_existing_version(self):
        with patch.object(release, "pom_urls", return_value=["url"]), patch.object(release, "exists", return_value=True):
            with self.assertRaises(RuntimeError):
                release.guard("1.2.3")

    def test_kmp_and_jvm_poms(self):
        with patch.object(release, "modules", return_value={"a": {"publication": "kmp"}, "b": {"publication": "jvm"}}):
            urls = list(release.pom_urls("1.2.3"))
            self.assertEqual(len(urls), 3)
            self.assertTrue(any("/a-jvm/" in url for url in urls))

    def test_failed_portal_never_certifies(self):
        deployment = "b7e2ce74-02c5-46e3-84c2-a15c283abdec"
        with patch.object(release, "status", return_value={"deploymentId": deployment, "deploymentName": "toolkit-1.2.3", "deploymentState": "FAILED"}):
            with self.assertRaises(RuntimeError):
                release.wait(deployment, "v1.2.3", "sha")

    def test_remote_success(self):
        with patch.object(release, "pom_urls", return_value=["url"]), patch.object(release, "exists", return_value=True):
            release.remote("1.2.3")

    def test_publication_and_consumer_are_separate(self):
        deployment = "b7e2ce74-02c5-46e3-84c2-a15c283abdec"
        state = {"deploymentId": deployment, "deploymentName": "toolkit-1.2.3", "deploymentState": "PUBLISHED", "purls": ["pkg:maven/org.evoleq.toolkit/a@1.2.3"]}
        with patch.object(release, "status", return_value=state), patch.object(release, "modules", return_value={"a": {"publication": "jvm"}}), patch.object(release, "write") as write:
            release.wait(deployment, "v1.2.3", "sha")
            record = write.call_args.args[1]
            self.assertFalse(record["consumerVerified"])
            with patch.object(release, "read", return_value=record):
                release.complete("v1.2.3")
            self.assertTrue(write.call_args.args[1]["consumerVerified"])
