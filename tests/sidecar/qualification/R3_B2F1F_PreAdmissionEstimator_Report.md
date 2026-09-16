# R3-B2F1F: Alternative D Pre-Admission Estimator — Qualification Report

**Authoritative design:** `SFM_CGN_R3_B2F1F_Alternative_D_PreAdmission_Estimator_Design_2026-09-16.md`
**Prompt:** `SFM_CGN_R3_B2F1F_Alternative_D_PreAdmission_Estimator_ClaudeCode_Prompt_2026-09-16 (1).md`
**Status:** `B2F1F PRE-ADMISSION ESTIMATOR MODEL QUALIFIED — TEST-ONLY INTEGRATION AUTHORIZED`

No frozen production/provider/broker code was modified. No SFM was run. Run 5 remains blocked. B2C/B2D remain unauthorized.

---

## 1. Available ResourceShape fields (from the real, unmodified format)

Read `tools/sfm_master_sidecar/format.py` directly (unchanged, SHA `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259`). The fixed `HEADER_STRUCT` (108 bytes) plus 9 `DIRECTORY_ROW_STRUCT` rows (28 bytes each, one per section — 252 bytes) give **every** field the design's Section 3 asks for, with no new field invented:

| Requested field | Source | Available pre-read? |
|---|---|---|
| artifact byte size | caller's own `os.path.getsize`/`fstat`, not the header | yes (trivial) |
| format version | `Header.format_contract_version` | yes |
| group count | `DirectoryRow(SECTION_GROUP_TABLE).row_count` | yes |
| metadata count | `DirectoryRow(SECTION_METADATA_TABLE).row_count` | yes |
| occurrence/control-record count | `DirectoryRow(SECTION_OCCURRENCE_TABLE).row_count` | yes |
| fold/family count | `DirectoryRow(SECTION_FOLD_TABLE).row_count` | yes |
| string-pool byte size | `DirectoryRow(SECTION_STRING_POOL).length` | yes |
| group-table byte size | `DirectoryRow(SECTION_GROUP_TABLE).length` | yes |
| metadata-table byte size | `DirectoryRow(SECTION_METADATA_TABLE).length` | yes |
| other section sizes | `DirectoryRow(*).length` for `STRING_TABLE`/`CHILD_ID_INDEX`/`OCCURRENCE_TABLE`/`OCC_BY_GROUP_INDEX`/`FOLD_TABLE`/`OCC_BY_FOLD_INDEX` | yes |

**Total preflight read: 108 + 9×28 = 360 bytes**, regardless of artifact size — independent of payload scale, satisfying "Bounded" (Section 8 of the design).

## Object topology (from the real, unmodified provider and builder)

Read `candidate_packed_provider_r3a2b.py` (`iter_groups`, `_ensure_groups`, `iter_metadata`, `_ensure_metadata`, `_string`) and `sfm_master_authority/projections.py` (`build_normalizer_like_projection`) directly:

- **Retained payload** (`projections.py`): `payload["groups"] = list(provider.iter_groups())` — one dict per group (7 fields: `path_id`, `name`, `full_path`, `parent_path_id`, `parent_path`, `declare_order`, `sibling_rank`). `payload["metadata_by_path"]` — one dict entry per group, each holding a list of that group's metadata dicts (3 fields: `key`, `value`, `source_order`), `metadata_count` dicts total. This is a **complete** copy of the hierarchy+metadata, by explicit design ("complete hierarchy/metadata fidelity").
- **Provider decode cache** (`candidate_packed_provider_r3a2b.py`): `self._groups` — `group_count` `GroupTableRow` namedtuples (40 packed bytes each, plus real namedtuple instance overhead). `self._metadata_rows` — `metadata_count` `MetadataTableRow` namedtuples (16 packed bytes each). `self._string_cache` — a dict keyed by string_id; the **string content itself is shared by reference** with the payload (`_string()` caches and returns the same object), so only the dict-slot/int-key overhead is genuinely extra, never double-counted.
- **Validator scratch** (`candidate_packed_validator_r3a2b.py`, read directly — the file the earlier B2F1E report had not yet inspected for this purpose): `path_id_col`/`local_rank_col`/`fold_id_col` are each an `array.array("I")` sized by `occurrence_count` (exact 4 bytes/element, C-level, not estimated); `fold_key_string_id_col`/`occ_index_start_col`/`occ_index_count_col` are each `array.array("I")` sized by `fold_count`; `rank_seen_by_path` is one `bytearray` per group whose combined length is exactly `occurrence_count` bytes; `string_pool_offsets`/`string_pool_lengths` are each `array.array("I")` sized by `string_count`. **This scratch — allocated and freed entirely inside `validate_packed()`, before the projection builder ever runs, but simultaneously live with the just-read packed buffer — is the reason Family B (high occurrence/string count, tiny payload) peaks higher than Family A despite a near-identical file size and identical group/metadata counts.** This was the missing term in the model's first iteration (see Section 6).

## 2. Pure ResourceShape parser

`b2f1f_resource_shape_estimator.py`'s `parse_resource_shape()`:
- Accepts only a caller-supplied byte prefix (≤ the exact preflight region) plus the artifact's own total byte size — never the complete artifact.
- Checked arithmetic throughout: magic check, format-version whitelist against `fmt.NORMATIVE_ROW_SIZES`, `section_count` must equal the known section set (never trusted larger), `section_directory_offset` must not overlap the fixed header, directory-region end must not exceed `artifact_bytes` **and** must not exceed an explicit small bound (`_MAX_PREFLIGHT_REGION_BYTES = 64 KiB`) independent of artifact scale, every section's `[offset, offset+length)` must lie within `artifact_bytes`, every section's declared `row_size` must match the format's own normative row size (never decode by a file-declared row size), `row_count * row_size` must equal the declared `length`, and section IDs must be complete and non-duplicate.
- Raises `PreflightCorruptOrIncompatible` for any of the above — **never** `PreflightResourceRefusal`. Malformed structure and unsupported versions are corruption/incompatibility, exactly as required; a *valid* structure whose estimate exceeds a gate is the only path to resource refusal.

## 3. Estimator formulas, constants, and rationale

**Model version: `b2f1f-v1`.**

### `estimate_retained(shape)`
```
per_string_bytes = 60 (PyUnicodeObject header, narrow/UCS-2 CPython 2.7) + 2 * avg_chars
avg_chars = string_pool_bytes // string_count

per_group_bytes = 400 (7-key dict overhead)
                + 4*28 (path_id/parent_path_id/declare_order/sibling_rank ints)
                + per_string_bytes            # name
                + per_string_bytes * 4        # full_path (conservative: up to 4x an average
                                               #   string's length, to account for hierarchy
                                               #   depth ancestor-name concatenation, since
                                               #   depth is not itself a header/directory field)
                + per_string_bytes            # parent_path

per_metadata_bytes = 280 (3-key dict overhead) + 28 (source_order int) + 2*per_string_bytes

estimate_retained = group_count * per_group_bytes
                  + metadata_count * per_metadata_bytes
                  + group_count * 80           # metadata_by_path's per-group dict-of-lists bucket
                  + 4096                       # fixed payload scaffolding (wrapper_path, lookup_results)
```

### `estimate_transient(shape, runtime_cap_bytes)`
```
read_bound = runtime_cap_bytes + 1            # B2F1B: Python 2.7 file.read(size) allocates by
                                               #   the REQUESTED size, not the bytes returned

provider_decode_upper =
    group_count * (40 + 120)                  # GroupTableRow packed bytes + namedtuple overhead
  + metadata_count * (16 + 90)                 # MetadataTableRow packed bytes + namedtuple overhead
  + (group_count + metadata_count) * 72        # string_cache dict-slot overhead (content shared
                                                #   by reference with the payload -- not double-counted)

validator_scratch_upper =
    occurrence_count * 13                      # 3x array.array("I") columns (12B) + 1 rank_seen_by_path byte
  + fold_count * 12                            # 3x array.array("I") columns
  + string_count * 8                           # 2x array.array("I") columns (string_pool_offsets/lengths)
  + group_count * 56                           # one bytearray object header per group (rank_seen_by_path)

projection_upper = estimate_retained(shape)

estimate_transient = read_bound + provider_decode_upper + validator_scratch_upper
                    + projection_upper
                    + 2 MiB   (fixed runtime/import overhead margin)
                    + 4 MiB   (explicit measurement/model guard -- see Section 6)
```

Every constant traces to a real structure in the actual builder/provider/validator code (namedtuple/dict/array overheads), not a regression fit. The two fixed margins (2 MiB + 4 MiB) are the only "generously rounded" terms, and their necessity/size was established empirically against the qualification corpus (Section 4), never used to fit per-sample behavior.

## No double-counting

Documented explicitly in the code: the packed buffer (`read_bound`), the provider's raw namedtuple caches (`provider_decode_upper`), the validator's scratch arrays (`validator_scratch_upper`), and the projection payload (`projection_upper`) are the four **simultaneously live** structures at the P5 peak (per R3-B2F1E's phase-isolation finding) — each charged exactly once. String *content* is charged once (via `per_string_bytes`, embedded in `projection_upper`) and referenced, not duplicated, by the string-cache dict-slot term.

## 4. Qualification matrix (official + all 12 A/B/C fixtures)

| Fixture | groups | meta | artifact bytes | actual retained | est. retained | actual transient | est. transient (16 MiB cap) | Admission @ 16 MiB |
|---|---|---|---|---|---|---|---|---|
| official_control | 43 | 54 | 9,506,244 | 69,155 | 78,392 | — | 28,109,532 | **ADMIT** |
| fixtureA_1p0x/1p25x/1p5x | 127 | 252 | 9.5–14.3 M | 271,176 | 736,724 | 21,753,856 (1.5x) | 25,183,813 | **ADMIT** |
| fixtureA_2p0x | 127 | 252 | 18,990,503 | 271,176 | 736,724 | — | 25,608,901 | REFUSE (raw cap) |
| fixtureB_1p0x/1p25x/1p5x | 127 | 126 | 9.5–14.2 M | 194,190 | 205,292 | 27,017,216 (1.5x) | 30,781,913 | **ADMIT** |
| fixtureB_2p0x | 127 | 126 | 18,899,314 | 194,190 | 205,292 | — | 33,261,593 | REFUSE (raw cap) |
| fixtureC_1p0x | 2,729 | 10,912 | 9,568,377 | 10,970,574 | 13,231,328 | — | 42,145,509 | **REFUSE (transient)** — see Section 6 note |
| fixtureC_1p25x | 2,729 | 19,096 | 12,179,112 | 16,732,110 | 22,561,448 | 40,681,472 (offline) / 38,858,752 (real-SFM) | 52,997,877 | **REFUSE (retained)** |
| fixtureC_1p5x | 2,729 | 27,280 | 14,789,847 | 22,493,646 (existing system's own refusal estimate) | 32,720,784 | — | 64,679,461 | **REFUSE (retained)** |
| fixtureC_2p0x | 2,729 | 40,920 | 19,141,077 | 32,109,846 (existing system's own refusal estimate) | 51,151,488 | — | 85,647,245 | REFUSE (raw cap) |

Full row-by-row data: `b2f1f_qualification_matrix.json`. Ground-truth source data (the real, unmodified `acquire_or_reuse_views` path, run offline against every fixture): `b2f1f_ground_truth.json`.

## 5. No underestimation, proven

Every row above satisfies `estimated_retained ≥ actual_authoritative_retained_charge` and `estimated_transient ≥` the best available actual transient evidence (phase-isolation and/or real-SFM). The qualification script's own `ANY UNDERESTIMATE ACROSS CORPUS` check returns **False**, confirmed under both Python 3.10 and real Python 2.7.5.

**Iteration history, reported honestly, not hidden:** the model's first version underestimated Family A (19.69 MiB est. vs. 21.75 MiB actual) and Family B (19.13 MiB est. vs. 27.02 MiB actual) — the validator-scratch term (Section 1) was entirely missing. Adding it (structurally derived from the real validator source, not guessed) closed most of the gap; a final, explicitly-named 4 MiB "measurement/model guard" term closed the small remainder. This is exactly the derive-then-calibrate process the design mandates, not a best-fit regression — every coefficient still traces to a real object/array in the real code.

## Monotonicity and boundary tests — 20/20 PASS (both interpreters)

`b2f1f_monotonicity_boundary_tests.py`, real Python 2.7.5 and Python 3.10, both **20/20 PASS**:
- Increasing `group_count`, `metadata_count`, `occurrence_count`, `fold_count`, `string_pool_bytes` (fixed string count), `string_count` (fixed average string length), and `runtime_cap_bytes` — none reduce the relevant estimate.
- Exact 16 MiB and 32 MiB boundary comparisons use `<=` (a value exactly at the gate admits; one byte over refuses).
- Checked-arithmetic / overflow tests: an oversized directory region against a tiny `artifact_bytes` is rejected; bad magic, unsupported format version, a section exceeding `artifact_bytes`, a duplicate `section_id`, and a `row_count*row_size` mismatch against declared `length` are all rejected as `PreflightCorruptOrIncompatible` — never miscategorized as resource refusal.

**One deliberate, documented modeling choice, not a flaw:** `estimate_retained` derives per-string cost from `string_pool_bytes / string_count` (an average). Holding `string_pool_bytes` fixed while increasing `string_count` *would* reduce the computed average string length — and does reduce `estimate_retained` in that narrow synthetic scenario. This is not a violation of the required monotonicity properties: it is not an independently memory-increasing quantity for the *retained payload* specifically (more distinct strings sharing the same total pool content are, in reality, shorter on average, so the payload's real string-copy cost genuinely would be smaller) — it is the design's *transient* validator-scratch term, not the retained term, that must (and does) scale directly and unconditionally with `string_count`, and it does.

## 6. Known-fixture admission decisions vs. target list

| Fixture | Design's target | This model's decision | Match |
|---|---|---|---|
| official | admit | ADMIT | ✅ |
| A_1p5x | admit | ADMIT | ✅ |
| B_1p5x | admit | ADMIT | ✅ |
| C_1p25x | preflight refuse | REFUSE (retained) | ✅ |
| C_1p5x | preflight refuse | REFUSE (retained) | ✅ |
| C_2p0x | raw-cap refuse if still >16 MiB | REFUSE (raw cap) | ✅ |

**Every required disposition matches exactly.** Neither A nor B is refused by an excessively loose model (Section 6 of the prompt's own concern) — both admit with real headroom under both gates.

**One additional, unrequested finding, reported rather than suppressed:** the model also refuses `fixtureC_1p0x` on the transient gate (42.1 MiB estimated vs. 33.55 MiB gate), even though the *existing* system currently accepts it (its actual retained charge, 10,970,574 bytes, is comfortably under the 16 MiB retained gate — the only check the current system runs). `fixtureC_1p0x` shares C_1p25x's identical `occurrence_count`/`fold_count`/`string_count`/`group_count` (only `metadata_count` is smaller: 10,912 vs. 19,096) — meaning `fixtureC_1p0x`'s validator-scratch and provider-decode costs (which dominate for Family C, independent of metadata) are nearly identical to C_1p25x's already-measured ~38–41 MiB real/offline transient peak. This is very likely a **real, previously undetected transient-gate violation that the current post-hoc, retained-only admission check simply never had the means to observe** — not an artifact of over-conservative modeling. Per the design's own Section 11 ("do not optimize the estimator to save a particular fixture... early resource refusal is correct behavior"), this is reported as a legitimate, safety-relevant discovery, not walked back.

## 7. Same-handle integration design (specification only — not implemented)

The design doc's own Section 2 required ordering is adopted verbatim. The minimal future integration point:

- **Where:** inside `sfm_master_authority.sidecar_contract.validate_selected_artifact()` (and, on the same code path, `Cohort._open_provider_once()`'s call into `BoundedProvider.open_path()`), **after** the candidate file is opened by path but **before** `_read_path_bounded`'s full `f.read(runtime_cap_bytes + 1)` call.
- **API boundary needed:** `BoundedProvider.open_path()` currently does `open(path, "rb")` → immediately `_read_path_bounded` (full read) → `_validate_complete` (full validation) → object construction, all inside one method with no seam. A same-handle-preserving integration would need `_read_path_bounded` (or a new sibling function sharing its already-open `f`) to, immediately after `open(path, "rb")`, read exactly `preflight_region_size(header_bytes)` bytes (a `f.read(360)`-scale call, negligible), call `parse_resource_shape()` + `estimate_retained()`/`estimate_transient()`, and raise `ResourceAdmissionRefusal` (never a fresh `PreflightResourceRefusal` type reaching the caller — see Section 8) **before** `f.seek(0)` and the existing full bounded read proceeds on the **same** open `f`. This satisfies the "same-handle rule" exactly: one `open()`, one file identity, preflight and full read both operate on it.
- **Not proposed:** reading the path once for preflight and reopening it separately for the full read — explicitly rejected by the design and not what this specification describes.
- This remains a specification only. No frozen file was edited to implement it in this task.

## 8. Error-semantic design (specification only)

Demonstrated distinctions, matching the design's Section 7 exactly:
- Malformed header/directory (bad magic, bad section containment, row-size/row-count mismatch, unknown/duplicate section IDs) → `PreflightCorruptOrIncompatible` (mapping, in a real integration, to the existing `SidecarCorrupt`/format-incompatibility path — never `ResourceAdmissionRefusal`, never `SidecarMissing`).
- A structurally valid candidate whose `estimate_retained` exceeds 16,777,216 or whose `estimate_transient` exceeds 33,554,432 → `PreflightResourceRefusal` (mapping, in a real integration, to the existing `errors.ResourceAdmissionRefusal` — the same exception type the B2F selection-layer fix already preserves distinctly; this task does not touch or need to touch that fix, since it remains correct and necessary regardless).
- An unsupported `format_contract_version` → `PreflightCorruptOrIncompatible` (incompatible, never corruption-as-such, never missing) — tested directly (Section 5).
- The diagnostic payload recommended by the design (`reason`, `estimator_model_version`, `artifact_bytes`, `group_count`, `metadata_count`, `estimated_retained_bytes`, `retained_gate_bytes`, `estimated_transient_bytes`, `transient_gate_bytes`, `runtime_cap_bytes`) is exactly what `PreflightResourceRefusal.diagnostics` is designed to carry in a real integration; not yet wired to a live exception path since no integration was implemented.

## 9. Frozen identities — unchanged, confirmed

| File | SHA-256 |
|---|---|
| Canonical Master | `ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93` |
| Official sidecar artifact | `bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b` |
| FINAL R3-A2B validator | `74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f` |
| FINAL R3-A2B provider | `d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677` (unchanged; also re-read for object-topology analysis, never edited) |
| Production Normalizer | `6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e` |
| `sfm_master_authority/selection.py` | `946791edb172dcc295d1cd8c161db1be68a138e255a7ecb313afb2fee9d85abd` |
| `tools/sfm_master_sidecar/format.py` (read for field inventory only) | `b401967db8d07943e9f171058a006c30f0e23eb70a7b43bb5ab950203a3c3259` |

No shared authority implementation was changed. No B2A/B2B regression rerun required.

New test-only files (pure offline, never wired into production):

| File | SHA-256 |
|---|---|
| `b2f1f_resource_shape_estimator.py` | `3c675b4e5651acc2194dd6315a2a85f00355d4d28ba49b2de0cf247c72709465` |
| `b2f1f_qualify_estimator.py` | `4710c141308c7a5dcb46938b8ed3c050bad6e3c9bc5b8ebca468b3acd1350a4d` |
| `b2f1f_monotonicity_boundary_tests.py` | `98ed36905f15e82692ae5e0d899a2bd98dbd0e4ce8ec6daab08a822b3b3e4dd0` |
| `b2f1f_collect_ground_truth.py` | `eba02784c6fc69a5d9544a4d7d42a9090abde1b3ce08d6e3a5e882c99db0e2a8` |

## 10. Deliverables checklist

1. ✅ Exact available ResourceShape fields — Section 1.
2. ✅ Exact derived estimator formulas/constants and rationale — Section 3.
3. ✅ Estimator model version — `b2f1f-v1`.
4. ✅ Qualification matrix — Section 4.
5. ✅ Adversarial/boundary test results — 20/20 PASS, both interpreters.
6. ✅ Proof of no underestimation — Section 5 (`False`, both interpreters).
7. ✅ Known-fixture admission decisions — Section 6 (all 6 match target; 1 additional legitimate finding).
8. ✅ Same-handle integration design — Section 7 (specification only).
9. ✅ Error-semantic design — Section 8.
10. ✅ Unchanged frozen identities — Section 9.
11. ✅ Status: **`B2F1F PRE-ADMISSION ESTIMATOR MODEL QUALIFIED — TEST-ONLY INTEGRATION AUTHORIZED`**

## Hard stop

No frozen provider/broker code was edited. No real-SFM run was made. Run 5 remains not requested. B2C/B2D remain unauthorized. Per the design's own Stage F2→F3 sequencing, the next available step (not begun here) would be a **test-only** provider-branch integration exercising the same-handle design above — still short of any production change or real-SFM run.
