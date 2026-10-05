# CPM real-SFM Session 2 — controlled G1→G2 generation qualification (runbook)

**Status: S2-A_R2 prepared, not run; S2-B blocked until S2-A_R2 passes.** Session 2 proves exactly
the two handoff §21 cases:
- **S2-A:** open-window generation replacement;
- **S2-B:** a generation change during a Save prompt.

**First S2-A attempt (folder `S2A`, 2026-10-01): procedurally invalid.**
- **What happened:** selecting `BodyTest` after G2 activation re-evaluated CPM's semantic readiness.
  That detected the stale scope and rebuilt it under G2 before Apply was clicked. The Apply then
  ran under valid G2 authority.
- **Why it was not a product failure:** this was a runbook design error. The early stale-detection
  and rebuild path behaved correctly (§13): no stale mutation, the stale scope discarded, the G2
  scope rebuilt, no replay.
- **Why it does not count:** it did not qualify the stale-action rejection boundary.
- **Status of that folder:** restored to exact G1. It is preserved unchanged as evidence and must
  never be reused.

S2-A is rerun as **S2-A_R2** (§3).

It changes no CPM, launcher, Normalizer, adapter/projection, shared authority package, sidecar
reader/generator or preset format. Record actual results only, in `SESSION2_EVIDENCE.md`, at
closeout.

## 0. Mechanism and identities (reused, already real-SFM-qualified)

The G1→G2 switch and the restoration use the **unchanged Checkpoint I tooling** in
`../checkpoint_i_generation_replacement/`. That tooling closed I_PASS on 2026-09-26 with an exact
restoration. It consists of:
- `I_Generation_Helper.py inventory | compare` (read-only);
- `I_Generation_Publisher.py prepare-publish-g2 | activate-g2 | finalize` (Python 3,
  repository-side; never deployed into SFM).

Everything runs from a PowerShell window **outside SFM**, so it works while a CPM modal prompt is
open.

| Generation | Master SHA-256 | Sidecar SHA-256 | Manifest SHA-256 |
|---|---|---|---|
| G1 — production, current live state | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | `d810d6486305a098d4855eea15f6feea3dc7fe7f7aaf97a08415fcac8e7701d6` |
| G2 — G1 bytes + one trailing LF | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` | `cd370f67bfd4db6a17fdc3d425ffae6934ad223c2f5519eda99e3f5b2264ffe3` | as recorded by Phase A (`manifest_sha256_after_publication`) |

- **Semantics:** G1 and G2 are semantically identical; the publisher proves parity before
  publishing. Only the generation identity changes.
- **Publication:** G2 is published by the real, accepted compiler/publisher, so the Master/sidecar
  source-generation relationship stays valid.
- **Current state:** at preparation, the live state was re-inventoried read-only and is
  byte-identical to Checkpoint I's restored baseline.

**Why this is the production boundary:**
- Phase A publishes G2's sidecar and manifest through the real publisher.
- Phase B atomically replaces the live Master the broker observes (`MoveFileExW`, hash-gated).
- CPM's next semantic action calls `prod_cpm_authorize_operation`, which reaches
  `verify_current_generation`, which reaches `broker.acquire_or_reuse_views(…,
  expected_generation=<scope SHA>)`. The broker re-observes the Master on every acquisition
  (handoff §13).
- Nothing is stubbed, bypassed or modified.

**Restoration:** `finalize` (with SFM closed) restores the exact G1 Master, republishes G1 and
removes only the exact recorded G2 sidecar. It requires the final inventory to equal the campaign
baseline exactly. No sidecar is regenerated except G2's own publication and G1's republication by
this qualified tooling.

## 1. Global rules (fail-closed)

1. **Two campaigns, in order, each in a fresh SFM process:** S2-A_R2, then S2-B. Each starts from,
   and must end restored to, exact production G1.
2. **S2-B is blocked until S2-A_R2 passes.** That requires both:
   - S2-A_R2's `S2-Finalize` printed `S2 RESTORED EXACT G1`;
   - S2-A_R2 was adjudicated PASS (§6).

   The original `S2A` folder is preserved evidence of the invalid first attempt; never pass it to
   any function.
3. **Never end Session 2 with anything other than exact G1.** If any restoration is not exact, STOP:
   do not start SFM again and report.
4. **Write-once evidence:** every record and output has its own path per campaign (§2.2). The helper
   functions refuse to overwrite. Never reuse, edit or delete a campaign folder.
5. **During Session 2:**
   - do not save the SFM document;
   - run no Normalizer or other authority tool;
   - do not reselect the model after a stale-scope warning. The warning text says "Reselect the
     model", but CPM rebuilds the scope itself, and a manual reselection would confound the rebuild
     evidence.
6. **Phase A and Phase B run back to back**, with no SFM interaction between them. After Phase A
   the manifest already names G2 while the Master is still G1, so a CPM action in that window
   would be an authority-unavailable refusal, not a generation change.
7. **Use the frozen functions verbatim.** Preparation, Phase A, Phase B and finalization must run
   only through `S2-Prepare`, `S2-PhaseA`, `S2-PhaseB` and `S2-Finalize` exactly as defined in §2.1
   (and `S2-VerifyUntouched` for R1). Do not substitute shortened or manual command blocks. Each
   campaign must produce its full record set (§2.2), including `post_switch_inventory.json`,
   `restored_inventory.json` and `restore_compare.json`. A campaign missing any of them is
   incomplete.
8. **Operator role:** follow the visible steps only. Probe JSON and the CPM log are adjudicated after
   each campaign, never while SFM is being manipulated (§6). The shell functions print one
   `S2 … OK` or `STOP: …` line per step. On any `STOP` line, follow the text it prints and §5.

## 2. Shell set-up and exact commands

### 2.1 Set-up (Windows PowerShell 5.1)

Paste this whole block once into a PowerShell window, with SFM closed. Fill in the two
placeholders first.

```powershell
# ---- CPM Session 2 shell set-up. Fill the two placeholders, then paste the whole block. ----
$R    = "<repository root>"
$GAME = "<SFM game>"            # the folder containing sfm.exe
$CFG  = Join-Path $GAME "usermod\cfg"
$M    = Join-Path $CFG "sfm_defaultanimationgroups.txt"
$AUTH = Join-Path $CFG "sfm_shared_authority"
$I    = Join-Path $R "real_sfm_qualification\checkpoint_i_generation_replacement"
$LIB  = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "SFM Character Preset Manager\Characters\mia--2e6533ed1490"
$EA2  = Join-Path $env:PUBLIC "Documents\CPM_Session2\S2A_R2"   # S2-A rerun (the original S2A folder is preserved; never reused)
$EB   = Join-Path $env:PUBLIC "Documents\CPM_Session2\S2B"
$G1_MASTER   = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
$G2_MASTER   = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
$G1_SIDECAR  = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
$G2_SIDECAR  = "cd370f67bfd4db6a17fdc3d425ffae6934ad223c2f5519eda99e3f5b2264ffe3"
$G1_MANIFEST = "d810d6486305a098d4855eea15f6feea3dc7fe7f7aaf97a08415fcac8e7701d6"
$env:PYTHONDONTWRITEBYTECODE = "1"

function S2-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
function S2-Sha([string]$Path) {   # .NET SHA-256 (no dependency on Get-FileHash/module paths)
    $sha = [System.Security.Cryptography.SHA256]::Create(); $fs = [System.IO.File]::OpenRead($Path)
    try { -join ($sha.ComputeHash($fs) | ForEach-Object { $_.ToString("x2") }) } finally { $fs.Dispose(); $sha.Dispose() }
}
function S2-New([string]$Path) { if (Test-Path -LiteralPath $Path) { throw "STOP: $Path already exists (write-once)." } }
function S2-Py { & python @args; if ($LASTEXITCODE -ne 0) { throw "STOP: python exited with code $LASTEXITCODE." } }
function S2-SfmClosed { if (Get-Process -Name sfm -ErrorAction SilentlyContinue) { throw "STOP: close SFM first." } }
function S2-SidecarSet($Inv) { (@($Inv.sidecars | ForEach-Object { $_.sha256.ToLowerInvariant() }) | Sort-Object) -join "," }
function S2-Inventory([string]$E, [string]$Name) {
    $out = Join-Path $E $Name; S2-New $out
    S2-Py (Join-Path $I "I_Generation_Helper.py") inventory --master $M --authority-dir $AUTH --out $out | Out-Null
    S2-Json $out
}
function S2-Compare([string]$E, [string]$Current, [string]$Name) {
    $out = Join-Path $E $Name; S2-New $out
    S2-Py (Join-Path $I "I_Generation_Helper.py") compare --baseline (Join-Path $E "baseline_inventory.json") `
        --current (Join-Path $E $Current) --out $out | Out-Null
    (S2-Json $out).exact_match -eq $true
}

# Baseline: new campaign folder, byte copy of live G1, baseline inventory.
function S2-Prepare([string]$E) {
    S2-SfmClosed; S2-New $E
    New-Item -ItemType Directory -Path $E | Out-Null
    Copy-Item -LiteralPath $M -Destination (Join-Path $E "g1_source.txt")
    if ((S2-Sha (Join-Path $E "g1_source.txt")) -ne $G1_MASTER) { throw "STOP: the live Master is not production G1. Do not continue." }
    $b = S2-Inventory $E "baseline_inventory.json"
    if ($b.master_sha256 -ne $G1_MASTER -or $b.manifest_sha256 -ne $G1_MANIFEST -or (S2-SidecarSet $b) -ne $G1_SIDECAR) {
        throw "STOP: the baseline is not exact production G1 (Master/manifest/single sidecar). Do not continue."
    }
    "S2 BASELINE OK: $E"
}

# Phase A: publish the G2 sidecar + manifest. The live Master stays G1.
function S2-PhaseA([string]$E) {
    $src = Join-Path $E "g2_source.txt"; $plan = Join-Path $E "g2_plan_record.json"
    $pub = Join-Path $E "g2_publication_record.json"; $log = Join-Path $E "phase_a_stdout.json"
    S2-New $src; S2-New $plan; S2-New $pub; S2-New $log
    try {
        S2-Py (Join-Path $I "I_Generation_Publisher.py") --repo-root $R prepare-publish-g2 `
            --g1-source (Join-Path $E "g1_source.txt") --g2-source-out $src --plan-out $plan `
            --output-dir $AUTH --record-out $pub --baseline-inventory (Join-Path $E "baseline_inventory.json") |
            Out-File -LiteralPath $log -Encoding utf8
        $p = S2-Json $pub
        if ($p.g2_source_sha256 -ne $G2_MASTER -or $p.g2_sidecar_sha256 -ne $G2_SIDECAR -or $p.manifest_source_sha256 -ne $G2_MASTER) {
            throw "the publication record does not show the exact expected G2 identities"
        }
    } catch {
        if (Test-Path -LiteralPath $plan) {
            "STOP: PHASE A FAILED AFTER ITS PLAN RECORD (authority may have changed). Do not touch CPM. Close SFM without saving, then run:  S2-Finalize `"$E`""
        } else {
            "STOP: PHASE A FAILED BEFORE ANY AUTHORITY WRITE. Do not touch CPM. Close SFM without saving, then run:  S2-VerifyUntouched `"$E`""
        }
        throw
    }
    "S2 PHASE A OK: G2 sidecar published; live Master still G1."
}

# Phase B: atomically activate the G2 Master, then prove exact G2.
function S2-PhaseB([string]$E) {
    $act = Join-Path $E "g2_activation_record.json"; $log = Join-Path $E "phase_b_stdout.json"
    S2-New $act; S2-New $log
    try {
        S2-Py (Join-Path $I "I_Generation_Publisher.py") --repo-root $R activate-g2 --master $M --authority-dir $AUTH `
            --baseline-inventory (Join-Path $E "baseline_inventory.json") `
            --publication-record (Join-Path $E "g2_publication_record.json") --out $act |
            Out-File -LiteralPath $log -Encoding utf8
        $a = S2-Json $act
        if ($a.success -ne $true -or $a.pre_activation_master_sha256 -ne $G1_MASTER -or $a.post_activation_master_sha256 -ne $G2_MASTER) {
            throw "the activation record does not prove G1 -> exact G2"
        }
        $v = S2-Inventory $E "post_switch_inventory.json"
        $p = S2-Json (Join-Path $E "g2_publication_record.json")
        $want = (@($G1_SIDECAR, $G2_SIDECAR) | Sort-Object) -join ","
        if ($v.master_sha256 -ne $G2_MASTER -or (S2-SidecarSet $v) -ne $want -or $v.manifest_sha256 -ne $p.manifest_sha256_after_publication) {
            throw "the post-switch inventory is not exact G2"
        }
    } catch {
        "STOP: EXACT G2 ACTIVATION NOT PROVEN. Do not touch or confirm anything in CPM. Close SFM without saving, then run:  S2-Finalize `"$E`""
        throw
    }
    "S2 G2 ACTIVE OK: live Master = $G2_MASTER at $(Get-Date -Format 'HH:mm:ss')"
}

# Phase A failed before its plan record: prove nothing changed (no finalization needed).
function S2-VerifyUntouched([string]$E) {
    S2-SfmClosed
    S2-Inventory $E "untouched_inventory.json" | Out-Null
    if (-not (S2-Compare $E "untouched_inventory.json" "untouched_compare.json")) {
        throw "STOP: AUTHORITY STATE DIFFERS FROM BASELINE WITHOUT A PLAN RECORD. Do not start SFM. Report."
    }
    "S2 UNTOUCHED: exact production G1, no finalization needed. Session 2 stops here; report."
}

# Restoration (SFM closed): exact G1 Master, G1 republished, G2 sidecar removed, exact baseline.
function S2-Finalize([string]$E) {
    S2-SfmClosed
    $fin = Join-Path $E "finalization_record.json"; $log = Join-Path $E "finalize_stdout.json"
    S2-New $fin; S2-New $log
    $plan = Join-Path $E "g2_plan_record.json"; $pub = Join-Path $E "g2_publication_record.json"
    $a = @((Join-Path $I "I_Generation_Publisher.py"), "--repo-root", $R, "finalize", "--master", $M,
           "--authority-dir", $AUTH, "--g1-source", (Join-Path $E "g1_source.txt"),
           "--baseline-inventory", (Join-Path $E "baseline_inventory.json"), "--out", $fin)
    if (Test-Path -LiteralPath $plan) { $a += @("--plan-record", $plan) }
    if (Test-Path -LiteralPath $pub)  { $a += @("--publication-record", $pub) }
    try {
        S2-Py @a | Out-File -LiteralPath $log -Encoding utf8
        $f = S2-Json $fin
        $v = S2-Inventory $E "restored_inventory.json"
        $same = S2-Compare $E "restored_inventory.json" "restore_compare.json"
        if ($f.exact_match -ne $true -or -not $same -or $v.master_sha256 -ne $G1_MASTER) { throw "restoration is not exact" }
    } catch {
        "STOP: RESTORATION IS NOT EXACT G1. Do not start SFM or any further campaign. Preserve $E and report."
        throw
    }
    "S2 RESTORED EXACT G1: $E"
}

# S2-B preset library inventory: sorted (ordinal) relative paths + SHA-256, UTF-8 without BOM, LF.
function Write-LibInventory([string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $LIB).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
        $rows.Add($rel + "`t" + (S2-Sha $_.FullName))
    }
    $arr = $rows.ToArray()
    [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    "LIBRARY INVENTORY WRITTEN: $Out files=$($arr.Count) sha256=$(S2-Sha $Out)"
}
function Compare-LibInventory([string]$A, [string]$B) {
    if ((S2-Sha $A) -eq (S2-Sha $B)) { "LIBRARY IDENTICAL: $(Split-Path $A -Leaf) == $(Split-Path $B -Leaf)" }
    else {
        "LIBRARY DIFFERENT: $(Split-Path $A -Leaf) != $(Split-Path $B -Leaf)"
        Compare-Object (Get-Content -LiteralPath $A) (Get-Content -LiteralPath $B) | Format-Table -AutoSize | Out-String -Width 400
    }
}
"S2 SHELL READY"
```

`python` must be Python 3: `python --version` should print 3.x.

### 2.2 Campaign paths (write-once; no path shared between campaigns)

`%PUBLIC%\Documents\CPM_Session2\S2A\` holds the invalid first S2-A attempt. It is preserved
unchanged as evidence and is never written to again.

| Record / output | S2-A_R2 (`$EA2`) | S2-B (`$EB`) |
|---|---|---|
| Campaign folder | `%PUBLIC%\Documents\CPM_Session2\S2A_R2\` | `%PUBLIC%\Documents\CPM_Session2\S2B\` |
| G1 byte copy | `S2A_R2\g1_source.txt` | `S2B\g1_source.txt` |
| Baseline inventory | `S2A_R2\baseline_inventory.json` | `S2B\baseline_inventory.json` |
| G2 source (Phase A) | `S2A_R2\g2_source.txt` | `S2B\g2_source.txt` |
| Plan record (Phase A) | `S2A_R2\g2_plan_record.json` | `S2B\g2_plan_record.json` |
| Publication record (Phase A) | `S2A_R2\g2_publication_record.json` | `S2B\g2_publication_record.json` |
| Phase A output | `S2A_R2\phase_a_stdout.json` | `S2B\phase_a_stdout.json` |
| Activation record (Phase B) | `S2A_R2\g2_activation_record.json` | `S2B\g2_activation_record.json` |
| Phase B output | `S2A_R2\phase_b_stdout.json` | `S2B\phase_b_stdout.json` |
| Post-switch inventory | `S2A_R2\post_switch_inventory.json` | `S2B\post_switch_inventory.json` |
| Finalization record | `S2A_R2\finalization_record.json` | `S2B\finalization_record.json` |
| Finalize output | `S2A_R2\finalize_stdout.json` | `S2B\finalize_stdout.json` |
| Restored inventory | `S2A_R2\restored_inventory.json` | `S2B\restored_inventory.json` |
| Restoration comparison | `S2A_R2\restore_compare.json` | `S2B\restore_compare.json` |
| Only if Phase A fails before its plan record | `S2A_R2\untouched_inventory.json`, `S2A_R2\untouched_compare.json` | `S2B\untouched_inventory.json`, `S2B\untouched_compare.json` |
| Library inventories | — | `S2B\library_1_before_prompt.txt`, `S2B\library_2_g2_active_prompt_open.txt`, `S2B\library_3_after_refusal.txt`, `S2B\library_4_after_g2_save.txt` |

**Deployment check** (SFM closed, before S2-A_R2). These SHA-256 values must match:

| File | SHA-256 |
|---|---|
| Menu `ChadChan3D\SFM_Character_Preset_Manager.py` | `996ca483…` |
| `usermod\scripts\ChadChan3D_CPM\SFM_Character_Preset_Manager.py` | `9a78fc96…` |
| `CPM_Session1_Probe.py` | `ce4ace98…` |
| `cpm_authority_adapter.py` | `e96e21b5…` |
| `cpm_compat_v1_projection.py` | `9b077a1b…` |
| `Rebuild_Control_Groups_Normalizer.py` | `1f4ec5a2…` |

## 3. S2-A_R2 — open-window generation replacement (corrected rerun)

A **P#** means: SFM Scripts menu → ChadChan3D → `CPM_Session1_Probe`. Write down the clock time.
Run a probe only when no CPM action or dialog is open. Running the probe does not touch the CPM
window.

**No-interaction window.** From G2 activation (A6) until the stale Apply click (A8), **do not
interact with the CPM window at all.** In CPM, any of the following re-evaluates semantic
readiness, which detects the stale scope and rebuilds it before Apply, invalidating the run:
- list clicks, tab switches, search, sort, Favorites;
- the model list, Refresh, Model Info, the Fit tree, Review.

`BodyTest` is therefore selected under G1 (A4), and A8 clicks only the already-enabled
**Apply Preset** button.

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| A0 | Shell (SFM closed) | `S2-Prepare $EA2` | `S2 BASELINE OK`. Otherwise STOP (nothing changed; report). |
| A1 | SFM | Start SFM fresh; open the qualified fixture (the R15 addendum scene: Mia on `shot3`). **P1.** | — |
| A2 | CPM | Scripts → ChadChan3D → SFM_Character_Preset_Manager. Choose **Mia** in the model list; wait for the Body / Expression / Review counts (Mia under G1). | Counts appear. |
| A3 | CPM | Body tab: select preset **`Body`**, click **Apply Preset**. | A success status. |
| A4 | CPM | Still under G1: select preset **`BodyTest`** in the Body list. **Do not apply it.** | The status reads "Ready to apply "BodyTest"." |
| A5 | SFM | **P2.** | — |
| A6 | Shell | `S2-PhaseA $EA2`, then at once `S2-PhaseB $EA2`. Do not touch SFM in between. **The no-interaction window starts now.** | `S2 PHASE A OK`, then `S2 G2 ACTIVE OK`. On any `STOP` line: §5 R1/R2/R3. |
| A7 | SFM | **P3** (Scripts menu only; do not touch the CPM window). | — |
| A8 | CPM | Click only the already-enabled **Apply Preset** button (`BodyTest` is still selected). Click nothing else first. | A warning says the semantic scope is stale. Click **OK**. Do not reselect. Let CPM rebuild on its own; wait (up to 60 s) until the counts are shown again. **STOP → §5 R4** if no stale warning appears, if Apply reports success, if any other error appears, or if the counts do not return. **STOP → §5 R7** if CPM visibly refreshed or reloaded at any point between A6 and this click. |
| A9 | SFM | **P4.** | — |
| A10 | CPM | Click **Apply Preset** again (the rebuild keeps `BodyTest` selected). | A successful G2 Apply: success status, no warning. **STOP → §5 R4** on any warning or error. |
| A11 | SFM | **P5.** | — |
| A12 | CPM/SFM | Close CPM with ✕. Close SFM **without saving**. | — |
| A13 | Shell | `S2-Finalize $EA2` | `S2 RESTORED EXACT G1`. Otherwise STOP (§5 R6). S2-B stays blocked until S2-A_R2 is also adjudicated PASS (§6). |

## 4. S2-B — generation change during the Save prompt

| Step | Where | Do | Visible expectation / STOP |
|---|---|---|---|
| B0 | Shell (SFM closed) | Only after S2-A_R2 has passed (§1 rule 2): `S2-Prepare $EB` | `S2 BASELINE OK`. |
| B1 | SFM | Start SFM fresh; open the same fixture. **P1.** | — |
| B2 | CPM | Open CPM; choose **Mia**; wait for the counts. **P2.** | Counts appear. |
| B3 | Shell | `Write-LibInventory (Join-Path $EB "library_1_before_prompt.txt")` | `LIBRARY INVENTORY WRITTEN …` |
| B4 | CPM | Body tab: click **Save New**. In the name prompt, type `S2 STALE SAVE`. **Leave the prompt open; do not confirm.** | The prompt is open. |
| B5 | Shell | With the prompt still open: `S2-PhaseA $EB`, then `S2-PhaseB $EB`, then `Write-LibInventory (Join-Path $EB "library_2_g2_active_prompt_open.txt")` | `S2 PHASE A OK`, `S2 G2 ACTIVE OK`, `LIBRARY INVENTORY WRITTEN`. On any `STOP` line: **do not confirm the prompt**; §5 R1/R2/R3. |
| B6 | CPM | Confirm the already-open Save prompt (**OK**). | The expected refusal dialog appears, titled **Can't save preset**, with the message **Preset could not be saved. Nothing was saved.** Click **OK**. Do not reselect anything. Wait (up to 60 s) for the CPM counts to return. **STOP → §5 R4** if this refusal dialog does not appear, if Save reports success, if any other error appears, or if the counts do not return. |
| B7 | SFM + shell | **P3.** Then run, in the shell: `Write-LibInventory (Join-Path $EB "library_3_after_refusal.txt")`; `Compare-LibInventory (Join-Path $EB "library_1_before_prompt.txt") (Join-Path $EB "library_3_after_refusal.txt")`; `Compare-LibInventory (Join-Path $EB "library_2_g2_active_prompt_open.txt") (Join-Path $EB "library_3_after_refusal.txt")` | Both comparisons print `LIBRARY IDENTICAL`. **Any `LIBRARY DIFFERENT` → STOP, §5 R4.** |
| B8 | CPM | Click **Save New**, type `S2 G2 SAVE`, confirm (**OK**). | A success status, with no warning. **STOP → §5 R4** on any warning or error. |
| B9 | SFM + shell | **P4.** Then: `Write-LibInventory (Join-Path $EB "library_4_after_g2_save.txt")`; `Compare-LibInventory (Join-Path $EB "library_3_after_refusal.txt") (Join-Path $EB "library_4_after_g2_save.txt")` | `LIBRARY DIFFERENT`, with the listed changes (adjudicated in §6). |
| B10 | CPM/SFM | Close CPM with ✕. Close SFM **without saving**. | — |
| B11 | Shell | `S2-Finalize $EB` | `S2 RESTORED EXACT G1`. Otherwise STOP (§5 R6). |

## 5. Recovery (fail-closed, at every authority transition)

| Case | Signal | Action |
|---|---|---|
| R1 | Phase A fails **before** its plan record (`STOP: PHASE A FAILED BEFORE ANY AUTHORITY WRITE`) | Do not proceed. Do not touch or confirm CPM. Close SFM without saving. Run `S2-VerifyUntouched <campaign folder>`. It must print `S2 UNTOUCHED`; the plan record is written before any authority write, so none occurred. Stop Session 2 and report. If it prints a STOP, report and do not start SFM. |
| R2 | Phase A fails **after** its plan record (`STOP: PHASE A FAILED AFTER ITS PLAN RECORD`) | Do not proceed. Do not touch or confirm CPM. Close SFM without saving. Run `S2-Finalize <campaign folder>`. It uses the plan record, plus the publication record if one was written. Require `S2 RESTORED EXACT G1`. Stop and report. |
| R3 | Phase B fails, or activation does not prove the exact G2 SHA (`STOP: EXACT G2 ACTIVATION NOT PROVEN`) | Do not proceed. Do not touch or confirm CPM. Close SFM without saving. Run `S2-Finalize <campaign folder>`. Require `S2 RESTORED EXACT G1`. Stop and report. |
| R4 | Any visible acceptance condition fails while G2 is active (A8, A10, B6, B7, B8) | Change nothing else. Close any CPM dialog with Cancel (B4/B6 prompts) or OK (warnings). Close CPM and SFM without saving. Run `S2-Finalize <campaign folder>`. Require `S2 RESTORED EXACT G1`. Preserve all evidence. Stop Session 2 and report. |
| R5 | SFM crashes or hangs after Phase A | End the SFM process. Run `S2-Finalize <campaign folder>`. Require `S2 RESTORED EXACT G1`. Preserve evidence. Stop and report. |
| R6 | `S2-Finalize` prints `STOP: RESTORATION IS NOT EXACT G1` | Do not start SFM. Do not begin or continue any campaign. Do not edit the authority folder or the Master by hand. Preserve the campaign folder and report. |
| R7 | **Invalid S2-A run:** CPM visibly refreshes or reloads before the A8 stale Apply click (live), **or** adjudication finds `PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED` before the A8 `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED` | Live: stop and click nothing further in CPM. Close CPM and SFM without saving. Run `S2-Finalize <campaign folder>`. Require `S2 RESTORED EXACT G1`. Classify the run as procedurally invalid (not PASS, not a product failure). Preserve the folder. A further attempt needs a new write-once campaign path; that campaign path is never reused. |

## 6. Post-campaign adjudication (reviewer; never during SFM manipulation)

**Sources:**
- the CPM log `SFM_CSP_G18AN_SaveNewCopy.log`;
- the probe JSONL;
- the campaign folder's records, inventories and library inventories.

CPM log times are local `HH:MM:SS`; the tool records carry `wall_time` and `epoch`.

### S2-A_R2 PASS — all of:

0. **Valid run:**
   - no `PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED`, `PROD_CPM_STALE_GENERATION_REBUILD` or
     automatic `Select Model` occurs between G2 activation and the A8
     `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED`; otherwise the run is procedurally invalid (§5 R7);
   - the campaign folder holds the full record set, including `post_switch_inventory.json`,
     `restored_inventory.json` and `restore_compare.json`.
1. **G1 scope:**
   - P2 `cpm.scope_generation_prefix` = `ac45e5c1cd45`;
   - the selection's `PROD_PROVIDER_HEALTH … sha256=u'ac45e5c1…'`.
2. **Observed G2:**
   - the activation record shows `post_activation_master_sha256` `54413b6c…`;
   - the post-switch inventory shows Master G2 with both sidecars;
   - P3 still shows the G1 scope.
3. **Stale G1 action rejected before mutation:**
   - the A8 Apply logs
     `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED operation=u'Apply Preset' reason=u'generation-mismatch'`;
   - that operation has no `PROD_APPLY_UNDO_BEFORE`, no `apply.mutation_transaction`, no
     `PROD_APPLY outcome=` and no `phase=u'native-commit'`;
   - its `PROD_OPERATION_END` has `native_commit=None`.
4. **Stale scope discarded, G2 authority acquired, G2 scope rebuilt and published:**
   - **after** that refusal, the log has `PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED`, then
     `PROD_CPM_STALE_GENERATION_REBUILD`;
   - then exactly one automatic `Select Model` operation, with no operator reselection, carrying
     `PROD_PROVIDER_HEALTH status=u'healthy' … sha256=u'54413b6c…'` and
     `PROD_MODEL_SWITCH_STAGE stage='scope-ready'`;
   - P4 shows `scope_generation_prefix` `54413b6ca618`, the same `window.id`, broker
     `total_provider_opens` greater than at P2, and a G2 `cpm_compat_v1` view.
5. **No replay:** between the A8 refusal and the A10 click there is no other `PROD_OPERATION_BEGIN …
   'Apply Body Preset'` and no `PROD_APPLY` line.
6. **Later deliberate G2 action succeeds:**
   - the A10 Apply logs `PROD_CPM_OPERATION_AUTHORIZED … sha256=54413b6c…` and
     `PROD_APPLY outcome='committed' … changed_sides≥1`;
   - the later committed G2 Apply is corroborating evidence only: it shows the intended `BodyTest`
     state had not already been fully applied. The authoritative no-mutation evidence for A8 is
     criterion 3: no Undo entry, mutation transaction, Apply outcome or native-commit phase, and
     `native_commit=None`.
7. **Idle authority:** P2–P5 have leases 0 and open providers 0; one ProdWindow and one watcher.
8. **Restoration:** `finalization_record.json` and `restore_compare.json` both report
   `exact_match: true`, and `restored_inventory.json` shows Master `ac45e5c1…`.

### S2-B PASS — all of:

1. **G1 scope:** P2 `scope_generation_prefix` = `ac45e5c1cd45`.
2. **Authorization after prompt return.** The proof is this sequence:
   - the Save operation and its prompt were already open: `PROD_OPERATION_BEGIN … 'Save Current
     Body'` at B4;
   - the operator then activated exact G2 at B5 while the prompt visibly remained open
     (`S2 G2 ACTIVE OK`; the activation record proves exact G2);
   - the prompt then returned at B6: `PROD_RESOURCE label=u'Q2_SAVE_POST_CONFIRM'`;
   - only after that, the stale G1 authorization was refused:
     `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED operation=u'Save Preset'
     reason=u'generation-mismatch'`.

   The activation record and its `epoch` are preserved as evidence. Its second-resolution
   `wall_time` is not used as a precise ordering proof.
3. **The stale Save writes nothing:**
   - the log has no `PROD_SAVE=` and no `durable-commit` phase for that operation;
   - its `PROD_OPERATION_END` has `durable_commit=None`;
   - `library_1_before_prompt.txt`, `library_2_g2_active_prompt_open.txt` and
     `library_3_after_refusal.txt` are **byte-identical** (equal SHA-256);
   - no inventory line contains `S2 STALE SAVE`.
4. **G2 scope rebuild without replay:**
   - the same rebuild evidence as S2-A_R2 criterion 4 (P3 `54413b6ca618`, same `window.id`);
   - no further `Save Current Body` operation before B8.
5. **Later deliberate G2 Save succeeds:**
   - the B8 Save logs `PROD_CPM_OPERATION_AUTHORIZED operation=u'Save Preset' sha256=54413b6c…` and
     `PROD_SAVE=PASS … name=u'S2 G2 SAVE'`.
   - **Library diff:** `library_4_after_g2_save.txt` differs from `library_3_after_refusal.txt`
     **only** by exactly these lines, which are the files CPM's existing Save path writes:
     - (a) one added line `Body Presets/S2 G2 SAVE--preset-<5 hex>.json` (the preset written);
     - (b) the `character.json` line changed (character profile refreshed by `prod_ensure_character`);
     - (c) a `character.json.bak` line added or changed (the `ReplaceFileW` backup of the
       profile's safe write).

     Any other added, removed or changed line FAILS.
6. **Idle authority:** P2–P4 have leases 0 and open providers 0.
7. **Restoration:** `finalization_record.json` and `restore_compare.json` both report
   `exact_match: true`.

### FAIL (any of)

- the stale operation shows any mutation, `native-commit`, `PROD_APPLY outcome`, `PROD_SAVE` or
  `durable-commit`;
- `library_1/2/3` are not byte-identical;
- `library_4` has any change outside (a)–(c);
- a refusal reason other than `generation-mismatch`;
- no automatic rebuild, or a rebuild that is still G1;
- any automatic replay;
- the deliberate G2 action failing;
- a non-zero lease or provider at an idle P#;
- a restoration that does not report `exact_match: true`.

## 7. Return

Return the following:
- the probe JSONL;
- the CPM log;
- the campaign folders (`%PUBLIC%\Documents\CPM_Session2\S2A_R2`, then `…\S2B`), plus the
  preserved invalid `…\S2A` folder;
- the shell output (copy the PowerShell window text);
- one note per step: done / problem.

At closeout, raw outputs are copied into the repository with workstation paths redacted, as for R15.
