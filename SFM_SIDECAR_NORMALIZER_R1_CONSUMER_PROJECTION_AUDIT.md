# SFM Sidecar / Normalizer — R1 Consumer Projection Qualification Audit

Controlling review: `SFM_Normalizer_Sidecar_Reconciliation_Audit_2026-09-13.md` (ADOPT
CONDITIONALLY; PRODUCTION INTEGRATION: NO-GO).
Ownership boundary: ChatGPT owns and develops the SFM Normalizer; Claude Code owns
the Master/compiled sidecar work. The Normalizer is treated throughout this gate as
a **frozen external consumer** — nothing in this gate edits, redesigns, or
reinterprets its behavior.

## 1. VERDICT

**R1 PASS — AUTHORIZE R2 DECISIVE COST COMPARISON**

Zero semantic/coverage/failure/conflict-timing/rank/order/required-metadata
mismatches were found on the supported profile. Every unsupported-profile case
(backslash-containing source, escaped-token source) is refused explicitly by the
existing qualification-only source-profile gate, never silently accepted or
converted into `MasterUnknown`. The detached view is provably consumable by both
real consumer families after complete backing is closed, on both desktop Python 3
(for the dict-consuming functions) and real embedded Python 2.7 (end-to-end,
including the real TXT-tokenizing functions themselves). No binary-format change
was required or made.

Two items are reported honestly as **PARTIAL** rather than papered over (§11-13):
the exact historical Fox/six-target/72-shot vocabularies were not recoverable
byte-for-byte in this session (the controlling reconciliation audit itself
found these numbers contested); real, honestly-labeled current-Master stand-ins
were used instead, per the brief's own explicit "report actual count" instruction.
This does not block the PASS verdict — R1 is a projection/compatibility gate, not
the R2 cost benchmark those exact vocabularies exist to serve.

## 2. BASELINE

- Expected/actual HEAD: `e1ef50e3990a9773760e0d92a1d9d3380cd3e9d7` "Qualify sidecar
  source freshness lifecycle" — confirmed matching before any change.
- `git status --short` / staged files: clean except the same long-standing pool of
  unrelated pre-existing untracked files; nothing staged at any point.
- `git diff --check`: PASS throughout.
- See §18 for the full identity table.

## 3. REAL MANUAL CONSUMER CONTRACT

Verified by direct reading of the current, installed
`Rebuild_Control_Groups_Normalizer.py` (SHA-256
`6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`):

- `parse_targeted_master(path, wanted_folds, validate_conflicts=False)` (lines
  ~1416-1723): whole-source token stream; `mapping_count`/`destination_count`
  incremented/added for EVERY control token regardless of scope (whole-source);
  `folded`/`exact_literals` retained only for `wanted_folds`; `group_sibling_order`/
  `group_metadata` built for EVERY group; `group_metadata` carries
  `groupColor_raw`/`selectable_raw`/`visible_raw`/`snappable_raw` (lists, raising
  if any has more than one entry) plus promoted `group_color_explicit`/
  `selectable_explicit`/`selectable_authority` (color and selectable only — visible
  and snappable have NO promoted field in the real manual parser).
- `master_lookup(master, literal)` (lines ~1767-1825): returns the fold family's
  FIRST occurrence by `(global_index, local_index)` regardless of which spelling
  was queried; raises `ProbeError` on a multi-destination family (never a soft
  result); `mode` is `EXACT` iff the QUERIED literal itself is in `exact_literals`.
- `validate_master_subset_conflicts(master, wanted_folds)` (lines ~1726-1764):
  checks only the folds explicitly passed in, raising `ProbeError` on the first
  batch of conflicts found within that subset.

## 4. REAL LIVE CONSUMER CONTRACT

Verified by direct reading of
`SFM_20260910_T130_LiveTrigger20sOrdinaryUseRequalification.py` (the T120/T130
lineage; deployed/embedded-run copy SHA-256
`560de294c2db05e89e3d82eedbf14f614448a9f64e6deeddd7160d565a5d4ee6`):

- `t120_parse_master(path, wanted_names)` (lines ~1229-1330): `sha256`/
  `total_controls` are whole-source; `folded`/`exact_literals` scoped;
  `group_metadata` uses an `explicit_fields` set, accepts `snap` as a canonical
  alias for `snappable`, and raises `ProbeError` on a duplicate canonical key
  (including `snap` + `snappable` together). `target_conflicts` is computed and
  stored directly in the returned dict (not a separate call).
- `t120_master_lookup(master, literal)` (lines ~1333-1360): on conflict, returns
  `{"known": None, "destination": None, "mode": "CONFLICT", "global_index": None,
  "local_index": None, "destinations": tuple(dests)}` — a soft result, never a
  raised exception (a real, confirmed difference from the manual `master_lookup`).
- `t130_t95_master_from_t120(master)` (lines ~7932-7973): `mapping_count` is
  `int(master["total_controls"])` (whole-source, same value as manual's
  `mapping_count`); `destination_count` is computed from the retained (SCOPED)
  `folded` rows only — a genuinely different, narrower count than manual's.
  Metadata is promoted into `*_raw` lists + `group_color_explicit`/
  `selectable_explicit`/`selectable_authority`, matching the manual shape for
  those three fields.

## 5. PROJECTION IMPLEMENTATION UNDER TEST

New, qualification-only modules (none promoted to or imported by production):

- `tests/sidecar/qualification/normalizer_oracle_import.py`: installs minimal
  placeholder `sfmApp`/`vs`/`PySide` modules so the REAL Normalizer/T130 files can
  be imported on desktop without their embedded-only dependencies; suppresses only
  each file's own bare top-level auto-run call (`StartRebuildControlGroups()` /
  `install_t121()`) so importing them does not itself invoke the real command —
  every function body is compiled and executed completely unmodified. Not used at
  all in the embedded probe (real `sfmApp`/`vs`/`PySide` are already present there;
  the same auto-run suppression technique is reused directly).
- `tests/sidecar/qualification/r1_consumer_projection.py`: `build_manual_projection`
  and `build_live_master120`, both operating on an already-open bounded sidecar
  provider (S1) and producing dicts shaped EXACTLY like §3/§4's real contracts.
  Neither function reimplements `master_lookup`/`validate_master_subset_conflicts`/
  `t120_master_lookup`/`t130_t95_master_from_t120` — those real functions are
  called directly against the dicts this module builds.
- `tests/sidecar/qualification/desktop_r1_consumer_projection_qualification.py`:
  the desktop harness (55 checks).
- `tests/sidecar/qualification/r1_embedded_evidence/gate_r1_embedded_probe.py`: the
  embedded harness (15 checks), preserved byte-exact (§17).

**Genuine cross-version finding (disclosed, not worked around by mirroring):** the
real `parse_targeted_master`/`t120_parse_master` tokenizers are Python-2-only in
their exact byte-iteration behavior — under desktop Python 3 they raise
`AttributeError: 'int' object has no attribute 'isspace'` (Python 3 iterates a
binary-mode file as integers, not one-character strings). This was discovered
directly (not assumed) when the desktop harness first attempted to call the real
tokenizer, and is now an explicit, checked assertion in the desktop harness (§16,
R1.1). The real tokenizers are exercised natively and correctly in the embedded
Python 2.7 probe instead (§17), where they run exactly as production does.

## 6. COVERAGE SEMANTICS

Proven directly (`desktop_r1_consumer_projection_qualification.py` §R1.5, 5
checks):
- a requested-and-present fold appears in `folded` (positive);
- a requested-but-absent fold resolves to `known=False` via `master_lookup` (a
  true covered `MasterUnknown`);
- a fold never requested by this action is simply absent from `folded` (uncovered
  — never confused with a proven negative);
- `validate_master_subset_conflicts` against an uncovered fold is a silent no-op
  (no rows exist for it, so no conflict can be found) — this is the SAME real
  function; it never needs a special "uncovered" code path because an uncovered
  fold's absence from `folded` already produces the correct behavior;
- calling the provider's own `evict_reusable_cache()` after a projection dict is
  already built has no effect on that dict (it is a plain, already-detached Python
  object) — eviction cannot retroactively turn unavailable coverage into
  `MasterUnknown`.
- "No per-row fallback to TXT occurs" is verified by direct code inspection:
  neither `build_manual_projection` nor `build_live_master120` ever opens a TXT
  path or references `parse_targeted_master`/`t120_parse_master` internally — both
  read exclusively from the already-open provider.

## 7. CONFLICT TIMING

Proven directly (§R1.6, 3 checks + embedded checks 4-5): a broad command inventory
containing a conflicting fold does NOT force rejection when the immediately active
subset excludes it; `validate_master_subset_conflicts` rejects only once the active
subset includes the conflicting fold; the scalar `master_lookup` retains its own
(raising) conflict behavior independently. This is the exact real function, called
with different `wanted_folds` subsets against the SAME already-built projection —
no new timing logic was added anywhere.

## 8. COUNTS / RANKS / ORDER

Proven directly against the OFFICIAL Master (§R1.7, 3 checks): manual
`mapping_count`/`destination_count` equal the provider's own whole-source
`occurrence_count()`/`destination_count()`; rows are already presented in
global-rank order (`sorted(rows, key=lambda r: r["global_index"])` at projection
-build time, matching the real parser's own insertion-order-by-scan-position,
never re-sorted by lookup key). Root/child/sibling order is proven preserved
exactly for a 3-sibling fixture (§R1.2, case 06-07). The live T95 bridge's
`destination_count` is separately proven to be SCOPED (from retained rows only),
genuinely distinct from the manual projection's whole-source count (§R1.8) — this
distinction is preserved, not merged away, per the brief's explicit instruction.

## 9. METADATA / PRESENCE / ALIASES

- Manual: raw per-key lists (`groupColor_raw`/`selectable_raw`/`visible_raw`/
  `snappable_raw`), duplicate-raising for ANY of the four (proven with a
  `selectable` x2 fixture, §R1.2 case 15), omission preserved as empty lists
  (§R1.2 case 09), `group_color_explicit`/`selectable_explicit`/
  `selectable_authority` promotion.
- Live: `snap` accepted as a canonical alias for `snappable` (§R1.3, embedded check
  7); duplicate canonical rejection across `snap` + `snappable` together (§R1.3);
  the manual profile does NOT accept `snap` at all (proven directly — the real
  manual parser's `field_map` has no `"snap"` key), confirming the two profiles are
  genuinely different, never silently merged.
- `groupColor`/`visible` promoted-field behavior beyond the raw list is mechanism
  -verified by direct code/source reading (the manual parser itself has no
  promoted field for `visible`, matching this projection's own behavior exactly)
  but not independently hand-fixtured with an explicit value in this pass — see the
  parity matrix's honest PARTIAL-style annotation for cases 10/12.

## 10. OFFICIAL MASTER PARITY

The manual projection against the real, current official Master reproduces
`mapping_count == 128,555` (via `provider.occurrence_count()`) and the provider's
own `destination_count()` exactly, for a real requested fold (`rig_root`) — §R1.7.

## 11. FOX SCOPE

**PARTIAL.** The historical Fox scope (208 controls, shot209 with Tails/Krystal
peers) is named literally in the real T130 source (`EXPECTED_EXERCISED = u"Fox"`,
`EXPECTED_PEERS`), but the exact 208 control-name vocabulary itself was not
recoverable byte-for-byte within this evidence-collection session — the mega
reconciliation evidence tree does not contain a standalone enumerated Fox
control-name list, and the controlling reconciliation audit itself treats Fox's
208-control figure as a fact to be independently reconfirmed, not something it
reconstructed either. Per the brief's explicit "if recoverable exactly" / "report
actual count" instructions, a real, honestly-labeled 216-fold subset of the
official Master (the `Face` group's recursive fold vocabulary) was used as
workload A's stand-in instead (§R1.10) — real folds, real projection build,
correctly labeled as a stand-in, not claimed to be the historical Fox scope.

## 12. SIX-TARGET SCOPE

**PARTIAL**, same disposition as §11. The real six-target shot's exact 1,680
-occurrence vocabulary was not recoverable in this session. A real 17-fold subset
(`RigArms`) was used as workload B's honestly-labeled stand-in.

## 13. LARGE SELECTED/ALL SCOPE

**PARTIAL**, same disposition. The 72-shot/216-eligible-target stress command's
exact ~800-fold vocabulary was not recoverable in this session (the controlling
audit's own text: "Verify the historically reported 800 unique folds; report any
change instead of forcing that number" — this review did not have access to a
runnable copy of that exact command either). A real 27,414-fold subset (the same
`Face` group's full recursive vocabulary, deliberately taken at its full size
rather than trimmed) was used as workload C's honestly-labeled stand-in, and its
actual recovered count (27,414) is reported plainly rather than forced to the
historical 800.

## 14. HAND-AUDITED ADVERSARIAL FIXTURES

20 required profile/adversarial cases (brief §4) were each given an explicit,
written-in-advance expected result (`desktop_r1_consumer_projection_qualification.py`,
the `cases` list) BEFORE either producer was run. Hand-auditing caught two of the
author's own initial mistakes during this exact process (not left silently
corrected out of the record):
- an initial expectation that `master_lookup("foo")` would return
  `mode="ASCII_CASEFOLD"` was WRONG — the fixture's three exact spellings
  (Foo/foo/FOO) are ALL in `exact_literals`, so `mode` is `EXACT` for all three;
  only a spelling absent from the fixture (`"fOO"`) actually exercises
  `ASCII_CASEFOLD`. Corrected before the case was reported as passing.
- an initial expectation that the escaped-quote fixture (`21_escaped_quote_spelling.txt`)
  would produce a successful HIT was WRONG — that fixture's raw bytes contain a
  literal backslash, which the EXISTING `normalizer_source_profile` gate (Gate
  C0.2, unmodified, reused here) already refuses outright. The case was
  re-classified as an explicit-refusal case (matching required case #20's
  intent), not a HIT case, and a second assertion was added confirming the refusal.

All 20 cases, plus 15 additional coverage/conflict-timing/counts/metadata/detached
-view checks, are recorded with PASS/FAIL and evidence pointers in
`SFM_SIDECAR_NORMALIZER_R1_PARITY_MATRIX.json`.

## 15. DETACHED-VIEW AFTER BACKING CLOSE

Proven directly, both runtimes (§R1.9, 5 checks; embedded check 8): both
projections are built while the provider is open; the provider is then closed
(`provider.close()`, `is_valid() == False`) and dereferenced (`del provider`); the
REAL `master_lookup`/`t120_master_lookup` still correctly consume the
already-built, now fully detached dicts, and the T95 bridge kernel (built before
close) remains usable. Every value in both detached dicts was confirmed to be a
plain Python primitive/container (str/int/set/dict/list/None) with no `.close()`
-bearing object reachable from either.

## 16. DESKTOP RESULTS

`desktop_r1_consumer_projection_qualification.py`: **55 PASS / 0 FAIL**.

## 17. EMBEDDED PYTHON 2.7 RESULTS

Real embedded SFM (Python 2.7.5, Qt/PySide main thread), event-loop
`QTimer.singleShot`-chained phases only — no long main-thread sleeps, no native
Rebuild, no DME mutation, no project mutation.

- Disposable SFM process, launched fresh; trigger via the `usermod/scripts/sfm/
  mainmenu/` flat-file convention (clicked by the user).
- Deployed qualification modules (`bounded_provider.py`, `bounded_view.py`,
  `r1_consumer_projection.py`) SHA-256-verified byte-identical to repo originals;
  deployed `real_normalizer.py`/`real_t130.py` SHA-256-verified byte-identical to
  the exact installed Normalizer / downloaded T130 source before the run.
- First two runs failed with genuine, disclosed findings (both fixed, redeployed,
  reverified, same running SFM process — no restart needed since the custom
  module loader always re-reads/re-compiles fresh): (1) Python 2's `compile()`
  rejects a unicode string that also contains a source-encoding declaration
  comment — fixed by reading/compiling raw bytes instead of a decoded unicode
  string; (2) a missing `tools/` sys.path entry for `sfm_master_sidecar` — fixed
  by adding it, mirroring the same fix required in Round 3's own embedded probe.
- Final run: **15 PASS / 0 FAIL**, including the decisive proof unavailable on
  desktop: the REAL, native `parse_targeted_master`/`t120_parse_master`
  tokenizers, run natively against the real TXT fixture path, agree EXACTLY (byte
  -for-byte dict equality) with the sidecar-based projection built from the SAME
  generation's compiled artifact, for both a HIT/alias/family case and a conflict
  case; the real live `t120_master_lookup`/`t130_t95_master_from_t120` agree on the
  sidecar-built live projection; the real live parser's `snap` alias is confirmed
  natively; detached-view-after-close is reconfirmed end-to-end.
- Cleanup: disposable SFM process killed with the user's explicit confirmation;
  `usermod/scripts/sfm/gate_r1_deploy/` removed entirely; the mainmenu probe script
  removed; stray `.pyc` files removed from `tools/sfm_master_sidecar/`.
- `sfm_init.py` (both copies) confirmed unchanged (§18) — neither was ever edited.

## 18. IDENTITIES

| Artifact | SHA-256 | Bytes |
|---|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` | 3,972,355 |
| Official sidecar | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` | 9,506,244 |
| `reader.py` | `1b95261c52d95c306b28fc6e5e9340afa65de4ea2574ed29c2bab427d252719f` | 44,993 |
| `format.py` | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` | 14,249 |
| `manifest.py` | `bfe09c4188ec2c27de95a35d38053b3823a4a8296fc7ba6e2060ec2c3d0ec413` | 8,102 |
| Current qualification `session_owner.py`/`command_boundary.py` | unchanged from the Minimum C3 checkpoint (`e1ef50e3`) | -- |
| External Normalizer (installed) | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` | 339,944 |
| T120/T130 live source (as downloaded/deployed) | `560de294c2db05e89e3d82eedbf14f614448a9f64e6deeddd7160d565a5d4ee6` | -- |
| Platform `sfm_init.py` | `7ee38d22df91dc02440553668b2df9a88d6b381ff23447c1a06f82280f12bf2c` | 123 |
| Usermod `sfm_init.py` | `08be8719e2f9d321c72ae434fb1fd8f260e684543567ee1b4832fa107b7cbf15` | 122 |

All unchanged versus the Minimum C3 checkpoint. No production reader/format/
manifest/compiler defect was discovered during this gate.

## 19. WHAT R1 PROVES

- The existing compiled Master artifact, read through a bounded sidecar provider,
  can reproduce BOTH the real manual and real live Normalizer static-authority
  consumer contracts exactly, for every supported-profile case exercised —
  verified against the REAL consumer functions (never mirrored), on both desktop
  Python 3 (dict-consuming functions) and real embedded Python 2.7 (including the
  real TXT tokenizers themselves, natively).
- Coverage, conflict-timing, count/rank/order, and metadata-fidelity semantics —
  including the `snap` alias and duplicate-canonical-key rejection Astra flagged
  as a required, previously-unqualified adapter behavior — are all preserved
  correctly.
- A detached projection remains fully consumable by real consumer code after the
  complete backing is closed, with no provider/file dependency remaining.
- Unsupported-profile sources (backslash-containing, hence escape-ambiguous) are
  refused explicitly by an already-existing qualification gate, never silently
  mis-normalized or reported as a fabricated absence.

## 20. WHAT R1 DOES NOT PROVE

- Product value, cold/warm timing, memory/VAS cost, or process-wide lifetime —
  explicitly out of scope for R1, reserved for R2.
- The exact historical Fox/six-target/72-shot vocabularies (§11-13) — real,
  honestly-labeled current-Master stand-ins were used instead.
- Every one of the 20 required cases with an INDEPENDENTLY hand-fixtured explicit
  value (cases 10/12, `groupColor`/`visible` with an explicit value) — the
  underlying mechanism was verified correct by direct code/source comparison, but
  not separately exercised with its own dedicated fixture in this pass.
- Any production integration seam, wiring, or adapter design — none was selected,
  proposed, or implied by this gate, per the ownership boundary.
- Behavior under concurrent/multi-threaded access — this gate's proofs are
  single-threaded and deterministic.
- Whether a persistent, cross-command owner (`session_owner.py`) is even the
  right shape for the real Normalizer's existing build-once-per-command,
  hard-fail-on-change model — that question remains explicitly open (see the
  Post-C3 evidence package and the controlling reconciliation audit).

## 21. R2 AUTHORIZATION

**YES.** R1 PASS authorizes R2 (decisive cost comparison) to begin as a separate,
future task. R1 does NOT authorize production Normalizer integration, an
integration seam selection, or any change to Normalizer freshness/lifecycle
semantics — those remain explicitly deferred per the ownership boundary and the
controlling review's own next-step plan.

## 22. GIT STATE

- HEAD unchanged throughout: `e1ef50e3990a9773760e0d92a1d9d3380cd3e9d7`.
- Nothing staged at any point; no commits made.
- `git diff --check`: PASS.
- New (untracked): `tests/sidecar/qualification/normalizer_oracle_import.py`,
  `tests/sidecar/qualification/r1_consumer_projection.py`,
  `tests/sidecar/qualification/desktop_r1_consumer_projection_qualification.py`,
  `tests/sidecar/qualification/r1_embedded_evidence/` (4 files), this audit,
  the parity matrix JSON.
- No production file (Normalizer, T120/T130 source, Master, `reader.py`,
  `format.py`, `manifest.py`, binary format, `sfm_init.py`) appears in any diff.
- Temporary SFM deployment (`usermod/scripts/sfm/gate_r1_deploy/`, the mainmenu
  probe script, stray `.pyc` files) all removed.

---

## PROVIDER-SIDE CHANGES / FINDINGS

Every qualification-side change made by Claude Code in this gate:

1. **New module `r1_consumer_projection.py`** (`build_manual_projection`,
   `build_live_master120`). Necessary because no existing qualification code
   produced dicts matching the real manual/live contracts exactly (the existing
   `bounded_view.build_view_bounded` omits raw metadata lists and has no live
   -profile shape at all — a gap the controlling reconciliation audit itself
   identified in §4/§9 of that review). Satisfies the frozen contract facts in
   §3-4 above (raw lists, `snap` alias, scoped-vs-whole-source count distinction).
   Confirmed: no consumer-side behavior changed — every dict this module builds is
   consumed by the REAL, unmodified `master_lookup`/`validate_master_subset_conflicts`/
   `t120_master_lookup`/`t130_t95_master_from_t120`.
2. **New module `normalizer_oracle_import.py`**. Necessary to import the real
   Normalizer/T130 files on desktop without their embedded-only dependencies, and
   to prevent their own auto-run top-level call from executing during an oracle
   import. Confirmed: it stubs only `sfmApp`/`vs`/`PySide` (never touched by any
   consumer function this gate calls) and suppresses only the ONE bare trailing
   call each file already makes unconditionally at import time — it does not
   alter, patch, or reinterpret any function body.
3. **New desktop/embedded harnesses**. Test-only; no consumer behavior changed.
4. **Existing `normalizer_source_profile.py` (Gate C0.2) reused unmodified** to
   classify the escaped-token fixture as an explicit-refusal case (§16, §11.14)
   rather than inventing new refusal logic.

No production Normalizer file, T120/T130 source file, Master, binary format,
compiler, or `manifest.py` was ever modified.

## QUESTIONS / FINDINGS FOR NORMALIZER OWNER

1. **Ambiguity in the consumer contract:** the contract document (§4) says the
   live bridge's `destination_count` "is computed from retained rows, unlike the
   manual global count" — confirmed exactly by source reading, but the contract
   does not state whether this SCOPED live count is intentional product behavior
   or an artifact of `t130_t95_master_from_t120`'s implementation. Worth an
   explicit decision before any future adapter treats one or the other as
   authoritative for a shared use.
2. **Direct consumer access beyond `master_lookup`:** both real consumer families
   read `group_sibling_order`/`group_metadata` directly as dict keys (never only
   through a lookup function). This gate's projections already expose those keys
   in the correct shape, but any future adapter must preserve this — a scalar
   -lookup-only interface would not be sufficient, confirming the controlling
   review's own §9 finding.
3. **`visible`/`groupColor` explicit-value cases were not independently
   hand-fixtured** with a real explicit value in this pass (only the omitted case
   and the `selectable`-duplicate case were). The underlying mechanism is verified
   correct by direct code comparison, but the Normalizer owner may want an
   explicit fixture/example of a real Master `groupColor`/`visible` value to
   cross-check against in a future review.
4. **The sidecar artifact does contain every fact the current consumer contract
   requires** — no case was found where the binary format itself lacks a required
   fact. No format change was needed or proposed.
5. **Source/evidence mismatch:** the reconciliation manifest states the exact
   current Normalizer source bytes were unavailable to its own review; this gate's
   installed-path copy (SHA-256 `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e`)
   matches the SHA the earlier Astra Round 2 review already recorded for the same
   file — worth confirming this is still the intended current source for any
   future Normalizer-side review, since this gate did not independently verify it
   against a File-Library-native hash.

None of these items were resolved by editing the Normalizer; they are surfaced
here for the Normalizer owner's own review.
