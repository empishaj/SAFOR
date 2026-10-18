#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("v0.13.0/chat-execution-model.json", "v0.14.0/chat-execution-model.json"),
    ("v0.13.0/composable-package-model.json", "v0.14.0/composable-package-model.json"),
    ("v0.13.0/domain-framework-profiles.json", "v0.14.0/domain-framework-profiles.json"),
)

for source, target in CASES:
    value = json.loads((ROOT / source).read_text(encoding="utf-8"))
    value["schemaVersion"] = "0.14.0"
    destination = ROOT / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
