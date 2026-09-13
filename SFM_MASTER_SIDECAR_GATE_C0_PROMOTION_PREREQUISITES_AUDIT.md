# SFM Master Sidecar — Gate C0: Promotion Prerequisites Audit

## 1. VERDICT

**C0 PASS — PROCEED TO C1 OWNER QUALIFICATION**

All ten C0-PASS criteria are met (see §19). Two items carry an explicit,
non-blocking caveat rather than a clean pass: the ≤16/32 MiB idle planning
targets are missed (by a small margin, and are non-normative to begin
with), and the constrained loaded-project measurement surfaced a real,
material resource-safety margin concern that Gate C1 must act on (an
explicit pre-admission headroom check), not ignore.

## 2. ASTRA ROUND 2 FINDINGS INCORPORATED

The completed Astra Round 2 audit document was not available as a file in
this repository or supplied to this task; only the brief given to Astra
(`SFM_Sidecar_Astra_Round2_Review_Brief_2026-09-12.md`) and this Gate C0
brief's own §0 "Current authoritative status" summary of Astra's actual
findings were available. This is stated plainly rather than glossed over.
All work below was scoped directly from the C0 brief's own explicit
findings list (which is detailed enough to execute against directly):
withdrawn Gate B resource claims, the mirrored-oracle gap in Gate A2/Gate B
consumer-function testing, the escape/wrapper compatibility-profile gap,
the duplicated-validator drift risk, the phase-boundary/sampling-quality
concerns, and the unproven withheld-late-vocabulary claim. Each is closed
in a numbered C0.x section below.

## 3. BASELINE IDENTITIES

- HEAD at task start: `8c4afedbe6053cd98dd4b1c86cd104dff3d99c86` "Qualify bounded sidecar consumer value" — confirmed, no drift.
- `git status --short` at task start: clean except pre-existing unrelated untracked files (Flex Bone/Sexual Bones/Phase2 review artifacts, Master backups) and the Astra Round 2 evidence bundle from the prior task; nothing staged.
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — matches expected, unchanged throughout C0.
- Official sidecar (freshly recompiled via the production writer, never a stored copy): 9,506,244 bytes, SHA-256 `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` — matches expected exactly, unchanged throughout C0.
- Production `reader.py`: SHA-256 at task start `c0ed4250cfe13b892e54baf0538ee3bab946f000f20466d5c4da5b15c60bf2a9` (matches expected) — **intentionally changed during C0.3** to `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` (one closure-cycle fix; see §6). Unstaged.
- Production `format.py`: SHA-256 `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` — unchanged throughout.
- Gate B qualification `bounded_provider.py`: SHA-256 changed twice during C0 (delegated validation to the production validator in C0.3; added resource-introspection methods for C0.4/C0.7) — both changes are qualification-only, unstaged.
- `bounded_view.py`: unchanged.
- Current Normalizer source: `E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py`, SHA-256 `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` — unchanged throughout, reverified after every real-SFM session in this gate.
- Full current test suite (final, post-C0.3-edit): 421 passed, 265 subtests passed, 0 failures.
- Validator: PASS — 0 grammar errors, 0 exact duplicates, 0 cross-path casefold invariant violations.
- No identity drift not already explained by an approved, documented change was found. No STOP condition was triggered.

## 4. C0.1 ACTUAL CONSUMER PARITY

**Result: PASS.** Executed in real embedded Python 2.7.5 SFM (autoinit, Qt/main-event thread), calling the ACTUAL, unmodified Normalizer functions `oracle.master_lookup` and `oracle.validate_master_subset_conflicts` directly against BOTH a TXT-derived view (built by the real `parse_targeted_master`) and a sidecar-derived view (built by S1's `bounded_view.build_view_bounded`) — the same function objects both times, no reimplemented mirror used as the oracle for this comparison.

21/21 PASS across all 7 required fixture categories:
1. no-conflict family (`duplicate_occurrences_one_group`) — `validate_master_subset_conflicts` both `None`; `master_lookup("Dupe")` identical dicts both sides.
2. same-destination ASCII aliases (`same_destination_aliases`) — no conflict, identical results.
3. cross-destination fold conflict (`cross_destination_conflict`) — **exact exception message parity**: both raise `ProbeError("Multiple targeted Master destinations for u'Bar': [u'GrpA', u'GrpB']")`.
4. exact spelling inside conflicting family (`exact_spelling_inside_conflict`) — exact literal `"Baz"` still raises (fold-level conflict, not spelling-level) with identical message both sides.
5. valid absent query — identical `known=False`/`mode=NONE` dict both sides.
6. valid ASCII case variant (`"fOo"`, not itself an exact spelling in source) — identical `mode=ASCII_CASEFOLD` dict both sides.
7. valid non-ASCII input (`顔`/`注視TipsParent`) — identical `mode=EXACT`, non-ASCII destination string, both sides.

No STOP condition triggered (Stop condition 1 — "actual Normalizer conflict behavior differs between TXT and sidecar views" — did not occur).

## 5. C0.2 NORMALIZER SOURCE PROFILE

**Result: PASS.** New qualification-only module `tests/sidecar/qualification/normalizer_source_profile.py` defines `check_normalizer_source_profile(source_bytes, wrapper_name)`, raising `NormalizerSourceProfileRefused` (never `MasterUnknown`) for exactly two evidence-backed divergence classes: wrapper ≠ `groupFile`, and any backslash byte present in the source.

Real-embedded-SFM proof, 8/8 PASS:
1. Official Master source: **ACCEPTED**.
2. Compatible custom fixture: **ACCEPTED**.
3. Escaped-token fixture (`"Line1\nLine2"`): **REFUSED explicitly**, and the underlying divergence was concretely demonstrated (not merely asserted) — the real oracle's resolved literal set for this scope came back `[]` (its own fold key differs entirely after escape resolution) while the sidecar's came back `['Line1\\nLine2']` — a genuine fold-IDENTITY divergence, not just a content difference.
4. Custom-wrapper fixture (`customWrapper`): **REFUSED explicitly**, corroborated by the real oracle independently raising `ProbeError('Master root is not groupFile.')` on the same file.
5. Both refusals are `NormalizerSourceProfileRefused`, never `MasterUnknown` — confirmed.
6. Generic sidecar reader/compiler: confirmed it still opens/reads BOTH "refused" fixtures successfully (1 occurrence each) — refusal is adapter-specific, the generic capability is unchanged.

This is a qualification-only adapter boundary (per the brief, "may remain qualification-only in C0") — no binary-format change, no Normalizer change.

## 6. C0.3 VALIDATION CONSOLIDATION

**Result: preferred outcome 1 achieved — one shared validation implementation, no public semantics change.**

Inspection found the qualification candidate (`bounded_provider.py`) had, up to this point, a hand-copied ~320-line transcription of production `reader.py`'s `_validate_and_decode` — exactly the drift risk Astra flagged. Investigation showed `_validate_and_decode` is already a private, module-level function (not a method), already importable from `tools/sfm_master_sidecar/reader.py` by anything that imports the `reader` module — which `bounded_provider.py` already does.

**Change made:** `bounded_provider._validate_complete(buf)` now delegates entirely:
```python
def _validate_complete(buf):
    backing = prod_reader._validate_and_decode(buf)
    return backing.header, backing.directory
```
The full decoded `_Backing` (strings, groups, occurrence_rows, fold_rows, child_id_index, metadata_rows, both index arrays) is used only to extract `header`/`directory`; everything else is discarded the instant this function returns, by never retaining a reference to `backing` past this point. There is now exactly ONE validation implementation in the codebase — production `reader.SidecarReader` and the qualification `BoundedProvider` both call the identical function object. No public API changed; no binary format changed.

**Validation-class mapping** (every check now lives in exactly one place, `reader._validate_and_decode`, mapped against the B2C corruption/integrity corpus):

| Section (A–J) | What it checks | Corpus coverage |
|---|---|---|
| A | Header/Directory/protected regions, magic, versions, payload_length, embedded digest, section-set completeness, region overlap | `test_structural_corruption_header.py` (14 tests), `test_basic_corruption.py` (10 tests, incl. digest mismatch) |
| B | String Table + Pool bounds, UTF-8 validity, resource limits | `test_structural_corruption_strings.py` (7), `test_resource_limits.py` (9) |
| C | Group Table structural checks, anti-cycle, path-identity uniqueness | `test_structural_corruption_groups.py` (25) |
| D | Child-ID Index partition/ownership/ordering | `test_structural_corruption_groups.py` (shared) |
| E | Metadata Table partition/ownership | `test_structural_corruption_groups.py` (shared) |
| F | Occurrence Table bounds, literal-to-fold agreement, local_rank density | `test_structural_corruption_occurrences.py` (15) |
| G | Occurrence-by-Group Index complete partition | `test_structural_corruption_occurrences.py` (shared) |
| H | Fold Table ordering, occ_index_count | `test_structural_corruption_folds.py` (19) |
| I | Occurrence-by-Fold Index complete partition | `test_structural_corruption_folds.py` (shared) |
| J | Cardinality cross-checks | all of the above (shared invariant) |

All 99 corruption/limit tests, plus the full 421-test/265-subtest suite, pass unchanged after the consolidation (§9). Since `bounded_provider.py` now calls this exact function, every one of these 99 tests transitively covers the qualification candidate's admission path too — not just production's.

**Preferred-outcome ordering honored:** outcome 1 (shared implementation, no semantics change) was achieved; outcomes 2/3 were not needed.

## 7. VALIDATION SCRATCH / CLEANUP LIFETIME

The "nested path-resolution closure/cycle" Astra identified was a real, specific defect: `_validate_and_decode`'s path-reconstruction helper (`full_path_of`) was a **self-referential recursive closure** — in CPython this forms a genuine reference cycle (the closure's cell holds the function; the function's `__closure__` holds the cell) that only the periodic cyclic garbage collector reclaims, never deterministic refcounting. This is exactly the kind of thing an "unexplained later `gc.collect()`" would paper over.

**Fix applied** (production `reader.py`, `_validate_and_decode`): replaced the recursive closure with a plain forward loop. The anti-cycle check earlier in the same function already guarantees `parent_path_id < i` for every non-root row, so a single `for i in range(group_count)` pass resolves every full path with no recursion and no closure — provably equivalent (same values; the anti-cycle invariant it depends on is already checked before this code runs). Exact diff:

```diff
-    def full_path_of(idx, _seen=None):
-        if full_paths[idx] is not None:
-            return full_paths[idx]
-        row = groups[idx]
+    for i in range(group_count):
+        row = groups[i]
         name = strings[row.name_string_id]
         if row.parent_path_id == fmt.ROOT_SENTINEL:
-            fp = name
+            full_paths[i] = name
         else:
-            fp = full_path_of(row.parent_path_id) + "/" + name
-        full_paths[idx] = fp
-        return fp
-
-    for i in range(group_count):
-        full_path_of(i)
+            full_paths[i] = full_paths[row.parent_path_id] + "/" + name
```

**What survives function return:** only `backing.header` and `backing.directory` (both tiny, fixed-size). **What allocations exist during validation:** transient lists (`strings`, `groups`, `occurrence_rows`, `fold_rows`, `child_id_index`, `metadata_rows`, both index arrays) — all plain lists/namedtuples, no cycles, reclaimed by ordinary refcounting the moment the caller drops its reference to the returned `_Backing`. **No reference cycle remains** after this fix — confirmed by the absence of any other self-referential closure in the function (all other local helpers, e.g. `section_bytes`/`section_row_count`, close over `directory`/`buf` only, never over themselves). **Deterministic cleanup is possible before steady-state measurement, with no `gc.collect()` required anywhere** — confirmed empirically: no `gc.collect()` call appears anywhere in the C0.4/C0.5/C0.6 probes, and all steady-phase samples were taken without one.

**Production-edit rule followed exactly:** smallest semantics-preserving change; full regression run (369 passed/265 subtests on the sidecar suite alone, 421/265 on the full suite) before relying on it; `git diff --check` clean; official artifact SHA/bytes and Master SHA reverified unchanged; the edit remains unstaged. No STOP condition (4) was triggered — the consolidation strengthened, not weakened, corruption rejection (it is now impossible for the two paths to disagree, since there is only one path).

## 8. C0.4 IDLE RESOURCE METHOD

Real embedded SFM (fresh disposable process), Qt/main-event thread, **non-blocking QTimer-chained phases** (no long `sleep()` on the main thread) — a genuine architectural change from prior gates' single blocking `main()` call. Each steady phase held open ~2.6s via `QTimer.singleShot` chaining, giving the external sampler multiple genuine, evenly-spaced observations per phase (confirmed: 4–5 VAS scans per steady phase at 0.6s cadence, 15–17 memory samples per phase at 0.15s cadence — comfortably exceeding the required "≥3 VAS observations per steady hold").

Vocabularies (Fingers=216 folds "small", RigArms=17 folds "second") were precomputed on desktop **before** the measured SFM process ever launched, serialized to a small JSON file the probe only reads — the measured process never runs a vocabulary-discovery scan, never opens an eager reader, never touches T1/T2, adversarial fixtures, or any diagnostic full-occurrence scan.

Sampler (`gate_c0_external_sampler.py`, a documented fork of the Gate 2A sampler): attaches to the exact PID, records PID + `GetProcessTimes` creation time, writes a `SAMPLER_READY` flag file immediately on successful attach; the probe polls for that flag (150ms cadence) and does not begin `S0_BASELINE` until it exists. All 27 required phase markers were implemented and fired in the expected order with clean, consistent hold durations (~2.6–2.65s each).

One implementation bug was found and fixed during this work (Python-2-incompatible `open(path, "r", encoding="utf-8")` calls, corrected to `open(path, "rb").read().decode("utf-8")`) — caught by the very discipline this section exists to enforce (an uncaught exception during the first run, not silently patched around).

## 9. C0.4 IDLE RESOURCE RESULTS

All figures are **averages of samples strictly inside their own phase window** (no adjacent-phase borrowing); max-in-window is also reported for the transient admission phase.

| phase | avg Private (MiB) | Δ vs S0 (avg) | Δ vs S0 (max) | n_mem | n_vas |
|---|---|---|---|---|---|
| S0 baseline | 442.94 | — | — | 17 | 4 |
| ADMISSION (begin→end) | 486.70 | +43.76 | **+63.59** | 11 | 3 |
| S2 admitted, empty | 465.71 | **+22.77** | +22.77 | 17 | 5 |
| S3 small view retained | 465.74 | +22.80 | +22.80 | 16 | 4 |
| S4 two views retained | 465.74 | +22.80 | +22.80 | 17 | 4 |
| S5 views released, provider alive | 465.74 | +22.80 | +22.80 | 16 | 4 |
| S6 post-close | 456.65 | +13.71 | +13.72 | 17 | 4 |

**S2→S3→S4→S5 are flat (±0.04 MiB)**: building two tiny views (216+17=233 folds) produces no measurable whole-process delta at this tool's resolution (`GetProcessMemoryInfo`, page-granular). This is an honest finding, not a claim of "zero cost" — a Python-internal measurement (`tracemalloc`) would be needed to see the true, almost certainly single-digit-KB cost of views this small; the OLD Gate B claim of precise sub-MiB view deltas was very likely reading the same kind of noise this measurement now avoids asserting.

**S5→S6 (+13.71 MiB residual, not full recovery to S0):** closing the provider released ~9.1 MiB (22.80→13.71) but did **not** return fully to the S0 baseline within the observed ~2.6s post-close window. Reported precisely rather than claimed as "full recovery" — this is a real, honest, and more conservative number than history would have implied.

**Admission peak instrumented cadence limitation:** 0.15s memory / 0.6s VAS. A higher, instantaneous, unsampled peak may have existed between samples and would not have been captured; the reported +63.59 MiB max is a lower bound on the true peak, not a ceiling.

**Comparison against the historical eager Candidate A figures** (~1.84s / ~63.24 MiB peak / ~38.83 MiB retained): admission wall time is statistically identical (1.798–1.869s across C0.4/C0.5, exactly as architecturally expected — same validator, now literally the same function); peak is now measured at essentially the same order (+63.59 MiB here vs. the historical ~63.24 MiB — **not** the ~3x-lower figure Gate B claimed); retained steady-state (+22.77 MiB) is real and meaningfully lower than eager's ~38.83 MiB, but only by **~1.7x**, not the withdrawn ~5.2x.

## 10. CACHE / VIEW BUDGETS

New qualification-only module `tests/sidecar/qualification/resource_budgets.py` defines explicit, provisional budgets and a `ResourceBudgetExceeded` exception (distinct from both `MasterUnknown` and `AuthorityUnavailable`):

| budget | value | basis |
|---|---|---|
| artifact bytes before whole-file acquisition | 64 MiB | headroom above the real 9.06 MiB official artifact |
| string cache estimated bytes | 4 MiB | ~70x the ~55.6 KB observed for a 233-fold two-view session |
| one family result (occurrence rows) | 5,000 rows | real max=7, synthetic adversarial=500; conservative ceiling |
| one consumer snapshot (occurrence rows) | 50,000 rows | tested LARGE workload=21,989, comfortable headroom |
| total pinned views/cache (bytes) | 20 MiB | provisional aggregate |

These are **provisional C0 qualification limits, not public format limits** (per the brief's own instruction, stated here explicitly since no external requirement justifies these exact numbers).

**Demonstrated on the existing synthetic 500-row/50-destination family:** accepted whole, complete, no truncation (500/500 rows retained, correctly classified `FoldConflict`).

**Demonstrated on a new, deliberately larger synthetic fixture (6,000 occurrences, one fold, 601 destinations):** the SAME wrapper function explicitly **refused** it — `ResourceBudgetExceeded: fold 'overbudgetcontrol' resolves to a family of 6000 occurrence rows, exceeding the qualification budget of 5000 rows...` — raised **before** any partial view was constructed; never truncated; never reported as `MasterUnknown`.

Per-fold budget checks run via a bounded `lookup_fold` probe on each wanted fold **before** committing to full view construction, so an oversized single family is caught pre-emptively, not after partial materialization. Eviction semantics: this qualification candidate has no persistent fold/family-level cache to evict from (confirmed via `resource_snapshot()["family_cache_entries"] == 0` at every measured phase in C0.4/C0.5/C0.6) — so the "eviction must never turn uncovered into MasterUnknown" invariant is trivially satisfied today (there is nothing to wrongly evict), and is flagged as a requirement Gate C1's actual owner design must carry forward once any family-level cache is introduced.

## 11. C0.5 CONSTRAINED LOADED CONTEXT

Run in the user's own live, substantial, already-open project (never closed, never mutated — triggered via a manually-run mainmenu script, per the same operator-action discipline established in Gate B). `sfmApp.GetDocument()`-based project-identity capture (shot count, animation-set count) was attempted and returned `{"available": False}` — the API path guessed did not succeed; this is reported honestly as **unavailable**, not fabricated.

**This context turned out to be genuinely, materially constrained** — unlike the prior Gate B loaded-project measurement (which had ~2.9 GiB free VAS and ~1.98 GiB largest free region, effectively as roomy as idle):

| | S0 baseline (this run) | idle S0 (C0.4, for comparison) |
|---|---|---|
| Private bytes | 3,149.63 MiB | 442.94 MiB |
| Committed VAS | 3,479.70 MiB | ~758.6 MiB |
| **Free VAS** | **293.88 MiB** | ~2,969 MiB |
| **Largest free contiguous region** | **73.44 MiB** | ~1,983 MiB |

This satisfies the brief's own instruction ("prefer a context whose pre-admission headroom is materially constrained, comparable in spirit to the historically concerning Gate 2B state") without any artificial memory consumption — it is what this particular loaded project actually presented.

## 12. C0.5 LOADED RESOURCE RESULTS

Same phase structure and discipline as C0.4, run once (not independently repeated — flagged as a remaining, non-blocking item in §25).

| phase | avg Private (MiB) | Δ vs S0 (avg) | Δ vs S0 (max) |
|---|---|---|---|
| S0 baseline | 3,149.63 | — | — |
| ADMISSION | 3,193.51 | +43.88 | **+63.15** |
| S2 admitted, empty | 3,170.19 | +20.56 | +23.36 |
| S3 small view | 3,170.02 | +20.39 | +20.39 |
| S4 two views | 3,170.02 | +20.39 | +20.39 |
| S5 views released | 3,170.02 | +20.39 | +20.39 |
| S6 post-close | 3,160.94 | +11.31 | +11.31 |

**These numbers are remarkably consistent with the idle-session C0.4 results** (admission peak +63.15 vs. +63.59 MiB; steady retained +20.56 vs. +22.77 MiB) — strong evidence that S1's admission/retention cost is a stable, reproducible property of the architecture itself, essentially independent of host-process load.

**Material safety finding (this is the important part):** in this constrained context, the largest free contiguous VAS region was only **57.62–73.44 MiB** — and S1's admission peak delta (+63.15 MiB max) is **comparable to, and in the worst-observed-sample case exceeds, that largest contiguous region.** This run happened to succeed without visible allocation failure, but the margin was thin, not comfortable. This is flagged as a **material** finding requiring action in Gate C1 (an explicit pre-admission x86 headroom check), not a minor one, and not something this run "disproves" merely by having succeeded once (per the brief's own explicit instruction not to try to disprove the historical +58.97 MiB figure — here a similar-magnitude peak is independently reproduced with a *known*, *narrow* headroom context, which is more informative than the historical figure's unknown cause).

## 13. POST-CLOSE RESULTS

Both C0.4 (idle) and C0.5 (loaded) show **partial, not full, recovery** after `close()`: idle settled at +13.71 MiB above its own baseline, loaded at +11.31 MiB above its own baseline, roughly 2.6s after close in both cases. Neither run showed unbounded or growing residual (both are flat within their own post-close window), and VAS free/largest-free-region also partially recovered (idle: unchanged at this scale; loaded: free VAS improved from 226.79→246.08 MiB after close). This is reported as **partial recovery**, not the "full recovery" the withdrawn Gate B claim asserted — a more conservative, defensible characterization.

## 14. C0.6 WITHHELD LATE VOCABULARY

**Result: PASS — value is real and material.**

A = "Toes" (2,510 folds), B = "Wings" (2,967 known folds) + 1 genuinely absent sentinel fold (2,968 total), precomputed on desktop before the measured SFM process launched, confirmed disjoint by construction and by assertion in-process.

**Withheld-B proof (corrected mid-run — see below):** the first proof attempt asserted zero string-cache overlap with B's fold-key strings and genuinely failed (35 of 6,071 cached strings, after only processing A, happened to also be B's fold-key spellings). Root cause: this is **exactly** the binary-search-pivot-overlap phenomenon the C0.6 brief itself explicitly anticipated ("Binary-search pivot strings may naturally overlap; report cache counters rather than pretending no implementation-level overlap can occur") — resolving any of A's fold keys via binary search over the (alphabetically sorted) FOLD TABLE necessarily probes pivot keys spread across the whole table, some of which land on unrelated Wings-prefixed spellings purely as comparison bytes, never as resolved occurrence data. The check was corrected to the properly-scoped claim: zero fold/family-level cache entries exist before B's own timed request (`family_cache_entries == 0`, true throughout — this provider has no persistent fold-level cache at all), and the informational pivot-overlap count (35) is reported rather than hidden. Final: 8/8 PASS.

| | value |
|---|---|
| T2 prepare A (first scan) | 2.607s |
| S1 admission | 1.727s |
| S1 acquire A | 0.124s |
| T2 uncovered-detection (B) | 0.000s (trivial set difference) |
| **T2 authority acquisition (B, real TXT rescan)** | **2.624s** |
| T2 total B | 2.626s |
| **S1 total B (first-ever request, decisive measurement)** | **0.161s** |
| T2 view B folded keys | 5,477 (A∪B cumulative, coalesced scan) |
| S1 view B folded keys | 2,967 |
| T2 vs S1 payload equality (B's folded-key set) | **identical, 0 diff** |

## 15. T2 VS S1 VALUE RESULT

**Speedup for the decisive, genuinely-withheld late-vocabulary expansion: 2.626s / 0.161s ≈ 16.3x.** This is a real authority-layer speedup for one specific operation — not a whole-Normalizer-command speedup, and not claimed as such. The payload equality check (identical folded-key sets, 0 diff) confirms this speedup is not bought by returning a smaller/wrong answer.

## 16. HISTORICAL GATE B CLAIMS WITHDRAWN/PRESERVED

**Withdrawn** (per the brief's explicit instruction, and superseded by the C0.4/C0.5 measurements above):
- "+7.41 MiB retained" (idle steady) — superseded by +22.77 MiB (idle) / +20.56 MiB (loaded), measured with a cleaner phase-isolation method.
- "+21.11 MiB peak" (idle admission) — superseded by +43.76 MiB avg / +63.59 MiB max.
- "~5.2x smaller than eager retained" / "~3x smaller than eager peak" — superseded by ~1.7x smaller retained; peak now essentially matches the historical eager figure, not 3x smaller.
- "16/32 MiB idle PASS" — both now MISS against the same (non-normative) targets, though not disqualifying (see §19).
- "Full post-close recovery" — superseded by "partial recovery" (+13.71 MiB idle / +11.31 MiB loaded residual).
- The three T1/T2/S1 desktop-vs-embedded speedup ratios computed against the eager BINARY reader specifically (Gate B §6) are **preserved** (not touched by this gate) since C0 did not re-examine that specific comparison.

**Preserved** (re-confirmed or not contradicted by any C0 work):
- 183/183 desktop semantic parity and 126/126 (now newly 21/21 + 8/8 + 8/8 = additional real-embedded PASS counts under C0) — parity holds.
- The large-scope crossover (S1 slower than the eager binary reader at ~17% of total fold space) — untouched, not re-optimized, not re-measured this gate.
- Two-consumer sharing (one provider, no duplicate authority) — not re-run this gate but not contradicted.
- The 18x–104x late-scope speedup claim from Gate B — **not directly re-used**; C0.6 independently re-measured a genuinely withheld late scope and got a materially consistent ~16.3x, using a corrected (non-prewarmed) methodology, which is stronger evidence than Gate B's own figure, not merely a repeat of it.
- Loaded-project admission wall time (~1.8–1.9s) — reconfirmed twice more in C0.5.

## 17. WHAT C0 PROVES

- The actual, unmodified Normalizer consumer functions (not mirrors) behave identically whether backed by a TXT-derived or sidecar-derived view, across 7 required categories including exact conflict-exception-message parity.
- A precise, evidence-backed, testable Normalizer-source compatibility profile exists, with explicit (never-`MasterUnknown`) refusal for the two concretely-demonstrated divergence classes.
- There is now exactly one validation implementation shared by production and the qualification candidate, with a specific, previously-real reference-cycle defect identified and fixed at the source.
- Under a genuinely careful, phase-isolated, pre-ready-sampler measurement methodology, S1's admission is real but its resource profile is more modest than previously claimed: real retained-memory advantage (~1.7x vs. eager), but peak memory essentially matches the eager path, and post-close recovery is partial, not full.
- A materially constrained real loaded-project context reproduced admission peaks of similar magnitude to the historical unexplained loaded-project figure, this time in a context whose narrow VAS headroom is directly measured and disclosed — surfacing a genuine, actionable resource-safety margin question for Gate C1.
- Explicit, enforced, non-truncating resource budgets exist and were proven to work in both directions (accept-in-budget, refuse-out-of-budget) on real fixtures.
- The genuinely-withheld late-vocabulary value case is real (~16.3x) under a corrected, rigorously-non-prewarmed methodology.

## 18. WHAT C0 DOES NOT PROVE

- No claim about artist-facing Normalizer command latency.
- No claim that S1 is production-ready — this remains a qualification-only harness; the shared-validator delegation is the only production-adjacent change, and it is unstaged.
- No independent reconfirmation of the C0.5 loaded-project measurement (single run) — its numbers are consistent with C0.4's idle numbers, which is reassuring, but the specific VAS-headroom safety margin finding has not been repeated.
- No resolution of the large-scope crossover or the unbounded-single-family architecture question beyond the C0.7 budget mechanism (which refuses rather than solves the underlying crossover).
- No claim that Character Preset or any second consumer can safely share this provider — untested this gate.
- No production integration, no format v1 freeze, no Candidate B/C evidence — all explicitly out of scope and untouched.

## 19. C1 AUTHORIZATION OR STOP

All ten C0-PASS criteria (brief §"C0 final verdict"):
1. Actual Normalizer consumer/error parity PASS for the declared profile — **YES** (§4).
2. Explicit compatible source profile + explicit refusal tests PASS — **YES** (§5).
3. Complete integrity validator contract consolidated/promotion-safe — **YES** (§6–7).
4. Clean idle resource phases valid — **YES**, with the two claim-strength corrections above (§8–9).
5. Clean constrained-loaded resource phases valid — **YES** (§11–13), and materially informative.
6. Admitted resource envelope acceptable under existing resource guard — **CONDITIONAL**: acceptable in the idle case; in the constrained-loaded case the peak is close to the observed headroom ceiling — treated as a required Gate C1 design input (explicit pre-admission headroom check), not a blocker to defining Gate C1.
7. Real cache/result/view budgets enforced — **YES** (§10).
8. Genuinely withheld late-vocabulary value remains material — **YES**, ~16.3x (§14–15).
9. No semantic weakening — **YES**, confirmed by full regression both after the reader.py fix and after every qualification-module change.
10. Official artifact and Master unchanged — **YES**, reverified repeatedly.

**Verdict: C0 PASS — PROCEED TO C1 OWNER QUALIFICATION**, with the explicit carry-forward requirement that Gate C1's design include a pre-admission x86 headroom check (criterion 6) before any production consideration.

## 20. SAFETY / CLEANUP

- Production Normalizer: unchanged (reverified after every real-SFM session).
- Binary format (`format.py`): unchanged.
- Canonical Master: unchanged (reverified repeatedly).
- `sfm_init.py`: unchanged (reverified after every real-SFM session).
- No native Rebuild was invoked, no model was mutated, no Character Preset code was touched.
- All temporary SFM deployments (`gate_c0_deploy/`, autoinit probes, mainmenu probes) were removed after use; no `.pyc` residue or stray files remain in `usermod/scripts/`.
- The user's live SFM session (used for C0.5) was never closed, never mutated, and remained open and unaffected throughout and after this gate.
- One production file (`reader.py`) and the qualification module directory were intentionally modified per this gate's own explicit, pre-authorized production-edit rule — see §6/§7/§21 for exactly what and why. Nothing was staged or committed.

## 21. GIT STATE

```
 M tests/sidecar/qualification/bounded_provider.py   (delegates to reader._validate_and_decode; adds resource_snapshot()/budget-support introspection methods)
 M tools/sfm_master_sidecar/reader.py                (closure-cycle fix in _validate_and_decode; no public API/format change)
?? tests/sidecar/qualification/normalizer_source_profile.py   (new, C0.2)
?? tests/sidecar/qualification/resource_budgets.py            (new, C0.7)
```
Plus the pre-existing, unrelated untracked files already present before this gate (Flex Bone/Sexual Bones/Phase2 artifacts, Master backups, the Astra Round 2 evidence bundle) — untouched. `git diff --check`: clean. Nothing staged (`git diff --cached --name-only` empty). No commits made.
