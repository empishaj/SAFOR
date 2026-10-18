# KWP-00/01 integration failure

```text
SAFOR 0.14.0-rc.2 integration phase baseline: prepared
test_activation_model_requires_human_go_and_no_runtime_install (test_agent_activation_v014.AgentActivationV014Tests.test_activation_model_requires_human_go_and_no_runtime_install) ... ok
test_automatic_activation_is_forbidden (test_agent_activation_v014.AgentActivationV014Tests.test_automatic_activation_is_forbidden) ... ok
test_display_name_must_differ_from_agent_id (test_agent_activation_v014.AgentActivationV014Tests.test_display_name_must_differ_from_agent_id) ... ok
test_exact_human_go_is_required (test_agent_activation_v014.AgentActivationV014Tests.test_exact_human_go_is_required) ... ok
test_go_binds_to_selected_job_without_prompt_transport (test_agent_activation_v014.AgentActivationV014Tests.test_go_binds_to_selected_job_without_prompt_transport) ... ok
test_go_is_case_insensitive_and_whitespace_trimmed (test_agent_activation_v014.AgentActivationV014Tests.test_go_is_case_insensitive_and_whitespace_trimmed) ... ok
test_pointer_only_read_contract_forbids_full_scan (test_agent_activation_v014.AgentActivationV014Tests.test_pointer_only_read_contract_forbids_full_scan) ... ok
test_stale_identity_revision_is_not_claimable (test_agent_activation_v014.AgentActivationV014Tests.test_stale_identity_revision_is_not_claimable) ... ok
test_template_contains_one_time_prompt_and_go_reuse (test_agent_activation_v014.AgentActivationV014Tests.test_template_contains_one_time_prompt_and_go_reuse) ... ok
test_uncertain_chat_binding_requires_reidentification (test_agent_activation_v014.AgentActivationV014Tests.test_uncertain_chat_binding_requires_reidentification) ... ok
test_valid_chat_identity (test_agent_activation_v014.AgentActivationV014Tests.test_valid_chat_identity) ... ok
test_wp01_json_files_parse_and_declare_v014 (test_agent_activation_v014.AgentActivationV014Tests.test_wp01_json_files_parse_and_declare_v014) ... ok
test_actual_provider_rights_check_is_mandatory (test_agent_job_v014.AgentJobV014Tests.test_actual_provider_rights_check_is_mandatory) ... ok
test_all_five_response_contracts_are_mandatory (test_agent_job_v014.AgentJobV014Tests.test_all_five_response_contracts_are_mandatory) ... ok
test_blocked_chat_requires_git_reference (test_agent_job_v014.AgentJobV014Tests.test_blocked_chat_requires_git_reference) ... ok
test_direct_default_branch_mutation_is_forbidden (test_agent_job_v014.AgentJobV014Tests.test_direct_default_branch_mutation_is_forbidden) ... ok
test_go_transition_requires_go_evidence (test_agent_job_v014.AgentJobV014Tests.test_go_transition_requires_go_evidence) ... ok
test_independent_reviewer_must_differ (test_agent_job_v014.AgentJobV014Tests.test_independent_reviewer_must_differ) ... ok
test_job_requires_human_go_and_no_prompt_transport (test_agent_job_v014.AgentJobV014Tests.test_job_requires_human_go_and_no_prompt_transport) ... ok
test_minimal_chat_output_for_all_allowed_statuses (test_agent_job_v014.AgentJobV014Tests.test_minimal_chat_output_for_all_allowed_statuses) ... ok
test_remote_product_and_response_repositories_are_separate (test_agent_job_v014.AgentJobV014Tests.test_remote_product_and_response_repositories_are_separate) ... ok
test_response_contract_cannot_point_to_wrong_template (test_agent_job_v014.AgentJobV014Tests.test_response_contract_cannot_point_to_wrong_template) ... ok
test_rework_requires_superseded_job_and_conflict (test_agent_job_v014.AgentJobV014Tests.test_rework_requires_superseded_job_and_conflict) ... ok
test_state_machine_separates_submission_verification_acceptance (test_agent_job_v014.AgentJobV014Tests.test_state_machine_separates_submission_verification_acceptance) ... ok
test_valid_job_contract (test_agent_job_v014.AgentJobV014Tests.test_valid_job_contract) ... ok
test_wp03_files_parse (test_agent_job_v014.AgentJobV014Tests.test_wp03_files_parse) ... ok
test_all_five_response_types_validate (test_agent_responses_v014.AgentResponsesV014Tests.test_all_five_response_types_validate) ... ok
test_blocker_cannot_allow_more_product_mutation (test_agent_responses_v014.AgentResponsesV014Tests.test_blocker_cannot_allow_more_product_mutation) ... ok
test_capability_mismatch_has_explicit_expected_and_available_sets (test_agent_responses_v014.AgentResponsesV014Tests.test_capability_mismatch_has_explicit_expected_and_available_sets) ... ok
test_clarification_must_go_to_master_not_human (test_agent_responses_v014.AgentResponsesV014Tests.test_clarification_must_go_to_master_not_human) ... ok
test_conflict_requires_open_status_and_full_fields (test_agent_responses_v014.AgentResponsesV014Tests.test_conflict_requires_open_status_and_full_fields) ... ok
test_improvement_proposal_cannot_change_job_scope (test_agent_responses_v014.AgentResponsesV014Tests.test_improvement_proposal_cannot_change_job_scope) ... ok
test_job_binding_mismatch_is_rejected (test_agent_responses_v014.AgentResponsesV014Tests.test_job_binding_mismatch_is_rejected) ... ok
test_resolution_is_separate_and_can_supersede (test_agent_responses_v014.AgentResponsesV014Tests.test_resolution_is_separate_and_can_supersede) ... ok
test_response_index_path_is_deterministic (test_agent_responses_v014.AgentResponsesV014Tests.test_response_index_path_is_deterministic) ... ok
test_result_requires_output (test_agent_responses_v014.AgentResponsesV014Tests.test_result_requires_output) ... ok
test_superseded_resolution_requires_new_job_id (test_agent_responses_v014.AgentResponsesV014Tests.test_superseded_resolution_requires_new_job_id) ... ok
test_template_must_match_discriminator (test_agent_responses_v014.AgentResponsesV014Tests.test_template_must_match_discriminator) ... ok
test_unknown_response_type_fails_closed (test_agent_responses_v014.AgentResponsesV014Tests.test_unknown_response_type_fails_closed) ... ok
test_wp02_json_files_parse (test_agent_responses_v014.AgentResponsesV014Tests.test_wp02_json_files_parse) ... ok
test_complete_attempt_is_idempotent (test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_complete_attempt_is_idempotent) ... ok
test_product_commit_then_response_failure_requires_response_only_reconcile (test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_product_commit_then_response_failure_requires_response_only_reconcile) ... ok
test_read_before_retry_prevents_duplicate_product_mutation (test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_read_before_retry_prevents_duplicate_product_mutation) ... ok
test_response_cannot_be_recorded_before_product_commit (test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_response_cannot_be_recorded_before_product_commit) ... ok
test_atomic_claim_uses_expected_revision_and_consumes_activation (test_go_evidence_v014.GoEvidenceV014Tests.test_atomic_claim_uses_expected_revision_and_consumes_activation) ... ok
test_consumed_evidence_fails (test_go_evidence_v014.GoEvidenceV014Tests.test_consumed_evidence_fails) ... ok
test_duplicate_claim_fails (test_go_evidence_v014.GoEvidenceV014Tests.test_duplicate_claim_fails) ... ok
test_foreign_job_agent_binding_and_dispatch_fail (test_go_evidence_v014.GoEvidenceV014Tests.test_foreign_job_agent_binding_and_dispatch_fail) ... ok
test_string_containing_go_is_not_evidence (test_go_evidence_v014.GoEvidenceV014Tests.test_string_containing_go_is_not_evidence) ... ok
test_valid_evidence (test_go_evidence_v014.GoEvidenceV014Tests.test_valid_evidence) ... ok
test_capability_and_capacity_are_enforced (test_master_scheduler_v014.MasterSchedulerV014Tests.test_capability_and_capacity_are_enforced) ... ok
test_compact_status_lists_agents_to_start_without_full_scan (test_master_scheduler_v014.MasterSchedulerV014Tests.test_compact_status_lists_agents_to_start_without_full_scan) ... ok
test_compact_status_rejects_full_repository_scan (test_master_scheduler_v014.MasterSchedulerV014Tests.test_compact_status_rejects_full_repository_scan) ... ok
test_expired_lease_requires_reconciliation_and_no_reassignment (test_master_scheduler_v014.MasterSchedulerV014Tests.test_expired_lease_requires_reconciliation_and_no_reassignment) ... ok
test_intersecting_write_domains_serialize (test_master_scheduler_v014.MasterSchedulerV014Tests.test_intersecting_write_domains_serialize) ... ok
test_read_only_jobs_do_not_conflict (test_master_scheduler_v014.MasterSchedulerV014Tests.test_read_only_jobs_do_not_conflict) ... ok
test_safe_jobs_are_dispatched_but_chat_is_not_activated (test_master_scheduler_v014.MasterSchedulerV014Tests.test_safe_jobs_are_dispatched_but_chat_is_not_activated) ... ok
test_separation_of_duties_blocks_author_review (test_master_scheduler_v014.MasterSchedulerV014Tests.test_separation_of_duties_blocks_author_review) ... ok
test_stale_status_is_explicit (test_master_scheduler_v014.MasterSchedulerV014Tests.test_stale_status_is_explicit) ... ok
test_status_reports_response_completion_separately_from_acceptance (test_master_scheduler_v014.MasterSchedulerV014Tests.test_status_reports_response_completion_separately_from_acceptance) ... ok
test_unbound_chat_agent_is_not_eligible (test_master_scheduler_v014.MasterSchedulerV014Tests.test_unbound_chat_agent_is_not_eligible) ... ok
test_unknown_scope_conflicts_with_every_mutating_job (test_master_scheduler_v014.MasterSchedulerV014Tests.test_unknown_scope_conflicts_with_every_mutating_job) ... ok
test_wp04_files_parse (test_master_scheduler_v014.MasterSchedulerV014Tests.test_wp04_files_parse) ... ok
test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) ... 
  test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='CANCELED') ... ERROR
  test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='SUPERSEDED') ... ERROR
  test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='REJECTED') ... ERROR
test_explicit_decision_can_waive_response_expectation (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_explicit_decision_can_waive_response_expectation) ... ERROR
test_stale_after_is_evaluated_without_manual_reason (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_stale_after_is_evaluated_without_manual_reason) ... ERROR
test_unverified_readback_is_unknown_not_current (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_unverified_readback_is_unknown_not_current) ... ERROR
test_verified_response_readback_is_required (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_verified_response_readback_is_required) ... ERROR
test_active_target_must_use_canonical_repository (test_migration_v014.MigrationV014Tests.test_active_target_must_use_canonical_repository) ... ok
test_all_agents_need_distinct_display_name_and_disabled_legacy_dispatch (test_migration_v014.MigrationV014Tests.test_all_agents_need_distinct_display_name_and_disabled_legacy_dispatch) ... ok
test_dual_active_authority_is_rejected (test_migration_v014.MigrationV014Tests.test_dual_active_authority_is_rejected) ... ok
test_history_deletion_or_mutation_is_forbidden (test_migration_v014.MigrationV014Tests.test_history_deletion_or_mutation_is_forbidden) ... ok
test_inventory_coverage_must_be_exact (test_migration_v014.MigrationV014Tests.test_inventory_coverage_must_be_exact) ... ok
test_known_legacy_formats_are_classified_read_only (test_migration_v014.MigrationV014Tests.test_known_legacy_formats_are_classified_read_only) ... ok
test_legacy_artifact_can_never_claim_or_dispatch (test_migration_v014.MigrationV014Tests.test_legacy_artifact_can_never_claim_or_dispatch) ... ok
test_provider_readback_and_evidence_are_required (test_migration_v014.MigrationV014Tests.test_provider_readback_and_evidence_are_required) ... ok
test_repository_alias_cycle_fails_closed (test_migration_v014.MigrationV014Tests.test_repository_alias_cycle_fails_closed) ... ok
test_repository_alias_resolves_to_canonical_name (test_migration_v014.MigrationV014Tests.test_repository_alias_resolves_to_canonical_name) ... ok
test_valid_manifest_preserves_all_inventory (test_migration_v014.MigrationV014Tests.test_valid_manifest_preserves_all_inventory) ... ok
test_wp05_json_files_parse (test_migration_v014.MigrationV014Tests.test_wp05_json_files_parse) ... ok
test_all_five_typed_responses_are_documented (test_product_boundary_v014.ProductBoundaryV014Tests.test_all_five_typed_responses_are_documented) ... ok
test_all_product_boundary_documents_exist (test_product_boundary_v014.ProductBoundaryV014Tests.test_all_product_boundary_documents_exist) ... ok
test_docs_preserve_actual_tool_and_rights_boundary (test_product_boundary_v014.ProductBoundaryV014Tests.test_docs_preserve_actual_tool_and_rights_boundary) ... ok
test_job_lifecycle_separates_submission_acceptance_integration (test_product_boundary_v014.ProductBoundaryV014Tests.test_job_lifecycle_separates_submission_acceptance_integration) ... ok
test_master_only_human_domain_interface_is_documented (test_product_boundary_v014.ProductBoundaryV014Tests.test_master_only_human_domain_interface_is_documented) ... ok
test_minimal_chat_contract_is_documented (test_product_boundary_v014.ProductBoundaryV014Tests.test_minimal_chat_contract_is_documented) ... ok
test_no_document_requires_additional_end_user_runtime (test_product_boundary_v014.ProductBoundaryV014Tests.test_no_document_requires_additional_end_user_runtime) ... ok
test_normal_chat_agent_has_only_human_go_activation (test_product_boundary_v014.ProductBoundaryV014Tests.test_normal_chat_agent_has_only_human_go_activation) ... ok
test_v014_models_declare_no_runtime_installation_requirement (test_product_boundary_v014.ProductBoundaryV014Tests.test_v014_models_declare_no_runtime_installation_requirement) ... ok

======================================================================
ERROR: test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='CANCELED')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 18, in test_canceled_or_superseded_without_decision_and_response_is_not_complete
    result = self.status(job)
             ^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='SUPERSEDED')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 18, in test_canceled_or_superseded_without_decision_and_response_is_not_complete
    result = self.status(job)
             ^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_canceled_or_superseded_without_decision_and_response_is_not_complete (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) (lifecycle='REJECTED')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 18, in test_canceled_or_superseded_without_decision_and_response_is_not_complete
    result = self.status(job)
             ^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_explicit_decision_can_waive_response_expectation (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_explicit_decision_can_waive_response_expectation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 24, in test_explicit_decision_can_waive_response_expectation
    result = self.status(job)
             ^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_stale_after_is_evaluated_without_manual_reason (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_stale_after_is_evaluated_without_manual_reason)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 37, in test_stale_after_is_evaluated_without_manual_reason
    result = self.status(job, observed_at="2026-10-18T12:00:00Z", stale_after="2026-10-18T11:00:00Z")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_unverified_readback_is_unknown_not_current (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_unverified_readback_is_unknown_not_current)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 43, in test_unverified_readback_is_unknown_not_current
    result = self.status(job, provider_readback_verified=None)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

======================================================================
ERROR: test_verified_response_readback_is_required (test_master_status_truth_v014.MasterStatusTruthV014Tests.test_verified_response_readback_is_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 31, in test_verified_response_readback_is_required
    self.assertFalse(self.status(job, [invalid])["allExpectedResponsesReceived"])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_status_truth_v014.py", line 12, in status
    return build_compact_project_status(**defaults)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: build_compact_project_status() got an unexpected keyword argument 'response_status_entries'

----------------------------------------------------------------------
Ran 89 tests in 0.019s

FAILED (errors=7)
```
