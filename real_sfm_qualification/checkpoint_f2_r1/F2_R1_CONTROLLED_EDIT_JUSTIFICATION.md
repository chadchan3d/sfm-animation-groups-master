# F2-R1 Controlled Edit — Justification

The controlled edit is derived from an already-qualified target, not invented. Every fact below is
cited directly from a real, preserved production artifact already accepted into this project's own
evidence trail — never guessed or assumed.

## Exact edit

| Field | Value |
|---|---|
| Shot | `shot3` |
| Animation set / target | `foxmccouldwm1` |
| Control affected | `rig_hand_L` |
| Initial qualified state | Direct member of group `RigArms/LeftArm` |
| Operator mutation | Move `rig_hand_L`, using SFM's own ordinary Animation Set Editor UI, out of `RigArms/LeftArm` and into the existing `RigHelpers` group |
| Expected normalized state after command 2 | `rig_hand_L` back in `RigArms/LeftArm`; `RigArms/LeftArm`'s own direct-control order restored to exactly `(rig_collar_L, rig_elbow_L, rig_hand_L)` |

## Why this is already qualified, not invented

Cited directly from `C:\Users\Public\Documents\sfm_checkpoint_f1_2_production_log_command1.txt` (the
real, preserved production log from F1-2's own command 1 — a Selected-Shots run against exactly
`shot3`), line 111:

```
PRODUCTION_DESTINATION_DIRECT_ORDER_AUTHORITIES target=(u'shot3', u'foxmccouldwm1') rows={
  u'RigArms/LeftArm': {'order': (u'rig_collar_L', u'rig_elbow_L', u'rig_hand_L'), 'authority': 'EXACT_MASTER_DESTINATION_TOTAL_ORDER'},
  ...
}
```

`authority: 'EXACT_MASTER_DESTINATION_TOTAL_ORDER'` means the canonical Master itself defines the
complete, deterministic ordering of `RigArms/LeftArm`'s own direct controls for this target — production
enforces this order every time it runs, regardless of the controls' prior positions. This is why the
expected post-command-2 state is not a guess: it is the same deterministic destination production has
already been observed, in this exact real log, to produce for this exact target.

The same log's own root order line (line 110) confirms `RigHelpers` is a real, already-existing group in
this exact target's own tree (`order=[..., u'RigBody', u'RigArms', u'RigLegs', u'RigHelpers', u'Attachments']`),
so the operator's mutation moves the control into a real, pre-existing group — never a newly-invented one.

`foxmccouldwm1` is one of the two targets (with `mia1`) that this entire project's own qualification
history has exercised more than any other real target — `C1-1`/`C1-2`/`C2-1` (Selected-Shots baseline and
integrated equivalence), `F1-1`/`F1-R1`/`F1-2` (repeated-use stability), all specifically selected `shot3`
and normalized exactly these two targets, repeatedly, with hash-level verification. `rig_hand_L` is part
of the real, already-eligible, already-model-backed control inventory for this target (confirmed by its
own `PRE rig status=SUPPORTED_ACTIVE_RIG controls=208...` capture in the same log) — moving it is not an
inventory change, does not introduce a new model, and does not raise any new model-support question.

## Why this edit satisfies every stated requirement

- **Same existing model/vocabulary**: `rig_hand_L` is an existing, already-classified control on an
  already-qualified target; nothing about the model or its control vocabulary changes.
- **No inventory change**: the control is not added or removed, only its group membership changes.
- **No new model-support question**: `foxmccouldwm1`'s own model-backed/eligible status is unaffected.
- **Deterministic**: `EXACT_MASTER_DESTINATION_TOTAL_ORDER` authority means the corrected destination and
  order are fixed facts, not probabilistic outcomes.
- **Small**: exactly one control, one group membership change.
- **Visibly/semantically meaningful**: a hand control sitting in `RigHelpers` instead of `RigArms/LeftArm`
  is a real, recognizable authoring mistake of the exact kind this tool exists to correct — not an
  artificial/contrived perturbation.
- **Creates a state the existing Normalizer is expected to repair**: production's own composer logic
  (`PRODUCTION_GENERIC_RIG_DESTINATION_AUTHORITIES`, `MASTER_PLUS_ACTIVE_RIG_COUNTERPART` authority for
  `rig_hand_L`) is specifically designed to detect and relocate misplaced rig-authority controls back to
  their Master-defined destination.
- **Expected post-command-2 state is mechanically testable**: `capture_tree(aset.GetRootControlGroup())`
  (production's own function, reused verbatim, applied only to this one target's own tree) plus
  `one_membership()` (also reused verbatim) gives an exact, single-value group path for `rig_hand_L`, and
  the exact expected `RigArms/LeftArm` order is already known from the citation above.
