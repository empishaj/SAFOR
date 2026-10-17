"""Deterministic reference bridge for SAFOR public paid-domain evaluation.

The domain Framework distribution contains paid-mode test Factory and Operating
Model bytes. The matching public evaluation access bundle contains external
entitlement evidence for those exact test versions. This module binds both
artifacts without weakening the production commercial boundary.

The resolver is pure: it performs no I/O, reads no wall clock and issues no
entitlement. All trust and evaluation-time inputs must be present in the loaded
access bundle. Malformed or inconsistent untrusted input fails closed and is
returned as a typed rejection rather than escaping as a runtime exception.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Dict, Optional, Tuple

from runtime.bootstrap_policy import (
    compute_domain_package_digest,
    evaluate_domain_framework_pair,
    resolve_composable_creation_packages,
    validate_domain_package,
)


PUBLIC_EVALUATION_FORMAT = "SAFOR_PUBLIC_EVALUATION_ACCESS_BUNDLE"
PUBLIC_EVALUATION_PURPOSE = "PUBLIC_TEST_EVALUATION_ONLY"
PUBLIC_EVALUATION_PUBLICATION_MODE = "PUBLIC_TEST_EVALUATION"
PUBLIC_EVALUATION_BINDING_MODE = "PUBLIC_TEST_EVALUATION_ONLY"
PUBLIC_EVALUATION_NEXT_OPERATION = "SELECT_PROJECT_WORKSPACE_TYPE"


def _rejected(reason: str, **details: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "outcome": "PUBLIC_EVALUATION_ACCESS_REJECTED",
        "reason": reason,
        "productionAuthorization": False,
    }
    result.update(details)
    return result


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def compute_domain_framework_distribution_digest(
    distribution: Mapping[str, Any],
) -> str:
    """Compute the rc.6 domain-distribution digest used by the builder."""
    projection = {key: value for key, value in distribution.items() if key != "integrity"}
    payload = _canonical(projection).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _module_identity(module: Mapping[str, Any]) -> Tuple[str, str]:
    return str(module.get("packageId", "")), str(module.get("version", ""))


def _grant_identity(entitlement: Mapping[str, Any]) -> Tuple[str, str]:
    grant = entitlement.get("grant", {})
    if not isinstance(grant, Mapping):
        return "", ""
    return str(grant.get("packageId", "")), str(grant.get("versionRange", ""))


def _non_empty_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def _validate_distribution_integrity(
    distribution: Mapping[str, Any],
) -> Optional[Dict[str, Any]]:
    integrity = distribution.get("integrity")
    if not isinstance(integrity, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_INTEGRITY_METADATA_INVALID")
    if integrity.get("canonicalization") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION_V1":
        return _rejected("DOMAIN_FRAMEWORK_INTEGRITY_METADATA_INVALID")
    if integrity.get("digestAlgorithm") != "SHA-256":
        return _rejected("DOMAIN_FRAMEWORK_INTEGRITY_METADATA_INVALID")
    if integrity.get("digestScope") != "DISTRIBUTION_EXCLUDING_INTEGRITY":
        return _rejected("DOMAIN_FRAMEWORK_INTEGRITY_METADATA_INVALID")
    expected_digest = compute_domain_framework_distribution_digest(distribution)
    if integrity.get("contentDigest") != expected_digest:
        return _rejected(
            "DOMAIN_FRAMEWORK_INTEGRITY_MISMATCH",
            expectedDigest=expected_digest,
        )
    return None


def _validate_embedded_domain_pair(
    distribution: Mapping[str, Any],
    domain: Mapping[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[Mapping[str, Any]], Optional[Mapping[str, Any]]]:
    framework = distribution.get("framework")
    if not isinstance(framework, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_FRAMEWORK_INVALID"), None, None
    framework_version = framework.get("bundleVersion")
    if not isinstance(framework_version, str) or not framework_version:
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_FRAMEWORK_INVALID"), None, None

    creation_type = domain.get("creationType")
    domain_id = domain.get("domainId")
    if not isinstance(creation_type, str) or not creation_type:
        return _rejected("DOMAIN_FRAMEWORK_DOMAIN_INVALID"), None, None
    if not isinstance(domain_id, str) or not domain_id:
        return _rejected("DOMAIN_FRAMEWORK_DOMAIN_INVALID"), None, None

    modules = distribution.get("embeddedDomainModules")
    if not isinstance(modules, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_MODULES_INVALID"), None, None
    factory = modules.get("factory")
    operating_model = modules.get("operatingModel")
    if not isinstance(factory, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_FACTORY_INVALID"), None, None
    if not isinstance(operating_model, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_OPERATING_MODEL_INVALID"), None, None

    try:
        factory_validation = validate_domain_package(
            factory,
            framework_version,
            creation_type,
        )
        operating_model_validation = validate_domain_package(
            operating_model,
            framework_version,
            creation_type,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_PACKAGE_VALIDATION_ERROR"), None, None

    if not factory_validation.get("valid"):
        return (
            _rejected(
                "DOMAIN_FRAMEWORK_EMBEDDED_FACTORY_INVALID",
                packageErrors=factory_validation.get("errors", []),
            ),
            None,
            None,
        )
    if not operating_model_validation.get("valid"):
        return (
            _rejected(
                "DOMAIN_FRAMEWORK_EMBEDDED_OPERATING_MODEL_INVALID",
                packageErrors=operating_model_validation.get("errors", []),
            ),
            None,
            None,
        )

    try:
        pair = evaluate_domain_framework_pair(
            factory,
            operating_model,
            framework_version,
            creation_type,
            domain_id,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_PAIR_VALIDATION_ERROR"), None, None
    if pair.get("compatible") is not True:
        return (
            _rejected(
                "DOMAIN_FRAMEWORK_EMBEDDED_PAIR_INCOMPATIBLE",
                compatibilityDecision=pair,
            ),
            None,
            None,
        )

    binding = distribution.get("defaultBinding")
    if not isinstance(binding, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_DEFAULT_BINDING_INVALID"), None, None
    binding_factory = binding.get("factory")
    binding_operating_model = binding.get("operatingModel")
    if not isinstance(binding_factory, Mapping) or not isinstance(
        binding_operating_model, Mapping
    ):
        return _rejected("DOMAIN_FRAMEWORK_DEFAULT_BINDING_INVALID"), None, None

    expected_factory_binding = {
        "packageId": factory.get("packageId"),
        "packageFamily": factory.get("packageFamily"),
        "version": factory.get("version"),
        "contentDigest": compute_domain_package_digest(factory),
    }
    expected_operating_model_binding = {
        "packageId": operating_model.get("packageId"),
        "packageFamily": operating_model.get("packageFamily"),
        "version": operating_model.get("version"),
        "contentDigest": compute_domain_package_digest(operating_model),
    }
    if dict(binding_factory) != expected_factory_binding:
        return _rejected("DOMAIN_FRAMEWORK_DEFAULT_FACTORY_BINDING_MISMATCH"), None, None
    if dict(binding_operating_model) != expected_operating_model_binding:
        return (
            _rejected("DOMAIN_FRAMEWORK_DEFAULT_OPERATING_MODEL_BINDING_MISMATCH"),
            None,
            None,
        )
    if binding.get("compatibility") != "COMPATIBLE":
        return _rejected("DOMAIN_FRAMEWORK_DEFAULT_COMPATIBILITY_INVALID"), None, None
    if binding.get("domainId") != domain_id:
        return _rejected("DOMAIN_FRAMEWORK_DEFAULT_DOMAIN_BINDING_MISMATCH"), None, None

    return None, factory, operating_model


def resolve_public_evaluation_access(
    distribution: Mapping[str, Any],
    access_bundle: Mapping[str, Any],
    package_catalog: Mapping[str, Any],
    *,
    access_file_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and bind one public evaluation access bundle.

    Only public test/evaluation domain distributions are accepted. The resolver
    verifies the complete distribution digest, embedded package digests, active
    domain, bidirectional Factory/Operating-Model compatibility, immutable
    default binding, exact test entitlements and the no-production boundary.
    """

    if not isinstance(distribution, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_CONTAINER_INVALID")
    if not isinstance(access_bundle, Mapping):
        return _rejected("PUBLIC_EVALUATION_ACCESS_CONTAINER_INVALID")
    if not isinstance(package_catalog, Mapping):
        return _rejected("PUBLIC_EVALUATION_PACKAGE_CATALOG_INVALID")

    if distribution.get("format") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION":
        return _rejected("DOMAIN_FRAMEWORK_FORMAT_INVALID")
    if distribution.get("publicationMode") != PUBLIC_EVALUATION_PUBLICATION_MODE:
        return _rejected("DOMAIN_FRAMEWORK_NOT_PUBLIC_EVALUATION")

    integrity_rejection = _validate_distribution_integrity(distribution)
    if integrity_rejection is not None:
        return integrity_rejection

    evaluation_access = distribution.get("evaluationAccess")
    if not isinstance(evaluation_access, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_ACCESS_INVALID")
    if evaluation_access.get("mode") != "EXTERNAL_TEST_ACCESS_BUNDLE":
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_MODE_INVALID")
    if evaluation_access.get("embeddedModulesSourceClass") != "HUMAN_LOADED_PACKAGE":
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_SOURCE_CLASS_INVALID")
    if evaluation_access.get("productionAuthorization") is not False:
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_PRODUCTION_AUTHORIZATION_INVALID")

    expected_access_file = evaluation_access.get("file")
    if not isinstance(expected_access_file, str) or not expected_access_file:
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_ACCESS_FILE_MISSING")
    if access_file_name is not None and access_file_name != expected_access_file:
        return _rejected(
            "PUBLIC_EVALUATION_ACCESS_FILENAME_MISMATCH",
            expectedAccessFile=expected_access_file,
            receivedAccessFile=access_file_name,
        )

    if access_bundle.get("format") != PUBLIC_EVALUATION_FORMAT:
        return _rejected("PUBLIC_EVALUATION_ACCESS_FORMAT_INVALID")
    if access_bundle.get("schemaVersion") != distribution.get("schemaVersion"):
        return _rejected("PUBLIC_EVALUATION_ACCESS_SCHEMA_VERSION_MISMATCH")
    if access_bundle.get("purpose") != PUBLIC_EVALUATION_PURPOSE:
        return _rejected("PUBLIC_EVALUATION_ACCESS_PURPOSE_INVALID")

    domain = distribution.get("domain")
    if not isinstance(domain, Mapping):
        return _rejected("DOMAIN_FRAMEWORK_DOMAIN_INVALID")
    embedded_rejection, factory, operating_model = _validate_embedded_domain_pair(
        distribution,
        domain,
    )
    if embedded_rejection is not None:
        return embedded_rejection
    if factory is None or operating_model is None:
        return _rejected("DOMAIN_FRAMEWORK_EMBEDDED_MODULES_INVALID")

    if access_bundle.get("domainId") != domain.get("domainId"):
        return _rejected(
            "PUBLIC_EVALUATION_ACCESS_DOMAIN_MISMATCH",
            expectedDomainId=domain.get("domainId"),
            receivedDomainId=access_bundle.get("domainId"),
        )
    if access_bundle.get("creationType") != domain.get("creationType"):
        return _rejected(
            "PUBLIC_EVALUATION_ACCESS_CREATION_TYPE_MISMATCH",
            expectedCreationType=domain.get("creationType"),
            receivedCreationType=access_bundle.get("creationType"),
        )

    restrictions = access_bundle.get("restrictions")
    if not isinstance(restrictions, Mapping):
        return _rejected("PUBLIC_EVALUATION_RESTRICTIONS_INVALID")
    if restrictions.get("testPackageVersionsOnly") is not True:
        return _rejected("PUBLIC_EVALUATION_TEST_VERSION_RESTRICTION_MISSING")
    if restrictions.get("productionAuthorization") is not False:
        return _rejected("PUBLIC_EVALUATION_PRODUCTION_AUTHORIZATION_FORBIDDEN")
    if restrictions.get("transferable") is not False:
        return _rejected("PUBLIC_EVALUATION_TRANSFER_FORBIDDEN")
    if restrictions.get("commercialPurchaseEvidence") is not False:
        return _rejected("PUBLIC_EVALUATION_COMMERCIAL_EVIDENCE_CLAIM_FORBIDDEN")

    activation = access_bundle.get("activationContract")
    if not isinstance(activation, Mapping):
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_CONTRACT_INVALID")
    if activation.get("requiredDistributionFormat") != distribution.get("format"):
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_FORMAT_MISMATCH")
    if activation.get("requiredDistributionId") != distribution.get("distributionId"):
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_DISTRIBUTION_MISMATCH")
    if activation.get("requiredDistributionFile") != distribution.get("fileName"):
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_FILE_MISMATCH")
    if activation.get("bindingMode") != PUBLIC_EVALUATION_BINDING_MODE:
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_BINDING_MODE_INVALID")
    if activation.get("applyEntitlementsToEmbeddedModules") is not True:
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_APPLICATION_RULE_INVALID")
    if activation.get("suppressCreationTypeSelection") is not True:
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_DOMAIN_PRESELECTION_INVALID")
    if activation.get("onSuccess") != "CONTINUE_AT_PROJECT_WORKSPACE_SELECTION":
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_SUCCESS_ROUTE_INVALID")
    if activation.get("onMissingDistribution") != "REQUEST_REQUIRED_DISTRIBUTION_FILE":
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_MISSING_ROUTE_INVALID")
    if activation.get("onMismatch") != "REJECT_AND_KEEP_PREVIOUS_VALID_BINDING":
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_MISMATCH_ROUTE_INVALID")

    subject_ref = access_bundle.get("subjectRef")
    if not isinstance(subject_ref, str) or not subject_ref:
        return _rejected("PUBLIC_EVALUATION_SUBJECT_INVALID")
    verification_context = access_bundle.get("verificationContext")
    if not isinstance(verification_context, Mapping):
        return _rejected("PUBLIC_EVALUATION_VERIFICATION_CONTEXT_INVALID")
    if verification_context.get("subjectRef") != subject_ref:
        return _rejected("PUBLIC_EVALUATION_SUBJECT_CONTEXT_MISMATCH")
    if not isinstance(verification_context.get("evaluatedAt"), str) or not verification_context.get(
        "evaluatedAt"
    ):
        return _rejected("PUBLIC_EVALUATION_VERIFICATION_CONTEXT_INVALID")
    for trust_field in (
        "trustedIssuerIds",
        "trustedEntitlementVerifierIds",
        "trustedDeliveryVerifierIds",
    ):
        if not _non_empty_string_list(verification_context.get(trust_field)):
            return _rejected(
                "PUBLIC_EVALUATION_VERIFICATION_CONTEXT_INVALID",
                invalidField=trust_field,
            )

    expected_modules = {_module_identity(factory), _module_identity(operating_model)}
    if any(not package_id or not version for package_id, version in expected_modules):
        return _rejected("PUBLIC_EVALUATION_EMBEDDED_MODULE_IDENTITY_INVALID")
    if len(expected_modules) != 2:
        return _rejected("PUBLIC_EVALUATION_EMBEDDED_MODULE_SET_INVALID")

    for module in (factory, operating_model):
        commercial = module.get("commercial")
        if not isinstance(commercial, Mapping):
            return _rejected("PUBLIC_EVALUATION_MODULE_COMMERCIAL_CONTRACT_INVALID")
        if commercial.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
            return _rejected("PUBLIC_EVALUATION_MODULE_NOT_PAID_MODE")
        if commercial.get("entitlementRequired") is not True:
            return _rejected("PUBLIC_EVALUATION_MODULE_ENTITLEMENT_FLAG_INVALID")

    entitlements = access_bundle.get("entitlements")
    if not isinstance(entitlements, list) or len(entitlements) != 2:
        return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_SET_INVALID")
    if not all(isinstance(entitlement, Mapping) for entitlement in entitlements):
        return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_SHAPE_INVALID")

    entitlement_ids = [entitlement.get("entitlementId") for entitlement in entitlements]
    if not all(isinstance(item, str) and item for item in entitlement_ids):
        return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_ID_SET_INVALID")
    if len(set(entitlement_ids)) != len(entitlement_ids):
        return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_ID_SET_INVALID")

    required_entitlement_objects = (
        "grant",
        "subject",
        "commercialBasis",
        "validity",
        "issuer",
        "verification",
    )
    for entitlement in entitlements:
        for field in required_entitlement_objects:
            if not isinstance(entitlement.get(field), Mapping):
                return _rejected(
                    "PUBLIC_EVALUATION_ENTITLEMENT_SHAPE_INVALID",
                    entitlementId=entitlement.get("entitlementId"),
                    invalidField=field,
                )

    grant_identities = {_grant_identity(entitlement) for entitlement in entitlements}
    if grant_identities != expected_modules:
        return _rejected(
            "PUBLIC_EVALUATION_GRANT_SET_MISMATCH",
            expectedGrants=sorted(expected_modules),
            receivedGrants=sorted(grant_identities),
        )

    for entitlement in entitlements:
        subject = entitlement.get("subject")
        if not isinstance(subject, Mapping) or subject.get("subjectRef") != subject_ref:
            return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_SUBJECT_MISMATCH")

    try:
        package_result = resolve_composable_creation_packages(
            str(domain.get("creationType", "")),
            package_catalog,
            [
                {
                    "sourceClass": "HUMAN_LOADED_PACKAGE",
                    "artifact": factory,
                },
                {
                    "sourceClass": "HUMAN_LOADED_PACKAGE",
                    "artifact": operating_model,
                },
            ],
            entitlements,
            verification_context=verification_context,
        )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        return _rejected(
            "PUBLIC_EVALUATION_PACKAGE_RESOLUTION_ERROR",
            errorType=type(error).__name__,
        )
    if not isinstance(package_result, Mapping):
        return _rejected("PUBLIC_EVALUATION_PACKAGE_RESOLUTION_ERROR")
    if package_result.get("outcome") != "PACKAGE_ACCESS_RESOLVED":
        return _rejected(
            "PUBLIC_EVALUATION_PACKAGE_ACCESS_NOT_RESOLVED",
            packageAccessOutcome=package_result.get("outcome"),
            packageAccess=dict(package_result),
        )

    return {
        "outcome": "PUBLIC_EVALUATION_ACCESS_RESOLVED",
        "domainId": domain.get("domainId"),
        "creationType": domain.get("creationType"),
        "distributionId": distribution.get("distributionId"),
        "accessFile": expected_access_file,
        "subjectRef": subject_ref,
        "productionAuthorization": False,
        "packageAccess": dict(package_result),
        "nextOperation": PUBLIC_EVALUATION_NEXT_OPERATION,
    }
