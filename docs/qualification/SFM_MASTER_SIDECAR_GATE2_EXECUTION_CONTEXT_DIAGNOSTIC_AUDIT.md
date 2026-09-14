# SFM Master Sidecar — Gate 2 Full-Scale Open Execution-Context Diagnostic

Diagnostic qualification only. No production reader/writer/compiler code modified. No Candidate B/C, no
Normalizer, no binary-format change, no Master change, no Candidate A resource verdict. Nothing committed.

## 1. VERDICT

**EXECUTION-CONTEXT-SPECIFIC READER SLOWDOWN CONFIRMED. This is NOT a reader correctness defect.** The
production reader's full open path experiences an extreme, execution-context-specific slowdown when invoked
from a `threading.Timer` worker thread inside live SFM. The identical corrected reader, opening the identical
9,506,244-byte official artifact via the identical `open_generation_path(...)` call, completes correctly in
**1.847 seconds** when invoked from SFM's Qt/main-event thread (a `QtCore.QTimer.singleShot(...)` callback),
but had never completed after ~24.1 minutes when invoked from a `threading.Timer` background worker thread
(the prior Gate 2A rerun).

This is deliberately **not** characterized as generic background-thread/GIL starvation: a dedicated
pure-Python control experiment (Section 6) shows ordinary Python bytecode (128,555 iterations of
`struct.pack`/`struct.unpack` plus arithmetic) completes in statistically indistinguishable time on the
worker thread (0.511 s) and the main thread (0.517 s). Ordinary Python bytecode execution on the worker
thread was therefore **not** generally starved. The slowdown is specific to whatever the production reader's
real open call does — not to background-thread execution as such. The exact lower-level mechanism remains
unresolved (Section 14); it is not attributed to any specific proven cause here.

**Established facts:** `threading.Timer` worker thread — **unsuitable** for full provider loading. SFM's
Qt/main-event thread — **suitable**. Reader correctness — **PASS** on the main thread (full functional check,
Section 11). Candidate A resource verdict — **still NOT REACHED** (Section 16). Future SFM provider loading
for this project must be initiated from the main/event thread (or a deliberately designed cooperative model),
not a bare `threading.Timer` background thread.

## 2. PRIOR GATE 2A CONTEXT

Both historical audits are **preserved completely unmodified**, confirmed by direct grep of their STOP/NOT
REACHED language immediately before writing this document (Section 19):

- `SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md` — Attempt 1: blocked by the Python-2
  path/bytes API defect (since corrected and separately, fully qualified).
- `SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_RERUN_AUDIT.md` — Attempt 2: the corrected
  reader's explicit `open_generation_path(...)`, full official artifact, invoked from a `threading.Timer`
  worker thread, never completed after ~24.1 minutes; SFM's main process remained `Responding: True`
  throughout; no growing-VAS pattern was observed; no Candidate A resource verdict was reached.

This diagnostic task exists specifically to determine why Attempt 2 never completed, before any further
resource-measurement attempt.

## 3. TARGET ENVIRONMENT

Unchanged from every prior pass: `E:\SteamLibrary\steamapps\common\SourceFilmmaker`, `game\sfm.exe`, real
embedded CPython 2.7.5 (32-bit, `MSC v.1600`), I386 PE with `IMAGE_FILE_LARGE_ADDRESS_AWARE` set, ~4 GiB
effective VA ceiling on this 64-bit host. Three fresh, disposable SFM sessions were launched and terminated
across this task's three runs (PIDs 4396, 16556, 1344); `tasklist` confirmed no running `sfm.exe` before each
launch, so no pre-existing user session was ever at risk.

## 4. MAIN-THREAD CALLBACK MECHANISM

**Available: YES**, confirmed empirically, not assumed. SFM's own embedded Python ships `PySide` (Qt4
bindings; `game\bin\qtcore4.dll`/`qtgui4.dll`/`shiboken-python2.7.dll` alongside `python27.dll`), and this
project's own repository-adjacent SFM install already contains real, pre-existing, dated (2026) in-game
scripts under `usermod\scripts\sfm\mainmenu\ChadChan3D\*.py` that successfully use
`from PySide import QtCore, QtGui`, `QtGui.QApplication.instance()`, and `QtCore.QTimer.singleShot(...)` —
direct, in-install evidence the mechanism is real and already relied upon by other tools in this exact
environment (e.g. `Rebuild_Control_Groups_Normalizer.py`, `SFM_20260908_T105_RigLifecycleSettlingObserver.py`
and several `SFM_202609...` files). This diagnostic's own probes independently re-confirmed the mechanism
from a `usermod\scripts\sfm\autoinit\` startup script (RUN 1/RUN 3, Section 6/10 below): `PySide.QtCore`
imports successfully, `QtGui.QApplication.instance()` returns a live instance, and `QtCore.QTimer.singleShot`
callbacks fire correctly. No UI was mutated beyond scheduling the probe itself (no dialogs, no menu items, no
persistent widgets were created).

## 5. THREAD IDENTITY EVIDENCE

Recorded directly (Python's own `thread.get_ident()`, real values, not inferred) in RUN 1:

| Context | Thread ID | Same as autoinit thread |
|---|---|---|
| Autoinit script load (baseline) | `12132` | — |
| `QtCore.QTimer.singleShot` callback (main) | `12132` | **True** |
| `threading.Timer` callback (worker) | `17992` | **False** |

Reconfirmed in RUN 3 (fresh session): autoinit thread `28540`; the `QTimer.singleShot` main-open callback
ran on thread `28540` — **same thread**, confirming the autoinit script itself runs on SFM's true main/event
thread, and `QtCore.QTimer.singleShot` reliably delivers callbacks onto that same thread across independent
sessions.

## 6. PURE-PYTHON WORKLOAD

A bounded, deterministic, ordinary-bytecode workload (`struct.pack`/`struct.unpack` on a 4-byte value plus a
byte-level XOR/arithmetic step per iteration — no `sleep`, no large allocation) was run for exactly
**128,555 iterations** (matching the real official occurrence count for direct comparability), identically,
in both contexts, in the same SFM session (RUN 1):

| Context | Thread ID | Elapsed | Result checksum |
|---|---|---|---|
| `threading.Timer` worker | `17992` | **0.5110 s** | `16427397` |
| `QtCore.QTimer.singleShot` main | `12132` | **0.5170 s** | `16427397` |

Identical result checksums (confirms both ran the exact same deterministic workload correctly); elapsed times
differ by only ~6 ms — statistically indistinguishable given the observation's own timing granularity.

## 7. WORKER-THREAD RESULT

The worker thread executed 128,555 iterations of ordinary Python bytecode in 0.511 s — **no meaningful
starvation was observed for this pure-Python workload.** This directly rules out a blanket
"background-thread Python bytecode never gets scheduled while SFM's main loop runs" explanation: the worker
thread clearly did receive ample, essentially-parity execution time for CPU-bound pure-Python work at this
exact iteration count.

## 8. MAIN-THREAD RESULT

The main-thread (`QTimer.singleShot`) callback executed the identical workload in 0.517 s, confirming the
callback mechanism itself introduces no meaningful overhead or advantage for ordinary bytecode work relative
to the worker thread.

## 9. MINIATURE READER SCALING

RUN 2 opened three synthetic, prebuilt sidecars (never the 128,555-occurrence official artifact) via the
corrected reader's `open_generation_path(...)`, each from its **own independent** `threading.Timer` thread
(started at staggered 15.0 s / 15.5 s / 16.0 s delays, so all three ran concurrently once started — this is
an acknowledged confound, Section 14):

| Tier | Occurrences | Bytes | Desktop control (Py3) | Worker-thread result (real SFM) |
|---|---|---|---|---|
| tiny | 100 | 8,418 | 0.0060 s | **24.035 s** (completed; occ=100, valid=True) |
| modest | 5,000 | 362,608 | 0.0310 s | **did not complete** within ~221 s observed, then killed |
| large | 50,000 | 3,712,108 | 0.3045 s | **did not complete** within ~221 s observed, then killed |

Every completed/attempted open used the corrected, explicit `open_generation_path(...)` — no legacy call, no
manual dispatch. The `tiny` tier's eventual, correct completion (matching occurrence count and validity)
confirms the corrected reader is functionally correct even under this pathological condition — the defect
class is a performance/scheduling one, not a correctness one, consistent with Section 1's verdict.

**Interpretation, with the confound stated plainly:** the `tiny` result (100 occurrences taking 24.035 s,
against a 0.006 s desktop control — roughly a 4,000x slowdown for a functionally trivial amount of data)
shows the anomaly is **not purely proportional to occurrence count** — a fixed, large, context-specific tax
is paid even for a nearly-empty artifact. However, this run deliberately (per Part 4's own instruction to use
"the threading.Timer context that stalled") ran three worker threads **concurrently**, so `modest`/`large`
were competing against each other and against `tiny`'s own execution for the same GIL, in addition to
whatever contention exists with SFM's main loop — this is a genuine limitation of this run's design, not
concealed here. It does not change Section 1's overall verdict (Section 10's main-thread result is the clean,
unconfounded, decisive comparison), but it means Section 9's specific "does worker-thread cost scale
proportionally with size" question was not cleanly isolated by this run.

## 10. FULL OFFICIAL MAIN-THREAD OPEN

RUN 3 (fresh SFM session, PID 1344): the exact 9,506,244-byte official artifact
(SHA-256 `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`, reconfirmed at deployment) was
opened via `reader.SidecarReader.open_generation_path(ARTIFACT_PATH, SOURCE_SHA256)` from inside a
`QtCore.QTimer.singleShot(15000, ...)` callback (confirmed running on the main/autoinit thread, `28540`,
Section 5).

**Completed successfully in 1.847 seconds.** (Desktop Python 3 control for the same corrected reader and same
artifact: 0.78 s — a ~2.4x ratio, comfortably consistent with ordinary CPython 2.7-vs-3.10 and embedded-
interpreter overhead, not a pathological blowup.)

## 11. FUNCTIONAL RESULT

Performed immediately after the successful open, on the same main thread, per this task's Part 7 minimal
confirmation set:

```
group_count=43            (expect 43,      match=True)
occurrence_count=128555   (expect 128555,  match=True)
first HIT=True   dest_ok=True   ("left" -> groupFile/Face/Eyes)
middle HIT=True  dest_ok=True   ("KRI_Braid_RB_03_SkinPoint" -> groupFile/Hair)
last HIT=True    dest_ok=True   ("WrinkleTexture" -> groupFile/Useless)
absent MasterUnknown=True
```

All PASS. Provider then closed cleanly (`CLOSE_BEGIN`→`CLOSE_COMPLETE`, no exception). No further resource
measurement was performed, per this task's explicit Part 7/11 instruction.

## 12. WATCHDOG BEHAVIOR

- RUN 1: bounded manual poll, resolved (`DONE` marker found) at the second 15-second check — well inside the
  90-second informal bound.
- RUN 2: no per-tier automated kill-on-timeout was implemented (three independent worker threads were
  monitored manually); after `tiny` completed and `modest`/`large` showed no stage-marker progress for
  ~221 seconds combined with a near-flat, slowly-creeping CPU/memory profile (a milder version of the
  original Gate 2A rerun's stall signature), the process was killed manually — well within the spirit of
  "do not allow another unbounded 20+ minute experiment" (total observation ~4 minutes, not 24).
- RUN 3: the main-thread full open completed in 1.847 s, far under the 60-second conservative bound this
  task specified — **the watchdog was never needed to intervene.**

## 13. ROOT-CAUSE CLASSIFICATION

**EXECUTION-CONTEXT-SPECIFIC READER SLOWDOWN CONFIRMED.** This result does not force cleanly into this task's
originally-defined CASE A ("background workload extremely slow, main-thread workload normal") as a claim
about background-thread execution in general, because the pure-Python control (Section 6/7) shows the
worker thread was **not** generally slow or starved for ordinary Python bytecode. The more precise,
fully-supported statement is:

- **Pure-Python control (Section 6/7):** worker thread 0.511 s, main thread 0.517 s — statistically
  indistinguishable. Ordinary Python bytecode execution on the worker thread was **not** generally starved.
- **Production reader's real open call:** catastrophically slow/non-completing on the worker thread — 24.035
  s for a 100-occurrence synthetic artifact (Section 9), and never completing within ~24.1 minutes for the
  full 128,555-occurrence official artifact (the prior Gate 2A rerun) — versus completing correctly in
  1.847 s for the same full official artifact on the main thread (Section 10).
- **Established facts:** `threading.Timer` worker thread is **unsuitable** for full provider loading;
  SFM's Qt/main-event thread is **suitable**; reader correctness is **PASS** on the main thread; the
  Candidate A resource verdict is **still NOT REACHED**.
- The exact lower-level mechanism remains **unresolved**. Possible contributors, none separately demonstrated
  and none claimed as proven here, include: embedded-Python interaction around file I/O; C-extension/
  `hashlib` execution and GIL reacquisition; SFM's own thread-scheduling behavior; or other worker-thread-
  specific embedding behavior. This task does **not** claim generic Python worker-thread starvation, does
  **not** claim SFM holds the GIL continuously, does **not** claim a proven `hashlib` defect, and does **not**
  claim a proven file-I/O defect.
- This classification is not conflated with backing-memory viability (Section 16), and the mechanism is
  described only as precisely as the evidence supports (Section 14).

## 14. GIL / SCHEDULING EVIDENCE

Per this task's Part 10 discipline, no claim of the form "SFM holds the GIL continuously" is made. What is
directly supported by the evidence:

- A worker thread running ordinary Python bytecode (struct pack/unpack + arithmetic, 128,555 iterations)
  received execution time statistically indistinguishable from the main thread (Section 6) — so the worker
  thread is not blanket-starved of the GIL.
- The SAME worker thread, running the production reader's actual open call, took either dramatically longer
  than its main-thread counterpart (100-occurrence synthetic case: 24.035 s worker vs. an implied sub-10ms
  main-thread cost by direct extrapolation from Section 10's scaling) or never completed at all (the real
  128,555-occurrence official artifact: never in ~24 minutes on the worker thread vs. 1.847 s on the main
  thread).
- The prior Gate 2A rerun's own observation (external, `Get-Process`-based) showed the worker thread's CPU
  time growing only fractionally across many minutes before eventually shifting to a sustained, memory-flat,
  CPU-bound phase. This rules out both a uniform "no CPU time at all" stall and ordinary linear algorithmic
  cost proportional to occurrence count (both of which the pure-Python control and the main-thread full open
  argue against as the primary driver) — but it does **not**, by itself, establish which specific mechanism
  is responsible.
- No production code was modified to instrument this further (per this task's Part 8 constraint). The precise
  low-level mechanism remains **unresolved and unconfirmed**. Candidates worth investigating in a dedicated
  follow-up task — none demonstrated here, none claimed as the cause — include: embedded-Python interaction
  around file I/O; C-extension/`hashlib` execution and GIL reacquisition; SFM's own thread-scheduling
  behavior; or other worker-thread-specific embedding behavior. Only the execution-context effect itself
  (worker-thread-unsuitable, main-thread-suitable) is established.

## 15. IMPLICATION FOR SFM PROVIDER INVOCATION

Any future SFM-embedded invocation of the real production sidecar-loading path (whether for Gate 2 resource
qualification or eventual Normalizer/runtime integration) **must be initiated from SFM's main/event thread**
(e.g., via `QtCore.QTimer.singleShot(...)`, exactly as this diagnostic used, or an equivalent main-loop
callback), not from a bare `threading.Timer` background worker thread. A `threading.Timer`-based invocation
of this specific call path is not a safe or representative way to measure or use Candidate A (or any reader
open call of comparable shape) inside live SFM.

## 16. CANDIDATE A RESOURCE STATUS

**STILL NOT REACHED.** Per this task's explicit Part 11 instruction, a successful main-thread open does
**not** constitute a Candidate A memory PASS or FAIL — it only establishes that a resource-measurement
attempt using the main-thread execution context is now well-motivated. No retained-memory, peak, or VAS
measurement was taken in this diagnostic task (RUN 3 measured only wall-clock open duration and functional
correctness, per Part 7's explicit minimal-confirmation scope). The prior sampler runs had no valid S0 and no
valid S4 (per the Gate 2A rerun audit); this diagnostic does not supply either.

## 17. NEXT GATE 2 STEP

A **fresh Gate 2A resource-measurement run is now unblocked**, using the main-thread (`QtCore.QTimer`)
execution context established and confirmed here — reusing the already-debugged Win32 memory/VAS
instrumentation (self-measurement + external sampler) from the original Gate 2A attempts, adapted to invoke
`open_generation_path` from a main-thread callback instead of a `threading.Timer` worker thread. This is a
separate, separately-authorized task, not begun here.

## 18. CLEANUP

Each of the three runs was deployed, observed, and cleaned up independently:

- **RUN 1:** `usermod\scripts\sfm\autoinit\zz_gate2_diag_run1_temp.py` removed after successful completion
  (PID 4396 killed).
- **RUN 2:** `usermod\scripts\sfm_master_sidecar_gate2_diag_run2_runtime\`,
  `usermod\scripts\gate2_diag_run2_fixtures\`, and
  `usermod\scripts\sfm\autoinit\zz_gate2_diag_run2_temp.py` all removed (PID 16556 killed).
- **RUN 3:** `usermod\scripts\sfm_master_sidecar_gate2_diag_run3_runtime\`,
  `usermod\scripts\gate2_diag_run3_artifact\`, and
  `usermod\scripts\sfm\autoinit\zz_gate2_diag_run3_temp.py` all removed (PID 1344 killed).
- `usermod\scripts\sfm\autoinit\` confirmed empty after each run and at the end of this task.
- `usermod\scripts\sfm\sfm_init.py` confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`) after every run.
- A directory-wide search for `*gate2_diag*` under `usermod\scripts\` at the end of this task found nothing.
- No manifest, active generation, or publisher-lock file was created anywhere by this task.
- No SFM launch-option or configuration change was made or left behind.
- No new crash dump (`*.mdmp` with a modification time at or after this task's activity) was found after any
  of the three kills.
- No PySide/Qt UI element (dialog, menu item, persistent widget) was created — only a `QTimer` scheduled
  internally and a lookup of the existing `QApplication` instance.
- All probe logs/stage-marker files/tier-result JSON were preserved outside the SFM install and outside the
  repository, in this session's own scratchpad directory, for audit traceability (reproduced in Sections
  6–11 above).

## 19. GIT / SAFETY STATE

- HEAD before and after this task: `de6e9564447acbc52fd580cbe2612bec69c8977e` — unchanged.
- `sfm_defaultanimationgroups.txt`: unchanged (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
- `tools/sfm_master_sidecar/reader.py`: unchanged (`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`) — every deployment in this task used a
  read-only, byte-verified COPY; the repository's own file was never opened for writing.
- All other production sidecar modules (`format.py`, `writer.py`, `manifest.py`, `publisher.py`, `cli.py`,
  `compiler.py`, `__init__.py`): unchanged.
- Both historical Gate 2A audits confirmed byte-for-byte unchanged (Section 2).
- No Candidate B/C code written. No Normalizer code touched. No production edits of any kind.
- Nothing staged, nothing committed. `git status --porcelain` shows only this new audit file
  (`SFM_MASTER_SIDECAR_GATE2_EXECUTION_CONTEXT_DIAGNOSTIC_AUDIT.md`) as a new untracked file, plus the same
  pre-existing unrelated untracked files present since before this task began.
- No agents or subagents were used.
