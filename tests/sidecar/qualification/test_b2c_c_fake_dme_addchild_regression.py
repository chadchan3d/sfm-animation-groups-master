# -*- coding: utf-8 -*-
"""B2C-C GitHub Checkpoint, Section 9: dedicated regression proof for the
fake-DME `AddChild` non-exclusive-reparenting defect found and fixed
during the B2C-C execution-layer qualification round.

The ORIGINAL bug (reconstructed verbatim below as `_broken_add_child`,
never shipped as the qualified `candidate_b2c_c/fake_dme.py`'s own
`AddChild`): a group created via `root.CreateControlGroup(name)` (which
attaches it under ROOT) then reparented via `some_group.AddChild(group)`
ended up duplicated under BOTH ROOT and its true intended parent, because
the original `AddChild` implementation only appended to `self.children`
without first removing `group` from any PRIOR parent's `.children` list,
and without updating `group._parent`.

This file proves, with the REAL frozen `production_generic_composer` and
a REAL qualified fixture (`B3_nested_sibling_ordering`, which exercises
exactly this `CreateControlGroup` + `AddChild` reparenting sequence, not
a synthetic toy case):

1. under the OLD broken `AddChild`, the corruption is real and
   detectable in TWO independent ways:
     a. `production_generic_composer`'s OWN postcondition check raises
        `ProbeError` mentioning `duplicate_invariant` (and wrong
        `destination` tuples) -- production's own contract catches it;
     b. even capturing the (corrupted) live tree AFTER that raise via
        the same real `capture_snapshot_explicit`/`discover_rig_context`
        functions the qualified harness uses shows the duplication
        directly: the final tree contains BOTH the stale root-level
        groups ("A", "B") AND the correctly-collapsed nested groups
        ("RigArms/A", "RigArms/B") simultaneously -- an inflated
        `group_count` and the same group name appearing at two distinct
        paths, which is exactly what "multiple parents" looks like once
        serialized;
2. under the CURRENT (fixed, qualified) `AddChild`, the same fixture
   composes cleanly (`outcome == "composed"`), with the correct,
   non-duplicated 4-group final tree;
3. no other structural fake-DME mutation primitive (`CreateControlGroup`,
   `RemoveChild`, `AddControl`) permits an analogous impossible state for
   the paths this qualification actually exercises -- each already
   enforces the SAME "remove from any prior owner first" exclusivity
   `AddChild` was missing (`AddControl`'s `control_owner` reassignment,
   `RemoveChild`'s explicit single-parent detach) -- verified by direct
   reading of `candidate_b2c_c/fake_dme.py` as committed.

Scope discipline: this file does NOT claim the fake model is a complete
DME simulation -- it documents exactly the one exclusivity contract that
was found broken, fixed, and is now regression-tested, for exactly the
mutation primitives this qualification's fixtures actually exercise.
Never launches SFM. Read-only with respect to the frozen production file
and the qualified Correction6 candidate.
"""
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_DIR = os.path.join(_THIS_DIR, "candidate_b2c_c")
if CANDIDATE_DIR not in sys.path:
    sys.path.insert(0, CANDIDATE_DIR)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import authority_pair as ap  # noqa: E402
import fake_dme  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402
import test_b2c_c_execution_layer_equivalence as harn  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

master_path, artifact_path, master_sha256 = ap.load_authority_fixture()
spec = SCENARIOS["B3_nested_sibling_ordering"]
baseline_master = ap.compute_baseline_master(spec["wanted_folds"], master_path)


def _broken_add_child(self, group):
    """Verbatim reconstruction of the ORIGINAL fake_dme.py `AddChild`
    defect (never the qualified, currently-committed implementation):
    non-exclusive reparenting -- does not remove `group` from any prior
    parent's `.children`, does not update `group._parent`."""
    if group not in self.children:
        self.children.append(group)
    self._mlog.record("add_child", target=group._handle, destination_path=self.name)


# --- 1. Reproduce the OLD bug against a REAL qualified fixture ---------
_orig_add_child = fake_dme.FakeDmeControlGroup.AddChild
fake_dme.FakeDmeControlGroup.AddChild = _broken_add_child
try:
    broken_run = harn.run_execution(spec, baseline_master)
finally:
    fake_dme.FakeDmeControlGroup.AddChild = _orig_add_child

check("broken_addchild.composer_raises the REAL production_generic_composer's own postcondition "
      "check catches the non-exclusive-reparenting corruption and raises",
      broken_run["outcome"].startswith("raised:ProbeError"), broken_run["outcome"])

check("broken_addchild.duplicate_invariant_named the raised ProbeError explicitly names "
      "'duplicate_invariant' (not some unrelated failure)",
      "duplicate_invariant" in broken_run["outcome"], broken_run["outcome"])

broken_groups = set(broken_run["final_tree"]["groups"].keys())
expected_stale_and_correct = {u"A", u"B", u"RigArms/A", u"RigArms/B"}
check("broken_addchild.final_tree_shows_duplication even AFTER the composer's own raise, the "
      "(corrupted) live tree captured via the SAME real capture_snapshot_explicit/discover_rig_"
      "context the qualified harness uses shows BOTH the stale root-level groups ('A','B') AND "
      "the correctly-collapsed nested groups ('RigArms/A','RigArms/B') simultaneously -- "
      "final-tree serialization independently detects the multi-parent corruption",
      expected_stale_and_correct.issubset(broken_groups), sorted(broken_groups))

check("broken_addchild.inflated_group_count the corrupted final tree has MORE groups than the "
      "correct result (6 vs the fixed result's 4) -- a directly observable structural signal",
      broken_run["final_tree"]["group_count"] > 4, broken_run["final_tree"]["group_count"])

# --- 2. Prove the CURRENT (fixed, qualified) AddChild composes cleanly -
fixed_run = harn.run_execution(spec, baseline_master)

check("fixed_addchild.composes_cleanly the CURRENT qualified AddChild (exclusive reparenting) "
      "reaches a clean 'composed' outcome for the identical fixture/master",
      fixed_run["outcome"] == "composed", fixed_run["outcome"])

fixed_groups = set(fixed_run["final_tree"]["groups"].keys())
check("fixed_addchild.no_stale_duplicates the fixed final tree contains ONLY the correctly-"
      "collapsed groups, with no stale root-level 'A'/'B' left behind",
      fixed_groups == {u"<ROOT>", u"RigArms", u"RigArms/A", u"RigArms/B"}, sorted(fixed_groups))

check("fixed_addchild.exact_group_count the fixed final tree has exactly 4 groups (no "
      "duplication of any kind)", fixed_run["final_tree"]["group_count"] == 4,
      fixed_run["final_tree"]["group_count"])

# --- 3. No other structural mutation primitive permits an analogous ----
#        impossible state, for the paths this qualification exercises.
import inspect  # noqa: E402

addcontrol_src = inspect.getsource(fake_dme.FakeDmeControlGroup.AddControl)
check("other_primitives.addcontrol_exclusive AddControl reassigns `control_owner` and removes "
      "the control from any PRIOR owner's `.controls` before appending -- the same exclusivity "
      "AddChild was missing", "control_owner" in addcontrol_src and "owner.controls.remove" in addcontrol_src)

removechild_src = inspect.getsource(fake_dme.FakeDmeControlGroup.RemoveChild)
check("other_primitives.removechild_detaches RemoveChild removes the group from `self.children` "
      "and clears `group._parent` when `self` was the real parent -- no orphan/multi-parent state "
      "possible via this primitive",
      "self.children.remove(group)" in removechild_src and "_parent = None" in removechild_src)

createcontrolgroup_src = inspect.getsource(fake_dme.FakeDmeControlGroup.CreateControlGroup)
check("other_primitives.createcontrolgroup_single_attach CreateControlGroup attaches the newly "
      "created group under exactly one parent (`self`) at creation time -- no way to create a "
      "group already multiply-parented",
      "group._parent = self" in createcontrolgroup_src)

fixed_addchild_src = inspect.getsource(fake_dme.FakeDmeControlGroup.AddChild)
check("committed_addchild.is_exclusive the CURRENTLY COMMITTED AddChild (as qualified, not the "
      "reconstructed old bug above) removes `group` from any prior parent's `.children` before "
      "appending to `self.children`, and updates `group._parent`",
      "_parent.children.remove(group)" in fixed_addchild_src and "group._parent = self" in fixed_addchild_src)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
