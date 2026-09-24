# Checkpoint F1-R3 — Native-Only Retention Attribution

## Purpose

F1-R2 established `PASS` as an attribution checkpoint: the reopened normalized copy did **not** retain
the prior run's large memory increase (serialized-resident deltas were small and negative), but a second
All-Shots production run against that same normalized scene reproduced essentially the same process-
retained pressure (~+265 MiB private / ~-238 MiB free VAS / ~-111 MiB largest free block). This
establishes **per-run process-retained pressure**, but not its internal owner. F1-R3 answers exactly one
question:

> On the same normalized scene, in a fresh process, how much of that retained pressure occurs when we
> execute only the same native Rebuild work across the same 62 production-eligible targets, in the same
> order, without the contextual reconciliation/composer/capture workload?

This is a measurement checkpoint. It does not reopen O3 and does not implement or authorize any
optimization. See `F1_R3_NATIVE_PATH_AUDIT.md` for the full static audit this design is built from.

**This checkpoint mutates the scene** (native Rebuild runs for real, exactly as production does). **Do not
save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only**:
   `E:\SourceFilmmaker Sessions\F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
   — never the original `testscripts.dmx`. The script structurally refuses to proceed if the currently
   open document's own filename does not match this exact name (case-insensitive), and explicitly
   detects and refuses the original fixture's own filename as an extra safeguard.
4. Run `Checkpoint_F1_R3_Native_Only_Retention_Attribution`.
5. Choose **All Shots** in the real dialog that appears (this is the same scope the production
   eligibility gate was measured against: 15 shots, 85 model-backed targets, 62 eligible for native
   Rebuild after gate skips).
6. Wait for completion. The script processes exactly 62 targets, in production's own exact order, calling
   only native Rebuild for each — no composer, no capture, no semantic verification.
7. Return the three output files (see below).
8. **DO NOT SAVE.**
9. **Fully restart SFM afterward.**

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r3_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r3_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r3_native_only_log.txt`

## What this run does NOT do

- Does not run contextual classification, policy planning, or the composer.
- Does not perform PRE/POST/composer-before/composer-after/terminal semantic captures.
- Does not perform the whole-session identity census/deep-verification layers, or the final exhaustive
  85-eligible/78-excluded semantic verifier.
- Does not reopen or touch O3, and does not implement any caching, reuse, or shortcut.
- Does not save the scene.

## Static native-path findings (summary; full audit in `F1_R3_NATIVE_PATH_AUDIT.md`)

Every genuinely-required guard around the native call is reused directly from the real, already-
initialized production run instance's own methods — never reimplemented: pointer-stability check,
`get_game_model`/`get_root_group` validity, `dm.SetUndoEnabled(False)` (Undo must be off during the native
call, matching production's own "entire per-target transaction is non-undoable" policy) + restore,
`native_master_protect_acquire`/`release` (Master-file protection is part of the invocation), and
`assert_master_stable()`. Shot activation (`sfmApp.SetHeadTimeInSeconds` + immediate
`GetShotAtCurrentTime` verification) is genuinely required, not contextualizer-only — SFM's own native
Rebuild implicitly operates against the currently-active shot. The real run instance's own further
progression is neutralized by setting `instance.finished = True` immediately after locating it and before
ever pumping the Qt event loop — every state-machine method on the real instance begins `if self.finished:
return` (verified by direct reading), so this permanently and safely prevents production's own contextual
pipeline from ever running, without any monkey-patch. The one deliberate, narrow deviation: target
re-resolution for the second-or-later target in a multi-target shot reuses the same core matching logic as
`instance.contextualizer_resolve_resume_target()`, omitting only its `production_terminal_results`
membership check (which verifies a fact — prior terminal capture completion — that only exists once
production's own fuller pipeline has run, which this checkpoint deliberately never does).

## Expected ordered target count and checksum

Expected count: **62** (85 model-backed − 23 gate skips: static=12, follower=4, low-bone/no-ALH=7,
fail-closed-process=0 — verified against a real preserved production log,
`checkpoint_f1/f1_1_crash_evidence/sfm_rebuild_control_groups_F1-1_command3_crash.txt`, not assumed). The
script emits `provenance.ordered_sequence_checksum_sha256` — a SHA-256 over the JSON-serialized, **order-
preserving** list of `(shot_name, target_name)` pairs exactly as `instance.work` orders them — so the
processed sequence can be compared mechanically against any other run's own sequence over the same
fixture. This checkpoint does not hard-code the expected checksum value itself (the exact 62 target names
were not independently enumerated ahead of the real run), only the expected **count** and the exact gate-
skip breakdown; the emitted checksum is for cross-run comparison, not a pre-declared pass/fail gate.

## Mechanical PASS / FAIL / INCOMPLETE

**PASS** requires: correct production Normalizer/canonical Master SHA-256; correct normalized-copy
fixture filename (and confirmed refusal of the original fixture's filename); the real run instance located
and neutralized before any event pump; `instance.work` present with exactly 15 shots and exactly 62
eligible targets; gate-skip counts (static/follower/lowbone/failclosed) matching the verified expected
values; all 62 native Rebuild calls complete; `instance.total_shots_processed == 0` (proving production's
own real pipeline never advanced); before/after/post-GC resource checkpoints all captured; zero anomalies.

**FAIL** if: the target sequence's own count differs from 62; any native guard or the native call itself
raises; the run aborts; a resource measurement endpoint is unavailable.

**INCOMPLETE** if: the production-equivalent native-only invocation cannot be isolated safely (e.g. the
real instance could not be located, or its `work` attribute is empty/absent); fixture/provenance cannot be
proven; the measurement is contaminated by an unexpectedly heavyweight step.

The later attribution label (`NATIVE_DOMINANT` / `CONTEXTUAL_LAYER_MATERIAL` / `MIXED` / `UNRESOLVED`) is
analyst-applied from the raw reported numbers after the real run — the script does not compute or embed
this verdict itself, and does not claim exact causation beyond what this matched control establishes.

## Reported quantities

Raw: `native_private_delta`, `native_free_vas_delta`, `native_largest_free_delta`,
`native_working_set_delta`, `postgc_private_delta`, `postgc_free_vas_delta`,
`postgc_largest_free_delta`. Ratios (informational only, not a verdict): `native_private_ratio`,
`native_free_vas_loss_ratio`, `native_largest_free_loss_ratio`, each computed against F1-R2 Phase 2's own
established production baseline (`private_delta=+265,461,760`, `free_vas_delta=-237,633,536`,
`largest_free_delta=-110,985,216`).

## Offline verification performed before deployment

(1) Script syntax-checked under the real embedded Python 2.7.5, PASS. (2) `test_f1_r3_diagnostic_
regression.py` (SHA-256 `3e342e24b191718f162f94a0fb62800802815e7d3c6dbbbba6b2c9b321f64f17`) verifies: the
exact gate-skip counts and shot/target totals against a real preserved production log (not invented); the
ordered-sequence checksum is deterministic and order-sensitive (reordering the same pairs produces a
different checksum); the shared resource-checkpoint parser and atomic writers (verbatim reused from every
earlier checkpoint) behave correctly; `native_only_resolve_target()` (extracted verbatim from the deployed
script) correctly finds the unique match and correctly raises on shot-context mismatch or zero matches;
`native_only_rebuild_target()` (extracted verbatim) correctly sequences Undo-disable/Master-protection-
acquire/`assert_master_stable`/the native call/protection-release/Undo-restore, correctly raises before
any native call on a pointer-stability, model-backing, or root-group failure, and correctly passes the
native `ctypes.c_void_p`-wrapped pointer; resource-delta and ratio arithmetic verified against a worked
example; static checks on the deployed script's own source confirm it contains no call to `SaveToFile`,
`discover_rig_context`, `capture_snapshot_explicit`, `production_generic_composer`, or
`preflight_reconciliation_plan`, and that the real instance is neutralized (`instance.finished = True`)
strictly before `instance.work` is ever read. **54/54 PASS** under the real embedded Python 2.7.5. Not yet
run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R3 script SHA-256: `c3b3098dfdd737899a6c1a9cbec3fd8d552db0423ca7fad35693dcdc8f9195c6`
- F1-R3 offline regression SHA-256: `3e342e24b191718f162f94a0fb62800802815e7d3c6dbbbba6b2c9b321f64f17`
- F1-R2 Phase 2 production baseline (for ratio reporting only): private `+265,461,760`, free VAS
  `-237,633,536`, largest free block `-110,985,216`
