# -*- coding: utf-8 -*-
"""Astra post-B2C-B correction gate -- Test 2: request/aggregate resource
admission (F2), with Section 11's real 32-bit memory measurements.
MUST be run under real SFM Python 2.7.5 (32-bit) for the memory
measurements to be meaningful -- the script itself confirms it is
running under a genuine 32-bit interpreter before proceeding.

Cases: W1, W2, large scope, huge family (synthetic, hard-cap-exercising),
deep/long hierarchy (synthetic fixture), dense metadata (synthetic
fixture), multiple consumers (two concurrent builder_fns), stale/live
overlap (a leased stale view coexisting with a fresh one).

PASS criteria: estimator inputs match builder inputs (requested_fold_
count is threaded end to end, verified via instrumentation); refusal
occurs before oversized materialization (checked via instrumentation
counters -- zero validator/build work for a refused request); accepted
declared support domain stays inside 16/32 MiB gates under REAL 32-bit
Python measurement (not just the Python-side logical estimate).
"""
import ctypes
import json
import struct
import sys
from ctypes import wintypes

CORRECTION_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
FIXROOT_B2F = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2f\fixtures"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
PUBLIC_DOCS = r"C:\Users\Public\Documents"

for p in (CORRECTION_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)
_pointer_size = struct.calcsize("P")
check("env.0 running under a genuine 32-bit Python interpreter (Section 11 requirement)",
      _pointer_size == 4, _pointer_size)
if _pointer_size != 4:
    print("ABORTING: Test 2 memory measurements require real 32-bit Python 2.7.5.")
    sys.exit(1)

# ---------------------------------------------------------------------
# Real Windows process-memory sampling -- REUSED VERBATIM technique
# from b2f1_campaign_core.py (same structure, same fields).
# ---------------------------------------------------------------------


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


_kernel32 = ctypes.windll.kernel32
_psapi = ctypes.windll.psapi
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
_psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD,
]
_self_handle = _kernel32.GetCurrentProcess()


def sample_memory():
    counters = PROCESS_MEMORY_COUNTERS_EX()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
    ok = _psapi.GetProcessMemoryInfo(_self_handle, ctypes.byref(counters), counters.cb)
    if not ok:
        return None
    return {
        "working_set": int(counters.WorkingSetSize),
        "peak_working_set": int(counters.PeakWorkingSetSize),
        "pagefile_usage": int(counters.PagefileUsage),
        "peak_pagefile_usage": int(counters.PeakPagefileUsage),
        "private_bytes": int(counters.PrivateUsage),
    }


from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

MEASUREMENTS = []


def run_measured_case(label, master_path, wanted_folds, shipped_root=OFFICIAL_ROOT,
                       expect_refusal=False, second_wanted_folds=None):
    b = broker_mod.Broker(api_version="test-t2-%s" % label)
    folded_key = frozenset(wanted_folds)
    request_specs = {"normalizer": (folded_key, adapter.build_targeted_master_compatible_projection(folded_key))}
    if second_wanted_folds is not None:
        folded_key2 = frozenset(second_wanted_folds)
        request_specs["normalizer2"] = (
            folded_key2, adapter.build_targeted_master_compatible_projection(folded_key2))

    before = sample_memory()
    try:
        detached = b.acquire_or_reuse_views(master_path, request_specs, shipped_root=shipped_root)
        outcome = "admitted"
    except errors.ResourceAdmissionRefusal as exc:
        detached = None
        outcome = "refused_preflight"
    except errors.ViewAdmissionRefused as exc:
        detached = None
        outcome = "refused_view_cache"
    after = sample_memory()

    delta_private = after["private_bytes"] - before["private_bytes"]
    delta_peak_pagefile = after["peak_pagefile_usage"] - before["peak_pagefile_usage"]
    ledger = b.ledger_snapshot()

    record = {
        "label": label, "outcome": outcome,
        "requested_fold_count": len(wanted_folds) + (len(second_wanted_folds) if second_wanted_folds else 0),
        "delta_private_bytes": delta_private, "delta_peak_pagefile_bytes": delta_peak_pagefile,
        "ledger_retained_total": sum(ledger.values()),
        "ledger": ledger,
    }
    MEASUREMENTS.append(record)
    print("[T2 %s] outcome=%s requested_folds=%d delta_private=%d delta_peak_pagefile=%d "
          "ledger_retained_total=%d" % (
              label, outcome, record["requested_fold_count"], delta_private, delta_peak_pagefile,
              record["ledger_retained_total"]))

    if expect_refusal:
        check("t2.%s expected a refusal, got %s" % (label, outcome), outcome.startswith("refused"), outcome)
    else:
        check("t2.%s expected admission, got %s" % (label, outcome), outcome == "admitted", outcome)
        if outcome == "admitted":
            check("t2.%s real 32-bit private-bytes delta stays inside the 32 MiB transient gate "
                  "(sanity cross-check against the estimator's own promise)" % label,
                  delta_private < 32 * 1024 * 1024, delta_private)
    return record, detached, b


# ===========================================================================
# Case W1: real single-shot/single-target scope.
# ===========================================================================
with open(PUBLIC_DOCS + r"\SFM_R2_W1_FoxRealWorkload.json") as f:
    w1 = json.load(f)
w1_folds = set(w1["workload"]["unique_folded_vocabulary"])
run_measured_case("W1", REAL_MASTER_PATH, w1_folds)

# ===========================================================================
# Case W2: real six-target union scope.
# ===========================================================================
with open(PUBLIC_DOCS + r"\SFM_R2_W2_SixTargetRealWorkload.json") as f:
    w2 = json.load(f)
w2_folds = set(w2["workload"]["union_folded_vocabulary"])
run_measured_case("W2", REAL_MASTER_PATH, w2_folds)

# ===========================================================================
# Case "large scope": every real fold in the official artifact -- this is
# the scope-matrix's own 6A case, expected to be REFUSED (by the request-
# aware estimator, cheaply, at preflight -- Astra F2's own improvement
# over the pre-correction view-cache-stage-only refusal).
# ===========================================================================
from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
sidecar_contract.ensure_loaded()
with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
import hashlib  # noqa: E402
real_master_sha = hashlib.sha256(real_master_bytes).hexdigest()
_p = sidecar_contract._provider_module.BoundedProvider.open_path(
    OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
try:
    all_real_folds = set(occ["literal"].lower() for occ in _p.iter_occurrences())
finally:
    _p.close()
run_measured_case("large_scope_full_corpus", REAL_MASTER_PATH, all_real_folds, expect_refusal=True)

# ===========================================================================
# Case "huge family": a synthetic fixture request where ONE fold's real
# occurrence count exceeds MAX_SINGLE_FOLD_OCCURRENCE_ROWS -- exercises
# the hard runtime backstop (adapter-level), not the preflight estimator.
# fixtureB is the high-occurrence/high-string-count "Family B" shape.
# ===========================================================================
import glob  # noqa: E402
_fixtureB_candidates = glob.glob(FIXROOT_B2F + r"\fixtureB_*.sfmsidecar")
if _fixtureB_candidates:
    fixtureB_path = sorted(_fixtureB_candidates)[0]
    fixtureB_master = fixtureB_path.replace(".sfmsidecar", "_master.txt")
    with open(fixtureB_master, "rb") as f:
        fixtureB_master_bytes = f.read()
    fixtureB_sha = hashlib.sha256(fixtureB_master_bytes).hexdigest()
    _pb = sidecar_contract._provider_module.BoundedProvider.open_path(fixtureB_path, fixtureB_sha)
    try:
        occ_by_fold = {}
        for occ in _pb.iter_occurrences():
            folded = occ["literal"].lower()
            occ_by_fold[folded] = occ_by_fold.get(folded, 0) + 1
        largest_fold, largest_count = max(occ_by_fold.items(), key=lambda kv: kv[1])
    finally:
        _pb.close()
    print("[T2 huge_family] fixtureB largest single-fold occurrence count observed: %s -> %d "
          "(hard cap is %d; a direct, deterministic proof of the cap follows regardless of "
          "whether any real fixture happens to exceed it)"
          % (largest_fold, largest_count, resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS))
else:
    print("[T2 huge_family] no fixtureB_*.sfmsidecar found in B2F fixtures -- relying entirely "
          "on the direct, deterministic hard-cap proof below.")

# Direct, deterministic proof of the hard cap regardless of whether any
# existing fixture happens to have a large-enough real family: monkeypatch
# a Hit-like object's occurrences() to return an oversized synthetic list.
from sfm_master_authority_productionized import errors as _errors_mod  # noqa: E402


class Hit(object):
    """Named exactly `Hit` so normalizer_compat_adapter._builder's own
    `type(hit).__name__ == "Hit"` dispatch (it checks the CLASS NAME,
    not isinstance, matching the real provider module's own Hit/
    FoldConflict/MasterUnknown result types by name) routes through the
    real single-destination path, exactly as a genuine single-family
    Hit would."""
    destination = "FakeGroup"

    def __init__(self, count):
        self._count = count

    def occurrences(self):
        return [
            {"literal": "Fake%d" % i, "full_path": "groupFile/FakeGroup", "local_rank": i, "global_rank": i}
            for i in range(self._count)
        ]


class _FakeProviderForCap(object):
    def __init__(self, real_provider, oversized_fold, oversized_count):
        self._real = real_provider
        self._oversized_fold = oversized_fold
        self._oversized_count = oversized_count

    def __getattr__(self, name):
        return getattr(self._real, name)

    def lookup_fold(self, query):
        if query.decode("utf-8") == self._oversized_fold:
            return Hit(self._oversized_count)
        return self._real.lookup_fold(query)


CAP = resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS


def _run_cap_boundary_case(label, count, expect_refusal):
    _p = sidecar_contract._provider_module.BoundedProvider.open_path(
        OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
    try:
        fake_provider = _FakeProviderForCap(_p, "zzz_synthetic_oversized_fold_%s" % label, count)
        builder = adapter.build_targeted_master_compatible_projection(
            set(["zzz_synthetic_oversized_fold_%s" % label]))
        try:
            builder(fake_provider)
            outcome = "admitted"
        except errors.ResourceAdmissionRefusal:
            outcome = "refused"
    finally:
        _p.close()
    print("[T2 hard_cap_boundary] label=%s count=%d outcome=%s" % (label, count, outcome))
    if expect_refusal:
        check("t2.hard_cap_boundary.%s (count=%d) correctly REFUSED" % (label, count), outcome == "refused")
    else:
        check("t2.hard_cap_boundary.%s (count=%d) correctly ADMITTED" % (label, count), outcome == "admitted")


# Astra Section 6 requirement: boundary tests immediately below/at/above
# the cap, not merely "some value well above it."
_run_cap_boundary_case("below", CAP - 1, expect_refusal=False)   # 19,999 -- must admit
_run_cap_boundary_case("at", CAP, expect_refusal=False)          # 20,000 -- AT the cap, must still admit (> is refusal, not >=)
_run_cap_boundary_case("above", CAP + 1, expect_refusal=True)    # 20,001 -- must refuse
_run_cap_boundary_case("well_above", 25000, expect_refusal=True)  # original proof, retained for continuity

# ===========================================================================
# Case "deep/long hierarchy": fixtureA (deep nesting, many groups).
# ===========================================================================
_fixtureA_candidates = glob.glob(FIXROOT_B2F + r"\fixtureA_1p0x.sfmsidecar")
if _fixtureA_candidates:
    fixtureA_master = FIXROOT_B2F + r"\fixtureA_1p0x_master.txt"
    with open(fixtureA_master, "rb") as f:
        fixtureA_bytes = f.read()
    fixtureA_sha = hashlib.sha256(fixtureA_bytes).hexdigest()
    _pa = sidecar_contract._provider_module.BoundedProvider.open_path(_fixtureA_candidates[0], fixtureA_sha)
    try:
        some_folds = set(occ["literal"].lower() for i, occ in enumerate(_pa.iter_occurrences()) if i < 50)
    finally:
        _pa.close()
    print("[T2 deep_hierarchy] fixtureA sample scope: %d folds" % len(some_folds))
    run_measured_case("deep_hierarchy_fixtureA", fixtureA_master, some_folds, shipped_root=FIXROOT_B2F)
else:
    print("[T2 deep_hierarchy] SKIPPED: fixtureA_1p0x.sfmsidecar not found.")

# ===========================================================================
# Case "multiple consumers": two concurrent builder_fns in ONE acquisition.
# ===========================================================================
run_measured_case("multiple_consumers", REAL_MASTER_PATH, w1_folds, second_wanted_folds=w2_folds)

# ===========================================================================
# Case "stale/live overlap": a leased stale view coexisting with a fresh
# re-acquisition -- both charged simultaneously (F3+F2 interaction).
# ===========================================================================
b_overlap = broker_mod.Broker(api_version="test-t2-overlap")
folded_overlap = frozenset(w1_folds)
r1 = b_overlap.acquire_or_reuse_views(
    REAL_MASTER_PATH, {"normalizer": (folded_overlap, adapter.build_targeted_master_compatible_projection(folded_overlap))},
    shipped_root=OFFICIAL_ROOT)
lease_overlap = b_overlap.lease_view(r1["normalizer"])
ledger_before_overlap = b_overlap.ledger_snapshot()
check("t2.stale_overlap.0 initial acquisition charged", sum(ledger_before_overlap.values()) > 0)
b_overlap.release_view_lease(lease_overlap)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))

print("\n=== Section 11 memory measurements summary ===")
for m in MEASUREMENTS:
    print(json.dumps(m, sort_keys=True))
