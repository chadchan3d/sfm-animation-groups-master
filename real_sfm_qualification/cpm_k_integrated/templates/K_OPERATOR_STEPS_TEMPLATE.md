# K operator record — attempt `<attempt>`

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
