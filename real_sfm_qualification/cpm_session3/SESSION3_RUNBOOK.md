# CPM real-SFM Session 3 — Clothing Fit generation interruption (runbook)

**Status: prepared, not run.** Session 3 proves the handoff §15 / §21 Clothing Fit generation
transition:
- one user Fit owns `Gfit` = G1;
- target 1 commits;
- G2 becomes current before target 2;
- target 2 is refused before mutating, and the Fit stops with truthful accounting;
- target 1's Undo stays valid;
- CPM rebuilds under G2;
- a later new Fit runs under G2.

No product, launcher, Normalizer, adapter/projection, shared authority package, sidecar or preset
format changes. Record actual results only, in `SESSION3_EVIDENCE.md`, at closeout.

## 0. Design and identities

**Why a qualification hook is needed.**
- **The timing:** target 1's stage takes about 0.15 s and ends with
  `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`. Target 2 is then queued with a **zero-delay**
  timer.
- **The only pause point:** CPM's only pause between targets is the production deferral at the top
  of `fit_stage`. It applies when `scene_activity_suspended` is set, which happens only through the
  100 ms foreign-modal watcher.
- **Conclusion:** no human (or polling timer) can reliably act between the two targets. This is the
  same problem Checkpoint I solved with a per-instance wrapper.

**The hook.** `S3_Fit_Pause_Harness.py` is qualification-only; its SHA-256 is in §2.2. It is
deployed temporarily to the ChadChan3D Scripts menu and removed at closeout with an exact
deployment comparison. It is one state-driven menu script:

| Campaign state | Mode | Visible result |
|---|---|---|
| no `harness_arm_record.json` | ARM | `S3 ARMED` |
| arm + valid pause + resume records, no undo record | SNAPSHOT | `S3 UNDO SNAPSHOT WRITTEN` |
| anything else | REFUSE | `S3 HARNESS REFUSED` |

The result is printed to the SFM console and shown in a non-modal harness notice.

**ARM** checks every precondition (§5 C4) before installing anything:
- CPM is ready and idle;
- source `krystal20201` is selected, with its scope at G1;
- both targets are Fit candidates;
- leases, unreleased and open providers are all 0;
- the live Master is G1;
- no G2 or harness records exist yet.

It records target 1's pre-Fit values using CPM's own read-only helpers (`g11a_resolve_target`,
`p01_all_supported_flex_bindings`, `binding_snapshot`). It then installs a one-shot wrapper as an
instance attribute on the live window's `fit_stage`.

**The wrapper:**
- Index 0 passes straight through, as does any call that is not the armed Fit's target 2.
- At **target-2 entry** it removes itself, then runs two gates. If either fails, it records INVALID
  and **never invokes target 2**.
- **Gate B (target-1 boundary):**
  - Fit active as a `Clothing Fit` operation;
  - selected targets exactly [target 1, target 2];
  - committed exactly [target 1];
  - `fit_stage_running == False`;
  - broker leases, unreleased and open providers all 0;
  - `Gfit == G1`;
  - live Master G1;
  - target 1's post-commit values differ from its pre-Fit values in at least one value.
- **Gate A (modal establishment):** it shows a parentless application-modal "CPM Session 3 —
  Fit paused" dialog and runs CPM's own `poll_foreign_modal()` once. It then requires all three of:
  - the dialog is `QApplication.activeModalWidget()`;
  - `window.modal_yield_active` is True;
  - `window.scene_activity_suspended` is True.
- **Only then** does it call the unmodified `ProdWindow.fit_stage(window, generation, 1)`. Production
  takes its `G18AN_MODAL_DEFER_FIT` branch, and the harness verifies
  `modal_deferred_fit_stage == (generation, 1)`.

**Continue.** It is enabled only for a valid pause. It closes the dialog only when exact G2 is
proven: live Master `54413b6c…`, a valid activation record, and an exact-G2 post-switch inventory.
CPM's own watcher then resumes target 2, and the §15 Gfit proof runs at that resume boundary.

**Why production semantics are unchanged:**
- no product file changes;
- the harness never writes authority files and never calls the broker; it only reads counters;
- the injected event, a foreign dialog, is one any SFM dialog causes;
- the watcher check the harness runs once is the same code the 100 ms timer runs;
- CPM's deferral, resume, Gfit proof, stop, accounting and rebuild run unmodified.

Offline: `test_s3_fit_pause_harness.py` (§9).

**Authority switch.** The frozen Session 2 functions (`SESSION2_RUNBOOK.md` §2.1 at `0597927`), using
the unchanged Checkpoint I tooling.

| Generation | Master | Sidecar |
|---|---|---|
| G1 (production) | `ac45e5c1…` | `bcd97641…` |
| G2 (G1 + one LF, semantic parity) | `54413b6c…` | `cd370f67…` |

Phase A and Phase B run **during the pause**, back to back.

## 1. Rules (fail-closed)

1. **Session:** one fresh SFM process. Do not save the SFM document. Run no Normalizer or other
   authority tool.
2. **No CPM interaction:**
   - from ARM (C4) until the Fit click (C6), none except checking the two targets;
   - from the Fit click until **Continue**, none at all.
3. **Reselection:** never reselect the model after a warning; CPM rebuilds on its own.
4. **After any Phase A/B STOP:**
   - never click Continue and never resume the Fit; keep it paused;
   - close or terminate SFM without saving;
   - run exactly the recovery the shell printed (`S2-VerifyUntouched` or `S2-Finalize`).

   No SFM process may start again until exact G1 is restored.
5. **Write-once:** every record has one path per campaign. Never reuse, edit or delete a campaign
   folder; a retry uses a new folder (`S3_R2`, …).
6. **Operator role:** visible steps only. Logs and JSON are adjudicated after the campaign (§7).

## 2. Shell set-up

### 2.1 Session 2 functions (verbatim)

With SFM closed, paste the **frozen Session 2 §2.1 block** from `SESSION2_RUNBOOK.md` at commit
`0597927` unchanged, filling its two placeholders. It defines `S2-Prepare`, `S2-PhaseA`,
`S2-PhaseB`, `S2-VerifyUntouched` and `S2-Finalize`. Do not shorten or retype it.

### 2.2 Session 3 block (paste after 2.1)

```powershell
# ---- CPM Session 3 shell set-up. Paste AFTER the frozen Session 2 section 2.1 block. ----
foreach ($f in "S2-Prepare","S2-PhaseA","S2-PhaseB","S2-VerifyUntouched","S2-Finalize","S2-Sha","S2-New","S2-Json","S2-SfmClosed") {
    if (-not (Get-Command $f -ErrorAction SilentlyContinue)) { throw "STOP: paste the frozen Session 2 section 2.1 block first ($f missing)." }
}
$S3ROOT      = Join-Path $env:PUBLIC "Documents\CPM_Session3"
$E3          = Join-Path $S3ROOT "S3"                  # retries: S3_R2, S3_R3, ... (never reuse)
$SCRIPTS     = Join-Path $GAME "usermod\scripts"
$MENU        = Join-Path $SCRIPTS "sfm\mainmenu\ChadChan3D"
$HARNESS_SRC = Join-Path $R "real_sfm_qualification\cpm_session3\S3_Fit_Pause_Harness.py"
$HARNESS_DST = Join-Path $MENU "S3_Fit_Pause_Harness.py"
$HARNESS_SHA = "39440ca7fb4e63eb13ea7e06b102ccdc82cc343f7583cd0f31b1453146d30e9d"
$UTF8 = New-Object System.Text.UTF8Encoding($false)

# Deterministic Scripts-menu inventory: every file under usermod\scripts, relative path + SHA-256, ordinal sort.
function S3-ScriptsInventory([string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rows.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/') + "`t" + (S2-Sha $_.FullName))
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $UTF8)
    "SCRIPTS INVENTORY WRITTEN: $(Split-Path $Out -Leaf) files=$($arr.Count) sha256=$(S2-Sha $Out)"
}

# Deployment baseline BEFORE the harness is added (SFM closed, after S2-Prepare).
function S3-DeployBaseline([string]$E) {
    S2-SfmClosed
    if (-not (Test-Path -LiteralPath (Join-Path $E "baseline_inventory.json"))) { throw "STOP: run S2-Prepare first." }
    if (Test-Path -LiteralPath $HARNESS_DST) { throw "STOP: a harness file is already installed (residue). Report." }
    S3-ScriptsInventory (Join-Path $E "deploy_before_harness.txt")
}

# Temporary harness deployment (exact bytes, pinned SHA-256).
function S3-DeployHarness([string]$E) {
    S2-SfmClosed
    $rec = Join-Path $E "harness_deploy_record.json"; S2-New $rec; S2-New $HARNESS_DST
    if (-not (Test-Path -LiteralPath (Join-Path $E "deploy_before_harness.txt"))) { throw "STOP: run S3-DeployBaseline first." }
    if ((S2-Sha $HARNESS_SRC) -ne $HARNESS_SHA) { throw "STOP: repository harness is not the pinned SHA-256." }
    Copy-Item -LiteralPath $HARNESS_SRC -Destination $HARNESS_DST
    $got = S2-Sha $HARNESS_DST
    if ($got -ne $HARNESS_SHA) { Remove-Item -LiteralPath $HARNESS_DST; throw "STOP: installed harness SHA mismatch; removed." }
    [System.IO.File]::WriteAllText($rec, ('{"harness_sha256": "' + $got + '", "installed_relative": "sfm/mainmenu/ChadChan3D/S3_Fit_Pause_Harness.py", "wall_time": "' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '"}'), $UTF8)
    "S3 HARNESS DEPLOYED: sha256=$got"
}

# Point the harness at this campaign folder.
function S3-Activate([string]$E) {
    if (-not (Test-Path -LiteralPath (Join-Path $E "harness_deploy_record.json"))) { throw "STOP: run S3-DeployHarness first." }
    [System.IO.File]::WriteAllText((Join-Path $S3ROOT "ACTIVE_CAMPAIGN.txt"), (Split-Path $E -Leaf), $UTF8)
    "S3 CAMPAIGN ACTIVE: $(Split-Path $E -Leaf)"
}

# Authority switch during a VALID pause only (frozen Session 2 Phase A + Phase B).
function S3-Switch([string]$E) {
    $pause = Join-Path $E "harness_pause_record.json"
    if (-not (Test-Path -LiteralPath $pause)) { throw "STOP: no pause record; the harness has not paused the Fit. Do not switch." }
    if ((S2-Json $pause).status -ne "PAUSED_VALID") { throw "STOP: pause is INVALID; do not switch. Close SFM without saving, then S2-VerifyUntouched." }
    if (Test-Path -LiteralPath (Join-Path $E "harness_resume_record.json")) { throw "STOP: already resumed." }
    try { S2-PhaseA $E; S2-PhaseB $E }
    catch {
        "STOP: DO NOT CLICK CONTINUE. Keep the Fit paused; close or terminate SFM without saving; run exactly the recovery printed above; require exact G1 before any SFM start."
        throw
    }
    "S3 SWITCH DONE: click Continue in the pause dialog."
}

# Closeout: remove the harness and require the Scripts deployment to equal the pre-harness baseline exactly.
function S3-RemoveHarness([string]$E) {
    S2-SfmClosed
    if (Test-Path -LiteralPath $HARNESS_DST) {
        if ((S2-Sha $HARNESS_DST) -ne $HARNESS_SHA) { throw "STOP: installed harness is not the pinned file; do not delete. Report." }
        Remove-Item -LiteralPath $HARNESS_DST
    }
    $pointer = Join-Path $S3ROOT "ACTIVE_CAMPAIGN.txt"
    if (Test-Path -LiteralPath $pointer) { Remove-Item -LiteralPath $pointer }
    $before = Join-Path $E "deploy_before_harness.txt"; $after = Join-Path $E "deploy_after_removal.txt"
    S3-ScriptsInventory $after | Out-Null
    if ((S2-Sha $before) -ne (S2-Sha $after)) {
        Compare-Object (Get-Content -LiteralPath $before) (Get-Content -LiteralPath $after) | Format-Table -AutoSize | Out-String -Width 400
        throw "STOP: Scripts deployment differs from the pre-harness baseline. Report."
    }
    "S3 DEPLOYMENT RESTORED EXACT: no harness residue."
}
"S3 SHELL READY"
```

## 3. Fixture

The Session 1 completion-run Krystal scene:

| Role | Animation set | Model |
|---|---|---|
| Source | `krystal20201` (checksum −1441261258) | `models/fursonas/starfox/krystal/bodies/krystal2020.mdl` |
| Target 1 | `assaultsuitbody1` (−791536511) | `…/krystal/cosmetics/assaultsuitbody.mdl` (Session 1: 34-literal stage, 26 mappings, committed) |
| Target 2 | `loinclothbra_chadfix_071` (480892851) | `…/krystal/cosmetics/loinclothbra_chadfix_07.mdl` |

Fit order is the Fit-tree order: both targets are under **nearby**, with `assaultsuitbody1` first.

## 4. Campaign records (`%PUBLIC%\Documents\CPM_Session3\S3\`, write-once)

| Producer | Records |
|---|---|
| `S2-Prepare` | `g1_source.txt`, `baseline_inventory.json` |
| `S3-DeployBaseline` | `deploy_before_harness.txt` |
| `S3-DeployHarness` | `harness_deploy_record.json` |
| Harness ARM | `harness_arm_record.json` (preconditions, pre-Fit target-1 values) |
| Harness wrapper | `harness_pause_record.json` (`status` PAUSED_VALID / INVALID, gate B/A facts, post-commit values) |
| `S3-Switch` (S2-PhaseA/B) | `g2_source.txt`, `g2_plan_record.json`, `g2_publication_record.json`, `phase_a_stdout.json`, `g2_activation_record.json`, `phase_b_stdout.json`, `post_switch_inventory.json` |
| Continue | `harness_resume_record.json` |
| Harness SNAPSHOT | `harness_undo_snapshot.json` |
| `S2-Finalize` | `finalization_record.json`, `finalize_stdout.json`, `restored_inventory.json`, `restore_compare.json` |
| `S3-RemoveHarness` | `deploy_after_removal.txt` |
| Only if Phase A fails before its plan record | `untouched_inventory.json`, `untouched_compare.json` |

`ACTIVE_CAMPAIGN.txt` in `CPM_Session3\` is the harness's pointer, not evidence. It is removed at
closeout.

## 5. Operator procedure

A **P#** means: Scripts → ChadChan3D → `CPM_Session1_Probe`. Note the time. Run it only when no CPM
action or dialog is open.

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| C0 | Shell (SFM closed) | `S2-Prepare $E3`, then `S3-DeployBaseline $E3`, then `S3-DeployHarness $E3`, then `S3-Activate $E3` | `S2 BASELINE OK`, `SCRIPTS INVENTORY WRITTEN`, `S3 HARNESS DEPLOYED`, `S3 CAMPAIGN ACTIVE: S3`. Any STOP: stop (no authority change). |
| C1 | SFM | Start SFM fresh; open the Krystal scene. **P1.** | — |
| C2 | CPM | Open CPM; choose **krystal20201**; wait for the Body / Expression / Review counts. Open the **Clothing Fit** tab; confirm `assaultsuitbody1` then `loinclothbra_chadfix_071` under nearby. Do not check anything yet. | Counts appear; order as stated. |
| C3 | SFM | **P2** (G1 scope). | — |
| C4 | SFM | Scripts → ChadChan3D → `S3_Fit_Pause_Harness`. | `S3 ARMED`. Any `S3 HARNESS REFUSED`: stop → R1. |
| C5 | CPM | Clothing Fit tab: check **assaultsuitbody1** and **loinclothbra_chadfix_071**. Nothing else. | — |
| C6 | CPM | Click **Fit Selected to Model**. | CPM disappears; the **"CPM Session 3 — Fit paused"** dialog appears with "S3 PAUSED (valid)". If it says **INVALID**, or no dialog appears and the Fit finishes: stop → R1. |
| C7 | Shell | `S3-Switch $E3` | `S2 PHASE A OK`, `S2 G2 ACTIVE OK`, `S3 SWITCH DONE`. Any STOP: **do not click Continue** → R2. |
| C8 | Dialog | Click **Continue**. | The dialog closes and CPM reappears. Then CPM's **"Clothing Fit stopped"** dialog says it stopped after committing 1 target and to use SFM Undo 1 time. Click **OK**. Do not reselect. Wait (up to 60 s) for the counts. If Continue is refused: stop → R2. If the Fit reports success, or a second target changes: stop → R3. |
| C9 | SFM | **P3.** | — |
| C10 | SFM | **Edit → Undo** once (one Undo only). Confirm visually that `assaultsuitbody1` returned to its pre-Fit state. | — |
| C11 | SFM | Scripts → ChadChan3D → `S3_Fit_Pause_Harness`. | `S3 UNDO SNAPSHOT WRITTEN: target 1 RESTORED to its pre-Fit values.` "does NOT match": continue, but report (adjudicated). |
| C12 | SFM | **P4.** | — |
| C13 | CPM | Clothing Fit tab: check only **loinclothbra_chadfix_071** → **Fit Selected to Model**. | The Fit completes with no stop dialog and no error. A "skipped" status from production's expected structural skip (for example "has no established compatible Body mappings") is not a product failure; continue. A stop dialog, an error, or a failed / not-attempted status: R3. |
| C14 | SFM | **P5.** Close CPM with ✕; close SFM **without saving**. | — |
| C15 | Shell | `S2-Finalize $E3`, then `S3-RemoveHarness $E3`. | `S2 RESTORED EXACT G1`, then `S3 DEPLOYMENT RESTORED EXACT`. Otherwise R5. |

## 6. Recovery (fail-closed)

| Case | Signal | Action |
|---|---|---|
| R1 | Before any Phase A: ARM refused, INVALID pause, no pause, or the Fit finished without pausing | Do not run `S3-Switch`. Close or terminate SFM without saving. Run `S2-VerifyUntouched $E3` (requires `S2 UNTOUCHED`), then `S3-RemoveHarness $E3`. Invalid run; retry only in a new folder. |
| R2 | `S3-Switch` STOP (Phase A or B failed), or Continue refused | **Never click Continue; keep the Fit paused.** Close or terminate SFM without saving. If the shell said Phase A failed before any authority write: `S2-VerifyUntouched $E3`. In every other case (plan record exists, authority may have changed, Phase B failed, or Continue refused): `S2-Finalize $E3`. Require exact G1. Then `S3-RemoveHarness $E3`. No SFM start until both pass. |
| R3 | After Continue, target 2 runs, the Fit succeeds, or the later G2 Fit errors | Product finding: click nothing further in CPM. Close or terminate SFM without saving. `S2-Finalize $E3`, then `S3-RemoveHarness $E3`. Preserve all evidence and stop. |
| R4 | SFM crash or hang at any point after C0 | End SFM. If any `g2_*` record exists: `S2-Finalize $E3`; otherwise `S2-VerifyUntouched $E3`. Then `S3-RemoveHarness $E3`. |
| R5 | `S2-Finalize` not exact, or `S3-RemoveHarness` STOP | Do not start SFM. Do not edit the Master, authority or Scripts folders by hand. Preserve evidence and report. |

## 7. Adjudication (after the campaign; from the CPM log, probes and campaign records)

**INVALID run:** the harness never fired; the pause record is INVALID; G2 activation was not proven
during the pause; or there was CPM interaction between the Fit click and Continue. An invalid run
is restored and repeated in a new folder.

**PASS requires all of:**

1. **Gfit = G1:** the Fit start logs `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit'
   sha256=ac45e5c1…`.
2. **Target 1 committed under G1:**
   - `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=ac45e5c1…`;
   - a `native-commit` phase;
   - `CLOTHING_FIT_STAGE=PASS … index=0 … committed=True`.
3. **Lease released before target 2:**
   - `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True` precedes every index-1 event;
   - the pause record (PAUSED_VALID) shows `fit_before.fit_stage_running == false` and broker
     `outstanding_leases`, `unreleased_leases` and `open_providers` all 0;
   - `target1_changed_literals` is non-empty.
4. **Exact G2 between targets:**
   - the log has `G18AN_MODAL_YIELD_ENTER`, then `G18AN_MODAL_DEFER_FIT generation=N index=1`;
   - the pause record shows `modal` all true and `modal_deferred_fit_stage == [N, 1]`;
   - the activation record shows `post_activation_master_sha256 54413b6c…`;
   - `post_switch_inventory` is exact G2;
   - the resume record shows a live G2 Master;
   - then `G18AN_MODAL_YIELD_EXIT`.
5. **Gfit re-proved at the resume boundary:** `G18AN_MODAL_RESUME_FIT generation=N index=1`, then the
   index-1 stage proof.
6. **Refused:** `PROD_CPM_FIT_STAGE_REFUSED index=1 gfit=ac45e5c1… kind=u'generation-mismatch'`.
7. **Target 2 never mutated:**
   - no `PROD_CPM_FIT_STAGE_OPEN index=1`;
   - no index-1 native-commit;
   - `CLOTHING_FIT_FAIL … index=1 … committed_current=False`.
8. **No continuation under G2:** no further stage events for generation N.
9. **Truthful accounting:**
   - `CLOTHING_FIT_FAIL` shows `failed=[]` and `unattempted` = [loinclothbra_chadfix_071]. Target 1
     is in `changed` **or**, when it committed with plan warnings, in the partial set (it is then
     absent from `changed`);
   - `G18AN_FIT_FAILURE_DIALOG` shows `verified_changed=[u'assaultsuitbody1']`, empty
     `committed_uncertain` and `recovery_unverified`, `unattempted=[u'loinclothbra_chadfix_071']`
     and `undo_count=1`;
   - the "Clothing Fit stopped" dialog and the status say 1 target committed.
10. **Target-1 Undo valid:**
    - `harness_undo_snapshot.json` shows `undo_restored_pre_fit: true`: after-Undo equals pre-Fit,
      and after-Undo differs from post-commit;
    - plus the operator's visual confirmation at C10.
11. **Scope rebuilt under G2:**
    - `PROD_OPERATION_END … 'Clothing Fit'`;
    - `PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED`, then `…REBUILD`;
    - one automatic Select Model with `PROD_PROVIDER_HEALTH … sha256=54413b6c…`;
    - P3 shows the same window, scope `54413b6ca618`, and 0 leases / 0 open providers.
12. **A later new Fit under G2:** at C13:
    - `…AUTHORIZED operation=u'Clothing Fit' sha256=54413b6c…`;
    - `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=54413b6c…`;
    - `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`;
    - `CLOTHING_FIT_RESULT=PASS … failed=0 unattempted=0`. An expected structural skip
      (`CLOTHING_FIT_STAGE=SKIP`, counted in `skipped`) is not a product failure. It does not prove
      a G2 commit; that is proven by addendum S3_ADD (§10).
13. **No lease across queued stages:**
    - every `FIT_STAGE_OPEN` is followed by `RELEASED ok=True` before any later stage event;
    - P2–P5 and the pause record show 0 leases, 0 unreleased and 0 open providers.
14. **Exact restoration and no residue:**
    - `finalization_record` and `restore_compare` both report `exact_match: true`;
    - `deploy_after_removal.txt` is byte-identical to `deploy_before_harness.txt`.

**FAIL (product finding):**
- target 2 mutates or opens a stage under G2;
- the Fit continues under G2;
- wrong accounting;
- a lease or provider remains when idle;
- invalid Undo (once the visual and snapshot checks agree);
- no G2 rebuild;
- the new G2 Fit fails.

## 8. Return

Return the following:
- the probe JSONL;
- the CPM log;
- the full `%PUBLIC%\Documents\CPM_Session3\S3` folder;
- the shell window text (if retained);
- one note per step: done / problem.

At closeout, raw outputs are copied into the repository with workstation paths redacted (as in
Sessions 1 and 2).

## 9. Offline qualification of the harness

`test_s3_fit_pause_harness.py` runs the actual harness against the actual R15 launcher and private
CPM application (a real `ProdWindow`). It uses real PySide/Qt 4.8 on 2.7.5, plus the behavioural Qt
4.8 model on 2.7.5 and 3.10. It proves:
- ARM refuses on each failed precondition (12 cases) and writes nothing;
- index 0 and other generations pass straight through to production;
- a valid pause runs the real `poll_foreign_modal` and production's `G18AN_MODAL_DEFER_FIT` branch,
  with the wrapper disarmed and all three modal facts true;
- Continue is refused without the records and refused while the live Master is G1, then accepted
  for exact G2;
- the real watcher then resumes target 2 exactly once;
- each gate-B failure (11 cases) and each gate-A failure (2 cases) records INVALID and **never
  invokes target 2**;
- SNAPSHOT reports both restored and not-restored correctly, and REFUSE covers every other state;
- statically, the harness has no authority-mutating, broker-acquiring, adapter, `sys.path` or
  `exec` code, and its single write site is write-once.

A mutation check (disabling the modal gate, the lease gate, the Continue G2 check, or ARM's
plan-record check) makes the suite fail.

## 10. Addendum S3_ADD — fresh Clothing Fit committing under G2

**Status: prepared, not run.**
- **Why:** the main campaign (`S3`, 2026-10-06) is accepted as **CORE PASS**. The G1→G2
  interruption and target-1 Undo are proven.
- **What C13 showed:** its later G2 Fit on `loinclothbra_chadfix_071` began under G2 (authorization
  and stage proof) but ended in production's expected structural skip ("has no established
  compatible Body mappings"). The P5 idle check was not taken.
- **What S3_ADD adds:** one fresh, user-initiated Fit that genuinely commits under G2, using the
  already-qualified target `assaultsuitbody1` (Session 1, and S3 target 1). Then the idle probes,
  one Undo, and exact G1 restoration.

**Scope:**
- no harness and no Scripts-menu deployment change;
- no interruption;
- the frozen Session 2 functions run unchanged, with SFM closed, **before** SFM starts.

### 10.1 Shell

Paste the frozen Session 2 §2.1 block (`SESSION2_RUNBOOK.md` at `0597927`) and this runbook's §2.2
block, then:

```powershell
$EAD = Join-Path $S3ROOT "S3_ADD"                      # write-once; a retry uses S3_ADD_R2, ...
if (Test-Path -LiteralPath $HARNESS_DST) { throw "STOP: the Session 3 harness is installed; S3_ADD runs without it. Report." }
"S3_ADD SHELL READY"
```

Records in `%PUBLIC%\Documents\CPM_Session3\S3_ADD\` (write-once): the Session 2 record set.

| Producer | Records |
|---|---|
| `S2-Prepare` | `g1_source.txt`, `baseline_inventory.json` |
| `S2-PhaseA` | `g2_source.txt`, `g2_plan_record.json`, `g2_publication_record.json`, `phase_a_stdout.json` |
| `S2-PhaseB` | `g2_activation_record.json`, `phase_b_stdout.json`, `post_switch_inventory.json` |
| `S2-Finalize` | `finalization_record.json`, `finalize_stdout.json`, `restored_inventory.json`, `restore_compare.json` |

### 10.2 Operator procedure

A **P#** means: Scripts → ChadChan3D → `CPM_Session1_Probe`, run only when no CPM action or dialog is
open.

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| D0 | Shell (SFM closed) | `S2-Prepare $EAD`, then `S2-PhaseA $EAD`, then `S2-PhaseB $EAD` | `S2 BASELINE OK`, `S2 PHASE A OK`, `S2 G2 ACTIVE OK`. Start SFM **only** after `S2 G2 ACTIVE OK`. Any STOP: §10.3. |
| D1 | SFM | Start SFM fresh; open the Krystal scene (§3). **P1.** | — |
| D2 | CPM | Open CPM (Scripts → ChadChan3D → SFM_Character_Preset_Manager); choose **krystal20201**; wait for the Body / Expression / Review counts. | Counts appear. |
| D3 | SFM | **P2** (expected: G2 scope, idle authority). | — |
| D4 | CPM | Clothing Fit tab: check **only assaultsuitbody1** → **Fit Selected to Model**. | The Fit completes. Status: **"1 item updated."** No "Clothing Fit stopped" dialog, no warning dialog, no error. **STOP → §10.3 R-ADD-2** on a stop dialog, an error, or a status reporting failed / not attempted. A "skipped" status is not a product failure: stop and report for adjudication (R-ADD-2), and do not continue. |
| D5 | SFM | **P3.** | — |
| D6 | SFM | **Edit → Undo** exactly once. Confirm visually that `assaultsuitbody1` returned to its pre-Fit state. | — |
| D7 | SFM | **P4.** | — |
| D8 | CPM/SFM | Close CPM with ✕. Close SFM **without saving**. | — |
| D9 | Shell | `S2-Finalize $EAD` | `S2 RESTORED EXACT G1`. Otherwise §10.3 R-ADD-3. |

### 10.3 Recovery (fail-closed)

| Case | Signal | Action |
|---|---|---|
| R-ADD-1 | `S2-Prepare` STOP | Nothing changed. Report. |
| R-ADD-1b | `S2-PhaseA` / `S2-PhaseB` STOP | Do not start SFM. Run the recovery the shell printed (`S2-VerifyUntouched $EAD` if Phase A failed before its plan record; otherwise `S2-Finalize $EAD`). Require exact G1. Report. |
| R-ADD-2 | Any D2–D7 failure (no counts, stop dialog, error, unexpected skip) | Click nothing further in CPM. Close or terminate SFM without saving. `S2-Finalize $EAD`; require exact G1. Preserve evidence; report. |
| R-ADD-3 | `S2-Finalize` not exact | Do not start SFM. Do not edit the Master or authority folder by hand. Preserve evidence; report. |

### 10.4 Adjudication (from the CPM log, probes and `S3_ADD` records)

**PASS requires all of:**
1. **Exact G2 before SFM:** the activation record shows `success`, G1 → `54413b6c…`; the
   post-switch inventory is exact G2; the SFM process's first CPM log line comes after the
   activation `wall_time`.
2. **G2 scope at P2:** `PROD_PROVIDER_HEALTH … sha256=u'54413b6c…'` for `krystal20201`. P2 shows
   scope `54413b6ca618`, and 0 leases, 0 unreleased and 0 open providers.
3. **G2 authorization:** `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=54413b6c…`,
   then `CLOTHING_FIT_START` selecting exactly `assaultsuitbody1`.
4. **G2 stage:** `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=54413b6c…`.
5. **Native commit:** `PROD_OPERATION_PHASE … phase=u'native-commit'` for `assaultsuitbody1`.
6. **Committed-verified:** `CLOTHING_FIT_STAGE=PASS … index=0 … phase=u'committed-verified'
   mappings=26 warnings=7 committed=True`.
7. **Released:** `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`.
8. **Result:** `CLOTHING_FIT_RESULT=PASS … changed=1 … partial=1 partial_changed=1 … skipped=0
   failed=0 unattempted=0`. The status is "1 item updated."
9. **Idle authority:** P2, P3 and P4 all show 0 leases, 0 unreleased and 0 open providers; one
   window and one watcher.
10. **Undo:** D6 visual confirmation (one Undo).
11. **Exact G1 restoration:** `finalization_record` and `restore_compare` both report
    `exact_match: true`; `restored_inventory` shows Master `ac45e5c1…`.

**FAIL (product finding):** any G1 authorization or stage; no native commit; a verification other
than `committed-verified`; a release not ok; a result with failed or unattempted targets; a non-zero
lease or provider at P2–P4; non-exact restoration.

**Session 3 is a full PASS** when S3 (CORE PASS) and S3_ADD (PASS) both hold.
