# -*- coding: utf-8 -*-
"""Astra post-B2C-B correction gate -- Test 5: runtime identity + failure
matrix (F6 + F7). Directly exercises runtime.py's corrected is_canonical()
(the pre-correction version was a tautology -- see runtime.py's own
comment) and assert_expected_origin(). Missing/stale/corrupt/unsupported/
resource-refused/recovery/pointer-disagreement cases are NOT duplicated
here -- they are already exhaustively covered by test_b2c_correction_
b2a_equiv_offline.py's selection.2-8/identity.3-4 (re-run under this same
corrected package, Section 13) and by test_b2c_correction_test1_
bounded_io.py's caseD (unsupported format). This file cites those rather
than re-deriving them, and adds the two NEW, directly-provable identity
scenarios the F6 fix specifically targets (which the pre-correction
tautological check could never have caught), plus the main-thread policy
check.

Honest scope note on "stale/frozen package preloaded first": under
STANDARD Python `import` semantics, if a stale package at an earlier
sys.path location is imported first under the exact same dotted name,
Python's import machinery returns the CACHED stale module directly --
the corrected package's own code never even runs in that case, so no
in-module check (this one included) can detect or prevent it; the only
real defense is sys.path/deployment hygiene at the bootstrap layer,
outside this module's power. What IS provable, and IS proven below, is
the scenario the actual F6 bug allowed to go undetected: something else
taking over `sys.modules[canonical_name]` AFTER this module's own
initialization -- e.g. a non-standard loader (imp.load_source/execfile-
style) re-registering a different object under the same name later in
the same process.
"""
import sys
import types

CORRECTION_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"

for p in (CORRECTION_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

# runtime.py's own canonical-name self-check requires the exact dotted
# name "sfm_master_authority.runtime" -- import from the correctly-named
# staged copy (candidate_b2c_correction/sfm_master_authority/), not the
# differently-named sfm_master_authority_productionized/ directory this
# file's other imports use elsewhere.
import sfm_master_authority.runtime as authority_runtime  # noqa: E402
from sfm_master_authority import errors  # noqa: E402

authority_runtime._reset_for_test_only()

# ===========================================================================
# Case 1: normal canonical import is recognized as canonical (sanity).
# ===========================================================================
check("case1.0 is_canonical() is True for a normal, standard import",
      authority_runtime.is_canonical() is True)
b1 = authority_runtime.get_broker(is_main_thread_fn=lambda: True)
check("case1.1 get_broker() succeeds when canonical", b1 is not None)

# ===========================================================================
# Case 2 (Astra F6's exact fix target): something else takes over
# sys.modules[canonical_name] AFTER this module's own initialization.
# The pre-correction is_canonical() (`sys.modules.get(NAME) is
# sys.modules.get(__name__)`) could NEVER detect this -- both lookups
# used the SAME key (since __name__ == NAME is already guaranteed by the
# top-of-file check), making it compare sys.modules[NAME] to itself, an
# unconditional tautology. The corrected version compares against
# `_this_module`, a reference CAPTURED once at this module's own
# initialization -- genuinely detecting the replacement.
# ===========================================================================
_real_module = sys.modules[authority_runtime.__name__]
_fake_replacement = types.ModuleType(authority_runtime.__name__)
sys.modules[authority_runtime.__name__] = _fake_replacement
try:
    check("case2.0 is_canonical() correctly detects a LATER hijack of sys.modules[name] "
          "(the exact pre-correction tautology this replaces)",
          authority_runtime.is_canonical() is False)
    authority_runtime._reset_for_test_only()
    try:
        authority_runtime.get_broker(is_main_thread_fn=lambda: True)
        check("case2.1 get_broker() refuses to hand out a broker while sys.modules[name] "
              "points at a different object", False, "did not raise")
    except errors.BrokerIdentityConflict:
        check("case2.1 get_broker() refuses to hand out a broker while sys.modules[name] "
              "points at a different object", True)
finally:
    sys.modules[authority_runtime.__name__] = _real_module
    authority_runtime._reset_for_test_only()

check("case2.2 restoring the real module object makes is_canonical() True again",
      authority_runtime.is_canonical() is True)

# ===========================================================================
# Case 3: assert_expected_origin -- real bootstrap code pinning where the
# package should be loaded from.
# ===========================================================================
actual_dir = authority_runtime.get_actual_origin_dir()
check("case3.0 get_actual_origin_dir() returns the real on-disk directory",
      actual_dir.lower().endswith("sfm_master_authority"), actual_dir)
try:
    authority_runtime.assert_expected_origin(actual_dir)
    check("case3.1 assert_expected_origin succeeds when given the TRUE origin", True)
except errors.BrokerIdentityConflict:
    check("case3.1 assert_expected_origin succeeds when given the TRUE origin", False)

try:
    authority_runtime.assert_expected_origin(r"C:\some\other\stale\location")
    check("case3.2 assert_expected_origin refuses a WRONG expected origin", False, "did not raise")
except errors.BrokerIdentityConflict:
    check("case3.2 assert_expected_origin refuses a WRONG expected origin", True)

# ===========================================================================
# Case 4: wrong thread -- main-thread policy enforced at construction.
# ===========================================================================
authority_runtime._reset_for_test_only()
try:
    authority_runtime.get_broker(is_main_thread_fn=lambda: False)
    check("case4.0 get_broker() refuses construction off the main thread", False, "did not raise")
except errors.BrokerInitializationFailed:
    check("case4.0 get_broker() refuses construction off the main thread", True)
check("case4.1 a failed (wrong-thread) construction leaves state FAILED, not silently READY",
      authority_runtime.get_state() == authority_runtime.STATE_FAILED)
authority_runtime._reset_for_test_only()

# ===========================================================================
# Case 5: API/build identity mismatch (already-existing mechanism,
# re-confirmed here alongside the new checks for a complete picture).
# ===========================================================================
authority_runtime.get_broker(is_main_thread_fn=lambda: True)
try:
    authority_runtime.get_broker(expected_api_version="wrong-version-9.9.9")
    check("case5.0 incompatible expected API version is refused", False, "did not raise")
except errors.BrokerIdentityConflict:
    check("case5.0 incompatible expected API version is refused", True)
authority_runtime._reset_for_test_only()

print(
    "\n[NOTE] 'alternate import created no broker side effect' and the full failure "
    "matrix (missing/stale/corrupt/unsupported-format/resource-refused/corrupt-local-"
    "recovery/pointer-disagreement) are exhaustively covered by test_b2c_correction_"
    "b2a_equiv_offline.py (identity.4/4b, selection.2-8, re-run this session against "
    "this SAME corrected package) and test_b2c_correction_test1_bounded_io.py's caseD "
    "-- not duplicated here."
)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
