# R3 B2C-B — Final Targeted Infrastructure Correction (Post Re-Audit of 6bf803f)

Date: 2026-09-18
Candidate root: `tests/sidecar/qualification/candidate_b2c_correction4/` (source at
`sfm_master_authority_productionized/`, staged to `sfm_master_authority/`)
Normalizer candidate: `tests/sidecar/qualification/candidate_b2c_correction4_normalizer/`
Derived from commit: `6bf803fe3bee68a6224f4cc6b36ebf7ab89bd21b`, extracted directly from the git
object store (never a hand-copy of the working tree). Governing re-audit verdict:
`INDEPENDENT CORRECTION RE-AUDIT FAIL — B2C-C remains blocked by pre-admission sparse-prefix
allocation, non-durable release-failure cleanup ownership, and an immutable checkpoint whose
hash-pinned dependencies/fixtures are not byte-reproducible.` No git staging, commit, or push has
been performed during this phase; `.gitattributes` was modified in the working tree only (required
by Blocker 3.A — see Section 7) and remains uncommitted.

**Correct project status**: `B2C-B SEMANTIC EQUIVALENCE RETAINED — B2C-C BLOCKED PENDING TARGETED
INFRASTRUCTURE CORRECTION`. B2C-C remains blocked.

---

## 1. Each Independent-Audit Finding → Exact Correction

| Finding | Root cause | Correction | Evidence |
|---|---|---|---|
| **Blocker 1** — sparse-prefix preflight allocation (`bytearray(dir_region_end)`, scaling with the file-controlled directory offset) | `parse_resource_shape`'s directory-row loop indexed at the ABSOLUTE file offset (`section_directory_offset + i*ROW_SIZE`), forcing callers to reassemble a sparse buffer just to make that indexing line up | New `parse_resource_shape_parts(header_bytes, directory_bytes, artifact_bytes)` indexes directory rows at LOCAL offsets within `directory_bytes` — never reassembling anything sparse. `resource_preflight.py`'s Stage 1 (and Stage 3, as a bonus) now call this directly. | `test_b2c_correction4_offset_independent_preflight_memory.py`: 20/20 both interpreters; private-bytes delta is **exactly 0** at every offset from 64 KiB to 16.6 MB |
| **Blocker 2** — release-failure cleanup was not durably owned (no production retry path; the audit's own critique of the second correction's test pattern) | `final_report()` called a synchronous, single-shot lease-release helper with no retry mechanism reachable from any real lifecycle path | New `_b2c_attempt_lease_release_or_schedule_retry()`: on failure, schedules a bounded (3-attempt) retry via `QtCore.QTimer.singleShot`, keeping the command alive (never unparented/deleted) until resolved; on exhaustion, hands the lease off to a new broker-owned durable reconciliation registry (`register_unreleased_lease`/`retry_unreleased_leases`) before finalizing | `test_b2c_correction4_durable_release_failure_cleanup.py`: 25/25 both interpreters, covering all 8 required cases |
| **Blocker 3** — the immutable commit's `git archive` bytes did not reproduce several hash-pinned inputs (validator/provider, A/B Master fixtures); hardcoded machine-root dependence in `sidecar_contract.py`; non-relative fixture manifests | `git archive`'s zip writer marks text-heuristic blobs with a platform-text flag; without an explicit `.gitattributes` override, some zip extractors translate LF→CRLF on extraction — the git BLOB itself was already correct (verified via `git show`), only the ARCHIVED representation drifted. Separately, `sidecar_contract.py` hardcoded `E:\SFM Animation Group Master\...` and an installed-SFM path. | Added narrow `.gitattributes` `text eol=lf` rules for the two frozen files and the A/B Master fixture pattern (empirically reproduces the audit's exact finding, then empirically confirms the fix — see Section 7); `sidecar_contract.py`'s three path constants are now derived from `__file__`; new fixture manifest schema stores relative paths + semantic role + generation identity | `test_b2c_correction4_archive_reproducibility.py`: 15/15 both interpreters |
| **Section 6 item** — tracked `.pyc`/`__pycache__` allegedly in the `6bf803f` archive | **Investigated, does NOT reproduce.** `git ls-tree -r 6bf803f... --name-only \| grep -i "\.pyc\|__pycache__"` returns zero matches; the actual archive ZIP (`SFM_6bf803f_Independent_Audit.zip`, already verified in the prior checkpoint) also contains zero such entries. No tracked `.pyc`/`__pycache__` files exist to remove. Most plausible explanation: `__pycache__` directories the auditor's own environment generated while RUNNING the extracted Python files, mistaken for committed archive content. | None needed — nothing to fix. `.gitignore` coverage for these patterns was independently re-confirmed already correct. | `git ls-tree`/archive inspection, this session |

## 2. Changed Files + SHA-256

| File | SHA-256 |
|---|---|
| `sfm_master_authority_productionized/broker.py` | `d8935a021db15cce7971c96eeeea06462da6f9a4e251752d4b6f46c830b5350b` |
| `sfm_master_authority_productionized/resource_estimator.py` | `1a753aa3ffd6dfbc9a4f48ab502faba91ee3915fd95234ccb78ca2715bc1cbdb` |
| `sfm_master_authority_productionized/resource_preflight.py` | `5b7b69eb6974298d2d2880a41f875c4a432a53d87194f918eda0a3b9e48d6e70` |
| `sfm_master_authority_productionized/sidecar_contract.py` | `594dd9f6f7c10f48e015cf5e9dedfa563db56b28f0f303fb93f46bcb351684f9` |
| `sfm_master_authority_productionized/runtime.py` | `7d369ea31270bdbfbaec9ab5564166292e5b3f62e0ebdaeb6db407e5f592e80e` |
| `candidate_b2c_correction4_normalizer/Rebuild_...correction4_candidate.py` | `9126c9f020f89a0ad5ccac51b6852a0760d46c64cdcc7c268dde20fc34642ebf` |
| `.gitattributes` (repo root, modified, working tree only) | `a401b0c5af230187dfb4ff31c8214b2305aab8d38e9f4b9bd51332637b80f0b3` |

Every other productionized file (`cohort.py`, `descriptors.py`, `errors.py`, `memory_accounting.py`,
`native_discovery.py`, `normalizer_compat_adapter.py`, `observation.py`, `packed_family_counts.py`,
`pointer.py`, `projections.py`, `resolver.py`, `selection.py`, `view_cache.py`, `views.py`,
`win_file_identity.py`, `__init__.py`) is byte-identical to the version extracted from commit
`6bf803f...` — none of it needed any change for these three infrastructure blockers.

## 3. Exact Diff Against `6bf803f...`

Diffs at `tests/sidecar/qualification/candidate_b2c_correction4/diffs/`: `broker.py.diff` (77 lines),
`resource_estimator.py.diff` (135 lines), `resource_preflight.py.diff` (79 lines),
`sidecar_contract.py.diff` (62 lines), `runtime.py.diff` (13 lines),
`Rebuild_Control_Groups_Normalizer_candidate.py.diff` (230 lines) — each generated via `git diff
--no-index` against the exact file extracted from commit `6bf803f...`'s own object store.

## 4. Preflight Allocation Traces by Directory Offset

From `test_b2c_correction4_offset_independent_preflight_memory.py`, isolating exactly the Stage-1
preliminary-parse scope (header read + directory read + `parse_resource_shape_parts` — deliberately
never the separate, unrelated, already-bounded-by-`runtime_cap_bytes` full read):

| Directory offset | max single preflight read | total preflight bytes | private-bytes delta |
|---|---:|---:|---:|
| 64 KiB | 252 | 360 | 0 |
| 1 MiB | 252 | 360 | 0 |
| 8 MiB | 252 | 360 | 0 |
| 12 MiB | 252 | 360 | 0 |
| 15 MiB | 252 | 360 | 0 |
| 15.9 MiB | 252 | 360 | 0 |

Every offset produces the IDENTICAL 360-byte preflight footprint (108-byte header + 252-byte
directory), and **zero** measured private-bytes growth, under real 32-bit Python 2.7.5, fresh
process per case. This directly contradicts the independently-reproduced defect (~8 MiB offset → ~16
MiB peak; ~15.9 MiB → ~31.8 MiB) — that reproduction's ~2x-offset magnitude is exactly explained by
the OLD code's sparse-prefix allocation (≈offset, now eliminated) PLUS the separate, legitimate,
unrelated Stage-2 full read of a file that must itself be at least as large as its own directory
offset (a structural requirement of the format, unrelated to Blocker 1, unchanged, and out of this
probe's scope by design).

## 5. Real-Lifecycle Lease-Cleanup Traces

From `test_b2c_correction4_durable_release_failure_cleanup.py` (all against the REAL, extracted-
verbatim `_b2c_attempt_lease_release_or_schedule_retry`/`_b2c_finalize_teardown`/`release_run_lock`
methods, driven by an explicit fake Qt event loop rather than a manual out-of-band second call):

| Case | Attempts | Retry scheduled while pending? | Finalized (setParent+deleteLater) | Final lease state |
|---|---:|---|---|---|
| 1. Release succeeds immediately | 1 | — | Yes, immediately | Cleared |
| 2. Fails once, retry succeeds | 2 | Yes (1) | Only after retry succeeds | Cleared |
| 3. Fails twice, 3rd succeeds (within budget) | 3 | Yes (2) | Only after 3rd attempt | Cleared |
| 4. All 3 retries fail | 3 | Yes (2) | Yes — AFTER hand-off, not before | Transferred to broker registry |
| 5–7. Cancellation / command failure / normal completion | — | — | — | Same path as 1–4 (no branch on success/failure) |
| 8. Deferred Qt deletion | — | — | Never while any retry pending | — |

Decisive proof of durable ownership: `cmd.delete_later_calls == 0` for every case as long as a retry
remains scheduled; it becomes `1` only once the lease is either successfully released OR explicitly
handed off — never before.

## 6. Retry/Reconciliation Behavior

Case 4's terminal hand-off is independently reconciled afterward using the broker's OWN sanctioned
path — `broker.retry_unreleased_leases()` — never a manual per-lease repair. The broker's
`unreleased_lease_count()` correctly reflects the hand-off (+1) and its resolution (back to the
pre-test baseline), while `outstanding_lease_count()` (the real ledger-backed lease-ownership count)
never drops during the hand-off itself — proving the underlying accounting was never lost, only its
RESPONSIBLE OWNER changed.

## 7. `.gitattributes` Rules

```
tests/sidecar/qualification/candidate_packed_validator_r3a2b.py text eol=lf
tests/sidecar/qualification/candidate_packed_provider_r3a2b.py text eol=lf
tests/sidecar/qualification/candidate_b2c_correction*/fixtures_ab/*_master.txt text eol=lf
```

Empirically verified both directions: WITHOUT this rule, `git archive --format=zip` of the
already-tracked validator/provider files, extracted via `unzip`, reproduces the EXACT audit-reported
mismatched hashes (`8373f377...`/`58976d42...`); WITH this rule (tested via `git archive
--worktree-attributes`, which honors this session's in-progress `.gitattributes` before it is
committed), the SAME archive-and-extract operation reproduces the contract-pinned hashes
(`74fe8d96...`/`d6ef9650...`) exactly. The git BLOB content itself (via `git show HEAD:<path>`) was
already correct throughout — only the zip-archival representation was affected, confirming this was
an archive-serialization artifact, not an actual content drift.

## 8. Validator/Provider Archive Hashes vs Pins

| | Archived (no `.gitattributes` rule) | Archived (with rule, `--worktree-attributes`) | Contract pin |
|---|---|---|---|
| Validator | `8373f37741c9129b1204e3e9fcc1524b6c4c5fb2e50672d269e883219b75b66b` | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` ✓ |
| Provider | `58976d42d9e571ee85ec391e79363ab4244de03352c74217789c952dba5a63e4` | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` ✓ |

## 9. A/B Master Archive Hashes vs Embedded/Manifest Hashes

New fixtures built by `build_test_ab_fixtures_correction4.py` (repo-relative, LF-only bytes,
asserted at build time), manifest recording relative paths + semantic role + generation identity
(Blocker 3.E):

| Fixture | Master SHA-256 (build-time = fresh-copy re-hash) | Artifact SHA-256 |
|---|---|---|
| `generation_a` | `45664ca281aff14540b0a177a24f354dd8ab0108647f0c252fbd675a0b9b15ed` | `08556ab61e65fa40c7da85331e3f1d2cc0322b3139184cdaf3ef75c68d9c2f1c` |
| `generation_b` | `563d32f4f3b3730fdf6f937138c00617eb680121c2c5bf4a8d8726bd070aab58` | `2b27c98b0ee1b34af1ff2ca0a7f0a169b577a0de951628025aaf91f5ee7c3b15` |

Both values match the ones the independent re-audit itself cited as the correct "embedded/manifest
source SHA" — confirming these were always the intended canonical bytes; only the git-archive
representation (fixed in Section 7) previously drifted from them.

## 10. Archive-Only A/B Sidecar Validation

`test_b2c_correction4_archive_reproducibility.py`, Part 4: opens each sidecar via `BoundedProvider.
open_path` using ONLY the fresh-copy/archive path (never the original working-tree path), against
its own recorded `master_sha256` — both A and B validate successfully (real `iter_groups()` succeeds,
`source_sha256` matches). 15/15 checks pass overall, both interpreters.

## 11. Machine-Root-Independent Archive Execution

Because `candidate_b2c_correction4` is not yet committed (staging/committing is forbidden during
this implementation phase), Part 2 of the same test detects this (`git ls-files` returns empty for
the candidate path) and explicitly reports which mode it ran in — falling back to a fresh, differently
-rooted WORKING-TREE COPY simulation for the candidate + fixtures (the same technique the prior
round's relocated-root test established), while STILL exercising a REAL `git archive` for the
already-tracked validator/provider (Section 7/8). `sidecar_contract`'s three path constants were
confirmed to resolve entirely under the fresh root, never the original `E:\SFM Animation Group
Master\...` path. **This test is permanent and self-upgrading**: once `candidate_b2c_correction4` is
actually committed at a future checkpoint, re-running this SAME file will additionally exercise the
real `git archive <SHA>` path for the fixtures too, without any code change.

## 12. Tracked `.pyc` Cleanup

See Section 1's last row: investigated and does not reproduce. Zero tracked `.pyc`/`__pycache__`
files exist in commit `6bf803f...` or in its own already-verified archive ZIP. `.gitignore` coverage
(`__pycache__/`, `*.pyc`) is confirmed correct and unchanged. No cleanup action was needed or taken.

## 13. Affected Test Totals

| Test | Python 3.10 | Real Python 2.7.5 |
|---|---:|---:|
| Test 1 — offset-independent preflight memory (Blocker 1) | 20/20 | 20/20 |
| Test 2 — durable lease-release cleanup (Blocker 2) | 25/25 | 25/25 |
| Test 3 — archive reproducibility + Test 4 (decisive A/B generation, from fresh root) (Blocker 3) | 15/15 | 15/15 |
| Test 5 — semantic regression | 10/10 | 14/14 |
| **Total** | **70/70** | **74/74** |

(Test 3 and Test 4 from Section 7 are combined into one file, `test_b2c_correction4_archive_
reproducibility.py`, whose own "Part 5" is explicitly labeled as the decisive A/B generation test run
from the fresh/extracted root — satisfying Test 4's requirements directly rather than duplicating the
broker/adapter wiring in a second file.)

## 14. Semantic Regression Results

Full-corpus combined structure hash re-verified against candidate4's (unchanged) adapter:
`3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2` — exact match, both against the
canonical recorded value and against a fresh frozen-parser run under real Python 2.7.5. W1/W2 real
command-scope requests match the frozen parser exactly. groupFile-wrapper regression holds. **W3
remains explicitly UNKNOWN.**

## 15. Frozen Production Identity Table

| Artifact | SHA-256 | Status |
|---|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | Re-verified unchanged |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | Re-verified unchanged |
| Frozen deployed `sfm_master_authority/broker.py` | `d2e66251fe26165976829456eba3ae7fa2420527e41092179d94a401f56dd8b9` | Re-verified unchanged |
| `candidate_b2c_correction3/` + `candidate_b2c_correction3_normalizer/` (pushed checkpoint) | — | Confirmed byte-identical via `git status --short` (empty) — never modified in place |

## 16. Status

**B2C-B FINAL TARGETED INFRASTRUCTURE CORRECTION IMPLEMENTATION PASS — INDEPENDENT RE-AUDIT REQUIRED**

This report does NOT self-authorize B2C-C. All three infrastructure blockers are closed and proven
on both Python 3.10 and real 32-bit Python 2.7.5, using real fixtures, the actual candidate lifecycle
methods, and a genuine (empirically-verified in both directions) `.gitattributes`-based fix for the
archive-reproducibility gap. No SFM was run; no history was rewritten; no staging/commit/push
occurred (the one necessary exception — the working-tree-only `.gitattributes` edit required by
Blocker 3.A — remains uncommitted, ready for the next checkpoint); the second-correction checkpoint
(`candidate_b2c_correction3/`) was never modified in place; frozen production files are confirmed
byte-identical throughout.
