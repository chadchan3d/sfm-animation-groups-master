# Checkpoint F1-R4 — Fresh Discovery Retention Attribution

## Purpose

F1-R3 was accepted: **`PASS -- CONTEXTUAL_LAYER_MATERIAL`**. Native Rebuild alone, across the same 62
targets, explained only a small fraction of F1-R2's own full-production retained pressure (private ratio
~0.054, free-VAS-loss ratio ~0.010). The unexplained gap (~+251 MiB private, ~235 MiB free-VAS loss, ~111
MiB largest-free loss) lives somewhere in the contextual layer F1-R3 deliberately excluded. F1-R4 measures
exactly one question:

> Does fresh `discover_rig_context()` traversal itself — repeated at the same production semantic
> boundaries, exactly as production does, never cached or reused — explain a material share of the
> remaining contextual resource pressure?

This is lifetime/allocation attribution, not a proposal to reuse stale discovery results, and does not
reopen O3's own rejected discovery-reuse/cache design. See `F1_R4_DISCOVERY_SCHEDULE_AUDIT.md` for the
full re-derived branch/discovery-schedule audit this design is built from.

**This checkpoint mutates the scene** (native Rebuild runs for real, exactly as production/F1-R3 do). **Do
not save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never the original `testscripts.dmx`. The
   script structurally refuses to proceed if the currently open document's own filename does not match
   this exact name.
4. Run `Checkpoint_F1_R4_Fresh_Discovery_Retention_Attribution`.
5. Choose **All Shots**.
6. Wait for completion. The script processes exactly 62 targets, in production's own exact order,
   performing native Rebuild plus fresh discovery at each production semantic boundary for that target's
   own observed branch — no composer, no capture, no classification, no semantic verification.
7. Return the three output files (see below).
8. **DO NOT SAVE.**
9. **Fully restart SFM afterward.**

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r4_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r4_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r4_native_discovery_log.txt`

## What this run does NOT do

- Does not perform `capture_snapshot_explicit()`, `capture_tree()`, `production_generic_composer()`,
  `preflight_reconciliation_plan()`, `isolation_fingerprint()`, `verify_current_shot_peers()`, or
  `semantic_target_fingerprint()` — confirmed by static source check (never called with real arguments
  anywhere in the deployed script).
- Does not reopen O3 and does not implement any discovery caching, reuse, or shortcut — every discovery
  call is genuinely fresh, exactly preserving the behavior O3 concluded could not safely be cached.
- Does not save the scene.

## Branch/discovery-schedule summary (full derivation in `F1_R4_DISCOVERY_SCHEDULE_AUDIT.md`)

Re-derived directly from current accepted production source (not assumed from prior checkpoints):

| Branch | Discovery calls (count) |
|---|---|
| `PRE_CAPTURE_UNSUPPORTED` (PRE discovery itself raised) | 2 (PRE + terminal) |
| `NATIVE_POST_ONLY_STATUS_MISMATCH` (PRE's own rig status wasn't `SUPPORTED_ACTIVE_RIG`) | 3 (PRE + NATIVE_POST + terminal) |
| `NATIVE_POST_WRAPPER_SURVIVED` (a reconciliation-wrapper group still exists post-Rebuild) | 3 (PRE + NATIVE_POST + terminal) |
| `COMPOSER_ENTRY_PATH` (would reach composer in real production) | 5 (PRE + NATIVE_POST + composer-before + composer-after + terminal) |

Two production branch conditions (`NATIVE_POST_ONLY_DUPLICATE_SEMANTICS`, `NATIVE_POST_POLICY_FALLBACK`)
depend on fields only `capture_tree()`/full capture dicts provide, which this checkpoint never calls — both
are explicitly disclosed as skipped (not silently faked) and fall through to `COMPOSER_ENTRY_PATH`, a
one-directional conservative bias that can only add discovery work relative to production's own true
branch for those two specific conditions, never remove it.

The branch each of the 62 targets actually takes is determined **dynamically, at runtime**, from the same
live PRE/POST discovery comparisons production itself uses — this checkpoint does not have access to a
preserved F1-R2 production log file, so it does not assume a pre-declared schedule; it reports the branch
it actually observes for every target (`branch` field per target, plus aggregate `branch_counts`).

## Emitted evidence

Per target: `branch`, `discovery_call_count`, `native_elapsed_seconds`, `discovery_elapsed_seconds`.
Aggregate: `branch_counts`; `discovery_summary.expected_total_discovery_calls` (computed from the observed
branch counts via the table above) vs. `discovery_summary.actual_total_discovery_calls` (directly counted
— these must match exactly, a validity gate in themselves); `provenance.invocation_stream_checksum_sha256`
— a deterministic SHA-256 over the ordered `(shot, target, branch, discovery_site)` invocation stream, for
mechanical cross-run comparison.

## Reported resource quantities

Raw: `native_discovery_private_delta`, `native_discovery_free_vas_delta`, `native_discovery_largest_free_delta`,
`native_discovery_working_set_delta`, `postgc_private_delta`, `postgc_free_vas_delta`,
`postgc_largest_free_delta`. Compared against both baselines (informational only, no auto-computed
verdict): F1-R3's own native-only result (private `+14,307,328`, free VAS `-2,490,368`, largest free `0`)
and F1-R2's own full-production result (private `+265,461,760`, free VAS `-237,633,536`, largest free
`-110,985,216`). `incremental_vs_native_only` reports `(native+discovery) - native_only` — the quantity
attributable to adding fresh discovery traversal under the matched control. `ratios_vs_full_production`
reports the same three ratios F1-R3 already established, now for native+discovery combined.

## Mechanical PASS / FAIL / INCOMPLETE

**PASS** requires: correct production Normalizer/canonical Master SHA-256; correct normalized-copy fixture
filename (and confirmed refusal of the original fixture's filename); the real run instance located and
neutralized before any event pump; `instance.work` present with exactly 15 shots and exactly 62 eligible
targets; gate-skip counts matching the verified expected values; all 62 native Rebuild calls complete; the
exact expected discovery-site stream completed for every target; `actual_total_discovery_calls ==
expected_total_discovery_calls` (derived from the observed branch counts); `instance.total_shots_processed
== 0` (proving production's own real pipeline never advanced); no semantic capture/composer/verifier
executed; resource and post-GC endpoints captured; no save; zero anomalies.

**FAIL** for any sequence/call/guard/resource mismatch.

**INCOMPLETE** if the exact fresh-discovery workload cannot be isolated without dragging semantic capture
or mutation into the measurement.

The later interpretation label (`DISCOVERY_DOMINANT` / `DISCOVERY_MATERIAL_BUT_INCOMPLETE` /
`DISCOVERY_SMALL` / `UNRESOLVED`) is analyst-applied from the raw numbers after the real run — the script
does not compute or embed this verdict itself. If discovery proves dominant, the next design question is
fresh-traversal lifetime/streaming, not stale-traversal reuse — not implemented by this checkpoint.

## Offline verification performed before deployment

(1) Script syntax-checked under the real embedded Python 2.7.5, PASS. (2) `test_f1_r4_diagnostic_
regression.py` (SHA-256 `adf426c125edc2337ffe8dd299d8ad5bf2ce19685f0c906671ce6110acd10eff`) verifies: the
gate-skip counts against a real preserved production log; the branch-discovery-count constants (2/3/3/5)
match the audit doc's own derivation; `sequence_checksum()` is deterministic and order-sensitive; the
shared resource-checkpoint parser and atomic writers (verbatim reused) behave correctly;
`matched_native_and_discovery_workload()` (extracted verbatim from the deployed script) correctly produces
all four branches with the exact expected discovery-call counts and ordered site sequences, correctly
still invokes native Rebuild when PRE itself raises, and correctly logs (rather than raises) an anomaly
when POST rig identity drifts from PRE while still completing the target; resource-delta/incremental
arithmetic verified against a worked example; static checks confirm the deployed script's own source
contains no real call (as opposed to a documentation reference) to `capture_snapshot_explicit`,
`capture_tree`, `production_generic_composer`, `preflight_reconciliation_plan`, `isolation_fingerprint`,
`verify_current_shot_peers`, or `semantic_target_fingerprint`, and that the real instance is neutralized
strictly before `instance.work` is read. **53/53 PASS** under the real embedded Python 2.7.5. Not yet run
against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R4 script SHA-256: `0efe92d4955407110889cb0d0da78682cfeccfdcf533e864f4d5c620f59f7f58`
- F1-R4 offline regression SHA-256: `adf426c125edc2337ffe8dd299d8ad5bf2ce19685f0c906671ce6110acd10eff`
- F1-R3 native-only baseline (for incremental/ratio reporting only): private `+14,307,328`, free VAS
  `-2,490,368`, largest free `0`
- F1-R2 full-production baseline (for ratio reporting only): private `+265,461,760`, free VAS
  `-237,633,536`, largest free `-110,985,216`
