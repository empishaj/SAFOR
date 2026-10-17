import copy
import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_active_conditional_requirements,
    evaluate_domain_package_pair,
    validate_factory_contract_consistency,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class WebsiteFactory160Tests(unittest.TestCase):
    def setUp(self):
        self.factory = load_json(
            "v0.13.0/packages/factories/software-delivery/1.6.0/package.json"
        )
        self.om = load_json(
            "v0.13.0/packages/operating-models/saas-engineering/1.6.0/package.json"
        )
        self.nodes = {
            node["id"]: node
            for node in self.factory["model"]["flowGraph"]["nodes"]
        }

    def test_factory_contract_is_internally_consistent(self):
        result = validate_factory_contract_consistency(self.factory)
        self.assertTrue(result["valid"], result["errors"])

    def test_strategic_investment_is_not_a_hard_factory_requirement(self):
        counterpart = self.factory["compatibility"]["counterpart"]
        self.assertNotIn("strategic_investment", counterpart["requiredAuthorities"])
        self.assertNotIn("strategic_investment", self.factory["exports"]["authorities"])

    def test_conditional_authorities_are_not_base_pair_requirements(self):
        required = set(self.factory["compatibility"]["counterpart"]["requiredAuthorities"])
        conditional = {
            item["authorityId"]
            for item in self.factory["model"]["compatibilityContract"]["conditionalAuthorities"]
        }
        self.assertTrue(required.isdisjoint(conditional))
        self.assertEqual(
            {"product_scope_approval", "business_outcome_acceptance"},
            required,
        )

    def test_missing_conditional_release_authority_does_not_break_base_compatibility(self):
        om = copy.deepcopy(self.om)
        om["exports"]["authorities"] = [
            authority
            for authority in om["exports"]["authorities"]
            if authority != "production_release_approval"
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)
        result = evaluate_domain_package_pair(
            self.factory, om, "0.13.0-rc.2", "SOFTWARE_WEBSITE"
        )
        self.assertTrue(result["compatible"], result)

    def test_missing_conditional_release_authority_fails_when_condition_activates(self):
        om = copy.deepcopy(self.om)
        om["exports"]["authorities"] = [
            authority
            for authority in om["exports"]["authorities"]
            if authority != "production_release_approval"
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)
        result = evaluate_active_conditional_requirements(
            self.factory, om, {"PRODUCTION_AND_MATERIAL_RISK"}
        )
        self.assertFalse(result["satisfied"])
        self.assertEqual(
            ["production_release_approval"],
            result["missingAuthorities"],
        )

    def test_incident_recovery_capabilities_are_conditionally_enforced(self):
        om = copy.deepcopy(self.om)
        om["exports"]["capabilities"] = [
            capability
            for capability in om["exports"]["capabilities"]
            if capability not in {"incident_response", "recovery_execution"}
        ]
        om["integrity"]["contentDigest"] = compute_domain_package_digest(om)

        base = evaluate_domain_package_pair(
            self.factory, om, "0.13.0-rc.2", "SOFTWARE_WEBSITE"
        )
        self.assertTrue(base["compatible"], base)

        active = evaluate_active_conditional_requirements(
            self.factory, om, {"INCIDENT_OR_SERVICE_DEGRADATION"}
        )
        self.assertFalse(active["satisfied"])
        self.assertEqual(
            ["incident_response", "recovery_execution"],
            active["missingCapabilities"],
        )

    def test_security_and_quality_are_shifted_left_before_implementation(self):
        self.assertEqual(
            "QUALITY_SECURITY_REQUIREMENTS",
            self.nodes["SW-02"]["workItemType"],
        )
        self.assertIn("SECURITY_REQUIREMENTS", self.nodes["SW-02"]["produces"])
        self.assertIn("QUALITY_REQUIREMENTS", self.nodes["SW-02"]["produces"])
        self.assertIn("THREAT_MODEL", self.nodes["SW-03"]["produces"])
        self.assertEqual(["SW-03"], self.nodes["SW-04"]["dependsOn"])

    def test_implementation_produces_continuous_verification_and_supply_chain_evidence(self):
        produced = set(self.nodes["SW-04"]["produces"])
        self.assertTrue({
            "BUILD_EVIDENCE",
            "DEPENDENCY_INVENTORY",
            "SBOM",
            "BUILD_PROVENANCE",
            "CONTINUOUS_VERIFICATION_EVIDENCE",
        }.issubset(produced))
        minimum = set(
            self.factory["model"]["continuousVerificationContract"]["perChangeMinimum"]
        )
        self.assertTrue({
            "BUILD",
            "UNIT_OR_EQUIVALENT_FAST_TESTS",
            "STATIC_QUALITY_CHECKS",
            "SECRET_SCAN",
            "DEPENDENCY_STATUS_CHECK",
        }.issubset(minimum))

    def test_independent_verification_is_not_first_test_point(self):
        self.assertEqual(
            "INDEPENDENT_VERIFICATION",
            self.nodes["SW-05"]["workItemType"],
        )
        self.assertIn(
            "CONTINUOUS_VERIFICATION_EVIDENCE",
            self.nodes["SW-04"]["produces"],
        )
        self.assertEqual(["SW-04"], self.nodes["SW-05"]["dependsOn"])

    def test_release_deployment_activation_and_operation_are_distinct(self):
        self.assertEqual("RELEASE", self.nodes["SW-07"]["workItemType"])
        self.assertEqual("DEPLOYMENT", self.nodes["SW-08"]["workItemType"])
        self.assertEqual("ACTIVATION", self.nodes["SW-09"]["workItemType"])
        self.assertEqual("OPERATE_OBSERVE", self.nodes["SW-10"]["workItemType"])
        self.assertEqual(["SW-07"], self.nodes["SW-08"]["dependsOn"])
        self.assertEqual(["SW-08"], self.nodes["SW-09"]["dependsOn"])
        self.assertEqual(["SW-09"], self.nodes["SW-10"]["dependsOn"])

    def test_recovery_and_vulnerability_response_are_event_driven_side_paths(self):
        self.assertEqual(
            "INCIDENT_OR_SERVICE_DEGRADATION",
            self.nodes["SW-11"]["activationCondition"],
        )
        self.assertEqual(
            "POST_RELEASE_VULNERABILITY_OR_SECURITY_DEFECT",
            self.nodes["SW-12"]["activationCondition"],
        )
        self.assertEqual(["SW-10"], self.nodes["SW-11"]["dependsOn"])
        self.assertEqual(["SW-10"], self.nodes["SW-12"]["dependsOn"])

    def test_outcome_requires_measurement_contract_not_delivery_claim(self):
        outcome = self.factory["model"]["outcomeModel"]
        required = set(outcome["measurementContract"]["requiredFields"])
        self.assertTrue({
            "metric",
            "baselineOrBaselineResolution",
            "targetOrDecisionThreshold",
            "observationWindow",
            "dataSource",
            "decisionRule",
            "uncertaintyHandling",
        }.issubset(required))
        self.assertIn(
            "INCONCLUSIVE",
            outcome["measurementContract"]["allowedDecisions"],
        )
        self.assertIn(
            "CONTINUE_OBSERVATION",
            outcome["measurementContract"]["allowedDecisions"],
        )

    def test_web_quality_profile_covers_accessibility_performance_and_discoverability(self):
        profiles = self.factory["model"]["qualityPlanningContract"]["webConditionalProfiles"]
        flat_requirements = {
            requirement
            for profile in profiles
            for requirement in profile.get("require", [])
        }
        self.assertIn("ACCESSIBILITY", flat_requirements)
        self.assertIn("WEB_PERFORMANCE", flat_requirements)
        self.assertIn("CRAWLABILITY", flat_requirements)
        accessibility = next(
            profile for profile in profiles if "defaults" in profile
        )
        self.assertEqual("WCAG_2_2", accessibility["defaults"]["standard"])
        self.assertEqual("AA", accessibility["defaults"]["targetLevel"])

    def test_review_policy_is_risk_based_not_universally_independent(self):
        levels = self.factory["model"]["reviewPolicy"]["levels"]
        self.assertFalse(levels["LOW"]["independentReviewRequired"])
        self.assertTrue(levels["STANDARD"]["independentReviewRequired"])
        self.assertTrue(levels["ELEVATED"]["independentReviewRequired"])
        self.assertTrue(levels["CRITICAL"]["independentReviewRequired"])

    def test_retry_count_is_marked_as_configurable_safety_default(self):
        policy = self.factory["model"]["reworkPolicy"]
        self.assertEqual(3, policy["defaultMaximumAttempts"])
        self.assertEqual(
            "CONFIGURABLE_SAFETY_DEFAULT_NOT_DOMAIN_TRUTH",
            policy["defaultPolicyClass"],
        )
        self.assertIn("RISK_CLASS", policy["overrideDimensions"])
        self.assertIn("REVERSIBILITY", policy["overrideDimensions"])

    def test_default_operating_model_covers_all_mandatory_requirements(self):
        result = evaluate_domain_package_pair(
            self.factory, self.om, "0.13.0-rc.2", "SOFTWARE_WEBSITE"
        )
        self.assertTrue(result["compatible"], result)
        self.assertEqual([], result["missingCapabilities"])
        self.assertEqual([], result["missingAuthorities"])


if __name__ == "__main__":
    unittest.main()
