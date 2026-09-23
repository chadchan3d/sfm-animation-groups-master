# O2-R1 Narrow Static Proof: Outer Native POST → Composer-Before Capture

Read-only source analysis of `Rebuild_Control_Groups_Normalizer.py` (production Normalizer, SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`), reconciled supported-active-rig
path only. This does **not** authorize reuse of any code — proof-gathering only, feeding a decision made
elsewhere. Corroborating context (not proof): O2's real-SFM run found the outer POST and composer-before
captures produce hash-equivalent results (both aggregate and per-field) for Fox and Mia, both commands.

## Interval traced

From the outer native POST capture completing (`run_target_transaction`, line ~11482-11492) through to
the composer-before capture being invoked (inside `production_generic_composer`, line ~7175-7185).

## Itemized trace

| Region | Lines | Classification |
|---|---|---|
| Dict comparisons on already-captured `pre`/`post` data: control-order, rig-status, rig-identity, owned-control-set, hidden-groups, duplicate checks | 11494-11587 | Pure read-only; each either passes or raises `ProbeError`/`NativePostFallback` (fallback branch point, not a mutation) |
| Python-only counter increments (`self.total_*`) | 11515-11891 | Plain attribute writes on `self` — not DME |
| `wanted_folds = set([ascii_fold(...) for ...])` | 11589-11597 | Pure string computation over already-captured data |
| `self.contextualizer_validate_master_index_subset(wanted_folds, "TARGET")` | 11601 | Validates against `self.master_index`, source-documented "Pure Python only; no DME refs" |
| `plan = self.preflight_reconciliation_plan(pre, post, master, exact_pair)` | 10683-10819 | Takes only already-captured dicts/pure-Python data; exhaustively grepped for every DME-write-capable call (`SetValue`, `AddChild`, `RemoveChild`, `SetAttribute`) — none found in this function's range |
| `uniformity_plan = derive_generic_uniformity_plan(pre, post, master, plan)` | 5767-6347 | Same input constraints, same exhaustive-grep result — no write-capable calls found |
| `self.get_root_group(aset)`, `live_control_map(aset)` | 11714, 11737 | Getters/reads, not writes |
| Extensive `self.log(...)` calls | throughout | File I/O only |
| Composer-before capture invoked | ~7175-7185 | The boundary this proof traces to |

## Decisive corroborating trace: where the file's DME-mutating primitives actually live

The file's only DME-mutating primitives (`set_visible`/`set_selectable`/`set_group_color`/`SetValue` at
line 2097; `create_independent_group`/`AddChild` at line 2226; `production_reorder_children_by_master`/
`AddChild`+`RemoveChild` at lines 6851-6890) are called **exclusively** from
`production_reorder_contextual_tree` (line 6932) and directly inside `production_generic_composer`
itself (call sites at lines 7205, 7222, 7239, 7293, 7391, 7513, 7519) — **all of which sit after**
composer's own before-capture (~7175-7185) and around its own after-capture (~7524-7534). None of these
mutation call sites exist anywhere in the 11492-11897 interval, nor inside `preflight_reconciliation_plan`
or `derive_generic_uniformity_plan`.

**No Qt event-loop yield in this interval**: every `QTimer.singleShot` call site (lines 12556, 12646,
12758) is well after both captures in question; no `processEvents`/`singleShot` call exists in
11492-11897.

**The single native Rebuild call** (`self.rebuild(...)`, line 11464) occurs *before* the outer POST
capture (11487-11492) — by construction, no second native mutation can occur later in this interval.

## Answers

**1. Explicit DME write in the interval?**
No — exhaustively confirmed by whole-file grep for every write-capable primitive; the only write-capable
calls found anywhere in the file are downstream, inside the composer's own post-before-capture mutation
phase.

**2. Native Rebuild or other native mutation in the interval?**
No — the one native call already happened before the outer POST capture.

**3. Qt event-loop yield in the interval?**
No — no `processEvents`/`singleShot` calls exist before line 12556, well after this interval.

**4. Any operation that could legitimately change the semantic tree being captured?**
No — every operation in the interval reads already-captured data or increments Python-only counters;
`get_root_group`/`live_control_map` are reads.

**5. Exceptions composer-before could raise that outer POST could not already have raised?**
None — composer-before calls the identical `capture_snapshot_explicit`/`capture_tree`/
`discover_rig_context` code path on the same `(shot, aset)` pair, against state nothing in the interval
touched. Whatever exception class outer POST could raise, composer-before could raise identically,
under identical conditions.

**6. Additional validation composer-before performs that outer POST does not?**
None — same function, same code path, no wrapping or post-processing differentiates the two calls.

## Mechanical conclusion

**`SOURCE_EQUIVALENCE_SUPPORTED`** — for the reconciled supported-active-rig path, every intervening
operation between the outer native POST capture and the composer-before capture is either a pure read of
already-captured data, a Python-only counter/log side effect, or a call into functions exhaustively
confirmed to contain no DME-mutation, no native-mutation, and no Qt-yield call sites.

Unlike the composer-after→terminal interval (see `O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`), this
interval contains **no distinct procedural validation step** analogous to the undo-restore/
protect-release/Master-stability-reassert sequence — the interval is comparison/planning logic only,
with the actual mutation-capable code confirmed to live entirely downstream of composer-before's own
capture. This makes the outer-POST/composer-before pair a structurally cleaner equivalence than the
composer-after/terminal pair.

This is proof-gathering only; no reuse is authorized by this document.
