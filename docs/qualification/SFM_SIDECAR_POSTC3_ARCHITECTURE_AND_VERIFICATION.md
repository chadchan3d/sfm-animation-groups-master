# SFM Sidecar — Post-C3 Architecture Map and Direct Source Verification

Collected at HEAD `1028adcde35dd7681cfad7db2bbc7c367c7b2565` "Qualify sidecar source
freshness lifecycle". Evidence-collection only — no implementation code was changed
while producing this document.

This document covers brief sections 2 (architecture map), 3 (Astra Round 3 correction
verification), 4 (Minimum C3 verification), and 5 (Python-2 manifest/pointer seam).
Every claim below was checked directly against current source and/or a fresh test
run in this session — never taken only from prior audit prose.

---

## Section 2 — Current architecture / source map

### Production/runtime code

| Module | Role | Status |
|---|---|---|
| `tools/sfm_master_sidecar/reader.py` | Sole production sidecar reader/validator (`_validate_and_decode`, `SidecarReader`). Python-2/3 compatible by design (this is what would run inside embedded SFM). | Production, unmodified since the C0.3 closure-cycle fix (commit `d12c821c`). |
| `tools/sfm_master_sidecar/format.py` | Binary layout constants, row packers/unpackers, ASCII-fold byte function. Python-2/3 compatible. | Production, unmodified throughout this entire conversation. |
| `tools/sfm_master_sidecar/manifest.py` | Manifest build (`build_manifest_dict`, `serialize_manifest`) and hardened parse (`parse_manifest_bytes`, `resolve_generation_path`). **Python-3-only by its own docstring** — "the embedded runtime reader never reads a manifest." | Production (compiler/publisher-side only), unmodified. Never runs inside embedded SFM today. |
| `tools/sfm_master_sidecar/compiler.py` | `capture_source_snapshot`, `parse_and_compile`, `verify_semantic_parity`, `generation_basename`. Orchestrates parse+compile+self-validate. | Production (offline/build-side), unmodified. |
| `tools/sfm_master_sidecar/writer.py` | `compile_sidecar` — the actual binary serializer. | Production (offline/build-side), unmodified. |
| `tools/sfm_master_sidecar/publisher.py`, `cli.py` | Publication/CLI helpers around the above. | Production (offline/build-side), unmodified; not touched by any gate in this arc. |
| `Rebuild_Control_Groups_Normalizer.py` (external, `usermod/scripts/sfm/mainmenu/ChadChan3D/`) | The real, currently-shipping Normalizer script. Runs inside embedded SFM (Python 2.7, imports `sfmApp`/`sfmClipEditor`/`vs`/PySide). | Production, unmodified. **Contains zero references to sidecar/qualification code** (verified: `grep -i "sidecar\|session_owner\|command_boundary\|bounded_provider\|MasterAuthorityOwner"` over the whole 339,944-byte file returns no matches). See `SFM_SIDECAR_POSTC3_NORMALIZER_KNOWLEDGE_BOUNDARY.md` for what it actually does today. |

### Qualification-only code

All of the following live under `tests/sidecar/qualification/`, carry an explicit
"QUALIFICATION-ONLY... NOT production code... never imported by `tools/sfm_master_sidecar/*.py`... never imported by the production Normalizer" docstring, and are never
referenced from any production file (verified by the same grep above, run against
each production file in turn — zero hits).

| Module | Invariant it implements | Exists in production today? | Intended disposition |
|---|---|---|---|
| `session_owner.py` | One process-wide owner per resolved namespace; lazy admission; pre-admission resource guard; explicit leases (not GC-based); epoch-stamped detached action views; per-request budget accounting; terminal close; **minimum-C3 retirement** (new `RETIRED` state, idempotent `retire()`, no new work after retirement, existing leases stay valid, registry self-cleanup). | No. Nothing resembling an owner/lease/view object exists in the current Normalizer. | Undecided — this is exactly the open question Astra Round 3 raised and this evidence package exists to let Astra re-judge. |
| `command_boundary.py` | Command-boundary source-SHA freshness; candidate/manifest compatibility check; old-generation retirement trigger; **includes its own qualification-only, Python-2/3-compatible manifest reader** (see §5 below) because production `manifest.py` cannot run under embedded Python 2.7. | Partially — see §5: the Normalizer already has its own, different, real SHA-256 stability check (`contextualizer_assert_master_stable_for_index_use`), not this module. | Undecided; explicitly NOT authorized for production per the Minimum C3 audit's carried-forward caveat. |
| `resource_budgets.py` | Provisional qualification budgets (artifact bytes, string-cache bytes, one-family rows, one-snapshot rows, total-pinned-view bytes). | No enforced equivalent found in the current Normalizer beyond its own memory-delta *logging* (`contextualizer_process_memory_sample`) — it measures but does not appear to enforce a budget. | Test-only / undecided values; explicitly documented as provisional, never a frozen SLA. |
| `bounded_provider.py` (S1) | Bounded-materialization sidecar reader: complete immutable byte snapshot, validation delegated entirely to production `reader.py`, on-demand cached decoding of only requested folds. | No — this is the qualification stand-in for what a production consumer's read path *would* look like if it used the sidecar. | Test-only today; its bounded-decode *design* is the thing under evaluation, not a shipped module itself. |
| `bounded_view.py` | Fast, per-fold-bounded Gate A2 contract view builder (`build_view_bounded`, `compat_master_lookup`). | The Normalizer's own `master_lookup`/`parse_targeted_master` already do the equivalent job today, independently, via full/scoped TXT token streaming (§ Normalizer reference doc). | Test-only; a parity target/reference to prove against, not a production replacement yet. |
| `normalizer_source_profile.py` | Refuses non-`groupFile` wrapper / any backslash byte in source (Gate C0.2). | Not verified as an explicit Normalizer-side check in the source read for this package (the Normalizer's own `parse_targeted_master` requires literal `"groupFile"` as the first token — functionally similar, independently implemented, not shared code). | Test-only compatibility-profile gate. |
| `shared_txt_session.py` | The T2 "warm shared TXT" counterfactual object (`SharedTxtSession.acquire`/`invalidate`) used as the fair comparison baseline throughout Gate B/Round 3. | No — purely a qualification counterfactual. | Test-only, used to keep the "is the sidecar actually better than TXT" comparison honest (§10 TXT counterfactual doc). |
| `desktop_session_owner_qualification.py`, `desktop_view_expansion_qualification.py`, `desktop_round3_foundation_qualification.py`, `desktop_minimum_c3_qualification.py`, `desktop_parity_and_timing.py` | Desktop Python 3 qualification harnesses (75/44/40/53/183 PASS respectively, reconfirmed fresh in this session — §6). | N/A (test harnesses). | Test-only, permanently. |
| `round3_embedded_evidence/`, `minimum_c3_embedded_evidence/` | Preserved exact embedded Python 2.7 probe scripts + raw logs/results, committed byte-exact. | N/A (evidence, not code). | Historical evidence, permanently. |
| `official_master_fixture.py` | Shared one-parse/one-compile fixture cache for the real official Master, used by every desktop harness. | N/A (test fixture). | Test-only, permanently. |

### Historical/experimental code

- **Candidate B/C** (file-backed reads, mmap): named only in prior audits as
  explicitly-out-of-scope alternatives to Candidate A (the immutable-byte-snapshot
  backing every qualification module in this arc actually uses). No Candidate B/C
  source code exists anywhere in the current repository — confirmed by `git grep -i
  "candidate b\|candidate c"` returning only audit-prose references, never a module.
  Status: **never built, not merely removed.**
- **Gate B1/B1.1 sidecar design documents** (`SFM_MASTER_SIDECAR_PHASE_B1_DESIGN.md`,
  `SFM_MASTER_SIDECAR_PHASE_B1_1_REVISED_DESIGN.md`, both untracked, present in the
  working tree) and **Gate 2A/2C candidate-comparison audits**
  (`SFM_MASTER_SIDECAR_GATE2A_CANDIDATE_A_EMBEDDED_BASELINE_AUDIT.md`,
  `..._RERUN_AUDIT.md`, `SFM_MASTER_SIDECAR_GATE2C_BACKING_STRATEGY_COMPARISON_AUDIT.md`)
  — superseded design/comparison documents from before Gate B's own final direction
  was set. Kept as historical record only; not included in this package's core
  evidence (available on request, excluded per the brief's "do not include ...
  large historical files that add no review value").
- **The Round 2/Round 3-era reusable positive/negative coverage cache**
  (`_EpochCoverage`, Gate C2) — genuinely deleted from `session_owner.py` by the
  Round 3 foundation repair, not merely deprecated. Confirmed absent: `grep -n
  "_EpochCoverage" tests/sidecar/qualification/session_owner.py` returns only two
  docstring lines explaining its removal, zero class/attribute references.
- **The redundant fourth guard criterion** (`min_committed_ceiling_reserve_bytes`,
  `ASSUMED_ADDRESS_SPACE_CEILING_BYTES`) — also genuinely deleted, same verification
  method, zero live references.

---

## Section 3 — Astra Round 3 required corrections, verified against current source

Checklist taken directly from `SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md`'s
"most consequential findings" (§1) and the Round 3 foundation repair brief's Repair
A-J list. For each item: exact current source location, current behavior, the test
assertion(s) that exercise it, and verdict.

| # | Finding | Current source location | Current behavior | Test assertion(s) | Embedded evidence | Verdict |
|---|---|---|---|---|---|---|
| 1 | Cross-owner lease confusion | `session_owner.py`, `MasterAuthorityOwner.get_view_via_lease` (top: `if lease.owner_id != self.owner_id: raise LeaseRejected`) and `release_lease` (same check) | Foreign-owner lease raises `LeaseRejected` immediately, before touching any state | `desktop_round3_foundation_qualification.py` "Round3 Repair A" section (6 checks) | `round3_embedded_evidence/gate_round3_embedded_result.log`, checks "3:*" (4/4 PASS) | **PASS** |
| 2 | Inactive lease/history accumulation | `session_owner.py`, `MasterAuthorityOwner.release_lease` (`del self._leases[lease.lease_id]`, no tombstone) | A released lease is deleted from `_leases`, not flagged-and-kept; idempotency is checked via the passed `Lease` object's own `.active` flag | `desktop_round3_foundation_qualification.py` "Round3 Repair B" (release-removes-record + no-history-growth checks) | Embedded checks "4:*" (3/3 PASS) | **PASS** |
| 3 | Closed-owner retained registry/state | `session_owner.py`, `MasterAuthorityOwner.close` (`if _OWNER_REGISTRY.get(self.namespace_identity) is self: del _OWNER_REGISTRY[...]`) | Closed owner immediately removed from the process registry; never rediscoverable via `get_or_create_owner` | Same section, "terminal close removes owner from the process registry" + "closed owner never discoverable" checks | Embedded checks "6:*" (3/3 PASS) | **PASS** |
| 4 | Reusable positive/negative cross-action cache | `session_owner.py`, `acquire_view` — entirely rewritten to resolve every fold from private local state on every call; `_EpochCoverage` class deleted | No owner-level cache exists at all (verified structurally absent, not merely emptied) | "Round3 Repair F" section: `hasattr(owner, "_coverage")` is False, `hasattr(so, "_EpochCoverage")` is False, repeated lookup still correct | Embedded: "session_owner has no _EpochCoverage class" (PASS) | **PASS (closed by removal, not by re-bounding)** |
| 5 | Decode-cache bound bypass after refused request | `session_owner.py`, `MasterAuthorityOwner._enforce_decode_cache_bound`, called from a `finally:` wrapping the entire `acquire_view` body | Provider's `string_cache_estimated_bytes()` checked and evicted (`provider.evict_reusable_cache()`) after every attempt — ordinary, refused, or faulted | `desktop_view_expansion_qualification.py` "Round3 Repair G" (4 checks: ordinary, held-view-survives-eviction, refused, injected-failure) | Embedded check "9" (1/1 PASS, using the same 500-occurrence large-family fixture) | **PASS** |
| 6 | Negative-only view zero-byte accounting | `session_owner.py`, `MasterAuthorityOwner._estimate_accounted_bytes` (charges `per_view_fixed_overhead_bytes` + `per_requested_fold_overhead_bytes * len(wanted_folds)` + row bytes) | A negative-only view is charged a nonzero, provisional estimate; mixed views cost more than positive-only | `desktop_view_expansion_qualification.py` "Round3 Repair H" (4 checks) | Embedded checks "8:*" (3/3 PASS, identical byte figures — 320/640/576 — on both runtimes) | **PASS** |
| 7 | Shared mutable row/view payloads | `session_owner.py`, `acquire_view` (`folded[fold_key] = [dict(r) for r in rows]`, a fresh per-view copy at publish time) | Mutating one published view's rows cannot affect another view or the provider's own cache | `desktop_view_expansion_qualification.py` "Round3 Repair I" (2 checks: A/B isolation, C reacquire-after-mutation) | Embedded checks "7:*" (2/2 PASS) | **PASS**; terminology corrected from "immutable payload copy" to "detached stable action view" (`ViewEnvelope` docstring) |
| 8 | Redundant/impossible fourth guard criterion | `session_owner.py`, `GuardPolicy` — the class no longer has `min_committed_ceiling_reserve_bytes`/`assumed_address_space_ceiling_bytes`/`ASSUMED_ADDRESS_SPACE_CEILING_BYTES` at all | Guard evaluates exactly 3 criteria (free VAS, largest free region, artifact bytes) plus snapshot-validity | `desktop_session_owner_qualification.py` "Part 7" (3 physical-consistency regression checks replacing the withdrawn Guard D); `desktop_round3_foundation_qualification.py` confirms the attributes are gone via `hasattr` | Embedded: "GuardPolicy has no committed-ceiling criterion" (PASS) | **PASS (removed, not repaired)** |
| 9 | Simulated registration-install claim | `session_owner.py`, `MasterAuthorityOwner.__init__` — no `registration_install_count`/`registration_identity`/`_REGISTRATION_ID_COUNTER` anywhere; only `init_call_count` remains | Owner tracks call-site attempts only; makes no claim about an installed callback | `desktop_session_owner_qualification.py` C1.1 (updated); `desktop_round3_foundation_qualification.py` "3 init call sites -> 1 owner" section | Embedded check "1" (2/2 PASS) | **PASS (claim withdrawn, not repaired)** |
| 10 | Missing-artifact PREPARING failure | `session_owner.py`, `MasterAuthorityOwner._run_guard` — artifact-metadata lookup now wrapped in its own `try/except`, returning `(False, "artifact metadata unavailable: ...")` instead of letting an `OSError` escape | Owner always reaches `UNAVAILABLE` on a missing/unreadable artifact; never stuck mid-`PREPARING` | `desktop_round3_foundation_qualification.py` "Round3 Repair E" (7 checks, including restore-and-retry) | Not separately re-run embedded for Round 3 (superseded/subsumed by the Minimum C3 embedded probe's own missing-manifest recoverable-failure check, which exercises the same `UNAVAILABLE`-not-`PREPARING` guarantee at the command-boundary layer) | **PASS (desktop); embedded coverage is via the C3 probe, not a Round 3-labeled embedded case** |
| 11 | Overly broad rollback/immutability wording | `session_owner.py`, `acquire_view` docstring (Repair J language): no "byte-identical whole-owner rollback" claim anywhere; publication guarantee narrowed to "no lease/view authorized before all checks succeed; failed candidate publishes nothing; existing views remain valid; provider decode cache may change within its bound" | Docstring-level correction, verified by direct read of the current file (grep for "byte-identical" returns zero matches in `session_owner.py`) | N/A (a wording/claim-scope correction, not independently a runtime behavior with its own test) | N/A | **PASS (wording corrected)** |
| 12 | Architecture simplification requirement | Whole-file diff: `session_owner.py` grew by +242/-17 in the original C2/C2R checkpoint, then **shrank** by the Round 3 foundation repair (removing `_EpochCoverage`, the registration token, and the fourth guard criterion) while adding only the minimum retirement/lease-ownership/accounting/detachment fixes | Net effect: a genuinely smaller retained-state surface than pre-Round-3, not a larger one | Full regression (75+44+40 = 159 desktop PASS across the three historical/updated harnesses, 0 FAIL) confirms no silent regrowth | N/A | **PASS** — confirmed subtractive, not merely relabeled |

**No source/test contradiction was found for any of the 12 items above.** Every
current source location cited was re-opened and re-read in this session (not
recalled from memory of the earlier repair work), and every regression count was
freshly re-run (§6).

---

## Section 4 — Minimum C3, verified against current source

| Claim | Current source | Verified how | Verdict |
|---|---|---|---|
| Source identity uses actual TXT SHA-256 | `command_boundary.hash_source_file` — `hashlib.sha256(open(path,"rb").read())` | Direct read of the function body; `desktop_minimum_c3_qualification.py` C3.2 proves SHA changes while size/mtime are pinned identical | **Confirmed** |
| Same-size/preserved-mtime edit is detected | Same test, `os.utime()` pins mtime explicitly | C3.2 (8 checks) | **Confirmed** |
| Retirement is idempotent | `session_owner.py`, `MasterAuthorityOwner.retire` (`"retired"` then `"already-retired-noop"`) | C3.3 (2 checks) | **Confirmed** |
| No new work after retirement | `acquire_view`, top-of-function `STATE_RETIRED` check | C3.4, C3.5 | **Confirmed** |
| Stale authorization is rejected | Same check; `get_view_via_lease` unaffected by RETIRED (only CLOSED blocks it) | C3.4 (payload remains inspectable while new work is refused) | **Confirmed, and the distinction between the two is directly tested, not assumed** |
| Active leases can drain | `release_lease`/`close`, unchanged from Round 3 | C3.5 (11 checks); embedded "7"/"8" | **Confirmed** |
| Retired owner/provider closes after drain | `close()`'s existing unconditional `self.state = STATE_CLOSED` (never gated on the transition table) | C3.5 | **Confirmed** — verified this works from RETIRED specifically, not just READY |
| Registry does not offer retired/closed authority for new work | `retire()` and `close()` both call `del _OWNER_REGISTRY[...]` | C3.5, C3.6 | **Confirmed** |
| G2 admission occurs only later, explicitly | `command_boundary.prepare_command_boundary` returns a new owner object with `provider is None`; admission happens only at the first `acquire_view` call, deliberately placed in a later test phase | C3.6 (8 checks); embedded "9" | **Confirmed** |
| No G1/G2 provider overlap in the qualified path | Test sequencing: G2's `prepare_command_boundary` call is placed only after G1's `close()` returns `"closed"` | C3.6; embedded phases 3→4 ordering | **Confirmed as a property of the qualified sequence — not something the code itself forbids independently of that sequencing** (see the honest caveat already in the C3 audit §21: real overlap-prevention would need to be a property of a future production caller, not a runtime lock in this qualification code) |
| Unchanged pointer/manifest rewrite does not cause false invalidation | `prepare_command_boundary`'s registry-key equality check (`NamespaceIdentity` equality on `source_sha256`, unaffected by re-serializing the same manifest) | C3.7 (1 check) | **Confirmed** |
| Stale/missing/corrupt/incompatible candidate failures are recoverable | `command_boundary.resolve_candidate` (stale/missing/incompatible) + `session_owner._ensure_admitted`'s existing try/except (corrupt) | C3.8-C3.13 (12 checks total) | **Confirmed** |
| No owner is left PREPARING | Same as above — every failure path returns `UNAVAILABLE` or constructs no owner at all | C3.11, C3.13 explicitly assert `owner.state == STATE_UNAVAILABLE` | **Confirmed** |
| No mixed-generation publication | `acquire_view`'s two `self.state in (STATE_RETIRED, STATE_CLOSED)` checks (mid-resolution and pre-publication) | C3.14 (2 checks); the mechanism is the SAME atomicity check Round 3 already proved for epoch changes, extended to retirement | **Confirmed** |
| Sidecar-unavailable remains distinct from MasterUnknown | No code path anywhere converts `ResourceRefused`/`LeaseRejected` into a `MasterUnknown`-shaped result; verified by reading every `except` clause in `command_boundary.py` and the touched parts of `session_owner.py` | No test can "prove a negative" exhaustively; this is a structural/code-reading verification, consistent across every gate in this arc | **Confirmed by code inspection**; no counter-evidence found |
| No watcher/poller/hot replacement exists | Whole-repo grep for `QFileSystemWatcher`, `watchdog`, `threading.Timer`, `while True.*sleep` scoped to `tests/sidecar/qualification/` returns no matches outside the already-known qualification-only `QTimer.singleShot` embedded-probe scheduling (which fires once per phase, not on a timer loop) | Direct grep in this session | **Confirmed absent** |

**No source/test contradiction was found for any Minimum C3 claim.**

---

## Section 5 — The Python-2 manifest/pointer seam

### Why production `manifest.py` is Python-3-only

`tools/sfm_master_sidecar/manifest.py`'s own module docstring states: "Python 3 only
(compiler/publisher-side; the embedded runtime reader never reads a manifest --
resolving which generation is active is a host-application/Normalizer concern,
entirely outside `reader.py`'s job)." This is a genuine, verified runtime
incompatibility, not merely an unexercised code path: `parse_manifest_bytes`'s
`isinstance(obj[key], str)` type checks (`_REQUIRED_KEYS = {"generation_basename":
str, "sidecar_sha256": str, "source_sha256": str, ...}`) reject the `unicode`
objects Python 2.7's own `json` module produces for JSON string values. This was
confirmed empirically during the Minimum C3 embedded probe's **first run**, which
raised a real `ManifestError("manifest key 'source_sha256' has wrong type (expected
str)")` the first time `command_boundary.py` tried to call the production parser
from inside embedded SFM (see the Minimum C3 audit §17, and the fix that followed).

### What `command_boundary.py` does instead

`command_boundary._parse_manifest_bytes_compat` — a small, explicitly-narrow,
hand-written reader:
- reads exactly 5 fields: `source_sha256`, `sidecar_sha256`, `generation_basename`
  (string-typed, checked via `isinstance(value, (str, unicode))` under Python 2 /
  `(str,)` under Python 3), and `format_contract_version`,
  `authority_semantics_version` (integer-typed);
- does **not** replicate the production validator's additional hardening: no
  duplicate-JSON-key detection, no exact 64-hex-char SHA-256 regex check, no
  safe-basename check (no path-separator/`..`/drive-prefix rejection), no
  `MAX_MANIFEST_BYTES` size cap;
- reuses `sidecar_manifest.resolve_generation_path` **unmodified** (verified
  syntax-safe on both runtimes — no Python-3-only construct in that one function —
  and it duck-types on `.generation_basename`, so the qualification-only manifest
  object satisfies it without inheritance);
- never calls `sidecar_manifest.parse_manifest_bytes`, `build_manifest_dict`, or
  `serialize_manifest` — those remain exclusively used by the desktop qualification
  harness's own fixture-building helper (`build_generation` in
  `desktop_minimum_c3_qualification.py`), which runs under Python 3 only, matching
  how a real generation would actually be built today (offline, by the existing
  compiler/publisher tooling).

### Does its semantics match the production/offline manifest contract?

**Partially, and only for the fields it reads.** It does not verify manifest
authenticity/corruption as thoroughly as `manifest.py` does (see the missing
hardening above). A manifest that would be rejected by the production parser for,
say, a duplicate JSON key or a malformed-but-syntactically-valid SHA string would
currently be silently ACCEPTED by the qualification-only reader if the 5 fields it
checks happen to look right. This is a real, currently-open compatibility gap — not
a bug in the sense of causing wrong behavior in any test run so far, but a genuine
reduction in hardening versus the production contract.

### Is generation-path resolution reused or duplicated?

**Reused, not duplicated.** `resolve_generation_path` is called directly from the
unmodified production module.

### What has and has not been qualified in embedded SFM Python 2.7

**Qualified embedded:** hashing the live Master TXT (`hash_source_file`, plain
`hashlib.sha256`); reading a well-formed manifest via the compatible reader; source
-SHA-staleness detection driving retirement; a missing-manifest-file recoverable
failure.

**NOT qualified embedded:** a genuinely malformed-JSON-syntax manifest (only
exercised on desktop, per the Minimum C3 audit §20 — the embedded probe's one
failure scenario used a missing file to stay compact); the full production
hardening checks (duplicate keys, SHA regex, safe-basename) at all, on either
runtime, since the qualification-only reader never performs them.

### Does any current production runtime code already perform an equivalent job?

**Yes — and it is a different, independently-written mechanism.** The current
`Rebuild_Control_Groups_Normalizer.py` already contains its own real, in-production,
Python-2.7 SHA-256 freshness check:

```text
self.master_hash = sha256_stream(self.master_path)              # computed once, near startup
...
def contextualizer_assert_master_stable_for_index_use(self, phase):
    current_hash = sha256_stream(self.master_path)
    if current_hash.lower() != self.master_hash.lower():
        raise ProbeError("Live Master changed before scoped-index %s use." % phase)
```

(exact line numbers: `self.master_hash = sha256_stream(...)` at line 9225;
`contextualizer_assert_master_stable_for_index_use` defined at line 9402;
`sha256_stream` itself defined at line 1149 — a streaming hash, not a whole-file
`open().read()` like `command_boundary.hash_source_file`, but semantically
equivalent: an exact byte-content SHA-256.)

This is a **materially different design** from what Minimum C3 qualified: the
Normalizer's existing behavior is to **hard-fail the current command outright**
(`raise ProbeError`) if the source changed since the command started — it does not
retire an old authority object and lazily readmit a new one; there is no persistent
owner object to retire in the first place, because `self.master_index` is rebuilt
fresh, once, per command invocation, and discarded when the command ends.

### What still needs an explicit design decision before real Normalizer integration

- Whether a persistent, cross-command owner (as `session_owner.py` qualifies) is
  wanted at all, given the Normalizer today deliberately does NOT persist its Master
  index across commands — it rebuilds from scratch every time and hard-fails on a
  mid-command change, a strictly simpler model than retire/drain/close/lazy-readmit.
- If a persistent owner is wanted, how `command_boundary.py`'s manifest reader
  should be hardened (or replaced by reusing the production validator via some
  Python-3-side helper process, or reimplemented with a full compatible parser) to
  close the gap documented above.
- How the existing `contextualizer_assert_master_stable_for_index_use` /
  `sha256_stream` mechanism and any future sidecar-based freshness check would
  coexist — using both would be pure duplication; replacing the existing one
  requires its own review since it is already shipping production behavior.

### Flagged semantic duplication risk

**Confirmed, concretely:** the Normalizer's `sha256_stream` + `self.master_hash` +
`contextualizer_assert_master_stable_for_index_use` triad already solves "has the
live Master changed since I last looked at it" in production today.
`command_boundary.hash_source_file` solves the same narrow problem a second,
independent way in the qualification layer. Any future integration must pick ONE of
these, not run both — this is exactly the kind of "qualification code drifting
toward its own production shape without reconciling against what production
already does" risk Astra was asked to judge.
