# CPM Item-8 Focused Post-Cleanup Real-SFM Qualification Design

**Status: owner-approved design, incorporating the three required corrections.**

Qualify the exact post-item-7 candidate in **one fresh SFM process**, using ordinary operations, one Save-prompt generation transition, one production Normalizer command, and two close/reopen transitions.

Do not repeat the forced rollback or queued-Fit interruption campaigns. Do not change production code, reopen R14/R15, or begin K/L.

## 1. Synchronization and exact-build authority

The design is based on the following verified local state:

| Authority | Verified value |
|---|---|
| Repository | `<repository root>` |
| Branch checkpoint | `0e6a1e3c58cd40f9489ec80e368d10b788a25c84` |
| Local `origin/master` | Same commit |
| Candidate app SHA-256 | `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` |
| Previously installed private app SHA-256 | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` |

The repository contains untracked historical evidence files. They are not candidate changes and must remain untouched. Verification used the local remote-tracking reference; it was not a fresh GitHub synchronization.

**Current disposition:**

- Items 6–7: complete, offline qualification PASS.
- Candidate `bfba4d3a…`: not deployed or real-SFM qualified.
- Sessions 1–4: historical qualification of `9a78fc96…`.
- Item 8: design approved; preparation and execution not started.
- K/L: not started.

The governing sources are the current [Ledger](cpm/qualification/CPM_CONVERGENCE_LEDGER.md), [handoff](docs/qualification/CPM_CONVERGENCE_INTEGRATION_HANDOFF.md), [item-7 evidence](cpm/qualification/ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_EVIDENCE.md), and [R15 Blueprint](cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md).

## 2. What item 8 must establish

The cleanup creates four relevant regression risks:

1. **Authority routing:** removing historical machinery must leave actual SFM operations exclusively on the canonical broker.
2. **Execution continuity:** diagnostic removal and exception protection must not alter UI/native operation completion, persistence, or cleanup.
3. **Observability:** retained events and independent observations must still distinguish success, refusal, commit, and idle ownership.
4. **Real-process lifecycle:** the new bytes must preserve module isolation, window reuse, close/reopen behavior, and Normalizer coexistence.

Item 8 must establish those properties for the **new exact bytes**. It need not independently re-prove every semantic branch already covered by unchanged code, reconstruction, and historical runtime evidence.

### Evidence reused

- Sessions 1–4 establish the earlier runtime behavior and known qualifications.
- Item-6 qualification establishes the authority cleanup offline.
- Item-7 reconstruction, unchanged-block checks, existing suites, new qualification, and mutation sensitivity establish a strong bounded-change argument.
- R14/R15 establish the private-module and resource-telemetry architecture.
- Session 2 establishes the genuine publisher-based generation-change mechanism.
- Sessions 3–4 establish queued-Fit generation protection and forced rollback behavior.

This is **combined evidence**, not a claim that historical runtime PASS automatically transfers to the candidate.

## 3. Exact campaign scope

Use the established Krystal clothing fixture and Mia fixture. Record their actual session-file identities during preparation; do not invent a fixture filename or assemble a new synthetic scene.

The prepared fixture manifest must identify:

- `krystal20201` and `assaultsuitbody1`, including model paths/checksums;
- the available unselected clothing peer used for isolation observation;
- `mia1` on the established `shot3` fixture;
- a supported Body control and Expression control for deliberate changed-state operations;
- supported channel states for snapshot comparison;
- the Selected shot as a proper subset of the Normalizer’s project scope.

The source identities are documented in the [Session-4 harness](real_sfm_qualification/cpm_session4/CPM_S4_Rollback_Harness.py). Fixture availability and current contents must be verified before execution.

### Required scenarios

| Phase | Scenario | Purpose |
|---|---|---|
| A | Exact deployment and fresh-process identity | Exclude stale/private-module and dependency confusion |
| B | Krystal launch, compatible-window reuse, one ordinary Fit, native Undo | Exercise target authority, native work, completion and release |
| C | Title-bar close; Mia reopen; Body Save/Update/Apply/Undo and Expression Save/Apply/Undo | Exercise cleanup, persistence, scopes and both operation kinds |
| D | One production Selected Normalizer command with CPM active; CPM Apply and Save without reselection | Prove candidate coexistence and continued use of the existing scope |
| E | G1→G2 during a Body Save prompt; refusal, automatic rebuild, deliberate G2 Save | Exercise freshness after a UI yield and no-replay behavior |
| F | Escape close; reopen under G2; final close, exit and exact restoration | Confirm teardown, stable module ownership and campaign cleanup |

**A valid item-8 campaign attempt uses one fresh SFM process from Phase A through SFM exit in Phase F. If that SFM process exits, crashes, or must be restarted before Phase F, the attempt is incomplete/inconclusive; preserve its evidence and begin any replacement attempt from Phase A in a new write-once attempt directory.**

Changing between the established fixture documents is permitted after closing CPM and observing idle ownership. Do not save either fixture document.

### Deliberately excluded

Do not repeat:

- Session-3 queued second-target interruption;
- Session-4 forced verifier failure or release fault injection;
- R15 foreign-window, notice-lifetime, changed-build refusal, or legacy-launch campaigns;
- separate stale-Apply testing in addition to the Save-prompt test;
- Expression Update solely for symmetry with Body Update;
- Review/Reclassify and the full taxonomy fixture matrix;
- full Normalizer requalification or repeated alternation;
- performance benchmarking, authority throughput tests, or stress loops.

Those paths have existing evidence and unchanged semantics. The selected scenarios test the real-SFM consequences of cleanup without expanding item 8 into K.

## 4. Deployment and restart procedure

This section specifies future execution; nothing is deployed by this design.

### Production file replacement

Source:

`cpm/app/SFM_Character_Preset_Manager.py`

Destination:

`<SFM game>/usermod/scripts/ChadChan3D_CPM/SFM_Character_Preset_Manager.py`

Required procedure:

1. Close every SFM process.
2. Record repository commit, candidate hash, installed-file hash, and the installed dependency inventory.
3. Copy the installed `9a78fc96…` app into the write-once campaign backup directory. Verify its full hash.
4. Verify the source app is exactly `bfba4d3a…`.
5. Replace only the private implementation file, using a temporary sibling followed by replacement.
6. Verify the destination’s full SHA-256.
7. Verify all other production dependencies remain unchanged.
8. Install only the separately qualified item-8 probe.
9. Start a fresh SFM process.

**Closing the CPM window is not sufficient.** R15 keeps the application module resident for the SFM process. Do not delete `sys.modules` entries, reload the module, or use an existing process after replacement.

### Files that remain unchanged

- Thin menu launcher, SHA:
  `996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51`
- CPM adapter and projection.
- Shared authority deployment.
- Production Normalizer.
- Frozen G18AN baseline.
- Historical probes, harnesses and raw evidence.
- Master/sidecar, except the controlled generation test and exact restoration.

Compare the shared package against the **accepted installed manifest**, not every repository Python file: qualification-only files are not necessarily deployed.

### Pre-run harness exclusion

Inventory the relevant Scripts-menu and private-module locations. Confirm:

- no old full CPM implementation under the SFM menu-discovery tree;
- no deployed Session-3/Session-4 mutating harness;
- no active campaign pointer or flag enabling an old harness;
- no stale notice/timing harness flags;
- no unexpected qualification script or duplicate authority package.

Preserve historical files outside deployment. Do not indiscriminately delete anything.

## 5. New item-8 observation tools

Prepare a **new item-8 probe**, not a repinned historical probe.

The existing [Session-1 probe](real_sfm_qualification/cpm_session1/CPM_Session1_Probe.py) contains optional timing operations that acquire authority and optional notice behavior. Those modes must not exist in the item-8 revision.

### Probe contract

The item-8 probe must:

- execute with isolated local names in the shared Scripts-menu environment;
- inspect already-loaded modules without constructing a broker;
- avoid authorizing operations, opening adapters, acquiring views, or evaluating semantic readiness;
- avoid calling `G18AN_POST_FIT_ACTION_STATE` or its readiness helper;
- install no wrappers, timers, callbacks, modal dialogs, or mutation hooks;
- retain no DME objects after writing its record;
- write only campaign evidence.

Record:

**Identity**

- PID and Python version;
- installed implementation and launcher hashes;
- private-module name, origin, loader identity, state and build SHA;
- module/class/function-global ownership;
- window ownership and census;
- run ID and log destination.

**Authority and lifecycle**

- canonical runtime origin/build/API and broker identity;
- outstanding leases, unreleased lease registry and open provider count;
- bounded view/cache accounting and generation identities;
- scope generation and semantic counts;
- operation/Fit/stage/modal-defer state;
- active watcher count and window slot;
- all preserved historical provider counters and provider reference.

**Resources**

- PrivateUsage, working set, handles, GDI and USER counts;
- existing bounded scope/cache accounting;
- errors explicitly, never substituted with zero.

Record broker counters immediately before and after observation. The probe must not itself cause an acquisition.

### Scene and persistence observations

Add a narrow snapshot mode for the **explicit fixture animation sets only**:

- control identity and literal;
- source/destination/evaluated values;
- supported channel/log state and relevant key values;
- native Undo enabled/count/description;
- selected and unselected Fit target values;
- relevant bone-scale state only where the exercised operation actually includes it.

Do not traverse the whole session.

The Session-4 snapshot uses CPM’s own read helpers. Reusing those helpers gives a useful state observation, but **not an independent semantic oracle**. Item 8 must pair snapshots with:

- operator-observed native Undo;
- expected values chosen before the operation;
- direct file readback;
- explicit unchanged-peer comparisons.

No PASS may rest solely on a production “verified” flag.

### Offline preparation gates

Under Python 2.7.5 and Python 3.10, qualify the new probe and evidence reader for:

- exact candidate pinning;
- missing module/broker handling;
- no acquisition or semantic action;
- no retained runtime objects or callback installation;
- current event formats;
- explicit observation failures;
- write-once output handling.

Reuse the unchanged Checkpoint-I publisher/helper. A new item-8 shell driver may supply new campaign paths and record identities, but must preserve its publication, hash-gating and recovery behavior.

No new in-SFM mutation harness is needed.

## 6. Operator runbook

Use numbered checkpoints with a short operator record: **step, time, action, visible result, evidence filename**.

Wait for actual operation completion. At idle checkpoints, allow queued cleanup to settle before probing. A 60-second wait allowance is an observation window, not a performance requirement; never interpret a timeout as permission to continue.

### Phase A — fresh-process verification

1. Open the established Krystal fixture.
2. Run the item-8 probe before launching CPM.
3. Open CPM through the normal thin launcher.
4. Select Krystal and wait for a healthy scope.
5. Probe.
6. Click the CPM launcher again.
7. Probe again.

**PASS:**

- Python 2.7.5;
- exact `bfba4d3a…` private-module build;
- correct private origin and function globals;
- one owned CPM window and one active watcher;
- second click reuses the same window/module/run ID/scope;
- no authority acquisition caused by the second click;
- no historical provider activity;
- idle broker counts are zero.

### Phase B — one ordinary Fit and Undo

1. Select only `assaultsuitbody1` as the Fit target.
2. Establish a meaningful difference using ordinary fixture controls if needed.
3. Record source, target and unselected-peer snapshots, plus Undo state.
4. Run Fit once.
5. Wait for completion and probe.
6. Use SFM native Undo once.
7. Record restoration and idle state.

**PASS:**

- actual changed target state, not merely a no-op;
- source and unselected peer remain unchanged by Fit;
- expected mapping behavior, including the established target-only vocabulary case;
- truthful warnings/partial accounting where the fixture normally produces them;
- native Undo restores the pre-Fit state;
- stage activity ends and all authority ownership returns idle.

Do not demand historical mapping counts if deliberate fixture values differ; do demand a pinned fixture and an explained result.

Then close CPM with the title-bar **X**. After settling, require an empty window slot, no live CPM window/watcher, no active Fit operation and zero idle authority ownership.

### Phase C — reopen and ordinary persistence/Apply

1. Open the established Mia fixture in the **same SFM process**.
2. Reopen CPM and select Mia.
3. Verify the same private module/class/run ID and a newly owned window.
4. Use campaign-unique preset names.

**Body sequence**

- Set a supported Body value.
- Save a new disposable preset.
- Read the written JSON directly.
- Change that Body value and Update the same preset.
- Read back the updated value and inventory changes.
- Move the live control away from the stored state.
- Capture the pre-Apply state.
- Apply the updated preset.
- Verify the actual changed state.
- Native Undo once; verify restoration.

**Expression sequence**

- Save one disposable Expression preset with a known supported value.
- Verify file readback.
- Move away from that value.
- Apply it and verify the actual change.
- Native Undo once; verify restoration.

The Body and Expression fixtures must have qualifying controls identified during preparation. A missing fixture is **INCONCLUSIVE**, not a skipped PASS.

At the end, probe idle authority, scope, module/window and historical-provider state.

### Phase D — minimum Normalizer coexistence

Keep CPM open on Mia’s existing active scope.

1. Record module/window/scope/broker identities and scene values.
2. Run the unchanged production **Selected** Normalizer once on the established shot.
3. Respect its existing admission policy.
4. Wait for the actual final completion report.
5. Record Normalizer resource results and probe.
6. Return to the **same CPM window and scope, without reselection**.
7. Make a normal changed-state Body Apply; verify it.
8. Save a new disposable Body preset; read it back.
9. Undo the Apply before unrelated scene edits, and verify restoration.

**PASS requires normal Apply and Save continuation.**

A stale-authority refusal is not acceptable here. Any independently legitimate scene-state refusal stops the phase for adjudication; it is not automatically a candidate defect or a PASS.

Also require:

- the same canonical broker serves both consumers;
- valid Normalizer resource telemetry;
- no namespace or log-destination contamination;
- CPM still owns its original window/module;
- idle leases/providers return to zero.

Do not run another Normalizer command, All Shots, or an alternation campaign.

### Phase E — one controlled Save-prompt generation transition

Use the corrected Session-2 Save-prompt pattern, with new item-8 evidence paths.

**ARM**

1. Confirm healthy G1 scope and idle ownership.
2. Capture scene/Undo state.
3. Inventory the affected character-library subtree, including metadata and backup files.
4. Open Body **Save New**, enter a unique stale-test name, and leave the prompt open.

**ACT**

5. Outside SFM, publish and activate G2 using the frozen Checkpoint-I tooling.
6. Perform publication and activation back-to-back, with no SFM interaction between them.
7. Verify exact G2 activation and capture another library inventory.
8. Confirm the already-open Save prompt.

**OBSERVE**

9. Require generation-mismatch refusal before persistence.
10. Dismiss the refusal.
11. Do not reselect the model.
12. Wait for the automatic G2 scope rebuild.
13. Capture library, scene/Undo and probe state.
14. Deliberately click Save New again, with a different unique name.
15. Require successful G2 Save and independent readback.

**PASS:**

- G1 scope was active when the prompt opened;
- exact G2 activation happened while it remained open;
- authorization after prompt return refuses the stale operation;
- library inventories before the prompt, after activation, and after refusal are identical;
- no scene mutation or new mutation Undo item;
- one resulting G2 scope publication, without automatic Save replay;
- deliberate later Save succeeds under G2;
- resulting file changes are limited to the expected preset/profile/backup effects;
- idle ownership returns to zero.

Do not rigidly require three changed files: a metadata write may leave identical bytes. Require the expected new preset, valid readback, and **no changes outside the allowed persistence footprint**.

**RESTORE** occurs after SFM exits in Phase F.

### Phase F — Escape teardown, reopen and exit

1. Close CPM with **Escape**.
2. Observe completed teardown and zero idle ownership.
3. Reopen CPM in the same process.
4. Confirm stable private module/class/run ID, one new owned window/watcher, and a healthy G2 scope.
5. Leave it idle briefly and probe.
6. Close normally and probe final teardown.
7. Exit SFM without saving fixture documents.
8. Restore exact G1 with the qualified finalization mechanism.
9. Require an exact baseline inventory comparison.

This covers both close routes without repeating R15’s three-cycle and foreign-window campaigns.

## 7. Events and independent acceptance evidence

Use the item-7 event contract.

| Area | Supporting events | Required corroboration |
|---|---|---|
| Deployment/lifecycle | `PROD_R15_MODULE`, window reuse/shown, close request/finalized | File hashes, module/window ownership, Qt census |
| Scope/authority | Provider health/gate, scope-ready, operation authorized/refused | Canonical broker state, full generation identities, historical counters |
| Body/Expression | Operation begin/phase/end, Save/Update/Apply outcomes | JSON readback, actual control changes, native Undo |
| Fit | Stage open/released, Fit stage/result | Target/peer snapshots, stage state, Undo, zero idle ownership |
| Generation | Authorization refused, rebuild scheduled/rebuild | External publication records and identical refusal-period library inventories |
| Resources | Retained resource events | Probe measurements and lifecycle accounting |

Do not expect:

- `PROD_PERF`;
- `ASTRA_PERF`;
- `PROD_ACTION_TIMING`;
- the removed candidate dump;
- `CLOTHING_FIT_RESULT=PASS`.

The current Fit result begins `CLOTHING_FIT_RESULT generation=…`. Its callback `generation` is distinct from authority `gfit`.

The `MODEL_RENDER_BEFORE_SCOPE`→`MODEL_RENDER_AFTER_SCOPE` bracket may be recorded descriptively. It includes diagnostic overhead and is not equivalent to the old timing metric.

## 8. Idle ownership and historical-provider proof

At each completed operation and close checkpoint, require:

- outstanding leases: **0**;
- unreleased lease registry: **0**;
- open packed providers: **0**;
- no active operation or running Fit stage;
- no deferred Fit continuation left pending;
- expected window/watcher census.

Detached bounded views may remain cached. **Idle does not mean an empty view cache.**

For historical machinery, record:

- `_SEMANTIC_PROVIDER is None`;
- open/reuse/invalidation/production-parse/generation telemetry remains at its inactive baseline;
- canonical module and broker identities;
- successful operations attributable to canonical consumer views.

Zero telemetry alone cannot prove absence of every possible hidden route. The conclusion combines these runtime observations with item-6 route removal and offline qualification. Missing legacy log lines are not proof.

### Known Fit release observation

Carry the Session-4 note unchanged:

- one exception path uses bare `release()` without its own release event and discards the result;
- a raising success-path release could theoretically lead to another attempt;
- Session-4 observed one successful release in its exercised injected stages.

Item 8 observes the ordinary Fit path’s actual state and retained events. It does **not** prove the exceptional path repaired, and must not instrument or repair it silently.

An observed leak, release error, or credible double-release evidence is a STOP requiring separate adjudication.

## 9. Resource interpretation

Record resources at:

- initial scope;
- repeated launcher click;
- Fit completion/Undo;
- each closed state;
- each reopen;
- before/after Normalizer;
- generation rebuild;
- final idle and closed states.

Separate:

- CPM scope/cache accounting;
- process PrivateUsage;
- working set;
- handles/GDI/USER objects;
- the Normalizer’s known process-retained resource effects;
- fixture loading effects.

Do not invent a new MB threshold or require memory to return exactly to startup.

A higher reading after Normalizer is not, by itself, a CPM regression. Persistent duplicate objects, nonzero ownership, repeated acquisition while idle, or an unexplained growing retention pattern is material.

If resource behavior becomes suspicious, stop qualification and preserve evidence. Do not convert the run into an unbounded stress investigation.

## 10. PASS, FAIL, INCONCLUSIVE and STOP

**PASS:** the scenario was exercised on pinned bytes, its required observations exist, and all acceptance conditions hold.

**FAIL:** an observed product behavior violates the contract—for example, stale persistence, incorrect Apply, failed Undo, ownership leakage or namespace contamination.

**INCONCLUSIVE:** the proposition was not validly exercised or observed—for example:

- wrong/missing fixture;
- no-op instead of required changed Apply/Fit;
- early G2 rebuild before the intended stale boundary;
- missing snapshot or unreadable required state;
- operator action contaminating the comparison;
- missing evidence because retained observability proved insufficient.

A campaign attempt whose SFM process exits, crashes, or must restart before Phase F is **incomplete/inconclusive**. Preserve any observed product failure as a finding; do not erase it through the attempt classification. Any replacement attempt starts at Phase A in a fresh process and a new write-once attempt directory.

**STOP:** halt further campaign operations on any safety, identity, restoration or evidentiary failure. STOP is an execution action; subsequent adjudication determines FAIL versus INCONCLUSIVE.

Mandatory STOP conditions include:

- candidate/deployment hash mismatch or unexpected changed dependency;
- historical provider activity;
- nonzero idle ownership;
- stale operation mutating or persisting;
- automatic replay after refusal;
- failed native Undo restoration;
- persistence/readback mismatch;
- Fit-stage leak or release anomaly;
- failed intended post-Normalizer continuation;
- duplicate module/window/watcher ownership;
- material unexplained resource accumulation;
- insufficient required observability;
- incomplete G1 restoration.

Do not patch production logging or implementation during the campaign.

## 11. Evidence layout and restoration

Prepare a new directory beneath:

`real_sfm_qualification/cpm_item8_post_cleanup/`

Required files:

```text
ITEM8_RUNBOOK.md
CPM_Item8_Probe.py
test_cpm_item8_probe.py
ITEM8_GENERATION_DRIVER.ps1
ITEM8_EVIDENCE.md
raw/<attempt-id>/
    authority_pins.json
    deployment_before.json
    deployment_after.json
    fixture_manifest.json
    operator_steps.md
    probe.jsonl
    scene_snapshots/
    library_inventories/
    preset_readback/
    generation/
    logs/
    restoration/
    SHA256SUMS.txt
```

Use a new write-once live output folder for every attempt. Preserve failed and inconclusive attempts.

Pin full hashes for:

- candidate and previous installed app;
- launcher, adapter, projection, Normalizer;
- accepted shared deployment;
- new probe/driver/tests;
- frozen publisher/helper;
- fixture files;
- G1/G2 artifacts.

Known generation pins:

| Item | SHA-256 |
|---|---|
| G1 Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| G2 Master | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` |

At closeout:

- restore exact G1 using recorded publisher recovery;
- archive generated presets and inventories before cleanup;
- restore only campaign-owned library changes from recorded backups, after confirming no intervening unrelated changes;
- remove the exact temporary item-8 probe, campaign pointers/hooks, and other qualification-only deployment;
- verify installed production dependencies;
- preserve every raw log and failure record.

### Final deployment policy

**After PASS:**

- Leave the exact qualified candidate\
  `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`\
  installed.
- Remove only temporary qualification deployment.
- Record explicitly that the qualified candidate remains installed.
- K, if subsequently authorized, must begin in a **fresh SFM process**.
- This does not decide L’s final installation layout.

**After FAIL or INCONCLUSIVE:**

- With SFM closed, restore the previous installed app:\
  `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`.
- Verify its full hash exactly.
- Preserve the candidate attempt’s evidence and findings.

## 12. Ledger consequence and K authorization

After preparation only:

> **§22 item 8 — PREPARED, NOT RUN.** Exact candidate `bfba4d3a…` remains pending real-SFM qualification. New item-8 observation tools qualified offline. Historical Sessions 1–4 unchanged. K/L not started.

After a fully evidenced PASS and exact restoration:

> **§22 item 8 — COMPLETE / PASS.** Exact candidate `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` qualified in one fresh real-SFM Python 2.7.5 process for focused post-cleanup operation, persistence, native Undo, ordinary Fit, generation refusal/rebuild, canonical idle ownership, Normalizer coexistence and close/reopen behavior. Historical forced rollback and queued-Fit evidence retained with their existing qualifications. Exact G1 restored. Temporary item-8 probe, campaign pointers/hooks and other qualification-only deployment removed. **The exact qualified candidate remains installed.** No new convergence blocker. **CPM is eligible to enter K; K/L have not started. K, if subsequently authorized, must begin in a fresh SFM process.** This checkpoint does not decide L’s final installation layout.

K eligibility requires:

- all required phases PASS within one valid campaign attempt;
- independently reviewable raw evidence;
- no unresolved product failure or required observation gap;
- exact authority restoration;
- completed deployment closeout, with the qualified candidate left installed;
- explicit disposition of any anomaly.

A design approval or offline probe PASS does not authorize K.

## 13. Bounded execution assignment

Prepare the new item-8 runbook, observation-only probe, offline tests, fixture/pin manifest and external generation driver. Preserve all historical artifacts and production dependencies.

After preparation gates pass, execute exactly the six-phase campaign above on the pinned candidate, in one fresh SFM process. Stop at the first material failure or invalid observation, restore safely, and report actual results. A replacement attempt must begin from Phase A in a new process and new write-once attempt directory.

Do not add fault injection, production instrumentation, semantic fixes, new optimization work, or extra historical replay. Complete item-8 adjudication and Ledger closeout, applying the explicit PASS/FAIL deployment policy, then stop before K/L.
