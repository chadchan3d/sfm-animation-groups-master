# -*- coding: utf-8 -*-
"""Package-Boundary Targeted Correction, Section 3/4: decisive
build-identity regression.

Independent-audit finding: `RUNTIME_BUILD_ID` was left at
`"b2c-correction6-parsedeferred-floor-targeted-2026-09-18"` -- the
identity of the PRE-package-boundary-correction build -- even though
the intervening package-boundary correction commits (`d039c92`,
`1abe914`) added real, caller-relevant behavior changes (leased-orphan
generation revocation, the `acquire_generation()` call-contract repair,
the bundled-dependency resolution change, the canonical-module-name
repair). `runtime.py`'s own docstring requires bumping this string
"whenever a build adds or changes an API surface that callers depend
on, even if RUNTIME_API_VERSION does not change" -- this had not been
done, silently defeating the stale/wrong-package protection the build
ID exists to provide.

Fix: `RUNTIME_BUILD_ID` bumped to `"package-boundary-corrected-2026-09-22"`.
`RUNTIME_API_VERSION` intentionally left UNCHANGED (`"1.0.0-b2a"`) --
source inspection found no reason the broad API generation itself must
change; the independent audit did not require an API-version bump
either.

This test is independent of sidecar I/O -- it exercises only `runtime.
py`'s own module-level state machine (`get_broker`/`_reset_for_test_
only`), never a compiled sidecar or provider.

Never launches SFM. Read-only with respect to the frozen production
file and the canonical Master (neither is referenced by this file).
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
TOOLS_DIR = os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools")
for _p in (os.path.abspath(CORRECTION6_ROOT), os.path.abspath(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

from sfm_master_authority_productionized import runtime as rt  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

NEW_BUILD_ID = "package-boundary-corrected-2026-09-22"
OLD_BUILD_ID = "b2c-correction6-parsedeferred-floor-targeted-2026-09-18"
EXPECTED_API_VERSION = "1.0.0-b2a"

# --- 1. Current runtime reports the new build ID. ---
check("build_id.constant_is_new_value RUNTIME_BUILD_ID is the new package-boundary identity",
      rt.RUNTIME_BUILD_ID == NEW_BUILD_ID, rt.RUNTIME_BUILD_ID)
check("build_id.constant_is_not_old_value RUNTIME_BUILD_ID is no longer the stale "
      "pre-package-boundary identity", rt.RUNTIME_BUILD_ID != OLD_BUILD_ID)
check("build_id.getter_matches_constant get_runtime_build_id() returns the same value",
      rt.get_runtime_build_id() == NEW_BUILD_ID)

# --- 2. get_broker(expected_build_id=<new-id>) accepts it. ---
rt._reset_for_test_only()
try:
    broker_new = rt.get_broker(expected_build_id=NEW_BUILD_ID, is_main_thread_fn=lambda: True)
    check("build_id.new_id_accepted get_broker(expected_build_id=NEW_BUILD_ID) returns a real, "
          "READY broker", broker_new is not None and rt.get_state() == "READY")
except Exception as exc:
    check("build_id.new_id_accepted get_broker(expected_build_id=NEW_BUILD_ID) returns a real, "
          "READY broker", False, exc)

# --- 3. get_broker(expected_build_id=<OLD id>) rejects it with the
#        expected broker identity conflict -- this is the actual
#        stale/wrong-package protection being restored. ---
rt._reset_for_test_only()
try:
    rt.get_broker(expected_build_id=OLD_BUILD_ID, is_main_thread_fn=lambda: True)
    check("build_id.old_id_rejected get_broker(expected_build_id=OLD_BUILD_ID) raises "
          "BrokerIdentityConflict (a caller still pinned to the pre-package-boundary build is "
          "correctly refused a broker from this build)", False, "did not raise at all")
except errors.BrokerIdentityConflict as exc:
    check("build_id.old_id_rejected get_broker(expected_build_id=OLD_BUILD_ID) raises "
          "BrokerIdentityConflict (a caller still pinned to the pre-package-boundary build is "
          "correctly refused a broker from this build)", True)
    check("build_id.old_id_rejection_names_both_ids the rejection message names both the "
          "caller's expected (old) build id and the actually-loaded (new) build id",
          OLD_BUILD_ID in str(exc) and NEW_BUILD_ID in str(exc), str(exc))
except Exception as exc:
    check("build_id.old_id_rejected get_broker(expected_build_id=OLD_BUILD_ID) raises "
          "BrokerIdentityConflict", False, ("wrong exception type", type(exc).__name__, exc))

# --- 4. Broad RUNTIME_API_VERSION behavior remains unchanged (not
#        bumped -- intentional, since no broad API generation change
#        was made). ---
check("api_version.unchanged RUNTIME_API_VERSION was intentionally NOT bumped by this "
      "correction", rt.RUNTIME_API_VERSION == EXPECTED_API_VERSION, rt.RUNTIME_API_VERSION)
rt._reset_for_test_only()
try:
    broker_api = rt.get_broker(expected_api_version=EXPECTED_API_VERSION, is_main_thread_fn=lambda: True)
    check("api_version.matching_expectation_still_accepted a caller still pinned to the "
          "unchanged RUNTIME_API_VERSION is accepted exactly as before",
          broker_api is not None and rt.get_state() == "READY")
except Exception as exc:
    check("api_version.matching_expectation_still_accepted a caller still pinned to the "
          "unchanged RUNTIME_API_VERSION is accepted exactly as before", False, exc)

rt._reset_for_test_only()
try:
    rt.get_broker(expected_api_version="9.9.9-not-real", is_main_thread_fn=lambda: True)
    check("api_version.mismatch_still_rejected a caller pinned to a WRONG API version is still "
          "rejected (unrelated to the build-id fix, confirms no regression)", False, "did not raise")
except errors.BrokerIdentityConflict:
    check("api_version.mismatch_still_rejected a caller pinned to a WRONG API version is still "
          "rejected (unrelated to the build-id fix, confirms no regression)", True)

rt._reset_for_test_only()

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
