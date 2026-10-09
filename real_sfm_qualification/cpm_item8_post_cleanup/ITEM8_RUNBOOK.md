# CPM handoff §22 item 8 — focused post-cleanup real-SFM qualification (runbook)

**Status: EXECUTED — PASS (attempt `I8A1`, 2026-10-08; results in `ITEM8_EVIDENCE.md` §6).** The
runbook text below is unchanged from the executed checkpoint `d4ad3cf`. The candidate `bfba4d3a…`
remains installed per the PASS disposition. Any later real-SFM campaign needs its own authorization
and a fresh SFM process.

Authoritative design: `cpm/qualification/ITEM8_POST_CLEANUP_REAL_SFM_QUALIFICATION_DESIGN.md`
(owner-approved). This runbook translates its six phases into exact operator steps. It changes no
product, launcher, Normalizer, adapter/projection, shared authority, Master, sidecar or preset
format, and no historical Sessions 1–4 artifact.

**Exact build under test:** `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`
(item-7 candidate, `cpm/app/SFM_Character_Preset_Manager.py`). Sessions 1–4 qualified only
`9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900`; their PASS does not transfer.

| Phase | Scenario |
|---|---|
| A | Exact deployment, fresh-process identity, launch and compatible-window reuse |
| B | Krystal: one ordinary Clothing Fit, native Undo, idle state; title-bar close |
| C | Mia reopen; Body Save/Update/Apply/Undo; Expression Save/Apply/Undo |
| D | Exactly one production Selected Normalizer command with CPM open; continuation without reselection |
| E | Session-2-style Body Save-prompt G1→G2 transition; stale refusal; rebuild; deliberate G2 Save |
| F | Escape teardown; reopen under G2; final close; SFM exit; exact G1 restoration |

**Not repeated:** Session-3 queued-Fit interruption; Session-4 forced rollback/verifier or release
fault injection; R15 foreign-window, notice-lifetime, changed-build or legacy-launch campaigns; a
separate stale Apply; Expression Update; Review/Reclassify; the taxonomy matrix; a second
Normalizer command, All Shots or alternation; benchmarking or stress loops.

## 0. Identities and tools

| Item | SHA-256 |
|---|---|
| Candidate app (repository and, after deployment, installed) | `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` |
| Previously installed app (backed up; restored after FAIL/INCONCLUSIVE) | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` |
| Launcher (unchanged) | `996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51` |
| `cpm_authority_adapter.py` / `cpm_compat_v1_projection.py` (unchanged) | `e96e21b5…` / `9b077a1b…` (full values in the manifest) |
| Production Normalizer (unchanged) | `1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7` |
| Shared authority deployment | the accepted **installed** manifest: 23 + 3 files in `ITEM8_FIXTURE_MANIFEST.json` (Checkpoint A table) |
| Accepted Scripts inventory (Session 4 closeout) | `cefc2b8874c938533b5ded7c194d6a260b49b9faa1404957161cfbc65ccee922` (`cpm_session4/raw/S4A/deploy_after_removal.txt`) |
| G1 Master / sidecar / manifest | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` / `bcd97641…` / `d810d648…` |
| G2 Master / sidecar | `54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7` / `cd370f67…` |
| `CPM_Item8_Probe.py` (qualification-only; deployed for one attempt) | `f503c0abaf63f891c108fd81c726b1101288a2dcf1091bf6a386388be1571257` |
| `ITEM8_GENERATION_DRIVER.ps1` | `8526c6b18464e691ca269f4d0cdefb2d8c4e52d527620e9d32ae369fe9074ec1` |
| `ITEM8_FIXTURE_MANIFEST.json` | `40b51416fb8e742b2512dd973ade07ccd0e618a58ebd6c96e9dd62efc1afeb2b` |
| `item8_evidence_reader.py` | `a3d3bd90e34eb0691e5290a94e599bfab1425afcc11d8312f16c448089444a10` |
| `test_cpm_item8_probe.py` / `test_item8_generation_driver.py` | `c5e6c627f2acbc23cfac7fba5f2edca3ef7f65ec19dbf5f5dd7bc6cf84367f32` / `73a5229658d6535e27252a1152a2e3b64c3806aae23e1ef0ad5e593eade76b3e` |
| `templates/ITEM8_OPERATOR_STEPS_TEMPLATE.md` | `416d4d255b01923b8b73f72dc54b92814ecdb8c5003d7c6f281ce1b7b2bddfb2` |
| Fixture document `testscripts.dmx` (one document, two contexts: Krystal `shot10`, Mia `shot3`; never saved) | `197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f` (14,245,089 bytes) |
| Frozen generation tooling | Session 2 §2.1 block at `0597927` (verbatim inside the driver); `I_Generation_Publisher.py` / `I_Generation_Helper.py` and `tools/sfm_master_sidecar`, pinned (LF) in the driver and manifest |

All values are LF-normalized SHA-256 (this directory is `eol=lf`). The driver re-checks every pin it
uses before acting.

**The probe** (`CPM_Item8_Probe.py`) is observation-only. It never constructs a broker,
authorizes, opens an adapter/provider/view/stage, evaluates readiness or calls
`G18AN_POST_FIT_ACTION_STATE`'s helper. It installs no wrapper, timer, callback, dialog or hook,
writes no CPM log line, and retains no DME/Qt object. It records:
- identity: PID, Python, installed implementation/launcher/probe hashes, private module
  name/origin/loader/state/build, function-global and window ownership, census, run ID, log path;
- authority: runtime origin/build/API, broker identity, leases, unreleased registry, provider
  counters, view cache and views, consumers served, ledger — **before and after** its own reads, with
  the difference (`acquisition_by_probe`);
- CPM state: scope generation and counts, operation/Fit/stage/modal-defer state, stale-rebuild flag,
  watcher, slot; historical provider telemetry (`_SEMANTIC_PROVIDER` and its five counters);
- resources: PrivateUsage, working set, handles, GDI, USER;
- a write-once scene snapshot of the explicit fixture animation sets present in the current shot
  (CPM's own pure readers `p03_model_animsets`, `p01_all_supported_flex_bindings`,
  `binding_snapshot`, plus native Undo enabled/count/description).

Every observation failure is recorded explicitly (`{"observed": false, "error": …}` plus
`errors`), never as zero. A probe snapshot uses CPM's own readers: it is a state observation, **not
an independent semantic oracle** (§6).

## 1. Global rules (fail-closed)

1. **One valid attempt = one fresh SFM process from A1 through SFM exit at F7.** If SFM exits,
   crashes or must be restarted before F7, the attempt is **incomplete/INCONCLUSIVE**: preserve all
   evidence and findings, never splice a second process onto it, and start any replacement attempt at
   S0 with a **new attempt id** (new write-once folder) after the previous attempt's disposition.
2. **Write-once.** Attempt ids `I8A1`, `I8A2`, …; a folder is never reused, edited or deleted. The
   driver refuses to overwrite any record.
3. **Closing the CPM window is not a restart.** Never reload the module, delete `sys.modules`
   entries, or reuse a process that was running before deployment.
4. **Fixture document:** one document, `testscripts.dmx`, serves both fixture contexts: Krystal on
   `shot10`, Mia on `shot3`. It is opened once at A1 and never reopened or saved (answer **No** to
   any save prompt). The only fixture navigation is switching the already-open document from
   `shot10` to `shot3` at C1, with CPM closed, after the B8 closed-idle probe.
5. **No other tools:** no Normalizer except D3; no other authority tool; never open an older CPM build
   (`SFM_CSP_*`, `SFM_Character_Slider_Preset_Tool_*`) — they share the CPM window slot; never run
   `CPM_Session1_Probe`.
6. **No reselection** of the model in Phases D and E. Selecting `mia1` after a reopen (C3, F3) is part
   of opening CPM.
7. **Probes:** run the probe only when no CPM action or dialog is open. At closed or idle checkpoints,
   wait for completion and then about 10 s before probing. Waiting up to 60 s for a completion is an
   observation window, never permission to continue: no completion → STOP.
8. **Undo** only at the named steps (B5, C16, C26, D12), exactly once each, with **Edit > Undo**.
9. **No production patching, no fault injection, no instrumentation** during the campaign.
10. **Operator record:** every step in `operator_steps.md` (step, time, action, visible result,
    evidence filename). Adjudication happens afterwards (§6), never while SFM is being manipulated.
11. Any STOP condition (§7) → halt further campaign operations and follow §7.

## 2. Operator preflight items (before S0)

These facts cannot be established offline; each must be resolved and written into the attempt's
`operator_steps.md` notes before Phase A.

| Item | Requirement |
|---|---|
| **OWNER-1** (owner decision) | The accepted Scripts inventory under which Sessions 1–4 ran contains historical full CPM builds in the menu tree (`sfm/mainmenu/SFM_CSP_G*.py`, `sfm/mainmenu/SFM_Character_Slider_Preset_Tool_*.py`) and historical authority/sidecar package copies (`sfm/gate_r*_deploy/`), listed in `ITEM8_FIXTURE_MANIFEST.json`. Item 8 never invokes them and must not delete them. `I8-Preflight` lists them and STOPs unless `-Owner1Recorded` is passed, which records the owner's written acceptance that they remain present and uninvoked exactly as in Sessions 1–4. Any other disposition (for example relocating them) changes the accepted inventory and needs a revised preparation before any attempt. |
| PRE-2 Fixture document (resolved) | Owner decision: the original qualification document `testscripts.dmx` (in the local SFM sessions folder; SHA-256 `197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f`, 14,245,089 bytes) serves **both** fixture contexts; derivative/variant documents are not used. Its real path is passed to `I8-New` for both parameters, which re-hashes it (must equal the pin). |
| PRE-3 Fixture shots (resolved) | Krystal context = **`shot10`** (holds `krystal20201`, `assaultsuitbody1`, `loinclothbra_chadfix_071`; `shot12` also holds them and is not used). Mia context = **`shot3`** (exactly `foxmccouldwm1` and `mia1`), among 16 film clips, so a sole Selected `shot3` is a proper subset of the Normalizer's project scope. Verified offline read-only; model checksums are confirmed live by the probe (A5, C4). |
| PRE-4 Mia library | `Documents\SFM Character Preset Manager\Characters\mia--2e6533ed1490` exists (`I8-Preflight` checks). No existing preset uses a campaign name (`I8 <attempt> …`). |
| PRE-5 Shells | Windows PowerShell 5.1; `python --version` prints Python 3.x (the frozen generation tooling). |
| PRE-6 Repository | At the item-8 preparation commit or a later commit that leaves every pinned file unchanged; tracked tree clean. |
| PRE-7 Process | No SFM process running. |

Recovered fixture identities (manifest; all in `testscripts.dmx`): on `shot10`, source `krystal20201` (`models/fursonas/starfox/krystal/bodies/krystal2020.mdl`, −1441261258); Fit target `assaultsuitbody1` (…`/cosmetics/assaultsuitbody.mdl`, −791536511); unselected peer `loinclothbra_chadfix_071` (…`/cosmetics/loinclothbra_chadfix_07.mdl`, 480892851); and on `shot3`, `mia1` (`models/annoad/foxbase/mia/mia.mdl`, 1153028609). Qualifying controls (offline-derived from the candidate's own `prod_scope` over the real G1 Master and Mia's 108 recorded literals: 46 Body, 58 Expression, 4 other): **Body `Fat`** (mono), **Expression `SmileClosed`** (mono).

## 3. Shell set-up and attempt creation (S0; SFM closed)

In Windows PowerShell 5.1, outside SFM:

```powershell
. "<repository root>\real_sfm_qualification\cpm_item8_post_cleanup\ITEM8_GENERATION_DRIVER.ps1" `
    -RepoRoot "<repository root>" -Game "<SFM game>"
$A = "I8A1"      # a new id for every attempt
```

Expect `S2 SHELL READY` and `I8 SHELL READY`. Each function prints its `… OK` line or throws `STOP: …`.

| Step | Do | Expect |
|---|---|---|
| S0.2 | `$D = "<local SFM sessions folder>\testscripts.dmx"`; `I8-New $A -KrystalDocument $D -MiaDocument $D` | `I8 ATTEMPT CREATED`: `authority_pins.json`, `fixture_manifest.json` (static manifest + the document's path and SHA-256 under both context names), `operator_steps.md`. Both recorded SHA-256 values must equal `197e6011…`; otherwise STOP (wrong document). |
| S0.3 | Only after OWNER-1 is recorded: `I8-Preflight $A -Owner1Recorded` | `S2 BASELINE OK` (exact production G1 Master/manifest/single sidecar), `LIBRARY INVENTORY WRITTEN`, `I8 PREFLIGHT OK`. Read-only gates first: Python 3; frozen tooling pins; repository candidate, probe and manifest pins; **installed app exactly `9a78fc96…`**; no harness/pointer/flag residue (Session 3/4 harnesses and `ACTIVE_CAMPAIGN.txt`, `CPM_R15_NOTICE_HARNESS.txt`, an item-8 pointer, the G18AN menu copy); private folder holds only the implementation; **Scripts inventory equals the accepted Session 4 closeout inventory**; launcher/adapter/projection/Normalizer and the 23 + 3 package files equal the accepted installed manifest; historical-content scan (OWNER-1); Mia library present. A read-only STOP writes nothing; resolve and rerun. |
| S0.4 | `I8-Deploy $A` | Backs up the installed `9a78fc96…` into `restoration/installed_app_backup.py`; stages the candidate in a temporary sibling, verifies it, replaces the private implementation file only, verifies `bfba4d3a…`; installs only the pinned probe; requires the Scripts inventory to differ from the pre-deployment one by exactly those two lines; re-verifies the dependencies; writes `deployment_after.json` and the pointer `%PUBLIC%\Documents\CPM_Item8\ACTIVE_ATTEMPT.txt`. `I8 DEPLOYED … Start a FRESH SFM process.` |

## 4. Evidence layout (write-once)

Live folder: `%PUBLIC%\Documents\CPM_Item8\<attempt>\`. At closeout it is copied into the repository
as `real_sfm_qualification/cpm_item8_post_cleanup/raw/<attempt>/` (§11).

| Path | Producer | Content |
|---|---|---|
| `authority_pins.json` | `I8-New` | G1/G2 pins, candidate/previous app, probe, manifest, driver, tooling pins |
| `fixture_manifest.json` | `I8-New` | static manifest + the fixture document (path, bytes, SHA-256) recorded under both context names |
| `operator_steps.md` | `I8-New` (template), operator | step, time, action, visible result, evidence filename |
| `deployment_before.json` | `I8-Preflight` | repository HEAD and tracked changes, installed identities, dependencies, inventory equality, historical content, OWNER-1 flag, log states |
| `deployment_after.json` | `I8-Deploy` | installed candidate/probe, backup, dependencies, inventory |
| `probe.jsonl` | probe | one record per run, `seq` 1..n, append-only |
| `scene_snapshots/probe_NNNN.json` | probe | fixture-set snapshot + Undo for that `seq` (hash in the probe record) |
| `library_inventories/*.txt` | `I8-Library`, `I8-Preflight`, `I8-GenerationSwitch` | Mia library: relative path + SHA-256 (frozen `Write-LibInventory`) |
| `preset_readback/<label>.json` + `.source.json` | `I8-Readback` | exact copy of the written preset + its library path and SHA-256 |
| `generation/` | frozen `S2-*` functions | `g1_source.txt`, `baseline_inventory.json`, Phase A/B records, `post_switch_inventory.json`, finalization or untouched records, `restore_compare.json` / `untouched_compare.json` |
| `logs/` | `I8-CollectLogs` | copies of the CPM log and the Normalizer log + their hashes |
| `restoration/` | driver | Scripts inventories (before deploy, after deploy, after qualification removal, final), app backup, `qualification_removal.json`, `live_evidence_sha256.txt`, `disposition.json` |
| `SHA256SUMS.txt` | `I8-Disposition` | SHA-256 of every other file; written last (seals the attempt) |

The probe refuses to write when no attempt is active, the attempt is not deployed, `probe.jsonl`
is truncated, or the attempt is sealed.

## 5. Operator procedure

**P** = Scripts > ChadChan3D > `CPM_Item8_Probe`. Its console line must read
`CPM_ITEM8_PROBE seq=<n> attempt=<attempt> impl_is_candidate=True …`; write `seq` in the step
row. `REFUSED`, `impl_is_candidate=False`, or a non-empty `errors=[…]` → STOP (observability).
Launcher console lines read `[ChadChan3D CPM launcher] outcome=… code=…`.

### Phase A — fresh-process verification (`testscripts.dmx`, `shot10`)

| Step | Do | Visible expectation / STOP |
|---|---|---|
| A1 | Start SFM fresh. Open `testscripts.dmx` (**File > Open**). Make **`shot10`** the current shot (in the Clip Editor, move the playhead into `shot10`), before any probe or CPM action. | `testscripts.dmx` open; `shot10` current; `krystal20201`, `assaultsuitbody1`, `loinclothbra_chadfix_071` listed in the Animation Set Editor. Otherwise STOP. |
| A2 | **P** (before CPM). | Probe line with `module=None` (no private module yet) and `impl_is_candidate=True`. |
| A3 | Scripts > ChadChan3D > SFM_Character_Preset_Manager. | One CPM window; console `outcome=created code=create`. |
| A4 | Select `krystal20201`; wait for the Body/Expression/Review counts. | Counts appear; no warning. |
| A5 | **P**. | — |
| A6 | Click the launcher again. | The same window comes forward; console `outcome=reused code=reuse`. A second window, a notice or `refused` → STOP. |
| A7 | **P**. | — |

### Phase B — one ordinary Fit and Undo

| Step | Do | Visible expectation / STOP |
|---|---|---|
| B1 | Clothing Fit tab: check **only** `assaultsuitbody1` (under nearby). | Only that target checked. |
| B2 | **P** (pre-Fit: source, target, peer, Undo). | — |
| B3 | **Fit Selected to Model**. Wait for completion. | A completion status such as "1 item updated."; no dialog. A failure dialog or "Clothing Fit could not …" → STOP. An all-already-matched result → STOP (INCONCLUSIVE: no changed state). |
| B4 | **P** (post-Fit). | — |
| B5 | **Edit > Undo** once. Confirm `assaultsuitbody1` looks as before the Fit. | Visual restoration. Otherwise STOP. |
| B6 | **P**. | — |
| B7 | Close CPM with the title-bar **X**. Settle. | Window gone. |
| B8 | **P** (closed). | — |

### Phase C — Mia reopen, Body and Expression

| Step | Do | Visible expectation / STOP |
|---|---|---|
| C1 | With CPM still closed, make **`shot3`** the current shot of the already-open `testscripts.dmx` (in the Clip Editor, move the playhead into `shot3`). Do **not** reopen or save the document. | `shot3` current; `foxmccouldwm1` and `mia1` listed in the Animation Set Editor. Otherwise STOP. |
| C2 | **P** (closed, `shot3`). | — |
| C3 | Launcher; select `mia1`; wait for the counts. | `outcome=created code=create`; counts appear. |
| C4 | **P** (reopened). | — |
| C5 | Set **Fat** to **0.50** (ordinary SFM slider entry). | — |
| C6 | **P**; shell `I8-Library $A library_C01_before_body_save`. | — |
| C7 | Body tab: **Save New**, name `I8 <attempt> C BODY`, OK. | "Body Preset saved." |
| C8 | Shell: `I8-Readback $A C_body_save "Body Presets/I8 $A C BODY--preset-*.json"`; `I8-Library $A library_C02_after_body_save`. | `I8 READBACK`, `LIBRARY INVENTORY WRITTEN`. |
| C9 | Set **Fat** to **0.80**; **P**. | — |
| C10 | Select preset `I8 <attempt> C BODY` → **Update Preset** → confirm. | `"I8 <attempt> C BODY" updated.` |
| C11 | Shell: `I8-Readback $A C_body_update "Body Presets/I8 $A C BODY--preset-*.json"`; `I8-Library $A library_C03_after_body_update`. | — |
| C12 | Set **Fat** to **0.20**. | — |
| C13 | **P** (pre-Apply). | — |
| C14 | With `I8 <attempt> C BODY` selected: **Apply Preset**. | "Body Preset applied." ("Already matches this preset." → STOP: no-op). |
| C15 | **P** (post-Apply). | — |
| C16 | **Edit > Undo** once. | Fat visibly back. |
| C17 | **P**. | — |
| C18 | Set **SmileClosed** to **0.60**. | — |
| C19 | **P**; shell `I8-Library $A library_C04_before_expr_save`. | — |
| C20 | Expression tab: **Save New**, name `I8 <attempt> C EXPR`, OK. | "Expression saved." |
| C21 | Shell: `I8-Readback $A C_expr_save "Expressions/I8 $A C EXPR--preset-*.json"`; `I8-Library $A library_C05_after_expr_save`. | — |
| C22 | Set **SmileClosed** to **0.00**. | — |
| C23 | **P** (pre-Apply). | — |
| C24 | With `I8 <attempt> C EXPR` selected: **Apply Preset**. | "Expression applied." |
| C25 | **P** (post-Apply). | — |
| C26 | **Edit > Undo** once. | SmileClosed visibly back. |
| C27 | **P** (idle). | — |

### Phase D — one Normalizer command and continuation

| Step | Do | Visible expectation / STOP |
|---|---|---|
| D1 | Leave CPM open on Mia's existing scope. **P**. | — |
| D2 | Shell: `I8-Library $A library_D01_before_normalizer`. | — |
| D3 | In the Clip Editor, select **only `shot3`** (it must be the **sole** Selected shot). Then Scripts > ChadChan3D > `Rebuild_Control_Groups_Normalizer`: **Rebuild Selected Shots**. Complete its normal prompts; respect its admission guard. Wait for its final completion report. Run it **once**. | Completion report for one shot (`shot3`). Any other shot selected, or a refusal by its admission guard → STOP (adjudicate). |
| D4 | Shell: `I8-CollectLogs $A D_after_normalizer`. | `I8 LOGS COLLECTED`. |
| D5 | **P**. | — |
| D6 | Return to the **same** CPM window and scope, **without reselecting**. Set **Fat** to **0.30**. | — |
| D7 | **P** (pre-Apply). | — |
| D8 | Select `I8 <attempt> C BODY` → **Apply Preset**. | "Body Preset applied." A stale-authority/stale-scope refusal → STOP (FAIL); any other refusal → STOP (adjudicate). |
| D9 | **P** (post-Apply). | — |
| D10 | Body tab: **Save New**, name `I8 <attempt> D BODY`, OK. | "Body Preset saved." |
| D11 | Shell: `I8-Readback $A D_body_save "Body Presets/I8 $A D BODY--preset-*.json"`; `I8-Library $A library_D02_after_save`. | — |
| D12 | **Edit > Undo** once (undoes the D8 Apply; Save makes no Undo entry). | Fat visibly back. |
| D13 | **P** (idle). | — |

### Phase E — Save-prompt generation transition

| Step | Do | Visible expectation / STOP |
|---|---|---|
| E1 | **P** (healthy G1 scope, idle). | — |
| E2 | Shell: `I8-Library $A library_E1_before_prompt`. | — |
| E3 | Body tab: **Save New**; type `I8 <attempt> E STALE`. **Leave the prompt open; do not confirm.** | Prompt open. |
| E4 | Shell, prompt still open, no SFM interaction: `I8-GenerationSwitch $A`. | `S2 PHASE A OK`, `S2 G2 ACTIVE OK`, `LIBRARY INVENTORY WRITTEN` (`library_E2_g2_active_prompt_open`). Any STOP line → §7 R3 (do **not** confirm the prompt). |
| E5 | Confirm the already-open prompt (**OK**). | Dialog **Can't save preset** — "Preset could not be saved. Nothing was saved." **OK**. Do not reselect. Wait (≤ 60 s) for the counts to return. No refusal, a success, another error, or no counts → STOP. |
| E6 | **P** (after the automatic rebuild). | — |
| E7 | Shell: `I8-Library $A library_E3_after_refusal`; `I8-LibraryCompare $A library_E1_before_prompt library_E3_after_refusal`; `I8-LibraryCompare $A library_E2_g2_active_prompt_open library_E3_after_refusal`. | Both `LIBRARY IDENTICAL`. `LIBRARY DIFFERENT` → STOP. |
| E8 | **Save New**, name `I8 <attempt> E G2`, OK. | "Body Preset saved." A warning or error → STOP. |
| E9 | **P**. | — |
| E10 | Shell: `I8-Readback $A E_g2_save "Body Presets/I8 $A E G2--preset-*.json"`; `I8-Library $A library_E4_after_g2_save`. | — |

### Phase F — Escape teardown, reopen, exit, restoration

| Step | Do | Visible expectation / STOP |
|---|---|---|
| F1 | Focus CPM; press **Escape**. | Window closes. |
| F2 | Settle; **P** (closed). | — |
| F3 | Launcher; select `mia1`; wait for the counts. | `outcome=created code=create`; counts appear (G2 scope). |
| F4 | **P** (reopened under G2). | — |
| F5 | Leave idle about 30 s; **P**. | — |
| F6 | Close CPM with the title-bar **X**; settle; **P** (final teardown). | — |
| F7 | Exit SFM **without saving**. | SFM process gone. |
| F8 | Shell: `I8-CollectLogs $A F_final`; `I8-Finalize $A`; `I8-RemoveQualificationDeployment $A`. | `I8 LOGS COLLECTED`; `S2 RESTORED EXACT G1`; `I8 QUALIFICATION DEPLOYMENT REMOVED … Do not start SFM before I8-Disposition.` Otherwise §7 R5/R6. |
| F9 | Adjudication (§6, reviewer). Then `I8-Disposition $A -Verdict PASS` / `FAIL` / `INCONCLUSIVE`. | §10 policy applied; `SHA256SUMS.txt` written; attempt sealed. |

## 6. Adjudication (reviewer, after F8; never during SFM manipulation)

Sources: `probe.jsonl` + snapshots, `logs/F_final__SFM_CSP_G18AN_SaveNewCopy.log` (the excerpt
after `deployment_before.json`'s recorded CPM-log size), `logs/D_after_normalizer__sfm_rebuild_control_groups.txt`,
library inventories, preset readbacks, `generation/`, `restoration/`, `operator_steps.md`.

Mechanical helper (offline, read-only): `item8_evidence_reader.py summary <attempt> --log <excerpt>`,
`snapshot-diff <attempt> <seq-a> <seq-b> [animset]`, `library-diff <before> <after> --allow …`,
`readback <preset.json> <literal>`, `verify-sums <attempt>`. Its event table matches only the
candidate's current formats; it flags historical `CLOTHING_FIT_RESULT=PASS` and the item-7-removed
`PROD_PERF`/`ASTRA_PERF`/`PROD_ACTION_TIMING`/`PROD_MODELS` candidate dump instead of counting them.
The current Fit result begins `CLOTHING_FIT_RESULT generation=…`; its callback `generation` is
distinct from authority `gfit`. `MODEL_RENDER_BEFORE_SCOPE`→`MODEL_RENDER_AFTER_SCOPE`
(`PROD_RESOURCE` labels) may be recorded descriptively only.

**No PASS rests solely on a production "verified" flag.** Each changed-state claim pairs a probe
snapshot difference with the preselected value, the direct preset-file readback, an unchanged-peer
comparison and the operator's native-Undo observation.

**Every checkpoint (all P#):** identity (`identity_check`): Python 2.7.5, installed implementation and
module build `bfba4d3a…`, launcher `996ca483…`, private origin/loader/state `ready`, module
dictionary ≠ `__main__`, function globals private, no CPM names in `__main__`, no other module
defining CPM; `acquisition_by_probe` determinable and false; historical provider inactive
(`_SEMANTIC_PROVIDER is None`, five counters 0); no observation errors.

**Idle checkpoints** (A5, A7, B6, B8, C2, C4, C17, C27, D1, D5, D13, E1, E6, E9, F2, F4–F6):
outstanding leases 0, unreleased registry 0, open providers 0; no operation, Fit, running stage or
deferred Fit continuation; census as expected (open: 1 ProdWindow / 1 watcher; closed: 0 / 0, empty
slot). Detached bounded views may remain cached — idle does not mean an empty view cache.

| Phase | PASS requires (all) |
|---|---|
| **A** | Operator record: `testscripts.dmx` (SHA-256 `197e6011…` in `fixture_manifest.json` under both names), `shot10` current. A5 snapshot: `krystal20201`, `assaultsuitbody1`, `loinclothbra_chadfix_071` present with matching model and checksum. A2: no private module; the canonical runtime state recorded as found (not constructed by the probe). A5: one owned window, one watcher; `PROD_R15_MODULE … build_sha256=bfba4d3a…`, `G18AN_RUN`; healthy scope with `PROD_PROVIDER_HEALTH … sha256=u'ac45e5c1…'`; canonical runtime origin = the deployed menu package. A7 vs A5: same PID, module, class, `StartProdTool`, run ID, window id and scope generation; `PROD_R15_WINDOW_REUSED` once; broker provider opens/closes unchanged between A5 `broker_after` and A7 `broker_before` (the second click acquired nothing). |
| **B** | Snapshot diff B2→B4: `assaultsuitbody1` changed (≥ 1 literal); `krystal20201` and `loinclothbra_chadfix_071` unchanged; Undo count +1. Log: `PROD_CPM_OPERATION_AUTHORIZED operation=u'Clothing Fit' sha256=ac45e5c1…`; `PROD_CPM_FIT_STAGE_OPEN index=0 gfit=ac45e5c1… literals=<n>`; `CLOTHING_FIT_STAGE=PASS … committed=True`; exactly one `PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True`; `CLOTHING_FIT_RESULT generation=… selected=1 … failed=0 unattempted=0` with one changed or partial-changed target; mappings/warnings explained against the pinned fixture (historically 34 literals, 26 mappings, 7 unmatched-target warnings — explanatory, not demanded). B6 snapshot equals B2 for all three sets and Undo is back to the B2 state. B4/B6 idle (stage released). B8: empty slot, census 0/0, `PROD_CLOSE_REQUEST` then `PROD_CLOSE_FINALIZED=True`. |
| **C** | C1/C2: `shot3` current in the same open document (no reopen, no save); C4 snapshot: `mia1` present with matching model and checksum. C4: same PID/module/class/run ID as Phase A, **new** window id, 1/1. Readbacks: `C_body_save` Fat = C6 snapshot value; `C_body_update` Fat = C9 snapshot value; `C_expr_save` SmileClosed = C19 value (reader `readback`, tolerance 1e-5). Library diffs: C01→C02 = one new `Body Presets/I8 <attempt> C BODY--preset-*.json` (+ allowed `character.json`/`.bak`); C02→C03 = that preset (+ its `.bak`, `character.json`/`.bak` allowed); C04→C05 = one new `Expressions/I8 <attempt> C EXPR--preset-*.json` (+ profile files). Apply: C13→C15 diff on `mia1` = exactly `Fat`, value = the update readback; Undo: C17 equals C13 (all literals) and the Undo count returns. Expression: C23→C25 diff = exactly `SmileClosed` = save readback; C27 equals C23. Log: `PROD_SAVE=PASS`, `PROD_UPDATE=PASS`, two `PROD_APPLY outcome='committed'` (`changed_sides`≥1), every authorization `sha256=ac45e5c1…`. C17/C27 idle. Each deliberate change exceeds 0.1 (no no-op). |
| **D** | Normalizer log: `scope_mode=SELECTED_SHOTS scope_shots=1`, `CONTEXTUALIZER_SCOPE_SHOT_NAMES = [u'shot3']`, `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`, `PRODUCTION_CONTEXTUALIZER = PASS`, `mem_ok=True` at every checkpoint, live Master G1, no CPM `PROD_` lines. D5 vs D1: same broker id (one canonical broker serves both), `consumers_served` includes `cpm_compat_v1` and `normalizer_compat`, same module/window/run ID/scope generation, idle. Between D1 and D13 the CPM log has no `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED`, no `PROD_CPM_STALE_GENERATION_REBUILD*`, no new `scope-begin` (no reselection). D7→D9 diff = exactly `Fat`, value = the Phase C update readback; `D_body_save` Fat = D9 value; D01→D02 = one new `I8 <attempt> D BODY` preset (+ profile files); D13 equals D7. |
| **E** | Valid run: E1 scope G1; between E4's activation and the E5 refusal there is no `PROD_CPM_STALE_GENERATION_REBUILD*` and no scope rebuild (otherwise INCONCLUSIVE). `g2_activation_record.json` proves `ac45e5c1…`→`54413b6c…`; `post_switch_inventory.json` is exact G2. The Save operation was open before the switch (`PROD_OPERATION_BEGIN … 'Save Current Body'` before E4); the prompt returned (`PROD_RESOURCE label=u'Q2_SAVE_POST_CONFIRM'`); then `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED operation=u'Save Preset' reason=u'generation-mismatch'`; no `PROD_SAVE=` and no durable phase for it; its `PROD_OPERATION_END … durable_commit=None`. `library_E1`, `library_E2` and `library_E3` byte-identical; no `E STALE` file. E1→E6 snapshot diff empty and Undo count unchanged (no scene mutation, no Undo item). After the refusal: `PROD_CPM_STALE_GENERATION_REBUILD_SCHEDULED`, `PROD_CPM_STALE_GENERATION_REBUILD`, exactly one automatic scope publication with `PROD_PROVIDER_HEALTH … sha256=u'54413b6c…'` and `scope-ready`; E6 scope G2, same window; no further `Save Current Body` before E8 (no replay). E8: `PROD_CPM_OPERATION_AUTHORIZED operation=u'Save Preset' sha256=54413b6c…`, `PROD_SAVE=PASS … name=u'I8 <attempt> E G2'`; E3→E4 = exactly one new `I8 <attempt> E G2` preset + allowed `character.json`/`.bak`, nothing else; E10 readback valid. E6/E9 idle. |
| **F** | F2: Escape teardown complete (empty slot, 0/0, `PROD_CLOSE_FINALIZED=True`), idle. F4: same PID/module/class/run ID, **new** window id, 1 ProdWindow / 1 watcher, healthy G2 scope. F5/F6 idle; F6 closed 0/0. `restore_compare.json` and `finalization_record.json` `exact_match: true` (`S2 RESTORED EXACT G1`). Qualification-only deployment removed with the exact expected Scripts difference. |

**Resources (design §9):** record `resources` at A5, A7, B4, B6, B8, C4, C17, C27, D1, D5, E6, F2,
F4, F5, F6; separate CPM scope/cache accounting, PrivateUsage, working set, handles/GDI/USER, the
Normalizer's known process-retained effects (D1→D5) and fixture loading (C1). No MB threshold and no
requirement to return to startup. Material: persistent duplicate objects, non-zero ownership, repeated
acquisition while idle, or an unexplained growing retention pattern across the closed/reopened states.

## 7. STOP and recovery

**STOP** halts further campaign operations; adjudication later decides FAIL or INCONCLUSIVE.
Mandatory STOP conditions:
- candidate/deployment hash mismatch, or an unexpected changed dependency;
- historical provider activity;
- non-zero idle ownership;
- a stale operation mutating or persisting;
- automatic replay after a refusal;
- failed native Undo restoration;
- persistence/readback mismatch;
- Fit-stage leak or release anomaly;
- failed intended post-Normalizer continuation;
- duplicate module/window/watcher ownership;
- material unexplained resource accumulation;
- insufficient required observability (probe `REFUSED`, observation errors, missing snapshot);
- incomplete G1 restoration.

| Case | Signal | Action |
|---|---|---|
| R0 | STOP inside `I8-New`/`I8-Preflight` | SFM stays closed. Read-only gates write nothing: resolve the cause and rerun. A STOP from `S2-Prepare` (authority not exact G1): do not start SFM; report. |
| R1 | STOP inside `I8-Deploy` | Do not start SFM. `I8-RemoveQualificationDeployment $A`, then `I8-Disposition $A -Verdict INCONCLUSIVE` (restores `9a78fc96…`). Report. |
| R2 | Any STOP while SFM is running, before E4 | Note the time. Click **OK**/**Cancel** only on a dialog named in the step (Cancel an open Save prompt). If no CPM dialog is open, one **P** for evidence. No further CPM action. Close CPM and exit SFM without saving (end the process if it hangs). Then F8 and F9. |
| R3 | A STOP line from `I8-GenerationSwitch` (E4) | **Do not confirm the prompt**; Cancel it. Close CPM and exit SFM without saving. `I8-CollectLogs`, `I8-Finalize` (restores exact G1 using whichever records exist), `I8-RemoveQualificationDeployment`, adjudication, `I8-Disposition`. |
| R4 | SFM crashes, exits or must restart before F7 | The attempt is incomplete/INCONCLUSIVE. Never restart SFM for this attempt. F8 and F9 (`INCONCLUSIVE` unless an observed product failure makes it FAIL). Preserve every finding. A replacement attempt starts at S0 with a new id. |
| R5 | `I8-Finalize` does not print `S2 RESTORED EXACT G1` / `S2 UNTOUCHED` | Do not start SFM. Do not edit the Master or authority folder by hand. Preserve the attempt; report. |
| R6 | `I8-RemoveQualificationDeployment` / `I8-Disposition` STOP (unexpected Scripts difference, wrong installed app) | Do not delete anything; do not start SFM. Preserve; report. These steps write no evidence when refused and can be rerun once resolved. |

Do not patch production logging or implementation during the campaign.

## 8. PASS / FAIL / INCONCLUSIVE / STOP

- **PASS:** the scenario was exercised on the pinned bytes, its required observations exist, and
  all acceptance conditions hold.
- **FAIL:** observed product behaviour violates the contract (for example stale persistence,
  incorrect Apply, failed Undo, ownership leakage, namespace contamination).
- **INCONCLUSIVE:** the proposition was not validly exercised or observed (wrong/missing fixture;
  a no-op instead of the required changed Apply/Fit; an early G2 rebuild before the intended stale
  boundary; a missing snapshot or unreadable required state; operator contamination; insufficient
  retained observability).
- **STOP:** an execution action — halt on any safety, identity, restoration or evidentiary failure;
  adjudication then decides FAIL or INCONCLUSIVE.

An attempt whose SFM process exits, crashes or must restart before F7 is incomplete/INCONCLUSIVE.
An observed product failure in it is preserved as a finding; the classification never erases it.
Item 8 is PASS only when **all six phases PASS within one valid attempt**, with independently
reviewable raw evidence, no unresolved product failure or observation gap, exact authority
restoration, completed deployment closeout, and explicit disposition of every anomaly.

## 9. Known Fit release observation (carried from Session 4; not repaired)

- One exception path in `fit_stage` releases the stage with a bare `release()`, without its own
  `PROD_CPM_FIT_STAGE_RELEASED` event, and discards the result.
- A raising success-path release could theoretically lead to another `release()` attempt.
- Session 4 observed exactly one successful release in each of its exercised injected stages.

Item 8 observes the **ordinary** Fit path's actual stage state and retained events only. It does
not prove the exceptional path repaired, and must not instrument, inject or repair it. Any observed
leak, release error or credible double-release evidence is a **STOP** requiring separate adjudication.

## 10. Deployment policy (applied by `I8-Disposition`, SFM closed)

**After PASS** (`-Verdict PASS`): the exact qualified candidate
`bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` **remains installed**; only the
qualification-only probe and pointer were removed (F8); the final Scripts inventory must equal the
accepted inventory except the implementation line. Record that the candidate remains installed. K may
be considered only after item-8 adjudication; K, if authorized, starts in a **fresh SFM process**.
This does not decide L's final installation layout.

**After FAIL or INCONCLUSIVE** (`-Verdict FAIL` / `INCONCLUSIVE`): with SFM closed, the installed
app is restored to `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` from the
attempt's verified backup (temporary sibling + replacement), its full hash verified, and the final
Scripts inventory must equal the accepted inventory exactly. All candidate evidence and findings are
preserved.

In both cases exact G1 must already be proven (`restore_compare.json` or `untouched_compare.json`
exact). Campaign presets are archived in the evidence (readbacks, inventories); campaign-owned library
entries are restored or removed only from recorded state, after confirming no unrelated intervening
change, under a separate explicit closeout step.

## 11. Closeout into the repository

After disposition: copy the sealed attempt folder into
`real_sfm_qualification/cpm_item8_post_cleanup/raw/<attempt>/`, redacting only the SFM install,
user-profile and Public-profile path prefixes (`<SFM_GAME>`, `<USERPROFILE>`, `<PUBLIC>`), with a
`raw/MANIFEST.md` recording each file's original, excerpt and committed SHA-256 (the Session 4
practice). Record actual results in `ITEM8_EVIDENCE.md` and the Ledger (design §12 wording). Never
edit a historical session artifact.

## 12. Offline preparation qualification

Commands (from this directory, `PYTHONDONTWRITEBYTECODE=1`):

```text
<python 3.10>    test_cpm_item8_probe.py --phase=run      (run first: publishes the temp G1 fixture)
<embedded 2.7.5> test_cpm_item8_probe.py --phase=run
<python 3.10>    test_item8_generation_driver.py
```

| Suite | Interpreter | Qt | Result |
|---|---|---|---|
| `test_cpm_item8_probe.py --phase=run` | Python 3.10.6 | model | **172/172 ALL PASS** (with the live fixture-document check) |
| `test_cpm_item8_probe.py --phase=run` | embedded Python 2.7.5 | real PySide/Qt 4.8 + model | **231/231 ALL PASS** |
| `test_item8_generation_driver.py` | Python 3.10.6 + Windows PowerShell 5.1 | — | **76/76 ALL PASS** |

Coverage (check groups; 2.7.5 adds the real-Qt children):
- **pins (18):** candidate `bfba4d3a…`; launcher; previous app restorable from git (`9d405c8`); design,
  manifest and Session 2 G1/G2 identities; repository Master = G1 and G1+LF = G2; probe/reader/driver
  pins equal the actual files; accepted inventory pin; manifest dependencies equal both the accepted
  installed inventory and their repository sources; generation tooling pins equal the repository and
  the driver and are unchanged since `0597927`.
- **fixture document (6 static; 5 live under 3.10):** one physical document serves both named contexts
  with distinct shots (Krystal `shot10`, Mia `shot3`), the Normalizer's sole Selected shot is the Mia
  shot, the manifest pins the document without a workstation path, and the driver accepts one path for
  both; live (`--fixture-document=… --dmxconvert=…`, temporary copy only): pinned SHA-256 and size,
  `shot10` holds the Krystal triple, `shot3` is exactly `foxmccouldwm1` + `mia1`, 16 film clips, source
  unchanged.
- **fixtures (8) and classification (6):** fixture identities equal the Session 4 harness constants,
  the probe's fixture table and `SESSION3_RUNBOOK.md`; Mia's 108 literals partition into 46/58/4;
  `Fat`/`SmileClosed` are mono and correctly classified; planned changes exceed 0.1; the
  classification is re-derived through the candidate's own `prod_scope` over the real published G1
  Master (healthy, G1, no miss/conflict, idle afterwards).
- **probe static (12):** ASCII/LF; one function + guarded call + delete, no module docstring;
  compiles; no forbidden name (broker construction/acquisition/release, authorization, adapter/stage,
  readiness, `G18AN_POST_FIT_ACTION_STATE`, logging, timers/dialogs/connect/`setattr`, Undo/mutation,
  file removal); no dynamic code; CPM calls limited to the four pure scene readers; broker calls
  limited to read accessors; no timing/notice/harness mode; no removed-event dependency; exactly one
  write-once and one append write site; the reused CPM readers' call closure is pure.
- **reader (51) and candidate (2):** the reader parses lines produced by the candidate's own format
  strings for every retained event it uses; every reader tag exists in the candidate; no removed tag is
  current; the candidate has no removed events and one current Fit-result format; the real Session 4
  log's `CLOTHING_FIT_RESULT=PASS` and `PROD_PERF`/`ASTRA_PERF` lines are flagged, never counted;
  preset readback through the candidate's own `p02_saved_value_record` (mono/stereo, missing →
  error); library footprint rules (allowed, collision suffix, Expressions folder, extra change,
  missing preset, removal); idle rules (zero idle, non-zero lease, unobserved never idle, no broker,
  running stage, probe acquisition); snapshot hash/tamper, `seq` gaps, `SHA256SUMS` verify/tamper.
- **probe runtime (per Qt mode; lifecycle 52, pin_mismatch 5, real_broker 7):** the actual probe run
  as SFM runs a menu script (`__main__` dictionary) beside the actual launcher and candidate
  `ProdWindow`: refusal with no pointer / undeployed attempt / truncated log / sealed attempt (nothing
  written); before launch (no module, runtime absent recorded explicitly, no acquisition, empty slot);
  after launch (exact module identity, owned window with private globals, census, idle state,
  historical inactive, only read accessors called on a strict broker, before/after counters, no
  acquisition, no timer/dialog constructed, module namespace/window/QApplication/`__main__`
  unchanged, no CPM or authority module imported); explicit fixture snapshot only, values from the
  candidate's `binding_snapshot`, Undo facts, **no DME object retained** (weak references dead);
  identity-mismatch reporting; busy state reported, never acted on; explicit failures (broker read,
  scene, resources, missing broker) never zero; write-once snapshot and append-only log; a different
  installed build (item-6 `1e866871…`) reported and rejected by the reader; the **real**
  shared-package broker unchanged by the probe (counters, diagnostics, ledger), idle and canonical
  origin recorded.
- **driver (76):** frozen block byte-identical to `SESSION2_RUNBOOK.md` at `0597927` except the two
  placeholders, not redefined, no generation-tool calls outside it; ASCII/LF; parses in Windows
  PowerShell 5.1. Sandbox end to end with the real previous app, launcher, adapter, projection,
  Normalizer, shared package and sidecar-reader bytes and real G1 published by the real publisher:
  write-once attempt creation (pins, document hashes, operator template); read-only preflight STOPs
  that write nothing and leak nothing (OWNER-1, harness residue, old campaign pointer, changed
  dependency, unexpected script named, extra private-folder file); preflight records and exact G1
  baseline; deployment by temporary sibling + replacement with the exact two-line Scripts difference;
  single active attempt; the frozen G1 → exact G2 switch; library identity; readback; log collection;
  frozen exact-G1 finalization with the G2 sidecar removed; ordering gates; an unexpected Scripts
  change refusing qualification removal without spoiling the retry; live-evidence seal;
  INCONCLUSIVE disposition restoring `9a78fc96…` with the inventory equal to the accepted one; PASS
  disposition in a second attempt (one document passed for both fixture contexts) keeping `bfba4d3a…` (only the implementation line differs) with the
  untouched-authority proof; sealed attempts verified by the reader; a later preflight refusing while
  the candidate remains installed.

Defects found and fixed during preparation (tooling only): `File.Replace` received `""` for a
`$null` backup path (now `[NullString]::Value`); PowerShell's case-insensitive names made the
inventory comparison coerce its maps into the `[string]` parameters, so every inventory comparison
compared nothing (renamed; negative tests now prove each comparison can fail); preflight and later
inventory checks wrote write-once files before refusing (now temp-then-move, so refused steps can be
rerun).

Mocks cannot qualify real DME objects, the installed deployment, the real broker under SFM or the
operator steps; those are the live campaign.
