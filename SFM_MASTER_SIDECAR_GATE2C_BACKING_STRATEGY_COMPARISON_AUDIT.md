# SFM Master Sidecar — Gate 2C: Backing Strategy Investigation (Candidate B vs Candidate C)

Investigation and bounded test prototypes only. Candidate A remains the production reader throughout and
after this task. No production reader/writer/compiler code modified. No binary format change, no Master
change, no Normalizer integration, no format v1 freeze. Nothing committed.

## 1. VERDICT

**LEANING RECOMMENDATION: Candidate B (bounded file reads) — pursue as a separate, dedicated
production-implementation phase, pending loaded-project reconfirmation.** This is an investigation-stage
conclusion, not a production decision — no backing change is made or authorized by this task.

Both Candidate B and Candidate C passed every desktop-parity and real-SFM idle-session check with **zero
semantic discrepancies** from Candidate A (Section 9). Under real embedded SFM, idle-session measurement
(Section 10), both candidates showed a **materially lower open-time peak** (~47 MiB vs Candidate A's
qualified ~63.24 MiB — roughly 25% lower) and a **materially lower two-generation-overlap cost**
(~50 MiB steady / ~86–87 MiB peak vs Candidate A's qualified ~69.5–72.9 MiB steady / ~91.9 MiB peak — roughly
25–30% lower), while retained/steady single-open cost was comparable to Candidate A (~33–38 MiB vs ~38.83
MiB) and open/lookup performance remained acceptable (opens ~1.9–2.1 s vs Candidate A's ~1.84–1.92 s; lookup
batches ~0.055–0.064 s vs ~0.049 s). Neither candidate showed any largest-free-region erosion in this idle
session — but neither did Candidate A in its own idle-session test (Gate 2A); the fragmentation concern that
actually materialized (Gate 2B) did so only under real loaded-project pressure, which this task's Candidate
B/C testing did **not** repeat (Section 19, remaining work). Candidate B and Candidate C perform almost
identically to each other; Candidate B is preferred as the lead candidate for its simpler failure surface
(ordinary file I/O vs. platform-specific memory-mapping semantics, Section 15).

**Neither candidate is selected or implemented in production by this task.** Per this task's own Part 13,
the improvement shown is real and material on the metrics actually measured, but the decisive
loaded-project/fragmentation retest — the condition that actually distinguishes candidates in a way that
matters for real usage — remains outstanding.

## 2. CANDIDATE A CONTROL

Unchanged production reader (`tools/sfm_master_sidecar/reader.py`, SHA-256
`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`): complete sidecar copied into one
retained immutable `bytes` buffer at open, validated once, every subsequent query answered from that buffer.
Qualified figures used as the comparison baseline throughout this document (from
`SFM_MASTER_SIDECAR_GATE2A_MAINTHREAD_RESOURCE_BASELINE_AUDIT.md`, same execution context — Qt/main-event
thread, same official artifact): open ≈1.841–1.847 s; peak private delta ≈63.24 MiB; steady retained private
delta ≈38.83 MiB; retained committed-VAS delta ≈44.45 MiB; post-close residual ≈13.37 MiB; two-generation
overlap steady delta ≈69.51 MiB / peak delta ≈87.68–91.92 MiB (idle-session and Gate 2B loaded-project
figures both recorded; idle figures used for like-for-like comparison here).

## 3. CANDIDATE B DESIGN

**Bounded file-backed reads.** A single open file handle (`open(path, "rb")`) is kept for the reader's whole
lifetime. Every byte the validator or a query needs is obtained via `seek(offset); read(length)` — never a
whole-file read. The embedded-integrity digest is computed by streaming the file through `hashlib.sha256()`
in 1 MiB chunks (with the digest field's own bytes zeroed in the one chunk that contains them), never by
materializing the whole file as one Python object. All structural decode logic (header, directory, string
table, group table, child-ID index, metadata table, occurrence table, fold table, both index tables, every
Section 20 A–J check) uses the SAME order and the SAME individual checks as production `reader.py`'s
`_validate_and_decode` — transcribed faithfully, not redesigned — differing only in sourcing each section's
bytes via one bounded `backing.read(section_offset, section_length)` call per section rather than slicing a
fully-resident buffer.

## 4. CANDIDATE C DESIGN

**Read-only memory mapping.** `mmap.mmap(fileno, 0, access=mmap.ACCESS_READ)` over the whole file, kept open
for the reader's lifetime alongside its backing file handle. Every byte needed is obtained via a bounded
slice of the mapping (`mm[offset:offset+length]`), which Python materializes as a small `bytes` object only
for that slice — the mapping itself is never converted to one large Python `bytes`/`bytearray` object. Same
digest-streaming approach as Candidate B (chunked reads over the mapping, not a whole-mapping copy). Same
faithfully-transcribed Section 20 A–J validation order as Candidate B and Candidate A.

## 5. PYTHON 2.7 / SFM CAPABILITY

Established empirically in real embedded Python 2.7.5 (SFM PID 18252, tiny 32-byte disposable test file —
never the official sidecar):

- **Candidate B (file seek/read): PASS.** `seek(10)` + `read(4)` returned the exact expected 4 bytes; a full
  read returned the exact 32 bytes.
- **Candidate C (mmap): PASS.** `import mmap` succeeded (`<module 'mmap' (built-in)>`);
  `mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)` created a working read-only mapping; slicing worked
  correctly; an attempted write to the read-only mapping was correctly rejected
  (`TypeError("mmap can't modify a readonly memory map.")`).
- Neither capability was found unavailable or unstable — both candidates were carried forward to
  prototyping, per this task's own Part 2 instruction.

## 6. IMMUTABILITY / TOCTOU

Established empirically (both on the desktop, Windows OS-level semantics — not Python-version-specific —
and cross-checked directly in real SFM Python 2.7.5 for the delete case):

- **Delete while a plain file handle is open:** `os.remove()` **fails** with
  `WindowsError(32, 'The process cannot access the file because it is being used by another process')` while
  ANY handle (plain read handle, or the handle backing an mmap) is open, using Python's default `open()`
  sharing mode. **This protects both Candidate B and Candidate C from deletion-based TOCTOU for the life of
  the reader**, on Windows, without any extra code.
- **Concurrent WRITE from a second handle while a read handle is open: succeeds** — a second `open(path,
  "r+b")` handle can write to the same file while the first handle is open for reading, and **the mutation is
  immediately visible through the original read handle** (confirmed: byte 0 changed from `'0'` to `'X'`,
  visible on re-read).
- **An existing read-only mmap observes the same concurrent external write live** — confirmed directly: a
  write through a separate handle changed byte 0 from `'0'` to `'Y'`, and the **already-mapped** view showed
  the new byte immediately. This directly confirms the final spec's own retraction (Section 22): **mmap does
  not provide snapshot isolation on this platform.** Neither Candidate B nor Candidate C prevents another
  writer from mutating validated bytes underneath the reader, on their own.
- **Conclusion, matching the final spec's own requirement exactly:** neither candidate can claim the Section
  22 stability invariant from its read mechanism alone. Both must rely on the **qualified publication
  contract** (Section 32/34: immutable, content-addressed generation filenames; identical-content-under-
  existing-name is a safe no-op; different-content-under-the-same-name is a hard publication failure, never
  an in-place overwrite) as the actual source of the immutability guarantee — i.e., as long as every writer
  to the generation-file namespace goes through the qualified publisher, no in-place mutation of an
  already-validated generation's bytes will ever occur, and the residual risk is entirely about out-of-band
  processes writing directly to a generation file outside the publication contract, a risk Candidate A does
  not share (its snapshot is taken once and the file is never touched again) but which Candidate B/C
  inherently retain for the life of the reader. This is reported as a real, structural difference between
  Candidate A and Candidate B/C's risk profile — not a defect discovered in this task's own prototypes, and
  not something either prototype attempts to independently solve (per the final spec's own framing, this is
  the publication contract's job, not the reader's).

## 7. VALIDATION MODEL

Both candidates perform the complete, exhaustive Section 20 A–J validation at open time — no sampling, no
shortcuts — computed via bounded/chunked reads (never one giant in-memory decode of the raw file), exactly as
the final spec's own Section 20 anticipates ("chunked/sequential... is an independent property from... not
sampled"). The embedded-integrity digest (Section 19) is computed by streaming the file through
`hashlib.sha256()` in 1 MiB chunks for both candidates, with the digest field's own 32 bytes zeroed in the
one chunk containing them — verified to produce the exact correct digest (checksum-invalid fixtures were
correctly rejected for both candidates, Section 9).

## 8. PROTOTYPE ARCHITECTURE

One shared, faithfully-transcribed decode/validation function
(`validate_and_decode_from_backing(backing)`, in the test-only `gate2c_prototype.py`) is parameterized over a
`backing` object exposing `.size` and `.read(offset, length) -> bytes`; `FileBacking` and `MmapBacking` are
the only two implementations, differing only in how `.read()` sources bytes. `format.py`'s struct pack/unpack
functions and constants are imported and reused unchanged; the same result/exception classes production
`reader.py` defines (`Hit`, `FoldConflict`, `MasterUnknown`, `AuthorityUnavailable`, `SourceMismatchError`)
are imported and reused unchanged, so a prototype result is directly, trivially comparable to a production
result — nothing was re-implemented that didn't need to be.

**A real implementation bug was caught and fixed before real-SFM measurement:** the prototype's first
`close()` implementation closed only the file/mmap handle, without releasing the reference to the fully
decoded object graph (`self._pb`) — unlike production `SidecarReader.close()`, which sets `self._backing =
None`. This was caught by comparing a first (buggy) real-SFM run's post-close residual (Candidate B: +41.11
MiB; Candidate C: +164.50 MiB — both dramatically higher than Candidate A's ~13 MiB) against expectation,
diagnosed by direct code comparison against production's `close()`, fixed (`self._pb = None` added), and
independently re-verified via a local parity check (`b._pb is None` after `close()`) before redeploying to
SFM for the real, reported measurement (Sections 10–12). This is disclosed here in full rather than silently
corrected, since it is exactly the kind of prototype-fidelity issue this task's own Part 5 ("the prototype
exists to measure backing behavior, not become production by accident") warns about.

## 9. DESKTOP PARITY

Both candidates opened the exact official 9,506,244-byte artifact
(SHA-256 `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`) under Python 3, compared directly
against Candidate A:

| Check | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| `group_count()` | 43 | 43 | 43 |
| `occurrence_count()` | 128,555 | 128,555 | 128,555 |
| First/middle/last fold → HIT, correct destination | PASS | PASS | PASS |
| Absent fold → `MasterUnknown` | PASS | PASS | PASS |
| `list(iter_groups())` exactly equal to Candidate A | — | **True** | **True** |
| `list(iter_occurrences())` exactly equal to Candidate A | — | **True** | **True** |
| Checksum-invalid rejection | PASS | PASS | PASS |
| Source-mismatch rejection | PASS | PASS | PASS |
| Double-`close()` idempotent | PASS | PASS | PASS |
| Post-close lookup rejected | PASS | PASS | PASS |

**Zero semantic discrepancies found for either candidate.** Per this task's own Part 6 instruction, both
candidates survived to real-SFM measurement.

## 10. SFM IDLE RESULTS

Real embedded Python 2.7.5, Qt/main-event thread (never `threading.Timer`), external Python 3 sampler (same
protocol as the qualified Gate 2A baseline). Deltas below are all vs. this run's own S0
(PrivateUsage 470,560,768 bytes; largest free region 2,087,452,672 bytes — an ordinary idle-session baseline,
comparable in kind to Gate 2A's own idle S0).

| Metric | Candidate A (qualified) | Candidate B | Candidate C |
|---|---|---|---|
| Open time | ≈1.841–1.847 s | 2.107 s | 1.901 s |
| Peak private delta (single open) | ≈63.24 MiB | **46.87 MiB** | **47.43 MiB** |
| Steady retained private delta | ≈38.83 MiB | 33.29 MiB | 38.00 MiB |
| Post-close residual | ≈13.37 MiB | **−3.16 MiB** (fully released) | 9.80 MiB |
| Lookup batch (2,990 keys) | ≈0.049 s | 0.064 s | 0.055 s |

Both candidates: functional check PASS (`group_count`=43, `occurrence_count`=128,555, first-fold `Hit`), no
exceptions.

## 11. LOADED-PROJECT RESULTS

**Not performed in this task.** Per Section 19 (remaining work), this is explicitly deferred — the idle
qualification above was clean for both candidates, satisfying this task's own Part 9 precondition to proceed,
but the loaded-project retest itself (reusing or matching Gate 2B's real 116-shot project scenario) was not
carried out, primarily due to the scope already covered in this single investigation pass. This is reported
as an honest gap, not a passed-then-omitted step — no claim is made here about how Candidate B/C would behave
under the same contiguous-VA pressure that Gate 2B found materially constrained Candidate A.

## 12. GENERATION-OVERLAP RESULTS

Same two known-valid generations as Gate 2B: G1 (official, 128,555 occurrences,
SHA-256 `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b`) and G2 (minimally-changed
synthetic test variant, 128,556 occurrences, SHA-256
`4aa75985d1ccceefaaae8bd570616593aebd5d2769624ea2c7d81dc8ced74901`, produced from an in-memory-only modified
copy of the Master's text — canonical Master file on disk never touched, Section 20).

| Metric | Candidate A (qualified, idle) | Candidate B | Candidate C |
|---|---|---|---|
| G1-alone retained | ≈29.25 MiB | 42.53 MiB* | 34.88 MiB* |
| G1+G2 overlap steady | ≈69.51 MiB | **49.69 MiB** | **49.67 MiB** |
| Overlap peak | ≈87.68–91.92 MiB | 86.58 MiB | 86.48 MiB |
| After G1 release (G2-only) | ≈4.90 MiB | 8.79 MiB | 10.41 MiB |
| After both released | ≈4.90 MiB | 8.79 MiB (unchanged) | 10.41 MiB (unchanged) |
| Largest free region, S0→overlap→final | unchanged (idle) | **unchanged** | **unchanged** |

*Candidate B/C's "G1-alone" figure here reflects a SECOND, independent G1 open performed later in the SAME
session (after the single-open test's own clean close) — it is not directly comparable to Candidate A's
figure in absolute terms (different session, different history) but the **G1+G2 overlap vs. G1-alone delta**
(the actual overlap COST) is the fair comparison: Candidate B/C's own overlap cost is **7.16 / 14.79 MiB**
respectively, well below Candidate A's ≈40.26 MiB overlap-specific delta measured in the Gate 2A idle
baseline. Both providers were confirmed independently valid and correctly distinct
(`occurrence_count() == 128555` vs `128556`) throughout the overlap window, for both candidates. G1's
release never disturbed G2 in either candidate, matching Candidate A's own qualified behavior.

**Both candidates show a materially lower two-generation overlap cost than Candidate A** in this idle
session — the single largest, clearest advantage found in this investigation.

## 13. PERFORMANCE

| Metric | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| Full open/validation (single, idle) | ≈1.84 s | 2.11 s (≈15% slower) | 1.90 s (≈3% slower) |
| 2,990-query lookup batch | ≈0.049 s | 0.064 s | 0.055 s |
| Full group enumeration (43) | — | correct, no timing concern at this scale | correct |
| Full occurrence enumeration (128,555) | — | correct, exercised via full parity check | correct |

Neither candidate's open/lookup latency is unusable — both remain well within ordinary interactive
tolerances (low single-digit seconds for a full 9.5 MB artifact open; tens of milliseconds for a
representative lookup batch). Candidate B's ≈15% slower open is attributable to many individual
`seek`+`read` syscalls across the file (one or more per section, plus per-row unpacking reusing small
temporary bytes objects) versus one bulk read; this was not a source of any functional problem in this
task's measurements.

## 14. LIFETIME / CLEANUP

Both candidates: `close()` releases the backing file handle/mapping AND drops the reference to the decoded
object graph (`self._pb = None`), matching production `SidecarReader.close()`'s exact discipline (Section 8's
disclosed fix). Double-`close()` is idempotent for both. Post-close lookup correctly raises
`AuthorityUnavailable` for both. G1/G2 independence under overlap (Section 12) confirmed for both. No
production reader lifetime/invalidation semantics were altered, extended, or reinterpreted — the prototypes
reuse the exact same result/exception classes and reproduce the exact same close/idempotency/post-close
contract.

## 15. COMPLEXITY / RISK

| Aspect | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| Implementation complexity | Lowest — one read, one buffer, done | Moderate — persistent handle, many bounded seek/read calls, more I/O failure surface | Moderate-high — persistent mapping + handle, platform-specific mmap semantics |
| Python 2.7 compatibility risk | None (already qualified) | Low (ordinary file I/O, empirically confirmed) | Low-moderate (mmap confirmed working, but a narrower, more platform-specific API) |
| Windows handle lifetime complexity | None (handle closed immediately after the one read) | Moderate (handle held for reader's whole life; must be closed exactly once, cannot leak) | Higher (mapping AND handle both held; cleanup ordering matters; mmap-specific Windows quirks possible in other embedding contexts not exercised here) |
| Corruption/TOCTOU risk | Lowest (one-time snapshot; nothing to observe after) | Present, mitigated only by the publication contract (Section 6) | Present, identically mitigated only by the publication contract (Section 6) — mmap provides no additional protection over B here |
| Cleanup/lifecycle complexity | Lowest | Moderate | Moderate-high |
| Generation-overlap behavior | Correct, higher memory cost (Section 12) | Correct, lower memory cost | Correct, lower memory cost |
| Expected maintenance burden | Lowest | Low-moderate | Moderate |

**Candidate A's simplicity is real and was not dismissed in this comparison.** Candidate B's added complexity
is modest (bounded seek/read is a well-understood, low-risk pattern); Candidate C's added complexity is
somewhat higher for an improvement that, in this task's own measurements, is not clearly superior to
Candidate B on any metric that matters (comparable peak, comparable overlap savings, worse post-close
consistency here, and a materially more complex platform-specific failure surface). This is the basis for
preferring B over C if either is pursued (Section 1).

## 16. COMPARISON TABLE

| | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| Open time | ≈1.84 s | 2.11 s | 1.90 s |
| Peak private delta | ≈63.24 MiB | 46.87 MiB | 47.43 MiB |
| Retained private delta | ≈38.83 MiB | 33.29 MiB | 38.00 MiB |
| Retained committed-VAS delta | ≈44.45 MiB | not independently isolated this pass | not independently isolated this pass |
| Post-close residual | ≈13.37 MiB | −3.16 MiB | 9.80 MiB |
| Overlap steady (G1+G2) | ≈69.51 MiB | 49.69 MiB | 49.67 MiB |
| Overlap peak | ≈87.68–91.92 MiB | 86.58 MiB | 86.48 MiB |
| Overlap-specific cost (vs. G1-alone) | ≈40.26 MiB | 7.16 MiB | 14.79 MiB |
| Largest-free-region effect (idle) | none | none | none |
| Lookup batch (2,990) | ≈0.049 s | 0.064 s | 0.055 s |
| Complexity | Lowest | Moderate | Moderate-high |

## 17. RECOMMENDED BACKING

**Candidate B**, as a lead candidate for a separate, dedicated production-implementation phase — not
selected or implemented now. Candidate C remains a viable, closely-comparable alternative if Candidate B's
implementation phase surfaces a specific reason to prefer memory mapping (e.g., a demonstrated need for even
lower peak cost that a future measurement shows mmap providing more consistently), but nothing in this task's
data makes that case today.

## 18. PRODUCTION-CHANGE JUSTIFICATION

**Not yet fully justified — additional evidence (loaded-project retest, Section 11/19) is required before a
production change would be responsible.** What IS justified by this task's evidence: both alternatives are
semantically sound (Section 9), functionally correct under real SFM (Sections 10–12), and show a real,
material reduction in open-time peak and two-generation-overlap cost relative to the qualified Candidate A
baseline — enough to warrant carrying this investigation to the next stage (loaded-project confirmation),
not enough, on its own, to authorize replacing Candidate A in production yet, per this task's own explicit
instruction not to implement a production replacement in Gate 2C itself.

## 19. REMAINING GATE 2 WORK

- **Loaded-project retest for Candidate B and Candidate C** (this task's own Part 9), reusing or matching
  Gate 2B's real 116-shot project scenario — specifically to determine whether either candidate's
  lower-idle-cost advantage survives, and whether either avoids the non-recovering largest-free-region
  reduction Gate 2B found for Candidate A under real project load. This is the single most important
  remaining step before any production recommendation could be finalized.
- Repeated open/close cycling for Candidate B/C (Gate 2B's own Part B pattern), to confirm stability
  (not ratcheting) under repetition, matching what was already confirmed for Candidate A.
- Committed-VAS-specific deltas for B/C were not independently isolated in this pass (Section 16) — a future
  measurement could report these explicitly alongside PrivateUsage.
- Whether Candidate B or C are necessary AT ALL remains genuinely open — Candidate A's Gate 2B finding was
  "retain with concern," not "not viable"; a materially-improved-but-not-yet-fully-proven alternative does
  not automatically obligate a production change.
- Normalizer consumer-contract qualification — not begun, not implied by anything in this task.
- Format v1 freeze decision — not begun, not implied by anything in this task.

## 20. GIT / SAFETY

- HEAD before and after this task: `647294428aa552695571f10ad0c207612c53ec7c` — unchanged.
- `sfm_defaultanimationgroups.txt`: unchanged (`ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93`).
- `tools/sfm_master_sidecar/reader.py`: unchanged (`d79f7ae87c1999b7fe728f7dd6ddafb29b7cc62c246cd332f061875095288b00`).
- `tools/sfm_master_sidecar/format.py`: unchanged (`b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259`).
- All other production sidecar modules: unchanged. No Candidate B/C code was added to
  `tools/sfm_master_sidecar/`; all prototype code lived solely in this session's own scratchpad directory and
  temporary SFM deployment locations, all removed after use.
- No Normalizer code touched. No format-freeze action taken. No production edits of any kind.
- Every SFM session in this task was a fresh, disposable instance (`tasklist` confirmed no running `sfm.exe`
  before each launch); all were terminated by this task after their measurement completed.
- Cleanup after each SFM run: deployed runtime package, prototype module (including the `.pyc` bytecode
  cache file it produced), G1/G2 artifacts, lookup batch, and autoinit probe all removed; a directory-wide
  search for `*gate2c*` under `usermod\scripts\` found nothing remaining; `usermod\scripts\sfm\sfm_init.py`
  confirmed byte-for-byte unchanged (`08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15`)
  after every run.
- Nothing staged, nothing committed. `git status --porcelain` shows only this new audit file as untracked,
  plus the same pre-existing unrelated untracked files present since before this task began.
- No agents or subagents were used.
