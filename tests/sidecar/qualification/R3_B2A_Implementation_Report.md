# R3-B2A — Shared Broker Identity / Resolver / Selection — Implementation Report

Date: 2026-09-15. Implementation (B2A scope only). No SFM launched by this
task. No R1D modification. No modification of the final R3-A2B candidate.
No modification of production Normalizer or Character Preset. No Master
modification. No B2B/B2C/B2D/B2E/B2F implementation.

## 1. Governing corrected B1 artifact — re-verified

`R3_B1_Lifecycle_Broker_Rebuild_Architecture_ASTRA_CORRECTED.md`
SHA-256: `d9861f0e3e044e0cc1506325d83744881bcbe34d15ce9f4e896380dc5d91ea77`
— unchanged from its R3-B1C delivery, confirmed at the start of this task.

## 2. Acceptance-matrix bookkeeping (17 vs 18 vs 19) — resolved, no gap

The R3-B1C prompt contains **19** distinct numbered correction sections
(1 through 19: TXT-fallback through the B2-order fix), but its own
Section 21 literally asked for a table of "B1.1 through B1.17" (17).
Sections **2 through 18 inclusive** are exactly 17 items — the natural
reading is that the "17" refers to the core technical corrections
(broker ownership through retry/UX), with §1 (removing the false
TXT-fallback conflict) treated as a foundational premise-correction and
§19 (the B2 dependency reordering) treated as a sequencing consequence,
both sitting outside that specific "17" count.

My own `ASTRA_CORRECTED.md` acceptance matrix used **18** rows
(B1.1–B1.18), by mapping all 19 prompt sections and merging exactly two
(§18 retry/UX + §19 B2-order) into one combined row (B1.18) — a
deliberate 2-into-1 merge, not a systematic renumbering.

**Direct cross-reference, proving no correction was dropped or hidden by
renumbering:**

| B1C prompt § | Topic | ASTRA_CORRECTED.md § | My matrix row |
|---|---|---|---|
| 1 | TXT-fallback conflict | §1 | B1.1 |
| 2 | Broker module ownership | §2 | B1.2 |
| 3 | Resolver | §3 | B1.3 |
| 4 | Provider lifetimes | §4 | B1.4 |
| 5 | Aggregate memory | §5 | B1.5 |
| 6 | Four identities | §6 | B1.6 |
| 7 | SHA/freshness map | §7 | B1.7 |
| 8 | H0/H1 native race | §8 | B1.8 |
| 9 | Same-source/artifact | §9 | B1.9 |
| 10 | Corrupt-local recovery | §10 | B1.10 |
| 11 | Rebuild parity | §11 | B1.11 |
| 12 | Publisher serialization | §12 | B1.12 |
| 13 | Immutable artifact publication | §12 (merged) | B1.13 |
| 14 | Pointer schema | §13 | B1.14 |
| 15 | Custom-sidecar gating | §14 | B1.15 |
| 16 | CSP migration | §15 | B1.16 |
| 17 | Normalizer migration | §16 | B1.17 |
| 18 | Retry/failure UX | §17 (merged) | B1.18 |
| 19 | B2 dependency order | §19 (merged) | B1.18 |

Every one of the 19 substantive corrections is addressed somewhere in
`ASTRA_CORRECTED.md` with an explicit CLOSED status, regardless of which
counting convention (17, 18, or 19) is used to describe the total.
**No Astra correction is actually still open. B2A proceeds.**

## 3–4. New implementation files + SHA-256

Package location (new, isolated deploy directory — mirrors how
`sfm_master_sidecar` itself was kept isolated inside `gate_r2_formal_deploy`
during its own qualification phase):
`E:\SteamLibrary\...\game\usermod\scripts\sfm\gate_r3_b2a_broker_deploy\sfm_master_authority\`

| File | SHA-256 |
|---|---|
| `__init__.py` | `3d313d0409716c75c408f7099c94f0d5b1028256b9211a42c13ab435fe5a533e` |
| `errors.py` | `a57bc78e17485d05106a708e4b41fa03b87ece86991639e37f62712388eb82c8` |
| `win_file_identity.py` | `31bf82ff84f4a55b8100e1e9dc126bd35dd587c6874e4ed712538ecc5a5c6e74` |
| `resolver.py` | `267391483bcd83359c6fc7647580646f1464de380de89f61e1fbced38be9e392` |
| `native_discovery.py` | `463b2a89a9533a9bf99258f3f90f838562f70ba4cee23b8480698d1b087f2c98` |
| `descriptors.py` | `79c0bcd6aff1c769ed58b8aecefbea5fb5b8a8dcd4c76e75967d715d31b60b5a` |
| `observation.py` | `6ce3763d4de05e710ac65e03e21fabe8f6a6bccf87fab01bc17b76409baaf8a3` |
| `pointer.py` | `5ddfb66d0e119534141365a42356bad0560b079911db9c7661a681610211e6f1` |
| `sidecar_contract.py` | `24732dbf61034f9c111824dead8f4004d66aa0547913e3719c4a36f66467d761` |
| `selection.py` | `2d328cce7d04f3c31e01d89fa92f4aabc543a60263f405181437de0bbbe70a55` |
| `broker.py` | `c7c2a71fa5e6bd51bed48d1385ccf633f0e3fd45502c2cbafff5b7a1e3a98d73` |
| `runtime.py` | `dadb5db175466693eb10c83a920f15e230567bc53420fbdb1dbc01d8d3c99fd0` |

SFM runtime identity probe (`usermod/scripts/sfm/mainmenu/`):
`CGN_R3_B2A_BrokerSingletonIdentity_Probe_01.py`
SHA-256: `0952940db4abdcf64a99b505969cbf4a19f9786670f7468ea5cf4729bbea0e00`

Offline tests exported to `tests/sidecar/qualification/` (untracked):
`test_b2a_offline.py` (`a0a678dd2aae177844bcb6a081fe031238ef3d585856ccf0f4e8ad0964101f1c`),
`b2a_build_fixtures.py` (`73234f6d322305c113a8479bdaeb01bcf734821acf105f08e6a98c1ebec7dd6b`).

## 5. Broker singleton/import contract implemented

`runtime.py`:
- Top-of-module `if __name__ != "sfm_master_authority.runtime": raise ImportError(...)` —
  rejects `execfile`/alternate-alias execution *before* any broker/provider
  side effect, verified by a real test (loading the module's own source
  under a different name via `exec`, confirming the `ImportError` fires
  and no broker state leaks).
- `UNINITIALIZED` → `INITIALIZING` → `READY`/`FAILED` state machine, held
  as module-level state (not per-caller), with a `_construction_in_progress`
  reentry guard — a reentrant call during construction raises
  `BrokerInitializationFailed` rather than returning a partial broker
  (verified by monkeypatching `Broker.__init__` to call `get_broker()`
  recursively).
- `is_canonical()` checks `sys.modules['sfm_master_authority.runtime'] is
  <this module>` on every `get_broker()` call.
- `get_broker(expected_api_version=...)` raises `BrokerIdentityConflict`
  on any API-version mismatch, simulating a second/incompatible package.
- A `_reset_for_test_only()` escape hatch exists *only* for offline tests
  to exercise the state machine repeatedly in one process — never called
  by the probe or any production path, and hot-reload of the live module
  remains unsupported as designed.

## 6–7. Resolver + Windows file-identity implementation

`resolver.py` reproduces production `derive_paths()`'s directory
validation verbatim (ifm.dll path → tools_dir/bin_dir/game_dir →
`usermod/cfg/sfm_defaultanimationgroups.txt`), taking the ifm.dll path as
a parameter (offline-testable; real discovery lives in
`native_discovery.py`, used only by the probe).

`win_file_identity.py` implements the corrected-B1 handle-based identity
proof via `CreateFileW` + `GetFileInformationByHandle` (volume serial +
file index) + `CloseHandle`, with `GetFinalPathNameByHandleW` as
best-effort corroborating evidence only.

**This was tested against real files on this real Windows 10 machine**,
independent of the offline suite, before any package code was written
around it:
- Same file via two differently-cased path strings → identical
  `(volume, file_index)` → `same_file_as() == True`.
- Two genuinely different files → different `file_index` →
  `same_file_as() == False`.
- Nonexistent path → clean `FileIdentityUnavailable`, no crash.

Offline resolver test results (7 real + 1 explicitly skipped):
`RESOLVED_CORROBORATED` (primary+corroborator same identity) — PASS;
`RESOLVED_PRIMARY_QUALIFIED` (no corroborator signal) — PASS;
`RESOLVED_PRIMARY_QUALIFIED` (corroborator dir exists, no Master file) —
PASS; disagreement → `AmbiguousMasterPath` — PASS; missing Master →
`MasterAbsent` — PASS; ifm.dll not under tools/bin →
`AmbiguousMasterPath` — PASS; 2000× identity queries, no handle leak —
PASS. Junction/reparse-point behavior: **SKIPPED**, honestly reported —
creating a real junction fixture requires elevated privileges not
available/exercised on this host; not silently claimed as tested.

## 8. Generation descriptor structures

`descriptors.py`: `SemanticGeneration` (identity #1),
`ArtifactIdentity` (identity #2, `sidecar_artifact_sha256` explicitly
excluded from `SemanticGeneration` equality), `CoverageDescriptor`
(identity #3, schema-only — no consumer views built in B2A),
`ObservationToken` (identity #4, never cached as "still fresh"),
`AcquiredGeneration` (the B2A return value: semantic generation +
artifact identity only — no provider, no view).

## 9. H0/H1 implementation + results

`observation.py`'s `observe_master()` does one full streamed SHA-256 +
exact byte length, never mtime/size. `broker.py`'s
`acquire_generation()` retries the whole H0→select→H1 cycle **at most
once, total** on `AuthorityChangedDuringAcquisition`, per
ASTRA_CORRECTED.md §17.

Real test results, using a stub selection function that mutates a real
fixture Master file *between* the broker's own H0 capture and its H1
recheck (exercising the actual comparison logic in
`Broker._acquire_generation_once`, not a stubbed exception):
- Stable source: two observations agree — PASS.
- Instability on attempt 1, stable on attempt 2 → succeeds after exactly
  2 total attempts (1 retry) — PASS.
- Instability on every attempt → fails with
  `AuthorityChangedDuringAcquisition` after exactly 2 total attempts
  (retry budget exhausted, never unbounded) — PASS.
- **Documented observation limit**: edit-then-exact-restore before the
  next observation is indistinguishable from never-changed under
  SHA-256-only content observation — demonstrated directly (not claimed
  impossible, reported as an inherent property of content-hash
  observation) — PASS.

## 10–11. Sidecar selection behavior + local-corrupt→shipped result

`selection.py` implements the order: local pointer/artifact
(qualification-mode only, `allow_local_candidates=False` by default —
arbitrary local generations remain production-gated pending B2F) →
shipped artifact → `SidecarMissing`/`RebuildRequired`. No TXT path exists
anywhere in the package (verified by a static source scan asserting no
file mentions `TxtSemanticProvider`/`parse_targeted_master`/`MasterTxt`).

Real test results (real official artifact, `MutableSidecar`-corrupted
copy, and real occurrence-count-0xFFFFFFF0 corruption — same technique as
R3-A2B):
- Shipped valid → selected — PASS.
- Sidecar missing (empty shipped root) → `SidecarMissing` — PASS.
- Source mismatch (H0 doesn't match any shipped artifact) →
  `SidecarMissing`, plus a direct `SourceGenerationMismatch` check against
  a wrong expected SHA — PASS/PASS.
- **Corrupt local → shipped recovery**: a corrupted local artifact
  (pointer valid, artifact fails validation) correctly falls through to
  the shipped artifact, logs the exact passive notice
  ("Local compiled Master is damaged; using the matching shipped copy.
  Rebuild to repair."), and the returned result's path is provably the
  shipped path, never the corrupt local one — PASS/PASS/PASS.
- `ResourceAdmissionRefusal` (real artifact refused under an artificially
  tiny cap) propagates and is never converted into a corrupt-fallback
  passive notice — PASS/PASS.

## 12. Explicit failure categories

`errors.py` implements exactly the 15 named categories from Section 12
(`MasterAbsent` through `BrokerInitializationFailed`). `MasterUnknown` is
confirmed absent from this module — there is no consumer semantic lookup
in B2A.

## 13. Offline test counts/results — both interpreters, real runs

`test_b2a_offline.py`: **37/37 PASS** under real Python 2.7.5 (32-bit,
SFM-bundled interpreter) **and** 37/37 PASS under Python 3.10 — two
independent, real interpreter runs, not a single run assumed portable.

## 14. Proof of zero eager provider residency

- `identity.6`: constructing the broker (import + `get_broker()`) opens
  **zero** providers (instrumented count == 0).
- `residency.0/1`: across a mix of genuinely successful and genuinely
  failing `acquire_generation()` calls, every *successfully* opened
  provider was closed (`success_count == close_count`); failed opens
  (exceptions raised inside `open_path` itself) correctly never counted
  as needing a close, since none was ever constructed.
- `residency.2`: the `Broker` instance holds no attribute whose name
  suggests a retained provider/buffer.
- `residency.3`: the bounded diagnostics list stays ≤ 32 entries across
  repeated acquisitions.

## 15. SFM runtime probe — offline preflight

`CGN_R3_B2A_BrokerSingletonIdentity_Probe_01.py` (SHA above). Its actual
logic (`run_probe()`/`_guarded_run()`, bypassing the Qt-timer scheduling
wrapper) was dry-run directly under **both** Python 3.10 and the real
SFM-bundled Python 2.7.5 (which has real `PySide`/`QtCore` available,
confirmed — the module-level `schedule()` call fired without error under
2.7.5): **12/12 checks PASS** in both dry-runs. One real, load-bearing
Python-2.7 syntax issue was caught and fixed during this process: `exec`
is disallowed inside a function that also defines a nested closure in
Python 2.7 — the alternate-alias-rejection check was moved to a
standalone function to satisfy this. Dry-run output artifacts were
deleted afterward so they can never be mistaken for a genuine in-SFM
result.

**This dry-run proves the probe's logic is correct. It does not, and
cannot, prove SFM's own real script-entry/import behavior — only running
it inside real SFM can do that**, which this task does not do (hard
stop: no automatic SFM launch).

## 16. Operator instructions

See the separate operator-instructions message — numbered steps only,
kept apart from findings/analysis per the required format.

## 17–19. Unchanged-identity re-verification

| File | SHA-256 | Status |
|---|---|---|
| R1D validator | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` | unchanged |
| R1D provider | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` | unchanged |
| Final R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | unchanged |
| Final R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` | unchanged |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | unchanged (never opened for write) |
| Production G18AD Character Preset | `7e8036c4b8fcfe8477fbd719ad7c2e94ba710d9780b5df9fa5161ec9c093875c` | unchanged (never opened for write) |

## 20. Verdict

**`B2A OFFLINE PASS — RUNTIME SINGLETON PROBE REQUIRED`**

All offline preflight passed (37/37 offline suite, both interpreters; the
probe's own logic dry-ran 12/12, both interpreters), but SFM's real
script-entry/import behavior is an empirical requirement this task cannot
satisfy without launching SFM — which is explicitly prohibited here. Full
`B2A PASS` requires the operator to run the probe inside a real,
just-restarted SFM session and report its result.

Per the hard stop: no SFM launched automatically, no R1D/final-R3-A2B/
Master/production-Normalizer/production-CharacterPreset modification, no
B2B implementation, no rebuild publisher/mutex, no arbitrary local/custom
production runtime enabled, no formal R3 qualification begun. Stopping
after B2A offline implementation/preflight and creation of the single
runtime identity probe.
