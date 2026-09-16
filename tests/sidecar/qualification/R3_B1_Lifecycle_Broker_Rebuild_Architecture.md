# R3-B1 — Lifecycle / Shared Broker / Rebuild Architecture

Date: 2026-09-15. Design only. No SFM launch. No R1D modification. No
modification of the final R3-A2B candidate, Character Preset Manager,
Normalizer production code, or the Master. No broker/rebuild
implementation. No formal R3 qualification begun.

## 1. Governing inputs — identities re-verified this task

| Artifact | SHA-256 |
|---|---|
| R1D validator (`.../gate_r2_formal_deploy/candidate_packed_validator.py`) | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` |
| R1D provider (`.../gate_r2_formal_deploy/candidate_packed_provider.py`) | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| **Final R3-A2B validator** (`tests/sidecar/qualification/candidate_packed_validator_r3a2b.py`) | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| **Final R3-A2B provider** (`tests/sidecar/qualification/candidate_packed_provider_r3a2b.py`) | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| R3-A2B decision report | `ff669be33fa10e71fdb5a996fe88c85fe1c9d4adf87d1ce6f247e50d044bb471` |
| R3-A1 final contract (`R3_A1_Authority_Binding_Contract_FINAL_PREPROBE.md`) | `e2a3b0b6ea1ad99200202fb181db861309ce40c47578f82d0d9f974bbaf9f12e` |

R1D re-confirmed byte-identical to its Section-1 value at the start of
this task (never touched by R3-A2/R3-A2B). All designs below build on the
**final R3-A2B FINAL candidate**, not R1D — R1D remains the frozen
historical control only.

**Astra guidance actually available** (re-checked, not assumed): the only
completed Astra review with real architectural verdicts,
`docs/qualification/SFM_SIDECAR_ASTRA_ROUND3_HOLISTIC_AUDIT_2026-09-13.md`,
reviews an **earlier, now-superseded owner/lease sidecar architecture**
(predates R1D). Its provider-lifetime principles ("conditional retention
reasonable; always retire old bindings; permit release under pressure or
explicit action; do not force close/reopen on every switch"; lazy
admission at an explicit authority-requiring command; no eager
preload/scan) transfer directly and are used below. Its verdict that TXT
fallback is "essential product architecture" **conflicts** with the
current locked-in no-silent-fallback policy — flagged, not silently
resolved, in §21. `SFM_CGN_Astra_R3_Sidecar_Audit_Packet_2026-09-15.zip`
is our own prepared handoff packet for Astra's *next* review, not a
completed review — it contains a draft sketch that overlaps with several
sections below; no Astra response exists yet for the current R1D-based
design.

## 2. R3-B1 goal

One shared, generation-safe, bounded authority system for both Control
Group Normalizer and Character Preset Manager:

```
effective editable Master
  -> matching validated immutable SIDECAR generation
  -> shared process-local authority broker
  -> finite acquisition
  -> detached consumer-specific views
  -> fresh mutation/use authorization
```

Master TXT remains authored source of truth. SIDECAR remains required
normal runtime producer. No silent TXT fallback.

## 3. Effective Master resolver

**One process-local resolver**, shared by both consumers post-migration
(§17/§18). Current state (re-verified): Normalizer's `derive_paths`
(ifm.dll-derived install + hardcoded `usermod/cfg` join) and Character
Preset's `filesystem.valve.mod()` + cfg join are two *independent*
implementations that happen to agree in the tested installation.

**Resolution algorithm:**
1. Obtain signal A: ifm.dll-derived installation root (module introspection).
2. Obtain signal B: `filesystem.valve.mod()`-derived mod root.
3. Join each with the fixed relative path `cfg/sfm_defaultanimationgroups.txt`.
4. Canonicalize both resulting paths (resolve symlinks/junctions,
   case-normalize per Windows/NTFS case-insensitivity, normalize
   separators).
5. If both signals are available and canonicalize to the **same** path:
   use it (highest confidence).
6. If both signals are available and canonicalize to **different**
   paths: **`AmbiguousMasterPath`** — fail closed, never guess.
7. If only one signal is obtainable in a given embedding context: use it
   alone, but tag the resolution as reduced-confidence in diagnostics
   (never surfaced as an error by itself).
8. If neither signal is obtainable, or a signal's own derivation is not
   unique (e.g. ifm.dll introspection returns more than one candidate
   module): `AmbiguousMasterPath`.

**Multi-install behavior**: the resolver only ever resolves the
*currently running* process's install (via the actually-loaded `ifm.dll`
module path) — it never enumerates or chooses among installs on disk.
Different SFM installations naturally get different resolver results when
run independently (see §15 item 8).

**Path canonicalization rules**: `os.path.realpath` (or equivalent) +
lower-case comparison (NTFS default) + normalized separators, applied
before every equality/mismatch decision in this document.

**`AmbiguousMasterPath`** = the two independent signals canonicalize to
different paths, or a signal's own derivation is non-unique/unavailable
when it was expected to be available.

Do not maintain two consumer-specific resolver implementations after
broker integration — both migration seams (§17/§18) replace their own
ad-hoc resolution with a call into this one function.

## 4. Generation descriptor

Immutable, shared by both consumers.

| Field | Classification |
|---|---|
| `effective_master_path` | diagnostic-only |
| `master_sha256` | **authority-defining** |
| `master_byte_length` | diagnostic-only (fast pre-check; SHA is the real authority) |
| `sidecar_artifact_sha256` | diagnostic-only (identifies *which* byte-build; two conforming builds of the same Master can legitimately differ — R3-A1 finding) |
| `sidecar_source_sha256` | **authority-defining** (must equal `master_sha256`, or the generation is invalid) |
| `format_contract_version` | **compatibility-defining** |
| `authority_semantics_version` | **compatibility-defining** |
| `projection_contract_version` | **compatibility-defining** |
| `producer` | diagnostic-only (which compiler/build produced the artifact) |
| `admission_id` / `transaction_id` | diagnostic-only (per-acquisition correlation id, not per-generation) |
| bounded-view coverage identity | diagnostic-only; properly belongs to the per-view coverage descriptor (§8), included here only as an optional passthrough annotation |

No runtime model/rig/selection/pose state anywhere in this descriptor.

## 5. Sidecar selection hierarchy

1. Resolve effective Master (§3).
2. Compute **H0** = exact-byte SHA-256 of the Master (full read, never
   mtime/size).
3. Inspect local pointer (`current_pointer.json`, §14). If unreadable/
   malformed: `LocalPointerCorrupt` — treat as "no usable local pointer"
   and fall through to step 5 (a corrupt pointer conveys no false
   information about artifact content, only a missing shortcut — safe to
   bypass).
4. If pointer readable and its `master_sha256` == H0: attempt to open the
   referenced local artifact
   (`<generated_root>/<namespace>/<artifact_sha256>.sfmsidecar`) via the
   FINAL R3-A2B bounded-read + complete validation gate. Verify the
   artifact's own embedded `source_sha256`/`source_byte_length` == H0
   (**pointer metadata never overrides sidecar header truth** — the
   pointer is only a hint pointing at a candidate file).
   - If this succeeds: **use it**, done.
   - If the artifact fails validation (`SidecarCorrupt`): do **not**
     silently treat this as equivalent to a missing pointer. See the
     explicit decision below.
5. Inspect the shipped sidecar location (§14). Same validation gate,
   verify embedded `source_sha256` == H0.
   - If this succeeds: use it (this is not a "fallback to TXT" — it is
     the same producer type, SIDECAR, just a different valid source).
6. If nothing validates: explicit `RebuildRequired` (a local generation
   could plausibly be built for this Master) or `SidecarMissing` (no
   local pointer/artifact at all yet) per §11's taxonomy. **Never**
   silently parse TXT.

**Decision — corrupt local pointer/artifact fall-through** (explicitly
required by the prompt to be justified): a corrupt local **pointer**
(step 3) falls through silently to shipped — it carries no false claim
about content, only a missing shortcut. A corrupt local **artifact**
(step 4, validation itself fails) is treated differently: it is **first
surfaced** as `SidecarCorrupt` in diagnostics/logs (so a broken local
rebuild is never invisible — the user should eventually re-run Rebuild),
and **only then**, in the same selection pass, may the resolver attempt
the shipped sidecar as an explicitly-logged secondary candidate (never
silent about *which* generation source ended up serving the request).
This satisfies "must not silently switch producer type" (shipped SIDECAR
is the same producer type as local SIDECAR, not TXT) while never hiding
that the local generation is broken. This specific judgment call is
flagged again in §21 as one Astra should specifically stress-test.

**Per-candidate validation gate** (every artifact, local or shipped):
bounded read (FINAL R3-A2B `_read_path_bounded`/`_validate_runtime_cap_bytes`)
→ format/semantics compatibility (§4 compatibility-defining fields) →
full digest/integrity → complete Section 20 A-J structural validation
(FINAL R3-A2B `validate_packed`) → embedded `source_sha256`/
`source_byte_length` == H0.

## 6. H0/H1 publication lifecycle

```
H0 (current-source observation)
  -> select one candidate artifact (§5)
  -> complete validation
  -> build requested detached view(s) (§8)
  -> H1 (fresh current-source observation)
  -> require H0 == H1 == artifact's own embedded source generation
  -> publish descriptor + view(s)
  -> close provider when the acquiring cohort is complete (§7)
```

No qualified protected no-write interval exists today (R3-A1); external
file changes do not require a Qt yield; therefore **H1 is mandatory
before every publication, unconditionally**.

- **Failure if H0 != H1**: `AuthorityChangedDuringAcquisition`. Nothing
  is published; any partially-built detached views are discarded (never
  partially published); the provider/backing opened for this attempt is
  closed.
- **Retry**: exactly **one bounded automatic retry** (a fresh H0 is taken
  and the whole cycle re-run once). If the second attempt also disagrees,
  **stop** and surface `AuthorityChangedDuringAcquisition` to the caller/
  event layer — it decides whether to retry again on a user/event-driven
  basis. This avoids both spurious single-edit failures and a silent
  infinite-retry loop.
- **State retained/released on failure**: nothing — each attempt starts
  from a fresh H0; no descriptor/generation state survives a failed
  cycle.

## 7. Provider/acquisition lifetime

Astra's rejection of an "indefinitely retained full provider" (on the
now-superseded owner/lease architecture) generalizes: retention must be
justified and bounded, never open-ended "just in case." G18AD's *actual*
current behavior is already dialog/session-scoped, not indefinite or
process-lifetime — this must not regress when routed through the broker.

**Acquisition cohort** = a short-lived, explicitly-scoped grant of
provider access spanning one coherent operation window:
- **Normalizer**: one *command*-level cohort (e.g. one "Selected"/"All"/
  "Resume" invocation), spanning however many individual target
  transactions that one command touches. Acquired at command start,
  closed at command completion (success or failure).
- **Character Preset**: one *dialog-session*-level cohort — matches its
  current actual lazy-acquire-on-first-query / release-on-dialog-close
  behavior exactly.

**Sharing**: the broker's provider is keyed by generation
(`master_sha256` + `sidecar_artifact_sha256`) and reference-counted.
Concurrent cohorts against the **same** generation share one underlying
provider/backing (refcount++ on acquire, refcount-- on close); backing is
torn down only at refcount zero. Cohorts against *different* generations
each get their own backing — no forced serialization at the read layer
(only the rebuild utility's final commit needs serialization, §13).

- **One command needing multiple target scopes**: all covered within one
  command-level cohort; no per-target reacquisition.
- **Character Preset repeated semantic queries**: all covered within one
  dialog-session cohort; new queries reuse the still-open provider.
- **Both consumers near the same time**: independent cohorts, refcount-
  shared backing if same generation — see decision below.
- **Later-uncovered scope after prior detached views exist**: the still-
  open cohort issues a new bounded query against its still-open provider
  and publishes an *additional* small detached view tagged with the same
  generation (views stay immutable once published; never mutated in
  place).
- **Provider close**: at refcount zero. Already-published detached views
  remain valid and usable afterward — they are self-contained, immutable
  snapshots with no live reference into the closed provider's buffer.
- **Aggregate retained-memory budget**: sum of (a) currently-open
  provider backings, each ≤ the runtime admission cap (§16), times the
  number of concurrently-open *distinct* generations (expected 1, rarely
  2 during a generation transition), plus (b) all currently-retained
  detached views (bounded by consumer-side eviction, §8). Recommend: at
  most 2 concurrently-open distinct generations; a 3rd is refused with
  `AuthorityBusy` (expected to be effectively unreachable at human
  operation timescales).

**Decision — can one cohort span both consumers?** No. Normalizer's
command-scoped cohort and Character Preset's dialog-scoped cohort are
**never lifetime-coupled** — one consumer's command completing must never
force-close the other's still-open dialog. They may share one underlying
provider (refcount) purely as a resource optimization when generations
match; their cohort *lifetimes* remain fully independent.

**Do not keep backing alive for hypothetical future consumers**: enforced
automatically by refcount-to-zero-closes — no keep-alive/grace-period
caching layer in first R3.

## 8. Detached view contract

- **Normalizer view**: complete hierarchy/metadata fidelity (bounded by
  `group_count`/`metadata_row_count`, exactly how the FINAL R3-A2B
  provider's `_ensure_groups`/`_ensure_metadata` already work) + the
  specific requested exact/fold lookups + an explicit coverage
  descriptor.
- **Character Preset view**: only the semantic vocabulary/projection it
  actually queries — a bounded subset of fold lookups, never full
  hierarchy/metadata (matches its existing targeted `lookup_fold` usage).
- Both: plain immutable data (already-decoded strings + structural
  facts). **Never** a handle into the provider's packed backing bytes;
  **never** expose provider internals (`_buf`, `_string_cache`, etc.).
- **View immutability**: a published view's content never changes. New
  queries produce new view objects.
- **Generation tag**: every view carries the authority-defining +
  compatibility-defining fields of its generation descriptor (§4), so a
  caller can check freshness without re-querying the broker.
- **Coverage descriptor**: the exact set of fold-keys/queries resolved
  into this view, each tagged Hit / FoldConflict / MasterUnknown.
- **`MasterUnknown`**: a query was actually executed and the authority
  affirmatively has no matching fold — a real, trustworthy negative.
- **Uncovered/not-requested**: the consumer never asked about that key in
  this view — absent from the coverage descriptor entirely. **Never**
  conflated with `MasterUnknown` (a distinct sentinel/exception on lookup
  of a not-requested key).
- **Authority unavailable**: a third, separate state — occurs *before*
  any view exists (the cohort's acquisition attempt itself failed, §11);
  not a property of a view at all.
- **Cache key**: `(master_sha256, sidecar_source_sha256==master_sha256
  check passed, format/semantics/projection versions, exact requested
  fold-key set or "full hierarchy")` — so two views of the same
  generation with different query shapes never collide.
- **Cache invalidation**: a view becomes stale the instant its generation
  no longer matches the currently-resolvable generation (§9). Never
  mutated/silently revalidated in place. A stale view may still finish
  whatever target is already mid-flight (§10) but must never authorize a
  *new* target without fresh (re-)acquisition.

## 9. Freshness / SHA-check map

Re-read directly from the current production Normalizer (line numbers
confirmed current, not assumed from memory):

| # | Call site | Guards |
|---|---|---|
| 1 | `assert_master_stable()` @ line 10952, inside `run_target_transaction` | pre-mutation guard for this target |
| 2 | `assert_master_stable()` @ line 11752, same `run_target_transaction` | post-mutation/terminal-commit guard for the same target |
| 3 | `assert_master_stable()` @ line 11921, inside `contextualizer_resolve_resume_target` | Resume-target resolution |
| 4 | `contextualizer_assert_master_stable_for_index_use()` @ line 9431, inside `contextualizer_validate_master_index_subset` | scoped-index use, per gate/target phase (many calls per run — T93 alone logs 20) |
| 5 | `contextualizer_assert_master_stable_for_index_use()` @ line 13184, inside `start()` | initial scoped-index build |

**Classification**: all 5 are **required distinct boundaries**. None are
provably guarding the same unchanged observation window — real
mutation/build work with no proven Qt-yield-free guarantee occurs between
every pair (matches R3-A1's "no qualified protected no-write interval
exists" finding, confirmed again at the source level this task). **None
consolidatable today; all 5 must remain until a future protected/
uninterrupted-interval mechanism is separately designed and qualified.**

**Relationship to the broker's H0/H1 cycle**: these checks are NOT
replaced by broker acquisition. The broker's H0/H1 governs "is my SIDECAR
generation still valid" at *read/acquisition* time; these 5 checks govern
"is the Master file I'm about to *write* still what I last saw" at
*mutation* time. Different concerns, both required, may eventually share
a low-level "compute master_sha256" helper (code-level dedup only, never
a shared value/token across genuinely different observation windows).

**Cost — corrected from R3-A1's "unknown" framing**: real current-
generation telemetry exists (5 independent real logs, all dated
2026-09-07, all matching the pinned R2 Master SHA
`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`
exactly — T93 additionally logs `mapping_count=128555`, an exact match to
the real official artifact's `occurrence_count`, independently confirming
current-generation validity): **35 checks, 0.606 s aggregate, ≈17.3
ms/check**. The older T80 log (2026-09-05, different/older 40-group
Master generation) showed ≈14.6 ms/check — same order of magnitude,
consistent with the current generation's modestly larger shape. **Report
this separately from the ≈0.990 s FINAL R3-A2B sidecar admission cost**
(§1) — a ~17 ms Master re-hash and a ~990 ms full packed-sidecar
validation are different operations of different magnitude; never
conflate them.

Do not use mtime/size as a cryptographic substitute anywhere in this
design (already true in production: `assert_master_stable` does a full
`sha256_stream` re-hash).

## 10. Mixed-generation rules

**Principle: no operation silently switches authority generation midway
through a target/transaction.**

- **Master changes during acquisition** → H0≠H1 → `AuthorityChangedDuring
  Acquisition` (§6); nothing published.
- **Master changes after view publication** → the published view remains
  valid to *finish* whatever operation is already in flight (immutable,
  generation-tagged snapshot); no *new* target/operation may start
  against it — fresh acquisition required first.
- **Master changes between Normalizer targets** (within one command/
  cohort): each target's own pre-check (§9 #1) independently detects
  this and that target must stop; already-completed prior targets in the
  same command are not retroactively invalidated. Surface
  `AuthorityChangedDuringOperation` for the remaining targets; report
  completed vs. stopped explicitly.
- **Sidecar rebuilt/repointed during an active operation**: the open
  cohort keeps its already-acquired provider/views to finish its current
  work; it never hot-swaps mid-operation. The *next* cohort naturally
  picks up the new pointer.
- **One consumer has an old detached view while another acquires a new
  generation**: fully expected and fine — independent cohorts (§7); no
  cross-consumer blocking, bounded by the ≤2-distinct-generation budget.
- **Callback arrives using a stale cached view**: must re-check the
  view's generation tag against the currently-resolvable generation
  (cheap comparison, not full re-acquisition) before using it for
  anything beyond read-only/diagnostic purposes; using it to authorize a
  *new* mutation follows the "between targets" rule above.
- **Same source Master, byte-different valid sidecar artifact**: per §4,
  `sidecar_artifact_sha256` is diagnostic-only — `master_sha256`/
  `sidecar_source_sha256` identity is what defines "same authority."
  Byte-different-artifact-same-source **is** semantically compatible for
  continuation; not treated as a generation change.
- **Receipts/completion state tagging**: every mutation-transaction
  receipt embeds the generation descriptor's authority-defining fields
  (`master_sha256` at minimum) it operated under, so audit/Undo tooling
  can always identify which authority-generation produced which result
  and detect a mid-batch generation change across a receipt set.

## 11. Error taxonomy + UX

| Category | Meaning | Remediation |
|---|---|---|
| `MasterAbsent` | resolved path doesn't exist | select/restore a valid Master |
| `MasterUnreadable` | exists, can't be opened (permissions/lock) | check permissions/other-process lock |
| `AmbiguousMasterPath` | independent resolver signals disagree/non-unique | manual confirmation, never guessed |
| `MasterInvalid` | Master exists/reads but fails minimal TXT structural sanity | Master is corrupted/not a valid file |
| `SidecarMissing` | no local or shipped sidecar matches current Master | explicit Rebuild |
| `SourceGenerationMismatch` | sidecar found, `source_sha256` != current H0 | Rebuild (Master edited since last build) |
| `SidecarCorrupt` | sidecar matches source generation but fails structural/integrity validation | Rebuild (this artifact is damaged) |
| `FormatUnsupported` | `format_contract_version` unsupported by this reader | update tool / rebuild with compatible version |
| `AuthoritySemanticsUnsupported` | `authority_semantics_version` unsupported | same class as above |
| `ResourceAdmissionRefusal` | sidecar exceeds runtime admission cap (§16) | large/custom Master not yet supported; wait for cap qualification |
| `AuthorityChangedDuringAcquisition` | H0≠H1 during broker acquisition | transient; bounded auto-retry, then "try again" |
| `AuthorityChangedDuringOperation` | Master changed after authority already granted, mid-operation | operation stopped partway; re-run remaining targets |
| `AuthorityBusy` | publisher mutex held elsewhere, or resource budget exceeded | try again shortly |
| `LocalPointerCorrupt` | local pointer JSON malformed/unreadable | usually silently absorbed (§5); logged; may surface as SidecarMissing if it leaves nothing usable |
| `LocalGenerationMissing` | no local pointer/artifact exists yet | Rebuild, or falls through to shipped |
| `RebuildRequired` | terminal state whenever no valid sidecar can be produced automatically | always paired with one explicit Rebuild action |

`MasterUnknown` is kept **separate** from this taxonomy entirely — it is
a normal, valid, negative lookup result (§8), never an error.

**No repeated modal spam**: live/automatic/background checks never pop a
modal — they log and set a passive/status indicator only. Only an
explicit user-initiated command may surface a modal, and even then:
- one meaningful surfaced failure, not one popup per sub-check;
- full detail goes to the log;
- bounded automatic retry (§6) happens silently before anything surfaces;
- the modal, when shown, always offers the single most relevant explicit
  action (typically Rebuild).

## 12. Rebuild utility architecture

Standalone tool, same authoritative compiler pipeline as official builds.
Transaction (elaborating the prompt's own 15 steps with concrete meaning):

1. Resolve/select the input Master explicitly (same resolver, §3, or an
   explicit user-chosen path for non-default scenarios).
2. Read one stable source snapshot (bounded, full read).
3. Compile to a unique temporary immutable artifact (content-addressed
   filename derived from the artifact's own future SHA — written to a
   temp name, renamed to its final SHA-named path only after step 5-7
   pass).
4. Flush/close the temp file handle.
5. Production-validate the completed artifact with the **FINAL R3-A2B**
   validator/provider contract at its exact exported SHA (§1) — bounded
   read, full Section 20 A-J structural validation.
6. Verify embedded `source_sha256`/`source_byte_length` match the read
   snapshot, and `format_contract_version`/`authority_semantics_version`
   are supported.
7. Compiler source-core parity check: confirm the compiler used the same
   normative row-size/format tables (`fmt.NORMATIVE_ROW_SIZES` etc.) as
   the reader — i.e. the writer and reader agree on format identity, not
   just that the bytes happen to validate.
8. Acquire publisher serialization (named mutex, §13) for this Master
   slot.
9. Re-resolve/re-hash the live Master — **H1**.
10. If H1 != the source generation this artifact was compiled from: do
    **not** publish; release the mutex; report the mismatch (the Master
    changed again during compilation/validation — a fresh rebuild attempt
    is needed, not a forced publish of a now-stale artifact).
11. Publish the immutable artifact (move/rename into
    `<generated_root>/<namespace>/<artifact_sha256>.sfmsidecar`) if not
    already present (content-addressed — a second rebuild producing
    byte-identical output is a harmless no-op here).
12. Atomically replace the selection pointer (`current_pointer.json`,
    write-temp + rename; back up the prior pointer to `.bak` first).
13. Re-read/verify the just-committed pointer from disk independently.
14. Release the mutex.
15. Report source/artifact/compiler identities (Master SHA, artifact SHA,
    compiler/producer identity) to the caller/log.

**Failure leaves prior valid selection recoverable**: pointer replacement
is the last write (step 12), gated by full validation (5-7) and a final
H1 recheck (9-10) before it happens. Any failure before step 12 leaves
the existing `current_pointer.json` completely untouched. A partially
written candidate artifact, if any, is either never referenced by any
pointer (harmless orphan; no first-R3 GC, §14) or explicitly deleted
before releasing the mutex on a detected failure.

## 13. Publisher serialization

Atomic pointer replacement is not writer serialization by itself — two
concurrent rebuilds could each individually complete an atomic rename and
still race each other's *ordering*.

**Chosen mechanism**: a named Windows mutex,
`Local\SFM_CGN_R3_PublisherLock_<installation-root-hash>` (per-install
namespace, avoiding cross-install serialization on a machine with
multiple SFM installs).

- Compilation (steps 1-7) may run fully concurrently across processes —
  each writes to its own uniquely artifact-SHA-named temp file;
  collisions require byte-identical content and are harmless.
- Only the final commit (steps 8-14: H1 recheck through pointer release)
  is serialized behind the mutex.
- **Crash recovery**: automatic — the OS releases a named mutex when its
  owning process dies, with no orphaning and no PID-liveness/staleness-
  timeout logic required.
- **Stale ownership**: not applicable given automatic OS release; a
  bounded acquire-timeout still applies (`AuthorityBusy` if not acquired
  within it, §11).
- **Permissions**: standard user session-kernel object; no elevated
  rights required.
- **Runtime/location clarification** (resolves R3-A1's previously-open
  "unverified in embedded Python 2.7" concern): per this prompt's own
  text, the rebuild utility runs **outside SFM** as Python 3 / a packaged
  executable — `ctypes`/`win32event`-equivalent named-mutex primitives
  are unambiguously available there. The earlier concern was specific to
  SFM's *embedded* Python 2.7, which never needs to take this lock at
  all (see next point) — so it is moot for the writer, though listed
  again in §21 as one item worth a final explicit confirmation before
  B2E.
- **Runtime readers never need this lock**: ordinary sidecar
  acquisition/selection (§5) reads an already-published, already-atomic
  pointer+artifact pair — lock-free.

## 14. Local generated storage layout

- **Generated root** (shared, content-addressed, install-independent —
  identical artifact bytes are valid regardless of which install produced
  them): `%LOCALAPPDATA%\SFM_ControlGroupNormalizer\generated\
  <format_namespace>\<artifact_sha256>.sfmsidecar`.
- **Selection pointer** (per-install, since "current generation" is
  install-specific): `%LOCALAPPDATA%\SFM_ControlGroupNormalizer\pointers\
  <installation-root-hash>\current_pointer.json` (+ `.bak`), containing:
  `master_sha256`, `master_byte_length`, `artifact_sha256`,
  `artifact_relative_path`, `format_contract_version`,
  `authority_semantics_version`, optional compiler diagnostics.
- **Shipped-artifact location**: inside the package's own install tree
  (e.g. a `shipped_sidecars/` folder under `usermod/...`), read-only,
  package/Workshop-managed, updated only by package updates.
- **Local-vs-shipped precedence**: local (if valid and matching current
  H0) always preferred over shipped — local reflects the user's actual
  current (possibly edited) Master; shipped only matches the official
  unmodified Master.
- **Pointer backup/recovery**: `.bak` written before every pointer
  replacement (§12 step 12); on primary-pointer read failure, attempt
  `.bak`; if both fail, `LocalPointerCorrupt` (§5/§11).
- **Stale pointer handling**: a pointer whose `master_sha256` no longer
  matches current H0 is simply not selected (falls through naturally,
  §5 step 4) — never auto-deleted (preserves forensic/recovery value); a
  later maintenance feature may prune it.
- **No-GC first-R3 rule**: generated artifacts accumulate; no automatic
  deletion; deferred to a later explicit maintenance feature (R3-A1).
- **Do not silently merge user Master edits with package updates**: an
  edited local Master's generation store/pointer is never reconciled
  against a package update; the update only changes what's available as
  a *new* official-Master option, never overwrites/merges into the user's
  local Master or local generation store.

## 15. Workshop/update behavior

1. **Official Master + matching shipped sidecar update**: no forced
   action either way — governed purely by H0 matching (§5); an unedited
   user naturally re-resolves to the new shipped generation once their H0
   (recomputed from the now-current official Master, if it changed too)
   matches its embedded `source_sha256`.
2. **User has no custom Master**: relies entirely on shipped sidecar once
   the resolver confirms Master == official content; no local rebuild
   ever needed.
3. **User has edited Master**: shipped sidecar's `source_sha256` correctly
   excludes it (doesn't match H0, §5); local generation is used if one
   exists for the edited content, else `RebuildRequired`.
4. **Local rebuilt sidecar exists**: used per precedence (§14) whenever
   it matches H0.
5. **Workshop/package update lands while SFM is running**: any already-
   open cohort is untouched (detached/immutable, §7/§10); the *next*
   acquisition picks up whatever is now on disk; a mid-write file is
   caught cleanly by the validation gate (§5), never partially trusted.
6. **Master and shipped sidecar update non-atomically**: the transient
   mismatch window is handled exactly like case 5 — if Master updates
   before its matching sidecar, H0 simply won't match the still-old
   shipped `source_sha256` → correctly falls through to
   `RebuildRequired`/`Unavailable` until the sidecar update also lands (or
   a local rebuild happens) — never a mixed-authority state.
7. **Local pointer references an older source**: excluded naturally by
   the H0-match check (§5 step 4), same as any other mismatch.
8. **Multiple SFM installations**: each install has its own pointer
   namespace (§14) but shares the content-addressed generated_root — an
   artifact built for install A's Master is transparently reusable by
   install B if B's Master hashes identically (the common case); no
   cross-install coupling or shared "current" assumption.

Do not assume Workshop-managed directories are safe local-output targets:
`generated_root`/pointer storage are explicitly outside any Workshop/
package-managed tree (§14), since such directories can be silently
overwritten/re-validated by Steam Workshop's own integrity mechanisms.

## 16. Runtime admission-cap gate

The FINAL R3-A2B candidate includes bounded reading with an explicit
EXPERIMENTAL 16 MiB default (hardened against malformed overrides, §1 of
the R3-A2B decision report) — but the production runtime admission
*maximum* is not yet qualified.

- The broker's selection gate (§5) enforces the current best-known cap
  uniformly for both shipped and local artifacts — no special-casing.
- **Broker/rebuild implementation may proceed before full cap
  qualification**: the official ~9.5 MB artifact is already safely within
  any plausible cap and already qualified end-to-end (R2/R3-A2B).
- **Arbitrary local custom Master-derived generations remain gated/not
  production-promoted** until the cap qualification (2-3 synthetic
  enlarged artifacts at differing row-density shapes, real Python 2.7.5
  32-bit SFM, external memory sampler, validation-only vs. representative
  query/view phases distinguished, existing transient ≤32 MiB / retained
  ≤16 MiB gates retained unless governance changes them) actually passes.
  The bounded-read admission cap itself is already a correct, functioning
  safety backstop even pre-qualification — an oversized custom artifact
  is cleanly refused (`ResourceAdmissionRefusal`) rather than risking
  resource exhaustion, so shipping the broker/rebuild architecture for
  the common (official + modest custom) case is safe today.
- **Do not invent a final cap in B1** — not done; 16 MiB stays explicitly
  EXPERIMENTAL.

## 17. Character Preset migration seam

Current confirmed state (line numbers re-verified this task):
`SEMANTIC_PROVIDER_FORCE_MODE` (line 1128, hardcoded SIDECAR),
`_SEMANTIC_PROVIDER` module-global singleton (1849),
`SidecarSemanticProvider` (2298, `resident_packed_backing_policy:
one-handle-per-adapter-lifetime` at 2386), `acquire_semantic_provider_
for_mode` (3301), `get_semantic_provider()` (3339),
`invalidate_semantic_provider()` (3391). Acquisition is lazy (first
semantic query in a dialog session); release happens at dialog close
(`invalidate_semantic_provider()`) — i.e. genuinely session/dialog-scoped
already, not indefinite.

**Migration**:
- Remove `_SEMANTIC_PROVIDER` module-global + `get_semantic_provider()`/
  `invalidate_semantic_provider()` — replaced by a broker cohort acquired
  lazily at first semantic query (matches current timing and Astra's
  lazy-admission guidance) and closed at dialog close (matches current
  release timing exactly).
- Remove the dormant AUTO → `MasterTxtSemanticProvider` branch inside
  `acquire_semantic_provider_for_mode` entirely (dead code deletion — it
  is physically present but permanently unreachable since
  `SEMANTIC_PROVIDER_FORCE_MODE` never evaluates to AUTO).
- `SidecarSemanticProvider`'s internals are replaced with calls into the
  broker's detached-view contract (§8) instead of holding its own packed
  backing; newly-needed vocabulary extends its cohort's queries (§7)
  rather than growing a private cache.
- **Preserve**: exact current semantic lookup behavior (Hit/FoldConflict/
  MasterUnknown outcomes, fold-key matching) must be byte-identical — this
  migration changes *who owns the provider/backing lifecycle*, not
  lookup semantics.
- **Do not assume Normalizer qualification (B2C) automatically qualifies
  Character Preset (B2D)** — separate tests needed:
  1. dialog-open → first-query → dialog-close cohort-lifecycle test (no
     leaked provider/backing across repeated open/close cycles);
  2. semantic-lookup-output parity test (old singleton-based provider vs.
     new broker-routed one, same real artifact, same queries → identical
     results);
  3. concurrent-with-Normalizer test (dialog open while Normalizer runs a
     command against the same generation → both succeed, refcounted
     sharing works, neither force-closes the other early);
  4. dormant-AUTO-branch-removed regression test (no code path can ever
     reach TXT).

## 18. Normalizer migration seam

Current production Normalizer does its own ad-hoc Master TXT parsing/
lookup (`master_lookup` line 1767, `parse_targeted_master` line 1416) —
it does not consume a sidecar today at all (the sidecar work has been
qualification-only, never deployed). The B2C migration is therefore
"replace ad-hoc TXT parsing with broker-provided views," not "replace an
existing sidecar consumer."

- **Path resolution**: `derive_paths` → shared resolver call (§3).
- **Authority acquisition**: `master_lookup`/`parse_targeted_master`'s
  role is replaced by acquiring a command-level cohort (§7) and consuming
  its Normalizer detached view (§8) instead of re-parsing TXT per lookup.
- **Contextualizer index building**: `contextualizer_validate_master_
  index_subset`/`start()`'s scoped-index build becomes a consumer of the
  broker's Normalizer view instead of building its own structure from raw
  TXT.
- **Per-target freshness checks**: all 5 sites identified in §9 are
  **kept unchanged** in count and position — they guard mutation/write
  safety on the Master file, a concern the broker's read-side H0/H1 cycle
  does not replace.
- **Provider/view ownership**: the Normalizer holds broker-issued
  detached views scoped to its command-level cohort, not ad-hoc parsed
  structures.
- **Shutdown/error cleanup**: `cohort.close()` on command completion,
  failure, or exception (try/finally or equivalent) — routed through the
  broker's cohort API in place of whatever ad hoc cleanup exists today.
- **Preserve exactly**: current user-facing behavior, day-to-day early
  normalization semantics, target transaction/Undo behavior, existing
  preemption behavior, all current canonical presentation rules. This
  migration is authority-plumbing only. **Do not mix UI redesign into
  R3.**

## 19. Minimal state machine

```
IDLE
  -> RESOLVE (shared resolver, §3)
       --fail--> [MasterAbsent / MasterUnreadable / AmbiguousMasterPath] -> IDLE
  -> H0_OBSERVED
  -> SELECT_ARTIFACT (selection hierarchy, §5)
       --fail--> [SidecarMissing / SourceGenerationMismatch / SidecarCorrupt /
                   FormatUnsupported / AuthoritySemanticsUnsupported /
                   ResourceAdmissionRefusal / RebuildRequired] -> IDLE
  -> VALIDATE (bounded read + full structural validation, FINAL R3-A2B contract)
       --fail--> [SidecarCorrupt] -> back to SELECT_ARTIFACT (try next candidate)
                                      or IDLE if hierarchy exhausted
  -> BUILD_VIEWS (detached views per consumer contract, §8)
  -> H1_VERIFY (fresh current-source observation)
       --fail--> [AuthorityChangedDuringAcquisition] -> bounded 1x retry -> RESOLVE
                                                          or IDLE if retry exhausted
  -> READY_DETACHED (views published, cohort holds authority)
  -> AUTHORIZE_USE (consumer-internal freshness re-check per §9 boundaries)
  -> TARGET_TRANSACTION (0..N targets/queries; independently freshness-guarded;
                          concurrent consumers admitted via refcounted sharing, §7)
       --generation change detected--> [AuthorityChangedDuringOperation] -> SAFE_STOP
  -> COMPLETE / SAFE_STOP  (never leaves partial/inconsistent authority state)
  -> RELEASE (cohort.close(), refcount--)
  -> bounded detached-cache state (already-published views may still be held/
     used read-only by the consumer until discarded or re-acquired)
  -> IDLE
```

- **Concurrent consumer admission**: modeled as multiple independent
  state-machine instances (one per cohort), optionally sharing underlying
  provider backing (refcount) without sharing transitions.
- **Generation invalidation**: any transition from READY_DETACHED /
  AUTHORIZE_USE / TARGET_TRANSACTION triggered by a detected Master
  change goes to SAFE_STOP — never silently continues.
- **Rebuild visibility**: a successful external rebuild is not pushed to
  any already-READY_DETACHED cohort; visible only on the next fresh
  RESOLVE→SELECT_ARTIFACT cycle (no live invalidation-push in first R3 —
  matches Astra's C4 no-seamless-handoff simplicity guidance).
- **Retry**: bounded, only from the H1_VERIFY failure transition (§6).
- **Shutdown**: abrupt SFM exit / dialog close → RELEASE from whatever
  state is current, best-effort, no assumption of a graceful IDLE-first
  transition (the reader side holds no cross-process locks at all, unlike
  the writer's mutex, so this is inherently simple).

## 20. Implementation decomposition

Confirms the prompt's own suggested ordering — already bottom-up
(shared infra proven in isolation → each consumer migrated independently
→ external tooling → measurement-only cap work) — no safer alternative
ordering is evidenced.

**B2A — shared resolver + generation descriptor + sidecar selection, no
consumer migration**
- Files: one new module implementing §3/§4/§5/§6. No Normalizer/CSP
  changes.
- Behavioral surface: none (net-new, unused).
- Tests: resolver cross-check/`AmbiguousMasterPath`; descriptor-field
  classification; selection-hierarchy matrix (local/shipped/corrupt/
  missing, using real artifact + `corruption_helpers.py`); H0/H1
  mismatch-and-retry.
- Rollback: delete the unused module; zero production impact.
- Frozen: R1D, final R3-A2B candidate (consumed, not modified),
  Normalizer, Character Preset.

**B2B — broker acquisition + detached-view lifecycle**
- Files: extend B2A's module with §7/§8. Still no consumer wiring.
- Behavioral surface: none.
- Tests: cohort refcount (concurrent, same/different generation);
  detached-view coverage/cache-key/invalidation; aggregate memory-budget
  assertions (reusing the R3-A2B real peak-memory measurement technique).
- Rollback: trivial, as B2A.
- Frozen: as B2A.

**B2C — Normalizer migration**
- Files: `Rebuild_Control_Groups_Normalizer.py` (§18 seams). First
  production file touched.
- Behavioral surface: internal only if done correctly (all current
  user-facing behavior preserved) — highest-risk checkpoint.
- Tests: full existing Normalizer regression suite + broker-integration
  tests + a regression test asserting exactly 5 freshness-check call
  sites remain (§9).
- Rollback: revert this checkpoint's commit(s).
- Frozen: Character Preset; R1D/R3-A2B (consumed only).

**B2D — Character Preset migration**
- Files: `SFM_CSP_G18AD_EmbeddedIconFix.py` (§17 seams).
- Behavioral surface: internal only if done correctly; dormant AUTO
  branch physically removed.
- Tests: the 4 tests listed in §17.
- Rollback: revert.
- Frozen: Normalizer (already migrated); R1D/R3-A2B.

**B2E — rebuild utility + pointer publication**
- Files: new standalone utility (Python 3/packaged exe), outside the
  SFM-embedded codebase entirely.
- Behavioral surface: net-new — Rebuild becomes a real, actionable UX
  path (§11).
- Tests: full 15-step transaction test (§12) offline against real +
  synthetic Masters; mutex-serialization test (concurrent rebuild
  attempts); failure-leaves-prior-selection-recoverable test.
- Rollback: the utility is a separate executable; not shipping it leaves
  the broker in a safe "RebuildRequired, no self-service remediation
  yet" state.
- Frozen: everything else.

**B2F — custom-sidecar runtime-cap qualification**
- Files: none in the broker (pure measurement, §16).
- Behavioral surface: none immediately; large custom Masters remain gated
  until this passes.
- Tests: the 2-3-synthetic-artifact real-sampler design already specified
  in the R3-A2B report's Section 4 future-qualification design.
- Rollback: N/A.
- Frozen: everything.

## 21. Unresolved questions

1. **TXT-fallback tension**: an earlier completed Astra review (ROUND3
   HOLISTIC AUDIT, on the now-superseded owner/lease architecture) called
   TXT fallback "essential product architecture," while the current
   locked-in policy (R3-A1, G18AD's actual hardcoded behavior) is
   no-silent-fallback. This document follows the current/newer policy
   throughout, but the conflict is real and should be explicitly
   re-confirmed with Astra, not assumed resolved by recency alone.
2. Whether an explicit, opt-in "use TXT for this session" escape hatch
   should exist at all (raised as open in our own draft
   `05_MASTER_SIDECAR_REBUILD_PRODUCT_ARCHITECTURE.md`). This document's
   default is no; it is a product decision, not purely technical.
3. **Corrupt-local-artifact fall-through** (§5): the logged/non-silent
   fallback-to-shipped design is my own reasoned judgment call, not a
   pre-existing decision — the prompt explicitly required this to be
   justified rather than assumed; flagging it specifically for adversarial
   stress-testing.
4. `win32event`/`ctypes`-based named-mutex availability in whatever
   Python 3 packaging the rebuild utility ultimately uses — very likely
   fine, not literally verified this task.
5. Exact `generated_root`/pointer path convention
   (`%LOCALAPPDATA%\SFM_ControlGroupNormalizer\...`) is a reasonable
   default, not checked against any existing tool/path convention already
   used elsewhere in this codebase — needs a quick confirmation pass
   before B2A.
6. Bounded-retry counts (1 automatic H0/H1 retry; a mutex-wait timeout for
   `AuthorityBusy`) are placeholder reasonable defaults, not evidence-
   derived — should be tunable configuration, not hardcoded assumptions.
7. Whether the Normalizer's proposed "command-level cohort" granularity
   (spanning a multi-target Selected/All/Resume invocation) is actually
   achievable given the current call-graph shape — inferred from the
   existing per-target function structure, not confirmed by tracing the
   actual multi-target command caller; should be confirmed in B2C's own
   preflight, not assumed here.
8. The ≤2-concurrent-distinct-generations memory budget (§7) is a
   first-cut policy, not derived from a measured ceiling — revisit once
   B2B's memory-budget tests produce real numbers.

## Astra-review recommendation

**Review B1 before implementation.** Per §21, several materially open
authority/lifetime/publication questions remain (the TXT-fallback policy
tension being the most significant), matching the prompt's own stated
default preference for this exact situation.

## 22. Architecture artifact

This document. Exported (§ below) alongside the R3-A2B artifacts at:
`E:\SFM Animation Group Master\tests\sidecar\qualification\
R3_B1_Lifecycle_Broker_Rebuild_Architecture.md`

---

Per the hard stop: no SFM launch, no R1D modification, no modification of
the final R3-A2B candidate, no Character Preset Manager modification, no
Normalizer production-code modification, no Master modification, no
broker/rebuild implementation, no formal R3 qualification begun. Design
only. Stopping here.
