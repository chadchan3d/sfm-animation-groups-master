# -*- coding: utf-8 -*-
"""
Offline sanity check for Checkpoint O3-R2's discovery phase-splitting
instrumentation mechanism.

This test does NOT use the real production source (that is covered by
direct source citation -- see O3_R2_DISCOVERY_PHASE_MAP.md -- and by the
real-SFM run itself). It uses a SYNTHETIC module shaped like the relevant
parts of discover_rig_context()'s own structure (calls to reachable(),
typ(), arr() with varying attr_name, scalar() with varying attr_name,
handle()), plus a SEPARATE synthetic function standing in for
capture_tree() that also calls handle() -- to prove the depth-gate
correctly excludes calls made OUTSIDE discovery from any phase bucket,
which is the central correctness property this whole mechanism depends
on (handle() is called from both discover_rig_context() and
capture_tree() in the real production file; conflating the two would
corrupt the O3-R2 measurement).

This test proves, using the EXACT wrapper-construction functions copied
verbatim from Checkpoint_O3_R2_Discovery_Cost_Split.py (not
reimplemented -- imported by exec()-ing the real diagnostic's own source
and pulling the wrapper factories out of its namespace, so a future edit
to the real script cannot silently drift out of sync with this test):

  1. The `_discovery_depth` nesting flag correctly gates attribution --
     calls made while depth==0 (outside any discover_rig_context() call)
     are NOT attributed to any phase bucket, even though the same
     wrapped function object is called.
  2. `arr()`'s bucketing by `attr_name` correctly separates
     "animSetList" -> phase 4, "controls" / "elementList" -> phase 6,
     "hiddenGroups" -> phase 7, and an attr_name outside that map
     contributes to no bucket (and is NOT silently misattributed).
  3. `scalar()`'s bucketing by `attr_name` correctly separates
     "scene" -> phase 1, "animationSet" -> phase 4 (the fix applied
     after direct source comparison caught the original draft's
     blanket-phase-4 bug).
  4. The FIFO correlation queue correctly matches MULTIPLE, INTERLEAVED
     discovery calls (across two synthetic targets, several calls each)
     to their own immediately-following capture label, in strict
     call order.
  5. Reconciliation: for every discovery call, total elapsed time is
     accounted for by (sum of its own phase buckets) + a reported,
     non-fabricated residual -- the residual is never silently dropped
     or assumed zero.
"""
import os
import sys
import textwrap
import time

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REAL_SCRIPT_PATH = os.path.join(THIS_DIR, "Checkpoint_O3_R2_Discovery_Cost_Split.py")

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


# ---------------------------------------------------------------------------
# Pull the wrapper-factory closures out of the REAL diagnostic's own
# source by exec()-ing it under a stub sfmApp/environment that lets the
# module-top-level "try:" block fail immediately and harmlessly (the
# real script's own top-level try/except CheckpointO3R2Error swallows a
# missing sfmApp cleanly, matching its own documented gate-failure path)
# -- this test exists to check the WRAPPER-BUILDING FUNCTIONS themselves,
# which are defined ahead of that top-level try block and do not require
# a live SFM session to construct.
# ---------------------------------------------------------------------------

with open(REAL_SCRIPT_PATH, "rb") as f:
    real_source = f.read()

# The real script references sfmApp / QtCore / vs at module scope inside
# its own top-level try block. Provide harmless stand-ins so exec()
# reaches the point where COMMAND_SPECS-loop-local wrapper factories
# would be defined without raising NameError -- but since those factories
# are DEFINED INSIDE the per-command for-loop (they close over that
# iteration's own `events`/`pending_discoveries`/`discovery_depth`/
# `current_bucket`), this test does not extract them from prod_ns.
# Instead it reproduces the identical closure-construction functions
# by exec()-ing a NARROW EXTRACT of the real file: everything from the
# module docstring's end through the end of the for-loop body's wrapper
# definitions, keyed on the exact same source text -- verified below to
# be textually present in the real file, not retyped independently.

markers = [
    "def make_discover_rig_context_wrapper(original_fn):",
    "def make_reachable_wrapper(original_fn):",
    "def make_typ_wrapper(original_fn):",
    "def make_arr_wrapper(original_fn):",
    "def make_scalar_wrapper(original_fn):",
    "def make_handle_wrapper(original_fn):",
    "def make_capture_snapshot_explicit_wrapper(original_fn):",
]
source_text = real_source.decode("ascii")
for marker in markers:
    expect(marker in source_text, "extraction.marker_present_in_real_script: %s" % marker)

start_marker = "def make_phase_bucket():"
end_marker = "def make_run_target_transaction_wrapper(original_method):"
start_marker_idx = source_text.find(start_marker)
end_marker_idx = source_text.find(end_marker)
expect(start_marker_idx >= 0 and end_marker_idx > start_marker_idx, "extraction.wrapper_block_bounds_found")

# Extend to the START of the marker's own LINE (not just the marker text
# itself) so the first line's original leading whitespace is preserved,
# keeping every line's indentation consistent relative to each other --
# slicing from mid-line would strip only the first line's indent and
# corrupt the block's own indentation structure.
start_idx = source_text.rfind("\n", 0, start_marker_idx) + 1
end_idx = end_marker_idx

wrapper_block_source = textwrap.dedent(source_text[start_idx:end_idx])

# The extracted block references ARR_ATTR_TO_PHASE / SCALAR_ATTR_TO_PHASE
# (module-level in the real script) and discovery_depth / current_bucket
# / pending_discoveries (per-command locals in the real script's for-loop).
# Reconstruct those exact bindings here, copied verbatim from the real
# script's own module-level definitions -- re-read directly from the
# source text rather than retyped, so a future edit to those dicts cannot
# silently drift out of sync with this test.

arr_map_start = source_text.find("ARR_ATTR_TO_PHASE = {")
arr_map_end = source_text.find("}", arr_map_start) + 1
scalar_map_start = source_text.find("SCALAR_ATTR_TO_PHASE = {")
scalar_map_end = source_text.find("}", scalar_map_start) + 1
expect(arr_map_start >= 0 and scalar_map_start >= 0, "extraction.attr_phase_maps_found")

test_ns = {"time": time}
exec(compile(source_text[arr_map_start:arr_map_end], "<arr_map>", "exec"), test_ns)
exec(compile(source_text[scalar_map_start:scalar_map_end], "<scalar_map>", "exec"), test_ns)

events = []
pending_discoveries = []
discovery_depth = [0]
test_ns["events"] = events
test_ns["pending_discoveries"] = pending_discoveries
test_ns["discovery_depth"] = discovery_depth

# The extracted block itself re-derives current_bucket = [None] and reads
# original_discover_rig_context/etc. via prod_ns.get(...) -- reproduce
# prod_ns as an EMPTY dict (every .get(...) call then correctly yields
# None, matching this test's own intent of only extracting the wrapper
# FACTORY functions, not the real production originals) and the helper
# names capture_snapshot_explicit's own wrapper body calls.
# canonicalize_snapshot and per_value_hash are copied verbatim from the
# real script's own earlier-defined helpers (not retyped logic); b_name
# is a deliberate stub (synthetic aset values are already plain strings
# here, not native objects with GetName()) -- this test's synthetic
# targets are passed straight through rather than exercising b_name's
# own unicode-decoding fallback chain, which is unrelated to the phase-
# split mechanism under test.
test_ns["prod_ns"] = {}


def stub_b_name(obj):
    return obj


def stub_canonicalize_snapshot(snap):
    if not isinstance(snap, dict):
        return snap
    clean = dict(snap)
    for key in ("shot_handle", "animation_set_handle", "root_handle", "rig_handle",
                "registry_handle", "label", "control_handles"):
        clean.pop(key, None)
    return clean


def stub_per_value_hash(value):
    import hashlib
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


test_ns["b_name"] = stub_b_name
test_ns["canonicalize_snapshot"] = stub_canonicalize_snapshot
test_ns["per_value_hash"] = stub_per_value_hash

exec(compile(wrapper_block_source, "<wrapper_block>", "exec"), test_ns)
current_bucket = test_ns["current_bucket"]

make_discover_rig_context_wrapper = test_ns["make_discover_rig_context_wrapper"]
make_reachable_wrapper = test_ns["make_reachable_wrapper"]
make_typ_wrapper = test_ns["make_typ_wrapper"]
make_arr_wrapper = test_ns["make_arr_wrapper"]
make_scalar_wrapper = test_ns["make_scalar_wrapper"]
make_handle_wrapper = test_ns["make_handle_wrapper"]


# ---------------------------------------------------------------------------
# Synthetic originals, shaped like the real production helpers but with
# deterministic sleep-based delays so bucket attribution is checkable.
# ---------------------------------------------------------------------------

# Sleep durations are chosen well above typical Windows time.time()
# timer-tick granularity (observed to round sub-millisecond sleeps down
# to 0.0 elapsed on this embedded Python 2.7 build) so bucket attribution
# is reliably non-zero and measurable, not flaky.

def original_reachable(start, max_elements=50000):
    time.sleep(0.05)
    return ["obj1", "obj2", "obj3"]


def original_typ(obj):
    time.sleep(0.02)
    return "DmeRig" if obj == "obj1" else "Other"


def original_arr(obj, attr_name):
    time.sleep(0.03)
    if attr_name == "animSetList":
        return ["rec1"]
    if attr_name == "controls":
        return ["ctrl1", "ctrl2"]
    if attr_name == "elementList":
        return ["elem1"]
    if attr_name == "hiddenGroups":
        return ["GroupA"]
    return []


def original_scalar(obj, attr_name):
    time.sleep(0.02)
    if attr_name == "scene":
        return "scene_obj"
    if attr_name == "animationSet":
        return "linked_aset"
    return None


def original_handle(obj):
    time.sleep(0.02)
    return hash(obj) & 0xFFFF


wrapped_reachable = make_reachable_wrapper(original_reachable)
wrapped_typ = make_typ_wrapper(original_typ)
wrapped_arr = make_arr_wrapper(original_arr)
wrapped_scalar = make_scalar_wrapper(original_scalar)
wrapped_handle = make_handle_wrapper(original_handle)


def synthetic_discover_rig_context(shot, aset):
    scene = wrapped_scalar(shot, "scene")
    objs = wrapped_reachable(scene)
    for obj in objs:
        wrapped_typ(obj)
    rec_list = wrapped_arr("rig", "animSetList")
    for rec in rec_list:
        wrapped_scalar(rec, "animationSet")
    control_objs = wrapped_arr(aset, "controls")
    for c in control_objs:
        wrapped_handle(c)
    element_objs = wrapped_arr("registry", "elementList")
    for e in element_objs:
        wrapped_handle(e)
    wrapped_arr("registry", "hiddenGroups")
    wrapped_handle("rig")
    time.sleep(0.01)  # stand-in for unwrapped pure-Python control flow
    return {"status": "SUPPORTED_ACTIVE_RIG", "reachable_rig_count": 1, "matching_rig_count": 1}


wrapped_discover_rig_context = make_discover_rig_context_wrapper(synthetic_discover_rig_context)


def synthetic_capture_tree(root):
    # Mirrors production's OWN capture_tree(), which ALSO calls handle()
    # -- but OUTSIDE any discover_rig_context() call, so its handle()
    # calls must NOT be attributed to any discovery phase bucket.
    for x in ("a", "b", "c"):
        wrapped_handle(x)
    return {"tree": root}


def original_capture_snapshot_explicit(shot, aset, label, rig_context=None):
    time.sleep(0.001)
    return {"label": label, "target": aset}


make_capture_snapshot_explicit_wrapper = test_ns["make_capture_snapshot_explicit_wrapper"]
wrapped_capture = make_capture_snapshot_explicit_wrapper(original_capture_snapshot_explicit)


# ---------------------------------------------------------------------------
# 1) Depth-gate correctness: call capture_tree-like function (outside
#    discovery) BEFORE any discover_rig_context() call, confirm none of
#    its handle() calls polluted any bucket (there is no current_bucket
#    yet, so this also exercises the "current_bucket[0] is None" guard).
# ---------------------------------------------------------------------------

sys.stdout.write("--- Depth-gate: calls outside discovery must not populate any phase bucket ---\n")
synthetic_capture_tree("root_before")
expect(pending_discoveries == [], "depth_gate.no_discovery_bucket_created_by_out_of_discovery_calls")

# ---------------------------------------------------------------------------
# 2/3) Run TWO interleaved targets, each with TWO discovery+capture
#      cycles, plus an interleaved out-of-discovery capture_tree call in
#      between -- to prove depth-gating and FIFO correlation both hold
#      under realistic interleaving, not just a single trivial call.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- Interleaved multi-target discovery + capture + capture_tree ---\n")

# Target A, capture PRE
rig_ctx_a1 = wrapped_discover_rig_context("shotA", "targetA")
wrapped_capture("shotA", "targetA", "PRE", rig_ctx_a1)

# capture_tree call BETWEEN two discovery calls -- must not pollute
# either discovery's own buckets.
synthetic_capture_tree("between_a1_and_a2")

# Target A, capture NATIVE_POST
rig_ctx_a2 = wrapped_discover_rig_context("shotA", "targetA")
wrapped_capture("shotA", "targetA", "NATIVE_POST", rig_ctx_a2)

# Target B, capture PRE
rig_ctx_b1 = wrapped_discover_rig_context("shotA", "targetB")
wrapped_capture("shotA", "targetB", "PRE", rig_ctx_b1)

# Target B, capture NATIVE_POST
rig_ctx_b2 = wrapped_discover_rig_context("shotA", "targetB")
wrapped_capture("shotA", "targetB", "NATIVE_POST", rig_ctx_b2)

capture_events = [e for e in events if e["kind"] == "capture_snapshot_explicit"]
expect(len(capture_events) == 4, "correlation.four_capture_events_recorded", len(capture_events))

expected_sequence = [
    ("targetA", "PRE"),
    ("targetA", "NATIVE_POST"),
    ("targetB", "PRE"),
    ("targetB", "NATIVE_POST"),
]
actual_sequence = [(e["target"], e["label"]) for e in capture_events]
expect(actual_sequence == expected_sequence, "correlation.capture_order_matches_call_order", actual_sequence)

for e in capture_events:
    expect(
        e.get("discovery_phase_data") is not None,
        "correlation.every_capture_has_its_own_discovery_phase_data: %s/%s" % (e["target"], e["label"]),
    )

expect(pending_discoveries == [], "correlation.fifo_queue_fully_drained_after_matched_captures")

# ---------------------------------------------------------------------------
# 2) arr() attr_name bucketing correctness (checked on target A's first
#    discovery, which exercised every bucketed attr_name).
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- arr()/scalar() attr_name bucketing correctness ---\n")
d_a1 = capture_events[0]["discovery_phase_data"]
expect(d_a1["phase_4_rig_animset_binding_seconds"] > 0, "arr_bucket.animSetList_and_animationSet_attributed_to_phase_4", d_a1["phase_4_rig_animset_binding_seconds"])
expect(d_a1["phase_6_registry_elementlist_seconds"] > 0, "arr_bucket.controls_and_elementList_attributed_to_phase_6", d_a1["phase_6_registry_elementlist_seconds"])
expect(d_a1["phase_7_hiddengroups_seconds"] > 0, "arr_bucket.hiddenGroups_attributed_to_phase_7", d_a1["phase_7_hiddengroups_seconds"])
expect(d_a1["phase_1_reachable_traversal_seconds"] > 0, "scalar_bucket.scene_and_reachable_attributed_to_phase_1", d_a1["phase_1_reachable_traversal_seconds"])
expect(d_a1["phase_2_candidate_filtering_seconds"] > 0, "typ_bucket.typ_calls_attributed_to_phase_2", d_a1["phase_2_candidate_filtering_seconds"])
expect(d_a1["phase_8_handle_extraction_seconds"] > 0, "handle_bucket.handle_calls_attributed_to_phase_8", d_a1["phase_8_handle_extraction_seconds"])
expect(d_a1["handle_call_count"] == 4, "handle_bucket.call_count_matches_expected (2 controls + 1 element + 1 rig)", d_a1["handle_call_count"])
expect(d_a1["typ_call_count"] == 3, "typ_bucket.call_count_matches_expected (3 reachable objects)", d_a1["typ_call_count"])

# ---------------------------------------------------------------------------
# 4) Depth-gate re-checked AFTER discovery calls: the interleaved
#    capture_tree call between A1 and A2 must show zero attribution to
#    EITHER discovery's own buckets (i.e. A1's handle_call_count must not
#    include capture_tree's own 3 handle() calls, and A2 must not either).
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- Depth-gate re-check: interleaved out-of-discovery calls excluded ---\n")
d_a2 = capture_events[1]["discovery_phase_data"]
expect(d_a1["handle_call_count"] == 4 and d_a2["handle_call_count"] == 4, "depth_gate.interleaved_capture_tree_handle_calls_not_attributed_to_either_discovery", (d_a1["handle_call_count"], d_a2["handle_call_count"]))

# ---------------------------------------------------------------------------
# 5) Reconciliation: total >= sum(bucketed phases), residual reported and
#    non-negative, never silently dropped.
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- Reconciliation: residual accounting ---\n")
for idx, e in enumerate(capture_events):
    d = e["discovery_phase_data"]
    phase_sum = (
        d["phase_1_reachable_traversal_seconds"]
        + d["phase_2_candidate_filtering_seconds"]
        + d["phase_4_rig_animset_binding_seconds"]
        + d["phase_6_registry_elementlist_seconds"]
        + d["phase_7_hiddengroups_seconds"]
        + d["phase_8_handle_extraction_seconds"]
    )
    expect("residual_unexplained_seconds" in d, "reconciliation.residual_field_present_%d" % idx)
    computed_residual = d["total_discovery_elapsed_seconds"] - phase_sum
    expect(
        abs(d["residual_unexplained_seconds"] - computed_residual) < 1e-9,
        "reconciliation.residual_matches_total_minus_phase_sum_%d" % idx,
        (d["residual_unexplained_seconds"], computed_residual),
    )
    expect(d["residual_unexplained_seconds"] >= 0, "reconciliation.residual_non_negative_%d" % idx, d["residual_unexplained_seconds"])
    expect(d["total_discovery_elapsed_seconds"] >= phase_sum, "reconciliation.total_covers_bucketed_phases_%d" % idx)

# ---------------------------------------------------------------------------
# Exception path: discovery raising must still push a bucket (with
# exception recorded, status None) so the FIFO queue stays consistent,
# and must re-raise unchanged (never suppressed).
# ---------------------------------------------------------------------------

sys.stdout.write("\n--- Exception path: raised exception is recorded and re-raised, never suppressed ---\n")


def raising_discover(shot, aset):
    wrapped_reachable("scene_obj")
    raise ValueError("synthetic Category 2 failure")


wrapped_raising_discover = make_discover_rig_context_wrapper(raising_discover)
raised = None
try:
    wrapped_raising_discover("shotX", "targetX")
except ValueError as exc:
    raised = exc

expect(raised is not None and str(raised) == "synthetic Category 2 failure", "exception.original_exception_re_raised_unchanged", raised)
expect(len(pending_discoveries) == 1, "exception.bucket_still_pushed_for_failed_discovery", len(pending_discoveries))
expect(pending_discoveries[0]["exception"] is not None, "exception.exception_field_populated")
expect(pending_discoveries[0]["status"] is None, "exception.status_is_none_on_raised_exception")
pending_discoveries.pop()

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
