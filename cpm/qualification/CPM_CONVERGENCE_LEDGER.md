# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
**§22 item 8 — PREPARED, NOT RUN.** Exact candidate `bfba4d3a…` remains pending real-SFM
qualification. New item-8 observation tools qualified offline. Historical Sessions 1–4 unchanged.
K/L not started.

- Exact candidate: `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` (unchanged).
  **Not deployed**; no live item-8 phase (A–F) has been executed, no SFM process was started for
  item 8, no G2 was published, and the live Master, sidecars and installed deployment are untouched.
- Design (owner-approved): `cpm/qualification/ITEM8_POST_CLEANUP_REAL_SFM_QUALIFICATION_DESIGN.md`
  (`fe605188…`; workstation paths normalized to repository-relative, content unchanged).
- Preparation (`real_sfm_qualification/cpm_item8_post_cleanup/`): `ITEM8_RUNBOOK.md`;
  observation-only `CPM_Item8_Probe.py` `f503c0ab…`; `test_cpm_item8_probe.py` `859b75d1…`;
  `ITEM8_GENERATION_DRIVER.ps1` `3545ac72…` (frozen Session 2 §2.1 block verbatim + item-8
  deployment/evidence functions); `test_item8_generation_driver.py` `3f4aa26a…`;
  `ITEM8_FIXTURE_MANIFEST.json` `2b78f182…`; `item8_evidence_reader.py` `a3d3bd90…`; operator
  template; `ITEM8_EVIDENCE.md` (PREPARED, NOT RUN).
- **Offline preparation qualification:** probe test 2.7.5 **225/225** (real PySide/Qt 4.8 + model),
  3.10 **161/161** (model); driver test 3.10 + Windows PowerShell 5.1 **75/75** (sandbox: real
  G1 → exact G2 → exact G1 with the frozen tooling; both disposition paths).
- **Operator-preflight items (open):** **OWNER-1** — historical full CPM builds and package copies in
  the accepted Scripts inventory need an owner disposition before any attempt (the tooling supports
  acceptance as in Sessions 1–4); the two fixture session files; Mia document shot scope; Mia
  library; live inventory/installed app/authority (checked by `I8-Preflight`).
- Fixture identities recovered from Sessions 3–4; qualifying controls derived offline from the
  candidate's own scope over real G1: Body `Fat`, Expression `SmileClosed` (Mia).
- The Session 4 Fit release-path observation is carried forward unchanged (not repaired).
- Stale-scope UI presentation and `SidecarMissing` messaging remain undecided and out of scope.

Previous milestone: **§22 item 7 — COMPLETE: diagnostic/development logging reduction; offline
qualification PASS** (candidate `bfba4d3a…`; design and evidence
`ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_*.md`; manifest `cbb3010b…`; reporting constants removed,
superseding item 6's retention; Q1 parity oracle retained disabled). Its qualification is unchanged.

Previous milestone: **§22 item 6 — COMPLETE: historical authority cleanup; offline qualification
PASS** (candidate `1e866871…`; design and evidence `ITEM6_HISTORICAL_AUTHORITY_CLEANUP_*.md`;
manifest `a9264794…`). Its qualification is unchanged.

Previous milestone: Real-SFM Session 4 (forced rollback-verification qualification, handoff §22
blockers 4–5). **Status: COMPLETE — PASS.**
- S4A (Body Apply): PASS — CONTROL (authentic Abort, rollback verified), GATE (authentic verifier
  True, harness substitutes False → production recovery-unverified), ordinary Apply.
- S4F (Clothing Fit): PASS — CONTROL (`not-committed`), GATE (`abort-unverified`), ordinary Fit and
  Undo.

Evidence: `real_sfm_qualification/cpm_session4/SESSION4_EVIDENCE.md`, raw outputs in `raw/`.
Runbook: `SESSION4_RUNBOOK.md` at `b65c085`; harness `45c44f3d…`.

Sessions 1–4 remain complete (evidence for app `9a78fc96…`). R15 and R14 remain CLOSED.

## Current state
`master`. Before item 6 the product was unchanged since `00d0d83` (last commit touching `cpm/app`,
`cpm/baseline` or the adapter/projection). Items 6 and 7 changed only the mutable app
(`9a78fc96…` → `1e866871…` → `bfba4d3a…`); the launcher, baseline, adapter/projection, shared
package, Normalizer, Master and sidecars are unchanged.

**References for transfer:**
- Authoritative R15 design: `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md`, frozen from
  checkpoint `bd169401fba1c04bf24a148cd8e65748ae757912` (unchanged since `382c79b`). Its header
  status banner ("R15 remains OPEN…") predates R15 closure; this Ledger is authoritative for status.
- `cpm/qualification/R15_NAMESPACE_ISOLATION_PROPOSAL.md`: superseded, historical only.
- Convergence requirements and the §22 sequence:
  `docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md`.

The Session 4 campaign folders (`S4A`, `S4F`), the probe JSONL and the CPM log are copied,
redacted, into `real_sfm_qualification/cpm_session4/raw/`. The qualification-only rollback harness
was removed after each campaign; the Scripts deployment equals its pre-harness baseline exactly
(`cefc2b88…`), and no `ACTIVE_CAMPAIGN.txt` remains.

The live authority is exact production G1 after Session 4: Master `ac45e5c1…`, manifest
`d810d648…`, one sidecar `bcd97641…`.

**Deployed and verified** (runbook §0; re-verified against the workstation at the 2026-10-06
transfer checkpoint, including the shared package, whose qualification-only `projections.py` is
intentionally not deployed):
- launcher `996ca483…` as the Scripts-menu entry;
- private app `9a78fc96…` in `usermod/scripts/ChadChan3D_CPM/` (outside `scripts/sfm`, no
  `__init__.py`);
- probe v3 `ce4ace98…`.

Neither cleanup candidate (`1e866871…`, `bfba4d3a…`) is deployed; the deployed app remains the
pre-cleanup `9a78fc96…`. Any later deployment follows the R15 restart rule; item 8 deploys only
through `ITEM8_GENERATION_DRIVER.ps1` (`I8-Deploy`, SFM closed, verified backup, temporary sibling +
replacement) and applies the design's PASS / FAIL-INCONCLUSIVE policy through `I8-Disposition`.

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
| Session 2 S2-B_R2: G1→G2 during a Save prompt (2026-10-05) | **PASS** |
| Session 3 S3: queued Fit, G1→G2 between targets (2026-10-06) | **CORE PASS** |
| Session 3 S3_ADD: fresh Fit committing under G2 (2026-10-06) | **PASS** |
| Session 4 S4A: forced Body Apply rollback-verification control + gate (2026-10-06) | **PASS** |
| Session 4 S4F: forced Clothing Fit rollback-verification control + gate (2026-10-06) | **PASS** |

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
- **Session 2 S2-B_R2 (2026-10-05, pid 23944, broker `0x31141250`, window `0x30466580`):**
  - **Save opened under G1:** Save and its prompt opened at 18:36:40, under G1.
  - **Exact G2 while the prompt was open:** activated 18:40:42; no CPM activity until the prompt
    returned (`Q2_SAVE_POST_CONFIRM` 18:41:04).
  - **Stale Save refused:** the stale G1 Save authorization was refused with
    `generation-mismatch` (18:41:09); no `PROD_SAVE`, no durable phase, `durable_commit=None`;
    library inventories 1 = 2 = 3 byte-identical.
  - **Rebuild without replay:** one automatic rebuild to G2 after the refusal; the same window;
    no replay.
  - **Deliberate G2 Save:** passed, with the library diff exactly the three allowed entries.
  - **Idle authority and restoration:** P2–P4 leases and providers 0; exact G1 restoration.
  - **Aborted `S2B` attempt:** confirmed a normal G1 Save before any switch; the authority was
    untouched and the preset was removed. Its residual `character.json` metadata (`updated_at`,
    `last_validated_provider`) is never read for a decision and `semantic_overrides` is empty, so
    it cannot confound the tested boundary (adjudicated in `SESSION2_EVIDENCE.md`).
- **Session 3 S3 (2026-10-06, pid 26156, broker `0x314d92b0`, window `0x30ee7698`):**
  - **Target 1 under G1:** authorized and staged under G1, committed, released ok before target 2.
  - **G2 between targets:** the Fit was deferred at index 1 behind a modal; exact G2 was activated
    and proven live before resume.
  - **Refused, not mutated:** at resume, the target-2 stage proof was refused
    (`generation-mismatch`); no index-1 stage or commit; no continuation under G2.
  - **Truthful stop:** "Clothing Fit stopped" reported 1 committed target and Undo 1 time
    (`verified_changed=[assaultsuitbody1]`, target 2 unattempted). The target was committed with
    plan warnings, so it is accounted as partial rather than in `changed`.
  - **Undo, rebuild and idle state:** one Undo restored target 1 to pre-Fit (snapshot and visual).
    CPM rebuilt to G2 in the same window. P2–P4 were 0/0/0.
  - **Later G2 Fit:** authorized and staged under G2, then an expected structural skip
    (`loinclothbra_chadfix_071` has no compatible Body mappings). The G2 commit is carried by
    S3_ADD.
- **Session 3 S3_ADD (2026-10-06, pid 2324, broker `0x31419270`, window `0xb92d1c60`):** exact G2
  active before SFM started;
  `assaultsuitbody1` authorized, staged, committed and verified under G2 (`committed-verified`,
  26 mappings, 7 warnings), released ok; result PASS `partial_changed=1 failed=0 unattempted=0`;
  P2–P4 0/0/0; one Undo; exact G1 restoration.
- **Session 4 S4A (2026-10-06, pid 2540, broker `0x30fab290`, window `0x309ae698`):**
  - both injected `BodyTest` Applies authorized under G1, writes inside the open Undo
    (`changed_sides=1`, real precommit predicate True);
  - CONTROL: `PROD_APPLY_ABORT_VERIFY restored=True`, "Can't apply preset";
  - GATE: real verifier True, harness substituted False → `restored=False`,
    `ProdRecoveryUnverifiedError`, "Recovery could not be verified";
  - no `native-commit` or committed outcome; Undo state and `mia1` values equal ARM; 0 adapter
    calls during rollback verification; P2–P5 0/0/0; ordinary `BodyTest` Apply committed.
- **Session 4 S4F (2026-10-06, pid 17544, broker `0x311d72b0`, window `0x30bea698`):**
  - both injected Fits authorized under G1, stage `index=0 gfit=ac45e5c1… literals=34`, writes
    inside the open Undo (`changed_sides=3`, real predicate True);
  - CONTROL: `PROD_CLOTHING_FIT_ABORT_VERIFY … restored=True`, `not-committed`, "Nothing changed";
  - GATE: real verifier True, substituted False → `restored=False`, `abort-unverified`, dialog
    `recovery_unverified=[assaultsuitbody1] unattempted=[loinclothbra_chadfix_071] undo_count=0`;
  - stage lease outstanding (1) during rollback verification, 0 adapter calls, exactly one
    successful `release()`; target 2 never staged; nothing committed; P2–P6 0/0/0;
  - ordinary Fit committed-verified and released ok; one Undo restored it visually.
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
    For Apply this is "Preset could not be applied safely…"; for Save it is "Can't save preset —
    Preset could not be saved. Nothing was saved."
  - The stale-scope reason is logged only, and CPM then rebuilds automatically.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  (K/L).
- **Remaining pre-K qualification:**
  - Session 2: **COMPLETE — PASS** (S2-A_R2 and S2-B_R2).
  - Session 3: **COMPLETE — PASS** (S3 CORE PASS and S3_ADD).
  - the forced Apply and forced Fit rollback-verification failure gates: **Session 4 COMPLETE —
    PASS** (S4A, S4F);
  - §22 item 6 (historical authority cleanup): **COMPLETE — offline qualification PASS**
    (candidate `1e866871…`; not real-SFM qualified);
  - §22 item 7 (diagnostic/development logging reduction): **COMPLETE — offline qualification
    PASS** (candidate `bfba4d3a…`; not real-SFM qualified);
  - §22 item 8 (focused post-cleanup regression, including post-cleanup real-SFM qualification):
    **PREPARED, NOT RUN** (owner decision OWNER-1 and operator preflight open).

  **K, L:** not started.
- **Session 4 notes (not failures; carried to cleanup/K; unchanged by item 7):**
  - Fit's exception path releases the stage with a bare `release()` (no
    `PROD_CPM_FIT_STAGE_RELEASED` line; result discarded); a raising success-path release could in
    theory be followed by a second `release()`. Live S4F shows exactly one successful release per
    injected stage.
  - The Body bone-scale branch of rollback verification is covered offline only (`BodyTest` changes
    no bone scales); Expression Apply shares `prod_apply` and is covered offline.
- R3, R6, R9, R13, R14, R15: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS (C10 also real-SFM);
  R15 suite PASS.

## Next
After designer/owner review of this checkpoint and the OWNER-1 disposition: execute item 8 exactly
per `real_sfm_qualification/cpm_item8_post_cleanup/ITEM8_RUNBOOK.md` (one fresh SFM process, Phases
A–F), only under an explicit execution authorization; then adjudicate and apply the deployment
policy. K and L follow only after item-8 adjudication; neither has begun.

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
