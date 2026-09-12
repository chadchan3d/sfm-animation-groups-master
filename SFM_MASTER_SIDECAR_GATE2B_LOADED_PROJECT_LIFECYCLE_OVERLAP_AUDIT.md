# SFM Master Sidecar — Gate 2B: Loaded-Project Headroom, Repeated Lifecycle, Generation Overlap

Measurement/qualification only. No production reader/writer/compiler code modified. No Candidate B/C
implemented, no Normalizer integration, no binary-format change, no Master change. All provider invocation
was diagnostic/test-only. Nothing committed.

## 1. VERDICT

**CANDIDATE A — RETAIN WITH CONCERN; ALTERNATIVE-BACKING INVESTIGATION WARRANTED.** Candidate A is
functionally sound and its repeated-lifecycle behavior is stable, but loaded-project contiguous-VA headroom
is already constrained in this environment, and generation overlap produced a concerning further reduction.
This authorizes a bounded Candidate B/C investigation. It does **not** yet select Candidate B or Candidate C,
and it is not a functional-defect finding.

Candidate A opened the official artifact correctly every time in this task — a real, substantial, 116-shot
loaded project, five repeated open/close cycles, and a two-generation overlap all completed with **zero
exceptions** and fully correct functional results (Section 2). Retained/peak deltas in isolation (tens of
MiB) are not alarming on their own, and repeated-cycle private-memory behavior was stable, not monotonically
ratcheting (Section 8). But the **loaded-project starting headroom was drastically smaller than the
idle-session baseline** (largest contiguous free VA region ≈52.4 MiB loaded, vs. ≈1.94 GiB idle in the prior
Gate 2A baseline — a ≈97% reduction, a fact about this loaded project's own footprint, not caused by
Candidate A), and the **largest contiguous free region measured smaller at two later points in this same
session** — ≈36.6 MiB later during the repeated-cycle qualification (Part B), and ≈14.7 MiB during and after
the generation-overlap qualification (Part C) — **and had not recovered by the end of this task's observation
window.** This measurement isolates the second reduction to the generation-overlap window specifically
(Section 13); the first reduction is time-correlated with Part B's cycling but, as with the rest of this
live, real, concurrently-active SFM session, is not isolated with certainty from other activity in the
process (Section 8's caveat applies equally here). Taken together, this is enough to say Candidate A
**materially increases concern about contiguous-VA headroom and fragmentation under realistic loaded-project
and generation-overlap conditions** — the "materially fails" bar this task's own verdict logic uses to
authorize further investigation — without claiming the reduction is permanent or unrecoverable by the
process beyond what was actually observed, and without claiming every measured address-space change in this
session was uniquely caused by Candidate A.

## 2. PROJECT / SESSION DESCRIPTION

- File: `E:\SourceFilmMaker Sessions\Momiji at the Spa\momijiprepoolspascenes.dmx` (219 MB on disk), an
  existing, real, substantial project selected by the user from their own working library.
- Loaded via the user's own manual File-menu action in the live SFM UI (not scripted — see Section 22 for
  why: `sfmApp.OpenDocument(...)` was found, via bounded diagnosis across 7 path variants and both
  `forceSilent` settings, to fail silently/immediately in this build/environment; the mechanism was never
  identified, and rather than continue guessing, loading was handed to the user).
- Confirmed loaded via `sfmApp.HasDocument()` (True) and `sfmApp.GetShots()`: **116 shots** — a genuinely
  substantial real project, not a trivial fixture.
- The Gate 2B measurement script itself ran as an SFM "mainmenu" script
  (`usermod/scripts/sfm/mainmenu/Gate2BDiagnostic/Gate2B_Candidate_A_Measurement.py`), triggered by the user
  from SFM's Scripts menu — the same main/event thread execution context qualified in the prior Gate 2A
  main-thread baseline (thread ID recorded at load, `1196`, confirmed as the thread SFM's own document/UI
  work runs on).
- SFM was never restarted, never killed, and remained the user's own live, continuing session throughout and
  after this task.

## 3. LOADED-PROJECT S0

Nearest external sample to `PROJECT_S0_CAPTURED` (offset 23 ms):

- PrivateUsage: **3,321,802,752 bytes (≈3.093 GiB)**
- WorkingSetSize: **3,253,350,400 bytes (≈3.031 GiB)**

Nearest VAS scan:

- Committed: 3,716,046,848 bytes (≈3.460 GiB)
- Reserved: 353,251,328 bytes (≈336.8 MiB)
- Free: **225,669,120 bytes (≈215.2 MiB)**
- **Largest free contiguous region: 54,919,168 bytes (≈52.4 MiB)**

This is the real, substantial pre-existing memory cost of a 116-shot loaded project on the 4 GiB LAA ceiling
— **already leaving only ≈52.4 MiB of contiguous free address space before any sidecar work begins.** This
is not attributable to Candidate A; it is the project's own footprint. It is reported here because it is the
correct incremental baseline for everything that follows, per this task's own Part A instruction not to
compare against the idle S0 as though they were the same process state.

## 4. SINGLE CANDIDATE-A OPEN PEAK (Part A)

`open_generation_path(G1, ...)` on the main thread: **1.916 s** (consistent with the prior idle-session
baseline's 1.841–1.847 s; the loaded project did not materially slow the open call itself).

- Peak (within `A_OPEN_BEGIN`→`A_STEADY_CAPTURED`, 24 correlated samples): PrivateUsage **3,386,494,976**
  bytes — **delta vs S0: +64,692,224 bytes (≈61.70 MiB)**.
- Steady (1.5 s after open, `gc.collect()`'d): PrivateUsage **3,335,069,696** — **delta vs S0: +13,266,944
  bytes (≈12.65 MiB)**.
- Post-close: PrivateUsage **3,324,755,968** — **delta vs S0: +2,953,216 bytes (≈2.82 MiB)** residual.

Groups=43, occurrences=128,555 — both matched exactly. `is_valid()` True.

## 5. STEADY RETAINED DELTA

Reported above (Section 4): **+13,266,944 bytes (≈12.65 MiB)** for the single isolated Part-A open, in the
loaded-project context. This is smaller in absolute terms than the idle-session baseline's ≈38.83 MiB
retained figure — plausibly because the loaded project's own already-active allocator arenas had more
existing free space to absorb Candidate A's allocations into without requesting fresh pages from the OS (a
plausible, not confirmed, explanation; not claimed as proven mechanism).

## 6. FREE VAS / LARGEST FREE REGION (Part A only)

Unchanged through Part A alone: largest free region remained **54,919,168 bytes (≈52.4 MiB)** throughout
`A_OPEN_BEGIN`→`A_CLOSE_COMPLETE` — no erosion attributable to the single isolated open/close cycle by
itself (Section 9 shows the erosion begins during Part B).

## 7. REPEATED-CYCLE TABLE (Part B, 5 cycles, same loaded session)

| Cycle | Open elapsed | Peak Priv (delta vs S0) | Steady Priv (delta vs S0) | Post-close Priv (delta vs S0) |
|---|---|---|---|---|
| 1 | 1.949 s | 3,386,458,112 (+64,655,360 / ≈61.66 MiB) | 3,363,401,728 (+41,598,976 / ≈39.67 MiB) | 3,333,124,096 (+11,321,344 / ≈10.80 MiB) |
| 2 | 2.028 s | 3,384,434,688 (+62,631,936 / ≈59.73 MiB) | 3,363,868,672 (+42,065,920 / ≈40.12 MiB) | 3,329,011,712 (+7,208,960 / ≈6.88 MiB) |
| 3 | 1.998 s | 3,371,831,296 (+50,028,544 / ≈47.72 MiB) | 3,323,711,488 (+1,908,736 / ≈1.82 MiB) | 3,323,711,488 (+1,908,736 / ≈1.82 MiB) |
| 4 | 1.991 s | 3,372,531,712 (+50,728,960 / ≈48.39 MiB) | 3,352,825,856 (+31,023,104 / ≈29.59 MiB) | 3,311,931,392 (−9,871,360 / ≈−9.41 MiB) |
| 5 | 1.978 s | 3,372,568,576 (+50,765,824 / ≈48.42 MiB) | 3,325,014,016 (+3,211,264 / ≈3.06 MiB) | 3,313,737,728 (−8,065,024 / ≈−7.69 MiB) |

(Deltas are all vs. loaded-project S0, Section 3. Every cycle: `open_generation_path` PASS, `is_valid()`
True, double-`close()` harmless, no exceptions.)

## 8. RESIDUAL TREND

**STABLE — not ratcheting.** Post-close residual deltas run +10.80, +6.88, +1.82, −9.41, −7.69 MiB across the
five cycles: a **downward** trend, not monotonic growth, with the last two cycles actually finishing *below*
the original S0 reading. Peak-per-cycle also trends down (≈61.7 → ≈59.7 → ≈47.7 → ≈48.4 → ≈48.4 MiB),
consistent with the process's allocator reusing arena space freed by earlier cycles rather than requesting
fresh pages each time. This is exactly the "stable plateau" pattern this task's own instructions distinguish
from a ratcheting leak, and is a genuinely reassuring result for repeated-lifecycle behavior specifically.
**Caveat, stated plainly:** this is a real, live, working SFM session with the project's own background
activity (asset reference-counting, undo history, etc.) running concurrently — the negative deltas in cycles
4–5 cannot be attributed to Candidate A's own behavior with certainty; some of this drift may reflect
unrelated SFM activity releasing memory coincidentally. The absence of a ratcheting *upward* trend is the
robust, defensible conclusion; the exact per-cycle numbers carry that caveat.

## 9. G1 BASELINE (Part C)

A sixth open of G1 (fresh provider, retained): steady-state (1.5 s after open) PrivateUsage
**3,352,473,600** — **delta vs S0: +30,670,848 bytes (≈29.25 MiB)**. Largest free region at this point: still
**38,338,560 bytes (≈36.57 MiB)** — already down from the Section 3/6 starting value of ≈52.4 MiB. This
step-down (52.4 → 36.6 MiB) occurred **during Part B** (first observed at the B_CYCLE_2→3 transition,
Section 13) and had **not recovered** by the time Part C began, several cycles and close operations later.

## 10. TWO-GENERATION STEADY COST (Part C overlap)

With G1 still retained and valid, G2 (the minimally-changed synthetic variant, 1 additional control,
occurrence_count 128,556 vs. G1's 128,555 — confirmed distinct and both simultaneously valid) opened
successfully:

- **G1+G2 overlap steady (1.5 s after G2 open):** PrivateUsage **3,394,691,072** — **delta vs S0: +72,888,320
  bytes (≈69.51 MiB); delta vs G1-alone: +42,217,472 bytes (≈40.26 MiB).**
- **Overlap peak** (within `C_G2_OPEN_BEGIN`→`C_OVERLAP_STEADY_CAPTURED`): PrivateUsage **3,413,725,184** —
  **delta vs S0: +91,922,432 bytes (≈87.68 MiB).**
- Both providers independently confirmed `is_valid()` True, correct and distinct `occurrence_count()` values,
  simultaneously — Candidate A correctly supports two live, independent generations at once with no
  correctness defect.
- **Largest free region during this step measured smaller: 21,757,952 bytes (≈20.75 MiB) then
  15,388,672 bytes (≈14.68 MiB)** — a second, larger reduction, temporally coincident with the G1+G2
  overlap window specifically (Section 13's full timeline shows the drop occurring at
  `C_G2_OPEN_COMPLETE`/`C_OVERLAP_STEADY_CAPTURED`). Coincidence in time is what this measurement
  establishes; it is not, on its own, isolated proof that no other concurrent process activity contributed.

## 11. G1-RELEASE RESULT

After `g1.close()` and 1.5 s stabilization: G2 remained `is_valid()` True with its correct
`occurrence_count()` (128,556) — G1's release did not disturb G2 in any way (expected, given Candidate A's
immutable, independent-buffer design). PrivateUsage at this point: **3,326,939,136** — **delta vs S0:
+5,136,384 bytes (≈4.90 MiB)**, i.e. most of the overlap's incremental cost was released. **Largest free
region: still 15,388,672 bytes (≈14.68 MiB) — unchanged from the overlap peak, i.e. releasing G1 while G2
remained open did not recover any of the reduction observed at this point in the session.**

## 12. FINAL RELEASE RESULT

After `g2.close()` and 1.5 s stabilization: PrivateUsage **3,326,939,136** (same reading as Section 11 at
this sampling cadence — both close operations happened close enough together that no distinct intervening
external sample was captured, a measurement-granularity limitation, not a claim that G2's release cost
nothing). **Largest free region: still 15,388,672 bytes (≈14.68 MiB)** — confirmed **unchanged from the
overlap peak all the way through both providers being fully closed.** The largest-free-region reductions
first observed during Part B and Part C did **not** recover at any point this task observed, up through the
end of this measurement session. Whether the region would recover later (e.g. after further unrelated SFM
activity, or after the process is eventually closed) is not something this task measured and is not claimed
either way.

## 13. FRAGMENTATION / HEADROOM ASSESSMENT

Full largest-free-region timeline across the entire task (65 VAS scans, 2 s cadence):

| Phase | Largest free region |
|---|---|
| Session start / Part A / B cycles 1–2 | 54,919,168 bytes (≈52.4 MiB) — flat, unchanged |
| From B cycle 2→3 transition through end of Part B | 38,338,560 bytes (≈36.6 MiB) — measured smaller from this point on; did not recover within the remainder of Part B |
| During Part C G2 open / overlap steady | 21,757,952 → 15,388,672 bytes (≈20.8 → ≈14.7 MiB) — a second, larger reduction |
| G1 release, G2 release, final | 15,388,672 bytes (≈14.7 MiB) — unchanged; no recovery observed within this task's remaining observation window |

**This is the central, load-bearing finding of this task.** Two discrete reductions in the largest
contiguous free VA region were measured — one time-correlated with ordinary repeated open/close cycling, a
second, larger one time-correlated with two-generation overlap — for a cumulative **≈73% reduction
(52.4 → 14.7 MiB)** in the single largest block of contiguous address space available on this 4 GiB LAA
process, within one measurement session, that had not recovered by the time this task's observation ended,
even after every provider was closed. This measurement does not isolate Candidate A as the exclusive cause of
either reduction with certainty — this is a live, real, concurrently-active SFM session (Section 8's caveat
applies here too) — and does not establish that the reduction is permanent or unrecoverable by the process
beyond the window actually observed. What it does establish is the ≈73% reduction itself, its timing relative
to Candidate A's own operations, and the absence of recovery within this task's observation window. Total
committed VAS stayed in the 3.7–3.8 GiB range throughout (i.e., the process was already close to its 4 GiB
ceiling before this task began, purely from the loaded project itself) — meaning the margin for any future
large contiguous allocation (whether by Candidate A again, or by an unrelated SFM subsystem) measured
**materially thinner** at the end of this session than at its start, and thinner than any measurement in the
idle-session Gate 2A baseline
ever suggested (which showed zero fragmentation effect, Section 16 of that audit). This is a genuinely
different and more concerning picture than the idle baseline gave, and is exactly the kind of finding Part A
of this task was designed to surface.

## 14. CANDIDATE A VERDICT

**CANDIDATE A — RETAIN WITH CONCERN; ALTERNATIVE-BACKING INVESTIGATION WARRANTED.** Not "not viable" — every
open, in every context tested across this entire Gate 2 arc (idle main-thread, loaded-project main-thread,
five repeated cycles, two-generation overlap), succeeded functionally with zero defects, and repeated-cycle
lifecycle behavior was stable (Section 8). But the fragmentation finding (Section 13) — a genuine, measured
reduction in contiguous address-space headroom that had not recovered within this task's observation window,
observed specifically under realistic loaded-project and generation-overlap conditions that the idle-session
baseline could not have revealed — is enough, on its own, to say Candidate A materially increases concern
about contiguous-VA headroom and fragmentation under those conditions. That is sufficient to authorize a
bounded Candidate B/C investigation; it does not by itself select Candidate B or Candidate C, and it does not
move Candidate A to a "not viable" or functional-failure verdict.

## 15. CANDIDATE B/C JUSTIFICATION

**Yes — a bounded Candidate B/C design comparison is now justified**, specifically targeted at the
fragmentation question this task surfaced: does an alternative backing strategy (e.g., a bounded/streaming
read that avoids retaining a second complete immutable copy during generation overlap, or a backing model
that returns memory to the OS more predictably on close) measurably reduce or eliminate the largest-free-region
reduction seen here (which had not recovered within this task's observation window)? This is explicitly NOT
a mandate to abandon Candidate A, implement
anything yet, or declare a final backing choice — only that the isolated-baseline "clean pass" from the
prior main-thread Gate 2A task does not hold up once tested under the realistic loaded-project + overlap
conditions this task added, and that gap is worth a bounded, deliberate investigation before treating
Candidate A as settled.

## 16. CLEANUP

- All deployed files removed after the measurement completed and was confirmed successful:
  `usermod\scripts\sfm_master_sidecar_gate2b_runtime\`,
  `usermod\scripts\gate2b_artifact\` (G1/G2 binaries + manifest), and
  `usermod\scripts\sfm\mainmenu\Gate2BDiagnostic\` (the mainmenu script itself) — all removed entirely.
- Directory-wide search for `*gate2b*` under `usermod\scripts\` after cleanup: **none found.**
- `usermod\scripts\sfm\sfm_init.py` confirmed byte-for-byte unchanged
  (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`) throughout this task (autoinit was
  never used for this task's actual measurement — only the diagnostic sub-attempts, Section 22, which were
  each cleaned up immediately after use).
- **The user's own live SFM session (PID 22576) was never terminated by this task** — it remained the user's
  own, ongoing, real working session throughout and after this task's measurement, exactly as intended (this
  was NOT a disposable session, unlike every other Gate 2 task in this arc).
- No manifest, active generation, or publisher-lock file was created anywhere by this task.
- No SFM launch-option or configuration change was made or left behind.
- The canonical Master file was never opened for writing by this task; G2 was produced from an in-memory
  modified copy of its bytes, compiled directly to a binary artifact, with the on-disk canonical file
  reconfirmed byte-identical immediately after (Section 21).
- All measurement logs (stage markers, result log, external sampler CSV/VAS/stdout, cycle-results JSON) were
  preserved outside the SFM install and outside the repository, in this session's own scratchpad directory.

## 17. GIT / SAFETY STATE

- HEAD before and after this task: `06cb52b39e2b302b05728ac089f8e6af016528d6` — unchanged.
- `sfm_defaultanimationgroups.txt`: unchanged (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
- `tools/sfm_master_sidecar/reader.py`: unchanged
  (`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`) — every deployment in this task used a
  read-only, byte-verified COPY; the repository's own file was never opened for writing.
- All other production sidecar modules: unchanged. No Candidate B/C code written. No Normalizer code
  touched. No production edits of any kind.
- Nothing staged, nothing committed. `git status --porcelain` shows only this new audit file as untracked,
  plus the same pre-existing unrelated untracked files present since before this task began.
- No agents or subagents were used.

## 18. G1/G2 ARTIFACT IDENTITY (for reproducibility)

- G1 (official): 9,506,244 bytes, SHA-256 `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`
  — identical to the qualified official artifact throughout this project.
- G2 (minimally-changed synthetic test variant): built from an **in-memory-only** modified copy of the
  Master's text (one additional harmless control literal,
  `"Gate2BOverlapTestControlDoNotUseElsewhere"`, appended to the last top-level group) — never written to
  the canonical Master file on disk. Source SHA-256
  `ae0a196d98ab51d1093f88c3e3c9d9b949daab7314c61295cea4b8a6e7ca501e`; compiled artifact 9,506,378 bytes,
  SHA-256 `4aa75985d1ccceefaaae8bd570616593aebd5d2769624ea2c7d81dc8ced74901`.
- The canonical `sfm_defaultanimationgroups.txt` on disk was verified byte-identical to its pre-task state
  immediately after G2 was generated.

## 19. FUNCTIONAL RESULTS (both artifacts, every open)

- G1: `group_count()==43`, `occurrence_count()==128555` — confirmed at Part A and at every one of the five
  Part B cycles.
- G2: `occurrence_count()==128556` (one more than G1, as expected from the single added control) — confirmed
  distinct from G1's count during the Part C overlap, both providers simultaneously valid.
- No `AuthorityUnavailable`, no exception, no incorrect result anywhere in this task.

## 20. THREAD-CONTEXT CONFIRMATION

The mainmenu script executed on thread ID `1196` at load — the same thread SFM's own document-loading and
UI work runs on, matching the qualified execution context from the prior Gate 2 diagnostic
(`SFM_MASTER_SIDECAR_GATE2_EXECUTION_CONTEXT_DIAGNOSTIC_AUDIT.md`). `threading.Timer` was not used anywhere
in this task.

## 21. SFM RESPONSIVENESS

`Get-Process` confirmed `Responding: True` for the SFM process throughout and immediately after this task's
measurement completed. The user's session remained interactively usable.

## 22. DIAGNOSTIC NOTE: `sfmApp.OpenDocument` COULD NOT BE MADE TO WORK PROGRAMMATICALLY

Before falling back to a manual user-driven project load, this task bounded-diagnosed
`sfmApp.OpenDocument(filename=..., forceSilent=...)` across: both backslash and forward-slash path forms; the
originally-chosen large (219 MB) nested project file; two much smaller pre-existing test `.dmx` files already
in the session root; a copy placed at a no-space drive-root path; and a copy placed inside SFM's own
`game\usermod\` directory tree. Every combination returned `False`/`0` immediately (single-digit to
low-hundreds-of-milliseconds), with **no error dialog** shown even with `forceSilent=False` (topLevelWidgets
enumeration before/after showed no new dialog). The mechanism was never identified; per the user's own
choice, this was not investigated further, and the real project used in this task was loaded by the user
manually instead. This is recorded here as a genuine, unresolved environment/API limitation for any future
task that might need scripted document loading — not something this task attempted to patch or work around
via reader/production code changes (none were made).
