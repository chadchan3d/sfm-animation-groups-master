# SFM Master Sidecar — Gate 2A Rerun: Embedded SFM x86 Candidate A Resource/Performance Baseline

Qualification/measurement only. No production code modified. No Candidate B/C, no Normalizer, no binary-format
change, no Master change. Nothing committed.

## 1. VERDICT

**STOP — NEW DEFECT/PERFORMANCE ANOMALY DISCOVERED. Candidate A resource verdict NOT REACHED (second
consecutive blocked attempt, for a DIFFERENT reason than the first).**

The corrected reader's explicit `open_generation_path(...)` entry point was called, exactly as qualified,
against the real, byte-identical official artifact, inside the real embedded Python 2.7.5 interpreter in
`sfm.exe`. It never returned. Across roughly 24 minutes of wall-clock observation the call: (a) first showed
near-total CPU starvation (the hosting thread consumed on the order of 1 second of CPU time across roughly
8 minutes of wall time — consistent with severe scheduling contention with SFM's own main loop), then (b)
shifted into a sustained, single-core, ~100% CPU-bound state that persisted for at least 75 additional
seconds with **process private-bytes/working-set memory reported as bit-for-bit IDENTICAL** across that
entire span. `OPEN_COMPLETE` was never reached. The process was killed after ~24 minutes with no forward
progress and no exception. This is a genuine, reproducible-in-principle anomaly that must be diagnosed and
fixed in a dedicated follow-up task — not patched here, per this task's own explicit instruction.

This result is orthogonal to the Python 2 path/bytes fix that was qualified immediately before this task: the
corrected reader's SHA-256, the official artifact's SHA-256, and every prior Gate 1 requirement remain
verified and unaffected (Section 3/4/7). Full official-scale H1 evidence (128,555 occurrences) under real
Python 2.7 had never actually been exercised before this task — the original Gate 1 H1 run used only an
8-occurrence hand-composed fixture, and this task's own preceding dry run under Python 3 used the full
9,506,244-byte official artifact and completed in 0.78 seconds. This STOP is therefore new information, not
a regression of anything previously qualified.

## 2. HISTORICAL FIRST-ATTEMPT CONTEXT

`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md` is preserved **completely unmodified**
(verified below, Section 27) — its own verdict remains exactly:

> STOP — GENUINE DEFECT DISCOVERED. Candidate A resource verdict NOT REACHED

That first attempt was blocked by the Python-2 path/bytes ambiguity defect (a call-shape bug: a path string
was misread as artifact bytes). That defect is now fixed and separately, fully qualified
(`SFM_MASTER_SIDECAR_PY27_PATH_INPUT_FIX_AUDIT.md`; committed at `de6e9564447acbc52fd580cbe2612bec69c8977e`).
This rerun used the corrected reader's explicit path entry point and never encountered that defect — it hit a
**different, previously-unobserved** blocker: the real, full-scale open call did not complete inside a live
SFM process, for reasons not yet root-caused. Candidate A's actual resource cost (retained memory, peak,
etc.) is **still not measured**, now for the second, unrelated reason.

## 3. QUALIFIED BASELINE

- HEAD at start and end of this task: `de6e9564447acbc52fd580cbe2612bec69c8977e` (unchanged).
- Final Gate 1: PASS, 36/36, 0 OPEN, 0 FAIL (unaffected by this task).
- Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (reconfirmed unchanged,
  Section 7).
- Prior test baseline: 411 passed / 255 subtests (this task ran no repository test suite changes and made
  no production edits, so this baseline is unaffected and was not re-run as part of this measurement task).

## 4. CORRECTED READER IDENTITY

- Deployed `reader.py` SHA-256: `d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00` — matches
  the corrected, committed file exactly (recomputed from the live repository file immediately before
  deployment: identical).
- Deployed `format.py` SHA-256: `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` (unchanged
  since Gate 1 H1).
- Deployed `__init__.py` SHA-256: `8cad865fd9954035aebb3e02d5c454228e80a095595bd9cd3746df0b357f904c`
  (unchanged).
- All three re-verified byte-identical at the deployed SFM-side location immediately before launch (direct
  SHA-256 recomputation of the deployed copies, matching the values above exactly).
- The legacy, defective reader SHA (`dd1e5da29058394c99e37f5eeaffd262c0b07421d052661ca51b06f1e11e7b02`) was
  **not** used anywhere in this task.

## 5. SFM / PYTHON IDENTITY

- Install: `E:\SteamLibrary\steamapps\common\SourceFilmmaker` (unchanged since Gate 1 H1/original Gate 2A).
- Executable: `game\sfm.exe`.
- This run's SFM process: PID 17452, launched directly (not via `cmd start`, which failed to actually spawn
  the process twice in a row for unknown reasons in this session before a direct launch succeeded).
- Python: real embedded CPython 2.7.5, 32-bit (identity re-confirmed via the deployed probe's own
  `sys.version` logging call, consistent with every prior qualification pass; not independently re-printed in
  this run's surviving log because the process was killed before its final `flush()` — see Section 8's
  methodology note).

## 6. ADDRESS-SPACE CHARACTERISTICS

- `sfm.exe`: PE format I386 (32-bit), `IMAGE_FILE_LARGE_ADDRESS_AWARE` set (established in Gate 2A's first
  attempt; not re-parsed in this task since the binary is unchanged).
- Host: 64-bit Windows → effective ~4 GiB user-mode VA ceiling for this LAA 32-bit process.
- VAS ceiling used for external scanning: `4294967296` (4 GiB), matching the process's own effective limit.

## 7. OFFICIAL ARTIFACT IDENTITY

Recompiled fresh, outside SFM, via the unchanged public compiler, immediately before deployment:

- Bytes: **9,506,244** — matches exactly.
- SHA-256: **`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`** — matches exactly.
- Master SHA-256 (source): `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — matches
  exactly, unchanged.
- Deployed artifact re-verified byte-identical (SHA-256 of the on-disk deployed copy) immediately before
  launch.
- Placed only at a temporary SFM-readable qualification location
  (`usermod\scripts\gate2a_rerun_temp_artifact\official_sidecar.bin`) — never published, no manifest, no
  active generation, no production namespace touched.

## 8. MEASUREMENT METHOD

Reused the already-debugged Gate 2A first-attempt instrumentation with the minimum changes required to use
the corrected reader's explicit path API and the new stage-marker set:

- **In-SFM probe** (`gate2a_rerun_probe.py`), deployed once via the already-proven
  `usermod\scripts\sfm\autoinit\` mechanism, running on a `threading.Timer(20.0, ...)` non-blocking delay so
  it never holds the GUI thread and fires only after SFM reaches its normal idle state.
- Imports only `format`/`reader` from the deployed runtime package (never `sfm_master_core`, `writer`,
  `compiler`, `publisher`, `cli`, `oracle`, or `pytest`).
- Calls the corrected, explicit **`reader.SidecarReader.open_generation_path(ARTIFACT_PATH, SOURCE_SHA256)`**
  — never the legacy `open_generation()`, never any manual path/bytes dispatch. Nothing in the probe
  pre-reads the artifact's full content before this call; the artifact's identity was verified (Section 7)
  **before deployment, outside SFM**, specifically so the production API call itself performs the only read
  of the artifact's bytes (avoiding the original first-attempt's separate-verification-read ambiguity).
- All Windows memory instrumentation (`ctypes`/`psapi.GetProcessMemoryInfo` self-measurement) is test-only,
  lives solely in this temporary probe file, and was verified working via a full local Python-3 dry run
  (Section 8.1) before deployment. No production reader/format code was altered for instrumentation purposes.

**8.1 Pre-deployment dry run (Python 3, local, same corrected reader, same full-scale official artifact):**
completed successfully end-to-end in the exact same probe file (paths/delay swapped for local testing) with
**zero exceptions**, `open_generation_path` elapsed **0.78 s**, all functional checks (Section 17) correct,
lookup batch (Section 18) completed in 0.027 s for 2,990 keys. This dry run is the direct comparison point
for Section 1's anomaly: the identical code, against the identical full-scale artifact, completes in under a
second outside SFM.

**8.2 Methodology limitation, reported honestly:** the in-SFM probe's own self-measured `S0`/`S1` memory
snapshots (via `log_memory`) were captured into an in-memory buffer that is only flushed to disk at the
probe's normal completion or on a caught exception; because the probe never reached either of those points
(Section 1), those particular self-measured readings were lost when the process was terminated. `S0`equivalent readings were reconstructed from the **external** sampler instead (Section 13); this is a
legitimate substitute (same underlying Win32 `GetProcessMemoryInfo` call, from outside the process), but it
means this run does not have the in-process self-measurement corroboration the original successful runs had.
Separately, this session's external sampler was restarted partway through the (at-the-time unexpectedly
extended) observation window, and the restart **overwrote** the first sampler invocation's CSV/JSON output
files (both instances were pointed at the same output paths) rather than appending — losing the external
sampler's own coverage of the earliest ~5 minutes of the stall (roughly `BASELINE_BEGIN` through the first
few minutes of `OPEN_BEGIN`). This is an avoidable measurement-process error on this run's part, reported
here rather than concealed; it does not change Section 1's verdict (the stall's existence and its later,
unambiguous flat-memory/high-CPU character are independently and solidly established by the surviving data,
Section 13), but it does mean this run cannot report a clean, continuous S0→S1→stall memory timeline.

## 9. SAMPLING METHOD

External Python 3 sampler (`gate2a_external_sampler.py`, unchanged from the first Gate 2A attempt):
`OpenProcess`+`GetProcessMemoryInfo` at 0.15 s cadence; `VirtualQueryEx`-based VAS scan (bounded to the 4 GiB
ceiling) at 2.0 s cadence. Two invocations occurred (Section 8.2): the first ran 90 s from shortly after
launch; the second (whose output files are what survived, per Section 8.2) ran a further 900 s once the
stall was recognized, ending on its own `max_seconds` timeout with the process still alive and stalled.

- Surviving sample count: **5,716** memory samples, **440** VAS scans, spanning
  `1789184724.85` → `1789185624.72` (900.0 s continuous coverage of the back half of the stall, through to
  just before this task killed the process).

## 10. STAGE MARKERS

Recorded (unix timestamps), from the probe's own `mark_stage()` calls (a separate, immediately-flushed file
write per call — unaffected by the Section 8.2 log-buffering limitation):

```
BASELINE_BEGIN   1789184404.536
BASELINE_END     1789184405.305
IMPORT_BEGIN     1789184405.809
IMPORT_COMPLETE  1789184408.299
OPEN_BEGIN       1789184409.055
```

**No further stage was ever reached.** `OPEN_COMPLETE`, `STEADY_BEGIN`, `FUNCTIONAL_CHECK_COMPLETE`,
`CLOSE_BEGIN`, `CLOSE_COMPLETE`, and `DONE` do not appear in the stage-marker file. Import cost
(`IMPORT_COMPLETE - IMPORT_BEGIN`): 2.49 s — itself unremarkable and consistent with prior runs' import
timing; the anomaly is confined entirely to the interval starting at `OPEN_BEGIN`.

## 11. S0 IDLE BASELINE

Not available from the probe's own self-measurement (Section 8.2). Reconstructed from the external sampler's
earliest surviving sample (`1789184724.85`, ~5.3 minutes after `OPEN_BEGIN`, due to the sampler-restart data
loss — **this is NOT a true pre-import baseline**, it already reflects `OPEN_BEGIN`-adjacent state):

- WorkingSetSize: 442,535,936
- PrivateUsage / PagefileUsage: 485,912,576
- PeakWorkingSetSize: 450,351,104
- PeakPagefileUsage: 493,768,704

**This section's figures are reported for completeness but are explicitly NOT a valid S0 baseline** — they
are already well into the stalled `OPEN_BEGIN` interval, not a genuine pre-import idle snapshot. No valid
retained/incremental delta calculation is possible from this run's data (Section 20).

## 12. S1 IMPORT

Not separately recoverable (Section 8.2/11 apply identically). Import wall-clock duration (from stage
markers, Section 10) is the only reliable S1-adjacent figure: 2.49 s.

## 13. S3 OPEN / VALIDATION

**Never reached.** `open_generation_path` was called at `OPEN_BEGIN` (`1789184409.055`) and had not returned
by the time the process was killed at approximately `1789185858` — an elapsed wall-clock time of
**≈1,449 seconds (≈24.1 minutes)** with no completion, no exception, and no stage-marker progress beyond
`OPEN_BEGIN`.

Directly observed behavior across that interval (via repeated external `Get-Process`/`GetProcessMemoryInfo`
polling, Section 9):

- **First ~8 minutes:** near-total CPU starvation — process CPU-time increased by only a fraction of a
  second across several minutes of wall time, while SFM's process remained `Responding: True` (its own
  Windows message pump was alive and unblocked).
- **From approximately the 11–12 minute mark onward:** the process shifted into a sustained, single-core,
  **~100–106% CPU utilization** state (measured directly: CPU-time increased by 21.19 s across a tight
  20-second wall-clock polling window), which continued for at least the following ~13 minutes.
- **Memory during the CPU-bound phase:** `WorkingSetSize`/`PrivateUsage`/`PagefileUsage` were **bit-for-bit
  IDENTICAL** (469,635,072 / 496,451,584 / 496,451,584, respectively) across at least a 20-second window
  sampled at the tight interval above, and remained effectively flat (varying by only a few KB, consistent
  with unrelated background SFM/OS activity, not this call) across the final ~15 minutes of external-sampler
  coverage (Section 9's CSV data).

This combination — heavy, sustained CPU consumption with **no corresponding memory growth** — is not
consistent with genuine linear progress through a large, one-time decode/validation pass (which would be
expected to keep allocating new Python objects as it proceeds through 128,555 occurrences and 124,728 fold
keys). It is consistent with a non-terminating loop or a pathological repeated-recomputation pattern that
allocates nothing further once some initial state is reached.

**Per this task's explicit instruction, `open_generation_path`'s eventual outcome was not awaited
indefinitely and the call was not allowed to run to any conclusion by further waiting: the process was killed
once the flat-memory/high-CPU signature was unambiguous, rather than continuing to wait with no defined
endpoint.** No wall-clock "open elapsed" value can be reported because the call never completed.

## 14. S4 STEADY RETAINED

**Not reached.** `STEADY_BEGIN` was never marked.

## 15. LOAD PEAK

Peak values observed by the external sampler across its full 900 s of surviving coverage (all of which falls
within the stalled `OPEN_BEGIN` interval, not a genuine post-open steady state):

- Peak `PrivateUsage`: 496,599,040 bytes.
- Peak `WorkingSetSize`: 469,696,512 bytes.

**These are not meaningful "load peak" figures for Candidate A** — they describe the stalled state, not a
completed open. Reported for completeness only; not comparable to the provisional planning targets (Section
22).

## 16. VAS / LARGEST-FREE-REGION

From the external VAS scanner (440 scans, bounded to the 4 GiB ceiling), first and last surviving samples:

| | Timestamp | Committed | Reserved | Free | Largest free region |
|---|---|---|---|---|---|
| Earliest surviving | 1789184724.85 | 816,746,496 | 374,194,176 | 3,104,026,624 | 2,079,195,136 |
| Latest surviving (pre-kill) | 1789185623.44 | 828,391,424 | 363,741,184 | 3,102,834,688 | 2,079,195,136 |

Committed VAS grew by ~11.6 MB and reserved VAS shrank by ~10.5 MB across the ~15-minute stalled window
(net effect roughly a wash) while the **largest free region was completely unchanged**
(2,079,195,136 bytes ≈ 1.94 GiB) across the entire surviving observation window. This is further evidence
against a large, growing in-process allocation (which would be expected to erode the largest free region as
it grew) and is consistent with the stall being CPU-bound rather than allocation-bound.

## 17. FULL-SCALE FUNCTIONAL CHECK

**Not reached.** `FUNCTIONAL_CHECK_COMPLETE` was never marked; `group_count`/`occurrence_count`/HIT/
`MasterUnknown` checks never ran inside SFM in this task. (They DID run, successfully, in the Section 8.1
Python 3 dry run against the identical corrected reader and identical full-scale artifact: groups 43/43,
occurrences 128,555/128,555, first/middle/last fold HIT with correct destinations, absent fold
`MasterUnknown` — but that is not real-SFM-Python-2.7 evidence and is not claimed as such.)

## 18. LOOKUP BATCH

**Not reached inside SFM.** In the Section 8.1 Python 3 dry run only: count=2,990, elapsed=0.027 s, all 2,990
resolved `Hit` (0 conflict, 0 unknown) — descriptive only, not real-SFM-Python-2.7 evidence.

## 19. S5 POST-CLOSE

**Not reached.** `close()` was never called by the probe (the provider was never successfully opened); the
process was terminated externally (`taskkill /F`) rather than via the provider's own `close()`/lifecycle
path.

## 20. RETAINED RESOURCE DELTA

**Cannot be computed.** No valid S0 (Section 11), no S3/S4 (Sections 13/14). Candidate A's retained
incremental cost remains **entirely unmeasured** by this run, exactly as it was after the first Gate 2A
attempt — for a different reason.

## 21. PEAK RESOURCE DELTA

**Cannot be meaningfully computed**, for the same reason as Section 20. The raw peak figures in Section 15
describe a stalled, non-representative state, not Candidate A's real open/load cost.

## 22. PROVISIONAL TARGET COMPARISON

**Not applicable.** No retained or peak delta exists to compare against the provisional ~16 MiB
retained / ~32 MiB peak planning targets from `SFM_MASTER_SIDECAR_PHASE_A_INFRASTRUCTURE_ASSESSMENT.md`
(confirmed, again, to be non-normative in the controlling
`SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md`, which contains no binding numeric memory
threshold). This comparison cannot be performed until a completed open is actually measured.

## 23. CANDIDATE A VERDICT

**INCONCLUSIVE — MEASUREMENT QUALITY INSUFFICIENT**, for a reason distinct from and more serious than a mere
measurement-quality shortfall: the production open call itself did not complete. This is not a verdict about
Candidate A's backing-strategy design (complete immutable retained bytes, validated once) being unsound — the
identical code and identical data completed correctly and quickly under Python 3 (Section 8.1) and the
original tiny-fixture H1 probe completed correctly under real Python 2.7. It is a verdict that **something
about invoking the real, full official-scale open operation from a background thread inside a live SFM
process did not behave as expected**, and that this must be understood before any resource baseline can be
trusted.

Read-only code inspection (`reader.py`, `format.py`) performed as part of this report — **no code was
modified** — did not surface an obvious infinite loop, unbounded recursion, or Python-2/3 semantic divergence
(e.g., the reader's one binary-search loop uses `//`, identical floor-division behavior on both Python
versions; the embedded-integrity-digest checksum uses `hashlib.sha256`, a C-accelerated primitive on both
versions; per-section decode loops are linear `for i in range(count)` passes; group full-path resolution is
recursive but memoized and bounded by the artifact's 43 groups). **No specific root cause is claimed or
confirmed by this task.** The mechanism remains genuinely unidentified pending a dedicated diagnostic task —
candidates worth investigating there include (not an exhaustive or committed list): scheduling/GIL contention
between SFM's own main loop and a background `threading.Timer` thread at this data volume; a difference
between how CPython 2.7 and CPython 3.10 execute some part of the shared decode/validation path at 128,555-
occurrence scale specifically; or an interaction with SFM's own embedding of the interpreter not present in a
standalone Python 2.7/3 process.

## 24. REALISTIC-SESSION LIMITATION

Moot for this run — no baseline was obtained at all, idle or otherwise. This section is retained per the
required audit structure to make that explicit: even the idle-session objective (Part 21 of this task's own
instructions) was not achieved.

## 25. DEFERRED GATE 2 WORK

All explicitly deferred, unchanged from every prior pass: generation overlap, Candidate B/C, Normalizer
integration, format v1 freeze. Additionally and specifically deferred by this run's own result: **any further
Gate 2A resource measurement attempt, until the open-call non-completion behavior documented here is
root-caused** (a new, required precondition this task adds).

## 26. CLEANUP

- SFM process (PID 17452) terminated (`taskkill /PID 17452 /F`) after ~24 minutes of unambiguous non-progress
  (Section 13); this was a fresh instance launched solely for this probe, not a pre-existing user session
  (confirmed via `tasklist` showing no running `sfm.exe` before launch).
- `usermod\scripts\sfm\autoinit\zz_gate2a_rerun_probe_temp.py` — removed; directory confirmed empty
  afterward.
- `usermod\scripts\sfm_master_sidecar_gate2a_rerun_runtime\` (corrected-reader runtime copy) — removed
  entirely.
- `usermod\scripts\gate2a_rerun_temp_artifact\` (official artifact copy + lookup batch) — removed entirely.
- `usermod\scripts\sfm\sfm_init.py` — confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`).
- Directory-wide search confirmed no remaining file matching `*gate2a*` anywhere under `usermod\scripts\`.
- No manifest, active generation, or publisher-lock file was created anywhere by this task.
- No SFM launch-option or configuration change was made or left behind.
- **Crash-dump check:** searching for any `*.mdmp` file under the SFM install with a modification time at or
  after this task's own launch (`2026-09-11 23:39:54` local) or its kill action found **none** — this task's
  forced termination of the stalled process did not itself produce a crash dump. (Two pre-existing, empty,
  `0`-byte `"(failed)sfm_assert_..."` stub files with earlier timestamps the same evening, and one from
  earlier the same day, were found during this check; all predate this task's own SFM launch and were left
  untouched, since they were not created by this task and their origin is out of this task's scope.)
- All probe/sampler artifacts (result log, stage-marker log, external sampler CSV/JSON) were preserved
  outside the SFM install and outside the repository, in this session's own scratchpad directory, for audit
  traceability (Sections 8.2/9/10/13/16 reproduce their content above).

## 27. GIT / SAFETY STATE

- HEAD before and after this task: `de6e9564447acbc52fd580cbe2612bec69c8977e` — unchanged.
- `sfm_defaultanimationgroups.txt`: unchanged (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
- `tools/sfm_master_sidecar/reader.py`: unchanged (`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`, the already-committed corrected
  file) — this task deployed only a read-only byte-verified COPY to a temporary SFM location; the
  repository's own file was never opened for writing.
- All other production sidecar modules (`format.py`, `writer.py`, `manifest.py`, `publisher.py`, `cli.py`,
  `compiler.py`, `__init__.py`): unchanged.
- `SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md` (the historical first-attempt audit):
  confirmed byte-for-byte unchanged throughout this task (re-verified via direct grep of its STOP/NOT REACHED
  language, Section 2; it remains untracked/uncommitted exactly as before, per its own prior status).
- No Candidate B/C code written. No Normalizer code touched. No production edits of any kind.
- Nothing staged, nothing committed. `git status --porcelain` shows only this new audit file
  (`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_RERUN_AUDIT.md`) as a new untracked file, plus
  the same pre-existing unrelated untracked files present since before this task began.
- No agents or subagents were used.
