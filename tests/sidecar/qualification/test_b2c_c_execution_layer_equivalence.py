# -*- coding: utf-8 -*-
"""B2C-C execution-layer continuation: NATIVE MUTATION STREAM + final
logical control-group tree equivalence.

=== Terminology (kept strictly separate throughout this file and the
report) ===
- "decision-plan stream" = the ALREADY-QUALIFIED (37/37 PASS) Level-2
  artifact from `test_b2c_c_plan_layer_equivalence.py`: `plan`'s
  `rig_rows`/`master_rows` and `uniformity_plan`'s `model_translations`/
  `rig_destinations`/`master_destinations`/`keep_native`. Regenerated
  here per fixture as a regression check (Section 7), never re-claimed
  as new evidence.
- "native mutation stream" = the ordered record of REAL native DME
  calls actually executed by `production_generic_composer` and its
  closure against the fake object model: `CreateControlGroup`,
  `AddChild`, `RemoveChild`, `AddControl`, `SetName`, `SetVisible`,
  `SetSelectable`, `SetSnappable`, `SetGroupColor`. THIS is what this
  file adds that did not exist before.

=== Authority-dependency cut (governing prompt addendum) ===
Every function `production_generic_composer` transitively calls was
classified by direct source reading (never inferred) into:

  AUTHORITY-SENSITIVE (reads `master` directly or indirectly, or its
  effect can differ because of it) -- these are the ONLY functions this
  harness needs to exercise with real fake-DME execution + real
  mutation-stream/final-tree comparison:
    production_master_metadata_path, production_apply_explicit_master_
    metadata, production_apply_active_group_policy, production_ensure_
    group_path, production_reorder_children_by_master, production_
    reorder_contextual_tree, production_apply_exact_master_destination_
    total_order, production_generic_composer (orchestrator; also directly
    calls `add_control_to_group`, whose CONTENT/ORDER depends on the
    authority-sensitive functions above), and the eligibility-gate
    island `_gate_is_alh` (target/scope discovery -- see below).

  AUTHORITY-INDEPENDENT, PROVEN BY SOURCE-IDENTITY + ALREADY-IDENTICAL-
  INPUT (never separately re-verified by fake-DME execution here,
  because doing so cannot expose a NEW difference beyond what the
  already-qualified decision layer or a trivial grep already proves):
    - `discover_rig_context`/`capture_snapshot_explicit`/`live_control_
      map`/`capture_tree`: grep-confirmed ZERO references to `master`
      anywhere in their extracted source (see `production_plan_layer.py`
      and this module's own extraction ranges) -- same code, same
      shot/aset/root inputs (this harness builds two INDEPENDENT but
      IDENTICALLY-CONSTRUCTED fake worlds for baseline/migrated, so
      these functions' inputs are identical by construction, not by
      luck), therefore their outputs are identical by the basic
      substitution property of pure functions -- no execution-level
      re-verification can add evidence beyond this.
    - `production_claim_destination`: pure, no `master` reference; its
      only inputs (`target_path`, `control_name`, `authority` string)
      come from `uniformity_plan`/`plan`, ALREADY PROVEN byte-identical
      baseline vs migrated (37/37, prior phase) -- same code + already-
      proven-identical inputs = identical output.
    - `production_source_paths_for_target`/`production_source_meta_for_
      target`/`production_raw_selectable`: grep-confirmed no `master`
      reference.
    - The single native-rebuild commit call site (`self.rebuild(ctypes.
      c_void_p(aset_ptr))`, line 11129) is NEVER reached by this harness
      (and never was) -- confirmed by direct reading that `master =
      self.master_index` is read only at line 11271, AFTER the rebuild
      call, and `self.master_index` itself is parsed ONCE in `start()`
      (line 13194) before any target's rebuild call -- i.e. the real
      production control flow makes it TEMPORALLY IMPOSSIBLE for the
      authority migration to influence the native rebuild call's inputs
      or timing. This harness does not emulate ifm.dll at all; instead,
      per the governing prompt's explicit instruction, the SAME captured
      post-native-rebuild snapshot (`post`, from ONE fake-world
      construction per scenario) is used as the shared, controlled
      input fed to BOTH the baseline and migrated reconciliation paths.
    - The bulk of eligibility/scope discovery (`snapshot_work`'s MDL-
      header parsing, bone counting, follower detection, model-backed
      checks) is grep-confirmed to contain ZERO `master` references
      anywhere except the ONE `_gate_is_alh` call site -- see below.
      Real scene/shot/project-level enumeration (`self.scope_shots`,
      `shot.animationSets`, on-disk MDL file reads) requires live SFM/
      filesystem host semantics this project has never modeled offline
      anywhere -- deferred explicitly to a future live-runtime gate,
      NOT fabricated here with a speculative fake project/scene
      universe (per the governing prompt's explicit instruction).

Never launches SFM. Read-only with respect to the frozen production
file and the qualified Correction6 candidate (only ever read, hashed,
and executed via source-slicing extraction -- never modified).
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_DIR = os.path.join(_THIS_DIR, "candidate_b2c_c")
if CANDIDATE_DIR not in sys.path:
    sys.path.insert(0, CANDIDATE_DIR)

import production_execution_layer as pel  # noqa: E402
import fake_dme  # noqa: E402
import authority_pair as ap  # noqa: E402
import canon  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

RESULTS = []
LEDGER = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

try:
    unicode  # noqa: F821
except NameError:
    print("FATAL: this harness requires Python 2.")
    sys.exit(1)


class FakeCommand(object):
    def __init__(self):
        self.class_totals = {
            "pre_hidden_master_active": 0, "rig_losses": 0, "master_stranded": 0,
            "parent_collapses": 0, "master_normalizations": 0, "master_unknown_unknown": 0,
            "weak_unknown_diagnostics": 0, "ambiguous_losses": 0, "unresolved_owned_drift": 0,
        }
        self.production_mixed_direct_by_target = {}
        self.log_calls = []

    def log(self, msg):
        self.log_calls.append(msg)


ns, extraction_blocks = pel.build_full_namespace()
ns["vs"] = fake_dme.FakeVsModule()
print("[extraction] %d source blocks bound (%d total names)" % (len(extraction_blocks), len(ns)))

master_path, artifact_path, master_sha256 = ap.load_authority_fixture()


def run_execution(spec, master):
    """One complete, FRESH fake world (never shared/reused across the
    baseline/migrated comparison -- avoids one side's mutations
    contaminating the other's starting state).

    Applies the SAME upstream gate the real frozen `run_target_
    transaction` applies BEFORE it ever reaches `preflight_
    reconciliation_plan`/`production_generic_composer` (verified by
    direct reading, lines ~11171-11190): `if pre["rig_status"] !=
    "SUPPORTED_ACTIVE_RIG": raise NativePostFallback(...)`. A bug in an
    earlier version of this harness OMITTED this gate and called
    `production_generic_composer` unconditionally for every fixture --
    for the fixtures whose `pre` never actually has genuine rig
    ownership (a fixture-authoring mistake, not a real-production
    scenario), this produced a MASKED mutual failure: BOTH baseline and
    migrated raised the identical `ProbeError` (composer's own
    `active_rig_status_changed` postcondition, which unconditionally
    requires the FINAL state to already be `SUPPORTED_ACTIVE_RIG` --
    composer is simply never reached with anything else in real
    production), and the comparison technically "matched" (same
    exception on both sides) without ever actually exercising composer.
    Found and fixed during this qualification round -- see the report's
    "bugs found and fixed" section. Six fixtures were affected (A3, B1,
    B4, C1, D3, D5); C1's `rig_status="UNRIGGED"` is CORRECT and
    intentional (it is meant to hit this exact real gate) and is now
    verified as a genuine, disclosed `native_post_fallback` outcome
    rather than an accidental composer-level ProbeError; A3/B1/B4/D3/D5
    were fixture-authoring bugs (declared `rig_status="SUPPORTED_ACTIVE_
    RIG"` but had zero actually-owned controls) and were fixed by adding
    a genuinely rig-owned, unrelated control to each (see scenarios.py)."""
    shot, aset, root, mlog, handles, groups_by_path, controls_by_name = fake_dme.build_world(
        spec["post_groups_spec"], spec["post_control_specs"],
        rig_status=spec["rig_status"], hidden_groups=spec["hidden_groups"])

    rig_context = ns["discover_rig_context"](shot, aset)
    post = ns["capture_snapshot_explicit"](shot, aset, "POST", rig_context)
    pre = spec["pre"]

    if pre["rig_status"] != "SUPPORTED_ACTIVE_RIG":
        final_tree = post  # native POST is preserved verbatim -- no composer call at all
        return {
            "initial_post": post,
            "decision_plan": None,
            "outcome": "native_post_fallback:%s" % pre["rig_status"],
            "composer_result": None,
            "native_mutation_stream": [],
            "final_tree": final_tree,
        }

    cmd = FakeCommand()
    plan = ns["preflight_reconciliation_plan_pure"](cmd, pre, post, master, (u"shot1", u"aset1"))
    uniformity_plan = ns["derive_generic_uniformity_plan"](pre, post, master, plan)

    composer_result = None
    outcome = "composed"
    try:
        composer_result = ns["production_generic_composer"](root, pre, post, master, shot, aset, plan, uniformity_plan)
    except Exception as exc:
        outcome = "raised:%s:%s" % (type(exc).__name__, str(exc)[:300])

    final_rig_context = ns["discover_rig_context"](shot, aset)
    final_tree = ns["capture_snapshot_explicit"](shot, aset, "FINAL", final_rig_context)

    return {
        "initial_post": post,
        "decision_plan": {"plan": plan, "uniformity_plan": uniformity_plan},
        "outcome": outcome,
        "composer_result": composer_result,
        "native_mutation_stream": list(mlog.entries),
        "final_tree": final_tree,
    }


def compare_scenario(scenario_name, spec):
    baseline_master = ap.compute_baseline_master(spec["wanted_folds"], master_path)
    migrated_master = ap.compute_migrated_master(spec["wanted_folds"], artifact_path, master_sha256)

    # Determinism gate (Section 12): each side run TWICE before ever
    # comparing baseline vs migrated.
    baseline_run1 = run_execution(spec, baseline_master)
    baseline_run2 = run_execution(spec, baseline_master)
    migrated_run1 = run_execution(spec, migrated_master)
    migrated_run2 = run_execution(spec, migrated_master)

    b1_stream_hash = canon.sha_of(baseline_run1["native_mutation_stream"])
    b2_stream_hash = canon.sha_of(baseline_run2["native_mutation_stream"])
    m1_stream_hash = canon.sha_of(migrated_run1["native_mutation_stream"])
    m2_stream_hash = canon.sha_of(migrated_run2["native_mutation_stream"])
    b1_tree_hash = canon.sha_of(baseline_run1["final_tree"])
    b2_tree_hash = canon.sha_of(baseline_run2["final_tree"])
    m1_tree_hash = canon.sha_of(migrated_run1["final_tree"])
    m2_tree_hash = canon.sha_of(migrated_run2["final_tree"])

    determinism_ok = (
        b1_stream_hash == b2_stream_hash and m1_stream_hash == m2_stream_hash
        and b1_tree_hash == b2_tree_hash and m1_tree_hash == m2_tree_hash
    )
    check("%s.determinism native-mutation-stream AND final-tree hashes each reproduce "
          "identically across two independent runs, per side" % scenario_name, determinism_ok,
          (b1_stream_hash, b2_stream_hash, m1_stream_hash, m2_stream_hash, b1_tree_hash, b2_tree_hash, m1_tree_hash, m2_tree_hash))

    if not determinism_ok:
        LEDGER.append({"scenario": scenario_name, "verdict": "INCONCLUSIVE",
                        "reason": "nondeterministic within one side"})
        return

    # Regression check (Section 7.3): the decision-plan stream (already
    # qualified 37/37) must STILL match here, fed by the SAME
    # `pre`/`post` this execution harness independently derives.
    decision_hash_b = canon.sha_of(baseline_run1["decision_plan"])
    decision_hash_b2 = canon.sha_of(baseline_run2["decision_plan"])
    decision_hash_m = canon.sha_of(migrated_run1["decision_plan"])
    decision_hash_m2 = canon.sha_of(migrated_run2["decision_plan"])
    decision_match = decision_hash_b == decision_hash_m
    check("%s.decision_plan_regression the already-qualified decision-plan stream still "
          "matches baseline vs migrated when derived from this execution harness's own "
          "fake-world POST snapshot" % scenario_name, decision_match, (decision_hash_b, decision_hash_m))

    initial_post_match = canon.sha_of(baseline_run1["initial_post"]) == canon.sha_of(migrated_run1["initial_post"])
    check("%s.initial_post_sanity the two independently-constructed fake worlds (baseline, "
          "migrated) start from an identical POST snapshot (fixture-construction sanity, not "
          "authority evidence -- discover_rig_context/capture_snapshot_explicit never read "
          "master at all)" % scenario_name, initial_post_match)

    outcome_match = baseline_run1["outcome"] == migrated_run1["outcome"]
    check("%s.outcome_match composer outcome (composed / native_post_fallback:<status> / "
          "raised-exception-with-exact-message) matches exactly" % scenario_name, outcome_match,
          (baseline_run1["outcome"], migrated_run1["outcome"]))

    # No fixture in this qualified matrix is expected to ever hit an
    # UNEXPECTED composer exception -- every non-active-rig fixture now
    # correctly short-circuits at the `native_post_fallback` gate
    # BEFORE composer is ever called (matching real production's own
    # upstream gate), and every active-rig fixture is expected to reach
    # a clean "composed" outcome. A "raised:" outcome surviving to here
    # would mean a genuine, unexplained composer failure -- flagged
    # explicitly rather than silently accepted merely because both
    # sides happened to fail identically (exactly the masked-mutual-
    # failure class of bug this round found and fixed in A3/B1/B4/D3/D5).
    check("%s.no_unexplained_composer_exception neither side raised an unexpected exception "
          "(every fixture reaches either a clean 'composed' outcome or the expected, disclosed "
          "'native_post_fallback:<status>' pre-composer gate)" % scenario_name,
          not baseline_run1["outcome"].startswith("raised:") and not migrated_run1["outcome"].startswith("raised:"),
          (baseline_run1["outcome"], migrated_run1["outcome"]))

    stream_match = m1_stream_hash == b1_stream_hash
    check("%s.native_mutation_stream the ordered native mutation stream (CreateControlGroup/"
          "AddChild/RemoveChild/AddControl/SetName/SetVisible/SetSelectable/SetSnappable/"
          "SetGroupColor, in order) matches exactly between baseline and migrated" % scenario_name,
          stream_match, (b1_stream_hash, m1_stream_hash))

    tree_match = m1_tree_hash == b1_tree_hash
    check("%s.final_tree the resulting logical control-group tree (full hierarchy, sibling "
          "order, control membership, metadata) matches exactly between baseline and migrated"
          % scenario_name, tree_match, (b1_tree_hash, m1_tree_hash))

    no_unexplained_exception = (
        not baseline_run1["outcome"].startswith("raised:") and not migrated_run1["outcome"].startswith("raised:")
    )
    verdict = "PASS" if (decision_match and outcome_match and stream_match and tree_match
                          and no_unexplained_exception) else "FAIL"
    # Deterministic fixture-spec identity SHA (governing prompt Section 5)
    # -- the declarative spec itself (groups/controls/wanted_folds/rig
    # status/hidden groups), independent of any run's output, so a
    # fixture's own identity is separately verifiable from its evidence.
    fixture_spec_hash = canon.sha_of({
        "post_groups_spec": spec["post_groups_spec"],
        "post_control_specs": spec["post_control_specs"],
        "wanted_folds": sorted(spec["wanted_folds"]),
        "rig_status": spec["rig_status"],
        "hidden_groups": spec["hidden_groups"],
    })
    LEDGER.append({
        "scenario": scenario_name,
        "note": spec["note"],
        "wanted_folds": sorted(spec["wanted_folds"]),
        "outcome": baseline_run1["outcome"],
        "mutation_count": len(baseline_run1["native_mutation_stream"]),
        "composer_result": baseline_run1["composer_result"],
        "initial_post_hash": canon.sha_of(baseline_run1["initial_post"]),
        "fixture_spec_hash": fixture_spec_hash,
        # Full repeat-1/repeat-2, baseline/migrated evidence (governing
        # prompt Section 5) -- NOT replaced with only
        # `determinism_confirmed: true`; every one of the 12 required
        # SHAs is preserved explicitly.
        "baseline_decision_plan_hash_repeat1": decision_hash_b,
        "baseline_decision_plan_hash_repeat2": decision_hash_b2,
        "migrated_decision_plan_hash_repeat1": decision_hash_m,
        "migrated_decision_plan_hash_repeat2": decision_hash_m2,
        "baseline_native_mutation_stream_hash_repeat1": b1_stream_hash,
        "baseline_native_mutation_stream_hash_repeat2": b2_stream_hash,
        "migrated_native_mutation_stream_hash_repeat1": m1_stream_hash,
        "migrated_native_mutation_stream_hash_repeat2": m2_stream_hash,
        "baseline_final_tree_hash_repeat1": b1_tree_hash,
        "baseline_final_tree_hash_repeat2": b2_tree_hash,
        "migrated_final_tree_hash_repeat1": m1_tree_hash,
        "migrated_final_tree_hash_repeat2": m2_tree_hash,
        # Back-compat convenience aliases (repeat-1 values) -- kept so
        # any existing tooling/report text referencing the older
        # unsuffixed field names still resolves to a value.
        "baseline_decision_plan_hash": decision_hash_b,
        "migrated_decision_plan_hash": decision_hash_m,
        "baseline_native_mutation_stream_hash": b1_stream_hash,
        "migrated_native_mutation_stream_hash": m1_stream_hash,
        "baseline_final_tree_hash": b1_tree_hash,
        "migrated_final_tree_hash": m1_tree_hash,
        "verdict": verdict,
    })


print("\n=== Execution-layer fixture matrix (reusing the 10 qualified decision fixtures) ===")
for scenario_name in sorted(SCENARIOS.keys()):
    compare_scenario(scenario_name, SCENARIOS[scenario_name])

print("\n=== Target/scope-discovery authority-sensitive island: _gate_is_alh ===")
gate_handles = fake_dme._HandleAllocator()
gate_controls_arm_leg_head = [
    fake_dme.FakeDmeControl(gate_handles, u"valve.l_upperarm"),
    fake_dme.FakeDmeControl(gate_handles, u"normalizing_control"),
    fake_dme.FakeDmeControl(gate_handles, u"head_bone"),
]
gate_aset = fake_dme.FakeDmeAnimationSet(gate_handles, u"gate_aset", None, gate_controls_arm_leg_head)
gate_wanted = {u"valve.l_upperarm", u"normalizing_control", u"head_bone"}
gate_baseline_master = ap.compute_baseline_master(gate_wanted, master_path)
gate_migrated_master = ap.compute_migrated_master(gate_wanted, artifact_path, master_sha256)
gate_result_baseline = ns["_gate_is_alh"](gate_aset, gate_baseline_master)
gate_result_migrated = ns["_gate_is_alh"](gate_aset, gate_migrated_master)
check("gate.alh_arm_leg_head_match _gate_is_alh (the ONE authority-sensitive function in "
      "target/scope eligibility discovery -- everything else in that layer is grep-confirmed "
      "master-independent) produces the identical (alh_pass, arm, leg, head) tuple for "
      "baseline vs migrated authority", gate_result_baseline == gate_result_migrated,
      (gate_result_baseline, gate_result_migrated))
LEDGER.append({
    "scenario": "GATE_is_alh_arm_leg_head",
    "note": "target/scope-discovery authority-sensitive island (low-bone/no-ALH skip gate)",
    "baseline_result": list(gate_result_baseline),
    "migrated_result": list(gate_result_migrated),
    "verdict": "PASS" if gate_result_baseline == gate_result_migrated else "FAIL",
})

print("\n=== Negative controls (Section 9) -- prove the execution oracle detects real differences ===")

# NC-EXEC-1: suppress one mutation primitive -- monkeypatch AddControl on
# the migrated run's fake group to become a no-op, confirm the missing
# mutation is detected in the native mutation stream AND the final tree.
# Uses A4 (parent_collapse), not A2 -- A2's control is already correctly
# placed by production_ensure_group_path's metadata pass alone
# (moved_count=0, AddControl never even called for it), which would make
# this perturbation vacuously ineffective through no fault of the
# oracle; A4's control genuinely moves (17 real mutation-log entries,
# including add_control_to_group), so suppressing AddControl there has
# something real to suppress.
nc_spec = SCENARIOS["A4_rig_owned_visible_parent_collapse"]
baseline_master_nc = ap.compute_baseline_master(nc_spec["wanted_folds"], master_path)
migrated_master_nc = ap.compute_migrated_master(nc_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_nc = run_execution(nc_spec, baseline_master_nc)

_orig_add_control = fake_dme.FakeDmeControlGroup.AddControl


def _noop_add_control(self, control):
    pass  # suppressed -- deliberately never calls the real method


fake_dme.FakeDmeControlGroup.AddControl = _noop_add_control
try:
    migrated_run_nc1 = run_execution(nc_spec, migrated_master_nc)
finally:
    fake_dme.FakeDmeControlGroup.AddControl = _orig_add_control

nc1_stream_mismatch = canon.sha_of(baseline_run_nc["native_mutation_stream"]) != canon.sha_of(migrated_run_nc1["native_mutation_stream"])
nc1_tree_mismatch = canon.sha_of(baseline_run_nc["final_tree"]) != canon.sha_of(migrated_run_nc1["final_tree"])
nc1_outcome_changed = baseline_run_nc["outcome"] != migrated_run_nc1["outcome"]
check("NC-EXEC-1 suppressing AddControl (one mutation primitive) is detected -- via mutation-"
      "stream difference, final-tree difference, and/or a composer postcondition failure "
      "(production_generic_composer's own 'destination' failure check)",
      nc1_stream_mismatch or nc1_tree_mismatch or nc1_outcome_changed,
      {"stream_differs": nc1_stream_mismatch, "tree_differs": nc1_tree_mismatch,
       "outcome_changed": nc1_outcome_changed, "migrated_outcome": migrated_run_nc1["outcome"]})

# NC-EXEC-2: change one destination group -- poison the migrated
# authority's destination for the decisive control, confirm detection
# (mirrors NC1 from the plan-layer phase, now propagated all the way to
# the native mutation stream/final tree).
poisoned_master_nc2 = json.loads(json.dumps(migrated_master_nc, default=list))
for entries in poisoned_master_nc2["folded"].get(u"collapsing_control", poisoned_master_nc2["folded"].get("collapsing_control", [])):
    entries["destination"] = u"DELIBERATELY_WRONG_DESTINATION"
migrated_run_nc2 = run_execution(nc_spec, poisoned_master_nc2)
nc2_stream_mismatch = canon.sha_of(baseline_run_nc["native_mutation_stream"]) != canon.sha_of(migrated_run_nc2["native_mutation_stream"])
nc2_tree_mismatch = canon.sha_of(baseline_run_nc["final_tree"]) != canon.sha_of(migrated_run_nc2["final_tree"])
check("NC-EXEC-2 poisoning one destination group is detected at the execution layer (mutation "
      "stream and/or final tree differ)", nc2_stream_mismatch or nc2_tree_mismatch,
      {"stream_differs": nc2_stream_mismatch, "tree_differs": nc2_tree_mismatch})

# NC-EXEC-3: alter one sibling insertion index -- reverse the poisoned
# migrated master's root sibling order, confirm the final tree's
# root_order (an explicit `after`-invariant `production_generic_composer`
# itself checks: "root_master_projection") is affected.
sib_spec = SCENARIOS["A5_rig_owned_visible_master_normalization"]
baseline_master_sib = ap.compute_baseline_master(sib_spec["wanted_folds"], master_path)
migrated_master_sib = ap.compute_migrated_master(sib_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_sib = run_execution(sib_spec, baseline_master_sib)
poisoned_master_sib = json.loads(json.dumps(migrated_master_sib, default=list))
root_order = poisoned_master_sib.get("group_sibling_order", {}).get(u"<ROOT>", poisoned_master_sib.get("group_sibling_order", {}).get("<ROOT>"))
if root_order:
    poisoned_master_sib["group_sibling_order"][u"<ROOT>"] = list(reversed(root_order))
migrated_run_sib = run_execution(sib_spec, poisoned_master_sib)
nc3_tree_mismatch = canon.sha_of(baseline_run_sib["final_tree"]) != canon.sha_of(migrated_run_sib["final_tree"])
nc3_root_order_differs = (baseline_run_sib["composer_result"] or {}).get("root_order") != (migrated_run_sib["composer_result"] or {}).get("root_order")
check("NC-EXEC-3 reversing root sibling order in the migrated authority is detected: "
      "composer's own root_order differs (baseline [RigArms, RigLegs] vs poisoned "
      "[RigLegs, RigArms]) and/or the final tree hash differs",
      nc3_tree_mismatch or nc3_root_order_differs,
      {"tree_differs": nc3_tree_mismatch, "baseline_root_order": (baseline_run_sib["composer_result"] or {}).get("root_order"),
       "migrated_root_order": (migrated_run_sib["composer_result"] or {}).get("root_order")})

# NC-EXEC-4 (first attempt, DISCLOSED as ineffective): suppressing
# RemoveChild inside B3's full composer run produced NO detectable
# difference, because `production_reorder_children_by_master`'s own
# short-circuit (`if desired == current_names: return desired`) means
# RemoveChild is never even CALLED for B3's RigArms -- the fixture's own
# authority Master TXT declares no nested child GROUPS under "RigArms"
# (only direct CONTROLS), so `master["group_sibling_order"]["RigArms"]`
# is empty and the existing creation order ("A" then "B", alphabetical)
# already equals the (trivially empty-master-order) desired order. This
# is a bad perturbation-SCENARIO choice, not oracle insensitivity --
# confirmed by testing `production_reorder_children_by_master` in
# ISOLATION below, with a hand-built master whose sibling order
# genuinely disagrees with creation order (guaranteeing a real
# remove-then-readd dance actually happens).
reorder_spec = SCENARIOS["B3_nested_sibling_ordering"]
baseline_master_ro = ap.compute_baseline_master(reorder_spec["wanted_folds"], master_path)
migrated_master_ro = ap.compute_migrated_master(reorder_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_ro = run_execution(reorder_spec, baseline_master_ro)
_orig_remove_child = fake_dme.FakeDmeControlGroup.RemoveChild
fake_dme.FakeDmeControlGroup.RemoveChild = lambda self, group: None
try:
    migrated_run_ro = run_execution(reorder_spec, migrated_master_ro)
finally:
    fake_dme.FakeDmeControlGroup.RemoveChild = _orig_remove_child
nc4a_differs = (
    canon.sha_of(baseline_run_ro["native_mutation_stream"]) != canon.sha_of(migrated_run_ro["native_mutation_stream"])
    or canon.sha_of(baseline_run_ro["final_tree"]) != canon.sha_of(migrated_run_ro["final_tree"])
)
print("[NC-EXEC-4a, disclosed ineffective] suppressing RemoveChild in the full B3 composer run "
      "produced a difference: %r (expected False -- RemoveChild is never called for this "
      "fixture's RigArms at all; superseded by NC-EXEC-4b)" % nc4a_differs)

# NC-EXEC-4b: `production_reorder_children_by_master` tested directly
# (isolated unit call, not through the full composer/scenario matrix) --
# a hand-built group with children created in order [X, Y], and a
# hand-built master whose `group_sibling_order["Parent"] = [Y, X]`
# GENUINELY disagrees with creation order, forcing a real remove-then-
# readd cycle. Applied identically to "baseline" and "migrated" calls
# of the SAME real extracted function; RemoveChild suppressed ONLY on
# the second ("migrated") call.
gate_handles_nc4 = fake_dme._HandleAllocator()
mlog_a = fake_dme.MutationLog()
mlog_b = fake_dme.MutationLog()
parent_a = fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_a, u"Parent")
parent_a.children = [fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_a, u"X"),
                      fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_a, u"Y")]
for c in parent_a.children:
    c._parent = parent_a
parent_b = fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_b, u"Parent")
parent_b.children = [fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_b, u"X"),
                      fake_dme.FakeDmeControlGroup(gate_handles_nc4, mlog_b, u"Y")]
for c in parent_b.children:
    c._parent = parent_b
hand_master = {"group_sibling_order": {u"Parent": [u"Y", u"X"]}}

reorder_a = ns["production_reorder_children_by_master"](parent_a, hand_master, u"Parent", False)
_orig_remove_child2 = fake_dme.FakeDmeControlGroup.RemoveChild
fake_dme.FakeDmeControlGroup.RemoveChild = lambda self, group: None
try:
    try:
        reorder_b = ns["production_reorder_children_by_master"](parent_b, hand_master, u"Parent", False)
        outcome_b = "ok:%r" % (reorder_b,)
    except Exception as exc:
        outcome_b = "raised:%s:%s" % (type(exc).__name__, str(exc)[:200])
finally:
    fake_dme.FakeDmeControlGroup.RemoveChild = _orig_remove_child2

nc4b_final_order_a = [c.GetName() for c in parent_a.children]
check("NC-EXEC-4b.setup real reorder genuinely happened for the UNPERTURBED call (desired "
      "[Y, X] != creation order [X, Y])", reorder_a == [u"Y", u"X"] and nc4b_final_order_a == [u"Y", u"X"], reorder_a)
check("NC-EXEC-4b suppressing RemoveChild during a GENUINE reorder is detected -- the perturbed "
      "call either raises (duplicate-sibling-name postcondition) or leaves the tree in the "
      "wrong order", outcome_b.startswith("raised") or [c.GetName() for c in parent_b.children] != [u"Y", u"X"],
      {"outcome_b": outcome_b, "parent_b_children": [c.GetName() for c in parent_b.children]})

# NC-EXEC-5 (first attempt, DISCLOSED as ineffective): adding a
# "RigHelpers" group to only the LIVE post-tree had no effect, because
# `production_generic_composer`'s RigHelpers-restoration branch gates on
# `rig_source["groups"].get("RigHelpers")` -- `rig_source` comes from
# `canonicalize_rig_source_snapshot(pre)`, and this scenario's hand-
# authored `pre` dict has no "RigHelpers" entry at all, regardless of
# what the LIVE tree contains. Superseded by NC-EXEC-5b, which adds
# RigHelpers to `pre` too (the actual gating input).
helper_spec_groups = dict(reorder_spec["post_groups_spec"])
helper_spec_groups[u"RigHelpers"] = {"visible": True}
helper_spec_controls = list(reorder_spec["post_control_specs"]) + [
    {"name": u"helper_control", "path": u"RigHelpers", "owned": False}]
migrated_shot, migrated_aset, migrated_root, migrated_mlog, _h, _g, _c = fake_dme.build_world(
    helper_spec_groups, helper_spec_controls,
    rig_status=reorder_spec["rig_status"], hidden_groups=reorder_spec["hidden_groups"])
migrated_rig_context = ns["discover_rig_context"](migrated_shot, migrated_aset)
migrated_post_helper = ns["capture_snapshot_explicit"](migrated_shot, migrated_aset, "POST", migrated_rig_context)
migrated_cmd = FakeCommand()
migrated_plan_helper = ns["preflight_reconciliation_plan_pure"](
    migrated_cmd, reorder_spec["pre"], migrated_post_helper, migrated_master_ro, (u"shot1", u"aset1"))
migrated_uniformity_helper = ns["derive_generic_uniformity_plan"](
    reorder_spec["pre"], migrated_post_helper, migrated_master_ro, migrated_plan_helper)
ns["production_generic_composer"](migrated_root, reorder_spec["pre"], migrated_post_helper, migrated_master_ro,
                                   migrated_shot, migrated_aset, migrated_plan_helper, migrated_uniformity_helper)
nc5a_differs = len(baseline_run_ro["native_mutation_stream"]) != len(migrated_mlog.entries)
print("[NC-EXEC-5a, disclosed ineffective] RigHelpers added to the LIVE tree only produced a "
      "mutation-count difference: %r (expected False -- the restoration branch also requires "
      "RigHelpers in `rig_source`, derived from `pre`, unchanged here; superseded by NC-EXEC-5b)"
      % nc5a_differs)

# NC-EXEC-5b: add "RigHelpers" to BOTH `pre` (the actual gating input,
# via rig_source) AND the live tree, for the perturbed run only.
from fixture_builder import build_snapshot, ROOT as _ROOT  # noqa: E402
pre_with_helpers_groups = dict(reorder_spec["post_groups_spec"])
pre_with_helpers_groups[u"RigHelpers"] = {"visible": True}
pre_with_helpers_controls = list(reorder_spec["post_control_specs"])
pre_with_helpers = build_snapshot("PRE_with_helpers", pre_with_helpers_groups, pre_with_helpers_controls,
                                   rig_status=reorder_spec["rig_status"], hidden_groups=reorder_spec["hidden_groups"])

shot5b, aset5b, root5b, mlog5b, _h5b, _g5b, _c5b = fake_dme.build_world(
    helper_spec_groups, helper_spec_controls,
    rig_status=reorder_spec["rig_status"], hidden_groups=reorder_spec["hidden_groups"])
rc5b = ns["discover_rig_context"](shot5b, aset5b)
post5b = ns["capture_snapshot_explicit"](shot5b, aset5b, "POST", rc5b)
cmd5b = FakeCommand()
plan5b = ns["preflight_reconciliation_plan_pure"](cmd5b, pre_with_helpers, post5b, migrated_master_ro, (u"shot1", u"aset1"))
uniformity5b = ns["derive_generic_uniformity_plan"](pre_with_helpers, post5b, migrated_master_ro, plan5b)
ns["production_generic_composer"](root5b, pre_with_helpers, post5b, migrated_master_ro, shot5b, aset5b, plan5b, uniformity5b)

nc5b_differs = len(baseline_run_ro["native_mutation_stream"]) != len(mlog5b.entries)
check("NC-EXEC-5b a RigHelpers group present in BOTH `pre` (rig_source) and the live tree "
      "correctly fires the RigHelpers-restoration branch (extra set_visible/set_selectable/"
      "set_snappable mutations), detected via a mutation-stream length difference",
      nc5b_differs, {"baseline_mutation_count": len(baseline_run_ro["native_mutation_stream"]),
                      "perturbed_mutation_count": len(mlog5b.entries)})

print("\n=== Final Expansion Fixture negative controls (per-fixture, as specified) ===")

# NC-A (Fixture A / toe relocation): suppress AddControl for ONE toe
# control only ("keep one toe in the old location").
toe_spec = SCENARIOS["D1_active_rig_toe_relocation"]
toe_baseline_master = ap.compute_baseline_master(toe_spec["wanted_folds"], master_path)
toe_migrated_master = ap.compute_migrated_master(toe_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_toe = run_execution(toe_spec, toe_baseline_master)

_orig_add_control_toe = fake_dme.FakeDmeControlGroup.AddControl


def _suppress_one_toe(self, control):
    if control.GetName() == u"canon_toe_l":
        return  # keep this ONE toe in its old location -- suppressed
    _orig_add_control_toe(self, control)


fake_dme.FakeDmeControlGroup.AddControl = _suppress_one_toe
try:
    migrated_run_toe = run_execution(toe_spec, toe_migrated_master)
finally:
    fake_dme.FakeDmeControlGroup.AddControl = _orig_add_control_toe

nc_a_differs = (
    canon.sha_of(baseline_run_toe["native_mutation_stream"]) != canon.sha_of(migrated_run_toe["native_mutation_stream"])
    or canon.sha_of(baseline_run_toe["final_tree"]) != canon.sha_of(migrated_run_toe["final_tree"])
)
check("NC-A (toe relocation) keeping 'canon_toe_l' in its old canonical location instead of "
      "relocating it beneath RigLegs/LeftLeg/LeftToes is detected", nc_a_differs)

# NC-B (Fixture B / flex-first ordering): swap the declared order in the
# MIGRATED authority only (poison global_index/local_index so bone
# sorts before flex).
flex_spec = SCENARIOS["D5_flex_first_ordering"]
flex_baseline_master = ap.compute_baseline_master(flex_spec["wanted_folds"], master_path)
flex_migrated_master = ap.compute_migrated_master(flex_spec["wanted_folds"], artifact_path, master_sha256)
poisoned_flex_master = json.loads(json.dumps(flex_migrated_master, default=list))
flex_entries = poisoned_flex_master["folded"].get(u"eye_flex_control", poisoned_flex_master["folded"].get("eye_flex_control", []))
bone_entries = poisoned_flex_master["folded"].get(u"eye_bone_control", poisoned_flex_master["folded"].get("eye_bone_control", []))
for e in flex_entries:
    e["global_index"], e["local_index"] = 999999, 999999  # push flex to the END of the order
baseline_run_flex = run_execution(flex_spec, flex_baseline_master)
poisoned_run_flex = run_execution(flex_spec, poisoned_flex_master)
nc_b_differs = canon.sha_of(baseline_run_flex["native_mutation_stream"]) != canon.sha_of(poisoned_run_flex["native_mutation_stream"])
check("NC-B (flex-first ordering) swapping eye_flex_control's declared order to AFTER "
      "eye_bone_control in the migrated authority is detected in the native mutation stream "
      "(add_control_to_group call order changes)", nc_b_differs)

# NC-C (Fixture C / Tail relocation, CORRECTED fixture D6): retain
# 'tail_control_a' in its prior path (WrongGroup) instead of relocating
# it into the real Master-declared "Tail" group -- suppress AddControl
# for that one control only, mirroring NC-A's proven pattern.
tail_spec = SCENARIOS["D6_tail_relocation"]
tail_baseline_master = ap.compute_baseline_master(tail_spec["wanted_folds"], master_path)
tail_migrated_master = ap.compute_migrated_master(tail_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_tail = run_execution(tail_spec, tail_baseline_master)

_orig_add_control_tail = fake_dme.FakeDmeControlGroup.AddControl


def _suppress_one_tail_move(self, control):
    if control.GetName() == u"tail_control_a":
        return  # retain this control in its prior path (WrongGroup) -- suppressed
    _orig_add_control_tail(self, control)


fake_dme.FakeDmeControlGroup.AddControl = _suppress_one_tail_move
try:
    migrated_run_tail_wrong = run_execution(tail_spec, tail_migrated_master)
finally:
    fake_dme.FakeDmeControlGroup.AddControl = _orig_add_control_tail

nc_c_differs = (
    canon.sha_of(baseline_run_tail["native_mutation_stream"]) != canon.sha_of(migrated_run_tail_wrong["native_mutation_stream"])
    or canon.sha_of(baseline_run_tail["final_tree"]) != canon.sha_of(migrated_run_tail_wrong["final_tree"])
)
check("NC-C (Tail relocation, D6) retaining 'tail_control_a' in its prior path (WrongGroup) "
      "instead of relocating it into the real Master-declared 'Tail' group is detected", nc_c_differs)

# NC-D (Fixture D / repeated-control preservation): D3's two repeated-
# key controls ('stranded_control', 'Stranded_Control') are BOTH
# already correctly placed in HiddenGroup -- real production's
# `already_correct` skip means `add_control_to_group` is NEVER called
# for either (confirmed by direct inspection: D3's native mutation
# stream contains only group-level restoration/reorder operations, zero
# `add_control_to_group` entries). Monkeypatching `AddControl` is
# therefore ineffective here (disclosed below as NC-D-a) -- the
# meaningful "accidental duplicate/suppressed membership mutation" for
# THIS fixture must be injected directly into the live fake world's
# membership graph at construction time (mirroring NC-EXEC-5b's
# proven "perturb world construction" technique), superseded as NC-D-b.
rep_spec = SCENARIOS["D3_repeated_control_preservation"]
rep_baseline_master = ap.compute_baseline_master(rep_spec["wanted_folds"], master_path)
rep_migrated_master = ap.compute_migrated_master(rep_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_rep = run_execution(rep_spec, rep_baseline_master)

_orig_add_control_rep = fake_dme.FakeDmeControlGroup.AddControl


def _duplicate_one_membership(self, control):
    _orig_add_control_rep(self, control)
    if control.GetName() == u"Stranded_Control":
        _orig_add_control_rep(self, control)  # accidental duplicate call


fake_dme.FakeDmeControlGroup.AddControl = _duplicate_one_membership
try:
    migrated_run_rep_a = run_execution(rep_spec, rep_migrated_master)
finally:
    fake_dme.FakeDmeControlGroup.AddControl = _orig_add_control_rep

nc_d_a_differs = (
    canon.sha_of(baseline_run_rep["native_mutation_stream"]) != canon.sha_of(migrated_run_rep_a["native_mutation_stream"])
    or canon.sha_of(baseline_run_rep["final_tree"]) != canon.sha_of(migrated_run_rep_a["final_tree"])
)
print("[NC-D-a, disclosed ineffective] suppressing/duplicating AddControl for 'Stranded_Control' "
      "produced a difference: %r (expected False -- both repeated-key controls are already-correctly "
      "placed, so real production never calls add_control_to_group for either; superseded by NC-D-b)"
      % (nc_d_a_differs,))

_orig_build_world_d = fake_dme.build_world


def _build_world_duplicate_membership(*args, **kwargs):
    result = _orig_build_world_d(*args, **kwargs)
    shot, aset, root, mlog, handles, groups_by_path, controls_by_name = result
    stranded = controls_by_name.get(u"Stranded_Control")
    rigarms = groups_by_path.get(u"RigArms")
    if stranded is not None and rigarms is not None:
        # Accidental extra membership mutation: reparents 'Stranded_Control'
        # into RigArms in addition to its correct HiddenGroup placement --
        # something no real classify_production/production_generic_composer
        # path ever does for an already-correctly-placed MASTER_STRANDED
        # control. AddControl's exclusive-ownership bookkeeping means this
        # is a genuine, mlog-recorded structural mutation.
        rigarms.AddControl(stranded)
    return result


fake_dme.build_world = _build_world_duplicate_membership
try:
    migrated_run_rep_b = run_execution(rep_spec, rep_migrated_master)
finally:
    fake_dme.build_world = _orig_build_world_d

nc_d_b_differs = (
    canon.sha_of(baseline_run_rep["native_mutation_stream"]) != canon.sha_of(migrated_run_rep_b["native_mutation_stream"])
    or canon.sha_of(baseline_run_rep["final_tree"]) != canon.sha_of(migrated_run_rep_b["final_tree"])
)
check("NC-D-b (repeated-control preservation) an accidental extra membership mutation reparenting "
      "'Stranded_Control' into RigArms is detected", nc_d_b_differs)

# NC-E (Fixture E / untouched custom group, REDESIGNED D4): the
# corrected UserCustomGroup/{Alpha,Beta} subtree receives ZERO direct
# native mutations from real production at all (confirmed below by an
# EXACT handle/name-based scan of the mutation log, not just a hash
# comparison) -- monkeypatching `SetVisible` is therefore ineffective
# (disclosed below as NC-E-a, same reason as before: real production
# never calls SetVisible on this group at all); the effective negative
# control instead injects one accidental mutation directly into the
# live world's UserCustomGroup at construction time, superseded as
# NC-E-b.
custom_spec = SCENARIOS["D4_untouched_custom_group_preservation"]
custom_baseline_master = ap.compute_baseline_master(custom_spec["wanted_folds"], master_path)
custom_migrated_master = ap.compute_migrated_master(custom_spec["wanted_folds"], artifact_path, master_sha256)
baseline_run_custom = run_execution(custom_spec, custom_baseline_master)

# Precise, handle/name-based proof (governing prompt Section 3): "zero
# mutation-log entries target any group/control handle inside the
# custom subtree" -- stronger than a hash-equality check, which could in
# principle mask a mutation that happened to leave the final state
# byte-identical (e.g. a set-then-reset toggle). Build one throwaway
# world from the SAME declarative spec purely to read out the custom
# subtree's real handles/names, then scan the ACTUAL baseline run's own
# mutation log against them directly.
_probe_shot, _probe_aset, _probe_root, _probe_mlog, _probe_handles, _probe_groups_by_path, _probe_controls_by_name = (
    fake_dme.build_world(custom_spec["post_groups_spec"], custom_spec["post_control_specs"],
                          rig_status=custom_spec["rig_status"], hidden_groups=custom_spec["hidden_groups"])
)
custom_subtree_group_handles = set(
    _probe_groups_by_path[p].GetHandle() for p in
    (u"UserCustomGroup", u"UserCustomGroup/Alpha", u"UserCustomGroup/Beta")
)
custom_subtree_control_names = {u"custom_control_alpha", u"custom_control_beta"}
custom_subtree_touched = [
    e for e in baseline_run_custom["native_mutation_stream"]
    if e.get("target") in custom_subtree_group_handles or e.get("control") in custom_subtree_control_names
]
check("custom_subtree.zero_mutation_log_entries zero mutation-log entries (by exact group handle "
      "or control name) target anything inside UserCustomGroup/{Alpha,Beta}", len(custom_subtree_touched) == 0,
      custom_subtree_touched)

_orig_set_visible = fake_dme.FakeDmeControlGroup.SetVisible


def _accidental_custom_mutation(self, value):
    _orig_set_visible(self, value)
    if self.name == u"UserCustomGroup":
        _orig_set_visible(self, not value)  # accidental extra, wrong-value toggle


fake_dme.FakeDmeControlGroup.SetVisible = _accidental_custom_mutation
try:
    migrated_run_custom_a = run_execution(custom_spec, custom_migrated_master)
finally:
    fake_dme.FakeDmeControlGroup.SetVisible = _orig_set_visible

nc_e_a_differs = (
    canon.sha_of(baseline_run_custom["native_mutation_stream"]) != canon.sha_of(migrated_run_custom_a["native_mutation_stream"])
    or canon.sha_of(baseline_run_custom["final_tree"]) != canon.sha_of(migrated_run_custom_a["final_tree"])
)
print("[NC-E-a, disclosed ineffective] wrapping SetVisible with an accidental extra toggle on "
      "'UserCustomGroup' produced a difference: %r (expected False -- real production never calls "
      "SetVisible on UserCustomGroup at all, so the wrapper is never invoked for it; superseded by "
      "NC-E-b)" % (nc_e_a_differs,))

_orig_build_world_e = fake_dme.build_world


def _build_world_accidental_custom_mutation(*args, **kwargs):
    result = _orig_build_world_e(*args, **kwargs)
    shot, aset, root, mlog, handles, groups_by_path, controls_by_name = result
    custom_group = groups_by_path.get(u"UserCustomGroup")
    if custom_group is not None:
        # Accidental mutation no fixture-intended code path should ever
        # perform against this untouched, unrelated subtree.
        custom_group.SetVisible(False)
    return result


fake_dme.build_world = _build_world_accidental_custom_mutation
try:
    migrated_run_custom_b = run_execution(custom_spec, custom_migrated_master)
finally:
    fake_dme.build_world = _orig_build_world_e

nc_e_b_differs = (
    canon.sha_of(baseline_run_custom["native_mutation_stream"]) != canon.sha_of(migrated_run_custom_b["native_mutation_stream"])
    or canon.sha_of(baseline_run_custom["final_tree"]) != canon.sha_of(migrated_run_custom_b["final_tree"])
)
check("NC-E-b (untouched custom group) an accidental SetVisible(False) mutation targeting "
      "'UserCustomGroup' (which no fixture-intended code path should ever touch) is detected", nc_e_b_differs)

# Final Expansion Fixtures evidence enrichment (governing prompt's
# "Evidence" section): fixture SHA (the shared b2c_c authority Master/
# artifact this whole round's D1-D5 fixtures were compiled from -- see
# authority_pair.MASTER_TXT_BODY), explicit group/control counts (from
# each fixture's own declarative spec, the single source of truth
# fixture_builder/fake_dme both construct from), determinism repeat
# confirmation (proven above by each scenario's own .determinism check;
# recorded here as a boolean for ledger completeness), and which
# fixture(s) were additionally verified through the REAL broker-
# mediated path (test_b2c_c_broker_mediated_authority_sanity.py's new
# flex-first D5 case, 17/17 PASS, not re-run from this file).
_D_FIXTURE_BROKER_MEDIATED = {"D5_flex_first_ordering"}
for _row in LEDGER:
    _name = _row["scenario"]
    if _name.startswith("D") and _name in SCENARIOS:
        _spec = SCENARIOS[_name]
        _row["fixture_master_sha256"] = master_sha256
        _row["fixture_artifact_path"] = os.path.relpath(artifact_path, _THIS_DIR)
        _row["group_count"] = len(_spec["post_groups_spec"])
        _row["control_count"] = len(_spec["post_control_specs"])
        _row["determinism_confirmed"] = True
        _row["broker_mediated_sanity"] = _name in _D_FIXTURE_BROKER_MEDIATED

print("\n=== Ledger ===")
ledger_path = os.path.join(_THIS_DIR, "R3_B2C_C_execution_layer_ledger.json")
with open(ledger_path, "w") as f:
    json.dump({"scenarios": LEDGER}, f, indent=2, sort_keys=True, separators=(",", ": "))
print("Ledger written to: %s" % ledger_path)
for row in LEDGER:
    print("  %-45s %s" % (row["scenario"], row.get("verdict")))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))

# B2C-C Targeted Audit Correction, Section 4: a failed check must cause
# a failed process.
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
