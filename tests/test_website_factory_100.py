import json
import unittest
from pathlib import Path

from runtime.bootstrap_policy import (
    evaluate_active_conditional_requirements,
    evaluate_domain_package_pair,
    validate_factory_contract_consistency,
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class WebsiteFactory100Tests(unittest.TestCase):
    def setUp(self):
        self.factory = load_json(
            "v0.13.0/packages/factories/website-delivery/1.0.0/package.json"
        )
        self.om = load_json(
            "v0.13.0/packages/operating-models/website-team/1.0.0/package.json"
        )
        self.nodes = {
            node["id"]: node for node in self.factory["model"]["flowGraph"]["nodes"]
        }

    def test_factory_is_explicitly_website_only(self):
        self.assertEqual(["WEBSITE"], self.factory["compatibility"]["supportedCreationTypes"])
        self.assertEqual("WEBSITE", self.factory["model"]["discoveryContract"]["creationType"])
        self.assertEqual("WEBSITE", self.factory["model"]["planningContract"]["creationType"])

    def test_factory_excludes_general_saas_operations(self):
        excluded = set(self.factory["model"]["scopeBoundary"]["excluded"])
        self.assertIn("GENERAL_SAAS_PRODUCT_ENGINEERING", excluded)
        self.assertIn("SERVICE_OPERATIONS", excluded)
        self.assertIn("INCIDENT_RESPONSE", excluded)
        self.assertIn("SOFTWARE_SUPPLY_CHAIN_GOVERNANCE", excluded)

    def test_discovery_escalates_application_scope_to_software_saas(self):
        boundary = self.factory["model"]["discoveryContract"]["boundaryCheck"]
        self.assertEqual("CREATION_TYPE_CHANGE_REQUIRED", boundary["outcome"])
        self.assertEqual("SOFTWARE_SAAS", boundary["targetCreationType"])

    def test_website_flow_is_content_and_publish_focused(self):
        self.assertEqual("WEBSITE_DEFINITION", self.nodes["WEB-01"]["workItemType"])
        self.assertEqual("CONTENT_INFORMATION_ARCHITECTURE", self.nodes["WEB-02"]["workItemType"])
        self.assertEqual("EXPERIENCE_DESIGN", self.nodes["WEB-03"]["workItemType"])
        self.assertEqual("WEBSITE_IMPLEMENTATION", self.nodes["WEB-04"]["workItemType"])
        self.assertEqual("WEBSITE_VERIFICATION", self.nodes["WEB-05"]["workItemType"])
        self.assertEqual("PUBLISH", self.nodes["WEB-06"]["workItemType"])
        self.assertEqual("POST_PUBLISH_OBSERVATION", self.nodes["WEB-07"]["workItemType"])
        self.assertEqual("WEBSITE_OUTCOME_ASSESSMENT", self.nodes["WEB-08"]["workItemType"])

    def test_web_quality_covers_accessibility_responsive_and_performance(self):
        quality = self.factory["model"]["webQualityContract"]
        self.assertEqual("WCAG_2_2", quality["accessibility"]["defaultStandard"])
        self.assertEqual("AA", quality["accessibility"]["defaultTargetLevel"])
        self.assertTrue(quality["responsiveVerificationRequired"])
        self.assertTrue(quality["performanceEvidenceRequired"])

    def test_search_visibility_is_conditional_not_universal(self):
        contract = self.factory["model"]["compatibilityContract"]
        conditional = contract["conditionalCapabilities"]
        self.assertEqual(
            [{"capabilityId": "search_visibility_verification", "when": "PUBLIC_DISCOVERABILITY_REQUIRED"}],
            conditional,
        )
        self.assertNotIn(
            "search_visibility_verification",
            self.factory["compatibility"]["counterpart"]["requiredCapabilities"],
        )
        active = evaluate_active_conditional_requirements(
            self.factory, self.om, {"PUBLIC_DISCOVERABILITY_REQUIRED"}
        )
        self.assertTrue(active["satisfied"], active)

    def test_publish_and_outcome_are_distinct(self):
        self.assertEqual(["WEB-05"], self.nodes["WEB-06"]["dependsOn"])
        self.assertEqual(["WEB-06"], self.nodes["WEB-07"]["dependsOn"])
        self.assertEqual(["WEB-07"], self.nodes["WEB-08"]["dependsOn"])
        rule = self.factory["model"]["outcomeModel"]["rule"]
        self.assertIn("published website is not evidence", rule.lower())

    def test_free_website_operating_model_is_lightweight_and_compatible(self):
        roles = {x["id"] for x in self.om["model"]["roles"]}
        self.assertEqual(
            {
                "WEBSITE_OWNER",
                "CONTENT_DESIGNER",
                "UX_DESIGNER",
                "WEB_DEVELOPER",
                "WEBSITE_REVIEWER",
                "PUBLISHER",
                "WEB_ANALYST",
            },
            roles,
        )
        self.assertNotIn("SITE_RELIABILITY_ENGINEER", roles)
        result = evaluate_domain_package_pair(
            self.factory, self.om, "0.13.0-rc.4", "WEBSITE"
        )
        self.assertTrue(result["compatible"], result)

    def test_factory_contract_is_internally_consistent(self):
        result = validate_factory_contract_consistency(self.factory)
        self.assertTrue(result["valid"], result["errors"])

    def test_outcome_has_measurement_contract(self):
        measurement = self.factory["model"]["outcomeModel"]["measurementContract"]
        self.assertTrue({
            "metric",
            "baselineOrBaselineResolution",
            "targetOrDecisionThreshold",
            "observationWindow",
            "dataSource",
            "decisionRule",
        }.issubset(set(measurement["requiredFields"])))
        self.assertIn("INCONCLUSIVE", measurement["allowedDecisions"])


if __name__ == "__main__":
    unittest.main()
