import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import evaluate_k10a_binding_gate

ROOT = Path(__file__).resolve().parents[1]


class K10ABindingGateV014Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT / "v0.14.0/package-catalog.json").read_text(encoding="utf-8"))
        cls.website = next(p for p in catalog["creationProfiles"] if p["creationType"] == "WEBSITE")

    def default_binding(self):
        return {
            "factoryPackageId": self.website["defaultFactoryPackageId"],
            "operatingModelPackageId": self.website["defaultOperatingModelPackageId"],
        }

    def premium_binding(self):
        return {
            "factoryPackageId": "safor.factory.website-premium",
            "operatingModelPackageId": self.website["defaultOperatingModelPackageId"],
        }

    def test_default_binding_skips_k10a(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.default_binding(),
            access_verified=True,
            compatibility_verified=True,
        )
        self.assertEqual("SKIP_DEFAULT_BINDING", result["route"])
        self.assertFalse(result["invokeK10A"])
        self.assertTrue(result["canProceedToK11"])
        self.assertFalse(result["activeBindingMutationAllowed"])

    def test_existing_default_binding_never_creates_redundant_question(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.default_binding(),
            access_verified=True,
            compatibility_verified=True,
            existing_binding=self.default_binding(),
            prior_decision_reusable=False,
        )
        self.assertEqual("SKIP_DEFAULT_BINDING", result["route"])
        self.assertFalse(result["invokeK10A"])
        self.assertTrue(result["canProceedToK11"])

    def test_unchanged_nondefault_binding_reuses_valid_prior_decision(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.premium_binding(),
            access_verified=True,
            compatibility_verified=True,
            existing_binding=self.premium_binding(),
            prior_decision_reusable=True,
        )
        self.assertEqual("REUSE_UNCHANGED_BINDING_DECISION", result["route"])
        self.assertFalse(result["invokeK10A"])
        self.assertTrue(result["canProceedToK11"])

    def test_changed_compatible_binding_requires_k10a(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.premium_binding(),
            access_verified=True,
            compatibility_verified=True,
            existing_binding=self.default_binding(),
        )
        self.assertEqual("REQUIRE_HUMAN_APPROVAL", result["route"])
        self.assertTrue(result["invokeK10A"])
        self.assertFalse(result["canProceedToK11"])
        self.assertEqual("WAITING_HUMAN_PACKAGE_BINDING_APPROVAL", result["outcome"])

    def test_approved_k10a_only_authorizes_k11_materialization(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.premium_binding(),
            access_verified=True,
            compatibility_verified=True,
            existing_binding=self.default_binding(),
            human_decision="APPROVED",
        )
        self.assertTrue(result["invokeK10A"])
        self.assertTrue(result["canProceedToK11"])
        self.assertFalse(result["activeBindingMutationAllowed"])
        self.assertEqual("K10A_APPROVED_FOR_K11_MATERIALIZATION", result["outcome"])

    def test_denied_k10a_preserves_last_valid_binding(self):
        result = evaluate_k10a_binding_gate(
            self.website,
            self.premium_binding(),
            access_verified=True,
            compatibility_verified=True,
            existing_binding=self.default_binding(),
            human_decision="DENIED",
        )
        self.assertTrue(result["invokeK10A"])
        self.assertFalse(result["canProceedToK11"])
        self.assertEqual("K10A_DENIED_PRESERVE_LAST_VALID_BINDING", result["outcome"])

    def test_invalid_binding_blocks_before_human_approval(self):
        for access_verified, compatibility_verified in ((False, True), (True, False)):
            with self.subTest(
                access_verified=access_verified,
                compatibility_verified=compatibility_verified,
            ):
                result = evaluate_k10a_binding_gate(
                    self.website,
                    self.premium_binding(),
                    access_verified=access_verified,
                    compatibility_verified=compatibility_verified,
                    existing_binding=self.default_binding(),
                )
                self.assertEqual("BLOCK_INVALID_BINDING", result["route"])
                self.assertFalse(result["invokeK10A"])
                self.assertFalse(result["canProceedToK11"])

    def test_k10a_is_reachable_between_k10_and_k11(self):
        master = json.loads((ROOT / "v0.14.0/SAFOR-MASTER.json").read_text(encoding="utf-8"))
        bootstrap = next(p for p in master["controlPlane"]["phases"] if p["id"] == "BOOTSTRAP")
        self.assertLess(bootstrap["actions"].index("K10"), bootstrap["actions"].index("K10A"))
        self.assertLess(bootstrap["actions"].index("K10A"), bootstrap["actions"].index("K11"))

        route = next(
            r
            for r in master["controlPlane"]["conditionalActionRoutes"]
            if r["id"] == "BOOTSTRAP-K10A-PACKAGE-BINDING"
        )
        self.assertEqual("K10", route["predecessor"])
        self.assertEqual("K10A", route["actionId"])
        self.assertEqual("K11", route["successor"])
        self.assertEqual(
            "SKIP_K10A_AND_CONTINUE_TO_K11",
            route["routes"]["SKIP_DEFAULT_BINDING"]["effect"],
        )
        self.assertEqual(
            "BLOCK_BEFORE_K10A_AND_PRESERVE_LAST_VALID_BINDING",
            route["routes"]["BLOCK_INVALID_BINDING"]["effect"],
        )

    def test_every_executable_action_is_reachable_from_a_phase(self):
        master = json.loads((ROOT / "v0.14.0/SAFOR-MASTER.json").read_text(encoding="utf-8"))
        action_ids = {a["id"] for a in master["controlPlane"]["actions"]}
        phase_actions = {
            action_id
            for phase in master["controlPlane"]["phases"]
            for action_id in phase["actions"]
        }
        self.assertEqual(set(), action_ids - phase_actions)


if __name__ == "__main__":
    unittest.main()
