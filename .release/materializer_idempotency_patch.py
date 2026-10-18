#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / ".release/integrate_v014_rc2.py"
text = path.read_text(encoding="utf-8")
old = '''def _patch_validator(module_map: Mapping[str, Any]) -> None:
    relative = "tools/validate_safor.py"
    text = path(relative).read_text(encoding="utf-8")
'''
new = '''def _patch_validator(module_map: Mapping[str, Any]) -> None:
    relative = "tools/validate_safor.py"
    text = path(relative).read_text(encoding="utf-8")
    # A prior integration phase may already have installed the v0.14-native
    # validator. In that case the old rc.9 regex migration is intentionally
    # skipped; the validator itself is then exercised after bundle materialization.
    if 'VERSION = "0.14.0-rc.2"' in text and 'v0.14 package catalog invalid' in text:
        return
'''
if old not in text:
    raise SystemExit("_patch_validator insertion point not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
