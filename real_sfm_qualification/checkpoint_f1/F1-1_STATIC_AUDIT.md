# F1-1 Static Object-Lifetime / Reachability Audit

Performed per explicit instruction after the F1-1 SFM crash (command 3, All Shots,
target_seq 52, `PRE_NATIVE`). This is a read-only audit. **No production file and no
F1 harness file was modified while performing this audit.**

Scope: every large-object category the governing instruction listed, covering both
the F1 harness (`Checkpoint_F1_Repeated_Warm_Use_Stability.py`, deployed SHA-256
`d2af8cc6ac6eb2ed69fc5fae886ab715be8b79f3860274cd7f836aa874cd4ec6`) and the
production invocation lifecycle it repeatedly executes
(`Rebuild_Control_Groups_Normalizer.py`, accepted SHA-256
`cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867`).

For each item: **owner**, **lifetime intended**, **reachable after one command?**,
**why**.

## 1. Per-command `exec` globals (`prod_ns`)

- **Owner**: the F1 `for` loop, one fresh `{}` per iteration
  (`prod_ns = {}` at loop top; `exec(compile(production_source, ...), prod_ns)`).
- **Lifetime intended**: one command only.
- **Reachable after one command?**: **NOT via any name in F1's own script** — the
  next loop iteration reassigns `prod_ns = {}` before the old dict is used again,
  and F1 never stores `prod_ns` itself (or the `authority_runtime` module object
  bound inside it) into `report` or any longer-lived structure — confirmed by
  direct grep: every value F1 extracts from inside `prod_ns` (e.g.
  `authority_runtime.RUNTIME_API_VERSION`, `broker.provider_counters()`) is a
  small scalar/dict copy, never a reference back into `prod_ns` itself.
- **Why this is still a real concern**: reassignment only guarantees CPython's
  **refcounting** GC frees *acyclic* garbage immediately. `prod_ns` holds the
  **entire freshly-`exec`'d production Normalizer namespace** — every class and
  function the ~340KB production source defines, plus whatever instances/
  closures/bound-method callbacks its own top-level code and Qt-driven execution
  create. Bound-method-as-attribute and Qt-signal-connection patterns are classic
  **reference cycles**, which refcounting alone cannot free — only the cyclic
  collector (`gc.collect()`, or its automatic threshold-triggered runs) can.
- **Finding**: F1's own script calls `gc.collect()` **exactly once**, in its
  finalize section, **after all 4 commands complete** — never between commands.
  Production's own module docstring (`Rebuild_Control_Groups_Normalizer.py` line
  43) explicitly states **"no gc.collect()"** is used internally, by design.
  Therefore nothing in this pipeline reclaims cyclic garbage from one command's
  `prod_ns` before the next command begins, except CPython's automatic
  generation-threshold collection, which is not guaranteed to fire before the
  next command's own allocations start. Empirically confirmed under the real
  embedded Python 2.7.5 (see `test_gc_cycle_accumulation_across_exec.py`,
  below): 4 exec-created cycles, no interim collection, all 4 remain
  simultaneously alive until one final `gc.collect()` reclaims 52 objects; the
  same 4 iterations with `gc.collect()` after each one never accumulate (0
  alive at any point). **This is the single most concrete, actionable
  harness-side finding of this audit.**

## 2. Normalizer application/controller object (`RebuildControlGroupsProductionRun`)

- **Owner**: a local variable (`run`) inside production's own
  `StartRebuildControlGroups()`, which itself lives inside `prod_ns`.
- **Lifetime intended**: for the full duration of that command's async,
  Qt-timer-driven multi-target processing.
- **Reachable after one command?**: **Not directly observable from outside
  production without new instrumentation**, which the governing brief forbids
  adding. It is *necessarily* kept alive during the run via Qt
  callback/timer/signal references (otherwise the run could not complete
  asynchronously). Whether every one of those references (in particular, any
  Qt signal/slot **connections** that were made but never explicitly
  disconnected) is released once the command's own `final_report()` /
  run-lock-removal signals completion is production's own internal behavior,
  not something this audit can assert either way from outside.
- **Why**: this is exactly the ambiguity the F1-R1 diagnostic (Outcome A vs. B
  vs. C) is designed to help attribute, not something this static audit can
  resolve by reading source alone without executing it under real Qt.

## 3. Qt callbacks / timers / closures / deferred callbacks

- **F1's own closures** (e.g. `normalizer_run_is_active()`, redefined fresh
  each loop iteration to poll for the run-lock object's removal): plain
  functions closing only over `run_lock_name`/`main_window`, no `self`-cycles,
  no custom `__del__`. Become unreachable once the next iteration rebinds the
  name; freed by ordinary refcounting. **Low risk.**
- **Production's own Qt objects** (timers, signal connections it creates
  internally): same reasoning and same caveat as item 2 — governed by
  production's own cleanup discipline, outside this audit's ability to assert
  without new instrumentation.

## 4. Target inventories (`eligible_targets_of_interest`, etc.)

- **Owner**: main script scope, built once before the loop.
- **Lifetime intended**: entire script (read every iteration, never rebuilt).
- **Reachable after one command?**: yes, intentionally — same object every
  iteration, never grows. 85 short tuples; trivial size. **Not a concern.**

## 5. Semantic fingerprint raw trees / PRE / POST fingerprint dicts / per-target raw fingerprints

- **Owner**: loop-local `raw_eligible` / `raw_excluded`, reassigned via
  `capture_all(...)` fresh each iteration.
- **Lifetime intended**: transient — long enough to compute
  `compute_target_hashes()` / the aggregate hash, then released.
- **Reachable after one command?**: **No** — confirmed by direct grep that
  `del raw_eligible, raw_excluded` (or equivalent) executes in the same
  iteration, immediately after the hash computation that consumes them, before
  the next capture. These are plain dicts/lists/strings returned by
  `capture_snapshot_explicit_fn` with native handles already stripped by
  `canonicalize_snapshot()` **before** they are ever stored into the returned
  dict (confirmed by re-reading `capture_all()`'s per-target loop: the raw
  `snap` dict is canonicalized in the same expression that stores it into
  `result`). No reference cycles are plausible in plain data structures like
  these. **Genuinely low risk, verified by reachability, not merely by
  `del` intent.**

## 6. Excluded witness raw rows

- Same as item 5 (`raw_excluded`), and smaller (78 targets, no native handles
  retained). **Low risk.**

## 7. D1 / D2 manifest objects

- **N/A for F1.** Confirmed by grep: F1 never loads `d1_comparison_manifest.json`
  or any D1/D2 manifest object. F1 compares directly against pinned hash
  constants (`EXPECTED_INITIAL_PRE_HASH`, etc.), not a loaded manifest file.

## 8. Authority broker / view references

- **Owner**: `authority_runtime.get_broker(...)` returns the **same
  process-wide singleton** broker object every call (confirmed via source
  reading in the D2 phase of this project) — F1's own local name `broker` is
  reassigned to the identical object each iteration, not a growing chain.
- **Reachable after one command?**: the singleton itself persists by design
  (process lifetime), which is correct and intended. F1 only performs
  read-only queries against it (`provider_counters()`,
  `outstanding_lease_count()`) — confirmed idempotent, no new
  view/lease/provider is opened by these calls themselves.
- **Why this is not a harness concern**: the broker's own internal state
  (view cache, ledger) is bounded by production's own already-qualified
  `resource_estimator.py` / `resource_preflight.py` envelopes
  (historical authority: ≤16 MiB retained / ≤32 MiB transient), not by
  anything F1 controls.

## 9. Scoped `master_index`

- **Owner**: production's own `RebuildControlGroupsProductionRun` instance
  (`self.master_index`), released via
  `self._release_master_index_lease_durable()` (confirmed present at line
  9674 / called from `final_report()`'s own cleanup path at line 13326).
- F1 never holds a reference to this. **Production's own responsibility,
  outside harness scope.**

## 10. Session / isolation baselines, native-handle objects, log/parser data

- **Session/isolation baselines** and **native-handle objects**: entirely
  production-internal (native Rebuild call, guarded by the already-qualified
  native-protection gates); F1 holds no reference to either.
- **Log/parser data**: F1 reads `NORMALIZER_LOG_PATH` fresh each command
  (`open(..., "rb")`, read full bytes, extract two boolean markers), then
  `del`s the raw bytes/text promptly. Bounded to one command's log size
  (~300–400 KB observed). **Low risk**, though F1-R1 will hold the log text
  slightly longer to parse the full `CONTEXTUALIZER_RESOURCE_CHECKPOINT`
  series — still bounded to one command's log, no accumulation across
  commands since the production log is truncated (`"w"` mode) by every new
  command.

## 11. F1 command-record accumulation (`report["command_records"]`)

- **Owner**: main script scope; intentionally growing list, one entry
  appended per command (4 total), each holding compact **hash maps only**
  (85 + 78 entries of hex strings), not raw fingerprints.
- **Reachable after one command?**: yes — **intentionally**, this is the
  final evidence artifact's own content, not a leak.
- **Why this is not a plausible crash contributor**: total size is tens of
  KB across all 4 records combined, several orders of magnitude below the
  ~3.45 GB process working set observed at crash time. Noted for
  completeness, not flagged as a risk.

## 12. Exception / traceback references

- `except Exception as exc: anomaly(traceback.format_exc())` — `format_exc()`
  returns a **string** (safe to retain), appended to a small `ANOMALIES` list.
  This path did not execute on commands 1–2 (both apparently completed, per
  the preserved log showing command 3 already in progress) and is not
  implicated in the crash. Python 2's `sys.exc_info()` frame-retention risk is
  a real general hazard, but F1 does not hold `sys.exc_info()` tuples or raw
  traceback objects anywhere — only the formatted string. **Low risk.**

## 13. `sys.modules` import caching (`sfm_master_authority_productionized`, `sfm_master_sidecar`)

- **Owner**: process-wide `sys.modules` cache, populated on the **first**
  command's `exec()` (which runs `from sfm_master_authority_productionized
  import runtime as authority_runtime`), and **reused** (not re-imported) on
  every subsequent command's `exec()`, since Python's import cache is
  process-wide, independent of any one `exec()` namespace.
- **Reachable after one command?**: yes, by design — this is the single
  shared singleton (`_state`, `_broker` module-level state) that makes
  per-command provider/lease **delta** tracking meaningful in the first
  place. **Not a leak — this is the intended architecture.** Does not grow
  per command (same module object every time).

## 14. Any global/module-level reference retained by executing the production file repeatedly

- Reduces to items 1 and 2 above: the dominant candidate mechanisms are (a)
  reference-cycle garbage inside each command's own fresh `prod_ns` namespace,
  not reclaimed between commands because `gc.collect()` is called only once
  at the very end (**concrete, harness-side, fixed in F1-R1**); and (b)
  whatever production's own Qt-callback/signal cleanup does or does not
  release once a command's `final_report()` completes (**not directly
  observable without new instrumentation; this is what F1-R1's
  attribution experiment is for**).

## Offline empirical test

`test_gc_cycle_accumulation_across_exec.py` (SHA-256
`a7dbaa8fa290e57f457a7df88858ff57daee0db82ab913a5ca7db5a2135dbd3f`, run under
the real embedded Python 2.7.5, 32-bit — the same interpreter build SFM
itself embeds) proves
the general mechanism, using a synthetic stand-in (a class whose bound
method is stored as its own attribute — a common shape for callback/handler
objects, not a claim about production's exact internal object graph):

```
Case A: no gc.collect() between iterations (F1-1's actual pattern)
  nodes_alive_before_any_collect = 4         (all 4 iterations' cycles alive simultaneously)
  objects_reclaimed_by_single_final_collect = 52
  nodes_alive_after_final_collect = 0
  ACCUMULATION_PROVED = True

Case B: gc.collect() after every iteration (the F1-R1 fix)
  max_nodes_alive_at_any_point_during_run = 0
  nodes_alive_after_run = 0
  NO_ACCUMULATION_PROVED = True

OVERALL_TEST_PASS = True
```

This demonstrates the mechanism is real under the actual interpreter F1 runs
under. It does **not** by itself prove this mechanism materially caused the
F1-1 crash (production's own per-command Qt/native retention, item 2 above,
remains a live alternative/contributing hypothesis) — that attribution is
exactly what Checkpoint F1-R1 is designed to help resolve.

## Summary

| Category | Reachable after 1 command? | Risk assessed |
|---|---|---|
| `prod_ns` (exec globals) | Not via any F1 name; **cyclic garbage may survive** absent `gc.collect()` | **Concrete finding — fixed in F1-R1** |
| Production controller object / Qt callbacks | Not independently observable | Open — F1-R1 attribution target |
| Target inventories | Yes (intentional, static, trivial) | None |
| Raw fingerprint dicts (eligible/excluded) | No (verified `del` before next capture, no cycles possible) | None |
| D1/D2 manifests | N/A (not used by F1) | None |
| Authority broker/view singleton | Yes (intentional, bounded by production's own envelopes) | None (harness-side) |
| `master_index` | N/A (production-internal, not held by F1) | None (harness-side) |
| Session baselines / native handles | N/A (production-internal) | None (harness-side) |
| Log/parser data | No (bounded, `del`ed promptly) | None |
| `report["command_records"]` | Yes (intentional; tens of KB total) | None |
| Exception/traceback strings | Bounded, string-only | None |
| `sys.modules` singleton | Yes (intentional architecture) | None |

**Conclusion**: this audit identifies exactly one concrete, fixable,
harness-side deficiency — absence of `gc.collect()` between commands,
allowing exec-created reference cycles to accumulate for up to 3 full
command-cycles before the next `gc.collect()` (which never ran until after
all 4 commands) — and confirms every other harness-owned large object is
either provably released by reachability or is a small, intentional,
non-growing artifact. It explicitly leaves open, as production-internal and
not resolvable by static reading alone, whether the production controller
object's own Qt-callback/signal lifecycle also retains references across
command boundaries. Per the governing instruction, this audit **does not
claim root cause** and **does not modify production**. Checkpoint F1-R1
(prepared separately) is designed to empirically separate these two
hypotheses.
