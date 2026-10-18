# KWP-02/03/04 integration failure

```text
SAFOR 0.14.0-rc.2 integration phase security: prepared
test_activation_model_requires_human_go_and_no_runtime_install (tests.test_agent_activation_v014.AgentActivationV014Tests.test_activation_model_requires_human_go_and_no_runtime_install) ... ok
test_automatic_activation_is_forbidden (tests.test_agent_activation_v014.AgentActivationV014Tests.test_automatic_activation_is_forbidden) ... ok
test_display_name_must_differ_from_agent_id (tests.test_agent_activation_v014.AgentActivationV014Tests.test_display_name_must_differ_from_agent_id) ... ok
test_exact_human_go_is_required (tests.test_agent_activation_v014.AgentActivationV014Tests.test_exact_human_go_is_required) ... ok
test_go_binds_to_selected_job_without_prompt_transport (tests.test_agent_activation_v014.AgentActivationV014Tests.test_go_binds_to_selected_job_without_prompt_transport) ... ok
test_go_is_case_insensitive_and_whitespace_trimmed (tests.test_agent_activation_v014.AgentActivationV014Tests.test_go_is_case_insensitive_and_whitespace_trimmed) ... ok
test_pointer_only_read_contract_forbids_full_scan (tests.test_agent_activation_v014.AgentActivationV014Tests.test_pointer_only_read_contract_forbids_full_scan) ... ok
test_stale_identity_revision_is_not_claimable (tests.test_agent_activation_v014.AgentActivationV014Tests.test_stale_identity_revision_is_not_claimable) ... ok
test_template_contains_one_time_prompt_and_go_reuse (tests.test_agent_activation_v014.AgentActivationV014Tests.test_template_contains_one_time_prompt_and_go_reuse) ... ok
test_uncertain_chat_binding_requires_reidentification (tests.test_agent_activation_v014.AgentActivationV014Tests.test_uncertain_chat_binding_requires_reidentification) ... ok
test_valid_chat_identity (tests.test_agent_activation_v014.AgentActivationV014Tests.test_valid_chat_identity) ... ok
test_wp01_json_files_parse_and_declare_v014 (tests.test_agent_activation_v014.AgentActivationV014Tests.test_wp01_json_files_parse_and_declare_v014) ... ok
test_actual_provider_rights_check_is_mandatory (tests.test_agent_job_v014.AgentJobV014Tests.test_actual_provider_rights_check_is_mandatory) ... ok
test_all_five_response_contracts_are_mandatory (tests.test_agent_job_v014.AgentJobV014Tests.test_all_five_response_contracts_are_mandatory) ... ok
test_blocked_chat_requires_git_reference (tests.test_agent_job_v014.AgentJobV014Tests.test_blocked_chat_requires_git_reference) ... ok
test_direct_default_branch_mutation_is_forbidden (tests.test_agent_job_v014.AgentJobV014Tests.test_direct_default_branch_mutation_is_forbidden) ... ok
test_go_transition_requires_bound_single_use_evidence (tests.test_agent_job_v014.AgentJobV014Tests.test_go_transition_requires_bound_single_use_evidence) ... ok
test_independent_reviewer_must_differ (tests.test_agent_job_v014.AgentJobV014Tests.test_independent_reviewer_must_differ) ... ok
test_job_requires_human_go_and_no_prompt_transport (tests.test_agent_job_v014.AgentJobV014Tests.test_job_requires_human_go_and_no_prompt_transport) ... ok
test_minimal_chat_output_for_all_allowed_statuses (tests.test_agent_job_v014.AgentJobV014Tests.test_minimal_chat_output_for_all_allowed_statuses) ... ok
test_remote_product_and_response_repositories_are_separate (tests.test_agent_job_v014.AgentJobV014Tests.test_remote_product_and_response_repositories_are_separate) ... ok
test_response_contract_cannot_point_to_wrong_template (tests.test_agent_job_v014.AgentJobV014Tests.test_response_contract_cannot_point_to_wrong_template) ... ok
test_rework_requires_superseded_job_and_conflict (tests.test_agent_job_v014.AgentJobV014Tests.test_rework_requires_superseded_job_and_conflict) ... ok
test_state_machine_separates_submission_verification_acceptance (tests.test_agent_job_v014.AgentJobV014Tests.test_state_machine_separates_submission_verification_acceptance) ... ok
test_valid_job_contract (tests.test_agent_job_v014.AgentJobV014Tests.test_valid_job_contract) ... ok
test_wp03_files_parse (tests.test_agent_job_v014.AgentJobV014Tests.test_wp03_files_parse) ... ok
test_all_five_response_types_validate (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_all_five_response_types_validate) ... ok
test_blocker_cannot_allow_more_product_mutation (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_blocker_cannot_allow_more_product_mutation) ... ok
test_capability_mismatch_has_explicit_expected_and_available_sets (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_capability_mismatch_has_explicit_expected_and_available_sets) ... ok
test_clarification_must_go_to_master_not_human (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_clarification_must_go_to_master_not_human) ... ok
test_conflict_requires_open_status_and_full_fields (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_conflict_requires_open_status_and_full_fields) ... ok
test_improvement_proposal_cannot_change_job_scope (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_improvement_proposal_cannot_change_job_scope) ... ok
test_job_binding_mismatch_is_rejected (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_job_binding_mismatch_is_rejected) ... ok
test_resolution_is_separate_and_can_supersede (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_resolution_is_separate_and_can_supersede) ... ok
test_response_index_path_is_deterministic (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_response_index_path_is_deterministic) ... ok
test_result_requires_output (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_result_requires_output) ... ok
test_superseded_resolution_requires_new_job_id (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_superseded_resolution_requires_new_job_id) ... ok
test_template_must_match_discriminator (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_template_must_match_discriminator) ... ok
test_unknown_response_type_fails_closed (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_unknown_response_type_fails_closed) ... ok
test_wp02_json_files_parse (tests.test_agent_responses_v014.AgentResponsesV014Tests.test_wp02_json_files_parse) ... ok
test_capability_and_capacity_are_enforced (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_capability_and_capacity_are_enforced) ... ok
test_compact_status_lists_agents_to_start_without_full_scan (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_compact_status_lists_agents_to_start_without_full_scan) ... ok
test_compact_status_rejects_full_repository_scan (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_compact_status_rejects_full_repository_scan) ... ok
test_expired_lease_requires_reconciliation_and_no_reassignment (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_expired_lease_requires_reconciliation_and_no_reassignment) ... ok
test_intersecting_write_domains_serialize (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_intersecting_write_domains_serialize) ... ok
test_read_only_jobs_do_not_conflict (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_read_only_jobs_do_not_conflict) ... ok
test_safe_jobs_are_dispatched_but_chat_is_not_activated (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_safe_jobs_are_dispatched_but_chat_is_not_activated) ... ok
test_separation_of_duties_blocks_author_review (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_separation_of_duties_blocks_author_review) ... ok
test_stale_status_is_explicit (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_stale_status_is_explicit) ... ERROR
test_status_reports_response_completion_separately_from_acceptance (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_status_reports_response_completion_separately_from_acceptance) ... ok
test_unbound_chat_agent_is_not_eligible (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_unbound_chat_agent_is_not_eligible) ... ok
test_unknown_scope_conflicts_with_every_mutating_job (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_unknown_scope_conflicts_with_every_mutating_job) ... ok
test_wp04_files_parse (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_wp04_files_parse) ... ok
test_atomic_claim_uses_expected_revision_and_consumes_activation (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_atomic_claim_uses_expected_revision_and_consumes_activation) ... ok
test_consumed_evidence_fails (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_consumed_evidence_fails) ... ok
test_duplicate_claim_fails (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_duplicate_claim_fails) ... ok
test_foreign_job_agent_binding_and_dispatch_fail (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_foreign_job_agent_binding_and_dispatch_fail) ... ok
test_string_containing_go_is_not_evidence (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_string_containing_go_is_not_evidence) ... ok
test_valid_evidence (tests.test_go_evidence_v014.GoEvidenceV014Tests.test_valid_evidence) ... ok
test_canceled_or_superseded_without_decision_and_response_is_not_complete (tests.test_master_status_truth_v014.MasterStatusTruthV014Tests.test_canceled_or_superseded_without_decision_and_response_is_not_complete) ... ok
test_explicit_decision_can_waive_response_expectation (tests.test_master_status_truth_v014.MasterStatusTruthV014Tests.test_explicit_decision_can_waive_response_expectation) ... ok
test_stale_after_is_evaluated_without_manual_reason (tests.test_master_status_truth_v014.MasterStatusTruthV014Tests.test_stale_after_is_evaluated_without_manual_reason) ... ok
test_unverified_readback_is_unknown_not_current (tests.test_master_status_truth_v014.MasterStatusTruthV014Tests.test_unverified_readback_is_unknown_not_current) ... ok
test_verified_response_readback_is_required (tests.test_master_status_truth_v014.MasterStatusTruthV014Tests.test_verified_response_readback_is_required) ... ok
test_complete_attempt_is_idempotent (tests.test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_complete_attempt_is_idempotent) ... ok
test_product_commit_then_response_failure_requires_response_only_reconcile (tests.test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_product_commit_then_response_failure_requires_response_only_reconcile) ... ok
test_read_before_retry_prevents_duplicate_product_mutation (tests.test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_read_before_retry_prevents_duplicate_product_mutation) ... ok
test_response_cannot_be_recorded_before_product_commit (tests.test_execution_reconciliation_v014.ExecutionReconciliationV014Tests.test_response_cannot_be_recorded_before_product_commit) ... ok

======================================================================
ERROR: test_stale_status_is_explicit (tests.test_master_scheduler_v014.MasterSchedulerV014Tests.test_stale_status_is_explicit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/tests/test_master_scheduler_v014.py", line 119, in test_stale_status_is_explicit
    self.assertIn('Provider', status['freshness']['staleReason'])
                              ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
KeyError: 'staleReason'

----------------------------------------------------------------------
Ran 68 tests in 0.011s

FAILED (errors=1)
```
