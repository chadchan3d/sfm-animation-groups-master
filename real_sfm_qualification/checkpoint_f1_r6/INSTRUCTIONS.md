# Checkpoint F1-R6 — Fresh Streaming Discovery Parity

## Purpose

F1-R5 was accepted: **`PASS — TRAVERSAL/MATERIALIZATION DOMINANT`**. Even after 126 of the 250 fresh
discovery sites were reduced to isolated `reachable(scene)` traversal, ~92% of discovery-associated
private growth and ~96% of discovery-associated free-VAS loss remained — strong evidence that fresh scene
traversal/materialization is the primary actionable resource target. F1-R6 designs, offline-verifies, and
(having passed offline parity) real-SFM-tests a **fresh streaming** equivalent of `discover_rig_context()`
that avoids materializing the ~4,250-element `reachable()` list, while preserving exact semantics and
freshness. See `F1_R6_CONTRACT_AND_ALLOCATION_AUDIT.md`, `F1_R6_SWIG_ITERATION_INVESTIGATION.md`,
`F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_CONTRACT.md`, and `F1_R6_SUMMARY_AND_DECISION.md` for the full
design record.

**This is not authorization to modify production.** O3 remains closed — no cross-boundary discovery
reuse, topology caching, stale handles, or immutable-topology assumptions are introduced anywhere. Every
discovery call, legacy or candidate, performs a complete, fresh, live observation every time.

**This checkpoint does not mutate the scene at all** — no native Rebuild, no shot activation, no writes of
any kind. **Do not save afterward anyway**, per this whole project's own standing discipline.

## Sequence

1. **RESTART SFM FIRST.**
2. **Do not save any prior experimental state.**
3. Open **only** `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx` — never the original `testscripts.dmx`. The
   script structurally refuses to proceed otherwise.
4. Run `Checkpoint_F1_R6_Fresh_Streaming_Discovery_Parity`.
5. Choose **All Shots** in the real dialog that appears (needed only so `instance.work` reflects the full
   62-target scope — this script does not process shots/targets the way production does; it reads
   `instance.work` directly and never advances the real pipeline).
6. Wait for completion — the script compares legacy vs. candidate discovery for all 62 targets, alternating
   which arm runs first per target to control for measurement-ordering bias.
7. Return the output files (see below).
8. **DO NOT SAVE.**
9. **Fully restart SFM afterward.**

## Output files to return

- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_result.json`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_result_summary.txt`
- `C:\Users\Public\Documents\sfm_checkpoint_f1_r6_production_log.txt`

## What this run does NOT do

- Does not call native Rebuild, activate a shot, or write anything to the scene — confirmed by static
  source check (no `self.rebuild(`/`instance.rebuild(` call, no `SetHeadTimeInSeconds(` call anywhere).
- Does not perform `capture_snapshot_explicit()`, `capture_tree()`, `production_generic_composer()`,
  or `preflight_reconciliation_plan()` — confirmed by static source check.
- Does not reopen O3 and does not implement any discovery caching, reuse, or shortcut.
- Does not save the scene.

## Design summary

`discover_rig_context(shot, aset)`'s own first statement reads `shot`'s own `scene` **attribute**
directly — it does not depend on SFM's own playhead/active-shot state at all (unlike native Rebuild, which
genuinely requires shot activation, per F1-R3's own audit). This means legacy and candidate can both be
called directly against every one of the 62 real targets recorded in `instance.work`, with **zero scene
mutation and zero risk of one observation affecting the other's own state** — a strictly simpler, read-only
design than F1-R3/F1-R4/F1-R5.

**Legacy** is `discover_rig_context`, extracted unmodified from the exec()'d production namespace (never
reimplemented). **Candidate** is `discover_rig_context_streaming`, from `F1_R6_Discovery_Streaming_
Prototype.py` (deployed alongside this script), loaded into a namespace seeded with the SAME extracted
legacy helpers (`handle`, `typ`, `arr`, `scalar`, `element_ref_pairs`, `name`, `to_unicode`, `ProbeError`) —
guaranteeing the candidate calls the identical native-bound functions legacy itself uses; only the
traversal/classification fusion is new code.

Per target, which arm runs first alternates (even index: legacy first; odd index: candidate first) to
cancel out any first-position resource-measurement bias in aggregate. Cheap process-memory sampling
(private/working-set) brackets every individual call, attributing incremental cost to whichever arm it
belongs to; the more expensive VAS (free/largest-free) scan is taken only at low cadence (every 8th
target, plus start/final/post-GC).

## Emitted evidence

Per target: `status`, `parity_match` (boolean), `mismatch_fields` (empty list on a match — never a full
object dump). Aggregate: `parity_summary` (match/mismatch counts, status distribution — informational, not
a pass/fail branch schedule, since this workload does not make branch-entry decisions);
`resource_attribution` (summed private/working-set deltas attributed separately to the legacy arm and the
candidate arm across all 124 individual calls); `resource_deltas` (whole-command before/after/post-GC
deltas, for cross-reference against F1-R3/F1-R4/F1-R5's own established baselines).

## Mechanical PASS / FAIL / INCOMPLETE

**PASS** requires: correct production Normalizer/canonical Master SHA-256; correct normalized-copy fixture
filename (and confirmed refusal of the original fixture's filename); the real run instance located and
neutralized before any event pump; `instance.work` present with exactly 15 shots and exactly 62 eligible
targets, gate-skip counts matching the verified expected values; **all 62 targets show `parity_match ==
True`, zero mismatches** (`parity.all_62_targets_matched`); `instance.total_shots_processed == 0`; resource
and post-GC endpoints captured; zero anomalies.

**FAIL** for any parity mismatch or gate/guard failure.

**INCOMPLETE** if the exact comparison cannot be produced without dragging semantic capture or mutation
into the measurement.

## Offline verification performed before deployment

(1) Both scripts (the real-SFM checkpoint and the prototype module) syntax-checked under the real embedded
Python 2.7.5, PASS. (2) `test_f1_r6_adversarial_parity.py` (SHA-256
`ec345eeba80bd1e086d48fcaad98e03a81caea03971fb67335e817699335bb2d`) compares legacy (extracted verbatim
from the pinned production source) against the candidate prototype across 21 adversarial fake-DME
fixtures — simple tree, shared-reference DAG, cycle, duplicate paths, no rig, one rig (two topologies),
multiple competing rigs, registry absent/unique/ambiguous, target absent/unique, multiple candidates with
one match, malformed/null references, attribute/handle-access exceptions, an ordering-sensitive layout, a
1,500+-element synthetic graph, zero ownership, and both discovery-unavailable/failure edge cases —
**205/205 PASS, zero parity mismatches**. (3) `test_f1_r6_realscript_regression.py` (SHA-256
`ce6900fe266337234b89224c77b792c77bc5c40518e3bd3253c4577f19ecbbe0`) verifies the real-SFM script's own
shared atomic-write primitives and its `compare_discovery_results()` function (extracted verbatim) against
synthetic result dicts, including the `AMBIGUOUS_MULTIPLE_RIGS` both-`None` case; static checks confirm the
deployed script contains no call to native Rebuild, shot activation, or any semantic-capture/composer
function, and that neutralization happens before `instance.work` is read — **19/19 PASS**. All under the
real embedded Python 2.7.5. Not yet run against real SFM.

## Identities this checkpoint is pinned against

- Installed, accepted, integrated production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Expected normalized-copy fixture filename: `F1_R2_NORMALIZED_DIAGNOSTIC_COPY.dmx`
- F1-R6 real-SFM script SHA-256: `1f4096e98a37bd0fd9d328692cf638e24b00e4aae6e6bc9dfeda38b817f5c975`
- F1-R6 prototype module SHA-256: `17851cd1fed519aa8134fb15c2f057c82a471b8d9b7d1f7b3ae7378edfab4cb8`
- F1-R6 adversarial parity test SHA-256: `ec345eeba80bd1e086d48fcaad98e03a81caea03971fb67335e817699335bb2d`
- F1-R6 real-script regression test SHA-256: `ce6900fe266337234b89224c77b792c77bc5c40518e3bd3253c4577f19ecbbe0`

## Explicit non-authorization

Even excellent parity and resource results from this checkpoint do not themselves authorize production
implementation. Per explicit instruction, the result returns to independent review before any production
change is considered. This checkpoint does not patch production, does not touch authority/broker code, and
does not close F.
