# R3 Package-Boundary Correction Report
**Date:** 2026-09-21

Governing prompt: `SFM_SharedAuthority_PackageBoundaryCorrection_ClaudeCode_Prompt_2026-09-21.md`.
Governing disposition: `docs/qualification/SFM_CGN_ASTRA_HOLISTIC_AUDIT_c0122762_2026-09-21.md`
(documentation-only, committed separately and first, per that prompt's own ordering requirement).

**`Normalizer production integration has NOT yet been performed in this task.`**

## 1. Exact base commits

| Item | Value |
|---|---|
| Astra review target | `c0122762acf11b8ccc4bb7b9d0d891434bf4eb7c` |
| Astra-disposition documentation commit (this task, first commit) | `ae24ceebdec0d9ae425d3494f912b6779d98f1ee` |
| Qualified B2C-B checkpoint | `514a100a380e33b6b6281afdc489921fd68728e1` |
| Final B2C-C correction | `3b5aaa955bafa822da27603514271944b280654e` |
| Frozen production Normalizer SHA-256 | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` (unchanged) |
| Canonical Master SHA-256 | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` (unchanged) |

## 2. Astra findings addressed

| Finding | Priority | Addressed here |
|---|---|---|
| A — leased orphan views escape generation invalidation | RELEASE / INTEGRATION BLOCKER | Yes — fixed + decisive regression |
| B — compiler output / broker input do not form one deployable contract | RELEASE / INTEGRATION BLOCKER | Yes — fixed + decisive regression |
| C — legacy `acquire_generation()` broken | IMPORTANT BUT DEFERRABLE unless supported | Fixed (real, exported, one-line fix) + regression |
| D — failed batch admission can evict unrelated cache entries | IMPORTANT BUT DEFERRABLE | Deferred, unmodified, per explicit instruction |
| Candidate bootstrap depends on repository qualification paths / `__file__` / provisional dirs | Remaining release boundary | Yes — closed (Section 8) |
| Native Master hash → native-use race | Explicitly out of scope for this task | Deferred to Normalizer integration, per Section 15 |
| Eviction-on-failed-admission, custom-Master universality, superset view reuse, CPM migration | Explicit non-campaigns (Section 10) | Not touched |

## 3. Orphan-revocation root cause

`ViewCache.invalidate_generation()` (`candidate_b2c_correction6/sfm_master_authority_
productionized/view_cache.py`) iterated `self._entries.values()` (the live cache dict) only. A view
displaced into `self._leased_orphans` by `_remove()` (the `admit()`/`admit_batch()` same-cache-key
retirement path, when a still-leased entry is retired to make room for a same-key replacement)
keeps its OWN `views.LiveAuthorizationToken` unless that exact token object is separately visited.
The real broker creates exactly ONE token per cohort/acquisition (`cohort.py:144`: `authorization =
views.LiveAuthorizationToken(self.semantic_generation.master_sha256)`), so a displaced orphan from
an EARLIER cohort and its same-generation replacement from a LATER cohort hold two DIFFERENT token
objects — entries-only iteration finds and invalidates the replacement's token, but never the
orphan's own. Confirmed by direct reading (not assumed) and empirically reproduced: constructing
the exact displacement sequence with per-cohort-distinct tokens and reverting the fix showed the
orphan's `is_stale()` remaining `False` after `invalidate_generation()`.

## 4. Orphan-revocation fix

`view_cache.py`'s `invalidate_generation()` now additionally iterates `self._leased_orphans.
values()`, invalidating any matching-generation token found there via the SAME token-dedup set
(so a token shared by multiple orphans is never invalidated twice). Ownership/accounting for an
orphan (its `_leased_orphans` entry, its re-keyed ledger charge from `_remove()`) is completely
untouched by this change — only `LiveAuthorizationToken.invalidate()` is called. This preserves the
required distinction exactly: **ownership remains releasable/accounted; generation authorization is
revoked.**

## 5. Decisive orphan regression

`tests/sidecar/qualification/test_package_boundary_leased_orphan_invalidation.py` — **20/20 PASS**
(real Python 2.7.5 and Python 3.10, identical). Directly constructs `ViewCache`/`DetachedView`/
`AggregateLedger` objects (no I/O, no compiled sidecar needed — the defect and fix live entirely in
this in-memory object graph) and proves, in order:

1. publish/acquire generation A;
2. hold a lease to A;
3. cause A's cached entry to be displaced into `_leased_orphans` (a same-cache-key admission from a
   separate cohort/token);
4. publish/acquire generation B;
5. invalidate A;
6. the old A token/view (the orphan) can no longer pass the current validity/authorization path —
   **and** the still-cached A-generation sibling is also correctly invalidated (both token objects
   checked independently);
7. the old lease can still be released deterministically (no error, orphan entry cleared);
8. retained accounting reaches the correct final value (only the still-live generations' bytes
   remain charged — the orphan's re-keyed charge is fully released);
9. B remains valid (unaffected by A's invalidation);
10. no outstanding leases and no stray ledger-category leakage remain.

Also covers: invalidation-before-release (steps 5–7 above), release-before-invalidation (a separate
scenario, proving the ordinary non-orphan-at-invalidation-time path still works), and repeated-
invalidation idempotence (calling `invalidate_generation` twice more raises no error and leaves
state correctly stale).

**Decisiveness independently verified**: reverting the fix (restoring the entries-only iteration)
while running this exact test produces `18/20 SOME FAILED`, with the two failures being precisely
`step6.A1_orphan_now_stale`/`step6.A1_own_token_invalid` — the exact defect, not an unrelated
symptom.

## 6. Old compiler output contract

| Layer | Producer | Files/fields/layout |
|---|---|---|
| Compiler | `tools/sfm_master_sidecar/compiler.py` `generation_basename()` | `sfm_master_<fmt>_<64-hex-sidecar-sha256>.bin` |
| Manifest | `tools/sfm_master_sidecar/manifest.py` `build_manifest_dict` | `generation_basename, sidecar_sha256, source_sha256, source_byte_length, format_contract_version, authority_semantics_version, compiler_build_version, counts{...}`, validated suffix `.bin` |
| Publisher | `tools/sfm_master_sidecar/publisher.py` `publish()` | writes the artifact + `manifest.json` + `publisher.lock`, all flat in `output_dir` |

## 7. Old runtime input contract

| Layer | Consumer | Files/fields/layout expected |
|---|---|---|
| Shipped-root selection (default production path) | `selection.py` `_find_and_open_matching_artifact` | `os.listdir(root)`, keeps only names ending `.sfmsidecar` — no manifest/pointer read at all |
| Local-candidate selection (qualification-mode only, `allow_local_candidates=True`) | `selection.py` `_try_local_candidate` → `pointer.py` `load_pointer()` | required fields `master_sha256, master_byte_length, artifact_sha256, artifact_relative_path, format_contract_version, authority_semantics_version`; artifact path derived as `<generated_root>/sfmsidecar_v1/<artifact_sha256>.sfmsidecar` |

## 8. Exact mismatches found (before this correction)

| # | Publisher produced | Runtime expected | Effect |
|---|---|---|---|
| 1 | `.bin` extension | Shipped-root scan accepts only `.sfmsidecar` | Real compiled+published artifact invisible to shipped-root scan → `SidecarMissing` |
| 2 | Artifact + manifest flat in `output_dir` | Local candidate resolved at `<generated_root>/sfmsidecar_v1/<sha>.sfmsidecar` | No publisher ever wrote that subdirectory/naming scheme — local-pointer path could never resolve a real artifact |
| 3 | `manifest.json` fields `source_sha256`/`source_byte_length`/`sidecar_sha256`/`generation_basename` | Pointer fields `master_sha256`/`master_byte_length`/`artifact_sha256`/`artifact_relative_path` | Every real field renamed — `load_pointer` raised `LocalPointerCorrupt: missing required field 'master_sha256'` on a real `manifest.json` |
| 4 | — | `sidecar_contract.py` loaded its validator/provider from `tests/sidecar/qualification/candidate_packed_validator_r3a2b.py`/`candidate_packed_provider_r3a2b.py` (two directory levels outside the package) | Package could not run at all without the qualification-tree layout present |
| 5 (found during this task, not named by Astra) | — | `runtime.py`'s canonical-module-name self-check hardcoded `"sfm_master_authority.runtime"` (the old, pre-productionized name) | `import sfm_master_authority_productionized.runtime` raised `ImportError` unconditionally — the documented canonical broker-factory entry point was completely unreachable |

Root cause of #1–#3 never being caught: every existing qualification fixture builder (e.g.
`build_test_ab_fixtures_correction4.py`) bypasses the public compiler/publisher entirely, calling
`compiler.parse_and_compile`/`self_validate_from_bytes` directly and hand-inventing its own
`.sfmsidecar`-suffixed filename and a FIFTH, ad-hoc manifest schema that only that same script's own
`json.load` ever reads back.

## 9. Selected canonical installed contract

One supported publication format/layout, no binary/format changes, minimal field renames:

1. **Extension**: `compiler.generation_basename()` now emits `.sfmsidecar` (was `.bin`) —
   `manifest.py`'s own naming-scheme validation updated to match in lockstep. This alone makes a
   real publish visible to the default, production-facing shipped-root scan with zero runtime code
   changes (that scan already just globs `*.sfmsidecar` in a flat directory, exactly where
   `publisher.publish()` already writes).
2. **Pointer schema reconciled to the real manifest schema**: `pointer.py`'s required fields renamed
   from `master_sha256`/`master_byte_length`/`artifact_sha256`/`artifact_relative_path` to
   `source_sha256`/`source_byte_length`/`sidecar_sha256`/`generation_basename` — matching
   `manifest.py` EXACTLY. `derive_artifact_path` simplified to `os.path.join(generated_root,
   pointer_record.generation_basename)` (the artifact lives directly alongside its manifest, the
   same directory `manifest.resolve_generation_path` uses on the publisher side — the old
   `sfmsidecar_v1/` subdirectory convention was never written by anything). `manifest.json` is now
   literally usable AS the pointer file for both consumption paths — one file, one schema, one
   contract, not two.
3. **Bundled validator/provider**: `candidate_packed_validator_r3a2b.py`/`candidate_packed_
   provider_r3a2b.py` copied byte-for-byte (SHA-256 unchanged, matching `sidecar_contract.py`'s
   pinned constants exactly) into `sfm_master_authority_productionized/` itself; `sidecar_
   contract.py` now resolves them from its own directory, never reaching into `tests/sidecar/
   qualification/`. The original qualification-tree files are left in place, untouched (other,
   older correction-round tests still reference them at their original location).
4. **Fixed `runtime.py`'s canonical-module-name constant** to the real, current package name.

`selection.py`'s two direct field references (`ptr.master_sha256` → `ptr.source_sha256`,
`ptr.artifact_sha256` → `ptr.sidecar_sha256`) updated in lockstep with the pointer schema rename.

## 10. Clean-directory publish → broker-acquire evidence

`tests/sidecar/qualification/test_package_boundary_clean_directory_publish_and_acquire.py`, two
interpreter phases against the SAME published directory (no repository-relative fixture paths — a
fresh `tempfile.gettempdir()`-based directory each run):

- **`--phase=publish` (Python 3.10)**: starts from an EMPTY directory, invokes the real public
  `compiler`/`publisher` path unmodified in flow, then self-checks acquisition immediately —
  **15/15 PASS**. Confirms: `.sfmsidecar` extension produced; artifact and manifest files exist;
  publisher's own reported `source_sha256` matches an independent hash; shipped-root acquisition
  succeeds (no `SidecarMissing`); source generation/artifact identity/semantic projection all
  correct; lease/release lifecycle clean, zero provider leak; the (fixed) local-pointer path,
  reading the real publisher's own `manifest.json` directly as the pointer file, also succeeds.
- **`--phase=acquire` (real Python 2.7.5, a SEPARATE process, no recompilation, no manifest
  rewriting)**: against the directory the publish phase already populated — **11/11 PASS**,
  identical checks, proving cross-interpreter/cross-process compatibility (the real deployment
  shape: Python-3-only compiler tooling, real embedded-Python-2.7.5 runtime).

## 11. Installed bootstrap/package layout

New module `candidate_b2c_correction6/sfm_master_authority_productionized/bootstrap.py`:
- `game_root()`: SFM game root derived from `os.path.dirname(sys.executable)` — the ALREADY-
  QUALIFIED runtime mechanism (confirmed against the real embedded Python 2.7.5 interpreter,
  `docs/qualification/SFM_MASTER_SIDECAR_GATE1_H1_PY27_RUNTIME_AUDIT.md`: `sys.executable ==
  '...\SourceFilmmaker\game\sfm.exe'`) — never `__file__`, never CWD.
- `installed_authority_root()`: the one documented installed location for a published Master
  sidecar generation + manifest, under `usermod/cfg/sfm_shared_authority` (co-located convention
  with `resolver.py`'s own canonical Master path, `usermod/cfg/sfm_defaultanimationgroups.txt`).
- `bootstrap_import_path()`: where the package's own code is expected to be installed, for MAINMENU
  entry code to add to `sys.path` before importing — a separate, independently documented constant
  from the published-data location.
- `ownership_report()`: a single explicit snapshot (game root, installed roots, whether `runtime.py`
  is loaded and canonical) for real bootstrap code to log/inspect.

This module does not itself install/copy/publish anything — it only locates. Actual publication
remains `publisher.py`'s job; actual ownership/readiness state remains `runtime.py`'s job (fixed in
this same correction, Section 9 item 4).

## 12. `__file__`/repo-path elimination evidence (installed-package isolation test)

`tests/sidecar/qualification/test_package_boundary_installed_isolation.py` — **14/14 PASS**:
copies ONLY the real package files (`sfm_master_authority_productionized/`, `sfm_master_sidecar/`,
`sfm_master_core.py` — no qualification/candidate scaffolding) into a fresh temp "installed"
directory; publishes a synthetic Master into a SEPARATE temp directory via the real public
compiler/publisher; then runs the actual acquisition proof as a REAL, SEPARATE Python 2.7.5
**subprocess** whose `sys.path` is built from scratch (stdlib + only the isolated installed-package
directory — never the repository root, never any `candidate_*` directory, never `tools/`), whose
working directory is an unrelated temp directory, and whose environment has `PYTHONPATH` cleared.

Proves, in that genuinely isolated subprocess:
- `sys.path` contains no repository/candidate-directory reference before the script inserts
  anything;
- `sfm_master_authority_productionized.runtime` imports successfully from the isolated directory
  alone (this is what surfaced defect #5, Section 8 — see below);
- `runtime.is_canonical()` reports `True` (duplicate-ownership protection intact);
- `get_broker()` returns a real, `READY` broker, idempotently (a second call returns the SAME
  object);
- real broker acquisition succeeds from the isolated installed publication (`shipped_root` points
  only at the isolated published directory);
- the acquired view's source generation and resolved semantic content match the ISOLATION-specific
  Master, proving no silent fallback to any repository fixture;
- lease/release lifecycle is clean, zero open providers afterward.

**Honest scope limit** (explicitly stated in the test's own docstring, per the governing prompt's
"if this cannot be honestly proven without live SFM, separate what is proven offline from the one
small check that must move to real-SFM qualification" instruction): this proves the package/import/
acquisition boundary is independent of repository paths and CWD, using a real, separate Python
2.7.5 process. It does NOT prove the exact SFM MAINMENU exec/import mechanics themselves
(`execfile()` semantics, Qt main-thread identity, or `sys.executable` actually pointing at a real
`sfm.exe`) — those require real SFM and remain explicitly deferred to real-SFM qualification, not
fabricated here.

**Defect found while building this test** (not named by Astra): the FIRST run of this isolation
test failed with `IOError: No such file or directory: '...\candidate_packed_validator_r3a2b.py'`
— proving, empirically and independently, the EXACT "candidate bootstrap still depends on
repository qualification paths" boundary Astra named. Traced to `sidecar_contract.py`'s external
load path (Section 8 item 4/Section 9 item 3) and the separately-discovered broken `runtime.py`
canonical-name check (Section 8 item 5/Section 9 item 4). Both fixed; the isolation test then
passed cleanly on re-run, with NO changes to the test's own isolation strictness.

## 13. `acquire_generation()` disposition

**Fixed** (not deprecated/removed): a real, non-underscore, independently-documented public
`Broker` method, by that criterion part of the supported surface. One-line fix — the same real
`aggregate_existing_retained_bytes` parameter the qualified path (`cohort.py`) already uses,
computed the same way, replacing the invalid `ledger=` keyword `select_sidecar_candidate` has never
accepted. No redesign of acquisition around this legacy method.

`tests/sidecar/qualification/test_package_boundary_acquire_generation_legacy_fix.py` — **6/6 PASS**
(real Python 2.7.5 and Python 3.10, identical): static proof the bad keyword is gone from the real
call site and the fix uses the real accepted parameter; static proof `select_sidecar_candidate`'s
real signature never had a `ledger` parameter (confirming the original bug was real, not
hypothetical); a real call against a nonexistent shipped root now raises a real `SidecarMissing`-
family error, never `TypeError`; confirmed `normalizer_compat_adapter.py` never references
`acquire_generation` at all (fixing/not-fixing it carried zero risk to already-qualified B2C-C
evidence either way).

## 14. Exact regressions rerun

All under real Python 2.7.5 unless noted; every count below is a fresh run against the exact
corrected source in this commit.

| Suite | Result |
|---|---|
| **New**: leased-orphan invalidation | `20/20 PASS` (both Py2.7.5 and Py3.10) |
| **New**: clean-directory publish (Py3.10) → acquire (Py2.7.5) | `15/15` + `11/11 PASS` |
| **New**: installed-package isolation | `14/14 PASS` |
| **New**: `acquire_generation()` legacy fix | `6/6 PASS` (both interpreters) |
| Decision equivalence (`test_b2c_c_plan_layer_equivalence.py`) | `55/55 PASS` (unchanged) |
| Execution equivalence (`test_b2c_c_execution_layer_equivalence.py`) | `125/125 PASS` (unchanged) |
| Broker composition (`test_b2c_c_broker_mediated_authority_sanity.py`) | `20/20 PASS` (unchanged) |
| Semantic regression (`test_b2c_correction6_semantic_regression.py`) | `14/14 PASS`, canonical hash unchanged |
| AddChild regression (`test_b2c_c_fake_dme_addchild_regression.py`) | `11/11 PASS` (unchanged) |
| Tail real-canonical authority (`test_b2c_c_tail_real_canonical_authority.py`) | `15/15 PASS` (unchanged) |
| Exit-status self-test (`test_b2c_c_exit_status_self_test.py`) | `4/4 PASS` (unchanged) |
| Archive reproducibility (`test_b2c_correction6_archive_reproducibility.py`) | `15/15 PASS` (unchanged; directly exercises `generation_basename()`) |
| Pre-read floor (`test_b2c_correction6_preread_floor.py`) | `18/18 PASS` (matches Astra's independently-reported total) |
| Offset-independent preflight (`test_b2c_correction6_offset_independent_preflight_memory.py`) | `20/20 PASS` (matches Astra's total) |
| Durable release-failure cleanup (`test_b2c_correction6_durable_release_failure_cleanup.py`) | `25/25 PASS` (matches Astra's total) |

Historical F1–F8 external-sampler experiments were NOT rerun — none of their code paths were
touched by this correction, and their evidence is carried forward unchanged by exact identity (see
`docs/qualification/ASTRA_REPO_INDEX.md` Section E for their superseded/historical status).

## 15. Unchanged frozen Normalizer/Master identities

Re-verified before staging, after commit, and after push:

| Identity | SHA-256 |
|---|---|
| Production `Rebuild_Control_Groups_Normalizer.py` | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| Canonical `sfm_defaultanimationgroups.txt` | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |

No drift.

## 16. Deferred findings (explicit, not silently dropped)

- **Defect D (eviction on failed batch admission)**: `IMPORTANT BUT DEFERRABLE`, per the governing
  prompt's explicit instruction. `admit_batch()`'s eviction-before-refusal sequencing was not
  touched by this correction — no code path this correction modifies interacts with it.
- **Arbitrary custom-Master physical-memory universality**: not reopened; the qualified support
  envelope (16 MiB retained / 32 MiB transient promotion gates) is unchanged.
- **Superset view reuse / richer diagnostics / hash micro-optimization**: nice-to-have only, not
  pursued.
- **CPM migration**: CPM was not modified. The package design (bootstrap's two separately-documented
  location constants; the runtime's canonical-ownership contract) accounts for CPM as a plausible
  second consumer without requiring speculative abstractions CPM does not demonstrably need.
- **Native Master hash → native-use race**: explicitly out of scope for this task (Section 15 of
  the governing prompt). Astra's preferred minimum treatment (a short Windows Master read handle
  permitting readers, denying writes/deletion, held from final protected hash through native
  Rebuild and contextual reconciliation) requires one decisive real-SFM compatibility test, recorded
  here as a boundary for the next integration phase, not built or emulated in this task.

**`Normalizer production integration has NOT yet been performed in this task.`**
