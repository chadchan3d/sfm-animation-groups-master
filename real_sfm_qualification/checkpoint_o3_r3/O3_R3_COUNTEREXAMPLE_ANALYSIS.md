# O3-R3 — Counterexample Analysis

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. This
document mechanically applies Astra's six hypothetical cases to the reuse object named in
`O3_R3_REUSE_OBJECT_DECISION.md` (archetype (b): the complete `reachable(scene)` object list retained from
native POST, with `typ()`/`HasAnimationSet()` re-filtering run fresh over that retained list at composer
entry). Per instruction, this test is applied **independently** of whether an authoritative mechanism or an
immutable-interval proof exists — both of which are separately established absent in
`O3_R3_ENUMERATION_VALIDITY_MECHANISM_SEARCH.md` and `O3_R3_INTERVAL_IMMUTABILITY_PROOF.md`. This document
answers a narrower, structural question: even granting (for the sake of this test only) that the interval
cannot mutate, is the reused enumeration itself logically sufficient to guarantee correctness? A design
cannot survive if any case below can silently produce a supported composer-entry context where fresh
discovery would materially differ.

## A. Additional matching rig appears

A second `DmeRig`-typed object, call it B, becomes reachable from `scene` and matches `aset` (via
`HasAnimationSet`) sometime after native POST's own `reachable(scene)` call but before composer entry.

**Would the retained enumeration necessarily detect/preclude it?** No. The retained list is exactly the set
`reachable(scene)` returned at native-POST time. B, by construction of this scenario, was not a member of
that returned set (it was not yet reachable). Re-running `typ()`/`HasAnimationSet()` filtering over the
retained list — however freshly, however correctly — can only ever examine objects that were already in the
list. B is structurally invisible to this re-filter. Fresh discovery, by contrast, would re-run
`reachable(scene)` itself and would find B. **Fails.**

## B. Selected rig becomes unreachable but remains readable

The retained candidate rig A is still present in the retained list (a live wrapper referencing an
allocated C++ object), and its own `typ()`/`HasAnimationSet()` checks still succeed when freshly re-run —
but A itself is no longer reachable from `scene` in the *current* scene graph (e.g., it was detached from
its parent, orphaned, but not destroyed).

**Would the retained enumeration necessarily detect/preclude it?** No. Reachability is a property of the
*current* scene graph, established only by walking it — exactly the operation being skipped. A retained
wrapper object has no intrinsic "am I still reachable" property to query; `typ()` and `HasAnimationSet()`
both operate on the object directly and say nothing about its current position (or absence) in the graph.
Fresh discovery, by re-walking `reachable(scene)`, would not find A at all and would correctly fail to
match it (or would match a different, now-actually-reachable rig instead). **Fails.**

## C. Old rig replaced by new matching rig

A becomes unreachable (as in case B) **and** a new object B becomes reachable and matches `aset` (as in
case A) — a combined replacement.

**Would the retained enumeration necessarily detect/preclude it?** No — this is the union of cases A and B,
and both individually fail for the reasons above. Worse: a naive design might successfully "re-validate" A
(A's own native object may still respond to `typ()`/`HasAnimationSet()` without raising, since it has not
been destroyed, only detached), producing a *confident, no-exception* result built on a rig that fresh
discovery would never have selected at all. This is the most dangerous of the six cases: no exception is
raised in the reused path, yet the answer differs from what fresh discovery would produce. **Fails.**

## D. New current rig has a registry read that would raise

A new rig B (as in case A) is the *actually correct* current candidate, and B's own registry resolution
(`arr(B, "animSetList")`, `arr(registry_B, "elementList")`, or similar) would raise a Category 2 exception
if freshly discovered (per `O3_R3_FAILURE_CONTRACT_CORRECTION.md`'s enumeration of these unwrapped calls).

**Would fresh composer-before behavior still encounter that exception before mutation?** Yes — true fresh
discovery always would, because it re-walks the scene, finds B, and attempts B's own registry reads, which
raise before `production_ensure_group_path()`'s own first write (see
`O3_R3_FAILURE_CONTRACT_CORRECTION.md`). **Would the reused-enumeration design encounter it?** No — the
reused design never examines B at all; it only re-validates the *retained* candidate A, which may pass its
own checks cleanly. The reused design would therefore **silently proceed to write** in a scenario where
today's actual production code would abort first. This is a genuine correctness/safety regression, not
merely a missed optimization opportunity — it is precisely the scenario `O3_R3_REUSE_OBJECT_DECISION.md`'s
"what it does not prove" column warned about for every candidate archetype. **Fails, and fails in the
most consequential direction (a write proceeds where production would have aborted).**

## E. Scene graph changes without target animation-set handle changing

The `aset` pointer itself is unchanged (the existing pointer-stability check at `run_target_transaction`
line 11225-11233 continues to pass), but the surrounding scene's rig topology changes — e.g., a `DmeRig`
elsewhere in the reachable graph is added, removed, or reparented, without touching `aset` directly.

**Would the retained enumeration necessarily detect/preclude it?** No. The `aset_ptr` equality check
guards only the animation-set target itself; it says nothing about the rig topology around it, which is
exactly what `reachable(scene)` traversal exists to (re-)discover. A retained enumeration is blind to any
topology change that does not happen to invalidate the one pointer this existing check examines. **Fails.**

## F. Native wrapper/handle recycling

The C++ object underlying retained candidate A is destroyed and its native handle slot is reused by an
unrelated new object, while the Python-side wrapper object still referenced by the retained enumeration
continues to exist.

**Would the retained enumeration necessarily detect/preclude it?** No, and this case is qualitatively worse
than the others: `typ()` and `name()` both catch `Exception` internally and degrade gracefully (`typ()`
falls back to the wrapper's own Python class name; `name()` yields `u"<UNNAMED>"`) — but `handle()` (line
860-861, `return int(obj.GetHandle())`) has **no** internal exception handling at all, and calling any
method on a Python wrapper whose underlying C++ object has been destroyed is not guaranteed to raise a
catchable Python exception in the first place — depending on how the SWIG binding and the engine's own
object-lifetime model behave, this can be a genuine memory-safety hazard (a crash or undefined behavior),
not merely a wrong answer. **This project has no evidence establishing that stale-wrapper access here is
safe**, and no evidence establishing it is unsafe either — it is simply unverified, and the consequence of
being wrong is categorically worse than any other case in this table. **Fails, and fails in a way this
project cannot bound the severity of.**

## Summary

| Case | Detected/precluded by the retained-enumeration design? | Consequence if missed |
|---|---|---|
| A. Additional matching rig appears | No | Wrong (stale) rig used; correct rig ignored |
| B. Selected rig becomes unreachable but remains readable | No | Stale rig used as if still current |
| C. Old rig replaced by new matching rig | No | Combined A+B; confident wrong answer, no exception |
| D. New current rig has a registry read that would raise | No | **Write proceeds where production would have aborted** |
| E. Scene graph changes without `aset` handle changing | No | Existing pointer check provides no protection here |
| F. Native wrapper/handle recycling | No | **Unbounded severity — potential memory-safety hazard, not just a logic error** |

All six cases fail. None is detected or precluded by any of the reuse-object archetypes evaluated in
`O3_R3_REUSE_OBJECT_DECISION.md` — the failure is structural (a stale snapshot cannot detect changes to the
set it snapshotted), not an implementation detail fixable by adding more re-validation of the retained
object itself. Per the instruction this document is answering: "A design cannot survive if any case can
silently produce a supported context where fresh discovery would materially differ" — that condition is met
by every one of the six cases.
