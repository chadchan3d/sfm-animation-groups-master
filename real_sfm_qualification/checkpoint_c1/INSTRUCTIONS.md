# Checkpoint C1-2 — Baseline (Pre-Integration) Selected-Shots Run (corrected)

## CORRECTION NOTICE (2026-09-22)

Your C1-1 run correctly detected a fixture mismatch (the live selected shot had changed to `shot6`,
not `shot3`) but then continued into the mutating baseline run anyway. Independent review found three
concrete harness defects, all now fixed in this corrected script (SHA-256 changed):

1. **Fixture mismatch now hard-gates before any mutation.** If the live selection/project does not
   exactly match the B-2 witness, the script raises and writes its report **before** ever executing a
   byte of the historical baseline. No "continue for evidence."
2. **The semantic comparator no longer produces a guaranteed false positive.** `capture_snapshot_
   explicit`'s own `"label"` field (`"PRE"` vs `"POST"`) is now stripped before comparison — a prior
   version compared it directly, so every captured target necessarily differed on that one field alone
   regardless of any real change. (Diagnostic finding from C1-1, preserved: after excluding `label`,
   all 82 captured peer fingerprints in that run were semantically identical before and after — C1-1
   is not evidence the historical baseline broadly mutated 82 peers.)
3. **All 85 eligible targets are now fingerprinted**, not just the peer subset — both expected-Selected
   targets and all 83 untouched peers.

C1-1's result is preserved permanently in the ledger as a FAIL, not overwritten. The historical
baseline, production Normalizer, and canonical Master identities were all confirmed unchanged
throughout C1-1 and remain unchanged now — only this harness script was wrong.

## THIS CHECKPOINT MUTATES THE SCENE

Unlike Checkpoints A and B, C1 **does** mutate the disposable qualification project. It invokes the
exact historical, pre-integration frozen Normalizer's own real Selected Shots behavior, unmodified.

**Do not save afterward.**

## 1. Exact historical baseline — source and SHA proof

Required SHA-256: `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`

Five independent, byte-identical copies were located across separate prior work sessions and each
independently hashed — all five matched the required SHA-256 exactly:

- `C:\Users\Eman\Documents\Codex\2026-09-07\files-pasted-by-the-user-use\work\round2_evidence\01_CURRENT_SOURCE\Rebuild_Control_Groups_Normalizer.py`
- `C:\Users\Eman\Documents\Codex\2026-09-07\review-x20-3\work\mechanics_v3_1\...\05_HOST_AND_LEGACY_REFERENCE\Rebuild_Control_Groups_Normalizer_KnownWorking_MAINMENU.py`
- `C:\Users\Eman\Documents\Codex\2026-09-07\review-x20-3\work\post_r10c\...\07_PROTOTYPE_AND_REFERENCE\Rebuild_Control_Groups_Normalizer.py`
- `C:\Users\Eman\Documents\Codex\2026-09-07\review-x20-3\work\review\Astra_Character_Preset_Review\04_Rebuild_Control_Groups_Normalizer_Known_Working_MAINMENU.py`
- `C:\Users\Eman\Documents\Codex\2026-09-07\review-x20-3\work\round3_sidecar\02_CURRENT_PRODUCTION_REFERENCE\Rebuild_Control_Groups_Normalizer.py` (used as the canonical source for deployment)

No reconstruction, patching, or approximation was used — the deployed baseline is a direct copy of
one of these five independently-verified, byte-identical historical files.

## 2. Baseline isolation

The historical baseline source is deployed at:

`usermod\scripts\sfm\mainmenu\ChadChan3D\_qualification_baseline_source\Rebuild_Control_Groups_Normalizer_PRE_INTEGRATION_BASELINE.py.txt`

Deliberately in a **subdirectory**, with a **non-`.py` extension** (`.py.txt`) — this guarantees it is
never auto-discovered as its own separate, ungated MAINMENU menu entry (which would let it be run
directly, with no pre-flight checks and no fingerprint capture around it). It is never imported as a
Python module and never occupies any `sys.modules` name the production Normalizer or the accepted
authority package uses. The C1 wrapper script reads its bytes, verifies the SHA-256 above, and
`exec()`s it into its own fresh, isolated namespace dictionary — functionally identical to how SFM's
own MAINMENU system already runs any top-level script file, and distinguishable from the installed
production Normorializer by nothing more than which bytes were executed. The historical source itself
is never modified in any way — same bytes, same behavior, same real interactive dialog it always had.
Module-identity collision is not a practical risk here: the historical baseline predates and contains
zero references to `sfm_master_authority_productionized` (it uses only its own original
`parse_targeted_master()`), so there is no shared singleton/package state between the baseline and
the integrated package to collide with in the first place.

## 3. What C1 actually does (non-interactive parts)

1. Verifies the historical baseline's SHA-256 (above).
2. Verifies the **installed production Normalizer has not been replaced**
   (`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`) — read-only; it is never
   imported or executed by this checkpoint.
3. Verifies the canonical Master's SHA-256 (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
4. Independently re-derives the Checkpoint-B-style fixture witness fresh from the live document and
   cross-checks it against the exact B-2 totals (15 shots, 163 targets, 85 eligible, 78 excluded, 2
   expected-Selected candidates, 83 untouched peers, 22 distinct models, 21 distinct vocabulary
   hashes), the two named selected-shot targets' model names/control counts/vocabulary hashes, and a
   name-based (session-stable) selected-shot-set check. **If any of these checks fails, the script
   raises and writes its report here — it never proceeds to step 5 or beyond.** (Note: Checkpoint B's
   own JSON `selected_shot_set_hash` field is computed from process-local native-pointer identities,
   which are reassigned fresh on every SFM launch, so it cannot be bit-for-bit reproduced in this
   separate session by construction — a genuine, newly-discovered latent gap in that specific B field,
   not something fixable from inside C1. This checkpoint's own gate uses a name-based hash instead,
   which achieves the same fixture-identity assurance and is session-stable.)
5. Only if every fixture check passes: captures a **structural PRE fingerprint of all 85 eligible
   targets** (both `shot3/foxmccouldwm1` and `shot3/mia1`, AND all 83 independently-witnessed
   untouched peers — never just a subset) using the accepted Normalizer's own already-qualified,
   purely read-only `capture_snapshot_explicit()`/`capture_tree()`/`discover_rig_context()` functions
   — extracted verbatim (34 function/class definitions, exact line ranges, reusing the SAME
   already-proven range table `candidate_b2c_c/production_plan_layer.py` already uses and has run
   55/55 PASS against this exact file) from the **currently installed** Normalizer file. These
   functions are byte-identical in both the historical and integrated code paths (the Production
   Normalizer Integration work never touched them) — they are the neutral structural-reading
   mechanism, not the scope/mutation-outcome difference this checkpoint exists to observe. Before
   comparison, each captured snapshot is canonicalized: the `"label"` field (`"PRE"`/`"POST"`) and
   process-local handle integers are stripped, so only real semantic state is ever compared.

## 4. What C1 needs from you (the interactive part)

After the PRE fingerprint is captured, the script executes the historical baseline source. This
triggers the historical code's own real, completely unmodified "choose scope" dialog.

**When that dialog appears: select "Selected Shots" and confirm.** Do not modify or work around this
dialog in any way — it is the real, original product behavior, and part of exactly what this
checkpoint is qualifying.

The script then waits (by pumping SFM's own Qt event loop and watching for the historical run's own
completion signal, never inventing a new synchronization mechanism) for the real, asynchronous,
multi-callback historical operation to actually finish, before capturing the POST fingerprint and
writing its report. **Do not interact with SFM while it's running** — let it complete on its own.

## Exact project to open, and required selection state

Open the **exact same disposable qualification project used for Checkpoint B-2**. Before running this
script, make sure **`shot3` is the only selected shot** in the Clip Editor (matching the B-2 witness
this checkpoint verifies against). If your project or selection has changed since B-2, the script will
mechanically detect and report the mismatch rather than silently proceeding.

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the same disposable qualification project used for B-2.
4. Select `shot3` in the Clip Editor (and only `shot3`).
5. Run **`Checkpoint_C1_Baseline_Selected_Shots`**, the same way as the earlier checkpoints.
6. **A real dialog will appear.** Select **"Selected Shots"** and confirm. Give it generous time to
   run — 85 targets' worth of structural capture plus the real historical operation itself.
7. Do not touch SFM again until the console output shows the final summary and the
   "DO NOT SAVE. Restart SFM..." message.
8. Return the exact contents of **both** output files:
   - `C:\Users\Public\Documents\sfm_checkpoint_c1_baseline_result_summary.txt`
   - `C:\Users\Public\Documents\sfm_checkpoint_c1_baseline_result.json`

   Also tell me about any error dialog or console traceback beyond what's in those files.
9. **DO NOT SAVE. Restart SFM to discard the baseline mutation before C2.**

## Output artifact paths

- `C:\Users\Public\Documents\sfm_checkpoint_c1_baseline_result.json` (full detail — every check,
  every anomaly, both fingerprints, touched-target list)
- `C:\Users\Public\Documents\sfm_checkpoint_c1_baseline_result_summary.txt` (concise, read this first)

## Mechanical C1 PASS/FAIL criteria (decided before execution)

`OVERALL_PASS` in the report requires **all** of:

- exact historical SHA verified;
- production Normalizer SHA still installed (unreplaced);
- canonical Master SHA unchanged;
- fixture identity matches the B-2 witness exactly (totals, selected-shot-set name check, selected-shot
  targets, untouched-peer count) — **a mismatch here means the script already stopped; no mutation
  occurred, and none of the checks below apply**;
- PRE capture completes for all 85 eligible targets;
- the historical run was actually started (dialog was confirmed with Selected Shots, not cancelled)
  and completed within the wait timeout;
- POST capture completes for all 85 eligible targets;
- the SEMANTIC (label/handle-stripped) touched-target set exactly equals
  `{shot3/foxmccouldwm1, shot3/mia1}` — no more, no less;
- none of the 83 untouched peers show any semantic fingerprint change;
- the script completes without an unhandled exception.

If the report shows `"gate_failure": true`, that means the fixture check itself failed and the script
correctly stopped before touching anything — re-verify the project/selection and rerun, rather than
treating it as a script bug.

This checkpoint does **not** decide baseline-vs-integrated equivalence — C2 has not run yet. It only
establishes that the historical run itself behaved as the historical product always has, against the
independently-witnessed expected scope.

## Source review: production Normalizer is never overwritten

Direct grep of the C1 script for every file-write and every reference to the installed production
Normalizer's path confirms it is opened exactly once, in `"rb"` (read-only) mode, purely to compute
its SHA-256 for the "has it been replaced" check. There is no code path anywhere in this script that
opens that path for writing, and `Rebuild_Control_Groups_Normalizer.py` is never imported. The only
two `"wb"` (write) operations in the entire script are the two report files listed above. The
canonical Master is likewise opened only `"rb"`, once, for its own SHA-256 check. The accepted
authority package (`sfm_master_authority_productionized`) is never imported or referenced anywhere in
this script.

## Offline verification already performed

Before this first deployment: (1) all 34 extraction ranges were confirmed to each start with the exact
expected `def`/`class` line; (2) the combined extracted source was `exec()`'d under real Python 2.7.5
and every expected function name (`capture_snapshot_explicit`, `discover_rig_context`, `capture_tree`,
`native_ptr`, `name`, `handle`, `typ`, `arr`, `attr`, `scalar`) was confirmed present and callable;
(3) `capture_snapshot_explicit` was functionally exercised end-to-end against a synthetic fake
shot/animation-set/two-level-group-tree/two-control fixture and correctly returned the expected
group count (2), correct recursive group names (`<ROOT>`, `ChildGroup`), and correct control-to-group
membership mapping.

Before this corrected (C1-2) deployment, additionally: (4) a new offline regression,
`real_sfm_qualification/checkpoint_c1/test_c1_semantic_comparator_regression.py`, extracts the deployed
script's own `canonicalize_snapshot` function verbatim (SHA-256 pinned) and proves two otherwise-
identical fingerprints tagged `PRE`/`POST` compare EQUAL after canonicalization, and a real semantic
change (a renamed control inside the group tree) still compares UNEQUAL — **8/8 PASS, both Python 3.10
and real Python 2.7.5**; (5) the fixture-identity hard gate was dry-run against a synthetic fixture
reproducing the EXACT C1-1 mismatch (a different shot selected than expected) and confirmed to
correctly compute failure in that case, and success when the correct shot is selected.

## Identities this checkpoint is pinned against

- Historical baseline SHA-256: `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`
- Installed production Normalizer SHA-256 (must remain unreplaced):
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- C1-2 (corrected) script SHA-256: `4387b03de820ae05e6647d68d22bb2bc084b1bf3ae4c78cbb060dddc412219dc`
  (C1-1's superseded script SHA-256, preserved for the record: `bebdd1c384e292fd11c42f57a3bfd57b08a2528db2fcfe16c0eb58d6465a8aa6`)
