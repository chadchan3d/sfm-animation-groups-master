# SFM Sidecar — Claims Ledger (Supported / Narrowed / Withdrawn / Unproven)

Collected at HEAD `1028adcde35dd7681cfad7db2bbc7c367c7b2565`. Strict, source-first.
"Evidence class" uses: RAW (a preserved log/measurement), CURRENT SOURCE (verified by
reading the current file), AUDIT SUMMARY (asserted in a prior audit, re-verified
here), DERIVED (computed from other evidence), NOT PRESERVED (claimed but no
artifact survives to check it).

| Claim | Current status | Evidence | Evidence class | What it proves | What it does NOT prove | Superseded/withdrawn predecessor | Production consequence |
|---|---|---|---|---|---|---|---|
| Semantic parity (HIT/alias/conflict/absent/metadata) through the owner/view layer | **SUPPORTED** | `desktop_parity_and_timing.py` 183/183; `desktop_session_owner_qualification.py` Part 16 (6/6); `desktop_view_expansion_qualification.py` semantic-parity section (6/6); embedded checks "10:*" | RAW (fresh re-run this session) + CURRENT SOURCE | The owner-mediated path returns byte-identical semantic answers to the already-qualified `bounded_view.compat_master_lookup` adapter, for every case tested | Parity against the REAL Normalizer's own `master_lookup`/`parse_targeted_master` (never directly diffed against the shipping Normalizer's output in this arc) | None | If integration proceeds, still needs a direct diff against the real Normalizer's own lookup semantics, not only the qualification adapter |
| Sidecar late-vocabulary value (arbitrary new fold resolved without a full re-scan) | **NARROWED** | Gate B audit (historical, not re-run this session); Round 3/C3 never re-measured this specific claim | AUDIT SUMMARY (Gate B, not re-verified in this evidence pass) | A per-fold-bounded lookup was faster/lighter than an eager whole-file scan, as measured in Gate B | Whether this holds after Round 3 removed the reusable cross-action cache (repeated requests now re-query the provider every time, per Repair F) — no fresh timing was collected for repeated-request cost post-Round-3 | The original Gate B claim assumed a persistent owner with reuse; Repair F removed that reuse mechanism for cross-action requests | The genuine differentiator (first-touch of new vocabulary without a full TXT scan) still holds structurally, but "repeated cheap reuse" no longer does — this is a narrower claim than Gate B originally implied |
| Resource/admission costs (steady/peak SFM memory) | **NARROWED / PARTIALLY STALE** | C0.4/C0.5 audit figures (steady ~22.77 MiB, peak ~63 MiB, constrained-loaded ~73 MiB largest free region) — historical, not re-measured in this pass | AUDIT SUMMARY, NOT PRESERVED as raw re-measurement here | These were real measured numbers at the time C0 ran | Whether they still hold after Round 3's structural changes (smaller retained-state surface should, if anything, improve this, but it was not re-measured) | None withdrawn, but not refreshed | Any Normalizer-integration cost argument should re-measure, not cite C0-era numbers unchanged |
| Retained-memory claims (owner-level cache bound) | **WITHDRAWN (mechanism removed)** | Round 3 foundation audit §4, §10; `session_owner.py` has no `_EpochCoverage` | CURRENT SOURCE | There is no owner-level cross-action cache left to make a retained-memory claim about | The provider's own decode-cache bound (Repair G) is a DIFFERENT, still-live claim (see below) | Gate C2R's "the cache is explicitly bounded (32 MiB positive / 100k negative)" claim is fully withdrawn — the cache itself no longer exists | None — simplification, not a regression |
| Owner sharing (one provider, two consumers) | **SUPPORTED** | `desktop_session_owner_qualification.py` C1.3 (unchanged since Gate C1); embedded C1/C1R evidence (historical, not re-run this pass, but structurally unaffected by Round 3/C3) | CURRENT SOURCE + AUDIT SUMMARY | A single admitted provider correctly serves two independent consumer leases | Multi-consumer behavior under Round 3's new retirement semantics specifically (not separately re-tested with >1 consumer mid-retirement, only single-consumer-pair drain in C3.5) | None | Fine for the qualified shape; a real multi-consumer Normalizer scenario is still unproven |
| Lease identity (foreign-owner rejection) | **SUPPORTED** | Round 3 Repair A, desktop (6/6) + embedded (4/4) | RAW (embedded log, re-verified this session) + CURRENT SOURCE | Cross-owner lease confusion is structurally impossible (owner_id check) | Nothing about lease identity under concurrent/multi-threaded access (this qualification is single-threaded/event-loop only) | The original C1 lease design (no owner_id check) is fully withdrawn | None new |
| Action-view detachment | **SUPPORTED** | Round 3 Repair I, desktop (2/2) + embedded (2/2) | RAW (re-verified) + CURRENT SOURCE | Mutating one published view cannot affect another view or the provider's cache | Immutability in the strict sense (payloads remain ordinary mutable Python objects; only cross-view isolation is guaranteed, per the corrected "detached stable action view" terminology) | The original "independent immutable payload copies" wording is withdrawn as inaccurate | None |
| Decode-cache bound (provider string cache) | **SUPPORTED, narrow** | Round 3 Repair G, desktop (4/4) + embedded (1/1) | RAW (re-verified) + CURRENT SOURCE | The bound is enforced after ordinary/refused/faulted requests via eviction | Anything about the production `BUDGET_STRING_CACHE_ESTIMATED_BYTES` constant being a real production limit (it remains explicitly provisional) | The pre-Round-3 state (constant existed, never enforced) is corrected | None — a qualification-only accounting improvement |
| Command-boundary SHA freshness | **SUPPORTED** | Minimum C3 §4/§5, desktop C3.1/C3.2 (11/11) + embedded checks "3" | RAW (re-verified) + CURRENT SOURCE | Freshness is byte-accurate, not mtime/size-based, at an explicit boundary | Frequency/cost at realistic Normalizer command rates (only measured as a single isolated ~2.7 ms hash of the real Master, not under load) | None | The Normalizer ALREADY has its own independent SHA-based freshness mechanism (`sha256_stream`/`contextualizer_assert_master_stable_for_index_use`) — see the architecture/verification doc §5. Any integration must reconcile these, not run both. |
| Retirement/drain/close | **SUPPORTED** | Minimum C3 §6-9, desktop C3.3-C3.6 (24 checks) + embedded checks "4"-"8" | RAW (re-verified) + CURRENT SOURCE | The full retire -> drain -> close sequence works with no provider overlap and correct registry cleanup | Multi-generation churn (only one retirement cycle, G1->G2, was exercised — not G1->G2->G3 in sequence) | None | The real Normalizer today has NO equivalent lifecycle at all (it rebuilds fresh every command) — this claim is entirely about NEW qualification-only machinery, not a parity claim against existing production behavior |
| G2 lazy readmission | **SUPPORTED** | Minimum C3 §10, desktop C3.6 (8/8) + embedded checks "9"-"11" | RAW (re-verified) + CURRENT SOURCE | Admission stays lazy; a later, separate explicit call produces correct new-generation semantics | Real "next command" timing/triggering in a live Normalizer (this is simulated by direct function calls, not by an actual second Normalizer invocation) | None | Still qualification-only; no evidence yet that a real Normalizer command boundary would call this API the same way |
| No mixed generations | **SUPPORTED** | Minimum C3 §14, desktop C3.14 (2/2); mechanism shared with Round 3's epoch-mismatch guard | RAW (re-verified) + CURRENT SOURCE | A single injected mid-flight retirement race cannot publish mixed content | Concurrency under real multi-threaded/multi-process access (single-threaded, deterministically-injected only) | None | None |
| Python-2 manifest compatibility | **UNPROVEN AS PRODUCTION-READY / explicitly narrow** | Architecture/verification doc §5; Minimum C3 audit §20-21 (explicit carry-forward) | CURRENT SOURCE (the gap is documented, not measured away) | A minimal, narrower reader can run under embedded Python 2.7 for the 5 fields it checks, in the one embedded scenario tested | Production-grade hardening (duplicate keys, SHA regex, safe-basename); malformed-JSON-syntax handling under Python 2.7 (never tested on that runtime); compatibility with the Normalizer's EXISTING freshness mechanism (not reconciled) | The original design assumption ("we can just call `manifest.py`") is withdrawn — it does not work under Python 2.7 at all | This is the single most concrete open item before any real integration |
| Normalizer production integration | **NOT STARTED** | Verified by direct grep: zero sidecar/qualification references anywhere in `Rebuild_Control_Groups_Normalizer.py` | CURRENT SOURCE (a negative result, directly verified) | Nothing has been silently integrated | Whether integration is even a good idea for THIS Normalizer's actual architecture (its own independent freshness/index-build mechanism, see §5) — that comparison is exactly what this package is for | None | N/A — this is the gate the whole package exists to inform |
| Character Preset compatibility | **NOT ESTABLISHED** | No source reference found anywhere in this evidence collection | NOT PRESERVED / not applicable | Nothing | Nothing — genuinely out of scope for every gate in this arc so far | None | No claim should be made either way until a real Character Preset integration task exists |
| Format-v1 readiness | **UNPROVEN, not attempted this arc** | No format change occurred in Gate B through C3 (format.py SHA unchanged throughout, verified §1) | CURRENT SOURCE (a stability fact, not a readiness proof) | The experimental format has not needed to change to support any of B0 through C3 | Whether the format is actually final/frozen-worthy — that determination was explicitly out of scope for every gate audited here | None | Format-v1 freeze remains a separate, unaddressed decision |

**Strictness note:** every "SUPPORTED" row above cites a specific, re-verified test
count from THIS evidence-collection session (§6 of the architecture/verification
document), not merely a historical audit's PASS claim. Every "NARROWED" or
"UNPROVEN" row states exactly what part of the original claim no longer holds or
was never established, rather than leaving the gap implicit.

---

## Addendum (2026-09-18): R3 B2C-B/B2C-C arc — a DIFFERENT, later architecture

Everything above this line describes an EARLIER architecture (`session_owner.py`,
retirement/drain/close generation lifecycle) that the current `sfm_master_authority`
broker/view_cache/resource_preflight package (qualified through Correction2–6,
commit `514a100a380e33b6b6281afdc489921fd68728e1`) has since superseded. The rows
above are NOT re-validated against, and do not describe, the current architecture —
they are preserved here only as the historical record for the arc they actually
audited. This addendum is the current arc's own append point (per B2C-C's governing
prompt, Section 17); no dedicated "cumulative empirical ledger" existed yet for the
B2/B2C arc before this entry.

| Script/test identity | Scope | Evidence | Interpretation | Verdict | Proves | Does NOT prove | Design consequence | Next decision |
|---|---|---|---|---|---|---|---|---|
| `test_b2c_c_plan_layer_equivalence.py` (candidate `candidate_b2c_c/`) | Downstream decision layer (`classify_production`, `order_candidate_rows_by_policy`, `preflight_reconciliation_plan`, `derive_generic_uniformity_plan`) — 10 fixtures, 4 negative controls, real Python 2.7.5 | 37/37 PASS, `R3_B2C_C_plan_layer_ledger.json` (per-fixture hashes/counts) | RAW (fresh run this session), CURRENT SOURCE (extracted verbatim by exact line range from the frozen production file, SHA-256-pinned) | **SUPPORTED, narrow** | The qualified Correction6 authority (broker/adapter) produces BYTE-IDENTICAL downstream classification/ordering/uniformity-plan decisions to the frozen production parser, across every distinct `classify_production` category and several structural edge cases (ASCII-fold, left/right pairing, unrigged target, simultaneous multi-row ordering) | Native mutation EXECUTION (`production_generic_composer` and ~15-function closure, 7 native primitive wrappers) — never invoked, not compared; live target/scope-eligibility discovery (`snapshot_work`) — never exercised; authority-generation/lease sanity under the REAL broker-mediated acquisition path (this harness opens the provider directly, one layer below the broker) | B2C-C cannot reach a full PASS on the strength of this evidence alone — the decision layer is qualified, the execution layer is not | Before any further B2C-C attempt: either build and independently validate a fake-DME-object-model sufficient for `production_generic_composer`'s closure, or explicitly re-scope B2C-C's own PASS criteria to acknowledge a decision-layer-only qualification tier |
| Frozen production Normalizer negative controls (NC1, NC2/NC2b, Section-8 swap detection) | Proves the comparison oracle actually detects real disagreements (destination misroute, authority-subject swap) rather than being vacuously insensitive | 4/4 negative controls produced their expected result (3 detected a real perturbation; 1 — NC2's first attempt — was disclosed as an ineffective perturbation choice, not a harness insensitivity, and superseded by NC2b) | RAW (fresh run this session) | **SUPPORTED** | The canonical-hash comparison mechanism is sensitive to real destination/routing disagreements and to authority-subject-identity swaps | Sensitivity to native-execution-layer differences (order of native calls, group-creation timing) — not tested, since that layer is not exercised at all | The decision-layer oracle is trustworthy for what it covers | Same as above |

**Strictness note (addendum):** the "SUPPORTED, narrow" verdict above is deliberately
narrow — it is scoped exactly to what `test_b2c_c_plan_layer_equivalence.py` actually
exercises (Section 2 of `R3_B2C_C_Downstream_Mutation_Equivalence_Report.md` has the
full justification), not a general "B2C-C passed" claim. The governing prompt's own
final verdict for this round is `B2C-C PARTIAL`, not PASS — B2C-D is NOT authorized.

---

## Addendum 2 (2026-09-19): execution-layer continuation

| Script/test identity | Scope | Evidence | Interpretation | Verdict | Proves | Does NOT prove | Design consequence | Next decision |
|---|---|---|---|---|---|---|---|---|
| `test_b2c_c_execution_layer_equivalence.py` (candidate `candidate_b2c_c/fake_dme.py` + `production_execution_layer.py`) | Native-mutation EXECUTION layer (`production_generic_composer` and its authority-sensitive closure, `_gate_is_alh`) — same 10 decision fixtures, 5 negative-control types (2 first attempts disclosed ineffective, superseded), full determinism gate, real Python 2.7.5 | 67/67 PASS, `R3_B2C_C_execution_layer_ledger.json` (per-fixture decision-plan/native-mutation-stream/final-tree hashes) | RAW (fresh run this session), CURRENT SOURCE (execution-layer functions extracted verbatim by exact line range, SHA-256-pinned against the same frozen production file) | **SUPPORTED, narrow** | For all 10 qualified fixtures, the qualified Correction6 authority produces BYTE-IDENTICAL native mutation streams AND resulting logical control-group trees to the frozen production parser, when both are run through the SAME real extracted `production_generic_composer` closure against independently-constructed-but-identical fake-DME worlds; the ONE authority-sensitive target/scope-eligibility function (`_gate_is_alh`) also matches; a real bug (non-exclusive `AddChild` reparenting) was found and fixed in the fake model itself, caught by the REAL production code's own postcondition checks | A specific named subset of Section 8's mutation-sensitive expansion fixtures (toe relocation, flex-first ordering, Tail relocation, repeated-control preservation, dedicated untouched-custom-group case) — not attempted; live target/scope enumeration (`snapshot_work`'s real scene/shot/project walk) — confirmed authority-independent by dependency analysis but never exercised, explicitly deferred to a future live-runtime gate | B2C-C's decision AND execution layers are now both qualified for the fixture set actually built; B2C-D remains unauthorized pending the named remaining fixtures | Before B2C-D: either build the remaining named expansion fixtures (toe relocation is the highest-value, since its code path is already fully read and mapped) or explicitly accept a fixture-set-scoped PASS tier |
| `test_b2c_c_broker_mediated_authority_sanity.py` | Real `Broker.acquire_or_reuse_views`/`lease_view` integration seam (not the direct-provider-open shortcut the plan/execution harnesses otherwise use) | 8/8 PASS, both Python 3.10 and real Python 2.7.5 | RAW (fresh run this session) | **SUPPORTED** | The real production integration seam a Normalizer command would actually use reaches the would-be mutation boundary with agreeing source/embedded/command generations, a valid lease, zero open providers, and no TXT fallback | That this seam was wired all the way through the fake-DME execution harness itself in this round (a natural, not-yet-done extension) | The real integration seam, not just the isolated provider-open shortcut, is sound for at least one case | Wire the broker-mediated path directly into the execution harness in a future round if a stronger end-to-end claim is needed |

**Strictness note (addendum 2):** the execution-layer "SUPPORTED, narrow" verdict is scoped
exactly to the 10 fixtures + gate function + negative controls actually built (Section 21-22 of
the updated report). The governing prompt's own final verdict for this round remains
`B2C-C PARTIAL` — B2C-D is NOT authorized. The gap narrowed substantially between Addendum 1 and
Addendum 2 (from "entire execution layer uncovered" to "a specific named subset of expansion
fixtures uncovered"), which is itself evidence the methodology is converging, not evidence of
completion.

---

## Addendum 3 (2026-09-19): Final Offline Expansion Fixtures — closes the named gap

| Script/test identity | Scope | Evidence | Interpretation | Verdict | Proves | Does NOT prove | Design consequence | Next decision |
|---|---|---|---|---|---|---|---|---|
| `test_b2c_c_plan_layer_equivalence.py` + `test_b2c_c_execution_layer_equivalence.py`, extended `candidate_b2c_c/scenarios.py` (15 fixtures total) | Decision layer AND native-mutation execution layer, now including the 5 named expansion fixtures (active-rig toe relocation, flex-first ordering, Tail relocation, repeated-control preservation, untouched custom/unrelated group preservation) | Decision layer 52/52 PASS, execution layer 117/117 PASS, both real Python 2.7.5, `R3_B2C_C_execution_layer_ledger.json`/`R3_B2C_C_plan_layer_ledger.json` (per-fixture hashes/counts, enriched with fixture SHA/group-control counts/determinism/broker-mediated flags for D1-D5) | RAW (fresh run this session), CURRENT SOURCE (same verbatim-extracted functions, unchanged this round) | **SUPPORTED** | For all 15 fixtures (the original 10 plus the 5 named expansion fixtures), the qualified Correction6 authority produces BYTE-IDENTICAL decision-plan streams, native mutation streams, AND resulting logical control-group trees to the frozen production parser; a real harness defect (masked mutual failure via a missing upstream `NativePostFallback` gate, affecting A3/B1/B4/C1/D3/D5) was found and fixed; all 5 new fixtures have effective negative controls, with two disclosed-ineffective first attempts (NC-D-a, NC-E-a) honestly superseded rather than hidden; full determinism confirmed for all 5; a new broker-mediated sanity case (flex-first content, through the REAL `Broker.acquire_or_reuse_views`/`lease_view` path) also passes (17/17 total, up from 8/8) | Live target/scope enumeration (`snapshot_work`'s real scene/shot/project walk, on-disk MDL reads) — still never exercised, explicitly deferred to a future live-runtime gate per the dependency cut (unchanged from Addendum 2); the native `ifm.dll` rebuild callback itself is still never emulated (by design) | The named gap from Addendum 2 (a specific subset of expansion fixtures) is now closed; B2C-C reaches a full offline PASS conditioned on the live-enumeration deferral remaining valid | B2C-D is candidate-authorized by this local result, but per the governing checkpoint prompt's own governance clause, treat this as `B2C-C CANDIDATE PASS — INDEPENDENT AUDIT REQUIRED BEFORE B2C-D`, not a self-authorized production promotion |
| `test_b2c_c_broker_mediated_authority_sanity.py` (extended) | Real `Broker.acquire_or_reuse_views`/`lease_view` integration seam, now including a SECOND case using this round's own flex-first fixture content (`eye_flex_control`/`eye_bone_control`), not just the pre-existing Correction6 "left"/"right" fixture | 17/17 PASS (8 original + 9 new), real Python 2.7.5 | RAW (fresh run this session) | **SUPPORTED** | The real integration seam also works end-to-end for this round's own new fixture content, closing Addendum 2's own noted "not yet done" extension | Nothing beyond the two fixture cases exercised (generic left/right, flex-first) — not every fixture's content was independently run through the real broker path, only one representative new case, per the governing prompt's "at least one" requirement | The real broker/adapter integration seam is sound for the fixture content this round added, not just the pre-existing content | None — this closes Addendum 2's explicitly named follow-up |

**Strictness note (addendum 3):** this addendum's "SUPPORTED" verdicts are still scoped to what
was actually built and run offline this round (Section 32-42 of the updated report) — they do
NOT constitute live-runtime qualification, and live target/scope enumeration remains explicitly
deferred, not fabricated. The local result is:

`B2C-C DOWNSTREAM MUTATION EQUIVALENCE PASS — AUTHORIZE B2C-D`

but per the governing GitHub-checkpoint prompt's own governance clause, this local result must be
treated as `B2C-C CANDIDATE PASS — INDEPENDENT AUDIT REQUIRED BEFORE B2C-D` until an independent
audit of the pushed checkpoint confirms it. B2C-D has NOT begun. No self-authorized production
promotion is claimed anywhere in this addendum.

---

## Addendum 4 (2026-09-21): independent audit, targeted correction, independent re-audit — B2C-C CLOSED

This addendum preserves the full historical sequence exactly as it happened. Earlier
PARTIAL/CANDIDATE verdicts above are NOT rewritten or deleted — they are the accurate record of
what was true at each point in the arc.

1. **Independent audit of `5cc98966d2425ca25ffcf310809fd01ae8514ff8`** (the checkpoint Addendum 3
   above staged/pushed) found two narrow fixture-contract gaps, verdict `B2C-C PARTIAL — CORE
   DOWNSTREAM EQUIVALENCE EVIDENCE SUPPORTED; TWO FINAL-FIXTURE CONTRACT GAPS BLOCK B2C-D`:
   - the "Tail relocation" fixture (D2) was not actually a Tail fixture (synthetic `Body/Tail`
     Master entry that does not match the real canonical Master's structure; always
     `already_correct_count=1`/`moved_count=0`; silently refined back to `RigBody`);
   - the "untouched custom group" fixture (D4) was not actually zero-touch (its root children
     never reached the real reorder function's early exit, so the unconditional detach/re-add
     genuinely fired against the custom group's own root position).
2. **Commit `3b5aaa955bafa822da27603514271944b280654e` closed both gaps**: D2 renamed to
   `D2_rigbody_family_counterpart_refinement` (retained only as valid RigBody-refinement evidence,
   no longer claimed as Tail); a new dedicated real-canonical-Master Tail authority test added
   (15/15 PASS); a new `D6_tail_relocation` fixture added (genuine, observable relocation into a
   real root-level `Tail` group, effective negative control); D4 redesigned as
   `UserCustomGroup/{Alpha,Beta}` (verified `mutation_count == 0`, with a precise handle/name-based
   zero-mutation-log-entries assertion, non-trivial metadata, effective negative control); all four
   RESULTS-accumulating harnesses hardened to exit non-zero on failure, self-test-proven in both
   directions; complete per-fixture evidence (all repeat-1/repeat-2 SHAs) for all 16 named
   fixtures; an explicit broker-to-execution D5 composition proof added. See
   `R3_B2C_C_Downstream_Mutation_Equivalence_Report.md` Part 4 for the full derivation.
3. **Independent re-audit of `3b5aaa9`**: `INDEPENDENT B2C-C RE-AUDIT PASS — B2C-C CLOSED —
   AUTHORIZE B2C-D`. See `R3_B2C_C_Independent_Reaudit_3b5aaa9_Report.md` for the full record,
   including independently-reproduced synthetic-authority and official-sidecar SHA-256 identities.
4. **B2C-C is CLOSED.**
5. **B2C-D is authorized to begin** (as a future phase — this addendum documents the
   authorization, it does not itself perform any B2C-D work).
6. **Production promotion remains unauthorized.** Nothing in this arc — Addendum 1 through this
   entry — constitutes or implies production-promotion authorization. Live target/scope
   enumeration, native `ifm.dll` behavior, and W3 (still `UNKNOWN`) remain separate, deferred
   gates, unchanged by B2C-C's closure.
