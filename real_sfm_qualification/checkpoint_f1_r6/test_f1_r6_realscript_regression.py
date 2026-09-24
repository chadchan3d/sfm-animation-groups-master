# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R6's real-SFM script
(Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity.py), TWO-MODE /
SEPARATE-FRESH-PROCESS design (design correction from the prior
single-process, alternating-arm-order version).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes, then runs static
source checks confirming the two-mode design is actually present in the
deployed script (mode dialog, per-mode output paths, no in-process
cross-arm comparison, no candidate-module loading in LEGACY mode).

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r6_realscript_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity.py")
EXPECTED_SCRIPT_SHA256 = "1de63943f6fd670a91f110f94d2b6e16f56473b95a7e40c6d41ad83df4c02eeb"

WRITE_JSON_ATOMIC_RANGE = (236, 280)
WRITE_TEXT_ATOMIC_RANGE = (283, 321)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(SCRIPT_PATH, "rb") as f:
    script_bytes = f.read()
script_text = script_bytes.decode("ascii")
script_lines = script_text.splitlines()

expect(hashlib.sha256(script_bytes).hexdigest() == EXPECTED_SCRIPT_SHA256, "script.sha256_matches_pinned")


def extract(range_tuple, lines=script_lines):
    start, end = range_tuple
    return "\n".join(lines[start - 1:end])


sys.stdout.write("--- Shared primitives (verbatim, reused from every earlier checkpoint) ---\n")

ns1 = {"os": os, "json": json}
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), ns1)
write_json_atomic = ns1["write_json_atomic"]

tmp_dir = tempfile.mkdtemp(prefix="f1_r6_test_")
json_target = os.path.join(tmp_dir, "result.json")
ok, err, reparsed = write_json_atomic(json_target, {"a": 1, "b": [1, 2, 3]})
expect(ok is True, "write_json_atomic.simple_write_ok")
expect(reparsed == {"a": 1, "b": [1, 2, 3]}, "write_json_atomic.reparsed_matches_written")

ns2 = {"os": os}
exec(compile(extract(WRITE_TEXT_ATOMIC_RANGE), "<write_text_atomic>", "exec"), ns2)
write_text_atomic = ns2["write_text_atomic"]

text_target = os.path.join(tmp_dir, "result.txt")
ok2, err2 = write_text_atomic(text_target, b"hello world")
expect(ok2 is True, "write_text_atomic.simple_write_ok")

sys.stdout.write("\n--- Static safety checks on the actual deployed script source ---\n")


def never_actually_called(name):
    idx = 0
    while True:
        idx = script_text.find(name + "(", idx)
        if idx < 0:
            return True
        after = script_text[idx + len(name) + 1:idx + len(name) + 2]
        if after != ")":
            return False
        idx += 1


expect("SaveToFile(" not in script_text, "script.never_calls_SaveToFile -- no-save behavior enforced")
expect(never_actually_called("capture_snapshot_explicit"), "script.never_calls_capture_snapshot_explicit")
expect(never_actually_called("capture_tree"), "script.never_calls_capture_tree")
expect(never_actually_called("production_generic_composer"), "script.never_calls_production_generic_composer")
expect(never_actually_called("preflight_reconciliation_plan"), "script.never_calls_preflight_reconciliation_plan")
expect("self.rebuild(" not in script_text and "instance.rebuild(" not in script_text, "script.never_calls_native_rebuild -- confirms the no-mutation design")
expect("SetHeadTimeInSeconds(" not in script_text, "script.never_activates_a_shot -- confirms shot activation is genuinely unnecessary for discovery")
expect("instance.finished = True" in script_text, "script.neutralizes_real_instance_before_any_event_pump")
expect(
    script_text.index("instance.finished = True") < script_text.index("work = instance.work"),
    "script.neutralization_happens_before_reading_instance_work",
)

sys.stdout.write("\n--- Two-mode / separate-fresh-process design checks (F1-R6 design correction) ---\n")

expect("def select_mode_via_dialog" in script_text, "script.defines_mode_selection_dialog_function")
expect("QtGui.QMessageBox()" in script_text, "script.mode_dialog_uses_a_real_qt_messagebox")
expect('u"LEGACY"' in script_text and 'u"STREAMING_CANDIDATE"' in script_text, "script.mode_dialog_offers_exactly_legacy_and_streaming_candidate_labels")
expect("MODE_LEGACY = u\"LEGACY\"" in script_text, "script.defines_mode_legacy_constant")
expect('MODE_STREAMING_CANDIDATE = u"STREAMING_CANDIDATE"' in script_text, "script.defines_mode_streaming_candidate_constant")

expect(
    "sfm_checkpoint_f1_r6_legacy_result.json" in script_text and "sfm_checkpoint_f1_r6_streaming_candidate_result.json" in script_text,
    "script.legacy_and_streaming_modes_write_to_distinct_output_filenames -- prevents one arm's own fresh-process run from overwriting the other's evidence",
)

expect(
    "def compare_discovery_results" not in script_text,
    "script.no_in_process_cross_arm_comparison_function -- comparison moved fully offline, per design correction",
)
expect(
    "candidate_result " not in script_text and "candidate_result=" not in script_text
    and "legacy_result " not in script_text and "legacy_result=" not in script_text
    and "legacy_result," not in script_text and "candidate_result," not in script_text,
    "script.no_dual_arm_result_variables -- confirms only ONE arm's discover_rig_context is ever called per run",
)
expect(
    "= discovery_fn(shot, aset)" in script_text,
    "script.uses_a_single_selected_discovery_fn_per_run",
)
expect(
    "target_index % 2 == 0" not in script_text,
    "script.no_arm_order_alternation -- the rejected single-process alternating-order design is gone",
)

expect(
    "if mode == MODE_LEGACY:" in script_text,
    "script.branches_on_selected_mode_before_choosing_discovery_fn",
)
expect(
    "exec(compile(prototype_bytes," in script_text,
    "script.still_loads_prototype_bytes_somewhere",
)
prototype_exec_idx = script_text.index("exec(compile(prototype_bytes,")
legacy_branch_idx = script_text.index("if mode == MODE_LEGACY:")
else_branch_idx = script_text.index("else:", legacy_branch_idx)
expect(
    prototype_exec_idx > else_branch_idx,
    "script.prototype_exec_only_happens_in_the_streaming_candidate_else_branch -- never in a LEGACY run",
)

expect(
    "prototype_bytes = None" in script_text,
    "script.prototype_bytes_defaults_to_none_and_is_only_populated_for_streaming_candidate_mode",
)
expect(
    "if mode == MODE_STREAMING_CANDIDATE:\n        with open(PROTOTYPE_PATH" in script_text,
    "script.prototype_file_only_opened_in_streaming_candidate_mode",
)

expect(
    "workload_design_note" in script_text,
    "script.records_explicit_62_call_vs_250_site_workload_justification",
)
expect(
    "62 total)" in script_text or "(62 total)" in script_text,
    "script.explicitly_states_62_calls_per_arm_not_250",
)

expect(
    "This is ONE arm only (mode=%s)" in script_text,
    "script.own_summary_text_states_this_is_one_arm_only",
)
expect(
    "F1_R6_Compare_Legacy_vs_Streaming_Results.py" in script_text,
    "script.own_summary_text_points_to_the_separate_offline_comparator",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
