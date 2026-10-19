import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class HumanNoticeConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.framework = load("SAFOR-FRAMEWORK.json")
        cls.modules = cls.framework["embeddedModules"]
        cls.kernel = cls.modules["kernel"]["content"]

    def test_ordinary_chat_is_primary_and_runtime_install_is_not_required(self):
        model = self.modules["chatExecution"]["content"]
        self.assertEqual("DECLARATIVE_LLM_CHAT", model["primaryExecutionMode"])
        self.assertFalse(model["customerInstalledRuntimeRequired"])
        self.assertFalse(model["referenceImplementations"]["requiredForNormalChatUse"])

    def test_human_go_is_the_only_agent_activation(self):
        activation = self.modules["agentActivation"]["content"]["chatAgentActivationContract"]
        self.assertEqual("HUMAN_GO_REQUIRED", activation["activationMode"])
        self.assertEqual("GO", activation["acceptedHumanMessage"])
        for field in ("backgroundWakeupAssumed", "gitEventActivationAllowed", "pollingActivationAllowed", "automationActivationAllowed", "hostTriggerActivationAllowed", "schedulerMayActivateChat"):
            self.assertFalse(activation[field])
        self.assertEqual("ATOMIC_AGENT_STATE_CLAIM_WITH_SINGLE_USE_GO_EVIDENCE", activation["claimMode"])
        self.assertTrue(activation["stringSubstringEvidenceForbidden"])
        claim = self.modules["agentActivation"]["content"]["atomicClaimContract"]
        self.assertEqual("AGENT", claim["claimStateOwner"])
        self.assertFalse(claim["masterJobStateMutationAllowed"])
        preclaim = set(self.modules["agentActivation"]["content"]["onHumanGo"]["preClaimChecks"])
        self.assertTrue({
            "JOB_CONTRACT_POINTER_EXACT_MATCH",
            "AGENT_JOB_SCHEMA_VALID",
            "AGENT_JOB_CONTRACT_MODEL_VALID",
            "JOB_CLAIM_AND_RESPONSE_BINDINGS_COMPLETE",
        }.issubset(preclaim))
        self.assertTrue(claim["preCasSchemaValidationRequired"])
        self.assertTrue(claim["postReadbackSchemaValidationRequired"])
        self.assertTrue(claim["goEvidenceProviderReadbackRequired"])
        self.assertEqual("schemas/agent-state.schema.json", claim["agentStateSchemaRef"])
        self.assertEqual("templates/agent-state-claim.template.json", claim["claimStateTemplateRef"])
        self.assertEqual(
            "templates/agent-state-result-submitted.template.json",
            claim["resultSubmittedStateTemplateRef"],
        )
        self.assertEqual("HUMAN_ONLY", activation["activationAuthority"])
        self.assertFalse(activation["masterMayActivateChat"])
        self.assertFalse(activation["masterMaySynthesizeHumanGo"])
        self.assertFalse(activation["masterMayCreateHumanGoEvidence"])
        self.assertFalse(activation["currentInboxSnapshotBlobIsStableAcrossDispatch"])
        self.assertFalse(activation["inboxBlobChangeAloneRequiresReidentification"])
        authority = self.modules["agentActivation"]["content"]["onHumanGo"]["jobValidationAuthority"]
        self.assertEqual(
            "PINNED_SCHEMA_PLUS_PINNED_CONTRACT_MODEL",
            authority["authority"],
        )
        self.assertFalse(authority["referenceValidatorRequiredForNormalChatUse"])
        rearm = self.modules["agentActivation"]["content"]["onHumanGo"]["preSelectionAgentStateHandling"]
        self.assertTrue(rearm["rearmForbiddenDuringInitialization"])
        self.assertTrue(rearm["rearmRequiresSeparateDirectHumanGo"])
        self.assertEqual("GO", rearm["rearmHumanMessage"])
        self.assertEqual(
            "EXPLICIT_NULL",
            rearm["rearmSessionAndCurrentJobRepresentation"],
        )
        self.assertTrue(rearm["readyStatusForbiddenIfPersistedStateInvalid"])

    def test_agent_identity_requires_display_name_and_personal_inbox_binding(self):
        schema = self.modules["schemaAgentIdentity"]["content"]
        required = set(schema["required"])
        self.assertTrue({"agentId", "displayName", "inboxBinding", "activationContract", "communicationContractRef"}.issubset(required))
        inbox_binding = schema["$defs"]["inboxBinding"]
        self.assertIn("inboxIndexRef", inbox_binding["required"])
        self.assertIn("inboxIndexLocation", inbox_binding["required"])
        self.assertIn("identityRevision", inbox_binding["required"])
        self.assertIn("mutableInboxIndexLocation", schema["$defs"])
        self.assertNotIn("blobSha", schema["$defs"]["mutableInboxIndexLocation"]["required"])
        activation = schema["allOf"][0]["then"]["properties"]["activationContract"]["allOf"][0]["properties"]
        self.assertEqual("HUMAN_GO_REQUIRED", activation["activationMode"]["const"])
        self.assertFalse(activation["automationActivationAllowed"]["const"])

    def test_job_requires_domain_all_response_and_chat_contracts(self):
        schema = self.modules["schemaAgentJob"]["content"]
        self.assertTrue({"domainContext", "responseContracts", "communicationContract"}.issubset(schema["required"]))
        required_responses = set(schema["$defs"]["responseContracts"]["required"])
        self.assertTrue({"JOB_RESULT", "JOB_ERROR", "CLARIFICATION_REQUEST", "CAPABILITY_MISMATCH", "IMPROVEMENT_PROPOSAL"}.issubset(required_responses))
        claim_required = set(
            schema["$defs"]["scheduling"]["properties"]["claimPolicy"]["required"]
        )
        self.assertTrue({
            "humanGoEvidenceSchemaRef",
            "humanGoEvidenceTemplateRef",
            "goEvidenceWriteTarget",
            "agentStateSchemaRef",
            "claimStateTemplateRef",
            "resultSubmittedStateTemplateRef",
            "preCasSchemaValidationRequired",
            "postReadbackSchemaValidationRequired",
            "goEvidenceProviderReadbackRequired",
        }.issubset(claim_required))
        response_binding_required = set(schema["$defs"]["responseBinding"]["required"])
        self.assertTrue({
            "preWriteSchemaValidationRequired",
            "providerReadbackRequired",
            "postReadbackSchemaValidationRequired",
        }.issubset(response_binding_required))

    def test_response_contract_has_exact_five_types(self):
        model = self.modules["agentResponseContract"]["content"]
        self.assertEqual({"JOB_RESULT", "JOB_ERROR", "CLARIFICATION_REQUEST", "CAPABILITY_MISMATCH", "IMPROVEMENT_PROPOSAL"}, set(model["responseTypes"]))
        for response_type, contract in model["responseTypes"].items():
            self.assertTrue(contract["templateRef"].startswith("templates/responses/"), response_type)
        persistence = model["persistenceProtocol"]
        self.assertTrue(persistence["freeformResponseConstructionForbidden"])
        self.assertTrue(persistence["preWriteSchemaValidationRequired"])
        self.assertTrue(persistence["providerReadbackRequired"])
        self.assertTrue(persistence["postReadbackSchemaValidationRequired"])
        self.assertTrue(persistence["chatTerminalStatusBeforeValidatedReadbackForbidden"])

    def test_agent_chat_is_platform_owned_single_line_and_non_domain(self):
        model = self.modules["agentCommunication"]["content"]
        self.assertEqual("SAFOR_PLATFORM", model["owner"])
        self.assertTrue(model["humanBoundary"]["masterIsOnlyDomainInterface"])
        self.assertFalse(model["humanBoundary"]["agentMayAskHumanDomainQuestions"])
        self.assertEqual(1, model["budgets"]["maxLines"])
        self.assertTrue(model["rendering"]["singleLine"])
        self.assertTrue(model["rendering"]["menuForbidden"])
        self.assertIn("MENU", model["forbiddenContent"])

    def test_master_status_forbids_full_scan_and_requires_git_references(self):
        model = self.modules["masterStatus"]["content"]
        self.assertTrue(model["principles"]["fullRepositoryScanForRoutineStatusForbidden"])
        self.assertTrue(model["principles"]["allReportedResultsRequireGitReference"])
        self.assertTrue(model["principles"]["staleProjectionMustBeDisclosed"])

    def test_all_domain_distributions_embed_integrated_v014_contracts(self):
        required = {
            "chatExecution", "agentActivation", "agentResponseContract",
            "agentCommunication", "masterStatus", "schemaHumanGoEvidence",
            "schemaAgentResponse", "schemaAgentChatOutput", "executionAttempt",
            "templateHumanGoEvidence", "templateAgentStateClaim",
            "templateAgentStateResultSubmitted",
        }
        for file_name in ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json"):
            distribution = load(file_name)
            framework = distribution["framework"]
            self.assertEqual(VERSION, framework["bundleVersion"])
            self.assertEqual("0.14.0", framework["schemaVersion"])
            self.assertTrue(required.issubset(framework["embeddedModules"]))

    def test_platform_not_factory_or_operating_model_owns_human_communication(self):
        self.assertTrue(self.kernel["kernelPrinciples"]["platformOwnsHumanVisibleCommunication"])
        self.assertTrue(self.kernel["kernelPrinciples"]["minimalSubagentChatStatusOnly"])
        for file_name in ("SAFOR-FRAMEWORK-WEBSITE.json", "SAFOR-FRAMEWORK-SAAS.json", "SAFOR-FRAMEWORK-BOOK-CREATION.json"):
            distribution = load(file_name)
            for package in distribution["embeddedDomainModules"].values():
                serialized = json.dumps(package)
                self.assertNotIn("humanGoActivationOverride", serialized)
                self.assertNotIn("agentChatResponseLength", serialized)


if __name__ == "__main__":
    unittest.main()
