# CPM handoff §22 item 8 — focused post-cleanup real-SFM qualification (evidence)

**Status: EXECUTED — PASS (attempt `I8A1`, 2026-10-08).** Phases A–F all passed in one fresh SFM
process (PID 36912) from checkpoint `d4ad3cf`. The disposition was PASS: candidate `bfba4d3a…` remains
installed, the qualification-only probe and pointer were removed, and the live authority is exact G1.
§1–§5 are the preparation record; §6 holds the live results.

Design: `cpm/qualification/ITEM8_POST_CLEANUP_REAL_SFM_QUALIFICATION_DESIGN.md` (owner-approved).
Runbook: `ITEM8_RUNBOOK.md`.

## 1. Exact build and starting state

| Item | Value |
|---|---|
| Preparation checkpoint (HEAD = `origin/master` before preparation) | `0e6a1e3c58cd40f9489ec80e368d10b788a25c84`; no tracked modifications |
| Candidate under test | `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5` (unchanged by item 8 preparation) |
| Installed app at preparation (per Ledger; not re-read) | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` |
| Sessions 1–4 | historical qualification of `9a78fc96…` only; unchanged |

## 2. Preparation artifacts

| File | SHA-256 (LF) | Role |
|---|---|---|
| `cpm/qualification/ITEM8_POST_CLEANUP_REAL_SFM_QUALIFICATION_DESIGN.md` | `fe6051880a039fc18ca2606d3fe29105ad56b02a4afb11fa9d83eac3b35156f1` | approved design (paths normalized to repository-relative) |
| `ITEM8_RUNBOOK.md` | (this commit) | operator runbook |
| `CPM_Item8_Probe.py` | `f503c0abaf63f891c108fd81c726b1101288a2dcf1091bf6a386388be1571257` | observation-only probe (qualification-only; deployed per attempt) |
| `test_cpm_item8_probe.py` | `c5e6c627f2acbc23cfac7fba5f2edca3ef7f65ec19dbf5f5dd7bc6cf84367f32` | probe/reader/pin/fixture qualification |
| `ITEM8_GENERATION_DRIVER.ps1` | `8526c6b18464e691ca269f4d0cdefb2d8c4e52d527620e9d32ae369fe9074ec1` | Windows PowerShell driver: frozen Session 2 block + item-8 deployment/evidence functions |
| `test_item8_generation_driver.py` | `73a5229658d6535e27252a1152a2e3b64c3806aae23e1ef0ad5e593eade76b3e` | driver qualification (sandbox end to end) |
| `ITEM8_FIXTURE_MANIFEST.json` | `40b51416fb8e742b2512dd973ade07ccd0e618a58ebd6c96e9dd62efc1afeb2b` | static fixture/pin manifest |
| `item8_evidence_reader.py` | `a3d3bd90e34eb0691e5290a94e599bfab1425afcc11d8312f16c448089444a10` | offline evidence reader/helper |
| `templates/ITEM8_OPERATOR_STEPS_TEMPLATE.md` | `416d4d255b01923b8b73f72dc54b92814ecdb8c5003d7c6f281ce1b7b2bddfb2` | operator record template |
| `ITEM8_EVIDENCE.md` | (this commit) | this file |

`.gitattributes` gained one narrow `eol=lf` block for this directory's `*.py`, `*.json`, `*.ps1`
and `*.md` files (the Session 3/4 precedent), so the pinned probe/manifest/driver bytes survive any
checkout or archive export.

## 3. Facts established offline

- **Fixture document (pre-execution correction, 2026-10-08):** a read-only search of every `.dmx` on
  the local drives found no qualifying fixture in SFM's own sessions folder. Eight documents in the
  local SFM sessions folder satisfied both identities: `testscripts.dmx` and seven derivatives (the
  `testscripts_*` variants and the Normalizer-mutated `f1_r2_normalized_diagnostic_copy.dmx`). The owner
  selected the original `testscripts.dmx` (`197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f`), which the real-SFM ledger names as "the known
  original fixture filename", for both contexts (Krystal `shot10`, Mia `shot3`). Contents were read
  from a temporary copy converted by SFM's `dmxconvert`; the source's SHA-256 and modification time
  were unchanged throughout, and it was never opened by SFM or saved.

- **Fixture identities** recovered from Sessions 3–4 (harness constants, ARM records,
  `SESSION3_RUNBOOK.md` §3): `krystal20201`, `assaultsuitbody1`, `loinclothbra_chadfix_071` (the
  available unselected peer), `mia1` on `shot3` — models and checksums in the manifest.
- **Qualifying controls** derived offline: the candidate's own `prod_scope`, over the real G1 Master
  (published to a temporary root by the accepted sidecar publisher) and Mia's 108 recorded supported
  literals (S4A ARM snapshot), classifies 46 Body, 58 Expression and 4 other, with no miss or
  conflict. Pinned: **Body `Fat`** (mono), **Expression `SmileClosed`** (mono). The probe test
  re-derives this under Python 3.10 and 2.7.5.
- **Accepted installed deployment:** the Session 4 closeout Scripts inventory (`cefc2b88…`, 1,511
  files; S4A and S4F identical) records every installed file. Its launcher/adapter/projection/
  Normalizer lines and the 23 + 3 shared-package/sidecar-reader files equal the Checkpoint A installed
  manifest and the repository sources; its private-module folder holds only `9a78fc96…`.
- **Unchanged generation tooling:** `tools/`, the Checkpoint I publisher/helper and the Session 2
  runbook are unchanged since the Session 2 freeze (`0597927`); a temporary publication of the
  repository Master reproduces production G1 exactly (manifest `d810d648…`, sidecar `bcd97641…`).
- **Candidate formats:** the reader's event table matches the candidate's own `log_line` format
  strings; the candidate emits no `PROD_PERF`, `ASTRA_PERF`, `PROD_ACTION_TIMING` or
  `G18AN_PROVIDER_FORCE_MODE`, and its single Fit-result format starts `CLOTHING_FIT_RESULT generation=`.
- **Launcher compatibility:** the unchanged R15 launcher computes the build SHA from the installed
  bytes and pins no build, so it loads `bfba4d3a…` unchanged.

## 4. Operator-preflight items (not statically provable)

| Item | Status |
|---|---|
| **OWNER-1** — historical full CPM builds (`sfm/mainmenu/SFM_CSP_G*`, `SFM_Character_Slider_Preset_Tool_*`) and historical package copies (`sfm/gate_r*_deploy/`) present in the accepted inventory | **Resolved (owner decision):** they are accepted as known inert members of the exact Session-4 baseline. They are left present and unmodified, are never invoked, and are not an authority source. This applies only if the inventory is exact. The disposition was recorded verbatim in `I8A1/operator_steps.md`, and `I8-Preflight -Owner1Recorded` proved the exact inventory (`cefc2b88…`). |
| Fixture document | **Resolved (owner decision, 2026-10-08):** the original qualification document `testscripts.dmx` (local SFM sessions folder), SHA-256 `197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f`, 14,245,089 bytes, serves both contexts — Krystal `shot10`, Mia `shot3`. Derivative/variant documents are not used. Recorded again live by `I8-New`. |
| Fixture shot contents | **Resolved offline (read-only):** `shot10` holds `krystal20201`, `assaultsuitbody1`, `loinclothbra_chadfix_071` with the manifest models; `shot3` holds exactly `foxmccouldwm1` and `mia1`; 16 film clips, so a sole Selected `shot3` is a proper subset. Model checksums (not stored in session files) are confirmed live by the probe. |
| Mia preset library folder `mia--2e6533ed1490` present; no campaign-named presets | **Resolved live:** `library_00_preflight` (9 files, no campaign names). |
| Live Scripts tree still equals the accepted inventory; installed app `9a78fc96…`; live authority exact G1 | **Resolved live:** `I8-Preflight` OK; `S2 BASELINE OK`. |
| Actual Fit result on the fixture (changed state; mappings/warnings) | **Observed (Phase B):** stage 34 literals, committed-verified 26 mappings / 7 warnings, `changed=1 partial_changed=1 failed=0 unattempted=0`. |

## 5. Offline preparation qualification

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

## 6. Live campaign results

### 6.1 Attempt and identities

| Item | Value |
|---|---|
| Attempt | `I8A1` (only attempt), 2026-10-08 13:43–20:22, from checkpoint `d4ad3cf8b5c3ffe615b4ad9f4015e57f62acc16d` |
| Verdict | **PASS** (all six phases; mechanical adjudication 34/34) |
| SFM process | one fresh `sfm.exe`, PID **36912**, from A1 through exit at F7 |
| Private module / `ProdWindow` class | `0x30b6b490` / `0x307ed158`, resident throughout, `PROD_R15_MODULE` build `bfba4d3a…` ×3 |
| Run ID | `20261008-135639-pid36912` (only one) |
| CPM windows | `0xce494350` (Phase A–B), `0x310bea30` (Phase C–E), `0x30b87418` (Phase F reopen), in that order; census never above 1 window / 1 watcher |
| Broker | `0x310a7810` (only one); runtime origin is the installed `sfm_master_authority_productionized` menu package |
| Fixture | `testscripts.dmx` `197e6011…`: Krystal triple on `shot10`, `mia1` on `shot3`; not saved, unchanged at exit |
| Deployment (`I8-Deploy`, SFM closed) | installed `bfba4d3a…`, probe `f503c0ab…`, verified backup of `9a78fc96…`, pointer `I8A1`; Scripts difference exactly the two expected lines |
| Generation | G1 Master `ac45e5c1…` → exact G2 `54413b6c…` at 19:46:45 (frozen Phase A/B) → exact G1 restored at F8 (manifest `d810d648…`, single sidecar `bcd97641…`; `exact_match: true` in the finalization record and the independent comparison) |

### 6.2 Phase results

| Phase | Result | Evidence (probe `seq`, log) |
|---|---|---|
| **A** — load, identity, reuse | **PASS** | seq 1 (before launch: module and runtime absent); the launcher loaded `bfba4d3a…` through the private loader; Krystal G1 scope healthy (26 Body / 52 Expression / 2 other, 0 unresolved/conflict); seq 2–3 identical module/class/run/window/broker; the second click gave one `PROD_R15_WINDOW_REUSED` with no acquisition, Select Model or new module |
| **B** — Clothing Fit + Undo, close | **PASS** | authorized on G1; stage opened with 34 literals; committed-verified with 26 mappings / 7 warnings; one release `ok=True`; `CLOTHING_FIT_RESULT generation=2 … changed=1 partial_changed=1 failed=0 unattempted=0`; `G18AN_POST_FIT_ACTION_STATE` present. seq 5: only `assaultsuitbody1` changed (Breastsize, Muscles, slim); source and peer unchanged. One Undo → seq 6 equals B2 exactly. Title-bar close → `PROD_CLOSE_FINALIZED=True`; seq 7 closed-idle with the module resident |
| **C** — shot switch, Body/Expression persistence + Undo | **PASS** | `shot3` was made current with CPM closed; `mia1` identity confirmed (seq 8). Reopen: same module/run, new window, G1 scope 46 Body / 58 Expression / 4 other (equals the offline derivation). Body Save `preset-b41e5` (`Fat` 0.5), Update (0.8000000119) and Apply all equal their readbacks; only `Fat` changed; one Undo → exactly C13. Expression Save `preset-9b778` (`SmileClosed` 0.6000000238) and Apply equal the readback; one Undo → exactly C23. Each library change stayed within the allowed footprint, and Apply/Undo wrote nothing to the library |
| **D** — Normalizer coexistence | **PASS** | Rebuild Selected Shots on the sole Selected `shot3` with the CPM Mia scope active: `SELECTED_SHOTS` 1 [`shot3`], 2 eligible targets, REBUILD PASS, CONTEXTUALIZER PASS, `mem_ok=True` 15 / `False` 0, live Master G1, no `PROD_` lines in the Normalizer log; CPM `MODAL_YIELD_ENTER/EXIT restored=True`. The same broker served `cpm_compat_v1` and `normalizer_compat` (opens/closes 4/4, idle). Continuation without reselection: Apply committed (`Fat` back to 0.8000000119); Save `I8 I8A1 D BODY` `preset-a0b83` matched its readback; one Undo → D7; 0 refusals, 0 stale-generation events, 0 scope rebuilds since the Normalizer |
| **E** — generation transition during a Save prompt | **PASS** | Save opened under G1 at 19:45:32; exact G2 was activated at 19:46:45 while the prompt was open, with the CPM log quiet. On confirm: `Q2_SAVE_POST_CONFIRM` → `AUTHORIZATION_REFUSED` Save Preset `generation-mismatch`; no `PROD_SAVE`; `durable_commit=None`; the "Can't save preset" dialog appeared. Only then `REBUILD_SCHEDULED` → `REBUILD` → one automatic Select Model to healthy G2 in the same window. Libraries E1 = E2 = E3 byte-identical; no `E STALE` file; scene and Undo unchanged. The deliberate G2 Save `preset-c8ac9` (`Fat` 0.3000000119) was authorized on G2, matched its readback and stayed within the footprint |
| **F** — close/reopen, exit, restoration | **PASS** | Escape close → `PROD_CLOSE_FINALIZED=True` (seq 27 closed-idle). Reopen: same module/class/run, new window `0x30b87418`, healthy G2 scope, idle (seq 28–29). Title-bar close → seq 30 closed-idle, broker 0/0/0 (opens/closes 7/7, views 5). SFM exited with the save declined. F8: exact G1 restored; the qualification deployment (probe, pointer) was removed; the final inventory differs from the accepted one only by the app line |

Across all 30 probe records:
- same PID and no errors;
- no acquisition caused by the probe;
- fixture identities matched;
- idle at every checkpoint after the broker existed (leases 0, unreleased 0, open providers 0);
- historical providers inactive whenever the module was loaded;
- `__main__` held no CPM names, and no other module defined CPM.

CPM-log excerpt checks:
- no historical or removed event formats (`PROD_PERF`, `ASTRA_PERF`, `PROD_ACTION_TIMING`, `CLOTHING_FIT_RESULT=PASS`);
- every authorization before 19:46:45 was on G1 and every one after was on G2;
- exactly one refusal;
- exactly the four campaign Saves;
- three committed Applies and none uncommitted;
- every `PROD_PROVIDER_HEALTH` healthy;
- three close requests, each finalized.

### 6.3 Resources (probe-measured, same process)

| Point | Private bytes (MB) | Handles | GDI | USER |
|---|---|---|---|---|
| seq 1 (A2, before launch) | 3,067.8 | 1,294 | 1,165 | 109 |
| seq 7 (B8, first closed state) | 3,078.3 | 1,207 | 1,215 | 129 |
| seq 19 (D1, before Normalizer) | 3,092.3 | 1,214 | 1,247 | 144 |
| seq 20 (D5, after Normalizer) | 3,101.7 | 1,218 | 1,247 | 145 |
| seq 27 (F2, closed) | 3,103.3 | 1,222 | 1,243 | 144 |
| seq 30 (F6, final closed) | 3,103.3 | 1,224 | 1,243 | 145 |

Private usage rose about 35 MB over about 6.5 hours of use. This includes about 9 MB from the
Normalizer run, three CPM scope builds, two generations and all preset I/O. The two closed states after
the reopen (F2, F6) are equal in private bytes, and handles, GDI and USER stayed flat between them
(+2 / 0 / +1). Within one process this is consistent with retained SFM/document state, not a CPM leak
per close/reopen cycle. Attribution beyond that is not claimed.

### 6.4 Deviation and findings

- **Deviation (procedural, no effect):** at 13:58:51, before A5, the operator ran the installed
  Session 1 probe (`CPM_Session1_Probe`, v3 `ce4ace98…`) once. This was against runbook rule 5. Its own
  record showed timing and harness disabled and broker `0x310a7810` counters unchanged (leases 0, open
  0, opens/closes 1/1). Its side effects were one line in its own JSONL and helper names in `__main__`
  (60 → 86 names; no CPM names). No acquisition and no CPM state change was observed. It was recorded
  in `operator_steps.md` and adjudicated as no effect on any phase.
- **Finding (K/L, user-facing):** CPM resolves its scene from the shot under the playhead
  (`sfmApp.GetShotAtCurrentTime()`). The Normalizer uses the Clip Editor selection. Users are not told
  about this difference. No item-8 change.
- **Finding (K, Normalizer UX):** a successful Normalizer run gives no visible completion
  confirmation. Recommendation: a non-blocking success notice, with modals only for failures or
  decisions.
- The historical menu builds and package copies (OWNER-1) stayed on disk. None was loaded or used as
  authority: the probe's historical-provider check was inactive in every loaded record, and the log
  had no historical formats.

### 6.5 Restoration and disposition

- `I8-Finalize`: `S2 RESTORED EXACT G1`. The live Master is `ac45e5c1…`, the manifest `d810d648…`
  and the single sidecar `bcd97641…`; the G2 sidecar was removed. This was re-verified after
  disposition.
- `I8-RemoveQualificationDeployment`: removed the probe and the pointer.
- `I8-Disposition I8A1 -Verdict PASS` at 20:22:02: **the candidate was retained**. The installed app is
  `bfba4d3a54cf42d5eb744040e95f110d24e0870fcfcbb35d54e2885f9560e2b5`. The final Scripts inventory
  (`be663eb8…`) differs from the accepted Session 4 inventory (`cefc2b88…`) only by the private-app
  line (`9a78fc96…` → `bfba4d3a…`).
- The live attempt folder was sealed with `SHA256SUMS.txt` (85 files), and the reader's
  `verify-sums` passes.

### 6.6 Raw evidence

The redacted copy is under `raw/I8A1/` (82 files), with per-file original, excerpt and committed
SHA-256 and redaction counts in `raw/MANIFEST.md`. The two cumulative CPM-log copies are excerpts
from byte 642,260, which is `I8-Preflight`'s recorded log size. Four files are byte-identical to
repository material and are recorded rather than copied: G1, G2, the previous app and the accepted
inventory.

## 7. Limitations

- Offline tests run the actual probe, launcher and candidate `ProdWindow` in a fake game root with real
  PySide/Qt 4.8 (2.7.5) and the Qt model; they cannot qualify real DME objects, real Undo, the
  installed deployment, the real broker under SFM, the Normalizer, or operator steps.
- The driver test runs the real frozen publisher/finalizer only in a temporary sandbox; the live
  authority folder and Master were not touched.
- The probe's scene snapshot reuses CPM's own pure readers: a state observation, not an independent
  semantic oracle; the runbook pairs it with readbacks, preselected values, unchanged peers and
  native-Undo observation.
- The Session 4 Fit release-path observation is carried forward, not repaired or instrumented.
