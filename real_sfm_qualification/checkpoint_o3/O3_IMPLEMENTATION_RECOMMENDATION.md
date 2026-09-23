# O3 — Implementation Recommendation

**Status: DESIGN/PROOF ONLY. This document recommends; it does not implement or authorize.** No
production, integration, or lifecycle code has been modified. Implementation requires separate, explicit
approval and the qualification plan in `O3_FUTURE_QUALIFICATION_PLAN.md` to pass before any change is
made.

## Decision rule (restated)

A candidate proceeds to optimization design review only when: (1) demonstrated redundant work; (2)
material expected saving; (3) no weakened functional/validation semantics. Trivial cost is rejected
immediately even if technically redundant.

## Candidates considered

| | Candidate 1: outer-POST → composer-before discovery reuse | Candidate 2: composer-after → terminal discovery reuse |
|---|---|---|
| Demonstrated redundancy | `SOURCE_EQUIVALENCE_SUPPORTED` — exhaustive, no distinct procedural step in the interval | `RECONCILED_PATH_REUSE_PLAUSIBLE` — proven mutation-free, but terminal has a distinct procedural purpose the discovery-only reuse must not disturb |
| Branch gating required | Two-way (applies only when the reconciled path reaches composer at all) | Three-way (reconciled path + fallback sub-case A reuse; fallback sub-case B does not) |
| Theoretical saving (this fixture) | ~0.35-0.38 s, ~4.9-5.8% of measured runtime | Same magnitude |
| Implementation complexity | Lower — single, structurally clean interval | Higher — requires distinguishing three branch shapes correctly |

Both candidates pass the decision rule's three tests individually. Per explicit instruction not to
bundle optimizations, **at most one** proceeds.

## Recommendation

**Candidate 1: outer-POST → composer-before discovery reuse (Design B — discovery reuse only).**

Chosen over Candidate 2 because it delivers the same measured-magnitude saving with materially lower
implementation and correctness-review complexity (one branch condition instead of three), and its own
underlying proof (`O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`) is the structurally cleaner of the two
— the interval it covers contains no analog to terminal's own distinct undo-restore/protect-release/
Master-reassert procedural sequence. Candidate 2 remains a valid, separately-qualifiable candidate for a
future round; it is not rejected, only deferred in favor of the single-candidate constraint this round.

## Exact proposed change

Inside `production_generic_composer(root, pre, post, master, shot, aset, plan, uniformity_plan)`, the
existing line 7175-7178 (`before_rig = discover_rig_context(shot, aset)`) is replaced with: (a) accept a
new parameter carrying the outer NATIVE_POST discovery's own `DiscoveryIdentityToken` (requires extending
`production_generic_composer`'s own signature, and the one call site that invokes it, at line ~11897, to
pass this token through); (b) re-verify the stale-state guard (`handle(aset)` matches, `status` still
usable) against that token; (c) if the guard passes, construct a `rig_context`-shaped value from the
token (re-resolving `rig`/`registry` live references via a cheap handle-based lookup only if
`capture_snapshot_explicit`'s own body is confirmed to need them live, not just their handles — to be
resolved precisely during implementation, not assumed here) and pass it into the existing
`capture_snapshot_explicit(shot, aset, "PRODUCTION_GENERIC_COMPOSER_PRE", rig_context)` call unchanged;
(d) if the guard fails, fall back to today's exact behavior — a fresh `discover_rig_context()` call —
never silently proceed with a token that failed its own guard.

The **capture** itself (`capture_snapshot_explicit`/`capture_tree`, and everything downstream of it in
`production_generic_composer`'s own body) is **completely unchanged**.

## Exact branches affected

Only the reconciled supported-active-rig path (the only branch that ever calls
`production_generic_composer` at all, per `O3_DISCOVERY_CALL_MAP.md`).

## Exact branches unaffected

Native-only fallback (both sub-cases A and B) — neither ever reaches `production_generic_composer`.
`preflight_reconciliation_plan`, `derive_generic_uniformity_plan`, the PRE and NATIVE_POST captures
themselves, the composer-after capture, and the terminal capture are all unchanged.

## Preserved validations

- `aset.GetRootControlGroup()` / missing-root detection — unchanged, still runs fresh inside the
  (unchanged) capture call.
- `capture_tree()`'s own duplicate-group-path detection — unchanged, still runs fresh.
- All of composer's own downstream comparison/mutation logic (`failures` check, `desired`/`moved`/
  `already_correct` accounting) — entirely unchanged, operates on the (freshly captured) `before`
  snapshot exactly as today.

## New / still-required stale-state guard

Before consuming the reused token: `handle(aset) == token["expected_aset_handle"]` (target identity
unchanged since the token was computed) and `token["status"] == "SUPPORTED_ACTIVE_RIG"` (or whatever
status was captured, re-checked for usability). On guard failure, fall back to a fresh
`discover_rig_context()` call — never proceed with an unguarded or failed-guard token. This guard is the
single new piece of runtime logic this candidate introduces.

## Theoretical saving

~0.35-0.38 s measured-fixture savings (Fox + Mia, Selected Shots, one command) — see
`O3_THEORETICAL_SAVINGS.md` for the full table and the explicitly-labeled (unverified) extrapolation to
larger scopes. Tree-construction savings are not counted (already `IMMATERIAL`).

## Main correctness risk

The stale-state guard is the single point where an implementation bug could allow reuse of a token that
should have been invalidated. This risk is mitigated by: (a) the guard's own existence (fail-closed to a
fresh discovery on any doubt); (b) the interval being provably mutation-free *today*, per exhaustive
static proof, not merely assumed; (c) the token never crossing any boundary (Qt-deferred gap, shot
activation, target re-resolution) beyond the single proven-safe interval. The residual risk is a *future*
code change inside the proven-safe interval (e.g., a new validation step added between NATIVE_POST and
composer-before that does mutate DME state) silently invalidating this design's own premise without the
stale-state guard catching it, since the guard only checks target identity and status, not "did anything
mutate." This is a real, named risk, not eliminated by this design — see the required test below.

## Test required before authorization

At minimum, before any implementation is authorized: (1) an offline branch-specific equivalence test
proving the guarded-reuse code path produces byte-identical `capture_snapshot_explicit` output to the
current unconditional-fresh-discovery code path, for representative fixture data; (2) an offline
stale-token/guard-failure test proving the fallback-to-fresh-discovery path is exercised and correct when
the guard fails (e.g. a deliberately mismatched handle); (3) confirmation that native-only fallback (both
sub-cases) and the PRE-capture-unsupported path are byte-for-byte unchanged (since neither touches this
code path at all, this should be a structural/no-diff proof, not a new behavioral test); (4) a real-SFM
bounded comparison (see `O3_FUTURE_QUALIFICATION_PLAN.md`) — pre-change vs. candidate, on the same
`shot3` Fox+Mia Selected-Shots fixture, checking exact final semantic hashes, moved/already-correct
counts, authority lifecycle, native guards, isolation, resource behavior, discovery call count (must drop
from 10 to 8 for this fixture), and command timing.

No implementation is authorized by this document. Proceeding requires separate explicit approval.
