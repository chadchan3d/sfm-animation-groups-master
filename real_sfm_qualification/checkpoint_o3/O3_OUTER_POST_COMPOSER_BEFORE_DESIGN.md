# O3 — Outer POST → Composer-Before Consolidation Design

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Nothing
here authorizes an optimization. This document evaluates two candidate designs for the strongest
identified redundancy — it does not choose to implement either.

## Basis

`O3_DISCOVERY_CALL_MAP.md` (discovery call #3) and `O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`
(`SOURCE_EQUIVALENCE_SUPPORTED`) jointly establish: the interval between the outer `NATIVE_POST` capture
completing and `production_generic_composer`'s own `PRODUCTION_GENERIC_COMPOSER_PRE` capture contains no
DME write, no native mutation, and no Qt-yield anywhere — exhaustively confirmed by whole-file grep for
every write-capable primitive in the entire production Normalizer.

## Design A — Full POST snapshot reuse

Outer POST's own already-captured snapshot (`post`, already passed as a parameter into
`production_generic_composer(root, pre, post, master, shot, aset, plan, uniformity_plan)`, line
7162-7170) becomes composer-before's own input directly — `production_generic_composer` never calls
`capture_snapshot_explicit`/`capture_tree`/`discover_rig_context` again for its own "before" slot at all.

## Design B — Discovery reuse only

`production_generic_composer` still performs its own fresh semantic tree capture (still calls
`capture_snapshot_explicit`/`capture_tree` for its own "before" slot, unconditionally) — but skips the
expensive `reachable(scene)` broad-discovery walk by reusing the `DiscoveryIdentityToken` (see
`O3_MINIMAL_DISCOVERY_REUSE_OBJECT.md`) computed at outer NATIVE_POST time, subject to the stale-state
guard, instead of calling `discover_rig_context()` a second time.

## Comparison

| Criterion | Design A (full snapshot reuse) | Design B (discovery reuse only) |
|---|---|---|
| Exact semantic equivalence | Identical by construction (literally the same object) | Identical by construction *for the discovery-derived fields*; group/control tree content is independently, freshly re-verified to match |
| Freshness | **None** — no semantic operation re-runs for this slot at all | Preserved for the capture (tree/group/control state); relaxed only for discovery identity, which is proven unchanged |
| Missing-root detection | **Skipped entirely** — `aset.GetRootControlGroup()` check (line 3557-3567) never runs again for this slot | **Still runs**, fresh, every time |
| Duplicate-path detection | **Skipped entirely** — `capture_tree()`'s own `walk()` duplicate-path check (line 1214-1218) never runs again for this slot | **Still runs**, fresh, every time |
| Ownership validation | Skipped (inherited from the already-validated outer POST result) | Skipped for the *discovery* portion (inherited, but proven correct for this interval); capture-level checks still run fresh |
| Rig uniqueness | Skipped (inherited) | Skipped for discovery (inherited, proven correct); stale-state guard re-checks target identity |
| Target identity | Not re-verified at all for this slot | Re-verified via the stale-state guard (`handle(aset)` comparison) |
| Exception behavior | **Cannot raise** — no code runs, so composer-before's own current exception surface (`ProbeError` on duplicate paths, missing root, etc.) is **removed entirely** for this slot | **Unchanged** — the same exceptions the current fresh capture can raise today can still be raised, since the capture still runs |
| Native mutation risk | None in this interval (proven) | None in this interval (proven) |
| Qt/reentrancy risk | None in this interval (proven) | None in this interval (proven) |
| Live-object retention | None *beyond* what already exists — `post` is already alive as a parameter regardless of this design | Requires holding the tiny `DiscoveryIdentityToken` (plain data) between the two call sites — negligible |
| Memory/lifetime implications | No worse than status quo (no new retention) | Negligible new retention (a small dict of ints/strings/a set) |
| Implementation complexity | Low — skip the call, use `post` directly | Moderate — thread the token through (new parameter on `production_generic_composer`'s signature, since it does not currently accept `rig_context`); implement the stale-state guard; if `capture_snapshot_explicit`'s own body needs live `rig`/`registry` objects (not just their handles), a cheap handle-based re-resolution is needed (materially cheaper than `reachable(scene)`, but adds a small implementation step not required for full reuse) |
| Expected savings | One skipped discovery call's cost (~0.15-0.19s) **plus** the already-established-immaterial tree-construction cost (~0.002s) | One skipped discovery call's cost (~0.15-0.19s) — effectively the **same material savings** as Design A, since tree-construction was already measured `IMMATERIAL` in O2-R1 |

## Why not Design A merely because the exercised values were equal

O2 and O2-R1's own real runs found the outer-POST and composer-before captures hash-equivalent — but
equal *output* does not mean the *validation work that produced it* was redundant. Design A does not
skip a redundant *recomputation of the same answer*; it skips the **entire validation opportunity** for
composer-before's own slot (missing-root check, duplicate-path check) — even though that opportunity
happens to be redundant *today*, on the *current* codebase, for *this* interval. Design B preserves that
validation opportunity at essentially the same cost savings, because the validation itself
(`capture_tree()`'s own walk) was already independently measured `IMMATERIAL` — there is no material
cost benefit to removing it, only a correctness-strength cost.

## Mechanical result

**`DISCOVERY_REUSE_ONLY`**

Design B captures effectively all of the material savings available in this interval (the discovery
call's own `reachable(scene)` cost) while preserving strictly more of the existing validation surface
than Design A. Per the governing preference for "the smallest change that preserves the strongest
correctness semantics," Design B is the recommended direction if this candidate proceeds to
implementation — see `O3_IMPLEMENTATION_RECOMMENDATION.md`. Neither design is authorized for
implementation by this document.
