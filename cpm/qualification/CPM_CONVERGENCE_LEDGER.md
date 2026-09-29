# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
R15 investigation and fix proposal (no implementation). **Status: proposal complete
(`cpm/qualification/R15_NAMESPACE_ISOLATION_PROPOSAL.md`); awaiting owner approval to
implement.** Session 1 remains COMPLETE — PASS; R14 CLOSED.

## Current state
`master` at the R15 proposal commit, on top of `be5122e`. It adds only the proposal document and
this Ledger. No product code changed; the product is still at `2b8222a` (app `664a660c…`,
deployed).

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
- **R15: investigated; fix proposed; AWAITING OWNER APPROVAL.**
  - **Mechanism:** SFM's native `ScriptController` (`ifm.dll`: `PyRun_FileExFlags`, `__main__`)
    runs every Scripts-menu script in one shared process-lifetime `__main__` dict. This is backed
    by binary strings and the observed `OUTPUT_PATH` rebinding; the probe confirms it directly in
    the addendum.
  - **CPM vs Normalizer:** 18 shared names. 11 are identical modules and 2 are Py3-only fallbacks;
    `OUTPUT_PATH` is shared mutable configuration; `arr`, `handle`, `name` and `typ` differ.
  - **Larger surface:** old CPM builds share 470–600 names with the converged app, so running one
    could route the converged window back to the historical provider.
  - **Proposed fix:** a CPM-only private-namespace launcher that runs the implementation in a
    fresh private module each invocation, plus a one-line direct-execution guard in the app. The
    Normalizer, package and baseline are untouched.
  - **Required afterwards:** the offline R15 suite plus a real-SFM Session 1 addendum:
    active-scope simultaneous coexistence, no cross-script logging, `mem_ok=True`, the same
    broker, 0 leases/providers, CPM usable.
  - **Session 2 is gated on it.**
  - **Residuals for K/L:** Normalizer namespace isolation; the shared window slot and identity
    strings.
- **Preserved nuance:** Session 1's simultaneous-coexistence PASS ran with no CPM scope selected.
  Active-scope coexistence is still unproven and is covered by the R15 addendum.
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
Owner: approve or amend the R15 proposal. On approval: implement (launcher + guard), run offline
qualification, deploy, then the real-SFM Session 1 addendum. Session 2 is not started or prepared.

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
