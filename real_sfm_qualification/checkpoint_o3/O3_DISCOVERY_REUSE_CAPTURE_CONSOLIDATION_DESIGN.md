# O3 — Discovery Reuse / Capture Consolidation Design (Summary)

**Status: O3 — DISCOVERY REUSE / CAPTURE CONSOLIDATION DESIGN — DESIGN/PROOF ONLY, COMPLETE.** No
production, integration, or lifecycle code has been modified. No SFM was run. No optimization is
implemented or authorized by this checkpoint. F1-R2 remains parked/unrun. Checkpoint G was not prepared.

## Governing rule

> Tangible savings, demonstrated redundancy, zero functional compromise.

## Governing question

> Within the Normalizer's required post-Rebuild pathway, can expensive whole-shot rig discovery be
> safely reused across semantic capture boundaries where rig identity cannot have changed, while still
> performing fresh semantic reads whenever freshness is required?

Rebuild→Normalizer overlap itself is not treated as a newly discovered optimization target — the
Normalizer's job is to normalize the state native Rebuild produces, every time, warm or not (confirmed
by O2-R1's own measured warm-run reconstruction counts). The question this checkpoint answers is
narrower, as stated above.

## Controlling evidence

- Production Normalizer SHA-256: `cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
- Astra source baseline commit: `dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`
- O2/O2-R1 empirical basis: native Rebuild `MATERIAL` (not optimized — an SFM primitive, remains
  required); discovery `MATERIAL`; tree construction `IMMATERIAL`; outer-POST→composer-before
  `SOURCE_EQUIVALENCE_SUPPORTED`; composer-after→terminal `RECONCILED_PATH_REUSE_PLAUSIBLE` — neither
  currently authorizing implementation.

## Deliverables in this checkpoint

1. `O3_DISCOVERY_CALL_MAP.md` — every `discover_rig_context()` call, exact execution order, for the
   reconciled path (5 calls) and both native-only-fallback sub-cases (3 and 2 calls respectively).
2. `O3_MINIMAL_DISCOVERY_REUSE_OBJECT.md` — the minimal safe reusable data (a small, plain-Python
   `DiscoveryIdentityToken`, explicitly excluding the two live native references `rig`/`registry`), with
   a required stale-state guard.
3. `O3_OUTER_POST_COMPOSER_BEFORE_DESIGN.md` — Design A (full snapshot reuse) vs. Design B (discovery
   reuse only) — mechanical result `DISCOVERY_REUSE_ONLY`.
4. `O3_TERMINAL_DISCOVERY_REUSE_DESIGN.md` — `TERMINAL_DISCOVERY_REUSE_SAFE_ON_RECONCILED_PATH` (and
   fallback sub-case A), `FRESH_TERMINAL_DISCOVERY_REQUIRED` on fallback sub-case B.
5. `O3_THEORETICAL_SAVINGS.md` — ~0.35-0.38 s / ~4.9-5.8% of measured runtime per candidate, this
   fixture; extrapolation to larger scopes explicitly labeled unverified.
6. `O3_RESOURCE_LIFETIME_IMPLICATIONS.md` — neither candidate touches the separately-confirmed
   `capture_tree()` closure-cycle mechanism; no new retained live objects; no persistent cache.
7. `O3_IMPLEMENTATION_RECOMMENDATION.md` — **one** candidate recommended for a future implementation
   round: outer-POST→composer-before discovery reuse (Design B). Not authorized by this document.
8. `O3_FUTURE_QUALIFICATION_PLAN.md` — the offline + real-SFM plan that would apply if Candidate 1 is
   separately authorized. Not executed.

## Section 9 — explicitly frozen (unchanged by anything in this checkpoint or the recommended candidate)

- Native Rebuild requirement (remains a required, unmodified SFM primitive).
- PRE eligibility semantics.
- Native guards.
- Native Master protection.
- Command-scoped authority lease.
- Master validation.
- Exact literal/folding semantics.
- Contextual classification/planning (`preflight_reconciliation_plan`, `derive_generic_uniformity_plan`
  — untouched; the recommended candidate operates strictly inside `production_generic_composer`'s own
  discovery step, after classification/planning has already completed).
- Helper/toe/finger translations.
- Destination ordering.
- Metadata/selectability.
- Isolation validation.
- Target callback guards/re-resolution (`contextualizer_resolve_resume_target()` — untouched; the
  recommended candidate's own token never crosses this boundary).
- Failure behavior (fail-closed guard falls back to today's exact behavior on any doubt).
- Native-only fallback correctness (both sub-cases — neither reaches the code path the recommended
  candidate touches at all).
- Terminal validation (unless separately authorized — `O3_TERMINAL_DISCOVERY_REUSE_DESIGN.md` is a
  distinct, deferred candidate, not part of this round's recommendation).
- No runtime DME cache across callbacks (the proposed token is not a cache — see
  `O3_RESOURCE_LIFETIME_IMPLICATIONS.md`).

No warm-path shortcut. No stale semantic cache. No F1-R2. No Checkpoint G.

## What happens next

Nothing, without separate explicit authorization. This checkpoint is design/proof only, per its own
governing instruction. If Candidate 1 is authorized for implementation, `O3_FUTURE_QUALIFICATION_PLAN.md`
is the plan that governs how it would be qualified before acceptance.
