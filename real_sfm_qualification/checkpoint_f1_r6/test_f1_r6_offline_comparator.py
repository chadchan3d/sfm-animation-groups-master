# -*- coding: utf-8 -*-
"""
Offline regression for F1_R6_Compare_Legacy_vs_Streaming_Results.py (the
new, fully-offline comparator introduced by the F1-R6 two-mode /
separate-fresh-process design correction).

Exercises the comparator's own functions (imported directly, since this
comparator is plain, portable Python 2.7 with no SFM/PySide dependency --
unlike the MAINMENU checkpoint scripts, it does not need source-line-range
extraction) against synthetic legacy/streaming JSON report pairs covering:
  - a clean, fully-matching 62/62 pair (expected PASS)
  - a semantic mismatch on one target (status differs)
  - an identity/order mismatch (shot/target differs at some index)
  - a rig/registry handle mismatch
  - the AMBIGUOUS_MULTIPLE_RIGS-style both-None-handle case (must match
    cleanly, not be flagged as a spurious mismatch)
  - derived resource-metric arithmetic against known input deltas

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r6_offline_comparator.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
COMPARATOR_PATH = os.path.join(THIS_DIR, "F1_R6_Compare_Legacy_vs_Streaming_Results.py")
EXPECTED_COMPARATOR_SHA256 = "5d155f68fa5598c6a255b7b07a2981b22376d0c506c04ace5efd549cd7cf2d8e"

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(COMPARATOR_PATH, "rb") as f:
    comparator_bytes = f.read()
expect(hashlib.sha256(comparator_bytes).hexdigest() == EXPECTED_COMPARATOR_SHA256, "comparator.sha256_matches_pinned")

comparator_ns = {"__name__": "f1_r6_comparator_under_test"}
exec(compile(comparator_bytes, "<F1_R6_Compare_Legacy_vs_Streaming_Results>", "exec"), comparator_ns)
compare_target_records = comparator_ns["compare_target_records"]
main_fn = comparator_ns["main"]


def make_target_record(index, shot=u"Shot01", target=u"Target01", status=u"SUPPORTED_ACTIVE_RIG",
                        reachable_rig_count=1, matching_rig_count=1, rig_handle=42, registry_handle=99,
                        owned_handles=None, owned_names_in_order=None, hidden_groups=None,
                        is_ambiguous_status=False):
    return {
        "target_index": index,
        "shot": shot,
        "target": target,
        "status": status,
        "is_ambiguous_status": is_ambiguous_status,
        "reachable_rig_count": reachable_rig_count,
        "matching_rig_count": matching_rig_count,
        "rig_handle": rig_handle,
        "registry_handle": registry_handle,
        "owned_handles": owned_handles if owned_handles is not None else [1, 2, 3],
        "owned_names_in_order": owned_names_in_order if owned_names_in_order is not None else [u"a", u"b"],
        "hidden_groups": hidden_groups if hidden_groups is not None else [u"GroupA"],
        "elapsed_seconds": 0.01,
        "private_delta": 1000,
        "working_set_delta": 1000,
    }


sys.stdout.write("--- compare_target_records(): in-memory unit checks ---\n")

baseline = make_target_record(0)
identical = make_target_record(0)
is_match, mismatches = compare_target_records(baseline, identical)
expect(is_match is True and mismatches == [], "compare_target_records.identical_records_match")

status_diff = make_target_record(0, status=u"UNRIGGED")
is_match2, mismatches2 = compare_target_records(baseline, status_diff)
expect(is_match2 is False and "status" in mismatches2, "compare_target_records.status_mismatch_detected")

handle_diff = make_target_record(0, rig_handle=43)
is_match3, mismatches3 = compare_target_records(baseline, handle_diff)
expect(is_match3 is False and "rig_handle" in mismatches3, "compare_target_records.rig_handle_mismatch_detected")

both_none = make_target_record(0, rig_handle=None, registry_handle=None)
both_none_2 = make_target_record(0, rig_handle=None, registry_handle=None)
is_match4, mismatches4 = compare_target_records(both_none, both_none_2)
expect(is_match4 is True, "compare_target_records.both_none_handles_match_cleanly -- AMBIGUOUS_MULTIPLE_RIGS case")

owned_diff = make_target_record(0, owned_names_in_order=[u"a", u"c"])
is_match5, mismatches5 = compare_target_records(baseline, owned_diff)
expect(is_match5 is False and "owned_names_in_order" in mismatches5, "compare_target_records.owned_names_mismatch_detected")

sys.stdout.write("\n--- Full main() run against synthetic report pairs ---\n")

tmp_dir = tempfile.mkdtemp(prefix="f1_r6_comparator_test_")


def write_report(path, mode, targets, arm_summary_extra, resource_deltas):
    report = {
        "mode": mode,
        "overall_pass": True,
        "targets_processed": targets,
        "arm_summary": dict({
            "mode": mode,
            "total_discovery_calls": len(targets),
            "total_elapsed_seconds": 1.0,
            "status_counts": {"SUPPORTED_ACTIVE_RIG": len(targets)},
        }, **arm_summary_extra),
        "resource_deltas": resource_deltas,
    }
    with open(path, "wb") as f:
        json.dump(report, f)
    return report


def run_comparator(legacy_path, streaming_path, prefix):
    old_argv = sys.argv
    try:
        sys.argv = ["comparator", legacy_path, streaming_path, prefix]
        rc = main_fn(sys.argv)
    finally:
        sys.argv = old_argv
    with open(prefix + "_comparison_result.json", "rb") as f:
        result = json.load(f)
    return rc, result


# --- Case 1: clean 62/62 match, with known resource deltas for arithmetic check. ---
clean_targets = [make_target_record(i, shot=u"Shot%02d" % (i // 5), target=u"Target%02d" % i) for i in range(62)]
legacy_path_1 = os.path.join(tmp_dir, "legacy1.json")
streaming_path_1 = os.path.join(tmp_dir, "streaming1.json")
write_report(legacy_path_1, "LEGACY", clean_targets, {}, {
    "private_delta": 1000000, "working_set_delta": 1000000,
    "free_vas_delta": -500000, "largest_free_delta": -200000,
})
write_report(streaming_path_1, "STREAMING_CANDIDATE", clean_targets, {}, {
    "private_delta": 400000, "working_set_delta": 400000,
    "free_vas_delta": -100000, "largest_free_delta": -50000,
})
rc1, result1 = run_comparator(legacy_path_1, streaming_path_1, os.path.join(tmp_dir, "case1"))
expect(rc1 == 0, "main.case1_clean_match_returns_zero")
expect(result1["overall_comparison_pass"] is True, "main.case1_overall_comparison_pass_true")
expect(result1["derived_metrics"]["candidate_private_reduction_bytes"] == 600000, "main.case1_private_reduction_bytes_correct")
expect(abs(result1["derived_metrics"]["candidate_private_reduction_ratio"] - 0.6) < 1e-9, "main.case1_private_reduction_ratio_correct")
expect(result1["derived_metrics"]["candidate_free_vas_improvement_bytes"] == 400000, "main.case1_free_vas_improvement_correct")
expect(result1["derived_metrics"]["candidate_largest_free_improvement_bytes"] == 150000, "main.case1_largest_free_improvement_correct")
expect(len(result1["target_mismatches"]) == 0, "main.case1_zero_target_mismatches")

# --- Case 2: one semantic mismatch (status differs at index 10). ---
mismatched_targets = list(clean_targets)
mismatched_targets[10] = make_target_record(10, shot=u"Shot%02d" % (10 // 5), target=u"Target%02d" % 10, status=u"UNRIGGED")
streaming_path_2 = os.path.join(tmp_dir, "streaming2.json")
write_report(streaming_path_2, "STREAMING_CANDIDATE", mismatched_targets, {}, {
    "private_delta": 400000, "working_set_delta": 400000,
    "free_vas_delta": -100000, "largest_free_delta": -50000,
})
rc2, result2 = run_comparator(legacy_path_1, streaming_path_2, os.path.join(tmp_dir, "case2"))
expect(rc2 == 1, "main.case2_semantic_mismatch_returns_nonzero")
expect(result2["overall_comparison_pass"] is False, "main.case2_overall_comparison_pass_false")
expect(len(result2["target_mismatches"]) == 1 and result2["target_mismatches"][0]["target_index"] == 10, "main.case2_mismatch_pinpoints_target_index_10")

# --- Case 3: identity/order mismatch (target name differs at index 5, everything else same). ---
reordered_targets = list(clean_targets)
reordered_targets[5] = make_target_record(5, shot=u"Shot%02d" % (5 // 5), target=u"WRONG_TARGET_NAME")
streaming_path_3 = os.path.join(tmp_dir, "streaming3.json")
write_report(streaming_path_3, "STREAMING_CANDIDATE", reordered_targets, {}, {
    "private_delta": 400000, "working_set_delta": 400000,
    "free_vas_delta": -100000, "largest_free_delta": -50000,
})
rc3, result3 = run_comparator(legacy_path_1, streaming_path_3, os.path.join(tmp_dir, "case3"))
expect(rc3 == 1, "main.case3_identity_order_mismatch_returns_nonzero")
identity_check = [c for c in result3["checks"] if c["name"] == "parity.62_of_62_target_identity_and_order_match"][0]
expect(identity_check["pass"] is False, "main.case3_identity_order_check_fails")

# --- Case 4: wrong target count (61 instead of 62) -- must fail, not silently pass. ---
short_targets = clean_targets[:61]
streaming_path_4 = os.path.join(tmp_dir, "streaming4.json")
write_report(streaming_path_4, "STREAMING_CANDIDATE", short_targets, {}, {
    "private_delta": 400000, "working_set_delta": 400000,
    "free_vas_delta": -100000, "largest_free_delta": -50000,
})
rc4, result4 = run_comparator(legacy_path_1, streaming_path_4, os.path.join(tmp_dir, "case4"))
expect(rc4 == 1, "main.case4_short_target_list_returns_nonzero")
count_check = [c for c in result4["checks"] if c["name"] == "streaming_report.target_count_is_62"][0]
expect(count_check["pass"] is False, "main.case4_target_count_check_fails")

sys.stdout.write("\n--- Subprocess invocation smoke test (script actually runnable standalone) ---\n")
proc = subprocess.Popen(
    [sys.executable, COMPARATOR_PATH, legacy_path_1, streaming_path_1, os.path.join(tmp_dir, "case1_subprocess")],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
)
stdout_data, _ = proc.communicate()
expect(proc.returncode == 0, "subprocess.comparator_runs_standalone_and_exits_zero_on_clean_match")
expect(os.path.exists(os.path.join(tmp_dir, "case1_subprocess_comparison_result.json")), "subprocess.writes_expected_result_json")
expect(os.path.exists(os.path.join(tmp_dir, "case1_subprocess_comparison_summary.txt")), "subprocess.writes_expected_summary_txt")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
