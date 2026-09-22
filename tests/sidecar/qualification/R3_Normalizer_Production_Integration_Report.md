# R3 Production Normalizer Integration Report

## 1. Starting commit

`cf06ba4ec2080e17d5132ed15f641c143a4137b1` (accepted authority-package integration base, per the governing implementation brief's Section 0 -- independently re-audited).

## 2. Final commit

See the commit this report is included in (created immediately after this report was written, per the git-discipline section below).

## 3. Exact files changed

**Outside the git repository** (real SFM installation, not tracked by this repo):
- `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py` -- the frozen production Normalizer itself. This is the ONE functional change this checkpoint makes.

**Inside the git repository**:
- `tests/sidecar/qualification/candidate_b2c_c/production_plan_layer.py` -- line-range/SHA-256 pin relocation only (46 `PLAN_LAYER_RANGES` entries + `PREFLIGHT_RECONCILIATION_PLAN_RANGE`), forced by the frozen file's line-number shift; zero logic/assertion change.
- `tests/sidecar/qualification/candidate_b2c_c/production_execution_layer.py` -- line-range relocation only (30 `EXECUTION_LAYER_RANGES` entries); zero logic/assertion change.
- `tests/sidecar/qualification/candidate_b2c_c/authority_pair.py` -- SHA-256 pin + line-range relocation only (9 `PROD_RANGES` tuples); zero logic/assertion change.
- `tests/sidecar/qualification/test_b2c_c_tail_real_canonical_authority.py` -- SHA-256 pin + line-range relocation only; zero logic/assertion change.
- `tests/sidecar/qualification/test_normalizer_integration_bootstrap.py` -- new, Section 9A.
- `tests/sidecar/qualification/test_normalizer_integration_acquisition.py` -- new, Section 9B/9C.
- `tests/sidecar/qualification/test_normalizer_integration_native_protect.py` -- new, functional qualification for Section 6's native-Master-protect mechanism.
- `tests/sidecar/qualification/R3_Normalizer_Production_Integration_Report.md` -- this report.

Nothing inside `tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized/` or `tools/sfm_master_sidecar/` was touched (confirmed by `git diff --stat`, empty). The accepted package architecture was not reopened.

## 4. Pre-integration Normalizer SHA-256

`6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`

## 5. Post-integration Normalizer SHA-256

`f69a57436d46252fb78d9ae2a2155d7206e07869c74ac5f4d28f6676f5ef2cf0`

(353,711 bytes, 13,911 lines, still pure ASCII -- confirmed by direct decode -- and still pure LF line endings, matching the file's own pre-existing convention.)

## 6. Canonical Master hash confirmation

`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` -- unchanged. The canonical Master TXT was never opened for writing by any step of this checkpoint.

## 7. Accepted package/build identity used

- Package: `sfm_master_authority_productionized` (commit `cf06ba4`, unmodified this checkpoint).
- `RUNTIME_API_VERSION = "1.0.0-b2a"` -- pinned as a hardcoded literal in the Normalizer's own `_AUTHORITY_EXPECTED_API_VERSION`, never read back from the loaded module for the comparison itself.
- `RUNTIME_BUILD_ID = "package-boundary-corrected-2026-09-22"` -- pinned as `_AUTHORITY_EXPECTED_BUILD_ID`, same reasoning.
- Both are enforced at two independent points: (a) once, unconditionally, at module import time, via `_authority_verify_bootstrap_identity()`; (b) again, per command, inside `acquire_master_index_via_qualified_authority()`'s own `authority_runtime.get_broker(expected_api_version=..., expected_build_id=...)` call.

## 8. Exact parser/authority seam replaced

The Normalizer's ONE call to `parse_targeted_master()`, previously:

```python
self.master_index = parse_targeted_master(
    self.master_path, self.master_index_scope_folds, validate_conflicts=False,
)
```

is now:

```python
self.master_index = self.acquire_master_index_via_qualified_authority(usermod_dir)
```

`parse_targeted_master()` itself remains defined in the file, byte-unchanged, now unused at this call site -- deliberately not deleted (this checkpoint's own scope is the seam replacement, not a cleanup of the now-dead reference implementation). Every downstream consumer of `self.master_index` (`master_lookup()`, `validate_master_subset_conflicts()`, group-reorder/groupColor/selectable mutation, the `CONTEXTUALIZER_SCOPED_MASTER_INDEX_BUILD` log line) is completely unchanged, because `normalizer_compat_adapter.build_targeted_master_compatible_projection()`'s payload is byte-identical in shape and values to `parse_targeted_master()`'s own return contract (see that module's own docstring for its empirical, full-corpus, real-Python-2.7.5 proof, and Section 9D below for the downstream-equivalence regression evidence this checkpoint reused/re-verified).

## 9. Exact package/bootstrap entry path used

At module import time, a new block (lines 176-352 of the post-integration file) computes:

```python
game_root = os.path.dirname(os.path.abspath(sys.executable))
mainmenu_dir = os.path.join(game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D")
```

deliberately duplicating `sfm_master_authority_productionized.bootstrap`'s own identical `game_root()`/`bootstrap_import_path()` formula (an unavoidable bootstrap-ordering consequence, not a second discovery system -- the package cannot be asked to compute its own containing directory before it has been made importable). A self-consistency check immediately calls `authority_bootstrap.bootstrap_import_path()` once the package IS importable and asserts it agrees exactly with the Normalizer's own independently-computed value, so the two formulas can never silently drift apart unnoticed.

`mainmenu_dir` is inserted at the front of `sys.path`, and `sfm_master_authority_productionized` is imported from there.

**Discovered, previously-undocumented deployment requirement**: `normalizer_compat_adapter.py` imports `resource_estimator.py`, which does `from sfm_master_sidecar import format as fmt` at module level (not lazily) -- so a real deployment must place the `sfm_master_sidecar` package (currently `tools/sfm_master_sidecar/` in this repo) as a **second sibling directory** directly under `.../ChadChan3D/`, alongside `sfm_master_authority_productionized/`, so the SAME single `sys.path` insertion makes both importable. This was found empirically by `test_normalizer_integration_bootstrap.py` failing with `ModuleNotFoundError: No module named 'sfm_master_sidecar'` until the test's own fake layout was corrected to include it -- see Section 19 (known limitations) for what this implies about real deployment.

## 10. Compatibility projection

`sfm_master_authority_productionized.normalizer_compat_adapter.build_targeted_master_compatible_projection(wanted_folds)` -- unchanged, package-owned, already independently qualified by B2C-C's own equivalence evidence (Section 9D). The Normalizer supplies exactly one `request_specs` entry, `"normalizer_compat"`, covering `frozenset(self.master_index_scope_folds)` (the SAME command-wide vocabulary `collect_scope_master_wanted_folds()` already aggregated across every target in scope, unchanged by this integration).

## 11. Authority/lease lifecycle

One command == one `broker.acquire_or_reuse_views(self.master_path, request_specs, shipped_root=<usermod>/cfg/sfm_shared_authority, expected_generation=self.master_hash)` call, inside the new `acquire_master_index_via_qualified_authority()` method, called exactly once, at the same point `parse_targeted_master()` used to be called. The returned `DetachedView`'s `.payload` becomes `self.master_index`; its lease (`broker.lease_view(view)`) is stored on `self._master_index_lease`/`self._master_index_broker` for the remainder of the command. The packed provider/backing closes internally before `acquire_or_reuse_views()` returns (confirmed by `provider_counters()['current_open_provider_count'] == 0` immediately after, in `test_normalizer_integration_acquisition.py`).

Release is single-attempt, via the new `_release_master_index_lease_durable()`, called as the FIRST statement in `final_report()`'s own `finally:` block (so it runs on success, failure, and every exception path final_report already covers -- `start()`'s own `except Exception` always calls `final_report(False)` before `self.original_head` is ever set). A release failure hands off durably via `broker.register_unreleased_lease(...)`, deliberately simpler than a bounded retry-and-reschedule loop, since `final_report()` is already this command's own single, idempotent teardown point with no remaining command lifetime to retry across.

`expected_generation=self.master_hash` is enforced on every acquisition, cached or fresh -- a later command pinned to a stale/wrong generation is refused (`AuthorityChangedDuringAcquisition`, wrapped as `ProbeError`), never silently reused.

## 12. Native Master protection implementation

A short Windows read handle (`native_master_protect_acquire`/`native_master_protect_release`, `CreateFileW` with `FILE_SHARE_READ` only -- never `FILE_SHARE_WRITE`/`FILE_SHARE_DELETE`) is acquired immediately before the first `assert_master_stable()` call in `run_target_transaction()` (so that stability check's own hash read happens while already protected) and released as the first statement in that method's existing `finally:` block (undo-state restoration), covering native Rebuild and the entire contextual-reconciliation/composition window for one target. Never raises; its own absence never changes run behavior (purely additive to the existing SHA-256 stability checks). This is the minimum bounded protection selected for this checkpoint, per the governing brief's own Section 6 -- not a claim of full native-SFM-Rebuild-callback compatibility, which remains a real-SFM qualification-matrix question.

## 13. All tests run, exact pass/fail counts

| Suite | Result | Interpreter(s) |
|---|---|---|
| `py_compile` of the full post-integration Normalizer | OK | Python 3.10 AND real Python 2.7.5 |
| ASCII/newline-style integrity of the post-integration Normalizer | confirmed pure ASCII, pure LF | n/a (static check) |
| `test_normalizer_integration_bootstrap.py` (Section 9A: import/bootstrap, positive + negative stale-build-id cases) | **8/8 PASS** | Python 3.10 AND real Python 2.7.5 |
| `test_normalizer_integration_acquisition.py` (Section 9B/9C: acquisition/lifetime + failure atomicity) | **17/17 PASS** | Python 3.10 AND real Python 2.7.5 |
| `test_normalizer_integration_native_protect.py` (Section 6/9: native-Master-protect functional check) | **9/9 PASS** | Python 3.10 AND real Python 2.7.5 |
| `test_b2c_c_plan_layer_equivalence.py` (Section 9D, relocated ranges) | **55/55 PASS**, 0 ledger-hash drift across 16 scenarios | real Python 2.7.5 |
| `test_b2c_c_execution_layer_equivalence.py` (Section 9D, relocated ranges) | **125/125 PASS**, 0 ledger-hash drift across 17 scenarios | real Python 2.7.5 |
| `test_b2c_c_broker_mediated_authority_sanity.py` (Section 9D) | **20/20 PASS** | real Python 2.7.5 |
| `test_b2c_c_fake_dme_addchild_regression.py` (Section 9D, unaffected by the relocation) | **11/11 PASS** | real Python 2.7.5 |
| `test_b2c_c_tail_real_canonical_authority.py` (Section 9D, relocated ranges) | **15/15 PASS** | real Python 2.7.5 |
| `git diff --stat` for the accepted package + `tools/sfm_master_sidecar/` (Section 9E) | empty -- confirmed byte-for-byte untouched | n/a |

Totals for this checkpoint's own new/relocated evidence: **34/34** new-harness checks (8 + 17 + 9) and **226/226** carried-forward B2C-C downstream-equivalence checks (55 + 125 + 20 + 11 + 15), all PASS, both interpreters where applicable, zero failures anywhere.

Package-boundary regressions from the immediately-preceding checkpoint (leased-orphan invalidation, build-identity, clean-directory publish/acquire, installed-package isolation, `acquire_generation()` legacy fix) are carried forward **by exact identity**, not re-run: `git diff --stat` confirms the package they exercise is byte-for-byte unchanged this phase, so their prior results remain valid without re-derivation.

## 14. Tests that could not run, and why

None were skipped. The finite real-SFM qualification matrix (Selected/All Shots, Undo, artist workflow, native locking under a real embedded SFM process, etc.) was intentionally **not** attempted -- it is explicitly out of scope for this checkpoint per the governing brief's Sections 10 and 13, and is the next phase's own work (Section 19 below).

## 15. Confirmation: no silent TXT fallback exists

`acquire_master_index_via_qualified_authority()` has exactly one success path (the qualified-authority acquisition) and exactly one failure path (catch `authority_errors.BrokerError`/`authority_compat_adapter.AdapterCorrupt`, re-raise as `ProbeError`). There is no code path that calls `parse_targeted_master()` as a fallback, and `self.master_index` is never assigned on the failure path -- confirmed directly by `test_normalizer_integration_acquisition.py`'s failure-atomicity checks (`unpublished_never_took_a_lease`, `corrupt_never_took_a_lease`, `stale_generation_never_took_a_lease`), each of which asserts the fake command object's lease/master_index-equivalent state was never partially set.

## 16. Confirmation: CPM untouched

No file under any Character Preset Manager path was read for editing or modified. This checkpoint's only functional edit is the one frozen Normalizer file named in Section 3.

## 17. Confirmation: hardened custom rebuild remains deferred

`tools/sfm_master_sidecar/mutex_publisher.py` was not touched this checkpoint (confirmed by `git diff --stat`). Its three hardcoded, machine/repository-path-bound constants and their documented "not yet an installed-release feature" disposition (recorded in the immediately-preceding Package-Boundary Targeted Correction) stand unchanged.

## 18. Confirmation: SFM was not launched

At no point in this checkpoint was Source Filmmaker started. All qualification in Sections 13-14 ran offline, against extracted/exec'd source, fake directory layouts, and real-but-isolated Python interpreters.

## 19. Known remaining limitations

1. **No automated publish step yet.** Nothing in this repository or checkpoint automatically compiles/publishes a `.sfmsidecar` + `manifest.json` into `<game>/usermod/cfg/sfm_shared_authority/` (the `shipped_root` this integration now expects). A real deployment must run the existing manual `tools/sfm_master_sidecar/cli.py` (or an equivalent future install step) against the real canonical Master before the integrated Normalizer can successfully acquire authority in production -- until that happens, every real invocation will fail closed with `SidecarMissing` (wrapped as `ProbeError`), never a silent TXT fallback, but also never a successful run.
2. **`sfm_master_sidecar` must also be deployed as a sibling package directory** under `.../ChadChan3D/`, per Section 9's discovered requirement -- this is not yet automated either.
3. **The real MAINMENU bootstrap entry seam is proven only by a faithful offline simulation** (a fake `sys.executable` plus real, byte-identical package copies), not by a real embedded SFM process actually loading this script at real menu-registration/execution time. This remains, honestly, a real-SFM qualification-matrix question, not something offline testing can close.
4. **A small, deliberately-accepted native-Master-protect gap remains**: the handle is released at the START of `run_target_transaction()`'s existing `finally:` block (undo-state restoration), but the method's SECOND `assert_master_stable()` call happens a few lines AFTER that `finally:` completes -- a tiny window with no native calls in it, covered only by the pre-existing SHA-256 stability check itself, not by the handle. Extending the handle's lifetime further would have required restructuring the method's existing nesting, which this checkpoint deliberately avoided (Section 6's own "do not build a large synthetic race framework" / "STOP rather than invent a broader locking system" guidance).
5. **`mutex_publisher.py`'s hardened custom/local-Master rebuild path remains non-portable and deferred**, unchanged from the prior checkpoint.
6. **Failed-batch-admission eviction remains deferred**, unchanged from the prior checkpoint.
7. **`parse_targeted_master()` remains defined but dead** at its old call site -- intentionally preserved, not cleaned up, per this checkpoint's narrow scope.
8. **W3 remains `UNKNOWN`**, carried forward unchanged from the whole prior arc.

## 20. Exact next real-SFM qualification work (not performed in this checkpoint)

Per the governing brief's Section 13, the next phase is the finite real-SFM qualification matrix:

- Selected Shots and All Shots command scopes;
- mixed-project inventory, exclusions, and untouched-peer preservation;
- baseline-vs-integrated scene preservation;
- Undo restoration;
- artist workflow where applicable;
- cold and warm acquisition;
- later-model vocabulary (a fold not present at an earlier acquisition);
- cancellation;
- generation replacement (the Master TXT changing between commands);
- authority transient/retained memory under real SFM;
- VAS (virtual address space) behavior;
- total latency/responsiveness;
- one decisive native protected-Master-handle test under real native Rebuild.

This report does not perform that phase. It is explicitly deferred, per Section 13's own instruction, to a future, separately-scoped task, after this checkpoint's own narrow independent review.

---

**PRODUCTION NORMALIZER INTEGRATION READY FOR NARROW INDEPENDENT REVIEW**
