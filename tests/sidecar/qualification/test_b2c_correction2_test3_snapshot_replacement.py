# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 3: valid snapshot replacement (F5).

A genuinely valid artifact A is open (preflight header+directory already
read from A) when the SAME on-disk file is REWRITTEN IN PLACE (via a
SEPARATE file handle, before the module's own single full-bounded-read
call) to become a different, genuinely valid artifact B, whose REAL
cumulative estimate for the SAME requested fold set exceeds the retained
gate. PASS: the refusal comes from resource admission against B's ACTUAL
final bytes (not A's preliminary shape), strictly BEFORE the frozen
validator/projection expansion ever runs, and exactly ONE "full_bounded_
read" instrumentation record exists (never a second full disk read to
"double check")."""
import json
import sys

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT = CORRECTION2_ROOT + r"\fixtures"

for p in (CORRECTION2_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import resource_preflight  # noqa: E402
from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(FIXROOT + r"\manifest.json") as f:
    MANIFEST = json.load(f)

A_PATH = MANIFEST["boundary_below_19999"]["artifact_path"]  # small, valid, requested folds absent -> trivial cost
B_PATH = MANIFEST["astra_two_large_families"]["artifact_path"]  # valid, requested folds present & huge

with open(A_PATH, "rb") as f:
    A_BYTES = f.read()
with open(B_PATH, "rb") as f:
    B_BYTES = f.read()

# The scratch path this test actually opens -- starts as an exact copy of A.
import os
import shutil
import tempfile
SCRATCH = tempfile.mkdtemp(prefix="b2c_correction2_test3_")
SWAP_PATH = os.path.join(SCRATCH, "swap_target.sfmsidecar")
shutil.copy(A_PATH, SWAP_PATH)

# --- decode-call instrumentation (same technique as Test 2) ---
sidecar_contract.ensure_loaded()
_provider_mod = sidecar_contract._provider_module
_orig_open_from_buf = _provider_mod.BoundedProvider._open_from_buf
_decode_call_count = [0]


@classmethod
def _counting_open_from_buf(cls, *a, **kw):
    _decode_call_count[0] += 1
    return _orig_open_from_buf.__func__(cls, *a, **kw)


_provider_mod.BoundedProvider._open_from_buf = _counting_open_from_buf

# --- swap-on-full-read wrapper: rewrites SWAP_PATH to B's exact bytes,
# via a SEPARATE handle, the FIRST time resource_preflight asks for the
# "full_bounded_read" -- i.e. strictly AFTER the header+directory
# preflight read already happened against A. ---
_orig_instrumented_read = resource_preflight._instrumented_read
_swap_done = [False]


def _swap_on_full_read(f, size, inst, label):
    if label == "full_bounded_read" and not _swap_done[0]:
        _swap_done[0] = True
        # `f` may still hold STALE buffered bytes from the earlier header/
        # directory reads (io.BufferedReader does not necessarily discard
        # its internal buffer on seek() if the new position falls within
        # the already-buffered window) -- close it and rewrite the file
        # via a brand-new, never-before-read handle so the replacement is
        # genuine, not partially masked by a stale read-ahead buffer.
        f.close()
        with open(SWAP_PATH, "wb") as wf:
            wf.write(B_BYTES)
        f_fresh = open(SWAP_PATH, "rb")
        try:
            return _orig_instrumented_read(f_fresh, size, inst, label)
        finally:
            f_fresh.close()
    return _orig_instrumented_read(f, size, inst, label)


resource_preflight._instrumented_read = _swap_on_full_read

wanted = {"normalizer": [b"astrafamilyone", b"astrafamilytwo"]}
# expected_source_sha256 is irrelevant to this test's outcome -- the
# cumulative-admission refusal (if it fires, as expected) happens BEFORE
# the source hash is ever checked. Pass A's own declared source hash
# (arbitrary but harmless).
import hashlib  # noqa: E402
with open(MANIFEST["boundary_below_19999"]["master_path"], "rb") as f:
    dummy_expected_source_sha256 = hashlib.sha256(f.read()).hexdigest()

inst = resource_preflight.CandidateOpenInstrumentation()
try:
    resource_preflight.candidate_open_and_identify_with_preflight(
        SWAP_PATH, dummy_expected_source_sha256, runtime_cap_bytes=4 * 1024 * 1024, inst=inst,
        requested_folds_by_consumer=wanted,
    )
    outcome = "admitted"
except errors.ResourceAdmissionRefusal as exc:
    outcome = "refused"
    reason_text = str(exc)
except Exception as exc:
    outcome = "other_exception:%s" % type(exc).__name__
    reason_text = str(exc)

resource_preflight._instrumented_read = _orig_instrumented_read
_provider_mod.BoundedProvider._open_from_buf = _orig_open_from_buf

print("[t3] swap occurred=%s outcome=%s" % (_swap_done[0], outcome))
check("t3.0 the mid-open swap (A -> B) actually happened before the full read", _swap_done[0], _swap_done[0])
check("t3.1 the acquisition against the REPLACED (now-B) content is REFUSED "
      "(the preliminary A-based shape never gets to authorize anything)", outcome == "refused", outcome)
if outcome == "refused":
    check("t3.2 refusal reason is the real cumulative retained-gate check against B's ACTUAL bytes",
          "cumulative_retained_exceeds_gate" in reason_text or "cumulative admission refused" in reason_text,
          reason_text)
check("t3.3 preliminary shape WAS present (the header+directory read against A succeeded, proving "
      "the swap truly happened AFTER that stage, not before it)", inst.preliminary_shape_present, inst.to_dict())
check("t3.4 the final shape (parsed from the actual full-read bytes) DIFFERED from the preliminary "
      "(A-based) shape -- proof admission used B's real shape, not a cached/stale one",
      inst.final_shape_differed_from_preliminary, inst.to_dict())
check("t3.5 exactly ONE full_bounded_read occurred (never a second full disk read to \"double check\")",
      inst.full_bounded_read_call_count == 1, inst.full_bounded_read_call_count)
check("t3.6 the refusal happened strictly BEFORE the frozen validator ever ran "
      "(zero provider constructions for this acquisition)", _decode_call_count[0] == 0, _decode_call_count[0])
check("t3.7 the real cumulative_admission record was populated (computed against the FINAL buffer)",
      inst.cumulative_admission is not None, inst.cumulative_admission)
if inst.cumulative_admission is not None:
    check("t3.8 cumulative_admission.total_retained_bytes reflects B's real ~17.4MB cost, not A's "
          "near-zero cost for these folds",
          inst.cumulative_admission["total_retained_bytes"] > 16 * 1024 * 1024,
          inst.cumulative_admission["total_retained_bytes"])

shutil.rmtree(SCRATCH, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
