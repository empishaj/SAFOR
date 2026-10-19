#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> None:
    errors: list[str] = []

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    facts = load_json("RELEASE-FACTS.json")
    manifest = load_json("RELEASE-MANIFEST.json")
    trace = load_json("docs/master-subagent-orchestration/requirements-traceability-v0.14.0.json")
    profiles = load_json("v0.14.0/domain-framework-profiles.json")
    saas_access = load_json("SAFOR-TEST-ACCESS-SAAS.json")
    book_access = load_json("SAFOR-TEST-ACCESS-BOOK-CREATION.json")

    if facts.get("targetVersion") != version:
        fail(errors, "RELEASE-FACTS targetVersion differs from VERSION")
    if manifest.get("version") != version:
        fail(errors, "RELEASE-MANIFEST version differs from VERSION")
    if trace.get("releaseTarget") != version:
        fail(errors, "Traceability releaseTarget differs from VERSION")
    artifact_state = facts.get("releaseArtifacts", {}).get("state")
    if artifact_state == "PENDING_MATERIALIZATION":
        if facts.get("status") != "PENDING_MATERIALIZATION":
            fail(errors, "Pending release facts status mismatch")
        if manifest.get("releaseArtifactsState") != "PENDING_RELEASE_MATERIALIZATION":
            fail(errors, "Pending manifest artifact state mismatch")
        if trace.get("status") != "RC6_PENDING_MATERIALIZATION_AND_EXACT_HEAD_VALIDATION":
            fail(errors, "Pending rc.6 traceability status mismatch")
    elif artifact_state == "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
        if facts.get("status") != "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
            fail(errors, "Release facts PASS status mismatch")
        if manifest.get("releaseArtifactsState") != "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
            fail(errors, "Manifest does not declare materialized automated validation PASS")
        if "PENDING" in str(trace.get("status", "")):
            fail(errors, "PASS release traceability still declares a pending release phase")
    else:
        fail(errors, f"Unsupported release artifact state: {artifact_state}")
    if manifest.get("auditRemediation", {}).get("rc5InboxPull", {}).get("status") != "MATERIALIZED_AND_AUTOMATED_VALIDATION_PASS":
        fail(errors, "rc.5 inbox-pull remediation status is not materialized/pass")

    by_profile = {p["id"]: p for p in profiles.get("profiles", [])}
    facts_defaults = facts.get("domainDefaults", {})
    for profile_id, profile in by_profile.items():
        expected = {
            "creationType": profile["creationType"],
            "accessMode": profile["accessMode"],
            "factoryPackageId": profile["defaultFactory"]["packageId"],
            "factoryVersion": profile["defaultFactory"]["version"],
            "operatingModelPackageId": profile["defaultOperatingModel"]["packageId"],
            "operatingModelVersion": profile["defaultOperatingModel"]["version"],
            "publicationMode": profile["publicationMode"],
        }
        if facts_defaults.get(profile_id) != expected:
            fail(errors, f"RELEASE-FACTS domain default mismatch: {profile_id}")

    def grants(bundle: dict) -> dict[str, str]:
        return {
            item["grant"]["packageId"]: item["grant"]["versionRange"]
            for item in bundle.get("entitlements", [])
        }

    for profile_id, bundle in (("SAAS", saas_access), ("BOOK_CREATION", book_access)):
        profile = by_profile[profile_id]
        expected_grants = {
            profile["defaultFactory"]["packageId"]: profile["defaultFactory"]["version"],
            profile["defaultOperatingModel"]["packageId"]: profile["defaultOperatingModel"]["version"],
        }
        if grants(bundle) != expected_grants:
            fail(errors, f"Test-access grant mismatch: {profile_id}")
        if bundle.get("creationType") != profile["creationType"]:
            fail(errors, f"Test-access creationType mismatch: {profile_id}")
        if bundle.get("restrictions", {}).get("productionAuthorization") is not False:
            fail(errors, f"Public test access must not grant production authorization: {profile_id}")

    active_docs = [
        "README.md",
        "START-HIER.md",
        "QUICKSTART.md",
        "SUPPORT.md",
        "SECURITY.md",
        "LICENSE-DECISION.md",
        "ARCHITECTURE.md",
        "ACCEPTANCE-TESTS.md",
        "AGENT-WORKSPACE.md",
        "AGENT-JOB-CONTRACT.md",
        "MASTER-SUBAGENT-ORCHESTRATION.md",
        "MULTI-AGENT-SCHEDULER.md",
        "HUMAN-NOTICE-CONFORMANCE.md",
        "HUMAN-COGNITIVE-LOAD.md",
        "PRODUCT-READINESS.md",
        "RELEASE-CHECKLIST.md",
    ]
    stale_tokens = [
        "SAFOR-FRAMEWORK-v0.14.0-rc.3.json",
        "SAFOR v0.14.0-rc.3",
        "SAFOR 0.14.0-rc.3",
        "safor.factory.website-delivery@1.1.0",
        "safor.om.website-team@1.1.0",
        "safor.factory.software-delivery@1.7.0-test.1",
        "safor.om.saas-engineering@1.7.0-test.1",
        "safor.factory.book-production@1.0.0-test.1",
        "safor.om.book-authoring@1.0.0-test.1",
    ]
    obsolete_chat_phrases = [
        "same bound agent chat",
        "BOUND chat binding",
        "identity status and chat binding",
        "Identity und Chat Binding",
        "- Chat Binding;",
        "unsicherer Chatbindung",
    ]
    for path in active_docs:
        text = (ROOT / path).read_text(encoding="utf-8")
        for token in stale_tokens:
            if token in text:
                fail(errors, f"Stale active documentation token in {path}: {token}")
        for phrase in obsolete_chat_phrases:
            if phrase in text:
                fail(errors, f"Obsolete host-chat-binding semantics in {path}: {phrase}")

    for path in (
        "HUMAN-NOTICE-IMPLEMENTATION-PLAN.md",
        "docs/master-subagent-orchestration/IMPLEMENTATION-PLAN-v0.14.0.md",
    ):
        text = (ROOT / path).read_text(encoding="utf-8")
        if "HISTORISCHES PLANUNGSARTEFAKT" not in text:
            fail(errors, f"Historical plan lacks explicit historical banner: {path}")

    req = {item["id"]: item for item in trace.get("requirements", [])}
    if "Chatbindung" in req.get("REQ-008", {}).get("statement", ""):
        fail(errors, "REQ-008 still describes old chat-binding semantics")
    req11_acceptance = " ".join(req.get("REQ-011", {}).get("acceptance", []))
    if "Chat Binding Status" in req11_acceptance:
        fail(errors, "REQ-011 still requires Chat Binding Status")
    req24_acceptance = " ".join(req.get("REQ-024", {}).get("acceptance", []))
    if "READY" not in req24_acceptance:
        fail(errors, "REQ-024 does not describe all current minimal chat statuses")

    handbook = (ROOT / "START-HIER.md").read_text(encoding="utf-8")
    handbook_words = re.findall(r"\b[\wÄÖÜäöüß-]+\b", handbook, flags=re.UNICODE)
    if len(handbook_words) > 650:
        fail(errors, f"Non-tech handbook is too long: {len(handbook_words)} words > 650")
    required_headings = [
        "## 1. Wähle, was du machen willst",
        "## 2. Lade nur die passenden Dateien hoch",
        "## 3. Sende diesen Starttext",
        "## 4. Beantworte nur die Fragen des MASTER",
        "## 5. Wenn SAFOR einen Subagenten braucht",
        "## 6. Wenn SAFOR stoppt",
        "## 7. Diese Dinge musst du nicht tun",
    ]
    for heading in required_headings:
        if heading not in handbook:
            fail(errors, f"Non-tech handbook missing required step: {heading}")
    for filename in (
        "SAFOR-FRAMEWORK-WEBSITE.json",
        "SAFOR-FRAMEWORK-SAAS.json",
        "SAFOR-TEST-ACCESS-SAAS.json",
        "SAFOR-FRAMEWORK-BOOK-CREATION.json",
        "SAFOR-TEST-ACCESS-BOOK-CREATION.json",
    ):
        if filename not in handbook:
            fail(errors, f"Non-tech handbook missing entry file: {filename}")
    for jargon in (
        "identityRevision",
        "dispatchRevision",
        "blobSha",
        "schemaVersion",
        "compare-and-swap",
        "providerReadback",
        "chatBindingId",
        "sessionId",
        "predicate",
        "digest",
    ):
        if jargon.lower() in handbook.lower():
            fail(errors, f"Non-tech handbook exposes internal jargon: {jargon}")
    if "MASTER schreibt den Job in die INBOX. Du schreibst nur GO. Der Agent holt den Job selbst ab." not in handbook:
        fail(errors, "Non-tech handbook lacks the canonical agent handoff mnemonic")

    version_docs = (
        ("PRODUCT-READINESS.md",)
        if artifact_state == "PENDING_MATERIALIZATION"
        else ("README.md", "START-HIER.md", "SUPPORT.md", "HUMAN-NOTICE-CONFORMANCE.md", "PRODUCT-READINESS.md")
    )
    for path in version_docs:
        text = (ROOT / path).read_text(encoding="utf-8")
        if version not in text:
            fail(errors, f"Current release version missing from {path}")

    if errors:
        print("SAFOR content consistency: FAIL")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    print(
        "SAFOR content consistency: PASS "
        f"(version={version}; activeDocs={len(active_docs)}; handbookWords={len(handbook_words)})"
    )


if __name__ == "__main__":
    main()
