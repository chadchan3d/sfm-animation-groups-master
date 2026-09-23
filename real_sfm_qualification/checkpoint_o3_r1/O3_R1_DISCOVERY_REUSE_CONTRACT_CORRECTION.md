# O3-R1 — Discovery Reuse Contract Correction (Summary)

**Status: O3-R1 — DISCOVERY REUSE CONTRACT CORRECTION — DESIGN/PROOF CORRECTION COMPLETE.** No
production, integration, or lifecycle code has been modified. No SFM was run. No optimization is
implemented or authorized by this checkpoint. F1-R2 remains parked/unrun. Checkpoint G was not prepared.
Scope was not broadened.

## Why this checkpoint exists

Astra independently reviewed O3 and returned **`REVISE_BEFORE_IMPLEMENTATION`**. This checkpoint corrects
the specific overclaims Astra identified, without broadening scope. The sole candidate remains: **outer
native POST → composer-before discovery substitution on the supported-active-rig composer-entry path.**
Terminal reuse remains deferred/unresolved, per explicit instruction, and is not addressed here.

## Astra findings preserved

- The supported-active-rig composer-entry path really has five independent discoveries: PRE → native
  POST → composer-before → composer-after → terminal.
- No hidden sixth discovery was found.
- Native POST discovery remains required.
- Composer-after discovery remains required.
- Terminal discovery remains required.
- Native-only/fallback branches remain unchanged.
- Discovery reuse remains potentially worthwhile.
- Implementation is not yet authorized.

## O3 overclaims corrected

1. **Interval identity stability was overstated.** O2's own hash equality proved retained semantic
   equality at two observation points, not identity continuity. Native getter calls and
   `sys.stdout.write()` remain unproven call/reentrancy boundaries — classified `UNRESOLVED` in
   `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` (section 7), honestly, rather than assumed safe.
2. **O3's token was insufficient.** Animation-set handle equality does not prove rig/registry/root/
   ownership continuity; stored counts/status were historical observations, not current facts; names do
   not distinguish replacement incarnations; borrowed list/set fields were mutable; current-shot/reentry/
   pointer-reuse behavior was not covered. **Corrected**: Option C (`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md`)
   discards the "trust a historical token" architecture entirely — it reuses only the expensive
   candidate-identification work and freshly re-validates everything else, so none of these historical-
   trust concerns apply.
3. **The proposed token did not satisfy the existing capture contract.** Resolved precisely: direct
   reading of `capture_snapshot_explicit()`'s complete body (`O3_R1_DISCOVERY_CAPTURE_CONTRACT.md`)
   established it uses the live `rig` object for exactly one cheap `name()` call, and never uses
   `registry` at all. Option C satisfies the contract by producing a freshly-confirmed live `rig` object
   through its own re-validation sequence — no contract change, no `None` substitution.
4. **Fresh discovery has real failure semantics that were not being preserved.** Precisely enumerated in
   `O3_R1_PREWRITE_FAILURE_CONTRACT.md`: `discover_rig_context()` has both status-value failures
   (Category 1) and **raw, uncaught exceptions** (Category 2 — `arr()`/`handle()` calls not wrapped in
   their own `try/except`) that O3's own analysis did not distinguish. Option C re-executes every one of
   these fresh, in the same order, before composer writes.
5. **Terminal reuse remains deferred/unresolved.** Not addressed in this checkpoint, per explicit
   instruction.

## Deliverables

1. `O3_R1_DISCOVERY_CAPTURE_CONTRACT.md` — exact field-by-field discovery-to-capture contract; the
   `rig_name` fix; the A/target-identity, B/rig-topology-discovery, C/semantic-tree-capture separation.
2. `O3_R1_PREWRITE_FAILURE_CONTRACT.md` — the Category 1 / Category 2 failure-semantics enumeration this
   whole correction turns on.
3. `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` — Options A/B/C (B rejected, C adopted); the live-`rig`-contract
   resolution; the reentrancy investigation (`UNRESOLVED`, with an explicit argument for why the design's
   safety does not depend on resolving it); the corrected, phase-truthful branch map.
4. `O3_R1_MATERIALITY_REEVALUATION.md` — gross ceiling unchanged (~0.17-0.19 s/target); net saving
   **not yet established** — the specific split measurement needed is named, not run.
5. `O3_R1_QUALIFICATION_PLAN.md` — corrected offline + real-SFM plan, addressing Astra's "separate
   identity evidence, not stripped semantic hashes alone" concern directly. Not executed.

## Required final decision

**`MORE_MEASUREMENT_REQUIRED`**

A corrected, correctness-sound narrow design (Option C) now exists: it preserves pre-write failure
behavior (both Category 1 and Category 2), preserves every discovery-derived validation read, satisfies
`capture_snapshot_explicit`'s own input contract without modification, does not retain any unsafe live
object beyond a single transaction-local re-validation-plus-capture sequence, and does not depend on
proving native non-reentrancy. **What is not yet established is the net saving magnitude** — Option C
only skips `reachable(scene)`'s own traversal cost, not the full discovery call's cost, and O2-R1's own
measurement did not separately isolate that traversal's own share of the ~0.17-0.19 s/call figure. A
specific, narrow measurement (splitting `discover_rig_context()`'s own internal timing between the
traversal and the downstream validation reads) is required before recommending
`READY_FOR_ASTRA_REVIEW` — declaring readiness without it would risk repeating exactly the class of
overclaim this correction round exists to fix. This measurement is not authorized to run as part of this
checkpoint; it is named as the specific next step, per explicit instruction to identify but not execute
it.

## Frozen invariants (unchanged, restated)

Everything O3's own frozen list already covered remains frozen: native Rebuild, PRE eligibility, native
guards, Master protection/validation, authority lease, classification/planning, destination ordering,
isolation, target callback guards/re-resolution, failure behavior, native-only fallback correctness,
terminal validation, no runtime DME cache. No warm-path shortcut. No stale semantic cache. No F1-R2. No
Checkpoint G.

## What happens next

Nothing, without separate explicit authorization. If the identified split measurement is later performed
(offline, using the same extraction/instrumentation discipline this whole project has established) and
shows the traversal genuinely dominates `discover_rig_context()`'s own cost, Option C would become a
strong `READY_FOR_ASTRA_REVIEW` candidate. If the split shows the downstream validation reads themselves
are a significant fraction of the cost, the net benefit may be closer to `O3_R1_MATERIALITY_REEVALUATION.md`'s
own honestly-stated "not yet established" than to O3's own original gross-ceiling estimate, and
`DO_NOT_IMPLEMENT` would become the more defensible conclusion.
