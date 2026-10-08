# CPM handoff §22 item 8 — focused post-cleanup real-SFM qualification (evidence)

**Status: PREPARED, NOT RUN.** No item-8 attempt exists. No phase (A–F) has been executed; no SFM
process was started for item 8; the candidate was not deployed; no G2 was published; the live Master,
sidecars and installed deployment were not touched. This file holds the preparation record now and
the actual results after a campaign.

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
| `test_cpm_item8_probe.py` | `859b75d12848cf5fe353b5f0a6c0fae41f8ebe141af9e910102c01d35cc1945d` | probe/reader/pin/fixture qualification |
| `ITEM8_GENERATION_DRIVER.ps1` | `3545ac72d87654602877844d91725a165a5e6c4b2e9254d52073fc8fb8bdf0d0` | Windows PowerShell driver: frozen Session 2 block + item-8 deployment/evidence functions |
| `test_item8_generation_driver.py` | `3f4aa26a98fe4cd384fdb4a3dddd703a3982b2f0b3df1b3311cb28af5ed94da9` | driver qualification (sandbox end to end) |
| `ITEM8_FIXTURE_MANIFEST.json` | `2b78f182c154fdcc5acc169169b35bb6120080dea0a81fa9db1e264cdd69703e` | static fixture/pin manifest |
| `item8_evidence_reader.py` | `a3d3bd90e34eb0691e5290a94e599bfab1425afcc11d8312f16c448089444a10` | offline evidence reader/helper |
| `templates/ITEM8_OPERATOR_STEPS_TEMPLATE.md` | `be5354faf9a3e8d3a8f7818aac1b5c49e4c34dee09c6c96b8156a0db7c708879` | operator record template |
| `ITEM8_EVIDENCE.md` | (this commit) | this file |

`.gitattributes` gained one narrow `eol=lf` block for this directory's `*.py`, `*.json`, `*.ps1`
and `*.md` files (the Session 3/4 precedent), so the pinned probe/manifest/driver bytes survive any
checkout or archive export.

## 3. Facts established offline

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
| **OWNER-1** — historical full CPM builds (`sfm/mainmenu/SFM_CSP_G*`, `SFM_Character_Slider_Preset_Tool_*`) and historical package copies (`sfm/gate_r*_deploy/`) present in the accepted inventory | Open: owner disposition required before an attempt (runbook §2). The prepared tooling supports acceptance as in Sessions 1–4 (`-Owner1Recorded`); any other disposition needs a revised preparation. |
| Krystal and Mia fixture **session files** (names, SHA-256, current contents) | Open: recorded by `I8-New`; contents verified by the A2/C2 probes. |
| Mia document has a shot besides `shot3` (Selected scope is a proper subset) | Open: operator check; Normalizer log confirms `SELECTED_SHOTS`, 1 shot. |
| Mia preset library folder `mia--2e6533ed1490` present; no campaign-named presets | Open: `I8-Preflight` / first inventory. |
| Live Scripts tree still equals the accepted inventory; installed app `9a78fc96…`; live authority exact G1 | Open: `I8-Preflight` (read-only gates). |
| Actual Fit result on the fixture (changed state; mappings/warnings) | Open: observed in Phase B (historical 34/26/7 is explanatory only). |

## 5. Offline preparation qualification

| Suite | Interpreter | Qt | Result |
|---|---|---|---|
| `test_cpm_item8_probe.py --phase=run` | Python 3.10.6 | model | **161/161 ALL PASS** |
| `test_cpm_item8_probe.py --phase=run` | embedded Python 2.7.5 | real PySide/Qt 4.8 + model | **225/225 ALL PASS** |
| `test_item8_generation_driver.py` | Python 3.10.6 + Windows PowerShell 5.1 | — | **75/75 ALL PASS** |

Coverage (check groups; 2.7.5 adds the real-Qt children):
- **pins (18):** candidate `bfba4d3a…`; launcher; previous app restorable from git (`9d405c8`); design,
  manifest and Session 2 G1/G2 identities; repository Master = G1 and G1+LF = G2; probe/reader/driver
  pins equal the actual files; accepted inventory pin; manifest dependencies equal both the accepted
  installed inventory and their repository sources; generation tooling pins equal the repository and
  the driver and are unchanged since `0597927`.
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
- **driver (75):** frozen block byte-identical to `SESSION2_RUNBOOK.md` at `0597927` except the two
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
  disposition in a second attempt keeping `bfba4d3a…` (only the implementation line differs) with the
  untouched-authority proof; sealed attempts verified by the reader; a later preflight refusing while
  the candidate remains installed.

Defects found and fixed during preparation (tooling only): `File.Replace` received `""` for a
`$null` backup path (now `[NullString]::Value`); PowerShell's case-insensitive names made the
inventory comparison coerce its maps into the `[string]` parameters, so every inventory comparison
compared nothing (renamed; negative tests now prove each comparison can fail); preflight and later
inventory checks wrote write-once files before refusing (now temp-then-move, so refused steps can be
rerun).

## 6. Live campaign results

No attempt. (After a campaign: attempt id(s), phase verdicts with evidence references, anomalies and
their disposition, resource interpretation, exact G1 restoration, deployment disposition, and the
redacted raw copy under `raw/<attempt>/`.)

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
