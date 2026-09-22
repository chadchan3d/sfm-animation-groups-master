# Astra Holistic Review Brief — Master → Sidecar → Shared Authority System

**This is Astra's controlling assignment.** `docs/qualification/ASTRA_REPO_INDEX.md` is a
navigation aid for this review, not a constraint on what you may inspect.
`docs/qualification/R3_B2C_D_ASTRA_HANDOFF.md` is historical/supporting planning context written
before this review's remit was broadened — it is **not** the controlling scope for this review,
and you are not required to reach the same conclusions it anticipated.

## Mission

Audit the current Master → sidecar → shared-authority system holistically against the actual
product goals and against your prior architecture requirements.

Treat the repository, implementation, tests, and evidence as the review substrate. Do not assume
our PASS labels, stage boundaries, architecture conclusions, or proposed next steps are correct.

Your job is **not** merely to design "B2C-D." That name is one candidate framing among several this
review may or may not adopt. Do not let it constrain what you consider next.

## Product goals

The project is trying to deliver:

1. a production-quality **SFM Control Group Normalizer** that organizes controls consistently
   across heterogeneous SFM models;
2. a reusable semantic authority derived from the Animation Groups Master rather than duplicating
   model-name logic;
3. a second consumer, **Character Preset Manager**, that can use the same authority where
   appropriate without inheriting irrelevant Normalizer presentation semantics;
4. a maintainable product that works in the real SFM Python 2.7 / Qt environment;
5. safe failure behavior and reasonable runtime/memory cost;
6. a path to shipping, not an indefinitely expanding qualification program.

## Review questions

Determine:

- whether the shared authority is now fit for purpose;
- whether prior architecture requirements were implemented in substance;
- whether any material correctness/lifecycle/ownership/freshness/resource/deployment defects
  remain;
- whether the current consumer/view abstraction is appropriate;
- whether the Normalizer can now be connected directly, or whether another intermediate hardening
  step is genuinely necessary;
- what exact production integration seam should be used;
- how authority lifetime/freshness should work during a Normalizer operation;
- what must be tested offline vs in real SFM;
- whether the final authorization → native-use race is materially dangerous and how, if at all, it
  should be controlled;
- whether live target/scope enumeration belongs before integration, during integration, or only in
  real-SFM qualification;
- whether CPM's long-lived consumer model needs a different view/lifetime strategy from Normalizer;
- whether both tools can share one projection or should share the broker while using different
  projections;
- whether CPM's recorded provider generation/source provenance should remain diagnostic only;
- whether authority-generation changes should invalidate an open CPM semantic scope;
- what implementation sequence gets to a usable production Normalizer fastest without compromising
  correctness.

## Priority classification

Classify every finding as:

### RELEASE / INTEGRATION BLOCKER
Must be resolved before connecting/promoting the Normalizer.

### IMPORTANT BUT DEFERRABLE
Real risk or debt, but not required for the next production milestone.

### NICE-TO-HAVE HARDENING
Useful improvement that should not delay a working product.

Justify why each finding belongs in its class.

## Efficiency requirement

> Favor work that materially reduces risk to the actual products. Do not expand the qualification
> program merely because additional theoretical checks are possible. If current evidence already
> makes a proposed test redundant, say so. If one decisive real-SFM test can replace a large
> synthetic campaign, prefer the decisive test.

## Independence requirement

> You may reject or reorder our current B2C-D / live-runtime sequence if the evidence supports
> doing so. Derive the next steps from the product goals and current system, not from our stage
> labels.

## Character Preset constraint

> Treat Character Preset Manager as a known second consumer, not as a reason to over-generalize the
> first production integration. Flag Normalizer-specific architectural dead ends, but do not
> require speculative abstractions that CPM does not demonstrably need.

## Requested output

Return:

1. holistic verdict on current shared-authority architecture;
2. any material defects, each with evidence/path;
3. whether the system is ready to begin Normalizer production integration;
4. recommended Normalizer integration architecture/seam;
5. exact next implementation/testing sequence;
6. what should be tested in real SFM;
7. implications for CPM integration;
8. blocker / deferrable / nice-to-have classification;
9. what existing tests/evidence should NOT be repeated;
10. final recommended milestone sequence to reach a shippable Normalizer.

Do not merely confirm our plan.
