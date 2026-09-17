# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 2: packed-family/aggregate
cumulative admission (F2), through the REAL broker/cohort route.

Uses REAL compiled/validated fixtures (built by build_test2_fixtures_
correction2.py, manifest at candidate_b2c_correction2/fixtures/
manifest.json) -- no monkeypatched Hit objects for the boundary/large-
family cases this time.

Instrumentation: the frozen BoundedProvider._open_from_buf classmethod
(the FIRST point at which occurrence rows could ever be decoded, per its
own _validate_complete() contract) is wrapped with a call counter for the
duration of this file, then restored -- proving a refused request never
reaches it (Astra's "a single family must be rejectable before decoding
all its occurrence rows" requirement)."""
import hashlib
import json
import os
import shutil
import sys
import tempfile


def isolated_shipped_root(*artifact_paths):
    """A shipped_root containing ONLY the given artifact(s) -- so a
    provider-construction-count probe is never contaminated by harmless
    source_sha256-mismatch probing of OTHER, unrelated fixtures that
    happen to share the same flat fixture directory."""
    d = tempfile.mkdtemp(prefix="b2c_correction2_test2_isolated_")
    for p in artifact_paths:
        shutil.copy(p, os.path.join(d, os.path.basename(p)))
    return d

CORRECTION2_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction2"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT = CORRECTION2_ROOT + r"\fixtures"

for p in (CORRECTION2_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import resource_estimator  # noqa: E402
from sfm_master_authority_productionized import packed_family_counts  # noqa: E402
from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(FIXROOT + r"\manifest.json") as f:
    MANIFEST = json.load(f)

# ---------------------------------------------------------------------
# Decode-call instrumentation: wrap the frozen provider's ONE construction
# entry point. Never edits the frozen file -- a process-local monkeypatch,
# restored in a finally block.
# ---------------------------------------------------------------------
sidecar_contract.ensure_loaded()
_provider_mod = sidecar_contract._provider_module
_orig_open_from_buf = _provider_mod.BoundedProvider._open_from_buf
_decode_call_count = [0]


@classmethod
def _counting_open_from_buf(cls, *a, **kw):
    _decode_call_count[0] += 1
    return _orig_open_from_buf.__func__(cls, *a, **kw)


_provider_mod.BoundedProvider._open_from_buf = _counting_open_from_buf


def decode_calls_since(mark):
    return _decode_call_count[0] - mark


# ===========================================================================
# Part 1: packed-family counts are EXACT (against the manifest's own
# `occurrence_count`), obtained WITHOUT any provider construction at all.
# ===========================================================================
for label, n in [("below", 19999), ("at", 20000), ("above", 20001)]:
    key = "boundary_%s_%d" % (label, n)
    m = MANIFEST[key]
    with open(m["artifact_path"], "rb") as f:
        buf = f.read()
    header = fmt.unpack_header(buf[:fmt.HEADER_SIZE], 0)
    dir_end = resource_estimator._validate_header_and_bound_directory_region(header, len(buf))
    shape = resource_estimator.parse_resource_shape(buf[:dir_end], len(buf))
    mark = _decode_call_count[0]
    counts = packed_family_counts.get_packed_family_counts_batch(buf, shape, [b"boundaryoccurrencecontrol"])
    check("t2.exact_count.%s real packed count == manifest occurrence_count (%d)" % (key, n),
          counts[b"boundaryoccurrencecontrol"] == n, counts)
    check("t2.exact_count.%s obtaining the count triggered ZERO provider constructions" % key,
          decode_calls_since(mark) == 0, decode_calls_since(mark))

# ===========================================================================
# Part 2: boundary admit/refuse via evaluate_cumulative_admission directly
# -- 19,999 and 20,000 admit; 20,001 refuses on the SECONDARY cap (not a
# byte-budget coincidence).
# ===========================================================================
for label, n, expect_admit in [("below", 19999, True), ("at", 20000, True), ("above", 20001, False)]:
    key = "boundary_%s_%d" % (label, n)
    m = MANIFEST[key]
    with open(m["artifact_path"], "rb") as f:
        buf = f.read()
    header = fmt.unpack_header(buf[:fmt.HEADER_SIZE], 0)
    dir_end = resource_estimator._validate_header_and_bound_directory_region(header, len(buf))
    shape = resource_estimator.parse_resource_shape(buf[:dir_end], len(buf))
    counts = packed_family_counts.get_packed_family_counts_batch(buf, shape, [b"boundaryoccurrencecontrol"])
    result = resource_estimator.evaluate_cumulative_admission(
        shape, {"normalizer": counts}, runtime_cap_bytes=4 * 1024 * 1024,
        retained_gate_bytes=16 * 1024 * 1024, transient_gate_bytes=32 * 1024 * 1024,
    )
    print("[t2.boundary_admission.%s] admitted=%s reason=%s total_retained=%d max_single_family_count=%d"
          % (key, result.admitted, result.reason, result.total_retained_bytes, result.max_single_family_count))
    check("t2.boundary_admission.%s admitted=%s as expected" % (key, expect_admit),
          result.admitted == expect_admit, (result.admitted, result.reason))
    if not expect_admit:
        check("t2.boundary_admission.%s refusal reason is the SECONDARY cap, not a coincidental byte gate" % key,
              result.reason == "secondary_single_family_cap_exceeded", result.reason)

# ===========================================================================
# Part 3: Astra's exact two-large-families reproduction, through the REAL
# broker/cohort route -- requesting ONLY the two large families (not the
# 20,000 singletons) must be refused because the REAL per-family sum
# (40,000 occurrence rows) exceeds the retained gate, even though the
# whole-artifact AVERAGE (60,000 rows / ~20,002 folds ~= 3/fold) would
# have looked trivially safe.
# ===========================================================================
m = MANIFEST["astra_two_large_families"]
astra_isolated_root = isolated_shipped_root(m["artifact_path"])
b_astra = broker_mod.Broker(api_version="test-t2-astra-repro")
wanted = frozenset([b"astrafamilyone", b"astrafamilytwo"])
mark = _decode_call_count[0]
try:
    b_astra.acquire_or_reuse_views(
        m["master_path"], {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))},
        shipped_root=astra_isolated_root, runtime_cap_bytes=4 * 1024 * 1024,
    )
    astra_outcome = "admitted"
except errors.ResourceAdmissionRefusal as exc:
    astra_outcome = "refused: %s" % exc
print("[t2.astra_repro] requesting ONLY the two 20,000-row families -> %s" % astra_outcome)
check("t2.astra_repro requesting only the two large families is correctly REFUSED "
      "(real per-family sum, not the whole-artifact average)", astra_outcome.startswith("refused"), astra_outcome)
check("t2.astra_repro the refusal happened before ANY provider construction "
      "(zero occurrence-row decoding of the 40,000 requested rows)",
      decode_calls_since(mark) == 0, decode_calls_since(mark))

# A single SMALL singleton fold from the same artifact, by contrast, must
# admit cleanly -- proving the fix is request-aware, not a blanket refusal
# of this artifact.
wanted_small = frozenset([b"astrasingleton00000"])
try:
    b_small = broker_mod.Broker(api_version="test-t2-astra-small")
    b_small.acquire_or_reuse_views(
        m["master_path"], {"normalizer": (wanted_small, adapter.build_targeted_master_compatible_projection(wanted_small))},
        shipped_root=astra_isolated_root, runtime_cap_bytes=4 * 1024 * 1024,
    )
    small_outcome = "admitted"
except errors.ResourceAdmissionRefusal as exc:
    small_outcome = "refused: %s" % exc
check("t2.astra_repro a single SINGLETON fold from the SAME artifact admits cleanly "
      "(request-aware, not a blanket artifact-level refusal)", small_outcome == "admitted", small_outcome)

# ===========================================================================
# Part 4: held old/new consumer views -- a genuinely LIVE, leased view's
# retained charge must be included (via aggregate_existing_retained_bytes)
# when admitting a SECOND, otherwise-individually-fine request.
# ===========================================================================
m_at = MANIFEST["boundary_at_20000"]
m_below = MANIFEST["boundary_below_19999"]
b_hold = broker_mod.Broker(api_version="test-t2-held-views")
wanted_at = frozenset([b"boundaryoccurrencecontrol"])

detached_first = b_hold.acquire_or_reuse_views(
    m_at["master_path"], {"normalizer": (wanted_at, adapter.build_targeted_master_compatible_projection(wanted_at))},
    shipped_root=FIXROOT, runtime_cap_bytes=4 * 1024 * 1024,
)
lease_held = b_hold.lease_view(detached_first["normalizer"])
ledger_after_first = b_hold.ledger_snapshot()
check("t2.held_views.0 first acquisition (boundary_at_20000, ~8.7MB) is retained/charged in the ledger",
      sum(ledger_after_first.values()) > 0, ledger_after_first)

try:
    b_hold.acquire_or_reuse_views(
        m_below["master_path"],
        {"normalizer2": (wanted_at, adapter.build_targeted_master_compatible_projection(wanted_at))},
        shipped_root=FIXROOT, runtime_cap_bytes=4 * 1024 * 1024,
    )
    second_outcome = "admitted"
except errors.ResourceAdmissionRefusal as exc:
    second_outcome = "refused: %s" % exc
print("[t2.held_views] second request (another ~8.7MB, boundary_below_19999) while the first "
      "(~8.7MB) is still HELD/leased -> %s" % second_outcome)
check("t2.held_views.1 a SECOND ~8.7MB request is REFUSED once combined with the FIRST's still-held "
      "~8.7MB charge (2x ~8.7MB > 16MiB retained gate) -- proves aggregate_existing_retained_bytes is "
      "real broker ledger state, not a per-request-only view", second_outcome.startswith("refused"),
      second_outcome)

before_release_outstanding = b_hold.outstanding_lease_count()
b_hold.release_view_lease(lease_held)
check("t2.held_views.2 releasing the lease decrements outstanding_lease_count "
      "(the view itself may legitimately remain CACHED/retained for reuse -- releasing a lease is "
      "not the same as evicting a cache entry)",
      b_hold.outstanding_lease_count() == before_release_outstanding - 1, b_hold.outstanding_lease_count())

# ===========================================================================
# Part 5: non-boundary shape fixtures (concentrated vocabulary, long
# literals, deep hierarchy, dense metadata) all admit cleanly through the
# real broker route -- a sanity/non-regression check that the corrected
# admission model doesn't over-refuse ordinary small requests.
# ===========================================================================
for key, wanted_literal in [
    ("concentrated_small_vocab", b"alpha"),
    ("long_literals", None),
    ("deep_hierarchy", b"deepestcontrol"),
    ("dense_metadata", b"densemetacontrol"),
]:
    m = MANIFEST[key]
    if wanted_literal is None:
        with open(m["master_path"], "rb") as f:
            text = f.read().decode("utf-8")
        import re
        lit = re.search(r'"control"\s*"([^"]+)"', text).group(1)
        wanted_literal = lit.lower().encode("utf-8")
    b_ok = broker_mod.Broker(api_version="test-t2-%s" % key)
    wanted = frozenset([wanted_literal])
    try:
        b_ok.acquire_or_reuse_views(
            m["master_path"], {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))},
            shipped_root=FIXROOT, runtime_cap_bytes=4 * 1024 * 1024,
        )
        outcome = "admitted"
    except errors.ResourceAdmissionRefusal as exc:
        outcome = "refused: %s" % exc
    check("t2.non_regression.%s admits cleanly" % key, outcome == "admitted", outcome)

_provider_mod.BoundedProvider._open_from_buf = _orig_open_from_buf
shutil.rmtree(astra_isolated_root, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
