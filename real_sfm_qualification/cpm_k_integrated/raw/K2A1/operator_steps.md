# K operator record — attempt `K2A1`

Runbook: `cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md` (§8 K1, §9 K2).
Process: `K1` or `K2` (one fresh SFM process per attempt; a retry is a new attempt id).

Rules (design §7): one exact human action at a time; confirm the stated **playhead shot** and **selected
shot(s)** before every consumer action; divergent state = **selection first, playhead second, then
confirm both** (D3 = B); never `shot12`, never **Rebuild All Shots** (D2 = B), never save the
document, never run other scripts; any unexpected refusal, dialog, stale event, rebuild, authority
mismatch, scene value or freeze → **STOP** (no retry, no reinterpretation).

## Owner dispositions recorded for this attempt

- OWNER-1 (historical menu builds and package copies present, inert, never invoked): accepted
  (as for Sessions 1–4 and item 8); `K-Preflight -Owner1Recorded`.
- D1 = A (no authority-unavailable mechanism), D2 = B (no K3 / All Shots), D3 = B, D4 = YES.

## Shell steps

- (step id, wall time, command, result line)

## Owner steps

| Step | Time | Playhead shot | Selected shot(s) | Action as performed | Visible result reported | Probe seq |
|---|---|---|---|---|---|---|
| | | | | | | |

## Deviations and STOPs

(Anything unexpected, with the time. Do not interpret here; adjudication is separate.)
- 01:20:28 K2-S1 shell (checkpoint 13f57c1e, clean): K-New K2A1 (fixture pin OK); K-Preflight K2A1 -Owner1Recorded -> S2 BASELINE OK (exact G1 Master/manifest/single sidecar), K PREFLIGHT OK (expected inventory 59b8f28b..., exact deps); K-DeployProbe -> K READY (+CPM_K_Probe.py 96d873b7... only; app 4e35f292... unchanged). Owner K2 clarifications recorded: (1) before every Normalizer command re-establish the required state explicitly (K2-E1: select only shot3 first, then playhead shot10, confirm both); (2) K2-D4 changed-Muscles Apply must be a real committed G2 Apply, Undo must restore the operator value; (3) K2-E4 accepts only mutations attributable to known Save/Delete/Favorites-cleanup behavior.
- 02:17:51 K2-S2/S3/A1 (02:17): fresh SFM PID 41240; testscripts.dmx; DIV set selection only shot9 first, then playhead shot10, confirmed. Probe seq=1: no broker, no CPM. CPM opened first: run 20261010-021726-pid41240, build 4e35f292..., module 0x30041910, window 0x305e2670; krystal20201 healthy G1 scope 26/52. Probe seq=2: CPM constructed broker 0x3101aa50 (canonical, menu package), one cpm_compat_v1 G1 view, idle 0/0/0; identity OK.
- 02:19:21 K2-A2..A6 (02:18): Save New 'K K2A1 A2 BODY' (AUTHORIZED Save Preset G1 body 26; PROD_SAVE controls=26); library: +krystal2020--7d2aee52ef3a/Body Presets/K K2A1 A2 BODY--preset-008f3.json, character.json/.bak changed (Save footprint), nothing else; readback A2. DIV confirmed (selection only shot9, playhead shot10); Normalizer Rebuild Selected Shot(s): N1 shot9 krystalv21 RECONCILED, PASS/PASS, G1, mem_ok 13/0; CPM only MODAL_YIELD ENTER/EXIT restored=True. Probe seq=3: same broker 0x3101aa50, views cpm_compat_v1 G1 + normalizer_compat G1, no live leases, idle 0/0/0 (opens/closes 2/2).
- 02:20:05 K2-B1 shell (02:19): with SFM open and both consumers idle (CPM open on Krystal, no prompt), K-GenerationSwitch K2A1 -> S2 PHASE A OK (G2 sidecar published), S2 G2 ACTIVE OK (live Master 54413b6c... at 02:19:58). Authority dir: G1 + G2 sidecars. CPM log size unchanged across the switch (822757 bytes): no acquisition/rebuild by the change itself.
- 02:21:35 K2-B2 (02:20:46): probe seq=4 after G2 activation: no acquisition, no rebuild: views unchanged (cpm G1 x1, normalizer G1 x1), provider opens/closes 2/2, CPM scope still G1, idle. K2-C1..C3 (02:21): DIV confirmed (selection only shot9, playhead shot10); Normalizer touched G2 first: N2 shot9 krystalv21 RECONCILED, PASS/PASS, live Master SHA256 = G2 54413b6c..., mem_ok 13/0; broker: cohort_acquired cohort 3 G2 [normalizer_compat] (shipped_candidate_skipped), G1 views of both kinds now stale, no G1 reuse for the command. CPM log since switch: only MODAL_YIELD ENTER/EXIT restored=True (no CPM acquisition/rebuild). Probe seq=5: same broker; CPM window still holds its G1 scope with no lease; idle 0/0/0 (opens/closes 3/3).
- 02:23:09 K2-D1..D3 (02:22): first CPM action after G2: Apply 'K K2A1 A2 BODY' -> expected refusal dialog ('Preset could not be applied safely...', operator: as specified), dismissed. Log: exactly one PROD_CPM_OPERATION_AUTHORIZATION_REFUSED Apply Preset reason=generation-mismatch (02:22:25); no PROD_APPLY; PROD_OPERATION_END Apply Body Preset phase=BEGIN native_commit=None durable_commit=None; after dismissal REBUILD_SCHEDULED -> REBUILD -> one Select Model -> PROD_PROVIDER_HEALTH healthy G2 54413b6c...; no replay. Probe seq=6: same window/module/broker; CPM scope G2 26/52; G2 views for both consumers (G1 views stale); Krystal sets unchanged vs seq=5, Undo 0 (no mutation); idle 0/0/0 (opens/closes 6/6).
- 02:24:40 K2-D4/D5 (02:24): shot10 clip clicked (selection may change; allowed between Normalizer commands); Muscles set to 1.0; Apply 'K K2A1 A2 BODY' -> 'Body Preset applied': AUTHORIZED Apply Preset on G2 54413b6c... body 26; PROD_APPLY committed (real mutation 1.0 -> 0.3547 per preset); Edit>Undo once -> Muscles 1.0 (operator value) restored. Probe seq=7: only Muscles differs from seq=6 (the operator value); Undo top 'Modify Muscles'; CPM scope G2; still exactly one refusal since G2; idle 0/0/0.
- 02:26:16 K2-E1..E4 (02:25): DIV re-established per clarification (selection only shot3 first, then playhead shot10, confirmed); Normalizer N3: shot3 foxmccouldwm1 + mia1 RECONCILED, PASS/PASS, live Master G2, mem_ok 15/0; CPM only MODAL_YIELD ENTER/EXIT restored=True. Delete Preset 'K K2A1 A2 BODY' -> PROD_DELETE=PASS, file in Trash (20261010-022535...). CPM closed with X: CLOSE_REQUEST + CLOSE_FINALIZED=True. Probe seq=8: slot empty, module resident, same broker, G2 views for both consumers, idle 0/0/0 (opens/closes 7/7). Library E4 vs preflight: only krystal2020 character.json (updated_at 20261010-003355 -> 20261010-021816, i.e. the K2 Save at 02:18:16) and character.json.bak (= the preflight character.json); no library.json change, no other difference: all attributable to the known Save/Delete footprint.
- 02:27:22 K2-F1: with CPM closed, operator exited SFM (Don't Save); exit normal.
- 02:28:48 K2-F2 shell: K-CollectLogs final; K-Finalize -> S2 RESTORED EXACT G1 (Master ac45e5c1..., manifest d810d648..., single sidecar bcd97641...; G2 sidecar removed); K-RemoveProbe -> expected inventory 59b8f28b... restored, app 4e35f292... and fixture unchanged, live list sealed (51 files). Mechanical adjudication (after SFM exit, over sealed live evidence): 39/39 PASS. ADJUDICATION-SCRIPT CORRECTION (recorded, before the verdict): the first run's check banned any PROD_ACTION_ERROR/Traceback and flagged the guard's own record of the expected K2-D1 refusal (PROD_ACTION_ERROR 'Apply Body Preset' stale-scope RuntimeError at the refusal timestamp; same pattern as item 8 E). The check now requires exactly one action error, equal to the expected refusal, and no other error or traceback. Verdict: K2 PASS.
