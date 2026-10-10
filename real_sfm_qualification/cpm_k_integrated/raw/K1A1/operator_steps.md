# K operator record — attempt `K1A1`

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
- 17:57:19 K1-S1 shell: K-New K1A1 (fixture pin OK); K-Preflight K1A1 -Owner1Recorded -> S2 BASELINE OK, K PREFLIGHT OK (expected inventory 59b8f28b..., exact G1, deps exact); K-DeployProbe -> K READY (only +CPM_K_Probe.py 96d873b7...; app 4e35f292... unchanged). CPM log offset 765057. SFM was closed (no U3 process open).
- 23:52:13 K1-S2/S3 (22:29:09): operator opened testscripts.dmx in a fresh SFM (PID 19800), selection only shot9, playhead shot9, ran the probe once. Probe seq=1: no CPM module, no broker, no acquisition, identity OK, errors {}; resources private 3076964352, avail_virtual 528838656 (total_virtual 4294836224), handles 1157, GDI 1121, USER 100.
- 23:52:13 STOP (design section 5.4): free VAS 528 MB < 600 MB at the baseline probe, before either product consumer executed. No CPM or Normalizer action was performed in K1A1.
- 23:52:13 OWNER DECISION (verbatim classification): K1A1 is INCONCLUSIVE -- qualification-tooling false STOP before either product consumer executed. This is not a CPM or Normalizer failure. The fresh fixture-loaded process had 528 MB free VAS before any consumer ran, while prior successful Item-8 evidence includes a Normalizer run beginning with only 421 MB free VAS and mem_ok=True. The fixed VAS < 600 MB STOP is invalid and is removed by a K-0 amendment; K1A1 is not reused; K1 continues as a new attempt K1A2. SFM closed with Don't Save.
