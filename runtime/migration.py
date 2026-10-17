from __future__ import annotations
from collections import Counter
from copy import deepcopy
from typing import Any, Mapping, Sequence

class MigrationValidationError(ValueError):
    """Raised when a SAFOR migration would lose history or create dual authority."""
_ACTIVE_DISPOSITIONS = {'ACTIVE', 'MIGRATED_ACTIVE'}
_LEGACY_DISPOSITIONS = {'LEGACY_SNAPSHOT', 'SUPERSEDED'}

def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MigrationValidationError(f'{name} must be a mapping')
    return value

def _pointer(value: Any, name: str) -> Mapping[str, Any]:
    pointer = _mapping(value, name)
    for field in ('repository', 'ref', 'path', 'blobSha'):
        if not str(pointer.get(field, '')).strip():
            raise MigrationValidationError(f'{name.upper()}_{field.upper()}_MISSING')
    return pointer

def canonical_repository_name(repository: str, aliases: Mapping[str, str]) -> str:
    """Resolve aliases for newly generated v0.14 pointers only."""
    current = str(repository).strip()
    seen: set[str] = set()
    while current in aliases:
        if current in seen:
            raise MigrationValidationError('REPOSITORY_ALIAS_CYCLE')
        seen.add(current)
        current = str(aliases[current]).strip()
    if not current:
        raise MigrationValidationError('CANONICAL_REPOSITORY_EMPTY')
    return current

def classify_legacy_artifact(artifact: Mapping[str, Any]) -> str:
    artifact = _mapping(artifact, 'artifact')
    source_format = str(artifact.get('sourceFormat', ''))
    source_version = str(artifact.get('sourceSchemaVersion', ''))
    selected_active = artifact.get('selectedActive') is True
    if source_version == '0.14.0':
        return 'ACTIVE' if selected_active else 'SUPERSEDED'
    if source_version == '0.10.0' and source_format.startswith('SAFOR_'):
        return 'SUPERSEDED'
    if source_format.startswith('SAF_') or source_format.startswith('AWC_'):
        return 'LEGACY_SNAPSHOT'
    if str(artifact.get('artifactId', '')).startswith('AWC-'):
        return 'LEGACY_SNAPSHOT'
    return 'LEGACY_SNAPSHOT'

def build_artifact_dispositions(*, inventory: Sequence[Mapping[str, Any]], active_target_by_aggregate: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Classify every immutable source artifact without rewriting it."""
    dispositions: list[dict[str, Any]] = []
    for raw in inventory:
        artifact = _mapping(raw, 'inventoryArtifact')
        aggregate = str(artifact.get('aggregateKey', '')).strip()
        artifact_id = str(artifact.get('artifactId', '')).strip()
        if not aggregate or not artifact_id:
            raise MigrationValidationError('INVENTORY_ARTIFACT_ID_OR_AGGREGATE_MISSING')
        source_ref = dict(_pointer(artifact.get('sourceRef'), 'sourceRef'))
        disposition = classify_legacy_artifact(artifact)
        target = active_target_by_aggregate.get(aggregate)
        if disposition == 'ACTIVE':
            target_ref = source_ref
            claimable = bool(artifact.get('claimable', False))
            dispatch_enabled = bool(artifact.get('dispatchEnabled', False))
            mutable = bool(artifact.get('mutable', False))
            reason = 'Already selected as the sole v0.14 authority.'
        else:
            target_ref = dict(target) if target else None
            claimable = False
            dispatch_enabled = False
            mutable = False
            reason = 'Historical artifact retained read-only and excluded from current claim, dispatch and mutable authority.'
        dispositions.append({'artifactId': artifact_id, 'aggregateKey': aggregate, 'sourceRef': source_ref, 'sourceFormat': str(artifact.get('sourceFormat', 'UNKNOWN')), 'sourceSchemaVersion': str(artifact.get('sourceSchemaVersion', 'UNKNOWN')), 'disposition': disposition, 'targetRef': target_ref, 'claimable': claimable, 'dispatchEnabled': dispatch_enabled, 'mutable': mutable, 'preserved': True, 'reason': reason})
    return dispositions

def validate_migration_manifest(manifest: Mapping[str, Any], *, expected_inventory_ids: set[str] | None=None) -> None:
    manifest = _mapping(manifest, 'manifest')
    if manifest.get('format') != 'SAFOR_MIGRATION_MANIFEST':
        raise MigrationValidationError('MIGRATION_FORMAT_INVALID')
    if manifest.get('schemaVersion') != '0.14.0':
        raise MigrationValidationError('MIGRATION_SCHEMA_VERSION_INVALID')
    if manifest.get('toVersion') != '0.14.0':
        raise MigrationValidationError('MIGRATION_TARGET_VERSION_INVALID')
    if manifest.get('historyPreserved') is not True:
        raise MigrationValidationError('MIGRATION_MUST_PRESERVE_HISTORY')
    if manifest.get('sourceArtifactsMutated') is not False:
        raise MigrationValidationError('SOURCE_ARTIFACT_MUTATION_FORBIDDEN')
    if manifest.get('sourceArtifactsDeleted') is not False:
        raise MigrationValidationError('SOURCE_ARTIFACT_DELETION_FORBIDDEN')
    canonical = _mapping(manifest.get('canonicalControlRepository'), 'canonicalControlRepository')
    canonical_name = str(canonical.get('repository', '')).strip()
    if not canonical_name.endswith('/safor-memory'):
        raise MigrationValidationError('CANONICAL_CONTROL_REPOSITORY_INVALID')
    aliases: dict[str, str] = {}
    for index, raw in enumerate(manifest.get('repositoryAliases') or []):
        alias = _mapping(raw, f'repositoryAlias[{index}]')
        _pointer(alias.get('verificationRef'), f'repositoryAliasRef[{index}]')
        alias_name = str(alias.get('alias', '')).strip()
        canonical_alias = str(alias.get('canonical', '')).strip()
        if not alias_name or not canonical_alias:
            raise MigrationValidationError('REPOSITORY_ALIAS_INVALID')
        aliases[alias_name] = canonical_alias
        if canonical_repository_name(alias_name, aliases) != canonical_alias:
            raise MigrationValidationError('REPOSITORY_ALIAS_NOT_CANONICAL')
        if canonical_alias != canonical_name:
            raise MigrationValidationError('REPOSITORY_ALIAS_TARGET_MUST_MATCH_CONTROL_REPOSITORY')
    dispositions = [_mapping(raw, 'artifactDisposition') for raw in manifest.get('artifactDispositions') or []]
    if not dispositions:
        raise MigrationValidationError('ARTIFACT_DISPOSITIONS_REQUIRED')
    ids = [str(item.get('artifactId', '')) for item in dispositions]
    if len(ids) != len(set(ids)):
        raise MigrationValidationError('DUPLICATE_ARTIFACT_DISPOSITION')
    if expected_inventory_ids is not None and set(ids) != expected_inventory_ids:
        missing = sorted(expected_inventory_ids - set(ids))
        extra = sorted(set(ids) - expected_inventory_ids)
        raise MigrationValidationError(f'INVENTORY_COVERAGE_MISMATCH:missing={missing},extra={extra}')
    for item in dispositions:
        _pointer(item.get('sourceRef'), 'sourceRef')
        if item.get('preserved') is not True:
            raise MigrationValidationError('EVERY_SOURCE_ARTIFACT_MUST_BE_PRESERVED')
        disposition = item.get('disposition')
        if disposition in _LEGACY_DISPOSITIONS:
            if item.get('claimable') is not False:
                raise MigrationValidationError('LEGACY_ARTIFACT_CLAIM_FORBIDDEN')
            if item.get('dispatchEnabled') is not False:
                raise MigrationValidationError('LEGACY_DISPATCH_FORBIDDEN')
            if item.get('mutable') is not False:
                raise MigrationValidationError('LEGACY_MUTATION_FORBIDDEN')
        target = item.get('targetRef')
        if target is not None:
            target = _pointer(target, 'targetRef')
            target_repo = canonical_repository_name(str(target['repository']), aliases)
            if target_repo != canonical_name:
                raise MigrationValidationError('ACTIVE_TARGET_MUST_USE_CANONICAL_CONTROL_REPOSITORY')
    authorities = [_mapping(raw, 'activeAuthority') for raw in manifest.get('activeAuthorities') or []]
    if not authorities:
        raise MigrationValidationError('ACTIVE_AUTHORITIES_REQUIRED')
    authority_counts = Counter((str(authority.get('aggregateKey', '')) for authority in authorities))
    duplicate = sorted((aggregate for aggregate, count in authority_counts.items() if count != 1))
    if duplicate:
        raise MigrationValidationError(f'EXACTLY_ONE_ACTIVE_AUTHORITY_REQUIRED:{duplicate}')
    for authority in authorities:
        if authority.get('exclusive') is not True:
            raise MigrationValidationError('ACTIVE_AUTHORITY_MUST_BE_EXCLUSIVE')
        artifact_ref = _pointer(authority.get('artifactRef'), 'artifactRef')
        if canonical_repository_name(str(artifact_ref['repository']), aliases) != canonical_name:
            raise MigrationValidationError('ACTIVE_AUTHORITY_MUST_USE_CANONICAL_CONTROL_REPOSITORY')
        for legacy_ref in authority.get('legacySourceRefs') or []:
            _pointer(legacy_ref, 'legacySourceRef')
    agents = [_mapping(raw, 'agentMigration') for raw in manifest.get('agentMigrations') or []]
    agent_ids = [str(agent.get('agentId', '')) for agent in agents]
    if len(agent_ids) != len(set(agent_ids)):
        raise MigrationValidationError('DUPLICATE_AGENT_MIGRATION')
    for agent in agents:
        if str(agent.get('displayName', '')).strip().casefold() == str(agent.get('agentId', '')).strip().casefold():
            raise MigrationValidationError('MIGRATED_DISPLAY_NAME_MUST_DIFFER_FROM_AGENT_ID')
        if agent.get('legacyDispatchDisabled') is not True:
            raise MigrationValidationError('LEGACY_AGENT_DISPATCH_MUST_BE_DISABLED')
        _pointer(agent.get('activeIdentityRef'), 'activeIdentityRef')
        for legacy_ref in agent.get('legacyIdentityRefs') or []:
            _pointer(legacy_ref, 'legacyIdentityRef')
    if not manifest.get('evidenceRefs'):
        raise MigrationValidationError('MIGRATION_EVIDENCE_REQUIRED')
    for evidence in manifest['evidenceRefs']:
        _pointer(evidence, 'evidenceRef')
    if not manifest.get('providerReadbackRefs'):
        raise MigrationValidationError('PROVIDER_READBACK_REQUIRED')

def legacy_artifact_can_claim(disposition: Mapping[str, Any]) -> bool:
    """Central negative guard used by migration and conformance tests."""
    disposition = _mapping(disposition, 'disposition')
    if disposition.get('disposition') in _LEGACY_DISPOSITIONS:
        return False
    return disposition.get('claimable') is True and disposition.get('dispatchEnabled') is True
