from __future__ import annotations

TEST_JOB_ID = "0199f0aa-7e40-7abc-8a12-000000000014"


def pointer(path: str, repository: str = "example/safor-memory", ref: str = "commit123", blob_sha: str = "blob1234"):
    return {
        "repository": repository,
        "ref": ref,
        "path": path,
        "blobSha": blob_sha,
    }


def target(repository_class: str, repository: str, branch: str, path_pattern: str, operations=None):
    return {
        "repositoryClass": repository_class,
        "repository": repository,
        "branch": branch,
        "pathPattern": path_pattern,
        "allowedOperations": operations or ["READ", "CREATE", "MODIFY", "COMMIT", "PUSH"],
    }


def valid_agent_job(
    *,
    project_id: str = "project-001",
    job_id: str = TEST_JOB_ID,
    agent_id: str = "agent-a",
    display_name: str = "Agent Alpha",
    identity_revision: int = 2,
    dispatch_revision: int = 3,
    control_repository: str = "example/safor-memory",
    control_branch: str = "main",
    product_repository: str = "example/product",
    product_branch: str = "safor/job/test",
):
    response_types = {
        "JOB_RESULT": "job-result",
        "JOB_ERROR": "job-error",
        "CLARIFICATION_REQUEST": "clarification-request",
        "CAPABILITY_MISMATCH": "capability-mismatch",
        "IMPROVEMENT_PROPOSAL": "improvement-proposal",
    }
    response_contracts = {}
    for response_type, slug in response_types.items():
        response_contracts[response_type] = {
            "responseType": response_type,
            "templateRef": pointer(
                f"v0.14.0/templates/responses/{slug}.template.json",
                "empishaj/SAFOR",
            ),
            "schemaRef": pointer(
                "v0.14.0/schemas/agent-response.schema.json",
                "empishaj/SAFOR",
            ),
            "writeTarget": target(
                "CONTROL_REPOSITORY",
                control_repository,
                control_branch,
                f"projects/example/agents/{agent_id}/outbox/{{jobId}}/{{responseId}}.json",
                ["READ", "CREATE", "COMMIT", "PUSH"],
            ),
            "required": True,
            "preWriteSchemaValidationRequired": True,
            "providerReadbackRequired": True,
            "postReadbackSchemaValidationRequired": True,
        }
    response_contracts["responseIndexTarget"] = target(
        "CONTROL_REPOSITORY",
        control_repository,
        control_branch,
        f"projects/example/agents/{agent_id}/outbox/index.json",
        ["READ", "CREATE", "MODIFY", "COMMIT", "PUSH", "UPDATE_INDEX"],
    )
    response_contracts["resolutionSchemaRef"] = pointer(
        "v0.14.0/schemas/agent-response-resolution.schema.json",
        "empishaj/SAFOR",
    )

    return {
        "format": "SAFOR_AGENT_JOB",
        "schemaVersion": "0.14.0",
        "identity": {
            "jobId": job_id,
            "jobKey": "test-job",
            "jobType": "IMPLEMENTATION",
            "contractRevision": 1,
            "immutableAfterPublication": True,
        },
        "lineage": {
            "projectId": project_id,
            "valueStreamId": "value-stream-001",
            "packageId": "WP-TEST",
            "packageRevision": 1,
            "workItemId": "WP-TEST-IMPL",
            "workItemRevision": 1,
            "parentWorkItemId": None,
            "rootPackageId": "PLAN-001",
            "sequence": {
                "planSequence": 1,
                "packageSequence": 1,
                "dispatchSequence": dispatch_revision,
                "attempt": 1,
                "reworkCycle": 0,
            },
            "supersedesJobId": None,
            "triggerConflictRef": None,
        },
        "provenance": {
            "createdAt": "2026-10-18T09:58:00Z",
            "issuedAt": "2026-10-18T09:58:00Z",
            "masterId": f"SAFOR-MASTER:{project_id}",
            "masterVersion": "0.14.0-rc.6",
            "masterRunId": "run-test",
            "masterStateRevision": 1,
            "planningRef": pointer("projects/example/planning/plan.json"),
            "mandateRef": pointer("projects/example/decisions/mandate.json"),
        },
        "assignment": {
            "agentId": agent_id,
            "displayName": display_name,
            "identityRevision": identity_revision,
            "identityRef": pointer(f"projects/example/agents/{agent_id}/identity.json"),
            "assignmentMode": "EXCLUSIVE",
            "assignmentReason": "Exact test assignment.",
        },
        "domainContext": {
            "creationType": "WEBSITE",
            "domainId": "WEBSITE_CREATION",
            "factoryRef": pointer("packages/factory.json"),
            "operatingModelRef": pointer("packages/operating-model.json"),
            "compatibilityDecisionRef": pointer("packages/compatibility-decision.json"),
        },
        "roleContract": {
            "roleId": "TEST_CONTRIBUTOR",
            "roleName": "Test Contributor",
            "roleDefinitionRef": pointer("profiles/roles/test-contributor.json"),
            "mission": "Execute the exact test job.",
            "responsibilities": ["Respect scope."],
            "mustNotActAs": ["MASTER", "REVIEWER"],
            "decisionRights": [],
            "authorityExpansionAllowed": False,
        },
        "skills": [
            {
                "skillId": "test-skill",
                "skillVersion": "1.0.0",
                "mandatory": True,
                "description": "Test execution.",
                "executionInstructions": ["Follow the pinned contract."],
                "useFor": ["testing"],
                "skillRef": pointer("profiles/skills/test-skill.json"),
                "requiredLevel": "PROFICIENT",
            }
        ],
        "task": {
            "title": "Execute test",
            "objective": "Produce one verified test result.",
            "instruction": "Execute only the pinned scope.",
            "expectedOutcome": "A provider-verifiable result.",
            "completionDefinition": "All checks pass.",
            "inScope": ["test-output"],
            "outOfScope": ["deployment"],
            "assumptions": ["Pinned inputs are authoritative."],
            "acceptanceCriteria": ["Scope respected."],
        },
        "dependencies": {
            "requiredWorkItems": [],
            "dependencyPredicate": "ALL_REQUIRED_ACCEPTED",
        },
        "inputs": [
            {
                "inputId": "input-1",
                "artifactRef": pointer("artifacts/input.json"),
                "mode": "READ_ONLY",
                "expectedType": "TEST_INPUT",
                "purpose": "Test input.",
            }
        ],
        "authorization": {
            "authorityBasis": pointer("projects/example/decisions/mandate.json"),
            "actualProviderRightsMustBeVerified": True,
            "repositoryPermissions": [
                {
                    "repositoryClass": "WORK_REPOSITORY",
                    "repository": product_repository,
                    "read": True,
                    "write": {
                        "allowed": True,
                        "allowedBranches": [product_branch],
                        "allowedPaths": ["test-output/"],
                    },
                    "branchCreate": False,
                    "commit": True,
                    "push": True,
                    "changeRequestCreate": False,
                    "merge": False,
                    "deploy": False,
                },
                {
                    "repositoryClass": "CONTROL_REPOSITORY",
                    "repository": control_repository,
                    "read": True,
                    "write": {
                        "allowed": True,
                        "allowedBranches": [control_branch],
                        "allowedPaths": [
                            f"projects/example/agents/{agent_id}/state.json",
                            f"projects/example/agents/{agent_id}/outbox/",
                            f"projects/example/agents/{agent_id}/evidence/",
                        ],
                    },
                    "branchCreate": False,
                    "commit": True,
                    "push": True,
                    "changeRequestCreate": False,
                    "merge": False,
                    "deploy": False,
                },
            ],
            "responseWriteDoesNotGrantProductWrite": True,
            "productWriteDoesNotGrantResponseWrite": True,
            "explicitlyForbidden": ["default branch mutation", "MASTER state write", "merge", "deployment"],
        },
        "workspace": {
            "productWorkspace": {
                "workspaceClass": "REMOTE_GIT",
                "repository": product_repository,
                "defaultBranch": "main",
                "jobBranch": product_branch,
                "baseCommitSha": "abcdef1234567",
                "allowedPaths": ["test-output/"],
                "mutating": True,
            },
            "responseWorkspace": target(
                "CONTROL_REPOSITORY",
                control_repository,
                control_branch,
                f"projects/example/agents/{agent_id}/outbox/",
                ["READ", "CREATE", "MODIFY", "COMMIT", "PUSH"],
            ),
            "readSet": [pointer("artifacts/input.json")],
            "exclusiveKeys": [f"branch:{product_branch}"],
        },
        "scheduling": {
            "priority": 10,
            "dispatchRevision": dispatch_revision,
            "dispatchState": "WAITING_HUMAN_GO",
            "dispatchWaveRef": pointer("master/dispatch-waves/wave-test.json"),
            "resourceLeaseRefs": [],
            "activationMode": "HUMAN_GO_REQUIRED",
            "claimPolicy": {
                "exclusiveAgentClaim": True,
                "optimisticConcurrencyRequired": True,
                "humanGoEvidenceRequired": True,
                "claimAuthority": "AGENT_STATE_PROVIDER_CAS_READBACK",
                "claimStateTarget": target(
                    "CONTROL_REPOSITORY",
                    control_repository,
                    control_branch,
                    f"projects/example/agents/{agent_id}/state.json",
                    ["READ", "MODIFY", "COMMIT", "PUSH", "COMPARE_AND_SWAP"],
                ),
                "humanGoEvidenceSchemaRef": pointer(
                    "v0.14.0/schemas/human-go-evidence.schema.json",
                    "empishaj/SAFOR",
                ),
                "humanGoEvidenceTemplateRef": pointer(
                    "v0.14.0/templates/human-go-evidence.template.json",
                    "empishaj/SAFOR",
                ),
                "goEvidenceWriteTarget": target(
                    "CONTROL_REPOSITORY",
                    control_repository,
                    control_branch,
                    f"projects/example/agents/{agent_id}/evidence/{{jobId}}/human-go-{{activationId}}.json",
                    ["READ", "CREATE", "COMMIT", "PUSH"],
                ),
                "agentStateSchemaRef": pointer(
                    "v0.14.0/schemas/agent-state.schema.json",
                    "empishaj/SAFOR",
                ),
                "claimStateTemplateRef": pointer(
                    "v0.14.0/templates/agent-state-claim.template.json",
                    "empishaj/SAFOR",
                ),
                "resultSubmittedStateTemplateRef": pointer(
                    "v0.14.0/templates/agent-state-result-submitted.template.json",
                    "empishaj/SAFOR",
                ),
                "settledRearmStateTemplateRef": pointer(
                    "v0.14.0/templates/agent-state-settled-rearm.template.json",
                    "empishaj/SAFOR",
                ),
                "preCasSchemaValidationRequired": True,
                "postReadbackSchemaValidationRequired": True,
                "goEvidenceProviderReadbackRequired": True,
            },
        },
        "outputContract": {
            "requiredOutputs": ["TEST_OUTPUT"],
            "productWriteTarget": target(
                "WORK_REPOSITORY",
                product_repository,
                product_branch,
                "test-output/",
                ["READ", "CREATE", "MODIFY", "COMMIT", "PUSH"],
            ),
        },
        "responseContracts": response_contracts,
        "communicationContract": {
            "modelRef": pointer(
                "v0.14.0/agent-communication-model.json",
                "empishaj/SAFOR",
            ),
            "chatOutputSchemaRef": pointer(
                "v0.14.0/schemas/agent-chat-output.schema.json",
                "empishaj/SAFOR",
            ),
            "humanDomainConversationAllowed": False,
            "detailedReportsInGit": True,
            "allowedStatuses": [
                "READY",
                "STARTED",
                "SUBMITTED",
                "BLOCKED",
                "REIDENTIFICATION_REQUIRED",
            ],
        },
        "verificationContract": {
            "acceptanceCriteria": ["All task criteria pass."],
            "evidenceRequirements": ["TEST_RESULT_EVIDENCE"],
            "independentReviewRequired": False,
            "reviewerMustDifferFromAuthor": False,
            "acceptanceAuthority": "MASTER",
            "integrationAuthority": "MASTER_OR_EXPLICIT_HUMAN_AUTHORITY",
        },
        "constraints": {
            "stopConditions": ["STOP", "PAUSE", "identity mismatch", "missing permission"],
            "noScopeExpansion": True,
            "noRoleSwitch": True,
            "noSelfAcceptance": True,
            "noMasterStateWrite": True,
            "noAutomaticJobSwitch": True,
            "noJobPromptTransport": True,
        },
        "humanReadableProjection": pointer(
            f"projects/example/agents/{agent_id}/inbox/{job_id}.md"
        ),
    }


def expected_job_binding(job, *, blob_sha: str = "jobblob123", contract_path: str | None = None):
    return {
        "projectId": job["lineage"]["projectId"],
        "jobId": job["identity"]["jobId"],
        "packageId": job["lineage"]["packageId"],
        "workItemId": job["lineage"]["workItemId"],
        "agentId": job["assignment"]["agentId"],
        "identityRevision": job["assignment"]["identityRevision"],
        "jobContractBlobSha": blob_sha,
        "jobContractPath": contract_path or f"projects/example/agents/{job['assignment']['agentId']}/inbox/job.json",
    }


def canonical_response_index(*, response, response_blob_sha: str = "responseblob123"):
    return {
        "format": "SAFOR_AGENT_RESPONSE_INDEX",
        "schemaVersion": "0.14.0",
        "projectId": response["projectId"],
        "agentId": response["agentId"],
        "identityRevision": response["identityRevision"],
        "revision": 1,
        "authoritativeAcceptance": False,
        "entries": [
            {
                "responseId": response["responseId"],
                "responseType": response["responseType"],
                "jobId": response["jobId"],
                "responseRef": pointer(
                    f"projects/example/agents/{response['agentId']}/outbox/{response['jobId']}/{response['responseId']}.json",
                    blob_sha=response_blob_sha,
                ),
                "createdAt": response["createdAt"],
                "responseState": "SUBMITTED",
                "resolutionRef": None,
            }
        ],
        "updatedAt": response["createdAt"],
    }
