# F2-R1 Controlled Edit — Justification (CORRECTED 2026-09-24)

**Correction record:** the original design assumed the operator could freely drag `rig_hand_L` into an
arbitrary existing group (`RigHelpers`) via the Animation Set Editor. That assumption was wrong — SFM does
not support unilateral relocation into an arbitrary group that way. The actual, real, supported relocation
mechanism available to the operator is a first-party SFM DAG-view right-click command that moves the
selected control into a group literally named `Hidden`. This document replaces the original justification;
the prior attempt (which used the incorrect `RigHelpers` assumption) is treated as aborted, not
qualification evidence.

## The real mechanism (verified from the actual shipped script, not assumed)

`E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\platform\scripts\sfm\dag\exact\count1\move_to_hidden group .py`:

```python
def Hide_SelectedDag():
    animSet = sfm.GetCurrentAnimationSet()
    rootGroup = animSet.GetRootControlGroup()
    targetDag = sfm.FirstSelectedDag()

    HiddenGroup = rootGroup.FindControlByName("Hidden", False)
    if not HiddenGroup:
        HiddenGroup = rootGroup.CreateControlGroup("Hidden")
        HiddenGroup.SetGroupColor(vs.Color(0, 128, 255, 255), False)
        HiddenGroup.SetSelectable(False)
        HiddenGroup.SetVisible(False)

    sfmUtils.AddDagControlsToGroup(HiddenGroup, targetDag)

Hide_SelectedDag()
```

This is a real, first-party, already-shipped SFM DAG-view command (appears as a right-click context-menu
entry when a control is selected in the DAG/Animation Set Editor view). It operates on `rootGroup =
animSet.GetRootControlGroup()` — the exact same root object this checkpoint's own
`capture_tree(aset.GetRootControlGroup())` call already walks — confirming `Hidden` is a real, literal
`DmeControlGroup`, a direct child of the target's own root group, not a separate SFM-native concept outside
the tree production manages. If it does not already exist, it is created with `SetVisible(False)` and
`SetSelectable(False)`.

## Corrected exact edit

| Field | Value |
|---|---|
| Shot | `shot3` |
| Animation set / target | `foxmccouldwm1` |
| Control affected | `rig_hand_L` |
| Initial qualified state | Direct member of group `RigArms/LeftArm` |
| Operator mutation | Select `rig_hand_L` in the DAG view; run the real SFM DAG right-click command "move to hidden group" (`Hide_SelectedDag()`), moving it into the group literally named `Hidden` |
| Pre-Stage-2 required state | `rig_hand_L` present under `Hidden`; absent from `RigArms/LeftArm` |
| Expected post-Stage-2 normalized state | `rig_hand_L` restored to `RigArms/LeftArm`, in the already-qualified Master-defined order `(rig_collar_L, rig_elbow_L, rig_hand_L)` |

## Verification that Hidden is a valid perturbation (source-cited, not assumed)

### Q1: Is a control currently under Hidden still eligible for normal Master-driven destination reconciliation?

**Yes.** Traced directly in `audit_external_runtime/Rebuild_Control_Groups_Normalizer.py`. Composer's own
candidate-destination computation for every rig row (line ~5920-5932):

```python
lookup = master_lookup(master, control_name)
if lookup["known"]:
    target_path = _active_rig_counterpart_destination(
        lookup["destination"], source_path, has_rigarms, has_riglegs,
    )
    authority = u"MASTER_PLUS_ACTIVE_RIG_COUNTERPART"
    if control_name in pre_hidden_master_active_names:
        authority = u"PRE_HIDDEN_MASTER_ACTIVE+MASTER_DESTINATION+VISIBLE_SAME_DESTINATION_PEERS"
```

`target_path` — the actual computed destination — is derived from the **same** `_active_rig_counterpart_
destination()` call regardless of whether the control is in `pre_hidden_master_active_names`. Only the
**logged authority label** changes. `rig_hand_L`'s own real, already-established destination
(`RigArms/LeftArm`, `EXACT_MASTER_DESTINATION_TOTAL_ORDER`) is untouched by this distinction.

### Q2: Is Hidden treated specially anywhere — skipped, preserved, excluded, or a semantic change beyond presentation grouping?

**Partially — there is a real, deliberate special case, but it does not exclude the control; it is an
additional safety gate, and `rig_hand_L`'s own real siblings satisfy it.** The module's own docstring
(lines 59-64) names this explicitly as "PRE-hidden Master-active repair." Traced directly (lines
~3889-4034):

```python
# Production: fresh-PRE hidden active-rig completion.  This is deliberately
# stricter than ordinary rig-loss classification.  A hidden rig-owned
# transform is eligible only when current Master explicitly names an
# active RigBody/RigArms/RigLegs destination, that active root is
# already effectively visible in fresh PRE, and at least two other
# visible rig-owned transforms independently resolve to the exact same
# Master destination.
if not bool(pre_group["effective_visible"]):
    ...
    if (len(corroborating_peers) >= 2
            and not (row["post_matches_master"] and row["post_visible"])):
        row["category"] = "RIG_OWNED_PRE_HIDDEN_MASTER_ACTIVE"
        pre_hidden_master_active.append(row)
```

A control found in an **invisible** group (which `Hidden` is, by the DAG command's own
`SetVisible(False)`) before native Rebuild runs is classified this way, requiring: (a) its Master
destination resolves to an active `RigBody`/`RigArms`/`RigLegs` root that is itself visible; (b) **at least
two other** visible, rig-owned `DmeTransformControl` peers independently resolve to the exact same Master
destination. `rig_hand_L`'s own real destination root is `RigArms` (visible, untouched by this edit); its
own real siblings at the same destination, `rig_collar_L` and `rig_elbow_L`, remain visible and correctly
placed (this edit touches only `rig_hand_L`) — **exactly two** corroborating peers, satisfying the `>= 2`
requirement. This gate exists to prevent over-eager relocation of controls hidden for unrelated, legitimate
reasons with no independent corroborating evidence; it is not a general exclusion, and it does not skip
`rig_hand_L`, preserve its Hidden membership, or exclude it from discovery/composer. Discovery
(`discover_rig_context()`/`capture_tree()`) does not filter by visibility at all — it walks the full group
tree regardless of any group's own visible state, confirmed by direct reading of `capture_tree()` itself
(no `is_visible` check gates whether a group or its controls are walked/recorded).

### Q3: For shot3/foxmccouldwm1/rig_hand_L, is the authoritative normalized destination still unequivocally RigArms/LeftArm with the established exact order?

**Yes.** Both the ordinary path (`MASTER_PLUS_ACTIVE_RIG_COUNTERPART`) and the special hidden-control path
(`PRE_HIDDEN_MASTER_ACTIVE+...`) compute `target_path` via the identical
`_active_rig_counterpart_destination()` call. The final exact-order convergence step (module docstring
point 2: "once final contextual destinations are resolved... order that cohort by current Master
direct-control order") applies uniformly afterward, regardless of which authority label a given control
carried. The real, preserved evidence already cited from F1-2's own command-1 production log
(`PRODUCTION_DESTINATION_DIRECT_ORDER_AUTHORITIES` for `RigArms/LeftArm`,
`authority=EXACT_MASTER_DESTINATION_TOTAL_ORDER`, order `(rig_collar_L, rig_elbow_L, rig_hand_L)`) remains
the correct expected post-Stage-2 state.

## Why this edit still satisfies every stated requirement

- **Same existing model/vocabulary; no inventory change; no new model-support question**: unchanged from
  the original justification — only the relocation *mechanism* changed, not the control, target, or model.
- **Deterministic**: the destination computation is identical regardless of the hidden-control safety gate;
  the gate's own preconditions are satisfied by real, already-established facts about this exact target.
- **Small**: exactly one control, one real, supported SFM operation (the DAG "move to hidden group"
  command).
- **Visibly/semantically meaningful, and a real supported operation**: hiding a control via SFM's own
  first-party mechanism, then expecting the Normalizer to restore it to its Master-defined location on
  next use, is a genuine, real workflow — arguably more representative of actual product usage than an
  arbitrary drag-and-drop, since "move to hidden group" is a real, shipped, commonly-used SFM utility.
- **Creates a state the existing Normalizer is expected to repair**: confirmed directly above, not assumed
  — the Normalizer's own "PRE-hidden Master-active repair" logic exists specifically for this case.
  **This is used because it is the actual supported SFM relocation mechanism available to the operator, not
  an arbitrary or invented perturbation.**
- **Expected post-Stage-2 state is mechanically testable**: unchanged — `capture_tree()` +
  `one_membership()`, applied to exactly this one target's own root control group, gives an exact,
  single-value group path for `rig_hand_L`.
