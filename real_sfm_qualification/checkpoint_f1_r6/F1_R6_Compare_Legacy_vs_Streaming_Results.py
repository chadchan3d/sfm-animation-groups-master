# -*- coding: ascii -*-
"""
F1-R6 offline comparator.

Not a MAINMENU script. Not run inside SFM. Not run in-process with either
arm. This is a plain, standalone Python script that runs AFTER both a
LEGACY-mode and a STREAMING_CANDIDATE-mode run of
Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity.py have each completed in
their own separate, fresh SFM process, and have each produced their own
mode-specific JSON result file. It loads BOTH artifacts and performs the
one comparison that a shared, single-process, in-process design (correctly
rejected per this checkpoint's own design-correction note) would have
contaminated: semantic parity and resource-reduction metrics, computed
strictly from two independently-produced, already-written JSON files.

This script does not call SFM, does not import PySide, does not touch any
live DME object, and does not perform any discovery itself. It only reads
two JSON files and compares/derives from their already-recorded fields.

Usage (offline, any Python 2.7 interpreter with the json module):
  python F1_R6_Compare_Legacy_vs_Streaming_Results.py <legacy.json> <streaming.json> [output_prefix]

If no paths are given, the default paths this checkpoint's own runtime
script writes to are used:
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_legacy_result.json
  C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_streaming_candidate_result.json

Emits:
  <output_prefix>_comparison_result.json
  <output_prefix>_comparison_summary.txt
(output_prefix defaults to C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6)

This script never auto-declares production qualification. It reports
machine-derived facts only: per-target identity/order parity, per-target
semantic mismatches (if any), and the requested derived resource-reduction
metrics, computed strictly from the two arms' own recorded resource
deltas. Interpretation of these facts (whether they justify production
implementation) is explicitly out of scope, per this whole project's
standing "no unrequested semantic decisions" discipline.
"""
import json
import os
import sys


DEFAULT_LEGACY_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_legacy_result.json"
DEFAULT_STREAMING_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6_streaming_candidate_result.json"
DEFAULT_OUTPUT_PREFIX = "C:\\Users\\Public\\Documents\\sfm_checkpoint_f1_r6"

EXPECTED_TARGET_COUNT = 62

PER_TARGET_COMPARISON_FIELDS = (
    "status",
    "reachable_rig_count",
    "matching_rig_count",
    "rig_handle",
    "registry_handle",
    "owned_handles",
    "owned_names_in_order",
    "hidden_groups",
)


class ComparatorError(Exception):
    pass


def load_report(path):
    with open(path, "rb") as f:
        data = json.load(f)
    return data


def compare_target_records(legacy_record, streaming_record):
    """Returns (is_match, mismatch_fields) comparing two per-target JSON
    records already written by the runtime script. No live objects
    involved -- rig_handle/registry_handle are already the resolved
    integer handles the runtime script recorded, so identity comparison
    reduces to a plain equality check."""
    mismatch_fields = []
    for field in PER_TARGET_COMPARISON_FIELDS:
        legacy_value = legacy_record.get(field)
        streaming_value = streaming_record.get(field)
        if isinstance(legacy_value, list) and isinstance(streaming_value, list):
            if list(legacy_value) != list(streaming_value):
                mismatch_fields.append(field)
        else:
            if legacy_value != streaming_value:
                mismatch_fields.append(field)
    return (len(mismatch_fields) == 0), mismatch_fields


def safe_get(d, path_tuple):
    cur = d
    for key in path_tuple:
        if cur is None:
            return None
        cur = cur.get(key) if isinstance(cur, dict) else None
    return cur


def main(argv):
    legacy_path = argv[1] if len(argv) > 1 else DEFAULT_LEGACY_PATH
    streaming_path = argv[2] if len(argv) > 2 else DEFAULT_STREAMING_PATH
    output_prefix = argv[3] if len(argv) > 3 else DEFAULT_OUTPUT_PREFIX

    result = {
        "legacy_path": legacy_path,
        "streaming_path": streaming_path,
        "checks": [],
        "target_mismatches": [],
    }

    def check(name, condition, detail=None):
        result["checks"].append({"name": name, "pass": bool(condition), "detail": repr(detail) if detail is not None else None})
        sys.stdout.write("[%s] %s%s\n" % ("PASS" if condition else "FAIL", name, "" if detail is None else " -- %r" % (detail,)))

    legacy_report = load_report(legacy_path)
    streaming_report = load_report(streaming_path)

    check("legacy_report.mode_is_legacy", legacy_report.get("mode") == "LEGACY", legacy_report.get("mode"))
    check("streaming_report.mode_is_streaming_candidate", streaming_report.get("mode") == "STREAMING_CANDIDATE", streaming_report.get("mode"))
    check("legacy_report.overall_pass", bool(legacy_report.get("overall_pass")))
    check("streaming_report.overall_pass", bool(streaming_report.get("overall_pass")))

    legacy_targets = legacy_report.get("targets_processed") or []
    streaming_targets = streaming_report.get("targets_processed") or []

    check("legacy_report.target_count_is_62", len(legacy_targets) == EXPECTED_TARGET_COUNT, len(legacy_targets))
    check("streaming_report.target_count_is_62", len(streaming_targets) == EXPECTED_TARGET_COUNT, len(streaming_targets))

    identity_order_match = len(legacy_targets) == len(streaming_targets)
    if identity_order_match:
        for i in range(len(legacy_targets)):
            l = legacy_targets[i]
            s = streaming_targets[i]
            if l.get("target_index") != s.get("target_index") or l.get("shot") != s.get("shot") or l.get("target") != s.get("target"):
                identity_order_match = False
                result["target_mismatches"].append({
                    "target_index": i,
                    "kind": "IDENTITY_OR_ORDER_MISMATCH",
                    "legacy": {"target_index": l.get("target_index"), "shot": l.get("shot"), "target": l.get("target")},
                    "streaming": {"target_index": s.get("target_index"), "shot": s.get("shot"), "target": s.get("target")},
                })
    check("parity.62_of_62_target_identity_and_order_match", identity_order_match)

    semantic_match_count = 0
    semantic_mismatch_count = 0
    if identity_order_match:
        for i in range(len(legacy_targets)):
            is_match, mismatch_fields = compare_target_records(legacy_targets[i], streaming_targets[i])
            if is_match:
                semantic_match_count += 1
            else:
                semantic_mismatch_count += 1
                result["target_mismatches"].append({
                    "target_index": i,
                    "kind": "SEMANTIC_MISMATCH",
                    "shot": legacy_targets[i].get("shot"),
                    "target": legacy_targets[i].get("target"),
                    "mismatch_fields": mismatch_fields,
                })

    check(
        "parity.zero_semantic_mismatches",
        identity_order_match and semantic_mismatch_count == 0 and semantic_match_count == EXPECTED_TARGET_COUNT,
        (semantic_match_count, semantic_mismatch_count),
    )

    legacy_status_counts = safe_get(legacy_report, ("arm_summary", "status_counts")) or {}
    streaming_status_counts = safe_get(streaming_report, ("arm_summary", "status_counts")) or {}
    check(
        "parity.branch_relevant_status_distribution_matches",
        legacy_status_counts == streaming_status_counts,
        (legacy_status_counts, streaming_status_counts),
    )

    legacy_ambiguous_indices = set(t.get("target_index") for t in legacy_targets if t.get("is_ambiguous_status"))
    streaming_ambiguous_indices = set(t.get("target_index") for t in streaming_targets if t.get("is_ambiguous_status"))
    check(
        "parity.ambiguity_disposition_matches_by_target",
        legacy_ambiguous_indices == streaming_ambiguous_indices,
        (sorted(legacy_ambiguous_indices), sorted(streaming_ambiguous_indices)),
    )

    # --- Resource comparison: raw per-arm facts, then derived metrics. ---
    legacy_calls = safe_get(legacy_report, ("arm_summary", "total_discovery_calls"))
    streaming_calls = safe_get(streaming_report, ("arm_summary", "total_discovery_calls"))
    legacy_elapsed = safe_get(legacy_report, ("arm_summary", "total_elapsed_seconds"))
    streaming_elapsed = safe_get(streaming_report, ("arm_summary", "total_elapsed_seconds"))

    legacy_private_delta = safe_get(legacy_report, ("resource_deltas", "private_delta"))
    streaming_private_delta = safe_get(streaming_report, ("resource_deltas", "private_delta"))
    legacy_free_vas_delta = safe_get(legacy_report, ("resource_deltas", "free_vas_delta"))
    streaming_free_vas_delta = safe_get(streaming_report, ("resource_deltas", "free_vas_delta"))
    legacy_largest_free_delta = safe_get(legacy_report, ("resource_deltas", "largest_free_delta"))
    streaming_largest_free_delta = safe_get(streaming_report, ("resource_deltas", "largest_free_delta"))

    result["raw_facts"] = {
        "legacy": {
            "total_discovery_calls": legacy_calls,
            "total_elapsed_seconds": legacy_elapsed,
            "retained_private_delta": legacy_private_delta,
            "free_vas_delta": legacy_free_vas_delta,
            "largest_free_delta": legacy_largest_free_delta,
        },
        "streaming_candidate": {
            "total_discovery_calls": streaming_calls,
            "total_elapsed_seconds": streaming_elapsed,
            "retained_private_delta": streaming_private_delta,
            "free_vas_delta": streaming_free_vas_delta,
            "largest_free_delta": streaming_largest_free_delta,
        },
    }

    check("resource.legacy_call_count_is_62", legacy_calls == EXPECTED_TARGET_COUNT, legacy_calls)
    check("resource.streaming_call_count_is_62", streaming_calls == EXPECTED_TARGET_COUNT, streaming_calls)
    check(
        "resource.matched_call_counts_across_arms",
        legacy_calls is not None and legacy_calls == streaming_calls,
        (legacy_calls, streaming_calls),
    )

    def _safe_sub(a, b):
        if a is None or b is None:
            return None
        return a - b

    def _safe_ratio(numerator, denominator):
        if numerator is None or denominator is None or denominator == 0:
            return None
        return float(numerator) / float(denominator)

    candidate_private_reduction_bytes = _safe_sub(legacy_private_delta, streaming_private_delta)
    candidate_private_reduction_ratio = _safe_ratio(candidate_private_reduction_bytes, legacy_private_delta)
    candidate_free_vas_improvement_bytes = _safe_sub(streaming_free_vas_delta, legacy_free_vas_delta)
    candidate_largest_free_improvement_bytes = _safe_sub(streaming_largest_free_delta, legacy_largest_free_delta)
    candidate_elapsed_reduction_seconds = _safe_sub(legacy_elapsed, streaming_elapsed)
    candidate_elapsed_ratio = _safe_ratio(candidate_elapsed_reduction_seconds, legacy_elapsed)

    result["derived_metrics"] = {
        "candidate_private_reduction_bytes": candidate_private_reduction_bytes,
        "candidate_private_reduction_ratio": candidate_private_reduction_ratio,
        "candidate_free_vas_improvement_bytes": candidate_free_vas_improvement_bytes,
        "candidate_largest_free_improvement_bytes": candidate_largest_free_improvement_bytes,
        "candidate_elapsed_reduction_seconds": candidate_elapsed_reduction_seconds,
        "candidate_elapsed_ratio": candidate_elapsed_ratio,
    }

    result["workload_note"] = (
        "Both arms measure exactly one discover_rig_context() call per "
        "target (62 total), not the production 250-site schedule. These "
        "deltas and ratios are PER-COMMAND-SHAPED-AS-62-CALLS facts, not "
        "command-scale (250-call) projections. Any extrapolation to "
        "production's own real 250-call volume is a separate, explicitly-"
        "labeled analyst step, not performed by this script."
    )

    all_checks_passed = all(c["pass"] for c in result["checks"])
    result["overall_comparison_pass"] = bool(all_checks_passed)

    result_json_path = output_prefix + "_comparison_result.json"
    result_summary_path = output_prefix + "_comparison_summary.txt"

    with open(result_json_path + ".tmp", "wb") as f:
        json.dump(result, f)
    if os.path.exists(result_json_path):
        os.remove(result_json_path)
    os.rename(result_json_path + ".tmp", result_json_path)

    summary_lines = []
    summary_lines.append("F1-R6 OFFLINE COMPARATOR -- LEGACY vs STREAMING_CANDIDATE")
    summary_lines.append("legacy_path=%s" % legacy_path)
    summary_lines.append("streaming_path=%s" % streaming_path)
    summary_lines.append("")
    summary_lines.append("--- CHECKS ---")
    for c in result["checks"]:
        summary_lines.append("[%s] %s%s" % ("PASS" if c["pass"] else "FAIL", c["name"], "" if c["detail"] is None else " -- %s" % c["detail"]))
    summary_lines.append("")
    summary_lines.append("raw_facts=%r" % (result["raw_facts"],))
    summary_lines.append("")
    summary_lines.append("derived_metrics=%r" % (result["derived_metrics"],))
    summary_lines.append("")
    if result["target_mismatches"]:
        summary_lines.append("--- TARGET MISMATCHES (%d) ---" % len(result["target_mismatches"]))
        for m in result["target_mismatches"]:
            summary_lines.append("- %r" % (m,))
    else:
        summary_lines.append("--- TARGET MISMATCHES: none ---")
    summary_lines.append("")
    summary_lines.append("OVERALL_COMPARISON_PASS=%r" % result["overall_comparison_pass"])

    summary_text = "\n".join(summary_lines) + "\n"
    with open(result_summary_path + ".tmp", "wb") as f:
        f.write(summary_text)
    if os.path.exists(result_summary_path):
        os.remove(result_summary_path)
    os.rename(result_summary_path + ".tmp", result_summary_path)

    sys.stdout.write(summary_text)
    sys.stdout.write("\nWritten:\n  %s\n  %s\n" % (result_json_path, result_summary_path))

    return 0 if result["overall_comparison_pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
