# O3-R2 — Measurement Contract

**Status: DESIGN/PROOF/MEASUREMENT PREPARATION ONLY.** No production, integration, or lifecycle code has
been modified. No SFM has been run. This document specifies exactly what
`Checkpoint_O3_R2_Discovery_Cost_Split.py` measures and how, before any run occurs.

## Sole question this measurement answers

> Of the measured ~0.17-0.19 s per `discover_rig_context()` call, how much belongs to the reusable
> whole-scene traversal (phase 1, `reachable()`) versus the fresh validation Option C must retain
> (phases 2, 4, 6, 7, 8, and their own residual control-flow cost)?

## Instrumentation design (strictly observational, extends O2-R1's own established technique)

Six wrap points, all module-function or class-method reassignment in the `exec()`'d in-memory namespace
only — never editing the file on disk. Every wrapper calls the ORIGINAL function/method with the SAME
arguments and returns its SAME, unmodified return value.

1. **`discover_rig_context(shot, aset)`** — wrapped for its own total elapsed time (entry to exit) and
   its own returned `status`/`reachable_rig_count`/`matching_rig_count`. Also sets a thread-local-style
   nesting counter (`_discovery_depth`) around the call, incremented on entry, decremented on exit — this
   is what lets the other five wraps attribute their own timing to "inside discovery" versus "elsewhere"
   (e.g. `handle()` is also called from `capture_tree()`; only calls made while `_discovery_depth > 0`
   are attributed to discovery's own phase buckets).
2. **`reachable(start, max_elements=50000)`** — wrapped for elapsed time, attributed to Phase 1
   ("removable traversal") whenever `_discovery_depth > 0`.
3. **`typ(obj)`** — wrapped for elapsed time and call count, attributed to Phase 2 ("candidate filtering")
   whenever `_discovery_depth > 0`.
4. **`arr(obj, attr_name)`** — wrapped for elapsed time, **bucketed by `attr_name`** (`"animSetList"` →
   Phase 4, `"controls"`/`"elementList"` → Phase 6, `"hiddenGroups"` → Phase 7), attributed only when
   `_discovery_depth > 0`.
5. **`scalar(obj, attr_name)`** — wrapped for elapsed time, **bucketed by `attr_name`**: discovery calls
   it twice, `scalar(shot,"scene")` (line 3313, the scene lookup that precedes and feeds `reachable()`
   itself — bucketed to Phase 1, per `O3_R2_DISCOVERY_PHASE_MAP.md` row 1's own listed underlying calls)
   and `scalar(rec,"animationSet")` (line 3365, inside the rig->animset binding loop — bucketed to Phase
   4), attributed only when `_discovery_depth > 0`.
6. **`handle(obj)`** — wrapped for elapsed time and call count, attributed to Phase 8 ("handle
   extraction, aggregate") whenever `_discovery_depth > 0`.

Reused verbatim from O2/O2-R1 (already offline-verified, unchanged wrap technique): `capture_snapshot_
explicit` (module function — for label/target/branch correlation and equivalence-witness hashing, same
as O2-R1), `run_target_transaction` (class method — for target-level timing/resource snapshots), the
instance-level `self.rebuild` wrap (O2-R1's own corrected native-Rebuild timing fix, same root-cause
reasoning: patch the already-constructed instance immediately after `exec()` returns, not the class).

## Correlating a discovery call to its own capture label

`discover_rig_context()` itself carries no label. Every real call site immediately precedes its own
`capture_snapshot_explicit(..., label, rig_context)` call (confirmed exhaustively in
`checkpoint_o3/O3_DISCOVERY_CALL_MAP.md`). The diagnostic maintains a small FIFO queue: each completed
`discover_rig_context` wrapper call pushes its own phase-bucketed result onto the queue; each
`capture_snapshot_explicit` wrapper call pops the most recently pushed entry and associates it with its
own `label`. This is reliable because the two calls always happen in strict, immediate succession within
the same synchronous code path (no Qt yield between them, per the same static proofs O2-R1 already
established for the relevant intervals).

## Per-call report schema

For every discovery call:

```
{
  "target": "<aset name>",
  "branch": "reconciled" | "native_only_fallback" | "unknown",
  "label": "PRE" | "NATIVE_POST" | "PRODUCTION_GENERIC_COMPOSER_PRE" | "PRODUCTION_GENERIC_COMPOSER_POST" | "PRODUCTION_SEMANTIC_FINGERPRINT",
  "total_discovery_elapsed_seconds": <float>,
  "phase_1_reachable_traversal_seconds": <float>,
  "phase_2_candidate_filtering_seconds": <float>,
  "phase_4_rig_animset_binding_seconds": <float>,
  "phase_6_registry_elementlist_seconds": <float>,
  "phase_7_hiddengroups_seconds": <float>,
  "phase_8_handle_extraction_seconds": <float>,
  "residual_unexplained_seconds": <float>,   // total - sum(all phase buckets above)
  "reachable_element_count": <int>,           // len(objs) inside reachable(), if cheaply obtainable
  "matching_rig_count": <int>,
  "reachable_rig_count": <int>,
  "typ_call_count": <int>,
  "handle_call_count": <int>,
  "status": "<discover_rig_context's own returned status>",
  "exception": null | "<repr of any exception observed>"
}
```

## Command-level and fixture-level aggregation

Per command: sum/mean of the above across all 10 discovery calls (2 targets × 5 labels). Per fixture
(both commands): removable vs. retained totals for composer-before (`PRODUCTION_GENERIC_COMPOSER_PRE`)
specifically, since that is the one label the sole O3-R1 candidate touches — reported separately from the
other four labels' own totals (which remain diagnostic context, not the decision input).

## Decision computation (mechanical, from the measured data — not asserted in advance)

For composer-before discoveries specifically, across both targets and both commands:

- **Current cost** = `total_discovery_elapsed_seconds` (measured, unchanged).
- **Hypothetical Option C retained cost** = `phase_2 + phase_4 + phase_6 + phase_7 + phase_8 +
  residual_unexplained` (everything Option C's own corrected design, per `O3_R1_CORRECTED_SUBSTITUTION_
  DESIGN.md`, must freshly re-execute).
- **Hypothetical removable cost** = `phase_1_reachable_traversal_seconds` only.
- Per-target and two-target-fixture removable time reported separately, per instruction.

No guard/reuse-bookkeeping overhead is estimated in this measurement beyond what is directly observable
from the current, unmodified production code — Option C is not implemented here, so no such bookkeeping
exists to measure. If a rough bookkeeping estimate is wanted, it can only be a stated assumption (e.g.
"one cheap comparison"), not a measured value — the diagnostic's own JSON explicitly leaves this field
`null` with a note, rather than fabricating a number.

## Classification thresholds (materiality, not an arbitrary microbenchmark)

- **`OPTION_C_MATERIAL`**: removable (Phase 1) time is clearly the dominant or otherwise materially
  significant component of composer-before's own discovery cost, and eliminating it once per applicable
  target plausibly yields a meaningful command-scale saving.
- **`OPTION_C_MARGINAL`**: a removable portion exists but is small relative to the retained cost and to
  implementation/qualification complexity.
- **`OPTION_C_IMMATERIAL`**: retained (fresh-validation) cost dominates; traversal removal would not
  materially improve production.
- **`UNRESOLVED`**: only if the residual/unexplained bucket is large enough (relative to total discovery
  time) that phase attribution cannot be trusted.

This checkpoint does not itself assert which bucket the result falls into — the real-SFM run's own
numbers determine that, mechanically, per this contract.

## Correctness gates preserved (unchanged from O2/O2-R1's own discipline)

Production Normalizer and canonical Master SHA-256 verified unchanged; `shot3` scope confirmed; Fox+Mia
both transacted; native guards `PASS`; authority `READY`/canonical, zero outstanding leases;
`FINAL_REPORT_ENTRY` reached; semantic/accounting checks pass; zero anomalies. The diagnostic does not
suppress or normalize any discovery exception — an exception observed during a wrapped call is recorded
verbatim (`repr()`) and re-raised unchanged, exactly as O2-R1's own wrappers already do.

## Resource measurements

Command-level only, reusing production's own existing `CONTEXTUALIZER_RESOURCE_CHECKPOINT` log parsing
(the same technique O2/O2-R1 already established) for private bytes/working set/free VAS/largest free
block where the existing telemetry exposes them. No per-phase `VirtualQuery` or equivalent expensive
resource probe is introduced — this checkpoint is CPU/time attribution, not a memory diagnostic.
