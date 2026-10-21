import copy
import unittest

from runtime.multi_agent_preflight import validate_multi_agent_wave_preflight
from tests.v014_fixtures import pointer, valid_agent_job


class Sc101Wave003ReferenceShapeTests(unittest.TestCase):
    def test_six_agent_corrected_wave_passes_exact_preflight_shape(self):
        specs = [
            ("worker-architect","Atlas UX",6,"019a0c00-0000-7abc-8a12-000000000121","RESULT_SUBMITTED","SETTLED"),
            ("worker-developer","Nova Dev",4,"019a0c00-0000-7abc-8a12-000000000122","REIDENTIFICATION_REQUIRED","REIDENT"),
            ("worker-educator","Mira Learning",3,"019a0c00-0000-7abc-8a12-000000000123","REIDENTIFICATION_REQUIRED","REIDENT"),
            ("worker-product","Nova Product",4,"019a0c00-0000-7abc-8a12-000000000124","REIDENTIFICATION_REQUIRED","REIDENT"),
            ("worker-qa","Vera QA",4,"019a0c00-0000-7abc-8a12-000000000125","REIDENTIFICATION_REQUIRED","REIDENT"),
            ("worker-release","Pulse Release",4,"019a0c00-0000-7abc-8a12-000000000126","REIDENTIFICATION_REQUIRED","REIDENT"),
        ]
        jobs = {}
        states = {}
        authority = {}
        reident = {}
        wave_jobs = []

        for idx, (agent_id, display, rev, job_id, runtime_status, mode) in enumerate(specs, start=1):
            job = valid_agent_job(
                project_id="67454821-9325-41f3-ac41-d72121cfec5f",
                job_id=job_id,
                agent_id=agent_id,
                display_name=display,
                identity_revision=rev,
                dispatch_revision=3,
                control_repository="empishaj/safor-memory",
                control_branch="main",
                product_repository="empishaj/safomwebsite",
                product_branch=f"safor/sc101/{agent_id}",
            )
            work = next(p for p in job["authorization"]["repositoryPermissions"] if p["repositoryClass"]=="WORK_REPOSITORY")
            work["read"] = False
            work["write"] = {"allowed":False,"allowedBranches":[],"allowedPaths":[]}
            work["commit"] = False
            work["push"] = False
            job["workspace"]["productWorkspace"] = None
            job["outputContract"]["productWriteTarget"] = None
            job["workspace"]["exclusiveKeys"] = [f"agent:{agent_id}", f"scenario:SC-101:output:{idx}"]
            job["lineage"]["sequence"] = {"planSequence":11,"packageSequence":11,"dispatchSequence":3,"attempt":2,"reworkCycle":1}
            job["lineage"]["supersedesJobId"] = f"019a0c00-0000-7abc-8a12-00000000010{idx}"
            job["lineage"]["triggerConflictRef"] = pointer("projects/safomwebsite/decisions/or11-sc101-wave001-reidentification-binding-rework.json")

            if mode == "SETTLED":
                job["inputs"].append({
                    "inputId":"settled-rearm-template",
                    "artifactRef":pointer("v0.14.0/templates/agent-state-settled-rearm.template.json", repository="empishaj/SAFOR"),
                    "mode":"READ_ONLY",
                    "expectedType":"SAFOR_AGENT_STATE_SETTLED_REARM_TEMPLATE",
                    "purpose":"Exact preselection rearm contract.",
                })
            else:
                evidence_ref = pointer(f"projects/safomwebsite/evidence/{agent_id}-reidentification.json")
                job["inputs"].append({
                    "inputId":"reidentification-evidence",
                    "artifactRef":evidence_ref,
                    "mode":"READ_ONLY",
                    "expectedType":"SAFOR_AGENT_REIDENTIFICATION_EVIDENCE",
                    "purpose":"Exact ready acknowledgement for preselection rearm.",
                })
                reident[agent_id] = {
                    "ref": evidence_ref,
                    "evidence": {
                        "format":"SAFOR_AGENT_REIDENTIFICATION_EVIDENCE",
                        "schemaVersion":"0.14.0",
                        "evidenceId":f"evidence-{agent_id}",
                        "projectId":"67454821-9325-41f3-ac41-d72121cfec5f",
                        "agentId":agent_id,
                        "identityRevision":rev,
                        "observedAgentReply":f"Agent {display} ({agent_id}) bereit | Status: WAITING_HUMAN_GO",
                        "expectedAgentReply":f"Agent {display} ({agent_id}) bereit | Status: WAITING_HUMAN_GO",
                        "result":"PASS",
                        "stateAtBootstrap":{"runtimeStatus":"REIDENTIFICATION_REQUIRED"},
                        "validForRearm":True,
                        "immutable":True,
                    }
                }

            control = next(p for p in job["authorization"]["repositoryPermissions"] if p["repositoryClass"]=="CONTROL_REPOSITORY")
            mandate = {
                "format":"SAFOR_EXECUTION_MANDATE","schemaVersion":"0.14.0","mandateId":f"mandate-{agent_id}",
                "status":"ACTIVE","projectId":"67454821-9325-41f3-ac41-d72121cfec5f","agentId":agent_id,
                "allowedControlBranch":"main","allowedProductRepository":"empishaj/safomwebsite",
                "allowedProductBranch":"main","allowedProductPaths":["/"],
                "humanGoRequired":True,"humanOnlyActivation":True,"masterMayActivateAgent":False,
                "mergeAllowed":False,"deployAllowed":False,
            }
            job["authorization"]["authorityBasis"] = pointer(f"projects/safomwebsite/decisions/{agent_id}-mandate.json")
            job["provenance"]["mandateRef"] = copy.deepcopy(job["authorization"]["authorityBasis"])
            job["workspace"]["responseWorkspace"]["branch"] = "main"
            job["scheduling"]["claimPolicy"]["claimStateTarget"]["branch"] = "main"
            job["scheduling"]["claimPolicy"]["goEvidenceWriteTarget"]["branch"] = "main"
            for response_type in ("JOB_RESULT","JOB_ERROR","CLARIFICATION_REQUEST","CAPABILITY_MISMATCH","IMPROVEMENT_PROPOSAL"):
                job["responseContracts"][response_type]["writeTarget"]["branch"] = "main"
            job["responseContracts"]["responseIndexTarget"]["branch"] = "main"
            control["write"]["allowedBranches"] = ["main"]

            jobs[job_id] = job
            states[agent_id] = {
                "format":"SAFOR_AGENT_STATE","schemaVersion":"0.14.0",
                "projectId":"67454821-9325-41f3-ac41-d72121cfec5f",
                "agentId":agent_id,"identityRevision":rev,"revision":0,
                "runtimeStatus":runtime_status,"session":None,"currentJob":None,
                "lastResponseRef":None,"consumedActivationIds":[],"updatedAt":"2026-10-21T16:15:00Z",
            }
            authority[job_id] = mandate
            wave_jobs.append({"jobId":job_id,"agentId":agent_id})

        wave = {
            "format":"SAFOR_DISPATCH_WAVE","schemaVersion":"0.14.0",
            "waveId":"WAVE-OR11-SC101-SIX-AGENT-003",
            "projectId":"67454821-9325-41f3-ac41-d72121cfec5f",
            "dispatchRevision":3,"status":"PREPARED","jobs":wave_jobs,
            "conflictAnalysis":{"productRepositoryAccess":False},"immutable":True,
        }

        result = validate_multi_agent_wave_preflight(
            wave=wave,
            jobs_by_id=jobs,
            authority_bases_by_job_id=authority,
            agent_states_by_agent_id=states,
            reidentification_evidence_by_agent_id=reident,
        )
        self.assertEqual("PASS", result["status"])
        self.assertEqual(6, result["jobCount"])
        self.assertEqual(6, result["agentCount"])
        self.assertFalse(result["productRepositoryAccessAllowed"])


if __name__ == "__main__":
    unittest.main()
