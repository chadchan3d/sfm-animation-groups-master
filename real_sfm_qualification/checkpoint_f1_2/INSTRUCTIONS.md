# Checkpoint F1-2 — Corrected Repeated / Warm-Use Stability

## Why F1-2 exists

F1-1 (the original four-command design) crashed the real SFM process
during command 3. Diagnostic F1-R1 then produced **decisive attribution
evidence**: production's own command boundaries showed **zero** retained
private/pagefile/VAS growth (command 2: `CP0_COMMAND_START` and
`FINAL_REPORT_ENTRY` both showed private/pagefile `3239079936`, free VAS
`348925952`, largest free region `126353408` — identical — in 6.430s),
while the qualification harness's own post-command semantic verification
added ~76.15 MiB that did not return after `del` + `gc.collect()`. A
follow-up static trace (`../checkpoint_f1_r1/F1-R1_SEMANTIC_CAPTURE_STATIC_PROOF.md`)
plus an offline empirical test under the real embedded Python 2.7.5
(`../checkpoint_f1_r1/test_allocator_highwater_retention.py`) confirmed a
third retention category distinct from live-reference retention (ruled
out) and cyclic garbage (already fixed, and still insufficient):
**Python/CRT allocator high-water retention** — freed pymalloc arenas are
not returned to the OS merely because the objects using them became
unreachable and were swept by `gc.collect()`. The root cause was F1-R1
still transiently capturing the full 85-eligible-target semantic tree on
**every** command, just to compute an aggregate hash — even though it only
*persisted* the full hash map on command 3.

F1-2 corrects this at the source: **no command in the loop calls
`capture_all()` with the 85-target eligible fixture at all.** C1/C2/D1/D2
already established full historical-vs-integrated semantic equivalence;
F1-2 is about repeated-use stability, not re-proving full equivalence
after every intermediate command.

**Do not save afterward.**

## Command sequence — restored to all four

1. Selected Shots
2. Selected Shots again
3. All Shots
4. All Shots again

## Between-command evidence (genuinely lightweight now)

- Production command completion evidence (started/completed cleanly).
- Production's own pre-existing `CONTEXTUALIZER_RESOURCE_CHECKPOINT` log
  diagnostic, parsed (not reinstrumented) — first/last checkpoint per
  command.
- Broker/provider/lease counters and source/generation identity (existing
  `authority_runtime` diagnostics).
- **Selected commands (1, 2) only**: the two Selected targets' (Fox, Mia)
  own semantic hashes, captured via `capture_all()` given a target list
  containing **only those two targets** — never the 85-target fixture.
- A bounded structural witness rebuild (shot/target classification only,
  no rig-tree walk) for target-set drift and fixture totals, on all four
  commands.
- `del prod_ns` and `gc.collect()` before the next production command
  (F1-R1's own correction, retained here).

## Semantic gates per command

- **Selected #1**: Fox/Mia's structural identity (model name, control
  count, fold-vocabulary hash — pinned since Checkpoint B) is re-verified
  via the bounded witness, and their 2-target semantic capture must
  succeed cleanly. This project has never pinned an external
  Fox-alone/Mia-alone *semantic* hash (only 85-target AGGREGATE hashes,
  which by definition require the whole fixture — exactly the operation
  being eliminated) — so command 1 does not claim to match a pre-pinned
  semantic constant.
- **Selected #2**: proves idempotence directly and self-containedly — its
  own captured Fox/Mia hashes must be **exactly identical** to command 1's.
  This requires no external pin and no 85-target scan.
- **All #1 / All #2**: no external semantic capture of any kind. Required:
  production completes; native-protection/lifecycle gates pass; target
  inventory counts/source identity (bounded witness) match the pinned
  totals; no anomaly.

## The one heavyweight verification

Only **after command 4** — when no further production command depends on
remaining address-space headroom — this script performs the single, full
85-eligible/78-excluded external semantic verification, checking the
final aggregate hash against the already-qualified All-Shots state
(`299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`) and
the final target identities against the already-qualified 85/78 sets. No
production command runs after this.

## Resource evidence

At every production command boundary: production's own
`CONTEXTUALIZER_RESOURCE_CHECKPOINT` first/last values (command-start and
`FINAL_REPORT_ENTRY` working set, private, free VAS, largest free region),
plus the harness's own process measure after its own minimal
`gc.collect()`. These are diagnostic, not gated to an exact byte
threshold (consistent with how memory snapshots have always been treated
in this project) — the key repeated-use signal is whether
**production-command boundaries themselves** show unexplained accumulating
loss, matching what F1-R1's own command-2 evidence already established as
the clean baseline. Allocator footprint from the one final heavyweight
verification is not classified as production retention.

## Operator instructions (exact sequence)

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the same disposable qualification project.
4. Select `shot3` only.
5. Run corrected `Checkpoint_F1_2_Corrected_Repeated_Warm_Use_Stability`.
6. Choose **Selected Shots**.
7. Choose **Selected Shots** again.
8. Choose **All Shots**.
9. Choose **All Shots** again.
10. Do not alter the scene between commands.
11. Return summary + JSON and preserved production logs.
12. **DO NOT SAVE. Restart SFM afterward.**

## Output artifacts

- `C:\Users\Public\Documents\sfm_checkpoint_f1_2_result.json` — rewritten
  atomically after every command boundary **and** after the final
  heavyweight verification.
- `C:\Users\Public\Documents\sfm_checkpoint_f1_2_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_2_production_log_command{1,2,3,4}.txt`

## Mechanical PASS criteria

`OVERALL_PASS` requires all of: starting fixture gate exact (SHAs, totals,
`shot3` sole-selected, Fox/Mia identity, initial aggregate hash); all 4
commands started and completed cleanly; native-protection/lifecycle gates
PASS for every command; no target-set drift at any boundary; command 2's
Fox/Mia hashes exactly match command 1's; the final full verification's
aggregate hash exactly matches the pinned All-Shots hash; the final 85
eligible / 78 excluded hash-map counts and round-trip checksums are
correct; the artifact write is verified; zero anomalies. A degraded/
incomplete run (fewer than 4 commands, or the final verification missing)
can never report `overall_pass=True`.

## Offline verification performed before deployment

(1) Syntax-checked under the real embedded Python 2.7.5, PASS. (2) New
regression `test_f1_2_corrected_stability_regression.py` (SHA-256
`c12a7f9ebd08e87a84e38d2c4a3cd57b5f0e3ce67323addc36d51c8021f62052`)
structurally proves, by parsing the deployed script's own source, that
exactly 2 call sites pass the 85-target eligible fixture to `capture_all()`
(the initial pre-flight capture and the post-loop final verification —
**never** inside the command-loop body), and exactly 1 call site passes
the 2-target Selected list, gated by `if ordinal in SELECTED_ORDINALS:`.
It also proves `verify_artifact_evidence()` structurally rejects any
command record carrying a full eligible/excluded hash map, rejects an
All-Shots record carrying `selected_target_hashes`, requires
`final_full_verification` only once 4 commands are claimed complete and
validates its 85/78 counts and round-trip checksums, and — via an
incremental-write simulation across all 4 command boundaries plus a
simulated post-command-4 crash before the final verification — that
whatever was written survives complete and independently re-verifiable.
The degraded-fallback force-False block (reused verbatim) still forces
`overall_pass=False`/`artifact_write_verified=False` given a synthetic
`report` claiming `True`. **49/49 PASS** under the real embedded Python
2.7.5. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256 (invoked
  four times): `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Required initial aggregate hash: `eac633c939f53ed3e7d9e81d473110147d62ee364f1acbc4d099b96fe1891fa0`
- Required final All-Shots aggregate hash: `299cbba30634da1a4949ed7b14187b813260c533dced3d1e71149ede98c124e7`
- F1-2 script SHA-256: `245a0fa70ff09a2cee6a39941492a5ee4d0bc62fa7d75a5cd9f1d96bae10cfc4`
- F1-2 offline regression SHA-256: `c12a7f9ebd08e87a84e38d2c4a3cd57b5f0e3ce67323addc36d51c8021f62052`
