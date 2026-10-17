"""Deterministic bridge for SAFOR public paid-domain evaluation artifacts.

The domain Framework distribution contains paid-mode test Factory and Operating
Model bytes.  The matching public evaluation access bundle contains external
entitlement evidence for those exact test versions.  This module binds both
artifacts without weakening the production commercial boundary.

The resolver is pure: it performs no I/O, reads no wall clock and issues no
entitlement.  All trust and evaluation-time inputs must be present in the
loaded access bundle.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from runtime.bootstrap_policy import resolve_composable_creation_packages


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


def _module_identity(module: Mapping[str, Any]) -> Tuple[str, str]:
    return str(module.get("packageId", "")), str(module.get("version", ""))


def _grant_identity(entitlement: Mapping[str, Any]) -> Tuple[str, str]:
    grant = entitlement.get("grant", {})
    return str(grant.get("packageId", "")), str(grant.get("versionRange", ""))


def resolve_public_evaluation_access(
    distribution: Mapping[str, Any],
    access_bundle: Mapping[str, Any],
    package_catalog: Mapping[str, Any],
    *,
    access_file_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate and bind one public evaluation access bundle.

    The function deliberately accepts only public test/evaluation domain
    distributions.  It rejects cross-domain bundles, production authorization,
    missing or additional grants, and activation contracts that point to a
    different Framework file.  On success it delegates the package-level
    entitlement decision to the normal composable-package resolver.
    """

    if distribution.get("format") != "SAFOR_DOMAIN_FRAMEWORK_DISTRIBUTION":
        return _rejected("DOMAIN_FRAMEWORK_FORMAT_INVALID")
    if distribution.get("publicationMode") != PUBLIC_EVALUATION_PUBLICATION_MODE:
        return _rejected("DOMAIN_FRAMEWORK_NOT_PUBLIC_EVALUATION")

    evaluation_access = distribution.get("evaluationAccess", {})
    if evaluation_access.get("mode") != "EXTERNAL_TEST_ACCESS_BUNDLE":
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_MODE_INVALID")
    if evaluation_access.get("embeddedModulesSourceClass") != "HUMAN_LOADED_PACKAGE":
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_SOURCE_CLASS_INVALID")
    if evaluation_access.get("productionAuthorization") is not False:
        return _rejected("DOMAIN_FRAMEWORK_EVALUATION_PRODUCTION_AUTHORIZATION_INVALID")

    expected_access_file = str(evaluation_access.get("file", ""))
    if not expected_access_file:
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

    domain = distribution.get("domain", {})
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

    restrictions = access_bundle.get("restrictions", {})
    if restrictions.get("testPackageVersionsOnly") is not True:
        return _rejected("PUBLIC_EVALUATION_TEST_VERSION_RESTRICTION_MISSING")
    if restrictions.get("productionAuthorization") is not False:
        return _rejected("PUBLIC_EVALUATION_PRODUCTION_AUTHORIZATION_FORBIDDEN")
    if restrictions.get("transferable") is not False:
        return _rejected("PUBLIC_EVALUATION_TRANSFER_FORBIDDEN")
    if restrictions.get("commercialPurchaseEvidence") is not False:
        return _rejected("PUBLIC_EVALUATION_COMMERCIAL_EVIDENCE_CLAIM_FORBIDDEN")

    activation = access_bundle.get("activationContract", {})
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
    if activation.get("onMismatch") != "REJECT_AND_KEEP_PREVIOUS_VALID_BINDING":
        return _rejected("PUBLIC_EVALUATION_ACTIVATION_MISMATCH_ROUTE_INVALID")

    subject_ref = str(access_bundle.get("subjectRef", ""))
    verification_context = access_bundle.get("verificationContext", {})
    if not subject_ref or verification_context.get("subjectRef") != subject_ref:
        return _rejected("PUBLIC_EVALUATION_SUBJECT_CONTEXT_MISMATCH")

    modules = distribution.get("embeddedDomainModules", {})
    factory = modules.get("factory", {})
    operating_model = modules.get("operatingModel", {})
    expected_modules = {_module_identity(factory), _module_identity(operating_model)}
    if any(not package_id or not version for package_id, version in expected_modules):
        return _rejected("PUBLIC_EVALUATION_EMBEDDED_MODULE_IDENTITY_INVALID")
    if len(expected_modules) != 2:
        return _rejected("PUBLIC_EVALUATION_EMBEDDED_MODULE_SET_INVALID")

    for module in (factory, operating_model):
        commercial = module.get("commercial", {})
        if commercial.get("accessMode") != "PAID_ENTITLEMENT_REQUIRED":
            return _rejected("PUBLIC_EVALUATION_MODULE_NOT_PAID_MODE")
        if commercial.get("entitlementRequired") is not True:
            return _rejected("PUBLIC_EVALUATION_MODULE_ENTITLEMENT_FLAG_INVALID")

    entitlements: Sequence[Mapping[str, Any]] = access_bundle.get("entitlements", [])
    if not isinstance(entitlements, list) or len(entitlements) != 2:
        return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_SET_INVALID")
    grant_identities = {_grant_identity(entitlement) for entitlement in entitlements}
    if grant_identities != expected_modules:
        return _rejected(
            "PUBLIC_EVALUATION_GRANT_SET_MISMATCH",
            expectedGrants=sorted(expected_modules),
            receivedGrants=sorted(grant_identities),
        )

    for entitlement in entitlements:
        subject = entitlement.get("subject", {})
        if subject.get("subjectRef") != subject_ref:
            return _rejected("PUBLIC_EVALUATION_ENTITLEMENT_SUBJECT_MISMATCH")

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
    if package_result.get("outcome") != "PACKAGE_ACCESS_RESOLVED":
        return _rejected(
            "PUBLIC_EVALUATION_PACKAGE_ACCESS_NOT_RESOLVED",
            packageAccessOutcome=package_result.get("outcome"),
            packageAccess=package_result,
        )

    return {
        "outcome": "PUBLIC_EVALUATION_ACCESS_RESOLVED",
        "domainId": domain.get("domainId"),
        "creationType": domain.get("creationType"),
        "distributionId": distribution.get("distributionId"),
        "accessFile": expected_access_file,
        "subjectRef": subject_ref,
        "productionAuthorization": False,
        "packageAccess": package_result,
        "nextOperation": PUBLIC_EVALUATION_NEXT_OPERATION,
    }
