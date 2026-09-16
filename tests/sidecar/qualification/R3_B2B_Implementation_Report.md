# R3-B2B — Finite Acquisition / Detached Views / Aggregate Memory — Implementation Report

Date: 2026-09-15. Implementation (B2B scope only). No SFM launched by
this task. No R1D modification. No modification of the final R3-A2B
candidate. No modification of production Normalizer or Character Preset.
No Master modification. No B2C/B2D/B2E/B2F implementation.

## 1. B2A baseline — re-verified before changes

| File | SHA-256 |
|---|---|
| R1D validator | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` |
| R1D provider | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| Final R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| Final R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Production G18AD Character Preset | `7e8036c4b8fcfe8477fbd719ad7c2e94ba710d9780b5df9fa5161ec9c093875c` |
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| B2A probe (`CGN_R3_B2A_...Probe_01.py`) | `0952940db4abdcf64a99b505969cbf4a19f9786670f7468ea5cf4729bbea0e00` |

All unchanged since B2A. Additionally corroborated: the real B2A probe
result artifact `CGN_R3_B2A_BrokerSingletonIdentity_Probe_01_result.json`
was found in `C:\Users\Public\Documents\` showing `all_pass: true,
pass_count: 12, total_count: 12` — independent confirmation that the
operator's real-SFM run matches this task's authorization basis.

## 2. New/modified B2B package files + SHA-256

All in `.../gate_r3_b2a_broker_deploy/sfm_master_authority/`:

| File | Status | SHA-256 |
|---|---|---|
| `errors.py` | modified (+6 categories) | `0ebb3aad0f56aa0d556d935489911d38baa720465eb79f6e2f24668051dd8611` |
| `views.py` | **new** | `60a0c1afd8cd9260affb006dd67fac20c262e6a38946fa21578268d1270d8b0d` |
| `memory_accounting.py` | **new** | `13f15d29a315e15ea96e77073f427f5c1171e721ff5d320ed234055489d4b4ab` |
| `view_cache.py` | **new** | `3d89e0b9d342518996934bfa8d231d933d2e7aef6650e23228c76d942ebad04d` |
| `cohort.py` | **new** | `50e686c34b498f4213103e9e2bc0c41734b9d78874141457bffbed0610f85387` |
| `projections.py` | **new** | `7dd25ff7104730cef357a6710e3d56e098b7de216eb306527dad2b09c9f0b31a` |
| `broker.py` | modified (+cohort/cache/ledger integration) | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` |

Unchanged B2A files: `__init__.py`, `descriptors.py`, `native_discovery.py`,
`observation.py`, `pointer.py`, `resolver.py`, `runtime.py`, `selection.py`,
`sidecar_contract.py`, `win_file_identity.py` (SHAs unchanged from B2A).

New SFM runtime probe (`mainmenu/`):
`CGN_R3_B2B_FiniteAcquisitionLifetime_Probe_01.py`,
SHA-256 `851578dd4e73538a41373cc71cb78cb5adcf131e393375c39eea63dd2c4d4023`.

Offline tests exported to `tests/sidecar/qualification/` (untracked):
`test_b2b_offline.py`, `b2b_build_fixtures.py`, `measure_b2b_plateau.py`
(plus a residency-check fix to `test_b2a_offline.py`, re-exported).

## 3. Acquisition/cohort state machine

`cohort.py`'s `Cohort`: `OPEN → PROJECTIONS_BUILT → CLOSED_SUCCESS`, or
`OPEN → CLOSED_FAILURE` on any exception, or `OPEN/PROJECTIONS_BUILT →
CANCELLED` on explicit `cancel()`. One cohort ID (monotonic counter); one
H0; at most one open provider (`_open_provider_once` refuses a second
call outright); one declared builder-function set; one H1; the provider
is closed in a `finally` block regardless of outcome — success, failure,
or cancellation.

`broker.py`'s `acquire_cohort()` serializes construction: a second
acquisition attempted while `self._active_cohort.state == OPEN` raises
`AuthorityBusy` before any second provider could open — the only way
"concurrency" can arise in this single-threaded design is a **reentrant**
call (a builder_fn side effect calling back into `acquire_cohort`), which
this guard catches directly.

## 4. Detached-view envelope schema

`views.DetachedView`: `semantic_generation`, `artifact_identity`,
`coverage` (a real `CoverageDescriptor`, not schema-only),
`projection_contract_version`, `admission_id`, `created_at`,
`consumer_kind`, `payload` (plain, already-decoded data), `authorization`
(a separate `LiveAuthorizationToken`), `estimated_bytes`, `pinned`. No
`__slots__` entry for a provider/buffer/handle/traceback exists — checked
directly by a test (`envelope.8`).

## 5. Coverage semantics

`views.CoverageDescriptor.lookup(folded_key)` returns exactly one of:
`Known` (mapped, including fold conflicts — still a real covered result),
`MasterUnknown` (requested, searched, validly absent), or `Uncovered`
(never requested at all — key absent from the descriptor's own map).
`AuthorityUnavailable`-class failures (e.g. `SidecarMissing`) surface at
**acquisition** time, never as a property of an already-published view's
lookup. All four distinguished by 5 real tests using a genuinely
nonexistent real-artifact literal (`MasterUnknown`) vs. a never-requested
key (`Uncovered`).

## 6. One-provider invariant — proof

Real, always-active broker instrumentation (`_on_provider_opened`/
`_on_provider_closed`, never test-only monkeypatching):
`current_open_provider_count`, `peak_open_provider_count`,
`total_provider_opens`, `total_provider_closes`, `active_cohort_id`.

Tested (all real, against the real official artifact/Master):
sequential cohorts (`peak==1`, `current==0` after, `opens==closes`);
reentrant/near-simultaneous request (`AuthorityBusy`, peak stays 1);
failure during selection/validation (`SidecarMissing`, zero opens);
failure during projection building (opens==1, closes==1, current==0);
H0/H1 instability (peak stays 1 even across the retried attempt);
local→shipped recovery through a real cohort (exactly one open, never
one-for-local-plus-one-for-shipped); explicit cancellation before
publication (deterministic close, counters reflect it). **No code path
transiently owned two providers in any of these 7 scenarios.**

## 7. Aggregate memory accounting design

`memory_accounting.AggregateLedger`: one ledger per broker (== one
process-wide ledger), 8 independently-tracked categories (resident
broker metadata, retained views, stale-but-referenced views, pending
projection, incoming snapshot, validator scratch, provider caches,
replacement overlap) — never independent per-tool quotas. `<=16 MiB`
retained / `<=32 MiB` transient remain **aggregate promotion gates**, not
proven facts. `sys.getsizeof()` is never used; `projections.py`'s
`_estimate_payload_bytes` is a conservative structural walk (string
bytes + per-container overhead), explicitly documented as a logical
estimate, not a native/VAS measurement (`AggregateLedger.
RUNTIME_QUALIFICATION_NOTE`, present in code).

**Offline instrumentation** (deliverable 15): a 40-cycle repeated-
acquisition run under real Python 2.7.5 showed the cache entry count
and ledger retained-bytes total **perfectly flat** across all 40 cycles
(2 entries / 70,133 bytes, unchanged every cycle), real GC object-count
growth *decelerating* (153 objects in the first 20 cycles vs. 109 in the
second 20), and a real Windows peak-working-set delta of only ~132 KB
over the whole 40-cycle run — consistent with a genuine plateau, not
monotonic growth. **This offline measurement is not claimed as a
substitute for the designated external-sampler runtime qualification.**

## 8. Eviction/admission behavior

`view_cache.ViewCache.admit()`: computes the logical charge, evicts
under pressure in order (1) unpinned stale views, (2) unpinned
non-stale views (oldest first), refuses (`ViewAdmissionRefused`) only
once every remaining view is pinned. Tested: normal admission; admission
under pressure evicting an old view; refusal when only pinned views
remain; preferential eviction of a stale view before an unpinned-live
one. Invalidation (`invalidate_generation`) marks views stale via their
shared token but never frees/evicts them immediately — eviction happens
lazily under later admission pressure, matching "does not pretend bytes
are freed until references release."

## 9. Cache/reuse key

`DetachedView.cache_key()` = `(master_sha256, projection_contract_version,
coverage.covered_keys(), consumer_kind)`. Tested: same generation/coverage
but different `consumer_kind` → different keys; different
`master_sha256` → different keys; identical everything → identical keys
(reuse). Artifact SHA is deliberately excluded from the key (kept in
`artifact_identity`/provenance only) — proven not to cause conflation in
Section 10 below.

## 10. Same-source/different-artifact result — REAL fixture, not simulated

Built and verified for real this task: reordering the SECTION
DIRECTORY's own row positions in the real official artifact (semantically
invisible to the validator, which looks sections up by `section_id` in a
dict, never by file position) produces **artifact B**
(`e474fb5b405bce92237f8402d64a8567271a9005ed7ae545c8856257f97389e6`),
genuinely byte-different from **artifact A**
(`bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`),
both independently passing the FINAL R3-A2B validator, both sharing the
identical `source_sha256`
(`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).

Proven: an active view pins whichever artifact it selected (does not
hot-swap); semantic-generation equality holds regardless of which
artifact was picked; artifact identity remains distinct per-artifact; the
validation layer (`sidecar_contract.validate_selected_artifact`) never
conflates A and B — each independently re-validates to its own artifact
SHA even though both share one `embedded_source_sha256`.

## 11. Source-generation invalidation result

Using a real acquired view plus the broker's own
`_view_cache.invalidate_generation()` (the same call `acquire_cohort`
performs internally whenever it observes a changed `master_sha256`) —
never a Master file write: the view's `LiveAuthorizationToken` becomes
invalid; its payload remains fully readable; `require_valid()` raises
`ViewInvalidated` for a new mutation attempt; `ViewCache.get()` refuses
to hand the now-stale view back out. No production Master was modified —
only isolated fixture Master files (B2A's freely-mutable `h01` fixture)
and direct ledger/cache calls were used.

## 12. Failure taxonomy additions

`errors.py` gained exactly the 6 B2B categories:
`AuthorityBusy`, `ViewAdmissionRefused`, `ViewUncovered`,
`ViewInvalidated`, `AggregateResourceRefusal`, `CohortCancelled`.
`MasterUnknown` remains a successful covered negative (never an error
class); `ResourceAdmissionRefusal` confirmed distinct from corruption
(a dedicated test proves it never triggers the corrupt-local-recovery
path); `AuthorityBusy` confirmed distinct from memory refusal (separate
exception classes, separate trigger conditions).

## 13–14. Offline test counts/results — both interpreters, real runs

`test_b2b_offline.py`: **58/58 PASS** initially, **64/64 PASS** after
adding the reuse-without-reopening section — under **both** real
Python 2.7.5 (32-bit, SFM-bundled) and Python 3.10, independently run
twice each. `test_b2a_offline.py` (B2A regression suite): **38/38 PASS**
under both interpreters after the `broker.py` changes (one test-only
false-positive fixed: a naming-heuristic residency check flagged the new
*counter* attributes like `peak_open_provider_count` merely for
containing the substring "provider" — corrected to check attribute
*values* for an actual `BoundedProvider` instance or large raw bytes,
which is what the invariant actually means).

## 15. Repeated-cycle memory/cache plateau findings

See Section 7 above (40-cycle measurement) and the probe's own 15-cycle
in-SFM-process dry-run (Section 17), both showing the same plateau
pattern: cache entry count flat, ledger bytes flat, GC growth
decelerating, peak working set essentially flat.

## 16. Proof provider/backing is absent after every cohort

Every one of the 20 real test scenarios in Sections 6/13 above checks
`current_open_provider_count == 0` and/or `total_opens == total_closes`
after the cohort/acquisition completes — success, failure, retry, or
cancellation alike. `broker` instance attributes were checked by VALUE
(not name) to confirm none is a live `BoundedProvider` or large raw-bytes
object (`residency.2`/`residency.2b` in the B2A suite, exercised again
here against the B2B-augmented broker).

## 17. SFM runtime probe — offline preflight

`CGN_R3_B2B_FiniteAcquisitionLifetime_Probe_01.py` (SHA above). **Not**
auto-scheduled like the B2A probe — it contains no `QTimer`/`schedule()`
call at module scope; mainmenu auto-discovery only defines its functions.
It executes only when the file itself is run directly (standard Python
`if __name__ == "__main__":`, matching how SFM's Script Editor "Run"
action executes a file). Verified both ways for real:
- **Import-only** (simulating mainmenu auto-discovery): confirmed inert
  — no probe logic ran, only a "loaded, run me directly" log line.
- **Direct execution** (`runpy.run_path(..., run_name="__main__")` under
  Python 3.10, and native direct execution under real SFM-bundled
  Python 2.7.5): **13/13 checks PASS** in both dry-runs, against the
  real official Master and a staged copy of the real official artifact
  (read-only source, staged copy only to satisfy the `.sfmsidecar`
  extension the selection scanner expects — the real artifact file
  itself was never modified).

Dry-run output artifacts (result JSON, error log, done marker, staged
artifact copy) were deleted afterward so they can never be mistaken for
a genuine in-SFM result.

**This dry-run proves the probe's logic is correct. It does not, and
cannot, prove SFM's own Script-Editor-run behavior sets `__name__ ==
"__main__"`** — that specific assumption (standard, near-universal
Python convention, but not independently confirmed against SFM's actual
Script Editor implementation) is the one thing only the operator's real
run can confirm.

## 18. Operator instructions

See the separate operator-instructions message.

## 19. Unchanged-identity proof

Re-verified at the end of this task (repeated from Section 1's table,
confirmed still identical): R1D validator/provider, final R3-A2B
validator/provider, production Normalizer, production Character Preset,
canonical Master, and the B2A probe file — all byte-identical to their
values before this task began. No production consumer file was ever
opened for writing.

## 20. Verdict

**`B2B OFFLINE PASS — RUNTIME LIFETIME/MEMORY PROBE REQUIRED`**

All offline preflight passed (64/64 B2B suite + 38/38 B2A regression,
both interpreters; the plateau measurement; the probe's own logic
dry-ran 13/13, both interpreters/execution paths). SFM's real Script-
Editor-run behavior and real in-process provider-lifetime/memory
telemetry are empirical requirements this task cannot satisfy without
running inside actual SFM — explicitly prohibited here. The aggregate
retained/transient memory promotion gates (`<=16 MiB`/`<=32 MiB`) remain
**pending** the designated external-sampler runtime qualification; this
task's offline/in-process-dry-run numbers are real but explicitly not
claimed as that qualification.

Per the hard stop: no Master/R1D/final-R3-A2B/production-Normalizer/
production-CharacterPreset modification, no B2C/B2D/B2E/B2F
implementation, no arbitrary custom/local production runtime enabled, no
formal R3 qualification begun. Stopping after B2B offline implementation/
preflight and creation of the single manual SFM runtime probe.
