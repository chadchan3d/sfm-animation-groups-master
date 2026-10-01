# CPM R15 — real-SFM Session 1 addendum: evidence and verdict

- **Design:** `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` §12.
- **Procedure:** `R15_SESSION1_ADDENDUM_RUNBOOK.md`.
- **Date:** 2026-09-30.
- **Raw outputs:** `r15_addendum/`.
  - It holds exact addendum-span excerpts with two path prefixes redacted.
  - The SHA-256 of each original, excerpt and committed file is in `r15_addendum/MANIFEST.md`.

Every claim below comes from those files. Times are the local log times.

## Identities

| Item | Value |
|---|---|
| Implementation commit | `00d0d83c72fbbaa9a59816f607c1536033262efb` |
| Launcher (menu entry) | `996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51` — probe `deployed_launcher_sha256` matches in all 18 records |
| Private implementation `usermod/scripts/ChadChan3D_CPM/` | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` — probe `deployed_impl_sha256` matches; module `build_sha256` matches; `file_is_deterministic_impl_path: true` |
| Probe v3 | `ce4ace980ee2cf62c43de13a1686152019b025d4f2d776e3c80c45529283c7e3` |
| Python | 2.7.5 (every record) |

**Unchanged components** were re-hashed at closeout and match the pre-addendum deployment snapshot.
That snapshot covers the whole `usermod/scripts` tree and the sidecar store, and the step-9 G18AN
copy has been removed again.

| Component | SHA-256 |
|---|---|
| Normalizer | `1f4ec5a2…` |
| Adapter | `e96e21b5…` |
| Projection | `9b077a1b…` |
| Shared package | byte-unchanged |
| Master (`usermod/cfg`) | `ac45e5c1…` |
| Sidecar | byte-unchanged |
| Frozen baseline (repository) | `3326024d…` |

**Processes:**

| Process | Steps | Broker | Private module | Run ID |
|---|---|---|---|---|
| A, pid 25316 | 1–8 | `0x32922390` | `0x3224ee90` | `20260930-205622-pid25316` |
| B, pid 24884 | 9 (fresh process) | none loaded | `0xc87af110` | `20260930-215753-pid24884` |

## Checkpoint results

| P# | seq | Time | Result |
|---|---|---|---|
| P1 | 21 | 20:49:26 | PASS — probe globals are SFM's shared `__main__`; `cpm_names_in_main []`; private module absent; deployed hashes match |
| P2 | 22 | 20:49:49 | PASS — same as P1 |
| P3 | 23 | 20:57:54 | PASS — details below the table |
| P4 | 24 | 21:07:19 | PASS — details below the table |
| P5 | 25 | 21:13:18 | PASS — details below the table |
| P7a | 26 | 21:18:15 | PASS — after the title-bar close: slot empty; 0 ProdWindow / 0 watchers; leases 0 / providers 0 |
| P7b | 27 | 21:19:00 | PASS — reopened: same module/run/class/StartProdTool; new window `0x32a15fa8`; 1 window / 1 watcher |
| P8a | 28 | 21:21:35 | PASS — after Escape: slot empty; 0 / 0; leases 0 / providers 0 |
| P8b | 29 | 21:22:02 | PASS — reopened: same identities; new window `0x3211f530`; 1 / 1 |
| P9a | 30 | 21:35:20 | PASS — after the second Escape: slot empty; 0 / 0; leases 0 / providers 0 |
| P9b | 31 | 21:35:41 | PASS — reopened: same identities; new window `0x32a01e40`; 1 / 1 |
| P10 | 32 | 21:38:54 | PASS — about 3 min idle after P9b: same window, 1 / 1, leases 0 / providers 0, broker counters unchanged |
| P11 | 33 | 21:42:55 | PASS — slot empty (CPM closed at 21:41:58); harness `installed-placeholder` |
| P12 | 34 | 21:45:28 | PASS — details below the table |
| P13 | 35 | 21:47:25 | PASS — reopened at 21:47:11: same module `0x3224ee90`; 1 ProdWindow / 1 watcher; the retained notice widget still exists, hidden |
| P14 | 36 | 21:58:25 | PASS — details below the table |
| extra | 37 | 22:00:54 | Observational only, not P15 — details below the table |
| P15 | 38 | 22:01:43 | PASS — details below the table |

- **P3:**
  - private module `ready`, id `0x3224ee90`; window `0x32129ad0` owned by the private module;
    function globals are the private module (`function_globals_name chadchan3d_cpm_app`);
  - 1 ProdWindow / 1 watcher;
  - active Mia scope (`models/annoad/foxbase/mia/mia.mdl`; generation `ac45e5c1…`; 108 literals,
    0 miss, 0 conflict);
  - provider `canonical-broker-cpm-compat-v1`; broker `0x32922390`; leases 0; open providers 0.
- **P4:**
  - the second launcher click was logged as `PROD_R15_WINDOW_REUSED` at 21:06:48;
  - the same module, window `0x32129ad0`, run ID, `ProdWindow` class `0x31e639a8` and
    `StartProdTool` `0xc9a350b0`;
  - the same scope;
  - broker provider counters (opens 1 / closes 1) and ledger (123,230 B) identical to P3.

    The log has no `PROD_CPM_OPERATION_AUTHORIZED` between P3 and P4, so the reuse caused no
    authority acquisition.
- **P5:**
  - after the Normalizer run, the same module and window `0x32129ad0`, and the same scope
    (generation and counts identical);
  - same broker; `consumers_served` = `cpm_compat_v1` + `normalizer_compat`;
  - leases 0; providers 0;
  - `cpm_names_in_main []`, although the host dictionary grew from 85 to 280 names (the
    Normalizer's).
- **P12:**
  - placeholder in the slot (`owned_by_private_module false`);
  - **0 ProdWindow**;
  - exactly one launch notice, visible, `modal: false`;
  - no active modal; the probe ran while the notice was visible;
  - harness `removed-placeholder`.
- **P14 (process B):**
  - the slot holds the legacy G18AN window: `class_module __main__`, function globals = `__main__`,
    alive and visible;
  - the R15 private module is loaded (`ready`, `0xc87af110`);
  - 0 owned windows / 1 ProdWindow in total;
  - one non-modal notice, visible.
- **extra probe (process B):**
  - after the G18AN window was closed (22:00:36): slot empty, 0 windows / 0 watchers;
  - the private module is still `ready`, same identities;
  - no runtime loaded, so no authority was acquired; the probe changed no scene state.
- **P15 (process B):**
  - isolated CPM opened at 22:01:22;
  - `owned_by_private_module: true`, `function_globals_is_private_module: true`;
  - the same module `0xc87af110`, run ID, class `0x336cc748` and `StartProdTool` `0x33ab43b0` as
    P14;
  - 1 ProdWindow / 1 watcher.

  G18AN's own names remain in `__main__`, which the runbook expects.

## Active-scope CPM + Normalizer coexistence (step 5–6): PASS

**Normalizer run** (`sfm_rebuild_control_groups.txt`):
- one production Normalizer run, Rebuild Selected Shots: `scope_mode=SELECTED_SHOTS`, `shot3`,
  2 eligible targets (`foxmccouldwm1`, `mia1`);
- `PRODUCTION_REBUILD_CONTROL_GROUPS = PASS`, `PRODUCTION_CONTEXTUALIZER = PASS`;
- `mem_ok=True` 15 times, `mem_ok=False` 0 times;
- the CPM window yielded to its scope dialog from 21:10:02 to 21:11:07 (`G18AN_MODAL_YIELD_*`).

**CPM continuation**, in the same window and scope with no reselection (the only `Select Model` in
the run is at 20:56:40):

| Operation | Time | Result |
|---|---|---|
| Apply 5 | 21:11:12 | `no-op` |
| Apply 6 | 21:11:14 | `no-op` |
| Apply 7 | 21:11:22 | `committed` (BodyTest) |
| Apply 8 | 21:11:24 | `committed` (Body) |
| Save 9 | 21:13:01 | `PROD_SAVE=PASS` "R15 POST NORMALIZER", `semantic_scope_rebuild=False` |

- Every action was `PROD_CPM_OPERATION_AUTHORIZED` against `ac45e5c1…`.
- There is no stale-authority or stale-scope refusal and no scope rebuild (0 `stale` lines in the
  addendum log).

**Ordering observation (not a failure).** The Normalizer log was last written at 21:11:12.896, after
Apply 5 began (21:11:12.670). That last write is inside the Normalizer's post-verification final
reporting; its `END_OF_RUN_WHOLE_SESSION_ISOLATION` had already passed. Apply 5 was a no-op, with
`changed_flex=0` and no mutation.

The PASS rests on Applies 7–8 and Save 9, which all occur 9 s or more after the Normalizer's final
write. Run-to-run alternation stays with K.

## Log separation: PASS

- **Normalizer log:** CPM `PROD_` lines 0, `G18AN_` lines 0.
- **CPM log:** `CONTEXTUALIZER` lines 0, `PRODUCTION_` lines 0.
- **After the Normalizer:** CPM kept logging to its own log (Applies 5–8, Save 9); `module.output_path`
  is the CPM log in every record.

## Close / Escape lifecycle: PASS

- **Closes (process A):** all four closes (21:17:57, 21:21:20, 21:35:09, 21:41:58) log one
  `PROD_CLOSE_REQUEST operation=None` and one `PROD_CLOSE_FINALIZED=True`.
- **Opens:** each reopen logs one `PROD_WINDOW_SHOWN`.
- **Errors:** no `PROD_OPEN_FAIL` and no traceback.
- **Identity across the three cycles:**
  - the module, run ID and class are stable;
  - each reopen gives a new window lifecycle;
  - this is corroborated by the per-close log pairs, not by `id()` alone.
- **Probe readings after each close and reopen:**
  - no duplicate window or watcher;
  - no Fit activity;
  - leases 0 and providers 0 at every checkpoint.
- **Close method:** the log does not record whether a close came from the title bar or from Escape.
  The method per cycle (✕, Escape, Escape) is the operator procedure. The pre-R15 Escape path skipped
  `closeEvent` and logged neither line, so the presence of both lines on every close is consistent
  with the repair.

## Notice lifetime (step 8): PASS

- **Refusals:** two launcher clicks with the placeholder in the slot were refused:
  - `PROD_R15_LAUNCH_REFUSED code='refuse-foreign-window' detail="class='QDialog'"` at 21:44:40;
  - the same at 21:45:13.
- **Notice:** P12 shows exactly one notice widget, visible and non-modal, with no CPM window.
- **Afterwards:** CPM reopened normally (P13); the same widget was retained, hidden.

## Legacy slot (step 9, process B): PASS

- G18AN's own startup was logged at 21:57:44 (run `…215744-pid24884`).
- The R15 launcher click at 21:57:53 loaded the private module and refused:
  `refuse-foreign-window detail="class='ProdWindow'"`.
- At P14 the legacy window was still alive and visible, with one notice shown.
- G18AN was closed normally at 22:00:36. Then the isolated CPM opened (P15).
- No Normalizer run took place in process B.

## Resource trend (Clarification B, process A): no accumulation

Values are probe `memory_after`:

| Point | Working set | Private commit | Handles | GDI | USER |
|---|---|---|---|---|---|
| P3 initial open | 3,039.9 MB | 3,089.0 MB | 1164 | 1163 | 123 |
| P4 second click | 3,042.1 MB | 3,091.0 MB | 1164 | 1169 | 126 |
| P7b cycle 1 | 1,829.2 MB | 3,102.2 MB | 1079 | 1169 | 125 |
| P8b cycle 2 | 412.0 MB | 3,102.2 MB | 1078 | 1169 | 125 |
| P9b cycle 3 | 411.6 MB | 3,101.9 MB | 1075 | 1169 | 125 |
| P10 final settled | 402.4 MB | 3,101.8 MB | 1069 | 1169 | 124 |

- **P4 to P7b:** private commit rose by 11.2 MB. This span includes the Normalizer run (P5:
  3,100.7 MB).
- **Across the three close/reopen cycles (P7b to P10):** private commit −0.5 MB, handles −10, GDI 0,
  USER −1.
- **Working set:** fell sharply after the Normalizer. That is OS working-set trimming; private commit
  shows no matching drop.
- No hard threshold applies.

## Procedural deviations (benign; recorded, not hidden)

1. **Step 3 order:** the disposable baseline happened before P3 rather than after it.
   - Save "R15 TEMP" `PROD_SAVE=PASS` at 20:57:17; Apply `committed` at 20:57:37; P3 at 20:57:54.
   - The active-scope state and both successful operations are independently present.
2. **Extra probe between P14 and P15:** seq 37 was observation only. It is recorded above and not
   counted as P15.
3. **Launcher console transcript:** the SFM console `outcome=` lines were not retained. All acceptance
   facts above come from the probe JSONL and the logs.
4. **No separate pre-step-9 log archive:** the CPM log and probe JSONL are cumulative and contain
   both processes. The Normalizer log holds only the single addendum run.
5. **SFM exit modal at 21:49:08:** SFM's own exit confirmation (`QMessageBox 'SourceFilmmaker'`) was
   logged as a CPM modal yield while SFM was closing before step 9. This is expected watcher
   behaviour.

## Verdict

**Real-SFM Session 1 addendum: PASS.** Every Blueprint §12 step and failure criterion is satisfied by
the retained evidence:
- no namespace contamination;
- no module replacement;
- no duplicate live CPM window;
- no lifecycle-state reset;
- correct log destinations;
- the post-Normalizer Apply/Save continuation succeeded;
- clean close and unwind;
- no leaked authority ownership;
- no modal refusal loop.

Together with the offline gates (2.7.5: 345/345; 3.10: 188/188; all regressions PASS), **R15 is
CLOSED — PASS.**

Active-scope CPM + Normalizer coexistence is now proven in real SFM.
