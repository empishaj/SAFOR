# KWP-02/03/04 integration failure

```text
SAFOR 0.14.0-rc.2 integration phase security: prepared
Traceback (most recent call last):
  File "/home/runner/work/SAFOR/SAFOR/.release/security_compat_patch.py", line 14, in <module>
    runpy.run_path(str(root / ".release/bundle_v014_patch.py"), run_name="__main__")
  File "<frozen runpy>", line 287, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/SAFOR/SAFOR/.release/bundle_v014_patch.py", line 27, in <module>
    replace(
  File "/home/runner/work/SAFOR/SAFOR/.release/bundle_v014_patch.py", line 15, in replace
    raise RuntimeError(f"Expected text not found in {relative}: {old!r}")
RuntimeError: Expected text not found in runtime/bootstrap_policy.py: 'entitlement.get("schemaVersion") != "0.13.0"'
```
