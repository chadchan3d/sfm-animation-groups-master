# CPM Real-SFM Session 1 — completion runbook

Run only the items the first run did not prove (see `SESSION1_RUN1_RECONCILIATION.md`). Do not
repeat Save, Apply, Expression or C10 work.

**Scripts** (all in the Scripts menu, `ChadChan3D` folder):

| Script | Role | SHA-256 |
|---|---|---|
| `SFM_Character_Preset_Manager.py` | converged CPM, with the R14 fix | `664a660c7b896d62ba6cab4c27427a0c6a12de9e29912e7b88526ccc2d8b178b` |
| `CPM_Session1_Probe.py` | test-only probe, v2 | `0722610aa274bd9db2f355c4f85e61c51c07d810f3cd4d762255f085dffba1fe` |
| `Rebuild_Control_Groups_Normalizer.py` | production Normalizer | `1f4ec5a2…7db7` |

`Rebuild_Control_Groups_Normalizer.py` **is** the production Normalizer operation. Run it from the
Scripts menu and complete its own normal prompts and choices. Do not use SFM's built-in Rebuild
Control Groups command in its place.

**Rules:**
- **Setup:**
  - Use a fresh SFM process. Open only the converged CPM, not older `SFM_CSP_*` or
    `SFM_Character_Slider_Preset_Tool_*` builds.
  - Do not edit the Master, and add no synthetic fixture.
- **Timing:** wait for each stated completion condition. An hourglass during native work is
  normal; allow at least 60 s.
- **Probe:**
  - Run `CPM_Session1_Probe` at each **C#** checkpoint, only while no CPM action is in progress.
  - It appends to `%PUBLIC%\Documents\CPM_Session1_Probe.jsonl` and never changes the scene or
    presets.
  - Write down the time of each C#.
- **Return afterwards:**
  - the probe JSONL;
  - `%PUBLIC%\Documents\SFM_CSP_G18AN_SaveNewCopy.log`;
  - `%PUBLIC%\Documents\sfm_rebuild_control_groups.txt`;
  - a short note per item: done / skipped (why) / problem.

## 1. Simultaneous coexistence + R14 telemetry + memory (always possible)

This one pass closes simultaneous coexistence, confirms R14, and measures process memory.
**CPM must stay open from step 1.2 through step 1.7.**

1.1 Fresh SFM with a representative character loaded.
- **C1:** probe before opening CPM.

1.2 Open SFM Character Preset Manager (**keep it open**). Select the character. Wait until the
Body / Expression / Review counts appear and no action is in progress (idle).

1.3 **C2:** probe v2. Expect:
- converged `true`;
- leases 0, open providers 0;
- valid `memory_*` values (no `error`).

1.4 **With CPM still open**, run `Rebuild_Control_Groups_Normalizer` from the Scripts menu and
complete its normal prompts. Wait for its completion report.

1.5 The Normalizer must complete normally. Its log
(`%PUBLIC%\Documents\sfm_rebuild_control_groups.txt`) must show `mem_ok=True` on its
`CONTEXTUALIZER_RESOURCE_CHECKPOINT` lines. `mem_ok=False` means R14 is not fixed; report it.

1.6 **C3:** probe v2. Expect:
- the same `broker_id` as C2;
- `consumers_served` containing `cpm_compat_v1` and `normalizer_compat`;
- `cpm.window true`;
- **leases 0, open providers 0**;
- valid `memory_*` values.

1.7 Return to the **still-open** CPM. Re-select the character (or switch model and back), then
Apply an existing Body preset. Confirm it works.
- **C4.**

1.8 Only now may CPM be closed.
- **C5:** leases 0, open providers 0.

## 2. Body Update (always possible)

With CPM open on the character:
1. Move one Body slider.
2. Select an existing Body preset → **Update Preset** → confirm.
3. Wait for the Update success status. This must be an Update of an existing preset, not
   "Save New".

- **C6.**

## 3. Review / Reclassify (only if a valid fixture exists)

**Required:** a real model whose CPM window shows at least one item under **Needs review**, that
is, a healthy Master miss, with no Master edit. If no available model has one, record
"skipped — no healthy-miss model" and stop this item.

1. Select a Needs-review flex → classify it. Expect "Flex choice saved."
2. Select it under Reviewed choices → **Reclassify**. Expect it back under Needs review.
3. Confirm that resolved and conflict flexes are not offered for Review.

- **C7.**

## 4. Ordinary Clothing Fit + Undo (only if a valid fixture pair exists)

**Required:**
- the source character, plus a clothing or accessory model in the same shot;
- that target has at least one flex control the source character does not have.

If no such pair is available, record "skipped — no suitable target" and stop this item.

1. Clothing Fit tab → check only that target → **Fit**. Wait for the Fit status.
2. Verify the target changed.
3. SFM **Undo** once. Verify the target returned to its pre-Fit state.

- **C8:** leases 0.

Stop and report on a wrong semantic state, an unexpected error dialog, a lost Undo, a non-zero
lease at a C#, or differing `broker_id` values.
