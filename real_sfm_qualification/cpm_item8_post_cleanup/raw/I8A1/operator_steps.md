# CPM item 8 - operator record, attempt `I8A1`

One SFM process from A1 to F7. Record every step as it happens; do not edit earlier rows.
"Probe" = Scripts > ChadChan3D > CPM_Item8_Probe; write its console `seq=` in the evidence column.
Mark a step `STOP` (and stop) if its visible expectation fails; ITEM8_RUNBOOK.md section 7 then applies.

| Step | Time | Action | Visible result | Evidence filename |
|---|---|---|---|---|
| S0.2 | | I8-New | | authority_pins.json, fixture_manifest.json |
| S0.3 | | I8-Preflight | | deployment_before.json |
| S0.4 | | I8-Deploy | | deployment_after.json |
| A1 | | Fresh SFM; open testscripts.dmx; make shot10 current | | |
| A2 | | Probe (before CPM) | | probe seq |
| A3 | | Launcher | | |
| A4 | | Select krystal20201; wait for counts | | |
| A5 | | Probe | | probe seq |
| A6 | | Launcher again | | |
| A7 | | Probe | | probe seq |
| B1 | | Fit tab: check only assaultsuitbody1 | | |
| B2 | | Probe (pre-Fit) | | probe seq |
| B3 | | Fit Selected to Model; wait for completion | | |
| B4 | | Probe (post-Fit) | | probe seq |
| B5 | | Edit > Undo once; visual check | | |
| B6 | | Probe (after Undo) | | probe seq |
| B7 | | Close CPM with the title-bar X; settle | | |
| B8 | | Probe (closed) | | probe seq |
| C1 | | CPM closed: make shot3 current in the open testscripts.dmx (no reopen, no save) | | |
| C2 | | Probe (closed, Mia document) | | probe seq |
| C3 | | Launcher; select mia1; wait for counts | | |
| C4 | | Probe (reopened) | | probe seq |
| C5 | | Set Fat to 0.50 | | |
| C6 | | Probe; I8-Library library_C01_before_body_save | | probe seq |
| C7 | | Save New Body "I8 I8A1 C BODY" | | |
| C8 | | I8-Readback C_body_save; I8-Library library_C02_after_body_save | | preset_readback/C_body_save.json |
| C9 | | Set Fat to 0.80; probe | | probe seq |
| C10 | | Update Preset (I8 I8A1 C BODY) | | |
| C11 | | I8-Readback C_body_update; I8-Library library_C03_after_body_update | | preset_readback/C_body_update.json |
| C12 | | Set Fat to 0.20 | | |
| C13 | | Probe (pre-Apply) | | probe seq |
| C14 | | Apply Preset (I8 I8A1 C BODY) | | |
| C15 | | Probe (post-Apply) | | probe seq |
| C16 | | Edit > Undo once | | |
| C17 | | Probe (after Undo) | | probe seq |
| C18 | | Set SmileClosed to 0.60 | | |
| C19 | | Probe; I8-Library library_C04_before_expr_save | | probe seq |
| C20 | | Save New Expression "I8 I8A1 C EXPR" | | |
| C21 | | I8-Readback C_expr_save; I8-Library library_C05_after_expr_save | | preset_readback/C_expr_save.json |
| C22 | | Set SmileClosed to 0.00 | | |
| C23 | | Probe (pre-Apply) | | probe seq |
| C24 | | Apply Preset (I8 I8A1 C EXPR) | | |
| C25 | | Probe (post-Apply) | | probe seq |
| C26 | | Edit > Undo once | | |
| C27 | | Probe (after Undo; idle) | | probe seq |
| D1 | | Probe (before Normalizer) | | probe seq |
| D2 | | I8-Library library_D01_before_normalizer | | |
| D3 | | Select only shot3 (sole Selected shot); Normalizer Rebuild Selected Shots once; wait for the final report | | |
| D4 | | I8-CollectLogs D_after_normalizer | | logs/D_after_normalizer.json |
| D5 | | Probe (after Normalizer) | | probe seq |
| D6 | | Same CPM window, no reselection: set Fat to 0.30 | | |
| D7 | | Probe (pre-Apply) | | probe seq |
| D8 | | Apply Preset (I8 I8A1 C BODY) | | |
| D9 | | Probe (post-Apply) | | probe seq |
| D10 | | Save New Body "I8 I8A1 D BODY" | | |
| D11 | | I8-Readback D_body_save; I8-Library library_D02_after_save | | preset_readback/D_body_save.json |
| D12 | | Edit > Undo once (the D8 Apply) | | |
| D13 | | Probe (after Undo; idle) | | probe seq |
| E1 | | Probe (G1 scope, idle) | | probe seq |
| E2 | | I8-Library library_E1_before_prompt | | |
| E3 | | Save New Body; type "I8 I8A1 E STALE"; leave the prompt OPEN | | |
| E4 | | I8-GenerationSwitch (prompt still open) | | generation/, library_E2_g2_active_prompt_open |
| E5 | | Confirm the open prompt; refusal dialog; OK; no reselection; wait for counts | | |
| E6 | | Probe (after rebuild) | | probe seq |
| E7 | | I8-Library library_E3_after_refusal; two I8-LibraryCompare | | |
| E8 | | Save New Body "I8 I8A1 E G2" | | |
| E9 | | Probe | | probe seq |
| E10 | | I8-Readback E_g2_save; I8-Library library_E4_after_g2_save | | preset_readback/E_g2_save.json |
| F1 | | Close CPM with Escape | | |
| F2 | | Probe (closed) | | probe seq |
| F3 | | Launcher; select mia1; wait for counts | | |
| F4 | | Probe (reopened under G2) | | probe seq |
| F5 | | Leave idle about 30 s; probe | | probe seq |
| F6 | | Close CPM with the title-bar X; settle; probe | | probe seq |
| F7 | | Exit SFM without saving | | |
| F8 | | I8-CollectLogs F_final; I8-Finalize; I8-RemoveQualificationDeployment | | logs/, generation/, restoration/ |
| F9 | | Adjudication, then I8-Disposition (PASS / FAIL / INCONCLUSIVE) | | restoration/disposition.json, SHA256SUMS.txt |

## Notes

(Anything unexpected, with the time. Do not interpret here; adjudication is separate.)

### OWNER-1 disposition (recorded 2026-10-08 13:43, before I8-Preflight)

Owner decision (verbatim): The historical full CPM builds in `sfm/mainmenu/SFM_CSP_G*`,
`sfm/mainmenu/SFM_Character_Slider_Preset_Tool_*` and historical package copies in
`sfm/gate_r*_deploy/` are **accepted as known inert members of the exact Scripts baseline under
which Sessions 1-4 ran**. For item 8: leave them present; do not delete them; do not relocate them;
do not modify them; do not invoke them; do not import authority from them.
OWNER-1 applies only if I8-Preflight proves the Scripts inventory is exactly the accepted Session-4
closeout inventory. If those historical files differ from the accepted baseline, or if any historical
package/script is actually loaded or used as authority rather than merely present on disk, STOP.
OWNER-1 does not waive any other preflight gate.

### Fixture authority (owner decision, checkpoint d4ad3cf)

`testscripts.dmx` (SHA-256 197e6011faae2da539d0a06ae4924288104b956348cd1c4e0ef80618f9e4e16f) for both
contexts: Krystal = shot10, Mia/Normalizer = shot3. S0.2 (2026-10-08 13:43): I8-New recorded both context
hashes equal to the pin.

### Shell steps

- S0.3 (2026-10-08 13:44): I8-Preflight I8A1 -Owner1Recorded -> S2 BASELINE OK, LIBRARY INVENTORY WRITTEN, I8 PREFLIGHT OK (Scripts inventory = accepted cefc2b88...).
- S0.4 (2026-10-08 13:44): I8-Deploy I8A1 -> I8 DEPLOYED (installed bfba4d3a..., probe f503c0ab..., backup 9a78fc96..., pointer I8A1). SFM was closed throughout.
- A1 (reported 2026-10-08 13:50): operator: "Shot10 is current. No errors." SFM process sfm.exe PID 36912 (one process). Animation-set listing not yet reported.
- A1 (confirmed 2026-10-08 13:50): operator confirms krystal20201, assaultsuitbody1, loinclothbra_chadfix_071 listed in the Animation Set Editor with shot10 current.
- A2 (13:50:56): probe seq=1 written (pid 36912, impl_is_candidate=True, module absent, runtime absent, errors={}). Note: the CPM_ITEM8_PROBE summary line did not appear in the SFM console (only "Running script ..."); the on-disk record and snapshot are present and verified by the reviewer after each probe.
- A3 (13:56:39): launcher -> one CPM window, no error (operator). CPM log: G18AN_RUN run_id 20261008-135639-pid36912, PROD_R15_MODULE build bfba4d3a... state ready, PROD_WINDOW_SHOWN=True. SFM console shows no script output; CPM log used instead.
- A4 (13:57:35-13:57:37): selected krystal20201; counts appeared in ~2 s, no warning (operator). Log: PROD_PROVIDER_HEALTH healthy sha256 ac45e5c1..., scope-ready, body=26 expression=52 other=2 unresolved=0 conflict=0.
- DEVIATION (13:58:51): operator ran Scripts > ChadChan3D > CPM_Session1_Probe once before A5 (runbook rule 5). Evidence: installed probe v3 ce4ace98 (pinned); its record seq=72 shows timing skipped (disabled), harness disabled (flag absent), broker 0x310a7810 counters identical before/after (leases 0, open 0, opens 1, closes 1). Side effects: one line appended to %PUBLIC%\Documents\CPM_Session1_Probe.jsonl; its helper names left in __main__ (main_dict_size 60 -> 86; cpm_names_in_main still []). No acquisition, no CPM state change observed. Recorded for adjudication; campaign continues.
- A5 (13:58:59): probe seq=2 OK (module 0x30b6b490 bfba4d3a ready, window 0xce494350 owned, census 1/1, healthy G1 scope, idle 0/0/0, historical inactive, errors {}).
- A6 (14:00:37): second launcher click; window already on top, no new window/notice/error (operator). Log: one PROD_R15_WINDOW_REUSED, same run_id; no new module load or Select Model.
- A7 (14:04:27): probe seq=3; identical module/class/run/window/scope/broker counters to A5 (no acquisition by reuse); idle; snapshot: krystal20201, assaultsuitbody1, loinclothbra_chadfix_071 present with matching identity; Undo count 0.
- Operator instruction (14:05): silence after a step means the step went as specified.
- B1 (14:05): Clothing Fit tab; only assaultsuitbody1 checked (operator: done).
- B2 (14:05:56): probe seq=4 pre-Fit snapshot (source, target, peer; Undo count 0); idle.
- B3 (14:07:29-14:07:31): Fit Selected to Model -> "1 item updated." (operator). Log: authorized G1; stage open literals=34; committed-verified mappings=26 warnings=7; one release ok=True; CLOTHING_FIT_RESULT changed=1 partial_changed=1 failed=0 unattempted=0; G18AN_POST_FIT_ACTION_STATE present.
- B4 (14:08:44): probe seq=5: assaultsuitbody1 changed (Breastsize, Muscles, slim); krystal20201 and loinclothbra_chadfix_071 unchanged; Undo "Clothing Fit: assaultsuitbody1" (count 0->30); idle 0/0/0, opens/closes 2/2.
- B5 (14:10): Edit > Undo once; assaultsuitbody1 visibly returned (operator).
- B6 (14:11:17): probe seq=6: all three sets equal B2 (0 changed); Undo count 0; idle 0/0/0.
- B7 (14:13): CPM closed with title-bar X; settled (operator).
- B8 (14:15:04): probe seq=7 closed-idle: slot empty, census 0/0, watchers 0, module resident ready/idle, broker 0/0/0. Log: PROD_CLOSE_REQUEST (no op/fit/stage) then PROD_CLOSE_FINALIZED=True at 14:13:12.
- C1 (14:20): playhead moved into shot3 (no clip click); operator confirms foxmccouldwm1 and mia1 listed. CPM closed throughout; document not reopened or saved.
- Finding (14:2x, for K/L): CPM resolves the scene from the shot under the playhead (sfmApp.GetShotAtCurrentTime), not the Clip Editor selection; the Normalizer uses the selection. Not communicated to users; record for K/L, no item-8 change.
- C2 (14:21:36): probe seq=8 closed on shot3: mia1 present, identity matches (checksum confirmed live); idle; Undo count 0.
- C3 (14:22:46-14:22:54): launcher -> new window, same run_id; selected mia1 (~3 s, operator). Log: healthy G1, 108 literals, body=46 expression=58 other=4 unresolved=0 (equals offline derivation).
- C4 (14:25:24): probe seq=9: same module/class/run, new window 0x310bea30, census 1/1, healthy G1 scope 46/58, idle; Fat=0.0, SmileClosed=0.0.
- C5 (14:26): Fat set to ~0.50 in the Animation Set Editor (operator).
- C6 (14:27:24): probe seq=10: Fat=0.5 (only change vs C4); I8-Library library_C01_before_body_save (= preflight, 9 files).
- C7 (14:32:42): Save New "I8 I8A1 C BODY" -> "Body Preset saved." (operator); PROD_SAVE=PASS controls=46, authorized G1.
- C8 (shell): I8-Readback C_body_save (preset-b41e5, Fat mono 0.5 = C6); I8-Library library_C02 (diff: +preset, character.json/.bak changed; within footprint).
- C9 (14:33:26): Fat set to ~0.80; probe seq=11: Fat=0.8000000119 (only change); idle.
- C10 (14:34:45): Update Preset -> updated (operator); PROD_UPDATE=PASS, authorized G1.
- C11 (shell): I8-Readback C_body_update (Fat 0.8000000119 = C9); library_C03 (preset changed + its .bak; within footprint).
- C12 (14:37): Fat set to ~0.20 (operator).
- C13 (14:37:22): probe seq=12 pre-Apply: Fat=0.1999999881; Undo count 14 "Modify Fat"; idle.
- C14 (14:44): Apply Preset I8 I8A1 C BODY -> "Body Preset applied." (operator).
- C15 (14:45:36): probe seq=13: Fat=0.8000000119 = C_body_update readback; only Fat changed vs C13; Undo top "Apply Body Preset" (14->17); idle.
- C16 (14:47): Edit > Undo once; Fat visibly returned (operator, as specified).
- C17 (14:48:20): probe seq=14: snapshot equals C13 (0 changed of 108); Undo back to count 14 "Modify Fat"; idle.
- C18 (14:49): SmileClosed set to ~0.60 (operator).
- C19 (14:50:06): probe seq=15: SmileClosed=0.6000000238 (only change); library_C04 = library_C03 (Apply/Undo wrote nothing to the library).
- C20 (14:50:37): Save New Expression "I8 I8A1 C EXPR" -> saved (operator); PROD_SAVE=PASS controls=58, authorized G1.
- C21 (shell): I8-Readback C_expr_save (preset-9b778, SmileClosed 0.6000000238 = C19); library_C05 (+preset, character.json/.bak; within footprint).
- C22 (14:51): SmileClosed set to ~0.00 (operator).
- C23 (14:51:33): probe seq=16 pre-Apply: SmileClosed=0.0 (only change vs C19); Undo count 22 "Finish Floating Modification Layer"; idle.
- C24 (14:52): Apply Preset I8 I8A1 C EXPR (operator, as specified).
- C25 (18:58:44): probe seq=17: SmileClosed=0.6000000238 = C_expr_save readback; only change vs C23; Undo top "Apply Expression" (22->25); idle. (Gap 14:52-18:58 between C24 and C25; same process confirmed.)
- C26 (19:15): Edit > Undo once (operator, as specified).
- C27 (19:15:34): probe seq=18: snapshot equals C23 (0 changed); Undo back to 22; idle 0/0/0; historical inactive.
- D1 (19:25:53): probe seq=19 idle, broker 0x310a7810 counters 3/3.
- D2 (shell): I8-Library library_D01_before_normalizer (= C05). Normalizer log before run: 39361 bytes, 2026-09-30, sha 1bf88545....
- D3 (19:29:30-19:29:55): shot3 sole selected; Normalizer Rebuild Selected Shots once (operator: succeeded; no completion prompt appeared). Normalizer log: SELECTED_SHOTS 1 [shot3], 2 eligible targets, REBUILD PASS, CONTEXTUALIZER PASS, mem_ok True 15/False 0, live Master G1, no CPM lines. CPM log: MODAL_YIELD_ENTER RebuildScopeDialog / EXIT restored=True.
- Finding (for K): Normalizer gives no visible completion confirmation on success; recommend non-blocking success notice, modal only for failures/decisions.
- D4 (shell): I8-CollectLogs D_after_normalizer.
- D5 (19:32:15): probe seq=20: same broker 0x310a7810 serving cpm_compat_v1 + normalizer_compat (opens/closes 4/4), idle 0/0/0; CPM module/window/scope unchanged; private +~9 MB vs D1.
- D6 (19:33): same CPM window, no reselection; Fat set to ~0.30 (operator).
- D7 (19:37:24): probe seq=21 pre-Apply: Fat=0.3000000119 (only change vs D5); Undo 28 "Modify Fat"; idle.
- D8 (19:39): Apply Preset I8 I8A1 C BODY in same window, no reselection (operator, as specified).
- D9 (19:39:55): probe seq=22: Fat=0.8000000119 = Phase C update readback; only Fat changed vs D7; Undo top "Apply Body Preset" (28->31); idle; same window.
- D10 (19:41): Save New "I8 I8A1 D BODY" (operator, as specified).
- D11 (shell): I8-Readback D_body_save (preset-a0b83, Fat 0.8000000119 = D9); library_D02 (+preset, character.json/.bak; within footprint).
- D12 (19:42): Edit > Undo once (operator, as specified).
- D13 (19:43:01): probe seq=23: snapshot equals D7; Undo back to 28; idle; since Normalizer: 0 refusals, 0 stale-generation events, 0 scope-begin.
- E1 (19:44:13): probe seq=24: healthy G1 scope (ac45e5c1), idle 0/0/0.
- E2 (shell): I8-Library library_E1_before_prompt (= D02, 13 files, 799b314f...).
- E3 (19:45:57): Save New prompt open with "I8 I8A1 E STALE" typed; not confirmed (operator).
- E4 (shell, 19:46:4x): I8-GenerationSwitch -> S2 PHASE A OK, S2 G2 ACTIVE OK (ac45e5c1 -> 54413b6c at 19:46:45), library_E2 = E1. Save Current Body began 19:45:32 (under G1); CPM log quiet since.
- E5 (19:52:43-19:52:56): confirmed prompt; refusal "Can't save preset" dismissed; counts returned (operator, as specified). Log: Q2_SAVE_POST_CONFIRM -> AUTHORIZATION_REFUSED Save Preset generation-mismatch -> no PROD_SAVE, durable_commit=None -> REBUILD_SCHEDULED -> REBUILD -> one automatic Select Model, healthy G2 54413b6c.
- E6 (19:53:58): probe seq=25: G2 scope 54413b6c in same window 0x310bea30; idle 0/0/0 (opens/closes 7/7); scene and Undo unchanged vs E1.
- E7 (shell): library_E3 written; E1 == E3 and E2 == E3 (LIBRARY IDENTICAL x2); no E STALE file.
- E8 (20:01): Save New "I8 I8A1 E G2" (operator, as specified).
- E9 (20:01:56): probe seq=26: G2 scope, idle 0/0/0.
- E10 (shell): I8-Readback E_g2_save (preset-c8ac9, Fat 0.3000000119 = live); library_E4 (+preset, character.json/.bak; within footprint).
- F1 (20:03): Escape with CPM focused; window closed (operator, as specified).
- F2 (20:04:42): probe seq=27 closed: slot empty, census 0/0, watchers 0, broker idle 0/0/0. Log: PROD_CLOSE_REQUEST + PROD_CLOSE_FINALIZED=True at 20:03:12.
- F3 (20:06): launcher, selected mia1, counts appeared (operator, as specified).
- F4 (20:07:35): probe seq=28: same module/class/run; new window 0x30b87418; census 1/1, 1 watcher; healthy G2 scope 54413b6c; idle.
- F5 (20:09): idle ~30 s then probe (operator, as specified).
- F6 (20:15): title-bar X close, settle, probe (operator, as specified).
- F7 (20:20): SFM exited; save declined (operator).
- F8 (shell, 20:20): I8-CollectLogs F_final; I8-Finalize -> S2 RESTORED EXACT G1; I8-RemoveQualificationDeployment.
- F9 adjudication (2026-10-08 20:22): mechanical checks 34/34 PASS over 30 probe records, CPM log excerpt, Normalizer log, generation and library records; all six phases PASS in PID 36912; one recorded procedural deviation (CPM_Session1_Probe before A5) with evidence of no effect. Verdict: PASS.
