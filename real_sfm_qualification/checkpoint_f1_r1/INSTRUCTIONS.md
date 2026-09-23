# Checkpoint F1-R1 — Repeated-Use Attribution Diagnostic

## THIS IS A DIAGNOSTIC, NOT A REPEAT OF F1

Checkpoint F1-1 crashed the SFM process itself during command 3 (All Shots),
target_seq 52, immediately after `PRE_NATIVE` telemetry — no subsequent
`NATIVE_REBUILD_RETURNED`. F1-R1 exists to help attribute that crash between
two hypotheses, without acting on either prematurely:

- **(a) harness-side**: the F1 qualification harness itself retained objects
  across command boundaries. A static audit (`../checkpoint_f1/F1-1_STATIC_AUDIT.md`)
  found one concrete, fixable deficiency: `gc.collect()` was called only once,
  after all 4 commands, never between them. **Fixed here.**
- **(b) production/SFM-side**: repeated production Normalizer/SFM use itself
  inherently consumes/fragments 32-bit address space across multiple
  commands, independent of any harness contribution.

**Do not save afterward.**

## Sequence — deliberately only 3 commands, no repeat of All Shots

1. **Selected Shots**
2. **Selected Shots** again
3. **All Shots** — **no 4th command.** Unlike F1, this diagnostic does not
   attempt "All Shots again."

## Minimal-footprint evidence design

Deliberately more aggressive than F1's own already-compact evidence
discipline:

- Commands 1–2 (Selected Shots) persist **only** the two Selected targets'
  (Fox, Mia) own compact per-target hashes — never all 85 eligible targets'
  hashes. A full 85-target capture is still performed **transiently**, in
  memory only, each command (required to compute the aggregate hash and the
  changed/unchanged target-key lists against the pinned Selected-Shots hash),
  but only the 2-entry Fox/Mia subset and the compact key-**lists** (not hash
  values) are ever written to the persisted evidence artifact.
- Command 3 (All Shots) persists the full 85-eligible/78-excluded compact
  hash maps (matching F1's own per-command schema) — but only reaches that
  point if command 3 actually completes.
- No D1/D2 manifest is loaded. Only small pinned expected-hash constants are
  used for comparison.
- `gc.collect()` runs after **every** command, immediately following an
  explicit `del prod_ns` (the previous command's own `exec()` namespace) —
  this is the harness-side fix the static audit identified.
- Memory/VAS evidence is captured two ways, deliberately reusing existing
  diagnostics rather than inventing new instrumentation:
  1. This harness's own lightweight ctypes-based working-set/pagefile
     sampler (identical to every earlier checkpoint's own `memory_snapshot()`),
     taken specifically **after** this harness's own per-command
     `gc.collect()` — the one measurement point production's own diagnostics
     cannot give, since they only run inside production's own code.
  2. Production's **own pre-existing, already-qualified**
     `CONTEXTUALIZER_RESOURCE_CHECKPOINT` log lines — discovered during the
     F1-1 investigation, not newly instrumented. These already report
     working set, pagefile, private bytes, and (critically) free/reserved/
     committed virtual address space, the largest contiguous free VAS
     region, and free-region count, at labeled checkpoints throughout each
     command (`CP0_COMMAND_START` … `FINAL_REPORT_ENTRY`, confirmed by
     direct source read of `Rebuild_Control_Groups_Normalizer.py`'s
     `contextualizer_resource_checkpoint()`, ~line 9452). This script
     **parses** those lines from the production log after every command; it
     adds no new VAS instrumentation of its own.
- **Incremental evidence**: unlike every earlier checkpoint (which wrote its
  report exactly once, at the very end), this script atomically rewrites the
  full JSON evidence artifact after **every command boundary**. If the
  process crashes during command 3 (as F1-1 did), the artifact left on disk
  is whatever was written after command 2 — commands 1–2's evidence is not
  lost. Production's own log (freshly truncated by each command's own
  `start()`) is **also** copied, per command, into a small numbered
  preserved-log file before the next command can truncate it again.

## Do not weaken production gates

This diagnostic does **not**: increase resource limits; remove production
isolation checks; remove native protections; skip targets; alter Rebuild
semantics; reduce service; or remove validation to make itself "pass." Its
purpose is attribution, not qualification. It does not force-release any
object production itself legitimately requires — the `gc.collect()`/`del`
calls only ever touch objects owned by this harness script (`prod_ns`, its
own transient capture dicts), never anything inside production's own running
state.

## Operator instructions (exact sequence)

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE** any previous state — restart discards it.
3. Open the same disposable qualification project.
4. Select `shot3` and no other shot.
5. Run **`Checkpoint_F1_R1_Attribution_Diagnostic`**.
6. If the starting-fixture gate fails, the script stops on its own — no
   mutation occurs.
7. Choose **"Selected Shots"** for command 1.
8. Choose **"Selected Shots"** again for command 2.
9. Choose **"All Shots"** for command 3.
10. **Do not modify the scene between commands.**
11. If SFM crashes at any point, return the latest production log
    (`C:\Users\Public\Documents\sfm_rebuild_control_groups.txt`) plus **any**
    of the following that exist on disk — they are written incrementally, so
    a crash during command 3 does not destroy commands 1–2's evidence:
    - `sfm_checkpoint_f1r1_result.json` (rolling — reflects the last
      completed command boundary)
    - `sfm_checkpoint_f1r1_result_summary.txt`
    - `sfm_checkpoint_f1r1_production_log_command1.txt`
    - `sfm_checkpoint_f1r1_production_log_command2.txt`
    - `sfm_checkpoint_f1r1_production_log_command3.txt` (only if command 3
      started)
12. If it completes, return the same files (the JSON's `in_progress` field
    will be `false` and `overall_pass` will be set). **DO NOT SAVE.** Restart
    SFM afterward to discard the experimental state.

## Diagnostic interpretation (decide only after the run — not to be acted on prematurely)

- **Outcome A — crashes again during command 3**: repeated production/SFM
  use itself materially consumes/fragments address space, independent of the
  harness. **Stop there — do not optimize blindly.** Report the exact
  per-command memory/VAS deltas (both the harness's own post-`gc.collect()`
  snapshots and production's own parsed `CONTEXTUALIZER_RESOURCE_CHECKPOINT`
  evidence) plus the final preserved log.
- **Outcome B — completes successfully with substantially more headroom**
  than F1-1 had at the equivalent point: the harness materially contributed.
  Use the static audit (`../checkpoint_f1/F1-1_STATIC_AUDIT.md`) to identify
  the exact retained objects before preparing a corrected full F1.
- **Outcome C — the static audit already found a definite large
  retained-reference bug sufficient to explain the delta**: fix the harness
  only (already done here — the `gc.collect()`-per-command fix), regress it
  offline (done — see below), and this run itself **is** that confirmation
  run before any full F1 is restored.

## Output artifacts

- `C:\Users\Public\Documents\sfm_checkpoint_f1r1_result.json` — rewritten
  atomically after **every** command boundary, not only at the end.
- `C:\Users\Public\Documents\sfm_checkpoint_f1r1_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1r1_production_log_command{1,2,3}.txt`
  — a byte-for-byte preserved copy of production's own log for that specific
  command, written before the next command's own `start()` can truncate the
  shared log path again.

## Offline verification performed before deployment

(1) Syntax-checked under the real embedded Python 2.7.5, PASS. (2) New
regression `test_f1r1_attribution_diagnostic_regression.py` extracts
`stable_hash`/`dumps_sorted`/`per_target_hash`/`compute_target_hashes`/the
`CONTEXTUALIZER_RESOURCE_CHECKPOINT` parser
(`parse_resource_checkpoint_line`/`parse_all_resource_checkpoints`/
`summarize_resource_checkpoints`)/`write_json_atomic`/`write_text_atomic`/
`copy_bytes_atomic`/`verify_artifact_evidence`/the degraded-fallback
force-False block verbatim (SHA-256 pinned) and proves, under the real
embedded Python 2.7.5: the checkpoint parser correctly handles real
`CONTEXTUALIZER_RESOURCE_CHECKPOINT` lines (including `L`-suffixed long-int
stripping and `True`/`False`/`None` typing) using the **actual lines observed
in the preserved F1-1 crash-evidence log**; `verify_artifact_evidence()`
correctly accepts a **partial** (1- or 2-command) artifact, rejects more
records than commands attempted so far, a wrong full-capture hash count, a
mutated checksum, and an incomplete compact key set; and — the central,
decisive proof — an **incremental-write simulation** that writes a
1-command, then a 2-command, partial artifact to the same rolling path,
independently reopens it fresh (simulating a post-crash operator pass), and
confirms commands 1–2's evidence is present, complete, and independently
re-verifiable, exactly as this checkpoint's crash-tolerance design intends.
**50/50 PASS.** Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (invoked
  three times): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required initial aggregate hash: `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- Required Selected-Shots aggregate hash (commands 1 & 2): `d7b3bacb757253e126823db4e1445b57e4278d972c9be8b23920fc88cf1b5938`
- Required All-Shots aggregate hash (command 3): `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- F1-R1 script SHA-256: `e9ea42b08f6448cef174b4d5642dfc1a89dbe74cf0145d9fcc0a3d96b63e7763`
- F1-R1 offline regression SHA-256: `e15d860fa603eb305c889bef73bd597d528c788aa4105d48f43536444cfc29e7`
