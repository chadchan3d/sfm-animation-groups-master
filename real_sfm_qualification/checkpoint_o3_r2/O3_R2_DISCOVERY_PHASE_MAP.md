# O3-R2 — Discovery Phase Map

**Status: DESIGN/PROOF/MEASUREMENT PREPARATION ONLY.** Read-only source analysis of the accepted
production Normalizer (`Rebuild_Control_Groups_Normalizer.py`, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`). No production, integration, or
lifecycle code has been modified. This document decomposes `discover_rig_context()` (line 3299-3436)
into exact, source-grounded phases — it does not invent phase boundaries that do not exist in the code.

## Method

`discover_rig_context()` is a single function with no internal sub-function boundaries — it cannot be
phase-split by wrapping "sub-functions of itself" that do not exist. What **can** be independently timed,
without modifying the file, are the shared module-level helper functions it calls
(`reachable`, `typ`, `arr`, `scalar`, `handle`), each already reassignable in the `exec()`'d namespace by
the same monkey-patch technique O2/O2-R1 already established and offline-verified. `Checkpoint_O3_R2_
Discovery_Cost_Split.py` wraps these five functions plus `discover_rig_context` itself (for its own total
elapsed time and result fields) — see `O3_R2_MEASUREMENT_CONTRACT.md` for the wrapping design. This
document maps which of those wrapped calls correspond to which of the 11 requested phases.

## Exact phase boundaries, by source line

| # | Phase | Source lines | Underlying call(s) instrumented | Notes |
|---|---|---|---|---|
| 1 | Whole-scene reachable-element traversal | 3313-3329 (`scene = scalar(...)`, `objs = reachable(scene)`) | `scalar(shot,"scene")` (once), `reachable(scene)` (once) | The single O(scene-size) operation; `reachable()`'s own cost is measured directly by wrapping it |
| 2 | Candidate rig filtering | 3334-3344 (`for obj in objs: if typ(obj) != "DmeRig": continue; rigs.append(obj); ... obj.HasAnimationSet(aset) ...`) | `typ(obj)` (once per reachable object — the dominant iteration cost here), plus one `HasAnimationSet()` native call per `DmeRig`-typed object found (not separately wrappable — a bound native method call, not a module-level function; its own cost is captured only in the residual/"other" bucket, see below) | Iterates every object `reachable()` returned; cost scales with `reachable_rig_count`'s own denominator (total reachable objects), not just the final rig count |
| 3 | Rig uniqueness/status derivation | 3346-3357 (`result["reachable_rig_count"]=...`; `if not matches: ...`; `if len(matches)!=1: ...`; `rig = matches[0]`) | None — pure Python control flow and list-length checks | Expected cost: negligible (a handful of comparisons); measured only via the residual bucket |
| 4 | Rig → animation-set binding reads | 3359-3376 (`for rec in arr(rig,"animSetList"): if typ(rec)!="DmeRigAnimSetElements": continue; linked=scalar(rec,"animationSet"); same = handle(linked)==handle(aset)`) | `arr(rig,"animSetList")` (bucketed by attr_name `"animSetList"`), `typ(rec)` (per record), `scalar(rec,"animationSet")` (per record), `handle(linked)`/`handle(aset)` (per record) | The loop that resolves which `DmeRigAnimSetElements` record corresponds to this `aset` |
| 5 | Registry discovery/resolution (uniqueness check) | 3378-3384 (`if len(registry_matches)!=1: ... ; registry = registry_matches[0]`) | None — pure Python | Negligible; measured via residual |
| 6 | Registry `elementList` reads | 3386-3403 (`control_objs = arr(aset,"controls")`; `control_handles = set(...)`; `for obj in arr(registry,"elementList"): registry_handles.add(handle(obj))`) | `arr(aset,"controls")` (bucketed `"controls"`), `handle(control)` per control, `arr(registry,"elementList")` (bucketed `"elementList"`), `handle(obj)` per element | Two array reads (`aset`'s own controls, and the registry's own elementList) plus per-element handle extraction |
| 7 | Registry `hiddenGroups` reads | 3427-3433 (only reached on the success path, after ownership is confirmed non-empty) | `arr(registry,"hiddenGroups")` (bucketed `"hiddenGroups"`) | Only executes when `status` is about to become `SUPPORTED_ACTIVE_RIG` |
| 8 | Handle extraction (aggregate) | Scattered — `handle(rig)` (3381, 3409, 3423), `handle(registry)` (3410, 3424), `handle(control)`/`handle(obj)` (3388-3390, 3396) | `handle(x)`, all call sites, summed | Reported as one aggregate bucket per the requested phase list; individual call sites are not separately distinguishable without editing the file |
| 9 | Ownership derivation | 3400-3405 (`owned_handles = control_handles.intersection(registry_handles)`; `if not owned_handles: ...`) | None — pure Python set intersection | Expected negligible; measured via residual |
| 10 | Root/target-related reads | **N/A — no such read exists inside `discover_rig_context()` itself.** `aset.GetRootControlGroup()` happens in `capture_snapshot_explicit()` (line 3557), a different function, already unaffected by any Option C design. | N/A | Explicitly not a phase of discovery — listed here only to confirm its absence, not invented |
| 11 | Detached result construction | 3413-3436 (`owned_names = [...]`; `result.update({...})`) | None — pure Python list/dict construction | Expected negligible; measured via residual |

## Reconciling phase timings to total discovery elapsed

`discover_rig_context`'s own wrapped total elapsed time is measured directly (entry to exit). The sum of
all bucketed sub-call timings (`reachable` + `typ` + `arr` [all attr-name buckets] + `scalar` + `handle`)
will not exactly equal the total, because: (a) native `obj.HasAnimationSet(aset)` calls (phase 2) are not
independently wrappable (a bound native method, not a module-level function) — their cost lands in the
unexplained residual; (b) pure-Python control flow, list/set construction, and comparisons (phases 3, 5,
9, 11) are real but expected-negligible costs with no dedicated wrap. The diagnostic reports this
**residual** (`total - sum(bucketed sub-calls)`) explicitly, per the requirement that "unexplained
overhead is bounded and reported" — not hidden or assumed zero.

## What this phase map is used for

`Checkpoint_O3_R2_Discovery_Cost_Split.py` uses exactly this mapping to bucket its own measured timings
into: **removable** (phase 1 — `reachable()`'s own elapsed time, the only phase Option C proposes
skipping) versus **retained** (phases 2, 4, 6, 7, 8 and their own residual control-flow cost — everything
Option C must freshly re-execute per `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md`). See
`O3_R2_MEASUREMENT_CONTRACT.md` for the exact reporting schema.
