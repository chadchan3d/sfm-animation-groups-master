# Checkpoint F1-R5 — Fresh Discovery Component (Allocation/Traversal) Retention

## Purpose

F1-R4 was accepted: **`PASS -- DISCOVERY_DOMINANT`**. Fresh `discover_rig_context()` traversal, repeated at
the same 250 production semantic boundaries across the same 62 targets, reproduced the large majority of
F1-R2's own full-production retained pressure (private `+243,748,864` vs. full production
`+265,461,760` — reproduces ~92%; free VAS `-221,839,360` vs. `-237,633,536` — ~93%). F1-R5 narrows the
question further:

> Within that fresh-discovery cost, how much comes specifically from `reachable()`'s own whole-scene
> traversal/materialization (the ~94.4%-of-timing component O3-R2 already measured), as opposed to the
> smaller candidate/registry/ownership derivation that follows it — using memory retention evidence this
> time, not just timing?

This is lifetime/allocation attribution, not a proposal to reuse stale discovery results. Freshness
semantics remain mandatory: every production semantic boundary that currently requires a fresh observation
still receives one. This does not reopen O3's own rejected discovery-reuse/cache design and does not
implement any production change. See `F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md` for the full static audit.

**This checkpoint mutates the scene, twice, in one continuous SFM process.** **Do not save afterward.**

## Sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never the original `testscripts.dmx`. The
   script structurally refuses to proceed otherwise.
4. Run `Checkpoint_F1_R5_Fresh_Discovery_Component_Retention`.
5. **Command 1**: choose **All Shots** in the real dialog that appears (native-only baseline, matching
   F1-R3's own design).
6. Wait for command 1 to complete (the console will print a prompt right before command 2's own dialog
   appears).
7. **Command 2**: choose **All Shots** again, in the same continuous process (native + isolated fresh
   traversal component).
8. Wait for completion.
9. Return the output files (see below).
10. **DO NOT SAVE.**
11. **Fully restart SFM afterward.**

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r5_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r5_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r5_production_log_command1.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r5_production_log_command2.txt`

## What this run does NOT do

- Does not perform `capture_snapshot_explicit()`, `capture_tree()`, `production_generic_composer()`,
  `preflight_reconciliation_plan()`, `isolation_fingerprint()`, `verify_current_shot_peers()`, or
  `semantic_target_fingerprint()` in either command — confirmed by static source check.
- Does not reopen O3 and does not implement any discovery caching, reuse, or shortcut — every branch-
  determining discovery call and every isolated-traversal call is genuinely fresh.
- Does not save the scene.

## Design summary (full derivation in `F1_R5_ALLOCATION_TRAVERSAL_AUDIT.md`)

`reachable(start, max_elements=50000)` is already an independently-defined, directly-callable module-level
function inside the production Normalizer — the exact code path production itself uses for the expensive
whole-scene traversal component of every `discover_rig_context()` call. Calling `scalar(shot,"scene")` then
`reachable(scene)` directly reproduces that component in isolation, using the identical, unmodified
production code.

F1-R4's own branch determination requires the *full* `discover_rig_context()` result at the PRE and
NATIVE_POST sites for every target — a genuine logical necessity, not a measurement artifact. These 124
sites (62 × 2) remain full, correctness-complete fresh discovery calls in command 2, identical to F1-R4's
own. The remaining 126 sites (32 composer-entry targets × 3 extra sites [composer-before, composer-after,
terminal] = 96, plus 30 status-mismatch targets × 1 extra site [terminal] = 30) occur strictly *after* the
branch is already known — for these, command 2 substitutes the isolated traversal-only seam in place of
the full discovery call F1-R4 performed there.

**Command 1 (native-only)**: identical to F1-R3's own design, reused verbatim — establishes this process's
own native-only baseline for a same-process matched comparison.

**Command 2 (native + PRE/NATIVE_POST full discovery + isolated-traversal-only for the 126 remaining
sites)**: the measurement this checkpoint exists to produce.

## Emitted evidence

Per command: `native_summary` (calls/elapsed), `full_discovery_summary` (call count — command 2 only),
`traversal_only_summary` (calls/elapsed — command 2 only), `branch_counts` (command 2 only),
`ordered_branch_stream_checksum_sha256` (command 2 only — a deterministic SHA-256 over the ordered
`(shot, target, branch)` stream, for mechanical cross-run comparison against F1-R4's own 32/30
distribution), `resource_deltas` (private/free-VAS/largest-free/working-set, plus post-GC values).
`cross_command_comparison` reports `(command 2) - (command 1)` for each resource quantity within this same
process, plus the F1-R3/F1-R4/F1-R2 baselines for external comparison.

## Mechanical PASS / FAIL / INCOMPLETE

**PASS** requires (per command): correct production Normalizer/canonical Master SHA-256; correct
normalized-copy fixture filename (and confirmed refusal of the original fixture's filename); the real run
instance located and neutralized before any event pump; `instance.work` present with exactly 15 shots and
exactly 62 eligible targets; gate-skip counts matching the verified expected values; all 62 native Rebuild
calls complete; `instance.total_shots_processed == 0`; for command 2 specifically, the exact 32/30 branch
distribution where reproduced and the exact 250-site-equivalent schedule accounting
(`actual_total_sites == expected_total_sites`, derived mechanically from the observed branch counts); no
semantic capture/composer/verifier executed in either command; resource and post-GC endpoints captured;
no save; zero anomalies.

**FAIL** for any sequence/call/guard/resource mismatch.

**INCOMPLETE** if the exact isolation cannot be produced without dragging semantic capture or mutation into
the measurement.

The later interpretation label (unchanged four-way scheme from F1-R4, applied here to the narrower
traversal-component question) is analyst-applied from the raw numbers after the real run — the script does
not compute or embed this verdict itself.

## Offline verification performed before deployment

(1) Script syntax-checked under the real embedded Python 2.7.5, PASS. (2) `test_f1_r5_diagnostic_
regression.py` (SHA-256 `09adf13d0ef45df78850d9fd83dc249b35baa712d776d40f5e60971f2138c94f`) verifies: the
gate-skip counts against a real preserved production log; the branch-discovery-count constants (2/3/3/5)
reconcile exactly with the script's own inline full-discovery-count + extra-sites split (1+1, 2+1, 2+1,
2+3); `sequence_checksum()` is deterministic and order-sensitive; the shared resource-checkpoint parser and
atomic writers (verbatim reused) behave correctly; `timed_traversal_only()` (extracted verbatim) correctly
calls `scalar()` then `reachable()` and correctly skips `reachable()` entirely when `scalar()` returns
`None`; `branch_determining_discovery()` (extracted verbatim) correctly produces all four branch outcomes
and correctly calls PRE discovery exactly once (not twice) even when it raises; incremental resource
arithmetic verified against F1-R4's own real, accepted numbers as a worked example; static checks confirm
the deployed script's own source contains no real call to `capture_snapshot_explicit`, `capture_tree`,
`production_generic_composer`, `preflight_reconciliation_plan`, `isolation_fingerprint`,
`verify_current_shot_peers`, or `semantic_target_fingerprint`, and that the real instance is neutralized
strictly before `instance.work` is read, in either command. **47/47 PASS** under the real embedded Python
2.7.5. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R5 script SHA-256: `2dfee0da0fc1f836be186c8bf2792aaa8646ec316ff3ab633dc224f26320ec75`
- F1-R5 offline regression SHA-256: `09adf13d0ef45df78850d9fd83dc249b35baa712d776d40f5e60971f2138c94f`
- F1-R3 native-only baseline: private `+14,307,328`, free VAS `-2,490,368`, largest free `0`
- F1-R4 native+full-discovery baseline: private `+243,748,864`, free VAS `-221,839,360`, largest free
  `-184,778,752`
- F1-R2 full-production baseline: private `+265,461,760`, free VAS `-237,633,536`, largest free
  `-110,985,216`
