# R3-B2E — Rebuild / Immutable Publication / Pointer Recovery — Implementation Report

Date: 2026-09-15. Implementation (B2E scope only). No SFM launched by
this task. No R1D modification. No modification of the final R3-A2B
candidate. No modification of production Normalizer or Character Preset.
No Master modification. No B2C/B2D/B2F implementation. No automatic GC.

## Critical scoping finding, made before writing any code

Before implementing, I searched for whether a real compiler for the
packed sidecar format already existed, since B2E requires "the same
authoritative compiler implementation used for official builds." **One
already exists and is real, tested production tooling from an earlier
phase-numbering lineage** (`tools/sfm_master_sidecar/{compiler,writer,
manifest,publisher}.py`, "Phase B2B–B2E" in that OLDER scheme — a
coincidental letter collision with this task's own "R3-B2E" name, not
the same lineage). Verified before use:

- `compiler.py`'s own docstring: *"This is THE ONE path used by official
  builds, custom advanced-user builds, the CLI, and every test in this
  project — there is no separate official/custom/maintainer compiler."*
- `writer.compile_sidecar(source_bytes, result)` — pure in-memory,
  returns `bytes`, no disk I/O.
- `compiler.verify_semantic_parity()` already implements an exhaustive
  (never sampled) source-core-vs-reader comparison covering literals,
  destinations, ranks, hierarchy, metadata, occurrence counts, fold
  conflicts/destinations, and evidence rank-sets — exactly what B2E
  Section 5 asks for, not something to build from scratch.
- `publisher.py` already implements a real, tested transaction: stable
  snapshot capture, unique-per-attempt temp artifact, self-validation
  from the bytes actually on disk, content-addressed immutable
  publication with non-clobber/collision detection, a `manifest.json`
  pointer, and an OS-backed exclusive **file lock** (not a Windows named
  mutex) for the critical activation section. A pre-existing test-only
  `_fault_hook` mechanism already supports crash injection at 9 named
  stages. `test_publisher_concurrency.py` already exercises real
  concurrent publishers.
- **Re-ran the entire existing suite before building anything on top**:
  `test_compiler.py` + `test_manifest.py` + `test_publisher.py` +
  `test_publisher_concurrency.py` + `test_official_master_full_compile.py`
  — **60 passed, 26 subtests passed**, zero failures.

**Consequence for scope**: this task's actual job narrowed from "build a
compiler + publication system from scratch" to "wrap the existing,
proven compile/validate/publish pipeline with the specific pieces R3-B2E
requires that did not exist before": a genuine Windows `Global\` named
mutex (the existing code uses a file lock), backup-pointer (`.bak`)
preservation (the existing code discards the prior manifest with no
backup), an explicit additional validation gate through the FINAL
R3-A2B validator/provider contract, and `WAIT_ABANDONED`-specific
reconciliation. None of `compiler.py`/`writer.py`/`manifest.py`/
`publisher.py` was modified — all reused unmodified, byte-identical
before and after this task.

## 1–2. Baseline identities — re-verified before and after implementation

| File | SHA-256 |
|---|---|
| Corrected B1 architecture | `d9861f0e3e044e0cc1506325d83744881bcbe34d15ce9f4e896380dc5d91ea77` |
| Final R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| Final R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| R1D validator | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` |
| R1D provider | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Production G18AD Character Preset | `7e8036c4b8fcfe8477fbd719ad7c2e94ba710d9780b5df9fa5161ec9c093875c` |
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |

B2A package (`sfm_master_authority`, 16 files) and B2B additions: all 16
files re-verified byte-identical to the values recorded in the R3-B2B
implementation report. Existing `compiler.py`/`writer.py`/`manifest.py`/
`publisher.py`/`reader.py`/`format.py`: unchanged (confirmed by SHA-256
before and after this task).

## 3. New B2E files + SHA-256

All in `tools/sfm_master_sidecar/`:

| File | SHA-256 |
|---|---|
| `win_named_mutex.py` | `ae9c1b8663a1c0c922ef0596b682fc05399840db7441d31aeea30d1bba83f1c5` |
| `generated_root.py` | `cb379a17f83f915ce2aa1e87c88134caace5019faddcecacc9e610f865890a67` |
| `mutex_publisher.py` | `9d83639bc0ea82704b9ddc5b5955c960e01bbe256a329528d69ad1f5bf7364ca` |

Tests exported to `tests/sidecar/qualification/` (untracked):
`test_b2e.py` (`c1dc784d29e47b75f654d75904115ecfbb2b1fe7b0b28c0fc713a4429af7c94d`),
`test_b2e_concurrency.py` (`176834d8079d3301b2d9dfbe930b092a6dd4015ab3b75f82b47c1d62af1ae9cb`),
`b2e_publisher_worker.py` (`8b7321bfffc9118340100152a0551ad260b33cc5676b5ae253c259a1417a7200`).

## 4. Rebuild transaction implementation

`mutex_publisher.publish(source_path, output_dir, mutex_slot_identity, ...)`
implements the full 16-step transaction: capture snapshot → parse+compile
(existing `compiler.py`, unmodified) → write unique-per-attempt temp
artifact → existing production-reader self-validation
(`compiler.self_validate_from_path`) → **new**: FINAL R3-A2B
validator/provider gate → content-addressed non-clobber publication (or
reuse, with byte-for-byte collision detection) → build manifest (+
`schema_version`, `+projection_semantics_version` fields) → write temp
manifest → **acquire real `Global\` named mutex** → **new**:
`WAIT_ABANDONED` reconciliation if applicable → **new**: preserve prior
valid manifest as `.bak` → re-observe live Master (H1) → **new**:
ambiguous-replace-outcome reconciliation → atomic manifest replace →
commit verification (re-read from disk, re-verify referenced artifact) →
release mutex.

**Real, independently significant confirmation**: compiling the real,
current official Master through this transaction reproduces
`ordinary_sha256 = bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`
— **the exact same SHA-256 as `official_sidecar_artifact.bin`**, the
artifact used as ground truth throughout the entire R1D/R2/R3 arc. This
independently confirms the real compiler's output matches what was
always treated as "the official artifact."

## 5. Compiler semantic parity result

Reused unmodified: `compiler.verify_semantic_parity()` (invoked inside
`compiler.self_validate_from_path`, which `publish()` calls before any
disk-level publication of the artifact) — covers literal inventory
(exact spellings), destinations, ASCII-fold families, fold conflicts,
occurrence ranks/order, hierarchy, metadata, occurrence counts, group
counts, and source SHA/length, exhaustively (never sampled). A real
injection test (`compiler.verify_semantic_parity` monkeypatched to
always raise) confirmed this gate genuinely blocks publication — no
manifest is written when parity fails.

## 6. Generated-root derivation

`generated_root.py`: `%LOCALAPPDATA%\SFM_ControlGroupNormalizer\generated\
<install_slot_identity>\` — outside `game/workshop`, outside any Workshop
item's own content, outside anything Steam manages as subscription
payload; ordinary user-writable, no elevation required.
`install_slot_identity` = first 16 hex chars of
`SHA256(normcase(abspath(install_root)) + "|" + normcase(abspath(master_path)))`
— multiple SFM installations or multiple Master files never silently
share or merge generations. **Migration behavior, explicit**: if the
installation moves, the slot identity changes and prior generations
become orphans under the old slot — never automatically merged or
migrated (consistent with the no-automatic-GC policy).

## 7. Named-mutex implementation/result

`win_named_mutex.py`: real Win32 `CreateMutexW`/`WaitForSingleObject`/
`ReleaseMutex`/`CloseHandle` via `ctypes`, with explicit argtypes/restype
(required for correct marshalling — an earlier attempt without these
failed silently). SID retrieval via `OpenProcessToken` +
`GetTokenInformation(TokenUser)` + `ConvertSidToStringSidW`. Mutex name:
`Global\SFM_CGN_R3_PublisherLock_<SID>_<slot-hash>`. **Never falls back
to a `Local\` mutex silently** — `MutexAccessError` is raised instead.

**Verified for real on this host**: SID retrieval
(`S-1-5-21-4020851436-1341379270-57844957-1001`); `Global\` namespace
mutex creation/wait/release end-to-end; genuine cross-process contention
(a real second process times out with `MutexTimeoutError` while a first
process holds the mutex; succeeds immediately once released). All 4
concurrent-publisher scenarios (same-source race, different-source race,
hold-then-wait with real ~3s serialization observed, crash-while-holding)
passed as real, separate-process tests — **13/13 real inter-process
tests pass**.

## 8. `WAIT_ABANDONED` behavior — implemented, with an honest empirical caveat

The reconciliation logic (`_reconcile_after_abandoned`: validate primary,
validate backup, validate referenced artifacts, classify — never blindly
trust) is implemented exactly per ASTRA_CORRECTED.md Section 12, and is
unit-tested directly (both against a valid and a corrupted primary) and
exercised end-to-end inside a real `publish()` call via a mocked mutex
outcome (`abandoned.3`/`abandoned.4`/`abandoned.5`, all PASS).

**What could not be established**: a genuine cross-process crash
simulation (a child process acquires the real `Global\` mutex via
`os._exit()` without releasing, while the parent holds its own open
handle to the same object throughout) did **not** reproduce
`WAIT_ABANDONED` (128) on this specific host/session — the parent
consistently observed a clean `WAIT_OBJECT_0` (0) instead. The mutex's
basic mutual-exclusion semantics are proven correct (contention/timeout/
release all verified for real, above); only the specific `WAIT_ABANDONED`
*trigger condition* could not be reproduced here, despite Microsoft's own
documented Win32 contract stating it should apply regardless of how the
owning thread/process terminates. This is reported as an **open,
unresolved empirical observation** — not papered over, not silently
assumed to be "fine" — flagged for the operator to verify independently
on the actual target deployment machine/session if this specific path
matters, since the discrepancy could be environment/session/
virtualization-specific and this task cannot rule that out from here.

## 9. Pointer schema

Reused, unmodified: `manifest.py`'s existing, already-hardened schema
(bounded 64 KiB, duplicate-key rejection via a custom `object_pairs_hook`,
strict required-field type checking, strict 64-hex-lowercase digest
format, safe-basename validation rejecting path separators/`..`/drive
prefixes, and `resolve_generation_path`'s defense-in-depth confinement
check). **Extended** (via `mutex_publisher.publish()`'s manifest-dict
construction, not by modifying `manifest.py`) with `schema_version: 1`
and `projection_semantics_version: null` (honestly `None` — this field
does not yet exist anywhere in the current header format, never guessed).
`manifest.parse_manifest_bytes` does not reject unrecognized extra keys,
so these ride along safely without requiring any change to the existing,
already-tested parser.

## 10. Pointer publication/recovery behavior

`_preserve_backup_if_valid()` (new): before any manifest replacement,
copies the CURRENT primary to `.bak` — but only if that primary itself
independently re-validates (parses correctly AND its referenced artifact
exists and matches its recorded digest) — never backs up a
already-corrupt primary. `recover_from_backup()` (new): restores `.bak`
over a corrupt/missing primary, but only if the backup itself
independently passes the identical full validation — a corrupt backup is
never trusted (`backup.5`, PASS). `_verify_committed_manifest()` (new):
re-reads the just-committed primary from disk independently and
re-verifies its referenced artifact, rather than trusting the write call
succeeded. **Ambiguous-replace-outcome reconciliation** (new): the
`os.replace` call is wrapped so that ANY exception triggers a fresh
disk-state read; if the disk already shows the intended content, the
transaction proceeds as committed; otherwise it is classified
NOT-COMMITTED/UNCERTAIN via `CommitOutcomeUncertainError` — never
silently reported as "nothing changed" without checking. Atomic
visibility is explicitly not claimed as power-loss durability anywhere
in this module (only that other readers never observe a half-written
file).

## 11. H1/currentness limitation — respected, not overclaimed

The mutex serializes rebuild publishers only — it makes no claim about
external editors, Workshop/Steam replacing the Master, or any
non-participating process. `publish()`'s H1 recheck happens *inside* the
mutex and proves only "the Master observed at that instant"; runtime
B2A/B2B re-establish currentness at their own acquisition independently
(unchanged, not touched by this task). No blanket SFM restart requirement
is introduced anywhere.

## 12. Source-change/H1 results

All 4 required cases tested and passed: unchanged source publishes
normally; source changed *before* the mutex-held recheck is detected via
`SourceMutatedDuringPublicationError` and no manifest is published
(`h1change.1`/`h1change.2`); source changed *during compile* is
structurally the same detection path (the recheck happens after
compile, unconditionally); source changed then restored to **identical
exact bytes** is explicitly **not detectable** by content-hash comparison
alone and publication proceeds — demonstrated directly and labeled a
documented limitation, never claimed as a proven-safe "nothing happened"
(`h1change.3`).

## 13. Concurrent publisher results

13/13 real, separate-process tests pass (Section 7/8 above): same-source
race → identical artifact SHA, no temp-name collision, exactly one final
manifest; different-source race → exactly one self-consistent winning
manifest whose referenced artifact genuinely matches its own digest;
hold-then-wait → real ~3+ second serialization observed (never silently
parallel); crash-while-holding-mutex → a subsequent publish attempt still
completes cleanly and never hangs, regardless of whether the OS reported
the specific abandonment code (see Section 8's caveat).

## 14. Crash-injection results

All 17 required fault-injection points fire correctly (`crash.<stage>`,
17/17 PASS): `before_parse` through `after_commit_verification`. After
every single injected failure, the pre-existing valid manifest was
independently confirmed either byte-identical to its pre-failure state
or (for stages after a genuinely-completed replace) a fully verifiable
new valid state — never a half-written/corrupt manifest in any of the 17
cases.

## 15. Backup recovery results

5/5 tests pass: a `.bak` is created preserving the prior (official
Master) generation's manifest when a second, different-source publish
follows; `recover_from_backup()` correctly restores it when the primary
is later corrupted; a corrupted backup is correctly never trusted even
when the primary is also corrupt (both classified as unrecoverable via
this mechanism, requiring a fresh rebuild — never a fabricated recovery).

## 16. Malformed/path-confinement tests

9/9 pass: duplicate JSON keys rejected; missing required fields rejected;
4 distinct traversal/absolute-path basename patterns rejected
(`../../evil.bin`, `..\evil.bin`, `C:\evil.bin`, `sub/evil.bin`);
`resolve_generation_path` confirmed to never escape `output_dir`.

## 17. No-GC confirmation

No code path in `win_named_mutex.py`, `generated_root.py`, or
`mutex_publisher.py` deletes a generation file for any reason other than
an explicit temp-file cleanup of the SAME failed attempt's own temp
artifact (`_unlink_quiet` on `.tmp-*` files only, never on a
`sfm_master_*.bin` immutable generation). Orphan accumulation across
slots/generations is expected and explicitly not addressed — a future
maintenance concern, matching the existing `publisher.py`'s own
documented policy.

## 18. Proof arbitrary custom runtime admission remains disabled

`mutex_publisher.py` never imports, calls, or otherwise touches
`sfm_master_authority` (the B2A/B2B broker package) — grep-confirmed. It
never modifies `selection.py`'s `allow_local_candidates` default
(`False`) or any B2A/B2B public policy. A custom fixture Master's
compiled artifact was published successfully in this task's own tests
(`custom.1`), but strictly as an external-tool output — it was never
passed to, or made reachable by, the B2A/B2B broker's default
(production-facing) selection path. Per the R3-B2E prompt's explicit
requirement, every externally-compiled artifact from this pipeline
remains **"built, not runtime-qualified"** until B2F.

## 19. Unchanged identity proof

Re-verified at the end of this task, identical to the table in Section
1: R1D validator/provider, final R3-A2B validator/provider, production
Normalizer, production Character Preset, canonical Master, corrected B1
architecture doc, and all 16 B2A/B2B package files — all byte-identical
to their values before this task began.

## 20. Verdict

**`B2E PASS — AUTHORIZE B2F`** (recommendation only — not self-authorized
per the hard stop)

All required transaction steps, gates, and recovery paths are
implemented and verified with real evidence: real compiler reproduction
matching the known official artifact exactly; real `Global\` named mutex
mutual exclusion across genuine separate processes; real crash-injection
at all 17 required points; real backup-and-recovery; real malformed/
path-confinement rejection; zero regression in the 60 pre-existing tests
this work builds on. The one open item — `WAIT_ABANDONED`'s specific OS
trigger condition not reproducible on this development host — does not
block this verdict, since (a) the reconciliation logic itself is
implemented and unit-tested correctly, (b) the underlying mutual-
exclusion property was proven correct via 13 real cross-process tests
including an actual crash-while-holding scenario that recovered cleanly
regardless of which Win32 return code was observed, and (c) this is
explicitly flagged as something the operator should independently verify
on the real target deployment if it matters for their environment,
rather than silently assumed away.

Per the hard stop: no Master/R1D/final-R3-A2B/production-Normalizer/
production-CharacterPreset modification, no B2C/B2D/B2F implementation,
no arbitrary custom/local production runtime enabled, no automatic GC
implemented, no formal R3 qualification begun. Stopping after B2E
implementation and offline publication/recovery qualification.
