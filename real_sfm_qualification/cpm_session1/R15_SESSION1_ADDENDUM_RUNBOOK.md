# CPM R15 — real-SFM Session 1 addendum runbook

Authoritative design: `cpm/qualification/R15_IMPLEMENTATION_BLUEPRINT.md` (§12, with Clarification B).
This addendum is required before R15 can close; Session 2 stays blocked until it passes.

> **Status (2026-09-30): executed — PASS.** Results: `R15_SESSION1_ADDENDUM_EVIDENCE.md`; raw outputs:
> `real_sfm_qualification/cpm_session1/r15_addendum/`. The procedure below is unchanged.

Record actual results only, in `R15_SESSION1_ADDENDUM_EVIDENCE.md`; put raw outputs under
`real_sfm_qualification/cpm_session1/r15_addendum/`.

## 0. Deployment mapping

`<SFM game>` is the SFM `game` folder (the folder containing `sfm.exe`). Copy exact bytes; verify
every SHA-256 after copying.

| Repository source | Installed path | SHA-256 |
|---|---|---|
| `cpm/app/launcher/SFM_Character_Preset_Manager.py` | `<SFM game>/usermod/scripts/sfm/mainmenu/ChadChan3D/SFM_Character_Preset_Manager.py` (**replaces** the current full app `664a660c…`) | `996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51` |
| `cpm/app/SFM_Character_Preset_Manager.py` | `<SFM game>/usermod/scripts/ChadChan3D_CPM/SFM_Character_Preset_Manager.py` (new folder; **no** `__init__.py`; nothing else in it) | `9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900` |
| `real_sfm_qualification/cpm_session1/CPM_Session1_Probe.py` (v3) | `<SFM game>/usermod/scripts/sfm/mainmenu/ChadChan3D/CPM_Session1_Probe.py` (replaces v2 `0722610a…`) | `ce4ace980ee2cf62c43de13a1686152019b025d4f2d776e3c80c45529283c7e3` |
| Step 9 only: `cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py` | `<SFM game>/usermod/scripts/sfm/mainmenu/ChadChan3D/SFM_CSP_G18AN_SaveNewCopy.py` — deploy for step 9, **remove** afterwards | `3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e` |

Unchanged and not redeployed, but verify their hashes in `mainmenu/ChadChan3D`:

| File | SHA-256 |
|---|---|
| `cpm_authority_adapter.py` | `e96e21b5…` |
| `cpm_compat_v1_projection.py` | `9b077a1b…` |
| `Rebuild_Control_Groups_Normalizer.py` | `1f4ec5a2…` |

Also unchanged: the shared package and the Master (`ac45e5c1…`). Do not regenerate the sidecar.

No other copy of the CPM implementation may exist anywhere under `<SFM game>/usermod/scripts/sfm/`,
including `animset/`.

## Rules

- **Session:** use a fresh SFM process and the established qualified fixture scene. Use disposable
  qualification data for Save; do not edit the Master or sidecar.
- **Settling:** "settle" means wait until CPM is idle and then about 10 s more before running the
  probe.
- **Probe checkpoints:** a **P#** means run `CPM_Session1_Probe` from the Scripts menu.
  - It appends to `%PUBLIC%\Documents\CPM_Session1_Probe.jsonl`.
  - It prints `CPM_SESSION1_PROBE` and `CPM_R15_PROBE` lines to the SFM console.
  - Write down the time of each P#.
- **Launcher console:** each launcher click prints `[ChadChan3D CPM launcher] outcome=… code=…` to
  the SFM console. Copy those lines at each step if you can.
- **Resource telemetry (Clarification B):** record the probe's `memory_after` values at each
  telemetry point:
  - `working_set`, `private_usage`, `handles`, `gdi_objects`, `user_objects`.

  The telemetry points are: initial open (P3), second click (P4), each reopen (P7b/P8b/P9b) and the
  final settled state (P10). The purpose is an accumulation trend; there is no MB threshold.

## Sequence

1. **Deployment and identities.** Deploy per §0 and verify every hash. The probe's `python` field
   must read `2.7.5`.
   - **Scripts > ChadChan3D** shows `SFM_Character_Preset_Manager` (the launcher) and no
     `ChadChan3D_CPM` entry.
   - The animation-set right-click menu shows no CPM entry.
2. **Host context (observation).** Fresh SFM, with the fixture loaded.
   - **P1** and **P2**, run twice. Expect:
     - `r15.probe_globals_is_main_dict: true`;
     - `cpm_names_in_main: []`;
     - `r15.module.present: false`;
     - `deployed_launcher_sha256` and `deployed_impl_sha256` equal to §0.
3. **Open CPM and establish an active scope.** Launcher click → select the character → wait for the
   Body / Expression / Review counts → settle.
   - **P3 (telemetry: initial open).** Expect:
     - `module.state: ready`, `module.build_sha256 = 9a78fc96…`,
       `file_is_deterministic_impl_path: true`;
     - `window.owned_by_private_module: true`, `function_globals_is_private_module: true`;
     - census: 1 ProdWindow, 1 watcher;
     - broker present, `outstanding_leases 0`, `current_open_provider_count 0`.
   - Then perform the established Apply/Save baseline:
     - Save one disposable Body preset;
     - Apply an existing Body preset.
4. **Click the launcher again.** The same CPM window comes forward; the console shows
   `outcome=reused`.
   - **P4 (telemetry: second click).** Compared with P3, the following are unchanged:
     - `module.id`, `window.id`, `run_id`, `prodwindow_class_id`, `startprodtool_id`;
     - the scope;
     - the broker provider counters and ledger (no acquisition caused by reuse).

     Census stays 1 ProdWindow / 1 watcher.
5. **Run one production Normalizer command** (`Rebuild_Control_Groups_Normalizer`) with CPM still
   open on its active scope.
   - Complete its normal prompts and respect its admission guard.
   - Its log must show `mem_ok=True` at its checkpoints.
   - Run it once only.
6. **Return to the same CPM window and existing scope, without reselecting.** Run a normal Apply,
   then Save a disposable preset.
   - **PASS requires both to succeed** with the existing semantic checks.
   - A stale-authority or stale-scope refusal is **not** PASS.
   - Any other legitimate scene-state refusal: stop and report it for adjudication.
   - **P5.** Expect:
     - the same broker;
     - `consumers_served` includes `cpm_compat_v1` and `normalizer_compat`;
     - leases 0 and providers 0;
     - module and window identities unchanged;
     - `cpm_names_in_main: []`;
     - `module.output_path` is the CPM log.
   - **Logs:**
     - CPM's Apply/Save lines are in `SFM_CSP_G18AN_SaveNewCopy.log`;
     - `sfm_rebuild_control_groups.txt` has no CPM `PROD_…` lines after the Normalizer ran.
7. **Three close/reopen cycles.**
   - **Closes:** cycle 1 uses the title-bar ✕; cycles 2 and 3 use **Escape** with CPM focused.
   - **Per cycle, after the close:** settle, then run **P7a / P8a / P9a**. Expect:
     - the window slot empty;
     - census 0 ProdWindow, 0 watchers;
     - leases 0 and providers 0;
     - the CPM log shows exactly one new `PROD_CLOSE_REQUEST` and one new `PROD_CLOSE_FINALIZED`.
   - **Per cycle, reopen:** launcher click → CPM opens (`outcome=created`) → settle → run
     **P7b / P8b / P9b (telemetry: cycle 1/2/3)**. Expect:
     - the same `module.id`, `run_id` and `prodwindow_class_id`;
     - a new `window.id`;
     - census 1 ProdWindow / 1 watcher;
     - no orphan window, watcher or queued Fit activity.

     Do not rely on `window.id` alone: ids can be reused.
   - **P10 (telemetry: final settled).** Leave CPM idle and open for about 30 s, then probe.
8. **Notice lifetime.**
   1. Close CPM with ✕. Create an empty file `%PUBLIC%\Documents\CPM_R15_NOTICE_HARNESS.txt`.
   2. **P11:** the probe installs its hidden placeholder (`r15_harness.action:
      installed-placeholder`).
   3. Click the launcher. Expect one non-modal notice: "Another Character Preset Manager window (a
      different build) is open…".
      - SFM stays usable while the notice is shown.
      - No CPM window appears.
   4. Click **OK**, then click the launcher again. The same notice reappears; there is still only
      one.
   5. **P12:** `census.launch_notices: 1`, `notice_slot.modal: false`; the probe then removes its
      placeholder (`removed-placeholder`).
   6. Delete the flag file. Click the launcher: CPM opens.
   7. **P13:** 1 ProdWindow, 1 notice widget at most, same `module.id`.

   The harness touches only the window-slot attribute, never the broker, authority or scene.
9. **Separate fresh-process legacy-slot check.**
   1. Close SFM. Archive the three logs and the probe JSONL into the evidence folder.
   2. Deploy the G18AN copy (§0) and start a fresh SFM.
   3. Run `SFM_CSP_G18AN_SaveNewCopy` from the Scripts menu, which opens the legacy window.
   4. Click the CPM launcher. Expect a refusal notice, with the G18AN window still open and
      unchanged.
   5. **P14.**
   6. Close G18AN normally. Click the CPM launcher: the isolated CPM opens.
   7. **P15:**
      - `window.owned_by_private_module: true`, `function_globals_is_private_module: true`;
      - `cpm_names_in_main` may now list G18AN's own names; that is expected.
   8. Do **not** run the Normalizer in this check. Remove the G18AN copy from the menu afterwards.

## Failure criteria (R15 stays OPEN)

- namespace contamination;
- module replacement;
- a duplicate live CPM window;
- reset lifecycle state (run ID, counters);
- an incorrect log destination;
- a failed intended Apply/Save continuation after the Normalizer;
- a broken close or unwind;
- leaked authority ownership (a non-zero lease or provider when idle);
- a modal refusal loop.

No build-generation transition is part of this addendum. Stop and report at the first failure.

## Return

Return the following:
- the probe JSONL;
- `SFM_CSP_G18AN_SaveNewCopy.log`;
- `sfm_rebuild_control_groups.txt` (plus the step 9 archive);
- the copied launcher console lines;
- one note per step: done / skipped (why) / problem.
