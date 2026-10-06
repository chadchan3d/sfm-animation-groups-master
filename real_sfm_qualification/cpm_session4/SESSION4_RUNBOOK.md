# CPM real-SFM Session 4 — forced rollback-verification qualification (runbook)

**Status: prepared, not run.** Session 4 closes handoff §22 blockers 4 and 5: it deliberately
qualifies rollback-verification failure for Body Apply and for Clothing Fit.

Two campaigns, each in its own fresh SFM process, under exact production G1 throughout:

| Campaign | Scenario 1 — CONTROL | Scenario 2 — GATE | Then |
|---|---|---|---|
| **S4A** (Body Apply) | forced precommit failure → authentic Abort → authentic rollback verification **True** → "not applied" | same failure → authentic Abort → authentic verifier returns True, the harness substitutes **False** → production's own `ProdRecoveryUnverifiedError` | ordinary Apply is committed-verified |
| **S4F** (Clothing Fit) | forced precommit write-verification failure → authentic Abort → authentic structural verification **True** → `not-committed` | same → verifier True, substituted **False** → production's own `abort-unverified` accounting | ordinary Fit commits; operator Undo restores it |

Out of scope: postcommit Apply and post-stage Fit verification failure (the separate
committed-unverified branch); a live Expression Apply campaign (Expression shares `prod_apply`
and is covered offline, §9). No product, launcher, Normalizer, adapter/projection, shared
authority, Master, sidecar or preset-format changes. Record actual results only, in
`SESSION4_EVIDENCE.md`, at closeout.

## 0. Design

**Why rollback happens only before commit (source, app `9a78fc96…`).**
- `prod_apply` and `prod_apply_match` open a native Undo (`StartUndo`), write, run a **precommit**
  predicate (`p03_verify_saved_values` / `matches_value` readback), then `FinishUndo`.
- An exception while the Undo is open calls `prod_abort_apply_and_verify` /
  `prod_abort_fit_and_verify`: `AbortUndoableOperation`, then the **rollback verifier**
  (`prod_verify_apply_abort_baseline` / `p03_target_matches_baseline`). Verified → the original
  error is re-raised; not verified → `ProdRecoveryUnverifiedError`.
- After `FinishUndo` there is no rollback: postcommit failure is committed-unverified (out of
  scope).

**The hook.** `CPM_S4_Rollback_Harness.py` (qualification-only, SHA-256 in §2) is deployed
temporarily to the ChadChan3D Scripts menu and removed with an exact deployment comparison. No
window or class seam exists inside the open Undo, so ARM temporarily rebinds names in the private
module `chadchan3d_cpm_app` (owner-approved):

| Name | Role | Fires only when |
|---|---|---|
| `p03_verify_saved_values` (S4A) / `matches_value` (S4F) | precommit injection | caller frame is `prod_apply` / `prod_apply_match`, caller local `opened is True`, and the armed preset `BodyTest` (Body kind, `mia1`) / armed target `assaultsuitbody1` under a stage opened at Gfit = G1 |
| `prod_verify_apply_abort_baseline` (S4A) / `p03_target_matches_baseline` (S4F) | rollback verifier | caller frame is `prod_abort_apply_and_verify` / `prod_abort_fit_and_verify`, after the injection |
| `prod_cpm_open_adapter` | pass-through call counter | always (counts) |
| `prod_cpm_open_fit_stage` (S4F) | pass-through; wraps the armed stage's `release` with a counter | index 0, target `assaultsuitbody1`, stage generation G1 |

**Wrapper discipline.**
- ARM refuses unless the private app build is exactly `9a78fc96…` and every one of ten pinned
  functions (the wrapped names and their production callers) is the module's own function at its
  pinned definition line; it also refuses on a busy or closing CPM, an open modal, the wrong model,
  a non-G1 scope or live Master, or non-zero leases / unreleased / open providers.
- The injection restores its own binding, calls the **real** predicate first and records its
  result (it must be True: the writes really happened), then returns False. Production raises its
  own precommit error, runs its own Abort and its own verifier.
- The verifier wrapper restores its binding, calls the **real** verifier first, records the result
  (expected True), the adapter calls during verification, broker counters and the Undo state, then
  restores **every** binding and returns the real result (CONTROL) or False (GATE).
- Restoration also happens on a real-function exception, on ARM failure, on STATE and on any
  INVALID path. STATE proves no wrapper remains installed.
- The harness writes only its own write-once JSON records. It never writes production log lines,
  authority files or product files, and never acquires authority.

**State-driven menu clicks** (`%PUBLIC%\Documents\CPM_Session4\ACTIVE_CAMPAIGN.txt` names the
campaign; the leaf `S4A…` / `S4F…` selects the gate):

| Campaign state | Mode | Visible notice |
|---|---|---|
| no `s1_arm.json` | ARM scenario 1 | `S4 ARMED: … CONTROL (scenario 1)` |
| `s1_arm`, no `s1_state` | STATE 1 | `S4 RECORDED OK: … CONTROL` |
| `s1_state` RECORDED_OK, no `s2_arm` | ARM scenario 2 | `S4 ARMED: … GATE (scenario 2)` |
| `s2_arm`, no `s2_state` | STATE 2 | `S4 RECORDED OK: … GATE` |
| anything else | REFUSE | `S4 HARNESS REFUSED: …` |

STATE can also show `S4 INVALID: …` or `S4 CHECK FAILED: …` (→ §6 R-S4-2). The notice is a
non-modal harness box; close it with its **OK** (this is not a CPM dialog).

STATE computes harness-side checks from its own records and the live window (production status
copy, Fit accounting, release count, counters, Undo count/description, scene values versus ARM,
wrappers absent). Final adjudication is from the CPM log, probes and records (§7).

**Fit release observation (record, do not fix).** In `fit_stage`'s exception path the stage is
released by a bare `stage_authority.release()` (no `PROD_CPM_FIT_STAGE_RELEASED` line; the result
is discarded). On the success path, a raising `prod_cpm_release_fit_stage` could in theory be
followed by a second `release()` in the exception handler. S4F counts the actual `release()` calls
on the injected target's stage (`stage_released_exactly_once`). No production change unless live
evidence shows a defect.

## 1. Rules (fail-closed)

1. **One fresh SFM process per campaign.** Do not save the SFM document. Run no Normalizer or
   other authority tool.
2. **DO NOT USE UNDO during S4A, and during S4F until step F14.** The injected operations leave
   no Undo entry; an Undo would revert an earlier, unrelated edit.
3. **Dialogs:** click **OK** only on the dialogs named in the step. Never press Enter to dismiss a
   dialog you have not read. CPM and SFM stay open unless a step says otherwise.
4. **Probes** (`P#`: Scripts → ChadChan3D → `CPM_Session1_Probe`) and harness clicks only when no
   CPM action is running and no CPM dialog is open.
5. **No reselection** of the model during a campaign.
6. **Write-once:** a campaign folder is never reused or edited; a retry uses `S4A_R2`, `S4F_R2`, …
7. **Operator role:** visible steps only. Logs and JSON are adjudicated afterwards (§7).

## 2. Shell set-up

With SFM closed, paste the **frozen Session 2 §2.1 block** from `SESSION2_RUNBOOK.md` at commit
`0597927` unchanged, filling its two placeholders (only `S2-Prepare`, `S2-VerifyUntouched` and
its helpers are used; Session 4 never switches generation). Then paste:

```powershell
# ---- CPM Session 4 shell set-up. Paste AFTER the frozen Session 2 section 2.1 block. ----
foreach ($f in "S2-Prepare","S2-VerifyUntouched","S2-Sha","S2-New","S2-Json","S2-SfmClosed") {
    if (-not (Get-Command $f -ErrorAction SilentlyContinue)) { throw "STOP: paste the frozen Session 2 section 2.1 block first ($f missing)." }
}
$S4ROOT      = Join-Path $env:PUBLIC "Documents\CPM_Session4"
$EA          = Join-Path $S4ROOT "S4A"                 # retries: S4A_R2, ... (never reuse)
$EF          = Join-Path $S4ROOT "S4F"                 # retries: S4F_R2, ...
$SCRIPTS     = Join-Path $GAME "usermod\scripts"
$MENU        = Join-Path $SCRIPTS "sfm\mainmenu\ChadChan3D"
$APP_DST     = Join-Path $SCRIPTS "ChadChan3D_CPM\SFM_Character_Preset_Manager.py"
$APP_SHA     = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
$HARNESS_SRC = Join-Path $R "real_sfm_qualification\cpm_session4\CPM_S4_Rollback_Harness.py"
$HARNESS_DST = Join-Path $MENU "CPM_S4_Rollback_Harness.py"
$HARNESS_SHA = "45c44f3defd89559e53b4e592f7abd9f45d3da9f72028de8da0322749f140fc8"
$UTF8 = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path -LiteralPath $S4ROOT)) { New-Item -ItemType Directory -Path $S4ROOT | Out-Null }

# Deterministic Scripts-menu inventory: every file under usermod\scripts, relative path + SHA-256, ordinal sort.
function S4-ScriptsInventory([string]$Out) {
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
function S4-DeployBaseline([string]$E) {
    S2-SfmClosed
    if (-not (Test-Path -LiteralPath (Join-Path $E "baseline_inventory.json"))) { throw "STOP: run S2-Prepare first." }
    if (Test-Path -LiteralPath $HARNESS_DST) { throw "STOP: a harness file is already installed (residue). Report." }
    if ((S2-Sha $APP_DST) -ne $APP_SHA) { throw "STOP: the deployed private CPM app is not 9a78fc96... Report." }
    S4-ScriptsInventory (Join-Path $E "deploy_before_harness.txt")
}

# Temporary harness deployment (exact bytes, pinned SHA-256).
function S4-DeployHarness([string]$E) {
    S2-SfmClosed
    $rec = Join-Path $E "harness_deploy_record.json"; S2-New $rec; S2-New $HARNESS_DST
    if (-not (Test-Path -LiteralPath (Join-Path $E "deploy_before_harness.txt"))) { throw "STOP: run S4-DeployBaseline first." }
    if ((S2-Sha $HARNESS_SRC) -ne $HARNESS_SHA) { throw "STOP: repository harness is not the pinned SHA-256." }
    Copy-Item -LiteralPath $HARNESS_SRC -Destination $HARNESS_DST
    $got = S2-Sha $HARNESS_DST
    if ($got -ne $HARNESS_SHA) { Remove-Item -LiteralPath $HARNESS_DST; throw "STOP: installed harness SHA mismatch; removed." }
    [System.IO.File]::WriteAllText($rec, ('{"harness_sha256": "' + $got + '", "installed_relative": "sfm/mainmenu/ChadChan3D/CPM_S4_Rollback_Harness.py", "wall_time": "' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '"}'), $UTF8)
    "S4 HARNESS DEPLOYED: sha256=$got"
}

# Point the harness at this campaign folder (leaf S4A... = Apply, S4F... = Fit).
function S4-Activate([string]$E) {
    if (-not (Test-Path -LiteralPath (Join-Path $E "harness_deploy_record.json"))) { throw "STOP: run S4-DeployHarness first." }
    [System.IO.File]::WriteAllText((Join-Path $S4ROOT "ACTIVE_CAMPAIGN.txt"), (Split-Path $E -Leaf), $UTF8)
    "S4 CAMPAIGN ACTIVE: $(Split-Path $E -Leaf)"
}

# Closeout (SFM closed): remove the harness, require the exact pre-harness Scripts deployment,
# then require the authority to be exactly the S2-Prepare G1 baseline.
function S4-Close([string]$E) {
    S2-SfmClosed
    if (Test-Path -LiteralPath $HARNESS_DST) {
        if ((S2-Sha $HARNESS_DST) -ne $HARNESS_SHA) { throw "STOP: installed harness is not the pinned file; do not delete. Report." }
        Remove-Item -LiteralPath $HARNESS_DST
    }
    $pointer = Join-Path $S4ROOT "ACTIVE_CAMPAIGN.txt"
    if (Test-Path -LiteralPath $pointer) { Remove-Item -LiteralPath $pointer }
    $before = Join-Path $E "deploy_before_harness.txt"; $after = Join-Path $E "deploy_after_removal.txt"
    S4-ScriptsInventory $after | Out-Null
    if ((S2-Sha $before) -ne (S2-Sha $after)) {
        Compare-Object (Get-Content -LiteralPath $before) (Get-Content -LiteralPath $after) | Format-Table -AutoSize | Out-String -Width 400
        throw "STOP: Scripts deployment differs from the pre-harness baseline. Report."
    }
    "S4 DEPLOYMENT RESTORED EXACT: no harness residue."
    S2-VerifyUntouched $E
}
"S4 SHELL READY"
```

`S2-VerifyUntouched` prints its frozen Session 2 wording, `S2 UNTOUCHED: exact production G1, no
finalization needed. Session 2 stops here; report.` — for Session 4 this line is the expected
**success** result (authority untouched; nothing to finalize).

## 3. Fixtures

| Campaign | Scene | Model | Used |
|---|---|---|---|
| S4A | the R15 addendum scene (Mia on `shot3`), as in Session 2 | `mia1` (`models/annoad/foxbase/mia/mia.mdl`, 1153028609) | Body presets **`Body`** and **`BodyTest`** |
| S4F | the Session 1/3 Krystal scene (`SESSION3_RUNBOOK.md` §3) | source `krystal20201`; target 1 `assaultsuitbody1`; target 2 `loinclothbra_chadfix_071` | Fit order: `assaultsuitbody1` first |

## 4. Campaign records (`%PUBLIC%\Documents\CPM_Session4\<campaign>\`, write-once)

| Producer | Records |
|---|---|
| `S2-Prepare` | `g1_source.txt`, `baseline_inventory.json` |
| `S4-DeployBaseline` | `deploy_before_harness.txt` |
| `S4-DeployHarness` | `harness_deploy_record.json` |
| Harness ARM (×2) | `s1_arm.json`, `s2_arm.json` (preconditions, pins, Undo state, scene values) |
| Rollback-verifier wrapper (×2) | `s1_fire.json`, `s2_fire.json` (injection facts, real predicate result, real verifier result, substitution, adapter calls during verification, counters) |
| Harness STATE (×2) | `s1_state.json`, `s2_state.json` (status, checks, accounting, releases, wrappers absent) |
| `S4-Close` | `deploy_after_removal.txt`, `untouched_inventory.json`, `untouched_compare.json` |

`ACTIVE_CAMPAIGN.txt` is the harness pointer, not evidence; `S4-Close` removes it.

## 5. Operator procedure

### 5.1 S4A — Body Apply

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| A0 | Shell (SFM closed) | `S2-Prepare $EA`, `S4-DeployBaseline $EA`, `S4-DeployHarness $EA`, `S4-Activate $EA` | `S2 BASELINE OK`, `SCRIPTS INVENTORY WRITTEN`, `S4 HARNESS DEPLOYED`, `S4 CAMPAIGN ACTIVE: S4A`. Any STOP → R-S4-1. |
| A1 | SFM | Start SFM fresh; open the S4A fixture scene (§3). **P1.** | — |
| A2 | CPM | Scripts → ChadChan3D → SFM_Character_Preset_Manager. Choose **Mia**; wait for the Body / Expression / Review counts. | Counts appear. |
| A3 | CPM | Body tab: select **`Body`** → **Apply Preset** (ordinary Apply). | Status **"Body Preset applied."** (or "Already matches this preset."); no dialog. Otherwise → R-S4-2. |
| A4 | SFM | **P2.** | — |
| A5 | CPM | Body tab: select **`BodyTest`**. **Do not apply yet.** | The status reads **"Ready to apply "BodyTest"."** |
| A6 | SFM | Scripts → ChadChan3D → **CPM_S4_Rollback_Harness**. | Notice **`S4 ARMED: Apply CONTROL (scenario 1)`**. Close the notice with its **OK**. `S4 HARNESS REFUSED` → R-S4-2. |
| A7 | CPM | Click **Apply Preset** (`BodyTest` selected). | A dialog titled **"Can't apply preset"**: *"Preset could not be applied safely. This preset was not applied."* **Click OK.** CPM and SFM stay open. **DO NOT USE UNDO.** Any other dialog, or a success status → R-S4-2. |
| A8 | SFM | Harness again. | **`S4 RECORDED OK: Apply CONTROL (scenario 1)`**. Close the notice (**OK**). `S4 INVALID` / `S4 CHECK FAILED` / `REFUSED` → R-S4-2. |
| A9 | SFM | **P3.** | — |
| A10 | SFM | Harness again. | **`S4 ARMED: Apply GATE (scenario 2)`**. Close the notice (**OK**). |
| A11 | CPM | If `BodyTest` is no longer selected, select it. Click **Apply Preset**. | A dialog titled **"Recovery could not be verified"**: *"Preset Apply failed and recovery could not be verified. Inspect the model before retrying; use SFM Undo if an Apply entry is present."* **Click OK.** CPM and SFM stay open. **DO NOT USE UNDO** — there is no Apply entry (the harness records the Undo count); an Undo now would revert step A3. Any other dialog, or a success status → R-S4-2. |
| A12 | SFM | Harness again. | **`S4 RECORDED OK: Apply GATE (scenario 2)`**. Close the notice (**OK**). Otherwise → R-S4-2. |
| A13 | SFM | **P4.** | — |
| A14 | CPM | With `BodyTest` selected, click **Apply Preset** (ordinary follow-up). | Status **"Body Preset applied."**; no dialog. **Do not Undo.** Otherwise → R-S4-2. |
| A15 | SFM | **P5.** | — |
| A16 | CPM/SFM | Close CPM with ✕. Close SFM **without saving**. | — |
| A17 | Shell | `S4-Close $EA` | `S4 DEPLOYMENT RESTORED EXACT`, then `S2 UNTOUCHED: exact production G1 …`. Otherwise → R-S4-3. |

### 5.2 S4F — Clothing Fit

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| F0 | Shell (SFM closed) | `S2-Prepare $EF`, `S4-DeployBaseline $EF`, `S4-DeployHarness $EF`, `S4-Activate $EF` | `S2 BASELINE OK`, `SCRIPTS INVENTORY WRITTEN`, `S4 HARNESS DEPLOYED`, `S4 CAMPAIGN ACTIVE: S4F`. Any STOP → R-S4-1. |
| F1 | SFM | Start SFM fresh; open the Krystal scene (§3). **P1.** | — |
| F2 | CPM | Open CPM; choose **krystal20201**; wait for the counts. | Counts appear. |
| F3 | SFM | **P2.** | — |
| F4 | SFM | Harness. | **`S4 ARMED: Clothing Fit CONTROL (scenario 1)`**. Close the notice (**OK**). `REFUSED` → R-S4-2. |
| F5 | CPM | Clothing Fit tab: check **assaultsuitbody1** and **loinclothbra_chadfix_071** (nothing else) → **Fit Selected to Model**. | **No dialog.** Status **"Clothing Fit could not finish. Nothing changed."** CPM and SFM stay open. **DO NOT USE UNDO.** A dialog, or "items updated" → R-S4-2. |
| F6 | SFM | Harness again. | **`S4 RECORDED OK: Clothing Fit CONTROL (scenario 1)`**. Close the notice (**OK**). Otherwise → R-S4-2. |
| F7 | SFM | **P3.** | — |
| F8 | SFM | Harness again. | **`S4 ARMED: Clothing Fit GATE (scenario 2)`**. Close the notice (**OK**). |
| F9 | CPM | Check **assaultsuitbody1** and **loinclothbra_chadfix_071** again → **Fit Selected to Model**. | A dialog titled **"Clothing Fit stopped"**: *"Clothing Fit stopped before a completed target change."*, **Recovery could not be verified** – assaultsuitbody1, **Not attempted** – loinclothbra_chadfix_071, and the note to inspect the target and use an Undo entry only if one exists. **Click OK.** Status **"Clothing Fit stopped. Recovery of the failed target could not be verified."** CPM and SFM stay open. **DO NOT USE UNDO** — the harness records that no Fit entry exists. Any other dialog or status → R-S4-2. |
| F10 | SFM | Harness again. | **`S4 RECORDED OK: Clothing Fit GATE (scenario 2)`**. Close the notice (**OK**). Otherwise → R-S4-2. |
| F11 | SFM | **P4.** | — |
| F12 | CPM | Check **only assaultsuitbody1** → **Fit Selected to Model** (ordinary follow-up). | Status **"1 item updated."**; no dialog. Otherwise → R-S4-2. |
| F13 | SFM | **P5.** | — |
| F14 | SFM | **Edit → Undo exactly once** (the only Undo in Session 4). Confirm visually that `assaultsuitbody1` returned to its pre-Fit look. | — |
| F15 | SFM | **P6.** | — |
| F16 | CPM/SFM | Close CPM with ✕. Close SFM **without saving**. | — |
| F17 | Shell | `S4-Close $EF` | `S4 DEPLOYMENT RESTORED EXACT`, then `S2 UNTOUCHED: exact production G1 …`. Otherwise → R-S4-3. |

## 6. Recovery (fail-closed)

| Case | Signal | Action |
|---|---|---|
| R-S4-1 | A shell STOP at A0 / F0 | Do not start SFM. If `S2-Prepare` passed, run `S4-Close <campaign>` (removes any harness and proves G1 untouched). Report. |
| R-S4-2 | Any harness `REFUSED` / `INVALID` / `CHECK FAILED`, any unexpected dialog, status or error, or a crash | Click **OK** on any open dialog. **DO NOT USE UNDO.** Take no further CPM or harness action. Close CPM (✕) and close SFM **without saving** (terminate it if it does not respond). Run `S4-Close <campaign>`. Preserve the campaign folder; report. A retry uses a new folder (`S4A_R2` / `S4F_R2`) only after adjudication. |
| R-S4-3 | `S4-Close` STOP (deployment differs, or authority differs from the G1 baseline) | Do not start SFM. Do not edit the Master, authority folder or Scripts folder by hand. Preserve evidence; report. |

Nothing in Session 4 writes authority. Unsaved scene changes are discarded when SFM closes
without saving.

## 7. Adjudication (after each campaign; CPM log, probes, campaign records)

**INVALID run** (restore, then repeat in a new folder): the injection did not fire, or fired for
the wrong preset/target; the real precommit predicate was not True; the real verifier raised or
returned False (CONTROL then proves nothing); any harness error; CPM interaction outside the
procedure; or the operator used Undo during an injected scenario.

### 7.1 S4A PASS requires all of

1. **G1 authorization:** each injected Apply logs `PROD_CPM_OPERATION_AUTHORIZED operation=u'Apply
   Preset' sha256=ac45e5c1…`; the fire record's `authority_master_sha256` is G1.
2. **Native writes, predicate after writes:** `changed_sides` > 0 and the fire record's injection
   shows `caller_opened: true` and real predicate `true`.
3. **CONTROL (scenario 1):**
   - production logs `PROD_APPLY_ABORT_VERIFY restored=True` with the precommit error;
   - fire record `real_result: true`, `substituted: false`;
   - `PROD_ACTION_ERROR label='Apply Body Preset'`, "Can't apply preset", status "Preset could not
     be applied safely. This preset was not applied.";
   - Undo count and description equal ARM; `mia1` values equal ARM.
4. **GATE (scenario 2):**
   - fire record `real_result: true` (authentic verifier True), `substituted: true`;
   - production logs `PROD_APPLY_ABORT_VERIFY restored=False` and raises
     `ProdRecoveryUnverifiedError`; dialog "Recovery could not be verified";
   - Undo count and description equal ARM; `mia1` values equal ARM.
5. **No false success:** no `PROD_APPLY outcome='committed'` and no `native-commit` phase for either
   injected Apply.
6. **No reacquisition in rollback verification:** `adapter_calls_during_verification` 0 in both
   fire records; broker `total_provider_opens` unchanged across verification.
7. **Idle authority:** both state records and P2–P5 show 0 leases, 0 unreleased, 0 open providers,
   one window, one watcher; both state records `wrappers_absent: true`, status RECORDED_OK.
8. **Usable afterwards:** A14 logs `PROD_APPLY outcome='committed'` for `BodyTest`.
9. **Restoration:** `deploy_after_removal.txt` = `deploy_before_harness.txt`; `untouched_compare`
   exact (G1 throughout).

### 7.2 S4F PASS requires all of

1. **Gfit = G1:** `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=ac45e5c1…`;
   `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=ac45e5c1…` with the target vocabulary (`literals=` count).
2. **Native target-1 writes, predicate inside the open Undo:** injection `caller_opened: true`,
   `changed_sides` > 0, real predicate `true`.
3. **CONTROL:** `PROD_CLOTHING_FIT_ABORT_VERIFY target=… restored=True`; fire `real_result: true`,
   `substituted: false`; `CLOTHING_FIT_FAIL … index=0 … committed_current=False`; state shows
   `fit_failed` = [assaultsuitbody1, `committed: false`, `verification: not-committed`]; status
   "Clothing Fit could not finish. Nothing changed."; no dialog.
4. **GATE:** fire `real_result: true`, `substituted: true`; `PROD_CLOTHING_FIT_ABORT_VERIFY …
   restored=False`; `fit_failed` verification `abort-unverified`; `G18AN_FIT_FAILURE_DIALOG
   verified_changed=[] committed_uncertain=[] recovery_unverified=[u'assaultsuitbody1']
   unattempted=[u'loinclothbra_chadfix_071'] undo_count=0`.
5. **Lease through recovery:** fire `entry_counters.outstanding_leases == 1` (stage held during
   rollback verification) and `entry_releases == 0`; `adapter_calls_during_verification == 0`.
6. **Released exactly once:** each state record shows exactly one `release()` on the armed stage,
   result `None` (ok); then 0 leases / 0 unreleased / 0 open providers.
7. **Target 2 never staged or mutated:** no `PROD_CPM_FIT_STAGE_OPEN index=1`; target 2 in
   `fit_unattempted` only; target-2 values equal ARM.
8. **Nothing committed:** `fit_committed_order` empty; Undo count/description equal ARM.
9. **Idle authority:** P2–P6 0/0/0, one window, one watcher; state records RECORDED_OK,
   `wrappers_absent: true`.
10. **Usable afterwards:** F12 logs `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=ac45e5c1…`,
    `CLOTHING_FIT_STAGE=PASS … committed=True`, `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`,
    `CLOTHING_FIT_RESULT=PASS … failed=0 unattempted=0`; F14 visual Undo.
11. **Restoration:** deployment exact; `untouched_compare` exact.

**FAIL (product finding):** a false success or committed result for an injected operation; the
real rollback verifier False after a real Abort in CONTROL (state not restored); wrong accounting;
target 2 staged or mutated; an adapter call during rollback verification; a stage lease not held
during Fit rollback verification, released twice, or left outstanding; an Undo entry left by an
injected operation; the ordinary follow-up unusable.

**Session 4 is PASS** when S4A and S4F both pass.

## 8. Return

After each campaign, return `S4-Close` output and the campaign folder; the CPM log and probe JSONL
are read from `%PUBLIC%\Documents` at adjudication.

## 9. Offline qualification

`test_cpm_s4_rollback_harness.py` runs the actual harness against the actual R15 launcher and
private app (real `ProdWindow`) in the R15 suite's fake game root, under embedded Python 2.7.5 with
real PySide/Qt 4.8 and the Qt 4.8 model, and under Python 3.10 with the model.

- **Production exercised unmodified:** `apply_kind`/`guard`, `prod_apply`, both abort helpers, both
  rollback verifiers, `prod_live_bindings_for_cached_scope`, `p03_verify_saved_values`,
  `matches_value`, `binding_snapshot`, `prod_cpm_authorize_operation`, `prod_cpm_open_fit_stage`,
  `fit_stage` and its accounting and failure dialog.
- **Stubbed (scene/adapter boundary only):** `side_snapshot`, `dme_id`, `write_side`, `dm()`
  (Abort restores the pre-Undo snapshot), model/target resolution, `g11a_safe_plan`, the fake
  adapter module and broker, preset selection; under 3.10 only, the two perf-diagnostic loggers
  (the app targets 2.7).
- **Covered:** exact pins (app SHA and ten def lines); ARM refusal matrix; control and gate for
  Apply and Fit; no firing at the postcommit call (`opened` False) or from unrelated callers or an
  unarmed preset; one-shot and restoration after firing, on a real-predicate exception, and at
  STATE/INVALID; no adapter calls during rollback verification; lease held during Fit rollback
  verification; exactly one release; target 2 unattempted; ordinary follow-ups; Expression Apply's
  shared abort path (verified and unverified) without the harness; mutation tests proving the
  suite fails when either wrapper skips the real function.

```text
<embedded 2.7.5> test_cpm_s4_rollback_harness.py --phase=run   -> RESULT: 308/308 ALL PASS (real + model)
<python 3.10>    test_cpm_s4_rollback_harness.py --phase=run   -> RESULT: 166/166 ALL PASS (model)
```

Mocks cannot qualify real DME Undo/Abort or the real broker; those are the live campaigns.
