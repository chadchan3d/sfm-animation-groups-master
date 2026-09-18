# R3 B2C-B — Targeted Correction After Independent Audit of 743cad6

Date: 2026-09-18
Candidate root: `tests/sidecar/qualification/candidate_b2c_correction3/` (source at
`sfm_master_authority_productionized/`, staged to the importable `sfm_master_authority/` sibling via
`stage_candidate_authority.py`)
Normalizer candidate: `tests/sidecar/qualification/candidate_b2c_correction3_normalizer/`
Derived from commit: `743cad6bc645ae1aba48d6976f7eb318c859c778` (archive SHA-256
`7df0d4c89b95dde96d18a5344673376ca01a963022797882e2a25d37b19d4ede`), extracted directly from the git
object store (never from a `cp`/hand-copy of the working tree) to guarantee byte-identical ancestry.
Governing independent-audit verdict: `INDEPENDENT CORRECTION AUDIT FAIL — B2C-C MUST NOT PROCEED YET.`
No git staging, commit, or push has been performed as part of this phase.

**Correct project status**: `B2C-B SEMANTIC EQUIVALENCE RETAINED — TARGETED POST-INDEPENDENT-AUDIT
CORRECTION REQUIRED`. B2C-C remains blocked.

---

## 1. Exact Audit Finding → Correction Map

| Finding | Root cause | Correction | Evidence |
|---|---|---|---|
| **Blocker A** — `acquire_or_reuse_views()` accepts `expected_generation` but never forwarded it into its `acquire_cohort()` call | `acquire_cohort()` already had a correctly-ordered pre-publication mismatch check (runs before `_view_cache.invalidate_generation`/`admit_batch`) — it was simply never invoked, because the ONE call site that matters passed no `expected_generation` argument at all, silently defaulting to `None` | Added `expected_generation=expected_generation` to the `acquire_cohort(...)` call inside `acquire_or_reuse_views` (`broker.py`). No second/redundant generation system added — the existing check now actually runs where it was designed to. | `test_b2c_correction3_expected_generation_forwarding_no_prepublish_mismatch.py`, case1-4 (18/18 both interpreters) |
| **Blocker B** — the prior decisive generation test left only sidecar A available, so a rejection could trivially be `SidecarMissing` rather than a real generation-mismatch classification | Test design flaw, not a candidate-source bug in itself — but it meant Blocker A's fix (or its absence) was never actually exercised by a decisive case | New `build_test_ab_fixtures_correction3.py` builds two REAL, compiled, self-validated sidecars (generation A and generation B), both placed in ONE shared shipped root so B is genuinely available and admissible; the decisive case (`case2`) now specifically requires `AuthorityChangedDuringAcquisition`, explicitly rejecting `SidecarMissing` as a satisfying outcome | Same test file, `case2.0`–`case2.5`: rejects specifically on generation mismatch, B never published, prior state unchanged, bounded retry |
| **Blocker C** — `final_report()` unconditionally cleared `self._master_index_lease = None` in a `finally`, even when `release_view_lease` raised, discarding the only cleanup handle | Teardown treated "attempted release" and "successfully released" as the same event | New `_b2c_release_master_index_lease()` method: clears the handle and cleanup flag ONLY on success; on failure, retains the handle, sets `self.master_index_cleanup_incomplete = True`, logs (never swallowed), and remains callable again later for deterministic retry/reconciliation using the SAME method — never a manual, out-of-band repair | `test_b2c_correction3_release_failure_handle_retention.py`, cases 1–6 (27/27 both interpreters) |
| **Narrow Issue D** — `evaluate_cumulative_admission()`'s transient sum omitted `aggregate_existing_retained_bytes`, undercounting real concurrent memory pressure | Ambiguous/undocumented gate semantics; the formula implicitly chose interpretation A (incoming delta only) without ever stating so | Documented BOTH gate semantics explicitly in `resource_estimator.py`'s docstring; resolved to interpretation **B** (total resident pressure including already-retained state) per the prompt's preferred conservative reading; added `aggregate_existing_retained_bytes` as an explicit term in `total_transient_bytes`. 16/32 MiB thresholds themselves unchanged. | `test_b2c_correction3_retained_plus_incoming_transient.py` (9/9 both interpreters) — proves the OLD formula would have admitted a request the NEW formula correctly refuses, with the retained gate never the reason (isolates the transient-specific effect) |
| **Narrow Issue E** — the candidate hardcoded absolute `E:\SFM Animation Group Master\...` paths for its authority root, origin dir, and tools root | Bootstrap constants were literal strings instead of derived from the file's own location | `_B2C_QUALIFIED_AUTHORITY_ROOT`, `_B2C_EXPECTED_ORIGIN_DIR`, `_B2C_SIDECAR_TOOLS_ROOT` now computed via `os.path.dirname(os.path.abspath(__file__))`-relative navigation; `stage_candidate_authority.py` was already fully relative (unchanged in this respect). Installed-SFM-path references (real Master, real production Normalizer, historical W1/W2 capture files) remain explicit test inputs, as the prompt itself distinguishes. | `test_b2c_correction3_machine_root_independent_resolution.py` (11/11 both interpreters) — a full copy at a completely different absolute root boots and acquires correctly |

## 2. Candidate Files + SHA-256

| File | SHA-256 |
|---|---|
| `sfm_master_authority_productionized/broker.py` | `a61c89494eae45844158d53d847e2778b15d53932e8b568c21f543bf9376c670` |
| `sfm_master_authority_productionized/resource_estimator.py` | `fcab73655ca11c12f6143e438072a3282c62c9b10d1a27923b0c1f625bf6fe54` |
| `sfm_master_authority_productionized/runtime.py` | `82f7dfce2378854d0f9136b28319b1b86867dbe113b99b25c6091118a5492db1` |
| `candidate_b2c_correction3_normalizer/Rebuild_Control_Groups_Normalizer_B2CB_correction3_candidate.py` | `3078dcfe113886da9c112f532d422955d1223c31e7bf7b33e8ecb707672a1967` |
| `stage_candidate_authority.py` | `eb861a024e8eca64399ce0e7962368e7314b79f6577e295cf9d182f287b26f67` |

Every other file under `sfm_master_authority_productionized/` (`cohort.py`, `descriptors.py`, `errors.py`,
`memory_accounting.py`, `native_discovery.py`, `normalizer_compat_adapter.py`, `observation.py`,
`packed_family_counts.py`, `pointer.py`, `projections.py`, `resolver.py`, `resource_preflight.py`,
`selection.py`, `sidecar_contract.py`, `view_cache.py`, `views.py`, `win_file_identity.py`, `__init__.py`)
is **byte-identical** to the version extracted directly from commit `743cad6...` — none of the
preserved second-correction machinery (bounded direct directory reads, packed family counts before
expansion, aggregate/batch admission, evicted-view lease refusal, snapshot re-admission, failure
matrix) needed any change for this targeted correction.

## 3. Exact Diff Against `743cad6...`

Diffs at `tests/sidecar/qualification/candidate_b2c_correction3/diffs/`: `broker.py.diff` (34 lines),
`resource_estimator.py.diff` (73 lines), `runtime.py.diff` (22 lines),
`Rebuild_Control_Groups_Normalizer_candidate.py.diff` (157 lines) — each generated via
`git diff --no-index` against the exact file extracted from commit `743cad6...`'s own object store
(never the working tree, and never `candidate_b2c_correction2/`'s current on-disk state, to rule out
any accidental double-diff against an already-modified copy).

## 4. Valid A/B Fixture Identities

Built by `build_test_ab_fixtures_correction3.py` (repo-relative, Python 3 only, real
compiler/writer/reader pipeline — every fixture is genuinely compiled and self-validated, never
hand-assembled), at `candidate_b2c_correction3/fixtures_ab/`:

| Fixture | Master SHA-256 | Artifact SHA-256 | Bytes | Occurrences |
|---|---|---|---|---|
| `generation_a` | `45664ca281aff14540b0a177a24f354dd8ab0108647f0c252fbd675a0b9b15ed` | `08556ab61e65fa40c7da85331e3f1d2cc0322b3139184cdaf3ef75c68d9c2f1c` | 610 | 3 |
| `generation_b` | `563d32f4f3b3730fdf6f937138c00617eb680121c2c5bf4a8d8726bd070aab58` | `2b27c98b0ee1b34af1ff2ca0a7f0a169b577a0de951628025aaf91f5ee7c3b15` | 610 | 3 |

Both artifacts are copied into ONE shared shipped root (`fixtures_ab/shipped_both/`) so both
generations are simultaneously, genuinely discoverable — the exact condition Blocker B's decisive
case requires.

## 5. Pre/Post Cache and Generation State (Decisive A/B Test)

From `test_b2c_correction3_expected_generation_forwarding_no_prepublish_mismatch.py`, case2 (the
decisive case):

```
before: last_known_master_sha256=None view_cache_entry_count=0 view_cache_keys=[] ledger_total_retained=0
outcome: AuthorityChangedDuringAcquisition: acquire_cohort: command pinned to expected generation
         '45664ca2...', but this acquisition produced generation '563d32f4...' -- refusing to
         publish or return it.
after:  last_known_master_sha256=None view_cache_entry_count=0 view_cache_keys=[] ledger_total_retained=0
publications=0 (of a batch that WOULD have been genuinely admissible on its own)
cohort_attempts=2 (one bounded retry, both attempts correctly rejected before publication)
```

No cache invalidation, no publication, no `_last_known_master_sha256` mutation — state before and
after the rejected attempt is byte-for-byte identical. Case1/3/4 pre/post snapshots are printed in
full by the test's own stdout (`[case1] before=... after=...` etc.).

## 6. Real Teardown Ownership Traces

From `test_b2c_correction3_release_failure_handle_retention.py` (all against the REAL,
extracted-verbatim `_b2c_release_master_index_lease`/`final_report`/`release_run_lock` methods, bound
onto a minimal fake command object — never a re-implementation):

| Case | payload ref | lease ref | outstanding_lease_count delta | cleanup_incomplete |
|---|---|---|---|---|
| Normal completion | cleared | cleared | −1 | False |
| Cancellation (`success=False`) | cleared | cleared | −1 | False |
| Command failure after acquisition | cleared | cleared | −1 | False |
| Release failure | cleared | **RETAINED** | 0 (still live) | **True** |
| Retry/reconciliation (same method, same handle) | already cleared | cleared | −1 | False |
| Deferred QObject deletion after a failed release | cleared | **RETAINED** (untouched by `release_run_lock`) | 0 | True (until later retry) |

## 7. Release-Failure Retry/Reconciliation Evidence

Case 5 of the same test proves retry uses the candidate's OWN method, not an external repair:
`cmd4._b2c_release_master_index_lease()` is called a second time on the SAME `_FakeCommand` instance
that Case 4 left in the "release failed, handle retained" state — no other attribute is touched by
the test between Case 4 and Case 5. The retry succeeds (`_master_index_lease` becomes `None`,
`master_index_cleanup_incomplete` becomes `False`, the broker's real `outstanding_lease_count` drops
by exactly 1), and a THIRD call after that succeeded retry is a verified safe no-op (idempotent,
never a double-release).

## 8. Documented Retained/Transient Gate Semantics

Now stated explicitly in `resource_estimator.py`'s `evaluate_cumulative_admission` docstring:
- **Retained gate** (16 MiB, unchanged): maximum total retained authority state after publication
  (`aggregate_existing_retained_bytes + total_retained_bytes`) — unchanged behavior, already correct.
- **Transient gate** (32 MiB, unchanged): resolved to **interpretation B** — total authority-related
  resident memory pressure during the acquisition window, INCLUDING already-retained views, not
  merely the incoming delta. Rationale documented in-line: existing retained bytes are genuinely
  still resident (not evicted) for the whole acquisition window and therefore contribute to real
  concurrent peak pressure exactly like the acquisition's own new terms already did.

## 9. Retained+Incoming Memory Test

`test_b2c_correction3_retained_plus_incoming_transient.py`, decisive case: with 10 MiB of simulated
existing retained state and a real (tiny) incoming request, `combined_retained_bytes` = 10,491,984
(under the unchanged 16 MiB retained gate — isolates the transient effect); the OLD-style transient
total (incoming delta alone) = 23,075,300 (would have been ADMITTED under the pre-fix formula); the
NEW total = 33,561,060 (over the unchanged 32 MiB / 33,554,432-byte gate) — correctly REFUSED, with
`reason=cumulative_transient_exceeds_gate` specifically (never the retained gate or the secondary
cap). 9/9 checks PASS on both interpreters, including real Python 2.7.5.

## 10. Machine-Root-Independent Execution Evidence

`test_b2c_correction3_machine_root_independent_resolution.py`: copies `tools/`,
`candidate_b2c_correction3/`, and `candidate_b2c_correction3_normalizer/` into a fresh temporary root
at a completely different absolute path (verified NOT to start with the original repo path), then
runs the REAL bootstrap and a REAL acquisition entirely from that fresh location, using fixtures ALSO
copied there. 11/11 PASS on both interpreters — the resolved authority origin, the expected-root
constant, and the tools-root constant all resolve under the FRESH root, never the original
`E:\SFM Animation Group Master\...` path.

## 11. Affected Test Totals

| Test | Python 3.10 | Real Python 2.7.5 |
|---|---:|---:|
| Test A — pre-publication generation binding (Blockers A+B) | 18/18 | 18/18 |
| Test B — actual command teardown (Blocker C) | 27/27 | 27/27 |
| Test C — aggregate memory semantics (Issue D) | 9/9 | 9/9 |
| Test D — path/fixture reproducibility (Issue E) | 11/11 | 11/11 |
| Test E — semantic regression | 10/10 | 14/14 |
| **Total** | **75/75** | **79/79** |

Per Section 7's own instruction, unrelated historical campaigns (the full second-correction Test 1-6
suite) were NOT re-run — none of those suites' own code paths (`resource_preflight.py`,
`packed_family_counts.py`, `selection.py`, `view_cache.py`'s `admit_batch`/`acquire_lease`) were
touched by this targeted correction, so their prior evidence (already committed at `743cad6...`)
remains the standing proof for that surface.

## 12. Semantic Regression Results

Under real Python 2.7.5 (Test E): the corrected adapter's full-corpus combined structure hash exactly
matches the frozen production parser AND the previously-recorded canonical value
(`3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2`); W1 and W2 real command-scope
requests match the frozen parser exactly; the groupFile synthetic-wrapper regression holds (no
phantom `groupFile` group leaks into adapter output); the candidate Normalizer file references no
native/DME mutation symbol. **W3 remains explicitly UNKNOWN** (unchanged, not re-derived, not
force-substituted).

One test-authoring bug was found and fixed WHILE BUILDING this evidence (not a product regression):
the first draft of `test_b2c_correction3_semantic_regression.py` substituted Python's Unicode-aware
`str.lower()` for the real, extracted `ascii_fold()` under Python 3, which produced a spurious hash
mismatch; corrected to always use the real `ascii_fold()` regardless of interpreter, after which the
hash matched exactly. Documented here for transparency per this project's standing "trust but verify"
discipline.

## 13. Frozen Identity Verification

| Artifact | SHA-256 | Status |
|---|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | Re-verified unchanged |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | Re-verified unchanged |
| Frozen deployed `sfm_master_authority/broker.py` | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | Re-verified unchanged |
| `candidate_b2c_correction2/` + `candidate_b2c_correction2_normalizer/` (pushed second-correction checkpoint) | — | Confirmed byte-identical to `743cad6...` via `git diff --stat HEAD` (empty) |

**Self-correction note**: while extracting the starting content for `candidate_b2c_correction3/` from
the git object store, an intermediate `mv`-based extraction step briefly left the WORKING-TREE copy
of `candidate_b2c_correction2/`/`candidate_b2c_correction2_normalizer/` deleted (uncommitted, never
staged or committed — the commit object itself was never at risk). Caught before any further work via
routine `git status` review, and immediately restored with `git restore` from HEAD; verified
byte-identical to `743cad6...` afterward (see above). No data loss occurred; noted here in full for
transparency.

## 14. Current Support-Domain Statement

Unchanged from the second correction's declared support domain: read-only Normalizer authority
acquisition (B2C-B scope) only. This targeted correction touched exactly three productionized files
(`broker.py`, `resource_estimator.py`, `runtime.py`) plus the Normalizer candidate's bootstrap/
teardown code — no mutation policy, taxonomy, or presentation logic was touched. The 16 MiB retained
/ 32 MiB transient promotion gates are unchanged in VALUE; only the transient gate's own documented
formula changed (now includes existing retained state, per Issue D). `MAX_SINGLE_FOLD_OCCURRENCE_ROWS
= 20000` remains an explicitly-flagged, non-authoritative secondary ceiling, unchanged. B2C-C, B2C-D,
and Character Preset migration remain entirely out of scope and have not been started. No SFM was
run at any point in this phase.

## 15. Status

**B2C-B TARGETED CORRECTION IMPLEMENTATION PASS — INDEPENDENT RE-AUDIT REQUIRED**

This report does NOT self-authorize B2C-C. All five required regression probes (Section 8's naming
requirements: expected-generation-forwarding/no-prepublish-mismatch, valid-B-sidecar command-A
rejection, release-failure-handle-retention, retained-plus-incoming aggregate transient, machine-
root-independent bootstrap/fixture resolution) pass on both Python 3.10 and real 32-bit Python 2.7.5,
using real compiled fixtures and the actual candidate command/bootstrap code paths throughout — never
a weaker alternate outcome (`SidecarMissing` was never accepted for the generation test; manual
out-of-band lease cleanup was never used for the release-failure test). No SFM was run; no history
was rewritten; no git staging/commit/push occurred; frozen production files are confirmed byte-
identical throughout.
