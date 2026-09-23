# O3-R3 — Reuse Object Decision

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Nothing
here authorizes an optimization. This document resolves the reuse-object ambiguity Astra's second review
identified between `O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` and `checkpoint_o3_r2`'s own instrumentation
choices — it does not itself decide whether Option C survives; see `O3_R3_ENUMERATION_VALIDITY_DECISION.md`
for the final decision, which this document's own findings feed into.

## The ambiguity, stated precisely

`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md` (section "Option C") describes reusing "the candidate rig
identity that `reachable(scene)` + the `DmeRig`-type filter **already produced**" — prose that describes
reusing the *outcome* of both the traversal (`reachable(scene)`) **and** the candidate-filtering loop
(`typ(obj) != "DmeRig"` / `obj.HasAnimationSet(aset)`, `discover_rig_context()` lines 3334-3344) — i.e., a
single, already-identified candidate rig object (in practice, `matches[0]`, since the unambiguous-match
case is the only one that reaches `SUPPORTED_ACTIVE_RIG`).

`checkpoint_o3_r2`'s own instrumentation (`O3_R2_MEASUREMENT_CONTRACT.md`, "Decision computation") measured
a **different** object as the sole removable quantity: `phase_1_reachable_traversal_seconds` only — the
elapsed time of `reachable(scene)` itself (plus the `scalar(shot,"scene")` call that feeds it). Phase 2
(the `typ()`-based candidate-filtering loop) was explicitly measured as **retained**, not removable —
`O3_R2_DISCOVERY_PHASE_MAP.md` row 2 lists it as work Option C "must freshly re-execute."

These are two structurally different reuse objects:

- **O3-R1's prose** implies reusing a single, already-*identified* candidate rig (post-filtering).
- **O3-R2's measurement** implies reusing only the raw *traversal result* (`objs`, the list `reachable()`
  returns — up to ~4,250 live native-wrapper objects in this fixture, per Astra's own cited figure), with
  the `DmeRig`-type filter and `HasAnimationSet()` check re-run fresh over that retained list.

Astra is correct that these were never reconciled. This document reconciles them.

## Candidate reuse-object archetypes, evaluated

| Property | (a) Single identified candidate rig (O3-R1's prose) | (b) Raw `reachable(scene)` object list (O3-R2's measured quantity) | (c) Candidate `DmeRig`-typed subset only (`rigs`, before the `HasAnimationSet` filter) |
|---|---|---|---|
| Exact type | One live native `DmeRig` Python/SWIG wrapper object (`matches[0]`) | `list` of up to ~4,250 live native Python/SWIG wrapper objects (heterogeneous element types) | `list` of live native `DmeRig`-typed wrapper objects only (a small subset of (b)) |
| Contains live DME/native wrappers? | Yes — one live wrapper | Yes — every element is a live wrapper | Yes — every element is a live wrapper |
| Cardinality in this fixture | 1 (the unambiguous-match case; discovery aborts to a non-`SUPPORTED_ACTIVE_RIG` status otherwise) | Up to ~4,250 (bounded by `reachable()`'s own `max_elements=50000` default) | Small — the count of `DmeRig`-typed objects among the ~4,250 reachable objects; not separately measured this project, expected single-digit to low tens |
| Lifetime if retained | Would need to survive from native POST (`run_target_transaction` line 11482) through composer entry (`production_generic_composer` line 7175) — spans the entire interval audited in `O3_R3_INTERVAL_IMMUTABILITY_PROOF.md` | Same span, but for every one of ~4,250 objects simultaneously | Same span, for the smaller `DmeRig` subset |
| What it proves, if valid | "This specific native object was a `DmeRig` matching this `aset` at native-POST time" | "These specific native objects were reachable from `scene` at native-POST time" | "These specific native objects were `DmeRig`-typed and reachable at native-POST time" |
| What it does **not** prove | Whether it is still reachable now; whether it is still the *only* matching rig now; whether a *different* rig has since become the correct candidate; whether the underlying C++ object still exists | Whether the *current* reachable set is identical to this retained set (objects added or removed since native POST are invisible to a re-filter over this stale list); whether any retained wrapper's underlying C++ object still exists | Same gap as (b), narrowed to `DmeRig`-typed objects only — an object that became a matching `DmeRig` *after* native POST (e.g. a newly-attached rig) is absent from this retained subset by construction |
| What would invalidate it | Rig deletion/replacement; scene topology change adding a competing rig; the wrapper's underlying native handle being recycled | Any addition or removal of a reachable object between native POST and composer-before; any object's underlying C++ instance being destroyed | Same as (b), for the narrower subset |

## Why the choice between (a)/(b)/(c) does not change the outcome

All three archetypes share the same structural defect: each is a **snapshot of "what was true at native-POST
time,"** and none of them can be re-validated into "what is true right now" without re-running the one
operation being avoided — `reachable(scene)`'s own full scan. Freshly re-checking `typ()`/`HasAnimationSet()`
against a *retained* list (archetype (b) or (c)) can only ever re-confirm or reject members already present
in that list; it structurally cannot discover a rig that became reachable, or a rig that was replaced by a
different native object, **after** the list was captured — because such a rig was never enumerated into the
retained set in the first place. Freshly re-validating a *single* retained candidate (archetype (a)) has the
identical blind spot at smaller scale. This is exactly Astra's own framing: "the decisive missing property...
reused enumeration is still complete and applicable... do not answer these with target-handle equality or
local validation of A." See `O3_R3_COUNTEREXAMPLE_ANALYSIS.md` for the mechanical case-by-case confirmation
of this claim (cases A, C, and E specifically require re-scanning the reachable set to detect; no retained
object, of any of the three archetypes, can substitute for that re-scan).

## Explicit choice

**If Option C were pursued** (it is not — see `O3_R3_ENUMERATION_VALIDITY_DECISION.md`), the reuse object
that must be named is **archetype (b): the complete `reachable(scene)` object list**, because that is the
quantity `checkpoint_o3_r2`'s own real-SFM measurement actually classified as removable
(`phase_1_reachable_traversal_seconds`) — not archetype (a), which was O3-R1's own imprecise prose and is
**not** what was measured. Retaining only archetype (a) or (c) would not match the measured savings figure
at all (Phase 2's `typ()`-filtering cost, already measured and classified retained, would still need to run
over *something* — and running it over nothing produces no candidates). This resolves the ambiguity Astra
identified: **O3-R2 measured a much larger, much higher-risk reuse object than O3-R1's prose described**,
and the two documents must not be read as describing the same design. This document does not retain
multiple competing designs going forward — archetype (b) is the single named candidate for every downstream
section of this checkpoint (lifetime constraint in `O3_R3_ENUMERATION_VALIDITY_DECISION.md` section 7, and
the counterexample analysis).

## Lifetime constraint, addressed per instruction (see also main decision document section 7)

Since the final decision is `DO_NOT_IMPLEMENT` (see `O3_R3_ENUMERATION_VALIDITY_DECISION.md`), no
retention lifetime is authorized or specified for implementation. For completeness, had archetype (b)
survived sections 2-4, it would have required: acquisition immediately after `reachable(scene)` returns at
native POST (`run_target_transaction` line 11482's own `discover_rig_context()` call); release no later
than the end of that same `run_target_transaction` call for that target (never stored on `self`, never
shared across the `QTimer.singleShot`-deferred per-target boundary that separates one target's processing
from the next); release on both the success path and every exception path (the existing `try/finally`
structure already spanning native Rebuild through undo-restore, lines 11388-12029, would be the natural
owner). This is not a recommendation to build such a mechanism — see the complexity gate in
`O3_R3_ENUMERATION_VALIDITY_DECISION.md` section 8.
