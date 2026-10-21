from __future__ import annotations
import re
from typing import Any, Mapping
from runtime.go_evidence import GoEvidenceValidationError, validate_human_go_evidence

class AgentJobValidationError(ValueError):
    """Raised when a v0.14 agent job or chat status is unsafe."""
_REQUIRED_RESPONSE_TYPES = {'JOB_RESULT', 'JOB_ERROR', 'CLARIFICATION_REQUEST', 'CAPABILITY_MISMATCH', 'IMPROVEMENT_PROPOSAL'}
_TEMPLATE_PATHS = {'JOB_RESULT': 'v0.14.0/templates/responses/job-result.template.json', 'JOB_ERROR': 'v0.14.0/templates/responses/job-error.template.json', 'CLARIFICATION_REQUEST': 'v0.14.0/templates/responses/clarification-request.template.json', 'CAPABILITY_MISMATCH': 'v0.14.0/templates/responses/capability-mismatch.template.json', 'IMPROVEMENT_PROPOSAL': 'v0.14.0/templates/responses/improvement-proposal.template.json'}
_UUIDV7 = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
_TRANSITIONS = {'PREPARED': {'WAITING_HUMAN_GO', 'CANCELED', 'SUPERSEDED'}, 'WAITING_HUMAN_GO': {'GO_OBSERVED', 'CANCELED', 'SUPERSEDED'}, 'GO_OBSERVED': {'CLAIMED', 'BLOCKED', 'CANCELED'}, 'CLAIMED': {'RUNNING', 'BLOCKED', 'CANCELED'}, 'RUNNING': {'RESPONSE_SUBMITTED', 'BLOCKED', 'CANCELED'}, 'RESPONSE_SUBMITTED': {'VERIFIED', 'REJECTED', 'BLOCKED'}, 'VERIFIED': {'ACCEPTED', 'REJECTED'}, 'ACCEPTED': {'INTEGRATED'}, 'REJECTED': {'REWORK_READY', 'CANCELED'}, 'BLOCKED': {'REWORK_READY', 'SUPERSEDED', 'CANCELED'}, 'REWORK_READY': {'WAITING_HUMAN_GO', 'SUPERSEDED', 'CANCELED'}}

def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentJobValidationError(f'{name} must be a mapping')
    return value

def _nonempty(value: Any, code: str) -> str:
    text = str(value or '').strip()
    if not text:
        raise AgentJobValidationError(code)
    return text

def _pointer(value: Any, name: str) -> Mapping[str, Any]:
    pointer = _mapping(value, name)
    for field in ('repository', 'ref', 'path', 'blobSha'):
        _nonempty(pointer.get(field), f'{name.upper()}_{field.upper()}_MISSING')
    if len(str(pointer['blobSha'])) < 7:
        raise AgentJobValidationError(f'{name.upper()}_BLOB_SHA_INVALID')
    return pointer

def _write_target(value: Any, name: str) -> Mapping[str, Any]:
    target = _mapping(value, name)
    for field in ('repositoryClass', 'repository', 'branch', 'pathPattern', 'allowedOperations'):
        if field not in target:
            raise AgentJobValidationError(f'{name.upper()}_{field.upper()}_MISSING')
    if target['repositoryClass'] not in {'WORK_REPOSITORY', 'CONTROL_REPOSITORY'}:
        raise AgentJobValidationError(f'{name.upper()}_CLASS_INVALID')
    if not isinstance(target['allowedOperations'], list) or not target['allowedOperations']:
        raise AgentJobValidationError(f'{name.upper()}_OPERATIONS_INVALID')
    return target

def validate_agent_job(job: Mapping[str, Any]) -> None:
    """Reference validator; the JSON contract remains normative."""
    job = _mapping(job, 'job')
    if job.get('format') != 'SAFOR_AGENT_JOB':
        raise AgentJobValidationError('JOB_FORMAT_INVALID')
    if job.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('JOB_SCHEMA_VERSION_INVALID')
    identity = _mapping(job.get('identity'), 'identity')
    job_id = _nonempty(identity.get('jobId'), 'JOB_ID_MISSING')
    if not _UUIDV7.fullmatch(job_id):
        raise AgentJobValidationError('JOB_ID_MUST_BE_UUIDV7')
    if identity.get('immutableAfterPublication') is not True:
        raise AgentJobValidationError('JOB_MUST_BE_IMMUTABLE_AFTER_PUBLICATION')
    assignment = _mapping(job.get('assignment'), 'assignment')
    agent_id = _nonempty(assignment.get('agentId'), 'ASSIGNED_AGENT_ID_MISSING')
    display_name = _nonempty(assignment.get('displayName'), 'ASSIGNED_DISPLAY_NAME_MISSING')
    if ' '.join(agent_id.casefold().split()) == ' '.join(display_name.casefold().split()):
        raise AgentJobValidationError('DISPLAY_NAME_MUST_DIFFER_FROM_AGENT_ID')
    if not isinstance(assignment.get('identityRevision'), int):
        raise AgentJobValidationError('ASSIGNED_IDENTITY_REVISION_INVALID')
    _pointer(assignment.get('identityRef'), 'identityRef')
    lineage = _mapping(job.get('lineage'), 'lineage')
    sequence = _mapping(lineage.get('sequence'), 'sequence')
    attempt = sequence.get('attempt')
    rework_cycle = sequence.get('reworkCycle')
    if not isinstance(attempt, int) or attempt < 1:
        raise AgentJobValidationError('ATTEMPT_INVALID')
    if not isinstance(rework_cycle, int) or rework_cycle < 0:
        raise AgentJobValidationError('REWORK_CYCLE_INVALID')
    if attempt > 1 or rework_cycle > 0:
        _nonempty(lineage.get('supersedesJobId'), 'REWORK_MUST_REFERENCE_SUPERSEDED_JOB')
        if lineage.get('triggerConflictRef') is None:
            raise AgentJobValidationError('REWORK_MUST_REFERENCE_TRIGGER_CONFLICT')
        _pointer(lineage.get('triggerConflictRef'), 'triggerConflictRef')
    elif lineage.get('supersedesJobId') is not None:
        raise AgentJobValidationError('FIRST_ATTEMPT_MUST_NOT_SUPERSEDE_JOB')
    domain = _mapping(job.get('domainContext'), 'domainContext')
    for field in ('creationType', 'domainId', 'factoryRef', 'operatingModelRef', 'compatibilityDecisionRef'):
        if field not in domain:
            raise AgentJobValidationError(f'DOMAIN_{field.upper()}_MISSING')
    for field in ('factoryRef', 'operatingModelRef', 'compatibilityDecisionRef'):
        _pointer(domain[field], field)
    role = _mapping(job.get('roleContract'), 'roleContract')
    _nonempty(role.get('roleId'), 'ROLE_ID_MISSING')
    _pointer(role.get('roleDefinitionRef'), 'roleDefinitionRef')
    if role.get('authorityExpansionAllowed') is not False:
        raise AgentJobValidationError('ROLE_AUTHORITY_EXPANSION_FORBIDDEN')
    skills = job.get('skills')
    if not isinstance(skills, list) or not skills:
        raise AgentJobValidationError('AT_LEAST_ONE_SKILL_REQUIRED')
    for index, skill_value in enumerate(skills):
        skill = _mapping(skill_value, f'skill[{index}]')
        for field in ('skillId', 'skillVersion', 'description', 'executionInstructions', 'useFor', 'requiredLevel'):
            if field not in skill:
                raise AgentJobValidationError(f'SKILL_{index}_{field.upper()}_MISSING')
        _pointer(skill.get('skillRef'), f'skillRef[{index}]')
    task = _mapping(job.get('task'), 'task')
    for field in ('title', 'objective', 'instruction', 'expectedOutcome', 'completionDefinition', 'inScope', 'outOfScope', 'assumptions', 'acceptanceCriteria'):
        if field not in task:
            raise AgentJobValidationError(f'TASK_{field.upper()}_MISSING')
    if not isinstance(task['acceptanceCriteria'], list) or not task['acceptanceCriteria']:
        raise AgentJobValidationError('TASK_ACCEPTANCE_CRITERIA_REQUIRED')
    for index, raw in enumerate(job.get('inputs') or []):
        item = _mapping(raw, f'input[{index}]')
        _pointer(item.get('artifactRef'), f'inputRef[{index}]')
        if item.get('mode') != 'READ_ONLY':
            raise AgentJobValidationError('JOB_INPUT_MUST_BE_READ_ONLY')
    authorization = _mapping(job.get('authorization'), 'authorization')
    _pointer(authorization.get('authorityBasis'), 'authorityBasis')
    if authorization.get('actualProviderRightsMustBeVerified') is not True:
        raise AgentJobValidationError('ACTUAL_PROVIDER_RIGHTS_CHECK_REQUIRED')
    if authorization.get('responseWriteDoesNotGrantProductWrite') is not True:
        raise AgentJobValidationError('RESPONSE_WRITE_MUST_NOT_GRANT_PRODUCT_WRITE')
    if authorization.get('productWriteDoesNotGrantResponseWrite') is not True:
        raise AgentJobValidationError('PRODUCT_WRITE_MUST_NOT_GRANT_RESPONSE_WRITE')
    permissions = authorization.get('repositoryPermissions')
    if not isinstance(permissions, list) or len(permissions) < 2:
        raise AgentJobValidationError('SEPARATE_REPOSITORY_PERMISSIONS_REQUIRED')
    classes = {p.get('repositoryClass') for p in permissions if isinstance(p, Mapping)}
    if not {'WORK_REPOSITORY', 'CONTROL_REPOSITORY'}.issubset(classes):
        raise AgentJobValidationError('WORK_AND_CONTROL_PERMISSION_CLASSES_REQUIRED')
    for permission in permissions:
        permission = _mapping(permission, 'repositoryPermission')
        if permission.get('merge') is not False or permission.get('deploy') is not False:
            raise AgentJobValidationError('AGENT_MERGE_AND_DEPLOY_MUST_BE_FORBIDDEN')
    workspace = _mapping(job.get('workspace'), 'workspace')
    response_workspace = _write_target(workspace.get('responseWorkspace'), 'responseWorkspace')
    if response_workspace['repositoryClass'] != 'CONTROL_REPOSITORY':
        raise AgentJobValidationError('RESPONSE_WORKSPACE_MUST_BE_CONTROL_REPOSITORY')
    product_workspace = workspace.get('productWorkspace')
    output = _mapping(job.get('outputContract'), 'outputContract')
    product_target = output.get('productWriteTarget')
    if product_workspace is not None:
        product_workspace = _mapping(product_workspace, 'productWorkspace')
        if product_workspace.get('mutating') is True:
            if product_workspace.get('jobBranch') == product_workspace.get('defaultBranch'):
                raise AgentJobValidationError('DIRECT_DEFAULT_BRANCH_MUTATION_FORBIDDEN')
            product_target = _write_target(product_target, 'productWriteTarget')
            if product_target['repositoryClass'] != 'WORK_REPOSITORY':
                raise AgentJobValidationError('PRODUCT_TARGET_MUST_BE_WORK_REPOSITORY')
            if product_target['repository'] != product_workspace.get('repository'):
                raise AgentJobValidationError('PRODUCT_TARGET_REPOSITORY_MISMATCH')
            if product_target['branch'] != product_workspace.get('jobBranch'):
                raise AgentJobValidationError('PRODUCT_TARGET_BRANCH_MISMATCH')
            if product_workspace.get('workspaceClass') == 'REMOTE_GIT' and product_target['repository'] == response_workspace['repository']:
                raise AgentJobValidationError('REMOTE_PRODUCT_AND_RESPONSE_REPOSITORIES_MUST_DIFFER')
    elif product_target is not None:
        raise AgentJobValidationError('READ_ONLY_JOB_MUST_NOT_DECLARE_PRODUCT_WRITE_TARGET')
    scheduling = _mapping(job.get('scheduling'), 'scheduling')
    if scheduling.get('dispatchState') != 'WAITING_HUMAN_GO':
        raise AgentJobValidationError('JOB_MUST_PUBLISH_AS_WAITING_HUMAN_GO')
    if scheduling.get('activationMode') != 'HUMAN_GO_REQUIRED':
        raise AgentJobValidationError('JOB_MUST_REQUIRE_HUMAN_GO')
    claim = _mapping(scheduling.get('claimPolicy'), 'claimPolicy')
    if claim.get('humanGoEvidenceRequired') is not True:
        raise AgentJobValidationError('CLAIM_REQUIRES_HUMAN_GO_EVIDENCE')
    if claim.get('claimAuthority') != 'AGENT_STATE_PROVIDER_CAS_READBACK':
        raise AgentJobValidationError('CLAIM_AUTHORITY_MUST_BE_AGENT_STATE_CAS')
    claim_target = _write_target(claim.get('claimStateTarget'), 'claimStateTarget')
    if claim_target['repositoryClass'] != 'CONTROL_REPOSITORY':
        raise AgentJobValidationError('CLAIM_TARGET_MUST_BE_CONTROL_REPOSITORY')
    expected_claim_suffix = f"agents/{agent_id}/state.json"
    if not str(claim_target.get('pathPattern', '')).endswith(expected_claim_suffix):
        raise AgentJobValidationError('CLAIM_TARGET_MUST_BE_ASSIGNED_AGENT_STATE')
    if '/master/jobs/' in str(claim_target.get('pathPattern', '')):
        raise AgentJobValidationError('AGENT_MASTER_JOB_STATE_CLAIM_FORBIDDEN')
    required_claim_ops = {'READ', 'MODIFY', 'COMMIT', 'PUSH', 'COMPARE_AND_SWAP'}
    if not required_claim_ops.issubset(set(claim_target.get('allowedOperations') or ())):
        raise AgentJobValidationError('CLAIM_TARGET_OPERATIONS_INCOMPLETE')
    if claim_target['repository'] != response_workspace['repository'] or claim_target['branch'] != response_workspace['branch']:
        raise AgentJobValidationError('CLAIM_TARGET_CONTROL_WORKSPACE_MISMATCH')

    claim_refs = {
        'humanGoEvidenceSchemaRef': 'v0.14.0/schemas/human-go-evidence.schema.json',
        'humanGoEvidenceTemplateRef': 'v0.14.0/templates/human-go-evidence.template.json',
        'agentStateSchemaRef': 'v0.14.0/schemas/agent-state.schema.json',
        'claimStateTemplateRef': 'v0.14.0/templates/agent-state-claim.template.json',
        'resultSubmittedStateTemplateRef': 'v0.14.0/templates/agent-state-result-submitted.template.json',
        'settledRearmStateTemplateRef': 'v0.14.0/templates/agent-state-settled-rearm.template.json',
    }
    for field, expected_path in claim_refs.items():
        ref = _pointer(claim.get(field), field)
        if ref['path'] != expected_path:
            raise AgentJobValidationError(f'CLAIM_BINDING_PATH_MISMATCH:{field}')
    go_target = _write_target(claim.get('goEvidenceWriteTarget'), 'goEvidenceWriteTarget')
    if go_target['repositoryClass'] != 'CONTROL_REPOSITORY':
        raise AgentJobValidationError('GO_EVIDENCE_TARGET_MUST_BE_CONTROL_REPOSITORY')
    expected_go_suffix = f"agents/{agent_id}/evidence/{{jobId}}/human-go-{{activationId}}.json"
    if not str(go_target.get('pathPattern', '')).endswith(expected_go_suffix):
        raise AgentJobValidationError('GO_EVIDENCE_TARGET_PATH_INVALID')
    required_go_ops = {'READ', 'CREATE', 'COMMIT', 'PUSH'}
    if not required_go_ops.issubset(set(go_target.get('allowedOperations') or ())):
        raise AgentJobValidationError('GO_EVIDENCE_TARGET_OPERATIONS_INCOMPLETE')
    if go_target['repository'] != response_workspace['repository'] or go_target['branch'] != response_workspace['branch']:
        raise AgentJobValidationError('GO_EVIDENCE_TARGET_CONTROL_WORKSPACE_MISMATCH')
    for field in (
        'preCasSchemaValidationRequired',
        'postReadbackSchemaValidationRequired',
        'goEvidenceProviderReadbackRequired',
    ):
        if claim.get(field) is not True:
            raise AgentJobValidationError(f'CLAIM_SCHEMA_VALIDATION_REQUIRED:{field}')

    responses = _mapping(job.get('responseContracts'), 'responseContracts')
    if not _REQUIRED_RESPONSE_TYPES.issubset(responses):
        missing = sorted(_REQUIRED_RESPONSE_TYPES - set(responses))
        raise AgentJobValidationError(f'REQUIRED_RESPONSE_CONTRACTS_MISSING:{missing}')
    response_repositories = set()
    for response_type in sorted(_REQUIRED_RESPONSE_TYPES):
        binding = _mapping(responses[response_type], response_type)
        if binding.get('responseType') != response_type:
            raise AgentJobValidationError(f'RESPONSE_TYPE_BINDING_MISMATCH:{response_type}')
        template_ref = _pointer(binding.get('templateRef'), 'templateRef')
        if template_ref['path'] != _TEMPLATE_PATHS[response_type]:
            raise AgentJobValidationError(f'RESPONSE_TEMPLATE_MISMATCH:{response_type}')
        schema_ref = _pointer(binding.get('schemaRef'), 'schemaRef')
        if schema_ref['path'] != 'v0.14.0/schemas/agent-response.schema.json':
            raise AgentJobValidationError(f'RESPONSE_SCHEMA_MISMATCH:{response_type}')
        target = _write_target(binding.get('writeTarget'), 'responseWriteTarget')
        if target['repositoryClass'] != 'CONTROL_REPOSITORY':
            raise AgentJobValidationError(f'RESPONSE_TARGET_NOT_CONTROL:{response_type}')
        expected_response_suffix = (
            f"agents/{agent_id}/outbox/{{jobId}}/{{responseId}}.json"
        )
        if not str(target.get('pathPattern', '')).endswith(expected_response_suffix):
            raise AgentJobValidationError(
                f'RESPONSE_TARGET_PATH_INVALID:{response_type}'
            )
        response_repositories.add((target['repository'], target['branch']))
        if binding.get('required') is not True:
            raise AgentJobValidationError(f'RESPONSE_CONTRACT_MUST_BE_REQUIRED:{response_type}')
        for validation_field in (
            'preWriteSchemaValidationRequired',
            'providerReadbackRequired',
            'postReadbackSchemaValidationRequired',
        ):
            if binding.get(validation_field) is not True:
                raise AgentJobValidationError(
                    f'RESPONSE_SCHEMA_VALIDATION_REQUIRED:{response_type}:{validation_field}'
                )
    if len(response_repositories) != 1:
        raise AgentJobValidationError('ALL_RESPONSE_TYPES_MUST_SHARE_CONTROL_TARGET')
    index_target = _write_target(responses.get('responseIndexTarget'), 'responseIndexTarget')
    if (index_target['repository'], index_target['branch']) not in response_repositories:
        raise AgentJobValidationError('RESPONSE_INDEX_TARGET_MISMATCH')
    expected_index_suffix = f"agents/{agent_id}/outbox/index.json"
    if not str(index_target.get('pathPattern', '')).endswith(expected_index_suffix):
        raise AgentJobValidationError('RESPONSE_INDEX_TARGET_PATH_INVALID')
    _pointer(responses.get('resolutionSchemaRef'), 'resolutionSchemaRef')
    communication = _mapping(job.get('communicationContract'), 'communicationContract')
    _pointer(communication.get('modelRef'), 'communicationModelRef')
    _pointer(communication.get('chatOutputSchemaRef'), 'chatOutputSchemaRef')
    if communication.get('humanDomainConversationAllowed') is not False:
        raise AgentJobValidationError('AGENT_HUMAN_DOMAIN_DIALOG_FORBIDDEN')
    if communication.get('detailedReportsInGit') is not True:
        raise AgentJobValidationError('DETAILED_REPORTS_MUST_BE_IN_GIT')
    required_statuses = {'READY', 'STARTED', 'SUBMITTED', 'BLOCKED', 'REIDENTIFICATION_REQUIRED'}
    if set(communication.get('allowedStatuses') or []) != required_statuses:
        raise AgentJobValidationError('CHAT_STATUS_SET_INVALID')
    verification = _mapping(job.get('verificationContract'), 'verificationContract')
    if verification.get('acceptanceAuthority') != 'MASTER':
        raise AgentJobValidationError('MASTER_MUST_RETAIN_ACCEPTANCE')
    if verification.get('independentReviewRequired') is True and verification.get('reviewerMustDifferFromAuthor') is not True:
        raise AgentJobValidationError('INDEPENDENT_REVIEWER_MUST_DIFFER')
    constraints = _mapping(job.get('constraints'), 'constraints')
    for field in ('noScopeExpansion', 'noRoleSwitch', 'noSelfAcceptance', 'noMasterStateWrite', 'noAutomaticJobSwitch', 'noJobPromptTransport'):
        if constraints.get(field) is not True:
            raise AgentJobValidationError(f'JOB_CONSTRAINT_REQUIRED:{field}')


def _path_is_covered(path: str, allowed_paths: list[str]) -> bool:
    value = str(path or "")
    for allowed in allowed_paths:
        prefix = str(allowed or "")
        if not prefix:
            continue
        if value == prefix or value.startswith(prefix):
            return True
    return False


def validate_authority_basis_coverage(
    *,
    job: Mapping[str, Any],
    authority_basis: Mapping[str, Any],
    authority_basis_ref: Mapping[str, Any] | None = None,
) -> None:
    """Fail closed when a resolved active mandate does not cover the Job.

    The job's authorityBasis pointer stays immutable. MASTER and the Agent may
    use this validator after provider readback of that pointer. Provider rights
    remain a separate, mandatory check.
    """

    validate_agent_job(job)
    job = _mapping(job, "job")
    mandate = _mapping(authority_basis, "authorityBasisRecord")
    authorization = _mapping(job.get("authorization"), "authorization")
    pinned = _pointer(authorization.get("authorityBasis"), "authorityBasis")

    if authority_basis_ref is not None:
        observed = _pointer(authority_basis_ref, "authorityBasisRef")
        for field in ("repository", "ref", "path", "blobSha"):
            if observed.get(field) != pinned.get(field):
                raise AgentJobValidationError(
                    f"AUTHORITY_BASIS_POINTER_MISMATCH:{field}"
                )

    if mandate.get("schemaVersion") != "0.14.0":
        raise AgentJobValidationError("AUTHORITY_BASIS_SCHEMA_VERSION_INVALID")
    if mandate.get("status") != "ACTIVE":
        raise AgentJobValidationError("AUTHORITY_BASIS_NOT_ACTIVE")

    lineage = _mapping(job.get("lineage"), "lineage")
    assignment = _mapping(job.get("assignment"), "assignment")
    if mandate.get("projectId") != lineage.get("projectId"):
        raise AgentJobValidationError("AUTHORITY_BASIS_PROJECT_MISMATCH")
    if mandate.get("agentId") != assignment.get("agentId"):
        raise AgentJobValidationError("AUTHORITY_BASIS_AGENT_MISMATCH")

    if mandate.get("humanGoRequired") is not True:
        raise AgentJobValidationError("AUTHORITY_BASIS_HUMAN_GO_REQUIRED")
    if mandate.get("humanOnlyActivation") is not True:
        raise AgentJobValidationError("AUTHORITY_BASIS_HUMAN_ONLY_REQUIRED")
    if mandate.get("masterMayActivateAgent") is not False:
        raise AgentJobValidationError("AUTHORITY_BASIS_MASTER_ACTIVATION_FORBIDDEN")
    if mandate.get("mergeAllowed") is not False:
        raise AgentJobValidationError("AUTHORITY_BASIS_MERGE_FORBIDDEN")
    if mandate.get("deployAllowed") is not False:
        raise AgentJobValidationError("AUTHORITY_BASIS_DEPLOY_FORBIDDEN")

    permissions = authorization.get("repositoryPermissions") or []
    product_permissions = [
        _mapping(p, "productPermission")
        for p in permissions
        if isinstance(p, Mapping) and p.get("repositoryClass") == "WORK_REPOSITORY"
    ]
    control_permissions = [
        _mapping(p, "controlPermission")
        for p in permissions
        if isinstance(p, Mapping) and p.get("repositoryClass") == "CONTROL_REPOSITORY"
    ]
    if len(product_permissions) != 1 or len(control_permissions) != 1:
        raise AgentJobValidationError("AUTHORITY_BASIS_PERMISSION_CLASS_CARDINALITY_INVALID")

    product = product_permissions[0]
    control = control_permissions[0]
    if product.get("repository") != mandate.get("allowedProductRepository"):
        raise AgentJobValidationError("AUTHORITY_BASIS_PRODUCT_REPOSITORY_NOT_COVERED")

    allowed_product_branches = mandate.get("allowedProductBranches")
    if allowed_product_branches is None:
        single = mandate.get("allowedProductBranch")
        allowed_product_branches = [single] if single else []
    if not isinstance(allowed_product_branches, list) or not allowed_product_branches:
        raise AgentJobValidationError("AUTHORITY_BASIS_PRODUCT_BRANCH_SET_MISSING")

    product_write = _mapping(product.get("write"), "productWriteScope")
    requested_product_branches = list(product_write.get("allowedBranches") or [])
    workspace = _mapping(job.get("workspace"), "workspace")
    raw_product_workspace = workspace.get("productWorkspace")
    product_workspace = (
        None
        if raw_product_workspace is None
        else _mapping(raw_product_workspace, "productWorkspace")
    )
    output = _mapping(job.get("outputContract"), "outputContract")
    raw_product_target = output.get("productWriteTarget")
    product_target = (
        None
        if raw_product_target is None
        else _write_target(raw_product_target, "productWriteTarget")
    )

    if product_write.get("allowed") is not True:
        if product_workspace is not None and product_workspace.get("mutating") is True:
            raise AgentJobValidationError(
                "AUTHORITY_BASIS_READ_ONLY_PRODUCT_MUTATION_FORBIDDEN"
            )
        if product_target is not None:
            raise AgentJobValidationError(
                "AUTHORITY_BASIS_READ_ONLY_PRODUCT_TARGET_FORBIDDEN"
            )

    if product_workspace is not None:
        requested_product_branches.append(
            str(product_workspace.get("jobBranch") or "")
        )
    if product_target is not None:
        requested_product_branches.append(str(product_target.get("branch") or ""))
    for requested in requested_product_branches:
        if requested not in allowed_product_branches:
            raise AgentJobValidationError(
                "AUTHORITY_BASIS_PRODUCT_BRANCH_NOT_COVERED"
            )

    allowed_paths = mandate.get("allowedProductPaths")
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise AgentJobValidationError("AUTHORITY_BASIS_PRODUCT_PATH_SET_MISSING")
    requested_paths = list(product_write.get("allowedPaths") or [])
    if product_workspace is not None:
        requested_paths.extend(product_workspace.get("allowedPaths") or [])
    if product_target is not None:
        requested_paths.append(str(product_target.get("pathPattern") or ""))
    for requested in requested_paths:
        if not _path_is_covered(str(requested), allowed_paths):
            raise AgentJobValidationError("AUTHORITY_BASIS_PRODUCT_PATH_NOT_COVERED")

    allowed_control_branch = _nonempty(
        mandate.get("allowedControlBranch"),
        "AUTHORITY_BASIS_CONTROL_BRANCH_MISSING",
    )
    control_branches = list(
        _mapping(control.get("write"), "controlWriteScope").get("allowedBranches") or []
    )
    response_workspace = _write_target(
        workspace.get("responseWorkspace"), "responseWorkspace"
    )
    control_branches.append(str(response_workspace.get("branch") or ""))
    claim = _mapping(
        _mapping(job.get("scheduling"), "scheduling").get("claimPolicy"),
        "claimPolicy",
    )
    control_branches.append(
        str(_write_target(claim.get("claimStateTarget"), "claimStateTarget").get("branch") or "")
    )
    control_branches.append(
        str(_write_target(claim.get("goEvidenceWriteTarget"), "goEvidenceWriteTarget").get("branch") or "")
    )
    for requested in control_branches:
        if requested != allowed_control_branch:
            raise AgentJobValidationError(
                "AUTHORITY_BASIS_CONTROL_BRANCH_NOT_COVERED"
            )

    provenance = _mapping(job.get("provenance"), "provenance")
    mandate_ref = _pointer(provenance.get("mandateRef"), "mandateRef")
    for field in ("repository", "ref", "path", "blobSha"):
        if mandate_ref.get(field) != pinned.get(field):
            raise AgentJobValidationError(
                f"JOB_MANDATE_AND_AUTHORITY_BASIS_POINTER_MISMATCH:{field}"
            )

def validate_job_state_transition(*, from_status: str, to_status: str, evidence_refs: list[Any], go_evidence: Mapping[str, Any] | None = None, expected_go_context: Mapping[str, Any] | None = None, consumed_activation_ids: set[str] | frozenset[str] | None = None) -> None:
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise AgentJobValidationError(f'JOB_STATE_TRANSITION_FORBIDDEN:{from_status}->{to_status}')
    if from_status == 'WAITING_HUMAN_GO' and to_status == 'GO_OBSERVED':
        if go_evidence is None or expected_go_context is None:
            raise AgentJobValidationError('STRUCTURED_GO_EVIDENCE_REQUIRED')
        try:
            validate_human_go_evidence(
                go_evidence,
                expected=expected_go_context,
                consumed_activation_ids=consumed_activation_ids,
            )
        except GoEvidenceValidationError as exc:
            raise AgentJobValidationError(str(exc)) from exc
        if not evidence_refs or not all(isinstance(ref, Mapping) for ref in evidence_refs):
            raise AgentJobValidationError('GO_EVIDENCE_POINTER_REQUIRED')
        for ref in evidence_refs:
            _pointer(ref, 'goEvidenceRef')
    if from_status == 'RESPONSE_SUBMITTED' and to_status == 'ACCEPTED':
        raise AgentJobValidationError('RESPONSE_SUBMISSION_CANNOT_SKIP_VERIFICATION')

_SETTLED_AGENT_RUNTIME_STATUSES = {'RESULT_SUBMITTED', 'BLOCKED'}
_SETTLED_MASTER_JOB_STATUSES = {'REJECTED', 'ACCEPTED', 'INTEGRATED', 'CANCELED', 'SUPERSEDED'}
_BLOCKED_REARM_MASTER_STATUSES = {'REJECTED', 'CANCELED', 'SUPERSEDED'}
_BLOCKING_RESPONSE_TYPES = {'JOB_ERROR', 'CLARIFICATION_REQUEST', 'CAPABILITY_MISMATCH'}


def validate_agent_state_rearm_transition(*, current_state: Mapping[str, Any], proposed_state: Mapping[str, Any], prior_master_job_state: Mapping[str, Any], prior_response: Mapping[str, Any] | None = None) -> None:
    """Validate agent-owned rearm after a terminal prior execution."""
    current = _mapping(current_state, 'currentState')
    proposed = _mapping(proposed_state, 'proposedState')
    master = _mapping(prior_master_job_state, 'priorMasterJobState')
    status = current.get('runtimeStatus')
    if status not in _SETTLED_AGENT_RUNTIME_STATUSES:
        raise AgentJobValidationError('REARM_CURRENT_AGENT_STATUS_NOT_SETTLED')
    for field in ('format', 'schemaVersion', 'projectId', 'agentId', 'identityRevision'):
        if proposed.get(field) != current.get(field):
            raise AgentJobValidationError(f'REARM_MUST_PRESERVE_{field.upper()}')
    if current.get('format') != 'SAFOR_AGENT_STATE' or current.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('REARM_CURRENT_STATE_FORMAT_INVALID')
    if proposed.get('runtimeStatus') != 'WAITING_HUMAN_GO':
        raise AgentJobValidationError('REARM_PROPOSED_STATUS_INVALID')
    if not isinstance(current.get('revision'), int) or proposed.get('revision') != current.get('revision') + 1:
        raise AgentJobValidationError('REARM_STATE_REVISION_MUST_INCREMENT_ONCE')
    if proposed.get('session') is not None or proposed.get('currentJob') is not None:
        raise AgentJobValidationError('REARM_MUST_CLEAR_SESSION_AND_CURRENT_JOB')
    if proposed.get('lastResponseRef') != current.get('lastResponseRef') or not current.get('lastResponseRef'):
        raise AgentJobValidationError('REARM_MUST_PRESERVE_LAST_RESPONSE')
    if proposed.get('consumedActivationIds') != current.get('consumedActivationIds'):
        raise AgentJobValidationError('REARM_MUST_PRESERVE_CONSUMED_ACTIVATIONS')
    _nonempty(proposed.get('updatedAt'), 'REARM_UPDATED_AT_REQUIRED')

    current_job = _mapping(current.get('currentJob'), 'currentJob')
    job_id = _nonempty(current_job.get('jobId'), 'REARM_PRIOR_JOB_ID_REQUIRED')
    if master.get('format') != 'SAFOR_AGENT_JOB_STATE' or master.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('REARM_MASTER_JOB_STATE_FORMAT_INVALID')
    if master.get('projectId') != current.get('projectId') or master.get('jobId') != job_id:
        raise AgentJobValidationError('REARM_MASTER_JOB_BINDING_MISMATCH')
    if master.get('assignedAgentId') != current.get('agentId') or master.get('assignedIdentityRevision') != current.get('identityRevision'):
        raise AgentJobValidationError('REARM_MASTER_AGENT_BINDING_MISMATCH')
    master_status = master.get('lifecycleStatus')
    if master_status not in _SETTLED_MASTER_JOB_STATUSES:
        raise AgentJobValidationError('REARM_PRIOR_MASTER_JOB_NOT_TERMINALLY_SETTLED')

    if status == 'BLOCKED':
        if master_status not in _BLOCKED_REARM_MASTER_STATUSES:
            raise AgentJobValidationError('BLOCKED_REARM_MASTER_STATUS_INVALID')
        response = _mapping(prior_response, 'priorResponse')
        if response.get('format') != 'SAFOR_AGENT_RESPONSE' or response.get('schemaVersion') != '0.14.0':
            raise AgentJobValidationError('BLOCKED_REARM_RESPONSE_FORMAT_INVALID')
        if response.get('responseType') not in _BLOCKING_RESPONSE_TYPES:
            raise AgentJobValidationError('BLOCKED_REARM_TYPED_BLOCKING_RESPONSE_REQUIRED')
        for field, expected in (
            ('projectId', current.get('projectId')),
            ('jobId', job_id),
            ('agentId', current.get('agentId')),
            ('identityRevision', current.get('identityRevision')),
        ):
            if response.get(field) != expected:
                raise AgentJobValidationError(f'BLOCKED_REARM_RESPONSE_{field.upper()}_MISMATCH')
        if response.get('immutable') is not True:
            raise AgentJobValidationError('BLOCKED_REARM_RESPONSE_MUST_BE_IMMUTABLE')
        response_refs = master.get('responseRefs')
        if not isinstance(response_refs, list) or not response_refs:
            raise AgentJobValidationError('BLOCKED_REARM_MASTER_RESPONSE_REF_REQUIRED')

def validate_initialization_acknowledgement(*, pinned_identity: Mapping[str, Any], chat_output: Mapping[str, Any]) -> None:
    pinned = _mapping(pinned_identity, 'pinnedIdentity')
    output = _mapping(chat_output, 'chatOutput')
    if pinned.get('format') != 'SAFOR_AGENT_IDENTITY':
        raise AgentJobValidationError('PINNED_IDENTITY_FORMAT_INVALID')
    if output.get('format') != 'SAFOR_AGENT_CHAT_OUTPUT':
        raise AgentJobValidationError('CHAT_OUTPUT_FORMAT_INVALID')
    if output.get('status') == 'REIDENTIFICATION_REQUIRED':
        return
    if output.get('status') != 'READY':
        raise AgentJobValidationError('INITIALIZATION_ACK_MUST_BE_READY_OR_REIDENTIFICATION_REQUIRED')
    if output.get('projectId') != pinned.get('projectId'):
        raise AgentJobValidationError('INITIALIZATION_PROJECT_ID_MISMATCH')
    if output.get('agentId') != pinned.get('agentId'):
        raise AgentJobValidationError('INITIALIZATION_AGENT_ID_MISMATCH')
    if output.get('displayName') != pinned.get('displayName'):
        raise AgentJobValidationError('INITIALIZATION_DISPLAY_NAME_MISMATCH')
    if output.get('identityRevision') != pinned.get('identityRevision'):
        raise AgentJobValidationError('INITIALIZATION_IDENTITY_REVISION_MISMATCH')

def validate_reidentification_ready_transition(*, current_state: Mapping[str, Any], proposed_state: Mapping[str, Any], pinned_identity: Mapping[str, Any], evidence: Mapping[str, Any]) -> None:
    current = _mapping(current_state, 'currentState')
    proposed = _mapping(proposed_state, 'proposedState')
    identity = _mapping(pinned_identity, 'pinnedIdentity')
    proof = _mapping(evidence, 'reidentificationEvidence')

    if identity.get('format') != 'SAFOR_AGENT_IDENTITY':
        raise AgentJobValidationError('PINNED_IDENTITY_FORMAT_INVALID')
    if identity.get('status') != 'ACTIVE':
        raise AgentJobValidationError('REIDENTIFICATION_IDENTITY_NOT_ACTIVE')
    if proof.get('format') != 'SAFOR_AGENT_REIDENTIFICATION_EVIDENCE':
        raise AgentJobValidationError('REIDENTIFICATION_EVIDENCE_FORMAT_INVALID')
    if proof.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('REIDENTIFICATION_EVIDENCE_SCHEMA_VERSION_INVALID')
    if proof.get('source') != 'HUMAN_REPORTED_AGENT_REPLY_IN_MASTER_CHAT':
        raise AgentJobValidationError('REIDENTIFICATION_EVIDENCE_SOURCE_INVALID')
    if proof.get('result') != 'PASS' or proof.get('validForRearm') is not True or proof.get('immutable') is not True:
        raise AgentJobValidationError('REIDENTIFICATION_EVIDENCE_NOT_REARMABLE')
    if proof.get('initializationStateMutationObserved') is not False:
        raise AgentJobValidationError('REIDENTIFICATION_INITIALIZATION_STATE_MUTATION_FORBIDDEN')

    expected_reply = (
        f"Agent {identity.get('displayName')} ({identity.get('agentId')}) "
        "bereit | Status: WAITING_HUMAN_GO"
    )
    if proof.get('expectedAgentReply') != expected_reply or proof.get('observedAgentReply') != expected_reply:
        raise AgentJobValidationError('REIDENTIFICATION_READY_REPLY_MISMATCH')

    for field in ('projectId', 'agentId', 'identityRevision'):
        expected = identity.get(field)
        if current.get(field) != expected:
            raise AgentJobValidationError(f'REIDENTIFICATION_CURRENT_STATE_{field.upper()}_MISMATCH')
        if proposed.get(field) != expected:
            raise AgentJobValidationError(f'REIDENTIFICATION_PROPOSED_STATE_{field.upper()}_MISMATCH')
        if proof.get(field) != expected:
            raise AgentJobValidationError(f'REIDENTIFICATION_EVIDENCE_{field.upper()}_MISMATCH')

    if current.get('format') != 'SAFOR_AGENT_STATE' or current.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('REIDENTIFICATION_CURRENT_STATE_FORMAT_INVALID')
    if proposed.get('format') != 'SAFOR_AGENT_STATE' or proposed.get('schemaVersion') != '0.14.0':
        raise AgentJobValidationError('REIDENTIFICATION_PROPOSED_STATE_FORMAT_INVALID')
    if current.get('runtimeStatus') != 'REIDENTIFICATION_REQUIRED':
        raise AgentJobValidationError('REIDENTIFICATION_CURRENT_STATE_STATUS_INVALID')
    if proposed.get('runtimeStatus') != 'WAITING_HUMAN_GO':
        raise AgentJobValidationError('REIDENTIFICATION_PROPOSED_STATE_STATUS_INVALID')
    if not isinstance(current.get('revision'), int) or proposed.get('revision') != current.get('revision') + 1:
        raise AgentJobValidationError('REIDENTIFICATION_STATE_REVISION_MUST_INCREMENT_ONCE')
    if proposed.get('session') is not None or proposed.get('currentJob') is not None:
        raise AgentJobValidationError('REIDENTIFICATION_REARM_MUST_CLEAR_SESSION_AND_CURRENT_JOB')
    if proposed.get('lastResponseRef') != current.get('lastResponseRef'):
        raise AgentJobValidationError('REIDENTIFICATION_REARM_MUST_PRESERVE_LAST_RESPONSE')
    if proposed.get('consumedActivationIds') != current.get('consumedActivationIds'):
        raise AgentJobValidationError('REIDENTIFICATION_REARM_MUST_PRESERVE_CONSUMED_ACTIVATIONS')
    _nonempty(proposed.get('updatedAt'), 'REIDENTIFICATION_REARM_UPDATED_AT_REQUIRED')

    state_at_bootstrap = _mapping(proof.get('stateAtBootstrap'), 'stateAtBootstrap')
    _pointer(state_at_bootstrap.get('ref'), 'stateAtBootstrapRef')
    if state_at_bootstrap.get('revision') != current.get('revision'):
        raise AgentJobValidationError('REIDENTIFICATION_BOOTSTRAP_STATE_REVISION_MISMATCH')
    if state_at_bootstrap.get('runtimeStatus') != 'REIDENTIFICATION_REQUIRED':
        raise AgentJobValidationError('REIDENTIFICATION_BOOTSTRAP_STATE_STATUS_INVALID')

    inbox_at_bootstrap = _mapping(proof.get('inboxAtBootstrap'), 'inboxAtBootstrap')
    _pointer(inbox_at_bootstrap.get('ref'), 'inboxAtBootstrapRef')
    if not isinstance(inbox_at_bootstrap.get('revision'), int) or inbox_at_bootstrap.get('revision') < 1:
        raise AgentJobValidationError('REIDENTIFICATION_BOOTSTRAP_INBOX_REVISION_INVALID')
    if not isinstance(inbox_at_bootstrap.get('entryCount'), int) or inbox_at_bootstrap.get('entryCount') < 0:
        raise AgentJobValidationError('REIDENTIFICATION_BOOTSTRAP_INBOX_ENTRY_COUNT_INVALID')


def render_agent_chat_output(*, status: str, project_id: str, agent_id: str, display_name: str, identity_revision: int=1, job_key: str | None=None, target_branch: str | None=None, details_ref: str | None=None, persistence_state: str | None=None, attempt_id: str | None=None, phase: str | None=None, reason_code: str | None=None) -> dict[str, Any]:
    persistence_context_supplied = any(
        value is not None
        for value in (persistence_state, attempt_id, phase, reason_code)
    )
    if status != 'BLOCKED' and persistence_context_supplied:
        raise AgentJobValidationError('PERSISTENCE_FAILURE_CONTEXT_ONLY_ALLOWED_FOR_BLOCKED')
    if status == 'BLOCKED' and details_ref and persistence_context_supplied:
        raise AgentJobValidationError('BLOCKED_DETAILS_REF_AND_PERSISTENCE_FAILURE_ARE_MUTUALLY_EXCLUSIVE')
    if status == 'READY':
        text = f'Agent {display_name} ({agent_id}) bereit | Status: WAITING_HUMAN_GO'
        terminal = False
    elif status == 'STARTED':
        if not job_key or not target_branch:
            raise AgentJobValidationError('STARTED_REQUIRES_JOB_AND_TARGET_BRANCH')
        text = f'GO bestätigt | Agent: {display_name} ({agent_id}) | Job: {job_key} | Status: RUNNING | Zielbranch: {target_branch}'
        terminal = False
    elif status == 'SUBMITTED':
        if not job_key or not details_ref:
            raise AgentJobValidationError('SUBMITTED_REQUIRES_JOB_AND_DETAILS_REF')
        text = f'Job {job_key} abgeschlossen | Status: SUBMITTED | Ergebnis: {details_ref}'
        terminal = True
    elif status == 'BLOCKED':
        if not job_key:
            raise AgentJobValidationError('BLOCKED_REQUIRES_JOB')
        if details_ref:
            text = f'Job {job_key} blockiert | Status: BLOCKED | Meldung: {details_ref} | MASTER-Klärung erforderlich'
            persistence = None
        else:
            if persistence_state != 'FAILED' or not attempt_id or not phase or not reason_code:
                raise AgentJobValidationError('BLOCKED_WITHOUT_DETAILS_REQUIRES_PERSISTENCE_FAILURE_CONTEXT')
            text = f'Job {job_key} blockiert | Status: BLOCKED | Rückmeldung nicht gespeichert | MASTER-Klärung erforderlich'
            persistence = {'state': 'FAILED', 'target': 'CONTROL_REPOSITORY', 'reasonCode': reason_code, 'authoritativeResponsePersisted': False, 'attemptId': attempt_id, 'phase': phase}
        terminal = True
    elif status == 'REIDENTIFICATION_REQUIRED':
        text = 'Agentenidentität unsicher | Status: REIDENTIFICATION_REQUIRED | Bitte im MASTER-Chat neue Initialisierung anfordern'
        terminal = True
    else:
        raise AgentJobValidationError('CHAT_STATUS_FORBIDDEN')
    if status != 'BLOCKED' or details_ref:
        persistence = None
    if '\n' in text or '\r' in text:
        raise AgentJobValidationError('CHAT_OUTPUT_MUST_BE_ONE_LINE')
    if len(text.split()) > 36:
        raise AgentJobValidationError('CHAT_OUTPUT_WORD_BUDGET_EXCEEDED')
    if len(text) > 360:
        raise AgentJobValidationError('CHAT_OUTPUT_CHARACTER_BUDGET_EXCEEDED')
    return {'format': 'SAFOR_AGENT_CHAT_OUTPUT', 'schemaVersion': '0.14.0', 'status': status, 'projectId': project_id, 'agentId': agent_id, 'displayName': display_name, 'identityRevision': identity_revision, 'jobKey': job_key, 'targetBranch': target_branch, 'detailsRef': details_ref, 'persistence': persistence, 'text': text, 'terminal': terminal, 'containsDomainDetail': False}
