# R3-B2E1 — Abandoned-Mutex Qualification Report

Date: 2026-09-15. Narrow diagnostic/qualification task. No SFM launched.
No Master modification. No consumer modification. No R1D/final-R3-A2B
modification. No B2C/B2D/B2F implementation.

## 1. Prior B2E identities — re-verified before this task

| File | SHA-256 |
|---|---|
| R1D validator | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` |
| R1D provider | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| Final R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| Final R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Production G18AD Character Preset | `7e8036c4b8fcfe8477fbd719ad7c2e94ba710d9780b5df9fa5161ec9c093875c` |
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| `win_named_mutex.py` (before) | `ae9c1b8663a1c0c922ef0596b682fc05399840db7441d31aeea30d1bba83f1c5` |
| `mutex_publisher.py` (before) | `9d83639bc0ea82704b9ddc5b5955c960e01bbe256a329528d69ad1f5bf7364ca` |
| `generated_root.py` | `cb379a17f83f915ce2aa1e87c88134caace5019faddcecacc9e610f865890a67` (unchanged) |

All pre-existing `compiler.py`/`writer.py`/`reader.py`/`format.py`/
`publisher.py`/`manifest.py` confirmed unchanged, same SHAs as the R3-B2E
report.

## 2. Low-level abandoned-mutex probe + SHA

Two exported files (bypassing the B2E publisher abstraction entirely,
using exact Win32 named-mutex primitives via `ctypes`, per the prompt's
own required design):
- `b2e1_abandoned_mutex_child.py` — `c722366d00cc84aaa28384fdac64000280ded39807d35672a0c862205f29737e`
- `b2e1_abandoned_mutex_parent_probe.py` (v1, harness-race-bug found and
  fixed mid-task — see Section 3) — `02643c84ade252058bfd4dad63c392d014e64b258bdcbbc6332cc625a5ad00cf`
- `b2e1_abandoned_mutex_parent_probe_v2.py` (the version that isolates
  and proves the actual root cause) — `05a9dcd8580d4d66422b2472e2456d70a5a1f16e233d385c1516f2156fd19681`

## 3. Exact `os._exit` result

**v1 harness** (no persistent handle held elsewhere): parent
`WaitForSingleObject` on a *fresh* `CreateMutexW` call after the child's
`os._exit(66)` returned **`WAIT_OBJECT_0`** (0), not abandoned —
`already_existed_at_create2: false` proved the kernel object had been
destroyed and recreated, not merely reopened.

**v2 harness** (parent pre-opens and holds its own handle to the mutex,
created *before* the child even starts, never closed until after the
final wait): parent `WaitForSingleObject` on that SAME, already-open
handle returned **`WAIT_ABANDONED` (128)**, deterministically, on the
first attempt. Child log confirms `GetLastError_after_create: 183`
(`ERROR_ALREADY_EXISTS`) — the child correctly opened the parent's
pre-existing object rather than creating a new one.

## 4. Exact `TerminateProcess` result

Identical pattern: **v1** → `WAIT_OBJECT_0` (fresh object, not abandoned).
**v2** (parent's own handle held throughout, child killed externally via
real `OpenProcess(PROCESS_TERMINATE)` + `TerminateProcess`, never
Python's own `.kill()`/`.terminate()` wrapper) → **`WAIT_ABANDONED`
(128)**, deterministically.

Both death methods reproduce the exact required Windows result once the
correct condition (a persisting handle) is met — the discrepancy was
never about *how* the process died (`os._exit` vs. `TerminateProcess`),
only about *whether anything else held the kernel object open* at that
moment.

## 5. Proof both processes address the same kernel object

- Exact mutex name logged identically in parent and child (`Global\...`
  namespace confirmed in every trial).
- `CreateMutexW`'s own `GetLastError()` distinguishes "created new"
  (0) from "opened existing" (183, `ERROR_ALREADY_EXISTS`) — captured at
  every call site; the v2 child's log shows 183 (opened the parent's
  object), the v1 recovery call showed 0 (created a new object) —
  positive, mechanical proof of *which* case occurred each time, not an
  inference.
- Ownership was confirmed actually held at termination via the child's
  own real `WaitForSingleObject` call returning `WAIT_OBJECT_0` *before*
  it ever signals the parent's synchronization Event — the parent never
  proceeds until this positive confirmation.
- The child never calls `ReleaseMutex` on any code path leading to either
  death mode (confirmed by direct source inspection of
  `b2e1_abandoned_mutex_child.py`/`b2e1_real_wrapper_child.py`).
- No security/session/DACL issue was observed on this host in any trial
  (every `CreateMutexW`/`WaitForSingleObject`/`TerminateProcess` call
  succeeded; the only non-zero `GetLastError` values seen were the
  expected/informational `183` codes, never an access-denied class error).

## 6. Root cause of the prior non-trigger

**Classification: kernel-object lifetime, not a race/order bug in the
mutex-handling *logic*, but a race/order gap in the *test harness's*
handle lifetime — closest to "race/order bug" on the prompt's own list,
with the precise mechanism being:**

A Windows named mutex is a reference-counted kernel object. If the
crashing process holds the *only* open handle to it, the object is
destroyed the instant that process terminates (handle count reaches
zero) — there is no longer any object left for a later
`WaitForSingleObject` to observe an abandoned transition on; a subsequent
`CreateMutexW` with the identical name simply creates a **brand-new**
object. The prior `test_b2e_concurrency.py` crash test (`concurrent.11`)
used a **fully sequential** pattern — the crashing worker process
completely exits, *then* a second, separate process is started afterward
— during which **no process anywhere held an open handle** to that named
mutex. This is a real gap in that test's *design* (not its assertions,
which never over-claimed — its own comments already say "whether via a
clean re-acquire or via real WAIT_ABANDONED — both are handled"), not a
defect in `win_named_mutex.py`'s acquire/wait logic, which — once a
persisting handle exists — reports the transition correctly (Section 7).

Explicitly ruled out with direct evidence: harness never owned the mutex
(disproved — `wait_result: 0` in every child log); wrapper released
before death (disproved — no `ReleaseMutex` call exists on the crash
path, confirmed by source read); different named mutex / namespace
mismatch (disproved — identical logged name in both processes every
trial); wait result observed incorrectly (disproved — the SAME
observation code, unchanged between v1/v2, correctly reported
`WAIT_ABANDONED` the instant the real precondition was met);
security/session issue (disproved — zero access-denied results in any
trial).

**No change to `win_named_mutex.py`'s acquire()/wait logic was needed or
made** — only its docstring was corrected (a stale "unresolved
observation" note, now resolved; see Section 9).

## 7. Production wrapper abandoned-acquisition result

`test_b2e1_real_wrapper_abandoned.py` (**8/8 PASS**): a real child process
acquires through `win_named_mutex.WindowsNamedMutex` (the actual
production class, not raw ctypes) and dies via `os._exit()` without
releasing, while the parent holds its own persisting handle throughout.
A **separate** `WindowsNamedMutex` instance in the parent then reports
`outcome.kind == OUTCOME_ACQUIRED_ABANDONED` — genuinely, not mocked.
`release()` completes cleanly; a third, fresh `WindowsNamedMutex` instance
immediately afterward reports plain `OUTCOME_ACQUIRED` (proving release
actually worked, not merely didn't crash).

## 8. Reconciliation test results

`test_b2e1_real_abandoned_reconciliation.py` (**17/17 PASS**), all through
real `mutex_publisher.publish()` calls with a genuinely real (never
mocked) abandoned mutex, using isolated temporary generated-root/pointer
fixtures only:

1. **Primary valid / backup valid** — reconciliation reports both valid;
   publish completes normally.
2. **Primary corrupt / backup valid** — reconciliation correctly detects
   the corrupt primary; publish still completes (a fresh, independently-
   validated commit is about to replace it regardless).
3. **Primary references a missing artifact / backup valid** —
   reconciliation correctly detects this via the existing artifact-digest
   cross-check; publish still completes.
4. **Both pointers unusable → explicit failure** — a genuine gap was
   found here (Section 9) and fixed: `publish()` now raises
   `AbandonedStateUnrecoverableError` when real prior-state evidence
   exists (a primary and/or backup file is actually present) but *none*
   of it is trustworthy — refusing to silently commit a fresh pointer
   over an unrecoverable prior state.
5. **Already-published immutable artifact present after a pre-pointer
   crash** — confirmed directly: the compiled generation file is written
   to its final, content-addressed name *before* the mutex is even
   acquired, so a crash injected immediately before the pointer-commit
   step leaves it on disk as a correctly-named, byte-exact orphan (no
   automatic GC); a later successful publish attempt correctly *reuses*
   it (`result.reused == True`) rather than recompiling/duplicating it.

## 9. Code changes + SHAs

**`tools/sfm_master_sidecar/mutex_publisher.py`** (genuine production
gap found, not a test-only issue): the existing
`_reconcile_after_abandoned()` computed `primary_valid`/`backup_valid`
but never actually gated anything on the result — "both pointers
unusable" could previously fall through to a normal fresh commit. Added:
`AbandonedStateUnrecoverableError`; `_reconcile_after_abandoned()` now
additionally reports `primary_exists`/`backup_exists` (distinguishing
"never existed" — a legitimate first-ever publish, safe to proceed — from
"existed but is untrustworthy"); `publish()` now raises when real prior
state exists and both copies are simultaneously unusable. Verified this
distinction directly: an initial version that gated on validity alone
incorrectly broke the pre-existing `abandoned.3/4/5` tests (a fresh,
first-time output directory correctly has neither file yet) — caught by
re-running the existing suite immediately after the change, and
corrected before proceeding.
New SHA: `43d4819c3103154984b8adf26152d2c70190b91ae1ae63252c435e09d55ac6c8`
(was `9d83639bc0ea82704b9ddc5b5955c960e01bbe256a329528d69ad1f5bf7364ca`).

**`tools/sfm_master_sidecar/win_named_mutex.py`** (docstring only, no
logic change): replaced the now-resolved "unresolved empirical
observation" note with the root-cause explanation and the real
qualification result from this task.
New SHA: `61865de9e7b723996aca3043d876b940a19416837d106bf9d89f65448b7b64be`
(was `ae9c1b8663a1c0c922ef0596b682fc05399840db7441d31aeea30d1bba83f1c5`).

**`tests/sidecar/qualification/test_b2e.py`** (one assertion updated to
match the `mutex_publisher.py` change — the reconciliation dict
legitimately gained two new keys): new SHA
`c27edcea9ae483a8343961fa41dedee56c1f3eaefbc8a5f756014b522d96c04e`.

**New files** (all exported to `tests/sidecar/qualification/`):
`b2e1_abandoned_mutex_child.py`, `b2e1_abandoned_mutex_parent_probe.py`,
`b2e1_abandoned_mutex_parent_probe_v2.py`, `b2e1_real_wrapper_child.py`,
`test_b2e1_real_wrapper_abandoned.py`,
`test_b2e1_real_abandoned_reconciliation.py` — SHAs in Sections 2/7/8
above.

## 10. Regression results

After the `mutex_publisher.py` fix and the `test_b2e.py` assertion
update, re-ran everything:

- Pre-existing compiler/publisher regression suite: **60 passed, 26
  subtests passed** (unchanged).
- Full B2E suite (`test_b2e.py`): **53/53 PASS** (unchanged pass count;
  `abandoned.2`'s assertion updated to match the legitimately-extended
  dict shape, still passing).
- Full B2E concurrency suite (`test_b2e_concurrency.py`): **13/13 PASS**
  (unchanged — this suite was not modified; its own crash-recovery
  scenario remains valid for what it actually claims to prove: liveness/
  no-hang/no-corruption after a crash, never a claim about which specific
  Win32 wait code the OS reports).
- New: `test_b2e1_real_wrapper_abandoned.py` **8/8 PASS**;
  `test_b2e1_real_abandoned_reconciliation.py` **17/17 PASS**.

Zero regressions anywhere.

## 11. Hard-stop identities — unchanged, re-verified after this task

R1D validator/provider, final R3-A2B validator/provider, production
Normalizer, production Character Preset, canonical Master, and every
pre-existing `compiler.py`/`writer.py`/`reader.py`/`format.py`/
`publisher.py`/`manifest.py`/`generated_root.py` file: all byte-identical
to their values before this task began (table in Section 1, re-confirmed
identical after). Nothing committed to git. No SFM launched at any point.

## 12. Verdict

**`B2E PASS — WAIT_ABANDONED EMPIRICALLY QUALIFIED`**

The one open item from the prior R3-B2E report is closed with direct,
reproducible, real evidence: `WAIT_ABANDONED` is real, correctly
implemented, and now empirically demonstrated end-to-end through the
actual production `win_named_mutex`/`mutex_publisher` code (never
mocked), via both required death methods, with all required
reconciliation scenarios proven — including one genuine production gap
found and fixed (the missing "both pointers unusable" gate) as a direct
result of this qualification work, per the prompt's own "fix only the
test/harness unless production code is genuinely wrong" instruction.

Per the hard stop: no Master/consumer/R1D/final-R3-A2B modification, no
B2C/B2D/B2F implementation, no custom-runtime enablement, no SFM launch.
Not authorizing B2F myself — recommendation only, for the operator to
decide.
