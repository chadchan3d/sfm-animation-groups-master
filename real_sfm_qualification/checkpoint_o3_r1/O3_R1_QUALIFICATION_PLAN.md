# O3-R1 — Corrected Future Qualification Plan

**Status: PLAN ONLY. NOT EXECUTED.** This supersedes `checkpoint_o3/O3_FUTURE_QUALIFICATION_PLAN.md`
(which qualified O3's own, now-superseded, Option B design). This plan applies *if and only if* Option C
(`O3_R1_CORRECTED_SUBSTITUTION_DESIGN.md`) is separately authorized for implementation, and only after
the materiality question in `O3_R1_MATERIALITY_REEVALUATION.md` is resolved favorably. No implementation
checkpoint is prepared or executed here. No production, integration, or lifecycle code has been modified.

## Offline qualification

- **Same-target rig replacement**: construct a fixture where the candidate rig identified at outer
  NATIVE_POST time is deliberately made stale (e.g. simulate a different native object now occupying the
  same handle value) before the fresh re-validation sequence runs; assert the fresh
  `HasAnimationSet`-style re-check either confirms genuine continuity or the design falls back correctly
  — never silently trusts a replaced incarnation.
- **Registry replacement/rebinding**: construct a fixture where `arr(rig, "animSetList")` would now
  resolve to a *different* registry than at NATIVE_POST time; assert the freshly re-executed registry
  resolution reflects the CURRENT registry, not a stale one — since Option C never trusts a carried-forward
  registry value at all, this should be true by construction, but must be asserted, not assumed.
- **Ownership change**: construct a fixture where `owned_handles` would differ between the two discovery
  points; assert the freshly re-executed ownership intersection reflects the CURRENT state.
- **Root replacement**: construct a fixture where `aset.GetRootControlGroup()` would now return a
  different root; assert the capture step (unchanged, already fresh) reflects it — this is unaffected by
  the discovery-reuse change, but must be confirmed as unaffected, not assumed.
- **`hiddenGroups` change**: construct a fixture where the registry's own `hiddenGroups` list would now
  differ; assert the freshly re-executed read reflects the CURRENT value.
- **Unreadable registry/array reads**: construct a fixture where `arr(registry, "elementList")` (or the
  other array reads) would raise `ProbeError` if freshly attempted; assert the candidate design surfaces
  this exception, at the same point in the sequence, as today's fully-fresh code does — this is the
  direct test of `O3_R1_PREWRITE_FAILURE_CONTRACT.md`'s Category 2 preservation requirement.
- **Handle-read exceptions**: same technique for `handle()` calls on the rig/registry/controls.
- **Guard/revalidation exceptions**: assert that any exception raised during the fresh re-validation
  sequence propagates with the same timing (before composer writes) and the same effective behavior
  (target-level failure, not a silent skip) as today's fully-fresh `discover_rig_context()` call would.
- **Correct pre-write rejection timing**: an explicit ordering assertion — every fresh re-validation step
  must complete (successfully or by raising) strictly before the first composer-write call site (line
  7205 onward) executes. This is the single most important offline assertion this plan requires, directly
  answering Astra's objection #4.
- **Native-only/fallback path unchanged**: structural/no-diff proof that neither fallback sub-case's own
  code path is touched — Option C lives entirely inside `production_generic_composer`, which neither
  fallback sub-case ever calls, unchanged from O3's own equivalent claim.
- **No live DME retention beyond authorized scope**: confirm the candidate rig reference used for
  re-validation is never retained beyond the single re-validation-plus-capture sequence within one
  target's own transaction — never stored on `self`, never carried across the Qt-deferred inter-target
  boundary.

## Future bounded real-SFM qualification

Same established fixture (`shot3`, Fox + Mia, Selected Shots), same discipline as every earlier
checkpoint's own real-SFM comparison, but corrected to address Astra's evidence concerns:

- **Baseline vs. candidate**: pre-change production vs. the Option-C candidate, same continuous SFM
  process where feasible, matching this whole project's established bounded-comparison pattern.
- **Fresh + already-normalized**: both states, matching O2-R1's own two-command design.
- **Exact semantic parity**: aggregate + per-field hashes for every capture (PRE, NATIVE_POST,
  COMPOSER_PRE, COMPOSER_POST, TERMINAL) — candidate's own COMPOSER_PRE output must match the baseline's
  exactly, for both targets, both states.
- **Separate identity evidence rather than stripped semantic hashes alone**: per Astra's own concern that
  O2's hash-equality proof showed *retained semantic equality at two observation points*, not *identity
  continuity* — this round's own real-SFM comparison must additionally capture and compare `rig_handle`/
  `registry_handle`/`rig_name` (and ideally a raw identity marker beyond the handle value, if one can be
  obtained without new invasive instrumentation) at both the baseline's fresh-discovery point and the
  candidate's re-validated point, not rely on the final snapshot's own hash equality as sufficient proof
  that the *same* rig was involved throughout.
- **Discovery/traversal counts**: must show the expected reduction (discovery call count same as O2-R1's
  own 10, since Option C does not eliminate the *call*, only its internal cost — a new, separate counter
  for "full `reachable(scene)` traversals performed" should show the reduction instead, dropping from 5
  to 4 per target on the composer-entry path).
- **Native guards**: unchanged, must remain PASS.
- **Isolation**: unchanged, must remain clean.
- **Authority lifecycle**: unchanged, must remain clean.
- **Resource behavior**: no regression expected; should show a reduced discovery-stage time contribution.
- **Measured net runtime benefit**: the actual, observed timing delta between baseline and candidate for
  this fixture — replacing `O3_THEORETICAL_SAVINGS.md`'s own gross-ceiling estimate with a real,
  measured net figure, resolving the open question in `O3_R1_MATERIALITY_REEVALUATION.md`.

## What this plan does not do

Does not prepare or execute an implementation checkpoint. Does not run SFM. Does not modify production.
Requires, before any of the above executes: (1) separate explicit authorization of Option C's own
implementation, and (2) the materiality question resolved (via the offline-measurable split identified in
`O3_R1_MATERIALITY_REEVALUATION.md`, or via this plan's own real-SFM measured-net-benefit step, whichever
comes first) to confirm the net saving remains worth the added complexity.
