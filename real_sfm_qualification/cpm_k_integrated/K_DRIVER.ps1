# K_DRIVER.ps1 -- K integrated CPM/Normalizer product workflow qualification shell driver (qualification-only).
#
# Windows PowerShell 5.1, outside SFM. Dot-source once per shell, with SFM closed:
#   . "<repository root>\real_sfm_qualification\cpm_k_integrated\K_DRIVER.ps1" `
#       -RepoRoot "<repository root>" -Game "<SFM game>"
# then follow cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md. `python` must be
# Python 3 (the frozen generation tooling).
#
# Section 1 is the frozen Session 2 section 2.1 block (SESSION2_RUNBOOK.md at commit 0597927),
# byte-for-byte except its two placeholder lines, which are filled from -RepoRoot and -Game (identical
# to ITEM8_GENERATION_DRIVER.ps1 Section 1). Its publication (S2-PhaseA), activation (S2-PhaseB), hash
# gates, baseline (S2-Prepare), finalization (S2-Finalize) and untouched proof (S2-VerifyUntouched) are
# used unchanged; test_cpm_k_tooling.py proves the equivalence. K uses at most one transition (K2).
# Section 2 adds only K paths, pins, the probe deployment and evidence handling.
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
# Section 2 -- K functions (new). They only add K paths, pins and evidence
# handling; the one generation transition (K2) calls the frozen block unchanged.
# The CPM app is never redeployed: K requires the installed app to already be
# the exact K candidate (pre-K U3), and deploys only the probe and the pointer.
# ===========================================================================
foreach ($f in "S2-Prepare","S2-PhaseA","S2-PhaseB","S2-VerifyUntouched","S2-Finalize","S2-Sha","S2-New","S2-Json","S2-SfmClosed") {
    if (-not (Get-Command $f -ErrorAction SilentlyContinue)) { throw "STOP: the frozen Session 2 block did not load ($f missing)." }
}
$K_DRIVER_PATH        = $PSCommandPath
$K_DIR                = Join-Path $R "real_sfm_qualification\cpm_k_integrated"
$K_ROOT               = Join-Path $env:PUBLIC "Documents\CPM_K"
$K_POINTER            = Join-Path $K_ROOT "ACTIVE_ATTEMPT.txt"
$SCRIPTS              = Join-Path $GAME "usermod\scripts"
$MENU                 = Join-Path $SCRIPTS "sfm\mainmenu\ChadChan3D"
$APP_SRC              = Join-Path $R "cpm\app\SFM_Character_Preset_Manager.py"
$APP_DST              = Join-Path $SCRIPTS "ChadChan3D_CPM\SFM_Character_Preset_Manager.py"
$APP_REL              = "ChadChan3D_CPM/SFM_Character_Preset_Manager.py"
$CANDIDATE_SHA        = "4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7"
$S4_APP_SHA           = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
$PROBE_SRC            = Join-Path $K_DIR "CPM_K_Probe.py"
$PROBE_DST            = Join-Path $MENU "CPM_K_Probe.py"
$PROBE_REL            = "sfm/mainmenu/ChadChan3D/CPM_K_Probe.py"
$PROBE_SHA            = "96d873b795f6fc8e10e762c06045990fbd59663fdf6e03e86dfb79dcdd759365"
$FIXTURE_MANIFEST     = Join-Path $K_DIR "K_FIXTURE_MANIFEST.json"
$FIXTURE_MANIFEST_SHA = "0c390b8d3e3b51b3a3bc42b0473d05f3b48a7f9f26bff987f2cc02cd26d27b83"
$OPERATOR_TEMPLATE    = Join-Path $K_DIR "templates\K_OPERATOR_STEPS_TEMPLATE.md"
$FIXTURE_DOCUMENT_SHA = "197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f"
$ACCEPTED_SCRIPTS     = Join-Path $R "real_sfm_qualification\cpm_session4\raw\S4A\deploy_after_removal.txt"
$ACCEPTED_SCRIPTS_SHA = "cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922"
$EXPECTED_SCRIPTS_SHA = "59b8f28b7d5b7acc7c33f2561bb8a2641bcd7a3e773f68f25215c77681df9086"
$CPM_LOG              = Join-Path $env:PUBLIC "Documents\SFM_CSP_G18AN_SaveNewCopy.log"
$NORMALIZER_LOG       = Join-Path $env:PUBLIC "Documents\sfm_rebuild_control_groups.txt"
$CHARACTERS           = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "SFM Character Preset Manager\Characters"
$SLOT_MARKERS         = @("_sfm_character_slider_preset_tool_window", "class ProdWindow")
$SLOT_ALLOWED         = @("sfm/mainmenu/ChadChan3D/CPM_Session1_Probe.py", $PROBE_REL)
$ABSENT_BEFORE_DEPLOY = @(
    (Join-Path $MENU "S3_Fit_Pause_Harness.py"), (Join-Path $MENU "CPM_S4_Rollback_Harness.py"),
    (Join-Path $MENU "CPM_Item8_Probe.py"), (Join-Path $MENU "CPM_K_Probe.py"), (Join-Path $MENU "SFM_CSP_G18AN_SaveNewCopy.py"),
    (Join-Path $env:PUBLIC "Documents\CPM_Session3\ACTIVE_CAMPAIGN.txt"),
    (Join-Path $env:PUBLIC "Documents\CPM_Session4\ACTIVE_CAMPAIGN.txt"),
    (Join-Path $env:PUBLIC "Documents\CPM_R15_NOTICE_HARNESS.txt"),
    (Join-Path $env:PUBLIC "Documents\CPM_Item8\ACTIVE_ATTEMPT.txt"), $K_POINTER)
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
$K_UTF8 = New-Object System.Text.UTF8Encoding($false)

function K-ShaLf([string]$Path) {   # SHA-256 of the file with CRLF normalized to LF
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $text = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes).Replace("`r`n", "`n")
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { -join ($sha.ComputeHash([System.Text.Encoding]::GetEncoding(28591).GetBytes($text)) | ForEach-Object { $_.ToString("x2") }) } finally { $sha.Dispose() }
}
function K-Attempt([string]$Id) {
    if ($Id -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$') { throw "STOP: attempt id must match [A-Za-z0-9][A-Za-z0-9_-]{0,47}." }
    Join-Path $K_ROOT $Id
}
function K-WriteText([string]$Path, [string]$Text) { S2-New $Path; [System.IO.File]::WriteAllText($Path, $Text, $K_UTF8) }
function K-WriteJson([string]$Path, $Object) { K-WriteText $Path (($Object | ConvertTo-Json -Depth 12) + "`n") }
function K-Now { Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff" }

# Deterministic Scripts inventory (same rule as Sessions 3-4 and item 8): every file under usermod\scripts,
# relative path + SHA-256, ordinal sort.
function K-ScriptsInventory([string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rows.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/') + "`t" + (S2-Sha $_.FullName))
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $K_UTF8)
    "SCRIPTS INVENTORY WRITTEN: $(Split-Path $Out -Leaf) files=$($arr.Count) sha256=$(S2-Sha $Out)"
}
function K-ReadInventory([string]$Path) {
    $map = @{}
    foreach ($line in [System.IO.File]::ReadAllText($Path, $K_UTF8).Split("`n")) {
        if ($line) { $i = $line.LastIndexOf("`t"); $map[$line.Substring(0, $i)] = $line.Substring($i + 1) }
    }
    $map
}
# Differences B relative to A: "+path sha" added, "-path sha" removed, "~path old->new" changed (ordinal order).
# (PowerShell names are case-insensitive: the maps must not reuse the [string] parameter names.)
function K-InventoryDiff([string]$PathA, [string]$PathB) {
    $mapA = K-ReadInventory $PathA; $mapB = K-ReadInventory $PathB; $out = New-Object System.Collections.Generic.List[string]
    foreach ($k in $mapB.Keys) { if (-not $mapA.ContainsKey($k)) { $out.Add("+$k $($mapB[$k])") } elseif ($mapA[$k] -ne $mapB[$k]) { $out.Add("~$k $($mapA[$k])->$($mapB[$k])") } }
    foreach ($k in $mapA.Keys) { if (-not $mapB.ContainsKey($k)) { $out.Add("-$k $($mapA[$k])") } }
    $arr = $out.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal); ,$arr
}
function K-RequireDiff([string]$PathA, [string]$PathB, [string[]]$Expected, [string]$What) {
    $got = K-InventoryDiff $PathA $PathB
    $want = @($Expected); [System.Array]::Sort($want, [System.StringComparer]::Ordinal)
    if (($got -join "`n") -ne ($want -join "`n")) {
        "UNEXPECTED SCRIPTS DIFFERENCES ($What):"; $got | ForEach-Object { "  $_" }
        "EXPECTED:"; $want | ForEach-Object { "  $_" }
        throw "STOP: the Scripts deployment differs from the expected state ($What). Do not delete anything; report."
    }
}
# Inventory -> temporary file -> required difference -> moved into the attempt. A refused check
# writes no attempt evidence, so the step can be retried after the cause is resolved.
function K-InventoryChecked([string]$Out, [string]$Reference, [string[]]$Expected, [string]$What) {
    S2-New $Out
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_k_inventory_" + [System.Guid]::NewGuid().ToString("N") + ".txt")
    try {
        K-ScriptsInventory $tmp | Out-Null
        K-RequireDiff $Reference $tmp $Expected $What
    } catch { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp }; throw }
    Move-Item -LiteralPath $tmp -Destination $Out
    "SCRIPTS INVENTORY CHECKED ($What): $(Split-Path $Out -Leaf) sha256=$(S2-Sha $Out)"
}
# The expected K deployment: the accepted Session 4 inventory with only the private-app line changed.
function K-ExpectedInventory([string]$Out) {
    S2-New $Out
    if ((S2-Sha $ACCEPTED_SCRIPTS) -ne $ACCEPTED_SCRIPTS_SHA) { throw "STOP: the accepted Session 4 inventory in the repository is not the pinned file." }
    $text = [System.IO.File]::ReadAllText($ACCEPTED_SCRIPTS, $K_UTF8)
    $old = "$APP_REL`t$S4_APP_SHA"; $new = "$APP_REL`t$CANDIDATE_SHA"
    if (([regex]::Matches($text, [regex]::Escape($old))).Count -ne 1) { throw "STOP: the accepted inventory does not hold exactly one Session 4 app line." }
    [System.IO.File]::WriteAllText($Out, $text.Replace($old, $new), $K_UTF8)
    if ((S2-Sha $Out) -ne $EXPECTED_SCRIPTS_SHA) { Remove-Item -LiteralPath $Out; throw "STOP: the derived expected inventory is not $EXPECTED_SCRIPTS_SHA." }
}

# Production dependencies against the accepted installed manifest (not every repository file).
function K-CheckDependencies {
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
function K-CpmImplementationScan {
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $hits = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath (Join-Path $SCRIPTS "sfm") -Recurse -File -Force -Filter "*.py" | ForEach-Object {
        $text = [System.IO.File]::ReadAllText($_.FullName)
        foreach ($marker in $SLOT_MARKERS) { if ($text.Contains($marker)) { $hits.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/')); break } }
    }
    $arr = $hits.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    ,@($arr | Where-Object { $SLOT_ALLOWED -notcontains $_ })
}
function K-PackageCopyScan {
    $root = (Get-Item -LiteralPath $SCRIPTS).FullName.TrimEnd('\')
    $expected = @("sfm/mainmenu/ChadChan3D/sfm_master_authority_productionized", "sfm/mainmenu/ChadChan3D/sfm_master_sidecar")
    $arr = @(Get-ChildItem -LiteralPath $SCRIPTS -Recurse -Directory -Force | Where-Object {
        @("sfm_master_authority_productionized", "sfm_master_authority", "sfm_master_sidecar") -contains $_.Name
    } | ForEach-Object { $_.FullName.Substring($root.Length + 1).Replace('\', '/') } | Where-Object { $expected -notcontains $_ })
    [System.Array]::Sort($arr, [System.StringComparer]::Ordinal); ,$arr
}
function K-LogState([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return [ordered]@{ exists = $false } }
    [ordered]@{ exists = $true; bytes = (Get-Item -LiteralPath $Path).Length; sha256 = (S2-Sha $Path) }
}
# Preset library inventory over the whole Characters root (Krystal and Mia libraries): sorted (ordinal)
# relative paths + SHA-256, UTF-8 without BOM, LF (the frozen Write-LibInventory rule, rooted at $CHARACTERS).
function K-LibInventory([string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $CHARACTERS).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rows.Add($_.FullName.Substring($root.Length + 1).Replace('\', '/') + "`t" + (S2-Sha $_.FullName))
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $K_UTF8)
    "LIBRARY INVENTORY WRITTEN: $(Split-Path $Out -Leaf) files=$($arr.Count) sha256=$(S2-Sha $Out)"
}
function K-FixtureUnchanged([string]$E) {
    $fm = Get-Content -LiteralPath (Join-Path $E "fixture_manifest.json") -Raw | ConvertFrom-Json
    $doc = $fm.document
    if (-not (Test-Path -LiteralPath $doc.path -PathType Leaf)) { throw "STOP: the fixture document is missing ($($doc.path))." }
    $now = S2-Sha $doc.path
    if ($now -ne $doc.sha256) { throw "STOP: the fixture document changed ($now, recorded $($doc.sha256)). Report; do not continue." }
    $now
}

# ---- 1. Create the write-once attempt folder (SFM closed). ----
function K-New([string]$Id, [string]$Document) {
    S2-SfmClosed
    $E = K-Attempt $Id
    if (Test-Path -LiteralPath $K_POINTER) { throw "STOP: a K attempt pointer already exists ($K_POINTER). Close that attempt first." }
    if ((S2-Sha $FIXTURE_MANIFEST) -ne $FIXTURE_MANIFEST_SHA) { throw "STOP: K_FIXTURE_MANIFEST.json is not the pinned file." }
    $m = Get-Content -LiteralPath $FIXTURE_MANIFEST -Raw | ConvertFrom-Json
    if (-not $Document -or -not (Test-Path -LiteralPath $Document -PathType Leaf)) { throw "STOP: the fixture document was not found: $Document" }
    $docSha = S2-Sha $Document
    if ($docSha -ne $FIXTURE_DOCUMENT_SHA) { throw "STOP: the fixture document is $docSha, not the pinned $FIXTURE_DOCUMENT_SHA." }
    $doc = [ordered]@{ file_name = (Split-Path $Document -Leaf); path = (Get-Item -LiteralPath $Document).FullName
                       bytes = (Get-Item -LiteralPath $Document).Length; sha256 = $docSha }
    if (-not (Test-Path -LiteralPath $K_ROOT)) { New-Item -ItemType Directory -Path $K_ROOT | Out-Null }
    S2-New $E
    New-Item -ItemType Directory -Path $E | Out-Null
    foreach ($d in "scene_snapshots","library_inventories","preset_readback","logs","restoration") { New-Item -ItemType Directory -Path (Join-Path $E $d) | Out-Null }
    K-WriteJson (Join-Path $E "authority_pins.json") ([ordered]@{
        schema = "cpm-k-authority-pins-v1"; attempt = $Id; wall_time = (K-Now)
        G1 = $m.authority.G1; G2 = $m.authority.G2
        k_candidate_app_sha256 = $CANDIDATE_SHA; probe_sha256 = $PROBE_SHA; fixture_manifest_sha256 = $FIXTURE_MANIFEST_SHA
        driver_lf_sha256 = (K-ShaLf $K_DRIVER_PATH); expected_scripts_inventory_sha256 = $EXPECTED_SCRIPTS_SHA
        generation_tools_lf_sha256 = $GENERATION_TOOLS })
    K-WriteJson (Join-Path $E "fixture_manifest.json") ([ordered]@{
        schema = "cpm-k-attempt-fixture-manifest-v1"; attempt = $Id; wall_time = (K-Now)
        static_manifest_sha256 = $FIXTURE_MANIFEST_SHA; document = $doc })
    K-WriteText (Join-Path $E "operator_steps.md") ([System.IO.File]::ReadAllText($OPERATOR_TEMPLATE, $K_UTF8).Replace("<attempt>", $Id))
    "K ATTEMPT CREATED: $E"
}

# ---- 2. Preflight (SFM closed): identities, contamination, generation baseline. Read-only until all pass. ----
function K-Preflight([string]$Id, [switch]$Owner1Recorded) {
    S2-SfmClosed
    $E = K-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "authority_pins.json"))) { throw "STOP: run K-New first." }
    if (Test-Path -LiteralPath (Join-Path $E "deployment_before.json")) { throw "STOP: preflight already recorded for $Id (write-once)." }
    $pyver = (& python --version 2>&1 | Out-String).Trim()
    if ($pyver -notmatch '^Python 3\.') { throw "STOP: python must be Python 3 for the frozen generation tooling (got '$pyver')." }
    foreach ($p in $GENERATION_TOOLS.GetEnumerator()) {
        $got = K-ShaLf (Join-Path $R ($p.Key.Replace('/', '\')))
        if ($got -ne $p.Value) { throw "STOP: generation tool $($p.Key) is $got, not the frozen $($p.Value)." }
    }
    if ((S2-Sha $APP_SRC) -ne $CANDIDATE_SHA) { throw "STOP: the repository app is not the K candidate $CANDIDATE_SHA." }
    if ((S2-Sha $PROBE_SRC) -ne $PROBE_SHA) { throw "STOP: the repository K probe is not the pinned $PROBE_SHA." }
    $installed = S2-Sha $APP_DST
    if ($installed -ne $CANDIDATE_SHA) { throw "STOP: the installed private app is $installed, not the K candidate $CANDIDATE_SHA." }
    $present = @($ABSENT_BEFORE_DEPLOY | Where-Object { Test-Path -LiteralPath $_ })
    if ($present.Count) { $present | ForEach-Object { "PRESENT: $_" }; throw "STOP: qualification-only harness/pointer/flag residue is present. Do not delete anything; report." }
    $private = @(Get-ChildItem -LiteralPath (Split-Path $APP_DST) -Force | ForEach-Object { $_.Name })
    if (($private -join ",") -ne "SFM_Character_Preset_Manager.py") { throw "STOP: the private module folder holds more than the implementation file ($($private -join ', '))." }
    $docSha = K-FixtureUnchanged $E
    $tmpTag = [System.Guid]::NewGuid().ToString("N")
    $expected = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_k_expected_" + $tmpTag + ".txt")
    $liveInv = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_k_preflight_" + $tmpTag + ".txt")
    try {
        K-ExpectedInventory $expected
        K-ScriptsInventory $liveInv | Out-Null
        K-RequireDiff $expected $liveInv @() "before deployment vs the expected K inventory (accepted Session 4 inventory + K app line)"
        $deps = K-CheckDependencies
        $cpm = K-CpmImplementationScan
        $copies = K-PackageCopyScan
        if (($cpm.Count -or $copies.Count) -and -not $Owner1Recorded) {
            "HISTORICAL FULL-CPM FILES IN THE MENU TREE ($($cpm.Count)):"; $cpm | ForEach-Object { "  $_" }
            "HISTORICAL AUTHORITY/SIDECAR PACKAGE COPIES ($($copies.Count)):"; $copies | ForEach-Object { "  $_" }
            throw "STOP: owner disposition OWNER-1 is required for this accepted historical content (present, inert, never invoked). Do not delete anything."
        }
        if (-not (Test-Path -LiteralPath $CHARACTERS -PathType Container)) { throw "STOP: the CPM preset library root was not found ($CHARACTERS)." }
    } catch {
        foreach ($t in @($expected, $liveInv)) { if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t } }
        throw
    }
    Remove-Item -LiteralPath $expected
    $inv = Join-Path $E "restoration\scripts_inventory_before_deploy.txt"; S2-New $inv
    Move-Item -LiteralPath $liveInv -Destination $inv
    if ((S2-Sha $inv) -ne $EXPECTED_SCRIPTS_SHA) { throw "STOP: the recorded inventory is not the expected K inventory. Report." }
    $git = [ordered]@{ head = ((& git -C $R rev-parse HEAD 2>&1) | Out-String).Trim()
                       tracked_changes = @(& git -C $R status --porcelain --untracked-files=no 2>&1) }
    S2-Prepare (Join-Path $E "generation")
    K-LibInventory (Join-Path $E "library_inventories\library_00_preflight.txt")
    K-WriteJson (Join-Path $E "deployment_before.json") ([ordered]@{
        schema = "cpm-k-deployment-before-v1"; attempt = $Id; wall_time = (K-Now); sfm_running = $false
        repository = $git; python_for_generation_tooling = $pyver
        repository_candidate_sha256 = $CANDIDATE_SHA; installed_app_sha256 = $installed; fixture_document_sha256 = $docSha
        production_dependencies = $deps; scripts_inventory = "restoration/scripts_inventory_before_deploy.txt"
        scripts_inventory_equals_expected = $true
        historical_full_cpm_files = $cpm; historical_package_copies = $copies; owner1_recorded = [bool]$Owner1Recorded
        cpm_log = (K-LogState $CPM_LOG); normalizer_log = (K-LogState $NORMALIZER_LOG)
        generation_baseline = "generation/baseline_inventory.json" })
    "K PREFLIGHT OK: $Id"
}

# ---- 3. Deploy only the probe and the pointer (SFM closed). The CPM app is not touched. ----
function K-DeployProbe([string]$Id) {
    S2-SfmClosed
    $E = K-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "deployment_before.json"))) { throw "STOP: run K-Preflight first." }
    S2-New (Join-Path $E "deployment_after.json")
    if ((S2-Sha $APP_DST) -ne $CANDIDATE_SHA) { throw "STOP: the installed app is not the K candidate $CANDIDATE_SHA." }
    S2-New $PROBE_DST
    if ((S2-Sha $PROBE_SRC) -ne $PROBE_SHA) { throw "STOP: the repository probe is not $PROBE_SHA." }
    Copy-Item -LiteralPath $PROBE_SRC -Destination $PROBE_DST
    if ((S2-Sha $PROBE_DST) -ne $PROBE_SHA) { Remove-Item -LiteralPath $PROBE_DST; throw "STOP: the installed probe hash mismatched; removed." }
    try {
        K-InventoryChecked (Join-Path $E "restoration\scripts_inventory_after_deploy.txt") (Join-Path $E "restoration\scripts_inventory_before_deploy.txt") @("+$PROBE_REL $PROBE_SHA") "after probe deployment"
    } catch { Remove-Item -LiteralPath $PROBE_DST; throw }
    $deps = K-CheckDependencies
    K-WriteJson (Join-Path $E "deployment_after.json") ([ordered]@{
        schema = "cpm-k-deployment-after-v1"; attempt = $Id; wall_time = (K-Now)
        installed_app_sha256 = (S2-Sha $APP_DST); installed_probe_sha256 = (S2-Sha $PROBE_DST)
        production_dependencies = $deps; scripts_inventory = "restoration/scripts_inventory_after_deploy.txt"; pointer = $Id
        cpm_log = (K-LogState $CPM_LOG) })
    K-WriteText $K_POINTER $Id
    "K READY: probe installed; active attempt $Id; installed app $CANDIDATE_SHA unchanged. Start a FRESH SFM process."
}

# ---- Evidence during the run. ----
function K-Library([string]$Id, [string]$Name) {
    $E = K-Attempt $Id
    if ($Name -notmatch '^[A-Za-z0-9_-]+$') { throw "STOP: library inventory name must match [A-Za-z0-9_-]+." }
    K-LibInventory (Join-Path $E "library_inventories\$Name.txt")
}
function K-LibraryCompare([string]$Id, [string]$A, [string]$B) {
    $E = K-Attempt $Id
    $pa = Join-Path $E "library_inventories\$A.txt"; $pb = Join-Path $E "library_inventories\$B.txt"
    if ((S2-Sha $pa) -eq (S2-Sha $pb)) { "LIBRARY IDENTICAL: $A == $B" }
    else { "LIBRARY DIFFERENT: $A != $B"; K-InventoryDiff $pa $pb | ForEach-Object { "  $_" } }
}
# Copy exactly one preset file (wildcard relative to the Characters root) for direct readback.
function K-Readback([string]$Id, [string]$Label, [string]$RelativePattern) {
    $E = K-Attempt $Id
    if ($Label -notmatch '^[A-Za-z0-9_-]+$') { throw "STOP: readback label must match [A-Za-z0-9_-]+." }
    $root = (Get-Item -LiteralPath $CHARACTERS).FullName.TrimEnd('\')
    $hits = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object {
        $_.FullName.Substring($root.Length + 1).Replace('\', '/') -like $RelativePattern })
    if ($hits.Count -ne 1) { throw "STOP: readback pattern '$RelativePattern' matched $($hits.Count) files (exactly one required)." }
    $rel = $hits[0].FullName.Substring($root.Length + 1).Replace('\', '/')
    $dst = Join-Path $E ("preset_readback\" + $Label + ".json"); S2-New $dst
    Copy-Item -LiteralPath $hits[0].FullName -Destination $dst
    K-WriteJson (Join-Path $E ("preset_readback\" + $Label + ".source.json")) ([ordered]@{
        label = $Label; characters_relative_path = $rel; sha256 = (S2-Sha $dst); bytes = (Get-Item -LiteralPath $dst).Length; wall_time = (K-Now) })
    "K READBACK: $Label <- $rel sha256=$(S2-Sha $dst)"
}
# K2 only: publish and activate exact G2 back to back (frozen Session 2 Phase A + Phase B), SFM open and idle.
function K-GenerationSwitch([string]$Id) {
    $E = K-Attempt $Id
    $G = Join-Path $E "generation"
    if (-not (Test-Path -LiteralPath (Join-Path $G "baseline_inventory.json"))) { throw "STOP: no generation baseline for $Id." }
    if (Test-Path -LiteralPath (Join-Path $G "g2_plan_record.json")) { throw "STOP: $Id already performed its one generation transition." }
    S2-PhaseA $G
    S2-PhaseB $G
}
# Copies the cumulative CPM log and the per-run Normalizer log (truncated at each Normalizer run start).
function K-CollectLogs([string]$Id, [string]$Label) {
    $E = K-Attempt $Id
    if ($Label -notmatch '^[A-Za-z0-9_-]+$') { throw "STOP: log label must match [A-Za-z0-9_-]+." }
    $rec = [ordered]@{ label = $Label; wall_time = (K-Now) }
    foreach ($pair in @(@("cpm", $CPM_LOG), @("normalizer", $NORMALIZER_LOG))) {
        if (Test-Path -LiteralPath $pair[1]) {
            $dst = Join-Path $E ("logs\" + $Label + "__" + (Split-Path $pair[1] -Leaf)); S2-New $dst
            Copy-Item -LiteralPath $pair[1] -Destination $dst
            $rec[$pair[0]] = [ordered]@{ file = ("logs/" + (Split-Path $dst -Leaf)); sha256 = (S2-Sha $dst); bytes = (Get-Item -LiteralPath $dst).Length }
        } else { $rec[$pair[0]] = [ordered]@{ exists = $false } }
    }
    K-WriteJson (Join-Path $E ("logs\" + $Label + ".json")) $rec
    "K LOGS COLLECTED: $Label"
}

# ---- Closeout (SFM closed). ----
# Exact G1 restoration with the frozen finalization (K2), or proof that authority was never touched (K1).
function K-Finalize([string]$Id) {
    S2-SfmClosed
    $E = K-Attempt $Id
    $G = Join-Path $E "generation"
    if (Test-Path -LiteralPath (Join-Path $G "g2_plan_record.json")) { S2-Finalize $G } else { S2-VerifyUntouched $G }
}
# Remove the probe and pointer; prove the fixture and the installed app unchanged; seal the live evidence.
function K-RemoveProbe([string]$Id) {
    S2-SfmClosed
    $E = K-Attempt $Id
    $rec = Join-Path $E "restoration\qualification_removal.json"; S2-New $rec
    $actions = New-Object System.Collections.Generic.List[string]
    if (Test-Path -LiteralPath $PROBE_DST) {
        if ((S2-Sha $PROBE_DST) -ne $PROBE_SHA) { throw "STOP: the installed probe is not the pinned file; do not delete. Report." }
        Remove-Item -LiteralPath $PROBE_DST; $actions.Add("removed probe")
    }
    if (Test-Path -LiteralPath $K_POINTER) {
        $pointed = [System.IO.File]::ReadAllText($K_POINTER).Trim()
        if ($pointed -ne $Id) { throw "STOP: the pointer names attempt '$pointed', not '$Id'. Report." }
        Remove-Item -LiteralPath $K_POINTER; $actions.Add("removed pointer")
    }
    $app = S2-Sha $APP_DST
    if ($app -ne $CANDIDATE_SHA) { throw "STOP: the installed app is $app, not the K candidate. K never changes it. Report." }
    $docSha = K-FixtureUnchanged $E
    K-InventoryChecked (Join-Path $E "restoration\scripts_inventory_after_probe_removal.txt") (Join-Path $E "restoration\scripts_inventory_before_deploy.txt") @() "after removing the probe"
    K-WriteJson $rec ([ordered]@{ wall_time = (K-Now); actions = $actions.ToArray(); installed_app_sha256 = $app
                                  fixture_document_sha256 = $docSha
                                  scripts_inventory = "restoration/scripts_inventory_after_probe_removal.txt" })
    K-SealList $E (Join-Path $E "restoration\live_evidence_sha256.txt")
    "K PROBE REMOVED: installed app $app unchanged; fixture unchanged. Next: K-Disposition $Id."
}
function K-SealList([string]$E, [string]$Out) {
    S2-New $Out
    $root = (Get-Item -LiteralPath $E).FullName.TrimEnd('\')
    $rows = New-Object System.Collections.Generic.List[string]
    Get-ChildItem -LiteralPath $root -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($root.Length + 1).Replace('\', '/')
        if ($rel -ne "SHA256SUMS.txt" -and $_.FullName -ne $Out) { $rows.Add((S2-Sha $_.FullName) + "  " + $rel) }
    }
    $arr = $rows.ToArray(); [System.Array]::Sort($arr, [System.StringComparer]::Ordinal)
    [System.IO.File]::WriteAllText($Out, (($arr -join "`n") + "`n"), $K_UTF8)
    "SEALED: $(Split-Path $Out -Leaf) files=$($arr.Count)"
}
# Records the adjudicated verdict and seals the attempt. K never changes the installed CPM; authority must
# already be proven exact G1 and the qualification deployment removed.
function K-Disposition([string]$Id, [ValidateSet("PASS","FAIL","INCONCLUSIVE")][string]$Verdict) {
    S2-SfmClosed
    $E = K-Attempt $Id
    if (-not (Test-Path -LiteralPath (Join-Path $E "restoration\qualification_removal.json"))) { throw "STOP: run K-RemoveProbe first." }
    if (Test-Path -LiteralPath (Join-Path $E "SHA256SUMS.txt")) { throw "STOP: attempt $Id is already sealed." }
    $G = Join-Path $E "generation"
    $restore = Join-Path $G "restore_compare.json"; $untouched = Join-Path $G "untouched_compare.json"
    $cmp = $null; if (Test-Path -LiteralPath $restore) { $cmp = $restore } elseif (Test-Path -LiteralPath $untouched) { $cmp = $untouched }
    if (-not $cmp -or (S2-Json $cmp).exact_match -ne $true) { throw "STOP: exact G1 is not proven (run K-Finalize). Do not start SFM." }
    $rec = Join-Path $E "restoration\disposition.json"; S2-New $rec
    if ((S2-Sha $APP_DST) -ne $CANDIDATE_SHA) { throw "STOP: the installed app is not the K candidate $CANDIDATE_SHA." }
    $expected = Join-Path ([System.IO.Path]::GetTempPath()) ("cpm_k_expected_" + [System.Guid]::NewGuid().ToString("N") + ".txt")
    try {
        K-ExpectedInventory $expected
        K-InventoryChecked (Join-Path $E "restoration\scripts_inventory_final.txt") $expected @() "final"
    } finally { if (Test-Path -LiteralPath $expected) { Remove-Item -LiteralPath $expected } }
    K-WriteJson $rec ([ordered]@{ attempt = $Id; verdict = $Verdict; wall_time = (K-Now); action = "installed CPM unchanged (K never changes it)"
                                  installed_app_sha256 = (S2-Sha $APP_DST); scripts_inventory = "restoration/scripts_inventory_final.txt"
                                  authority_restoration = ((Split-Path $cmp -Leaf)) })
    K-SealList $E (Join-Path $E "SHA256SUMS.txt")
    "K DISPOSITION $($Verdict): installed app $(S2-Sha $APP_DST) unchanged; exact G1; attempt sealed."
}
"K SHELL READY"
