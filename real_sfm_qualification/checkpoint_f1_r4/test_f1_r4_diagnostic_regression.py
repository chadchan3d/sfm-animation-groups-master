# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R4
(Checkpoint_F1_R4_Fresh_Discovery_Retention_Attribution.py).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes and real preserved
evidence already on file in this repository -- never against invented
expectations.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r4_diagnostic_regression.py
"""
import ctypes
import hashlib
import json
import os
import sys
import tempfile
import time

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R4_Fresh_Discovery_Retention_Attribution.py")
EXPECTED_SCRIPT_SHA256 = "0efe92d4955407110889cb0d0da78682cfeccfdcf533e864f4d5c620f59f7f58"

REAL_PRODUCTION_LOG_WITH_GATE_EVIDENCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "checkpoint_f1", "f1_1_crash_evidence", "sfm_rebuild_control_groups_F1-1_command3_crash.txt",
)

CHECKPOINT_PARSER_RANGE = (194, 244)
WRITE_JSON_ATOMIC_RANGE = (247, 291)
WRITE_TEXT_ATOMIC_RANGE = (294, 332)
SEQUENCE_CHECKSUM_RANGE = (335, 337)
RESOLVE_TARGET_RANGE = (345, 383)
REBUILD_TARGET_RANGE = (386, 439)
TIMED_DISCOVERY_RANGE = (442, 446)
MATCHED_WORKLOAD_RANGE = (449, 555)

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


sys.stdout.write("--- Gate-count / branch-schedule expectations verified against real preserved evidence and the audit doc ---\n")

with open(REAL_PRODUCTION_LOG_WITH_GATE_EVIDENCE, "rb") as f:
    real_log_text = f.read().decode("ascii", "replace")

expect(
    "gate skips static=12 follower=4 lowbone_no_alh=7 failclosed_process=0" in real_log_text,
    "gate_evidence.real_log_contains_exact_expected_skip_line",
)
expect(85 - (12 + 4 + 7 + 0) == 62, "gate_evidence.arithmetic_reconciles_85_minus_23_equals_62")

for expected_constant in (
    "EXPECTED_TOTAL_SHOTS = 15",
    "EXPECTED_MODEL_BACKED_TARGETS = 85",
    "EXPECTED_GATE_STATIC_SKIPS = 12",
    "EXPECTED_GATE_FOLLOWER_SKIPS = 4",
    "EXPECTED_GATE_LOWBONE_SKIPS = 7",
    "EXPECTED_GATE_FAILCLOSED_PROCESS = 0",
    "EXPECTED_ELIGIBLE_NATIVE_TARGETS = 62",
):
    expect(expected_constant in script_text, "script.contains_expected_gate_constant: %s" % expected_constant)

# Branch discovery-call counts, per F1_R4_DISCOVERY_SCHEDULE_AUDIT.md's own
# derived schedule table (PRE_CAPTURE_UNSUPPORTED=2, STATUS_MISMATCH=3,
# WRAPPER_SURVIVED=3, COMPOSER_ENTRY_PATH=5 -- each including the
# unconditional terminal discovery).
branch_ns = {}
exec(compile(
    script_text[script_text.index("BRANCH_DISCOVERY_COUNTS = {"):script_text.index("}", script_text.index("BRANCH_DISCOVERY_COUNTS = {")) + 1],
    "<branch_counts>", "exec",
), branch_ns)
BRANCH_DISCOVERY_COUNTS = branch_ns["BRANCH_DISCOVERY_COUNTS"]

expect(BRANCH_DISCOVERY_COUNTS["PRE_CAPTURE_UNSUPPORTED"] == 2, "branch_schedule.pre_capture_unsupported_is_2")
expect(BRANCH_DISCOVERY_COUNTS["NATIVE_POST_ONLY_STATUS_MISMATCH"] == 3, "branch_schedule.status_mismatch_is_3")
expect(BRANCH_DISCOVERY_COUNTS["NATIVE_POST_WRAPPER_SURVIVED"] == 3, "branch_schedule.wrapper_survived_is_3")
expect(BRANCH_DISCOVERY_COUNTS["COMPOSER_ENTRY_PATH"] == 5, "branch_schedule.composer_entry_path_is_5")

sys.stdout.write("\n--- sequence_checksum(): order-sensitive, deterministic ---\n")

ns = {"json": json, "hashlib": hashlib}
exec(compile(extract(SEQUENCE_CHECKSUM_RANGE), "<sequence_checksum>", "exec"), ns)
sequence_checksum = ns["sequence_checksum"]

stream_a = [(u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH", u"PRE"), (u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH", u"NATIVE_POST")]
stream_a_reordered = [(u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH", u"NATIVE_POST"), (u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH", u"PRE")]
stream_b = [(u"shot3", u"mia1", u"COMPOSER_ENTRY_PATH", u"PRE"), (u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH", u"NATIVE_POST")]

checksum_a1 = sequence_checksum(stream_a)
checksum_a2 = sequence_checksum(list(stream_a))
checksum_a_reordered = sequence_checksum(stream_a_reordered)
checksum_b = sequence_checksum(stream_b)

expect(checksum_a1 == checksum_a2, "sequence_checksum.deterministic_same_input_same_hash")
expect(checksum_a1 != checksum_a_reordered, "sequence_checksum.order_sensitive_reordering_changes_hash")
expect(checksum_a1 != checksum_b, "sequence_checksum.content_sensitive_different_entries_change_hash")
expect(len(checksum_a1) == 64, "sequence_checksum.produces_64_char_hex_digest")

sys.stdout.write("\n--- Shared primitives (verbatim, reused from every earlier checkpoint) ---\n")

ns2 = {}
exec(compile(extract(CHECKPOINT_PARSER_RANGE), "<checkpoint_parser>", "exec"), ns2)
parse_all_resource_checkpoints = ns2["parse_all_resource_checkpoints"]
checkpoints_by_label = ns2["checkpoints_by_label"]

sample_log = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=F1R4_CP0_NATIVE_DISCOVERY_START run_elapsed=1.234 "
    "mem_ok=True working_set=3000000000L peak_working_set=3000000000L pagefile=3000000000L "
    "peak_pagefile=3000000000L private=3000000000L vas_requested=True vas_ok=True "
    "min_address=0 max_address=140737488355328 mem_free=500000000 mem_reserve=100000000 "
    "mem_commit=200000000 largest_free=300000000 free_regions=50 virtual_query_count=10 "
    "vas_elapsed=0.0500 vas_error=None\n"
)
parsed_all = parse_all_resource_checkpoints(sample_log)
expect(len(parsed_all) == 1, "parser.finds_the_checkpoint_line")
by_label = checkpoints_by_label(sample_log, "F1R4_CP0_NATIVE_DISCOVERY_START")
expect(len(by_label) == 1 and by_label[0]["private"] == 3000000000, "parser.checkpoints_by_label_filters_correctly")

ns3 = {"os": os, "json": json}
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), ns3)
write_json_atomic = ns3["write_json_atomic"]

tmp_dir = tempfile.mkdtemp(prefix="f1_r4_test_")
json_target = os.path.join(tmp_dir, "result.json")
ok, err, reparsed = write_json_atomic(json_target, {"a": 1, "b": [1, 2, 3]})
expect(ok is True, "write_json_atomic.simple_write_ok")
expect(reparsed == {"a": 1, "b": [1, 2, 3]}, "write_json_atomic.reparsed_matches_written")

ns4 = {"os": os}
exec(compile(extract(WRITE_TEXT_ATOMIC_RANGE), "<write_text_atomic>", "exec"), ns4)
write_text_atomic = ns4["write_text_atomic"]

text_target = os.path.join(tmp_dir, "result.txt")
ok2, err2 = write_text_atomic(text_target, b"hello world")
expect(ok2 is True, "write_text_atomic.simple_write_ok")

sys.stdout.write("\n--- Fakes shared by resolve/rebuild/workload tests ---\n")


class CheckpointF1R4Error(Exception):
    pass


def b_to_unicode(value):
    if isinstance(value, unicode):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        try:
            return value.decode("latin-1")
        except Exception:
            return unicode(value)


class FakeAnimSet(object):
    def __init__(self, ptr, name):
        self._ptr = ptr
        self._name = name

    def GetName(self):
        return self._name


class FakeShot(object):
    def __init__(self, ptr, animation_sets):
        self._ptr = ptr
        self.animationSets = animation_sets


class FakeSfmApp(object):
    def __init__(self, current_shot):
        self._current_shot = current_shot

    def GetShotAtCurrentTime(self):
        return self._current_shot


def fake_native_ptr(obj):
    return obj._ptr


class FakeInstance(object):
    def __init__(self):
        self.run_lock_asserted = 0
        self.master_stable_asserted = 0
        self.game_model_ok = True
        self.root_ok = True
        self.rebuild_calls = []
        self.master_path = u"C:\\fake\\master.txt"

    def contextualizer_assert_run_lock_present(self):
        self.run_lock_asserted += 1

    def assert_master_stable(self):
        self.master_stable_asserted += 1

    def get_game_model(self, aset):
        return FakeAnimSet(0x5150, u"fake_game_model") if self.game_model_ok else None

    def get_root_group(self, aset):
        return FakeAnimSet(0x1000, u"fake_root") if self.root_ok else None

    def rebuild(self, void_p_arg):
        self.rebuild_calls.append(void_p_arg)


class FakeDataModel(object):
    def __init__(self):
        self._undo_enabled = True
        self.set_undo_calls = []

    def IsUndoEnabled(self):
        return self._undo_enabled

    def SetUndoEnabled(self, value):
        self.set_undo_calls.append(value)
        self._undo_enabled = bool(value)


resolve_ns = {
    "CheckpointF1R4Error": CheckpointF1R4Error,
    "b_to_unicode": b_to_unicode,
    "native_ptr": fake_native_ptr,
}
target_a = FakeAnimSet(0xAAAA, u"foxmccouldwm1")
fake_shot = FakeShot(0x1234, [target_a])
resolve_ns["sfmApp"] = FakeSfmApp(fake_shot)
exec(compile(extract(RESOLVE_TARGET_RANGE), "<native_only_resolve_target>", "exec"), resolve_ns)
native_only_resolve_target = resolve_ns["native_only_resolve_target"]

rebuild_ns = {
    "CheckpointF1R4Error": CheckpointF1R4Error,
    "native_ptr": fake_native_ptr,
    "ctypes": ctypes,
    "time": time,
}


def fake_native_master_protect_acquire(path):
    return 0xDEADBEEF


def fake_native_master_protect_release(handle):
    pass


rebuild_ns["native_master_protect_acquire"] = fake_native_master_protect_acquire
rebuild_ns["native_master_protect_release"] = fake_native_master_protect_release
exec(compile(extract(REBUILD_TARGET_RANGE), "<native_only_rebuild_target>", "exec"), rebuild_ns)
native_only_rebuild_target = rebuild_ns["native_only_rebuild_target"]

sys.stdout.write("\n--- matched_native_and_discovery_workload(): all four branch paths ---\n")

workload_ns = dict(rebuild_ns)
workload_ns.update(resolve_ns)
workload_ns["native_only_rebuild_target"] = native_only_rebuild_target
exec(compile(extract(TIMED_DISCOVERY_RANGE), "<timed_discovery>", "exec"), workload_ns)
exec(compile(extract(MATCHED_WORKLOAD_RANGE), "<matched_native_and_discovery_workload>", "exec"), workload_ns)
matched_native_and_discovery_workload = workload_ns["matched_native_and_discovery_workload"]

shot_record = {"shot": fake_shot, "ptr": 0x1234, "name": u"shot3"}
target_dict = {"ptr": 0xAAAA, "name": u"foxmccouldwm1"}


def fake_find_direct_child_never_found(root, child_name):
    return None


def fake_find_direct_child_wrapper_found(root, child_name):
    return FakeAnimSet(0x9999, child_name) if child_name == "__RIG_VISIBLE_RECON__" else None


# --- Case 1: PRE discovery raises -> PRE_CAPTURE_UNSUPPORTED, 2 discoveries.
# Only the FIRST call (PRE) raises -- the SECOND call this branch performs
# (the unconditional terminal discovery, which still runs since native
# Rebuild still executes regardless of PRE's own outcome) is expected to
# succeed in this scenario, matching a realistic case where PRE alone
# failed but the target is otherwise healthy. ---
discover_raises_call_count = [0]


def discover_raises(shot, aset):
    discover_raises_call_count[0] += 1
    if discover_raises_call_count[0] == 1:
        raise ValueError("synthetic PRE failure")
    return {"status": "UNRIGGED", "rig_handle": None, "owned_names_in_order": [], "hidden_groups": []}


fake_instance_1 = FakeInstance()
fake_dm_1 = FakeDataModel()
branch, count, disc_elapsed, native_elapsed, stream, anomalies = matched_native_and_discovery_workload(
    fake_instance_1, fake_dm_1, discover_raises, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch == "PRE_CAPTURE_UNSUPPORTED", "workload.case1_branch_correct (%r)" % (branch,))
expect(count == 2, "workload.case1_discovery_count_is_2 (%r)" % (count,))
expect(len(fake_instance_1.rebuild_calls) == 1, "workload.case1_native_rebuild_still_invoked")
expect([s[3] for s in stream] == ["PRE", "TERMINAL"], "workload.case1_stream_sites_correct (%r)" % ([s[3] for s in stream],))
expect(all(s[2] == branch for s in stream), "workload.case1_stream_entries_labeled_with_branch")

# --- Case 2: PRE succeeds but not SUPPORTED_ACTIVE_RIG -> STATUS_MISMATCH, 3. ---
call_log_2 = []


def discover_unrigged(shot, aset):
    call_log_2.append(1)
    return {"status": "UNRIGGED", "rig_handle": None, "owned_names_in_order": [], "hidden_groups": []}


fake_instance_2 = FakeInstance()
fake_dm_2 = FakeDataModel()
branch2, count2, _de2, _ne2, stream2, anomalies2 = matched_native_and_discovery_workload(
    fake_instance_2, fake_dm_2, discover_unrigged, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch2 == "NATIVE_POST_ONLY_STATUS_MISMATCH", "workload.case2_branch_correct (%r)" % (branch2,))
expect(count2 == 3, "workload.case2_discovery_count_is_3 (%r)" % (count2,))
expect(len(call_log_2) == 3, "workload.case2_discover_rig_context_called_exactly_3_times")
expect([s[3] for s in stream2] == ["PRE", "NATIVE_POST", "TERMINAL"], "workload.case2_stream_sites_correct (%r)" % ([s[3] for s in stream2],))

# --- Case 3: SUPPORTED_ACTIVE_RIG both PRE/POST, wrapper survived -> 3. ---
def discover_supported_matching(shot, aset):
    return {
        "status": "SUPPORTED_ACTIVE_RIG", "rig_handle": 777,
        "owned_names_in_order": [u"a", u"b"], "hidden_groups": [u"GroupA"],
    }


fake_instance_3 = FakeInstance()
fake_dm_3 = FakeDataModel()
branch3, count3, _de3, _ne3, stream3, anomalies3 = matched_native_and_discovery_workload(
    fake_instance_3, fake_dm_3, discover_supported_matching, fake_find_direct_child_wrapper_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch3 == "NATIVE_POST_WRAPPER_SURVIVED", "workload.case3_branch_correct (%r)" % (branch3,))
expect(count3 == 3, "workload.case3_discovery_count_is_3 (%r)" % (count3,))
expect(anomalies3 == [], "workload.case3_no_anomalies_on_clean_match")

# --- Case 4: SUPPORTED_ACTIVE_RIG both, no wrapper -> COMPOSER_ENTRY_PATH, 5. ---
fake_instance_4 = FakeInstance()
fake_dm_4 = FakeDataModel()
branch4, count4, _de4, _ne4, stream4, anomalies4 = matched_native_and_discovery_workload(
    fake_instance_4, fake_dm_4, discover_supported_matching, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch4 == "COMPOSER_ENTRY_PATH", "workload.case4_branch_correct (%r)" % (branch4,))
expect(count4 == 5, "workload.case4_discovery_count_is_5 (%r)" % (count4,))
expect(
    [s[3] for s in stream4] == ["PRE", "NATIVE_POST", "COMPOSER_BEFORE", "COMPOSER_AFTER", "TERMINAL"],
    "workload.case4_stream_sites_correct_and_ordered (%r)" % ([s[3] for s in stream4],),
)

# --- Case 5: POST rig_handle mismatch -> anomaly logged, branch still proceeds (not raised). ---
post_toggle = [0]


def discover_rig_handle_drifts(shot, aset):
    post_toggle[0] += 1
    if post_toggle[0] == 1:
        return {"status": "SUPPORTED_ACTIVE_RIG", "rig_handle": 111, "owned_names_in_order": [u"a"], "hidden_groups": []}
    return {"status": "SUPPORTED_ACTIVE_RIG", "rig_handle": 222, "owned_names_in_order": [u"a"], "hidden_groups": []}


fake_instance_5 = FakeInstance()
fake_dm_5 = FakeDataModel()
branch5, count5, _de5, _ne5, _stream5, anomalies5 = matched_native_and_discovery_workload(
    fake_instance_5, fake_dm_5, discover_rig_handle_drifts, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch5 == "COMPOSER_ENTRY_PATH", "workload.case5_branch_still_proceeds_despite_anomaly")
expect(len(anomalies5) == 1 and "rig identity changed" in anomalies5[0], "workload.case5_anomaly_logged_for_rig_handle_drift (%r)" % (anomalies5,))

sys.stdout.write("\n--- Resource-delta / ratio / incremental arithmetic (worked example) ---\n")

before = {"private": 3064614912, "free": 527847424, "largest_free": 299696128}
after = {"private": 3327598592, "free": 288116736, "largest_free": 126353408}

private_delta = after["private"] - before["private"]
free_vas_delta = after["free"] - before["free"]
largest_free_delta = after["largest_free"] - before["largest_free"]

NATIVE_ONLY_PRIVATE_DELTA = 14307328
NATIVE_ONLY_FREE_VAS_DELTA = -2490368

incremental_private = private_delta - NATIVE_ONLY_PRIVATE_DELTA
incremental_free_vas = free_vas_delta - NATIVE_ONLY_FREE_VAS_DELTA

expect(private_delta == 262983680, "delta.private_matches_worked_example (%r)" % (private_delta,))
expect(incremental_private == 248676352, "delta.incremental_private_matches_worked_example (%r)" % (incremental_private,))
expect(incremental_free_vas == -237240320, "delta.incremental_free_vas_matches_worked_example (%r)" % (incremental_free_vas,))

sys.stdout.write("\n--- Static safety checks on the actual deployed script source ---\n")


def never_actually_called(name):
    # Distinguishes a real call ("name(shot, aset)") from a documentation
    # reference ("name()", empty parens, used in prose to explain what this
    # design deliberately does NOT call) -- production's own real calls
    # always pass arguments, never zero.
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
expect(never_actually_called("isolation_fingerprint"), "script.never_calls_isolation_fingerprint")
expect(never_actually_called("verify_current_shot_peers"), "script.never_calls_verify_current_shot_peers")
expect(never_actually_called("semantic_target_fingerprint"), "script.never_calls_semantic_target_fingerprint")
expect("instance.finished = True" in script_text, "script.neutralizes_real_instance_before_any_event_pump")
expect(
    script_text.index("instance.finished = True") < script_text.index("work = instance.work"),
    "script.neutralization_happens_before_reading_instance_work",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
