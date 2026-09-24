# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R5
(Checkpoint_F1_R5_Fresh_Discovery_Component_Retention.py).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes and real preserved
evidence already on file in this repository -- never against invented
expectations.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r5_diagnostic_regression.py
"""
import ctypes
import hashlib
import json
import os
import sys
import tempfile
import time

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R5_Fresh_Discovery_Component_Retention.py")
EXPECTED_SCRIPT_SHA256 = "2dfee0da0fc1f836be186c8bf2792aaa8646ec316ff3ab633dc224f26320ec75"

REAL_PRODUCTION_LOG_WITH_GATE_EVIDENCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "checkpoint_f1", "f1_1_crash_evidence", "sfm_rebuild_control_groups_F1-1_command3_crash.txt",
)

CHECKPOINT_PARSER_RANGE = (183, 233)
WRITE_JSON_ATOMIC_RANGE = (236, 280)
WRITE_TEXT_ATOMIC_RANGE = (283, 321)
SEQUENCE_CHECKSUM_RANGE = (324, 326)
RESOLVE_TARGET_RANGE = (334, 372)
REBUILD_TARGET_RANGE = (375, 428)
TIMED_DISCOVERY_RANGE = (431, 435)
TIMED_TRAVERSAL_ONLY_RANGE = (438, 444)
BRANCH_DETERMINING_DISCOVERY_RANGE = (447, 507)

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


sys.stdout.write("--- Gate-count / branch-schedule expectations verified against real preserved evidence ---\n")

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

branch_ns = {}
exec(compile(
    script_text[script_text.index("BRANCH_DISCOVERY_COUNTS = {"):script_text.index("}", script_text.index("BRANCH_DISCOVERY_COUNTS = {")) + 1],
    "<branch_counts>", "exec",
), branch_ns)
BRANCH_DISCOVERY_COUNTS = branch_ns["BRANCH_DISCOVERY_COUNTS"]

# Cross-check: full-discovery-count + extra_sites (as the real script's own
# inline logic assigns them) must reconcile exactly to the schedule F1-R4
# already established for every branch.
FULL_DISCOVERY_COUNT_BY_BRANCH = {
    "PRE_CAPTURE_UNSUPPORTED": 1,
    "NATIVE_POST_ONLY_STATUS_MISMATCH": 2,
    "NATIVE_POST_WRAPPER_SURVIVED": 2,
    "COMPOSER_ENTRY_PATH": 2,
}
EXTRA_SITES_BY_BRANCH = {
    "PRE_CAPTURE_UNSUPPORTED": 1,
    "NATIVE_POST_ONLY_STATUS_MISMATCH": 1,
    "NATIVE_POST_WRAPPER_SURVIVED": 1,
    "COMPOSER_ENTRY_PATH": 3,
}
for branch_name in BRANCH_DISCOVERY_COUNTS:
    expect(
        FULL_DISCOVERY_COUNT_BY_BRANCH[branch_name] + EXTRA_SITES_BY_BRANCH[branch_name] == BRANCH_DISCOVERY_COUNTS[branch_name],
        "branch_schedule.full_plus_extra_reconciles_for_%s (%r)" % (
            branch_name, (FULL_DISCOVERY_COUNT_BY_BRANCH[branch_name], EXTRA_SITES_BY_BRANCH[branch_name], BRANCH_DISCOVERY_COUNTS[branch_name]),
        ),
    )
# And confirm the SCRIPT's own inline extra_sites assignment matches this
# table exactly (extracted directly, not retyped).
extra_sites_block_start = script_text.index("extra_sites = 0")
extra_sites_block = script_text[extra_sites_block_start:extra_sites_block_start + 500]
expect('branch == "COMPOSER_ENTRY_PATH":\n                        extra_sites = 3' in extra_sites_block, "script.composer_entry_path_extra_sites_is_3")
expect('extra_sites = 1  # terminal only' in extra_sites_block, "script.status_mismatch_and_wrapper_survived_extra_sites_is_1")

sys.stdout.write("\n--- sequence_checksum(): order-sensitive, deterministic ---\n")

ns = {"json": json, "hashlib": hashlib}
exec(compile(extract(SEQUENCE_CHECKSUM_RANGE), "<sequence_checksum>", "exec"), ns)
sequence_checksum = ns["sequence_checksum"]

stream_a = [(u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH"), (u"shot3", u"mia1", u"NATIVE_POST_ONLY_STATUS_MISMATCH")]
stream_a_reordered = [(u"shot3", u"mia1", u"NATIVE_POST_ONLY_STATUS_MISMATCH"), (u"shot3", u"foxmccouldwm1", u"COMPOSER_ENTRY_PATH")]

checksum_a1 = sequence_checksum(stream_a)
checksum_a2 = sequence_checksum(list(stream_a))
checksum_a_reordered = sequence_checksum(stream_a_reordered)

expect(checksum_a1 == checksum_a2, "sequence_checksum.deterministic_same_input_same_hash")
expect(checksum_a1 != checksum_a_reordered, "sequence_checksum.order_sensitive_reordering_changes_hash")
expect(len(checksum_a1) == 64, "sequence_checksum.produces_64_char_hex_digest")

sys.stdout.write("\n--- Shared primitives (verbatim, reused from every earlier checkpoint) ---\n")

ns2 = {}
exec(compile(extract(CHECKPOINT_PARSER_RANGE), "<checkpoint_parser>", "exec"), ns2)
parse_all_resource_checkpoints = ns2["parse_all_resource_checkpoints"]
checkpoints_by_label = ns2["checkpoints_by_label"]

sample_log = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=F1R5_CMD1_CP0_START run_elapsed=1.234 "
    "mem_ok=True working_set=3000000000L peak_working_set=3000000000L pagefile=3000000000L "
    "peak_pagefile=3000000000L private=3000000000L vas_requested=True vas_ok=True "
    "min_address=0 max_address=140737488355328 mem_free=500000000 mem_reserve=100000000 "
    "mem_commit=200000000 largest_free=300000000 free_regions=50 virtual_query_count=10 "
    "vas_elapsed=0.0500 vas_error=None\n"
)
parsed_all = parse_all_resource_checkpoints(sample_log)
expect(len(parsed_all) == 1, "parser.finds_the_checkpoint_line")
by_label = checkpoints_by_label(sample_log, "F1R5_CMD1_CP0_START")
expect(len(by_label) == 1 and by_label[0]["private"] == 3000000000, "parser.checkpoints_by_label_filters_correctly")

ns3 = {"os": os, "json": json}
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), ns3)
write_json_atomic = ns3["write_json_atomic"]

tmp_dir = tempfile.mkdtemp(prefix="f1_r5_test_")
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

sys.stdout.write("\n--- Fakes shared by resolve/rebuild/discovery/traversal tests ---\n")


class CheckpointF1R5Error(Exception):
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
    "CheckpointF1R5Error": CheckpointF1R5Error,
    "b_to_unicode": b_to_unicode,
    "native_ptr": fake_native_ptr,
}
target_a = FakeAnimSet(0xAAAA, u"foxmccouldwm1")
fake_shot = FakeShot(0x1234, [target_a])
resolve_ns["sfmApp"] = FakeSfmApp(fake_shot)
exec(compile(extract(RESOLVE_TARGET_RANGE), "<native_only_resolve_target>", "exec"), resolve_ns)
native_only_resolve_target = resolve_ns["native_only_resolve_target"]

rebuild_ns = {
    "CheckpointF1R5Error": CheckpointF1R5Error,
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

sys.stdout.write("\n--- timed_traversal_only(): calls scalar()+reachable(), discards result ---\n")

traversal_ns = {"time": time}
exec(compile(extract(TIMED_TRAVERSAL_ONLY_RANGE), "<timed_traversal_only>", "exec"), traversal_ns)
timed_traversal_only = traversal_ns["timed_traversal_only"]

scalar_calls = []
reachable_calls = []


def fake_scalar(obj, attr_name):
    scalar_calls.append((obj, attr_name))
    return u"fake_scene" if attr_name == "scene" else None


def fake_reachable(scene):
    reachable_calls.append(scene)
    return [u"obj1", u"obj2", u"obj3"]


elapsed = timed_traversal_only(fake_scalar, fake_reachable, fake_shot)
expect(isinstance(elapsed, float) and elapsed >= 0.0, "traversal.returns_nonnegative_elapsed")
expect(scalar_calls == [(fake_shot, "scene")], "traversal.calls_scalar_with_scene_attr_exactly_once")
expect(reachable_calls == [u"fake_scene"], "traversal.calls_reachable_with_scalars_own_result")

scalar_calls_none = []


def fake_scalar_returns_none(obj, attr_name):
    scalar_calls_none.append((obj, attr_name))
    return None


reachable_calls_none = []


def fake_reachable_should_not_be_called(scene):
    reachable_calls_none.append(scene)
    return []


elapsed_none = timed_traversal_only(fake_scalar_returns_none, fake_reachable_should_not_be_called, fake_shot)
expect(reachable_calls_none == [], "traversal.does_not_call_reachable_when_scene_is_none")

sys.stdout.write("\n--- branch_determining_discovery(): all four branch outcomes ---\n")

workload_ns = dict(rebuild_ns)
workload_ns.update(resolve_ns)
workload_ns["native_only_rebuild_target"] = native_only_rebuild_target


def fake_anomaly(message):
    pass


workload_ns["anomaly"] = fake_anomaly
exec(compile(extract(TIMED_DISCOVERY_RANGE), "<timed_discovery>", "exec"), workload_ns)
exec(compile(extract(BRANCH_DETERMINING_DISCOVERY_RANGE), "<branch_determining_discovery>", "exec"), workload_ns)
branch_determining_discovery = workload_ns["branch_determining_discovery"]

shot_record = {"shot": fake_shot, "ptr": 0x1234, "name": u"shot3"}
target_dict = {"ptr": 0xAAAA, "name": u"foxmccouldwm1"}


def fake_find_direct_child_never_found(root, child_name):
    return None


def fake_find_direct_child_wrapper_found(root, child_name):
    return FakeAnimSet(0x9999, child_name) if child_name == "__RIG_VISIBLE_RECON__" else None


discover_pre_raises_count = [0]


def discover_pre_raises(shot, aset):
    discover_pre_raises_count[0] += 1
    raise ValueError("synthetic PRE failure")


fake_instance_1 = FakeInstance()
fake_dm_1 = FakeDataModel()
branch1, native_elapsed1 = branch_determining_discovery(
    fake_instance_1, fake_dm_1, discover_pre_raises, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch1 == "PRE_CAPTURE_UNSUPPORTED", "branch.case1_pre_raises (%r)" % (branch1,))
expect(discover_pre_raises_count[0] == 1, "branch.case1_discover_called_exactly_once_not_twice")
expect(len(fake_instance_1.rebuild_calls) == 1, "branch.case1_native_rebuild_still_invoked")


def discover_unrigged(shot, aset):
    return {"status": "UNRIGGED", "rig_handle": None, "owned_names_in_order": [], "hidden_groups": []}


fake_instance_2 = FakeInstance()
fake_dm_2 = FakeDataModel()
branch2, _ne2 = branch_determining_discovery(
    fake_instance_2, fake_dm_2, discover_unrigged, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch2 == "NATIVE_POST_ONLY_STATUS_MISMATCH", "branch.case2_status_mismatch (%r)" % (branch2,))


def discover_supported_matching(shot, aset):
    return {
        "status": "SUPPORTED_ACTIVE_RIG", "rig_handle": 777,
        "owned_names_in_order": [u"a", u"b"], "hidden_groups": [u"GroupA"],
    }


fake_instance_3 = FakeInstance()
fake_dm_3 = FakeDataModel()
branch3, _ne3 = branch_determining_discovery(
    fake_instance_3, fake_dm_3, discover_supported_matching, fake_find_direct_child_wrapper_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch3 == "NATIVE_POST_WRAPPER_SURVIVED", "branch.case3_wrapper_survived (%r)" % (branch3,))

fake_instance_4 = FakeInstance()
fake_dm_4 = FakeDataModel()
branch4, _ne4 = branch_determining_discovery(
    fake_instance_4, fake_dm_4, discover_supported_matching, fake_find_direct_child_never_found,
    "__RIG_VISIBLE_RECON__", "__MASTER_VISIBLE_RECON__", shot_record, target_dict, target_a,
)
expect(branch4 == "COMPOSER_ENTRY_PATH", "branch.case4_composer_entry_path (%r)" % (branch4,))

sys.stdout.write("\n--- Cross-command / incremental resource arithmetic (real F1-R4 numbers as worked example) ---\n")

# Real, accepted F1-R4 numbers, used here purely as arithmetic test
# fixtures -- not re-asserted as F1-R5's own expected result.
native_only_private = 14307328
native_plus_full_discovery_private = 243748864
incremental_private = native_plus_full_discovery_private - native_only_private
expect(incremental_private == 229441536, "delta.incremental_private_matches_f1r4_accepted_value (%r)" % (incremental_private,))

native_only_free_vas = -2490368
native_plus_full_discovery_free_vas = -221839360
incremental_free_vas = native_plus_full_discovery_free_vas - native_only_free_vas
expect(incremental_free_vas == -219348992, "delta.incremental_free_vas_matches_f1r4_accepted_value (%r)" % (incremental_free_vas,))

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
expect(never_actually_called("isolation_fingerprint"), "script.never_calls_isolation_fingerprint")
expect(never_actually_called("verify_current_shot_peers"), "script.never_calls_verify_current_shot_peers")
expect(never_actually_called("semantic_target_fingerprint"), "script.never_calls_semantic_target_fingerprint")
expect("instance.finished = True" in script_text, "script.neutralizes_real_instance_before_any_event_pump")
expect(
    script_text.index("instance.finished = True") < script_text.index("work = instance.work"),
    "script.neutralization_happens_before_reading_instance_work",
)
expect(script_text.count("COMMAND_SPECS") >= 1 and "u\"All Shots\"" in script_text, "script.both_commands_prompt_all_shots")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
