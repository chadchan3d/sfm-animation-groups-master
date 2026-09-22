# Checkpoint B — Independent Real-Project Inventory

## What this checkpoint proves

Whether the test project you use for later Selected/All Shots comparisons is actually a sufficient,
well-formed mixed fixture — inventoried completely independently of the Normalizer's own scope/
eligibility logic, so it can later serve as an unbiased witness. This checkpoint does not run the
Normalizer, does not touch the shared-authority package, and does not read the Master TXT at all.

## Does this test mutate the scene?

**No.** Zero scene mutation, zero native Rebuild, zero authority-generation replacement, zero Master
modification, zero save. The script never imports `vs`, never touches `vs.g_pDataModel`, never calls
any dialog (it does **not** invoke the existing "choose scope" popup), and never alters the Clip
Editor selection. A source review confirming this is at the bottom of this document.

## Should you save anything?

**No. Do not save the SFM project after running this script.**

## Exact project to open

Open (or continue using) a **real, disposable/mutable qualification project** — never your only copy
of anything important. It needs enough real variation to eventually support the planned Selected
Shots / All Shots comparisons:

- multiple shots (2 or more);
- multiple eligible, model-backed animation sets (2 or more) — "eligible" here means: has a real game
  model attached, has a valid root control group, and is not a duplicate reference;
- at least one target you expect a rebuild-type operation to actually act on;
- at least one peer target that should remain untouched during a Selected-Shots-scoped run;
- ideally two animation sets whose models/rigs are **materially different** from each other (different
  control vocabularies) — this is preferred, not required, for later warm/later-model testing.

**If the project you currently have open does not satisfy this, that is fine — run the script anyway.**
It mechanically reports exactly which requirement is unmet rather than guessing, and I will act on
that report rather than have you force the project into shape by hand.

## Required selection state

**None required.** This script faithfully records whatever Clip Editor selection currently exists —
including nothing selected at all — as an independent fact, and does not require or set up any
particular selection itself. If you already know you'll want a specific subset of shots selected for
a later Selected-Shots test, you're welcome to set that now (having at least one, but not all, shots
selected makes this checkpoint's own report more informative), but it is not necessary to run
Checkpoint B itself.

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Start SFM and open your disposable qualification project (per "Exact project to open" above).
4. Optionally: select some (not all) shots in the Clip Editor if you already have a plan for later
   Selected-Shots testing. Not required.
5. Run the script named **`Checkpoint_B_Independent_Inventory`**, the same way you ran
   `Checkpoint_A_Bootstrap_Smoke_Test` before (same menu location, same click-to-run action). It has
   been placed in the same folder:
   `usermod\scripts\sfm\mainmenu\ChadChan3D\Checkpoint_B_Independent_Inventory.py`
6. Wait for it to finish. Give it generous time — depending on project size this may take longer than
   Checkpoint A, since it walks every shot/animation-set/control in the document (still read-only,
   no native calls).
7. Return the exact contents of **both** of these files:
   - `C:\Users\Public\Documents\sfm_checkpoint_b_inventory_summary.txt` (concise, read this one first)
   - `C:\Users\Public\Documents\sfm_checkpoint_b_inventory.json` (full detail — I will need this to
     assess sufficiency and to use later as the comparison witness)

   Also tell me whether SFM showed any error dialog or console traceback beyond what is in those
   files.
8. Don't save. Restart SFM again before any later checkpoint.

## Mechanical PASS/FAIL criteria (decided before execution)

The script itself computes and reports `OVERALL_PASS` in both output files — you do not need to
interpret anything, just return the files. For reference, it requires **all** of the following
(each individually reported as `[PASS]`/`[FAIL]` in the summary file):

- `multiple_shots (>=2)`
- `multiple_eligible_targets (>=2)`
- `at_least_one_target_expected_processed (eligible>=1)`
- `at_least_one_expected_selected_candidate (>=1)`
- `at_least_one_untouched_peer (>=1)`
- `no_duplicate_or_unsupported_targets (excluded via duplicates/unsupported == 0)`
- the script completes without an unhandled exception
- (reported but **not** required for PASS: `preferred_two_distinct_vocabularies (>=2)`)

If any required item is `[FAIL]`, `OVERALL_PASS` will be `False` — this most likely means the current
project needs a different/larger fixture before Checkpoint C, not that anything is broken. Return the
files regardless; I will determine the right next step from the exact report rather than guess.

## Identities this checkpoint is pinned against

- Accepted integration commit: `68f1188e7dcb3fdd34d384396bf5d7a14acf7d25`
- Production Normalizer SHA-256 (not read by this script, cited for context only):
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Checkpoint B script SHA-256: `5d2782bd0fc5ca0734244c4bff3338715510795775fdc4f515e5d6ae5141e528`

## Why this witness is independent, not circular

This script never imports `Rebuild_Control_Groups_Normalizer.py` and never calls any of its
scope-resolution/eligibility/classification functions (`_choose_scope`, `_resolve_selected_scope`,
`snapshot_work`, `_gate_is_alh`, `classify_production`). It reads the same underlying real SFM APIs
the Normalizer also happens to read (`sfmApp.GetShots()`, `sfmClipEditor.GetSelectedShots()`,
`shot.animationSets`, `aset.GetAttribute(...)`, `aset.GetRootControlGroup()`,
`control.GetTypeString()`) — there is only one real way to ask SFM these questions — and reproduces
a small number of the Normalizer's own already-qualified, purely structural DME-reading helpers
(`native_ptr`, `to_unicode`, `ascii_fold`, `name`, `typ`, `attr`, `scalar`, `arr`, plus the same
neutral "does this animation set have a real game model with a resolvable pointer" and "is this
control a `DmeTransformControl`" checks `get_game_model`/`_gate_get_model_name`/
`_gate_transform_controls` already perform) because these are structural reading primitives, not
scope or eligibility POLICY — none of them decide what belongs in any scope. All classification
(`excluded` / `expected_selected_and_all_candidate` / `untouched_peer_eligible_all_only` /
`unsupported_unknown`) is computed independently in this script's own code, never borrowed from the
Normalizer's decision logic.

One classification is deliberately **not** attempted: whether a target's rig counts as a Master-
vocabulary "supported active rig" (the Normalizer's own `_gate_is_alh`, which requires cross-
referencing live Master data). Every target's report row is marked
`"rig_support_classification": "UNRESOLVED (requires Master-authority lookup; out of this
checkpoint's independent-witness scope)"` rather than guessed at.

## Source review: why this script cannot mutate anything

Direct grep of the deployed script for every write/mutation-shaped call found exactly the two
report-file writes and the `sys.stdout.write` calls used to print the summary — nothing else. No
`SetVisible`/`AddControl`/`CreateControlGroup`/`RemoveChild`/`AddChild`/`SetUndoEnabled`/`.rebuild(`
call appears anywhere in the file. `vs` is never imported. No `Save`/`SaveAs`-family call appears
anywhere. No `.exec_()` (dialog invocation) appears anywhere — the existing "choose scope" popup is
never triggered. The frozen production Normalizer is never imported, read, or referenced.

## Offline verification already performed (before handing this to the operator)

Before deployment, this script's own classification/hashing/aggregation logic was dry-run offline
(never touching real SFM) against synthetic fake shot/animation-set/model/control objects covering:
a mixed fixture (2 eligible targets with materially different control vocabularies, one selected,
one not, plus 2 structurally-ineligible targets) — produced the expected `expected_selected_and_all_
candidate` / `untouched_peer_eligible_all_only` / `excluded` classifications and `OVERALL_PASS=True`;
a duplicate animation-set reference across two shots — correctly flagged as an anomaly and correctly
failed the `no_duplicate...` sufficiency check; and a no-document-open scenario — completed without
exception, reported `document_has_content=False` and `OVERALL_PASS=False` with a clear anomaly
message, rather than crashing.
