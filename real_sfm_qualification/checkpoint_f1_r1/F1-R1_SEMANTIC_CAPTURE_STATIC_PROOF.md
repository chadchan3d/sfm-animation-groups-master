# F1-R1 Static Proof: What Runs Between Production FINAL_REPORT_ENTRY and the Harness's Own Post-Command GC Snapshot

Performed per explicit instruction after F1-R1's decisive attribution
finding. This is a read-only trace of the deployed F1-R1 script
(`Checkpoint_F1_R1_Attribution_Diagnostic.py`, SHA-256
`e9ea42b08f6448cef174b4d5642dfc1a89dbe74cf0145d9fcc0a3d96b63e7763`) and the
production functions it invokes. **No production file and no harness file
was modified while performing this trace.**

## Recorded finding

```
F1-R1 — DIAGNOSTIC PASS FOR ATTRIBUTION: harness post-command semantic
verification materially consumes retained process address space; production
Selected command #2 itself showed zero retained private/VAS growth.
```

Production command 2: `CP0_COMMAND_START` and `FINAL_REPORT_ENTRY` both show
private/pagefile `3239079936`, free VAS `348925952`, largest free region
`126353408` — **exactly zero** production-side retention, in 6.430 s. The
harness's own post-command measurement, taken after its own `gc.collect()`,
was `3318931456` — **79,851,520 bytes (~76.15 MiB) higher**, over a 129.206 s
total command-record duration (i.e. roughly 122+ s and ~76 MiB attributable
to code that is not the production command itself). The same pattern exists
after command 1.

## Exact code path traced, in execution order

All line numbers are 1-indexed, from the deployed script above, between the
point production's own `FINAL_REPORT_ENTRY` is logged (inside production,
not visible to the harness directly — the harness instead detects command
completion via its run-lock wait loop) and the harness's own post-command
`gc.collect()`/`memory_snapshot()` call.

| Step | Lines | Operation | Materializes a large object graph? |
|---|---|---|---|
| 1 | 1110–1122 | Read production's own log (`NORMALIZER_LOG_PATH`), decode as text, scan for two literal markers, parse `CONTEXTUALIZER_RESOURCE_CHECKPOINT` lines, preserve a byte-copy, `del log_bytes, log_text` | No — bounded to one command's log size (~300–400 KB observed), freed same-statement-block |
| 2 | 1135–1141 | `build_independent_witness()` (post-run structural witness) — iterates **all 163 targets**, for each calls `b_get_transform_controls()` (native array read into a Python list of control objects), builds a `set()` of folded control-name strings per target, hashes it via `stable_hash()` | **Yes, but bounded** — per-target control-name lists/sets only (no attribute values, no group tree), `del post_witness`/`del post_all_by_key` immediately after use |
| 3 | 1143–1160 | Missing/new/reclassified target-set diff (pure key-set arithmetic on the witness above) | No — small sets of key strings |
| 4 | **1169** | **`raw_eligible = capture_all("CMD%d" % ordinal, eligible_targets_of_interest)`** | **YES — the dominant cost.** Calls, for **all 85 eligible targets**, `capture_snapshot_explicit_fn(shot, target_aset, label)` — production's own `capture_snapshot_explicit()` (production source lines 3544–3726), which for each target calls `capture_tree(root)` (production source lines 1200–1334): a **recursive walk of the target's entire control-group hierarchy**, building nested Python dicts (`groups`, `memberships`) keyed by every group path, each holding every direct control's name/type/attribute data, plus duplicate-sibling/duplicate-control bookkeeping dicts. For a target with ~150–178 controls across ~20+ groups (Fox: 136 controls; Mia: 174 controls — the two known identities; other targets' counts are not individually pinned but are of the same order), this is thousands of small dict/list/string objects **per target**, ×85 targets, held simultaneously in `raw_eligible` until the next step completes |
| 5 | 1171 | `aggregate_hash = stable_hash([...dumps_sorted(v)...])` — serializes **every one of the 85 raw values to a JSON string** (`json.dumps(value, sort_keys=True)`, one call per target) to build the aggregate hash's input list | Yes — 85 additional large string allocations (the serialized form of step 4's structures), transient but simultaneously held with the raw dicts |
| 6 | 1172 | `current_eligible_hashes_full = compute_target_hashes(raw_eligible)` — re-serializes **each of the 85 values again** (a second, independent `dumps_sorted()` call per target inside `per_target_hash()`) to compute each one's own SHA-256 | Yes — a second full pass of 85 serializations, briefly overlapping with steps 4–5's still-live structures before step 7 |
| 7 | **1173** | `del raw_eligible` | Releases the Python-level references — **but see "Category 3" below: this does not by itself return allocator arenas to the OS** |
| 8 | 1178–1185 | `changed_keys`/`unchanged_keys` — set arithmetic over the **85-entry hash dict** (`current_eligible_hashes_full`, hex strings only, not raw data) | No — cheap, hashes not raw values |
| 9 | 1203–1231 (only for `ordinal in FULL_CAPTURE_ORDINALS`, i.e. command 3 in F1-R1) | A second `build_independent_witness()` pass plus `excluded_witness_row()` for 78 targets, then `compute_target_hashes()` again | Bounded (structural witness rows only, no rig-tree walk) — **not the cause of the command-1/command-2 retention**, since commands 1–2 are Selected Shots and never reach this branch |
| 10 | 1239–1305 | Authority/broker evidence capture (`provider_counters()`, `outstanding_lease_count()`, etc.) | No — small dicts of counters |
| 11 | **1311–1319** | `del prod_ns`; `del authority_runtime`; `del broker` | Releases the entire freshly-`exec`'d production namespace's own Python-level references |
| 12 | **1320** | `gc.collect()` | Sweeps **cyclic garbage** (proven effective for this category in the F1-1 static audit's own offline test) — **does not and cannot return freed pymalloc arenas to the OS; that is not what `gc.collect()` does** |
| 13 | **1321** | `memory_after_collect = memory_snapshot()` — **this is the measurement the user's evidence cites** | — |

## Which operations materialize large object graphs

Only **step 4** (`capture_all()` → `capture_snapshot_explicit_fn()` →
`capture_tree()`, all 85 eligible targets) and its two immediately-following
double-serialization passes (steps 5–6) build anything of consequence. Step
2 (the structural witness) is bounded and does not walk rig trees. Step 9
only fires on the one ordinal (3) designated `FULL_CAPTURE_ORDINALS` — it
cannot explain the retention observed after commands 1 and 2, which never
reach it. **Step 4 runs unconditionally on every command** (1, 2, and 3
alike), because F1-R1 still needs the full 85-target aggregate hash every
command to verify it against the pinned `EXPECTED_SELECTED_HASH` /
`EXPECTED_ALLSHOTS_HASH` constant — this is exactly the flaw the user has
identified: even though F1-R1 only **persists** the full hash map for
command 3, it still **materializes** the full raw semantic tree for all 85
targets transiently on *every* command, including the two Selected-Shots
commands where only 2 of those 85 targets (Fox, Mia) are semantically
relevant at all.

## Distinguishing the three retention categories

1. **Live-reference retention** — ruled out. Every large structure
   (`raw_eligible`, `post_witness`, `post_all_by_key`, `prod_ns`) is
   `del`-ed within the same command's own code before the next command
   begins (lines 1141, 1150, 1173, 1311); none is ever stored into `report`
   or any other longer-lived container. Confirmed by direct reading, not
   assumption.
2. **Cyclic garbage** — addressed by `gc.collect()` at line 1320 (the F1-1
   static-audit fix). The offline test `test_gc_cycle_accumulation_across_exec.py`
   (from the F1-1 audit) already proved this mechanism is real and that
   per-command `gc.collect()` eliminates it. It does **not**, however,
   explain the ~76 MiB delta observed here, because that delta persists
   even with the fix in place.
3. **Python/CRT allocator high-water retention** — **this is the
   operative mechanism.** CPython's own small-object allocator (pymalloc)
   manages freed objects via its own internal free lists, organized into
   fixed-size "pools" grouped into "arenas." A freed object's memory goes
   back to pymalloc's free lists, **not to the OS** — an arena is only
   released back to the OS once *every* pool within it is completely empty.
   Step 4's capture (many thousands of small, variously-sized dict/list/
   string objects allocated together, then freed together in a different
   pattern than allocated, across 85 targets' worth of rig trees) is
   exactly the allocation/fragmentation shape that leaves pymalloc arenas
   **partially occupied indefinitely** — `del` and `gc.collect()` are both
   fully effective at the Python-object level (steps 1–2 above) and both
   **structurally incapable** of addressing this category, because arena
   release is an allocator-internal decision pymalloc makes, not something
   application code controls.

## Offline empirical measurement (real embedded Python 2.7.5, 32-bit)

`test_allocator_highwater_retention.py` (SHA-256
`dd5a7c90f6e36f7836e5420b0635bf1dc90ff71f666219f4c8203b07092277ee`) builds a
synthetic structure shaped like `capture_tree()`'s own output (85 targets ×
20 groups × 8 controls, approximating Fox/Mia's real ~136–174-control scale
and this project's own D1/D2-measured ~9 MB real 85-target payload — a
size/shape-matched stand-in, not a claim about production's exact object
graph), repeats an allocate → hash → `del` → `gc.collect()` cycle four times
(mirroring F1-R1's own per-command pattern), and measures real process
working set at peak and after each cycle's own cleanup:

```
baseline working_set=9859072

cycle 1: peak_delta=+7041024 bytes (6.71 MiB)  after_cleanup_delta=+6361088 bytes (6.07 MiB)
cycle 2: peak_delta=+7614464 bytes (7.26 MiB)  after_cleanup_delta=+6148096 bytes (5.86 MiB)
cycle 3: peak_delta=+7602176 bytes (7.25 MiB)  after_cleanup_delta=+6000640 bytes (5.72 MiB)
cycle 4: peak_delta=+7589888 bytes (7.24 MiB)  after_cleanup_delta=+6000640 bytes (5.72 MiB)

ALLOCATOR_HIGH_WATER_RETENTION_SIGNATURE_PRESENT=True
```

Even after every raw structure is both unreachable and `gc.collect()`-swept,
working set never returns to baseline — a permanent ~6 MiB floor appears
after the very first cycle and persists (a plateau, not runaway growth, in
this bounded synthetic case) across all four cycles. This empirically
confirms category 3 is real and is not addressed by `del`/`gc.collect()`
under the actual interpreter build F1-R1 runs under. It does **not** by
itself reproduce the full ~76 MiB/command figure F1-R1 observed against the
real production rig data (the synthetic structure is a size-matched
approximation, not a byte-identical reproduction, and the real 32-bit SFM
process additionally interleaves native DME/Rebuild-side allocations in the
same address space) — it demonstrates the *mechanism*, which is sufficient
to explain *why* `del` + `gc.collect()` could not have prevented F1-R1's
observed retention, without over-claiming an exact size match.

## Conclusion

The static trace and the offline empirical test agree: the ~76 MiB/command
retention F1-R1 observed is attributable to step 4
(`capture_all()`/`capture_snapshot_explicit_fn()`/`capture_tree()`, the
full 85-target semantic capture that F1-R1 still performed transiently on
**every** command) landing in **category 3 — Python/CRT allocator
high-water retention** — not live-reference retention (ruled out by direct
code reading) and not cyclic garbage (already fixed by the F1-1 audit's
`gc.collect()`-per-command correction, which is present in F1-R1 and still
did not prevent the observed delta). This is now the principal, evidence-backed
explanation for F1-1's command-3 headroom collapse, and directly motivates
Checkpoint F1-2's design: **stop performing any whole-85-target semantic
capture between production commands at all** — perform it exactly once, at
the very end, after no further production command depends on the
address-space headroom it consumes.
