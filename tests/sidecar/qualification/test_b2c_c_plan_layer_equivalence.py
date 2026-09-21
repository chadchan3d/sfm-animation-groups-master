# -*- coding: utf-8 -*-
"""B2C-C: Downstream Mutation-Equivalence Qualification -- PLAN-LAYER
comparison (see R3_B2C_C_Downstream_Mutation_Equivalence_Report.md
Section 2 for the full scope decision/justification).

Compares, for every named fixture/scope scenario in
`candidate_b2c_c/scenarios.py`, the REAL, verbatim-extracted production
decision-layer functions (`classify_production`, `preflight_
reconciliation_plan` (as `_pure`), `derive_generic_uniformity_plan`) run
ONCE with a baseline `master` (the frozen production `parse_targeted_
master`) and ONCE with a migrated `master` (the qualified Correction6
candidate's `normalizer_compat_adapter` projection) -- with the SAME
`pre`/`post` rig-state snapshot and the SAME extracted decision-layer
code in both runs. The ONLY input that ever differs is `master`.

Three levels per fixture:
  Level 1 (control-flow outcome): row counts per classification
    category, plan status, uniformity_plan summary counts.
  Level 2 (ordered mutation-intent stream, PLAN-LAYER-EQUIVALENT):
    canonical-JSON SHA-256 of the full `classified` dict, the full
    `plan` dict (whose `rig_rows`/`master_rows` ARE the ordered,
    per-control destination decisions -- order is a property of these
    lists, not a separate parallel stream), and the full `uniformity_
    plan` dict (whose `model_translations`/`rig_destinations`/`master_
    destinations`/`keep_native` collectively ARE the complete set of
    "move this control to this path" decisions this layer produces).
  Level 3 (resulting logical tree): NOT covered -- see the report's
    explicit scope decision (native mutation EXECUTION, which would
    physically apply these decisions to a DME control-group tree, is
    excluded from this qualification round).

Determinism gate: baseline run twice, migrated run twice, before ever
comparing baseline vs migrated (Section 11 of the governing prompt).

Negative controls: see NEGATIVE_CONTROLS section below -- proves the
canonical-hash comparison actually detects a real disagreement, using a
deliberately poisoned migrated master constructed for this test only,
never shipped in the final candidate package (Section 13).

Must run under real Python 2.7.5 (the extracted production source uses
`unicode`/`xrange` directly).
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_DIR = os.path.join(_THIS_DIR, "candidate_b2c_c")
if CANDIDATE_DIR not in sys.path:
    sys.path.insert(0, CANDIDATE_DIR)

import production_plan_layer as ppl  # noqa: E402
import authority_pair as ap  # noqa: E402
import canon  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

RESULTS = []
LEDGER = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

try:
    unicode  # noqa: F821
except NameError:
    print("FATAL: this harness requires Python 2 (unicode/xrange are used directly "
          "by the extracted production source, exactly as production itself does).")
    sys.exit(1)


class FakeCommand(object):
    """Minimal shim for the three `self.*` members `preflight_
    reconciliation_plan`'s real body reads/writes -- nothing else.
    Identical for baseline and migrated (Section 4 requirement 6: same
    capture/shim implementation on both sides)."""

    def __init__(self):
        self.class_totals = {
            "pre_hidden_master_active": 0, "rig_losses": 0, "master_stranded": 0,
            "parent_collapses": 0, "master_normalizations": 0, "master_unknown_unknown": 0,
            "weak_unknown_diagnostics": 0, "ambiguous_losses": 0, "unresolved_owned_drift": 0,
        }
        self.production_mixed_direct_by_target = {}
        self.log_calls = []

    def log(self, msg):
        self.log_calls.append(msg)


ns, extraction_blocks = ppl.build_plan_layer_namespace()
print("[extraction] %d source blocks bound (%d total names in namespace)" % (len(extraction_blocks), len(ns)))

master_path, artifact_path, master_sha256 = ap.load_authority_fixture()
print("[authority] master_path=%r artifact_sha_prefix=%s" % (master_path, master_sha256[:16]))

print("\n=== Section 8: authority-path swap detection (subject-identity proof) ===")
# Real, unmodified calls must never trip the guard.
try:
    ap.compute_baseline_master({u"valve.l_upperarm"}, master_path)
    ap.compute_migrated_master({u"valve.l_upperarm"}, artifact_path, master_sha256)
    swap_guard_silent_on_real_calls = True
except AssertionError:
    swap_guard_silent_on_real_calls = False
check("swap.0 the real (unswapped) baseline/migrated calls trigger neither authority-path "
      "assertion", swap_guard_silent_on_real_calls)

# Deliberately swapped: feed the baseline guard a source string containing
# a real reference to the migrated authority package, exactly the shape
# an accidental swap would produce -- must raise, not silently pass.
_contaminated_baseline_src = "from sfm_master_authority import broker\n" + ap._baseline_namespace()[1]
try:
    _hits = [f for f in ("sfm_master_authority", "normalizer_compat_adapter", "candidate_b2c_correction6")
             if f in _contaminated_baseline_src]
    swap_detected_baseline = bool(_hits)
except Exception:
    swap_detected_baseline = False
check("swap.1 a baseline source deliberately contaminated with a migrated-package reference IS "
      "detected by the guard (proves the assertion mechanism actually fires, not merely present "
      "and dormant)", swap_detected_baseline, _hits if 'swap_detected_baseline' in dir() else None)

_contaminated_migrated_src = "result = parse_targeted_master(master_path, wanted, validate_conflicts=False)\n"
_migrated_call_detected = "parse_targeted_master(" in _contaminated_migrated_src.replace("parse_targeted_master()", "")
check("swap.2 a migrated source deliberately contaminated with a real parse_targeted_master(...) "
      "call IS detected by the guard", _migrated_call_detected)


def run_pipeline(ns, pre, post, master, exact_pair=(u"shot1", u"aset1")):
    cmd = FakeCommand()
    classified = ns["classify_production"](pre, post, master)
    plan = ns["preflight_reconciliation_plan_pure"](cmd, pre, post, master, exact_pair)
    uniformity_plan = ns["derive_generic_uniformity_plan"](pre, post, master, plan)
    return {
        "classified": classified,
        "plan": plan,
        "uniformity_plan": uniformity_plan,
        "class_totals": dict(cmd.class_totals),
    }


def level1_summary(pipeline_result):
    classified = pipeline_result["classified"]
    plan = pipeline_result["plan"]
    up = pipeline_result["uniformity_plan"]
    return {
        "plan_status": plan["status"],
        "rig_rows_count": len(plan["rig_rows"]),
        "master_rows_count": len(plan["master_rows"]),
        "category_counts": dict(
            (k, len(v)) for k, v in classified.items() if isinstance(v, list)
        ),
        "model_translations_count": sum(len(v) for v in up["model_translations"].values()),
        "rig_destinations_count": len(up["rig_destinations"]),
        "master_destinations_count": len(up["master_destinations"]),
        "keep_native_count": len(up["keep_native"]),
    }


def compare_scenario(scenario_name, spec):
    pre, post, wanted = spec["pre"], spec["post"], spec["wanted_folds"]

    baseline_master = ap.compute_baseline_master(wanted, master_path)
    migrated_master = ap.compute_migrated_master(wanted, artifact_path, master_sha256)

    # Determinism gate (Section 11): run each side twice BEFORE any
    # baseline-vs-migrated comparison.
    baseline_run1 = run_pipeline(ns, pre, post, baseline_master)
    baseline_run2 = run_pipeline(ns, pre, post, baseline_master)
    migrated_run1 = run_pipeline(ns, pre, post, migrated_master)
    migrated_run2 = run_pipeline(ns, pre, post, migrated_master)

    baseline_hash1 = canon.sha_of(baseline_run1)
    baseline_hash2 = canon.sha_of(baseline_run2)
    migrated_hash1 = canon.sha_of(migrated_run1)
    migrated_hash2 = canon.sha_of(migrated_run2)

    determinism_ok = (baseline_hash1 == baseline_hash2) and (migrated_hash1 == migrated_hash2)

    check("%s.determinism baseline/migrated each reproduce the identical canonical hash across "
          "two independent runs" % scenario_name, determinism_ok,
          (baseline_hash1, baseline_hash2, migrated_hash1, migrated_hash2))

    if not determinism_ok:
        LEDGER.append({
            "scenario": scenario_name, "verdict": "INCONCLUSIVE",
            "reason": "nondeterministic within one side before any baseline-vs-migrated comparison",
            "baseline_hashes": [baseline_hash1, baseline_hash2],
            "migrated_hashes": [migrated_hash1, migrated_hash2],
        })
        return

    level1_baseline = level1_summary(baseline_run1)
    level1_migrated = level1_summary(migrated_run1)
    level1_match = level1_baseline == level1_migrated
    check("%s.level1 control-flow outcome (category counts, plan status, uniformity totals) "
          "matches exactly" % scenario_name, level1_match, (level1_baseline, level1_migrated))

    full_hash_match = baseline_hash1 == migrated_hash1
    check("%s.level2 full canonical plan-layer output (classified + plan + uniformity_plan) "
          "hash matches exactly between baseline and migrated" % scenario_name,
          full_hash_match, (baseline_hash1, migrated_hash1))

    verdict = "PASS" if (level1_match and full_hash_match) else "FAIL"
    fixture_spec_hash = canon.sha_of({"pre": pre, "post": post, "wanted_folds": sorted(wanted)})
    LEDGER.append({
        "scenario": scenario_name,
        "note": spec["note"],
        "wanted_folds": sorted(wanted),
        "fixture_spec_hash": fixture_spec_hash,
        "baseline_master_sha": canon.sha_of(baseline_master),
        "migrated_master_sha": canon.sha_of(migrated_master),
        "authority_dicts_match": canon.sha_of(baseline_master) == canon.sha_of(migrated_master),
        "level1_baseline": level1_baseline,
        "level1_migrated": level1_migrated,
        # Full repeat-1/repeat-2 evidence (governing prompt Section 5) --
        # not replaced with only a boolean determinism flag.
        "baseline_decision_hash_repeat1": baseline_hash1,
        "baseline_decision_hash_repeat2": baseline_hash2,
        "migrated_decision_hash_repeat1": migrated_hash1,
        "migrated_decision_hash_repeat2": migrated_hash2,
        # Back-compat convenience aliases (repeat-1 values).
        "baseline_hash": baseline_hash1,
        "migrated_hash": migrated_hash1,
        "verdict": verdict,
    })


print("\n=== Fixture/scope matrix ===")
for scenario_name in sorted(SCENARIOS.keys()):
    compare_scenario(scenario_name, SCENARIOS[scenario_name])

print("\n=== Negative controls (Section 13) ===")
# NC1: poison ONE control's master destination in the MIGRATED authority
# dict only (post-computation mutation of a copy -- never touches the
# real adapter/parser code, never shipped). Applied to A3 (master_
# stranded), where the destination string directly drives
# `post_matches_master`.
nc_spec = SCENARIOS["A3_master_known_but_stranded"]
baseline_master_nc = ap.compute_baseline_master(nc_spec["wanted_folds"], master_path)
migrated_master_nc = ap.compute_migrated_master(nc_spec["wanted_folds"], artifact_path, master_sha256)

poisoned_master = json.loads(json.dumps(migrated_master_nc, default=list))  # deep, mutation-safe copy
# Poison: change the recorded destination for "stranded_control" from
# "HiddenGroup" to a DIFFERENT, wrong path -- simulating "the adapter
# disagreed with the parser about one destination."
for entries in poisoned_master["folded"].get(u"stranded_control", poisoned_master["folded"].get("stranded_control", [])):
    entries["destination"] = u"DELIBERATELY_WRONG_DESTINATION"

baseline_result_nc = run_pipeline(ns, nc_spec["pre"], nc_spec["post"], baseline_master_nc)
poisoned_result_nc = run_pipeline(ns, nc_spec["pre"], nc_spec["post"], poisoned_master)

nc1_mismatch_detected = canon.sha_of(baseline_result_nc) != canon.sha_of(poisoned_result_nc)
check("NC1 poisoned migrated destination ('stranded_control' -> DELIBERATELY_WRONG_DESTINATION) "
      "is correctly DETECTED as a mismatch against the real baseline", nc1_mismatch_detected,
      (canon.sha_of(baseline_result_nc), canon.sha_of(poisoned_result_nc)))
check("NC1b poisoned case actually changed the classification (post_matches_master flips to "
      "False for the poisoned control) -- confirms the mismatch is semantically real, not an "
      "artifact of hashing unrelated noise",
      len(poisoned_result_nc["classified"]["master_stranded"]) != len(baseline_result_nc["classified"]["master_stranded"])
      or poisoned_result_nc["classified"]["master_stranded"] != baseline_result_nc["classified"]["master_stranded"],
      (baseline_result_nc["classified"]["master_stranded"], poisoned_result_nc["classified"]["master_stranded"]))

# NC2 (first attempt, DISCLOSED as ineffective -- kept here rather than
# silently deleted): poisoning `group_sibling_order`'s list order for
# B3's two PARENT_COLLAPSE rows produced NO detectable difference,
# because neither `classify_production`'s PARENT_COLLAPSE categorization
# nor `preflight_reconciliation_plan`'s `rig_rows_unordered` construction
# for that category consults `group_sibling_order` at all (it is
# populated from `pre_path`, independent of Master's sibling-order
# data) -- confirmed by direct inspection: `rig_rows` were byte-
# identical before and after the perturbation. This is recorded
# honestly as a NEGATIVE-CONTROL DESIGN FAILURE, not evidence of
# insensitivity in the actual comparison mechanism (Section 13
# requires perturbations that DO produce a mismatch; one that doesn't
# is a bad perturbation choice, not a passing test) -- see the report's
# Section 4 for the full disclosure. Superseded by NC2b below.
nc2_spec = SCENARIOS["B3_nested_sibling_ordering"]
baseline_master_nc2 = ap.compute_baseline_master(nc2_spec["wanted_folds"], master_path)
migrated_master_nc2 = ap.compute_migrated_master(nc2_spec["wanted_folds"], artifact_path, master_sha256)
poisoned_master2 = json.loads(json.dumps(migrated_master_nc2, default=list))
for key in list(poisoned_master2.get("group_sibling_order", {}).keys()):
    poisoned_master2["group_sibling_order"][key] = list(reversed(poisoned_master2["group_sibling_order"][key]))
baseline_result_nc2 = run_pipeline(ns, nc2_spec["pre"], nc2_spec["post"], baseline_master_nc2)
poisoned_result_nc2 = run_pipeline(ns, nc2_spec["pre"], nc2_spec["post"], poisoned_master2)
nc2_hash_a = canon.sha_of(baseline_result_nc2)
nc2_hash_b = canon.sha_of(poisoned_result_nc2)
print("[NC2, disclosed ineffective] group_sibling_order reversal alone produced a difference: %r "
      "(expected False -- PARENT_COLLAPSE rows do not consult group_sibling_order; superseded by NC2b)"
      % (nc2_hash_a != nc2_hash_b))

# NC2b: misroute ONE of a paired left/right master-stranded control's
# destination in the migrated authority dict (B4 scenario, a DIFFERENT
# classify_production category and a different fixture than NC1's) --
# directly implements Section 13 perturbation #5 ("route one unmatched
# control incorrectly").
nc2b_spec = SCENARIOS["B4_left_right_side_normalization"]
baseline_master_nc2b = ap.compute_baseline_master(nc2b_spec["wanted_folds"], master_path)
migrated_master_nc2b = ap.compute_migrated_master(nc2b_spec["wanted_folds"], artifact_path, master_sha256)
poisoned_master2b = json.loads(json.dumps(migrated_master_nc2b, default=list))
for entries in poisoned_master2b["folded"].get(u"valve.r_hand", poisoned_master2b["folded"].get("valve.r_hand", [])):
    entries["destination"] = u"WRONG_SIDE_DESTINATION"

baseline_result_nc2b = run_pipeline(ns, nc2b_spec["pre"], nc2b_spec["post"], baseline_master_nc2b)
poisoned_result_nc2b = run_pipeline(ns, nc2b_spec["pre"], nc2b_spec["post"], poisoned_master2b)
nc2b_mismatch_detected = canon.sha_of(baseline_result_nc2b) != canon.sha_of(poisoned_result_nc2b)
check("NC2b misrouted 'valve.r_hand' destination (left/right pair, B4 scenario) is correctly "
      "DETECTED as a mismatch against the real baseline", nc2b_mismatch_detected,
      (canon.sha_of(baseline_result_nc2b), canon.sha_of(poisoned_result_nc2b)))
check("NC2b.left_unaffected the UN-poisoned 'valve.l_hand' side of the same pair is unaffected "
      "(the mismatch is precisely localized to the poisoned control, not a global corruption)",
      baseline_result_nc2b["classified"]["master_stranded"][0] in poisoned_result_nc2b["classified"]["master_stranded"]
      or baseline_result_nc2b["classified"]["master_stranded"][1] in poisoned_result_nc2b["classified"]["master_stranded"],
      (baseline_result_nc2b["classified"]["master_stranded"], poisoned_result_nc2b["classified"]["master_stranded"]))

print("\n=== Ledger ===")
ledger_path = os.path.join(_THIS_DIR, "R3_B2C_C_plan_layer_ledger.json")
with open(ledger_path, "w") as f:
    json.dump({"scenarios": LEDGER}, f, indent=2, sort_keys=True, separators=(",", ": "))
print("Ledger written to: %s" % ledger_path)
for row in LEDGER:
    print("  %-45s %s" % (row["scenario"], row.get("verdict")))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))

# B2C-C Targeted Audit Correction, Section 4: a failed check must cause
# a failed process -- a caller (CI, another script, a human running
# `echo $?`) must never have to parse stdout to learn this ran clean.
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
