# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
Real-SFM Session 2 (controlled G1→G2; runbook
`real_sfm_qualification/cpm_session2/SESSION2_RUNBOOK.md` at `3b22b8b`).

**Status: S2-A_R2 (open-window generation replacement) PASS. S2-B (generation change during a Save
prompt) is the next authorized bounded step and has not been run.**

R15 CLOSED — PASS. Session 1 remains complete. R14 remains CLOSED.

## Current state
`master` at the S2-A_R2 adjudication commit (Ledger only). The product is unchanged since
`00d0d83`.

Session 2 campaign evidence is held outside the repository at
`%PUBLIC%\Documents\CPM_Session2\` (`S2A` invalid attempt; `S2A_R2`). It is copied in, redacted,
at Session 2 closeout (`SESSION2_EVIDENCE.md`).

The live authority is exact production G1 after S2-A_R2: Master `ac45e5c1…`, manifest
`d810d648…`, one sidecar `bcd97641…`.

**Deployed and verified** (runbook §0):
- launcher `996ca483…` as the Scripts-menu entry;
- private app `9a78fc96…` in `usermod/scripts/ChadChan3D_CPM/` (outside `scripts/sfm`, no
  `__init__.py`);
- probe v3 `ce4ace98…`.

The step-9 G18AN menu copy has been removed. The pre-R15 app `664a660c…` and probe v2 are archived
outside `usermod/scripts`.

Unchanged (byte-pinned by the R15 suite):
- the baseline `3326024d…`;
- the Normalizer `1f4ec5a2…`;
- the adapter `e96e21b5…` and projection `9b077a1b…`;
- the shared package;
- the Master `ac45e5c1…`;
- R14 private ctypes.

## Verified (real SFM)
Evidence:
- `SESSION1_RUN1_RECONCILIATION.md` (2026-09-28);
- `SESSION1_COMPLETION_EVIDENCE.md` (2026-09-29);
- `R15_SESSION1_ADDENDUM_EVIDENCE.md` (2026-09-30; raw outputs in `cpm_session1/r15_addendum/`).

| Session 1 item | Status |
|---|---|
| Normal CPM operation | PASS |
| Native Apply + Undo (incl. no-op) | PASS |
| Body Save / Update | PASS |
| Expression Save / Update / Apply | PASS |
| Review / Reclassify (Ayane, genuine miss; durable edit and rebuilt classification reported) | PASS |
| Ordinary Clothing Fit + Undo | PASS |
| C10 same-process broker | PASS |
| Simultaneous Normalizer coexistence | PASS, with no CPM scope selected (Session 1) **and with an active CPM scope (R15 addendum)** |
| Resource / latency | PASS (complete) |
| R14 ctypes isolation | CLOSED |
| R15 namespace isolation (Session 1 addendum, P1–P15) | **CLOSED — PASS** |
| Session 2 S2-A_R2: open-window G1→G2 replacement (2026-10-05) | **PASS** |

- **Clothing Fit detail:**
  - `Gfit` was authorized.
  - The stage requested 34 literals, more than the 26 source literals, so target-only vocabulary
    was included.
  - The planner produced 26 valid mappings (7 unmatched-target warnings).
  - The stage committed and verified, and its lease was released.
  - Undo visually restored the target.
- **R14:** CPM's resource snapshot ran first, then the Normalizer logged `mem_ok=True` at 13/13
  checkpoints (the first run logged `False` at 15/15).
- **R15 addendum (2026-09-30):**
  - **Design:** one thin menu launcher → one stable private `chadchan3d_cpm_app` module per SFM
    process → explicit compatible-window reuse (`R15_IMPLEMENTATION_BLUEPRINT.md`).
  - **Offline:** R15 suite 345/345 (2.7.5: real PySide/Qt 4.8 plus a model), 188/188 (3.10); all
    regressions PASS.
  - **Isolation:** `__main__` held no CPM names; private function globals.
  - **Stable identity:** one stable module, run ID and class across:
    - the reused second click (no authority acquired);
    - three close/reopen cycles (✕, Escape, Escape; one close request and one finalization each);
    - the notice step.
  - **Normalizer:** Rebuild Selected Shots on `shot3` with CPM's Mia scope active → PASS,
    `mem_ok=True` 15/15; 0 cross-log lines either way.
  - **Continuation:** without reselection, Apply ×2 committed and disposable Save PASS; no stale
    refusal and no scope rebuild.
  - **Notice and legacy slot:**
    - one reusable non-modal notice;
    - frozen G18AN in the slot was refused and preserved, then isolated CPM opened.
  - **Authority and resources:**
    - idle leases/providers 0;
    - across the cycles: private commit −0.5 MB, handles −10, GDI 0, USER −1 (no accumulation).
  - **Recorded deviations (benign):** the baseline ran before P3; one extra observational probe
    before P15; the console transcript was not retained.
  - **Observation:** one no-op Apply began about 0.2 s before the Normalizer's final report write.
    The PASS rests on later actions; alternation stays with K.
  - **Three findings, all resolved by R15, kept distinct:**
    1. the shared Scripts-menu namespace defect;
    2. the repeated-click re-initialization defect;
    3. the pre-existing Escape/reject teardown defect (discovered during R15).
- **Session 2 S2-A_R2 (2026-10-05, pid 25844, broker `0x32def250`, window `0x3210f580`):**
  - **Generation switch:** G1 `ac45e5c1…` → exact G2 `54413b6c…`, using the frozen Checkpoint I
    functions (complete write-once record set).
  - **No-interaction window held:** no CPM activity between G2 activation (17:55:09) and the
    stale Apply (17:56:10).
  - **A8 stale Apply refused before mutation:** `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED …
    reason=u'generation-mismatch'`; no Undo, mutation, native-commit or Apply outcome;
    `native_commit=None`.
  - **Rebuild only after the refusal:** `…REBUILD_SCHEDULED` at 17:57:17, after the dialog was
    dismissed; one automatic Select Model to G2 `54413b6c…`; the same window; no replay.
  - **A10 deliberate Apply:** authorized under G2 and committed (`BodyTest`, `changed_sides=1`).
  - **Idle authority:** P2–P5 leases 0, providers 0, one window / one watcher.
  - **Restoration:** exact G1 (`exact_match: true` in both the finalization record and the
    independent comparison).
  - **First S2-A attempt (folder `S2A`, 2026-10-01):** procedurally invalid (runbook design
    error). Selecting a preset after G2 activation re-evaluated readiness and rebuilt the scope
    under G2 before Apply. That path behaved correctly but does not qualify the stale-action
    boundary. The folder is preserved; its restoration was exact.
  - **Observation:** the refusal dialog shows the guard's generic copy ("Preset could not be
    applied safely. This preset was not applied."), not the stale-scope message, which is logged
    only. See the stale-scope UI presentation item.
- **Measurements (Session 1):**
  - process working set +36 MB across the session;
  - CPM scope 107–166 KB;
  - broker retained 666–888 KB;
  - authorization about 0.02 s; warm stage about 0.02 s; one Fit target 0.146 s; scope build
    1.2–1.5 s.

## Unresolved
- **K/L residuals from R15 (not in R15 scope, unchanged):**
  - Normalizer namespace isolation (the Normalizer still runs in the shared `__main__`);
  - the shared window slot, log name and identity strings that old CPM builds also claim.
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
  - Real SFM shows that a stale-generation refusal is presented through the guard's generic copy.
    For Apply this is "Preset could not be applied safely…"; for Save it would be "Can't save
    preset — Nothing was saved."
  - The stale-scope reason is logged only, and CPM then rebuilds automatically.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  (K/L).
- **Remaining pre-K qualification:**
  - Session 2:
    - S2-A_R2 (G1→G2 with CPM open): **PASS**.
    - **S2-B (G1→G2 during a Save prompt): next, not run.** Precondition: the frozen runbook's
      B6 visible expectation ("a warning says the semantic scope is stale") is inaccurate; the
      dialog will be the generic "Can't save preset" copy. Correct that wording in the runbook,
      with approval, before S2-B so the operator is not sent to STOP.
  - Session 3: queued Fit target-1 G1 → target-2 G2, and target 1's Undo after it;
  - the forced Apply and forced Fit rollback-verification failure gates;
  - then cleanup of historical authority and diagnostics, plus a focused regression.

  **K, L:** not started.
- R3, R6, R9, R13, R14, R15: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS (C10 also real-SFM);
  R15 suite PASS.

## Next
S2-B is the next authorized bounded qualification step.
1. Approve the one-step correction of the runbook's B6 visible-dialog expectation (the generic
   "Can't save preset" copy).
2. Then run S2-B per the runbook (`$EB`, a fresh write-once path), restore exact G1, and
   adjudicate.

Session 3 is not started.

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
