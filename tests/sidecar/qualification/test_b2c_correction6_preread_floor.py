# -*- coding: utf-8 -*-
"""Correction6 -- decisive regression probe: shape-independent pre-read
transient floor, applied on EVERY path that could reach the one full
bounded read -- including every header/directory parse-failure mode,
not only the parseable-shape path Correction5's own check covered.

=== Exact independent-audit counterexample ===

Correction5's pre-full-read aggregate transient check only ran inside
`if preliminary_shape is not None:`. A header/directory parse failure
(bad magic, unsupported format_contract_version, a short/truncated
header, an invalid section_count, an invalid directory offset/extent,
or a malformed directory row) set `preflight_parse_deferred = True` /
`preliminary_shape = None` and fell through to the one full bounded
read (`f.read(runtime_cap_bytes + 1)`) UNCONDITIONALLY -- no aggregate-
transient check of any kind on that path.

Independently reproduced here with a real malformed 1 KiB candidate
(`fixtures_malformed/malformed_1kib.sfmsidecar`, all-zero bytes -- bad
magic), runtime_cap_bytes=16 MiB, aggregate_existing_retained_bytes=10
MiB:

    minimum_full_read_transient = 23,068,673 B   (shape-independent:
                                                   read_bound=16,777,217
                                                   + FIXED_TRANSIENT_
                                                   RUNTIME_OVERHEAD_
                                                   BYTES=2,097,152
                                                   + MEASUREMENT_MODEL_
                                                   GUARD_BYTES=4,194,304)
    existing retained                = 10,485,760 B  (10 MiB)
    minimum aggregate transient      = 33,554,433 B
    TRANSIENT_GATE_BYTES             = 33,554,432 B  (32 MiB)

-- already over gate by exactly one byte, from trusted/runtime-known
inputs ALONE, before any header byte is even read. Against the buggy
Correction5 code (`candidate_b2c_correction5/`), this scenario still
performs the one full bounded read (`full_bounded_read_call_count ==
1`) and only then reaches the full validator's own corruption
classification. Against the corrected Correction6 code
(`candidate_b2c_correction6/`), the SAME scenario is refused BEFORE any
header/directory parse is even attempted
(`full_bounded_read_call_count == 0`).

This test exercises the SAME floor check against THREE distinct
preflight parse-failure modes (bad magic, unsupported format version,
truncated directory) to prove the fix applies uniformly on every path
that could reach the full read -- not merely the one exact fixture the
audit happened to cite -- and against both Correction5 (documenting
the bug) and Correction6 (proving the fix), so it fails against the
unfixed `3bb3468...` code and passes only with the Correction6 change.

Astra Narrow Issue E: paths derived from `__file__`.
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
CORRECTION5_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction5")
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
FIXROOT_MALFORMED = os.path.join(CORRECTION6_ROOT, "fixtures_malformed")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(os.path.join(FIXROOT_MALFORMED, "manifest.json")) as f:
    MANIFEST = json.load(f)

MALFORMED_1KIB = os.path.join(FIXROOT_MALFORMED, MANIFEST["fixtures"]["malformed_1kib"]["artifact_relative_path"])
UNSUPPORTED_FORMAT = os.path.join(FIXROOT_MALFORMED, MANIFEST["fixtures"]["unsupported_format"]["artifact_relative_path"])
TRUNCATED_DIRECTORY = os.path.join(FIXROOT_MALFORMED, MANIFEST["fixtures"]["truncated_directory"]["artifact_relative_path"])

RUNTIME_CAP_BYTES = 16 * 1024 * 1024
TRANSIENT_GATE_BYTES = 32 * 1024 * 1024
DUMMY_SHA = "0" * 64

# Exact independent-audit figures, reproduced fresh by this test.
DECISIVE_EXISTING_RETAINED_BYTES = 10 * 1024 * 1024        # 10,485,760
EXPECTED_MINIMUM_FULL_READ_TRANSIENT = 23068673             # shape-independent, fixed for runtime_cap=16MiB
EXPECTED_MINIMUM_AGGREGATE = DECISIVE_EXISTING_RETAINED_BYTES + EXPECTED_MINIMUM_FULL_READ_TRANSIENT


def _fresh_import(root_dir):
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority_productionized" or name.startswith("sfm_master_authority_productionized."):
            del sys.modules[name]
    if root_dir in sys.path:
        sys.path.remove(root_dir)
    sys.path.insert(0, root_dir)
    import sfm_master_authority_productionized.resource_preflight as rp
    import sfm_master_authority_productionized.resource_estimator as re_
    import sfm_master_authority_productionized.errors as errors
    return rp, re_, errors


def attempt(rp, errors, path, existing_retained_bytes):
    """Runs the decisive scenario against one candidate's
    `resource_preflight` module. Always passes its own instrumentation
    object explicitly (never relies on an exception carrying one --
    SidecarCorrupt/FormatUnsupported do not attach `.instrumentation`),
    so every observable fact is available regardless of outcome."""
    inst = rp.CandidateOpenInstrumentation()
    provider = None
    try:
        provider, identity, _ = rp.candidate_open_and_identify_with_preflight(
            path, DUMMY_SHA, RUNTIME_CAP_BYTES, inst=inst,
            requested_folds_by_consumer={}, aggregate_existing_retained_bytes=existing_retained_bytes,
        )
        outcome = "admitted"
        exc_type = None
    except errors.ResourceAdmissionRefusal as exc:
        outcome = "refused"
        exc_type = "ResourceAdmissionRefusal"
    except errors.SidecarCorrupt as exc:
        outcome = "corrupt"
        exc_type = "SidecarCorrupt"
    except errors.FormatUnsupported as exc:
        outcome = "format_unsupported"
        exc_type = "FormatUnsupported"
    except Exception as exc:
        outcome = "other"
        exc_type = type(exc).__name__
    finally:
        if provider is not None:
            provider.close()
    return {
        "outcome": outcome,
        "exc_type": exc_type,
        "reason": inst.reason,
        "full_bounded_read_call_count": inst.full_bounded_read_call_count,
        "validator_call_count": inst.validator_call_count,
        "preflight_parse_deferred": inst.preflight_parse_deferred,
        "preliminary_shape_present": inst.preliminary_shape_present,
        "file_open_count": inst.file_open_count,
        "file_close_count": inst.file_close_count,
    }


rp5, re5, errors5 = _fresh_import(CORRECTION5_ROOT)
rp6, re6, errors6 = _fresh_import(CORRECTION6_ROOT)

# Sanity: the shape-independent floor formula matches the exact
# independent-audit figure for this runtime cap, computed fresh (not
# hardcoded blindly).
computed_floor = re6.estimate_minimum_full_read_transient(RUNTIME_CAP_BYTES)
check("sanity.0 estimate_minimum_full_read_transient(16 MiB) matches the exact audit figure",
      computed_floor == EXPECTED_MINIMUM_FULL_READ_TRANSIENT, computed_floor)

# ===========================================================================
# Section 5.A: malformed file, decisive -- must fail against 3bb3468
# (Correction5), pass only with Correction6.
# ===========================================================================
result5_a = attempt(rp5, errors5, MALFORMED_1KIB, DECISIVE_EXISTING_RETAINED_BYTES)
print("[A/correction5(unfixed)] %s" % json.dumps(result5_a, sort_keys=True))
check("A.c5.0 (documenting the bug) Correction5 performs the full bounded read once on the "
      "malformed file despite the aggregate floor already exceeding the gate",
      result5_a["outcome"] in ("corrupt", "format_unsupported", "other")
      and result5_a["full_bounded_read_call_count"] == 1, result5_a)

result6_a = attempt(rp6, errors6, MALFORMED_1KIB, DECISIVE_EXISTING_RETAINED_BYTES)
print("[A/correction6(fixed)] %s" % json.dumps(result6_a, sort_keys=True))
check("A.c6.0 Correction6 refuses BEFORE any header/directory parse is attempted",
      result6_a["outcome"] == "refused" and result6_a["exc_type"] == "ResourceAdmissionRefusal", result6_a)
check("A.c6.1 refusal reason clearly indicates the shape-independent minimum floor",
      result6_a["reason"] == "minimum_floor_estimated_transient", result6_a)
check("A.c6.2 full_bounded_read_call_count == 0 -- the full read never happened",
      result6_a["full_bounded_read_call_count"] == 0, result6_a)
check("A.c6.3 validator_call_count == 0 -- no validator entered, no provider constructed",
      result6_a["validator_call_count"] == 0, result6_a)
check("A.c6.4 preflight never even attempted the header/directory parse (file_open/close still "
      "happened exactly once -- Gate A's fstat -- but no header read call recorded; "
      "preflight_parse_deferred stays at its unset default, never flipped to True by an actual "
      "parse attempt)",
      result6_a["file_open_count"] == 1 and result6_a["file_close_count"] == 1
      and result6_a["preflight_parse_deferred"] is False and result6_a["preliminary_shape_present"] is False,
      result6_a)
check("A.c6.5 no cache/generation/ledger mutation possible -- this call path never reaches "
      "Cohort/Broker/ViewCache/AggregateLedger at all (validator_call_count == 0 and the "
      "exception raised before any provider exists)", result6_a["validator_call_count"] == 0)

# ===========================================================================
# Section 5.B: malformed file, low retained -- full read occurs, authoritative
# corruption classification remains observable (proves Correction6 did NOT
# turn all malformed input into a resource refusal).
# ===========================================================================
result6_b = attempt(rp6, errors6, MALFORMED_1KIB, 0)
print("[B/correction6(fixed, low-retained)] %s" % json.dumps(result6_b, sort_keys=True))
check("B.0 full bounded read occurs when the floor comfortably fits under the gate",
      result6_b["full_bounded_read_call_count"] == 1, result6_b)
check("B.1 authoritative corruption classification remains observable (SidecarCorrupt, not a "
      "resource refusal)", result6_b["outcome"] == "corrupt" and result6_b["exc_type"] == "SidecarCorrupt", result6_b)

# ===========================================================================
# Section 5.C: unsupported format, over floor -- zero full reads.
# ===========================================================================
result6_c_over = attempt(rp6, errors6, UNSUPPORTED_FORMAT, DECISIVE_EXISTING_RETAINED_BYTES)
print("[C/correction6(over floor)] %s" % json.dumps(result6_c_over, sort_keys=True))
check("C.0 unsupported-format candidate over the floor: refused pre-read, zero full reads",
      result6_c_over["outcome"] == "refused" and result6_c_over["reason"] == "minimum_floor_estimated_transient"
      and result6_c_over["full_bounded_read_call_count"] == 0, result6_c_over)

result6_c_under = attempt(rp6, errors6, UNSUPPORTED_FORMAT, 0)
check("C.1 same file, floor comfortably under gate: full read proceeds, FormatUnsupported "
      "classification remains observable",
      result6_c_under["full_bounded_read_call_count"] == 1
      and result6_c_under["outcome"] == "format_unsupported", result6_c_under)

# ===========================================================================
# Section 5.D: invalid/truncated directory, over floor -- zero full reads.
# Header parses; directory preflight itself cannot produce a shape
# (`preflight_parse_deferred=True`, `preliminary_shape_present=False`) when
# the floor is under the gate -- confirms this exercises the directory-
# level failure, not merely a header-level one.
# ===========================================================================
result6_d_over = attempt(rp6, errors6, TRUNCATED_DIRECTORY, DECISIVE_EXISTING_RETAINED_BYTES)
print("[D/correction6(over floor)] %s" % json.dumps(result6_d_over, sort_keys=True))
check("D.0 truncated-directory candidate over the floor: refused pre-read, zero full reads",
      result6_d_over["outcome"] == "refused" and result6_d_over["reason"] == "minimum_floor_estimated_transient"
      and result6_d_over["full_bounded_read_call_count"] == 0, result6_d_over)

result6_d_under = attempt(rp6, errors6, TRUNCATED_DIRECTORY, 0)
check("D.1 same file, floor comfortably under gate: full read proceeds, and the directory-level "
      "(not merely header-level) preflight parse failure is confirmed",
      result6_d_under["full_bounded_read_call_count"] == 1
      and result6_d_under["preflight_parse_deferred"] is True
      and result6_d_under["preliminary_shape_present"] is False, result6_d_under)

# ===========================================================================
# Section 5.E: exact boundary matrix on the malformed_1kib fixture.
# ===========================================================================
one_below_existing = (TRANSIENT_GATE_BYTES - 1) - EXPECTED_MINIMUM_FULL_READ_TRANSIENT
exact_existing = TRANSIENT_GATE_BYTES - EXPECTED_MINIMUM_FULL_READ_TRANSIENT
one_above_existing = (TRANSIENT_GATE_BYTES + 1) - EXPECTED_MINIMUM_FULL_READ_TRANSIENT

result_one_below = attempt(rp6, errors6, MALFORMED_1KIB, one_below_existing)
check("E.one-byte-below (minimum aggregate == gate-1): may proceed -- full read occurs",
      result_one_below["full_bounded_read_call_count"] == 1, (one_below_existing, result_one_below))

result_exact = attempt(rp6, errors6, MALFORMED_1KIB, exact_existing)
check("E.exact (minimum aggregate == gate exactly): may proceed -- strict '>' semantics, "
      "consistent with the established gate contract (== gate is never a refusal)",
      result_exact["full_bounded_read_call_count"] == 1, (exact_existing, result_exact))

result_one_above = attempt(rp6, errors6, MALFORMED_1KIB, one_above_existing)
check("E.one-byte-above (minimum aggregate == gate+1): refused pre-read, zero full reads",
      result_one_above["outcome"] == "refused" and result_one_above["full_bounded_read_call_count"] == 0,
      (one_above_existing, result_one_above))
check("E.decisive-equals-one-above: the decisive 10 MiB case (Section A) is exactly this "
      "one-byte-above boundary case", one_above_existing == DECISIVE_EXISTING_RETAINED_BYTES, one_above_existing)


print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
