import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class V014ReleaseTests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_manifest_evidence_and_version_align(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        evidence = self.load(f"RELEASE-EVIDENCE-{VERSION}.json")
        self.assertEqual(VERSION, manifest["version"])
        self.assertEqual(VERSION, evidence["version"])
        self.assertEqual("v0.14.0", manifest["sourceRoot"])
        self.assertEqual("RELEASE_CANDIDATE", manifest["status"])

    def test_checksum_file_covers_all_release_artifacts(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        checksums = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in (ROOT / manifest["checksumFile"]).read_text(encoding="utf-8").splitlines() if line.strip()}
        evidence = self.load(manifest["releaseEvidenceRef"])
        self.assertEqual(7, len(evidence["artifacts"]))
        for artifact in evidence["artifacts"]:
            actual = hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest()
            self.assertEqual(actual, artifact["sha256"])
            self.assertEqual(actual, checksums[artifact["path"]])

    def test_open_evidence_boundaries_remain_explicit(self):
        manifest = self.load("RELEASE-MANIFEST.json")
        for blocker in ("V014_ISOLATED_REAL_GIT_END_TO_END_ACCEPTANCE", "V014_REFERENCE_PROJECT_MIGRATION_ACCEPTANCE", "V014_CROSS_HOST_HUMAN_GO_ACCEPTANCE", "V014_COGNITIVE_LOAD_EMPIRICAL_ACCEPTANCE"):
            self.assertIn(blocker, manifest["gaBlockers"])


if __name__ == "__main__":
    unittest.main()
