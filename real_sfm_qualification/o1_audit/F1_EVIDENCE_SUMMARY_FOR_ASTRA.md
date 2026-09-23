# F1 Series Evidence Summary (condensed, for Astra review)

Full detail, exact figures, and machine-derived validation results for every claim below are in
`real_sfm_qualification/LEDGER.md` (rows F1-1, F1-R1, F1-2, F1-R2) and each checkpoint's own directory
(`checkpoint_f1/`, `checkpoint_f1_r1/`, `checkpoint_f1_2/`, `checkpoint_f1_r2/`). This document is a
condensed orientation only — do not treat it as the authoritative record.

## F1-1 — FAIL (SFM process crash)

Four-command repeated-use test (Selected×2, All Shots×2) crashed the real SFM process during command 3
(All Shots), target_seq 52, immediately after `PRE_NATIVE` telemetry — no subsequent
`NATIVE_REBUILD_RETURNED`. 32-bit LAA process; VAS fragmentation observed (`largest_free` collapsed from
~125 MB to ~7.5 MB over the run). Root cause not claimed at the time.

**Static audit** of the F1 harness itself found one concrete harness-side deficiency: `gc.collect()`
called only once, after all 4 commands, never between them — proven (via an offline empirical test under
the real embedded Python 2.7.5) to allow reference-cycle garbage to accumulate across repeated `exec()`
of the production Normalizer's own namespace. Every other harness-owned object was verified low-risk by
reachability.

## F1-R1 — DIAGNOSTIC PASS FOR ATTRIBUTION (harness-side cause identified)

A minimal-footprint 3-command diagnostic (Selected×2, All Shots×1) with the `gc.collect()` fix applied.
**Decisive finding**: production's own command 2 showed **zero** retained private/pagefile/VAS growth
between its own `CP0_COMMAND_START` and `FINAL_REPORT_ENTRY` (identical figures, 6.430 s elapsed), while
the **harness's own** post-command semantic verification (which still transiently captured the full
85-eligible-target semantic tree on every command merely to compute an aggregate hash) added ~76.15 MiB
that did not return after `del()` + `gc.collect()`.

A follow-up static trace plus an offline empirical test under the real embedded Python 2.7.5 identified
the exact mechanism: **Python/CRT allocator high-water retention** — freed pymalloc arenas are not
returned to the OS merely because the Python objects using them became unreachable and were
`gc.collect()`-swept. This is distinct from live-reference retention (ruled out) and cyclic garbage
(already fixed, still insufficient).

## F1-2 — FAIL/INCOMPLETE (a second, different, production-internal phenomenon)

The corrected checkpoint: restored the original 4-command sequence but eliminated all inter-command
whole-85-target semantic capture (Selected commands capture only Fox/Mia; All-Shots commands capture
nothing externally; the one full verification is deferred to after command 4).

- Selected commands 1–2 completed cleanly: small, healthy production-side private growth (~13.8 MiB,
  ~3.1 MiB), **zero** free-VAS loss, confirmed idempotence (command 2's Fox/Mia hashes exactly matched
  command 1's).
- **All-Shots command 3** completed cleanly at the production level but showed, **within its own single
  run** (its own `CP0_COMMAND_START` vs its own `FINAL_REPORT_ENTRY`): private +238,366,720 bytes
  (~227.32 MiB), free VAS −233,242,624 bytes (~222.44 MiB), largest-free-block −111,017,984 bytes
  (~105.88 MiB). **This is production-internal, not harness-caused** — F1-2 had already eliminated the
  harness-side capture F1-R1 identified.
- Command 4 then produced **no completed record at all**, consistent with beginning against the reduced
  headroom command 3 left behind.

A production-internal static audit (`checkpoint_f1_2/F1-2_PRODUCTION_INTERNAL_STATIC_AUDIT.md`) traced
`RebuildControlGroupsProductionRun`'s own state and identified `self.work` (built once via
`snapshot_work()`, never shrunk) — holding live native `aset`/`game_model` DME references for every
eligible target simultaneously, for the whole command — as the primary architectural candidate, without
being able to determine by static reading alone whether the ~227 MiB is scene-resident (baked into the
normalized scene) or per-run native/allocator retention.

## F1-R2 — PENDING, PARKED (not yet run)

A two-phase diagnostic (Phase 1: normalize the original fixture once, Save-As a new diagnostic copy;
Phase 2: fresh SFM process, normalize the already-normalized copy again, then perform the one deferred
full verification) designed to separate scene-resident vs. per-run native-retention growth empirically.
Built, offline-regressed (30/30 PASS, including a proven-safe Save-As guard), and committed. **Explicitly
parked, not run, pending this broader O1 static audit.**

## Why this matters for O1 / Astra review

F1-2's within-command production-internal growth (~227 MiB / one All-Shots run) is the concrete resource
signal motivating O1's material-redundancy audit. O1 is a static-analysis attempt to identify *candidate*
sources of that growth (repeated per-target computation, retained native references, redundant semantic
captures) from source reading alone — F1-R2 remains available later if runtime proof is still needed
after Astra's review.
