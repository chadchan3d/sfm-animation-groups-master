# Checkpoint C2-1 — Integrated (Post-Integration) Selected-Shots Run

## THIS CHECKPOINT MUTATES THE SCENE

Unlike Checkpoints A and B, C2 **does** mutate the disposable qualification project. It invokes the
REAL, INSTALLED, ACCEPTED, INTEGRATED production Normalizer — the exact file at
`usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py`, never a copy, never the
historical baseline C1 used — running its own real Selected Shots behavior, unmodified.

**Do not save afterward.**

## Purpose

Mechanically prove the integrated (post-Production-Normalizer-Integration) Selected-Shots outcome is
semantically equivalent to Checkpoint C1-2's own already-accepted historical baseline outcome — not
merely "close", but equivalent on a per-target basis for every one of the 85 independently-witnessed
eligible targets. C2 never re-derives its own notion of "expected" from scratch: it loads C1-2's own
accepted machine-readable result artifact from disk and compares directly against it.

## 1. What C2 actually does (non-interactive parts)

1. Verifies the SHA-256 of the file it is **about to execute** —
   `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867` — the accepted, installed,
   integrated production Normalizer. (Unlike C1, which only fingerprinted with this file's functions
   but executed a *separate* historical file, C2 executes this exact file.)
2. Verifies the canonical Master's SHA-256 (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
3. Loads `C:\Users\Public\Documents\sfm_checkpoint_c1_baseline_result.json` (C1-2's own accepted
   result artifact) and integrity-checks it: `overall_pass` must be `True`, and its own
   `pre_fingerprint_hash`/`post_fingerprint_hash` fields must equal the pinned accepted values
   (`eac633c9...`/`d7b3bacb...`) before it is trusted as ground truth for any later comparison.
4. Independently re-derives the Checkpoint-B-style fixture witness fresh from the live document and
   cross-checks it against the exact B-2 totals — the same fixture C1 required.
5. Only if every check above passes: captures a **structural PRE fingerprint of all 85 eligible
   targets** using the same already-qualified `capture_snapshot_explicit()`/`capture_tree()`/
   `discover_rig_context()` functions, extracted verbatim from THIS run's own production Normalizer
   file (same range table C1 used, since it is the same underlying file).
6. **Hard gate**: in addition to every fixture-identity check, this run's own fresh integrated PRE
   fingerprint hash must equal C1-2's own accepted PRE hash exactly
   (`eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`) — this is the starting-state
   parity check (Comparison A). **If any of these checks fails, the script raises and writes its
   report here — it never invokes the production Normalizer or mutates the scene.**
7. Only if the full gate passes: executes the installed production Normalizer's own real source. Its
   own module-level `StartRebuildControlGroups()` call fires immediately, which resolves scope and
   opens the real interactive dialog.

## 2. What C2 needs from you (the interactive part)

After the PRE fingerprint is captured and the gate passes, the script executes the installed
production Normalizer. This triggers the Normalizer's own real, completely unmodified "choose scope"
dialog.

**When that dialog appears: select "Selected Shots" and confirm.** Do not modify or work around this
dialog in any way.

The script then waits (pumping SFM's own Qt event loop, watching for the Normalizer's own
`RUN_LOCK_NAME` completion signal — the same technique C1 used) for the real, asynchronous operation
to finish, before capturing the POST fingerprint, running Comparisons A-F, capturing shared-authority
and native-protection evidence, and writing its report. **Do not interact with SFM while it's
running** — let it complete on its own.

## Exact project to open, and required selection state

Open the **exact same disposable qualification project used for Checkpoint C1-2** (the same one used
for B-2). Before running this script, make sure **`shot3` is the only selected shot** in the Clip
Editor. If your project or selection has changed since C1-2 — or if the project's *state* has changed
(e.g. someone else's mutation between sessions) so that the fresh PRE fingerprint no longer matches
C1-2's own accepted PRE hash — the script will mechanically detect and report the mismatch, and abort
before touching anything, rather than silently proceeding on a starting state C2 was never meant to
qualify.

## Comparisons performed (A-F)

| | Comparison | What it checks |
|---|---|---|
| A | `starting_state_parity` | integrated PRE hash == C1's own accepted PRE hash (also the hard gate) |
| B | `scope_parity` | touched-target set (this run) == `{shot3\|foxmccouldwm1, shot3\|mia1}` == C1's own reported touched-target set |
| C | `final_state_parity` | integrated POST hash == C1's own accepted POST hash |
| D | `per_target_parity` | ALL 85 eligible targets compared **individually** (this run's canonicalized POST snapshot vs C1's own canonicalized POST snapshot) — never aggregate-hash-only, even if C already passed |
| E | `untouched_peer_parity` | for all 83 untouched peers: this run's PRE == this run's POST == C1's PRE == C1's POST (four-way, per target) |
| F | `selected_target_parity` | Fox (`foxmccouldwm1`) and Mia (`mia1`) compared individually against C1's own POST data |

Every comparison's machine-readable result is under `report["comparisons"]` in the JSON output, keyed
`A_starting_state_parity` … `F_selected_target_parity`, each with its own `"pass"` boolean and, for D/F,
per-target `"differing_fields"` detail if any target does not match.

## Shared-authority runtime evidence

Captured from the exec-exposed `authority_runtime` module binding the production Normalizer's own
source already imports at its own module scope (`RUNTIME_API_VERSION`, `RUNTIME_BUILD_ID`,
`is_canonical()`, `get_state()`), plus one additional, idempotent `authority_runtime.get_broker(...)`
call after the run to read `provider_counters()`/`outstanding_lease_count()` — this does **not**
acquire a new view or lease; it only returns the already-constructed broker singleton and reads its
own aggregate counters. No new instrumentation was added to the Normalizer or the authority package.
Recorded under `report["authority_runtime_evidence"]`.

## Native-protection / command-completion evidence

Captured by reading the production Normalizer's OWN existing log file at
`C:\Users\Public\Documents\sfm_rebuild_control_groups.txt` (its own `OUTPUT_PATH` constant), which this
exact run's own `start()` method opens in `"w"` (truncate) mode — so its content, read after this run
completes, pertains **only to this run**. The script records whether the log contains the literal
lines `"NATIVE_GUARDS = PASS"` and `"NATIVE_REBUILD_RETURNED = PASS"`. The Normalizer's own fail-closed
gate raises `ProbeError` before reaching `self.rebuild(...)` if native-handle acquisition did not
succeed, so the presence of `"NATIVE_REBUILD_RETURNED = PASS"` is proof-by-construction that native
protection was successfully acquired for this exact run — an inference from an existing qualified log,
not new instrumentation. This is explicitly **not** the dedicated native-handle coordination test (a
later checkpoint); C2 only reads this one existing log signal. Recorded under
`report["native_protection_evidence"]`.

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the same disposable qualification project used for C1-2/B-2.
4. Select `shot3` in the Clip Editor (and only `shot3`).
5. Run **`Checkpoint_C2_Integrated_Selected_Shots`**, the same way as the earlier checkpoints.
6. **A real dialog will appear.** Select **"Selected Shots"** and confirm. Give it generous time to
   run — 85 targets' worth of structural capture (twice) plus the real integrated operation itself.
7. Do not touch SFM again until the console output shows the final summary and the
   "DO NOT SAVE. Restart SFM..." message.
8. Return the exact contents of **both** output files:
   - `C:\Users\Public\Documents\sfm_checkpoint_c2_integrated_result_summary.txt`
   - `C:\Users\Public\Documents\sfm_checkpoint_c2_integrated_result.json`

   Also tell me about any error dialog or console traceback beyond what's in those files.
9. **DO NOT SAVE. Restart SFM to discard the integrated-run mutation.**

## Output artifact paths

- `C:\Users\Public\Documents\sfm_checkpoint_c2_integrated_result.json` (full detail — every check,
  every comparison A-F, both fingerprints, authority-runtime evidence, native-protection evidence)
- `C:\Users\Public\Documents\sfm_checkpoint_c2_integrated_result_summary.txt` (concise, read this first)

## Mechanical C2 PASS/FAIL criteria (decided before execution)

`OVERALL_PASS` in the report requires **all** of:

- production Normalizer SHA matches the accepted integration exactly;
- canonical Master SHA unchanged;
- the loaded C1-2 result artifact is itself a PASS and its own pinned hashes match exactly;
- fixture identity matches the B-2 witness exactly (totals, selected-shot-set name check, selected-shot
  targets, untouched-peer count, live target key set matches C1's own target key set);
- integrated PRE fingerprint hash equals C1-2's own accepted PRE hash exactly (Comparison A / the
  starting-state gate) — **a mismatch anywhere above means the script already stopped; no mutation
  occurred, and none of the checks below apply**;
- the integrated run was actually started (dialog was confirmed with Selected Shots, not cancelled)
  and completed within the wait timeout;
- POST capture completes for all 85 eligible targets;
- Comparisons B, C, D, E, F each report `"pass": true`;
- the script completes without an unhandled exception.

If the report shows `"gate_failure": true`, that means a pre-flight, C1-artifact-integrity, fixture, or
starting-state check failed and the script correctly stopped before touching anything — re-verify the
project/selection/installed files and rerun, rather than treating it as a script bug.

This checkpoint decides Selected-Shots baseline-vs-integrated equivalence. It does not test All Shots,
Undo, or the dedicated native-handle coordination scenario — those are later checkpoints.

## Source review: baseline / package / Master are never overwritten

Direct grep of the C2 script for every file-write confirms exactly two `"wb"` (write) operations in the
entire script — the two report files listed above — and no code path opens the production Normalizer,
the canonical Master, or `sfm_checkpoint_c1_baseline_result.json` for writing; each is opened exactly
once, in `"rb"` (read-only) mode. `sfm_master_authority_productionized`/`sfm_master_sidecar` are never
imported directly by this script — only read via the module bindings the production Normalizer's own
source already imports into the isolated `exec()` namespace. The historical baseline file (from
Checkpoint C1) is never referenced by this script at all.

## Offline verification already performed

Before deployment: (1) syntax-checked under the real embedded Python 2.7.5
(`sdktools\python\2.7\win32\python.exe -m py_compile`), PASS; (2)
`real_sfm_qualification/checkpoint_c2/test_c2_comparator_and_gate_regression.py` extracts the deployed
script's own `stable_hash`, `dumps_sorted`, `differing_top_level_fields`, and `canonicalize_snapshot`
functions verbatim (SHA-256 pinned) and proves: label/handle stripping and real-change detection (same
technique as C1's own regression); field-level diff identification correctly names exactly the changed
top-level keys; Comparison D's per-target equal/differing counting on a synthetic 85-target set with
exactly one injected difference correctly reports `equal_count=84`, `differing_count=1`, and names the
one differing target; Comparison E's four-way peer-parity logic correctly passes an unchanged peer and
flags a peer whose C1-baseline data differs from the live captures; the C1-artifact integrity gate
correctly accepts a matching, passing artifact and rejects both a tampered hash and a non-passing
artifact — **18/18 PASS under the real embedded Python 2.7.5**. Not yet run against real SFM.

One additional fix caught during offline authoring, before any dry run: the initial draft passed a
*decoded* (`unicode`) copy of the production Normalizer's own bytes to `compile()` for the actual
execution step, which raises `SyntaxError: encoding declaration in Unicode string` because the file's
own line-1 `# -*- coding: ascii -*-` declaration is incompatible with an already-decoded unicode
source string (the same class of bug previously hit and fixed elsewhere in this project's own
qualification suite). Corrected to pass the raw, undecoded bytes to `compile()` for execution — exactly
matching Checkpoint C1's own working `compile(baseline_source, ...)` call — while the *separate*,
already-decoded `all_lines`/`combined_source` text (used only for slicing out the 34 fingerprint
functions, never for executing the whole file) is unaffected, since its own extraction range begins
well after line 1.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (the file this checkpoint executes):
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- C1-2's own accepted PRE fingerprint hash (this run's required starting state):
  `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- C1-2's own accepted POST fingerprint hash (this run's required ending state):
  `d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938`
- C2-1 script SHA-256: `c5ca0d4cf423eb6e6af24ee0e530f309e7f157def3db3e536bb9cd6b3e4c2768`
