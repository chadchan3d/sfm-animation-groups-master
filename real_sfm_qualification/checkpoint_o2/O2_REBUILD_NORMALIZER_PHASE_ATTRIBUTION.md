# O2 — Bounded Rebuild + Normalizer Phase Attribution

**Status: O2 — BOUNDED PHASE ATTRIBUTION — PASS WITH NATIVE-INSTRUMENTATION GAP.** The real-SFM bounded
run completed and produced real, materially useful findings (below). One instrumentation seam --
native-Rebuild call timing -- failed (`native_rebuild_stage_summary.call_count = 0` despite the
production log independently proving native Rebuild ran twice and returned PASS both times). Root cause
found and corrected under Checkpoint O2-R1 (`real_sfm_qualification/checkpoint_o2_r1/`), which also adds
two narrow static proofs the real run's equivalence witnesses motivated. No production, integration, or
lifecycle code has been modified. Nothing here authorizes an optimization.

## Real-SFM findings (preserved, from the actual completed run)

| Stage | Fresh Selected | Already-normalized Selected | Disposition |
|---|---|---|---|
| Whole-shot/rig discovery | 10 calls, total ~1.538s, mean ~0.154s | 10 calls, total ~1.545s, mean ~0.155s | **MATERIAL** |
| Tree construction | 10 calls, total ~0.020s | 10 calls, total ~0.023s | **IMMATERIAL** (not pursued as standalone) |
| Composer-before witness (Fox+Mia) | `EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION`, no semantic field differences vs. outer native POST | same | **DESIGN REVIEW JUSTIFIED — VALIDATION/FRESHNESS PROOF STILL REQUIRED** |
| Composer-after → terminal witness (Fox+Mia) | `EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION` | same | **DESIGN REVIEW JUSTIFIED FOR RECONCILED PATH ONLY** — not generalized to native-only fallback |
| Native Rebuild timing | **instrumentation gap** — call_count recorded as 0 | same gap | Corrected under O2-R1 |

**Warm second run** (already-normalized Selected) still required substantial contextual reconstruction
after native Rebuild — Fox: desired 74 / moved 72 / already_correct 2; Mia: desired 69 / moved 67 /
already_correct 2. This is preserved as **expected Rebuild→Normalizer behavior**, not a bug or
redundancy by itself: native Rebuild and the Normalizer's own contextual composer are a single
end-to-end transaction, and the Normalizer is what normalizes the state native Rebuild produces every
time, warm or not.

Both narrow static proofs motivated by these witnesses are now complete:
- `real_sfm_qualification/checkpoint_o2_r1/O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md` —
  `SOURCE_EQUIVALENCE_SUPPORTED` (reconciled path).
- `real_sfm_qualification/checkpoint_o2_r1/O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md` —
  `RECONCILED_PATH_REUSE_PLAUSIBLE` (reconciled path only; terminal retains a distinct procedural
  purpose beyond content-equivalence — see that document).

## Governing rule

> Tangible savings, demonstrated redundancy, zero functional compromise.

## Why O2 exists

Astra's independent adversarial review of O1 disposed O1's three candidates as:

| O1 candidate | Astra disposition |
|---|---|
| `self.work`'s stored `aset` wrapper | **LOW-VALUE / REJECT** — no ablation experiment built |
| Repeated semantic captures | **STRONG MEASUREMENT CANDIDATE** — but not every capture is redundant; specific areas flagged (composer-before capture; reconciled-path composer-after↔terminal overlap; repeated shot-graph/rig discovery) |
| Zero-repair-row / warm-path early-out | **UNSAFE DIRECTION** — do not pursue, no shortcut predicate designed |

Astra additionally flagged, as measurement questions only: repeated shot-reachable DME discovery inside
major snapshot boundaries; `capture_tree()`'s own recursive closure cycle retaining semantic output
containers until cyclic collection; and unresolved native Rebuild / shot-activation / composer
contribution.

O2 attributes cost in the smallest representative real-SFM workload that can answer these questions —
without another broad All-Shots campaign and without pursuing the rejected/unsafe candidates.

## Measurement scope (bounded, as required)

- **Primary case**: the established `shot3` fixture, Selected Shots scope, targets Fox
  (`foxmccouldwm1`) and Mia (`mia1`) — both already-qualified identities from every earlier checkpoint.
  Command 1 runs from fresh (unnormalized) state; command 2 runs the identical Selected-Shots scope
  again, now against the already-normalized Fox/Mia — in the same continuous SFM process.
- **No All-Shots command.** No whole-fixture campaign. No F1-R2 execution.
- Branch coverage: whether Fox/Mia's own real transaction takes the "reconciled" path or the
  "native-only fallback" path is discovered EMPIRICALLY by this run, not assumed — see "Branch truth"
  below. If both targets take the same branch in this run, branch coverage for the other path remains
  unresolved and is explicitly reported as such, per the instruction not to expand scope merely for
  completeness.

## Instrumentation design (strictly observational)

Deployed script: `Checkpoint_O2_Bounded_Phase_Attribution.py`
SHA-256: `4eaa8e87356e65c127a8744949e956056b0a18f5a2e65907efd3430e8dd9c4fc`

This script never edits `Rebuild_Control_Groups_Normalizer.py`. It `exec()`s the pinned, SHA-256
verified production bytes into a fresh namespace (the same technique every earlier checkpoint in this
project already uses) and then monkey-patches exactly **five** call points in that IN-MEMORY namespace
only, each wrapper calling the ORIGINAL function/method with the SAME arguments and returning its SAME,
unmodified return value — only recording timing/identity/compact-hash metadata:

1. `discover_rig_context(shot, aset)` (module function) — records elapsed time and the two
   already-cheaply-available counts its own return value carries: `reachable_rig_count`,
   `matching_rig_count` (confirmed via direct source reading, line 3346-3347 of the production file —
   no additional traversal is performed by the wrapper itself).
2. `capture_tree(root)` (module function) — records elapsed time and `group_count`, membership count,
   and duplicate-diagnostic counts, all read directly from its own already-computed return value.
3. `capture_snapshot_explicit(shot, aset, label, rig_context=None)` (module function) — records label,
   target, elapsed time, and a canonicalized (handle-fields stripped, same discipline as every earlier
   checkpoint) aggregate hash **plus per-field hashes** (`rig_status`, `groups`, `memberships`,
   `group_count`, `duplicate_sibling_groups`, `duplicate_direct_controls`, `duplicate_memberships`) of
   the returned snapshot.
4. `RebuildControlGroupsProductionRun.run_target_transaction` (class method) — records entry/exit
   timing and a low-cadence memory snapshot at entry and exit only (never inside the recursive walk).
5. `RebuildControlGroupsProductionRun.prepare_native_callback` (class method) — wrapped only to
   post-process the already-assigned `self.rebuild` with a timing/memory wrapper around the native call
   itself; the setup method's own logic and return value are untouched.

The monkey-patch mechanism itself — reassigning a name in an `exec()`'d namespace dict after `exec()`
but before the wrapped function/method is ever called, and confirming this correctly affects calls made
from OTHER code defined in the same `exec()`'d source (because CPython resolves free variables via
`__globals__` at *call* time, not definition time) — was verified offline under the real embedded
Python 2.7.5 before deployment: `test_monkeypatch_mechanism.py` (SHA-256
`20144d8f4ec8aca08e9289fbfc87edc4e4d02b7810974a46b5e22979eccfd690`), **6/6 PASS**, including
confirmation that a fresh re-`exec()` (as happens between O2's own two commands) yields an independently
unpatched copy with no leftover state.

### Derived (not directly wrapped) stage boundaries

Per the explicit instruction not to add a boundary if observing it requires invasive behavioral change,
three requested boundaries are DERIVED from the timestamp gaps between the five wrapped events' own
recorded timings, rather than adding further wraps:

- **Classification/planning completion** = gap between the outer `NATIVE_POST` capture's end and the
  next capture's start (or, on the native-only fallback branch, simply absent — see branch truth below).
- **Contextual writes completion** = gap between the composer-before capture's end and the
  composer-after capture's start.
- **Target isolation** = gap between the terminal capture's end and `run_target_transaction`'s own end.

### Branch truth (not assumed, not inferred from exception-catching)

Direct source reading (this session, cross-checked against O1) confirmed the native-only fallback path
raises `NativePostFallback` internally — production's own control-flow exception — **before** the
composer-before capture would ever run. O2 does not catch or alter that exception. Instead, branch is
read directly from which capture LABELS actually occurred for a given target: exactly `{PRE,
NATIVE_POST}` ⇒ `native_only_fallback`; presence of `PRODUCTION_GENERIC_COMPOSER_PRE` ⇒ `reconciled`;
anything else ⇒ `unknown` (reported, not silently misclassified). This logic is offline-regressed — see
below.

### Composer-before / composer-after↔terminal equivalence witnesses

For every target, O2 mechanically compares captures by label using BOTH the aggregate hash and the
per-field hashes (never only the aggregate), producing one of exactly three results:
`EXERCISED_PATH_EQUIVALENT_NO_INTERVENING_MUTATION`, `NOT_EQUIVALENT`, or
`FRESHNESS_OR_EXCEPTION_SEMANTICS_UNRESOLVED` (when either capture is missing) for the composer-before
witness; the composer-after↔terminal witness additionally reports
`UNRESOLVED_NATIVE_ONLY_FALLBACK_NO_TERMINAL_COMPARISON` explicitly for the native-only-fallback branch,
rather than fabricating a comparison the fallback path never actually reaches. A field-level diff
(`field_diff()`) reports exactly which specific fields (hierarchy/groups, membership, rig status, etc.)
differ when an aggregate mismatch occurs, so a "not equivalent" result can be explained, not just
asserted.

This analysis logic is extracted VERBATIM from the deployed script (lines 792–856) and offline-regressed
against synthetic capture-event data: `test_o2_analysis_logic_regression.py` (SHA-256
`f39cc7facbf4174ec909829b76728c50e579723e3882245426c05e5d6e016115`), **17/17 PASS** — covering correct
branch classification (including the incomplete-capture "unknown" case, not silently misclassified),
correct witness results for matching/differing/missing captures, correct native-only-fallback
sentinel behavior, correct per-field diff identification, and correct derived-timing-gap arithmetic.

### Resource sampling discipline

Low-cadence only: once per target (`run_target_transaction` entry/exit) and once per native Rebuild
call — never inside `capture_tree`'s own recursive walk, never per DME element, per the explicit
instruction not to recreate the qualification-harness's own earlier VAS-scan mistake.

## Offline evidence collected this turn

### Closure-cycle mechanism (Astra finding #2 / Required Conclusion #5, mechanism half)

`test_capture_tree_closure_lifetime.py` (SHA-256
`2d1965886505bf98607985fc0c2f9e1ef37ac978ec700c3426ed1c943b796a51`) extracts `capture_tree()` and its
full dependency chain VERBATIM from the pinned production source, exercises it against fake DME objects
implementing the exact interface confirmed by direct source reading (`GetName`/`GetTypeString`/
`GetAttribute`/`IsVisible`/`IsSelectable`/`IsSnappable`/`GroupColor`), and empirically proves, under the
real embedded Python 2.7.5 (**9/9 PASS**):

1. `capture_tree()`'s nested `def walk(...)` recurses by calling itself by name, making its own closure
   cell self-referential — a cycle refcounting alone cannot free.
2. After the caller `del`s `capture_tree()`'s own return value, the returned `groups`/`memberships`
   payload dicts **remain reachable and alive** — proven by identity-tracking via `gc.get_objects()` —
   until `gc.collect()` (or an automatic collection) actually runs; a single `gc.collect()` then reclaims
   them all at once.
3. Repeating this 25 times with **no interim `gc.collect()`** (mirroring production's own
   docstring-confirmed "no gc.collect() used internally" design) leaves **all 25** payload dicts and all
   25 orphaned `walk` closures simultaneously alive and uncollected, until one final collection reclaims
   every one of them at once.

**This empirically CONFIRMS the mechanism Astra flagged is real and reproducible under the exact
interpreter production runs under.** It does **not** by itself establish materiality at real
target/command scale — the synthetic tree (20 groups × 8 controls) showed no measurable working-set
delta at this tiny scale, and the real-SFM bounded run (per this checkpoint's own operator instructions)
is what will determine whether this mechanism contributes a measurable amount at Fox/Mia's real control
counts (136/174) across the captures a real command actually performs.

### Corrected capture/branch truth (supersedes O1's inaccurate blanket claim)

Direct source reading (this session) precisely resolved what O1 only approximated: the native-only
fallback branch gets **exactly 2** captures (`PRE`, `NATIVE_POST`) — the fallback exception fires
**before** the composer-before capture would ever run. Only the reconciled branch reaches the remaining
3 captures (composer-before, composer-after, terminal). O1's "every target receives 3-5 captures" was
therefore inaccurate as a blanket claim, as Astra correctly flagged; O2's own instrumentation reports the
real, per-target, per-branch capture count and sequence directly from the live run, not from a static
assumption.

## Required conclusions — current status

The real-SFM bounded run resolved six of the eight; native Rebuild remains unresolved pending O2-R1's
corrected instrumentation (script prepared, not yet run this turn):

| # | Conclusion | Status |
|---|---|---|
| 1 | Discovery — is repeated whole-shot reachable-DME discovery materially expensive at target-command scale? | **`MATERIAL`** — 10 calls/command, ~1.54s total, ~0.15s mean per call |
| 2 | Tree capture — is recursive target semantic-tree construction materially expensive? | **`IMMATERIAL`** — 10 calls/command, ~0.02s total; not pursued as standalone |
| 3 | Composer-before — does O2 support further design investigation? | **`DESIGN_REVIEW_JUSTIFIED`** for the reconciled path — empirical equivalence (real run) plus exhaustive static proof (`checkpoint_o2_r1/O2_R1_OUTER_POST_TO_COMPOSER_BEFORE_PROOF.md`, `SOURCE_EQUIVALENCE_SUPPORTED`) — validation/freshness proof for any actual reuse design still required |
| 4 | Reconciled terminal overlap | **`DESIGN_REVIEW_JUSTIFIED`** for the reconciled path only — empirical equivalence plus static proof (`checkpoint_o2_r1/O2_R1_COMPOSER_AFTER_TO_TERMINAL_PROOF.md`, `RECONCILED_PATH_REUSE_PLAUSIBLE`) — terminal retains a distinct procedural purpose (post-cleanup capturability) not generalized to native-only fallback |
| 5 | Closure cycle | Mechanism: `MATERIAL_MECHANISM_CONFIRMED_OFFLINE`. Materiality at real scale: `UNRESOLVED` — O2's bounded run did not isolate this separately from tree-construction cost (found `IMMATERIAL` at Fox/Mia's own control-count scale) |
| 6 | Native Rebuild | `UNRESOLVED` — **instrumentation gap**, corrected under O2-R1; re-run pending |
| 7 | Contextual composer | Partially resolved: warm second run still requires substantial contextual reconstruction (Fox 72/74 moved, Mia 67/69 moved) — this is expected Rebuild→Normalizer behavior, not evidence of redundancy by itself; full materiality classification deferred alongside native-Rebuild timing (conclusion 6), since composer cost must be read against native cost to judge relative weight |
| 8 | Fresh vs. normalized | Resolved for discovery/tree/witness stages (see table above); native-Rebuild fresh-vs-warm comparison pending O2-R1 |

## Decision rule (restated, governs any future step)

A candidate proceeds to optimization design review only when: (1) O2 demonstrates material cumulative
cost; (2) the repeated work is demonstrably overlapping/redundant; (3) preserving its
validation/freshness obligation appears feasible; (4) the likely payoff is worth the added architectural
complexity. Trivial cost is rejected immediately even if technically redundant. **This audit does not
apply that rule yet — there is no real-scale data to apply it to.**

## Correctness gates preserved

O2's own script requires, every command: exact production Normalizer and canonical Master SHA-256;
`shot3` present; authority `READY`/canonical; zero outstanding leases; native guards and native-rebuild
log markers PASS; `FINAL_REPORT_ENTRY` reached; the run started and completed within timeout. Measurement
instrumentation adds fields to the evidence artifact; it does not weaken or replace any of these gates.

## F1-R2

Remains **PARKED / UNRUN**. Not executed during O2 preparation. Whether a corrected F1-R2 is still
warranted will be decided after O2's real-SFM results are in hand.

## Evidence artifacts

- `real_sfm_qualification/checkpoint_o2/o2_phase_attribution_result.json` — compact, machine-readable:
  the offline evidence collected this turn (closure test, monkeypatch mechanism test, analysis-logic
  regression, all PASS/FAIL counts) plus the real-SFM evidence schema, currently `null`/pending.
- `real_sfm_qualification/checkpoint_o2/INSTRUCTIONS.md` — operator instructions for the one real-SFM
  run this checkpoint requires.
