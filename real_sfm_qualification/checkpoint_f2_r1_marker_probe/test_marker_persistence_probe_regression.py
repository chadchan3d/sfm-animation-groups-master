# -*- coding: utf-8 -*-
"""
Offline regression for the F2-R1 Marker Persistence Probe
(Checkpoint_F2_R1_Marker_Persistence_Probe.py).

Uses REAL QtCore.QObject instances (PySide's QtCore is importable
standalone with the real embedded Python 2.7.5, confirmed directly) to
exercise find_probe_marker()/install_probe_marker() -- no fakes needed for
the Qt-level logic. classify_probe_invocation()/extract_pid_from_marker_
name()/read_state() are pure/file-backed and extracted verbatim.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_marker_persistence_probe_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

from PySide import QtCore

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F2_R1_Marker_Persistence_Probe.py")
EXPECTED_SCRIPT_SHA256 = "fba33198b636330d9a88cd4733f526a59a87cff1e201bfcf0b0f589ca1471b7d"

READ_STATE_RANGE = (136, 143)
FIND_PROBE_MARKER_RANGE = (146, 156)
INSTALL_PROBE_MARKER_RANGE = (159, 162)
EXTRACT_PID_RANGE = (165, 172)
CLASSIFY_PROBE_INVOCATION_RANGE = (175, 183)

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


class MarkerProbeError(Exception):
    pass


def b_to_unicode(value):
    if isinstance(value, unicode):
        return value
    return value.decode("utf-8")


MARKER_NAME_PREFIX = u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_"

ns = {
    "os": os, "json": json, "QtCore": QtCore,
    "b_to_unicode": b_to_unicode, "MarkerProbeError": MarkerProbeError,
    "MARKER_NAME_PREFIX": MARKER_NAME_PREFIX,
}
tmp_dir = tempfile.mkdtemp(prefix="marker_probe_test_")
STATE_PATH = os.path.join(tmp_dir, "state.json")
ns["STATE_PATH"] = STATE_PATH

exec(compile(extract(READ_STATE_RANGE), "<read_state>", "exec"), ns)
exec(compile(extract(FIND_PROBE_MARKER_RANGE), "<find_probe_marker>", "exec"), ns)
exec(compile(extract(INSTALL_PROBE_MARKER_RANGE), "<install_probe_marker>", "exec"), ns)
exec(compile(extract(EXTRACT_PID_RANGE), "<extract_pid_from_marker_name>", "exec"), ns)
exec(compile(extract(CLASSIFY_PROBE_INVOCATION_RANGE), "<classify_probe_invocation>", "exec"), ns)

read_state = ns["read_state"]
find_probe_marker = ns["find_probe_marker"]
install_probe_marker = ns["install_probe_marker"]
extract_pid_from_marker_name = ns["extract_pid_from_marker_name"]
classify_probe_invocation = ns["classify_probe_invocation"]

sys.stdout.write("--- read_state() ---\n")
expect(read_state() is None, "read_state.absent_returns_none")
with open(STATE_PATH, "wb") as f:
    f.write(b'{"installed": true, "install_pid": 4242}')
expect(read_state() == {"installed": True, "install_pid": 4242}, "read_state.reads_back_written_state")
with open(STATE_PATH, "wb") as f:
    f.write(b"not json")
raised = False
try:
    read_state()
except MarkerProbeError:
    raised = True
expect(raised, "read_state.corrupt_file_raises_not_a_guess")
os.remove(STATE_PATH)

sys.stdout.write("\n--- find_probe_marker()/install_probe_marker(): REAL QtCore.QObject instances ---\n")
window_a = QtCore.QObject()
expect(find_probe_marker(window_a) is None, "find_probe_marker.absent_on_fresh_window")
expect(find_probe_marker(None) is None, "find_probe_marker.none_window_is_none_not_exception")

install_probe_marker(window_a, 1234)
found_name = find_probe_marker(window_a)
expect(found_name == u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_1234", "find_probe_marker.finds_marker_just_installed_with_correct_pid_encoding")

window_b = QtCore.QObject()
expect(find_probe_marker(window_b) is None, "find_probe_marker.marker_on_one_window_not_visible_on_another -- simulates a real SFM restart")

sys.stdout.write("\n--- extract_pid_from_marker_name() ---\n")
expect(extract_pid_from_marker_name(u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_9999") == 9999, "extract_pid.parses_correct_pid")
expect(extract_pid_from_marker_name(None) is None, "extract_pid.none_input_is_none")
expect(extract_pid_from_marker_name(u"SOME_OTHER_MARKER") is None, "extract_pid.wrong_prefix_is_none")
expect(extract_pid_from_marker_name(u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_notanumber") is None, "extract_pid.non_numeric_tail_is_none_not_exception")

sys.stdout.write("\n--- classify_probe_invocation() ---\n")
mode, reason = classify_probe_invocation(None, None)
expect(mode == "A_INSTALL", "classify.no_state_no_marker_is_A_install")

mode, reason = classify_probe_invocation(None, u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_1")
expect(mode is None, "classify.no_state_but_marker_found_is_inconsistent_STOP")

mode, reason = classify_probe_invocation({"installed": True, "install_pid": 1}, u"F2R1_MARKER_PROBE_INSTALLED_BY_PID_1")
expect(mode == "B_SAME_PROCESS_CHECK", "classify.state_and_marker_present_is_B")

mode, reason = classify_probe_invocation({"installed": True, "install_pid": 1}, None)
expect(mode == "C_POST_RESTART_CHECK", "classify.state_present_marker_absent_is_C")

sys.stdout.write("\n--- Static safety checks ---\n")
expect("Rebuild_Control_Groups_Normalizer" not in script_text, "script.never_references_production -- pure marker probe, no Normalizer")
expect("SaveToFile(" not in script_text, "script.never_saves")
expect("capture_tree" not in script_text and "discover_rig_context" not in script_text, "script.no_scene_traversal_of_any_kind")
expect("os.getpid()" in script_text, "script.captures_process_pid_for_forensic_comparison")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
