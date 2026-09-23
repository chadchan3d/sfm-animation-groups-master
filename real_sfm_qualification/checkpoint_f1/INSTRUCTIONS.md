# Checkpoint F1-1 — Repeated / Warm-Use Stability

## THIS CHECKPOINT MUTATES THE SCENE, REPEATEDLY

Unlike every earlier checkpoint, F1 invokes the REAL, INSTALLED, ACCEPTED, INTEGRATED production
Normalizer **four separate times in a row, in one continuous SFM process, without restarting SFM between
commands**.

**Do not save afterward.**

## Purpose

Checkpoints C/D already established historical-vs-integrated **semantic equivalence** (Selected Shots and
All Shots, each individually, once). F1 is explicitly **not** another equivalence campaign — it proves the
accepted integrated production Normalizer remains correct AND authority-lifecycle-clean across several
consecutive real commands in one warm SFM process: repeated broker acquisition, fresh source
authorization per command, generation consistency, provider/lease cleanup after every command, warm reuse
vs. idempotence (does a repeated command disturb an already-normalized state?), absence of accumulating
retained state, and continued SFM responsiveness afterward.

## Command sequence

One continuous SFM process. Do **not** restart between commands. Do **not** alter the scene between
commands.

1. **Selected Shots** — expected resulting aggregate hash: the known Checkpoint C2 Selected-Shots state
   (`d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938`).
2. **Selected Shots again** — expected resulting aggregate hash: the **same** state, unchanged. The
   script does not assume zero internal work occurred; it independently measures the actual semantically
   changed target set between commands 1 and 2.
3. **All Shots** — expected resulting aggregate hash: the known Checkpoint D1/D2 All-Shots state
   (`299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`). The script does **not** assume
   this command's own changed-target count must equal D1's original 57 (Fox/Mia were already normalized
   by command 1) — it measures the actual changed set from this run's own immediately-preceding state.
4. **All Shots again** — expected resulting aggregate hash: the **same** All-Shots state, unchanged.
   Again measured, not assumed.

## Memory-bounded compact evidence

At every command boundary the script captures per-target **hashes** (never raw fingerprint dicts) for all
85 eligible targets and all 78 excluded targets — the same D1-3/D2-2 discipline, applied across four
commands instead of one. A raw captured fingerprint dict is held only transiently, long enough to compute
its aggregate hash and per-target hashes, then released (`del`) before the next command begins. At no
point does the script hold more than one command's worth of raw captured fingerprints in memory at once.

## Fresh-authorization evidence (grounded in source reading, not new instrumentation)

`sfm_master_authority_productionized/broker.py`'s own `acquire_or_reuse_views()` calls
`observation.observe_master(master_path)` **unconditionally** on every single call, before ever checking
the view cache — this is the architecturally-designed fresh-authorization step, and it runs on every
command regardless of whether the heavier provider-open path ends up being needed. If the requested
fold-scope for a command is already fully covered by a live cache entry for the current (freshly-observed)
generation, no provider is opened at all; otherwise exactly one `acquire_cohort()` call fills the gap.

This script cannot directly observe the internal `observe_master()` call without new instrumentation
(which the governing brief explicitly forbids), so it infers fresh authorization from **existing**,
already-qualified diagnostics:
- the canonical Master's own SHA-256 is independently re-verified once before the whole sequence;
- every command completing successfully (no `ProbeError`, native-protection log markers present) is
  proof-by-construction that no `expected_generation_mismatch`/`AuthorityChangedDuringAcquisition` was
  raised — the Normalizer's own fail-closed policy would have surfaced any such mismatch as a command
  failure;
- `provider_counters()`/`outstanding_lease_count()` deltas are captured **per command** (never only
  cumulative totals). Whether a given command's delta is `(0 opens, 0 closes)` (a genuine, valid cache-hit
  reuse) or `(1 open, 1 close)` (a fresh provider open because the requested fold-scope was not yet fully
  cached) — **both** are lifecycle-clean outcomes. The gated, required invariant is that the delta is
  **balanced** (opens == closes) for every command and zero leases/providers are ever left outstanding —
  not a predetermined delta value. This script does **not** force provider reopening and does **not**
  assume a fixed delta pattern; it measures and reports the actual deltas.

## Starting fixture gate

Before any command, requires: production Normalizer SHA and canonical Master SHA exact; the fixed
structural totals (15/163/85/78/22/21); `shot3` as the sole selected shot; Fox/Mia exact identities (model
name, control count, vocabulary hash — extra rigor, matching Checkpoints C1/C2's own established
practice); and the initial 85-target aggregate hash exactly equal to
`eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`. **Any mismatch aborts before any
invocation of the production Normalizer or scene mutation.**

## Operator instructions

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the exact same disposable qualification project.
4. Select `shot3` and no other shot.
5. Run **`Checkpoint_F1_Repeated_Warm_Use_Stability`**.
6. If the starting-fixture gate fails, the script stops on its own — no mutation occurs.
7. **A real dialog will appear four separate times, one per command.** Choose **"Selected Shots"** for
   command 1, **"Selected Shots"** again for command 2, **"All Shots"** for command 3, **"All Shots"**
   again for command 4.
8. **Do not alter the scene between commands.** Do not restart SFM between commands.
9. Give it generous time — this run performs four full command cycles.
10. Do not touch SFM again until the console output shows the final summary and the
    "DO NOT SAVE. Restart SFM..." message.
11. Return the exact contents of **both** output files:
    - `C:\Users\Public\Documents\sfm_checkpoint_f1_repeated_warm_use_result_summary.txt`
    - `C:\Users\Public\Documents\sfm_checkpoint_f1_repeated_warm_use_result.json`

    Also tell me about any error dialog or console traceback beyond what's in those files.
12. **DO NOT SAVE. Restart SFM afterward to discard the experimental state.**

## Output artifact paths

- `C:\Users\Public\Documents\sfm_checkpoint_f1_repeated_warm_use_result.json` (compact — initial state,
  four command records each with per-target hash maps/lifecycle deltas/native evidence/memory snapshot,
  final responsiveness result, anomalies — tens of KB, not megabytes, never four copies of raw
  multi-megabyte fingerprint trees)
- `C:\Users\Public\Documents\sfm_checkpoint_f1_repeated_warm_use_result_summary.txt` (concise, read this
  first)

## Mechanical F1 PASS criteria (decided before execution)

`OVERALL_PASS` in the report requires **all** of:

- starting fixture is exact (SHAs, totals, `shot3` sole-selected, Fox/Mia identities, initial aggregate
  hash) — **a mismatch here means the script already stopped; no mutation occurred, and none of the
  checks below apply**;
- command 1 (Selected Shots) reaches the known Selected-Shots aggregate hash exactly;
- command 2 (Selected Shots again) preserves that exact aggregate hash;
- command 3 (All Shots) reaches the known All-Shots aggregate hash exactly;
- command 4 (All Shots again) preserves that exact aggregate hash;
- all 85 eligible target identities and all 78 excluded target identities remain stable throughout, with
  zero additions/removals/reclassifications relative to the original fixture, at every command boundary;
- each command ends lifecycle-clean: broker `READY`/canonical, zero outstanding leases, zero currently
  open providers, no stale active cohort, and a balanced provider opens/closes delta for that command
  (whatever the actual delta magnitude turns out to be);
- native-protection log evidence shows both guard/rebuild markers `PASS` for every command;
- SFM remains responsive after command 4 (main window available, document still accessible, events
  process normally);
- the compact JSON evidence artifact itself was written, is nonzero, reopens and reparses, contains all
  four command records plus the initial state, and every per-command stored hash map recomputes a
  matching checksum after round-trip (`artifact_write_verified=True`);
- the script completes without an unhandled exception (no harness `MemoryError`, no allocation failure);
- zero unresolved anomalies.

F1 does **not** require a predetermined changed-target count for command 3 (All Shots) — that is measured
from this run's own actual PRE state (which already reflects command 1/2's Selected-Shots normalization),
not assumed to equal D1's original 57. A degraded/fallback artifact (written only if the complete compact
artifact write itself somehow still fails) can **never** report `overall_pass=True` or
`artifact_write_verified=True` — both are forced `False` explicitly, the same fix D2-2 introduced, reused
verbatim here.

If the report shows `"gate_failure": true`, that means a pre-flight or starting-fixture check failed and
the script correctly stopped before touching anything.

## Source review: historical baseline / canonical Master / package are never overwritten

Direct grep of the F1 script for every file-write confirms exactly two `"wb"` (write) operations in the
entire script — the two report files listed above — and no code path opens the production Normalizer or
the canonical Master for writing; each is opened only in `"rb"` (read-only) mode, once, before the command
sequence begins. The historical baseline file is never referenced by this script at all. `sfm_master_
authority_productionized`/`sfm_master_sidecar` are never imported directly — only read via the module
bindings the production Normalizer's own source already imports into each command's own isolated `exec()`
namespace (a fresh namespace per command, but the underlying `sfm_master_authority_productionized` module
objects are the SAME process-wide singletons across all four commands, since Python's import cache is
process-wide, not tied to any one `exec()` namespace — this is exactly what makes the cumulative
provider/lease counters meaningful across repeated commands).

## Offline verification already performed

Before deployment: (1) syntax-checked under the real embedded Python 2.7.5, PASS — including confirming
that the `for` loop containing both the per-command `exec()` call and a nested `def normalizer_run_is_
active():` closure does **not** trigger Python 2's "unqualified exec is not allowed in function ... because
it contains a nested function with free variables" restriction, since a `for` loop (unlike a `def`) is not
a function scope; (2) every `del`-based memory-hygiene point verified by direct grep to confirm no deleted
name is referenced afterward, and both `capture_all()` call sites (initial capture, and once per loop
iteration) confirmed to occur before the corresponding `fp_ns`/`capture_snapshot_explicit_fn` deletion
(which happens once, after the whole four-command loop completes); (3) a new regression,
`real_sfm_qualification/checkpoint_f1/test_f1_compact_artifact_regression.py`, extracts the deployed
script's own `stable_hash`/`dumps_sorted`/`per_target_hash`/`compute_target_hashes`/`write_json_atomic`/
`REQUIRED_EVIDENCE_KEYS`/`verify_artifact_evidence` and the degraded-fallback's own force-False code block
verbatim (SHA-256 pinned) and proves, using the REAL 85+78 target hashes from the accepted D1-3 artifact
to build four representative command records: the compact F1 artifact serializes/reopens/reparses and
stays well under 2MB; `verify_artifact_evidence()` PASSES on the unmutated artifact; exactly 4 command
records are required (3 or 5 both correctly FAIL); a wrong per-command hash count (84 eligible or 77
excluded) correctly FAILS; a mutated per-command checksum correctly FAILS; and — the same D2-1 bug class,
reused verbatim in F1 — the degraded-fallback's own force-False lines produce `overall_pass=False`/
`artifact_write_verified=False` even when fed a synthetic `report` claiming `True` — **29/29 PASS** under
the real embedded Python 2.7.5. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (the file this checkpoint executes, four
  times): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required initial aggregate hash: `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- Required Selected-Shots aggregate hash (commands 1 & 2): `d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938`
- Required All-Shots aggregate hash (commands 3 & 4): `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- F1-1 script SHA-256: `d2af8cc6ac6eb2ed69fc5fae886ab715be8b79f3860274cd7f836aa874cd4ec6`
