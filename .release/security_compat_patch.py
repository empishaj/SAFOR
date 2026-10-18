#!/usr/bin/env python3
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
runpy.run_path(str(root / ".release/bundle_v014_patch.py"), run_name="__main__")
runpy.run_path(str(root / ".release/materializer_idempotency_patch.py"), run_name="__main__")
