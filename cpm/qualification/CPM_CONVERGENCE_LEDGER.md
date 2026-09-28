# Ledger

## Current milestone

CPM Convergence Step 2a (bounded part of handoff §22 step 2): CPM-owned canonical authority adapter,
offline qualification only. Done means: canonical bootstrap, provider-shaped facade
(`generation_descriptor`, `query_many`), migrated health, descriptor/provenance mapping,
expected-generation freshness and the Suite 1 snapshot/signature parity are all proven under Python 3
and 2.7.5, with no runnable CPM created or wired. Status: implemented and qualified; awaiting review.

## Current state

Base `2a5285e`. Step 2a adds `cpm/convergence/cpm_authority_adapter.py` and
`cpm/convergence/tests/test_cpm_authority_adapter.py`, plus this ledger. Frozen G18AN, the shared
package, the Normalizer snapshot, `tools/` and the canonical Master are unchanged. No runnable
CPM candidate exists; nothing is wired.

## Verified

- Bootstrap: `locate_mainmenu_dir()` equals the qualified Normalizer's
  `_authority_locate_mainmenu_dir()` (extracted verbatim from `audit_external_runtime/`, SHA
  `1f4ec5a2…`) and the package's `bootstrap.bootstrap_import_path()` for 4 executable fixtures.
  The adapter checks origin, module identity, API `1.0.0-b2a`, build
  `package-boundary-corrected-2026-09-22`, and gets the broker via `runtime.get_broker`
  (no second broker). Origin, API, build, identity and `get_broker` failures all fail closed.
- Health policy (R3 decision): healthy only when canonical bootstrap, admission, authorization,
  `cpm-compat-v1` contract, complete coherent coverage and exact interpretation all succeed. No
  whole-Master counts are used or fabricated.
  - A small valid Master (16 occurrences, 12 families) is **healthy**. G18AN's legacy gate would call
    it `master-too-small`.
  - Corrupt and stale sidecars (`acquisition-failed:SidecarMissing`) and Uncovered requests
    (`projection-invalid`) are **unavailable**.
  - MasterUnknown is genuine absence; conflict is not absence.
  - The many-unrecognized advisory never changes the status.
- Failure mapping covers:
  - revoked authorization;
  - wrong consumer or contract;
  - omitted, Uncovered or disagreeing coverage;
  - malformed payload;
  - interpretation failure;
  - view generation differs;
  - missing view;
  - lease refused;
  - lease-release failure (durably registered, then reconciled).

  All of these raise `CpmAuthorityUnavailable`, never absence.
- Freshness: same generation succeeds and a repeat is a full cache hit. A changed generation raises
  `CpmGenerationMismatch`, the pin never moves, and the new generation is verifiable only explicitly.
- Retention: no outstanding lease and no open provider after every operation. Adapter state is
  detached text/int only. Failure tracebacks hold no view or lease, and exceptions carry no context.
- Snapshot parity: G18AN `semantic_snapshot_from_live_vocabulary`, `semantic_snapshot_signature`,
  `prod_pure_semantic_row`, `semantic_snapshot_for_model_row(row, adapter)` and
  `p03_unmapped_relevant_controls` all give identical results fed by the adapter or by the oracle.
  The oracle is G18AN `_answer_from_result` via the real broker, plus hand-audited conflicts.
  Coverage: 17 literals, 19 bindings, every §20 case; counts and rows hand-audited.
- Signature values are interpreter-specific because G18AN hashes `repr()`: 2.7.5 `04e437b4…`,
  3.10 `7b63cbda…`. Adapter equals oracle within each interpreter.
- Python 3.10: 205/205. Python 2.7.5: 205/205. Digests identical (`02cf2200…`). Step 1 suite still
  196/196 on both.
- Sensitivity: 8 perturbations on scratch copies were each detected: Uncovered accepted,
  authorization omitted, wrong contract, lease not released, expected generation ignored, legacy
  threshold, match_kind changed, spelling order changed.

## Unresolved

- **Suite 1: PASS (offline).** Every §20 Suite 1 item is now proven on synthetic fixtures under both
  interpreters: unique, alias, exact/folded, duplicates, absence, conflict, wrapper paths, reuse,
  v1/v2 separation, snapshot/signature, and Fit warning parity. Real-SFM live-model parity (§21) and
  Suites 2–4 and gates C7–C10 remain open. No mutation or runtime claim is made.
- R3: **CLOSED**. Health = canonical admission plus requested-view validation; no whole-Master count
  mechanism (reviewer decision at Step 2a).
- R6 (late helpers reaching the global provider): open. No runtime route exists yet.
- R13 (location and form of the G18AN-derived runnable candidate): open. Decide before Step 2b.
- UI reaction to a stale scope (R1): unspecified; Step 2b.
- `verify_py27_equivalence.py` is not runnable as-is (stale fixtures, old Normalizer SHA). It was
  left unmodified; the two-interpreter digest technique is used instead.
- Negative fixtures surface as `SidecarMissing` (the selector rejects all candidates) rather than a
  more specific class. That is still fail-closed; recorded for Step 2b health messaging.

## Next

Await review. Then decide R13. Step 2b, limited to:

- a G18AN-derived runnable candidate;
- adapter injection into `render → prod_scope`;
- the migrated health predicate replacing the legacy count gate;
- rerouting `prod_current_provider_descriptor` and `prod_probe_semantic_provider`;
- stale-scope UI behavior;
- making the parity shortcut unreachable;
- the R6 fail-closed rule.

No Step 3/4, Stage M/F, K or L work.

Maintenance: Update at checkpoints. Replace stale entries; keep about one screen. Preserve unresolved issues. Verify relevant claims when resuming. Keep history in Git or an archive.
