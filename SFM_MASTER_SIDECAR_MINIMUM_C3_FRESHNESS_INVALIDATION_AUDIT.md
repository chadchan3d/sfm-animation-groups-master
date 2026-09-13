# SFM Master Sidecar — Minimum C3 Freshness / Invalidation / Retire-Drain Audit

Controlling architecture decision: `SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md`
Controlling repaired foundation: `SFM_MASTER_SIDECAR_ROUND3_FOUNDATION_SIMPLIFICATION_REPAIR_AUDIT.md`

This is the **minimum C3** authorized by Astra Round 3 — command-boundary source
freshness, candidate/manifest compatibility, old-generation retirement, active-lease
drain, terminal close, and next-command lazy G2 readmission. Nothing here is a
filesystem watcher, a poller, a background rebuild service, hot replacement, G1/G2
overlap, a standalone C4 lifecycle platform, a reusable cross-action cache, or any
form of production/Character-Preset integration.

## 1. VERDICT

**MINIMUM C3 PASS — PROCEED TO NORMALIZER INTEGRATION ACCEPTANCE**

All 12 PASS criteria from the brief are met:

1. byte-accurate freshness detection (§4, §5);
2. old generation retirement (§6);
3. no new old-generation work (§6, §7);
4. stale authorization rejection (§7);
5. drain without provider overlap (§8);
6. terminal close/registry cleanup (§9);
7. later explicit G2 admission (§10);
8. changed semantics visible (§10);
9. all listed failure modes recoverable (§12);
10. no stuck PREPARING (§12);
11. no mixed-generation publication (§14);
12. embedded Python 2.7 lifecycle PASS (§17).

A separate C4 is **not** automatically authorized by this PASS (§22).

## 2. BASELINE

- Expected/actual HEAD before edits: `eace35b395ab2a0202c1ffa9ccdae13dccc03bc9` "Simplify sidecar owner foundation" — confirmed matching.
- `git status --short` before edits: clean except the same long-standing pool of unrelated pre-existing untracked files.
- Nothing staged before edits.
- `git diff --check`: PASS, before and after.
- Recorded baseline SHA-256:
  - canonical Master: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
  - official sidecar: `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` (9,506,244 bytes)
  - production reader.py: `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f`
  - format.py: `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259`
  - session_owner.py (pre-C3): `b5c69bec14847e179bb2e01d36fd98f363d7ea639f6eb85e8466a70992660234`
  - external Normalizer: `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`
- Baseline regression before edits (reconfirmed at the same values after, see §18): focused Round 3 foundation harness 40/40, `pytest tests/sidecar/` 369/265, `pytest tests/` 421/265, validator PASS.

## 3. MINIMUM C3 SCOPE

Implemented, and only, per the brief's §0:

1. command-boundary source freshness;
2. candidate generation/pointer compatibility checks;
3. stale authorization rejection after real source change;
4. no new old-generation work after retirement;
5. active operation drain;
6. terminal close of retired authority;
7. next-command lazy readmission of a fresh compatible generation;
8. recoverable failure handling for missing/stale/corrupt/unreadable candidate inputs;
9. no mixed-generation publication or mutation authorization.

Not added, confirmed absent from every file touched: filesystem watcher, periodic
polling, background rebuild service, automatic hot replacement, G1/G2 overlap, queued
job resumption, standalone C4 lifecycle platform, reusable cross-action family cache,
Normalizer production integration, Character Preset integration, native
Rebuild/model mutation, format changes, Candidate B/C.

## 4. FRESHNESS MODEL

Three facts, kept genuinely distinct in the implementation:

- **Source identity**: `command_boundary.hash_source_file(source_path)` — SHA-256 of
  the actual current Master TXT bytes, read and hashed fresh at the command boundary.
  Never mtime/size (§5 proves this explicitly).
- **Candidate generation identity**: `command_boundary.resolve_candidate(...)` reads
  the manifest (a minimal qualification-only parser, see §11) and compares its
  declared `source_sha256`/`format_contract_version`/`authority_semantics_version`
  against the current source hash and this harness's expected contract versions —
  all BEFORE any admission is attempted.
- **Authorization generation**: the owner's own `epoch` (unchanged mechanism from
  Round 3/C2, owned entirely by `session_owner.py`; `command_boundary.py` never reads
  or writes it directly).

Enforcing source: `tests/sidecar/qualification/command_boundary.py`,
`hash_source_file`/`resolve_candidate`/`prepare_command_boundary`.

## 5. SAME-SIZE / PRESERVED-MTIME SOURCE EDIT

Fixture: two hand-written Master TXT fixtures of **identical byte length** (65 bytes
each) differing only in one 3-character control literal (`"AAA"` -> `"CCC"`, same
character count). `os.utime()` explicitly pins the edited file's mtime to the
original file's mtime.

Desktop proof (`desktop_minimum_c3_qualification.py`, C3.2, 8 checks):
- file size unchanged (65 == 65);
- mtime unchanged (identical `os.path.getmtime()` value before/after);
- SHA-256 changed anyway (`fc2b2dc6...` -> `738c83e4...`);
- the freshness check (via `prepare_command_boundary`) detects the edit and returns a
  genuinely new owner;
- the old G1 owner is retired and refuses new work;
- the changed semantic (`"ccc"` newly present) is visible only through the new
  generation, never fabricated onto the old one.

This is the concrete demonstration of why SHA (not mtime/size) is required at the
boundary. Embedded: the same two fixtures (pre-compiled on desktop, see §17) drive
the identical source-change detection in real SFM.

## 6. RETIREMENT CONTRACT

**Minimal owner-state extension**: one new state, `RETIRED`, added to the existing
`EMPTY/PREPARING/READY/UNAVAILABLE/CLOSED` machine. Valid transitions: any live state
(`EMPTY`, `PREPARING`, `READY`, `UNAVAILABLE`) -> `RETIRED` -> `CLOSED` (terminal). No
other transition table changes.

`MasterAuthorityOwner.retire()`:
- idempotent (`"retired"` then `"already-retired-noop"` on repeated calls, proven in
  C3.3, desktop);
- new `acquire_view()` rejected identically to the existing `CLOSED` check (checked at
  the very top of `acquire_view`, and again — alongside the epoch check — both
  mid-resolution and just before publication, so a retirement injected mid-flight is
  caught the same way an epoch mismatch already was);
- existing same-owner active leases remain completely valid via `get_view_via_lease`
  (unaffected by retirement — only draining/closing changes their fate, never
  retirement itself);
- after the last lease releases, the owner may `close()` exactly as before (no new
  close-path code — `close()`'s existing unconditional `self.state = STATE_CLOSED`
  already worked from any prior state, RETIRED included);
- `retire()` also removes the owner from `_OWNER_REGISTRY` immediately (mirroring
  `close()`'s own registry-removal behavior) — a retired owner is never offered again
  for new command-boundary acquisition, even before it finishes draining.

Enforcing source: `session_owner.py`, `STATE_RETIRED`, `_VALID_TRANSITIONS`,
`MasterAuthorityOwner.retire`.

## 7. STALE AUTHORIZATION REJECTION

Desktop C3.4 (3 checks) proves the required distinction directly:
- a retired owner refuses a NEW action/mutation boundary (`acquire_view` raises
  `ResourceRefused`);
- no `MasterUnknown`/semantic fallback is ever fabricated — a real, explicit
  `ResourceRefused` is raised instead;
- the ALREADY-issued lease/payload remains inspectable (`get_view_via_lease` still
  succeeds) — detached payload existence is explicitly NOT the same fact as
  authorization for new work.

Embedded checks "5" and "6" reproduce both halves of this distinction in real SFM.

## 8. ACTIVE LEASE DRAIN

Desktop C3.5 (11 checks) and embedded checks "7"/"8" both reproduce the full
sequence from the brief's §6: G1 READY with two active leases -> retire -> new
acquisition refused -> release N (provider stays alive because P is active) ->
close deferred (`"deferred-active-leases:1"`) -> release P -> close succeeds ->
provider invalid -> registry contains no reusable G1 owner -> exactly ONE provider
allocation across G1's entire lifetime (no overlap).

Only the N-then-P release order was exercised in this C3 gate (the brief's own §6
example uses this single order; both orders were already independently proven for
the underlying `release_lease`/`close` mechanism in Gate C1R and Round 3 — this gate
did not re-derive that, per §15's "do not rerun historical removed-cache tests
unless still relevant").

## 9. G1 CLOSE / REGISTRY CLEANUP

Same mechanism as Round 3's Repair B (`close()` self-removes from `_OWNER_REGISTRY`),
reused unchanged. C3 adds nothing new here beyond confirming `retire()` also performs
the same immediate registry removal (§6), so a retired-but-not-yet-closed owner is
`ALREADY` unreachable via `get_or_create_owner`/`prepare_command_boundary`, not only
once it later closes.

## 10. NEXT-COMMAND G2 LAZY READMISSION

Desktop C3.6 (8 checks) and embedded checks "9"-"11" both prove: after G1 is fully
closed, a genuinely later, separate call to `prepare_command_boundary` (i) returns a
new owner object, (ii) does NOT admit a provider merely by returning (lazy admission
preserved — `provider is None`, `provider_allocation_count == 0` immediately after),
(iii) admits lazily only on the first `acquire_view()` call, which is deliberately
placed in a LATER phase/scenario step than where the new owner reference was
obtained, (iv) receives a new authorization epoch, (v) the changed source semantic
(`"ccc"`) is visible and the old fold (`"aaa"`) is correctly absent, (vi) the old G1
owner remains permanently rejected (now via its `CLOSED` check) even after G2 exists.
No seamless handoff, no automatic readmission on release — G2 only ever comes into
existence via an explicit `prepare_command_boundary` call.

## 11. MANIFEST / POINTER CASES

`command_boundary.py` reads the manifest via a **minimal, deliberately narrow,
qualification-only, Python-2/3-compatible reader** (`_parse_manifest_bytes_compat`),
not the production `tools/sfm_master_sidecar/manifest.py`'s `parse_manifest_bytes`.

This was a genuine finding during embedded qualification: `manifest.py`'s own
docstring states it is "Python 3 only (compiler/publisher-side; the embedded runtime
reader never reads a manifest -- resolving which generation is active is a
host-application/Normalizer concern, entirely outside reader.py's job)" — and its
hardened `isinstance(value, str)` type checks genuinely reject the `unicode` objects
Python 2.7's own `json` module produces for JSON string values, confirmed by a real
`ManifestError` the first time this gate's embedded probe ran against the actual
production parser. Since every other qualification module in this package is
deliberately embedded-Python-2.7-compatible, `command_boundary.py` needed its own
narrow compatible reader for this one purpose. The production `manifest.py` is
**never modified** and remains the sole BUILD-side implementation
(`build_manifest_dict`/`serialize_manifest`, used unmodified by this gate's own
desktop fixture-building helper); `resolve_generation_path` (syntax-safe on both
runtimes) is reused unmodified via duck-typing on `.generation_basename`.

Cases qualified (desktop unless noted):

- **A. Same compatible artifact**: implicit in C3.1/C3.7 — an unchanged or
  pointer-rewritten-but-identical candidate reuses the current owner.
- **B. Pointer rewrite only**: C3.7 (1 check) — re-serializing the manifest (same
  declared identity) does not force invalidation; the SAME owner object is returned.
- **C. New valid generation**: C3.2/C3.6 (throughout) — source changed, pointer
  resolves to a matching new generation; old owner retires; new generation eligible
  only after drain/close and a later command boundary.
- **D. Stale generation**: C3.8 (1 check) — a manifest declaring a `source_sha256`
  that does not match the current TXT is refused (`"candidate source stale"`),
  never admitted, never revives the old authority.

No watcher/polling anywhere in this mechanism — every check above only ever runs
because a test (in production, a real command) explicitly called
`prepare_command_boundary`.

## 12. FAILURE CLASSIFICATION / RECOVERY

Every failure case raises the existing `session_owner.ResourceRefused` — no new
exception hierarchy was created (`command_boundary.ManifestError` is a private,
internal detail of the compatible reader, never raised to a `command_boundary.py`
caller; every case a caller sees is a `ResourceRefused`, exactly as before). Every
case below was reproduced with a recoverable retry that succeeds after correction
(desktop; embedded reproduced case C3.9's missing-manifest scenario as its own
representative case, per §15's "compact fixtures, not a new research campaign"):

| Case | Desktop | Embedded | No owner stuck PREPARING |
|---|---|---|---|
| source unreadable | mechanism present (`hash_source_file`); not separately fixtured (no distinct desktop scenario beyond missing-manifest/missing-artifact, which exercise the same recoverable-refusal shape) | -- | N/A (no owner constructed) |
| manifest/pointer missing | C3.9 (2 checks) | check "12" (3 checks) | N/A (no owner constructed) |
| candidate artifact missing | C3.10 (2 checks) | -- (same shape as C3.9, not re-run embedded) | N/A (no owner constructed) |
| candidate corrupt (truncated .bin) | C3.11 (4 checks) | -- | confirmed `UNAVAILABLE`, not `PREPARING` |
| candidate source SHA stale | C3.8 (1 check) | -- (structurally identical to C3.2's own SHA-mismatch detection, already embedded-verified) | N/A (no owner constructed) |
| profile/version incompatible | C3.12 (2 checks) | -- | N/A (no owner constructed) |
| resource guard refusal | C3.13 (3 checks) | -- (already embedded-verified for the underlying guard mechanism in Round 3/C1R) | confirmed `UNAVAILABLE`, not `PREPARING` |

For every case: no new lease/view was ever published; the old (if any) retired
generation was never silently revived; no TXT fallback was automatically triggered;
a later explicit retry after correction succeeded in every desktop case.

## 13. TXT FALLBACK BOUNDARY

Not implemented or executed in this gate, per the brief's explicit instruction. The
architectural rule is documented here only: a sidecar failure/refusal
(`ResourceRefused`) is categorically distinct from `MasterUnknown` (an authoritative
"not present" answer) — nothing in `command_boundary.py` or the updated
`session_owner.py` ever converts one into the other. An explicit/manual consumer may
separately choose the already-qualified scoped TXT producer (`SharedTxtSession`,
unchanged since Gate B); an automatic/observer path must not surprise a user with a
hidden multi-second TXT parse. No fallback execution path exists in this
qualification code, and none was added.

## 14. NO MIXED-GENERATION PUBLICATION

Desktop C3.14 (2 checks) and embedded check via the mid-resolution retirement guard
(the same code path exercised in Round 3's own epoch-mismatch test, now proven
against `RETIRED`/`CLOSED` too): a `fault_injector` calls `owner.retire()` after the
first fold resolves, mid-candidate-resolution. The in-flight candidate is discarded
entirely (`ResourceRefused`, "no mixed-generation publication"); the owner's
pre-existing published view is untouched. This is the SAME atomicity mechanism
Round 3 already proved for epoch changes (`session_owner.py`'s resolution-loop and
pre-publication checks), extended with one additional `self.state in (STATE_RETIRED,
STATE_CLOSED)` check at both of the same two checkpoints — not a new mechanism.

## 15. COMMAND-BOUNDARY COST OBSERVATION

Measured directly against the REAL canonical Master (3,972,355 bytes) and a
representative real manifest:

- SHA-256 of the entire real Master TXT: **~0.0027s** (2.7 ms).
- Manifest parse (507-byte real manifest, this gate's compatible reader): **~0.00006s**
  (58 microseconds).

Both are trivially cheap at the scale of an explicit, human-initiated command
boundary. No product-value gate is drawn from these numbers (per the brief's
explicit instruction); they are recorded only to confirm hashing the real Master at
a command boundary is reasonable, and explicitly not extrapolated to any
high-frequency observer/callback scenario (none exists in this codebase).

## 16. DESKTOP QUALIFICATION

`desktop_minimum_c3_qualification.py`: **53 PASS / 0 FAIL**, covering every item in
the brief's §14 checklist (unchanged-source reuse, same-size/mtime-preserved edit,
retirement idempotence, new-acquisition-refused, stale-authorization-rejected,
active-lease-drain, no-provider-overlap, registry-cleanup, next-command G2
readmission, changed-semantic-visible, old-G1-lease-rejected-after-G2,
pointer-rewrite-does-not-invalidate, stale-artifact-refused,
missing-pointer/artifact-recoverable, corrupt-artifact-recoverable,
incompatible-profile/version-recoverable, guard-refusal-recoverable,
no-PREPARING-stuck, no-partial-publication, no-mixed-generation-publication). Every
PASS row cites its enforcing function/source region inline in the test output and in
§§4-14 above.

Built against REAL compiled generations (the actual, unmodified production
compiler/writer/manifest pipeline — `sfm_master_sidecar.compiler.parse_and_compile`,
`writer.compile_sidecar`, `manifest.build_manifest_dict`/`serialize_manifest`), never
a mocked or hand-serialized generation.

## 17. EMBEDDED PYTHON 2.7 QUALIFICATION

Real embedded SFM (Python 2.7.5, Qt/PySide main thread), event-loop
`QTimer.singleShot`-chained phases only — no long main-thread sleeps, no native
Rebuild, no model/project mutation, no watcher.

- G1/G2 fixture generations (TXT + compiled artifact + manifest) were pre-compiled
  on desktop Python 3 (the production compiler/writer/manifest pipeline is
  Python-3-only by design) and deployed as static files; the embedded probe only
  reads them and drives the qualification owner/command-boundary logic — it never
  runs the compiler under Python 2.7.
- Disposable SFM process, launched fresh for this probe; trigger via the
  `usermod/scripts/sfm/mainmenu/` flat-file convention (clicked once by the user),
  consistent with Round 3's established mechanism.
- All 5 deployed qualification modules (`bounded_provider.py`, `bounded_view.py`,
  `resource_budgets.py`, `session_owner.py`, `command_boundary.py`) were SHA-256
  -verified byte-identical to the repo originals before the run.
- First run failed with a genuine finding (§11's manifest Python-2/3 incompatibility)
  -- fixed in `command_boundary.py`, redeployed, verified byte-identical again, and a
  fresh disposable SFM process was launched (module caching in the first process's
  Python interpreter made a same-process retry insufficient once the module had
  already imported successfully once).
- Second run: **24 PASS / 0 FAIL**, covering all 13 items in the brief's §13
  checklist: admit G1 (2 checks); two active leases (1); source SHA changes at
  boundary + retire G1 (3); new G1 acquisition refused (1); stale lease rejected at
  the new-action gate while still inspectable (1); active leases drain, N-then-P
  order (3); close G1, no provider overlap (2); G1 lease rejected once CLOSED (1); G2
  admitted only on the later explicit step (1); G2 changed semantic visible (2); new
  authorization epoch (1); old G1 rejected after G2 exists (1); missing-manifest
  failure recoverable (3); final cleanup (1).
- Cleanup: disposable SFM process killed with the user's explicit confirmation both
  times; `usermod/scripts/sfm/gate_c3_deploy/` removed entirely;
  `usermod/scripts/sfm/mainmenu/ZZZ_Gate_C3_Freshness_Probe.py` removed; stray
  `.pyc` files Python 2 wrote into the repo's own `tools/sfm_master_sidecar/`
  directory (via the probe's `REPO_TOOLS` sys.path addition) were found and deleted.
- `sfm_init.py` (both platform and usermod copies) confirmed byte-unchanged
  throughout (see §18) — neither was ever edited.

Preserved durably in the repository (byte-exact, not regenerated):

- `tests/sidecar/qualification/minimum_c3_embedded_evidence/gate_c3_embedded_probe.py`
  — SHA-256 `02ee4b611652457d756ed9e4ee8ab6f5885ade2300b1a0498277216a01f878b8`
- `tests/sidecar/qualification/minimum_c3_embedded_evidence/gate_c3_embedded_result.log`
  — SHA-256 `481e5bd3fd1d09054f4b40e90c573eec53f4aa4de00841303b704e11265b5fd3`
- `tests/sidecar/qualification/minimum_c3_embedded_evidence/gate_c3_embedded_stage_markers.log`
  — SHA-256 `346a165b723746b390126161ee77d6ed0f7d6d383eae8c8f39998c3b97b22f73`
- `tests/sidecar/qualification/minimum_c3_embedded_evidence/gate_c3_embedded_results.json`
  — SHA-256 `2c8cb5c9b4f830e958e93700d2620ba34a01054aa4d80dc54644fa77fef4f7e6`

## 18. REGRESSION / IDENTITIES

| Command | Result |
|---|---|
| `desktop_round3_foundation_qualification.py` | 40 PASS / 0 FAIL |
| `desktop_session_owner_qualification.py` (C1/C1R) | 75 PASS / 0 FAIL |
| `desktop_view_expansion_qualification.py` (C2/C2R) | 44 PASS / 0 FAIL |
| `desktop_minimum_c3_qualification.py` (new) | 53 PASS / 0 FAIL |
| `desktop_parity_and_timing.py` (semantic parity) | 183 PASS / 0 FAIL |
| `python -m pytest tests/sidecar/ -q` | 369 passed, 265 subtests passed |
| `python -m pytest tests/ -q` | 421 passed, 265 subtests passed |
| `tools/validate_master.py` | PASS (0 duplicates, 0 cross-path casefold violations) |

`git diff --check`: PASS.

Production identities, reverified unchanged:

| Artifact | SHA-256 |
|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Official sidecar (9,506,244 bytes) | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| `reader.py` | `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` |
| `format.py` | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` |
| External Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Platform `sfm_init.py` | `7ee38d22df91dc02440553668b2df9a88d6b381ff23447c1a06f82280f12bf2c` |
| Usermod `sfm_init.py` | `08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15` |

No production reader/format defect was discovered during this gate.

## 19. WHAT C3 PROVES

- Source freshness is detected byte-accurately (SHA-256 of actual bytes), never by
  mtime/size, at an explicit command boundary only.
- A stale (source-changed) generation is retired, refuses new work, but keeps its
  already-issued leases inspectable until they drain.
- Drain and terminal close work with no provider overlap and correct registry
  cleanup, exactly mirroring Round 3's existing lease/close mechanisms.
- A fresh, compatible next generation is admitted lazily, only at a genuinely later
  explicit command boundary, with correct new semantics and a rejected old lease.
- Every realistic candidate-input failure (missing/stale/corrupt/incompatible
  manifest or artifact, guard refusal) is recoverable, never leaves a stuck
  `PREPARING` owner, and never silently revives old authority.
- No mixed-generation publication is possible, even under an injected mid-resolution
  retirement race.
- All of the above holds on both desktop Python 3 and embedded Python 2.7.

## 20. WHAT C3 DOES NOT PROVE

- Production Normalizer integration — not attempted, per explicit instruction.
- Character Preset integration — not attempted.
- Any TXT-fallback EXECUTION path — only the architectural boundary is documented
  (§13); no fallback code was written or run.
- Multiple concurrent consumers racing a real command boundary under load — this
  gate's races are single-threaded, deterministically injected (`fault_injector`),
  not a concurrency stress test.
- A generalized manifest/pointer discovery mechanism (directory scanning, "latest"
  resolution, multiple candidate ranking) — the manifest path is always given
  explicitly by the caller in this qualification, matching "keep discovery minimal."
- Behavior under a genuinely malformed-JSON-syntax manifest specifically in the
  embedded Python 2.7 runtime (only exercised on desktop; the embedded probe's one
  failure scenario used a missing file, not malformed JSON, to keep the embedded
  probe compact per the brief's "compact fixtures, not a new research campaign").
- Both lease-release orders in the embedded drain scenario (only N-then-P was run
  embedded; both orders remain proven for the underlying release/close mechanism
  itself from Gate C1R).
- **A production-grade Python-2-compatible manifest/pointer path.** The
  `command_boundary._parse_manifest_bytes_compat` reader (§11) is explicitly
  qualification-only: a minimal, narrow, hand-written reader built specifically
  because the real production `manifest.py` is Python-3-only and cannot run
  correctly under embedded Python 2.7. It does **not** carry that module's full
  hardening (duplicate-key detection, exact SHA-256 hex-regex validation, safe
  -basename checks, etc.). This qualification-layer reader must **not** be silently
  treated as the production answer -- Normalizer integration acceptance (§21) still
  needs its own explicit decision (and, if the answer is "yes, read manifests from
  inside the embedded Normalizer," its own hardened, reviewed implementation) for
  how a real command boundary resolves candidate/pointer identity under Python 2.7.
  This is carried forward as an open item, not resolved by this gate.

## 21. NORMALIZER INTEGRATION AUTHORIZATION OR STOP

Per §17's verdict, Normalizer integration acceptance may begin in a future task.
Nothing in this task begins it. That future task must explicitly address the
Python-2-compatible manifest/pointer path carried forward in §20 above -- this
gate's qualification-only reader is not itself an authorized production
component.

## 22. C4 STATUS

Not authorized by this PASS. A standalone C4 (serialized generation replacement,
hot-swap, or any lifecycle platform beyond what §6-§10 already implement) remains a
separate, future decision — this gate's retire -> drain -> close -> lazy-readmit
model may already be sufficient; that determination is explicitly deferred, per the
brief's own framing ("A separate C4 is not automatically authorized by C3 PASS").

## 23. GIT STATE

- HEAD unchanged throughout this gate: `eace35b395ab2a0202c1ffa9ccdae13dccc03bc9`
  "Simplify sidecar owner foundation".
- Nothing staged (`git diff --cached --name-only` empty throughout).
- No commits made.
- `git diff --check`: PASS.
- Changed (uncommitted): `tests/sidecar/qualification/session_owner.py`.
- New (untracked, uncommitted): `tests/sidecar/qualification/command_boundary.py`,
  `tests/sidecar/qualification/desktop_minimum_c3_qualification.py`,
  `tests/sidecar/qualification/minimum_c3_embedded_evidence/` (4 files), this audit
  document.
- No production file (Normalizer, Master, `reader.py`, `format.py`, binary format,
  `sfm_init.py`) appears in any diff.
- Temporary SFM deployment (`usermod/scripts/sfm/gate_c3_deploy/`, the mainmenu probe
  script, and stray `.pyc` files) all removed; see §17.
