import copy
import unittest

from runtime.multi_agent_preflight import (
    MultiAgentWavePreflightError,
    validate_multi_agent_wave_preflight,
)
from tests.v014_fixtures import pointer, valid_agent_job


class MultiAgentWavePreflightV014Tests(unittest.TestCase):
    def setUp(self):
        self.job_a = valid_agent_job(
            job_id="0199f0aa-7e40-7abc-8a12-000000000021",
            agent_id="agent-a",
            display_name="Agent Alpha",
            identity_revision=2,
            dispatch_revision=1,
            product_branch="safor/job/a",
        )
        self.job_b = valid_agent_job(
            job_id="0199f0aa-7e40-7abc-8a12-000000000022",
            agent_id="agent-b",
            display_name="Agent Beta",
            identity_revision=3,
            dispatch_revision=1,
            product_branch="safor/job/b",
        )
        self.wave = {
            "format": "SAFOR_DISPATCH_WAVE",
            "schemaVersion": "0.14.0",
            "waveId": "wave-test",
            "projectId": "project-001",
            "dispatchRevision": 1,
            "status": "PREPARED",
            "jobs": [
                {"jobId": self.job_a["identity"]["jobId"], "agentId": "agent-a"},
                {"jobId": self.job_b["identity"]["jobId"], "agentId": "agent-b"},
            ],
            "conflictAnalysis": {"productRepositoryAccess": True},
            "immutable": True,
        }
        self.jobs = {
            self.job_a["identity"]["jobId"]: self.job_a,
            self.job_b["identity"]["jobId"]: self.job_b,
        }
        self.states = {
            "agent-a": self.state("agent-a", 2, "WAITING_HUMAN_GO"),
            "agent-b": self.state("agent-b", 3, "WAITING_HUMAN_GO"),
        }
        self.authority = {
            self.job_a["identity"]["jobId"]: self.mandate(self.job_a),
            self.job_b["identity"]["jobId"]: self.mandate(self.job_b),
        }

    @staticmethod
    def state(agent_id, identity_revision, runtime_status):
        return {
            "format": "SAFOR_AGENT_STATE",
            "schemaVersion": "0.14.0",
            "projectId": "project-001",
            "agentId": agent_id,
            "identityRevision": identity_revision,
            "revision": 0,
            "runtimeStatus": runtime_status,
            "session": None,
            "currentJob": None,
            "lastResponseRef": None,
            "consumedActivationIds": [],
            "updatedAt": "2026-10-21T15:00:00Z",
        }

    @staticmethod
    def mandate(job):
        product_permission = next(
            item
            for item in job["authorization"]["repositoryPermissions"]
            if item["repositoryClass"] == "WORK_REPOSITORY"
        )
        control_permission = next(
            item
            for item in job["authorization"]["repositoryPermissions"]
            if item["repositoryClass"] == "CONTROL_REPOSITORY"
        )
        return {
            "format": "SAFOR_EXECUTION_MANDATE",
            "schemaVersion": "0.14.0",
            "mandateId": f"mandate-{job['assignment']['agentId']}",
            "status": "ACTIVE",
            "projectId": job["lineage"]["projectId"],
            "agentId": job["assignment"]["agentId"],
            "allowedControlBranch": control_permission["write"]["allowedBranches"][0],
            "allowedProductRepository": product_permission["repository"],
            "allowedProductBranch": product_permission["write"]["allowedBranches"][0],
            "allowedProductPaths": product_permission["write"]["allowedPaths"],
            "humanGoRequired": True,
            "humanOnlyActivation": True,
            "masterMayActivateAgent": False,
            "mergeAllowed": False,
            "deployAllowed": False,
        }

    @staticmethod
    def make_read_only(job):
        job = copy.deepcopy(job)
        work_permission = next(
            item
            for item in job["authorization"]["repositoryPermissions"]
            if item["repositoryClass"] == "WORK_REPOSITORY"
        )
        work_permission["read"] = False
        work_permission["write"] = {
            "allowed": False,
            "allowedBranches": [],
            "allowedPaths": [],
        }
        work_permission["commit"] = False
        work_permission["push"] = False
        job["workspace"]["productWorkspace"] = None
        job["outputContract"]["productWriteTarget"] = None
        return job

    def run_preflight(self, **overrides):
        values = {
            "wave": self.wave,
            "jobs_by_id": self.jobs,
            "authority_bases_by_job_id": self.authority,
            "agent_states_by_agent_id": self.states,
            "reidentification_evidence_by_agent_id": {},
        }
        values.update(overrides)
        return validate_multi_agent_wave_preflight(**values)

    def test_two_disjoint_jobs_pass(self):
        result = self.run_preflight()
        self.assertEqual("PASS", result["status"])
        self.assertEqual(2, result["jobCount"])
        self.assertEqual(2, result["agentCount"])

    def test_unknown_claim_policy_field_fails_before_dispatch(self):
        invalid = copy.deepcopy(self.jobs)
        invalid[self.job_a["identity"]["jobId"]]["scheduling"]["claimPolicy"][
            "settledRearmStateTemplateRef"
        ] = pointer("v0.14.0/templates/agent-state-settled-rearm.template.json")
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "CLAIM_POLICY_UNKNOWN_FIELDS",
        ):
            self.run_preflight(jobs_by_id=invalid)

    def test_reidentification_state_requires_pinned_evidence_input(self):
        states = copy.deepcopy(self.states)
        states["agent-b"]["runtimeStatus"] = "REIDENTIFICATION_REQUIRED"
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "REIDENTIFICATION_EVIDENCE_INPUT_REQUIRED",
        ):
            self.run_preflight(agent_states_by_agent_id=states)

    def test_valid_pinned_reidentification_evidence_passes(self):
        jobs = copy.deepcopy(self.jobs)
        states = copy.deepcopy(self.states)
        states["agent-b"]["runtimeStatus"] = "REIDENTIFICATION_REQUIRED"
        evidence_ref = pointer("projects/example/evidence/agent-b-reidentification.json")
        jobs[self.job_b["identity"]["jobId"]]["inputs"].append(
            {
                "inputId": "reidentification-evidence",
                "artifactRef": evidence_ref,
                "mode": "READ_ONLY",
                "expectedType": "SAFOR_AGENT_REIDENTIFICATION_EVIDENCE",
                "purpose": "Exact ready acknowledgement for preselection rearm.",
            }
        )
        evidence = {
            "format": "SAFOR_AGENT_REIDENTIFICATION_EVIDENCE",
            "schemaVersion": "0.14.0",
            "evidenceId": "evidence-agent-b",
            "projectId": "project-001",
            "agentId": "agent-b",
            "identityRevision": 3,
            "observedAgentReply": "Agent Beta ready",
            "expectedAgentReply": "Agent Beta ready",
            "result": "PASS",
            "stateAtBootstrap": {"runtimeStatus": "REIDENTIFICATION_REQUIRED"},
            "validForRearm": True,
            "immutable": True,
        }
        result = self.run_preflight(
            jobs_by_id=jobs,
            agent_states_by_agent_id=states,
            reidentification_evidence_by_agent_id={
                "agent-b": {"ref": evidence_ref, "evidence": evidence}
            },
        )
        self.assertEqual("PASS", result["status"])

    def test_settled_state_requires_preselection_template_input(self):
        states = copy.deepcopy(self.states)
        states["agent-a"]["runtimeStatus"] = "RESULT_SUBMITTED"
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "SETTLED_REARM_TEMPLATE_INPUT_REQUIRED",
        ):
            self.run_preflight(agent_states_by_agent_id=states)

    def test_settled_state_template_input_passes_without_claim_policy_extension(self):
        jobs = copy.deepcopy(self.jobs)
        states = copy.deepcopy(self.states)
        states["agent-a"]["runtimeStatus"] = "RESULT_SUBMITTED"
        jobs[self.job_a["identity"]["jobId"]]["inputs"].append(
            {
                "inputId": "settled-rearm-template",
                "artifactRef": pointer(
                    "v0.14.0/templates/agent-state-settled-rearm.template.json",
                    repository="empishaj/SAFOR",
                ),
                "mode": "READ_ONLY",
                "expectedType": "SAFOR_AGENT_STATE_SETTLED_REARM_TEMPLATE",
                "purpose": "Exact preselection rearm contract.",
            }
        )
        result = self.run_preflight(
            jobs_by_id=jobs,
            agent_states_by_agent_id=states,
        )
        self.assertEqual("PASS", result["status"])
        self.assertNotIn(
            "settledRearmStateTemplateRef",
            jobs[self.job_a["identity"]["jobId"]]["scheduling"]["claimPolicy"],
        )

    def test_agent_specific_authority_is_required(self):
        authority = copy.deepcopy(self.authority)
        authority[self.job_b["identity"]["jobId"]]["agentId"] = "agent-a"
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "AUTHORITY_BASIS_INVALID",
        ):
            self.run_preflight(authority_bases_by_job_id=authority)

    def test_shared_mutable_control_path_fails(self):
        jobs = copy.deepcopy(self.jobs)
        for job in jobs.values():
            control_permission = next(
                item
                for item in job["authorization"]["repositoryPermissions"]
                if item["repositoryClass"] == "CONTROL_REPOSITORY"
            )
            control_permission["write"]["allowedPaths"].append("projects/example/shared/")
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "MUTABLE_PATH_CONFLICT",
        ):
            self.run_preflight(jobs_by_id=jobs)

    def test_duplicate_agent_exceeds_capacity_one(self):
        wave = copy.deepcopy(self.wave)
        wave["jobs"][1]["agentId"] = "agent-a"
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "AGENT_CAPACITY_EXCEEDED",
        ):
            self.run_preflight(wave=wave)

    def test_no_product_access_wave_rejects_product_permissions(self):
        wave = copy.deepcopy(self.wave)
        wave["conflictAnalysis"]["productRepositoryAccess"] = False
        with self.assertRaisesRegex(
            MultiAgentWavePreflightError,
            "PRODUCT_ACCESS_FORBIDDEN",
        ):
            self.run_preflight(wave=wave)

    def test_no_product_access_wave_accepts_read_only_jobs(self):
        wave = copy.deepcopy(self.wave)
        wave["conflictAnalysis"]["productRepositoryAccess"] = False
        jobs = {
            job_id: self.make_read_only(job)
            for job_id, job in self.jobs.items()
        }
        authority = {
            job_id: self.mandate(job)
            for job_id, job in jobs.items()
        }
        for mandate in authority.values():
            mandate["allowedProductBranch"] = "main"
            mandate["allowedProductPaths"] = ["/"]
        result = self.run_preflight(
            wave=wave,
            jobs_by_id=jobs,
            authority_bases_by_job_id=authority,
        )
        self.assertEqual("PASS", result["status"])
        self.assertFalse(result["productRepositoryAccessAllowed"])


if __name__ == "__main__":
    unittest.main()
