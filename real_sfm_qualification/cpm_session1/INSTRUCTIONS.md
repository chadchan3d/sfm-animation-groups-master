# CPM Convergence — Real-SFM Qualification Session 1 (operator runbook)

Normal CPM operation through the converged authority seam, the native Apply transaction and
Undo, one ordinary Clothing Fit target, the C10 same-process broker check, minimal Normalizer
coexistence, and resource/latency measurement.

**Not in this session:**
- no G1→G2 change while CPM is open, and no authority change during a prompt;
- no queued mid-Fit generation change;
- no forced Apply or Fit rollback failures.

## 0. Qualification deployment (already placed; verify before starting)

Folder: `<SFM game>\usermod\scripts\sfm\mainmenu\ChadChan3D\`. This is the interim layout for
qualification only; L owns the final layout.

| File | SHA-256 |
|---|---|
| `SFM_Character_Preset_Manager.py` | `945eab6c9323ad35c238921f2a6654603d4510e61f68f45f72dabdbcdebbaf8a` |
| `cpm_authority_adapter.py` | `e96e21b537b5892fc5c1139b2396bbf5e3ce48a521b45876035d78789f126607` |
| `cpm_compat_v1_projection.py` | `9b077a1baf491262901812620c380a45eeb9cb2bf75ddc28a08ab18612faffc1` |
| `CPM_Session1_Probe.py` (test-only) | `d7f16fac085b7e0711fba5e0dfea75c102f6cdd73a2b5086e703af27f8e83cd6` |
| `Rebuild_Control_Groups_Normalizer.py` (unchanged) | `1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7` |

- **Shared package:** `sfm_master_authority_productionized` (unchanged, 23 files), API
  `1.0.0-b2a`, build `package-boundary-corrected-2026-09-22`.
- **Master:** `usermod\cfg\sfm_defaultanimationgroups.txt`, SHA-256 `ac45e5c1…904d93`.
- **Published sidecar:** `usermod\cfg\sfm_shared_authority\`, source-matched to that Master.

**Do not edit the Master during Session 1.**

## Ground rules

- Use a **fresh SFM process**. Open **only** "SFM Character Preset Manager" from `ChadChan3D`.
  - Do **not** open any older CPM build (`SFM_CSP_*`, `SFM_Character_Slider_Preset_Tool_*`) in the
    same process. They share the same window slot, so the old window would be shown instead.
- **Waiting:** SFM may hang or show an hourglass during native work. That is not a failure.
  - Wait for the stated completion condition (a status-bar message, or the window becoming
    responsive).
  - Allow at least 60 s before calling anything stuck.
- **Probe (P):** at each **P#** below, run `ChadChan3D > CPM_Session1_Probe` from the Scripts
  menu. It appends one line to `%PUBLIC%\Documents\CPM_Session1_Probe.jsonl` and prints one
  summary line to the SFM console.
  - Run it only when CPM shows no action in progress.
  - It never changes the scene or presets.
  - Note the probe `seq` next to each P# on your run sheet.
- **Evidence to return after the session:**
  - `%PUBLIC%\Documents\CPM_Session1_Probe.jsonl`;
  - `%PUBLIC%\Documents\SFM_CSP_G18AN_SaveNewCopy.log` (the CPM log; its name is inherited
    unchanged);
  - the Normalizer's log;
  - your run sheet, which should give for each step: pass/fail, what you observed, and any
    dialog text.

## Steps

**P0** — Fresh SFM, a session loaded with a representative character and at least one clothing
or accessory model. Do **not** open CPM yet. Run the probe. It is expected to report
`runtime_loaded false` or no broker.

### A. Startup and initial scope
1. Open SFM Character Preset Manager and select the representative character.
2. Wait until Body / Expression / Review counts appear in the window.
3. Note the displayed counts. Note one known resolved control, and (if present) one Review item,
   which is a genuine miss.

- **P1:** expect converged `true`, historical_open `false`, leases 0, open_providers 0, consumer
  kind `cpm_compat_v1`.
- Leave CPM idle for about 30 s. **P2** (idle): expect leases 0 and open_providers 0.

### B. Body Save / Update
1. Body tab → Save New Body Preset → enter a name → OK. Wait for "Body Preset saved."
2. Move one Body slider. Select that preset → Update Preset → confirm. Wait for the success
   status.

- **P3.**

### C. Expression Save / Update
Same as B on the Expression tab. Wait for "Expression saved." and the Update success status.

- **P4.**

### D. Native Body Apply + Undo
1. Change several Body sliders away from the saved Body preset. Apply that preset. Wait for the
   success status.
2. Verify the sliders now match the preset (the expected scene change).
3. Use SFM **Undo** once. Verify the sliders return to the pre-Apply values.
4. Apply the same preset again. Then Apply it once more with nothing changed: this is the
   **no-op Apply**. Record the status text and whether a new Undo entry appeared (expected: no
   new Undo entry).

- **P5.**

### E. Expression Apply
Change an Expression slider, then Apply the saved Expression preset. Verify the scene result.

- **P6.**

### F. Review / Reclassify (a genuine healthy miss)
1. In Review, select an unrecognized flex → classify it (Body or Expression). Expect "Flex choice
   saved." and the flex under Reviewed choices.
2. Select it under Reviewed choices → Reclassify. Expect it back under Needs review with "Choose
   a new classification for this flex."
3. Confirm that resolved (positive) and conflict flexes are **not** offered for Review.

- **P7.**

### G. Ordinary Clothing Fit (one target)
1. Pick a clothing/accessory model that has flex controls the character does not have (target
   vocabulary not all in the source). Clothing Fit tab → check only that target → Fit.
2. Wait for the Fit status.
3. Verify the target changed as expected.
4. SFM **Undo** once. Verify the target returns to its pre-Fit state.

- **P8.**

### H. C10 same-process broker + Normalizer coexistence
Without restarting SFM:
1. Run the production Normalizer (`ChadChan3D > Rebuild_Control_Groups_Normalizer`) on one
   representative model/shot, as it is normally used. Wait for its completion report.
2. **P9:** expect **the same `broker_id` as P1–P8**, and `consumers_served` (and usually
   the cached consumer kinds) including both `cpm_compat_v1` and `normalizer_compat`.
3. Return to CPM. Confirm the window still works: select the character again. **P10.**
4. Run the Normalizer once more (a representative operation remains usable). **P11.**

### I. Close
Close CPM. **P12:** expect leases 0 and open_providers 0.

## What the evidence shows (for the reviewer)

| Question | Source |
|---|---|
| Canonical route used | probe: `converged_app`; log: `PROD_PROVIDER_HEALTH … reason='canonical-admission-and-view-validated'` |
| Historical route unused | probe: `historical_provider_open false`, `historical_provider_open_count 0/None`; log: no `SEMANTIC_PROVIDER_OPEN` / `G18AN_SIDECAR_ADAPTER_READY` |
| Post-prompt authorization before writes | log: `PROD_CPM_OPERATION_AUTHORIZED` precedes `PROD_SAVE=PASS` / `PROD_UPDATE=PASS` / `PROD_OVERRIDE_*` |
| Apply authorization before mutation | log: `PROD_CPM_OPERATION_AUTHORIZED operation='Apply Preset'` before the Apply transaction lines; no later authorization line inside that Apply |
| Fit | log: `PROD_CPM_FIT_STAGE_OPEN` … `PROD_CPM_FIT_STAGE_RELEASED ok=True` per target |
| No idle lease/provider | probe P2, P3–P8, P12: leases 0, open_providers 0 |
| Same process broker (C10) | probe P1–P11: one `broker_id`; P9 `consumers_served` shows both consumers served by that one broker |
| Resources | probe: `scope_deep_bytes`, `views[].estimated_bytes`, `ledger`, `memory_*` at each P# |
| Latency | probe `timing` (authorization ×3, stage open+release ×3); log `ASTRA_PERF area='model-render' phase='semantic-scope'` for scope build |

**Stop if** any step shows a wrong semantic state, an unexpected error dialog, a lost Undo, a
non-zero lease at an idle probe, or two different `broker_id` values. Record the evidence and
report it before continuing.
