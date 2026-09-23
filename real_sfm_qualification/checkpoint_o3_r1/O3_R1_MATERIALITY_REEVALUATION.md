# O3-R1 — Materiality Re-Evaluation

**Status: DESIGN/PROOF CORRECTION ONLY.** No production, integration, or lifecycle code has been
modified. No new measurement has been taken — this document reasons from O2-R1's own existing figures
plus source-level structural analysis; it does not claim a measurement it does not have.

## Gross saving ceiling (unchanged from O3)

One full `discover_rig_context()` call removed per applicable target, on the supported-active-rig
composer-entry path only: **≈ 0.17-0.19 s/target** (O2-R1's own measured mean, fresh vs. already-normalized,
`shot3` Fox + Mia). This was O3's own figure, and it remains the correct *gross* ceiling — Option C does
not change what a *fully* eliminated discovery call would be worth.

## Why gross ceiling ≠ net candidate saving under the corrected design

O3's own original design assumed the *entire* discovery call's cost could be avoided (Option B: trust a
token, skip everything). The corrected design (Option C,
`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md`) does **not** skip the entire call — it skips only the
`reachable(scene)` broad-traversal-plus-filter portion, while freshly re-executing every Category 1 and
Category 2 discovery-derived validation read (`arr(rig,"animSetList")`, registry uniqueness,
`arr(registry,"elementList")`, ownership intersection, `arr(registry,"hiddenGroups")`, the associated
`handle()` calls). The **net** saving is the gross ceiling minus whatever these re-executed reads
themselves cost.

## What can be reasoned from source structure alone

`reachable(scene)` (line 1006-1039) is the **only** operation in `discover_rig_context()`'s own call
chain whose cost scales with the **whole shot's own scene complexity** — it walks every element reachable
from `shot.scene` via `element_ref_pairs`/`iter_attributes`, capped at 50,000 elements, entirely
independent of how large or small the *target's own* rig actually is. Every operation Option C proposes
re-executing fresh (`arr(rig,"animSetList")`, `arr(registry,"elementList")`, `arr(registry,"hiddenGroups")`,
the ownership-intersection set operations, the `handle()` calls) is bounded by the **rig/registry's own
local size** — proportional to the target's own control count and rig structure, not the shot's total
scene complexity. For a shot containing many unrelated props/lights/cameras/other models (as
qualification-fixture shots plausibly do, beyond just the 1-2 selected targets), this structural
asymmetry makes it **plausible** that `reachable(scene)` dominates `discover_rig_context()`'s own total
cost.

**This is reasoning, not measurement.** O2-R1 measured `discover_rig_context()` as a single, undivided
~0.17-0.19 s figure — it did not separately instrument the traversal-only portion versus the
downstream-validation portion. This document does not convert plausibility into a claimed percentage.

## The specific measurement needed (not run)

A finer-grained instrumentation of `discover_rig_context()` itself — timing `reachable(scene)` (plus the
`DmeRig`-type filter loop over its results) separately from everything after it in the same function body
— for the same bounded `shot3` Fox + Mia fixture, would directly answer: what fraction of the measured
~0.17-0.19 s is the traversal Option C proposes skipping, versus the validation reads Option C proposes
keeping. This is the smallest additional measurement that would convert this document's plausibility
argument into a defensible net-saving figure. **Not run as part of this correction round**, per explicit
instruction.

## Provisional assessment

Given the structural asymmetry (one O(scene-size) operation vs. several O(rig-size) operations), a net
saving in the same order of magnitude as the gross ceiling (i.e., most of the ~0.17-0.19 s/target, not a
small fraction of it) is plausible but **not proven**. Declaring a specific net percentage without the
split measurement would repeat exactly the class of overclaim Astra flagged in O3 — this document
deliberately does not do that.

## Consequence for the final decision

See `O3_R1_DISCOVERY_REUSE_CONTRACT_CORRECTION.md` (section 10) for the formal decision. The corrected
design (Option C) is judged **correctness-sound** by this and the companion documents in this round —
but the **net benefit magnitude is not yet established with evidence**, which is a distinct question from
correctness. This asymmetry between "the design is now safe" and "the design's net payoff is unverified"
is exactly the gap `MORE_MEASUREMENT_REQUIRED` exists to name.
