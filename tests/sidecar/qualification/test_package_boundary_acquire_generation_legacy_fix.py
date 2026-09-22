# -*- coding: utf-8 -*-
"""Package-Boundary Correction: legacy `Broker.acquire_generation()`
disposition (Astra-reproduced defect C).

Reproduced root cause (confirmed by direct reading, not assumed):
`Broker._acquire_generation_once` called `selection.select_sidecar_
candidate(..., ledger=self._ledger)` -- `ledger` has never been an
accepted keyword of that function (its real resource-accounting
parameter is `aggregate_existing_retained_bytes`, an int, not a ledger
object -- confirmed by reading `selection.py`'s real signature, and by
confirming `cohort.py`'s `_open_provider_once`, the QUALIFIED
Normalizer acquisition route's own call, has always used the correct
parameter). Every real call to `acquire_generation()` therefore raised
`TypeError: select_sidecar_candidate() got an unexpected keyword
argument 'ledger'` unconditionally.

Disposition (per the governing prompt's "minimum sensible disposition"
instruction): `acquire_generation()` is a real, non-underscore, public,
independently-documented `Broker` method -- by that criterion it counts
as part of the supported surface, so it is FIXED here (a one-line
change mirroring the exact parameter the already-qualified path already
uses), not deprecated/removed. This is deliberately the smallest
possible fix: no redesign of acquisition around this legacy method, no
change to its own contract ("identity only, no retained provider, no
mutation" -- unchanged). Confirmed separately (see the correction
report) that the qualified Normalizer acquisition path (`acquire_or_
reuse_views`/`acquire_cohort`/`Cohort._open_provider_once`) never calls
this method at all -- fixing it is therefore risk-free with respect to
the already-qualified B2C-C evidence.

Never launches SFM. Read-only with respect to the frozen production
file and the canonical Master (this test uses only synthetic fixtures).
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

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import selection as selection_mod  # noqa: E402
import inspect  # noqa: E402

# --- 1. Static proof the bad keyword is gone from the real call site. -
_source = inspect.getsource(broker_mod.Broker._acquire_generation_once)
check("static.no_bad_ledger_kwarg the real _acquire_generation_once source no longer passes "
      "ledger= to select_sidecar_candidate", "ledger=self._ledger" not in _source)
check("static.uses_real_parameter the fix uses the SAME real parameter the qualified path "
      "(cohort.py) already uses", "aggregate_existing_retained_bytes=self._ledger.total_retained_bytes()"
      in _source)

# --- 2. Confirm the real select_sidecar_candidate signature genuinely
#        has no `ledger` parameter (so the OLD call really would have
#        raised, proving this is a real fix, not a no-op). ---
try:
    _param_names = list(inspect.signature(selection_mod.select_sidecar_candidate).parameters.keys())
except AttributeError:  # Python 2.7 has no inspect.signature
    _param_names = inspect.getargspec(selection_mod.select_sidecar_candidate).args
check("static.selection_never_had_ledger_param select_sidecar_candidate's real signature has "
      "no 'ledger' parameter at all (confirms the original bug was real, not hypothetical)",
      "ledger" not in _param_names, sorted(_param_names))
check("static.selection_has_aggregate_param select_sidecar_candidate's real signature DOES "
      "accept 'aggregate_existing_retained_bytes' (the parameter the fix now uses)",
      "aggregate_existing_retained_bytes" in _param_names)

# --- 3. Direct regression: a real call to acquire_generation() against
#        a nonexistent shipped_root must fail with a real, EXPECTED
#        SidecarMissing-family error -- NEVER a TypeError from a bad
#        call contract. This is the exact call shape a caller would
#        make; the fixture path deliberately does not exist, so we are
#        only proving the call reaches real selection logic and fails
#        for a REAL reason, not a broken Python call. ---
b = broker_mod.Broker(api_version="package-boundary-acquire-generation-fix-test")
_nonexistent_master = os.path.join(_THIS_DIR, "_package_boundary_test_nonexistent_master.txt")
with open(_nonexistent_master, "wb") as f:
    f.write(b"\"groupFile\"\n{\n}\n")
try:
    _nonexistent_shipped_root = os.path.join(_THIS_DIR, "_package_boundary_test_nonexistent_shipped_root")
    try:
        b.acquire_generation(_nonexistent_master, shipped_root=_nonexistent_shipped_root)
        check("regression.raises_real_selection_error acquire_generation() call reaches real "
              "selection logic and raises a real SidecarMissing-family error (not TypeError)",
              False, "did not raise at all")
    except TypeError as exc:
        check("regression.raises_real_selection_error acquire_generation() call reaches real "
              "selection logic and raises a real SidecarMissing-family error (not TypeError)",
              False, "still raised TypeError: %s" % exc)
    except Exception as exc:
        check("regression.raises_real_selection_error acquire_generation() call reaches real "
              "selection logic and raises a real SidecarMissing-family error (not TypeError)",
              type(exc).__name__ in ("SidecarMissing", "RebuildRequired"), (type(exc).__name__, str(exc)))
finally:
    if os.path.isfile(_nonexistent_master):
        os.remove(_nonexistent_master)

# --- 4. Confirm the qualified Normalizer acquisition path never calls
#        this method at all (so fixing/not-fixing it carries zero risk
#        either way to already-qualified B2C-C evidence). ---
_adapter_path = os.path.join(CORRECTION6_ROOT, "sfm_master_authority_productionized", "normalizer_compat_adapter.py")
with open(_adapter_path, "rb") as f:
    _adapter_src = f.read().decode("utf-8")
check("scope.adapter_never_calls_acquire_generation normalizer_compat_adapter.py never "
      "references acquire_generation at all", "acquire_generation" not in _adapter_src)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
