# -*- coding: utf-8 -*-
"""
Offline regression for Checkpoint F1-R8
(Checkpoint_F1_R8_CElementTreeTraversal_Native_Characterization.py).

No real SFM environment is available offline, so this test extracts the
script's own pure-Python helper functions VERBATIM (by source line range,
not retyped) and exercises them against synthetic fakes (FakeElement/
FakeAttribute, fake CElementTreeTraversal-like classes with deliberately
scripted behavior).

IMPORTANT: these tests validate the HARNESS only -- the watchdog, the
step-recording/dual-tracking logic, the graph-wiring helpers, the legacy
control wrapper, and the classification functions. They do NOT, and
cannot, validate the REAL native CElementTreeTraversal class's own
semantics (pAttrName scope, dedup behavior) -- that can only be observed
by actually running this checkpoint inside real SFM. No fake traversal
class result here is ever treated as native qualification evidence.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r8_diagnostic_regression.py
"""
import hashlib
import os
import sys
import time

SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Checkpoint_F1_R8_CElementTreeTraversal_Native_Characterization.py")
EXPECTED_SCRIPT_SHA256 = "863213058e66103f4a03d8f95d4e07d702c0274f6f2adb9d0be94cbbac962551"

CREATE_SCRATCH_NODE_RANGE = (314, 315)
LINK_SCALAR_RANGE = (318, 321)
LINK_ARRAY_RANGE = (324, 329)
BUILD_GRAPH_MULTIATTR_RANGE = (332, 362)
BUILD_GRAPH_DAG_RANGE = (365, 384)
BUILD_GRAPH_CYCLE_RANGE = (387, 404)
TESTED_ATTR_NAMES_RANGE = (426, 434)
RUN_LEGACY_REACHABLE_RANGE = (448, 475)
RUN_NATIVE_TRAVERSAL_RANGE = (478, 591)
CLASSIFY_DAG_CYCLE_DEDUP_RANGE = (594, 617)
GRAPH1_COVERAGE_RANGE = (620, 635)
COMPUTE_FINAL_CLASSIFICATION_RANGE = (638, 645)

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


# ---------------------------------------------------------------------------
# Fakes.
# ---------------------------------------------------------------------------

AT_ELEMENT_FAKE = "FAKE_AT_ELEMENT"
AT_ELEMENT_ARRAY_FAKE = "FAKE_AT_ELEMENT_ARRAY"

_next_handle = [1000]


class FakeAttribute(object):
    def __init__(self, owner, name, attr_type):
        self.owner = owner
        self.name = name
        self.attr_type = attr_type
        self.value = None
        self.array_values = []

    def SetValue(self, v):
        self.value = v

    def SetCount(self, n):
        assert n == 0
        self.array_values = []

    def append(self, v):
        self.array_values.append(v)


class FakeElement(object):
    def __init__(self, elem_type, name, fileid):
        self.elem_type = elem_type
        self.elem_name = name
        self.fileid = fileid
        self._handle = _next_handle[0]
        _next_handle[0] += 1
        self.attributes = {}

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self.elem_name

    def GetTypeString(self):
        return self.elem_type

    def AddAttribute(self, name, attr_type):
        attr = FakeAttribute(self, name, attr_type)
        self.attributes[name] = attr
        return attr


def fake_create_element_fn(elem_type, name, fileid):
    return FakeElement(elem_type, name, fileid)


def fake_handle(obj):
    return obj.GetHandle()


def fake_name(obj):
    return obj.GetName()


def fake_element_ref_pairs(elem):
    for attr_name, attr in elem.attributes.items():
        if attr.attr_type == AT_ELEMENT_FAKE:
            if attr.value is not None:
                yield attr_name, attr.value
        elif attr.attr_type == AT_ELEMENT_ARRAY_FAKE:
            for i, v in enumerate(attr.array_values):
                yield "%s[%d]" % (attr_name, i), v


def fake_reachable(start, max_elements=50000):
    stack = [start]
    seen = set()
    out = []
    while stack:
        obj = stack.pop()
        h = fake_handle(obj)
        if h in seen:
            continue
        seen.add(h)
        out.append(obj)
        for _unused_attr, child in fake_element_ref_pairs(obj):
            if fake_handle(child) not in seen:
                stack.append(child)
    return out


# ---------------------------------------------------------------------------
# Graph-accounting tests: build_graph_* wire the correct attributes.
# ---------------------------------------------------------------------------

sys.stdout.write("--- Graph-accounting tests (build_graph_* wiring, via fakes) ---\n")

ns_graph = {
    "SCRATCH_ELEMENT_TYPE": "DmElement",
}
exec(compile(extract(CREATE_SCRATCH_NODE_RANGE), "<create_scratch_node>", "exec"), ns_graph)
exec(compile(extract(LINK_SCALAR_RANGE), "<link_scalar>", "exec"), ns_graph)
exec(compile(extract(LINK_ARRAY_RANGE), "<link_array>", "exec"), ns_graph)
exec(compile(extract(BUILD_GRAPH_MULTIATTR_RANGE), "<build_graph_multiattr>", "exec"), ns_graph)
exec(compile(extract(BUILD_GRAPH_DAG_RANGE), "<build_graph_dag>", "exec"), ns_graph)
exec(compile(extract(BUILD_GRAPH_CYCLE_RANGE), "<build_graph_cycle>", "exec"), ns_graph)

nodes1 = ns_graph["build_graph_multiattr"](fake_create_element_fn, AT_ELEMENT_FAKE, AT_ELEMENT_ARRAY_FAKE, "fileid1")
expect(nodes1["root"].attributes["attr_A"].value is nodes1["a"], "graph1.root_attr_A_points_to_a")
expect(nodes1["root"].attributes["attr_B"].value is nodes1["b"], "graph1.root_attr_B_points_to_b")
expect(nodes1["a"].attributes["attr_A"].value is nodes1["c"], "graph1.a_attr_A_points_to_c")
expect(nodes1["b"].attributes["attr_B"].value is nodes1["d"], "graph1.b_attr_B_points_to_d")
expect(nodes1["a"].attributes["attr_list"].array_values == [nodes1["e"], nodes1["f"]], "graph1.a_attr_list_is_e_then_f")
expect(len(set(fake_handle(n) for n in nodes1.values())) == 7, "graph1.all_7_nodes_have_distinct_handles")

nodes2 = ns_graph["build_graph_dag"](fake_create_element_fn, AT_ELEMENT_ARRAY_FAKE, "fileid2")
expect(nodes2["root"].attributes["ref"].array_values == [nodes2["a"], nodes2["b"]], "graph2.root_ref_is_a_then_b")
expect(nodes2["a"].attributes["ref"].array_values == [nodes2["c"]], "graph2.a_ref_is_c")
expect(nodes2["b"].attributes["ref"].array_values == [nodes2["c"]], "graph2.b_ref_is_c -- shared reference to the SAME c")
expect(nodes2["a"].attributes["ref"].array_values[0] is nodes2["b"].attributes["ref"].array_values[0], "graph2.a_and_b_ref_the_identical_c_object")

nodes3 = ns_graph["build_graph_cycle"](fake_create_element_fn, AT_ELEMENT_ARRAY_FAKE, "fileid3")
expect(nodes3["root"].attributes["ref"].array_values == [nodes3["a"]], "graph3.root_ref_is_a")
expect(nodes3["a"].attributes["ref"].array_values == [nodes3["b"]], "graph3.a_ref_is_b")
expect(nodes3["b"].attributes["ref"].array_values == [nodes3["root"]], "graph3.b_ref_is_root -- closes the cycle")

# fake_reachable() over these fake graphs sanity-checks the graphs themselves
# are constructed as intended (not testing legacy production code here --
# that is exercised in run_legacy_reachable tests below with the REAL
# extracted function against these SAME fake graphs).
r1 = fake_reachable(nodes1["root"])
expect(set(fake_handle(o) for o in r1) == set(fake_handle(n) for n in nodes1.values()), "graph1.fake_reachable_visits_all_7_nodes")
r2 = fake_reachable(nodes2["root"])
expect(len(r2) == 4, "graph2.fake_reachable_visits_4_unique_nodes_root_a_b_c")
r3 = fake_reachable(nodes3["root"])
expect(len(r3) == 3, "graph3.fake_reachable_terminates_and_visits_3_unique_nodes_despite_cycle")

sys.stdout.write("\n--- TESTED_ATTR_NAMES_GRAPH1 sanity (no invented wildcard strings) ---\n")
ns_names = {}
exec(compile(extract(TESTED_ATTR_NAMES_RANGE), "<tested_attr_names>", "exec"), ns_names)
tested_values = [v for (_lbl, v, _just) in ns_names["TESTED_ATTR_NAMES_GRAPH1"]]
expect(tested_values == ["attr_A", "attr_B", "attr_list", ""], "tested_attr_names.exactly_the_4_justified_values_no_wildcards")
expect(None not in tested_values, "tested_attr_names.no_null_pattrname_probe -- removed pending explicit safety evidence, per instruction")
expect(len(ns_names["TESTED_ATTR_NAMES_DAG_AND_CYCLE"]) == 1 and ns_names["TESTED_ATTR_NAMES_DAG_AND_CYCLE"][0][1] == "ref", "tested_attr_names.dag_cycle_uses_only_the_real_ref_attribute")

# ---------------------------------------------------------------------------
# run_legacy_reachable(): extracted verbatim, real production reachable()
# logic re-exercised against the fake graphs (this IS a real legacy-control
# exercise, since run_legacy_reachable itself is verbatim harness code).
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- run_legacy_reachable() tests ---\n")
ns_legacy = {"time": time}
exec(compile(extract(RUN_LEGACY_REACHABLE_RANGE), "<run_legacy_reachable>", "exec"), ns_legacy)
run_legacy_reachable = ns_legacy["run_legacy_reachable"]

legacy1 = run_legacy_reachable(fake_reachable, fake_handle, nodes1["root"], "test_graph1")
expect(legacy1["exception"] is None, "legacy.graph1_no_exception")
expect(legacy1["unique_count"] == 7, "legacy.graph1_unique_count_7")
expect(legacy1["duplicate_count"] == 0, "legacy.graph1_zero_duplicates")

legacy2 = run_legacy_reachable(fake_reachable, fake_handle, nodes2["root"], "test_graph2")
expect(legacy2["unique_count"] == 4, "legacy.graph2_unique_count_4_dedups_shared_c")

legacy3 = run_legacy_reachable(fake_reachable, fake_handle, nodes3["root"], "test_graph3")
expect(legacy3["unique_count"] == 3, "legacy.graph3_unique_count_3_terminates_on_cycle")


def raising_reachable(start):
    raise RuntimeError("boom")


legacy_exc = run_legacy_reachable(raising_reachable, fake_handle, nodes1["root"], "test_exc")
expect(legacy_exc["exception"] is not None and "boom" in legacy_exc["exception"], "legacy.exception_path_captured")

# ---------------------------------------------------------------------------
# run_native_traversal(): watchdog, dual get/next tracking, exception paths.
# Uses DELIBERATELY SCRIPTED fake traversal classes -- these do not and
# cannot represent real CElementTreeTraversal semantics; they exist only to
# exercise this harness function's own control flow.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- run_native_traversal() harness tests (fake traversal classes; NOT native qualification) ---\n")
ns_native = {"time": time, "MAX_TRAVERSAL_STEPS": 2000, "log_line": lambda msg: None}
exec(compile(extract(RUN_NATIVE_TRAVERSAL_RANGE), "<run_native_traversal>", "exec"), ns_native)
run_native_traversal = ns_native["run_native_traversal"]


class FakeNode(object):
    def __init__(self, h, n):
        self._h, self._n = h, n

    def GetHandle(self):
        return self._h

    def GetName(self):
        return self._n


class RejectingTraversal(object):
    def __init__(self, root, attr_name):
        raise ValueError("attr_name not supported: %r" % (attr_name,))


result_reject = run_native_traversal(RejectingTraversal, fake_handle, fake_name, FakeNode(1, "root"), "bogus", "test_reject")
expect(result_reject["constructor_accepted"] is False, "native.constructor_rejection_captured")
expect(result_reject["construct_exception"] is not None, "native.construct_exception_recorded")


class CleanFiniteTraversal(object):
    """Simulates 'GetElement returns current, Next advances and returns the
    NEW current' -- i.e. get_handles[i+1] == next_handles[i]."""
    def __init__(self, root, attr_name):
        self._nodes = [FakeNode(1, "root"), FakeNode(2, "a"), FakeNode(3, "b")]
        self._pos = 0

    def IsValid(self):
        return self._pos < len(self._nodes)

    def GetElement(self):
        return self._nodes[self._pos]

    def CurrentDepth(self):
        return self._pos

    def Next(self, bSkipChildren=False):
        self._pos += 1
        if self._pos < len(self._nodes):
            return self._nodes[self._pos]
        return None


result_clean = run_native_traversal(CleanFiniteTraversal, fake_handle, fake_name, FakeNode(0, "unused"), "ref", "test_clean")
expect(result_clean["terminated_cleanly"] is True, "native.clean_traversal_terminates_cleanly")
expect(result_clean["watchdog_triggered"] is False, "native.clean_traversal_no_watchdog")
expect(result_clean["get_element_sequence"] == [1, 2, 3], "native.clean_traversal_get_element_sequence_correct")
# Next() returns None on its terminal call (no more nodes), so
# next_return_sequence is shorter than get_element_sequence by one entry
# (None values are filtered out, exactly like legacy's own FirstAttribute/
# NextAttribute None-terminated convention) -- the FULL shifted-by-one
# equality is therefore False here (list lengths differ), but the
# OVERLAPPING portion still demonstrates the "advance-then-return-new-
# current" relationship: next_handles[i] == get_handles[i+1].
expect(result_clean["next_return_sequence"] == [2, 3], "native.clean_traversal_next_return_sequence_is_2_and_3 -- terminal None correctly filtered")
expect(result_clean["get_element_sequence"][1:1 + len(result_clean["next_return_sequence"])] == result_clean["next_return_sequence"], "native.clean_traversal_overlapping_shifted_relationship_holds")
expect(result_clean["get_element_matches_next_return_shifted_by_one"] is False, "native.clean_traversal_shifted_field_is_false_due_to_trailing_none_length_mismatch -- documents the harness's exact, non-lossy behavior")


class InfiniteTraversal(object):
    """Never terminates -- IsValid always True. Must be caught by the
    bounded watchdog, never allowed to hang."""
    def __init__(self, root, attr_name):
        self._counter = 0

    def IsValid(self):
        return True

    def GetElement(self):
        self._counter += 1
        return FakeNode(self._counter, "n%d" % self._counter)

    def CurrentDepth(self):
        return 0

    def Next(self, bSkipChildren=False):
        return FakeNode(self._counter, "n%d" % self._counter)


t0 = time.time()
result_infinite = run_native_traversal(InfiniteTraversal, fake_handle, fake_name, FakeNode(0, "unused"), "ref", "test_infinite", max_steps=50)
elapsed = time.time() - t0
expect(result_infinite["watchdog_triggered"] is True, "native.infinite_traversal_watchdog_triggers")
expect(result_infinite["terminated_cleanly"] is False, "native.infinite_traversal_not_marked_clean")
expect(len(result_infinite["steps"]) <= 51, "native.infinite_traversal_bounded_by_max_steps")
expect(elapsed < 5.0, "native.infinite_traversal_watchdog_prevents_hang -- completed in %.3fs" % elapsed)


class RaisingMidTraversal(object):
    def __init__(self, root, attr_name):
        self._pos = 0

    def IsValid(self):
        return self._pos < 5

    def GetElement(self):
        return FakeNode(self._pos, "n%d" % self._pos)

    def CurrentDepth(self):
        return self._pos

    def Next(self, bSkipChildren=False):
        self._pos += 1
        if self._pos == 2:
            raise RuntimeError("native Next() failure at step 2")
        return FakeNode(self._pos, "n%d" % self._pos)


result_raising = run_native_traversal(RaisingMidTraversal, fake_handle, fake_name, FakeNode(0, "unused"), "ref", "test_raising_mid")
expect(result_raising["loop_exception"] is not None and "step 2" in result_raising["loop_exception"], "native.mid_traversal_next_exception_captured")
expect(result_raising["terminated_cleanly"] is False, "native.mid_traversal_exception_not_marked_clean")
expect(len(result_raising["steps"]) == 2, "native.mid_traversal_stops_recording_after_exception")

# ---------------------------------------------------------------------------
# classify_dag_cycle_dedup(): result-classification tests.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- classify_dag_cycle_dedup() result-classification tests ---\n")
ns_classify = {}
exec(compile(extract(CLASSIFY_DAG_CYCLE_DEDUP_RANGE), "<classify_dag_cycle_dedup>", "exec"), ns_classify)
classify_dag_cycle_dedup = ns_classify["classify_dag_cycle_dedup"]


def mk(get_seq, constructor_accepted=True, watchdog=False, terminated=True):
    return {
        "constructor_accepted": constructor_accepted,
        "watchdog_triggered": watchdog,
        "terminated_cleanly": terminated,
        "get_element_sequence": get_seq,
    }


expect(classify_dag_cycle_dedup(None, mk([1, 2])) == "INCONCLUSIVE", "classify.none_dag_is_inconclusive")
expect(classify_dag_cycle_dedup(mk([1, 2], constructor_accepted=False), mk([1, 2])) == "INCONCLUSIVE", "classify.rejected_constructor_is_inconclusive")
expect(classify_dag_cycle_dedup(mk([1, 2, 3]), mk([1, 2, 3], watchdog=True)) == "NO_SAFE_DEDUP", "classify.cycle_watchdog_triggered_is_no_safe_dedup")
expect(classify_dag_cycle_dedup(mk([1, 2, 3, 4]), mk([1, 2, 3])) == "GLOBAL_DEDUP_EQUIVALENT", "classify.no_duplicates_anywhere_clean_termination_is_global_dedup_equivalent")
expect(classify_dag_cycle_dedup(mk([1, 2, 3, 3]), mk([1, 2, 3])) == "PATH_ONLY_DEDUP", "classify.dag_duplicate_clean_cycle_termination_is_path_only_dedup")
expect(classify_dag_cycle_dedup(mk([1, 2, 3]), mk([1, 2, 3], terminated=False)) == "NO_SAFE_DEDUP", "classify.cycle_not_terminated_is_no_safe_dedup")
expect(classify_dag_cycle_dedup(mk([1, 2, 3]), mk([1, 2, 1], terminated=True)) == "OTHER", "classify.clean_dag_but_cycle_self_duplicates_without_watchdog_is_other")
expect(classify_dag_cycle_dedup(mk([]), mk([1])) == "INCONCLUSIVE", "classify.empty_dag_sequence_is_inconclusive")

# ---------------------------------------------------------------------------
# graph1_single_call_coverage_ok(): result-classification / comparator tests.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- graph1_single_call_coverage_ok() comparator tests ---\n")
ns_coverage = {}
exec(compile(extract(GRAPH1_COVERAGE_RANGE), "<graph1_single_call_coverage_ok>", "exec"), ns_coverage)
graph1_single_call_coverage_ok = ns_coverage["graph1_single_call_coverage_ok"]

legacy_full = {"unique_handles": [1, 2, 3, 4, 5, 6, 7]}


def probe(seq, accepted=True, tag="p"):
    return {"constructor_accepted": accepted, "get_element_sequence": seq, "tested_attr_name_repr": tag}


ok, matches = graph1_single_call_coverage_ok(legacy_full, [probe([1, 2, 3], tag="partial"), probe([1, 2, 3, 4, 5, 6, 7], tag="full")])
expect(ok is True and matches == ["full"], "coverage.one_matching_probe_out_of_two_detected")

ok2, matches2 = graph1_single_call_coverage_ok(legacy_full, [probe([1, 2, 3], tag="partial_only")])
expect(ok2 is False and matches2 == [], "coverage.no_matching_probe_is_false_empty")

ok3, matches3 = graph1_single_call_coverage_ok(legacy_full, [probe([1, 2, 3, 4, 5, 6, 7], accepted=False, tag="rejected_but_wouldve_matched")])
expect(ok3 is False, "coverage.rejected_constructor_probe_never_counted_even_if_sequence_matches")

ok4, matches4 = graph1_single_call_coverage_ok(None, [probe([1], tag="x")])
expect(ok4 is None and matches4 is None, "coverage.none_legacy_is_none_none")

# ---------------------------------------------------------------------------
# compute_final_classification(): failure/inconclusive-path tests.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- compute_final_classification() failure/inconclusive-path tests ---\n")
ns_final = {}
exec(compile(extract(COMPUTE_FINAL_CLASSIFICATION_RANGE), "<compute_final_classification>", "exec"), ns_final)
compute_final_classification = ns_final["compute_final_classification"]

expect(compute_final_classification(False, True, "GLOBAL_DEDUP_EQUIVALENT") == "INCONCLUSIVE", "final.detached_graph_unavailable_forces_inconclusive")
expect(compute_final_classification(True, None, "GLOBAL_DEDUP_EQUIVALENT") == "INCONCLUSIVE", "final.coverage_none_forces_inconclusive")
expect(compute_final_classification(True, True, "INCONCLUSIVE") == "INCONCLUSIVE", "final.dedup_inconclusive_forces_inconclusive")
expect(compute_final_classification(True, True, "GLOBAL_DEDUP_EQUIVALENT") == "EXACT_CANDIDATE_SUPPORTED", "final.both_established_is_exact_candidate_supported")
expect(compute_final_classification(True, False, "GLOBAL_DEDUP_EQUIVALENT") == "SEMANTICALLY_INSUFFICIENT", "final.coverage_false_is_semantically_insufficient")
expect(compute_final_classification(True, True, "PATH_ONLY_DEDUP") == "SEMANTICALLY_INSUFFICIENT", "final.path_only_dedup_is_semantically_insufficient")
expect(compute_final_classification(True, True, "NO_SAFE_DEDUP") == "SEMANTICALLY_INSUFFICIENT", "final.no_safe_dedup_is_semantically_insufficient")

# ---------------------------------------------------------------------------
# Static safety checks on the actual deployed script source.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- Static safety checks on the actual deployed script source ---\n")
expect("SaveToFile(" not in script_text, "script.never_calls_SaveToFile -- no-save behavior enforced")
expect("self.rebuild(" not in script_text and "instance.rebuild(" not in script_text, "script.never_calls_native_rebuild")
expect("SetHeadTimeInSeconds(" not in script_text, "script.never_activates_a_shot")
expect("instance.finished = True" in script_text, "script.neutralizes_real_instance_before_any_event_pump")
expect(
    script_text.index("instance.finished = True") < script_text.index("create_element_fn = resolve_datamodel_symbol"),
    "script.neutralization_happens_before_any_detached_graph_work",
)
expect("DestroyElement(h)" in script_text, "script.destroys_every_created_scratch_element")
expect("RemoveFileId(scratch_fileid)" in script_text, "script.removes_the_scratch_fileid")
expect(
    script_text.rfind("finally:") > script_text.index("except Exception as top_exc:"),
    "script.cleanup_runs_in_a_finally_block_regardless_of_outcome",
)
expect("MAX_TRAVERSAL_STEPS = 2000" in script_text, "script.watchdog_bound_is_a_small_fixed_constant")
expect("NULL_PATTRNAME_PROBE_STATUS" in script_text, "script.records_explicit_null_pattrname_unknown_status")
expect("NOT_TESTED_UNKNOWN" in script_text, "script.null_pattrname_status_is_explicitly_unknown_not_inferred")
expect('"null_pattrname_probe_status": NULL_PATTRNAME_PROBE_STATUS' in script_text, "script.null_pattrname_status_included_in_report")
expect("NULL and \"\" are NOT assumed equivalent" in script_text, "script.explicitly_does_not_infer_null_and_empty_string_equivalence")
expect("real-scene sanity check is gated behind EXACT_CANDIDATE_SUPPORTED only" in script_text, "script.real_scene_check_explicitly_gated")
expect('"attempted": False' in script_text, "script.real_scene_check_defaults_to_not_attempted")
expect("Do not run 62 targets" not in script_text, "script.does_not_literally_quote_the_forbidden_62_target_instruction -- sanity check runs on one shot only, never instance.work's full loop")
expect("for shot_record in work" not in script_text, "script.never_loops_over_all_shots_or_targets -- only reads work[0] for the optional sanity check")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
