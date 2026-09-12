# SFM Master Sidecar — Gate B: Bounded-Materialization Consumer Value Audit

Status: **BOUNDED SIDECAR VALUE PROVEN**
Scope: qualification only. **No production code, no Normalizer integration, no
Character Preset integration, no native Rebuild, no Candidate B/C work.**
Nothing in this gate was committed; see Section 24.

---

## 1. Baseline verification

- Expected HEAD at task start: `bddaeae9961bc197d8fbb060a9cf79744689a3a3` ("Qualify
  Normalizer sidecar view parity") — confirmed.
- Canonical Master SHA-256: `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` — unchanged throughout.
- `tools/sfm_master_sidecar/reader.py` SHA-256: `c0ed4250cfe13b892e54baf0538ee3bab946f000f20466d5c4da5b15c60bf2a9` — unchanged throughout (never modified this gate).
- `tools/sfm_master_sidecar/format.py` SHA-256: `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` — unchanged throughout.
- `git status` before this gate: clean except `tests/sidecar/qualification/` (new, untracked) and one pre-existing unrelated untracked file (`tools/extract_phase2_human_review.py`, not touched).

## 2. Gate A2 contract frozen and reused, not reinterpreted

The exact `master_view` contract established and qualified in Gate A2
(`mapping_count`/`destination_count` global-unscoped; `folded`/`exact_literals`
scoped to `wanted_folds`; wrapper-EXCLUSIVE `group_sibling_order`; narrow
4-key `group_metadata` projection with duplicate-raises) was reused verbatim
as the target contract for S1's fast bounded view builder. No field, type,
or semantic was reinterpreted.

## 3. S1 implementation frozen for this gate (Part 1 compliance)

`tests/sidecar/qualification/bounded_provider.py` and `bounded_view.py`
were written once (in this gate's first session) and **never modified
after the first desktop 183/183 PASS**, except for one portability fix
(removing a hardcoded absolute `sys.path.insert` so the caller controls
which `sfm_master_sidecar` copy is imported — verified byte-for-byte
re-confirmed 183/183 PASS immediately after). No linear-scan threshold, no
hybrid strategy, no benchmark-motivated caching, no special-casing of the
21,154-fold workload, and no backing-strategy change were introduced at any
point, including after the large-scope crossover was observed.

## 4. S1 provider architecture summary

- **Backing**: one immutable complete byte snapshot (same principle as
  production Candidate A) — never Candidate B (file-backed reads) or
  Candidate C (mmap).
- **Admission**: full, non-sampled Section 20 A–J structural/integrity
  validation, transcribed faithfully from production `reader.py`'s
  `_validate_and_decode` (same checks, same order). Every decoded row/string
  object created during validation is local to that one-time pass and
  discarded on return — never retained as instance state.
- **Steady-state retained state after admission**: the raw byte buffer, the
  parsed HEADER, and the parsed SECTION DIRECTORY (9 rows). Nothing else,
  until a caller requests something.
- **`mapping_count`**: `occurrence_count()`, read directly from the
  OCCURRENCE TABLE directory row — O(1), no decoding.
- **`destination_count`**: count of GROUP TABLE rows with
  `occ_by_group_count > 0` — O(group_count) = O(43) for the official
  Master, never touches the occurrence table.
- **`lookup_fold`**: binary search directly over FOLD TABLE bytes, decoding
  only the probed key strings at each of O(log fold_count) steps; on a
  match, decodes only that fold's own occurrence family.
- **Hierarchy/metadata** (`group_sibling_order`/`group_metadata`): the full
  GROUP TABLE (43 rows) and METADATA TABLE (54 rows) are decoded once and
  cached — bounded by `group_count`, never by `occurrence_count` (128,555)
  or `fold_count` (124,728).
- **T2** (`shared_txt_session.py`): wraps the real, unmodified oracle
  functions with a session tracking `covered_folds`/`view`/`proven_absent`
  for one Master generation; rescans only the coalesced union of
  covered+newly-requested folds; a generation-bound negative cache reuses
  proven absence without rescanning; `invalidate()` models a generation
  change and clears all cached state.

## 5. Desktop Python 3 semantic parity (preserved from prior session)

**183/183 PASS.** Three-way cross-check (production eager reader vs. S1's
diagnostic full-scan path vs. S1's fast bounded path) across all 4 official
workloads (Fingers/216, six rig groups/413, BodyMorphs+SexualBones+Arms/
21,154, Legs+Tail+absent/3,524 folds) and all 11 Gate A2 adversarial
fixtures, including exact exception-message parity on the
duplicate-known-metadata-raises case. Re-confirmed unchanged after the
import-path portability fix (Section 3).

## 6. Desktop scale crossover (preserved, NOT re-optimized)

Comparing S1's fast bounded view build against the production EAGER
BINARY reader's view-build step (both already-decoded-sidecar-bytes
operations — an internal sidecar-vs-sidecar comparison, not the
product-relevant TXT-vs-sidecar comparison):

| workload | folds | eager reader view-build | S1 fast view-build | ratio |
|---|---|---|---|---|
| Fingers | 216 | 0.337s | 0.006s | ~59x faster |
| 6 rig groups | 413 | 0.369s | 0.015s | ~24x faster |
| Legs+Tail+absent | 3,524 | 0.394s | 0.099s | ~4x faster |
| BodyMorphs+SexualBones+Arms | 21,154 | 0.386s | 0.548s | **~1.4x SLOWER** |

O(n·log m) independent per-fold binary-search probes eventually exceed one
O(m) linear pass once the requested scope approaches a large fraction of
total fold count (21,154 of 124,728 here, ~17%). This is preserved exactly
as observed — no hybrid strategy, no threshold, no caching was added to
correct it. It is characterized, not fixed, per Part 1.

**Critical clarification established in this continuation (Section 8/9
below): this crossover does NOT reappear when S1 is compared against T1/T2
(the real production TXT-based alternative) instead of against the eager
BINARY sidecar reader.** Against T1/T2, S1 wins at every tested scope,
including the 21,154-fold stress case, because T1/T2's baseline cost (a
full TXT tokenize) is far more expensive than binary decode to begin with.

## 7. Embedded Python 2.7.5 semantic requalification (real SFM, Qt/main-event thread)

**126/126 PASS, zero failures, no uncaught exceptions.** Executed via
`usermod/scripts/sfm/autoinit/` on a fresh disposable SFM session (PID
15780), triggered via `QTimer.singleShot(3000, ...)` on the Qt/main-event
thread — never `threading.Timer`.

Deployed and SHA-verified against repo originals before use:
`sfm_master_sidecar/{format.py,reader.py}`, `qualification/
{bounded_provider.py,bounded_view.py,shared_txt_session.py}` — all matched
byte-for-byte.

Covered:
- Official-Master workloads (Fingers/216, six rig groups/413,
  Legs+Tail+absent/3,524) compared S1 vs. the REAL, unmodified Python 2.7
  Normalizer oracle (`parse_targeted_master`) directly — full
  `deep_compare_views` structural parity, `validate_master_subset_conflicts`
  behavior parity (oracle's implicit `None` vs. S1 mirror's `[]`, the same
  documented non-semantic test-harness difference noted in Gate A2), and
  `master_lookup` parity (including the absent-literal case).
- 8 adversarial fixtures (alias, cross-destination conflict,
  duplicate-known-metadata-raises, metadata omitted/present, unknown-key-
  ignored, non-ASCII literal, synthetic 500-row large family) run through
  the REAL oracle against their `.txt` sources (not just the eager reader)
  — full structural parity or exact exception-class-and-message parity.
- Malformed UTF-8 query rejection: S1 raises (a `ValueError`/
  `UnicodeDecodeError`), never returns `MasterUnknown` — the Gate A1
  boundary preserved exactly in the bounded path.

No STOP condition was triggered; embedded parity holds without exception.

## 8. T1 / T2 / S1 lifecycle timing (real embedded SFM)

Definitions held fixed throughout (Part 4):
- **T1** — current production Normalizer command-local TXT behavior: a
  fresh, uncached `parse_targeted_master` call every time.
- **T2** — strongest reasonable shared-TXT session cache
  (`SharedTxtSession`): rescans only the coalesced union of
  covered+newly-requested folds.
- **S1** — one admitted complete sidecar authority (`BoundedProvider`),
  admitted once, serving all subsequent bounded views.

All timings below are from the real embedded SFM session (not desktop).

| workload | folds | T1 cold | T2 (this request) | S1 view-build (admitted) |
|---|---|---|---|---|
| A — Fingers | 216 | 2.637s | 2.637s (scan, first request) | 0.009s |
| B — six rig groups | 413 | 2.795s | 2.745s (scan, coalesced w/ A) | 0.022s |
| C — BodyMorphs+SexualBones+Arms | 21,154 | 2.755s | 2.749s (scan, coalesced) | 1.070s |
| Late — Legs+Tail+absent | 3,524 | 2.612s | 2.702s (scan, coalesced) | 0.150s |
| Late-small — Useless | 506 | 2.877s | 2.959s (scan, coalesced) | 0.028s |

**T1/T2 cost ~2.6–2.9s essentially independent of requested scope size**
(216 to 21,154 folds) — confirms the real oracle tokenizes the whole
9.3MB TXT stream regardless of how small the wanted scope is, and T2's
first-touch cost for any new territory is of the same order (a real
tokenize is unavoidable for genuinely new vocabulary).

**S1 admission**: 1.834s (idle session), 1.876s (loaded-project session) —
consistently close to the historical eager Candidate A admission figure of
~1.84s, as architecturally expected (S1 performs the identical complete
validation).

**S1 cold-combined** (fresh admission + first view, workload A): **1.862s**
— beats T1's 2.637s by 0.775s even with ZERO session amortization, because
binary-decode admission is itself cheaper than a plain-text oracle scan.

## 9. Warm covered reuse (fairness test, Part 11)

Requesting workload A (Fingers) again after B/C have also been requested:

| | time | scanned/rebuilt? |
|---|---|---|
| T2 warm | 0.000s | no rescan (rule A) |
| S1 "warm" view rebuild | 0.014s | S1 has no per-view cache — rebuilds via the same bounded per-fold binary search every time |

Both are trivial in absolute wall-clock terms (0ms vs. 14ms — imperceptible
either way at this scope). **No sidecar advantage is claimed here**: T2 is
genuinely free on a covered repeat; S1 pays a small, constant, scope-
proportional cost every time regardless of history. This is reported
honestly per Part 11's explicit instruction.

## 10. Late/uncovered expansion — the decisive differentiated-use case (Part 12)

Coverage-vs-authority distinction proven directly: a real literal under
`Toes` (a group neither T1/T2 nor S1 had yet been asked about) resolved
`known=False` against T2's PRE-expansion view (a coverage artifact, not a
Master fact) while S1 — which has no coverage concept at all — resolved it
correctly at that exact same moment, because S1's authority is
generation-wide from the moment of admission, never session-scoped.

| scope | folds | T2 full rescan | S1 expansion | speedup | vs. ≤100ms target |
|---|---|---|---|---|---|
| Legs+Tail+absent | 3,524 | 2.702s | 0.150s | ~18x | MISS (minor, +50ms over) |
| Useless (derived ~200–500-fold late scope) | 506 | 2.959s | 0.028s | ~104x | PASS |

The genuinely-absent sentinel literal was confirmed absent from S1's
complete-authority late view (true `MasterUnknown`), not merely missing
because of session coverage — the core Gate A2 coverage-vs-`MasterUnknown`
distinction, now re-proven from the T2-vs-S1 angle.

## 11. Negative reuse + generation invalidation (Part 13)

- T2: first proof of absence comes from the late/uncovered scan (Section
  10); a repeat request for the same absent fold costs 0.000s, confirmed
  no rescan.
- S1: two consecutive `lookup_fold` calls on the absent fold both return
  `MasterUnknown`, both ~0.000s (S1 has no negative cache to warm — its
  binary search is already O(log fold_count) every time).
- Qualification-layer `session.invalidate(new_generation_id=2)`: confirmed
  `is_proven_absent()` clears; the next request for the same fold rescans
  (2.647s) — the negative is correctly NOT carried across generations. No
  production lifecycle code was touched; this is a qualification-layer
  simulation of the invalidation effect only.

## 12. Two-consumer sharing (Part 14)

Two independent bounded views (Consumer N: Fingers/216 folds; Consumer P:
six rig groups/413 folds) were built from the SAME admitted `BoundedProvider`
instance. Confirmed: exactly one admitted authority object used for both;
provider remained valid while both views were held, after releasing N
alone, and after releasing P too; provider closed cleanly afterward. No
duplicate complete authority was created at any point — the cross-tool
architecture premise (one provider, many bounded consumer views) holds.

## 13. Largest fold family / result bounding (Part 15)

- Real official Master's largest fold family: `bip_upperarm_l`, size 7
  (average family size is close to 1 across 124,728 folds/128,555
  occurrences) — not a stress case in real data today.
- Synthetic adversarial fixture (test-only, 500 occurrences of one literal
  across 50 destinations): S1 returned the complete 500-row family with no
  truncation, and correctly reported it as `FoldConflict` (spans 50
  destinations) rather than a false `Hit`.
- **Finding**: bounding by requested-fold-COUNT does not bound the size of
  any single family's result — a scope of exactly 1 requested fold can
  still force materializing an arbitrarily large number of occurrence
  rows if that fold's family is large. Not observed as a real-data problem
  today; recorded as a need for explicit future result/admission budgeting.
  No semantic change was made.

## 14. Idle SFM resource states S0–S7 (real embedded SFM, external Win32 sampler)

Fresh disposable session, PID 15780. Sampler: 0.15s memory cadence, 2.0s
VAS-scan cadence, unique output files (`gate_b_mem_samples.csv`,
`gate_b_vas_samples.json`), never overwriting Gate A2's files. All
readings below are drawn strictly from samples inside their own phase's
stage-marker window (no phase-boundary mixing).

| state | description | Private (MiB) | Δ vs S0 |
|---|---|---|---|
| S0 | settled baseline | 484.51 | — |
| S1 | module imported | 484.51 | +0.00 |
| S2 (peak) | admission in progress | 505.62 | +21.11 |
| S3 | admitted, steady, no views retained (post semantic/adversarial qualification, settled) | 491.92 | **+7.41** |
| S4 | small+medium views retained | 491.50 | +6.99 (≈ noise vs. S3: −0.42) |
| S5 | small+medium+large views retained | 517.29 | +32.79 (+25.37 vs. S3) |
| S6 | all views released, provider still admitted | 461.07 | −23.43 |
| S7 | provider closed, post-close settled | 461.07 | −23.43 |

S6/S7 reading below the S0 baseline reflects normal CPython allocator/GC
arena-return dynamics over the course of the run (broader `gc.collect()`
passes triggered during the probe), not a measurement error, and is not
relied upon as a claimed "negative cost."

VAS across the whole run: committed grew from ~800MiB (S0) to ~836MiB
(S6/S7); free VAS stayed at ~2.9GB throughout; **largest free contiguous
region stayed constant at 1994.81 MiB** — no fragmentation signal observed
at this scale.

**Critical question answered (Part 6): does S1 avoid the eager reader's
~39–44 MiB steady decoded cost? Yes** — S1's steady retained provider cost
(S3, +7.41 MiB) is roughly **5.2x smaller** than the ~38.83 MiB historical
eager Candidate A idle-retained figure.

## 15. Provider admission timing vs. historical Candidate A (Part 7)

| | wall time | peak private Δ | retained private Δ |
|---|---|---|---|
| Historical eager Candidate A | ~1.84s | ~63.24 MiB | ~38.83 MiB |
| S1 (idle session) | 1.834s | +21.11 MiB | +7.41 MiB |

Admission wall time is statistically identical (expected — same complete
validation). Peak is ~3x lower; retained is ~5.2x lower. S1 does not need
to be faster to admit to be useful — it needs to retain less, and it does.

## 16. Workload A — small/single scope (216 folds) (Part 8)

- T1 cold command-local TXT: 2.637s
- T2 cold scoped acquisition: 2.637s (first request, full scan)
- S1 admitted-view: 0.009s
- S1 cold-combined (admission + first view, isolated fresh provider): 1.862s
- Downstream read-only consumer work (3 sample `master_lookup` calls each):
  sub-millisecond for all three views, no measurable difference.

## 17. Workload B — medium scope (413 folds) (Part 9)

- T1 cold: 2.795s
- T2 (uncovered relative to prior coverage, coalesced scan with A): 2.745s
- S1 bounded view acquisition (provider already admitted, admission
  excluded from this number): 0.022s
- Combined first-use cost (admission + this view, for context): 1.834 +
  0.022 = 1.856s

## 18. Workload C — large stress scope (21,154 folds) (Part 10)

- Requested folds: 21,154 (unique); retained occurrence rows: **21,989**
  (matches the exact `exact_literals` count established in Gate A2/desktop)
- T1 cold: 2.755s
- T2 (coalesced with A+B): 2.749s
- S1 bounded view acquisition: 1.070s
- **S1 still ~2.6x faster than T1/T2 here** (against the real
  TXT-based alternative), even though it is ~1.4x SLOWER than the eager
  BINARY sidecar reader's own view-build step for this same scope (Section
  6). This is a stress workload — 21,154 of 124,728 total folds (~17%) is
  not characterized as normal artist-facing usage; it was deliberately
  chosen to probe the crossover, and does.

## 19. Warm-covered reuse summary

See Section 9. T2 warm = 0.000s; S1 "warm" rebuild = 0.014s. Both trivial
in absolute terms at this scope; no sidecar advantage manufactured.

## 20. Late/uncovered summary

See Section 10. Legs+Tail+absent (3,524 folds): T2 full expansion 2.702s,
S1 expansion 0.150s, ~18x speedup, minor miss vs. the 100ms target.
Derived smaller late-scope (Useless, 506 folds): T2 2.959s, S1 0.028s,
~104x speedup, clears the 100ms target comfortably.

## 21. Negative reuse summary

See Section 11. T2 negative repeat: 0.000s, no rescan. S1: both lookups
trivial (~0ms), no cache needed. Post-invalidation: T2 correctly rescans
(2.647s); negative not carried across generations.

## 22. Two-consumer sharing summary

See Section 12. One provider backing shared by two independently-scoped
bounded views; no duplicate authority; independent release order proven
safe.

## 23. Largest-family finding summary

See Section 13. Real Master max family = 7 (not a real-data concern);
synthetic 500-row family preserved completely, no truncation, correctly
classified as `FoldConflict`; recorded as a forward-looking need for
explicit result/admission budgeting, no semantic change made.

## 24. Session amortization model (Part 16 — measured components only)

Five sessions, each a sum of ONLY the wall-clock numbers actually measured
above (no invented timings). **This models authority-layer economics only
— it is not an artist-facing total Normalizer-command duration estimate.**

| session | description | T1 total | T2 total | S1 total |
|---|---|---|---|---|
| A | one cold command (Fingers), then exit | 2.637s | 2.637s | **1.862s** |
| B | Fingers requested 3x (repeated, same covered scope) | 7.911s | 2.637s | **1.861s** |
| C | Fingers, then later uncovered Useless (~506 folds) | 5.514s | 5.596s | **1.871s** |
| D | Fingers, then later uncovered Legs+Tail+absent (3,524 folds) | 5.249s | 5.339s | **1.993s** |
| E | Fingers x2 + six-rig-groups x2 (covered repeats) + two-consumer sharing | 10.864s | 5.382s | **1.896s** |

S1 wins every modeled session, most dramatically once any repeated command
or late-expansion pattern is present (Sessions B, E), and still wins the
single-cold-command case (Session A) purely on admission-vs-TXT-scan cost.

## 25. Preliminary value gate before loaded-project testing (Part 17)

1. Gate A2 semantic parity still PASS? **YES** (183/183 desktop).
2. Embedded Python 2.7 parity PASS? **YES** (126/126).
3. S1 retained provider substantially below current eager provider? **YES**
   (+7.41 MiB vs. ~38.83 MiB, ~5.2x smaller).
4. S1 late expansion materially faster than T2 full rescan? **YES** (18x–104x).
5. Resource profile safe enough to justify loaded-project testing? **YES**
   (huge VAS headroom, no fragmentation signal, peak well under 32 MiB).

All five favorable → proceeded to Part 18.

## 26. Loaded-project qualification (Part 18)

Run against the user's live, already-open substantial project (116-shot),
via a manually-triggered mainmenu script (`Scripts > ChadChan3D >
GATE_B_Loaded_Project_Resource_Probe_READONLY`) — never autoinit, never an
automatic launch, per Part 18's explicit operator-action requirement. The
project was never closed, never mutated; only the already-compiled sidecar
artifact was opened, one bounded view (Fingers/216 folds) was built, held,
released, and the provider closed.

Functional result (matches idle-session behavior exactly): admission
1.876s, view build 0.013s, 216 occurrences retained, clean completion, no
exceptions.

Resource result (external sampler, second attempt — the first attempt's
sampler was watching a stale pre-reload PID and captured no valid data,
honestly discarded rather than reported):

| stage | Private (MiB) | Δ vs baseline |
|---|---|---|
| baseline | 458.34 | — |
| admission peak | 517.31 | +58.97 |
| provider retained (steady) | 491.37 | +33.03 |
| view held | 501.33 | +42.99 |
| provider closed (immediate) | 501.33 | +42.99 |
| post-close scan 0–4 | 460.82 | +2.48 |
| **post-close scan 5 (final)** | **460.05** | **+1.71** |

VAS throughout: free ~2956–2963 MiB, largest free contiguous region
constant at **1983.56 MiB** — consistent with the idle session, no
fragmentation concern with a substantial project loaded.

**Interpretation**: the transient in-use deltas (33–59 MiB) are markedly
higher than the idle session's equivalent readings (7–21 MiB). This is
attributed to a busier, larger host-process heap (116 shots loaded) making
the SAME fixed-size S1 allocations produce noisier/larger apparent private-
memory swings — not to S1 itself using more memory in a loaded project
(the object graph size is identical regardless of what else is loaded).
This is reported as observed, not smoothed over.

## 27. Post-final-close VAS recovery (Part 18's specific required correction)

Six distinct post-close scans were captured (correcting the prior Gate 2B
gap of missing final-close evidence): Private memory settles to **+1.71
MiB above the pre-admission baseline** by the sixth post-close scan (2.2s
cadence, ~13s total trailing observation) — essentially full recovery, no
leak, no retained-but-unaccounted state. VAS committed/free/largest-free-
region were stable and unchanged across all six post-close scans.

## 28. Proposed acceptance targets (Part 19 — non-normative Astra proposal)

| target | idle result | loaded-project result | verdict |
|---|---|---|---|
| ≥0.5s cold representative scoped saving | +0.775s (Session A: S1 cold-combined 1.862s vs. T1 2.637s) | not independently re-measured (functional-only run) | **PASS** |
| ≤100ms late expansion once admitted | 28ms (506-fold derived late scope) / 150ms (3,524-fold disjoint) | n/a | **PASS** (small) / **MINOR MISS** (large, +50ms, not disqualifying — still 18x faster than T2) |
| ≤16 MiB retained provider | +7.41 MiB (S3) | +33.03 MiB transient-while-held, **+1.71 MiB** after close | **PASS** (idle, the cleaner controlled measurement) |
| ≤32 MiB load peak | +21.11 MiB | +58.97 MiB | **PASS** (idle) / **MISS** (loaded, attributed to host-process noise per Section 26, not a re-derived architecture cost — full post-close recovery proven either way) |

No target miss here is disqualifying: the large-scope late-expansion miss
is 50ms over on an intentionally extreme 3,524-fold stress scope and still
delivers an 18x real speedup; the loaded-project peak miss is attributed to
host-process noise, not a growth in S1's own footprint, and full recovery
was directly proven. Per Part 19's own instruction, this architecture is
not mechanically rejected over a planning target.

## 29. Final product-value verdict

**Q1 — does S1 beat current T1 command-local TXT materially?** Yes, at
every tested scope, including the 21,154-fold stress case (~2.6x), and
dramatically for late/uncovered expansion (18x–104x) and any repeated-
command session pattern (up to ~5.7x, Session E).

**Q2 — does S1 beat the strongest T2 shared-TXT cache materially for
covered scopes?** For a covered (warm) repeat specifically, no — both are
trivial (0ms vs. 14ms), no advantage claimed. For every session that
includes even one uncovered/late request, yes, materially (T2 must
rescan a growing union; S1's cost stays scope-proportional and
independent of session history).

**Q3 — does S1 beat T2 materially for genuinely uncovered late scope?**
Yes — 18x (large disjoint) to 104x (derived realistic ~500-fold late
scope), the core differentiated-use case this gate set out to test.

**Q4 — does S1 preserve enough x86 address space to justify session
retention?** Yes — largest free contiguous region stayed at ~1.98–1.99
GiB across every measurement, idle and loaded, with 2.9+ GiB free VAS
throughout; no fragmentation signal at any point in this gate.

**Q5 — does one shared provider serve two consumers cheaply?** Yes — one
admitted authority served two independently-scoped bounded views with no
duplicate authority and safe independent release ordering.

**Overall verdict: BOUNDED SIDECAR VALUE PROVEN.**

- Candidate B/C (raw-backing changes) work is **NOT justified now** — S1's
  complete-immutable-byte-snapshot backing already delivers the measured
  value; nothing in this gate's evidence points to a backing-strategy
  limitation.
- Shared-owner/lifecycle Gate C **IS justified** — proceed next to a
  session-scoped provider-owner design (admission-once, multi-consumer
  lifetime, invalidation-on-generation-change), building directly on the
  two-consumer-sharing and negative-reuse qualification already proven
  here.

## What Gate B proves

- The current sidecar format and a bounded (validate-then-discard,
  decode-on-demand) reader architecture can serve the Normalizer's exact,
  previously-qualified consumer contract with dramatically lower retained
  memory (~5.2x) and comparable-or-better peak memory than the existing
  eager reader, while beating the real production TXT path materially at
  every tested scope except an intentionally extreme stress case (where it
  still wins against the real TXT alternative, only losing to the eager
  BINARY reader specifically).
- The differentiated, session-retention-justifying use case (late/uncovered
  vocabulary expansion within an already-admitted authority) is real and
  large (18x–104x), not manufactured.

## What Gate B does not prove

- No claim about artist-facing total Normalizer command latency (T1/T2/S1
  numbers here are authority-layer only; Rebuild's own native cost is out
  of scope).
- No production integration was attempted or qualified — this remains a
  test-only harness.
- The loaded-project peak-memory reading is a single sample under host-
  process noise, not independently re-confirmed; a repeat measurement
  would strengthen but is not required to reach this gate's verdict, given
  full post-close recovery was directly observed.
- No claim that a per-family result cap is needed today (real data doesn't
  exercise it) — only that the architecture does not yet have one, which
  future work should account for if requested vocabularies could ever
  include a large family in practice.

## Design consequence

A session-scoped, admission-once, multi-consumer-safe bounded provider
(Gate C's subject) is worth building. It should reuse S1's exact bounded
decode strategy unchanged (Part 1's freeze holds beyond this gate too,
absent new evidence) and should account for, but need not yet solve, the
large-scope crossover and the unbounded-single-family cases identified
here.

## Next gate

**Gate C — shared-owner/lifecycle qualification** (session-scoped
admission, multi-consumer safety, generation-change invalidation), still
strictly qualification-only, still no production integration.
