import copy
import json
import unittest
from pathlib import Path
from runtime.migration import MigrationValidationError, build_artifact_dispositions, canonical_repository_name, classify_legacy_artifact, legacy_artifact_can_claim, validate_migration_manifest
ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

class MigrationV014Tests(unittest.TestCase):

    def pointer(self, path, repository='empishaj/safor-memory'):
        return {'repository': repository, 'ref': 'commit123', 'path': path, 'blobSha': 'blob1234'}

    def inventory(self):
        return [{'artifactId': 'legacy-master-v3', 'aggregateKey': 'CONTROL_STATE', 'sourceRef': self.pointer('projects/example/master/v3/state.json', 'empishaj/saf-memory'), 'sourceFormat': 'SAF_MASTER_STATE', 'sourceSchemaVersion': '0.3.0', 'selectedActive': False}, {'artifactId': 'legacy-agent-identity', 'aggregateKey': 'AGENT_IDENTITY:agent-a', 'sourceRef': self.pointer('projects/example/agents/agent-a/identity.json', 'empishaj/saf-memory'), 'sourceFormat': 'SAF_AGENT_IDENTITY', 'sourceSchemaVersion': '1.0.1', 'selectedActive': False}, {'artifactId': 'canonical-job-v010', 'aggregateKey': 'MASTER_JOB_STATE:job-old', 'sourceRef': self.pointer('projects/example/master/jobs/job-old.json'), 'sourceFormat': 'SAFOR_AGENT_JOB_STATE', 'sourceSchemaVersion': '0.10.0', 'selectedActive': False}, {'artifactId': 'active-control-v014', 'aggregateKey': 'CONTROL_STATE_V014', 'sourceRef': self.pointer('projects/example/state/control-v0.14.json'), 'sourceFormat': 'SAFOR_CONTROL_STATE', 'sourceSchemaVersion': '0.14.0', 'selectedActive': True, 'claimable': False, 'dispatchEnabled': False, 'mutable': True}]

    def manifest(self):
        canonical = 'empishaj/safor-memory'
        active_control = self.pointer('projects/example/state/control-v0.14.json', canonical)
        active_identity = self.pointer('projects/example/agents/agent-a/identity-v0.14.json', canonical)
        targets = {'CONTROL_STATE': active_control, 'AGENT_IDENTITY:agent-a': active_identity, 'MASTER_JOB_STATE:job-old': self.pointer('projects/example/master/jobs/job-old-v0.14.json', canonical), 'CONTROL_STATE_V014': active_control}
        dispositions = build_artifact_dispositions(inventory=self.inventory(), active_target_by_aggregate=targets)
        return {'format': 'SAFOR_MIGRATION_MANIFEST', 'schemaVersion': '0.14.0', 'migrationId': 'migration-example-v014', 'projectId': 'project-001', 'projectSlug': 'example', 'fromVersions': ['0.3.0', '0.10.0', '1.0.1'], 'toVersion': '0.14.0', 'canonicalControlRepository': {'provider': 'github', 'stableId': '1418924301', 'repository': canonical, 'branch': 'main'}, 'repositoryAliases': [{'alias': 'empishaj/saf-memory', 'canonical': canonical, 'verificationRef': self.pointer('evidence/repository-alias-readback.json', canonical)}], 'sourceInventoryRefs': [self.pointer('migration/source-inventory.json', canonical)], 'artifactDispositions': dispositions, 'activeAuthorities': [{'aggregateKey': 'CONTROL_STATE', 'artifactRef': active_control, 'exclusive': True, 'legacySourceRefs': [self.pointer('projects/example/master/v3/state.json', 'empishaj/saf-memory')]}, {'aggregateKey': 'AGENT_REGISTRY', 'artifactRef': self.pointer('projects/example/agents/index-v0.14.json', canonical), 'exclusive': True, 'legacySourceRefs': []}, {'aggregateKey': 'AGENT_IDENTITY:agent-a', 'artifactRef': active_identity, 'exclusive': True, 'legacySourceRefs': [self.pointer('projects/example/agents/agent-a/identity.json', 'empishaj/saf-memory')]}], 'agentMigrations': [{'agentId': 'agent-a', 'displayName': 'Nova Dev', 'legacyIdentityRefs': [self.pointer('projects/example/agents/agent-a/identity.json', 'empishaj/saf-memory')], 'activeIdentityRef': active_identity, 'registryDisposition': 'MIGRATED_ACTIVE', 'chatBindingStatus': 'UNVERIFIED', 'legacyDispatchDisabled': True}], 'createdAt': '2026-10-17T22:00:00Z', 'createdBy': 'SAFOR-MASTER:project-001', 'evidenceRefs': [self.pointer('projects/example/evidence/migration-v014.json', canonical)], 'providerReadbackRefs': ['github:empishaj/safor-memory@commit456'], 'historyPreserved': True, 'sourceArtifactsMutated': False, 'sourceArtifactsDeleted': False, 'status': 'VERIFIED'}

    def test_wp05_json_files_parse(self):
        for path in ('v0.14.0/migration-model.json', 'v0.14.0/legacy-artifact-policy.json', 'v0.14.0/schemas/migration-manifest.schema.json'):
            with self.subTest(path=path):
                doc = load(path)
                if '/schemas/' in path:
                    self.assertEqual(doc['properties']['schemaVersion']['const'], '0.14.0')
                else:
                    self.assertEqual(doc['schemaVersion'], '0.14.0')

    def test_known_legacy_formats_are_classified_read_only(self):
        inventory = self.inventory()
        self.assertEqual(classify_legacy_artifact(inventory[0]), 'LEGACY_SNAPSHOT')
        self.assertEqual(classify_legacy_artifact(inventory[1]), 'LEGACY_SNAPSHOT')
        self.assertEqual(classify_legacy_artifact(inventory[2]), 'SUPERSEDED')
        self.assertEqual(classify_legacy_artifact(inventory[3]), 'ACTIVE')

    def test_repository_alias_resolves_to_canonical_name(self):
        self.assertEqual(canonical_repository_name('empishaj/saf-memory', {'empishaj/saf-memory': 'empishaj/safor-memory'}), 'empishaj/safor-memory')

    def test_repository_alias_cycle_fails_closed(self):
        with self.assertRaisesRegex(MigrationValidationError, 'REPOSITORY_ALIAS_CYCLE'):
            canonical_repository_name('a', {'a': 'b', 'b': 'a'})

    def test_valid_manifest_preserves_all_inventory(self):
        manifest = self.manifest()
        validate_migration_manifest(manifest, expected_inventory_ids={artifact['artifactId'] for artifact in self.inventory()})
        self.assertTrue(all((disposition['preserved'] for disposition in manifest['artifactDispositions'])))

    def test_inventory_coverage_must_be_exact(self):
        manifest = self.manifest()
        manifest['artifactDispositions'].pop()
        with self.assertRaisesRegex(MigrationValidationError, 'INVENTORY_COVERAGE_MISMATCH'):
            validate_migration_manifest(manifest, expected_inventory_ids={artifact['artifactId'] for artifact in self.inventory()})

    def test_legacy_artifact_can_never_claim_or_dispatch(self):
        manifest = self.manifest()
        legacy = next((item for item in manifest['artifactDispositions'] if item['disposition'] == 'LEGACY_SNAPSHOT'))
        self.assertFalse(legacy_artifact_can_claim(legacy))
        legacy['claimable'] = True
        with self.assertRaisesRegex(MigrationValidationError, 'LEGACY_ARTIFACT_CLAIM_FORBIDDEN'):
            validate_migration_manifest(manifest)

    def test_history_deletion_or_mutation_is_forbidden(self):
        for field, message in (('sourceArtifactsDeleted', 'SOURCE_ARTIFACT_DELETION_FORBIDDEN'), ('sourceArtifactsMutated', 'SOURCE_ARTIFACT_MUTATION_FORBIDDEN')):
            with self.subTest(field=field):
                manifest = self.manifest()
                manifest[field] = True
                with self.assertRaisesRegex(MigrationValidationError, message):
                    validate_migration_manifest(manifest)

    def test_dual_active_authority_is_rejected(self):
        manifest = self.manifest()
        manifest['activeAuthorities'].append(copy.deepcopy(manifest['activeAuthorities'][0]))
        with self.assertRaisesRegex(MigrationValidationError, 'EXACTLY_ONE_ACTIVE_AUTHORITY_REQUIRED'):
            validate_migration_manifest(manifest)

    def test_active_target_must_use_canonical_repository(self):
        manifest = self.manifest()
        manifest['activeAuthorities'][0]['artifactRef']['repository'] = 'other/control'
        with self.assertRaisesRegex(MigrationValidationError, 'ACTIVE_AUTHORITY_MUST_USE_CANONICAL_CONTROL_REPOSITORY'):
            validate_migration_manifest(manifest)

    def test_all_agents_need_distinct_display_name_and_disabled_legacy_dispatch(self):
        manifest = self.manifest()
        manifest['agentMigrations'][0]['displayName'] = 'agent-a'
        with self.assertRaisesRegex(MigrationValidationError, 'MIGRATED_DISPLAY_NAME_MUST_DIFFER_FROM_AGENT_ID'):
            validate_migration_manifest(manifest)
        manifest = self.manifest()
        manifest['agentMigrations'][0]['legacyDispatchDisabled'] = False
        with self.assertRaisesRegex(MigrationValidationError, 'LEGACY_AGENT_DISPATCH_MUST_BE_DISABLED'):
            validate_migration_manifest(manifest)

    def test_provider_readback_and_evidence_are_required(self):
        manifest = self.manifest()
        manifest['providerReadbackRefs'] = []
        with self.assertRaisesRegex(MigrationValidationError, 'PROVIDER_READBACK_REQUIRED'):
            validate_migration_manifest(manifest)
        manifest = self.manifest()
        manifest['evidenceRefs'] = []
        with self.assertRaisesRegex(MigrationValidationError, 'MIGRATION_EVIDENCE_REQUIRED'):
            validate_migration_manifest(manifest)
if __name__ == '__main__':
    unittest.main()
