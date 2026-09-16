# R3-B1 — Lifecycle / Shared Broker / Rebuild Architecture (ASTRA CORRECTED)

Date: 2026-09-15. Design only. Fully supersedes
`R3_B1_Lifecycle_Broker_Rebuild_Architecture.md`
(SHA `4a00136034ee486989f115c6a7b3a066ceff7c9d1834b2446d3d9d6bfa08d389`).
No SFM launch. No R1D modification. No modification of the final R3-A2B
candidate, Character Preset Manager, Normalizer production code, or the
Master. No broker/rebuild implementation. No formal R3 qualification
begun. B2A is NOT authorized by this document.

## 0. Governing identities (re-verified this task)

| Artifact | SHA-256 |
|---|---|
| R1D validator | `2dc3fe2268fdd12ef0a3002199635a8d24322bc422c50a637a21e1f664b65802` |
| R1D provider | `74790fa285fad1b1369bf7bad9794f8125961dd553234c0294a55d7bc570f38c` |
| Final R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| Final R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` |
| Prior (superseded) R3-B1 doc | `4a00136034ee486989f115c6a7b3a066ceff7c9d1834b2446d3d9d6bfa08d389` |

All unchanged since prior R3-B1. Line numbers for every Normalizer call
site cited below were re-read directly from
`Rebuild_Control_Groups_Normalizer.py` this task (not carried over from
the prior document) — one was found off by one (§7).

## 1. TXT-fallback: locked contract, no conflict

The prior document's framing of a live "tension" between an earlier Astra
review and the current no-silent-fallback policy is deleted. There is no
conflict to track. Locked first-R3 product contract:

- Master TXT is the authored source of truth.
- SIDECAR is the required normal runtime producer.
- Missing/stale/corrupt/incompatible SIDECAR → explicit unavailable/
  rebuild/update handling (§10, §11).
- No silent TXT parsing.
- No automatic producer switch to TXT.
- An optional, explicit, manual "TXT slow mode" is out of scope for first
  R3 — not designed here, not precluded later, not a live question.

This decision is not reopened anywhere below.

## 2. Canonical broker module ownership

**One shared, Python-2-compatible installed package**: `sfm_master_authority`
(a real package on SFM's Python path — e.g.
`usermod/scripts/sfm/sfm_master_authority/`, with `__init__.py`,
`runtime.py`, etc.). Never `execfile`'d. Never vendored per-consumer.
Never copy-pasted into caller namespaces.

**Ownership**: only `sfm_master_authority.runtime` owns the broker
factory and all runtime state (the singleton broker instance, its
`INITIALIZING`/`READY`/`FAILED` status). Every entry point — Normalizer
menu init, Character Preset menu init, any Autoinit-triggered path — uses
the exact same absolute import:
`import sfm_master_authority.runtime as authority_runtime`. Never a
relative import, never a differently-aliased import path (a different
import spelling would resolve to a *different* `sys.modules` entry —
Python's own module cache is what provides "one module object," and only
holds as long as every importer spells the path identically).

**Reserve canonical `sys.modules['sfm_master_authority.runtime']`**: at
module import time, before constructing any broker/provider side effect,
`runtime.py` verifies `__name__ == 'sfm_master_authority.runtime'`. If
not (e.g. someone `execfile`'d it, or it was imported under a stray
alias), it refuses to proceed — raises immediately, before any
side-effecting factory work runs. Detect/reject happens *before*
construction, never after.

**Validate expected module origin and compatible API/build identity**: on
first real broker construction, verify `runtime.__file__` resolves to the
expected installed package location (defends against a stale/duplicate
copy earlier on `sys.path`), and check an explicit
`RUNTIME_API_VERSION` constant the module exports against what the
calling consumer was built against. A mismatch fails clearly
(`IncompatibleAuthorityRuntime`), never silently proceeds with mismatched
expectations. A second, incompatible package on `sys.path` fails this
same check — it must never silently instantiate a second, independent
broker.

**Initialization**: on SFM's main Python/Qt thread only. Explicit
tri-state status (`INITIALIZING` / `READY` / `FAILED`) recorded in the
canonical module's own state, not in any caller's local variable, so
every caller observing status sees the same truth.

**Reentry** (there is no true OS-thread concurrency here — SFM is
single-threaded on the main Python/Qt thread; "reentry" means a nested/
recursive call into the factory, e.g. a side effect during construction
calling back into "ensure broker exists"): the factory sets status to
`INITIALIZING` *before* any side-effecting work. A reentrant call arriving
while already `INITIALIZING` refuses/raises rather than recursively
re-entering construction — reentry must never observe, or produce, a
half-constructed broker.

**Long-lived callbacks** (Qt slot connections, deferred/idle callbacks,
native SFM event hooks) must be plain functions at module scope in the
canonical module, or bound methods of the canonical singleton broker
object itself — never closures over mutable Autoinit-local globals, which
can be reset/reloaded independently of the canonical module and leave a
callback referencing orphaned state.

**No hot-reload of the live module**: never
`del sys.modules['sfm_master_authority.runtime']` followed by re-import
while a broker is active — this silently forks identity (old callbacks
keep referencing the old module's state; new importers get a fresh
singleton), exactly the split-brain condition this whole design exists to
prevent. A genuine code upgrade requires either a controlled teardown
(drain all cohorts to zero, tear the broker down to clean uninitialized
state, then reload — not designed in B1) or a full tool/SFM restart.

**Minimal B2A runtime identity test**:
1. Launch both consumers in both orders (Normalizer-first, CSP-first),
   repeated.
2. Both direct-menu startup and Autoinit-triggered startup.
3. One interpreter process (explicitly confirm no subprocess/second-
   interpreter spawn).
4. `sfm_master_authority.runtime` is the same module object (`id()`
   equality) across every entry point.
5. The broker object itself is the same object (`id()` equality) across
   every entry point/order/repeat.
6. Zero eager provider opens (construction/import must be side-effect-
   free with respect to any actual sidecar I/O).
7. Zero duplicate callback registrations.
8. Alias/incompatible-duplicate/reentry attempts either fail clearly or
   transparently reuse the canonical owner — never construct a second
   independent broker.

If different Python interpreters are ever observed, **stop**; do not
claim a process-wide singleton — the `sys.modules`-based mechanism is
void across separate interpreters, and this design does not address that
case.

## 3. Effective Master resolver

**Qualified primary resolver** (unchanged from real production — reused
verbatim, re-read and confirmed this task at
`Rebuild_Control_Groups_Normalizer.py:9151`): `derive_paths()` —
ifm.dll module introspection (`get_loaded_ifm_module()` /
`get_loaded_module_path()`) → derive `tools_dir`/`bin_dir`/`game_dir` via
successive `os.path.dirname()` → validate directory-name expectations via
`os.path.normcase()` on **basenames only** (never full-path identity) →
join `game_dir/usermod/cfg/sfm_defaultanimationgroups.txt`. Confirmed:
this algorithm does **not** use `os.path.realpath()` anywhere — the
realpath+lowercasing "proof" in the prior document was never production
reality, it was an unsound claim in the design itself, now removed.

**Corroborating second signal, when available**: Character Preset's
`filesystem.valve.mod()`-derived path, joined the same way.

**Explicit single-signal case**: when only the ifm.dll-derived signal is
obtainable, proceed on it alone — this is the normal case in most
contexts today, not a degraded fallback; single-signal resolution is what
production already trusts.

**Handle-based final path/file identity comparison** (corrects the prior
document's unsound reliance on `realpath()` + lowercasing as Windows file
identity proof): when both signals are available and yield different
path *strings*, do not conclude "different files" from the strings alone
— Windows junctions, hardlinks, and 8.3 short names can make different
path strings name the same file. For existing files on both candidate
paths, compare genuine Windows file identity via
`GetFileInformationByHandle` (volume serial number + file index) — this
is what actually proves "same file," independent of path string form.

**`AmbiguousMasterPath`**: the two signals canonicalize to different
path strings *and* the handle-based comparison also finds them to be
different files (or one/both paths can't be opened for the comparison).
Fail closed. No unchecked manual override — any future manual-override
capability would be a separate, explicit, governance-approved feature,
never a silent escape hatch in this design.

**Separate confinement rule for intended output paths** (a distinct
problem from resolving an *existing* Master file, since there is no file
handle to compare identity against for a path that doesn't exist yet):
governs the generated-artifact storage layout (§14) — reject `..`,
absolute/drive-relative/UNC paths, and ADS suffixes via pure string/
component validation *before* any filesystem operation, then confirm the
final resolved location via the same handle-based identity technique
against the `generated_root` anchor (§14).

## 4. Provider/acquisition lifetime — at most one open backing

**First-R3 invariant: at most one open packed backing/provider, at a
time, process-wide.** This replaces the prior document's dialog-duration
ownership, command-duration-through-target-execution ownership, "at most
two open backings," and concurrent-different-generation providers —
all removed.

**Finite acquisition cohort** (redefined): one declared request set / a
bounded immediate request sequence; one semantic generation; one
provider; one explicit end. A cohort ends the moment its requested
projections are detached (views built and published) and H1 succeeds, or
on any failure. A cohort **never** waits for a future button press,
expression change, body operation, callback, target execution, or idle
dialog event.

**Normalizer**:
1. Collect command vocabulary — every fold-key/control-name the whole
   command will need across all its targets, computed upfront from the
   command's own already-known scope (no sidecar access needed for this
   step).
2. Acquire a cohort; build the command-scoped detached view covering the
   entire collected vocabulary.
3. Close the provider immediately.
4. Only then execute target transactions, against the already-detached
   view — no provider is open during mutation.
5. If genuinely uncovered scope appears later (a target needs a fold-key
   nobody predicted), do **not** silently reopen/expand the already-
   detached view mid-mutation. Either use existing fail-closed semantics
   (that target fails cleanly as "not covered by prepared authority") or
   initiate a separately-authorized new acquisition boundary (a distinct
   new cohort) — never an ad-hoc silent expansion during live mutation.

**Character Preset**:
1. Acquire only when an operation needs vocabulary not already covered by
   a still-valid, previously-detached view.
2. Build a bounded detached view for exactly that need.
3. Close the provider immediately.
4. Execute using the detached view.
5. Dialog lifetime itself grants no packed-backing lease — merely having
   the dialog open is never sufficient justification to hold a provider
   open; every acquisition ties to an actual operation's actual need and
   closes the moment that need is satisfied, regardless of how much
   longer the dialog stays open.

**Two consumers**: either they participate in one explicitly finite
*preparation* cohort together (when both already-known needs coincide in
time against the same generation, served by one open-then-close cycle),
or — the default/common case — they serialize separate acquisitions (one
consumer's cohort fully completes, including its provider close, before
the other's begins). Never retain backing waiting for a hypothetical
future cross-consumer reuse.

## 5. Aggregate memory ownership/budget

Refcounts are not a budget — the prior document's refcounted-provider
framing is removed. **One shared aggregate authority budget** tracks
(conservatively; never `sys.getsizeof()`-based, which badly undercounts
real CPython object overhead — use real measured techniques, the R3-A2B
`GetProcessMemoryInfo` peak-working-set technique or the provider's own
structural `resource_snapshot()`-style counting):

- retained Normalizer detached views
- retained Character Preset detached views
- stale/invalidated views still referenced by some consumer
- pending projections (views mid-construction, not yet published)
- one incoming sidecar snapshot (matches §4's at-most-one-provider
  invariant)
- validation scratch (the FINAL R3-A2B validator's `array.array`
  columns/`bytearray` coverage scratch, transient but present during
  validation)
- provider caches (`_string_cache`/`_groups`/`_metadata_rows`, bounded,
  already introspectable via the provider's own `resource_snapshot()`)
- temporary copies (intermediate read/validate buffers)
- replacement overlap (the brief window during a rebuild-triggered
  pointer switch where old-generation *views* may still be referenced
  while a new generation's provider is prepared — an allowed overlap of
  *retained view bytes*, never of *open providers*, which §4 forbids)

**Keep** the existing R2-qualified retained ≤16 MiB / transient ≤32 MiB
envelopes as **aggregate authority configuration gates for promotion**
across the whole process — not per-consumer allowances (never "16 MiB
each").

**Do not invent final production byte reservations from
`sys.getsizeof()`.**

First-R3 policy: account conservatively; evict unpinned reusable views
first; release stale views when their owners can (never forcibly reclaim
a live reference); if actively-pinned data prevents safe admission of a
new acquisition, defer/refuse (`AuthorityBusy`) rather than force an
over-budget admission; invalidating a view revokes mutation authorization
but does not free its bytes (ordinary refcounting/GC still governs actual
release, per §6); one provider at a time (so the "provider cache" budget
line is trivially singular, never summed across concurrent providers).

**B2B must empirically qualify actual aggregate memory behavior** — the
design specifies the accounting model; the real numbers come from B2B's
own measured tests, not from this document.

## 6. Four separated identities

1. **Semantic generation** — exact Master content SHA (`master_sha256`)
   + compatible authority/projection semantics (format/authority-
   semantics/projection versions all within the supported range). This
   is the true "same authority" question.
2. **Artifact validation identity** — artifact SHA
   (`sidecar_artifact_sha256`) + format/integrity identity of that
   specific byte-build. Answers "which exact file did I validate";
   explicitly **not** semantic-generation-defining (§9).
3. **View coverage** — the exact bounded vocabulary/projection actually
   represented in a published detached view (§8's coverage descriptor).
   Answers "what does this view actually contain," independent of
   whether the underlying generation is still current.
4. **Live authorization** — fresh, current-moment permission to use a
   given view for mutation *right now* (§7's freshness map). The only
   one of the four that can go stale from one instant to the next while
   the other three remain unchanged.

Effective source binding (#1) and view coverage (#3) are **not merely
diagnostic** — both are load-bearing facts a correct implementation
actively checks at defined points (§7 for #1/#4, §8 for #3), never facts
that exist only for logging. A view's payload (#3) may remain readable
for logs/diagnosis after its live authorization (#4) is revoked — the two
axes are independent; revoking #4 never destroys #3.

## 7. Corrected SHA/freshness boundary map

Not "exactly five checks" as a compatibility requirement, and not a
single H0/H1 pair replacing everything. Astra's semantic-boundary map,
with line numbers re-read directly this task (one correction from the
prior document, noted below):

**a. Initial command source identity** — `derive_paths()`
(`Rebuild_Control_Groups_Normalizer.py:9151`), which computes
`self.master_hash = sha256_stream(self.master_path)` at lines 9225-9229.
Establishes command source identity *before* scope inventory. Retain as
an explicit, distinctly-named/-logged "command identity observation" —
never silently buried inside resolver path-discovery internals. Moving
it later requires separate proof, not assumed here.

**b. BUILD boundary** — `contextualizer_assert_master_stable_for_index_use("BUILD")`
at line 13184, immediately preceding `parse_targeted_master()` at line
13195, both inside `start()` (defined line 12994). In the broker-
integrated design: **replace** this legacy BUILD hash-check with the
broker's own H0 at this exact semantic boundary. Do **not** run the
legacy BUILD hash *and* a duplicate broker H0 side by side — that is
redundant, not merely harmless. The broker's H1 becomes the natural
post-build/source-publication verification for this same boundary —
reusing the broker's already-required H0/H1 pair rather than adding a
third check.

**c. Resume-target resolution** — `assert_master_stable()` at line
**11922** (defined at line 9242). A possible consolidation candidate with
target-entry (item d) *only if* a future protected/uninterrupted interval
proves one observation token covers both. Retain distinct until such an
interval is separately designed and qualified.

**d. Target-entry** — `assert_master_stable()` at line **10952**, inside
`run_target_transaction`, the pre-mutation/PRE-capture guard for that
target. Retain. The command-level H1 (item b) cannot cover this — real
work and possible callbacks/yields intervene between command-level
acquisition and any individual target's actual mutation moment.

**e. GATE scoped-index use** — `contextualizer_assert_master_stable_for_index_use()`
at line 9431, inside `contextualizer_validate_master_index_subset`,
called per gate/target phase. Retain freshness at this semantic-use
boundary. May share a token with another boundary only if the *same*
protected observation token is proven to cover both — not proven today.

**f. TARGET scoped-index use after native** — `assert_master_stable()` at
line **11752**, the post-native-Rebuild-call guard inside
`run_target_transaction`. Retain separately — cannot merge with the
pre-native check (item d) or with H0/H1 (item b), since real native-call
work intervenes, and native is proven (R3-A1) to reread the Master
in-process for the tested action.

**g. Terminal/post-operation** — the same line-11752 check, viewed as the
final guard before a target's terminal state is declared. Conceptually
distinct from (f) even though production today satisfies both with one
call site: a formal successful receipt/publication must not be marked
irrevocable *before* this check passes — check first, then commit the
receipt, never the reverse. If a future redesign ever needs to separate
index-freshness (f) from receipt-commit ordering (g) into two literal
call sites, that is a future proof-required change, not assumed here.

**Correction from the prior document**: the third `assert_master_stable()`
call site (item c) is at line **11922**, not 11921 as previously stated —
an off-by-one error, corrected here from a direct re-read.

**Cost**: current-generation measured cost ≈ **17.3 ms/check** (35-sample
real measurement, 5 independent logs matching the pinned Master SHA
exactly, one confirmed via an exact `mapping_count=128555` match).
**Cost alone does not authorize consolidation** — correctness of the
observation-window argument is what matters, never cheapness.

## 8. H0/H1 and the native-use race

```
H0 -> select/open one immutable SIDECAR -> complete validation
   -> build requested detached views -> H1
   -> require H0 == H1 == embedded source identity -> publish view
   -> close provider at cohort end
```

**H0/H1 authorizes publication, not indefinite freshness** — it proves
the generation was valid at the moment of publication, nothing about
moments after (which is exactly why §7's per-boundary map still exists).

R3-A1 proved native rereads the Master in-process for the tested action.
Therefore a real race exists: between the final source-check (item f/g,
§7) and native's own read, an external edit could land in that narrow
window, and native would act on content our checks never observed.

**First-R3 design response**:
- Retain conservative cryptographic observations (full SHA re-hash,
  always — never mtime/size).
- Do not claim snapshot isolation.
- A **future B2C qualification** (not designed or built now) investigates
  whether a short source-read/no-write/no-delete Windows sharing interval
  spanning final observation through native's read is achievable without
  breaking SFM compatibility (native may itself require access this
  design hasn't confirmed is compatible with such a sharing mode).
- The publisher mutex (§12) does **not** protect against this at all — it
  serializes our own rebuild-tool writes against each other, never
  against an arbitrary external editor or Workshop update.
- If the sharing-interval mitigation cannot be qualified, this requires
  an **explicit governance decision** to accept a documented
  no-concurrent-edit operational limitation — a product decision, not
  something this design unilaterally resolves.
- Do not silently invent a restart requirement as a shortcut around this.

**Detecting a change after native**: stop further work under existing
failure/restoration semantics (whatever the Normalizer already does
today when this check fails — not redesigned here). Do not claim every
presentation mutation is automatically rolled back merely because Undo
exists as a feature. Do not unconditionally claim "finish in-flight
successfully" — a detected post-native change is a real race hit, never
papered over.

## 9. Same-source / different-artifact semantics

**Semantic generation** = Master exact-content identity (`master_sha256`)
+ compatible authority semantics + compatible projection semantics.

**Artifact SHA**:
- remains in the validation/cache key (a disambiguating component, even
  though it is not part of semantic-generation equality);
- remains in provenance (which exact build produced this artifact);
- remains in the detached-view envelope for tracing;
- is **not** automatically part of semantic-generation equality.

If the pointer switches artifact A → artifact B (both valid builds of the
same Master):
- an active operation pinned to A does not hot-swap to B;
- A may continue only if the current Master semantic generation remains
  identical (`master_sha256` unchanged) *and* live authorization (§6 #4)
  still passes at each required boundary (§7);
- future/new acquisitions may freely use B;
- the validation cache never conflates A and B by source SHA alone — each
  artifact SHA is cached independently; only the higher semantic-
  generation-equality layer treats them as interchangeable for
  continuation purposes.

## 10. Sidecar selection + corrupt-local → shipped recovery

Selection hierarchy (unchanged core sequence): resolve Master (§3) → H0 →
inspect local pointer → local artifact (full validation gate) → shipped
artifact (same gate) → `RebuildRequired`/`Unavailable`. Pointer metadata
never overrides sidecar header truth.

**Corrupt local artifact** (Astra's bounded recovery policy, adopted
exactly):
1. Surface/coalesce a passive notice: *"Local compiled Master is damaged;
   using the matching shipped copy. Rebuild to repair."*
2. Log the exact failure.
3. Release all failed local candidate state.
4. Open and fully validate an independently-matching shipped SIDECAR (the
   full gate — no shortcuts because this is "just a fallback").
5. Require the normal H0/H1 + source-generation-match cycle for the
   shipped candidate.
6. No failed-local rows/caches may be reused.
7. No TXT fallback — this is SIDECAR-to-SIDECAR only.

**Corrupt pointer**: may use a valid backup pointer (`.bak`, §14) *if* it
independently passes full pointer/artifact admission. Otherwise may
attempt one matching shipped SIDECAR (same full gate). If nothing valid
exists anywhere → `Unavailable`/`RebuildRequired`.

**`ResourceAdmissionRefusal` is not corruption** and must not
automatically trigger this recovery path — an oversized-but-otherwise-
fine artifact is a different situation than a damaged file; rebuilding
the same way would just reproduce the same refusal.

## 11. Rebuild compiler parity

Any "format-table agreement == compiler parity" claim is replaced.
Required compiler source-core parity after compilation is an **exhaustive
semantic/inventory comparison** between the source-core compiler's own
in-memory model and the generated artifact as read back through the
reader, covering: literals; destinations; fold families; ranks;
hierarchy; metadata; counts/inventories (exact match, not "roughly
matches"); conflicts/duplicates; encoding semantics. Row-size/format-
table agreement only proves the binary layout convention agrees — it says
nothing about whether the content was correctly compiled.

Same compiler implementation serves both official and custom builds — no
separate code path or reduced-rigor parity check for either.

## 12. Rebuild utility transaction + publisher serialization

**Transaction** (elaborating the earlier 15-step sketch with corrected
detail):
1. Resolve/select the input Master.
2. Read one stable source snapshot.
3. Compile to a temp file with a name unique per build attempt — even for
   identical content (never content-derived, so two concurrent identical
   compiles never collide on the temp name).
4. Flush/close.
5. Production-validate with the FINAL R3-A2B validator/provider contract.
6. Verify embedded `source_sha256`/`source_byte_length` and supported
   format/semantics.
7. Compiler source-core parity check (§11 — exhaustive, not format-table-
   only).
8. Acquire publisher serialization (below).
9. Re-resolve/re-hash the live Master — H1.
10. If H1 != this artifact's source generation, do not publish; release
    the mutex; report the mismatch.
11. Publish the immutable artifact with atomic **non-clobber** semantics
    (rename fails rather than silently overwrites if the destination
    already exists). If the final content-addressed filename already
    exists, independently verify digest/content/format of the *existing*
    file before treating it as reusable — never assume "same filename,
    therefore trustworthy" without checking. Never overwrite an immutable
    generation merely because the filename matches.
12. Atomically replace the pointer (write-temp + rename, same volume;
    back up the prior pointer to `.bak` first).
13. Re-read/verify the just-committed pointer, still under the mutex.
14. Release the mutex.
15. Report source/artifact/compiler identities.

Failure before step 12 leaves the existing pointer completely untouched
(prior valid selection recoverable).

**Publisher serialization**: named **`Global\`** Windows mutex (corrected
from `Local\` — `Global\` is required for genuine cross-*session*
serialization; `Local\` only serializes within one login session).
Namespace includes the user SID *and* the canonical Master-slot/pointer
identity. Restricted user DACL. Bounded wait, with explicit distinct
failure categories: timeout / abandoned (`WAIT_ABANDONED`) / access-or-
config failure — never collapsed into one generic busy state, and **no
silent fallback to a weaker `Local\` mutex** if `Global\` cannot be
created. If `Global\` genuinely cannot be supported in some environment,
the alternative is a *documented* single-session limitation — explicitly
never claimed equivalent to cross-session serialization.

**On `WAIT_ABANDONED`**: the caller now owns the mutex, but must treat
on-disk state as potentially inconsistent — validate the current pointer,
the backup pointer, and their referenced generations (full admission gate
on each) before proceeding with any new publish.

Compile may happen outside the mutex. Inside the mutex, exactly: final
source re-resolution/H1; the immutable-artifact publication decision;
pointer commit; commit verification. The runtime reader never takes this
mutex.

**H1 under the publisher mutex only excludes competing publishers** — it
does not exclude arbitrary Master editors. Do not claim "current source
at commit" without actual write protection. The runtime must always
re-establish currentness again on its own acquisition; it never trusts a
long-past publisher-time H1 as still valid.

## 13. Pointer schema/recovery hardening

**Pointer file bounds**: bounded total bytes (small — a few KB ceiling,
rejected outright before parsing if exceeded); bounded parse depth/shape
(the schema is flat and known; unexpected nesting is rejected, not
permissively accepted).

**Required fields**: `master_sha256`, `master_byte_length`,
`artifact_sha256`, `artifact_relative_path` (cross-check only, see
below), `format_contract_version`, `authority_semantics_version` — all
required, never silently defaulted. No duplicate/ambiguous required keys
(a literally-duplicated JSON key is rejected outright, never silently
resolved to "the last one"). Digest fields validated as exactly 64 hex
characters. Version fields validated against the reader's own expected
type/shape before any value comparison.

**Path derivation**: prefer deriving the artifact path from
`(validated format namespace, full artifact SHA)` — reconstruct
`<generated_root>/<namespace>/<artifact_sha256>.sfmsidecar`
programmatically — rather than trusting an arbitrary
`artifact_relative_path` string from the pointer. If the pointer supplies
one, treat it only as a cross-check that must match the derived path
exactly, never as the sole authority for the filesystem location.

**Reject**: absolute paths; drive-relative/UNC paths; Alternate Data
Streams; `..`/path traversal generally; junction/reparse-point escape.
The final resolved artifact must be confined to `generated_root` using
qualified Windows path identity (the same handle-based technique as §3 —
not mere string-prefix checking, which junctions/reparse points can
defeat).

**Validate** (once confinement is confirmed): the actual re-hashed
artifact SHA (never trust the pointer's claimed value as sufficient — it
is a lookup key/hint only); the artifact's own header-embedded source
identity; format/semantics compatibility; current H0. Never conflate
source byte length with SHA equality.

**Backup pointer**: written only from a prior *validated* pointer (never
from an unvalidated/speculative state). Same full admission rules apply
on recovery — never a shortcut path.

**Commit**: flush/close the artifact; atomic pointer replacement on the
same volume; preserve the valid previous pointer recoverably (`.bak`);
re-read/verify the primary while the mutex is still held; if the replace
API reports an uncertain failure after a possible commit, reconcile
actual on-disk state before reporting any outcome. Atomic visibility is
never claimed equivalent to power-loss durability — these are different
properties.

No automatic generated-artifact GC in first R3.

## 14. Runtime admission-cap gate (custom-sidecar gating)

Any claim that custom artifacts are "production-safe today merely because
they are under 16 MiB" is deleted.

**Until B2F passes, disabled for production**: arbitrary custom/local
generations; cap overrides that raise the embedded-runtime envelope; any
claim that successful *external* compilation (desktop Python 3) proves
safe *SFM runtime* (32-bit Python 2.7.5) admission — different runtime
environments, different real resource constraints; unqualified enlarged/
dense/deep custom artifacts generally.

**Allowed before B2F**: broker/rebuild development using already-
qualified fixtures (the real official artifact and other already-
qualified fixtures); external compilation of custom output, but always
explicitly labeled **"built, not runtime-qualified"** wherever surfaced;
the exact current official qualified artifact/control paths (this gating
only affects custom Master support, never the baseline official path).

**B2F must test**: 2-3+ enlarged valid artifacts; multiple row-density
shapes; long strings; deep hierarchy; large fold/family/occurrence
shapes; a representative two-consumer detached-view configuration
(exercising the §4 at-most-one-provider model realistically, not just
validator-alone timing); real Python 2.7.5 32-bit SFM; external VAS/
memory sampler; existing retained ≤16 MiB / transient ≤32 MiB gates
unless governance changes them; dynamic VAS admission under the real
sampler.

The byte cap is only an early read bound — it is not proof of safe
Python allocation. A file under the cap can still, once fully decoded
into Python-level structures, consume substantially more process memory
than its raw byte size, especially across varied row-density shapes —
exactly why B2F's real-sampler qualification is required before any
larger/denser artifact can be called safe.

## 15. Character Preset migration contract

Current confirmed state: `SEMANTIC_PROVIDER_FORCE_MODE` hardcoded SIDECAR
(line 1128); no TXT fallback; retains packed backing for adapter/dialog
lifetime (the behavior being changed); dormant AUTO→TXT path remains in
source (to be removed).

**Migration**:
- Remove the `_SEMANTIC_PROVIDER` module-global singleton.
- Remove the dormant AUTO→TXT supported runtime path entirely (dead code
  deletion).
- Acquire a finite broker cohort only when an operation needs uncovered
  vocabulary (§4) — not "at first query in the dialog."
- Detach a bounded view.
- Close packed backing **before returning to idle dialog** — the
  provider is never open while the dialog sits idle.
- Reuse a covered detached view only after a fresh live-freshness
  authorization check (§6 #4) — never assumed still valid merely because
  it was valid once.
- Dialog close releases its views/accounting.
- Delayed callbacks arriving after close/invalidation cannot mutate —
  a no-op/explicit-rejection, never silent use of stale closure state.

**Separate Character Preset integration suite** must cover: first query;
repeated body/expression/clothing actions; late (newly-needed)
vocabulary; two-consumer interaction; delayed callback after close;
invalidation; same-source artifact replacement (A→B, §9); changed-source
reacquisition; close/reopen; aggregate resource release; **zero packed
backing while idle** (a direct, explicit assertion — the core invariant
this migration establishes).

## 16. Normalizer migration contract

Preserve exactly: existing consumer lookup/view shape; current mutation
policy; early normalization timing; target transaction semantics; Undo
behavior; Selected/All/Resume behavior; preemption; hierarchy/metadata
fidelity; active-rig presentation; no late surprise normalization. Do not
redesign the target executor's own internal mutation logic in this
migration — only how it obtains authority/data changes.

Preparation: acquire/build a command-scoped detached view; close the
provider; only then mutate targets (§4).

**Correction**: the Normalizer does not write the Master. It reads
authority (today, its own ad-hoc TXT parse) and mutates *runtime
presentation* — the in-session control-group assignments/rig state — never
the Master file itself. Only the rebuild utility ever writes a new
SIDECAR artifact; the Master TXT is edited only by the user, externally.

**Correction**: TXT currently constructs a scoped view exactly **once**
per run — `parse_targeted_master()` is called a single time, at the BUILD
phase inside `start()` (confirmed at line 13195, immediately after the
BUILD freshness check at 13184). `master_lookup()` calls elsewhere in the
file query the already-built `self.master_index` structure — they never
re-invoke `parse_targeted_master`. Do not describe this as reparsing per
lookup.

## 17. Retry/failure UX

One initiating acquisition request: **at most one H0/H1 retry, total,
across its entire callback/request chain** — never per-attempt, never
unbounded. Retry applies only before mutation. Recheck user/target
eligibility before retrying (do not blindly retry a now-stale request).

**Do not retry automatically when**: the active live request was
cancelled by posing; corrupt/missing/incompatible authority needs user
action; cap/resource admission was refused; the current operation's
source already changed mid-operation.

Publisher contention (`AuthorityBusy` from mutex-wait timeout) is a
bounded wait/retry category of its own, explicitly distinct from memory/
resource refusal — never sharing one generic retry policy.

Live notifications: coalesce passive failures; at most one modal for an
explicit user command; no modal storm; no automatic rebuild triggered as
a side effect of a failed mutation callback.

`MasterUnknown` is a successful, covered negative result — never an
authority-error substitute; code must never use it as a lazy stand-in for
"something went wrong."

**Remove** any "minimal TXT structural sanity" runtime second parser
unless an exact, already-existing required check is identified by name
and deliberately preserved for a stated reason. Grammar validation
belongs to the compiler/rebuild parity check (§11), not to a separate
runtime-side sanity parser.

## 18. Minimal state machine (final)

```
IDLE
  -> RESOLVE (§3)
       --fail--> [MasterAbsent / MasterUnreadable / AmbiguousMasterPath] -> IDLE
  -> H0_OBSERVED
  -> SELECT_ARTIFACT (§10)
       --fail--> [SidecarMissing / SourceGenerationMismatch / SidecarCorrupt /
                   FormatUnsupported / AuthoritySemanticsUnsupported /
                   ResourceAdmissionRefusal / RebuildRequired] -> IDLE
  -> VALIDATE (FINAL R3-A2B bounded read + complete structural validation)
       --fail--> [SidecarCorrupt] -> corrupt-local recovery (§10) or IDLE
  -> BUILD_VIEWS (§8's coverage descriptor, per §4's collected-vocabulary
                  request set -- built while the SINGLE provider is open)
  -> H1_VERIFY
       --fail--> [AuthorityChangedDuringAcquisition] -> at most ONE bounded
                  retry (§17) -> RESOLVE, or IDLE if exhausted
  -> READY_DETACHED (views published; provider CLOSES here -- §4)
  -> AUTHORIZE_USE (consumer-internal freshness re-check, §7 boundaries)
  -> TARGET_TRANSACTION (0..N targets/queries, no provider open;
                          independently freshness-guarded per §7)
       --generation change detected--> [AuthorityChangedDuringOperation] -> SAFE_STOP
  -> COMPLETE / SAFE_STOP (never leaves partial/inconsistent authority state)
  -> RELEASE (cohort closed already at READY_DETACHED transition for the
              provider; this step releases/accounts the detached views)
  -> bounded detached-cache state (views may still be held read-only
     until discarded or superseded by re-acquisition)
  -> IDLE
```

Concurrent consumer admission is modeled as independent state-machine
instances, never sharing an open provider concurrently (§4 forbids
concurrent open providers; sharing, when it happens, is temporal —
serialized acquisitions, or one joint preparation cohort). Generation
invalidation from any of READY_DETACHED/AUTHORIZE_USE/TARGET_TRANSACTION
goes to SAFE_STOP, never silently continues. Rebuild visibility is never
pushed live to an already-READY_DETACHED cohort — visible only on the
next fresh RESOLVE cycle. Retry is bounded and only from the H1_VERIFY
transition, at most once total per initiating request (§17). Shutdown is
best-effort RELEASE from whatever state is current; the reader side holds
no cross-process locks (only the writer's mutex, §12, needs OS-level
crash-safety).

## 19. Corrected B2 dependency order

**B2A → B2B → B2E → B2F → B2C → B2D**

- **B2A** — canonical broker package ownership (§2) + resolver (§3) +
  generation descriptor (§6) + sidecar selection (§10) + H0/H1 (§8). No
  consumer migration.
- **B2B** — finite acquisition cohorts (§4) + detached views (§6 #3/§8-
  equivalent coverage contract) + aggregate ownership/memory accounting
  (§5). No consumer migration.
- **B2E** — external rebuild utility + immutable artifact/pointer
  publication + named mutex/recovery (§11-§13). Still isolated from
  consumers.
- **B2F** — runtime custom-artifact cap/resource-envelope qualification
  (§14). Must pass before public custom/local generation support.
- **B2C** — Normalizer migration only (§16).
- **B2D** — Character Preset migration only (§15).

Do not merge B2C/B2D. Do not publicize custom-artifact support before
B2F.

## 20. Astra correction acceptance matrix

Note on numbering: the prompt's 18 numbered correction sections (1-18)
plus the B2-order correction are tracked here as **B1.1 through B1.18**
(19 rows would double-count the order fix as both §19 and its own row —
the order fix is folded into B1.18 alongside its originating section).

| # | Correction | Corrected section | Design decision | Status |
|---|---|---|---|---|
| B1.1 | Remove false TXT-fallback conflict | §1 | Locked no-silent-fallback contract restated cleanly; no live tension tracked | **CLOSED** |
| B1.2 | Canonical broker module ownership | §2 | `sfm_master_authority.runtime` sole owner, absolute-import-only, origin/API-identity validation, no execfile/vendoring/hot-reload | **CLOSED** |
| B1.3 | Effective-Master path identity | §3 | Reuse production `derive_paths()` verbatim as primary; handle-based (`GetFileInformationByHandle`) identity proof replaces realpath+lowercase claim | **CLOSED** |
| B1.4 | Provider lifetimes | §4 | At-most-one-open-provider invariant; finite cohorts for both consumers redesigned | **CLOSED** |
| B1.5 | Aggregate memory budget | §5 | One shared aggregate budget, not refcount-based; ≤16/≤32 MiB as process-wide gates; B2B empirically qualifies | **CLOSED** (numbers deferred to B2B by design, not an open question) |
| B1.6 | Four identities | §6 | Semantic generation / artifact identity / view coverage / live authorization explicitly separated; #1 and #3 marked load-bearing, not diagnostic | **CLOSED** |
| B1.7 | SHA/freshness map | §7 | Astra's a-g semantic-boundary map adopted; line 11922 off-by-one corrected; BUILD boundary reuses broker H0/H1 instead of a duplicate check | **CLOSED** |
| B1.8 | H0/H1 + native-use race | §8 | Race acknowledged explicitly; conservative checks retained; sharing-interval mitigation deferred to a named future B2C qualification; governance decision required if unqualifiable | **CLOSED** (mitigation itself is a future B2C empirical question, not a B1 design gap) |
| B1.9 | Same-source/different-artifact | §9 | Semantic generation = master_sha256 + compatible semantics only; artifact SHA excluded from equality but kept in cache key/provenance; cache never conflates A/B | **CLOSED** |
| B1.10 | Corrupt-local → shipped recovery | §10 | Astra's exact 7-step bounded recovery adopted; ResourceAdmissionRefusal explicitly excluded from this path | **CLOSED** |
| B1.11 | Rebuild compiler parity | §11 | Exhaustive semantic/inventory comparison required; format-table agreement alone explicitly insufficient | **CLOSED** |
| B1.12 | Publisher serialization | §12 | `Global\` mutex (corrected from `Local\`), SID+slot namespace, restricted DACL, distinct failure categories, no silent downgrade, `WAIT_ABANDONED` reconciliation | **CLOSED** |
| B1.13 | Immutable artifact publication | §12 | Per-attempt-unique temp names even for identical content; atomic non-clobber final publish; existing-file digest re-verification | **CLOSED** |
| B1.14 | Pointer schema/recovery | §13 | Bounded bytes/shape, required-field validation, derive-path-from-SHA preferred over trusting stored path text, full traversal/ADS/junction rejection, handle-based confinement | **CLOSED** |
| B1.15 | Custom-sidecar gating | §14 | "Under 16 MiB therefore safe" claim deleted; explicit disabled/allowed lists until B2F; B2F test matrix specified | **CLOSED** |
| B1.16 | Character Preset migration | §15 | Zero-packed-backing-while-idle invariant; finite-cohort-on-uncovered-need model; 11-item integration suite specified | **CLOSED** |
| B1.17 | Normalizer migration | §16 | "Writes the Master" / "reparses per lookup" mischaracterizations corrected; command-scoped-then-close-then-mutate sequence confirmed against real `start()`/`parse_targeted_master()` call graph | **CLOSED** |
| B1.18 | Retry/failure UX + corrected B2 order | §17, §19 | Exactly one total H0/H1 retry; explicit no-auto-retry list; publisher contention as its own category; runtime TXT-grammar-parser removed unless a named check is preserved; B2A→B2B→B2E→B2F→B2C→B2D adopted | **CLOSED** |

**No STILL OPEN items remain. Nothing blocks B2A at the design level.**
(Several items — mutex-API availability in the chosen Python 3 packaging,
the exact `generated_root` path-string convention, the Normalizer
command-level-cohort call-graph achievability, B2B's real memory numbers,
and the B2C native-use-race sharing-interval investigation — are
correctly scoped as *empirical confirmations at their own later
checkpoint*, not open design questions blocking B2A itself; each is named
at its owning section above.)

## 21. Verdict

**`B1 CORRECTED — READY FOR OWNER ACCEPTANCE`**

Per the hard stop: design only. No SFM launch, no R1D modification, no
modification of the final R3-A2B candidate, no Character Preset Manager
modification, no Normalizer production-code modification, no Master
modification, no broker/rebuild implementation, no B2A begun. Stopping
here.
