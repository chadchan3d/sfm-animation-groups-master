# ITEM8_GENERATION_DRIVER.ps1 -- CPM handoff section 22 item 8 shell driver (qualification-only).
#
# Windows PowerShell 5.1, outside SFM. Dot-source once per shell, with SFM closed:
#   . "<repository root>\real_sfm_qualification\cpm_item8_post_cleanup\ITEM8_GENERATION_DRIVER.ps1" `
#       -RepoRoot "<repository root>" -Game "<SFM game>"
# then follow ITEM8_RUNBOOK.md. `python` must be Python 3 (the frozen generation tooling).
#
# Section 1 is the frozen Session 2 section 2.1 block (SESSION2_RUNBOOK.md at commit 0597927),
# byte-for-byte except its two placeholder lines, which are filled from -RepoRoot and -Game.
# Its publication (S2-PhaseA), activation (S2-PhaseB), hash gates, baseline (S2-Prepare),
# finalization (S2-Finalize) and untouched proof (S2-VerifyUntouched) are used unchanged;
# test_item8_generation_driver.py proves the equivalence.
# Section 2 adds only item-8 paths, pins, deployment checks and evidence handling.
param(
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [Parameter(Mandatory = $true)][string]$Game
)

# ===========================================================================
# Section 1 -- frozen Session 2 section 2.1 block (verbatim; placeholders filled)
# ===========================================================================
# ---- CPM Session 2 shell set-up. Fill the two placeholders, then paste the whole block. ----
$R    = $RepoRoot
$GAME = $Game                 # the folder containing sfm.exe
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

# ===========================================================================
# Section 2 -- item-8 functions (new). They only add item-8 paths, pins and
# evidence handling; every generation transition above is called unchanged.
# ===========================================================================
foreach ($f in "S2-Prepare","S2-PhaseA","S2-PhaseB","S2-VerifyUntouched","S2-Finalize","S2-Sha","S2-New","S2-Json","S2-SfmClosed","Write-LibInventory","Compare-LibInventory") {
    if (-not (Get-Command $f -ErrorAction SilentlyContinue)) { throw "STOP: the frozen Session 2 block did not load ($f missing)." }
}
$I8_DRIVER_PATH       = $PSCommandPath
$I8_DIR               = Join-Path $R "real_sfm_qualification\cpm_item8_post_cleanup"
$I8_ROOT              = Join-Path $env:PUBLIC "Documents\CPM_Item8"
$I8_POINTER           = Join-Path $I8_ROOT "ACTIVE_ATTEMPT.txt"
$SCRIPTS              = Join-Path $GAME "usermod\scripts"
$MENU                 = Join-Path $SCRIPTS "sfm\mainmenu\ChadChan3D"
$APP_SRC              = Join-Path $R "cpm\app\SFM_Character_Preset_Manager.py"
$APP_DST              = Join-Path $SCRIPTS "ChadChan3D_CPM\SFM_Character_Preset_Manager.py"
$APP_REL              = "ChadChan3D_CPM/SFM_Character_Preset_Manager.py"
$CANDIDATE_SHA        = "bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5"
$PREVIOUS_SHA         = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
$PROBE_SRC            = Join-Path $I8_DIR "CPM_Item8_Probe.py"
$PROBE_DST            = Join-Path $MENU "CPM_Item8_Probe.py"
$PROBE_REL            = "sfm/mainmenu/ChadChan3D/CPM_Item8_Probe.py"
$PROBE_SHA            = "f503c0abaf63f891c108fd81c726b1101288a2dcf1091bf6a386388be1571257"
$FIXTURE_MANIFEST     = Join-Path $I8_DIR "ITEM8_FIXTURE_MANIFEST.json"
$FIXTURE_MANIFEST_SHA = "40b51416fb8e742b2512dd973ade07ccd0e618a58ebd6c96e9dd62efc1afeb2b"
$OPERATOR_TEMPLATE    = Join-Path $I8_DIR "templates\ITEM8_OPERATOR_STEPS_TEMPLATE.md"
$ACCEPTED_SCRIPTS     = Join-Path $R "real_sfm_qualification\cpm_session4\raw\S4A\deploy_after_removal.txt"
$ACCEPTED_SCRIPTS_SHA = "cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922"
$CPM_LOG              = Join-Path $env:PUBLIC "Documents\SFM_CSP_G18AN_SaveNewCopy.log"
$NORMALIZER_LOG       = Join-Path $env:PUBLIC "Documents\sfm_rebuild_control_groups.txt"
$SLOT_MARKERS         = @("_sfm_character_slider_preset_tool_window", "class ProdWindow")
$SLOT_ALLOWED         = @("sfm/mainmenu/ChadChan3D/CPM_Session1_Probe.py", $PROBE_REL)
$ABSENT_BEFORE_DEPLOY = @(
    (Join-Path $MENU "S3_Fit_Pause_Harness.py"), (Join-Path $MENU "CPM_S4_Rollback_Harness.py"),
    (Join-Path $MENU "CPM_Item8_Probe.py"), (Join-Path $MENU "SFM_CSP_G18AN_SaveNewCopy.py"),
    (Join-Path $env:PUBLIC "Documents\CPM_Session3\ACTIVE_CAMPAIGN.txt"),
    (Join-Path $env:PUBLIC "Documents\CPM_Session4\ACTIVE_CAMPAIGN.txt"),
    (Join-Path $env:PUBLIC "Documents\CPM_R15_NOTICE_HARNESS.txt"), $I8_POINTER)
# Frozen Checkpoint I tooling (LF-normalized SHA-256; unchanged since the Session 2 freeze).
$GENERATION_TOOLS = [ordered]@{
    "real_sfm_qualification/checkpoint_i_generation_replacement/I_Generation_Publisher.py" = "16121575bb003ce3927d5fa039782428b2844d0fb82641ef59dcd64eff0c072e"
    "real_sfm_qualification/checkpoint_i_generation_replacement/I_Generation_Helper.py" = "1d08b0282b0904f2993fc0aa0a98f73b5260291c7f3700ca9f946e3f447fbad7"
    "tools/sfm_master_sidecar/__init__.py" = "8cad865fd9954035aebb3e02d5c454228e80a095595bd9cd3746df0b357f904c"
    "tools/sfm_master_sidecar/cli.py" = "9492955bafb549624216a11ddbacd22fa0fc6d53f85bb89c439f1b895249e9b5"
    "tools/sfm_master_sidecar/compiler.py" = "50dd18045c30aa5258b7821bb02d4f68fc0fa88d4e2fa9a335a2972d4e3f7643"
    "tools/sfm_master_sidecar/format.py" = "b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259"
    "tools/sfm_master_sidecar/generated_root.py" = "cb379a17f83f915ce2aa1e87c88134caace5019faddcecacc9e610f865890a67"
    "tools/sfm_master_sidecar/manifest.py" = "edc646679e326115a4c8f3b52452476db7cf1885c5d7992ff647e5c0d90c5173"
    "tools/sfm_master_sidecar/mutex_publisher.py" = "1c34aadaaee3809f8b03bf107d20bf441cab6a7a3eeb1acaccca428973246041"
    "tools/sfm_master_sidecar/publisher.py" = "d9ada0c9fd7cd694355189ce0d90ab1ebb38b514bae69965524bb5748c86b0a5"
    "tools/sfm_master_sidecar/reader.py" = "1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f"
    "tools/sfm_master_sidecar/win_named_mutex.py" = "61865de9e7b723996aca3043d876b940a19416837d106bf9d89f65448b7b64be"
    "tools/sfm_master_sidecar/writer.py" = "770d5beb1809e425869d12cd697e87fa741f085078589bcb982be8279f07d55d"
    "tools/sfm_master_core.py" = "a76e7e4e66f6ee0b4e15f4f2d5c412dcef120240c93d4cd1dd4dd0deff9ef37b"
}
$I8_UTF8 = New-Object System.Text.UTF8Encoding($false)

function I8-ShaLf([string]$Path) {   # SHA-256 of the file with CRLF normalized to LF
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $text = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes).Replace("`r`n", "`n")
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { -join ($sha.ComputeHash([System.Text.Encoding]::GetEncoding(28591).GetBytes($text)) | ForEach-Object { $_.ToString("x2") }) } finally { $sha.Dispose() }
}
function I8-Attempt([string]$Id) {
    if ($Id -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$') { throw "STOP: attempt id must match [A-Za-z0-9][A-Za-z0-9_-]{0,47}." }
    Join-Path $I8_ROOT $Id
}
function I8-WriteText([string]$Path, [string]$Text) { S2-New $Path; [System.IO.File]::WriteAllText($Path, $Text, $I8_UTF8) }
function I8-WriteJson([string]$Path, $Object) { I8-WriteText $Path (($Object | ConvertTo-Json -Depth 12) + "`n") }
function I8-Now { Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff" }

# Deterministic Scripts inventory (same rule as Sessions 3-4): every file under usermod\scripts, relative path + SHA-256, ordinal sort.
function I8-ScriptsInventory([string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rows.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/') + "`t" + (S2-Sha $_.FullName))
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $I8_UTF8)
    "SCRIPTS INVENTORY WRITTEN: $(Split-Path $Out -Leaf) files=$($arr.Count) sha256=$(S2-Sha $Out)"
}
function I8-ReadInventory([string]$Path) {
    $map = @{}
    foreach ($line in [System.IO.File]::ReadAllText($Path, $I8_UTF8).Split("`n")) {
        if ($line) { $i = $line.LastIndexOf("`t"); $map[$line.Substring(0, $i)] = $line.Substring($i + 1) }
    }
    $map
}
# Differences B relative to A: "+path sha" added, "-path sha" removed, "~path old->new" changed (ordinal order).
# (PowerShell names are case-insensitive: the maps must not reuse the [string] parameter names.)
function I8-InventoryDiff([string]$PathA, [string]$PathB) {
    $mapA = I8-ReadInventory $PathA; $mapB = I8-ReadInventory $PathB; $out = New-Object System.Collections.Generic.List[string]
    foreach ($k in $mapB.Keys) { if (-not $mapA.ContainsKey($k)) { $out.Add("+$k $($mapB[$k])") } elseif ($mapA[$k] -ne $mapB[$k]) { $out.Add("~$k $($mapA[$k])->$($mapB[$k])") } }
    foreach ($k in $mapA.Keys) { if (-not $mapB.ContainsKey($k)) { $out.Add("-$k $($mapA[$k])") } }
    $arr = $out.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal); ,$arr
}
function I8-RequireDiff([string]$PathA, [string]$PathB, [string[]]$Expected, [string]$What) {
    $got = I8-InventoryDiff $PathA $PathB
    $want = @($Expected); [System.Array]::Sort($want, [System.StringComparer]::Ordinal)
    if (($got -join "`n") -ne ($want -join "`n")) {
        "UNEXPECTED SCRIPTS DIFFERENCES ($What):"; $got | ForEach-Object { "  $_" }
        "EXPECTED:"; $want | ForEach-Object { "  $_" }
        throw "STOP: the Scripts deployment differs from the expected state ($What). Do not delete anything; report."
    }
}
# Inventory -> temporary file -> required difference -> moved into the attempt. A refused check
# writes no attempt evidence, so the step can be retried after the cause is resolved.
function I8-InventoryChecked([string]$Out, [string]$Reference, [string[]]$Expected, [string]$What) {
    S2-New $Out
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_item8_inventory_" + [System.Guid]::NewGuid().ToString("N") + ".txt")
    try {
        I8-ScriptsInventory $tmp | Out-Null
        I8-RequireDiff $Reference $tmp $Expected $What
    } catch { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp }; throw }
    Move-Item -LiteralPath $tmp -Destination $Out
    "SCRIPTS INVENTORY CHECKED ($What): $(Split-Path $Out -Leaf) sha256=$(S2-Sha $Out)"
}

# Production dependencies against the accepted installed manifest (not every repository file).
function I8-CheckDependencies {
    $m = Get-Content -LiteralPath $FIXTURE_MANIFEST -Raw | ConvertFrom-Json
    $result = [ordered]@{}
    foreach ($p in $m.deployment.unchanged_menu_dependencies.PSObject.Properties) {
        $path = Join-Path $SCRIPTS ($p.Name.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $path)) { throw "STOP: missing production dependency $($p.Name)." }
        $got = S2-Sha $path; $result[$p.Name] = $got
        if ($got -ne $p.Value) { throw "STOP: production dependency $($p.Name) is $got, not the accepted $($p.Value)." }
    }
    foreach ($pkg in @($m.deployment.shared_package, $m.deployment.sidecar_reader)) {
        $dir = Join-Path $SCRIPTS ($pkg.menu_relative_dir.Replace('/', '\'))
        $want = @($pkg.files.PSObject.Properties | ForEach-Object { $_.Name }) | Sort-Object
        $have = @(Get-ChildItem -LiteralPath $dir -File -Filter "*.py" | ForEach-Object { $_.Name }) | Sort-Object
        if (($want -join ",") -ne ($have -join ",")) { throw "STOP: $($pkg.menu_relative_dir) .py set differs from the accepted installed manifest." }
        foreach ($p in $pkg.files.PSObject.Properties) {
            $got = S2-Sha (Join-Path $dir $p.Name); $result["$($pkg.menu_relative_dir)/$($p.Name)"] = $got
            if ($got -ne $p.Value) { throw "STOP: $($pkg.menu_relative_dir)/$($p.Name) is $got, not the accepted $($p.Value)." }
        }
    }
    $result
}
# Files under usermod\scripts\sfm that carry a full-CPM marker (window slot or ProdWindow class).
function I8-CpmImplementationScan {
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $hits = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath (Join-Path $SCRIPTS "sfm") -Recurse -File -Force -Filter "*.py" | ForEach-Object {
        $text = [System.IO.File]::ReadAllText($_.FullName)
        foreach ($marker in $SLOT_MARKERS) { if ($text.Contains($marker)) { $hits.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/')); break } }
    }
    $arr = $hits.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    ,@($arr | Where-Object { $SLOT_ALLOWED -notcontains $_ })
}
function I8-PackageCopyScan {
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $expected = @("sfm/mainmenu/ChadChan3D/sfm_master_authority_productionized", "sfm/mainmenu/ChadChan3D/sfm_master_sidecar")
    $arr = @(Get-ChildItem -LiteralPath $SCRIPTS -Recurse -Directory -Force | Where-Object {
        @("sfm_master_authority_productionized", "sfm_master_authority", "sfm_master_sidecar") -contains $_.Name
    } | ForEach-Object { $_.FullName.Substring($root.Length + 1).Replace('\', '/') } | Where-Object { $expected -notcontains $_ })
    [System.Array]::Sort($arr, [System.StringComparer]::Ordinal); ,$arr
}
function I8-LogState([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [ordered]@{ exists = $false } }
    [ordered]@{ exists = $true; bytes = (Get-Item -LiteralPath $Path).Length; sha256 = (S2-Sha $Path) }
}

# ---- 1. Create the write-once attempt folder (SFM closed). ----
function I8-New([string]$Id, [string]$KrystalDocument, [string]$MiaDocument) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    if (Test-Path -LiteralPath $I8_POINTER) { throw "STOP: an item-8 attempt pointer already exists ($I8_POINTER). Close that attempt first." }
    if ((S2-Sha $FIXTURE_MANIFEST) -ne $FIXTURE_MANIFEST_SHA) { throw "STOP: ITEM8_FIXTURE_MANIFEST.json is not the pinned file." }
    $docs = [ordered]@{}
    foreach ($pair in @(@("krystal", $KrystalDocument), @("mia", $MiaDocument))) {
        if (-not $pair[1] -or -not (Test-Path -LiteralPath $pair[1] -PathType Leaf)) { throw "STOP: the $($pair[0]) fixture document was not found: $($pair[1])" }
        $docs[$pair[0]] = [ordered]@{ file_name = (Split-Path $pair[1] -Leaf); path = (Get-Item -LiteralPath $pair[1]).FullName
                                      bytes = (Get-Item -LiteralPath $pair[1]).Length; sha256 = (S2-Sha $pair[1]) }
    }
    if (-not (Test-Path -LiteralPath $I8_ROOT)) { New-Item -ItemType Directory -Path $I8_ROOT | Out-Null }
    S2-New $E
    New-Item -ItemType Directory -Path $E | Out-Null
    foreach ($d in "scene_snapshots","library_inventories","preset_readback","logs","restoration") { New-Item -ItemType Directory -Path (Join-Path $E $d) | Out-Null }
    $m = Get-Content -LiteralPath $FIXTURE_MANIFEST -Raw | ConvertFrom-Json
    I8-WriteJson (Join-Path $E "authority_pins.json") ([ordered]@{
        schema = "cpm-item8-authority-pins-v1"; attempt = $Id; wall_time = (I8-Now)
        G1 = $m.authority.G1; G2 = $m.authority.G2
        candidate_app_sha256 = $CANDIDATE_SHA; previous_installed_app_sha256 = $PREVIOUS_SHA
        probe_sha256 = $PROBE_SHA; fixture_manifest_sha256 = $FIXTURE_MANIFEST_SHA
        driver_lf_sha256 = (I8-ShaLf $I8_DRIVER_PATH); accepted_scripts_inventory_sha256 = $ACCEPTED_SCRIPTS_SHA
        generation_tools_lf_sha256 = $GENERATION_TOOLS })
    I8-WriteJson (Join-Path $E "fixture_manifest.json") ([ordered]@{
        schema = "cpm-item8-attempt-fixture-manifest-v1"; attempt = $Id; wall_time = (I8-Now)
        static_manifest_sha256 = $FIXTURE_MANIFEST_SHA; documents = $docs; static = $m })
    I8-WriteText (Join-Path $E "operator_steps.md") ([System.IO.File]::ReadAllText($OPERATOR_TEMPLATE, $I8_UTF8).Replace("<attempt>", $Id))
    "I8 ATTEMPT CREATED: $E"
}

# ---- 2. Preflight (SFM closed): identities, contamination, generation baseline. ----
function I8-Preflight([string]$Id, [switch]$Owner1Recorded) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "authority_pins.json"))) { throw "STOP: run I8-New first." }
    if (Test-Path -LiteralPath (Join-Path $E "deployment_before.json")) { throw "STOP: preflight already recorded for $Id (write-once)." }
    $pyver = (& python --version 2>&1 | Out-String).Trim()
    if ($pyver -notmatch '^Python 3\.') { throw "STOP: python must be Python 3 for the frozen generation tooling (got '$pyver')." }
    foreach ($p in $GENERATION_TOOLS.GetEnumerator()) {
        $got = I8-ShaLf (Join-Path $R ($p.Key.Replace('/', '\')))
        if ($got -ne $p.Value) { throw "STOP: generation tool $($p.Key) is $got, not the frozen $($p.Value)." }
    }
    if ((S2-Sha $ACCEPTED_SCRIPTS) -ne $ACCEPTED_SCRIPTS_SHA) { throw "STOP: the accepted Scripts inventory in the repository is not the pinned file." }
    if ((S2-Sha $APP_SRC) -ne $CANDIDATE_SHA) { throw "STOP: the repository app is not the candidate $CANDIDATE_SHA." }
    if ((S2-Sha $PROBE_SRC) -ne $PROBE_SHA) { throw "STOP: the repository item-8 probe is not the pinned $PROBE_SHA." }
    $installed = S2-Sha $APP_DST
    if ($installed -ne $PREVIOUS_SHA) { throw "STOP: the installed private app is $installed, not the previously installed $PREVIOUS_SHA." }
    $present = @($ABSENT_BEFORE_DEPLOY | Where-Object { Test-Path -LiteralPath $_ })
    if ($present.Count) { $present | ForEach-Object { "PRESENT: $_" }; throw "STOP: qualification-only harness/pointer/flag residue is present. Do not delete anything; report." }
    $private = @(Get-ChildItem -LiteralPath (Split-Path $APP_DST) -Force | ForEach-Object { $_.Name })
    if (($private -join ",") -ne "SFM_Character_Preset_Manager.py") { throw "STOP: the private module folder holds more than the implementation file ($($private -join ', '))." }
    # Every check below is read-only; attempt evidence is written only after all of them pass.
    $liveInv = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_item8_preflight_" + [System.Guid]::NewGuid().ToString("N") + ".txt")
    try {
        I8-ScriptsInventory $liveInv | Out-Null
        I8-RequireDiff $ACCEPTED_SCRIPTS $liveInv @() "before deployment vs the accepted Session 4 closeout inventory"
        $deps = I8-CheckDependencies
        $cpm = I8-CpmImplementationScan
        $copies = I8-PackageCopyScan
        if (($cpm.Count -or $copies.Count) -and -not $Owner1Recorded) {
            "HISTORICAL FULL-CPM FILES IN THE MENU TREE ($($cpm.Count)):"; $cpm | ForEach-Object { "  $_" }
            "HISTORICAL AUTHORITY/SIDECAR PACKAGE COPIES ($($copies.Count)):"; $copies | ForEach-Object { "  $_" }
            throw "STOP: owner disposition OWNER-1 (ITEM8_RUNBOOK.md section 2) is required for this accepted historical content. Do not delete anything."
        }
        if (-not (Test-Path -LiteralPath $LIB -PathType Container)) { throw "STOP: the Mia preset library folder was not found ($LIB)." }
    } catch { if (Test-Path -LiteralPath $liveInv) { Remove-Item -LiteralPath $liveInv }; throw }
    $inv = Join-Path $E "restoration\scripts_inventory_before_deploy.txt"; S2-New $inv
    Move-Item -LiteralPath $liveInv -Destination $inv
    if ((S2-Sha $inv) -ne (S2-Sha $ACCEPTED_SCRIPTS)) { throw "STOP: the recorded inventory differs from the accepted inventory. Report." }
    $git = [ordered]@{ head = ((& git -C $R rev-parse HEAD 2>&1) | Out-String).Trim()
                       tracked_changes = @(& git -C $R status --porcelain --untracked-files=no 2>&1) }
    S2-Prepare (Join-Path $E "generation")
    Write-LibInventory (Join-Path $E "library_inventories\library_00_preflight.txt")
    I8-WriteJson (Join-Path $E "deployment_before.json") ([ordered]@{
        schema = "cpm-item8-deployment-before-v1"; attempt = $Id; wall_time = (I8-Now); sfm_running = $false
        repository = $git; python_for_generation_tooling = $pyver
        repository_candidate_sha256 = $CANDIDATE_SHA; installed_app_sha256 = $installed
        production_dependencies = $deps; scripts_inventory = "restoration/scripts_inventory_before_deploy.txt"
        scripts_inventory_equals_accepted = $true
        historical_full_cpm_files = $cpm; historical_package_copies = $copies; owner1_recorded = [bool]$Owner1Recorded
        cpm_log = (I8-LogState $CPM_LOG); normalizer_log = (I8-LogState $NORMALIZER_LOG)
        generation_baseline = "generation/baseline_inventory.json" })
    "I8 PREFLIGHT OK: $Id"
}

# ---- 3. Deploy the candidate and the probe (SFM closed). ----
function I8-Deploy([string]$Id) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "deployment_before.json"))) { throw "STOP: run I8-Preflight first." }
    S2-New (Join-Path $E "deployment_after.json")
    $backup = Join-Path $E "restoration\installed_app_backup.py"; S2-New $backup
    Copy-Item -LiteralPath $APP_DST -Destination $backup
    if ((S2-Sha $backup) -ne $PREVIOUS_SHA) { throw "STOP: the installed-app backup is not $PREVIOUS_SHA." }
    if ((S2-Sha $APP_SRC) -ne $CANDIDATE_SHA) { throw "STOP: the repository app is not the candidate $CANDIDATE_SHA." }
    $tmp = $APP_DST + ".item8tmp"; S2-New $tmp
    Copy-Item -LiteralPath $APP_SRC -Destination $tmp
    if ((S2-Sha $tmp) -ne $CANDIDATE_SHA) { Remove-Item -LiteralPath $tmp; throw "STOP: the staged candidate is not $CANDIDATE_SHA; removed, installed app untouched." }
    [System.IO.File]::Replace($tmp, $APP_DST, [NullString]::Value)
    if (Test-Path -LiteralPath $tmp) { throw "STOP: the temporary sibling remained after replacement. Report." }
    $now = S2-Sha $APP_DST
    if ($now -ne $CANDIDATE_SHA) { throw "STOP: the installed app is $now after replacement, not $CANDIDATE_SHA. Report; then I8-Disposition $Id INCONCLUSIVE." }
    S2-New $PROBE_DST
    if ((S2-Sha $PROBE_SRC) -ne $PROBE_SHA) { throw "STOP: the repository probe is not $PROBE_SHA." }
    Copy-Item -LiteralPath $PROBE_SRC -Destination $PROBE_DST
    if ((S2-Sha $PROBE_DST) -ne $PROBE_SHA) { Remove-Item -LiteralPath $PROBE_DST; throw "STOP: the installed probe hash mismatched; removed." }
    I8-InventoryChecked (Join-Path $E "restoration\scripts_inventory_after_deploy.txt") (Join-Path $E "restoration\scripts_inventory_before_deploy.txt") @("~$APP_REL $PREVIOUS_SHA->$CANDIDATE_SHA", "+$PROBE_REL $PROBE_SHA") "after deployment"
    $deps = I8-CheckDependencies
    I8-WriteJson (Join-Path $E "deployment_after.json") ([ordered]@{
        schema = "cpm-item8-deployment-after-v1"; attempt = $Id; wall_time = (I8-Now)
        installed_app_sha256 = $now; installed_probe_sha256 = (S2-Sha $PROBE_DST); backup = "restoration/installed_app_backup.py"
        replacement = "temporary sibling + System.IO.File.Replace"; production_dependencies = $deps
        scripts_inventory = "restoration/scripts_inventory_after_deploy.txt"; pointer = $Id })
    I8-WriteText $I8_POINTER $Id
    "I8 DEPLOYED: candidate $CANDIDATE_SHA installed; probe installed; active attempt $Id. Start a FRESH SFM process."
}

# ---- Evidence during the run. ----
function I8-Library([string]$Id, [string]$Name) {
    $E = I8-Attempt $Id
    Write-LibInventory (Join-Path $E "library_inventories\$Name.txt")
}
function I8-LibraryCompare([string]$Id, [string]$A, [string]$B) {
    $E = I8-Attempt $Id
    Compare-LibInventory (Join-Path $E "library_inventories\$A.txt") (Join-Path $E "library_inventories\$B.txt")
}
# Copy exactly one preset/profile file (wildcard relative to the Mia library) for direct readback.
function I8-Readback([string]$Id, [string]$Label, [string]$RelativePattern) {
    $E = I8-Attempt $Id
    if ($Label -notmatch '^[A-Za-z0-9_-]+$') { throw "STOP: readback label must match [A-Za-z0-9_-]+." }
    $root = (Get-Item -LiteralPath $LIB).FullName.TrimEnd('\')
    $hits = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object {
        $_.FullName.Substring($root.Length + 1).Replace('\', '/') -like $RelativePattern })
    if ($hits.Count -ne 1) { throw "STOP: readback pattern '$RelativePattern' matched $($hits.Count) files (exactly one required)." }
    $rel = $hits[0].FullName.Substring($root.Length + 1).Replace('\', '/')
    $dst = Join-Path $E ("preset_readback\" + $Label + ".json"); S2-New $dst
    Copy-Item -LiteralPath $hits[0].FullName -Destination $dst
    I8-WriteJson (Join-Path $E ("preset_readback\" + $Label + ".source.json")) ([ordered]@{
        label = $Label; library_relative_path = $rel; sha256 = (S2-Sha $dst); bytes = (Get-Item -LiteralPath $dst).Length; wall_time = (I8-Now) })
    "I8 READBACK: $Label <- $rel sha256=$(S2-Sha $dst)"
}
# Phase E: publish and activate exact G2 back to back (frozen Session 2 Phase A + Phase B), then the
# library inventory with the Save prompt still open. No SFM interaction between them.
function I8-GenerationSwitch([string]$Id) {
    $E = I8-Attempt $Id
    $G = Join-Path $E "generation"
    if (-not (Test-Path -LiteralPath (Join-Path $G "baseline_inventory.json"))) { throw "STOP: no generation baseline for $Id." }
    S2-PhaseA $G
    S2-PhaseB $G
    Write-LibInventory (Join-Path $E "library_inventories\library_E2_g2_active_prompt_open.txt")
}
function I8-CollectLogs([string]$Id, [string]$Label) {
    $E = I8-Attempt $Id
    if ($Label -notmatch '^[A-Za-z0-9_-]+$') { throw "STOP: log label must match [A-Za-z0-9_-]+." }
    $rec = [ordered]@{ label = $Label; wall_time = (I8-Now) }
    foreach ($pair in @(@("cpm", $CPM_LOG), @("normalizer", $NORMALIZER_LOG))) {
        if (Test-Path -LiteralPath $pair[1]) {
            $dst = Join-Path $E ("logs\" + $Label + "__" + (Split-Path $pair[1] -Leaf)); S2-New $dst
            Copy-Item -LiteralPath $pair[1] -Destination $dst
            $rec[$pair[0]] = [ordered]@{ file = ("logs/" + (Split-Path $dst -Leaf)); sha256 = (S2-Sha $dst); bytes = (Get-Item -LiteralPath $dst).Length }
        } else { $rec[$pair[0]] = [ordered]@{ exists = $false } }
    }
    I8-WriteJson (Join-Path $E ("logs\" + $Label + ".json")) $rec
    "I8 LOGS COLLECTED: $Label"
}

# ---- Closeout (SFM closed). ----
# Exact G1 restoration with the frozen finalization (or proof that authority was never touched).
function I8-Finalize([string]$Id) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    $G = Join-Path $E "generation"
    if (Test-Path -LiteralPath (Join-Path $G "g2_plan_record.json")) { S2-Finalize $G } else { S2-VerifyUntouched $G }
}
# Remove the probe and pointer; the candidate stays installed pending adjudication. Seals the live evidence.
function I8-RemoveQualificationDeployment([string]$Id) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    $rec = Join-Path $E "restoration\qualification_removal.json"; S2-New $rec
    $actions = New-Object System.Collections.Generic.List[string]
    if (Test-Path -LiteralPath $PROBE_DST) {
        if ((S2-Sha $PROBE_DST) -ne $PROBE_SHA) { throw "STOP: the installed probe is not the pinned file; do not delete. Report." }
        Remove-Item -LiteralPath $PROBE_DST; $actions.Add("removed probe")
    }
    if (Test-Path -LiteralPath $I8_POINTER) {
        $pointed = [System.IO.File]::ReadAllText($I8_POINTER).Trim()
        if ($pointed -ne $Id) { throw "STOP: the pointer names attempt '$pointed', not '$Id'. Report." }
        Remove-Item -LiteralPath $I8_POINTER; $actions.Add("removed pointer")
    }
    if (Test-Path -LiteralPath ($APP_DST + ".item8tmp")) { throw "STOP: a temporary app sibling remains. Report." }
    $app = S2-Sha $APP_DST
    $expected = @(); if ($app -eq $CANDIDATE_SHA) { $expected = @("~$APP_REL $PREVIOUS_SHA->$CANDIDATE_SHA") } elseif ($app -ne $PREVIOUS_SHA) { throw "STOP: the installed app is $app (neither candidate nor previous). Report." }
    I8-InventoryChecked (Join-Path $E "restoration\scripts_inventory_after_qualification_removal.txt") (Join-Path $E "restoration\scripts_inventory_before_deploy.txt") $expected "after removing qualification-only deployment"
    I8-WriteJson $rec ([ordered]@{ wall_time = (I8-Now); actions = $actions.ToArray(); installed_app_sha256 = $app
                                   scripts_inventory = "restoration/scripts_inventory_after_qualification_removal.txt" })
    I8-SealList $E (Join-Path $E "restoration\live_evidence_sha256.txt")
    "I8 QUALIFICATION DEPLOYMENT REMOVED: installed app $app. Do not start SFM before I8-Disposition."
}
function I8-SealList([string]$E, [string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $E).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
        if ($rel -ne "SHA256SUMS.txt" -and $_.FullName -ne $Out) { $rows.Add((S2-Sha $_.FullName) + "  " + $rel) }
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $I8_UTF8)
    "SEALED: $(Split-Path $Out -Leaf) files=$($arr.Count)"
}
# Deployment policy after adjudication: PASS keeps the exact candidate; FAIL/INCONCLUSIVE restores 9a78fc96...
function I8-Disposition([string]$Id, [ValidateSet("PASS","FAIL","INCONCLUSIVE")][string]$Verdict) {
    S2-SfmClosed
    $E = I8-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "restoration\qualification_removal.json"))) { throw "STOP: run I8-RemoveQualificationDeployment first." }
    $G = Join-Path $E "generation"
    $restore = Join-Path $G "restore_compare.json"; $untouched = Join-Path $G "untouched_compare.json"
    $cmp = $null; if (Test-Path -LiteralPath $restore) { $cmp = $restore } elseif (Test-Path -LiteralPath $untouched) { $cmp = $untouched }
    if (-not $cmp -or (S2-Json $cmp).exact_match -ne $true) { throw "STOP: exact G1 restoration is not proven (run I8-Finalize). Do not start SFM." }
    $rec = Join-Path $E "restoration\disposition.json"; S2-New $rec
    $inv = Join-Path $E "restoration\scripts_inventory_final.txt"
    if (Test-Path -LiteralPath (Join-Path $E "SHA256SUMS.txt")) { throw "STOP: attempt $Id is already sealed." }
    if ($Verdict -eq "PASS") {
        if ((S2-Sha $APP_DST) -ne $CANDIDATE_SHA) { throw "STOP: PASS requires the installed candidate $CANDIDATE_SHA." }
        I8-InventoryChecked $inv $ACCEPTED_SCRIPTS @("~$APP_REL $PREVIOUS_SHA->$CANDIDATE_SHA") "final (PASS: candidate retained)"
        $action = "candidate retained"
    } else {
        if ((S2-Sha $APP_DST) -ne $PREVIOUS_SHA) {
            $backup = Join-Path $E "restoration\installed_app_backup.py"
            if ((S2-Sha $backup) -ne $PREVIOUS_SHA) { throw "STOP: the backup is not $PREVIOUS_SHA. Report." }
            $tmp = $APP_DST + ".item8tmp"; S2-New $tmp
            Copy-Item -LiteralPath $backup -Destination $tmp
            if ((S2-Sha $tmp) -ne $PREVIOUS_SHA) { Remove-Item -LiteralPath $tmp; throw "STOP: staged restore mismatch; removed." }
            [System.IO.File]::Replace($tmp, $APP_DST, [NullString]::Value)
            $action = "previous app restored"
        } else { $action = "previous app already installed" }
        if ((S2-Sha $APP_DST) -ne $PREVIOUS_SHA) { throw "STOP: the installed app is not $PREVIOUS_SHA after restoration. Report." }
        I8-InventoryChecked $inv $ACCEPTED_SCRIPTS @() "final ($($Verdict): previous app restored)"
    }
    I8-WriteJson $rec ([ordered]@{ attempt = $Id; verdict = $Verdict; wall_time = (I8-Now); action = $action
                                   installed_app_sha256 = (S2-Sha $APP_DST); scripts_inventory = "restoration/scripts_inventory_final.txt"
                                   authority_restoration = ((Split-Path $cmp -Leaf)) })
    I8-SealList $E (Join-Path $E "SHA256SUMS.txt")
    "I8 DISPOSITION $($Verdict): $action; installed app $(S2-Sha $APP_DST). Attempt sealed."
}
"I8 SHELL READY"
