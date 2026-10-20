import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.release_provenance import (
    ReleaseProvenanceError,
    artifact_set_digest,
    canonical_artifact_paths,
    sha256_bytes,
    sha256_file,
    validate_release_evidence,
)


SOURCE_SHA = "1" * 40
TREE_SHA = "2" * 40
RUN_ID = "123456789"
RUN_ATTEMPT = "1"
INTEGRATION_REF = "safor/operational-readiness-0.14.0-rc.6"


class ReleaseProvenanceV014Tests(unittest.TestCase):
    def make_fixture(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)

        artifacts = []
        for name in canonical_artifact_paths("0.14.0-rc.6"):
            payload = (json.dumps({"artifact": name}, sort_keys=True) + "\n").encode(
                "utf-8"
            )
            (root / name).write_bytes(payload)
            artifacts.append(
                {
                    "path": name,
                    "sha256": sha256_bytes(payload),
                    "bytes": len(payload),
                    "generatedFromSourceCommit": SOURCE_SHA,
                }
            )

        checksum_path = root / "SHA256SUMS-0.14.0-rc.6.txt"
        checksum_path.write_text(
            "".join(f"{item['sha256']}  {item['path']}\n" for item in artifacts),
            encoding="utf-8",
        )

        set_digest = artifact_set_digest(artifacts)
        checksum_digest = sha256_file(checksum_path)
        evidence = {
            "format": "SAFOR_RELEASE_EVIDENCE",
            "schemaVersion": "0.14.0",
            "contractVersion": "1.0",
            "contractRef": "docs/releases/RELEASE-EVIDENCE-CONTRACT-v1.json",
            "product": "SAFOR",
            "version": "0.14.0-rc.6",
            "status": "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS",
            "createdAt": "2026-10-19T12:00:00Z",
            "provenance": {
                "repository": "empishaj/SAFOR",
                "sourceCommitSha": SOURCE_SHA,
                "sourceTreeSha": TREE_SHA,
                "workflowHeadSha": SOURCE_SHA,
                "workflowRunId": RUN_ID,
                "workflowRunAttempt": RUN_ATTEMPT,
                "integrationRef": INTEGRATION_REF,
                "exactHeadRequired": True,
            },
            "validatedCommands": ["tests"],
            "artifacts": artifacts,
            "artifactSetDigest": set_digest,
            "truthBoundary": ["exact source only"],
            "materializedAt": "2026-10-19T12:00:01Z",
            "artifactCount": len(artifacts),
            "checksumFile": checksum_path.name,
            "checksumFileSha256": checksum_digest,
            "validation": {
                "status": "PASS",
                "validationSourceCommitSha": SOURCE_SHA,
                "validationWorkflowHeadSha": SOURCE_SHA,
                "validationWorkflowRunId": RUN_ID,
                "validatedArtifactSetDigest": set_digest,
                "validatedChecksumFileSha256": checksum_digest,
                "validatedAt": "2026-10-19T12:05:00Z",
            },
        }
        return temp, root, evidence

    def validate(self, root, evidence, **kwargs):
        validate_release_evidence(
            root=root,
            evidence=evidence,
            expected_version="0.14.0-rc.6",
            expected_source_sha=kwargs.get("expected_source_sha", SOURCE_SHA),
            expected_source_tree_sha=kwargs.get("expected_source_tree_sha", TREE_SHA),
            expected_workflow_run_id=kwargs.get("expected_workflow_run_id", RUN_ID),
            expected_workflow_run_attempt=kwargs.get(
                "expected_workflow_run_attempt", RUN_ATTEMPT
            ),
            expected_integration_ref=kwargs.get(
                "expected_integration_ref", INTEGRATION_REF
            ),
            require_pass=kwargs.get("require_pass", True),
        )

    def test_exact_release_evidence_passes(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        self.validate(root, evidence)

    def test_stale_source_commit_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_EXPECTED_SOURCE_SHA_MISMATCH"
        ):
            self.validate(root, evidence, expected_source_sha="3" * 40)

    def test_source_tree_mismatch_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_EXPECTED_SOURCE_TREE_MISMATCH"
        ):
            self.validate(root, evidence, expected_source_tree_sha="3" * 40)

    def test_workflow_run_attempt_must_be_positive_integer(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["provenance"]["workflowRunAttempt"] = "0"
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_WORKFLOW_RUN_ATTEMPT_INVALID"
        ):
            self.validate(root, evidence)

    def test_workflow_run_attempt_mismatch_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_EXPECTED_WORKFLOW_RUN_ATTEMPT_MISMATCH"
        ):
            self.validate(root, evidence, expected_workflow_run_attempt="2")

    def test_integration_ref_mismatch_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_EXPECTED_INTEGRATION_REF_MISMATCH"
        ):
            self.validate(root, evidence, expected_integration_ref="main")

    def test_workflow_head_source_drift_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["provenance"]["workflowHeadSha"] = "4" * 40
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_WORKFLOW_HEAD_SOURCE_DRIFT"
        ):
            self.validate(root, evidence)

    def test_old_workflow_run_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_EXPECTED_WORKFLOW_RUN_MISMATCH"
        ):
            self.validate(root, evidence, expected_workflow_run_id="987654321")

    def test_artifact_content_drift_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        path = root / "SAFOR-FRAMEWORK.json"
        original = path.read_bytes()
        replacement_tail = b"X" if original[-1:] != b"X" else b"Y"
        path.write_bytes(original[:-1] + replacement_tail)
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_DIGEST_DRIFT"
        ):
            self.validate(root, evidence)

    def test_artifact_hash_rewrite_without_set_digest_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        new_payload = b'{"a":2}\n'
        path = root / "SAFOR-FRAMEWORK.json"
        path.write_bytes(new_payload)
        evidence["artifacts"][0]["sha256"] = sha256_bytes(new_payload)
        evidence["artifacts"][0]["bytes"] = len(new_payload)

        checksum = root / evidence["checksumFile"]
        checksum.write_text(
            "".join(
                f"{item['sha256']}  {item['path']}\n"
                for item in evidence["artifacts"]
            ),
            encoding="utf-8",
        )
        evidence["checksumFileSha256"] = sha256_file(checksum)
        evidence["validation"]["validatedChecksumFileSha256"] = evidence[
            "checksumFileSha256"
        ]

        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_SET_DIGEST_DRIFT"
        ):
            self.validate(root, evidence)

    def test_release_artifact_path_set_must_be_canonical(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["artifacts"][0]["path"] = "README.md"
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_PATH_SET_INVALID"
        ):
            self.validate(root, evidence)

    def test_parent_traversal_artifact_path_fails_closed(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["artifacts"][0]["path"] = "../SAFOR-FRAMEWORK.json"
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_PATH_SET_INVALID"
        ):
            self.validate(root, evidence)

    def test_absolute_artifact_path_fails_closed(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["artifacts"][0]["path"] = str(
            (root / "SAFOR-FRAMEWORK.json").resolve()
        )
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_PATH_SET_INVALID"
        ):
            self.validate(root, evidence)

    def test_symlinked_canonical_artifact_is_forbidden(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        external = tempfile.TemporaryDirectory()
        self.addCleanup(external.cleanup)

        name = "SAFOR-FRAMEWORK.json"
        original = root / name
        payload = original.read_bytes()
        external_file = Path(external.name) / name
        external_file.write_bytes(payload)
        original.unlink()
        original.symlink_to(external_file)

        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_ARTIFACT_SYMLINK_FORBIDDEN"
        ):
            self.validate(root, evidence)

    def test_checksum_file_name_must_be_canonical(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)

        original = root / evidence["checksumFile"]
        alternate = root / "checksums.txt"
        alternate.write_bytes(original.read_bytes())
        evidence["checksumFile"] = alternate.name

        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_CHECKSUM_FILE_NAME_INVALID"
        ):
            self.validate(root, evidence)

    def test_checksum_file_drift_fails(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        checksum = root / evidence["checksumFile"]
        checksum.write_text(
            checksum.read_text(encoding="utf-8") + ("0" * 64) + "  extra.json\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            ReleaseProvenanceError,
            "RELEASE_CHECKSUM_PATH_SET_DRIFT|RELEASE_CHECKSUM_FILE_DIGEST_DRIFT",
        ):
            self.validate(root, evidence)

    def test_local_run_cannot_authorize_pass(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["provenance"]["workflowRunId"] = "LOCAL"
        evidence["validation"]["validationWorkflowRunId"] = "LOCAL"
        with self.assertRaisesRegex(
            ReleaseProvenanceError, "RELEASE_PASS_CANNOT_USE_LOCAL_RUN"
        ):
            validate_release_evidence(
                root=root,
                evidence=evidence,
                expected_version="0.14.0-rc.6",
                require_pass=True,
            )

    def test_pending_evidence_can_be_validated_without_pass_claim(self):
        temp, root, evidence = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence["status"] = "MATERIALIZED_VALIDATION_PENDING"
        evidence["validation"] = {
            "status": "PENDING",
            "validationSourceCommitSha": None,
            "validationWorkflowHeadSha": None,
            "validationWorkflowRunId": None,
            "validatedArtifactSetDigest": None,
            "validatedChecksumFileSha256": None,
            "validatedAt": None,
        }
        self.validate(root, evidence, require_pass=False)


if __name__ == "__main__":
    unittest.main()
