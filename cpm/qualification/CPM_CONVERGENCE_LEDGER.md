# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
R15 documentation synchronization (docs only). **Status: complete.** R15 design is FROZEN on
the stable private module: `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` is the single
authoritative design. The fresh-module-per-click proposal
(`R15_NAMESPACE_ISOLATION_PROPOSAL.md`) is SUPERSEDED (historical only). R15 remains OPEN.
Session 1 historical PASS intact; R14 CLOSED.

## Current state
`master` at the Blueprint §14 starting-point correction, on top of the approved R15
documentation-synchronization commit `5d94dbf` (itself on `bd16940`). The synchronization adds the
Blueprint and updates the superseded proposal (notice only), this Ledger and the handoff
(status + §16 entrypoint/deployment amendment). No product or test code changed; the product is
still at `2b8222a` (app `664a660c…`, deployed).

Also unchanged: the baseline (`3326024d…`), the shared package, the adapter/projection, the
Normalizer and the Master.

## Verified (real SFM)
Evidence: `SESSION1_RUN1_RECONCILIATION.md` (2026-09-28) and `SESSION1_COMPLETION_EVIDENCE.md`
(2026-09-29).

| Session 1 item | Status |
|---|---|
| Normal CPM operation | PASS |
| Native Apply + Undo (incl. no-op) | PASS |
| Body Save / Update | PASS |
| Expression Save / Update / Apply | PASS |
| Review / Reclassify (Ayane, genuine miss; durable edit and rebuilt classification reported) | PASS |
| Ordinary Clothing Fit + Undo | PASS |
| C10 same-process broker | PASS |
| Simultaneous Normalizer coexistence | PASS, as run (CPM window open; no scope selected when the Normalizer ran) |
| Resource / latency | PASS (complete) |
| R14 ctypes isolation | CLOSED |

- **Clothing Fit detail:**
  - `Gfit` was authorized.
  - The stage requested 34 literals, more than the 26 source literals, so target-only vocabulary
    was included.
  - The planner produced 26 valid mappings (7 unmatched-target warnings).
  - The stage committed and verified, and its lease was released.
  - Undo visually restored the target.
- **R14:** CPM's resource snapshot ran first, then the Normalizer logged `mem_ok=True` at 13/13
  checkpoints (the first run logged `False` at 15/15).
- **Measurements:**
  - process working set +36 MB across the session;
  - CPM scope 107–166 KB;
  - broker retained 666–888 KB;
  - authorization about 0.02 s; warm stage about 0.02 s; one Fit target 0.146 s; scope build
    1.2–1.5 s.

## Unresolved
- **R15: OPEN — design FROZEN, not implemented.** Pending: implementation, offline
  qualification (Python 2.7.5 + 3.10, Blueprint §11) and the real-SFM Session 1 addendum (§12).
  - **Frozen design:** one thin SFM menu launcher → one stable private CPM application module
    (`chadchan3d_cpm_app`) per SFM process → explicit compatible-window reuse. ABSENT → LOADING →
    READY (permanent); exact-byte compile; no reload (a changed build requires restart);
    allow-guard at the top of the app; bottom `StartProdTool()` removed. Private implementation
    deployed outside the `scripts/sfm` tree. Fresh module per click is superseded.
  - **Clarifications:** (A) the no-`sys.path` rule covers the new launcher/loader only; the
    existing adapter/bootstrap MAINMENU insertion is unchanged and not authorized for change.
    (B) the addendum records settled working set/private commit and handle/GDI/User counts at
    initial open, the second click, each of three close/reopen cycles and the final state, to
    detect accumulation (no MB threshold).
  - **Session 2 is gated on it.** Residuals for K/L: Normalizer namespace isolation; the shared
    window slot and identity strings.
- **Three separate findings (preserved distinct):**
  1. **R15 shared-namespace defect:** SFM's native `ScriptController` runs every Scripts-menu
     script in one shared `__main__` dict; long-lived CPM global resolution is corrupted (observed
     `OUTPUT_PATH` rebinding; 18 CPM/Normalizer shared names, dangerous: `OUTPUT_PATH`, `arr`,
     `handle`, `name`, `typ`; old CPM builds share 470–600 names).
  2. **Repeated-click initialization defect:** inferred reset/logging behavior of the old
     re-execute-per-click model (`OUTPUT_PATH`, provider counters, `PROD_RUN_ID`).
  3. **Pre-existing Escape/reject teardown defect,** discovered during R15; not the cause of
     namespace corruption. Repair frozen in Blueprint §8.
- **Preserved nuance:** Session 1's simultaneous-coexistence PASS ran with no CPM scope selected.
  Active-scope coexistence is still pending the R15 addendum.
- **Deferred UI findings (product/UI work; none are Session 1 blockers):**
  1. **Legacy preset.** Apply of an old `body.scale.head` preset is refused. Future message: "This
     preset uses an outdated scale format. Delete this preset and save a new Body preset." This
     is a legacy edge case only; generic bone-scale persistence works.
  2. **Update Preset confirmation.** Use "The preset's current values will be overwritten." and
     remove the question-mark icon.
  3. **Window.** Widen the CPM window, and keep all tabs visible without horizontal tab scrolling.
  4. **Buttons.** Clearer active/disabled contrast:
     - primary accent for Apply Preset;
     - restrained gold for Favorite;
     - restrained red for Delete.
  5. **Review.** Try a 2×2 Review action-button grid.
  6. **Reclassify wording.**
     - Rename the button to "Clear Classification".
     - Status: "Classified as Body. Click Clear Classification, then choose a new classification
       under Needs review."
     - Keep the clear → rebuild → reclassify behavior unchanged.
- **Stale-scope UI presentation** and **`SidecarMissing` messaging:** undecided.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  (K/L).
- **Remaining pre-K qualification:**
  - Session 2: G1→G2 with CPM open, and during a Save/Update prompt;
  - Session 3: queued Fit target-1 G1 → target-2 G2, and target 1's Undo after it;
  - the forced Apply and forced Fit rollback-verification failure gates;
  - then cleanup of historical authority and diagnostics, plus a focused regression.

  **K, L:** not started.
- R3, R6, R9, R13, R14: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS (C10 also real-SFM).

## Next
Implement the authoritative R15 Blueprint from starting point
`5d94dbfd41c9187170ee8a926d59f21317c1e19c` (Blueprint §14; allowlisted files only), run the
offline gates, report before deployment, then the real-SFM Session 1 addendum.
Session 2 is NOT STARTED and not prepared.

## Checkpoints
Update this Ledger and output its complete, concise contents when:
- The milestone is complete and checked.
- Progress is blocked or requires an owner decision.
- A Blueprint conflict, scope expansion, or unmet prerequisite is found.
- Work is being paused or transferred.

State why the checkpoint occurred. Stop at milestone completion.
For blockers or conflicts, pause affected work until resolved.
The owner relays the updated Ledger to the designer, or the designer
retrieves that same version from the shared repository.

## Maintenance
Replace stale entries; keep checkpoint content about one screen.
Preserve unresolved issues. Label uncertainty and untested claims.
Keep history in Git or an archive. Routine edits do not require a
full Ledger report.
