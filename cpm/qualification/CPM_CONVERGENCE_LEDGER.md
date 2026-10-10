# Ledger

## Coder gate
Before editing, compare the assignment with the Blueprint and this Ledger.
Verify the current code state and relevant claims.
If the assignment assumes unfinished work is complete, contradicts the
Blueprint, or expands scope, report the conflict before dependent edits.
Otherwise proceed with the assigned milestone.

## Current milestone
**K — Integrated CPM/Normalizer product workflow qualification: K PREPARED, NOT RUN (2026-10-09).**
- **Design approved:** `cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md`,
  with D1 = A, D2 = B, D3 = B and D4 = YES:
  - no new authority-unavailable mechanism; the shared G1→G2 stale-generation recovery only;
  - **K PASS = K1 + K2 only**; K3 / All Shots is optional post-K stress work;
  - divergent shots: selection first, playhead second, confirm both.
- **K-0 tooling** in `real_sfm_qualification/cpm_k_integrated/`:
  - probe `96d873b7…` (item-8 probe + declared deltas);
  - driver `270555e9…` (frozen Session 2 block + K functions; never writes the CPM app);
  - manifest `0c390b8d…`, reader `4fb42a3c…`, operator template.
- **Offline qualification:** `test_cpm_k_tooling.py` **2.7.5 156/156** (real Qt + model) and **3.10
  187/187**, including the driver sandbox G1 → exact G2 → exact G1.
- **K1 authorized (K2 is not).**
  - **K1A1 — INCONCLUSIVE:** a qualification-tooling false STOP before either product consumer
    executed; not a CPM or Normalizer failure. The baseline probe in a fresh fixture-loaded process
    showed 528 MB free VAS, which tripped the K rule "free VAS < 600 MB". Item 8 D's Normalizer had
    begun with 421 MB free and finished `mem_ok=True`.
  - **K1A1 closeout:** SFM closed with Don't Save; exact G1 untouched; probe removed; expected
    inventory restored; app and fixture unchanged; sealed (local evidence). It is not reused.
- **K-0 amendment:**
  - the VAS STOP is removed and free VAS (probe, Normalizer samples) is recorded as telemetry only;
  - the Normalizer's own `mem_ok=False` is the primary memory/VAS STOP, and the private-bytes
    safeguards are retained;
  - a regression check was added;
  - reader `e137536d…`, manifest `7bf1683a…`, driver `8b302a96…` (manifest pin only); probe
    unchanged;
  - tests: **2.7.5 160/160**, **3.10 191/191**.
  - Design §5.4 and §16.
- **Next:** K1A2, a new fresh attempt under the unchanged K1 runbook. K2 is NOT STARTED.

**Pre-K CPM UI polish pass — LIVE VERIFIED / PASS (2026-10-09).** The final build
**`4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7`** is installed and is **the
exact CPM candidate eligible to enter K**.
- **U3** verified it live as a Help wording delta from U2: owner review of the Getting started Help
  ("good looks"), plus a log showing the exact build loaded, Help opened and the close finalized,
  with no authorizations, mutations or refusals.
- It supersedes `7e4686d7…` (U2 LIVE VERIFIED / PASS) only in those two Help paragraphs. The offline
  UI test passes 100/100 and 65/65, and all existing suites PASS.
- Record: `PRE_K_UI_POLISH_PASS.md` §H; outputs in `pre_k_ui_polish_outputs_r3/`.
- **K: NOT STARTED** (needs separate authorization; must begin in a fresh SFM process). L: not
  started.
- Superseded candidates are retained with their records: `7e4686d7…` (U2 PASS) and `5c6e2789…`
  (U1 SUPERSEDED / NO QUALIFICATION VERDICT).
- Item 8 qualified `bfba4d3a…` functionally. That evidence is unchanged, and the UI pass is
  byte-bounded against it.

The pass makes eight presentation changes:
1. the owner-supplied woman icon, embedded at 64×64;
2. **Character Model:** and "Choose a character model" (Refresh Model List unchanged);
3. Help opens with **Getting started**: the character and the playhead workflow;
4. semantic buttons: blue Apply/Fit, gold Favorite, red Delete. In the refinement these are
   **neutral fills with restrained role-colored borders**, and every role uses the neutral disabled
   state;
5. window 580×800, minimum 540×650 (the four tabs fit);
6. Update confirmation copy, with no question icon;
7. Review buttons in a 2×2 grid;
8. **Clear Classification** wording.

No scope, authority, lifecycle, preset, Fit, generation or Normalizer behavior changed.

Offline results for `7e4686d7…`:
- all existing convergence/R14/R15 suites PASS under 2.7.5 (real Qt) and 3.10;
- `test_cpm_app_ui_polish_pass.py` passes **99/99** (2.7.5) and **64/64** (3.10), including byte
  reconstruction from `bfba4d3a…` and real-Qt pixel checks of fills, borders and disabled states.

(First candidate `5c6e2789…`: 96/96 and 61/61.)

The exact-build historical tests (item 6, item 7 reconstruction, item-8 probe/driver) refuse the new
bytes by design and were not edited. Record: `cpm/qualification/PRE_K_UI_POLISH_PASS.md`; outputs
in `pre_k_ui_polish_outputs_r2/` (first candidate: `pre_k_ui_polish_outputs/`).

**Live checks:**
- **U1** (`5c6e2789…`): SUPERSEDED / NO QUALIFICATION VERDICT.
- **U2** (`7e4686d7…`): **PASS**, on the owner's hands-on review ("Looks good") plus the log. The log
  shows the exact build loaded, the window shown, Help opened, and the close finalized, with no
  authorizations, mutations or refusals. Its only messages were the unchanged "No current shot." and
  "Choose a model first." guards.
- **U3** (`4e35f292…`): **PASS** as a Help wording delta from U2. The owner reviewed the Getting
  started Help; the log shows the exact build loaded, Help opened and the close finalized. Its only
  message was the expected "No current shot." at launch.

No model was selected in U2. Enabled border colors, the Update confirmation and Review rest on the
offline real-Qt checks and on U1 hands-on use. Each deployment was verified with SFM closed: Scripts
difference = the app line only; authority exact G1. Details: `PRE_K_UI_POLISH_PASS.md` §0.3.

Previous milestone: **§22 item 8 — COMPLETE / PASS** (qualifies `bfba4d3a…` only; unchanged). Exact candidate
`bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` was qualified in one fresh
real-SFM Python 2.7.5 process. The campaign covered:
- focused post-cleanup operation;
- persistence and native Undo;
- ordinary Fit;
- generation refusal and rebuild;
- canonical idle ownership;
- Normalizer coexistence;
- close/reopen behavior.

Historical forced-rollback and queued-Fit evidence is retained with its existing qualifications.
Exact G1 was restored. The temporary item-8 probe, campaign pointer and other qualification-only
deployment were removed. **The exact qualified candidate remains installed.** No new convergence
blocker was found. **CPM is eligible to enter K; K and L have not started. K, if later authorized,
must begin in a fresh SFM process.** This checkpoint does not decide L's final installation layout.
(Superseded for K entry by the pre-K UI pass: the build eligible to enter K is now the live-verified
`4e35f292…`.)

- **Attempt `I8A1` (2026-10-08, from `d4ad3cf`):**
  - one SFM process, PID 36912;
  - module `0x30b6b490`, class `0x307ed158`, run `20261008-135639-pid36912`;
  - broker `0x310a7810`;
  - windows `0xce494350` → `0x310bea30` → `0x30b87418`;
  - fixture `testscripts.dmx` (`197e6011…`): Krystal on `shot10`, Mia on `shot3`; not saved.
- **Phases A–F PASS.** Mechanical adjudication 34/34, from 30 probe records, the CPM-log excerpt,
  the Normalizer log, and the generation and library records.
  - **A — load and reuse:** `bfba4d3a…` loaded through the private loader; the second click gave
    `PROD_R15_WINDOW_REUSED` with no acquisition.
  - **B — Fit:** authorized on G1; 34 literals; committed-verified with 26 mappings and 7 warnings;
    one release `ok=True`; `changed=1 partial_changed=1 failed=0 unattempted=0`. Only the target
    changed, and Undo restored exactly.
  - **C — persistence and Undo:** Mia scope 46/58/4. Body Save/Update/Apply and Expression
    Save/Apply all equal their readbacks; each Undo restored exactly; library changes stayed within
    the footprint.
  - **D — Normalizer:** Selected `shot3` PASS/PASS, `mem_ok` True 15 / False 0. One broker served
    both projections. Apply and Save continued without reselection, refusal or rebuild.
  - **E — generation transition:** a Save opened under G1 and G2 was activated at 19:46:45 with the
    prompt open. The Save was refused with `generation-mismatch`: no `PROD_SAVE`,
    `durable_commit=None`, libraries E1 = E2 = E3. Only then did one rebuild to healthy G2 happen.
    A deliberate G2 Save was authorized on G2.
  - **F — close/reopen and exit:** Escape and ✕ closes finalized; the reopen kept the same
    module/run under the G2 scope. Idle 0/0/0 at every checkpoint (broker totals: opens/closes
    7/7, views 5).
- **Resources:** private bytes 3,067.8 → 3,103.3 MB (about +35 MB over about 6.5 hours, including
  about 9 MB for the Normalizer). The two closed states after the reopen were equal, with handles,
  GDI and USER flat.
- **Restoration and disposition:** exact G1 restored (Master `ac45e5c1…`, manifest `d810d648…`,
  sidecar `bcd97641…`). The probe and pointer were removed. PASS disposition: the installed app is
  `bfba4d3a…`. The final Scripts inventory differs from the accepted Session 4 inventory only by the
  app line.
- **OWNER-1 historical files:** present and inert; never loaded, never used as authority.
- **Deviation (no effect):** the operator ran the installed Session 1 probe once before A5. Its
  broker counters were unchanged and it caused no acquisition.
- **Evidence:**
  - `real_sfm_qualification/cpm_item8_post_cleanup/ITEM8_EVIDENCE.md` §6;
  - redacted raw files in `raw/I8A1/` (82 files; `raw/MANIFEST.md`).

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
package, Normalizer, Master and sidecars are unchanged. Item 8 (real SFM) changed no repository
product file. The pre-K UI polish pass changed only presentation in the app (`bfba4d3a…` → `5c6e2789…`, refined to
`7e4686d7…`).

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

**Deployed and verified** (runbook §0; re-verified at the 2026-10-06 transfer checkpoint and by
item-8 `I8-Preflight`/disposition on 2026-10-08 and the U1–U3 deployments on 2026-10-09; the shared package's qualification-only
`projections.py` is intentionally not deployed):
- launcher `996ca483…` as the Scripts-menu entry;
- private app **`4e35f292…`** (final pre-K UI build, LIVE VERIFIED / PASS in U3, 2026-10-09; the
  builds it replaced, `7e4686d7…`, `5c6e2789…` and the item-8-qualified `bfba4d3a…`, are
  preserved, see below) in
  `usermod/scripts/ChadChan3D_CPM/` (outside `scripts/sfm`, no `__init__.py`);
- probe v3 `ce4ace98…`.

Rollback chain, held in the local U3/U2/U1 attempt folders: `7e4686d7…` → `5c6e2789…` →
`bfba4d3a…`. `bfba4d3a…` can also be restored from git (`2fe9a27`). The previous app `9a78fc96…` remains restorable from git (`9d405c8`). The item-8 probe and campaign
pointer are not deployed. The Scripts deployment equals the accepted Session 4 inventory
(`cefc2b88…`) except the private-app line (U3 inventory `59b8f28b…`). The live authority is exact
production G1. Any later deployment change follows the R15 restart rule.

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
| §22 item 8 `I8A1`: post-cleanup candidate `bfba4d3a…`, Phases A–F (2026-10-08) | **PASS** |

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
- **§22 item 8 `I8A1` (2026-10-08, pid 36912, broker `0x310a7810`):** see Current milestone and
  `ITEM8_EVIDENCE.md` §6. Sessions 1–4 above qualify `9a78fc96…`; `I8A1` qualifies `bfba4d3a…`.
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
  1. **Legacy preset.** Still open. Apply of an old `body.scale.head` preset is refused. Future
     message: "This preset uses an outdated scale format. Delete this preset and save a new Body
     preset." This is a legacy edge case only; generic bone-scale persistence works.
  2. **Implemented in the pre-K UI polish pass, LIVE VERIFIED / PASS (final build `4e35f292…`,
     U2 + U3):**
     - Update Preset confirmation copy, with no question icon;
     - wider window with all tabs visible;
     - semantic button colors;
     - 2×2 Review grid;
     - Clear Classification wording.
- **Stale-scope UI presentation** and **`SidecarMissing` messaging:** undecided.
  - Real SFM shows that a stale-generation refusal is presented through the guard's generic copy.
    For Apply this is "Preset could not be applied safely…"; for Save it is "Can't save preset —
    Preset could not be saved. Nothing was saved."
  - The stale-scope reason is logged only, and CPM then rebuilds automatically.
- **Product identity strings** (window slot, log name, `PROD_VERSION`) are unchanged from G18AN
  (K/L).
- **Item-8 findings (K/L; user-facing, not failures):**
  1. **Scene source.** CPM resolves its scene from the shot under the playhead
     (`sfmApp.GetShotAtCurrentTime()`). The Normalizer uses the Clip Editor selection. The UI pass
     explains the playhead workflow in Help only; the behavior is unchanged by design.
  2. **Normalizer success.** A successful Normalizer run shows no visible completion confirmation.
     Recommendation: a non-blocking success notice, with modals only for failures or decisions.
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
    **COMPLETE / PASS** (`I8A1`, 2026-10-08; candidate `bfba4d3a…` real-SFM qualified and
    installed).

  - Pre-K CPM UI polish pass: **LIVE VERIFIED / PASS** (`7e4686d7…`, U2; supersedes `5c6e2789…`,
    whose U1 attempt was closed as SUPERSEDED / NO QUALIFICATION VERDICT). It is superseded in the
    repository by the Help-wording-only candidate `4e35f292…` (offline PASS; not deployed).

  - Final pre-K UI build `4e35f292…`: **LIVE VERIFIED / PASS** (U3, Help wording delta from U2).

  **Pre-K complete. `4e35f292…` is the exact CPM candidate eligible to enter K.**
  K and L have not started. K requires its own authorization and must begin in a fresh SFM process.
  L's final installation layout is undecided.
- **Session 4 notes (not failures; carried to K; unchanged by items 7–8):**
  - Fit's exception path releases the stage with a bare `release()` (no
    `PROD_CPM_FIT_STAGE_RELEASED` line; result discarded); a raising success-path release could in
    theory be followed by a second `release()`. Live S4F shows exactly one successful release per
    injected stage.
  - The Body bone-scale branch of rollback verification is covered offline only (`BodyTest` changes
    no bone scales); Expression Apply shares `prod_apply` and is covered offline.
- R3, R6, R9, R13, R14, R15: CLOSED. Offline: Suites 1–4 PASS; C7–C10 PASS (C10 also real-SFM);
  R15 suite PASS.

## Next
K1 is in progress: execute K1A2 (fresh SFM process; unchanged K1 runbook) under the existing K1
authorization. K2 needs separate authorization. L has not begun. `4e35f292…` remains installed.

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
