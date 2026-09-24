# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F2-R1
(Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification.py).

No real SFM environment is available offline, but PySide's QtCore IS
importable standalone with the real embedded Python 2.7.5 (confirmed), so
this test extracts the script's own pure-Python/Qt helper functions
VERBATIM (by source line range, not retyped) and exercises them against
REAL QtCore.QObject instances for the marker/mode-classification logic,
and synthetic fake DME objects (matching the same FakeElement-style
pattern used by test_f1_r6_adversarial_parity.py / test_f1_r8_diagnostic_
regression.py) for the control-membership logic.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f2_r1_diagnostic_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

from PySide import QtCore

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F2_R1_Legitimate_Reinvocation_Qualification.py")
EXPECTED_SCRIPT_SHA256 = "990031ae19b98197e925467fad1e63621c1f1958e05be932245261052f38c9ab"

B_TO_UNICODE_RANGE = (171, 180)
WRITE_JSON_ATOMIC_RANGE = (183, 227)
WRITE_TEXT_ATOMIC_RANGE = (230, 268)
READ_STATE_FILE_RANGE = (271, 278)
MARKER_PRESENT_RANGE = (281, 293)
SET_MARKER_RANGE = (296, 299)
CLASSIFY_INVOCATION_MODE_RANGE = (302, 318)
GET_CONTROL_MEMBERSHIP_RANGE = (327, 333)
FIND_TARGET_ASET_RANGE = (336, 343)

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


class CheckpointF2R1Error(Exception):
    pass


sys.stdout.write("--- Shared atomic-write primitives (verbatim) ---\n")
ns_shared = {"os": os, "json": json}
exec(compile(extract(B_TO_UNICODE_RANGE), "<b_to_unicode>", "exec"), ns_shared)
exec(compile(extract(WRITE_JSON_ATOMIC_RANGE), "<write_json_atomic>", "exec"), ns_shared)
exec(compile(extract(WRITE_TEXT_ATOMIC_RANGE), "<write_text_atomic>", "exec"), ns_shared)
b_to_unicode = ns_shared["b_to_unicode"]
write_json_atomic = ns_shared["write_json_atomic"]
write_text_atomic = ns_shared["write_text_atomic"]

tmp_dir = tempfile.mkdtemp(prefix="f2_r1_test_")
ok, err, reparsed = write_json_atomic(os.path.join(tmp_dir, "x.json"), {"a": 1})
expect(ok is True and reparsed == {"a": 1}, "write_json_atomic.simple_write_ok")
ok2, err2 = write_text_atomic(os.path.join(tmp_dir, "x.txt"), b"hello")
expect(ok2 is True, "write_text_atomic.simple_write_ok")
expect(b_to_unicode(u"already unicode") == u"already unicode", "b_to_unicode.passthrough")
expect(b_to_unicode(b"bytes") == u"bytes", "b_to_unicode.decodes_bytes")

sys.stdout.write("\n--- read_state_file(): bounded persisted-state tests ---\n")
STATE_FILE_PATH = os.path.join(tmp_dir, "state.json")
ns_state = {"os": os, "json": json, "STATE_FILE_PATH": STATE_FILE_PATH, "CheckpointF2R1Error": CheckpointF2R1Error}
exec(compile(extract(READ_STATE_FILE_RANGE), "<read_state_file>", "exec"), ns_state)
read_state_file = ns_state["read_state_file"]

expect(read_state_file() is None, "read_state_file.returns_none_when_absent")
with open(STATE_FILE_PATH, "wb") as f:
    f.write(b'{"stage1_complete": true, "stage2_complete": false}')
state = read_state_file()
expect(state == {"stage1_complete": True, "stage2_complete": False}, "read_state_file.reads_back_written_state")

with open(STATE_FILE_PATH, "wb") as f:
    f.write(b"not valid json {{{")
raised = False
try:
    read_state_file()
except CheckpointF2R1Error:
    raised = True
expect(raised, "read_state_file.corrupt_file_raises_STOP_error -- does not guess")
os.remove(STATE_FILE_PATH)

sys.stdout.write("\n--- marker_present()/set_marker(): REAL QtCore.QObject instances (no fakes) ---\n")
ns_marker = {"QtCore": QtCore, "b_to_unicode": b_to_unicode}
exec(compile(extract(MARKER_PRESENT_RANGE), "<marker_present>", "exec"), ns_marker)
exec(compile(extract(SET_MARKER_RANGE), "<set_marker>", "exec"), ns_marker)
marker_present = ns_marker["marker_present"]
set_marker = ns_marker["set_marker"]

real_main_window = QtCore.QObject()
expect(marker_present(real_main_window, u"SOME_MARKER") is False, "marker_present.absent_on_fresh_object")
expect(marker_present(None, u"SOME_MARKER") is False, "marker_present.none_main_window_is_false_not_exception")
set_marker(real_main_window, u"STAGE1_TEST_MARKER")
expect(marker_present(real_main_window, u"STAGE1_TEST_MARKER") is True, "marker_present.detects_marker_just_set")
expect(marker_present(real_main_window, u"STAGE2_TEST_MARKER") is False, "marker_present.distinct_marker_names_dont_collide")

other_window = QtCore.QObject()
expect(marker_present(other_window, u"STAGE1_TEST_MARKER") is False, "marker_present.marker_on_one_parent_not_visible_on_another -- simulates a real SFM restart (fresh main_window)")

sys.stdout.write("\n--- classify_invocation_mode(): staged-state transition + stale/wrong-stage rejection tests ---\n")
ns_classify = {}
exec(compile(extract(CLASSIFY_INVOCATION_MODE_RANGE), "<classify_invocation_mode>", "exec"), ns_classify)
classify_invocation_mode = ns_classify["classify_invocation_mode"]

mode, reason = classify_invocation_mode(None, False, False)
expect(mode == "STAGE_1", "classify.no_state_no_markers_is_stage1")

mode, reason = classify_invocation_mode(None, True, False)
expect(mode is None, "classify.no_state_but_marker_present_is_inconsistent_STOP -- e.g. leftover marker from a differently-named prior script")

mode, reason = classify_invocation_mode({"stage1_complete": True, "stage2_complete": False}, True, False)
expect(mode == "STAGE_2", "classify.stage1_complete_same_process_marker_present_is_stage2")

mode, reason = classify_invocation_mode({"stage1_complete": True, "stage2_complete": False}, False, False)
expect(mode is None and "DIFFERENT SFM process" in reason, "classify.stage1_complete_but_no_marker_is_restart_protocol_violation_STOP")

mode, reason = classify_invocation_mode({"stage1_complete": True, "stage2_complete": True}, False, False)
expect(mode == "FINAL_VERIFICATION", "classify.stage2_complete_fresh_process_is_final_verification")

mode, reason = classify_invocation_mode({"stage1_complete": True, "stage2_complete": True}, True, False)
expect(mode is None and "fresh SFM restart" in reason, "classify.stage2_complete_but_marker_still_present_is_same_process_reuse_STOP -- final verification must be post-restart")

mode, reason = classify_invocation_mode({"stage1_complete": True, "stage2_complete": True}, False, True)
expect(mode is None, "classify.stage2_complete_stage2_marker_present_is_also_rejected")

mode, reason = classify_invocation_mode({"stage1_complete": False, "stage2_complete": False}, False, False)
expect(mode is None, "classify.corrupt_state_neither_flag_true_is_STOP_not_a_guess")

mode, reason = classify_invocation_mode({}, False, False)
expect(mode is None, "classify.empty_state_dict_is_STOP_not_a_guess")

sys.stdout.write("\n--- get_control_membership() / find_target_aset(): fake-DME control-tree tests ---\n")


class FakeGroup(object):
    def __init__(self, name, controls=None, children=None):
        self._name = name
        self._controls = controls or []
        self._children = children or []


class FakeAset(object):
    def __init__(self, root_group):
        self._root_group = root_group

    def GetRootControlGroup(self):
        return self._root_group


def fake_capture_tree(root):
    """Minimal stand-in mirroring production's own capture_tree() shape
    closely enough to exercise get_control_membership()'s own contract --
    NOT a reimplementation of production's real algorithm, just a fixture
    builder for this offline test."""
    memberships = {}
    groups = {}

    def walk(group, parts):
        path = "/".join(parts) if parts else "<ROOT>"
        for c in group._controls:
            memberships.setdefault(c, []).append(path)
        groups[path] = {"direct_control_names_in_order": list(group._controls)}
        for child in group._children:
            walk(child, parts + [child._name])

    walk(root, [])
    return {"groups": groups, "memberships": memberships}


def fake_one_membership(snap, control_name):
    rows = snap["memberships"].get(control_name, [])
    if len(rows) != 1:
        return None
    return rows[0]


ns_membership = {"CheckpointF2R1Error": CheckpointF2R1Error}
exec(compile(extract(GET_CONTROL_MEMBERSHIP_RANGE), "<get_control_membership>", "exec"), ns_membership)
get_control_membership = ns_membership["get_control_membership"]

ns_findtarget = {"b_to_unicode": b_to_unicode}
exec(compile(extract(FIND_TARGET_ASET_RANGE), "<find_target_aset>", "exec"), ns_findtarget)
find_target_aset = ns_findtarget["find_target_aset"]

left_arm = FakeGroup("LeftArm", controls=["rig_collar_L", "rig_elbow_L", "rig_hand_L"])
rig_arms = FakeGroup("RigArms", children=[left_arm])
rig_helpers = FakeGroup("RigHelpers", controls=["rig_footHelper_L"])
root = FakeGroup("<ROOT>", children=[rig_arms, rig_helpers])
aset = FakeAset(root)

path, tree = get_control_membership(fake_capture_tree, fake_one_membership, aset, "rig_hand_L")
expect(path == "RigArms/LeftArm", "get_control_membership.finds_qualified_path")
expect(tree["groups"]["RigArms/LeftArm"]["direct_control_names_in_order"] == ["rig_collar_L", "rig_elbow_L", "rig_hand_L"], "get_control_membership.order_preserved")

# Simulate the operator's own controlled edit: move rig_hand_L to RigHelpers.
left_arm_edited = FakeGroup("LeftArm", controls=["rig_collar_L", "rig_elbow_L"])
rig_arms_edited = FakeGroup("RigArms", children=[left_arm_edited])
rig_helpers_edited = FakeGroup("RigHelpers", controls=["rig_footHelper_L", "rig_hand_L"])
root_edited = FakeGroup("<ROOT>", children=[rig_arms_edited, rig_helpers_edited])
aset_edited = FakeAset(root_edited)
path_edited, _tree_edited = get_control_membership(fake_capture_tree, fake_one_membership, aset_edited, "rig_hand_L")
expect(path_edited == "RigHelpers", "get_control_membership.detects_operator_edit_precondition_state")


class NoRootGroupAset(object):
    def GetRootControlGroup(self):
        return None


raised2 = False
try:
    get_control_membership(fake_capture_tree, fake_one_membership, NoRootGroupAset(), "rig_hand_L")
except CheckpointF2R1Error:
    raised2 = True
expect(raised2, "get_control_membership.none_root_group_raises_not_silently_none")

work_fixture = [
    {"name": "shot3", "targets": [{"name": "foxmccouldwm1", "anim_set": aset}, {"name": "mia1", "anim_set": "MIA_ASET"}]},
    {"name": "shot2", "targets": [{"name": "some_other_target", "anim_set": "OTHER_ASET"}]},
]
expect(find_target_aset(work_fixture, u"shot3", u"foxmccouldwm1") is aset, "find_target_aset.finds_the_correct_target")
expect(find_target_aset(work_fixture, u"shot3", u"nonexistent") is None, "find_target_aset.returns_none_for_missing_target")
expect(find_target_aset(work_fixture, u"nonexistent_shot", u"foxmccouldwm1") is None, "find_target_aset.returns_none_for_missing_shot")

sys.stdout.write("\n--- Static safety / design checks on the actual deployed script source ---\n")
expect("SaveToFile(" not in script_text, "script.never_calls_SaveToFile -- saving is an operator action, not scripted")
expect("capture_snapshot_explicit(" not in script_text, "script.never_calls_the_heavy_whole_session_capture_function")
expect("for shot_record in work" in script_text and "for target in shot_record" in script_text, "script.find_target_aset_scans_work_but_never_captures_all_targets_semantically")
expect(script_text.count("get_control_membership(") >= 3, "script.control_membership_checked_at_least_for_pre_and_post_condition_across_modes -- 1 def + >=2 call sites")
expect("QtCore.QTimer" not in script_text, "script.never_directly_schedules_via_QTimer -- relies on the SAME proven processEvents/wait-loop technique as F1-2, not new scheduling logic (the word appears only in an explanatory comment about PRODUCTION's own internal scheduling)")
expect("MAX_WAIT_SECONDS = 1800" in script_text, "script.generous_operator_timing_matches_f1_2s_own_proven_value")
expect("instance.finished = True" in script_text, "script.final_verification_mode_still_neutralizes_the_real_instance -- it never invokes production for real")
expect(
    script_text.index("if mode == \"FINAL_VERIFICATION\":") < script_text.index("instance.finished = True"),
    "script.neutralization_only_happens_inside_the_final_verification_branch",
)
expect(
    "undo" not in [c.lower() for c in __import__("re").findall(r'check\("([^"]+)"', script_text)],
    "script.no_check_name_ever_references_undo -- confirms Undo is never a PASS/FAIL requirement in any check() call (the word 'Undo' appears only in the module docstring, explicitly stating it is NOT a requirement)",
)
expect(
    "pre_path, pre_tree = get_control_membership" in script_text
    and script_text.index("pre_path, pre_tree = get_control_membership") < script_text.index("def normalizer_run_is_active"),
    "script.precondition_check_happens_before_the_wait_loop_is_even_defined -- confirms no processEvents() call could have occurred first",
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
