# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R3
(Checkpoint_F1_R3_Native_Only_Retention_Attribution.py).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes and real preserved
evidence already on file in this repository -- never against invented
expectations.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r3_diagnostic_regression.py
"""
import ctypes
import hashlib
import json
import os
import sys
import time

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R3_Native_Only_Retention_Attribution.py")
EXPECTED_SCRIPT_SHA256 = "c3b3098dfdd737899a6c1a9cbec3fd8d552db0423ca7fad35693dcdc8f9195c6"

REAL_PRODUCTION_LOG_WITH_GATE_EVIDENCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "checkpoint_f1", "f1_1_crash_evidence", "sfm_rebuild_control_groups_F1-1_command3_crash.txt",
)

CHECKPOINT_PARSER_RANGE = (184, 235)
WRITE_JSON_ATOMIC_RANGE = (237, 282)
WRITE_TEXT_ATOMIC_RANGE = (284, 322)
SEQUENCE_CHECKSUM_RANGE = (325, 327)
RESOLVE_TARGET_RANGE = (344, 382)
REBUILD_TARGET_RANGE = (385, 442)

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


sys.stdout.write("--- Gate-count expectations verified against real preserved production evidence ---\n")

with open(REAL_PRODUCTION_LOG_WITH_GATE_EVIDENCE, "rb") as f:
    real_log_text = f.read().decode("ascii", "replace")

expect(
    "gate skips static=12 follower=4 lowbone_no_alh=7 failclosed_process=0" in real_log_text,
    "gate_evidence.real_log_contains_exact_expected_skip_line",
)
expect(
    "scoped_shots=15" in real_log_text,
    "gate_evidence.real_log_contains_expected_shot_count",
)

for expected_constant, expected_value in (
    ("EXPECTED_TOTAL_SHOTS = 15", True),
    ("EXPECTED_MODEL_BACKED_TARGETS = 85", True),
    ("EXPECTED_GATE_STATIC_SKIPS = 12", True),
    ("EXPECTED_GATE_FOLLOWER_SKIPS = 4", True),
    ("EXPECTED_GATE_LOWBONE_SKIPS = 7", True),
    ("EXPECTED_GATE_FAILCLOSED_PROCESS = 0", True),
    ("EXPECTED_ELIGIBLE_NATIVE_TARGETS = 62", True),
):
    expect(expected_constant in script_text, "script.contains_expected_gate_constant: %s" % expected_constant)

expect(85 - (12 + 4 + 7 + 0) == 62, "gate_evidence.arithmetic_reconciles_85_minus_23_equals_62")

sys.stdout.write("\n--- sequence_checksum(): order-sensitive, deterministic ---\n")

ns = {"json": json, "hashlib": hashlib}
exec(compile(extract(SEQUENCE_CHECKSUM_RANGE), "<sequence_checksum>", "exec"), ns)
sequence_checksum = ns["sequence_checksum"]

pairs_a = [(u"shot3", u"foxmccouldwm1"), (u"shot3", u"mia1")]
pairs_a_reordered = [(u"shot3", u"mia1"), (u"shot3", u"foxmccouldwm1")]
pairs_b = [(u"shot3", u"foxmccouldwm1"), (u"shot4", u"mia1")]

checksum_a1 = sequence_checksum(pairs_a)
checksum_a2 = sequence_checksum(list(pairs_a))
checksum_a_reordered = sequence_checksum(pairs_a_reordered)
checksum_b = sequence_checksum(pairs_b)

expect(checksum_a1 == checksum_a2, "sequence_checksum.deterministic_same_input_same_hash")
expect(checksum_a1 != checksum_a_reordered, "sequence_checksum.order_sensitive_reordering_changes_hash")
expect(checksum_a1 != checksum_b, "sequence_checksum.content_sensitive_different_pairs_change_hash")
expect(len(checksum_a1) == 64, "sequence_checksum.produces_64_char_hex_digest")

sys.stdout.write("\n--- Shared primitives (verbatim, reused from every earlier checkpoint) ---\n")

ns2 = {}
exec(compile(extract(CHECKPOINT_PARSER_RANGE), "<checkpoint_parser>", "exec"), ns2)
parse_resource_checkpoint_line = ns2["parse_resource_checkpoint_line"]
parse_all_resource_checkpoints = ns2["parse_all_resource_checkpoints"]
checkpoints_by_label = ns2["checkpoints_by_label"]

sample_log = (
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=F1R3_CP0_NATIVE_ONLY_START run_elapsed=1.234 "
    "mem_ok=True working_set=3000000000L peak_working_set=3000000000L pagefile=3000000000L "
    "peak_pagefile=3000000000L private=3000000000L vas_requested=True vas_ok=True "
    "min_address=0 max_address=140737488355328 mem_free=500000000 mem_reserve=100000000 "
    "mem_commit=200000000 largest_free=300000000 free_regions=50 virtual_query_count=10 "
    "vas_elapsed=0.0500 vas_error=None\n"
    "CONTEXTUALIZER_RESOURCE_CHECKPOINT label=F1R3_CP_FINAL_NATIVE_TARGET_COMPLETE run_elapsed=9.876 "
    "mem_ok=True working_set=3260000000L peak_working_set=3260000000L pagefile=3260000000L "
    "peak_pagefile=3260000000L private=3260000000L vas_requested=True vas_ok=True "
    "min_address=0 max_address=140737488355328 mem_free=270000000 mem_reserve=100000000 "
    "mem_commit=430000000 largest_free=190000000 free_regions=60 virtual_query_count=20 "
    "vas_elapsed=0.0600 vas_error=None\n"
)

parsed_all = parse_all_resource_checkpoints(sample_log)
expect(len(parsed_all) == 2, "parser.finds_both_checkpoint_lines")
by_label = checkpoints_by_label(sample_log, "F1R3_CP_FINAL_NATIVE_TARGET_COMPLETE")
expect(len(by_label) == 1 and by_label[0]["private"] == 3260000000, "parser.checkpoints_by_label_filters_correctly")

ns3 = {"os": os, "json": json}
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), ns3)
write_json_atomic = ns3["write_json_atomic"]

import tempfile
tmp_dir = tempfile.mkdtemp(prefix="f1_r3_test_")
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
with open(text_target, "rb") as f:
    expect(f.read() == b"hello world", "write_text_atomic.content_matches_written")

sys.stdout.write("\n--- native_only_resolve_target(): reused re-resolution matching logic ---\n")


class CheckpointF1R3Error(Exception):
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
    "CheckpointF1R3Error": CheckpointF1R3Error,
    "b_to_unicode": b_to_unicode,
    "native_ptr": fake_native_ptr,
}
target_a = FakeAnimSet(0xAAAA, u"foxmccouldwm1")
target_b = FakeAnimSet(0xBBBB, u"mia1")
fake_shot = FakeShot(0x1234, [target_a, target_b])
resolve_ns["sfmApp"] = FakeSfmApp(fake_shot)
exec(compile(extract(RESOLVE_TARGET_RANGE), "<native_only_resolve_target>", "exec"), resolve_ns)
native_only_resolve_target = resolve_ns["native_only_resolve_target"]

shot_record = {"ptr": 0x1234, "name": u"shot3"}
target_dict = {"ptr": 0xAAAA, "name": u"foxmccouldwm1"}
fake_instance = FakeInstance()

resolved = native_only_resolve_target(fake_instance, shot_record, target_dict)
expect(resolved is target_a, "resolve.finds_the_correct_unique_match")
expect(fake_instance.run_lock_asserted == 1, "resolve.asserts_run_lock_present")
expect(fake_instance.master_stable_asserted == 1, "resolve.asserts_master_stable")

wrong_shot_record = {"ptr": 0x9999, "name": u"shot_wrong"}
raised_context_mismatch = False
try:
    native_only_resolve_target(fake_instance, wrong_shot_record, target_dict)
except CheckpointF1R3Error:
    raised_context_mismatch = True
expect(raised_context_mismatch, "resolve.raises_on_shot_context_mismatch")

missing_target = {"ptr": 0xFFFF, "name": u"does_not_exist"}
raised_no_match = False
try:
    native_only_resolve_target(fake_instance, shot_record, missing_target)
except CheckpointF1R3Error:
    raised_no_match = True
expect(raised_no_match, "resolve.raises_when_zero_matches")

sys.stdout.write("\n--- native_only_rebuild_target(): guarded native-invocation slice ---\n")

rebuild_ns = {
    "CheckpointF1R3Error": CheckpointF1R3Error,
    "native_ptr": fake_native_ptr,
    "ctypes": ctypes,
    "time": time,
}

protect_calls = {"acquire": [], "release": []}


def fake_native_master_protect_acquire(path):
    protect_calls["acquire"].append(path)
    return 0xDEADBEEF


def fake_native_master_protect_release(handle):
    protect_calls["release"].append(handle)


rebuild_ns["native_master_protect_acquire"] = fake_native_master_protect_acquire
rebuild_ns["native_master_protect_release"] = fake_native_master_protect_release
exec(compile(extract(REBUILD_TARGET_RANGE), "<native_only_rebuild_target>", "exec"), rebuild_ns)
native_only_rebuild_target = rebuild_ns["native_only_rebuild_target"]

fake_instance2 = FakeInstance()
fake_dm = FakeDataModel()

elapsed = native_only_rebuild_target(fake_instance2, fake_dm, target_a, 0xAAAA)
expect(isinstance(elapsed, float) and elapsed >= 0.0, "rebuild.returns_nonnegative_elapsed_seconds")
expect(len(fake_instance2.rebuild_calls) == 1, "rebuild.native_rebuild_called_exactly_once")
expect(isinstance(fake_instance2.rebuild_calls[0], ctypes.c_void_p), "rebuild.native_call_receives_ctypes_c_void_p")
expect(fake_dm.set_undo_calls == [False, True], "rebuild.undo_disabled_then_restored_in_order")
expect(protect_calls["acquire"] == [fake_instance2.master_path], "rebuild.master_protection_acquired_with_master_path")
expect(protect_calls["release"] == [0xDEADBEEF], "rebuild.master_protection_released_with_acquired_handle")
expect(fake_dm.IsUndoEnabled() is True, "rebuild.undo_ends_enabled_again_matching_prior_state")

# Failure path: pointer-stability mismatch must raise BEFORE any native
# call, Undo change, or protection acquisition.
fake_instance3 = FakeInstance()
fake_dm3 = FakeDataModel()
protect_calls["acquire"] = []
protect_calls["release"] = []
raised_ptr_mismatch = False
try:
    native_only_rebuild_target(fake_instance3, fake_dm3, target_a, 0xFFFF)
except CheckpointF1R3Error:
    raised_ptr_mismatch = True
expect(raised_ptr_mismatch, "rebuild.raises_on_pointer_stability_mismatch")
expect(len(fake_instance3.rebuild_calls) == 0, "rebuild.pointer_mismatch_prevents_native_call")
expect(protect_calls["acquire"] == [], "rebuild.pointer_mismatch_prevents_protection_acquisition")
expect(fake_dm3.set_undo_calls == [], "rebuild.pointer_mismatch_prevents_undo_change")

# Failure path: lost model backing must raise before the native call, but
# AFTER pointer-stability passes.
fake_instance4 = FakeInstance()
fake_instance4.game_model_ok = False
fake_dm4 = FakeDataModel()
raised_no_model = False
try:
    native_only_rebuild_target(fake_instance4, fake_dm4, target_a, 0xAAAA)
except CheckpointF1R3Error:
    raised_no_model = True
expect(raised_no_model, "rebuild.raises_when_model_backing_lost")
expect(len(fake_instance4.rebuild_calls) == 0, "rebuild.lost_model_backing_prevents_native_call")

# Failure path: lost root group must raise before the native call.
fake_instance5 = FakeInstance()
fake_instance5.root_ok = False
fake_dm5 = FakeDataModel()
raised_no_root = False
try:
    native_only_rebuild_target(fake_instance5, fake_dm5, target_a, 0xAAAA)
except CheckpointF1R3Error:
    raised_no_root = True
expect(raised_no_root, "rebuild.raises_when_root_group_lost")
expect(len(fake_instance5.rebuild_calls) == 0, "rebuild.lost_root_group_prevents_native_call")

sys.stdout.write("\n--- Resource-delta / ratio arithmetic (worked example) ---\n")

before = {"private": 3064614912, "free": 527847424, "largest_free": 299696128}
after = {"private": 3327598592, "free": 288116736, "largest_free": 126353408}

private_delta = after["private"] - before["private"]
free_vas_delta = after["free"] - before["free"]
largest_free_delta = after["largest_free"] - before["largest_free"]

expect(private_delta == 262983680, "delta.private_matches_worked_example (%r)" % (private_delta,))
expect(free_vas_delta == -239730688, "delta.free_vas_matches_worked_example (%r)" % (free_vas_delta,))
expect(largest_free_delta == -173342720, "delta.largest_free_matches_worked_example (%r)" % (largest_free_delta,))

PRODUCTION_PRIVATE_DELTA = 265461760
PRODUCTION_FREE_VAS_DELTA = -237633536
native_private_ratio = float(private_delta) / float(PRODUCTION_PRIVATE_DELTA)
native_free_vas_loss_ratio = float(free_vas_delta) / float(PRODUCTION_FREE_VAS_DELTA)
expect(abs(native_private_ratio - 0.9906650208301188) < 1e-9, "ratio.native_private_ratio_arithmetic_correct (%r)" % (native_private_ratio,))
expect(abs(native_free_vas_loss_ratio - 1.0088251516822946) < 1e-9, "ratio.native_free_vas_loss_ratio_arithmetic_correct (%r)" % (native_free_vas_loss_ratio,))

sys.stdout.write("\n--- Static safety checks on the actual deployed script source ---\n")

# These check for actual CALL syntax ("name(") rather than a bare
# substring match, since the script's own docstring and comments legitimately
# MENTION each of these names to document what this checkpoint deliberately
# does not do -- a bare substring check would false-positive on that prose.
expect("SaveToFile(" not in script_text, "script.never_calls_SaveToFile -- no-save behavior enforced")
expect("discover_rig_context(" not in script_text, "script.never_calls_discover_rig_context")
expect("capture_snapshot_explicit(" not in script_text, "script.never_calls_capture_snapshot_explicit")
expect("production_generic_composer(" not in script_text, "script.never_calls_production_generic_composer")
expect("preflight_reconciliation_plan(" not in script_text, "script.never_calls_preflight_reconciliation_plan")
expect("instance.finished = True" in script_text, "script.neutralizes_real_instance_before_any_event_pump")
expect("FORBIDDEN_ORIGINAL_FIXTURE_FILENAME" in script_text, "script.refuses_original_fixture_by_filename")
expect(
    script_text.index("instance.finished = True") < script_text.index("work = instance.work"),
    "script.neutralization_happens_before_reading_instance_work",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
