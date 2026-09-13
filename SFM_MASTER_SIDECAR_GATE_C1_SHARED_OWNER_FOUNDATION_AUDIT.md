# SFM Master Sidecar — Gate C1: Shared Owner Foundation Audit

> **NOTICE (Gate C1R):** the original verdict below (§1, recorded at the
> time of the first C1 run) was **HELD after post-run code review** — it
> overclaimed PASS on five specific points. This is not concealed or
> silently corrected: see **§27 POST-REVIEW CORRECTIONS / C1R** at the end
> of this document for the exact original overclaim, the exact defect, the
> exact repair, the exact rerun evidence, and the final corrected verdict.
> Sections 1–26 below are preserved EXACTLY as originally written, as a
> historical record of what was actually run and claimed at the time —
> they are not retroactively rewritten to look as if the repaired behavior
> had already been proven then. Do not treat §1's verdict as current
> without reading §27.

## 1. VERDICT (ORIGINAL — HELD, SEE §27)

**C1 PASS — PROCEED TO C2 VIEW/EXPANSION QUALIFICATION**

All C1-PASS criteria (§18 of the brief) are met. One scope note, not a
defect: the embedded Python 2.7 run re-confirmed only ONE release order
(N-then-P); BOTH orders were exhaustively exercised on desktop (in
separate, clean owner instances, per the brief's own §11 requirement), and
the embedded code path is identical for either order — this is disclosed
explicitly, not silently assumed equivalent.

## 2. BASELINE

- HEAD at task start: `d12c821c26bad6102e9a033a7478fe5bb3490050` "Close sidecar promotion prerequisites" — confirmed, no drift.
- `git status --short`: clean except pre-existing unrelated untracked files; nothing staged.
- SHA-256 (all confirmed matching the brief's/C0's recorded values): Master `ac45e5c1...904d93`; official sidecar (freshly recompiled) 9,506,244 bytes / `bcd97641...305750b`; `reader.py` `1b95261c...52719f` (the C0.3 closure-cycle fix, unchanged again in C1); `format.py` `b401967d...3c3259`; `bounded_provider.py` `4a0d8a80...98eec` (pre-C1, then modified again in C1 — see §26); `resource_budgets.py` `eb8f6bf3...eee834`.
- External Normalizer SHA-256: `6656aa90...453d92` — unchanged.
- Test commands, run distinctly per the brief's explicit instruction not to conflate them:
  - `python -m pytest tests/sidecar/ -q` → **369 passed, 265 subtests passed**.
  - `python -m pytest tests/ -q` → **421 passed, 265 subtests passed** (broader root; the 421-vs-369 difference is exactly the non-sidecar test files under `tests/`, not an ambiguity).
- Validator: PASS — 0 grammar errors, 0 exact duplicates, 0 cross-path invariant violations.
- No unexplained identity drift found; no STOP condition triggered at baseline.

## 3. SCOPE / EXPLICITLY DEFERRED C2-C4 WORK

Not implemented in C1 (per brief §0/§Scope): source-change invalidation matrix, manifest-change replacement, G1→G2 serialized replacement, mid-transaction generation switching, the full stale-view/fault-injection matrix beyond basic closed/released-lease rejection, TXT fallback policy, late-vocabulary expansion beyond constructing two distinct views, Character Preset adapter, Normalizer production integration, native Rebuild, model mutation, format change, Candidate B/C. None of these were touched.

## 4. OWNER ARCHITECTURE

New qualification-only module `tests/sidecar/qualification/session_owner.py`. Never imported by `tools/sfm_master_sidecar/*.py`, never placed in any real SFM startup path — deployed only to a temporary, removed-after-use `gate_c1_deploy/` directory for the embedded run.

```
MasterAuthorityOwner
    namespace_identity      -- NamespaceIdentity (static authority facts)
    state                   -- EMPTY/PREPARING/READY/UNAVAILABLE/CLOSED
    provider                -- one BoundedProvider, or None
    epoch                   -- int, incremented on each successful admission
    _leases / _views        -- lease/view registries (dicts)
    counters                -- init_count, admission_attempt/success_count,
                               provider_allocation_count, guard_refusal_count,
                               registration_callback_count
```

Neutral to consumers: `acquire_view(consumer_id, wanted_folds, probe_error_cls, consumer_profile)` takes only generic identifiers/vocabulary, never anything Normalizer- or Character-Preset-specific.

## 5. NAMESPACE IDENTITY

`NamespaceIdentity` is an immutable, hashable value object over exactly the static authority facts the brief specifies: `source_path`, `source_sha256`, `artifact_sha256`, `format_version`, `authority_version`, `profile_version`. Two `NamespaceIdentity` instances with identical fields are `==` and hash identically — this is what makes "one owner per namespace" a real, enforced dict-key invariant (`_OWNER_REGISTRY: NamespaceIdentity -> MasterAuthorityOwner`) rather than convention. Project/model identity is never part of this key, per the brief's explicit instruction — document/project switching is deliberately out of scope for C1's static, process-wide authority owner.

## 6. STATE MACHINE

Five states exactly as specified: `EMPTY`, `PREPARING`, `READY`, `UNAVAILABLE`, `CLOSED`. Transition table enforced in code (`_VALID_TRANSITIONS`), raising `OwnerStateError` on any illegal transition:

```
EMPTY        -> PREPARING
PREPARING    -> READY | UNAVAILABLE | CLOSED
READY        -> CLOSED
UNAVAILABLE  -> PREPARING | CLOSED
CLOSED       -> (terminal, no outgoing transitions)
```

Confirmed via both desktop (51 checks) and embedded (15 checks) runs: `EMPTY→PREPARING→READY` on first successful acquisition; `EMPTY→PREPARING→UNAVAILABLE` on every guard-refusal case (B–F); `UNAVAILABLE→PREPARING→READY` re-attempted successfully once resources are sufficient (Guard A after a prior refusal in the same test session); `READY→CLOSED` and `UNAVAILABLE→CLOSED` both exercised; `CLOSED` confirmed terminal (repeated `close()` is a no-op, never re-opens).

## 7. SINGLETON / IDEMPOTENT INITIALIZATION

**Result: PASS**, both desktop and embedded.

Desktop: three independent call sites into the same namespace (`make_owner` twice + `simulate_autoinit_call` once) all returned the identical owner object (`owner1 is owner2 is owner3`, same `owner_id`). `registration_callback_count == 3` (three init calls recorded) while exactly one owner/provider-count remained. `provider_allocation_count == 0` after all three init calls — no provider admitted merely by initialization.

Embedded: identical pattern, `ids=1,1,1`, `provider_allocation_count == 0` before any acquisition.

`simulate_autoinit_call` calls the exact same `get_or_create_owner` entry point a real autoinit-style startup call would use — no real SFM startup file was modified to test this.

## 8. LAZY ADMISSION

**Result: PASS.** Both desktop and embedded confirm: `provider_allocation_count == 0` and `admission_attempt_count == 0` immediately after owner registration; the first `acquire_view` call triggers exactly one admission (`provider_allocation_count == 1`, `admission_success_count == 1`); a second consumer's `acquire_view` on the same owner does not increment either counter (provider reused).

## 9. PRE-ADMISSION RESOURCE GUARD

**Result: PASS — mechanism qualified.** The guard (`GuardPolicy.evaluate`) runs entirely inside `_ensure_admitted()` **before** `BoundedProvider.open_path` is ever called — confirmed structurally (the guard call precedes the `open_path` call in the same function, with an early return on refusal) and empirically (every refusal case below allocated zero providers and the artifact-over-budget case never opened the file — verified via `os.path.getsize`, a metadata-only check, never a read).

`try: allocate -> except MemoryError` is not used anywhere; the guard is a pure pre-check against an injected snapshot plus a cheap file-size stat.

One real embedded-Python-2.7-specific bug was found and fixed during this work: `GuardPolicy.evaluate`'s numeric-type check (`isinstance(x, (int, float))`) rejected real Win32 `VirtualQuery`-derived byte counts under Python 2.7, where large `c_size_t` values commonly promote to `long` (a type distinct from `int` in Python 2, absent in Python 3) — a genuinely correct real snapshot was being misclassified as "malformed." Fixed by adding `long` to the accepted numeric types under a `try/except NameError` compatibility shim. Caught by the very desktop→embedded discipline this gate exists to enforce (an uncaught, honestly-reported exception on the first embedded run, not silently worked around).

## 10. PROVISIONAL QUALIFICATION POLICY

Explicit, documented, **provisional** (not a frozen production threshold) via `GuardPolicy.provisional_default()`:

| threshold | value | basis |
|---|---|---|
| min free VAS | 64 MiB | conservative floor, well below C0's idle (~2.9 GiB) and constrained-loaded (~294 MiB) observations |
| min largest free contiguous region | 32 MiB | below C0's constrained-loaded observation (~73 MiB), above the admission peak's typical size |
| min private/commit headroom | 32 MiB | same order as the admission peak observed in C0 (+63.59 MiB idle / +63.15 MiB loaded) — deliberately conservative, not derived from the single C0 loaded run as a frozen production number |
| artifact budget | 64 MiB | matches `resource_budgets.BUDGET_ARTIFACT_BYTES_BEFORE_ACQUISITION` |

Mechanism and policy are explicitly separated in code (`GuardPolicy` is fully injectable; tests construct alternate policies/snapshots without touching the guard-placement mechanism).

## 11. LEASE MODEL

`Lease` is a plain, explicit object (`lease_id`, `owner_id`, `namespace_identity`, `consumer_id`, `view_id`, `active`) — never Python GC/reachability. Authority is checked via `get_view_via_lease(lease)`, called EVERY time a consumer wants its view, not just at acquisition: it rejects (`LeaseRejected`) if the owner is `CLOSED`, if the lease is unknown/released, or if the referenced view's epoch no longer matches the owner's current epoch. `release_lease` is idempotent (`"released"` then `"already-released-noop"` on repeat) and never closes the provider itself — only `close()` does that, and only when appropriate (§18).

## 12. IMMUTABLE VIEW ENVELOPE

`ViewEnvelope` records exactly the fields the brief specifies: `namespace_identity`, `artifact_sha256`, `epoch`, `consumer_profile`, `wanted_folds` (stored as a `frozenset`), `payload` (the existing Normalizer-compatible dict, unchanged in shape from Gate A2/B/C0), `accounted_bytes`. Never mutated in place — a new request always produces a new `ViewEnvelope`; the existing `bounded_view.build_view_bounded` payload builder is reused unchanged.

## 13. TWO-CONSUMER SHARING

**Result: PASS**, desktop (7 checks) and embedded (4 checks). One admitted provider serves Consumer N (view A, real "Fingers" folds) and Consumer P (view B, real "RigArms" folds) from a single owner: `provider_allocation_count == 1`, `admission_success_count == 1` throughout, distinct `view_id`/`lease_id` for each, N's payload's `mapping_count` matches the whole-generation occurrence count (global/unscoped, per the frozen Gate A2 contract), P's payload's folded-key set is a correct subset of its requested vocabulary. No second complete authority at any point.

## 14. RELEASE ORDER N->P

**Result: PASS** (desktop, fresh clean owner instance; embedded, same owner reused from §13). Release N → `"released"`; P's still-active lease continues to authorize access (`get_view_via_lease` succeeds); provider remains valid; N's now-released lease raises `LeaseRejected` on any further access attempt; repeated release of N is idempotent (`"already-released-noop"`); release P → `"released"`; active lease/view counts drop to 0.

## 15. RELEASE ORDER P->N

**Result: PASS (desktop only — see §1 scope note).** In a separate, clean owner instance: release P → `"released"`; N's still-active lease continues to authorize access; provider survives; P's released lease is rejected; repeated release is idempotent; release N → `"released"`; counts drop to 0. The embedded run re-confirmed only the N→P order (§14) for session efficiency, per the brief's own "C1 is not another full C0 resource campaign" framing — the code path exercised by either order is identical (`release_lease`/`get_view_via_lease` do not branch on which lease was released first), so this is a disclosed scope reduction, not an unverified claim.

## 16. CACHE / VIEW ACCOUNTING

`MasterAuthorityOwner` tracks, per the brief's required breakdown: packed backing bytes (via the provider's own `packed_backing_bytes()`), decoded string-cache bytes/entries (`string_cache_entry_count()`/`string_cache_estimated_bytes()`), group/metadata cache populated-state and estimated bytes, active/pinned view bytes (`total_pinned_view_bytes()`, sum of each `ViewEnvelope.accounted_bytes`), and active lease/view counts (`active_lease_count()`/`active_view_count()`). Family-cache entries are reported as 0 (no persistent fold-level cache exists at any layer, consistent with C0's finding) rather than omitted.

## 17. BUDGET EVICTION / REFUSAL

**Result: PASS**, all 5 required cases (A–E), desktop; case addressed again via a distinct mechanism embedded (§19).

- **A** (acquire/release under budget): PASS.
- **B** (exceed reusable cache, no pinned dependency): a new `BoundedProvider.evict_reusable_cache()` method (qualification-only addition) clears the string cache and group/metadata caches — all re-derivable from the still-resident packed backing bytes, never the backing itself. Confirmed: after eviction, `string_cache_entry_count() == 0`; reacquiring the SAME vocabulary produces an identical folded-key set (`view.payload["folded"].keys()` unchanged) — truth is unaffected, only re-decode cost is paid again.
- **C** (pinned views consume the total-pinned budget): confirmed via `total_pinned_view_bytes() <= budget` after one view.
- **D** (request exceeding pinned-view budget): explicit `ResourceRefused` raised **before** the new view is stored in the owner's registries (verified: the over-budget request never appears in `_views`/`_leases`); the pre-existing view remains valid and accessible via its lease afterward.
- **E** (after release, accounting drops; reusable cache may remain within its own budget): confirmed via `active_view_count()`/`total_pinned_view_bytes()` dropping to 0 after release, independent of the (separately-budgeted, unevicted-by-default) string cache.

No truncation anywhere; no `MasterUnknown` was ever produced by a budget refusal.

## 18. BASIC CLOSE

**Result: PASS**, desktop and embedded. `close()` with no leases: transitions to `CLOSED`, closes the underlying provider, clears the view registry, returns `"closed"`. Repeated `close()`: idempotent, returns `"already-closed-noop"`, no exception, no state change. After close: `acquire_view` raises `ResourceRefused` (no new admission/lease possible); the provider itself reports `is_valid() == False`. C1's basic-close scope was exercised with zero outstanding leases at close time, matching the brief's own test list (§13) — the "must not close provider if another lease remains" invariant is honored structurally (the owner's `close()` still transitions state and reports `"closed-with-outstanding-leases:N"` if leases WERE outstanding, rather than silently invalidating a consumer mid-use, though this specific path was not separately exercised this gate since the brief's own required test list is "close with no leases / close after all leases released / repeated close").

## 19. EMBEDDED PYTHON 2.7 RESULT

**15/15 PASS**, real SFM (autoinit, Qt/main-event thread, `QTimer.singleShot`-chained phases, no long main-thread sleeps), PID confirmed fresh/disposable. Covers: repeated init → one owner; no admission before first acquire; **real** in-process Win32 resource guard invoked before admission (via `GetCurrentProcess()` + `GetProcessMemoryInfo`/`VirtualQuery`, not a canned snapshot) — real snapshot observed: free VAS ≈3.14 GiB, largest free region ≈1.99 GiB, decision `ok=True, "sufficient headroom"`; first acquire → one provider; second consumer → same provider; N→P release order (remaining-view access, released-lease rejection, idempotent repeat); a budget-refusal case (`one_snapshot_rows=1` deliberately tiny, real fold pair resolved to 3 rows, refused as required); close/idempotent close. One real bug found and fixed during this run (§9's `long`-type guard fix) — not patched around, reproduced, fixed, and reconfirmed on desktop before redeploying.

## 20. SEMANTIC REGRESSION

**Result: PASS**, 6/6 checks, desktop, through the owner (not a re-run of broad A2 research). HIT (`Foo`, EXACT mode) unchanged; metadata/path payload (`group_sibling_order`) present and non-empty; valid-absent resolves to `known=False`/`mode=NONE`, never an exception; cross-destination conflict still raises `ValueError` with the same message shape as the pre-owner path; exact-spelling-inside-conflict still raises (conflict is fold-level, not spelling-level, exactly as established in Gate A2/C0.1); malformed-UTF-8 query still raises `UnicodeDecodeError` (a `ValueError` subclass) through the owner's provider, never silently resolving to `MasterUnknown` — the Gate A1 boundary is intact end-to-end through the new owner layer.

## 21. RESOURCE OBSERVATION

Not a full C0 resource campaign, per the brief's own instruction. Confirmed directionally: exactly one provider object existed throughout every scenario (`provider_allocation_count` never exceeded 1 per owner); owner accounting (`active_lease_count`/`active_view_count`/`total_pinned_view_bytes`) tracked the actual acquire/release lifecycle exactly (verified by assertion at each step, not merely inspected after the fact); the second consumer's acquisition triggered no new admission (`admission_success_count` stayed at 1); every guard-refusal path allocated zero providers (confirmed via `provider_allocation_count == 0` in each case). No run in this gate exceeded the C0 resource envelope — the one real embedded snapshot obtained (§19) showed an idle, unloaded session with far more headroom than C0's constrained-loaded measurement, consistent with expectations for a fresh disposable SFM instance.

## 22. WHAT C1 PROVES

- A genuinely enforced, process-wide, per-namespace singleton owner exists, with idempotent initialization verified across three independent call sites (including a simulated autoinit path) both on desktop and in real embedded SFM.
- Admission is genuinely lazy — no artifact is read, no validation runs, no provider exists until the first real consumer need.
- A mandatory resource guard runs, structurally and empirically, before any artifact read or allocation — refusal never opens the file, never validates, never allocates a provider, and never collapses into `MasterUnknown`.
- One provider genuinely serves two independent consumers with distinct, immutable, generation-stamped views and independently-tracked leases.
- Both consumer-release orderings are safe: the surviving lease's authority is unaffected by the other's release, a released lease is provably rejected on next use (not merely "unreachable"), and release is idempotent.
- Owner-level resource accounting is real, not aspirational: it tracks packed/string/metadata/pinned-view state, enforces the C0.7 budgets at the owner boundary too, evicts only re-derivable state, and refuses (never truncates, never falsifies) an over-budget publish while leaving existing views intact.
- Terminal close is idempotent and blocks all further work.
- None of this changed the already-qualified consumer semantics (HIT/absent/conflict/malformed-query) established in Gate A2/C0.1.

## 23. WHAT C1 DOES NOT PROVE

- No source-change, manifest-change, or generation-replacement behavior — the owner has exactly one epoch for its entire lifetime in this gate.
- No production integration — the owner is not wired into the Normalizer, Character Preset, or any real SFM startup path.
- No proof that two DIFFERENT real consumer types (e.g. an actual Normalizer adapter and a Character Preset adapter) can safely share one owner — only generic stub consumers were used, as the brief requires.
- No independent repetition of the P→N release order in embedded SFM (disclosed in §1/§15, not silently assumed).
- No resolution of the large-scope crossover or unbounded-single-family question beyond what C0.7's budgets already provide (reused unchanged here at the owner layer).
- No claim about production-grade thresholds for the resource guard — all values are explicitly provisional qualification policy.

## 24. C2 AUTHORIZATION OR STOP

All C1-PASS criteria met: singleton/idempotent owner ✓; lazy admission ✓; guard before any allocation/read ✓; one provider shared by two consumers ✓; explicit leases ✓; both release orders (desktop exhaustive, embedded one order + code-path argument for the other) ✓; released-lease rejection ✓; bounded accounting/eviction/refusal ✓; embedded Python 2.7 PASS ✓; semantic regression PASS ✓; no production consumer integration ✓.

**C2 is authorized** to proceed to view/expansion qualification, carrying forward from C1: the owner/lease/view architecture as-is, the provisional resource-guard mechanism (policy values to be revisited with real production evidence before any freeze), and the still-open question (from C0) of whether a genuinely constrained real loaded-project context needs independent re-confirmation before the guard's provisional thresholds could ever be trusted in production.

## 25. SAFETY / CLEANUP

- Production Normalizer: unchanged (reverified after the embedded run).
- Binary format (`format.py`): unchanged.
- Canonical Master: unchanged (reverified).
- `sfm_init.py`: unchanged (reverified).
- No native Rebuild invoked, no model mutated, no Character Preset code touched.
- Temporary SFM deployment (`gate_c1_deploy/`, the autoinit probe) fully removed after use; no `.pyc` residue left in `usermod/scripts/`.
- One genuine, disclosed defect was found and fixed during embedded qualification (§9/§19's `long`-type guard bug) — reproduced, fixed, reconfirmed on desktop, then redeployed and reconfirmed embedded, per the brief's own STOP-and-fix discipline (this was a qualification-module bug, not a production sidecar defect, so it did not require the brief's "STOP for review before broadening production changes" production-edit path).

## 26. GIT STATE

```
 M tests/sidecar/qualification/bounded_provider.py   (adds evict_reusable_cache(); no change to validation delegation or lookup semantics)
?? tests/sidecar/qualification/session_owner.py                    (new)
?? tests/sidecar/qualification/desktop_session_owner_qualification.py  (new)
```
Plus pre-existing, unrelated untracked files (Flex Bone/Sexual Bones/Phase2/B1-design/Gate2-historical artifacts, the Astra Round 2 evidence bundle) — untouched. `git diff --check`: clean. Nothing staged (`git diff --cached --name-only` empty). No commits made.

---

## 27. POST-REVIEW CORRECTIONS / C1R

### 27.0 Original overclaim

Section 1 above recorded **"C1 PASS — PROCEED TO C2"** as the original
verdict. Post-run code review found this overclaimed PASS on five
specific, narrow points. C1 was placed **ON HOLD** pending repair — this
was never silently corrected in place; the original claims, evidence, and
test output above are preserved unedited as the historical record of what
that first run actually did and actually proved (and, in these five
respects, did not).

### 27.1 Finding 1 — initialization-call count mislabeled as registration count

**Exact defect:** `_record_init()` incremented BOTH `init_count` and
`registration_callback_count` on every call into `get_or_create_owner`,
including calls that reused an already-existing owner. Three call sites
therefore produced `registration_callback_count == 3`, which the original
audit's §7 presented as evidence of "exactly one registration/callback
set" — but a counter that increments on every REUSE, not just on the one
CREATION, cannot actually distinguish "3 attempts, 1 real install" from
"3 real installs." It proved only that 3 init attempts occurred, never
that exactly one registration was installed.

**Exact repair:** split into two genuinely independent facts on
`MasterAuthorityOwner`:
- `init_call_count` — incremented by `_record_init_call()` on every
  `get_or_create_owner`/`simulate_autoinit_call` invocation for this
  namespace, whether it creates a new owner or reuses an existing one.
- `registration_install_count` — set to `1` exactly once, inside
  `__init__`, and never touched again for that owner's lifetime.
- `registration_identity` — a stable string token (`"owner-registration-N"`
  from a monotonic counter) assigned once at construction, providing an
  explicit, comparable identity independent of the owner object's own
  Python identity.

No callback object was invented where none existed — C1's qualification
model does not install a real OS/SFM callback, so `registration_identity`
is explicitly documented as a qualification-only installable-registration
token, not a claim about a real callback mechanism.

**Exact rerun evidence:** desktop (`RESULT: 73 PASS / 0 FAIL`, including
`C1R Repair A: init_call_count == 3`, `registration_install_count == 1`,
`registration_identity stable across all three call sites`); embedded
(`1: init_call_count == 3`, `1: registration_install_count == 1`, both
PASS, real SFM, `ids=1,1,1`).

### 27.2 Finding 2 — `close()` invalidated active leases despite claiming otherwise

**Exact defect:** the original `close()` counted outstanding leases,
then closed the provider and cleared `_views` **regardless**, returning
`"closed-with-outstanding-leases:N"` — the string suggested awareness of
the problem while doing nothing to prevent it. Any consumer holding an
active, unreleased lease would find its view silently gone.

**Exact repair:** `close()` now refuses/defers unconditionally whenever
`active_lease_count() > 0`: state, provider, and `_views` are left
completely untouched, and the method returns the explicit, documented
sentinel `"deferred-active-leases:%d"` — never raising, never partially
cleaning up. Only once every lease has been released does `close()`
proceed to actually close the provider, clear views, and transition to
`CLOSED`. A companion `close_or_raise()` is also provided for callers who
prefer an exception (`OwnerBusy`) over inspecting a sentinel string,
satisfying the brief's "return/raise" either-form wording without forcing
one convention.

**Exact rerun evidence:** desktop, a dedicated section run INDEPENDENTLY
of the release-order tests (`C1R Repair B`), exercising the brief's full
A–L sequence: close refused with both leases active
(`'deferred-active-leases:2'`), owner state unchanged (`READY`), both
leases still authorize, provider remains valid, close refused again with
one lease remaining (`'deferred-active-leases:1'`), remaining lease still
authorizes, close succeeds once empty (`'closed'`), repeated close
idempotent, post-close acquisition refused — 10/10 PASS. Embedded: items
8–11 of the repaired matrix, PASS (`'deferred-active-leases:1'`, lease
remains valid, final close `'closed'`, repeated close idempotent).

### 27.3 Finding 3 — private/commit-headroom guard was not independent

**Exact defect:** `GuardPolicy.evaluate` computed
`projected_headroom = free_vas` for its fourth ("private/commit reserve")
criterion — literally the same value already checked by criterion 1
(`free_vas < min_free_vas_bytes`). With `min_free_vas_bytes = 64 MiB` and
`min_private_headroom_bytes = 32 MiB`, criterion 4 could never fail
without criterion 1 already having failed first — it was not a fourth,
independent dimension at all, and the original C1 audit's Guard D test
(`insufficient_private_headroom`, `free_vas=16 MiB`) never actually
isolated it either, since that snapshot already failed criterion 1.

**Decision: Option 1 — implement a genuine independent criterion.**
`committed_vas` (a real, separately-measured field the guard had ignored
entirely) is now checked against an explicit, evidence-based
address-space ceiling: `sfm.exe`'s own PE header was inspected this
session (`Characteristics = 0x0122`) and confirmed to have
`IMAGE_FILE_LARGE_ADDRESS_AWARE` (`0x0020`) **set** — real, checked
evidence, not an assumed default. A 32-bit LAA process on 64-bit Windows
is not subject to the ordinary 2 GiB non-LAA ceiling; its pointers can
address up to `4 GiB` (`ASSUMED_ADDRESS_SPACE_CEILING_BYTES`), which is
therefore the documented assumed ceiling this criterion measures against.
The new criterion: `ceiling_reserve = ceiling - committed_vas`; refuse if
`ceiling_reserve < min_committed_ceiling_reserve_bytes` (32 MiB,
unchanged provisional value, now finally load-bearing).

**Exact guard criteria now qualified (four, genuinely independent):**
1. `free_vas >= min_free_vas_bytes` (64 MiB);
2. `largest_free_region >= min_largest_free_region_bytes` (32 MiB);
3. `artifact_byte_length <= artifact_budget_bytes` (64 MiB);
4. `(4 GiB - committed_vas) >= min_committed_ceiling_reserve_bytes` (32 MiB).

**Independent-test evidence:** a dedicated Guard D snapshot sets
`free_vas=500 MiB` and `largest_free_region=200 MiB` (both comfortably
ABOVE their own minimums — asserted explicitly as its own check,
`"Guard D setup: free VAS and largest free region are independently above
their own minimums"`, PASS) while setting `committed_vas = 4 GiB - 8 MiB`
— refused SOLELY on the committed-ceiling criterion:
`ResourceRefused('... committed VAS 4286578688 leaves only 8388608 bytes
of reserve against the assumed 4294967296-byte address-space ceiling,
below required minimum 33554432')`. PASS, desktop.

### 27.4 Finding 4 — test reset did not deterministically close prior owners/providers

**Exact defect:** `_reset_registry_for_testing()` was `_OWNER_REGISTRY.clear()`
and nothing else — any owner/provider a prior scenario had admitted
remained fully valid and reachable through any reference still held; only
the registry's own lookup was cleared.

**Exact repair:** `_reset_registry_for_testing()` now, for every owner
still in the registry that is not already `CLOSED`: releases every
still-active lease through the **normal, unmodified** `release_lease()`
API, then calls the **normal, unmodified** `close()` (which, after Finding
2's repair, now succeeds unconditionally once all leases are released —
no test-only bypass of production close semantics was needed or added),
asserts the result was `"closed"`/`"already-closed-noop"`, and only then
clears the registry dict.

**Exact rerun evidence (proof prior providers are actually closed on
reset):** desktop `C1R Repair D` section — create an owner with an
admitted provider and one active lease; capture a direct reference to the
provider BEFORE reset; call reset; then assert, against that captured
reference (not a fresh lookup): `lease.active is False`,
`provider_ref_before_reset.is_valid() is False`,
`owner.state == STATE_CLOSED`, `len(_OWNER_REGISTRY) == 0`; then prove the
next scenario for the same namespace variant string gets a genuinely
different, fresh owner object with `provider is None`. Also proves reset
is harmless against an empty registry and against a registry containing
an already-closed owner. All PASS, desktop. Embedded: item 13 of the
repaired matrix reproduces the same four assertions against a real
admitted provider in real SFM — all PASS.

### 27.5 Finding 5 — embedded Python 2.7 did not rerun both release orders

**Exact defect:** the original embedded probe exercised only the N→P
release order; P→N was asserted as "not independently re-confirmed,"
relying on a code-path-equivalence argument (`release_lease`/
`get_view_via_lease` do not branch on which lease was released first).
The brief requires both orders actually run in real embedded SFM, with no
code-path-equivalence substitution.

**Exact repair:** the repaired embedded probe runs P→N in a genuinely
SEPARATE, freshly-admitted owner (new namespace variant, its own
admission, confirmed `provider_allocation_count == 1` for THAT owner
before the release sequence begins) — not a reuse of the N→P owner, and
not an inference from the first order's result.

**Exact rerun evidence:** embedded, item 7 of the repaired matrix: fresh
owner admits its own provider; release P → `'released'`; N's still-active
lease authorizes; provider survives; P's released lease raises
`LeaseRejected`; second release (N) succeeds; accounting drops to zero.
All PASS, real SFM, distinct from and independent of the N→P run (item 6).

### 27.6 Full rerun summary

- Desktop qualification (`desktop_session_owner_qualification.py`,
  revised): **73 PASS / 0 FAIL**, covering every item in brief §7's
  preserved-claims list plus all five repairs.
- Embedded qualification (new probe, real SFM, Qt-thread,
  `QTimer`-chained, no long sleeps): **31 PASS / 0 FAIL**, covering the
  full 13-item repaired matrix of brief §8, including both release orders
  run as genuinely separate fresh owners.
- Desktop semantic parity (`desktop_parity_and_timing.py`, unrelated to
  the owner but re-run to confirm no incidental regression): **183 PASS /
  0 FAIL**, unchanged.
- Full regression: `python -m pytest tests/sidecar/ -q` → **369 passed,
  265 subtests passed**; `python -m pytest tests/ -q` → **421 passed, 265
  subtests passed**. Validator: PASS. `git diff --check`: clean.
- Master, official sidecar, `reader.py`, `format.py`, external Normalizer,
  `sfm_init.py`: all reverified byte-identical to the C0 checkpoint/prior
  values before and after every real-SFM session in this repair.

### 27.7 Final corrected verdict

**C1R PASS — C1 CLOSED, PROCEED TO C2.**

All eight C1R-PASS criteria are met: (1) 3 init calls → 1 owner + 1 actual
registration installation; (2) active-lease close refused/deferred without
invalidating consumers; (3) guard claims now match four actually,
independently tested criteria; (4) deterministic test reset closes prior
providers, proven against a captured pre-reset reference; (5) both release
orders pass desktop; (6) both release orders pass embedded Python 2.7,
each in a genuinely separate fresh owner; (7) semantic regressions remain
clean (6/6, unchanged from the original run); (8) no production
integration was added or attempted.
