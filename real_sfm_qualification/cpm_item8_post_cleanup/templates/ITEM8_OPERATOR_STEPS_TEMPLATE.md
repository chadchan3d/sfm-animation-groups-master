# CPM item 8 - operator record, attempt `<attempt>`

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
| C7 | | Save New Body "I8 <attempt> C BODY" | | |
| C8 | | I8-Readback C_body_save; I8-Library library_C02_after_body_save | | preset_readback/C_body_save.json |
| C9 | | Set Fat to 0.80; probe | | probe seq |
| C10 | | Update Preset (I8 <attempt> C BODY) | | |
| C11 | | I8-Readback C_body_update; I8-Library library_C03_after_body_update | | preset_readback/C_body_update.json |
| C12 | | Set Fat to 0.20 | | |
| C13 | | Probe (pre-Apply) | | probe seq |
| C14 | | Apply Preset (I8 <attempt> C BODY) | | |
| C15 | | Probe (post-Apply) | | probe seq |
| C16 | | Edit > Undo once | | |
| C17 | | Probe (after Undo) | | probe seq |
| C18 | | Set SmileClosed to 0.60 | | |
| C19 | | Probe; I8-Library library_C04_before_expr_save | | probe seq |
| C20 | | Save New Expression "I8 <attempt> C EXPR" | | |
| C21 | | I8-Readback C_expr_save; I8-Library library_C05_after_expr_save | | preset_readback/C_expr_save.json |
| C22 | | Set SmileClosed to 0.00 | | |
| C23 | | Probe (pre-Apply) | | probe seq |
| C24 | | Apply Preset (I8 <attempt> C EXPR) | | |
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
| D8 | | Apply Preset (I8 <attempt> C BODY) | | |
| D9 | | Probe (post-Apply) | | probe seq |
| D10 | | Save New Body "I8 <attempt> D BODY" | | |
| D11 | | I8-Readback D_body_save; I8-Library library_D02_after_save | | preset_readback/D_body_save.json |
| D12 | | Edit > Undo once (the D8 Apply) | | |
| D13 | | Probe (after Undo; idle) | | probe seq |
| E1 | | Probe (G1 scope, idle) | | probe seq |
| E2 | | I8-Library library_E1_before_prompt | | |
| E3 | | Save New Body; type "I8 <attempt> E STALE"; leave the prompt OPEN | | |
| E4 | | I8-GenerationSwitch (prompt still open) | | generation/, library_E2_g2_active_prompt_open |
| E5 | | Confirm the open prompt; refusal dialog; OK; no reselection; wait for counts | | |
| E6 | | Probe (after rebuild) | | probe seq |
| E7 | | I8-Library library_E3_after_refusal; two I8-LibraryCompare | | |
| E8 | | Save New Body "I8 <attempt> E G2" | | |
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
