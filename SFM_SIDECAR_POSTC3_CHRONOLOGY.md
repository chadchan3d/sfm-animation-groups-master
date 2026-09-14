# SFM Sidecar — Chronology / Correction History (B0 through Minimum C3)

Purpose: let an independent reviewer judge whether this project learns from
correction or repeatedly overclaims. Each phase states the question being
answered, the original result, any later correction/reopening, and current
standing as of HEAD `1028adcde35dd7681cfad7db2bbc7c367c7b2565`.

## B0/B1/B2 — sidecar design and compiler/writer/manifest build

- **Question:** Can the Master TXT be compiled into a deterministic, self
  -validating binary sidecar generation with a diagnostic manifest pointer?
- **Original result:** Yes — `compiler.py`/`writer.py`/`manifest.py`/`reader.py`
  built, with exhaustive self-validation (`verify_semantic_parity`) and a hardened
  manifest parser.
- **Later correction/reopening:** None to the compiler/writer/format themselves in
  this arc. The manifest parser's Python-3-only nature was NOT flagged as a problem
  at this stage (it wasn't yet clear it would need to run under Python 2.7 for any
  qualification purpose) — this became relevant only much later, at Minimum C3.
- **Current standing:** Unmodified production code throughout the entire
  B0-through-C3 arc. `format.py`/`reader.py` SHA-256 unchanged since before Gate B;
  `reader.py` changed exactly once (Gate C0.3's closure-cycle fix).

## Gate B — Bounded-materialization consumer value

- **Question:** Is a bounded/on-demand-decoding reader ("S1") semantically identical
  to the eager production reader, and materially cheaper for realistic scopes?
- **Original result:** Yes, qualified with 183 desktop parity/timing checks plus
  real embedded SFM measurement.
- **Later correction/reopening:** Astra Round 2 reopened resource and
  compatibility questions (see below) rather than the semantic-parity result
  itself, which has never been challenged since.
- **Current standing:** `desktop_parity_and_timing.py` still 183/183 today,
  unchanged file, reconfirmed fresh in this evidence-collection session.

## Astra Round 2 — external review

- **Question:** Does the staged Gate C direction (owner/lease/view architecture)
  deserve to proceed, and what must be closed first?
- **Original result:** Seven specific findings requiring closure before further
  architecture work (real-oracle consumer/error parity, Normalizer source-profile
  restriction, validator consolidation, corrected resource measurements, a
  genuinely-withheld late-vocabulary proof, explicit resource budgets).
- **Later correction/reopening:** All seven were closed by Gate C0 (below); none
  were reopened later.
- **Current standing:** Closed, stable. See `10_PRIOR_CONTINUITY/SFM_SIDECAR_ASTRA_ROUND2_AUDIT_2026-09-12.md` in this package for the original findings and `10_PRIOR_CONTINUITY/SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md` for their closure.

## Gate C0 — Promotion prerequisites

- **Question:** Are Astra Round 2's seven findings genuinely closed?
- **Original result:** Yes — real-oracle parity proven directly against the
  production reader/adapter; a source-profile restriction added
  (`normalizer_source_profile.py`); the second hand-copied validator eliminated
  (S1 now delegates to `reader._validate_and_decode`, finding and fixing a genuine
  reference-cycle defect in the process — the ONE production edit in this whole
  arc); resource measurements redone cleanly; a genuinely-withheld late-vocabulary
  proof reframed correctly (distinguishing "no fold-level cache entries" from an
  impossible "zero string-level pivot overlap"); explicit resource budgets added.
- **Later correction/reopening:** None of C0's specific closures were reopened
  later.
- **Current standing:** Stable. `resource_budgets.py`'s original five constants
  (artifact bytes, string-cache bytes, one-family rows, one-snapshot rows,
  total-pinned-view bytes) are unchanged; only the later (Round 3-era, since
  removed) coverage-cache constants were added and then withdrawn.

## Gate C1 / C1R — Shared owner foundation

- **Question:** Can one process-wide owner per namespace, with lazy admission, a
  pre-admission resource guard, explicit leases, and terminal close, be qualified?
- **Original result (C1):** PASS claimed.
- **Later correction (C1R):** Independent code review found FIVE real defects: init
  count mislabeled as registration count; `close()` invalidated active leases
  instead of deferring; the fourth guard criterion was not actually independent of
  the first (`projected_headroom = free_vas`, identical); the test-reset helper
  didn't actually close prior owners; the embedded probe only reproduced one lease
  -release order. All five were repaired, including using real PE-header evidence
  (`sfm.exe`'s `IMAGE_FILE_LARGE_ADDRESS_AWARE` flag) to justify a genuinely
  independent replacement for the fourth guard criterion.
- **Current standing:** The C1R-era fourth guard criterion was ITSELF later removed
  entirely by the Round 3 foundation repair (found redundant/impossible even after
  the C1R fix) — a second correction to the same mechanism. The registration-count
  fix from C1R was also later fully withdrawn (not just fixed) by Round 3, which
  removed the registration-install concept altogether as a simulated claim that
  should never have been asserted in the first place.

## Gate C2 / C2R — Same-generation view/coverage expansion

- **Question:** Can warm reacquisition, late-known-vocabulary expansion, true
  negative coverage, atomic budget refusal, and epoch-mismatch publication guards
  be qualified on top of the C1(R) foundation?
- **Original result (C2):** PASS claimed, introducing the `_EpochCoverage`
  owner-level reusable cache.
- **Later correction (C2R):** Independent review found the new cache had NO
  enforced bound at all despite audit language implying otherwise. Repaired with
  explicit 32 MiB/100,000-entry provisional bounds and FIFO eviction
  (`collections.OrderedDict` for Python-2/3-consistent ordering).
- **Current standing:** The ENTIRE `_EpochCoverage` mechanism — cache, bounds, FIFO
  eviction, everything C2R added — was later deleted wholesale by the Round 3
  foundation repair. This is the clearest example in the whole arc of "learn from a
  correction, then go further and remove the thing entirely" rather than only ever
  patching forward.

## Astra Round 3 — holistic re-audit

- **Question:** With all evidence to date, is the compiled-sidecar +
  owner/lease/view direction still the right engineering choice, and if kept, what
  must change?
- **Original result:** "Keep the compiled-sidecar direction, simplify its owner
  substantially, do not begin C3 yet." Five consequential findings reproduced
  independently (cross-owner lease confusion; incomplete terminal cleanup; C2R's
  cache bounds covering only two containers while the provider's own declared
  string-cache budget was bypassed and negative-only views were zero-accounted; the
  redundant/impossible fourth guard criterion; inaccurate "independent immutable
  payload copies" wording). Verdict: "OVER-ENGINEERED BUT RECOVERABLE."
- **Later correction/reopening:** None — this audit itself has not been
  challenged since; it is the controlling document for both subsequent gates.
- **Current standing:** Controlling. See §3 of the architecture/verification
  document in this package for direct source-level verification of every finding's
  closure.

## Round 3 Foundation Simplification/Repair

- **Question:** Can Astra Round 3's findings be closed by SUBTRACTION (removing
  machinery) rather than by adding more generalized safety infrastructure?
- **Original result:** Yes — `_EpochCoverage`, the registration-install claim, and
  the fourth guard criterion were deleted outright; lease-ownership, registry
  -cleanup, missing-artifact-recovery, decode-cache-bound, negative-accounting, and
  detached-view defects were fixed with the smallest working mechanism in each
  case. Verdict: "ROUND3 FOUNDATION PASS — PROCEED TO MINIMUM C3." 342 desktop + 26
  embedded PASS, 0 FAIL.
- **Later correction/reopening:** None yet.
- **Current standing:** Checkpointed at commit `eace35b3` "Simplify sidecar owner
  foundation"; reconfirmed clean in this evidence-collection session (40/40 on the
  focused Round 3 harness, full regression unchanged).

## Minimum C3 — Freshness / invalidation / retire-drain

- **Question:** Can command-boundary source freshness, candidate/manifest
  compatibility, retirement, drain, close, and lazy G2 readmission be qualified
  with no watcher/poller/hot-replacement/standalone-C4 machinery?
- **Original result:** Yes — one new `RETIRED` owner state plus a new
  `command_boundary.py` orchestration module. Verdict: "MINIMUM C3 PASS — PROCEED
  TO NORMALIZER INTEGRATION ACCEPTANCE." 53 desktop + 24 embedded PASS, 0 FAIL. A
  genuine cross-version defect was found and fixed DURING this same gate (the
  production `manifest.py` parser cannot run under embedded Python 2.7) —
  discovered by the gate's own embedded probe failing on its first run, not
  papered over.
- **Later correction/reopening:** The checkpoint review required the audit to more
  explicitly carry forward the Python-2-manifest-compatibility gap as an unresolved
  item before Normalizer integration acceptance — done in the same checkpoint task,
  before commit.
- **Current standing:** Checkpointed at commit `e1ef50e3` "Qualify sidecar source
  freshness lifecycle" — the current HEAD this evidence package is built from.
  Normalizer integration acceptance has NOT begun (verified directly: zero
  sidecar-related references in the current Normalizer source).

## Pattern observed across the whole chronology

Three mechanisms were each independently reviewed, found deficient, and then
either repaired once more before being removed entirely, or removed outright on
first re-review:

1. The fourth guard criterion: introduced (C1) -> found non-independent, repaired
   with real evidence (C1R) -> found redundant/impossible even after repair,
   removed entirely (Round 3).
2. The registration-install claim: introduced (C1) -> mislabeling fixed (C1R) ->
   found to be a claim that should never have existed, removed entirely (Round 3).
3. The reusable coverage cache: introduced (C2) -> found unbounded, bounded with
   FIFO eviction (C2R) -> found to still not close the real problem (provider
   string-cache bypass, zero-byte negative accounting), removed entirely (Round 3).

Each of these took TWO review cycles to reach its final (subtractive) resolution,
not one. Whether that pattern indicates healthy, catching-real-bugs qualification
discipline or a project that overclaims PASS too early is exactly the judgment this
evidence package is assembled to let Astra make independently — this document
states the pattern factually without adjudicating it.
