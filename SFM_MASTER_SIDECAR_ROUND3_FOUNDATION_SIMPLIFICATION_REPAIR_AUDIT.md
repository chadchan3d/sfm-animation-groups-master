# SFM Master Sidecar — Round 3 Foundation Simplification / Repair Audit

Controlling architecture decision: `SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md`
(committed at `7af34a78194fa22a573280bbced79dcd813f3feb`, "Record sidecar Round 3 architecture audit").

This is a **subtractive** foundation repair, not another architecture-expansion gate. Nothing
in this document authorizes, begins, or scaffolds C3. Nothing here touches production
Normalizer, Character Preset, the Master file, or the binary format.

## 1. VERDICT

**ROUND3 FOUNDATION PASS — PROCEED TO MINIMUM C3**

All five most-consequential findings from the Astra Round 3 holistic audit are closed by
removal or repair, not by adding another generalized safety framework:

1. Cross-owner lease confusion — **fixed** (§5, Repair A).
2. Incomplete terminal cleanup (reusable coverage/lease history/registry retention) —
   **fixed by removal** of the reusable coverage cache entirely (§10, Repair F) plus
   release/close/registry repairs (§6, Repair B).
3. C2R's cache bounds covered only two containers, not the complete retained resource graph
   (provider string-cache budget bypassed; negative-only views zero-accounted) — **fixed**
   (§11 Repair G, §12 Repair H).
4. The redundant fourth guard criterion with an impossible isolation snapshot — **removed**
   (§8, Repair D).
5. "Independent immutable payload copies" was inaccurate (shared mutable rows) — **fixed**
   (§13, Repair I), and made largely moot in the first place by removing the cache that made
   sharing possible (§10).

No PASS claim in this document rests on a historical C1/C2 harness merely "still passing" —
every claim below is backed by either a fresh desktop assertion, a fresh embedded assertion,
or both.

## 2. ROUND 3 CONTROLLING DECISIONS

Per the Astra Round 3 holistic audit and the repair brief, this repair:

- keeps the compiled-sidecar + one-owner + detached-action-view direction;
- narrows C1/C1R and C2/C2R claims that no longer hold (both are REOPENED by the controlling
  audit and are addressed here);
- removes the owner-level cross-action reusable positive/negative coverage cache entirely
  (not merely re-bounds it);
- removes the simulated "registration installation" claim;
- removes the redundant fourth guard criterion;
- does **not** implement real source-change/generation replacement (explicitly deferred to
  minimum C3);
- does **not** replace removed machinery with more generalized infrastructure.

## 3. BASELINE

- Repository: `E:\SFM Animation Group Master`
- Expected baseline HEAD: `7af34a78194fa22a573280bbced79dcd813f3feb` "Record sidecar Round 3
  architecture audit" — confirmed matching before any change was made.
- `git status --short` before any change: clean except the same long-standing pool of
  unrelated pre-existing untracked files (Flex Bone/Sexual Bones/Phase2/historical Gate
  artifacts, Astra evidence bundles) — none touched by this repair.
- `git diff --check`: PASS (clean) before and after.
- Prior C1/C2 checkpoint commits (`0a4790e`, `9c44524`) confirmed present and unaltered at
  HEAD.

## 4. SUBTRACTIONS / REMOVED MACHINERY

Removed from `tests/sidecar/qualification/session_owner.py` entirely (not deprecated, not
left dead-but-present):

- `_EpochCoverage` class (owner-level cross-action reusable positive/negative cache).
- `MasterAuthorityOwner._coverage` attribute, `_new_epoch_coverage()`,
  `evict_reusable_coverage_cache()`, `_require_owner_valid_for_cache_op()`.
- `registration_install_count`, `registration_identity`, module-level
  `_REGISTRATION_ID_COUNTER`.
- `GuardPolicy.min_committed_ceiling_reserve_bytes`,
  `GuardPolicy.assumed_address_space_ceiling_bytes`,
  `GuardPolicy.ASSUMED_ADDRESS_SPACE_CEILING_BYTES`, and the committed-VAS-ceiling guard
  criterion in `evaluate()`.
- `ViewBudgets.coverage_positive_max_bytes`, `ViewBudgets.coverage_negative_max_entries`.

Removed from `tests/sidecar/qualification/resource_budgets.py`:

- `BUDGET_COVERAGE_CACHE_POSITIVE_ESTIMATED_BYTES`, `BUDGET_COVERAGE_CACHE_NEGATIVE_MAX_ENTRIES`
  (there is no owner-level cache left to bound with these).

Nothing was replaced with more general machinery: `acquire_view` is now a plain, private,
per-call resolve-then-publish function with no cross-call state at all (§10).

## 5. LEASE OWNERSHIP (Repair A)

**Defect:** `get_view_via_lease()`/`release_lease()` looked up leases only by owner-local
`lease_id`, so a foreign owner's lease with a colliding ID was accepted.

**Fix:** both methods now check `lease.owner_id != self.owner_id` first and raise
`LeaseRejected` before touching any state.

**Evidence:**

- Desktop (`desktop_round3_foundation_qualification.py`, "Round3 Repair A" section): owner A
  and owner B each independently issue lease ID 1; A's lease cannot authorize B
  (`LeaseRejected`); A's lease cannot release/mutate B's lease (`LeaseRejected`); B's lease
  remains valid after both foreign attempts; A's own lease still authorizes A; A's released
  lease is subsequently rejected. All 6 PASS.
- Embedded (`gate_round3_embedded_probe.py`, phase 2, checks "3:*"): identical scenario
  reproduced in real SFM Python 2.7 — 4/4 PASS, including
  `LeaseRejected('lease 1 belongs to owner 1, not this owner 2 -- does not authorize access')`.

Enforcing source region: `session_owner.py`, `MasterAuthorityOwner.get_view_via_lease` and
`MasterAuthorityOwner.release_lease` (owner_id check, first lines of each method).

## 6. RELEASE / CLOSE / REGISTRY CLEANUP (Repair B)

**Defect:** released leases were tombstoned forever inside `_leases` (only `active` flipped,
entry never removed); `close()` never removed the owner from `_OWNER_REGISTRY`, so a closed
owner could remain registry-discoverable.

**Fix:**

- `release_lease()` now `del self._leases[lease.lease_id]` on a real release. Idempotency for
  a repeated release of the same already-inactive `Lease` object is detected from that
  object's own `.active` flag (the exact object returned by `acquire_view` is the same object
  stored internally), never from a server-side history table.
- `close()`, once zero leases remain, clears `_views`/`_leases` and removes this owner from
  `_OWNER_REGISTRY` if that registry entry still points to this exact object
  (`if _OWNER_REGISTRY.get(self.namespace_identity) is self: del ...`).

**Evidence:**

- Desktop: "release removes owner-held record (no tombstone)"; "repeated release of an
  already-released lease grows no central history"; "terminal close removes owner from the
  process registry"; "a closed owner is never discoverable via the normal registry lookup"
  (`desktop_round3_foundation_qualification.py`, Repair B section, 10/10 PASS) plus the
  updated `desktop_session_owner_qualification.py` Order1/RepairD checks (2 new assertions,
  both PASS).
- Embedded: checks "4:*" (release/repeated-release) and "6:*" (terminal close + registry
  removal) — 4/4 PASS.

Enforcing source region: `session_owner.py`, `MasterAuthorityOwner.release_lease` (the
`del self._leases[...]` line) and `MasterAuthorityOwner.close` (the `_OWNER_REGISTRY` removal
line).

## 7. INIT / REGISTRATION CLAIM CORRECTION (Repair C)

**Defect:** `registration_install_count`/`registration_identity` implied a real installed
callback; this qualification owner never installs one.

**Fix:** removed both attributes and the counter that produced `registration_identity`. Only
`init_call_count` (every call-site attempt) remains, with the docstring narrowed to "3
initialization call sites -> 1 owner object."

**Evidence:** desktop C1.1 ("`init_call_count == 3`", no registration-install assertion
remains) and the new Round3 harness ("3 init call sites -> exactly 1 owner object") — both
PASS. Embedded check "1:*" — 2/2 PASS.

## 8. RESOURCE GUARD CORRECTION (Repair D)

**Defect:** the fourth guard criterion (`4 GiB - committed_vas >= reserve`) was mathematically
redundant with the free-VAS criterion for any physically consistent snapshot, and its own
"independence" isolation fixture summed private+committed+reserved+free to ~4,888 MiB against
a declared 4,096 MiB (4 GiB) ceiling model — an impossible snapshot.

**Fix:** the criterion, its fields, and its isolation fixture are removed. `GuardPolicy` now
evaluates exactly 3 criteria: snapshot validity/types, free VAS, largest free contiguous
region, plus the artifact-byte budget. A new regression check verifies every guard-test
fixture used across the harnesses is physically consistent (VAS components sum to at or under
the 4 GiB assumed ceiling).

**Evidence:** `desktop_session_owner_qualification.py` "Guard D" section (now 3 physical
-consistency checks, all PASS, e.g. `sufficient_snapshot` totals 3,670,016,000 bytes, under
4,294,967,296); `desktop_round3_foundation_qualification.py` confirms
`GuardPolicy` no longer exposes the removed fields and a consistent snapshot still evaluates
OK. Embedded check "GuardPolicy has no committed-ceiling criterion in this runtime" — PASS.

## 9. MISSING-ARTIFACT ADMISSION RECOVERY (Repair E)

**Defect:** `_run_guard()` called `os.path.getsize(self.artifact_path)` for the artifact-byte
budget check without a `try/except`; a missing/unreadable artifact raised an uncaught
`OSError`/`FileNotFoundError` straight out of `_ensure_admitted()` while the owner was still in
`PREPARING`, escaping the state machine's normal recoverable path.

**Fix:** `_run_guard()` now wraps the artifact-metadata lookup in its own `try/except`,
returning `(False, "artifact metadata unavailable: ...")` on failure — guaranteed never to
raise. `_ensure_admitted()` therefore always lands in `UNAVAILABLE` (never allocates a
provider, never publishes a partial lease/view) on this failure, and a later retry after the
artifact is restored returns through `PREPARING` and can succeed normally.

**Evidence:** `desktop_round3_foundation_qualification.py`, "Round3 Repair E" section: missing
artifact raises `ResourceRefused` (not an uncaught OS exception); owner ends in `UNAVAILABLE`;
no provider allocated; no partial lease/view; restoring the artifact and retrying succeeds
with exactly one successful admission. 5/5 PASS. This defect and its fix have no embedded
check in this repair (it is a pure Python-exception-handling path, verified sufficiently on
desktop; the embedded probe budget was spent on genuinely runtime-sensitive items instead —
see §21).

Enforcing source region: `session_owner.py`, `MasterAuthorityOwner._run_guard`.

## 10. ACTION COVERAGE MODEL (Repair F)

**Defect / decision:** the owner-level `_EpochCoverage` cross-action cache is removed
entirely, not merely re-bounded again. Every `acquire_view()` call now:

1. starts from private local candidate state (`candidate_positive`/`candidate_negative`);
2. resolves every requested fold against the already-admitted provider (repeated calls
   re-query — intentionally not optimized in this repair);
3. enforces the per-family and one-snapshot/pinned-view budgets;
4. checks the epoch is unchanged;
5. publishes one detached action view + lease, or discards the candidate entirely.

**Coverage contract:** the published payload now carries an explicit
`proven_negative_folds` field (a `frozenset`) alongside the existing `folded` dict, so a
consumer can distinguish a requested-positive fold, a requested-proven-negative fold, and a
fold this action never requested (present in neither) — without ever inferring a global
negative from absence in some other view.

**Evidence:**

- Desktop: `_coverage` attribute and `_EpochCoverage` class are structurally absent
  (`hasattr` checks, both PASS); repeated action lookup for the same fold across separate
  calls remains correct (PASS); the rewritten C2.1/C2.3 sections (5 PASS) prove repeated
  requests and the positive/negative/uncovered-within-one-view contract directly.
- Embedded: "session_owner has no _EpochCoverage class" (PASS); representative
  positive/negative semantics via `proven_negative_folds` (checks "10:*", 2/2 PASS).

## 11. PROVIDER DECODE-CACHE BOUND (Repair G)

**Defect:** Round 3 reproduced a refused request leaving ~14.84 MiB of estimated provider
string-cache state resident despite a declared 4 MiB qualification budget — the budget
constant existed but was never actually enforced by the owner path.

**Fix:** `MasterAuthorityOwner._enforce_decode_cache_bound()` checks
`provider.string_cache_estimated_bytes()` against `view_budgets.decode_cache_estimated_bytes_
budget` and calls `provider.evict_reusable_cache()` (a whole-cache clear — acceptable per the
brief) when exceeded. `acquire_view()` calls this in a `finally` block wrapping the entire
resolve-then-publish body, so it runs after every attempt: ordinary success, a refused
over-budget request, or an injected candidate failure.

**Evidence:**

- Desktop (`desktop_view_expansion_qualification.py`, "Round3 Repair G" section, 4 PASS):
  bound enforced after an ordinary request; a held action view remains valid after the
  eviction that bound enforcement triggers; bound enforced after a refused (over-budget,
  large-family-fixture) request; bound enforced after an injected candidate failure.
- Embedded (check "9:*", 1/1 PASS): bound enforced after a refused over-budget request against
  the same 500-occurrence large-family fixture, deployed and SHA-verified against the repo
  original.

Enforcing source region: `session_owner.py`,
`MasterAuthorityOwner._enforce_decode_cache_bound` and the `finally:` clause in
`acquire_view`.

## 12. ACTION-VIEW ACCOUNTING (Repair H)

**Defect:** pinned-byte accounting charged positive rows only; a negative-only view (every
requested fold proven absent) was accounted as exactly zero bytes.

**Fix:** `MasterAuthorityOwner._estimate_accounted_bytes()` now charges
`per_view_fixed_overhead_bytes` (default 256) plus `per_requested_fold_overhead_bytes`
(default 64) **per requested fold, positive or negative**, plus the existing per-row estimate
for actually-retained positive rows. This is an explicit provisional estimate, not a claim of
exact RSS/private bytes.

**Evidence:**

- Desktop (4 PASS): a negative-only view has nonzero accounted size (320 bytes observed);
  mixed positive+negative accounting (640 bytes) exceeds equivalent positive-only accounting
  (576 bytes); release drops pinned accounting; a negative-only view under a deliberately tiny
  budget (`total_pinned_bytes=1`) is refused.
- Embedded (checks "8:*", 3/3 PASS): negative-only nonzero accounting (320 bytes), correct
  `proven_negative_folds` representation, mixed accounting (640) exceeds positive-only (576) —
  identical numbers to desktop, confirming the estimate is deterministic across runtimes.

Enforcing source region: `session_owner.py`,
`MasterAuthorityOwner._estimate_accounted_bytes`.

## 13. DETACHED VIEW OWNERSHIP (Repair I)

**Defect:** Round 3 reproduced mutation of a row in published view A appearing in published
view B — rows were shared mutable list/dict objects (previously via the now-removed
coverage cache).

**Fix:** every row published in a view's `folded` payload is now a fresh per-view copy
(`folded[fold_key] = [dict(r) for r in rows]`) built at publish time. Terminology corrected
from "immutable payload copy" to **detached stable action view** (`ViewEnvelope`'s docstring)
— the payload itself remains ordinary mutable Python data; what is guaranteed is narrower and
constructed, not merely claimed.

**Evidence:**

- Desktop (2 PASS): publish A and an equivalent B for the same fold; mutate a nested row and
  append a new row directly on A's payload; B is unaffected; release A; reacquire C; C
  contains authoritative unmutated data.
- Embedded (checks "7:*", 2/2 PASS): identical A/B/C mutation-isolation scenario reproduced in
  real SFM.

Enforcing source region: `session_owner.py`, the `folded[fold_key] = [dict(r) for r in rows]`
line inside `acquire_view`.

## 14. PUBLICATION BOUNDARY (Repair J)

The publication guarantee is narrowed to exactly what is constructed, per the brief:

- no lease/view becomes authorized before candidate resolution, every budget check, and the
  epoch check all succeed;
- a failed candidate publishes nothing and merges nothing (there is nothing left to merge
  into, per §10);
- existing published views remain valid;
- the provider's own decode cache may change (via §11's `finally`-block eviction) so long as
  it remains truthful and within its retained bound.

No "byte-identical whole-owner rollback" claim is made anywhere in the updated source or this
audit. One focused injected pre-publication failure test is kept (C2.6, desktop and embedded
phase 5's predecessor pattern via the epoch-mismatch scenario) — no database-style transaction
rollback machinery was built.

## 15. DESKTOP QUALIFICATION

| Harness | Result |
|---|---|
| `desktop_session_owner_qualification.py` (updated C1/C1R) | 75 PASS / 0 FAIL |
| `desktop_view_expansion_qualification.py` (updated C2/C2R) | 44 PASS / 0 FAIL |
| `desktop_round3_foundation_qualification.py` (**new** Round3 harness) | 40 PASS / 0 FAIL |
| `desktop_parity_and_timing.py` (Gate B, unchanged) | 183 PASS / 0 FAIL |

Total desktop qualification: **342 PASS / 0 FAIL** across all four harnesses.

Every checklist item in the repair brief's §13 is asserted at least once above, each traced to
an enforcing function/source region in §§5-14.

## 16. EMBEDDED PYTHON 2.7 ACCEPTANCE

Real embedded SFM (Python 2.7.5, Qt/PySide main thread), event-loop `QTimer.singleShot`
-chained phases only — no long main-thread sleeps, no native Rebuild, no model mutation.

- Disposable SFM process PID 1884, launched fresh for this probe; the pre-existing SFM process
  (PID 20024, unrelated to this task) had already been closed by the user for unrelated
  reasons before this probe ran (confirmed with the user).
- Trigger mechanism: a `usermod/scripts/sfm/mainmenu/` flat-file entry
  (`ZZZ_Gate_Round3_Foundation_Probe.py`), manually clicked once by the user in the Scripts
  menu — the `usermod/scripts/sfm/autoinit/` directory was found to have no actual
  auto-execution hook anywhere in `sfm_init.py` (platform or usermod copy, both confirmed
  2-line stubs) or elsewhere in the installation, so the click-triggered mainmenu convention
  was used instead, per the user's explicit direction.
- All qualification modules deployed to `usermod/scripts/sfm/gate_round3_deploy/` were
  SHA-256-verified byte-identical to the repo originals before the run (bounded_provider.py,
  bounded_view.py, resource_budgets.py, session_owner.py) — see the deployment transcript
  captured in this session.
- Result: **26 PASS / 0 FAIL**, covering: 3 init calls -> 1 owner (2 checks); one admitted
  provider (1); foreign-owner lease rejection using two qualification owners (4); release
  cleanup without historical growth (3); active-lease close defer + terminal close + registry
  removal (3); detached view A/B/C mutation isolation (2); negative-only view nonzero
  accounting + correct representation + mixed accounting (3); decode-cache bound enforced
  after a refusal (1); representative positive/negative semantics (2); clean final
  release/close (1); plus 2 structural absence checks (`_EpochCoverage`,
  `GuardPolicy.min_committed_ceiling_reserve_bytes`) and 2 setup/fold-count log lines counted
  as informational, not PASS/FAIL.
- Cleanup performed: disposable SFM process (PID 1884) killed with the user's explicit
  confirmation; `usermod/scripts/sfm/gate_round3_deploy/` removed entirely;
  `usermod/scripts/sfm/mainmenu/ZZZ_Gate_Round3_Foundation_Probe.py` removed; stray `.pyc`
  files that Python 2 wrote into the repo's own `tools/sfm_master_sidecar/` directory (as a
  side effect of the probe importing production code directly from the repo path) were
  found and deleted; `autoinit/` directory confirmed empty again.
- `sfm_init.py` (both platform and usermod copies) confirmed byte-unchanged throughout (see
  §19 for hashes) — neither was ever edited.

Exact preserved embedded script/output paths (session-scratchpad, per this session's
established convention of not committing scratch embedded-probe artifacts to the repo):

- Script: `gate_round3_embedded_probe.py`
- Result log: `gate_round3_embedded_result.log`
- Stage markers: `gate_round3_embedded_stage_markers.log`
- Results JSON: `gate_round3_embedded_results.json`

(all under `C:\Users\REDACTED\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\
67454949-e69f-4280-93d9-87c1f4464330\scratchpad\`)

## 17. SEMANTIC PARITY

Representative HIT / ASCII-fold-alias / cross-destination-conflict / valid-absent / metadata
-path semantics were re-verified through the repaired owner on both runtimes:

- Desktop: `desktop_session_owner_qualification.py` Part 16 (6 checks, all PASS, unchanged
  fixtures/methodology from C1) and `desktop_round3_foundation_qualification.py`'s dedicated
  semantic-parity section (5 checks, all PASS) and `desktop_view_expansion_qualification.py`'s
  "Semantic parity through expansion" section (6 checks, all PASS, unchanged from C2).
- Embedded: checks "10:*" (representative positive fold present; representative negative fold
  proven absent, never a false positive) — 2/2 PASS.

No semantic regression versus the already-qualified `bounded_view.compat_master_lookup`
adapter was found anywhere in this repair.

## 18. REGRESSION

| Command | Result |
|---|---|
| `python -m pytest tests/sidecar/ -q` | 369 passed, 265 subtests passed |
| `python -m pytest tests/ -q` | 421 passed, 265 subtests passed |
| `python tools/validate_master.py sfm_defaultanimationgroups.txt` | PASS (0 exact duplicates, 0 cross-path casefold violations, structural parse PASS) |

No flake observed in this session's runs.

**Tests removed** (obsolete: tested the now-entirely-removed owner-level coverage cache):

- `desktop_view_expansion_qualification.py`: the "Cache eviction — performance only, never
  truth" section (3 assertions) and the "Gate C2R — enforced coverage-cache bound (FIFO
  eviction)" section (9 assertions across positive- and negative-bound scenarios). Both
  sections tested `_EpochCoverage`/`owner.evict_reusable_coverage_cache()`, neither of which
  exists any more. Replaced by the new Repair G/H/I sections in the same file (10 assertions),
  which test what actually still exists.

**Tests rewritten** (architecture intentionally simplified, premise changed):

- C2.1 ("warm covered reacquisition" -> "repeated request without an owner-level cache"):
  the claim "no `provider.lookup_fold` re-invocation for already-covered folds" is withdrawn
  (there is no cache to make that true any more); the claim "repeated request produces a
  semantically identical payload" is kept and re-verified.
- C2.3 ("true negative coverage" -> "positive/negative/uncovered within one view"): the
  cross-call negative-coverage-reuse claim is withdrawn; the coverage-contract claim
  (positive/negative/unrequested distinguishable within one action) is kept and sharpened.
- C1.1 (registration-install/-identity assertions removed, per §7).
- "Guard D" (committed-ceiling-reserve independence test replaced with a physical
  -consistency regression check, per §8).
- C1.5/C2.4.B/C2.5/C2.6 (`_coverage`-referencing assertions removed; C1.5/C2.5's tight
  pinned-budget test fixtures explicitly zero the new Repair H per-fold overhead to preserve
  their original row-count calibration, since they are testing family/pinned-row budgeting
  specifically, not Repair H's accounting feature).

**Tests preserved unchanged:** `desktop_parity_and_timing.py` in full (183 checks); the large
majority of `desktop_session_owner_qualification.py` (C1.2, C1.3, C1.4 both orders, RepairB,
RepairD's core reset-determinism claims, Part 16 semantic regression); the large majority of
`desktop_view_expansion_qualification.py` (C2.2, C2.4.A, C2.5's over-budget-refusal claim,
C2.6's core rollback claim, C2.7, semantic parity through expansion).

## 19. PRODUCTION IDENTITIES

| Artifact | SHA-256 | Bytes |
|---|---|---|
| Canonical Master (`sfm_defaultanimationgroups.txt`) | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | 3,972,355 |
| Official sidecar (fresh recompile) | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | 9,506,244 |
| `tools/sfm_master_sidecar/reader.py` | `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` | 44,993 |
| `tools/sfm_master_sidecar/format.py` | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` | 14,249 |
| External Normalizer (`Rebuild_Control_Groups_Normalizer.py`) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | 339,944 |
| Platform `sfm_init.py` | `7ee38d22df91dc02440553668b2df9a88d6b381ff23447c1a06f82280f12bf2c` | 123 |
| Usermod `sfm_init.py` | `08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15` | 122 |

All identities match every prior checkpoint in this arc (Gate B / C0 / C1(R) / C2(R)). No
production reader/format defect was discovered during this repair, so — per the brief's
explicit instruction — no production file was edited.

## 20. WHAT THIS REPAIR PROVES

- The five most-consequential Astra Round 3 findings are closed by removal or repair, with
  both desktop and embedded evidence for each item that has runtime-sensitive behavior.
- The owner's retained state surface is now genuinely smaller than before C2: no cross-action
  cache, no fake registration claim, one fewer guard criterion, deterministic decode-cache
  bounding, honest accounting, and honest detachment.
- The simplified model still supports the two things the original product goal actually
  needs: one shared provider per namespace, and a correct, budget-respecting, epoch-checked
  action view per request.

## 21. WHAT IT DOES NOT PROVE

- Real source-change/generation replacement (a different namespace key resolving to a fresh
  authority over time) — explicitly out of scope, belongs to minimum C3.
- Any claim about repeated-request performance: Repair F intentionally removed the
  cross-action cache, so repeated identical requests now cost a repeated provider lookup —
  this repair does not claim, measure, or optimize that cost; it only proves correctness is
  preserved.
- An exhaustive resource-exhaustion sweep of every possible guard/budget interaction — the
  provisional threshold VALUES (guard minimums, per-fold overhead estimates, budget defaults)
  remain qualification-only estimates, not production SLAs, exactly as in every prior gate in
  this arc.
- The missing-artifact recovery path (Repair E) was verified on desktop only, not re-run in
  embedded SFM — it is a pure Python exception-handling path with no OS/runtime-specific
  behavior, and the embedded probe's scope was allocated to the items with genuine
  runtime-sensitivity (lease ownership, decode-cache bytes, detachment) instead.

## 22. MINIMUM C3 AUTHORIZATION OR STOP

**Minimum C3 is authorized to begin in a future task**, per the verdict in §1. This document
does not itself begin C3, propose C3's design, or scaffold any C3 code/tests — per the brief's
explicit instruction, C3 requires its own separate task and its own brief.

## 23. GIT STATE

- HEAD unchanged throughout this repair: `7af34a78194fa22a573280bbced79dcd813f3feb` "Record
  sidecar Round 3 architecture audit".
- Nothing staged (`git diff --cached --name-only` empty throughout).
- No commits made.
- `git diff --check`: PASS.
- Changed (uncommitted): `tests/sidecar/qualification/session_owner.py`,
  `tests/sidecar/qualification/resource_budgets.py`,
  `tests/sidecar/qualification/desktop_session_owner_qualification.py`,
  `tests/sidecar/qualification/desktop_view_expansion_qualification.py`.
- New (untracked, uncommitted): `tests/sidecar/qualification/desktop_round3_foundation_
  qualification.py`, this audit document.
- No production file (Normalizer, Master, `reader.py`, `format.py`, binary format,
  `sfm_init.py`) appears in any diff.
- Temporary SFM deployment (`usermod/scripts/sfm/gate_round3_deploy/`, the mainmenu probe
  script, and stray `.pyc` files written into `tools/sfm_master_sidecar/`) all removed; see
  §16.
