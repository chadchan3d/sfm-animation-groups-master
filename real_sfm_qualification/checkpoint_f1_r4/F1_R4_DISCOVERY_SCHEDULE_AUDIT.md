# F1-R4 — Discovery-Call Schedule Audit

**Status: STATIC SOURCE AUDIT ONLY.** No production, integration, or lifecycle code has been modified.
This document independently re-derives, from the current accepted production Normalizer (SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`), the exact discovery-call schedule for
every branch a target can take, before any F1-R4 diagnostic code was written. It does not assume the
previously-cited "five discovery boundaries" figure without re-verifying it against current source.

## The five `capture_snapshot_explicit` call sites, each preceded by its own `discover_rig_context()` call — re-confirmed

```
line 5254   "PRODUCTION_SEMANTIC_FINGERPRINT"     (terminal, semantic_target_fingerprint())
line 7180   "PRODUCTION_GENERIC_COMPOSER_PRE"     (composer-before, production_generic_composer())
line 7529   "PRODUCTION_GENERIC_COMPOSER_POST"    (composer-after, production_generic_composer())
line 11267  "PRE"                                 (run_target_transaction())
line 11487  "NATIVE_POST"                         (run_target_transaction())
```

Re-confirmed by direct grep against the current pinned source -- exactly five `capture_snapshot_explicit(`
call sites exist in the entire file, each immediately preceded by its own `discover_rig_context()` call, as
in every prior checkpoint's own established finding. **F1-R4 reproduces only the `discover_rig_context()`
half of each site** -- never the accompanying `capture_snapshot_explicit()`/`capture_tree()` call -- per
explicit instruction ("do not perform semantic snapshot/tree capture... discard each discovery result
immediately after its corresponding site").

## Every `NativePostFallback` / `ContextualCompositionSuccess` raise site — re-confirmed (5 + 1)

Re-confirmed by direct grep: exactly five `raise NativePostFallback(...)` sites and one
`raise ContextualCompositionSuccess(...)` site in `run_target_transaction`/`production_generic_composer`:

| Line | Label | Condition | Discoveries completed by this point (PRE=1, NATIVE_POST=1, composer-before=1, composer-after=1) |
|---|---|---|---|
| 11478-11480 | `NATIVE_POST_ONLY_PRE_CAPTURE_UNSUPPORTED` | `not pre_capture_ok` (PRE's own `discover_rig_context()` or `capture_snapshot_explicit()` raised) | **PRE only (1)** -- fires *before* `post_rig = discover_rig_context(...)` (line 11482) is ever reached |
| 11520-11525 | `NATIVE_POST_ONLY_%s % pre["rig_status"]` (e.g. `_UNRIGGED`, `_AMBIGUOUS_MULTIPLE_RIGS`, `_AMBIGUOUS_RIG_REGISTRY`, `_STALE_ZERO_OWNERSHIP_RIG`) | `pre["rig_status"] != "SUPPORTED_ACTIVE_RIG"` | PRE + NATIVE_POST (2) -- fires *after* NATIVE_POST discovery |
| 11585-11587 | `NATIVE_POST_ONLY_DUPLICATE_SEMANTICS` | `post["duplicate_control_names"] or post["duplicate_sibling_groups"] or post["duplicate_direct_controls"] or post["duplicate_memberships"]` | PRE + NATIVE_POST (2) |
| 11689-11691 | `NATIVE_POST_POLICY_FALLBACK` | `plan["status"] != "AUTHORIZED"` (from `self.preflight_reconciliation_plan(pre, post, master, exact_pair)`) | PRE + NATIVE_POST (2) |
| 11732-11734 | `NATIVE_POST_WRAPPER_SURVIVED` | `find_direct_child(root, RIG_RECON_ROOT) is not None or find_direct_child(root, MASTER_RECON_ROOT) is not None` | PRE + NATIVE_POST (2) |
| 11974-11976 | `ContextualCompositionSuccess("RECONCILED")` | reached only if none of the above fired, `production_generic_composer(...)` completed without raising | PRE + NATIVE_POST + composer-before + composer-after (4) |

Two additional conditions raise a bare `ProbeError` (lines 11541-11543, 11553-11555, 11565-11567) rather
than a `NativePostFallback` -- these are **hard failures, not normal branches** (production would abort the
whole target transaction). They are not modeled as expected schedule entries; if F1-R4 ever detects the
equivalent condition it is logged as an anomaly, not a branch.

## Terminal discovery fires unconditionally on every target — re-confirmed

Re-traced `run_target_transaction`'s own body past the `try/except/finally` block (lines 12071-12132):
`semantic_target_fingerprint(shot, aset)` (line 12129, which itself calls `discover_rig_context()` then
`capture_snapshot_explicit(..., "PRODUCTION_SEMANTIC_FINGERPRINT", ...)`) is called **unconditionally**,
after `terminal_status` has already been set by either the `NativePostFallback` or
`ContextualCompositionSuccess` handler -- i.e. on every branch that doesn't hard-fail. **This adds exactly
one more discovery call to every branch's own total, regardless of which branch was taken.**

## Two additional semantic operations discovered this turn, both explicitly excluded from F1-R4

Re-tracing the same region (lines 12071-12174) surfaced two operations not previously itemized as separate
line items in this project's own discovery-call maps:

- `target_fingerprint = isolation_fingerprint(aset)` (line 12112-12116) -- a **separate**, non-rig tree-walk
  function (confirmed by direct reading, `isolation_fingerprint()` line 4555 onward: walks `arr(aset,
  "controls")` and the control-group tree directly; **does not call `discover_rig_context()` at all**). Not
  a sixth discovery site -- but a real semantic operation nonetheless.
- `self.verify_current_shot_peers(shot_record, target)` (line 12169) -- deeply verifies every OTHER
  animation set in the current shot against `self.session_expected` digests.

Both are explicitly named in this checkpoint's own "Critical constraint" list ("direct-target semantic
fingerprints"; "current-shot peer verification") and are **not performed by F1-R4** -- confirmed here
only to establish that skipping them does not silently also skip a discovery call, since neither one
contains one.

## Two branch conditions that cannot be evaluated without violating "no semantic tree capture" — disclosed, not silently approximated

Re-reading the comparison logic at lines 11494-11588 precisely: most of production's own PRE-vs-POST
comparisons operate on fields `discover_rig_context()` **already computes on its own bare return dict**
(re-confirmed by direct reading of `discover_rig_context()`'s own body, lines 3299-3436):
`status`, `rig_handle`, `owned_names_in_order` (equivalent to `capture_snapshot_explicit()`'s own
`owned_control_name_set` -- both are sorted views of the same rig-owned-handle-derived name list), and
`hidden_groups` are all present directly on the bare discovery result -- **F1-R4 can and does compare these
without ever calling `capture_snapshot_explicit()`/`capture_tree()`.**

Two conditions genuinely cannot be evaluated this way:

1. **`NATIVE_POST_ONLY_DUPLICATE_SEMANTICS`** depends on `post["duplicate_control_names"]` /
   `duplicate_sibling_groups"]` / `"duplicate_direct_controls"]` / `"duplicate_memberships"]` -- all four are
   populated only by `capture_tree(root)`, which F1-R4 never calls.
2. **`NATIVE_POST_POLICY_FALLBACK`** depends on `plan["status"]` from
   `self.preflight_reconciliation_plan(pre, post, master, exact_pair)`, which itself requires full
   `capture_snapshot_explicit()`-shaped `pre`/`post` dicts (`groups`, `memberships`, etc.) -- not the bare
   discovery dict.

**F1-R4's disclosed handling**: both checks are explicitly skipped (never evaluated, never faked), each
target's own report records `duplicate_semantics_check_skipped=True` and `policy_fallback_check_skipped=
True` unconditionally, and the schedule proceeds as though neither condition would have fired (i.e., toward
`NATIVE_POST_WRAPPER_SURVIVED` and then the composer-entry path) rather than guessing. This is a
conservative bias in one direction only: if a real target's true branch was actually
`NATIVE_POST_ONLY_DUPLICATE_SEMANTICS` or `NATIVE_POST_POLICY_FALLBACK` (each a 3-discovery branch),
F1-R4 would instead run the composer-entry path for it (5 discoveries) -- **strictly more** fresh-discovery
work than production's own true branch would have required for that target, never less. This cannot cause
F1-R4 to *understate* the contextual layer's own discovery cost; it can only, in this one narrow and
disclosed respect, slightly overstate it for any target actually on one of these two branches. Since all 62
targets in the real F1-R2 run reached `FINAL_REPORT_ENTRY` successfully (no hard failure), this approximation
does not risk mischaracterizing any target as failed.

## `NATIVE_POST_WRAPPER_SURVIVED`: reused directly, no approximation needed

`find_direct_child(root, RIG_RECON_ROOT)` / `find_direct_child(root, MASTER_RECON_ROOT)` (constants
`"__RIG_VISIBLE_RECON__"` / `"__MASTER_VISIBLE_RECON__"`) is a bounded, two-lookup existence check over
`children(parent)` -- not a recursive tree-walk, not a semantic capture, not excluded by the constraint
list. F1-R4 reuses this exact check, unmodified, via the already-qualified module-level `find_direct_child`
function.

## Final derived schedule (per branch, discovery-call count and order)

| Branch | Discovery calls, in order | Count |
|---|---|---|
| PRE capture unsupported | PRE | 2 (PRE + terminal) |
| PRE rig-status not supported-active-rig | PRE, NATIVE_POST | 3 (+ terminal) |
| NATIVE_POST_WRAPPER_SURVIVED | PRE, NATIVE_POST | 3 (+ terminal) |
| Composer-entry path (reconciled, or either undeterminable branch treated as pass-through) | PRE, NATIVE_POST, composer-before, composer-after | 5 (+ terminal) |

No branch schedule is assumed to be "three" or any other figure without this derivation -- every entry
above is grounded in a specific, cited source line.

## Using the F1-R2 real log to establish the actual branch per target

This checkpoint's own diagnostic does **not** have access to a preserved F1-R2 production log file (none
was returned/committed to this repository as a raw artifact -- only the summarized final numbers were
relayed). F1-R4's own design does not depend on having that log: it determines each target's own branch
**dynamically, at runtime**, using the exact same live comparisons described above, and reports the branch
it observed for every target in its own output (`branch` field per target, plus aggregate `branch_counts`).
This is the only way to produce a genuinely-matched, non-assumed schedule without that external log file,
and it produces a strictly more direct measurement (branch determined by the same live discovery data
production itself would have used) than trusting a pre-declared schedule would.
