# SFM Sidecar — Astra Round 3 holistic audit

2026-09-13. Review only: no repository implementation changed, no SFM process operated, no C3 implementation or qualification begun.

Primary evidence: the supplied Round 3 delta package at checkpoint `3518173f5652ecb136f303cbdea2bfe656c051ca`. I verified all 19 listed bundle hashes. Current owner/provider/budget/view source and production reader/format match the packaged versions. The two supplied ledger copies are byte-identical. I located the actual [Round 2 review](C:/Users/REDACTED/Documents/Codex/2026-09-07/files-pasted-by-the-user-use/outputs/SFM_SIDECAR_ASTRA_ROUND2_AUDIT_2026-09-12.md), which the delta manifest had not located.

Evidence terms: **verified source** means inspected implementation; **reproduced** means desktop Python checks against that implementation in this review; **reported embedded** means the supplied audit's account, not a new independently replayed SFM result. No new whole-suite or embedded run was necessary for the findings below.

## 1. Executive verdict

**Keep the compiled-sidecar direction, simplify its owner substantially, and do not begin C3 yet. C0 can remain closed within its qualification scope; C1/C1R and C2/C2R must narrowly reopen.**

The sidecar has a real product advantage: after admission, previously uncovered vocabulary can be resolved without another multi-second Master tokenization. A shared TXT cache cannot eliminate that specific cost without retaining a complete index or adding another indexing mechanism. But the present owner has acquired more cache, accounting and lifecycle machinery than the consumer evidence justifies, and current PASS claims still exceed the actual guarantees.

The most consequential findings are:

1. **Cross-owner lease confusion is reproducible.** A lease from owner A can authorize owner B's view and release B's lease when their owner-local IDs collide.
2. **Terminal cleanup is incomplete.** Closed owners retain reusable coverage and historical lease records; the registry retains the closed owner. Repeated acquisitions accumulate inactive leases.
3. **C2R really bounds its two coverage containers, but not the complete retained resource graph.** The owner bypasses the declared provider-string-cache budget, and negative-only pinned views are accounted as zero bytes.
4. **The purported independent commit-space guard remains mathematically redundant for valid VAS snapshots.** Its passing isolation test uses an impossible 4,888 MiB total inside a 4,096 MiB address-space model.
5. **“Independent immutable payload copies” is inaccurate.** Views and reusable cache share mutable row lists/dictionaries. Expansion and eviction preserve their values, but consumer mutation propagates across views and cache.

These findings justify repairing or removing mechanisms, not adding another generalized safety framework. **Overall direction: OVER-ENGINEERED BUT RECOVERABLE.**

## 2. Fresh-eye architecture choice

**Yes to a much narrower compiled-sidecar + one shared owner + stable action-view architecture. No to promoting the current qualification owner wholesale.**

Starting today, I would choose a small source-authority service with a lazy, resource-admitted packed sidecar for this project's explicit arbitrary-late-vocabulary requirement. I would retain the existing scoped TXT path as the manual-command alternative when compilation, compatibility or admission is unavailable. I would initially omit the separate owner-level reusable positive/negative family cache.

For a tool that only repeatedly normalized the same fixed vocabulary, I would choose shared scoped TXT instead: its warm behavior is already cheap and its retained state is much smaller. The reason to choose the sidecar here is the stated changing-vocabulary workflow and the measured cost of acquiring genuinely new scope—not sunk cost, lookup speed alone, or a hypothetical future ecosystem of consumers.

This is an optional acceleration/service boundary, not a requirement that artists maintain a database. The editable TXT remains authoritative. An advanced modeler who changes it must have an understandable route to current semantics, even before a fresh sidecar exists.

## 3. What the project is actually trying to accomplish

The product is reliable, taxonomically consistent SFM tooling. The first consumer is the Normalizer. The desired improvement is fewer unnecessary pauses while acquiring the Master facts needed for selected models and later additions, without compromising native workflow checks or imposing avoidable x86 memory pressure.

The sidecar is not responsible for model semantics beyond the Master, live DME safety, rig ownership, transaction recovery, or a general observer platform. Character Preset is a prospective second consumer whose adapter must earn compatibility separately. Two generic consumer IDs in a harness are not proof of two production tools coexisting.

A successful architecture should remain understandable as: acquire current source identity, choose an admissible producer, obtain a complete requested view, validate at the operation boundary, and release operation-owned references.

## 4. Evidence quality / correction-history assessment

The corrections were handled responsibly in one respect: failures and withdrawn claims are preserved, repairs are checkpointed, and source changes can be traced. C0's replacement resource account is substantially more careful than the withdrawn Gate B claims.

However, this is no longer merely a story of healthy testing discovering obscure edge cases. The original active-lease close defect, a counter that did not measure registration, and an entirely unbounded cache were direct contradictions between implementation and claimed invariants. This review finds additional contradictions after their repair. The pattern indicates **test assertions shaped too closely around intended implementation behavior and insufficient source-first review**.

Evidence limitations matter:

- The bundle preserves current source and a fresh 369-sidecar-test / 421-full-test transcript, each with 265 subtests.
- C1R's 73 desktop / 31 embedded checks and C2R's 54 desktop / 22 embedded checks are reported in audits. Standalone embedded scripts/transcripts are not preserved in this delta package.
- C0 resource and consumer results are described in detail, but raw C0 sampler records/probes are not included here. I accept the corrected measurements as reported evidence, not independently recalculated raw results.
- The recovered Round 2 report is an actual prior baseline; the correction index alone would not substitute for it.
- A transient publisher concurrency test failure followed by a pass is not proof the race is nonexistent. Track its supported concurrency scope; do not reopen unrelated publication research for this single-producer integration unless it affects that scope.

Future gate discipline should be small and concrete: every PASS row names an invariant, the enforcing source location, the actual assertion and evidence class. Review allocation/ownership paths before declaring resource or lifetime closure. Preserve the final embedded script, source hashes and raw output. Require physically consistent resource fixtures. Do not infer runtime callback installation from an assigned counter or memory bounds from a variable named “budget.”

## 5. C0 audit

**Decision: CLOSED for its declared qualification scope, with interpretation corrections.**

**Consumer/error parity:** the C0 audit reports actual Normalizer `master_lookup` and `validate_master_subset_conflicts` invoked on both producers, including matching conflict exceptions, aliases, absence and non-ASCII inputs. This addresses Round 2's mirrored-oracle problem. It is a finite compatible-source result, not unrestricted source-language equivalence. See [C0 audit](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/03_C0/SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md:45).

**Source profile:** the helper explicitly refuses a wrapper other than `groupFile` or any backslash byte. That deliberately over-restricts some harmless sources, including backslashes in comments, but prevents the demonstrated escape disagreement without changing generic compiler semantics. The current owner does not itself enforce this helper; production integration must connect it to an actual verified source generation. A profile-version string is not evidence the check ran.

**Validator consolidation:** `_validate_complete` now calls the production validator. The forward parent-path loop replaces the demonstrated recursive closure cycle. Keep this consolidation. Validation still temporarily decodes the complete graph; bounded steady materialization does not mean bounded-only admission work.

**Corrected resources, reported:**

| Observation | Idle | Constrained loaded |
|---|---:|---:|
| Admitted empty-provider process-private increment | 22.77 MiB | 20.56 MiB average |
| Sampled admission maximum increment | 63.59 MiB | 63.15 MiB |
| Post-close residual above baseline | 13.71 MiB | 11.31 MiB |

The phased method with pre-ready sampling and held steady windows is appropriate. These are observed whole-process deltas, not precise retained-object sizes. One idle and one loaded run do not establish “statistically identical” timings or load-independent resource behavior. The small-view phases cover 216 + 17 folds, not every future workload. The sampled maximum is not a peak ceiling.

**Late vocabulary:** reported disjoint A = 2,510 folds and B = 2,968 requested folds, including one absence, establish first family acquisition for B. Binary-search pivot strings are allowed to have been touched earlier; this is not a cold-CPU-cache claim. S1 B took 0.161 s; shared TXT B took 2.626 s. Preserve the benefit and its scope. The reported B equality is folded-key-set equality; this particular measurement alone does not prove full row/rank/metadata parity. Other parity evidence supplies that separate support.

**Budgets:** the C0 wrapper explicitly refuses oversized materialized families/views and checks estimated string-cache size. Those are useful qualification checks, not pre-allocation guarantees. It calls `result.occurrences()` before checking family size and checks the snapshot after constructing it. The later owner bypasses the C0 string-cache wrapper; C0's local result cannot certify C2's cumulative resource behavior.

Do not rerun C0 merely to obtain more observations. Keep its finite conclusions; fix the owner path that consumes them.

## 6. C1/C1R audit

**Decision: REOPEN narrowly. Preserve the working sharing and release-order evidence.**

Verified source supports lazy admission, a guard before artifact reading, reuse through one registry entry for equal identity tuples, active-lease close refusal without partial invalidation, and test reset closing providers through the normal APIs. Both ordinary release orders are reported embedded. These are useful results.

Four qualifications/corrections are necessary:

### Lease identity is not enforced

[`get_view_via_lease` and `release_lease`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:647) look up only `lease_id`. Each owner starts its counter at 1; neither method verifies that the supplied lease is the stored object belonging to that owner. I reproduced owner B accepting owner A's lease, then invalidating B's lease on release. This is a practical stale-reference/cross-namespace bug, not a request for an adversarial security system. Verify owner/object identity through the normal API.

### Close and release retain unnecessary state

[`release_lease`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:664) leaves inactive records in `_leases`. Thirty additional release cycles left 31 historical records with zero active leases. Release scans the growing history. [`close`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:706) clears views and closes backing but leaves coverage, leases and the registry reference. I reproduced retained positive coverage on a closed registered owner. Drop owned reusable state and inactive registry records; an externally retained old lease needs no central tombstone to remain invalid.

### Registration and singleton claims need narrowing

`registration_install_count = 1` and a generated identity token are assigned in the constructor. The audit explicitly admits no actual SFM/OS callback is installed. The supported result is **3 init calls → 1 owner → 1 simulated registration token**, not one actual callback installation. If the simplified product requires no new observer, remove this criterion instead of inventing a callback to satisfy it.

The registry key includes source SHA, artifact SHA and consumer-profile version, and receives a caller-supplied path without resolving it. It proves sharing for an equal key in one imported module instance. It does not yet enforce one owner per resolved source location across profile/generation changes or duplicate import locations. Production should use one neutral source namespace and keep generation/consumer compatibility as owned state. No general plugin registry is needed.

### C1R's fourth guard criterion remains invalid as an independence claim

For a consistent address-space scan, let C = committed, R = reserved, F = free, and A = address-space ceiling. Then:

`C + R + F <= A`, so `A - C >= R + F >= F`.

If the existing free-VAS test passes at 64 MiB, `A - C` cannot fail a 32 MiB reserve test. The “isolated” Guard D uses 4,088 MiB committed + 300 MiB reserved + 500 MiB free = **4,888 MiB**, exceeding its assumed 4,096 MiB ceiling. I verified these values directly in the harness.

LAA does support a 4 GiB user-address-space ceiling on 64-bit Windows, but does not make this test independent or measure system commit headroom. Windows distinguishes free/reserved/committed regions; neither free VAS nor `4 GiB - committed VAS` is a direct measurement of available system commit. See [Microsoft address-space limits](https://learn.microsoft.com/en-us/windows/win32/memory/memory-limits-for-windows-releases) and [VirtualQuery](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualquery).

**Remove the redundant fourth condition and its claimed qualification.** Do not add another memory subsystem simply to preserve four checks. If system commit pressure later proves material, measure that separate resource explicitly. Snapshot validity and the remaining admission limits still require honest engineering policy.

## 7. C2/C2R audit

**Decision: REOPEN narrowly for ownership/resource closure; preserve same-generation semantic results and the real C2R eviction repair.**

Positive, negative and uncovered states are correctly separated. New folds are resolved privately. Old views are not expanded in place. The documented family/snapshot/pinned refusal and mid-resolution fault cases avoid publishing partial views. Epoch checks detect the injected epoch change. Eviction forgets reusable facts and causes a complete-provider lookup, rather than inventing MasterUnknown. These source paths support the reported finite matrix.

### C2R genuinely bounds the coverage containers—but not all retained memory

`merge_positive` evicts until row-count × estimated-bytes-per-row is within its bound; `merge_negative` enforces its entry cap. This is automatic bound enforcement, not just manual eviction. However:

- At 256 bytes per row, all **128,555 official occurrences account for only 31.39 MiB**. The 32 MiB positive limit can retain the entire official row corpus by its own accounting. It is a very permissive optimization, not a small working-set policy.
- The positive estimate omits variable-length payload/key/container costs; the negative entry limit does not bound key lengths. Treat these as accounting limits, not measured RSS/private-byte ceilings.
- [`acquire_view`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:532) does not enforce the provider's declared 4 MiB decoded-string-cache budget. A reproduced request for all official folds was refused at the snapshot limit, but left **15,556,196 estimated string-cache bytes**, approximately **14.84 MiB**, with no view published and zero positive coverage.
- Negative-only views are charged zero because [`accounted_bytes`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:607) counts positive rows only. A reproduced 1,000-negative view succeeded under a zero-byte pinned budget, even when reusable negatives were capped at three entries. Its `wanted_folds`, envelope and hierarchy still occupy memory.
- Inactive leases and closed-owner coverage add the retention paths described in C1.

The large-refusal diagnostic is a desktop stress check, not a new claim about real Normalizer demand or SFM allocation size. It demonstrates the missing enforcement path without another intrusive SFM experiment.

### Immutable means more limited behavior than the audit claims

[`folded[fold_key] = rows`](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py:590) installs the same mutable lists/dicts used by coverage and later views. I reproduced mutation of a row in view A immediately appearing in view B and the cache.

Expansion/eviction stability remains proven under cooperative read-only consumers. Independent payload copies and enforced immutability do not. Choose the smaller appropriate contract: immutable internal records, or detached consumer-owned copies with a read-only adapter convention. Do not build a general deep-freeze framework. If sharing is retained, consumers must not receive mutable shared ownership accidentally.

### Publication claims are stronger than the tested boundary

The injected fault runs before publication. The commit section merges reusable caches before constructing/registering the envelope and lease, and describes subsequent allocations as having “no further failure points.” Allocation failure can still occur there. Diagnostics and provider-string caches also change during failed expansion; the tested equality concerns selected semantic registries, not every byte of owner state.

Require atomic publication of an authorized complete view. A harmless reusable cache warming on a failed request need not be an all-or-nothing transaction, provided truth and budgets remain valid. **Removing the reusable coverage cache eliminates much of this unnecessary coupled-commit problem.** Do not demand database-style transactional rollback for optional performance state.

## 8. Strongest TXT counterfactual

The fair alternative is one source-bound scoped TXT service:

1. Fresh source identity at the same command boundaries.
2. Reuse covered positive and negative answers for that generation.
3. When genuinely uncovered vocabulary arrives, scan/tokenize the complete TXT once.
4. Materialize only new requested families and merge into a new stable scoped result, preserving global counts, ranks and metadata.
5. Bound retained scoped state and discard it on relevant source change.

This is stronger than the current Normalizer's once-per-command rebuilding and potentially leaner than T2's cumulative-union rematerialization. The measured T2 is a fair working baseline but not the best possible implementation of every detail. Incremental materialization can reduce work; it does not remove full tokenization. A retained complete TXT index would avoid that scan but reintroduce complete indexing/materialization costs and needs its own evidence.

| Situation | Shared scoped TXT | Narrow sidecar service |
|---|---|---|
| First use | Approximately 2.6–2.9 s in referenced authority measurements. Small scoped retention. | Approximately 1.8 s admission plus requested view and owner/freshness overhead. Nontrivial transient/retained cost. |
| Covered repeated use | Already cheap; positive and negative reuse. | Also cheap. Not the decisive advantage. |
| New late vocabulary | Full tokenization again, even with incremental result merge. | Indexed family acquisition; C0 reports 0.161 s for the withheld B request. |
| Source edit | Current TXT can be used after validation. | Matching compilation required for sidecar; manual TXT fallback preserves usability. |
| Deployment | Simpler, no compiled pair. | Compiler, generation identity and compatibility handling. |
| Constrained x86 session | Much smaller retained scoped state in measured small cases. | Must justify admission and retained working set. |

The corrected C0 late result saves approximately **2.465 seconds of authority work** in that fixture. The 16.3× ratio is not a whole-Normalizer speedup. Nor is the 2,968-fold late request a measured frequency distribution of ordinary artist use; the earlier large real workload had only about 800 unique folds across many observations.

## 9. Product-value reassessment

The sidecar materially improves unpredictable new-scope acquisition. It may also save some initial acquisition time, but the complete owner/guard/freshness path has not been timed end to end against the best shared TXT implementation. Source checks and guard costs must be charged to the correct boundary; they should not run per scalar lookup.

Frequency is unresolved. Loading new assets is a real supported workflow, but this package contains no evidence of how often it causes novel folds during a user's session. Common-vocabulary models may be entirely covered already. Do not multiply a single expansion gain by every shot or animation set.

The benefit remains sufficient for a **small optional service** because eliminating a multi-second rescan at a known interaction boundary is worthwhile. It does not justify keeping a 32 MiB decoded family cache, 100,000 negative entries, historical lease registries or automatic generation orchestration by default. Most benefit comes from retaining the complete packed authority and doing bounded lookups, not from avoiding every repeated indexed lookup.

The architecture has not crossed the point where the sidecar concept is mostly solving self-created problems. **The current owner implementation is approaching that point.** If ordinary use starts requiring background watchers, job resumption, multiple generations, general cache coordination or per-document static authorities, I would retreat to shared scoped TXT for v1 rather than expand this infrastructure.

## 10. Complexity-drift classification

| Mechanism | Classification | Decision |
|---|---|---|
| Offline compiler | ESSENTIAL PRODUCT ARCHITECTURE | Keep one deterministic compilation path. |
| Packed sidecar | ESSENTIAL PRODUCT ARCHITECTURE | Keep as admitted complete authority; optional to the user workflow. |
| Manifest/pointer | NECESSARY SAFETY MECHANISM | Keep minimal generation discovery/consistent publication; no watcher service. |
| Source SHA binding | NECESSARY SAFETY MECHANISM | Keep exact generation binding and consumer-boundary source checks. |
| Process-wide owner | ESSENTIAL PRODUCT ARCHITECTURE | Narrow to one neutral service per resolved source namespace. |
| Pre-admission guard | NECESSARY SAFETY MECHANISM | Keep defensible checks; remove fictitious independent commit criterion. |
| Leases | NECESSARY SAFETY MECHANISM | Short-lived operation tokens; identity check and bounded cleanup. |
| Immutable views | NECESSARY SAFETY MECHANISM | Stable complete action snapshots; no general immutability framework. |
| Positive/negative coverage | NECESSARY SAFETY MECHANISM | Keep in each action/view so uncovered cannot mean absent. |
| Separate reusable coverage cache | OPTIONAL OPTIMIZATION | Remove from initial production; indexed provider remains complete. |
| FIFO eviction | OPTIONAL OPTIMIZATION | Remove with that cache; retain tests if a small cache returns later. |
| Resource budgets | NECESSARY SAFETY MECHANISM | Keep a few enforced aggregate limits; present current numbers as provisional. |
| Epoch token | NECESSARY SAFETY MECHANISM | One simple authorization generation; not a historical version store. |
| Fault injection | QUALIFICATION SCAFFOLDING — SHOULD NOT SHIP | Keep test seams; no deployed per-fold callbacks/counters. |
| Desktop qualification harnesses | QUALIFICATION SCAFFOLDING — SHOULD NOT SHIP | Preserve reproducible tests outside runtime imports. |
| Embedded SFM probes | QUALIFICATION SCAFFOLDING — SHOULD NOT SHIP | Preserve scripts/raw results; no autoinit residue. |
| New invalidation watcher/polling framework | COMPLEXITY DRIFT / SHOULD REMOVE OR SIMPLIFY | Use explicit command/use boundaries initially. |
| Serialized generation replacement | NECESSARY SAFETY MECHANISM | Keep only retire, drain, close, lazy readmission. |
| TXT fallback | ESSENTIAL PRODUCT ARCHITECTURE | Preserve manual usability for edits/absence/refusal through the existing producer. |
| Registration-install simulation tokens | QUALIFICATION SCAFFOLDING — SHOULD NOT SHIP | Delete unless a real consumer callback needs a real installation test. |
| Full cached-fold union rebuilt on each request | COMPLEXITY DRIFT / SHOULD REMOVE OR SIMPLIFY | Avoid O(entire cache) work just to answer a small request. |
| Historical inactive leases | COMPLEXITY DRIFT / SHOULD REMOVE OR SIMPLIFY | Delete records at release; no lifetime journal needed. |

## 11. Resource-policy assessment

Session sharing remains justified when it prevents duplicate admission and repeated parsing. It is not a license to retain all decoded history. The corrected approximately 20–23 MiB admitted cost can be reasonable in a roomy session; approximately 63 MiB sampled admission pressure is material in loaded x86 SFM.

The loaded 73.44 MiB largest free region is relevant, but **comparing aggregate private-byte peak delta directly with one largest contiguous region is dimensionally misleading**. The peak comprises multiple allocations, not one 63 MiB contiguous request. Do not claim that a 63 MiB peak exceeding a later 57.62 MiB region proves impending allocation failure. Conversely, success once does not establish adequate future headroom. Free address space, required contiguous allocations and system commit are separate concerns.

Current thresholds are not a production policy. A 64 MiB artifact allowance with a fixed 32 MiB largest-region minimum could admit an artifact larger than the largest region. A 64 MiB total-free floor leaves almost no margin over the observed official admission increment. Guard valid artifact size and observed admission envelope with an explicit margin; do not invent a universal “safe” numeric value from one run. Refusal should occur before attempting the allocation and should lead to the separately viable manual TXT path.

**Cache recommendation:** no separate reusable family/negative cache initially. Keep view coverage for active operations and a genuinely bounded provider decoding cache, including growth on unsuccessful requests. If later profiling justifies reuse, start with a small combined budget measured on actual workloads, not 32 MiB positive plus 100,000 negatives by inheritance.

**Across documents:** CONDITIONAL retention of the same static provider is reasonable because static semantics are not document-owned. Always retire old document jobs/bindings and action views. Permit release under resource pressure or an explicit release action. Do not force close/reopen on every switch, which repeats admission spikes and may not return allocator pages immediately. Do not retain providers for obsolete namespaces indefinitely.

**Admission:** lazy at an explicit authority-requiring command. No eager SFM startup load, per-document preload or mandatory permission dialog. Automatic observers must not initiate a surprising multi-second admission/fallback scan. A separate “Prepare/refresh authority” action can support their readiness.

## 12. Qualification-to-production pruning

**Keep in production:** compiler; compatible complete binary reader; one small shared source service; source/generation identity; action coverage; operation-bound leases; fresh live consumer checks; pre-read admission refusal; explicit bounded resource policy; minimal retirement; existing scoped TXT manual path.

**Keep only in tests:** synthetic namespaces, guard snapshots, registration tokens, per-fold fault hooks, counters used solely for assertions, whole-corpus stress requests, helper reset functions, temporary artifact creation, sampler launchers, autoinit/mainmenu probes and historical audit files.

**Delete/refactor before integration:** reusable coverage cache and its coupled atomic merge; inactive lease history; retained closed-owner caches; mutable cross-consumer ownership; owner-local-ID-only authorization; redundant commit guard; generation/profile fields as separate owner namespaces; repeated full-cache set construction; error paths that leave PREPARING stuck. Consolidate duplicated adapter utility code where practical without reopening semantics.

**Defer until a real consumer requires it:** filesystem watchers, periodic polling, hot replacement, multiple concurrent generations, automatic fallback from observer callbacks, shared view interning, expanded cache policies, generalized metadata adapters and full Character Preset integration. Keep Candidate B/C experiments deferred.

## 13. Minimum necessary C3

**C3 is necessary, but current checkpoint is NO-GO to start it. First repair/prune the C1/C2 foundation.** The necessary C3 is source freshness and action authorization, not a lifecycle platform.

The minimum model:

1. At an explicit command/preparation boundary, read current source identity and resolve the candidate manifest/pointer. Hash the actual TXT bytes; size/mtime alone cannot detect same-size preserved-mtime edits. Bind profile acceptance to that same verified generation.
2. Reuse a current admitted generation when identity/compatibility remain valid. A pointer timestamp or equivalent rewrite alone does not require reopen. A pointer is candidate discovery, not itself semantic truth.
3. If the TXT changes or becomes unreadable, revoke eligibility for new old-generation work, including old negatives. Retain detached payloads only for diagnostics/cleanup. Before mutation, the normal consumer authorization gate rejects stale leases/views.
4. Before admitting replacement, stop new work, drain/release active operation references and close old owned backing/caches. Fresh admission occurs on a later explicit command. Failure leaves authority unavailable; no silent revival of a source-mismatched generation.
5. Preserve existing immediately-before-use source checks and existing transaction cleanup semantics. No switch to a new generation inside an operation. Checks do not make arbitrary external editors atomic with native SFM; do not claim that impossible exclusion guarantee.

Minimal evidence cases can be consolidated into three scenarios: unchanged/same-pointer reuse; a real same-size/mtime-preserved source edit that changes an old negative to positive; and admission/freshness failure with stale references held. Include unreadable source, missing/stale/corrupt candidate and resource refusal as small fixtures in the last scenario, not separate research gates.

The current missing-artifact path demonstrates a concrete repair target: `_artifact_byte_length()` can raise outside `_ensure_admitted`'s failure handling, leaving the owner PREPARING. I reproduced that on desktop. C3 must classify failure and leave a recoverable unavailable state, but this does not require a new exception hierarchy.

**Explicit manual Normalizer command:** fresh checks at existing boundaries; allow compatible current TXT fallback with a concise status. If the source changed after planning, abort/replan rather than silently replace the plan's producer halfway through mutation.

**Live/automatic observer:** reuse prepared authority only after its existing action-boundary validation. If it is stale or unavailable, defer that event and request explicit preparation; no hidden parse, admission or delayed surprise application. If later measurements show existing event frequency makes hashing costly, assess a coalescing policy then. Do not install a new watcher now.

**Future Character Preset:** library browsing need not hold an authority lease. Capture/preview/apply obtain current semantics at their own operation boundaries. A changed generation between preview and Apply requires relevant revalidation, not a background rewrite of saved values.

## 14. C4 simplification/removal assessment

**SIMPLIFY C4; remove it as a separate ambitious replacement phase.**

The proposed rule—retire current authority, refuse new work, close once operation leases release, lazily admit fresh authority on the next command—is sufficient. There is no demonstrated need for seamless handoff, overlap, queued replacement jobs or automatic resumption.

Fold one drain/close/readmit scenario into minimum C3. Document-switch behavior belongs in ordinary consumer integration: static provider may survive; document-bound jobs may not. Verify actual owned references are released and no second full provider overlaps. Do not demand a repeat of the entire historical resource campaign merely to prove allocator bytes return exactly to baseline; that was never a realistic ownership contract.

## 15. Original-goal scorecard

| Goal | Assessment today | Tradeoff |
|---|---|---|
| Artist-visible responsiveness | Promising, not demonstrated end to end | Late authority acquisition improves; warm shared TXT is already fast. |
| Correctness | Mixed; blocked on narrow repairs | Static semantics strong; owner authorization still defective. |
| SFM stability | Conditional | Appropriate main-thread context established; no current integrated production evidence. |
| 32-bit memory safety | Not ready | Admission peak material; retained ownership/budgets incomplete. |
| Implementation complexity | Too high in current owner | Several layers can be deleted without losing the main gain. |
| Maintenance burden | Recoverable | One validator is a strong improvement; duplicated lifetime/cache policy is not. |
| Debuggability | Good records, overstated conclusions | Keep raw evidence and concise failure reasons; strengthen source-first gate review. |
| Advanced-modeler portability | Conditional | Editable TXT preserved; compilation/profile refusal must have a usable manual path. |
| Normalizer usefulness | Credible | A real authority seam and late-scope benefit exist; actual command acceptance remains. |
| Future Character Preset usefulness | Plausible, unqualified | Shared semantics useful; generic ConsumerP is not its production adapter. |
| Editable TXT authority | Strong architectural fit | Must reject stale sidecar authority after actual source change. |

## 16. Claims still unproven

- Whole-Normalizer time saved versus the strongest shared-TXT service, including actual owner/guard/freshness overhead.
- Frequency and size of genuinely new vocabulary in real use.
- Production-safe resource thresholds, all retained-memory bounds, and readiness under arbitrary constrained sessions.
- Actual callback installation and import-stable process-wide sharing across two real tools.
- Independent/enforced view immutability and correct cross-owner lease handling in the current code.
- Real source/pointer invalidation, stale-action refusal, complete failure recovery and serialized readmission.
- General custom-Master consumer equivalence outside the explicit source profile.
- Character Preset adapter compatibility and real production coexistence.

These limits do not call for a broad new benchmark catalog. Most are closed by pruning, focused foundation checks, minimum C3 and one existing-executor Normalizer integration acceptance.

## 17. Recommended ledger corrections/additions

1. Preserve C0 closure, but label corrected runtime numbers as reported embedded observations in this package. Remove “statistically identical” and “independent of host load” conclusions from two observations.
2. Correct aggregate-private-peak versus contiguous-region reasoning. Preserve resource concern without the invalid comparison.
3. Describe C0.6's timed equality as folded-key-set equality, supported separately by semantic parity tests. It is family-cold acquisition, not untouched-string memory.
4. Reopen C1 narrowly for foreign-lease identity, retained closed-owner/history state and guard-policy correction. Narrow “one registration installation” to the simulated token actually tested.
5. Withdraw the independent fourth guard claim: record the 4,888 MiB impossible fixture and redundant inequality.
6. Preserve C2R's successful FIFO/accounting repair; reopen overall bounded-resource closure for string-cache bypass, negative view accounting and ownership cleanup.
7. Replace “independent immutable copies” with expansion/eviction stability under read-only convention until sharing is corrected.
8. Narrow rollback claims to the tested pre-publication semantic state. Diagnostics and provider caches change; commit-phase allocation failure was not exercised.
9. Record the missing-artifact PREPARING failure as an existing admission error path to fix, not as evidence that C3 ran.
10. Change “C3 next” to “foundation simplification/repair, then minimum C3.” Replace planned C4 with the small drain/readmit scenario.
11. Correct manifest chronology: actual source invalidation is precisely part of minimum C3; the manifest's sentence excluding it from C3 conflicts with the controlling brief.
12. Link the recovered original Round 2 review. Keep the transient publisher race visible with the supported publication-concurrency scope.

## 18. One cohesive architecture I would choose TODAY

```text
editable Master TXT
        ↓ offline deterministic compiler
complete immutable binary generation + small discovery metadata
        ↓ explicit command/preparation boundary
one neutral source service
  current source/profile check
  lazy resource admission
  packed authority + bounded decode working set
        ↓
complete action view with covered positives/negatives
  short-lived owner-checked lease
  existing consumer freshness and mutation guards
        ↓
release action state

source change → retire → drain → close → next-command lazy admission
manual unavailable/refused sidecar → current compatible scoped TXT path
```

No separate reusable family cache by default; no lifetime lease history; no watchers; no automatic background rebuild; no multi-generation overlap; no library-browsing lease. The remaining lifecycle machinery is the minimum needed to keep authoritative bytes and action permission consistent.

If delivering even this bounded service requires repeated new infrastructure phases or a persistent memory budget disproportionate to its measured late-scope benefit, stop and ship shared scoped TXT. That is the retreat boundary, rather than continued expansion because prior gates exist.

## 19. Go/no-go table

| Required decision | Verdict | Reason |
|---|---|---|
| 1. C0 | **CLOSED** | Finite consumer/profile/validator/resource/value qualification stands with corrected interpretation. |
| 2. C1/C1R | **REOPEN** | Lease identity, cleanup/history and invalid guard independence claim. |
| 3. C2/C2R | **REOPEN** | Broader resource/ownership guarantees not established; preserve actual FIFO repair. |
| 4. Sidecar concept | **SIMPLIFY** | Keep differentiated indexed late-scope value, strip optional machinery. |
| 5. Current binary format | **KEEP EXPERIMENTAL** | No demonstrated missing field or layout defect from this review. |
| 6. Process-wide owner | **NARROW** | One neutral source service and action leases, not a lifecycle platform. |
| 7. Reusable positive/negative coverage cache | **REMOVE** | Initial production default; per-view coverage and bounded provider decoding remain. |
| 8. Retention across documents | **CONDITIONAL** | Same static source, fresh eligibility, adequate resources; release document-owned state. |
| 9. Candidate B/C | **DEFER** | Do not reopen backing experiments to fix owner defects. |
| 10. C3 | **NO-GO now** | Necessary minimum scope defined above; foundation repair must precede execution. |
| 11. C4 as conceived | **SIMPLIFY** | Fold drain/close/lazy-readmission into C3/integration; remove standalone hot-replacement phase. |
| 12. Normalizer production integration now | **NO-GO** | Repair foundation, minimum C3, then one real existing-executor acceptance. |
| 13. Character Preset integration now | **NO-GO** | Provider foundation and its own narrow adapter remain unqualified. |
| 14. Format v1 freeze now | **NO-GO** | No redesign requested; finish the actual first-consumer service contract before freezing. |
| 15. Overall direction | **OVER-ENGINEERED BUT RECOVERABLE** | Product value survives; current implementation/claims need subtraction and correction. |

## 20. Immediate next three actions

1. **Checkpoint this audit and correct status/evidence wording.** Preserve C0 and the specific successful C1/C2 results; record narrow reopenings. Do not begin C3 yet.
2. **Perform one bounded foundation simplification/repair.** Remove the default reusable coverage cache and inactive history; enforce lease ownership; clear terminal state; bound actual retained action/decode state; correct the guard and payload-ownership contract. Verify the reproduced defects and retained semantics with focused checks, plus only the necessary embedded compatibility acceptance for the changed runtime path.
3. **Once those checks pass, execute minimum C3 and then the existing Normalizer integration acceptance.** Use real source-change/drain/readmit cases, no new watcher or separate ambitious C4. Measure the actual authority contribution in that integration; keep Character Preset and format freeze behind their appropriate remaining contract checks.

### Independent review evidence

- [Desktop reproduction results](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/round3_independent_checks.json)
- [Exact packaged owner source](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/01_CURRENT_QUALIFICATION_SOURCE/session_owner.py)
- [C0 audit](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/03_C0/SFM_MASTER_SIDECAR_GATE_C0_PROMOTION_PREREQUISITES_AUDIT.md)
- [C1/C1R audit](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/04_C1_C1R/SFM_MASTER_SIDECAR_GATE_C1_SHARED_OWNER_FOUNDATION_AUDIT.md)
- [C2/C2R audit](C:/Users/REDACTED/Documents/Codex/2026-09-07/review-x20-3/work/round3_sidecar/05_C2_C2R/SFM_MASTER_SIDECAR_GATE_C2_VIEW_EXPANSION_AUDIT.md)

The reproduction used existing packaged code, verified matching production imports and the unchanged official artifact, in a disposable desktop Python process. It exercised current owner behavior only; no SFM runtime qualification or new implementation was performed.
