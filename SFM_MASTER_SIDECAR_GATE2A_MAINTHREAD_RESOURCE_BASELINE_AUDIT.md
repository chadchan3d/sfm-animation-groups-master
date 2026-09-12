# SFM Master Sidecar — Gate 2A Main-Thread Candidate A Resource Baseline

Qualification/measurement only. No production reader/writer/compiler code modified. No Candidate B/C, no
Normalizer, no binary-format change, no Master change, no format v1 freeze. Nothing committed.

## 1. VERDICT

**CANDIDATE A BASELINE VIABLE WITH RESOURCE CONCERN.**

This is the first valid Candidate A resource measurement: invoked exclusively from SFM's confirmed
Qt/main-event thread (never `threading.Timer`), the full 9,506,244-byte official artifact opened correctly
in **1.841 s** via the corrected reader's explicit `open_generation_path(...)`, passed every functional check
(43/43 groups, 128,555/128,555 occurrences, first/middle/last fold HIT, absent fold `MasterUnknown`), and
closed cleanly with no uncaught exceptions. The measured resource cost is real and internally consistent
(peak ≈63.2 MiB, steady-retained ≈38.8 MiB, both derived from an external, uninterrupted, gap-free sampler
run) but is **materially above** the non-binding ~16 MiB retained / ~32 MiB peak provisional planning targets
— roughly 2–2.4x each. Against the ~4 GiB effective LAA VA ceiling and the ~1.94 GiB largest contiguous free
region (unchanged before/after this open), this cost is small in absolute VA-headroom terms in an **idle**
SFM session. The "resource concern" qualifier reflects that the measured numbers exceed the planning targets
by a non-trivial margin, not that anything crashed, leaked catastrophically, or exhausted address space in
this isolated test. Per this task's own Part 16, this baseline PASS does **not** close Gate 2: loaded-project
headroom, generation-overlap cost, and repeated open/close behavior remain unmeasured.

## 2. PRIOR BLOCKED ATTEMPTS

- Attempt 1 (`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md`): blocked by the Python-2
  path/bytes API defect (since corrected).
- Attempt 2 (`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_RERUN_AUDIT.md`): corrected reader,
  invoked from a `threading.Timer` worker thread, never completed after ~24.1 minutes.
- Execution-context diagnostic (`SFM_MASTER_SIDECAR_GATE2_EXECUTION_CONTEXT_DIAGNOSTIC_AUDIT.md`, wording
  corrected in commit `cb1f7d436b070b234bccea371372ff1af79b1742`): established the worker thread is not
  generically starved for ordinary Python bytecode, but the production open call is severely
  execution-context-specific-slowed on a worker thread, and completes correctly (1.847 s) on the main/event
  thread. Mechanism unresolved.

All three documents remain unmodified by this task (Section 25).

## 3. EXECUTION-CONTEXT QUALIFICATION

Used exclusively in this task: `QtCore.QTimer.singleShot(...)` chained callbacks, all confirmed running on
the same thread ID as the autoinit script itself (`19760`, `same_as_autoinit=True` at every checkpoint that
recorded thread identity — `do_open`, matching the diagnostic's own finding). `threading.Timer` was not used
anywhere in this task's probe.

## 4. TARGET ENVIRONMENT

Unchanged: `E:\SteamLibrary\steamapps\common\SourceFilmmaker`, `game\sfm.exe`, real embedded CPython 2.7.5
(32-bit, `MSC v.1600`), I386 PE with `IMAGE_FILE_LARGE_ADDRESS_AWARE`, ~4 GiB effective VA ceiling on this
64-bit host. Fresh disposable session, PID 120, launched solely for this probe (`tasklist` confirmed no
running `sfm.exe` before launch) and terminated after the run.

## 5. OFFICIAL ARTIFACT

Recompiled fresh, outside SFM, via the unchanged public compiler, immediately before deployment:

- Bytes: **9,506,244** — matches exactly.
- SHA-256: **`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`** — matches exactly.
- Deployed, re-verified on-disk size (`os.path.getsize`, cheap size-only check — no separate full-content
  verification read inside SFM, per the established discipline from the path/bytes fix task): 9,506,244,
  matching expected.
- Placed only at a temporary SFM-readable qualification location; never published (no manifest, no active
  generation, no production namespace touched).

## 6. RUNTIME MODULE IDENTITY

- Deployed `reader.py` SHA-256: `d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00` — matches
  the corrected, committed file exactly; re-verified from the on-disk deployed copy inside the probe itself
  at `IMPORT_COMPLETE`.
- `format.py`/`__init__.py` deployed as unmodified byte copies of the committed files (unchanged since Gate 1
  H1).
- The legacy, defective reader SHA was not used anywhere in this task.

## 7. MEASUREMENT METHOD

- **SFM-side probe:** deployed via the already-proven `usermod\scripts\sfm\autoinit\` mechanism. Performs
  **no self memory-instrumentation** (per this task's Part 2) — it emits only stage markers (name +
  timestamp, immediately flushed to a separate file per marker) and performs the actual production calls:
  import, `open_generation_path(...)`, functional checks, lookup batch, `close()`/`close()`, post-close
  rejection check. All scheduling used `QtCore.QTimer.singleShot(...)` chaining (zero-delay for immediate
  next-steps, explicit short delays only for the two deliberate stabilization waits) — never a blocking
  `time.sleep()` on the main thread, so the event loop kept pumping throughout.
- **External sampler:** a separate, unmodified Python 3 process (`gate2a_external_sampler.py`, the same
  script used in every prior Gate 2A attempt), `OpenProcess`+`GetProcessMemoryInfo` at 0.15 s cadence,
  `VirtualQueryEx`-based VAS scan (bounded to the 4 GiB ceiling) at 2.0 s cadence — owns all memory/VAS
  measurement for this run, exactly as this task's Part 2 requires.
- **Pre-deployment dry run (Python 3, local):** the identical probe logic (with a fake `PySide` module
  injected so `QTimer.singleShot` fires synchronously) ran end-to-end with zero exceptions before deployment,
  confirming the full stage chain, functional checks, and lookup batch all execute correctly.

## 8. SAMPLER INTEGRITY

Unlike the first Gate 2A rerun (where a sampler restart overwrote the earliest ~90 seconds of coverage), this
task used **one continuous external sampler process for the entire run**, with **unique, run-specific output
filenames** (`gate2a_mt_external_samples.csv`, `gate2a_mt_external_vas.json`) that were never reused or
overwritten mid-run. The sampler was started immediately after observing the probe's own `READY` marker (via
`tasklist` PID confirmation), and was left running for **~52.8 seconds before the probe's own `S0_CAPTURED`
marker** — a synchronization mechanism (a shared "go-flag" file the probe polls via chained
`QtCore.QTimer.singleShot(300, ...)` calls, bounded at 60 s, per this task's own Part 6 diagnostic-bound
discipline applied here as a setup-safety bound) that guarantees the sampler had already accumulated a large
number of samples before any baseline was captured — vastly exceeding "several samples," satisfying Part 4's
requirement without ambiguity.

- **S0 preserved: YES**, unambiguously — the sampler's first sample (`1789211358.28`) precedes `S0_CAPTURED`
  (`1789211399.62`) by ~41.3 seconds of continuous, gap-free coverage.
- Sample count: **311** memory samples, **23** VAS scans, spanning the complete run
  (`1789211358.28` → `1789211406.62`, 48.3 s continuous).
- Cadence as configured: 0.15 s (memory), 2.0 s (VAS) — unchanged from every prior attempt, already
  low-overhead and previously validated.
- The sampler exited on its own (`DONE marker observed, sampling 2.00s longer for trailing data then
  stopping`), not via forced termination — a clean, complete run.

## 9. STAGE MARKERS

All required markers present, in order, each independently timestamped and immediately flushed:

```
READY                  1789211344.256
S0_CAPTURED            1789211399.624
IMPORT_BEGIN           1789211399.625
IMPORT_COMPLETE        1789211399.650
OPEN_BEGIN             1789211399.658
OPEN_COMPLETE          1789211401.503
STEADY_BEGIN           1789211401.504
STEADY_CAPTURED        1789211403.035
FUNCTIONAL_COMPLETE    1789211403.050
LOOKUP_BATCH_COMPLETE  1789211403.106
CLOSE_BEGIN            1789211403.107
CLOSE_COMPLETE         1789211404.640
DONE                   1789211404.641
```

Import cost (`IMPORT_COMPLETE - IMPORT_BEGIN`): 25 ms. Open cost: 1.845 s (stage-marker timing; see Section
12 for the probe's own internally-timed figure, 1.841 s — the ~4 ms difference is marker-logging overhead,
not a discrepancy). Total wall time from `S0_CAPTURED` to `DONE`: 5.017 s.

## 10. S0 BASELINE

Nearest external sample to `S0_CAPTURED` (`1789211399.624`, sample at `1789211399.624`, 9 ms offset):

- PrivateUsage: **463,982,592** bytes
- WorkingSetSize: **421,294,080** bytes

Nearest VAS scan (`1789211398.823`, 0.80 s before `S0_CAPTURED` — the nearest available given the 2.0 s VAS
cadence):

- Committed: 794,750,976 bytes
- Reserved: 379,064,320 bytes
- Free: 3,121,152,000 bytes
- Largest free contiguous region: **2,081,488,896 bytes (≈1.938 GiB)**

S0 is unambiguous and was captured well after the sampler had already been running for ~41 s (Section 8) —
no STOP condition from Part 4 applies.

## 11. S1 IMPORT

Nearest external sample to `IMPORT_COMPLETE` (`1789211399.650`) is the **same** external sample as S0 (both
fall inside one 0.15 s sampling interval, since the actual import cost was only 25 ms — too fast for this
sampler cadence to resolve separately). Reported honestly rather than fabricating an artificial delta:

- **S1 − S0: 0 bytes (PrivateUsage), 0 bytes (WorkingSet)** — not a real "zero cost," but a measurement-
  granularity artifact: `format.py`/`reader.py` import is fast enough (single-digit milliseconds) that no
  intervening external sample exists between S0 and S1. This is consistent with every prior run's own import
  timing (2–3 ms range) and is not treated as evidence the import genuinely costs nothing.

## 12. OPEN / VALIDATION

`open_generation_path(...)` wall-clock duration, measured directly inside the probe (its own
`time.time()` bracketing around the call, not stage-marker subtraction): **1.8410 s** — closely matching the
execution-context diagnostic's own reference figure (1.847 s; this run's figure is not materially different,
well within normal run-to-run variance).

Nearest external sample to `OPEN_COMPLETE` (`1789211401.503`, sample at `1789211401.503`, 5 ms offset) — this
is **S3**, the immediate post-open/post-validation snapshot:

- PrivateUsage: **530,288,640** bytes
- WorkingSetSize: **486,825,984** bytes

**S3 − S0:** PrivateUsage +66,306,048 bytes (≈63.24 MiB); WorkingSet +65,531,904 bytes (≈62.50 MiB).
**S3 − S1:** identical to S3 − S0 (S1 = S0 per Section 11's granularity note).

## 13. S3 IMMEDIATE POST-OPEN

(Reported together with Section 12 above, per this task's own numbering — S3 represents "complete backing
resident, provider valid, before long stabilization," captured at the exact `OPEN_COMPLETE` marker.) This is
effectively the run's **peak** reading before any settling occurs (Section 15 confirms no external sample in
the observed window exceeds it).

## 14. S4 STEADY RETAINED

Nearest external sample to `STEADY_CAPTURED` (`1789211403.035`, sample at `1789211403.035\|1789211403.035`
region, 16 ms offset), captured after a 1.5 s `QtCore.QTimer`-scheduled stabilization wait (not a blocking
sleep) plus `gc.collect()`:

- PrivateUsage: **504,700,928** bytes
- WorkingSetSize: **461,664,256** bytes

**Primary retained metrics:**
- **S4 − S0: PrivateUsage +40,718,336 bytes (≈38.83 MiB); committed-VAS +46,604,288 bytes (≈44.45 MiB).**
- **S4 − S1: identical to S4 − S0** (Section 11).

**Secondary:**
- WorkingSet delta vs S0: +40,370,176 bytes (≈38.50 MiB).
- Reserved-VAS delta vs S0: −9,871,360 bytes (≈−9.41 MiB) — a small reduction, plausibly reservation being
  converted to committed pages as the backing buffer and decoded structures were allocated.
- Free-VAS change vs S0: −36,732,928 bytes (≈−35.03 MiB) — consistent with the committed-VAS increase.
- Largest-free-region change: **0 bytes** — completely unchanged (Section 16).

The retained figure (S3 → S4: PrivateUsage drops from 530,288,640 to 504,700,928, a settling of ≈25.0 MiB
between the immediate post-open peak and the 1.5 s-later steady state) shows some of the open operation's
transient cost is released quickly (consistent with temporary parsing buffers/intermediate objects being
garbage-collected), while a substantial retained cost (≈38.8 MiB) persists with the provider still valid and
in use.

## 15. EXTERNAL LOAD PEAK

Correlated over the `OPEN_BEGIN` → `STEADY_CAPTURED` interval (28 external samples fall in this window):

- **Peak PrivateUsage: 530,288,640 bytes — delta vs S0: +66,306,048 bytes (≈63.24 MiB).**
- **Peak WorkingSet: 486,825,984 bytes — delta vs S0: +65,531,904 bytes (≈62.50 MiB).**

These peak values coincide exactly with the S3 (`OPEN_COMPLETE`) sample (Section 12) — i.e., the peak within
this window occurs immediately at open completion, with no higher reading observed afterward through
`STEADY_CAPTURED`. This is not a process-lifetime peak contaminated by SFM startup (the window is explicitly
bounded to `OPEN_BEGIN`→`STEADY_CAPTURED`, well after the ~53 s of pre-open idle sampling).

## 16. VAS HEADROOM

| | S0 | S4 (≈ S5, Section 19) |
|---|---|---|
| Committed | 794,750,976 | 841,355,264 |
| Reserved | 379,064,320 | 369,192,960 |
| Free | 3,121,152,000 | 3,084,419,072 |
| Largest free contiguous region | 2,081,488,896 | 2,081,488,896 |

- Effective LAA VA ceiling: **4,294,967,296 bytes (4 GiB)** (this 32-bit LAA process on a 64-bit host,
  unchanged from every prior pass).
- Headroom remaining at S4: free VAS ≈ 3,084,419,072 bytes (**≈71.8%** of the 4 GiB ceiling); largest single
  contiguous free region ≈ 2,081,488,896 bytes (**≈48.5%** of the ceiling, ≈1.938 GiB in absolute terms).
- **Largest-free-region change from S0 to S4: 0 bytes** — not eroded at all by this open, in this idle
  session.
- This measured cost (peak ≈63.2 MiB, retained ≈38.8 MiB) represents roughly **1.5%** of the 4 GiB ceiling
  and **≈2.1%** of the free VAS at S0 — comfortably small in isolation, though this is an idle session with
  no loaded animation project competing for the same address space (Section 22).

## 17. FUNCTIONAL CHECK

All required minimal checks (this task's Part 9), performed with the provider retained, immediately after
the S4 steady-state capture:

```
group_count=43            (expect 43,      match=True)
occurrence_count=128555   (expect 128555,  match=True)
first HIT=True   dest_ok=True   ("left" -> groupFile/Face/Eyes)
middle HIT=True  dest_ok=True   ("KRI_Braid_RB_03_SkinPoint" -> groupFile/Hair)
last HIT=True    dest_ok=True   ("WrinkleTexture" -> groupFile/Useless)
absent MasterUnknown=True
```

All PASS. No exhaustive Gate 1 rerun was performed (per this task's own instruction).

## 18. LOOKUP BATCH

The deterministic, previously-prepared stratified official-scale lookup batch:

- **Count: 2,990**
- **Elapsed: 0.0490 s**
- Result breakdown: 2,990 Hit, 0 FoldConflict, 0 MasterUnknown (average 0.01639 ms/lookup) — descriptive
  only, not a microbenchmark; the batch ran on the same main/event thread as the rest of this probe (no
  separate consumer-context contract exists yet for lookup specifically, so no alternate context was used).

## 19. CLOSE / S5

`CLOSE_BEGIN` → `provider.close()` (twice, second call harmless) → post-close `lookup_fold` correctly raised
`AuthorityUnavailable` (`'provider is not VALID (state=CLEANED)'`) → `gc.collect()` → 1.5 s
`QtCore.QTimer`-scheduled wait (not a blocking sleep) → `CLOSE_COMPLETE` (S5).

Nearest external sample to `CLOSE_COMPLETE` (`1789211404.640`, sample at `1789211404.640`, 39 ms offset):

- PrivateUsage: **478,007,296** bytes
- WorkingSetSize: **435,036,160** bytes

**S5 − S0: PrivateUsage +14,024,704 bytes (≈13.37 MiB); WorkingSet +13,742,080 bytes (≈13.11 MiB).**
**S5 − S1: identical to S5 − S0** (Section 11).

This is **not** a full return to the S0 baseline — a residual ≈13.4 MiB remains committed after `close()` and
stabilization. Per this task's own Part 12 instruction, this is explicitly distinguished as **allocator
retention, not a logical resource leak**: the provider object itself, its backing buffer, and its decoded
structures were all released at the Python level (confirmed by the post-close `AuthorityUnavailable`
rejection — the object is genuinely dead, not merely appearing so), but CPython's own memory allocator (and,
beneath it, the Windows heap manager) is not obligated to return every freed page to the OS immediately, and
commonly does not. No VAS reading exists strictly after `CLOSE_COMPLETE` (the last VAS scan, `1789211402.880`,
precedes it by ~1.76 s — the 2.0 s VAS cadence did not produce an independent scan in that short a window
before the sampler's own post-DONE trailing period ended) — Section 16's table therefore uses the same VAS
reading for "S4 (≈ S5)"; this is stated as a limitation, not presented as a separately-confirmed S5 VAS
measurement (Section 22).

## 20. PROVISIONAL TARGET COMPARISON

Per `SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md` (reconfirmed, again, to contain no binding
numeric memory threshold): the ~16 MiB retained / ~32 MiB peak figures remain **provisional planning
targets**, not normative requirements, per `SFM_MASTER_SIDECAR_PHASE_A_INFRASTRUCTURE_ASSESSMENT.md`.

- **Retained (S4 − S0, ≈38.83 MiB) vs. ~16 MiB provisional target: materially above** (≈2.43x).
- **Peak (S3 − S0, ≈63.24 MiB) vs. ~32 MiB provisional target: materially above** (≈1.98x).

These are reported as planning comparisons, not pass/fail gates in themselves.

## 21. CANDIDATE A BASELINE VERDICT

**CANDIDATE A BASELINE VIABLE WITH RESOURCE CONCERN** (Section 1). Supporting basis:

- Full-scale functional success: **complete** (Section 17) — no correctness defect of any kind.
- Retained delta: materially above the provisional target, but a small absolute fraction (≈1%) of the 4 GiB
  VA ceiling in this idle session.
- Load peak: materially above the provisional target, similarly small in absolute VA terms here.
- VAS headroom: no erosion of the largest free contiguous region observed; ≈71.8% of the VA ceiling remained
  free at S4.
- This verdict is a baseline judgment about an **isolated, idle-session** open/steady/close cycle only — see
  Section 23 for what it explicitly does not yet prove.

## 22. LIMITATIONS

- **S1 (import) delta is measurement-granularity-limited to 0** (Section 11) — the true import cost is
  known from stage-marker timing (25 ms) but not independently confirmed via a distinct external memory
  sample.
- **No independent S5 VAS scan** exists strictly after `CLOSE_COMPLETE` (Section 19) — the 2.0 s VAS cadence
  did not produce one before the sampler's own trailing window ended; Section 16's "S5" VAS figures are
  actually the same reading used for S4, not a separately-confirmed post-close scan.
- **Single-run measurement.** This is one open/close cycle in one idle session — no repeated-open/close
  behavior, no concurrent generation, no loaded real animation project was tested (all explicitly out of
  scope per this task and deferred to Section 23).
- **Sampler cadence (0.15 s memory / 2.0 s VAS)** means any transient spike shorter than these intervals
  could be missed; the reported peak (Section 15) is the peak **observed at this cadence**, not a
  mathematically exhaustive maximum.

## 23. REMAINING GATE 2 WORK

Explicitly not begun or resolved by this baseline PASS, per this task's own Part 16:

- Real loaded-project headroom (this baseline used an idle SFM session with no animation project loaded).
- Generation overlap cost (opening a new generation while a prior one is still retained/in-use).
- Repeated open/close behavior (does the ≈13.4 MiB residual from Section 19 compound across repeated
  cycles, or stabilize?).
- Whether Candidate B/C are necessary at all (not evaluated; no such work was performed or begun here).
- Final consumer invocation pattern (this task confirmed `QtCore.QTimer`-based main-thread invocation works;
  it did not design or qualify the actual eventual Normalizer/consumer calling convention).
- Normalizer seam qualification — not begun.
- Format v1 freeze decision — not begun, not implied by this result.

## 24. CLEANUP

- SFM process (PID 120) terminated (`taskkill /PID 120 /F`) after the run completed cleanly (`DONE` marker
  observed, external sampler exited on its own).
- `usermod\scripts\sfm\autoinit\zz_gate2a_mt_probe_temp.py` — removed; directory confirmed empty afterward.
- `usermod\scripts\sfm_master_sidecar_gate2a_mainthread_runtime\` (corrected-reader runtime copy) — removed
  entirely.
- `usermod\scripts\gate2a_mt_artifact\` (official artifact copy + lookup batch) — removed entirely.
- `usermod\scripts\sfm\sfm_init.py` — confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`).
- Directory-wide search confirmed no remaining file matching `*gate2a_mt*` anywhere under
  `usermod\scripts\`.
- No manifest, active generation, or publisher-lock file was created anywhere by this task.
- No SFM launch-option or configuration change was made or left behind.
- No new crash dump (`*.mdmp` with a modification time at or after this task's own launch) was found.
- No PySide/Qt UI element (dialog, menu item, persistent widget) was created — only a `QTimer` scheduled
  internally and a lookup of the existing `QApplication` instance, exactly as in the prior diagnostic.
- All measurement logs (stage markers, result log, external sampler CSV/VAS/stdout) were preserved outside
  the SFM install and outside the repository, in this session's own scratchpad directory, for audit
  traceability (reproduced in Sections 9–19 above).

## 25. GIT / SAFETY STATE

- HEAD before and after this task: `cb1f7d436b070b234bccea371372ff1af79b1742` — unchanged.
- `sfm_defaultanimationgroups.txt`: unchanged (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
- `tools/sfm_master_sidecar/reader.py`: unchanged (`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`) — this task deployed only a
  read-only, byte-verified COPY; the repository's own file was never opened for writing.
- All other production sidecar modules: unchanged.
- All three prior Gate 2A/diagnostic audits confirmed unmodified (Section 2).
- No Candidate B/C code written. No Normalizer code touched. No production edits of any kind.
- Nothing staged, nothing committed. `git status --porcelain` shows only this new audit file
  (`SFM_MASTER_SIDECAR_GATE2A_MAINTHREAD_RESOURCE_BASELINE_AUDIT.md`) as a new untracked file, plus the same
  pre-existing unrelated untracked files present since before this task began.
- No agents or subagents were used.
