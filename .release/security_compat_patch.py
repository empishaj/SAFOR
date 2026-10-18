#!/usr/bin/env python3
import json
import runpy
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / "runtime/master_orchestration.py"
text = path.read_text(encoding="utf-8")
old = "'freshness': {'status': freshness_status, 'observedAt': observed_at, 'staleAfter': stale_after, 'staleReasons': reasons, 'providerReadbackVerified': provider_readback_verified, 'sourceRevisionsConsistent': source_revisions_consistent}"
new = "'freshness': {'status': freshness_status, 'observedAt': observed_at, 'staleAfter': stale_after, 'staleReason': reasons[0] if reasons else None, 'staleReasons': reasons, 'providerReadbackVerified': provider_readback_verified, 'sourceRevisionsConsistent': source_revisions_consistent}"
if old not in text:
    raise SystemExit("freshness projection patch target not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
runpy.run_path(str(root / ".release/traceability_prereqs.py"), run_name="__main__")
validator = (root / "tools/validate_safor.py").read_text(encoding="utf-8")
if 'VERSION = "0.14.0-rc.2"' not in validator or 'v0.14 package catalog invalid' not in validator:
    runpy.run_path(str(root / ".release/bundle_v014_patch.py"), run_name="__main__")
communication_path = root / "v0.14.0/agent-communication-model.json"
communication = json.loads(communication_path.read_text(encoding="utf-8"))
communication["owner"] = "SAFOR_PLATFORM"
for forbidden in ("MENU", "FACTORY_PRESENTATION_OVERRIDE", "OPERATING_MODEL_PRESENTATION_OVERRIDE"):
    if forbidden not in communication["forbiddenContent"]:
        communication["forbiddenContent"].append(forbidden)
communication["rendering"] = {"singleLine": True, "menuForbidden": True, "substantiveContentStoredInGit": True}
communication_path.write_text(json.dumps(communication, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
runpy.run_path(str(root / ".release/materializer_idempotency_patch.py"), run_name="__main__")
