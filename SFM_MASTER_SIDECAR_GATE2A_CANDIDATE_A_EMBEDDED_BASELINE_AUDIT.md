# SFM Master Sidecar — Gate 2A: Embedded SFM x86 Candidate A Resource/Performance Baseline

Qualification only. **This run discovered a genuine, reproducible Python-2.7-specific compatibility defect
in production `reader.py` that blocked the resource/performance measurement itself before Candidate A's
actual retained/peak cost could ever be observed.** Per this task's own explicit instruction, the defect was
NOT patched in this task. No production code was modified. No Candidate A resource verdict (PASS/EXCEEDS)
was reached, because the defect prevented the reader from ever completing the open+validation step this
whole measurement depends on.

## 1. VERDICT

**STOP — GENUINE DEFECT DISCOVERED. Candidate A resource verdict NOT REACHED (Part 18 does not apply until
this defect is separately fixed and re-qualified).**

`reader.SidecarReader.open_generation(ARTIFACT_PATH, SOURCE_SHA256)`, called with `ARTIFACT_PATH` as an
ordinary file-path string (exactly as the production API's own docstring and the final spec describe as a
supported "path_or_bytes" call shape), failed under the real embedded Python 2.7.5 interpreter with:

```
AuthorityUnavailable("magic mismatch: expected 'SFMMSTR\x00', found 'E:\\Steam'",)
```

**Root cause, confirmed directly from the reader's own source (`tools/sfm_master_sidecar/reader.py`, lines
132–139):**

```python
def _read_all(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes)
    f = open(path_or_bytes, "rb")
    try:
        return f.read()
    finally:
        f.close()
```

Under Python 2.7, `bytes` **is** `str` (they are the exact same builtin type — there is no distinct native
byte-string type separate from `str`, unlike Python 3). Every ordinary Python 2.7 string literal — including
an ordinary filesystem path — therefore satisfies `isinstance(path_or_bytes, (bytes, bytearray))` and takes
the `return bytes(path_or_bytes)` branch, which is a no-op identity return of the PATH STRING ITSELF,
**never reaching the `open(path_or_bytes, "rb")` branch at all.** The reader then attempted to validate the
literal text of the path (`"E:\SteamLibrary\...official_sidecar.bin"`) as if those characters were the
sidecar's own binary header — hence the "magic mismatch" report showing the first 8 characters of the path
string (`E:\Steam`) instead of the artifact's real `SFMMSTR\x00` magic. **This is a categorical,
deterministic defect: it will misfire for every path-string argument, every time, under Python 2.7 — not an
intermittent or environment-specific fluke.**

**Why Gate 1 H1 did not catch this:** H1's probe always passed already-decoded `bytes` (from a base64
literal embedded in the probe script) directly to `open_generation`, never a path string. All B2B–B2E
Python 3 testing also never exposed this, because in Python 3 `str` and `bytes` are genuinely distinct
types, so `isinstance(path_string, (bytes, bytearray))` correctly evaluates `False` there, letting the
intended path-string branch work exactly as designed — completely masking this defect in every phase of
qualification prior to this one. This is the first time `open_generation` was ever called with a path-string
argument under real Python 2.7.

Per explicit task instruction, this defect was **not fixed in this task**. Resource/performance measurement
(Parts 9–18) could only be completed through **S0 (idle baseline)**, **S1 (runtime import)**, and **S2 (a
separate, test-only verification read of the artifact bytes performed before `open_generation` was ever
called)** — see Section 9–11. **S3 onward (open/validation, steady retained state, functional check, lookup
performance, close) were never reached and have no data.**

## 2. QUALIFIED BASELINE

- HEAD before and after this task: `59be3a5c044cae29b4d1890c9fa1fdf2998a90f3` (unchanged).
- Final Gate 1: PASS, 36/36 mandatory requirements, 0 OPEN, 0 FAIL (unaffected by this finding — Gate 1 H1
  never exercised the path-string code path, so its own PASS verdict remains factually accurate for what it
  actually tested).
- Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (unchanged).
- Official sidecar SHA-256: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`, size
  9,506,244 bytes (both reproduced exactly outside SFM — Section 5).

## 3. SFM / PYTHON TARGET IDENTITY

- SFM root: `E:\SteamLibrary\steamapps\common\SourceFilmmaker` (same install used for Gate 1 H1).
- Executable: `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\sfm.exe`.
- Embedded Python, recorded directly from the running process: `sys.version = '2.7.5 (default, Jul 3 2013,
  16:44:46) [MSC v.1600 32 bit (Intel)]'`; `os.getpid() = 18684` for this run.

## 4. SFM EXECUTABLE ADDRESS-SPACE CHARACTERISTICS

Determined by direct PE-header inspection of `sfm.exe` (no execution needed for this part), confirmed
against the host OS's own architecture:

- **Machine:** `0x014c` (IMAGE_FILE_MACHINE_I386 — 32-bit x86).
- **Characteristics:** `0x0122` — `IMAGE_FILE_32BIT_MACHINE` (0x0100) **set**; `IMAGE_FILE_LARGE_ADDRESS_AWARE`
  (0x0020) **set**; `IMAGE_FILE_EXECUTABLE_IMAGE` (0x0002) set; not a DLL.
- **Host OS:** confirmed 64-bit Windows (`wmic os get osarchitecture` → `64-bit`; `platform.machine()` →
  `AMD64`; `System Type: x64-based PC`).
- **Effective user-mode virtual-address ceiling:** because `sfm.exe` is a 32-bit, `LARGE_ADDRESS_AWARE`
  process running under WOW64 on a 64-bit Windows host, it receives the **full ~4 GiB (0x100000000)**
  user-mode address space automatically (no `/3GB` boot switch or any other host configuration is required
  for this — that requirement only applies on 32-bit Windows hosts). This ceiling was used directly as the
  VirtualQueryEx scan bound in Section 7/19's VAS measurements — never inferred solely from "32-bit."

## 5. OFFICIAL ARTIFACT IDENTITY

Compiled outside SFM via the qualified public compiler (`tools/sfm_master_sidecar/publisher.check_only`,
unchanged production code):

- Source SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — **matches**.
- Artifact SHA-256: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — **matches**.
- Artifact size: 9,506,244 bytes — **matches**.

Placed only in a temporary directory under SFM's own `usermod\scripts\gate2a_temp_artifact\` for the
duration of the test; never published as a manifest, never made SFM's active Master; fully removed after
the run (Section 24).

## 6. RUNTIME MODULE IDENTITY

Byte-identical copies of the exact committed files (verified both before deployment and, from inside the
probe itself, again immediately before import):

| File | SHA-256 |
|---|---|
| `tools/sfm_master_sidecar/format.py` | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` |
| `tools/sfm_master_sidecar/reader.py` | `dd1e5da29058394c99e37f5eeaffd262c0b07421d052661ca51b06f1e11e7b02` |
| `tools/sfm_master_sidecar/__init__.py` | `8cad865fd9954035aebb3e02d5c454228e80a095595bd9cd3746df0b357f904c` |

Confirmed identical (`True`/`True`) from inside the running probe's own log:
`format.py on-disk SHA matches committed: True`; `reader.py on-disk SHA matches committed: True`. No
modified/profiling version of `reader.py` was used — the defect in Section 1 is present in this exact,
unmodified, committed file.

## 7. MEASUREMENT METHOD

- **In-SFM probe** (temporary, Python 2.7, deployed via the already-proven `usermod\scripts\sfm\autoinit\`
  mechanism, never modifying `sfm_init.py`): scheduled its actual measurement logic via
  `threading.Timer(20.0, run_probe)` — a genuinely non-blocking delay (the GUI thread is never held; the
  callback runs on its own background thread after SFM has had 20 seconds to reach its normal idle
  main-window state) — then wrote stage-marker lines (`STAGE <name> <unix-timestamp>`) to a bounded log file
  and, at each stage, called Windows `GetProcessMemoryInfo` on its own process handle (via `ctypes`,
  `psapi.dll`) to self-measure `WorkingSetSize`/`PeakWorkingSetSize`/`PagefileUsage`/`PeakPagefileUsage`/
  `PrivateUsage`. Instrumentation lives ENTIRELY inside this temporary probe file — `reader.py` itself was
  never modified or wrapped.
- **External Python 3 controller** (`gate2a_external_sampler.py`, runs on the host machine, never inside
  SFM): opened the target PID via `OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, ...)` and
  sampled `GetProcessMemoryInfo` at a **0.15s** interval continuously throughout the run, and performed a
  full `VirtualQueryEx` walk of the target's address space (0 up to the 4 GiB ceiling from Section 4) at a
  **2.0s** interval, stopping automatically 2 seconds after observing the probe's `DONE` marker file (a
  bounded 90-second maximum was also set as a hard stop). This is the authoritative peak-detection
  mechanism (Part 7) — a single before/after snapshot was never relied upon as sufficient evidence.
- Both scripts were smoke-tested first: the in-SFM probe's exact logic (with the same ctypes memory calls)
  was dry-run locally under Python 3 against a local copy of the runtime package (catching and fixing one
  real `ctypes` `argtypes`/`restype` bug — a 64-bit-vs-32-bit handle-truncation issue in the ORIGINAL draft
  of the test-only instrumentation itself, unrelated to the reader defect below, fixed before deployment);
  the external sampler was smoke-tested against an arbitrary already-running unrelated process
  (`explorer.exe`) to confirm `OpenProcess`/`VirtualQueryEx` cross-process querying worked before pointing it
  at the real target.

## 8. PEAK SAMPLING METHOD

Covered in Section 7. Sampling interval: 0.15s (memory counters), 2.0s (VAS scan). 188 memory samples and
14 VAS scans were captured over the ~29-second observed window (process start through the point measurement
stopped after the defect surfaced). Correlation with in-process stage markers used the same OS wall clock on
the same machine for both the in-SFM probe and the external sampler, so no clock-skew adjustment was
needed.

## 9. S0 IDLE BASELINE

Window `1789181082.313`–`1789181083.330` (before the runtime package was ever imported), from the external
sampler's correlated samples (n=6, stable/flat across the window):

- Private bytes: **463,384,576 bytes (≈ 441.9 MiB)**
- Working set: **420,683,776 bytes (≈ 401.2 MiB)**
- Peak working set (process-lifetime, already elevated by SFM's own startup — not isolated to our interval):
  440,365,056 bytes (≈ 420.0 MiB)

This is SFM's own baseline cost (engine, Qt/PySide GUI, asset caches) before any sidecar code runs at all —
substantial on its own, and the reference point every later delta in this document is measured against.

## 10. S1 RUNTIME IMPORT

Window `1789181083.824`–`1789181088.335` (`import format`/`import reader` only, no sidecar activity):

- Private bytes: 463,384,576 → 464,416,768 bytes — **delta ≈ +1,032,192 bytes (≈ +1.0 MiB)**.
- Working set: 420,687,872 → 421,793,792 bytes — delta ≈ +1,105,920 bytes (≈ +1.05 MiB).

Small, expected: importing two pure-Python modules (no sidecar bytes touched yet).

## 11. S2 BACKING ACQUISITION (separately observable, but NOT via `open_generation`)

**Important scope note, stated per Part 11's own instruction not to fake a decomposition:** the production
reader's `open_generation()` performs its read and its full Section 20 structural validation as one
combined, non-decomposable operation — there is no API-level checkpoint between "bytes acquired" and
"validated" that this task could measure separately for a SUCCESSFUL open. Because `open_generation` itself
failed (Section 1) before ever reaching that combined operation, this "S2" measurement is instead a
SEPARATE, test-only verification read (`open(ARTIFACT_PATH, "rb").read()` inside the probe, purely to
confirm the on-disk artifact's size/SHA-256 before attempting the real open) — explicitly labeled as such,
never presented as if it were the reader's own backing acquisition:

Window `1789181088.831`–`1789181090.585`:

- Private bytes: 464,416,768 → up to 473,939,968 bytes at peak within this window — **delta from S0 ≈
  +10,555,392 bytes (≈ +10.07 MiB)**, consistent with reading the ~9.06 MiB artifact once into a Python
  `bytes` object plus normal allocator overhead.
- This confirms the artifact CAN be read from this location without I/O error, and that a single ~9 MiB
  read costs roughly the expected order of magnitude — but this is **not** Candidate A's real retained cost,
  since the actual reader-owned decoded structure was never built (Section 1).

## 12. S3 OPEN / VALIDATION

**NOT REACHED.** `reader.SidecarReader.open_generation(ARTIFACT_PATH, SOURCE_SHA256)` raised
`AuthorityUnavailable` immediately (Section 1) — no structural validation of the real artifact ever began,
no elapsed-time figure for open+validation exists, and no resource delta for this step was captured.

## 13. S4 STEADY RETAINED PROVIDER

**NOT REACHED.** No provider was ever successfully opened; there is no steady-state to measure.

## 14. FULL-SCALE FUNCTIONAL CHECK

**NOT REACHED.** Group/occurrence iteration, the first/middle/tail HIT checks, and the deterministic
absent-fold `MasterUnknown` check were all coded into the probe (Section 7) but never executed, because
`open_generation` failed before the probe's functional-check block was ever reached.

## 15. LOOKUP PERFORMANCE OBSERVATION

**NOT REACHED.** The prepared 2,990-key stratified lookup batch (spanning the full key space of the official
Master, built and verified against the real reader under Python 3 before deployment) was never exercised
against a real open provider.

## 16. S5 POST-CLOSE

**NOT REACHED.** No provider was ever opened, so there is nothing to close, and no close/idempotent-close/
post-close-failure behavior was exercised in this run (all of that lifecycle behavior remains separately,
validly proven by Gate 1 H1 — Section 1's "why H1 did not catch this" explains precisely why THAT evidence
remains sound while THIS specific code path's evidence does not yet exist).

## 17. LOAD PEAK

**Not measurable for Candidate A's real open/decode operation** (Section 12). The only "load" that actually
occurred was the S2 verification read (Section 11): peak private-bytes delta observed during that window was
≈ +10.07 MiB above S0 — this is NOT Candidate A's load peak, only the cost of reading the raw file bytes
once for identity verification.

## 18. RETAINED COST

**Not measurable.** No provider was ever retained.

## 19. VAS / LARGEST-FREE-REGION HEADROOM

From the external sampler's 14 VAS scans across the captured window (all stable, since no large operation
ever began), reported honestly as pre-defect / pre-load headroom, not as evidence of Candidate A's own
effect on VAS:

- Committed: ≈ 794.3–795.5 MB (drifting slightly upward, consistent with ordinary SFM engine activity, not
  our test).
- Reserved: ≈ 351.9–354.0 MB.
- Free: ≈ 3.146–3.148 GB.
- **Largest free contiguous region: a stable ≈ 2,092,761,088 bytes (≈ 1.95 GiB) throughout the entire
  captured window, unchanged across all 14 scans.**

This confirms substantial VAS headroom exists in this process BEFORE Candidate A's real open was ever
attempted — a necessary but not sufficient precondition; it says nothing about what a successful Candidate A
open/decode would actually consume or fragment, which remains unmeasured (Section 12).

## 20. RESOURCE TARGET COMPARISON

**Not reached.** Comparing S0/S1/S2's partial data against the governing thresholds would be
misleading, since none of them represent Candidate A's actual retained or peak cost. Per Part 1's own
instruction to report the exact governing thresholds: the CONTROLLING specification
(`SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md` §42) does **not** state a numeric pass/fail
threshold at all — it only lists categories to measure ("actual resident/VAS cost of an open handle...",
"validation/open latency, measured...") without committing to specific MiB figures. The **provisional**
target found recorded elsewhere in this project's history
(`SFM_MASTER_SIDECAR_PHASE_A_INFRASTRUCTURE_ASSESSMENT.md`, explicitly labeled "not proven or disproven...
pending actual measurement"): **≤ ~16 MiB incremental retained/provider address-space cost, ≤ ~32 MiB
incremental load peak.** These provisional figures are reported here exactly as found, unchanged, for
whenever this measurement is actually completed — they were not evaluated against real Candidate A data in
this run because that data does not exist yet.

## 21. CANDIDATE A VERDICT

**None of Part 18's three allowed verdicts is a clean fit, and none is declared as such:**
- Not `CANDIDATE A PASSES INITIAL GATE 2 RESOURCE BASELINE` — no resource baseline for the real operation was
  ever obtained.
- Not `CANDIDATE A EXCEEDS GATE 2 RESOURCE TARGET` — there is no resource observation to have exceeded
  anything; the failure occurred at a functional level, before any resource question could even be asked.
- Closest of the three, stated precisely so it is not mistaken for an instrumentation-quality problem:
  **`INCONCLUSIVE — MEASUREMENT BLOCKED BY A GENUINE FUNCTIONAL DEFECT`** (not "measurement quality
  insufficient" — the sampling/instrumentation mechanism itself worked correctly throughout, as proven by
  the clean S0/S1/S2 data; the block is a real code defect, not a measurement-quality shortfall).

## 22. REALISTIC-SESSION LIMITATION

Not reached for the same reason as Sections 12–18 — this was, in any case, always going to be an isolated
provider baseline with no production project loaded (per Part 19's own instruction), so even a fully
successful run here would not have proven adequate headroom during a heavy real editing session. That
limitation is now moot until the defect (Section 1) is fixed and this measurement is re-attempted.

## 23. EXPLICITLY DEFERRED GATE 2 WORK

Unchanged from this task's own scope — none of the following were touched, attempted, or implied by this
run:

- Candidate B / Candidate C backing implementations.
- Generation-overlap cost during a hot-swap.
- Normalizer integration of any kind (no model traversal, vocabulary requests, animation-set work, or shot
  processing).
- Format v1 freeze.
- Any optimization of Candidate A or of `reader.py` in response to the defect found here (explicitly
  forbidden by this task's own instructions).

## 24. CLEANUP

- SFM process terminated (`taskkill /PID 18684 /F`) after the probe's log/DONE-marker were captured and the
  external sampler finished its trailing samples — this was a fresh instance launched solely for this test,
  not a pre-existing user session (SFM was confirmed not running before this task began).
- `usermod\scripts\sfm\autoinit\zz_gate2a_probe_temp.py` — removed; directory confirmed empty afterward.
- `usermod\scripts\sfm_master_sidecar_gate2a_runtime\` (temporary runtime-module copy) — removed entirely.
- `usermod\scripts\gate2a_temp_artifact\` (official sidecar copy + lookup-batch JSON) — removed entirely; no
  manifest or publisher-lock file was ever created (the artifact was opened directly by path, never through
  `publisher.publish`).
- `usermod\scripts\sfm\sfm_init.py` — confirmed byte-for-byte unchanged (re-read after cleanup).
- No new crash dump appeared in `game\` from this session.
- A directory-wide search for any remaining `*gate2a*`-named file under `usermod\` after cleanup returned
  nothing.
- SFM is **not** left open after this task (it was closed as part of cleanup, since it was a fresh instance
  launched only for this test).
- Qualification logs (probe result log, stage-marker log, external sampler CSV/JSON) were preserved outside
  both the SFM install and the repository, in this session's own scratchpad directory, for the evidence
  reproduced in Sections 9–11/19 above.

## 25. GIT / SAFETY STATE

- `sfm_defaultanimationgroups.txt`: unchanged, SHA `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`.
- `tools/sfm_master_core.py`, `tools/validate_master.py`: unchanged.
- **All production sidecar code, including `tools/sfm_master_sidecar/reader.py` (where the defect lives),
  is unchanged** — confirmed via empty `git diff` on every file. The defect was diagnosed and reported, not
  patched, per explicit task instruction.
- `tests/`: unchanged (no new test-only Gate 2A infrastructure was added to the repository — all
  instrumentation lived only in the temporary scratchpad/SFM-deployed files described above, never
  committed to the repo).
- No Normalizer code touched.
- No persistent official sidecar, manifest, or publisher-lock artifact anywhere (repository or SFM install).
- HEAD unchanged: `59be3a5c044cae29b4d1890c9fa1fdf2998a90f3`.
- Nothing staged, nothing committed.
- No agents or subagents were used.
