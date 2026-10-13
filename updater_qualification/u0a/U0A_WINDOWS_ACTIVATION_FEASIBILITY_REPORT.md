# U0A — Windows Activation Feasibility Report

**Verdict: U0A PASS (bounded).** This is experimental filesystem evidence, not production
qualification.

The activation primitives and transaction shape in Astra's Updater Blueprint Revision 2 (§C4–C12)
held under ordinary process termination, on disposable synthetic files, on one Windows 10 / NTFS
configuration:
- 256 cases PASS;
- 1 case NOT RUN: cross-user lock contention (§6);
- 0 FAIL;
- 0 INCONCLUSIVE.

> **Correction (2026-10-12, documentation only):** this grand total originally read "255 cases
> PASS". The raw verdicts in `evidence/u0a_results.json` always summed to 256 PASS, 1 NOT RUN,
> 0 FAIL (257 recorded cases), as do the per-test counts (6 + 83 + 8 + 5 + 134 + 20 = 256). No case
> was rerun; the evidence, harness and bounded PASS verdict are unchanged. Owner-approved in
> `updater_qualification/design/OWNER_DECISION_2026-10-12.md`. R2, read uncommitted during U0A, is
> now committed byte-identical at `updater_qualification/design/SFM_Character_Tools_Updater_Blueprint_R2.md`.

Power-loss durability, cross-user contention, real disk-full and every real-SFM behavior remain
unproven. They are listed in §6 and §8.

| Item | Value |
|---|---|
| Date | 2026-10-12 (final run 21:26:05–21:27:43 UTC, 98.1 s) |
| Baseline | `af4c8d6245f3850460fae78e3f108b150d2f092a` (HEAD = origin/master; tracked tree clean; the 40 pre-existing untracked files were untouched) |
| Design under test | `SFM_Character_Tools_Updater_Blueprint_R2.md`, sha256 `61cf8ed56668142132cef37806f56165d4f7371273215e5301b2f2b8200341bb` (owner-supplied; read-only; not committed) |
| Frozen R15 Blueprint | unchanged |
| Product files | no CPM, Normalizer, compiler, publisher, Master, sidecar or authority file changed or executed |

## 0. Designer gate and scope

**Gate:**
- HEAD and the tree were verified.
- I read R2 §A–C12, G and I (Stage 0) and reconciled them with the U0A assignment.
- I found no conflict. U0A is exactly R2 Stage 0's "separately authorized disposable-file Windows
  experiment". The real-SFM half of Stage 0 is U0B and was not run.

**Isolation:**
- **Test root:** a new, empty directory under the per-session temporary scratch area on `C:`. In the
  evidence it is redacted as `<U0A_ROOT>`.
- **Checks (`isolation_check`, all true before any write):**
  - the root is local, fixed and NTFS;
  - it is outside the repository and any SFM installation;
  - there are no reparse points on its path;
  - it was new or empty.
- **Fixtures:** every case built its own fake `usermod\cfg` tree, with a synthetic Master TXT,
  synthetic sidecars and a manifest.
- **The one write outside the root:** the 1g cross-volume rename attempt named a non-existent
  target. The rename was refused and no file was created.

**Production fingerprint:** these were read-only SHA-256 hashes, taken before and after the run, of:
- the live `usermod\cfg` Master;
- every file in the live `sfm_shared_authority`;
- the repository canonical Master.

There were 5 entries, and all were **unchanged**.

**SFM was running during U0A.** An unrelated `sfm.exe` (owner session) was open the whole time.
U0A never opened, signaled or wrote any SFM file or process. The prototype's advisory "SFM running"
refusal was therefore set to *record only* for synthetic runs (`sfm_policy_record_only=1`). Case 6o
ran with the refusal enforced and showed that the real process is detected and that activation is
refused with nothing changed.

## 1. Windows version and filesystem

| Item | Value |
|---|---|
| OS | Windows 10 Pro 22H2, build 10.0.19045.6466, x64 |
| Filesystem | NTFS on a local fixed disk (`C:`), with transaction storage on the same volume (R2 C1) |
| Runtime | CPython 3.10.6 64-bit, `ctypes` → kernel32 (no third-party modules) |
| Token | interactive user, member of Administrators, running **non-elevated** (medium integrity; UAC-filtered token) |
| `LongPathsEnabled` | 1. The longest test path was 395 characters (see finding F7). |
| Other volume used | `E:` (NTFS), only as the 1g cross-volume target |

## 2. Implementation and reproduction

These are owned experiment artifacts. None is a production updater.

| File | sha256 | Role |
|---|---|---|
| `harness/w32.py` | `c7c21a5f…d5a8` | Win32 bindings. Every call is traced with access mask, share mode, disposition, flags and `GetLastError`. |
| `harness/proto.py` | `50ca7fcc…1aa3` | R2 C2–C12 prototype: synthetic compiler, intent, journal, activation, recovery. Runs one process per operation, with named barriers. |
| `harness/racer.py` | `c74c32ad…dd96` | Adversary in a separate process: in-place writer, Python editor, `ReplaceFileW` and `MoveFileExW(REPLACE_EXISTING)` editors, delete, rename, destination create, holders, lock contender. |
| `harness/run_u0a.py` | `90e97770…3102` | Controller: isolation, fixtures, deterministic barriers, `TerminateProcess` kills, independent verification, verdicts. |

**Reproduce** (no network, no elevation, SFM not required):

```
set U0A_PROD_WATCH=<live Master>;<live sfm_shared_authority>;<repo Master>   (optional, read-only)
python -B updater_qualification\u0a\harness\run_u0a.py <NEW_EMPTY_NTFS_DIR>\root <DIR>\evidence
```

**Determinism:** `proto.py` stops at a named barrier, prints `BARRIER <name>` and blocks on stdin.
At that point the controller does one of three things:
- runs an adversary process and then resumes the prototype;
- kills the prototype with `TerminateProcess` (exit code 1 every time);
- resumes it.

Nothing depends on timing.

**Evidence:** `evidence/u0a_results.json` holds every case with its scenario, before/after
inventories, SHA-256 hashes, physical identities (`<VOL>:<FileId128>`), Win32 traces, outcomes and
verdicts. `evidence/u0a_runs.zip` holds the 378 per-process prototype results with full traces.
`evidence/u0a_console.txt` is the console log.

Redactions: `<U0A_ROOT>` (including the `<U0A_ROOT_8DOT3>` and
`\\localhost\C$<U0A_ROOT_WITHOUT_DRIVE>` alias forms), `<USERPROFILE>`, `<USER>`, `<HOST>`, and
`<VOL>` (volume serial). Identity equality is preserved. A leak scan of all three files found 0
hits.

| Evidence file | sha256 |
|---|---|
| `evidence/u0a_results.json` | `c94d8789b415c5e1c0e9f2a75bf1038aa42a6db8c9770083b8495938b664706b` |
| `evidence/u0a_runs.zip` | `46bb9a297d5d8b5984bc4b69e993e7e4824680d9cd2a003e8e6eeed71e0838b3` |
| `evidence/u0a_console.txt` | `1c83c321ea1f2ddf2e630595822450bd02db56f08a28f6b02e9432d98585e367` |

### Prototype contract (R2 mapping)

**Lock (C4):**
- `CreateFileW(installation.lock, GENERIC_READ|GENERIC_WRITE, share 0, OPEN_ALWAYS)`;
- non-inheritable (verified with `GetHandleInformation`);
- ownership is the live handle.

**Preparation (C7 1–9), in order:**
1. Compile (synthetic; source-bound) and validate.
2. Preview with full-sharing path readers: hashes, FileIds, hard-link counts and the authority
   inventory. Unfamiliar authority content is refused.
3. Bind consent to the observed `M0` hash.
4. Create `transactions\<id>\{candidate,snapshot,retired}`.
5. Write `intent.json` and the journal.
6. Write candidates with `CREATE_NEW` → write → `FlushFileBuffers` → verify through the handle.
7. Make verified snapshot copies.
8. Take the lock and refuse if other transactions are not terminal.
9. Protect:
   - the retained Master: `GENERIC_READ`, share 0;
   - every file that moves: `GENERIC_READ|DELETE`, share 0;
   - directory pins: `FILE_READ_ATTRIBUTES`, `FILE_FLAG_BACKUP_SEMANTICS`, share READ|WRITE (no
     DELETE).
10. Revalidate bytes, FileIds and link counts **through the held handles**.
11. Recheck the inventory.

**Transitions (C8):**
- Each step is journaled: `BEGIN i` → `SetFileInformationByHandle(FileRenameInfo, ReplaceIfExists=FALSE)`
  → check the final path with `GetFinalPathNameByHandleW` → `DONE i`.
- Every journal record is checksummed, sequence-numbered and flushed.
- Plans:
  - rebuild: `S0→retired`, `P0→retired`, `S1→auth`, `P1→auth`;
  - replacement: adds `M0→retired` and `M1→Master` after `P0`.
- `M0 == M1` keeps the Master in place under a read-only exclusive handle (4a).

**Completion:**
- `VERIFIED` is written only after:
  - all moved files are re-hashed and re-located through their handles;
  - the retained Master is re-hashed;
  - the authority directory listing is exactly `{S1, manifest.json}`.
- The manifest rename alone is never trusted.
- Then `COMPLETE`, and the handles are closed.

**Forward failure:** the same primitive runs in reverse inside the same transaction (journaled
`DIR rollback`).

**Recovery (C12):**
- Paths come only from fixed layout rules and validated names. Journal paths are never used.
- The disk is compared with the expected state `E_k` for every `k` in `0..n`. A state is accepted
  only if exactly one `k` matches by hash.
- The journal must agree, within at most one unacknowledged move.
- Recovery re-protects, journals `RECONCILED k`, then continues in the recorded direction (or a
  requested rollback) and re-verifies the full set.
- Terminal transactions are verified read-only.
- Malformed or unknown-schema records cause no mutation.
- A torn final record is preserved and acknowledged, never trusted.

## 3. Per-test results

| Test | Cases | Result |
|---|---|---|
| U0A-1 protected file operations | 6 | 6 PASS |
| U0A-2 source-mutation races and destination occupation | 83 | 83 PASS |
| U0A-3 installation lock | 9 | 8 PASS, 1 NOT RUN (cross-user) |
| U0A-4 synthetic activation sequence | 5 | 5 PASS |
| U0A-5 interrupted activation and recovery | 134 | 134 PASS |
| U0A-6 failure cases | 20 | 20 PASS |

### U0A-1 (exact Win32 outcomes)

**1a/1b:** the file was opened with `GENERIC_READ|DELETE`, share 0, non-inheritable.

Every other-process access was refused:

| Other-process access | Result |
|---|---|
| full-share read | `ERROR_SHARING_VIOLATION(32)` |
| in-place write | `ERROR_SHARING_VIOLATION(32)` |
| `DeleteFileW` | `ERROR_SHARING_VIOLATION(32)` |
| `MoveFileExW` rename | `ERROR_SHARING_VIOLATION(32)` |
| `ReplaceFileW` | `ERROR_SHARING_VIOLATION(32)` |
| `MoveFileExW(REPLACE_EXISTING)` | `ERROR_ACCESS_DENIED(5)` |

The own-handle rename into a vacant destination in another directory **succeeded** while the
handle was retained:
- the final path through the handle is the new location;
- the hash through the handle is unchanged;
- the FileId is unchanged before and after;
- a reopen while the handle is held gives 32;
- after `CloseHandle`, a reopen and hash match, with the same FileId;
- the old name is gone.

**Other U0A-1 cases:**

| Case | Result |
|---|---|
| 1c: destination exists | `ERROR_ALREADY_EXISTS(183)`. The occupant and source are byte-identical and identity-identical. |
| 1d: no `DELETE` access | rename gives `ERROR_ACCESS_DENIED(5)`. `DELETE` is necessary. |
| 1e: retained protection (`GENERIC_READ`, share 0) | read, write, delete, rename and `ReplaceFileW` give 32; `MoveFileExW(REPLACE_EXISTING)` gives 5. |
| 1f: a directory occupies the destination name | 183 |
| 1g: cross-volume own-handle rename | `ERROR_NOT_SAME_DEVICE(17)`; the target was not created; there is no copy fallback. |

### U0A-2

**Master races:** 60 cases, covering both kinds × 5 phases × 6 actors.
- **Actors:** in-place write; Python `r+b` editor; `ReplaceFileW` temp-file editor;
  `MoveFileExW(REPLACE_EXISTING)` editor; delete; rename.
- **Before protection** (before preview, after preview, before protection) — 36 cases:
  - the racer wins;
  - the updater refuses before any active file moves, through one of: consent binding, snapshot
    hash mismatch, a missing source, or revalidation through the held handle;
  - the racer's bytes survive;
  - nothing is lost.
- **During protection** — 12 cases:
  - every racer is refused (32, or 5 for replace-style saves);
  - activation completes;
  - nothing is lost.
- **After release** — 12 cases:
  - activation completed and was verified first;
  - the user's later edit stands untouched.

**Sidecar races:** 8 cases.
- **Before protection:** refusal.
- **During protection:** the racer is refused.
- In one case a refused `ReplaceFileW` editor left its temp file inside the authority directory.
  The inventory recheck then stopped the activation before any move (finding F3).

**Destination occupied immediately before each move:** 10 moves across both plans.
- Every rename refused with 183.
- Rollback restored the verified old state when the occupant did not sit in an original's home
  slot. This held for the S0, P0 and M0 positions.
- Otherwise the result was an explicit CONFLICT with every byte preserved, for occupants at the
  `S1`, `P1` and `M1` destinations.
- A second recovery never overwrote the occupant.
- **The `M1` case:** a file created in the vacant Master path during replacement is the R2
  "no-clobber" blocker. The occupant was kept, `M0` stayed in `retired`, and the result was
  CONFLICT. No overwrite occurred.

### U0A-3

| Case | Result |
|---|---|
| 3a | Two processes: the second gets 32. |
| 3b | The holder was `TerminateProcess`-killed (exit 1). The lock file persists. A new process reacquires it (`created=False`). |
| 3c | Activation while the lock is held: ABANDONED, nothing changed. |
| 3d | Renaming the lock's directory while the lock is held gives 5. |
| 3e | A stale pre-existing lock file is acquired normally. Existence ≠ ownership. |
| 3f | Eight aliases, all at the same FileId, all refused with 32 while held: junction, case variant, `\\?\` prefix, `..` segments, 8.3 short name, hard link, `subst` drive, and `\\localhost\C$` loopback UNC. |
| 3g | A lock file that denies write gives 5. No substitute lock is created. |
| 3h | A directory that denies file creation gives 5. No lock file is created. |
| 3i | Cross-user: **NOT RUN**. There were no credentials for a second account and no elevation. |

### U0A-4

| Case | Result |
|---|---|
| 4a: rebuild with the TXT unchanged | COMPLETE. The Master bytes and FileId are unchanged; the old sidecar and manifest are in `retired`; the candidate directory is empty. Independent recomputation (synthetic compile of the active TXT) matches exactly `{S1, manifest.json}`. A repeat recovery is verify-only and changes nothing. |
| 4b: replacement TXT | COMPLETE. `M1` is active; `M0`, `S0` and `P0` are retired. The external import file is unmodified. |
| 4c | Verified no-op. Only the lock file was created. |
| 4d | Two historical sidecars and no manifest: both retired, exactly one active artifact. |
| 4e | Activation addressed through a junction alias of the installation resolves to the physical target and completes. |

### U0A-5

**Kill grid:**
- Every barrier from `candidates_written` to `released` was tested:
  - 19 barriers for rebuild;
  - 25 for replacement;
  - each under both resume and rollback recovery policies;
  - 88 kills in all.
- **Results:**
  - killed before protection → ABANDONED, old state verified;
  - killed after `BEGIN i`, after the rename but before `DONE i`, or after `DONE i` →
    - resume gives COMPLETE (new state verified);
    - rollback gives ROLLED_BACK (old state verified);
  - killed after `COMPLETE` → terminal; read-only verification is true.
- Every second recovery changed nothing (full inventory equality).

**Kill during recovery:** 34 cases. Recovery was itself killed at every recovery barrier, in both
directions, from a mid-transaction crash. Every case ended in a verified old or new state, and the
next recovery was idempotent.

**Post-crash cases:**
- the TXT was edited (rebuild) or created in the vacant Master path (replacement) → CONFLICT,
  "Your TXT changed…", and the newer bytes were retained;
- a retired original went missing → CONFLICT, "Automatic recovery is unavailable; required files are
  missing." There was no restore claim and nothing changed;
- a candidate was corrupted → CONFLICT, nothing changed;
- the journal claimed `DONE` for a move the disk did not show → CONFLICT ("journal and disk
  disagree"). There was no journal-only recovery.

**Activation rollback killed mid-way:** recovery refused while an unfamiliar occupant remained. After
the occupant was set aside, recovery finished the recorded rollback, and the old state was verified.

### U0A-6

| Case | Result |
|---|---|
| 6a: `DELETE` denied (file DE + directory DC ACEs) | protection gives 5 → ABANDONED before any move |
| 6b: file creation denied in the authority directory mid-transaction | forward 5. The rollback was also blocked (5) → CONFLICT, nothing lost. After the ACL was restored, recovery gave ROLLED_BACK, verified. |
| 6c | A Normalizer-style holder (`GENERIC_READ`, share READ) on the Master gives 32 → ABANDONED. |
| 6d | A full-sharing reader on a sidecar gives 32 → ABANDONED. |
| 6e / 6f | The old sidecar or the candidate disappeared before protection: `ERROR_FILE_NOT_FOUND(2)` → ABANDONED. |
| 6g | `ERROR_DISK_FULL(112)` on the candidate write → ABANDONED. **This was a simulated injection.** |
| 6h | A pre-existing `publisher.lock` in the authority directory → REFUSED as unfamiliar (finding F4). |
| 6i | A stranger sidecar created during the transaction (directory pins do not block new children) → final verification CONFLICT, no deletion, never success. |
| 6j | A flipped journal record, unknown intent schema or unknown journal schema → CONFLICT, "Use a compatible updater…", no data mutation. A traversal name in the intent is rejected. A constructed torn tail is preserved and acknowledged, then recovery completes after disk verification. |
| 6k | The Master was replaced by identical bytes with a new FileId before protection → identity mismatch → ABANDONED. |
| 6l | The authority directory was swapped for a copy → FileId and directory-identity mismatch → ABANDONED. |
| 6m | A hard-linked Master (2 links) → REFUSED. |
| 6n | The authority directory is a junction → REFUSED (reparse point inside the managed slots). |
| 6o | Advisory check with the real `sfm.exe` running → ABANDONED, nothing changed. |

## 4. Transition and recovery matrix (observed)

| Interruption point (process termination) | Active state found | Recovery (resume / rollback) | Second recovery |
|---|---|---|---|
| Before protection (candidates, snapshots, lock) | Original | ABANDONED, "Nothing was installed." | no change |
| Protected, no moves | Original | ABANDONED | no change |
| After `BEGIN i`, before rename | `E_i` | COMPLETE / ROLLED_BACK, verified | no change |
| After rename `i`, before `DONE i` | `E_(i+1)` (journal one behind) | COMPLETE / ROLLED_BACK, verified | no change |
| After `DONE i` | `E_(i+1)` | COMPLETE / ROLLED_BACK, verified | no change |
| Replacement: after `M0` retired, before `M1` | Master absent, no active sidecar | COMPLETE / ROLLED_BACK, verified | no change |
| All moves done, before `VERIFIED` | Full candidate set | COMPLETE ("Installation recovered.") / ROLLED_BACK | no change |
| After `COMPLETE` | Candidate set | terminal; read-only verify = true | no change |
| During recovery (any recovery barrier, either direction) | an `E_k` | verified old or new | no change |
| During activation rollback, occupant in active slot | mixed + occupant | CONFLICT (preserved); after the operator sets it aside, ROLLED_BACK | no change |
| TXT edited or created after crash | unexpected TXT | CONFLICT, "Your TXT changed…" | no change |
| Recovery component missing or corrupt | incomplete | CONFLICT, no restore claim | no change |
| Journal ahead of disk / malformed / unknown schema | any | CONFLICT, no mutation | no change |

No case produced lost bytes, an overwrite, success reported for an inconsistent set, a journal-only
recovery or a manifest-only restore.

## 5. Confirmed safety properties

These hold under process termination on this configuration:
1. A protected file (`GENERIC_READ[|DELETE]`, share 0) cannot be written, deleted, renamed or
   replaced by ordinary or editor-style saves from another process. Such attempts fail with 32 or
   5, and no bytes are lost.
2. The own-handle `FileRenameInfo` move with `ReplaceIfExists=FALSE`:
   - works while the protective handle is retained;
   - preserves the FileId;
   - refuses an occupied destination (file or directory) with 183, leaving both untouched;
   - refuses a cross-volume move (17) with no copy;
   - requires `DELETE` (5 without it).
3. Byte and identity revalidation through held handles detects every pre-protection mutation:
   in-place edits, atomic-save replacement, identical-bytes replacement and directory swap.
4. The installation lock gives one live owner per physical file across 8 path aliases. It is freed
   by process death, is independent of the lock file's existence, is non-inheritable, never
   produces a substitute on access denial, and keeps its directory from being renamed.
5. The transaction ends in exactly the intended `{TXT, one sidecar, manifest}`. This is established
   by independent recomputation, not by the manifest rename. Unexpected content prevents success
   and is never deleted.
6. Every kill point recovers to a verified old or new state, or to a preserved conflict.
   Recovery is idempotent, survives its own interruption in both directions, never trusts journal
   paths, and never reports success without full-set verification.

## 6. Failed or unproven properties

**No property failed.** Development defects in the prototype were found and fixed before the final
run. They are listed here for the record (they are prototype issues, not primitive failures):
- Recovery did not journal the disk state it had verified. A recovery killed right after its first
  `BEGIN` therefore made the next recovery report a needless CONFLICT. This was safe and nothing
  was lost. Fixed with a `RECONCILED k` record.
- Reparse points inside the managed slots and installation aliases were not handled up front. The
  move layer caught the mismatch only after moving files, and the result was a preserved CONFLICT.
  Fixed with up-front alias resolution (C1) and an explicit reparse refusal.

**Unproven (U0A could not establish these):**
- **Power or cache loss** (C10). No hard-reset campaign was run. `FlushFileBuffers` was used, but
  durability of the directory entries and device cache is not shown. Process-termination evidence
  is not power-loss evidence.
- **Cross-user lock contention** (3i, NOT RUN). The lock is a kernel share-mode property of the
  file object, not a SID-named object. That is the R2 correction to the per-user mutex. It still
  needs a real second account.
- **Standard (non-admin) user token:** only a filtered admin token was used.
- **Real disk-full and short writes.** 6g was simulated. The safe-space conditions for a real test
  were not available without elevation (VHD).
- **Antivirus or indexer interference** with renames. None was observed, but none was controlled.
- **Kill inside a kernel call.** Kills occur at user-mode barriers between Win32 calls. The atomicity
  of a single rename under termination is assumed from NTFS semantics, not separately proven.
- **Torn journal record.** It was constructed (truncated file), not produced by an interrupted
  write.
- **Other Windows versions or builds, other filesystems, network or removable media:** not tested.
  C1 limits support to local NTFS.
- **All real-SFM interaction** (U0B).

## 7. Is Astra R2 still viable?

**Yes, at the Windows filesystem-primitive level.** The C6 primitive set, the C7 protection order,
the C8 transition sequence and the C12 recovery matrix are implementable as specified and held
every tested invariant. No weaker overwrite, locking or recovery behavior was substituted.

**Findings that refine R2** (they belong to L design; none is a blocker):
- **F1:** the moving handle needs `DELETE`. A retained file needs only `GENERIC_READ`, share 0.
  Replace-style saves fail with 5 rather than 32.
- **F2:** recovery must journal the disk state it verified (`RECONCILED k`) before acting.
  Otherwise an interrupted recovery leaves the journal unable to vouch for the state it reached.
- **F3:** a refused editor save (for example `ReplaceFileW`) can leave a temp file in the managed
  directory. R2's "refuse unfamiliar content" then refuses activation. This is safe, but the user
  messaging should anticipate it.
- **F4:** the live `sfm_shared_authority` currently contains `publisher.lock` (observed read-only).
  Under R2's one-active-artifact and unfamiliar-content rules, the first activation on today's live
  layout would refuse unless L defines a recognized-file migration.
- **F5:** directory pins block rename and delete of the directory, but not new children (6i). The
  final exact-inventory verification is therefore essential, not optional.
- **F6:** an occupant appearing in an original's home slot (for example the vacant Master path
  during `M0→M1`) leads to a preserved CONFLICT with authority unavailable (fail-closed), not to
  automatic restoration. This is acceptable under R2 C12/J4, but the owner should confirm it.
- **F7:** transaction paths are long:
  `cfg\sfm_character_tools_updater\transactions\<32>\retired\sfm_master_<fmt>_<64>.sfmsidecar`
  adds about 172 characters to the `cfg` path. The tests reached 395 characters, which works only
  with long-path support. Legacy tools (`icacls`) failed past 260. L needs a path-length budget or
  `\\?\` handling and a test at the real installation depth.
- **F8:** C1's reparse refusal and alias resolution must be explicit preflight steps. Discovering
  them through post-move final-path checks is too late.
- **F9:** the prototype refuses a UNC-resolved installation. However, a loopback-UNC alias of a local
  installation does reach the same file (3f). The support boundary should state how that is
  treated.

## 8. Questions for U0B (real SFM; not run)

1. When the Normalizer's protection (`native_master_protect_acquire`, read handle denying
   write/delete) is held during native Rebuild, does the updater's protection fail cleanly with 32
   at every point? And what do the Normalizer and SFM do when the updater holds protection first?
2. Which sharing modes do SFM itself (startup, native Rebuild, any menu path) and CPM's
   operation-time authorization use for the Master and sidecar? Is any of them blocked by, or does
   any of them block, the updater, and does SFM behave safely when refused?
3. How do SFM, the Normalizer and CPM behave if launched at each post-crash state? In particular:
   Master absent (replacement window), sidecar absent, manifest absent, and the candidate valid but
   the manifest missing (R2 C8 rows).
4. Does a CPM detached scope retained across an activation stay coherent, with a refusal or a
   rebuild and no mixed generation?
5. How should `publisher.lock` in the live authority directory be disposed of (F4)?
6. What is the real installation path depth, and does the transaction path fit (F7)?
7. Is there Defender or indexer interference with renames inside the game's `usermod\cfg`?
8. Cross-user and standard-user lock contention (3i), if a second account can be provided safely.
9. A hard-reset or power-loss campaign (R2 C10/G, "required qualification") — probably a separate VM
   activity, not U0B.

## 9. Verdict

**U0A — PASS (bounded).** Every required U0A-1…6 property passed under process termination on
Windows 10 22H2 / NTFS with disposable synthetic files. Cross-user contention could not safely be
run, and the unproven items in §6 remain. Astra R2's activation mechanism remains viable.

This is experimental feasibility evidence only. It is not production qualification: no updater,
GUI, packaging or release client exists, and nothing was installed. **K remains COMPLETE / PASS.
L remains NOT STARTED. U0B was not started.**
