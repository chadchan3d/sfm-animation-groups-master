# O3 — Future Qualification Plan (Candidate 1 Only)

**Status: PLAN ONLY. NOT EXECUTED.** This is the qualification plan that would apply *if and only if*
Candidate 1 (`O3_IMPLEMENTATION_RECOMMENDATION.md`) is separately authorized for implementation. No
implementation checkpoint is prepared or executed by this document. No production, integration, or
lifecycle code has been modified.

## Scope discipline

Bounded to the same established fixture this entire O1→Astra→O2→O2-R1→O3 chain has used: `shot3`,
Selected Shots, Fox (`foxmccouldwm1`) + Mia (`mia1`). Broader scope (All Shots, other shots) is
considered only *after* this bounded comparison passes — not prepared now.

## Offline qualification (before any real-SFM run)

- **Branch-specific equivalence**: extract the modified `production_generic_composer` (guarded-reuse
  version) and the current unmodified version verbatim from their respective sources; feed both identical
  synthetic `(shot, aset)` fixture data (or, if feasible, real captured PRE/NATIVE_POST data from an
  already-accepted checkpoint artifact); assert byte-identical `capture_snapshot_explicit` output
  (aggregate hash + all per-field hashes, same discipline `checkpoint_o2`'s own witness comparison
  already uses) between the two.
- **Stale-token/reuse-failure test**: construct a deliberately invalidated token (mismatched
  `handle(aset)`, or a non-`SUPPORTED_ACTIVE_RIG` status) and assert the guard correctly falls back to a
  fresh `discover_rig_context()` call — never silently proceeds with the bad token. Assert the fallback
  path's own output is identical to today's unconditional-fresh-discovery behavior.
- **Missing-root/duplicate-path behavior unchanged**: since the capture itself is untouched, assert
  (via a structural diff of the modified function against the original, not a new behavioral test) that
  `capture_tree()`'s own duplicate-path `ProbeError` and `capture_snapshot_explicit`'s own missing-root
  `ProbeError` are reachable exactly as before — the guard only gates the *discovery* call, never the
  capture call.
- **No live DME retention beyond allowed lifetime**: an offline test analogous to
  `checkpoint_o2/test_capture_tree_closure_lifetime.py`'s own technique — construct the token, hold it
  only within the proposed interval, confirm it (and specifically the two live-reference fields, `rig`/
  `registry`, which the token itself never carries per `O3_MINIMAL_DISCOVERY_REUSE_OBJECT.md`) does not
  leak past the single target's own transaction scope.
- **Native-only fallback unchanged**: a structural/no-diff proof that neither fallback sub-case's own
  code path is touched by the change at all (the change lives entirely inside
  `production_generic_composer`, which neither fallback sub-case ever calls).
- **PRE-unsupported unchanged**: same structural/no-diff proof — this path never reaches
  `production_generic_composer` either.

## Real-SFM qualification (only after offline qualification passes)

Same established qualification fixture used throughout this project. At minimum, compare pre-change
production vs. the candidate on:

- **Selected `shot3` Fox + Mia**: exact scope this whole design was proven against.
- **Exact final semantic hashes/state**: the same aggregate + per-field hash discipline
  `checkpoint_o2`'s own witnesses already use, for every capture (PRE, NATIVE_POST, COMPOSER_PRE,
  COMPOSER_POST, TERMINAL) — the candidate's own COMPOSER_PRE hash must match the pre-change baseline's
  own COMPOSER_PRE hash exactly, for both Fox and Mia.
- **Moved/already-correct counts where applicable**: composer's own `desired`/`moved`/`already_correct`
  counts (the same figures O2-R1 already measured: Fox desired 74/moved 72/already_correct 2; Mia desired
  69/moved 67/already_correct 2, warm run) must be identical between pre-change and candidate.
- **Authority lifecycle**: broker `READY`/canonical, zero outstanding leases, balanced provider
  opens/closes — unchanged from every earlier checkpoint's own established gate.
- **Native guards**: `NATIVE_GUARDS = PASS`, `NATIVE_REBUILD_RETURNED = PASS` — unchanged.
- **Isolation**: whole-session isolation evidence (untouched peers, no target-set drift) — unchanged.
- **Resource behavior**: production's own `CONTEXTUALIZER_RESOURCE_CHECKPOINT` evidence — should show no
  new regression; the candidate is expected to show a *smaller* discovery-stage time contribution, not a
  larger one.
- **Discovery call count**: must drop from 10 to 8 for this exact 2-target fixture (one eliminated call
  per target) — a directly observable, mechanical confirmation the change took effect as designed.
- **Command timing**: production command duration should decrease by roughly the theoretical saving
  (~0.35-0.38 s for this fixture), not by more (a larger-than-expected drop would itself be suspicious and
  warrant investigation before acceptance) and not by materially less (which would suggest the guard is
  falling back to fresh discovery more often than expected).

## Only after bounded equivalence passes

Broader-scope qualification (a larger shot selection, or eventually All Shots) is considered only after
this bounded Selected-Shots comparison passes cleanly — not prepared, scheduled, or assumed by this plan.

## What this plan does not do

Does not prepare or execute an implementation checkpoint. Does not run SFM. Does not modify production.
Proceeding past this plan requires separate explicit authorization of Candidate 1's own implementation.
