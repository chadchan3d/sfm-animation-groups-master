# O3 — Resource/Lifetime Implications

**Status: DESIGN/PROOF ONLY.** No production, integration, or lifecycle code has been modified. Nothing
here authorizes an optimization.

## Relationship to the confirmed `capture_tree()` closure-cycle finding

O2's own offline test (`checkpoint_o2/test_capture_tree_closure_lifetime.py`, 9/9 PASS under the real
embedded Python 2.7.5) empirically confirmed `capture_tree()`'s own recursive `walk()` closure is
self-referential — its own closure cell keeps its own `groups`/`memberships` payload alive after the
caller's own `del()`, requiring `gc.collect()` (never called by production internally, per its own
module docstring) to actually release it. This is a **mechanism confirmed, materiality at real scale
still unresolved** finding (O2's own Required Conclusion #5).

`discover_rig_context()`'s own expensive operation, `reachable(scene)` (line 3329, def line 1006-1039),
is structurally **different**: it is an **iterative, stack-based** traversal (`stack = [start]` /
`while stack: ...`), not a recursive closure — it has no nested `def` closing over itself, and therefore
**no analogous self-referential-cycle mechanism**. Its cost is CPU time spent walking a large object
graph (`reachable_rig_count`/`reachable(scene)`'s own result list, capped at 50,000 elements), not
allocator-retention from an uncollected cycle.

**These are two independent redundancy sources, not one**: (a) `capture_tree()`'s own closure-cycle-driven
allocator retention (a *memory* concern, addressed conceptually in O1/O2's own findings, **unchanged by
either O3 candidate**); (b) `discover_rig_context()`'s own repeated full-scene-traversal CPU cost (a
*time* concern, measured `MATERIAL` in O2-R1, and the **only** thing either O3 candidate addresses).

## Per-question answers, for both O3 candidates

Both `O3_OUTER_POST_COMPOSER_BEFORE_DESIGN.md` (Design B) and `O3_TERMINAL_DISCOVERY_REUSE_DESIGN.md`
share the same answers below, since both propose the identical shape of change (skip a
`discover_rig_context()` call, keep the `capture_snapshot_explicit`/`capture_tree` call unchanged):

- **Does the proposed design reduce the number of `capture_tree()` invocations?** **No.** Both
  candidates keep the fresh semantic-tree capture for their own slot — only the *discovery* call
  preceding it is skipped. `capture_tree()`'s own invocation count is unchanged by either candidate.
- **Does it reduce only discovery calls while keeping capture count unchanged?** **Yes** — exactly this,
  for both candidates.
- **Does it change closure lifetime?** **No.** `capture_tree()` itself is untouched by either candidate;
  its own closure-cycle behavior (and whatever contribution it makes to allocator retention) is
  unaffected.
- **Does it reduce simultaneous collectible-cycle accumulation?** **No.** Since `capture_tree()`'s own
  call count is unchanged, the number of orphaned `walk` closures produced per command is unchanged.
  Neither candidate addresses the closure-cycle finding at all — that remains a separate, still-open
  question (O2's own Required Conclusion #5, materiality half).
- **Does it introduce any new retained live objects?** **No.** The proposed `DiscoveryIdentityToken`
  (`O3_MINIMAL_DISCOVERY_REUSE_OBJECT.md`) is small, plain Python data (a handful of ints/strings/one
  small set), explicitly scoped to a single target's own transaction, never stored on `self`, never
  persisted across the Qt-deferred inter-target boundary, and never shared between targets. It does not
  hold a live native reference (the two live-reference fields, `rig`/`registry`, are explicitly excluded
  from the token).

## Explicit constraints preserved

- **No forced `gc.collect()` scheduled as an optimization.** Neither candidate proposes any GC-timing
  change; this remains entirely orthogonal to the closure-cycle question.
- **No persistent rig cache created.** The token's lifetime is bounded to the interval between two
  specific capture calls within one target's own transaction — it is discarded, not retained, once that
  interval ends. It is not a cache in any sense that would outlive one target's own processing.
- **Reuse remains scoped to the smallest provably safe transaction lifetime.** Both candidates' own
  proven-safe intervals (`O3_DISCOVERY_CALL_MAP.md`) are the *only* scope in which reuse is proposed —
  neither candidate proposes carrying a token across a native Rebuild call, a composer-writes phase, a
  Qt-deferred boundary, a shot-activation boundary, or a target-re-resolution boundary.

## Summary

Neither O3 candidate touches the closure-cycle mechanism at all — they are additive, independent
improvements targeting a different (time, not memory) cost. If the closure-cycle question's own
materiality is later resolved as significant, that would motivate a **separate** design investigation
(likely targeting `capture_tree()` itself, or the pattern of calling it 3-5 times per target), not
something either O3 candidate here already covers or forecloses.
