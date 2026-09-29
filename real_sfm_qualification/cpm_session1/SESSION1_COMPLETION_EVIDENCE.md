# CPM Real-SFM Session 1 — completion run evidence and closeout

**Sources:**
- `CPM_Session1_Probe.jsonl`: seq 12–20, probe v2 `0722610a…`;
- `SFM_CSP_G18AN_SaveNewCopy.log`;
- `sfm_rebuild_control_groups.txt`;
- the owner's operator/visual observations.

**Build:** app `664a660c…` (R14 fix), adapter `e96e21b5…`, projection `9b077a1b…`, Normalizer
`1f4ec5a2…`, Master `ac45e5c1…`.

**Process:** a fresh SFM process, pid 24684, one broker `0xc9318070` for the whole run. A later,
separate process (pid 20792) made one owner check.

## Timeline (2026-09-29)

| Time | Evidence | Event |
|---|---|---|
| 00:28:20 | seq 12 | Before CPM: no runtime, no broker; memory valid (working set 3.047 GB, private 3.093 GB) |
| 00:28:27 | CPM log | CPM opened. `prod_resource_snapshot` logged real memory values: the point where the pre-fix code polluted the shared ctypes prototypes |
| 00:28:37 | seq 13 | CPM window open (converged); no character selected yet; runtime not yet loaded |
| ~00:28:47 | Normalizer log | **Normalizer run with the CPM window open** (no CPM scope yet): `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`; **`mem_ok=True` at 13/13 checkpoints** (0 False) |
| 00:29:22 | seq 14 | Broker `0xc9318070`; served `normalizer_compat`; CPM window open; leases 0; open providers 0 |
| 00:31–00:34 | Normalizer log (see R15) | In the still-open CPM: selected Krystal, Body Save, Favorite. Four Applies of an old preset were refused ("unsupported Head Scale data"); one Body Apply committed. CPM closed at 00:34:08 |
| 00:33:52 | seq 15 | Same broker; both `cpm_compat_v1` and `normalizer_compat` views cached; leases 0; Krystal scope (80 literals, 0 miss, 0 conflict) |
| 00:34:36 | CPM log | CPM reopened |
| 00:36:57 | CPM log | **Body Update** `PROD_UPDATE=PASS` |
| 00:44:40 | CPM log | Ayane model (70 literals, 15 Master-unknown): **Review** `PROD_OVERRIDE_SET` + `PROD_REVIEW_REFRESH=PASS` |
| 00:45:52 | CPM log | **Reclassify** `PROD_OVERRIDE_CLEAR` + `PROD_RECLASSIFY_REFRESH=PASS durable_edit=True returned_to_review=True` |
| 00:47:52–00:48:13 | CPM log | Body Save "Thin"; three Body Applies committed |
| 00:48:15 | CPM log | **Clothing Fit** (see below) |
| 00:48:43 | seq 20 | Same broker; leases 0; open providers 0; ledger retained 665,731 B |
| 01:02:57 | CPM log, pid 20792 | Owner check: Body Apply of a current bone-scale preset committed (`changed_existing_scales=1`) |

## Clothing Fit evidence (target `assaultsuitbody1`, source `krystal20201`)

1. **Gfit** was authorized once for the Body membership of 26 source literals.
2. The stage opened with **34 literals**: 26 source plus the target's own vocabulary. The target
   vocabulary exceeded the source's, so target-only controls were genuinely included in the
   authority stage.
3. The real planner produced **26 valid source→target mappings**. Its 7 warnings are the
   unmatched target controls under the existing exact Body Morphs / Clothing rule.
4. The stage **committed and verified** (`committed-verified`). The stage lease was **released**
   (`ok=True`) before the result was reported. The result was `CLOTHING_FIT_RESULT=PASS changed=1
   failed=0 unattempted=0`.
5. **Undo:** the owner observed the target visually restored. This is not logged.

## Verdicts (Session 1 final)

| Item | Status |
|---|---|
| Normal CPM operation (startup, canonical route, historical route unused, idle 0 leases/providers) | PASS |
| Native Apply + Undo (incl. no-op) | PASS (first run) |
| Body Save / Update | PASS |
| Expression Save / Update / Apply | PASS (first run) |
| Review / Reclassify | PASS |
| Ordinary Clothing Fit + Undo | PASS |
| C10 same-process broker | PASS (first run; confirmed again here with `0xc9318070`) |
| Simultaneous Normalizer coexistence | PASS, **as run**: the Normalizer ran while the CPM window was open *before* a character scope was selected. CPM remained usable afterwards |
| Resource / latency measurement | PASS (complete) |
| R14 ctypes isolation | **CLOSED (real SFM)** |

## Measurements (completion run)

- **Process memory:**
  - before CPM: working set 3.047 GB, private 3.093 GB;
  - end: working set 3.083 GB, private 3.125 GB;
  - about +36 MB working set across CPM, the Normalizer and all actions.
- **CPM pure scope:** 126,931 B (Krystal, 80 literals) and 107,307 B (Ayane, 70 literals).
- **Broker ledger retained:** 665,731 B at the end (Normalizer 253-fold view plus CPM views).
- **Latency:**
  - authorization 0.018–0.023 s;
  - stage open + release 0.017–0.021 s warm, 1.19–1.21 s cold;
  - scope build 1.233 s;
  - one Fit target 0.146 s end to end, including stage open, plan, mutation, verify and release.

## Findings

- **R15 (new; owner decision needed): SFM runs Scripts-menu scripts in a shared global
  namespace.**
  - After the Normalizer ran, the still-open CPM window's log lines (00:31:32–00:34:08) were
    written into the Normalizer's log file. The Normalizer had rebound the shared global
    `OUTPUT_PATH`.
  - The app and the Normalizer define 5 same-named globals: `OUTPUT_PATH`, `arr`, `handle`,
    `name` and `typ`. The four helpers differ:
    - the Normalizer's `handle(None)` raises;
    - its `typ(None)` returns `"NoneType"`;
    - its `arr` raises `ProbeError`.
  - So after a Normalizer run, CPM's callbacks run the Normalizer's versions; the reverse
    exposure also exists.
  - This session's CPM actions still behaved correctly, but it is a latent coexistence defect.
    It is inherited from G18AN-era script structure; it is not a convergence regression, and K
    covers alternation.
  - Not fixed here: no product changes in this closeout.
- **Legacy Apply error (UI finding, not a Session 1 failure):**
  - Cause: an old preset in the obsolete `body.scale.head` format. The existing refusal is "This
    old test preset contains unsupported Head Scale data. Delete it and save a new Body Preset."
  - Current generic bone-scale persistence works (pid 20792 Apply with `changed_existing_scales=1`).
  - Preferred future message: "This preset uses an outdated scale format. Delete this preset and
    save a new Body preset."
  - This is a legacy compatibility edge case, not a broader scaling defect.
