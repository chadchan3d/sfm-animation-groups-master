# CPM real-SFM Session 2 — evidence and verdict

- **Procedure:** `SESSION2_RUNBOOK.md`, frozen at `fda6810`, corrected at `3b22b8b` (S2-A_R2) and at
  `0597927` (S2-B step B6 wording).
- **Raw outputs:** `raw/`. These are exact excerpts with three path prefixes redacted; each
  original, excerpt and committed file is listed with its SHA-256 in `raw/MANIFEST.md`.
- **Times:** local times from the logs. Tool records carry `wall_time`/`epoch`.

**Verdict: Session 2 PASS.** S2-A_R2 (open-window G1→G2 replacement) and S2-B_R2 (G1→G2 during a
Save prompt) both pass. Production G1 was restored exactly after every campaign.

## Identities

| Item | Value |
|---|---|
| Product (unchanged since `00d0d83`) | launcher `996ca483…`, private app `9a78fc96…` (`PROD_R15_MODULE` build field in every process), probe v3 `ce4ace98…` |
| G1 (production) | Master `ac45e5c1…`, manifest `d810d648…`, sidecar `bcd97641…` |
| G2 (G1 + one LF; semantic parity proven by the publisher) | Master `54413b6c…`, sidecar `cd370f67…`, manifest after publication `9da5057f…` |
| Switch / restore mechanism | unchanged Checkpoint I tooling, through the frozen runbook functions |

## Campaigns

| Folder | Date | Process | Result |
|---|---|---|---|
| `S2A` | 2026-10-01 | pid 19016 | **Procedurally invalid** (runbook design error; see below). Restored exact G1. |
| `S2A_R2` | 2026-10-05 | pid 25844 | **PASS** |
| `S2B` | 2026-10-05 | pid 17996 | **Aborted before any authority switch** (operator error; see below). Live authority untouched. |
| `S2B_R2` | 2026-10-05 | pid 23944 | **PASS** |

## S2-A_R2 — open-window generation replacement: PASS

| Criterion | Evidence |
|---|---|
| Valid run; complete records | No CPM log activity between G2 activation (17:55:09) and the A8 Apply (17:56:10.858). `…REBUILD_SCHEDULED` appears only at 17:57:17.484. All 15 records are present (including `post_switch_inventory`, `restored_inventory`, `restore_compare`). |
| G1 scope; P2 G1 | Mia `PROD_PROVIDER_HEALTH … sha256=ac45e5c1…` at 17:50:04. `BodyTest` was selected under G1 at 17:50:14. P2 (seq 43, 17:53:24): scope `ac45e5c1cd45`, window `0x3210f580`. |
| Exact G2 activation | Activation record 17:55:09: G1 → `54413b6c…`, success. Post-switch inventory: G2 Master, G1 + G2 sidecars, manifest `9da5057f…`. P3 (seq 44): scope still G1. |
| Stale G1 refused before mutation | Op 4 (Apply) began 17:56:10.858. `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED operation=u'Apply Preset' reason=u'generation-mismatch'` at 17:56:15.356. No Undo, mutation transaction, native-commit or Apply outcome. Ended `phase=u'BEGIN' native_commit=None durable_commit=None`. |
| Rebuild only after refusal | `…REBUILD_SCHEDULED` 17:57:17.484 → `…REBUILD` .517 → one automatic Select Model (op 5), `sha256=54413b6c…`, scope-ready. |
| P4 same window under G2 | Seq 45: window `0x3210f580`, scope `54413b6ca618`, G1 view stale, provider opens 1 → 4. |
| No replay | No Apply between op 4's end and the deliberate op 6. |
| Deliberate G2 Apply | Op 6 at 17:57:48: authorized `54413b6c…`, `committed` `BodyTest`, `changed_sides=1`. |
| Idle authority P2–P5 | Seq 43–46: leases 0, unreleased 0, open providers 0; one window, one watcher. |
| Exact G1 restoration | `finalization_record` `exact_match: true`. `restore_compare` `exact_match: true`. `restored_inventory`: Master `ac45e5c1…`. |

## S2-B_R2 — generation change during the Save prompt: PASS

| # | Criterion | Evidence |
|---|---|---|
| 1 | P2 is G1 | Seq 50 (18:36:23): scope `ac45e5c1cd45`, window `0x30466580`, broker `0x31141250`. |
| 2 | Save and its prompt began under G1 | `library_1_before_prompt` written 18:36:32. Op 3 `Save Current Body` began 18:36:40.113 (pre-prompt check under G1). |
| 3 | Exact G2 activated with the prompt open | No CPM log line between 18:36:40.116 and 18:41:04.623 (prompt open). Activation record 18:40:42.999: G1 → `54413b6c…`, success. Post-switch inventory 18:40:43: exact G2. `library_2_g2_active_prompt_open` written 18:40:52, prompt still open. |
| 4 | `Q2_SAVE_POST_CONFIRM` only after activation | `Q2_SAVE_POST_CONFIRM` at 18:41:04.623, 21.6 s after the activation record's epoch. |
| 5 | Stale G1 authorization refused | `PROD_CPM_OPERATION_AUTHORIZATION_REFUSED operation=u'Save Preset' reason=u'generation-mismatch'` at 18:41:09.109, after `Q2_SAVE_POST_CONFIRM`. |
| 6 | No stale write | Op 3: no `PROD_SAVE`, no durable phase; `phase=u'BEGIN' native_commit=None durable_commit=None`. `library_1` = `library_2` = `library_3` byte-identical (`5605a2d9…`); no `S2 STALE SAVE` entry. |
| 7 | Rebuild to G2 without replay | `…REBUILD_SCHEDULED` 18:41:19.673 (after the refusal dialog) → `…REBUILD` → one automatic Select Model (op 4) `sha256=54413b6c…`. No further Save until the deliberate op 5. |
| 8 | P3 same window under G2, idle | Seq 51 (18:41:29): window `0x30466580`, scope `54413b6ca618`, G1 view stale, leases 0, open providers 0. |
| 9 | Deliberate G2 Save | Op 5 at 18:44:30: `AUTHORIZED operation=u'Save Preset' sha256=54413b6c…` → `durable-commit`/`durable-verified` → `PROD_SAVE=PASS name=u'S2 G2 SAVE'` (`preset-1914ae71…`). |
| 10 | Library diff within the allowed set | `library_4` vs `library_3` adds `Body Presets/S2 G2 SAVE--preset-1914a.json`, changes `character.json`, and changes `character.json.bak` (now holding the previous `character.json`). Nothing else changes. |
| 11 | Idle authority P2–P4 | Seq 50–52: leases 0, unreleased 0, open providers 0; one window, one watcher. |
| 12 | Exact G1 restoration | `finalization_record` `exact_match: true` (18:45:12). `restore_compare` `exact_match: true`. `restored_inventory` matches the baseline. |

## Invalid and aborted attempts

**`S2A` (2026-10-01): procedurally invalid.**
- **What happened:** selecting `BodyTest` after G2 activation re-evaluated readiness. CPM rebuilt the
  scope under G2 at 04:09:36 before Apply, and Apply then ran under valid G2 authority.
- **Classification:** runbook design error, not a product failure. The early detection path behaved
  correctly.
- **Records:** the folder lacks `post_switch_inventory`, `restored_inventory` and `restore_compare`;
  the frozen functions were not used verbatim. Its finalization record still reports
  `exact_match: true`.

**`S2B` (2026-10-05): aborted before any authority switch.**
- **What happened:** the operator confirmed the Save prompt before Phase A. The ordinary G1 Save
  (op 3, 18:26:39) authorized `ac45e5c1…` and wrote `S2 STALE SAVE` (`preset-afeef964…`).
- **Authority:** no plan, publication or activation record exists, so the authority was never
  touched.
- **Clean-up:** the operator removed the preset file before `S2B_R2`.

## Retry-contamination adjudication: no confound

- **The accidental Save's footprint:** that G1 Save also refreshed `character.json` through
  `prod_ensure_character`. In the aborted baseline, `character.json` was `7cb66abf…`; in the
  `S2B_R2` baseline it is `79fe6277…`, with `.bak` = `7cb66abf…`.
  - The `S2B_R2` baseline `character.json` (now preserved as `.bak`) carries
    `updated_at = 20261005-182639…`, the exact second of the accidental Save.
- **What a Save changes:** comparing that file with the post-G2-Save `character.json` shows a Save
  changes only `updated_at` and `last_validated_provider.source_sha256`.
  - `prod_ensure_character` can otherwise reset only `structural_capabilities` and refresh display
    metadata.
  - `semantic_overrides` is `{}`, revision 0, which `setdefault` preserves.
- **None of those fields feed the tested boundary:**
  - `last_validated_provider`, `updated_at` and `structural_capabilities` are only ever written by
    CPM; no code path reads them for a decision;
  - Save authorization reads only the scope's generation and literals;
  - the scope's semantic input from the profile, `semantic_overrides`, is empty and unchanged.
- **Comparisons are internal to the retry:** every library comparison in `S2B_R2` is within that
  campaign (`library_1` = `2` = `3`). Its baseline already includes the residual profile change,
  and the stale preset file is absent from all four inventories.
- **Conclusion:** the aborted attempt cannot confound the generation-mismatch boundary, the no-write
  proof or the rebuild.

## Observations (non-blocking)

- **Refusal dialogs:** they show the guard's generic copy, not the stale-scope reason, which is
  logged only:
  - Apply: "Preset could not be applied safely. This preset was not applied."
  - Save: "Can't save preset — Preset could not be saved. Nothing was saved."

  This is recorded under the Ledger's stale-scope UI presentation item.
- **Refusal latency:** a stale refusal takes about 4.5 s (17:56:10.865 → 17:56:15.356;
  18:41:04.636 → 18:41:09.109). Provider opens grow by 3 across refusal plus rebuild; the broker
  observes and validates G2 on first use. Idle state is clean afterwards.
- **Extra readiness checks:** `S2A_R2` shows two readiness observations under G1 at 17:51:46 with no
  operation, before P2 and the switch. They are harmless.
- **Library residue (owner's live preset library):**
  - the disposable `S2 G2 SAVE` preset (and the earlier `R15 TEMP` / `R15 POST NORMALIZER`);
  - the refreshed `character.json` / `.bak`.

  None affect authority.

## Operator notes (as reported)

| Campaign | Steps |
|---|---|
| S2A | Baseline OK → P1 → Mia under G1 → Body applied → P2 → Phase A OK → G2 ACTIVE OK → P3 → selected BodyTest → Apply: no stale warning → stopped → SFM closed without saving → restored exact G1 |
| S2A_R2 | Baseline OK → P1 → Mia under G1 → Body applied → BodyTest selected, not applied → P2 → Phase A OK → G2 ACTIVE OK → P3 → Apply without intervening CPM interaction → refusal dialog → OK → rebuild, counts returned → P4 → second Apply succeeded → P5 → closed without saving → RESTORED EXACT G1 |
| S2B | Baseline → P1/P2 → library_1 → Save prompt confirmed by mistake before Phase A → stopped; SFM closed; accidental preset file removed |
| S2B_R2 | Exact G1 baseline → P1/P2 → library_1 → prompt opened with `S2 STALE SAVE`, left open → G2 ACTIVE → library_2 identical → confirmed → "Can't save preset — … Nothing was saved." → rebuild → P3 → library_3 identical → `S2 G2 SAVE` succeeded → P4 → library_4 (three allowed changes) → closed without saving → RESTORED EXACT G1 |

**Shell evidence:** the PowerShell transcripts were not retained. The tool records and the
`phase_a/phase_b/finalize` stdout captures in `raw/` are the shell evidence; they corroborate every
reported `S2 … OK` line.
