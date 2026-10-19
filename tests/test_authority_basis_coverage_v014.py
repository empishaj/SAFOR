import copy
import unittest

from runtime.agent_jobs import (
    AgentJobValidationError,
    validate_authority_basis_coverage,
)
from tests.v014_fixtures import valid_agent_job


class AuthorityBasisCoverageV014Tests(unittest.TestCase):
    def setUp(self):
        self.job = valid_agent_job(
            project_id="project-001",
            agent_id="agent-a",
            display_name="Agent Alpha",
            identity_revision=2,
            dispatch_revision=3,
            control_repository="example/safor-memory",
            control_branch="control/e2e",
            product_repository="example/product",
            product_branch="work/e2e-r5",
        )
        self.mandate = {
            "format": "SAFOR_EXECUTION_MANDATE",
            "schemaVersion": "0.14.0",
            "mandateId": "mandate-001",
            "status": "ACTIVE",
            "projectId": "project-001",
            "agentId": "agent-a",
            "allowedControlBranch": "control/e2e",
            "allowedProductRepository": "example/product",
            "allowedProductBranch": "work/e2e-r5",
            "allowedProductPaths": ["test-output/"],
            "humanGoRequired": True,
            "humanOnlyActivation": True,
            "masterMayActivateAgent": False,
            "mergeAllowed": False,
            "deployAllowed": False,
        }

    def test_matching_active_mandate_covers_job(self):
        validate_authority_basis_coverage(
            job=self.job,
            authority_basis=self.mandate,
            authority_basis_ref=self.job["authorization"]["authorityBasis"],
        )

    def test_real_git_branch_mismatch_is_rejected_before_dispatch(self):
        invalid = copy.deepcopy(self.mandate)
        invalid["allowedProductBranch"] = "work/e2e"
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "AUTHORITY_BASIS_PRODUCT_BRANCH_NOT_COVERED",
        ):
            validate_authority_basis_coverage(
                job=self.job,
                authority_basis=invalid,
                authority_basis_ref=self.job["authorization"]["authorityBasis"],
            )

    def test_inactive_mandate_is_rejected(self):
        invalid = copy.deepcopy(self.mandate)
        invalid["status"] = "SUPERSEDED"
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "AUTHORITY_BASIS_NOT_ACTIVE",
        ):
            validate_authority_basis_coverage(
                job=self.job,
                authority_basis=invalid,
            )

    def test_product_path_outside_mandate_is_rejected(self):
        invalid = copy.deepcopy(self.mandate)
        invalid["allowedProductPaths"] = ["different-root/"]
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "AUTHORITY_BASIS_PRODUCT_PATH_NOT_COVERED",
        ):
            validate_authority_basis_coverage(
                job=self.job,
                authority_basis=invalid,
            )

    def test_control_branch_outside_mandate_is_rejected(self):
        invalid = copy.deepcopy(self.mandate)
        invalid["allowedControlBranch"] = "control/other"
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "AUTHORITY_BASIS_CONTROL_BRANCH_NOT_COVERED",
        ):
            validate_authority_basis_coverage(
                job=self.job,
                authority_basis=invalid,
            )

    def test_observed_authority_pointer_must_match_pinned_pointer(self):
        observed = dict(self.job["authorization"]["authorityBasis"])
        observed["blobSha"] = "differentblob"
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "AUTHORITY_BASIS_POINTER_MISMATCH:blobSha",
        ):
            validate_authority_basis_coverage(
                job=self.job,
                authority_basis=self.mandate,
                authority_basis_ref=observed,
            )

    def test_provenance_mandate_ref_must_equal_authority_basis(self):
        invalid_job = copy.deepcopy(self.job)
        invalid_job["provenance"]["mandateRef"]["blobSha"] = "otherblob"
        with self.assertRaisesRegex(
            AgentJobValidationError,
            "JOB_MANDATE_AND_AUTHORITY_BASIS_POINTER_MISMATCH:blobSha",
        ):
            validate_authority_basis_coverage(
                job=invalid_job,
                authority_basis=self.mandate,
            )


if __name__ == "__main__":
    unittest.main()
