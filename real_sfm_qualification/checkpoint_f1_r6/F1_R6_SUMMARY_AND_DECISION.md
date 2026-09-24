# F1-R6 — Summary and Phase H Decision

**Status: DESIGN + OFFLINE-VERIFIED PROTOTYPE + JUSTIFIED REAL-SFM CHECKPOINT.** Not authorization to modify
production. O3 remains closed. No cross-boundary discovery reuse, topology caching, stale handles,
semantic-generation shortcuts, or immutable-topology assumptions are introduced anywhere in this
checkpoint. Every discovery call — legacy or candidate — performs a full, fresh, live observation, every
time.

## Phase G result

The offline adversarial parity suite (`test_f1_r6_adversarial_parity.py`) exercises 21 fixtures: simple
tree, shared-reference DAG, cycle, duplicate paths to the same element, no rig, one rig (two different
topologies), multiple competing rigs, registry absent, registry unique, registry ambiguous, target absent,
target unique, multiple candidate rigs with one match, malformed/null references, an attribute-access
exception (`GetTypeString` raising), a handle-access exception (`GetHandle` raising), an ordering-sensitive
layout (the matching rig visited last), a very large synthetic graph (1,500+ chained elements), zero
ownership, `RIG_CONTEXT_UNAVAILABLE`, and the scene-traversal edge case. Legacy and candidate are compared
on: status, `reachable_rig_count`, `matching_rig_count`, `rig_handle`, `registry_handle`, `owned_handles`,
`owned_names_in_order`, `hidden_groups`, selected-rig identity, and selected-registry identity — for every
fixture. **205/205 PASS, zero parity mismatches**, under the real embedded Python 2.7.5, both legacy and
candidate extracted/loaded from their own real source (legacy via verbatim line-range extraction from the
pinned production file; candidate via the actual prototype module), never retyped or reimplemented for the
test itself.

One defect was caught and corrected **in the test fixture construction itself, not in the parity logic**:
the real algorithm treats the matched `DmeRigAnimSetElements` binding record itself as `registry` (`registry
= registry_matches[0]`, where `registry_matches` holds binding records, not a separate object) — an early
fixture-builder draft incorrectly modeled a separate "registry" object. This was caught precisely because
every fixture's parity checks (legacy vs. candidate) passed even while the fixture's own "expected status"
assertions failed — proving the parity comparison itself was sound throughout, and the bug was isolated to
test-fixture construction, not the equivalence being tested.

## Phase H decision: **real-SFM parity checkpoint is justified**

Both required conditions from `F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_CONTRACT.md` are met: offline parity
is exact (zero mismatches across every adversarial category requested), and the design introduces no new
semantic risk beyond one already-disclosed, argued-to-be-non-novel reentrancy question.

### Read-only design confirmed valid — a genuine simplification over F1-R3/4/5

Direct re-reading of `discover_rig_context(shot, aset)`'s own first statement — `scene = scalar(shot,
"scene")` — confirms discovery reads the shot's own `scene` **attribute** directly; it does **not** call
`sfmApp.GetShotAtCurrentTime()` or depend on SFM's own playhead/active-shot state at all (unlike native
Rebuild, which F1-R3's own audit already established genuinely requires shot activation). This means the
real-SFM checkpoint needs **no shot activation, no native Rebuild, and no scene mutation of any kind** —
it can call `discover_rig_context(shot_record["shot"], target["anim_set"])` directly, for every one of the
62 targets in `instance.work`'s own order, exactly as recorded, with **zero risk of one observation
mutating the state the other observes** (nothing mutates anything). This is the "read-only parity design"
Phase H itself prefers, confirmed technically valid by direct source reading rather than assumed.

Consequently, per-target re-resolution (the narrow helper F1-R3/4/5 each needed, to guard against native
Rebuild potentially invalidating a stale `aset` reference between targets) is unnecessary here: since
nothing in this checkpoint ever calls native Rebuild, `target["anim_set"]`'s own object reference, as
already recorded in `instance.work`, remains valid for the checkpoint's own entire duration.

### Controlling for ordering bias

Per Phase H's own explicit concern ("If ordering legacy/candidate itself could materially bias memory
measurement, design matched phases... and explain why"): legacy's own larger, ~4,250-element-per-call
materialization could plausibly grow the process's `pymalloc` arenas in a way that makes a
*subsequently-measured* candidate look artificially cheap (reusing already-reserved space), or the reverse
if measured first. This checkpoint alternates which arm runs first **per target** (even-indexed targets:
legacy then candidate; odd-indexed targets: candidate then legacy) — each pair is measured immediately
adjacent in time to its counterpart (minimizing environmental drift within a pair), while the alternation
itself cancels out any *first-position* advantage/penalty in the aggregate, unlike running all-legacy-then-
all-candidate (or the reverse) as two separate blocks.

### Scope clarification versus the general "Real-SFM parity requirements"

This checkpoint does not run native Rebuild and does not make any branch-entry decision — it is a discovery
-only parity/resource measurement. The general requirement "exact branch distribution if branch-bearing
workload is used" therefore does not apply here (this workload is not branch-bearing); each target's own
`status` is still recorded and reported per-target for informational comparison, but no branch distribution
is asserted as a pass/fail gate. The 15-shots/62-targets/production-SHA/Master-SHA/normalized-copy-fixture
requirements all still apply and are enforced identically to every prior F1-R checkpoint.

## Known unresolved risks (carried forward, not resolved by this checkpoint)

1. Interleaved native calls during an ongoing traversal — argued not to be a qualitatively new exposure
   relative to legacy's own already-interleaved native calls (see `F1_R6_STREAMING_DESIGN_AND_EQUIVALENCE_
   CONTRACT.md`), but not proven safe either; remains `UNRESOLVED`, consistent with the O3 series.
2. `CElementTreeTraversal`'s own unverified scope semantics and `FirstAttributeReferencingElement`'s own
   unverified reverse-lookup completeness (see `F1_R6_SWIG_ITERATION_INVESTIGATION.md`) — neither used,
   neither pursued, both recorded as leads for a possible future, separately-authorized investigation.
3. Whether reduced peak simultaneous wrapper retention actually translates into a measurable process-level
   resource improvement is exactly what the real-SFM checkpoint measures — not assumed here.

## Explicit non-authorization

This checkpoint does not patch the production Normalizer, does not touch authority/broker code, and does
not close F. Even excellent prototype parity and resource results do not themselves authorize production
implementation — per explicit instruction, that decision returns to independent review before any
production change is considered.
