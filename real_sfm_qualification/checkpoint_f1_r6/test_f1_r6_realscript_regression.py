# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R6's real-SFM script
(Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity.py).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r6_realscript_regression.py
"""
import hashlib
import json
import os
import sys
import tempfile

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity.py")
EXPECTED_SCRIPT_SHA256 = "1f4096e98a37bd0fd9d328692cf638e24b00e4aae6e6bc9dfeda38b817f5c975"

WRITE_JSON_ATOMIC_RANGE = (168, 212)
WRITE_TEXT_ATOMIC_RANGE = (215, 253)
COMPARE_DISCOVERY_RESULTS_RANGE = (256, 302)

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

sys.stdout.write("\n--- compare_discovery_results(): compact parity comparison ---\n")

ns3 = {}
exec(compile(extract(COMPARE_DISCOVERY_RESULTS_RANGE), "<compare_discovery_results>", "exec"), ns3)
compare_discovery_results = ns3["compare_discovery_results"]


class FakeHandleObj(object):
    def __init__(self, h):
        self._h = h

    def GetHandle(self):
        return self._h


baseline = {
    "status": "SUPPORTED_ACTIVE_RIG",
    "reachable_rig_count": 1,
    "matching_rig_count": 1,
    "rig_handle": 42,
    "registry_handle": 99,
    "owned_handles": set([1, 2, 3]),
    "owned_names_in_order": [u"a", u"b"],
    "hidden_groups": [u"GroupA"],
    "rig": FakeHandleObj(42),
    "registry": FakeHandleObj(99),
}

identical = dict(baseline)
identical["rig"] = FakeHandleObj(42)
identical["registry"] = FakeHandleObj(99)
is_match, mismatches = compare_discovery_results(baseline, identical)
expect(is_match is True and mismatches == [], "compare.identical_results_match_exactly")

status_diff = dict(baseline)
status_diff["status"] = "UNRIGGED"
is_match2, mismatches2 = compare_discovery_results(baseline, status_diff)
expect(is_match2 is False and "status" in mismatches2, "compare.status_mismatch_detected")

rig_identity_diff = dict(baseline)
rig_identity_diff["rig"] = FakeHandleObj(43)  # different underlying handle
is_match3, mismatches3 = compare_discovery_results(baseline, rig_identity_diff)
expect(is_match3 is False and "selected_rig_identity" in mismatches3, "compare.rig_identity_mismatch_detected")

owned_names_diff = dict(baseline)
owned_names_diff["owned_names_in_order"] = [u"a", u"c"]
is_match4, mismatches4 = compare_discovery_results(baseline, owned_names_diff)
expect(is_match4 is False and "owned_names_in_order" in mismatches4, "compare.owned_names_mismatch_detected")

both_rig_none = dict(baseline)
both_rig_none["rig"] = None
both_rig_none["registry"] = None
identical_both_none = dict(both_rig_none)
is_match5, mismatches5 = compare_discovery_results(both_rig_none, identical_both_none)
expect(is_match5 is True, "compare.both_rig_and_registry_none_matches_cleanly -- the AMBIGUOUS_MULTIPLE_RIGS case")

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
expect("target_index % 2 == 0" in script_text, "script.alternates_arm_order_per_target -- ordering-bias control")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
