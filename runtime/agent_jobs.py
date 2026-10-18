from __future__ import annotations
import re
from typing import Any, Mapping

class AgentJobValidationError(ValueError):
    """Raised when a v0.14 agent job or chat status is unsafe."""
_REQUIRED_RESPONSE_TYPES = {'JOB_RESULT', 'JOB_ERROR', 'CLARIFICATION_REQUEST', 'CAPABILITY_MISMATCH', 'IMPROVEMENT_PROPOSAL'}
_TEMPLATE_PATHS = {'JOB_RESULT': 'v0.14.0/templates/responses/job-result.template.json', 'JOB_ERROR': 'v0.14.0/templates/responses/job-error.template.json', 'CLARIFICATION_REQUEST': 'v0.14.0/templates/responses/clarification-request.template.json', 'CAPABILITY_MISMATCH': 'v0.14.0/templates/responses/capability-mismatch.template.json', 'IMPROVEMENT_PROPOSAL': 'v0.14.0/templates/responses/improvement-proposal.template.json'}
_UUIDV7 = re.compile('^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
_TRANSITIONS = {'PREPARED': {'WAITING_HUMAN_GO', 'CANCELED', 'SUPERSEDED'}, 'WAITING_HUMAN_GO': {'GO_OBSERVED', 'CANCELED', 'SUPERSEDED'}, 'GO_OBSERVED': {'CLAIMED', 'BLOCKED', 'CANCELED'}, 'CLAIMED': {'RUNNING', 'BLOCKED', 'CANCELED'}, 'RUNNING': {'RESPONSE_SUBMITTED', 'BLOCKED', 'CANCELED'}, 'RESPONSE_SUBMITTED': {'VERIFIED', 'REJECTED', 'BLOCKED'}, 'VERIFIED': {'ACCEPTED', 'REJECTED'}, 'ACCEPTED': {'INTEGRATED'}, 'REJECTED': {'REWORK_READY', 'CANCELED'}, 'REWORK_READY': {'WAITING_HUMAN_GO', 'SUPERSEDED', 'CANCELED'}}

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
        response_repositories.add((target['repository'], target['branch']))
        if binding.get('required') is not True:
            raise AgentJobValidationError(f'RESPONSE_CONTRACT_MUST_BE_REQUIRED:{response_type}')
    if len(response_repositories) != 1:
        raise AgentJobValidationError('ALL_RESPONSE_TYPES_MUST_SHARE_CONTROL_TARGET')
    index_target = _write_target(responses.get('responseIndexTarget'), 'responseIndexTarget')
    if (index_target['repository'], index_target['branch']) not in response_repositories:
        raise AgentJobValidationError('RESPONSE_INDEX_TARGET_MISMATCH')
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

def validate_job_state_transition(*, from_status: str, to_status: str, evidence_refs: list[str]) -> None:
    allowed = _TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        raise AgentJobValidationError(f'JOB_STATE_TRANSITION_FORBIDDEN:{from_status}->{to_status}')
    if from_status == 'WAITING_HUMAN_GO' and to_status == 'GO_OBSERVED' and (not any(('go' in ref.casefold() for ref in evidence_refs))):
        raise AgentJobValidationError('GO_EVIDENCE_REQUIRED')
    if from_status == 'RESPONSE_SUBMITTED' and to_status == 'ACCEPTED':
        raise AgentJobValidationError('RESPONSE_SUBMISSION_CANNOT_SKIP_VERIFICATION')

def render_agent_chat_output(*, status: str, project_id: str, agent_id: str, display_name: str, job_key: str | None=None, target_branch: str | None=None, details_ref: str | None=None) -> dict[str, Any]:
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
        if not job_key or not details_ref:
            raise AgentJobValidationError('BLOCKED_REQUIRES_JOB_AND_DETAILS_REF')
        text = f'Job {job_key} blockiert | Status: BLOCKED | Meldung: {details_ref} | MASTER-Klärung erforderlich'
        terminal = True
    elif status == 'REIDENTIFICATION_REQUIRED':
        text = 'Agentenidentität unsicher | Status: REIDENTIFICATION_REQUIRED | Bitte im MASTER-Chat neue Initialisierung anfordern'
        terminal = True
    else:
        raise AgentJobValidationError('CHAT_STATUS_FORBIDDEN')
    if '\n' in text or '\r' in text:
        raise AgentJobValidationError('CHAT_OUTPUT_MUST_BE_ONE_LINE')
    if len(text.split()) > 36:
        raise AgentJobValidationError('CHAT_OUTPUT_WORD_BUDGET_EXCEEDED')
    if len(text) > 360:
        raise AgentJobValidationError('CHAT_OUTPUT_CHARACTER_BUDGET_EXCEEDED')
    return {'format': 'SAFOR_AGENT_CHAT_OUTPUT', 'schemaVersion': '0.14.0', 'status': status, 'projectId': project_id, 'agentId': agent_id, 'displayName': display_name, 'jobKey': job_key, 'targetBranch': target_branch, 'detailsRef': details_ref, 'text': text, 'terminal': terminal, 'containsDomainDetail': False}
