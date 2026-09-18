# -*- coding: utf-8 -*-
"""Correction5 -- decisive regression probe: pre-full-read aggregate
transient gate ordering.

=== Exact independent-audit counterexample ===

`resource_preflight.candidate_open_and_identify_with_preflight`'s
PRE-FULL-READ preliminary gate compared the incoming/preliminary
transient estimate alone against `TRANSIENT_GATE_BYTES` (32 MiB) --
never adding `aggregate_existing_retained_bytes`, even though the
AUTHORITATIVE, post-full-read `resource_estimator.evaluate_cumulative_
admission` already adds that same figure to its own transient sum
(interpretation B, Correction3). A request whose preliminary transient
estimate alone stayed under the gate could therefore still trigger the
one full bounded read (`f.read(runtime_cap_bytes + 1)`) before the
later, correctly-aggregated Stage 3 check finally refused it.

Independently reproduced here, byte-for-byte, against the real
`fixtures_ab/generation_a.sfmsidecar` fixture (610 bytes, 3 real
occurrences), requesting 2 folds (`left`, `right`), runtime_cap_bytes
= 16 MiB, aggregate_existing_retained_bytes = 10 MiB:

    preliminary incoming transient  = 23,075,300 B
    existing retained               = 10,485,760 B (10 MiB)
    aggregate transient             = 33,561,060 B
    TRANSIENT_GATE_BYTES            = 33,554,432 B (32 MiB)

-- exactly the independent audit's cited figures. Against the buggy
Correction4 code (`candidate_b2c_correction4/`), this scenario is
ADMITTED at the preliminary stage (23,075,300 <= 32 MiB alone), the one
full bounded read runs (`full_bounded_read_call_count == 1`), and ONLY
THEN does the Stage 3 authoritative check refuse it
(`cumulative_transient_exceeds_gate`, total_transient=33,561,060). Against
the corrected Correction5 code (`candidate_b2c_correction5/`), the
SAME scenario is refused at the PRELIMINARY stage itself
(`preliminary_estimated_transient`), with `full_bounded_read_call_count
== 0` -- the full read never happens.

This test asserts BOTH sides of that contrast directly (it imports and
exercises BOTH candidate packages), so it fails against the unfixed
6e942f6 code and passes only with the Correction5 change -- and it can
never be satisfied by the OTHER, already-existing refusal path
(`cumulative_transient_exceeds_gate`, which only ever fires AFTER the
full read) alone; it specifically requires the refusal reason to be
`preliminary_estimated_transient` (or `preliminary_estimated_retained`,
if some case's retained gate fired first -- never used by the cases
here) and `full_bounded_read_call_count == 0`.

Because `candidate_open_and_identify_with_preflight` raises BEFORE
`BoundedProvider._open_from_buf` (the sole entry point into the frozen
structural validator, cohort/view-cache publication, or any generation
mutation) is ever called, `inst.validator_call_count == 0` on every
pre-read refusal here is direct, positive proof that no validator work,
no view/cache publication, and no generation-state mutation occurred --
that code path is simply never reached. This test calls the preflight
primitive directly with an explicit `aggregate_existing_retained_bytes`
argument -- the SAME parameter name/shape the broker's own aggregate
ledger already supplies to this exact function at both call sites in
`selection.py`; no second, independent notion of retained authority is
introduced by this test or by the fix it verifies.

Astra Narrow Issue E: paths derived from `__file__`.
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
CORRECTION4_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction4")
CORRECTION5_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction5")
FIXROOT_AB = os.path.join(CORRECTION5_ROOT, "fixtures_ab")

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(os.path.join(FIXROOT_AB, "manifest.json")) as f:
    MANIFEST = json.load(f)

ARTIFACT_PATH = os.path.join(FIXROOT_AB, MANIFEST["generation_a"]["artifact_relative_path"])
EXPECTED_SHA = MANIFEST["generation_a"]["master_sha256"]  # arbitrary but fixed; the scenario never
                                                           # reaches source-generation comparison
RUNTIME_CAP_BYTES = 16 * 1024 * 1024
REQUESTED_FOLDS = {"normalizer": [b"left", b"right"]}

TRANSIENT_GATE_BYTES = 32 * 1024 * 1024
RETAINED_GATE_BYTES = 16 * 1024 * 1024

# Exact independent-audit figures, reproduced fresh by this test (not
# hardcoded blindly) -- see the module docstring.
DECISIVE_EXISTING_RETAINED_BYTES = 10 * 1024 * 1024        # 10,485,760
EXPECTED_PRELIM_TRANSIENT = 23075300
EXPECTED_AGGREGATE_TRANSIENT = DECISIVE_EXISTING_RETAINED_BYTES + EXPECTED_PRELIM_TRANSIENT


def _fresh_import(root_dir):
    """Imports `sfm_master_authority_productionized` fresh FROM `root_dir`,
    evicting any previously imported copy first -- so candidate4's and
    candidate5's same-named packages never collide in sys.modules."""
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority_productionized" or name.startswith("sfm_master_authority_productionized."):
            del sys.modules[name]
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    else:
        sys.path.remove(root_dir)
        sys.path.insert(0, root_dir)
    import sfm_master_authority_productionized.resource_preflight as rp
    import sfm_master_authority_productionized.errors as errors
    return rp, errors


def attempt(rp, errors, existing_retained_bytes, artifact_path=None):
    """Runs the exact decisive scenario against one candidate's
    `resource_preflight` module. Returns a dict of observable facts --
    never re-raises, so callers can assert on the outcome either way."""
    inst = None
    provider = None
    outcome = None
    try:
        provider, identity, inst = rp.candidate_open_and_identify_with_preflight(
            artifact_path or ARTIFACT_PATH, EXPECTED_SHA, RUNTIME_CAP_BYTES,
            requested_folds_by_consumer=REQUESTED_FOLDS,
            aggregate_existing_retained_bytes=existing_retained_bytes,
        )
        outcome = "admitted"
    except errors.ResourceAdmissionRefusal as exc:
        inst = getattr(exc, "instrumentation", None)
        outcome = "refused"
    finally:
        if provider is not None:
            provider.close()
    return {
        "outcome": outcome,
        "reason": getattr(inst, "reason", None) if inst is not None else None,
        "full_bounded_read_call_count": getattr(inst, "full_bounded_read_call_count", None) if inst is not None else None,
        "validator_call_count": getattr(inst, "validator_call_count", None) if inst is not None else None,
        "file_open_count": getattr(inst, "file_open_count", None) if inst is not None else None,
        "file_close_count": getattr(inst, "file_close_count", None) if inst is not None else None,
        "cumulative_admission": getattr(inst, "cumulative_admission", None) if inst is not None else None,
    }


# ===========================================================================
# Section 4: the decisive test -- must fail against 6e942f6 (Correction4),
# pass only with Correction5.
# ===========================================================================

rp4, errors4 = _fresh_import(CORRECTION4_ROOT)
c4_fixture = os.path.join(CORRECTION4_ROOT, "fixtures_ab", MANIFEST["generation_a"]["artifact_relative_path"])
result_c4 = attempt(rp4, errors4, DECISIVE_EXISTING_RETAINED_BYTES, artifact_path=c4_fixture)
print("[decisive/correction4(unfixed)] %s" % json.dumps(result_c4, sort_keys=True, default=repr))

check("decisive.c4.0 (documenting the bug) Correction4 code ADMITS this exact scenario at the "
      "preliminary stage and performs the full bounded read once before Stage 3 refuses it",
      result_c4["outcome"] == "refused" and result_c4["full_bounded_read_call_count"] == 1, result_c4)
check("decisive.c4.1 (documenting the bug) Correction4's refusal reason is the POST-read "
      "cumulative check, never the pre-read preliminary one",
      result_c4["reason"] == "cumulative_transient_exceeds_gate", result_c4)
check("decisive.c4.2 (documenting the bug) Correction4's Stage 3 aggregate transient equals the "
      "exact independent-audit figure",
      result_c4["cumulative_admission"] is not None
      and result_c4["cumulative_admission"]["total_transient_bytes"] == EXPECTED_AGGREGATE_TRANSIENT, result_c4)

rp5, errors5 = _fresh_import(CORRECTION5_ROOT)
result_c5 = attempt(rp5, errors5, DECISIVE_EXISTING_RETAINED_BYTES)
print("[decisive/correction5(fixed)] %s" % json.dumps(result_c5, sort_keys=True, default=repr))

check("decisive.c5.0 Correction5 refuses the identical scenario",
      result_c5["outcome"] == "refused", result_c5)
check("decisive.c5.1 refusal reason clearly indicates the PRE-READ preliminary/aggregate transient "
      "gate (never the alternate post-read cumulative_transient_exceeds_gate path)",
      result_c5["reason"] == "preliminary_estimated_transient", result_c5)
check("decisive.c5.2 full_bounded_read_call_count == 0 -- the full read never happened",
      result_c5["full_bounded_read_call_count"] == 0, result_c5)
check("decisive.c5.3 validator_call_count == 0 -- the frozen structural validator (BoundedProvider."
      "_open_from_buf, the sole route into view/cache publication and generation mutation) was "
      "never entered",
      result_c5["validator_call_count"] == 0, result_c5)
check("decisive.c5.4 no cumulative_admission was ever computed -- Stage 3 (which is the only place "
      "cache/ledger/generation state could be touched downstream) was never reached",
      result_c5["cumulative_admission"] is None, result_c5)
check("decisive.c5.5 file was opened and closed exactly once (header/directory reads only -- no "
      "second open, no leaked handle)",
      result_c5["file_open_count"] == 1 and result_c5["file_close_count"] == 1, result_c5)


# ===========================================================================
# Section 5: boundary matrix -- all against the FIXED Correction5 code.
# ===========================================================================

# --- A. zero retained ---
result_a = attempt(rp5, errors5, 0)
check("boundary.A zero existing retained: pre-read aggregate remains under gate, full read "
      "proceeds normally", result_a["outcome"] == "admitted" and result_a["full_bounded_read_call_count"] == 1, result_a)
check("boundary.A validator was reached (normal admitted path, unchanged later behavior)",
      result_a["validator_call_count"] == 1, result_a)

# --- B. small retained, still comfortably under ---
SMALL_RETAINED = 5 * 1024 * 1024
assert SMALL_RETAINED + EXPECTED_PRELIM_TRANSIENT < TRANSIENT_GATE_BYTES
result_b = attempt(rp5, errors5, SMALL_RETAINED)
check("boundary.B small existing retained (%d B) still under gate: full read proceeds" % SMALL_RETAINED,
      result_b["outcome"] == "admitted" and result_b["full_bounded_read_call_count"] == 1, result_b)

# --- C. exact boundary: one byte below / exactly at / one byte above the gate ---
# existing_needed derived from EXPECTED_PRELIM_TRANSIENT so the aggregate total lands exactly
# on TRANSIENT_GATE_BYTES + delta, independent of any hardcoded absolute existing-bytes figure.
one_below_existing = (TRANSIENT_GATE_BYTES - 1) - EXPECTED_PRELIM_TRANSIENT
exact_existing = TRANSIENT_GATE_BYTES - EXPECTED_PRELIM_TRANSIENT
one_above_existing = (TRANSIENT_GATE_BYTES + 1) - EXPECTED_PRELIM_TRANSIENT

result_one_below = attempt(rp5, errors5, one_below_existing)
check("boundary.C.one-byte-below (aggregate == gate-1): admitted, full read proceeds",
      result_one_below["outcome"] == "admitted" and result_one_below["full_bounded_read_call_count"] == 1,
      (one_below_existing, result_one_below))

result_exact = attempt(rp5, errors5, exact_existing)
check("boundary.C.exact (aggregate == gate exactly): ADMITTED -- this project's existing gate "
      "comparison semantics are strict '>' (see resource_estimator.evaluate_cumulative_admission's "
      "own 'combined_retained_bytes > retained_gate_bytes' / 'total_transient_bytes > "
      "transient_gate_bytes'), so == gate is NOT a refusal; this fix's new preliminary comparison "
      "('prelim_total_transient > TRANSIENT_GATE_BYTES') uses the SAME strict operator, "
      "consistent with the existing contract",
      result_exact["outcome"] == "admitted" and result_exact["full_bounded_read_call_count"] == 1,
      (exact_existing, result_exact))

result_one_above = attempt(rp5, errors5, one_above_existing)
check("boundary.C.one-byte-above (aggregate == gate+1): refused at the PRE-READ stage, zero full reads",
      result_one_above["outcome"] == "refused"
      and result_one_above["reason"] == "preliminary_estimated_transient"
      and result_one_above["full_bounded_read_call_count"] == 0,
      (one_above_existing, result_one_above))

# --- D. high retained: 10, 11, 12, 15 MiB -- all must refuse pre-read, zero full reads ---
for mib in (10, 11, 12, 15):
    existing = mib * 1024 * 1024
    result_d = attempt(rp5, errors5, existing)
    check("boundary.D.%dMiB existing retained: aggregate preliminary transient exceeds gate -> "
          "zero full reads, immediate pre-read refusal" % mib,
          result_d["outcome"] == "refused"
          and result_d["reason"] == "preliminary_estimated_transient"
          and result_d["full_bounded_read_call_count"] == 0,
          (existing, result_d))


print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
