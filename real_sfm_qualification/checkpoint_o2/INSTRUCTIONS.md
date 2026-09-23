# Checkpoint O2 — Bounded Rebuild + Normalizer Phase Attribution

## Purpose

Attribute cost inside the real qualified target transaction — WITHOUT another broad All-Shots stress
campaign. This is measurement only. No optimization is implemented or authorized by this checkpoint.

**Instrumentation is strictly observational**: it never skips a capture, never bypasses native Rebuild
or the composer, never forces GC between production stages, never alters callback timing, never caches
a DME object, never reduces validation, never touches authority lifecycle. See
`O2_REBUILD_NORMALIZER_PHASE_ATTRIBUTION.md` for the full instrumentation design and the offline
evidence already collected (closure-cycle mechanism confirmed under the real embedded Python 2.7.5;
monkey-patch mechanism verified; analysis logic offline-regressed 17/17 PASS).

**Do not save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **DO NOT SAVE the previous experimental state; restart SFM to discard it.**
3. Open the established disposable qualification fixture (the same project every earlier checkpoint has
   used).
4. Select `shot3` and no other shot.
5. Run `Checkpoint_O2_Bounded_Phase_Attribution`.
6. If the starting-fixture gate fails, the script stops on its own — no mutation occurs.
7. Choose **Selected Shots** in the first real dialog that appears (command 1, fresh state — normalizes
   Fox and Mia for the first time).
8. Choose **Selected Shots** again in the second real dialog (command 2, **in the same continuous SFM
   process**, immediately after command 1 — this is deliberate: it measures the same bounded operation
   against the now-already-normalized Fox/Mia, without a restart, matching the fresh-vs-normalized
   comparison this checkpoint requires).
9. Do not alter the scene between the two commands.
10. Wait for both commands to complete.
11. Return the three output files (see below).
12. **DO NOT SAVE. Restart SFM afterward to discard the experimental state.**

## Output artifacts

- `C:\Users\Public\Documents\sfm_checkpoint_o2_result.json` — the full compact evidence artifact,
  rewritten atomically after each command boundary.
- `C:\Users\Public\Documents\sfm_checkpoint_o2_result_summary.txt` — concise, read this first.
- `C:\Users\Public\Documents\sfm_checkpoint_o2_production_log_command{1,2}.txt` — a byte-for-byte
  preserved copy of production's own log for each command.

## Mechanical PASS / FAIL / UNRESOLVED rules (decided before execution)

`OVERALL_PASS` in the artifact requires: exact production Normalizer and canonical Master SHA-256;
`shot3` present; both commands started and completed within timeout; native guards and native-rebuild
log markers PASS for both commands; `FINAL_REPORT_ENTRY` reached both commands; authority broker
`READY`/canonical with zero outstanding leases both commands; the script completes without an unhandled
exception. A run failing any of these is `FAIL`, not silently reported as measurement success.

Distinct from `OVERALL_PASS`, the **eight required conclusions** (discovery cost, tree-capture cost,
composer-before design-review justification, reconciled terminal overlap, closure-cycle materiality,
native-Rebuild materiality, contextual-composer materiality, fresh-vs-normalized stage differences) are
classified `MATERIAL`/`IMMATERIAL`/`UNRESOLVED` (or the specific enum each conclusion calls for) **from
the actual numbers this run produces** — not decided in advance. If Fox and Mia both happen to take the
same branch (reconciled or native-only-fallback), branch coverage for the other path is reported as
`UNRESOLVED`, not assumed or extrapolated.

## What this run does NOT do

- Does not run All Shots.
- Does not run F1-R2.
- Does not attempt to distinguish scene-resident vs. process-only retention at the whole-command scale
  (that remains F1-R2's own purpose, parked pending this checkpoint's results).
- Does not implement any shortcut, cache, or early-out — including no "already normalized" predicate,
  per Astra's explicit `UNSAFE DIRECTION` disposition on that candidate.

## After the run

Report the returned `sfm_checkpoint_o2_result_summary.txt` and `sfm_checkpoint_o2_result.json` contents.
The eight required conclusions will be filled in from this run's own actual per-target, per-branch,
per-stage numbers — including the closure-cycle mechanism's materiality at Fox/Mia's real control-count
scale (136/174), which the offline test could only confirm the mechanism for, not its real-scale
magnitude.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256:
  `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Astra source baseline commit: `dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`
- O2 script SHA-256: `4eaa8e87356e65c127a8744949e956056b0a18f5a2e65907efd3430e8dd9c4fc`
- Offline test SHA-256s: monkeypatch mechanism
  `20144d8f4ec8aca08e9289fbfc87edc4e4d02b7810974a46b5e22979eccfd690`; closure lifetime
  `2d1965886505bf98607985fc0c2f9e1ef37ac978ec700c3426ed1c943b796a51`; analysis logic
  `f39cc7facbf4174ec909829b76728c50e579723e3882245426c05e5d6e016115`
