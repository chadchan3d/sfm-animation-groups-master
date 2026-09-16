# -*- coding: utf-8 -*-
"""R3-B2F Section 5: offline pre-admission validation of every fixture --
production-reader parity was already proven during generation
(compiler.self_validate_from_bytes); this pass ADDITIONALLY validates
every fixture through the FINAL R3-A2B validator/provider contract
(bounded read + Section 20 A-J structural validation), using a generous
explicit runtime_cap_bytes (each artifact's own exact size) so this pass
tests pure FORMAT/STRUCTURAL validity, never conflated with the SEPARATE,
later runtime admission-cap question (Sections 10-12, tested only inside
real SFM).
"""
import hashlib
import json
import sys

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import mutex_publisher

# mutex_publisher.validate_with_final_r3a2b_contract() calls open_path()
# WITHOUT specifying runtime_cap_bytes, so it uses the 16 MiB EXPERIMENTAL
# DEFAULT -- which would reject several of these >16 MiB fixtures for the
# wrong reason (this pass tests pure structural validity, never conflated
# with the SEPARATE, later admission-cap question). Load the same FINAL
# R3-A2B modules directly instead, with an explicit generous cap.
mutex_publisher._ensure_final_r3a2b_loaded()
_provider_mod = mutex_publisher._r3a2b_provider_module
_GENEROUS_CAP_BYTES = 512 * 1024 * 1024  # the format's own absolute ceiling -- structural-validity test only

FIXROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2f\fixtures"

with open(FIXROOT + r"\fixture_manifest.json") as f:
    manifest = json.load(f)

results = []


def check(name, condition, detail=None):
    results.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


for m in manifest:
    with open(m["artifact_path"], "rb") as f:
        real_bytes = f.read()
    actual_sha = hashlib.sha256(real_bytes).hexdigest()
    check("%s: artifact bytes match manifest SHA-256" % m["name"], actual_sha == m["artifact_sha256"])

    try:
        provider = _provider_mod.BoundedProvider.open_path(
            m["artifact_path"], m["source_sha256"], runtime_cap_bytes=_GENEROUS_CAP_BYTES,
        )
        provider.close()
        ok = True
        detail = None
    except Exception as exc:
        ok = False
        detail = "%s: %s" % (type(exc).__name__, exc)
    check("%s: FINAL R3-A2B contract accepts this fixture (generous cap, structural validity only)" % m["name"], ok, detail)

print()
failed = [n for n, ok in results if not ok]
print("RESULT: %d/%d %s" % (len(results) - len(failed), len(results), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
if failed:
    sys.exit(1)
