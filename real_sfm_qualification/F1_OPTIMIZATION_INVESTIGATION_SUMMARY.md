# F1 Optimization Investigation — Summary (F1-R2 through F1-R8)

This closes the F1 optimization-search branch opened after `F1-1`'s real SFM process crash during
repeated-command stress testing. Every checkpoint below was a real-SFM-verified, machine-derived
measurement or a static/empirical binding characterization — never a proposal accepted on its own
narrative. See `LEDGER.md` for the exact per-checkpoint evidence this summary draws from.

## The search, in order

- **F1-1 / F1-2 (repeated/warm-use stability, pre-F1-R series)**: four consecutive real commands
  (Selected×2, All×2) in one continuous SFM process. `F1-1` **FAILED**: the real SFM process crashed
  during command 3. `F1-2`'s corrected harness still did not reach a clean, fully-verified command 4.
  This is the original, real, observed failure mode that opened this branch.
- **F1-R1 (diagnostic attribution)**: a real production Selected command, run a second time in the same
  process, itself showed **zero** retained private/VAS growth — the harness's own post-command semantic
  verification was shown to materially consume retained address space. This first separated "the
  harness's own measurement overhead" from "production's own retained cost," a distinction every later
  checkpoint preserved.
- **F1-R2**: per-run process-retained pressure established as real and repeatable; the hypothesis that
  serialized-scene size/content dominates the retained cost was tested and **rejected** — the retained
  cost is not primarily a function of how large the serialized scene is.
- **F1-R3**: isolated native Rebuild alone (no discovery). Native Rebuild's own resource retention is
  small relative to full production — native Rebuild is **not** the principal memory/VAS owner.
- **F1-R4**: isolated fresh `discover_rig_context()` calls at the real, source-derived per-branch call
  schedule (250 calls across 62 targets: 32×5 + 30×3). Fresh discovery reproduces the large majority of
  the full command's own retained private growth and free-VAS loss — **discovery-dominant**.
- **F1-R5**: decomposed discovery further into its own traversal/materialization component (isolated,
  repeated `reachable(scene)` calls) versus the rest of discovery. Even after reducing 126 of the 250
  full discovery sites to isolated traversal-only calls, ~92% of discovery-associated private growth and
  ~96% of discovery-associated free-VAS loss remained — **traversal/materialization-dominant**. This
  pointed squarely at `reachable()`'s own whole-scene walk (and whatever it retains/touches) as the
  actionable target, not at composer/classification logic downstream of it.
- **F1-R6**: designed, offline-qualified (205/205 adversarial parity, zero mismatches), and real-SFM-ran
  a streaming candidate that eliminates `reachable()`'s own large returned Python list while preserving
  exact legacy semantics (proven: 62/62 real-target semantic parity, zero mismatches). Real resource
  result: only 5.67% private / 6.49% working-set reduction, free-VAS actually **worse** by 5 MiB, ~4.36%
  **slower**. **Conclusion: semantics-preserving list-elimination alone provides no material command-scale
  resource benefit.** The large Python list itself is cleared as the dominant cause; the remaining cost
  lives in work preserved by both implementations — traversal itself and/or per-element DME/SWIG
  wrapper/reference activity.
- **F1-R7**: static audit of the real, installed SWIG datamodel bindings for a genuinely lower-level
  traversal/lookup mechanism (not another Python-side list/generator rewrite). Found and evaluated every
  materially relevant real API in the binding surface. `FirstAttributeReferencingElement`/
  `NextAttributeReferencingElement` is real, complete, and has a zero-wrapper-per-step profile, but is a
  **reverse**-reference lookup — structurally unable to replace the **forward** whole-scene search this
  algorithm needs, regardless of its own efficiency. `FirstAllocatedElement`/`NextAllocatedElement` has
  the cheapest raw profile found but is scoped to the whole datamodel/process, not to scene-reachability
  — wrong scope, real false-positive risk. `CElementTreeTraversal` was the **only** mechanism left open as
  a genuine `MEASUREMENT_CANDIDATE`, blocked by two questions no available evidence in this SFM install
  could resolve statically: whether `pAttrName` can cover every element-reference attribute, and whether
  its dedup is global or merely path-local.
- **F1-R8**: resolved those two questions empirically, against a small, detached, native DME graph (never
  attached to the open session, never saved), comparing legacy's own extracted `reachable()` against the
  real `CElementTreeTraversal` class. Real result: on the multi-attribute graph, every tested `pAttrName`
  value (`"attr_A"`, `"attr_B"`, `"attr_list"`, `""`) produced the identical single-element sequence,
  never reaching legacy's own 7-unique-handle full reachability — **no single call reproduces complete
  forward reachability**. On the shared-reference DAG, native emitted the shared node twice where legacy
  deduplicated it to once — **no global dedup**. On the cycle graph, native never terminated, cycling the
  same 3 handles until the 2000-step watchdog aborted it — **`NO_SAFE_DEDUP`**, a materially worse and
  unsafe behavior compared to legacy's own clean 3-handle termination. **Final classification:
  `SEMANTICALLY_INSUFFICIENT`.**

## Conclusion

**No further evidence-supported material optimization candidate exists in the current SFM Python/
datamodel surface without functional compromise.**

This is an empirical engineering conclusion, reached by exhausting every real, available lower-level
binding mechanism this SFM install actually exposes (audited and, where genuinely promising, empirically
tested against real native behavior) — it is **not** a proof that no imaginable engine-level
implementation could ever improve this. Do not pursue: `CElementTreeTraversal` wrappers layered with
manual per-attribute enumeration or manual dedup (this reintroduces exactly the wrapper-construction and
whole-traversal-state work the optimization search set out to remove); generator/list micro-variants of
the existing traversal (F1-R6 already showed list elimination alone is not material); stale discovery
reuse, topology caching, or reduced ambiguity checking (O3 remains closed for correctness reasons
independent of this search); narrowed model support (would silently regress supported categories).

Production is unchanged throughout this entire investigation (F1-R2 through F1-R8). No optimization was
implemented or authorized. This closes the search; it does not by itself close `F` — see
`F1_FINAL_DISPOSITION_REVIEW.md` for the prepared, not-yet-acted-on review of whether the originally
observed repeated-use behavior actually blocks release, given everything now established.
