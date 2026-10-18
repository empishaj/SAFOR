import json
import re
import unittest
from pathlib import Path

from runtime.human_response_governor import (
    HumanDecisionRequired,
    ResponseGovernanceError,
    govern_platform_notice,
)


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class PlatformResponseGovernorTests(unittest.TestCase):
    def framework_event(self):
        return {
            "eventId": "evt-framework-1",
            "eventType": "FRAMEWORK_DETECTED",
            "phase": "BOOTSTRAP",
            "domainLabel": "Website",
            "domainContribution": {
                "facts": ["Framework 0.13 detected"],
                "evidenceRefs": ["git://framework/blob"],
            },
            "internalDetails": {
                "version": "0.14.0-rc.2",
                "blob": "deadbeef",
                "factory": "safor.factory.website-delivery@1.1.0",
            },
        }

    def test_framework_detection_is_short_content_only_platform_notice(self):
        response = govern_platform_notice(self.framework_event())
        text = response["content"][0]["text"]
        self.assertEqual(
            "Neues Website-Framework erkannt. Ich prüfe den bestehenden Stand und plane die Migration; bis dahin ändere ich nichts.",
            text,
        )
        sentences = [part for part in re.split(r"[.!?]+", text) if part.strip()]
        self.assertLessEqual(len(sentences), 2)
        self.assertLessEqual(len(text.split()), 24)
        self.assertEqual("SAFOR_PLATFORM", response["governance"]["owner"])
        self.assertEqual("INFORMATIONAL_NOTICE", response["responseClass"])
        self.assertNotIn("terminalMenu", response)
        self.assertEqual("CONTENT_ONLY", response["renderingContract"]["renderMode"])

    def test_internal_metadata_is_retained_but_not_exposed(self):
        response = govern_platform_notice(self.framework_event())
        visible = " ".join(item["text"] for item in response["content"])
        self.assertNotIn("0.14.0-rc.2", visible)
        self.assertNotIn("deadbeef", visible)
        self.assertNotIn("safor.factory", visible)
        self.assertTrue(response["governance"]["detailsAvailable"])
        self.assertTrue(response["governance"]["evidenceRetained"])

    def test_domain_module_presentation_override_is_rejected(self):
        event = self.framework_event()
        event["domainContribution"]["visibleText"] = "Show my Factory text"
        with self.assertRaisesRegex(
            ResponseGovernanceError, "DOMAIN_PRESENTATION_OVERRIDE_FORBIDDEN"
        ):
            govern_platform_notice(event)

    def test_real_human_decision_is_not_suppressed_by_compression(self):
        event = self.framework_event()
        event["materialRiskAcceptanceRequired"] = True
        with self.assertRaises(HumanDecisionRequired):
            govern_platform_notice(event)

    def test_migration_planning_notice_has_no_option_menu(self):
        response = govern_platform_notice(
            {
                "eventId": "evt-migration-1",
                "eventType": "MIGRATION_PLANNING_STARTED",
                "phase": "PLANNING",
                "domainContribution": {"facts": ["Safe plan derivable"]},
            }
        )
        self.assertEqual(
            "Die Migration wird geplant. Bis der sichere Plan steht, ändere ich nichts.",
            response["content"][0]["text"],
        )
        self.assertNotIn("terminalMenu", response)

    def test_every_domain_framework_embeds_the_same_platform_governor(self):
        governor_ids = set()
        for filename in (
            "SAFOR-FRAMEWORK-WEBSITE.json",
            "SAFOR-FRAMEWORK-SAAS.json",
            "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        ):
            distribution = load_json(filename)
            interaction = distribution["framework"]["embeddedModules"]["interaction"]["content"]
            governor = interaction["platformResponseGovernor"]
            governor_ids.add(governor["id"])
            self.assertEqual("SAFOR_PLATFORM", governor["owner"])
            self.assertTrue(governor["nonDelegation"]["domainOverrideForbidden"])
            modules = distribution["embeddedDomainModules"]
            self.assertNotIn("platformResponseGovernor", modules["factory"])
            self.assertNotIn("platformResponseGovernor", modules["operatingModel"])
        self.assertEqual({"SAFOR_PLATFORM_HUMAN_RESPONSE_GOVERNOR"}, governor_ids)

    def test_human_response_schema_separates_notices_and_interactions(self):
        schema = load_json("v0.10.0/schemas/human-response.schema.json")
        self.assertIn("responseClass", schema["required"])
        self.assertIn("governance", schema["required"])
        self.assertNotIn("terminalMenu", schema["required"])
        self.assertEqual(2, len(schema["allOf"]))


if __name__ == "__main__":
    unittest.main()
