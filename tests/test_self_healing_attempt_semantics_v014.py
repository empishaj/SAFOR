import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SelfHealingAttemptSemanticsV014Tests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_failure_class_budgets_are_explicitly_additional(self):
        model = self.load("v0.14.0/self-healing-model.json")
        for failure_class in model["failureClasses"]:
            self.assertIn("defaultAdditionalRetryBudget", failure_class)
            self.assertNotIn("defaultRetryBudget", failure_class)
        policy = model["retryPolicy"]
        self.assertEqual("ADDITIONAL_REPAIR_EXECUTIONS_AFTER_INITIAL_ATTEMPT", policy["budgetMeaning"])
        self.assertFalse(policy["initialAttemptConsumesAdditionalRetryBudget"])
        self.assertFalse(policy["reconciliationCountsAsRepairAttempt"])
        self.assertFalse(policy["reconciliationMayMutate"])
        self.assertEqual("FORBIDDEN", policy["automaticMutationReplayDefault"])
        self.assertEqual("RECONCILE_REQUIRED", policy["effectUnknownOutcome"])
        self.assertEqual("DO_NOT_REPEAT_MUTATION", policy["provenAppliedOutcome"])

    def test_every_module_profile_allows_one_initial_and_zero_additional_retries(self):
        model = self.load("v0.14.0/module-self-healing-model.json")
        self.assertGreater(len(model["moduleProfiles"]), 0)
        for profile in model["moduleProfiles"]:
            self.assertEqual(1, profile["initialAutomaticAttemptBudget"], profile["moduleKey"])
            self.assertEqual(0, profile["additionalRetryBudget"], profile["moduleKey"])
            self.assertNotIn("retryBudget", profile)

    def test_profile_schema_names_initial_and_additional_budgets(self):
        schema = self.load("v0.14.0/schemas/module-recovery-profile.schema.json")
        self.assertIn("initialAutomaticAttemptBudget", schema["required"])
        self.assertIn("additionalRetryBudget", schema["required"])
        self.assertNotIn("retryBudget", schema["required"])
        self.assertNotIn("retryBudget", schema["properties"])
        self.assertEqual(1, schema["properties"]["initialAutomaticAttemptBudget"]["maximum"])

    def test_repair_record_distinguishes_initial_from_retry(self):
        schema = self.load("v0.14.0/schemas/self-healing-record.schema.json")
        for field in ("attemptKind", "attemptNumber", "priorAttemptRef", "retryAuthorization"):
            self.assertIn(field, schema["required"])
        self.assertEqual(["INITIAL", "RETRY"], schema["properties"]["attemptKind"]["enum"])
        retry_auth = schema["properties"]["retryAuthorization"]["properties"]
        self.assertEqual("PROVEN_NOT_APPLIED", retry_auth["priorEffectState"]["const"])
        self.assertTrue(retry_auth["eligibilityRevalidated"]["const"])
        self.assertTrue(retry_auth["selectedActionUnchanged"]["const"])
        self.assertTrue(retry_auth["scopeUnchanged"]["const"])

    def test_partial_write_model_never_replays_proven_product_mutation(self):
        model = self.load("v0.14.0/execution-attempt-model.json")
        rules = "\n".join(model["rules"])
        self.assertIn("known product commit is never repeated", rules)
        self.assertIn("Every retry reads provider state", rules)
        self.assertIn("Unknown external effects enter RECONCILE_REQUIRED", rules)

    def test_single_file_bundle_carries_same_contract(self):
        framework = self.load("SAFOR-FRAMEWORK.json")
        self_healing = framework["embeddedModules"]["selfHealing"]["content"]
        module_healing = framework["embeddedModules"]["moduleSelfHealing"]["content"]
        self.assertEqual(
            "ADDITIONAL_REPAIR_EXECUTIONS_AFTER_INITIAL_ATTEMPT",
            self_healing["retryPolicy"]["budgetMeaning"],
        )
        self.assertTrue(all(p["initialAutomaticAttemptBudget"] == 1 for p in module_healing["moduleProfiles"]))
        self.assertTrue(all(p["additionalRetryBudget"] == 0 for p in module_healing["moduleProfiles"]))
        rule = framework["runtimeContract"]["selfHealingRule"]
        self.assertIn("zero additional retries", rule)
        self.assertIn("proven product mutation is never replayed", rule)


if __name__ == "__main__":
    unittest.main()
