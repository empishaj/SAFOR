import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HumanResponseClassificationV014Tests(unittest.TestCase):
    def load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_classes_match_schema(self):
        schema = self.load("v0.14.0/schemas/human-response.schema.json")
        interaction = self.load("v0.14.0/interaction-model.json")
        self.assertEqual(set(schema["properties"]["responseClass"]["enum"]), set(interaction["responseClassification"]["classes"]))

    def test_menu_policy_is_class_derived(self):
        classes = self.load("v0.14.0/interaction-model.json")["responseClassification"]["classes"]
        self.assertEqual("FORBIDDEN", classes["INFORMATIONAL_NOTICE"]["terminalMenu"])
        for name in ("INTERACTIVE_CHECKPOINT", "DECISION_REQUEST", "BLOCKER", "DETAIL_RESPONSE"):
            self.assertEqual("REQUIRED_EXACTLY_ONE", classes[name]["terminalMenu"])

    def test_master_has_no_universal_menu_flag(self):
        contract = self.load("v0.14.0/SAFOR-MASTER.json")["humanCommunication"]
        self.assertFalse(contract["terminalMenuRequired"])
        self.assertEqual("DERIVED_FROM_RESPONSE_CLASS", contract["terminalMenuPolicy"])

if __name__ == "__main__":
    unittest.main()
