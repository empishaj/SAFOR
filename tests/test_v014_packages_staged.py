import json
import unittest
from pathlib import Path
from runtime.bootstrap_policy import compute_domain_package_digest

ROOT = Path(__file__).resolve().parents[1]


class V014PackagesStagedTests(unittest.TestCase):
    CASES = (
        ("v0.14.0/packages/factories/website-delivery/1.2.0/package.json", "1.2.0"),
        ("v0.14.0/packages/operating-models/website-team/1.2.0/package.json", "1.2.0"),
        ("v0.14.0/packages/factories/software-delivery/1.8.0-test.1/package.json", "1.8.0-test.1"),
        ("v0.14.0/packages/operating-models/saas-engineering/1.8.0-test.1/package.json", "1.8.0-test.1"),
        ("v0.14.0/packages/factories/book-production/1.1.0-test.1/package.json", "1.1.0-test.1"),
        ("v0.14.0/packages/operating-models/book-authoring/1.1.0-test.1/package.json", "1.1.0-test.1"),
    )

    def test_every_upgraded_package_has_v014_range_and_valid_digest(self):
        for relative, version in self.CASES:
            with self.subTest(relative=relative):
                package = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertEqual("0.14.0", package["schemaVersion"])
                self.assertEqual(version, package["version"])
                self.assertEqual("0.14.0", package["compatibility"]["framework"]["minimum"])
                self.assertEqual("0.15.0", package["compatibility"]["framework"]["maximumExclusive"])
                self.assertEqual(compute_domain_package_digest(package), package["integrity"]["contentDigest"])

    def test_provider_contracts_are_upgraded(self):
        for provider in ("github", "gitlab"):
            package = json.loads((ROOT / f"v0.14.0/providers/{provider}/0.6.0/package.json").read_text(encoding="utf-8"))
            self.assertEqual("0.14.0", package["schemaVersion"])
            self.assertEqual(">=0.14.0 <0.15.0", package["compatibility"]["kernel"])


if __name__ == "__main__":
    unittest.main()
