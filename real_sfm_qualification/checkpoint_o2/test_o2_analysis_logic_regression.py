# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint O2's own per-target branch-classification
and equivalence-witness analysis logic
(Checkpoint_O2_Bounded_Phase_Attribution.py, SHA-256
4eaa8e87356e65c127a8744949e956056b0a18f5a2e65907efd3430e8dd9c4fc).

Extracts the deployed script's own analysis block VERBATIM (by exact line
range, pinned below, dedented and wrapped in a callable function so it can
be exercised with synthetic capture-event data -- the underlying
per-target/branch/witness LOGIC is identical to what the real script runs;
only the surrounding indentation is adjusted to make it a standalone
function) and proves, offline, under the real embedded Python 2.7.5:

  1. A target whose captures are exactly {PRE, NATIVE_POST} is classified
     "native_only_fallback".
  2. A target whose captures include PRODUCTION_GENERIC_COMPOSER_PRE is
     classified "reconciled", regardless of what else is present.
  3. An incomplete/anomalous capture set (e.g. only PRE) is classified
     "unknown", not silently misclassified as native_only_fallback.
  4. composer_before_vs_outer_post_witness correctly reports
     EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION when the two
     captures' aggregate hashes match, NOT_EQUIVALENT when they differ,
     and FRESHNESS_OR_EXCEPTION_SEMANTICS_UNRESOLVED when either capture
     is missing.
  5. composer_after_vs_terminal_witness is only computed for the
     reconciled branch; native-only-fallback targets get the explicit
     UNRESOLVED_NATIVE_ONLY_FALLBACK_NO_TERMINAL_COMPARISON sentinel
     instead of a potentially-misleading comparison.
  6. field_diff() correctly identifies WHICH per-field hashes differ
     between two captures (not just the aggregate hash), and returns
     None when either capture is missing.
  7. The classification_planning_gap_seconds / contextual_writes_gap_seconds
     derived-timing fields are computed correctly from the real event
     timestamps, and are None when the relevant captures are absent.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_o2_analysis_logic_regression.py
"""
import hashlib
import json
import os
import sys

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_O2_Bounded_Phase_Attribution.py")
EXPECTED_SCRIPT_SHA256 = "4eaa8e87356e65c127a8744949e956056b0a18f5a2e65907efd3430e8dd9c4fc"

ANALYSIS_BLOCK_RANGE = (792, 856)  # capture_events = [...] through the closing per_target_summary[...] = { ... }

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


with open(SCRIPT_PATH, "rb") as f:
    script_bytes = f.read()
script_sha256 = hashlib.sha256(script_bytes).hexdigest()
expect(script_sha256 == EXPECTED_SCRIPT_SHA256, "deployed_script.sha256_matches_pinned (%s)" % script_sha256)

script_lines = script_bytes.decode("ascii").splitlines()
start, end = ANALYSIS_BLOCK_RANGE
raw_block_lines = script_lines[start - 1:end]

# Dedent by exactly 8 spaces (the block's real indentation inside
# `try: / for ordinal... :`), then wrap as a standalone function taking
# `events` and returning `per_target_summary` -- the LOGIC is verbatim;
# only the enclosing scope changes, from "inside the per-command loop"
# to "a plain callable," so this can be exercised with synthetic input.
dedented = []
for line in raw_block_lines:
    if line.startswith("        "):
        dedented.append(line[8:])
    elif line.strip() == "":
        dedented.append(line)
    else:
        raise AssertionError("Line does not have the expected 8-space indentation: %r" % (line,))

function_source = "def compute_per_target_summary(events):\n" + "\n".join("    " + l if l.strip() else l for l in dedented) + "\n    return per_target_summary\n"

ns = {}
exec(compile(function_source, "<o2_analysis_block_extracted>", "exec"), ns)
compute_per_target_summary = ns["compute_per_target_summary"]

sys.stdout.write("\n--- Branch classification ---\n")


def make_capture(target, label, start_t, end_t, aggregate_hash, per_field_hashes=None):
    return {
        "kind": "capture_snapshot_explicit",
        "target": target,
        "label": label,
        "start": start_t,
        "end": end_t,
        "elapsed": end_t - start_t,
        "aggregate_hash": aggregate_hash,
        "per_field_hashes": per_field_hashes or {},
    }


events_native_only = [
    make_capture("foxmccouldwm1", "PRE", 0.0, 0.1, "hashA"),
    make_capture("foxmccouldwm1", "NATIVE_POST", 0.2, 0.3, "hashB"),
]
summary1 = compute_per_target_summary(events_native_only)
expect(summary1["foxmccouldwm1"]["branch"] == "native_only_fallback", "branch.exactly_PRE_and_NATIVE_POST_is_native_only_fallback")
expect(summary1["foxmccouldwm1"]["capture_count"] == 2, "branch.native_only_fallback_capture_count_is_2")

events_reconciled = [
    make_capture("mia1", "PRE", 0.0, 0.1, "h1"),
    make_capture("mia1", "NATIVE_POST", 0.2, 0.3, "h2"),
    make_capture("mia1", "PRODUCTION_GENERIC_COMPOSER_PRE", 0.4, 0.5, "h2"),
    make_capture("mia1", "PRODUCTION_GENERIC_COMPOSER_POST", 0.6, 0.7, "h3"),
    make_capture("mia1", "PRODUCTION_SEMANTIC_FINGERPRINT", 0.8, 0.9, "h3"),
]
summary2 = compute_per_target_summary(events_reconciled)
expect(summary2["mia1"]["branch"] == "reconciled", "branch.presence_of_composer_pre_is_reconciled_regardless_of_rest")
expect(summary2["mia1"]["capture_count"] == 5, "branch.reconciled_capture_count_is_5")

events_anomalous = [make_capture("weird_target", "PRE", 0.0, 0.1, "hX")]
summary3 = compute_per_target_summary(events_anomalous)
expect(summary3["weird_target"]["branch"] == "unknown", "branch.incomplete_capture_set_is_unknown_not_misclassified")

sys.stdout.write("\n--- composer_before_vs_outer_post_witness ---\n")

expect(
    summary2["mia1"]["composer_before_vs_outer_post_witness"] == "EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION",
    "witness.matching_aggregate_hashes_report_equivalent (NATIVE_POST=h2, COMPOSER_PRE=h2)",
)

events_reconciled_not_equal = [
    make_capture("target_x", "PRE", 0.0, 0.1, "h1"),
    make_capture("target_x", "NATIVE_POST", 0.2, 0.3, "h2"),
    make_capture("target_x", "PRODUCTION_GENERIC_COMPOSER_PRE", 0.4, 0.5, "h2_DIFFERENT"),
    make_capture("target_x", "PRODUCTION_GENERIC_COMPOSER_POST", 0.6, 0.7, "h3"),
    make_capture("target_x", "PRODUCTION_SEMANTIC_FINGERPRINT", 0.8, 0.9, "h3"),
]
summary4 = compute_per_target_summary(events_reconciled_not_equal)
expect(
    summary4["target_x"]["composer_before_vs_outer_post_witness"] == "NOT_EQUIVALENT",
    "witness.differing_aggregate_hashes_report_not_equivalent",
)

summary_no_composer = compute_per_target_summary(events_native_only)
expect(
    summary_no_composer["foxmccouldwm1"]["composer_before_vs_outer_post_witness"] == "FRESHNESS_OR_EXCEPTION_SEMANTICS_UNRESOLVED",
    "witness.missing_composer_pre_capture_reports_unresolved_not_a_false_match",
)

sys.stdout.write("\n--- composer_after_vs_terminal_witness ---\n")

expect(
    summary2["mia1"]["composer_after_vs_terminal_witness"] == "EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION",
    "witness.reconciled_target_with_matching_hashes_reports_equivalent (COMPOSER_POST=h3, TERMINAL=h3)",
)
expect(
    summary1["foxmccouldwm1"]["composer_after_vs_terminal_witness"] == "UNRESOLVED_NATIVE_ONLY_FALLBACK_NO_TERMINAL_COMPARISON",
    "witness.native_only_fallback_target_never_gets_a_misleading_terminal_comparison",
)

sys.stdout.write("\n--- field_diff ---\n")

events_field_diff = [
    make_capture("target_y", "NATIVE_POST", 0.2, 0.3, "agg1", {"rig_status": "s1", "groups": "g1", "memberships": "m1"}),
    make_capture("target_y", "PRODUCTION_GENERIC_COMPOSER_PRE", 0.4, 0.5, "agg2", {"rig_status": "s1", "groups": "g2", "memberships": "m1"}),
]
summary5 = compute_per_target_summary(events_field_diff)
diffs = summary5["target_y"]["composer_before_vs_outer_post_field_diffs"]
expect(diffs is not None and set(diffs.keys()) == {"groups"}, "field_diff.identifies_exactly_the_differing_field", diffs)
expect(diffs["groups"] == {"a": "g1", "b": "g2"}, "field_diff.reports_both_sides_values_for_the_differing_field", diffs["groups"])

summary_missing = compute_per_target_summary([make_capture("target_z", "NATIVE_POST", 0.2, 0.3, "agg1")])
expect(
    summary_missing["target_z"]["composer_before_vs_outer_post_field_diffs"] is None,
    "field_diff.returns_None_when_a_capture_is_missing_not_a_spurious_empty_dict",
)

sys.stdout.write("\n--- derived timing gaps ---\n")

expect(
    abs(summary2["mia1"]["classification_planning_gap_seconds"] - (0.4 - 0.3)) < 1e-9,
    "timing.classification_planning_gap_is_composer_pre_start_minus_native_post_end",
    summary2["mia1"]["classification_planning_gap_seconds"],
)
expect(
    abs(summary2["mia1"]["contextual_writes_gap_seconds"] - (0.6 - 0.5)) < 1e-9,
    "timing.contextual_writes_gap_is_composer_post_start_minus_composer_pre_end",
    summary2["mia1"]["contextual_writes_gap_seconds"],
)
expect(
    summary1["foxmccouldwm1"]["classification_planning_gap_seconds"] is None,
    "timing.gap_is_None_when_composer_pre_never_happened (native-only fallback)",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
