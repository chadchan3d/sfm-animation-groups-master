# -*- coding: utf-8 -*-
"""R2 bounded-repair CANDIDATE. NOT production code. Never imported by
`tools/sfm_master_sidecar/*.py`, never imported by the production Normalizer.
The existing production validator (`reader._validate_and_decode`) is left
completely untouched and remains the comparison oracle -- this module is an
independent, parallel implementation, not a patch to it.

Performs the EXACT SAME Section 20 (A-J) complete validation as
`reader._validate_and_decode`, over the SAME single immutable buffer, but
with the memory-representation repair specified in
SFM_CGN_R2_Bounded_Repair_Spec_Packed_Validation_2026-09-14.md: no full
Python list is ever built for the source's decoded strings, occurrence
rows, fold rows, or either index. Every row is unpacked one at a time,
directly from the original buffer at an absolute offset (never a pre-sliced
whole-section blob), checked immediately, and discarded. Coverage/partition
proofs use `bytearray` scratch sized by occurrence_count instead of Python
lists of bools/ints. Groups/CHILD-ID-INDEX/metadata (43/42/54 rows for the
official Master) are still fully materialized in plain Python lists --
explicitly allowed by the spec (Section 3.4): they are small, fixed by
group_count/metadata_row_count (never by occurrence_count or fold_count),
and are exactly the structures the existing detached-view/hierarchy
consumer contract already expects a validator to hand back on request.

This function does NOT retain or return the fully-decoded graph -- like the
production validator, its caller decides what (if anything) to keep. It
returns exactly `(header, directory)`, matching the exact contract of
`bounded_provider.py`'s own `_validate_complete(buf)` (see
`candidate_packed_provider.py`, which is a byte-for-byte structural copy of
`bounded_provider.py` except for that one function).

Complete validation is mandatory here exactly as in the production
validator: every row in every section is visited and checked, regardless of
whether it belongs to any later-requested fold family. A corrupt row
anywhere in the artifact still invalidates the whole authority.
"""

import array
import hashlib

from sfm_master_sidecar import format as fmt
from sfm_master_sidecar import reader as prod_reader

# Reuse the exact same exception class the production validator raises, so
# every existing `except AuthorityUnavailable` caller (bounded_provider.py,
# the Normalizer's own consumer code, every existing test) behaves
# identically regardless of which validator produced the rejection.
AuthorityUnavailable = prod_reader.AuthorityUnavailable


def _fail(message):
    raise AuthorityUnavailable(message)


def _check_bounds(offset, length, container_length, what):
    if offset < 0 or length < 0 or offset + length > container_length:
        _fail("%s out of bounds (offset=%r length=%r container_length=%r)" % (
            what, offset, length, container_length,
        ))


# Second contained (remaining-hotpath) timing correction, per
# SFM_CGN_R2_R1D_Remaining_Hotpath_Optimization_ClaudeCode_Prompt_2026-09-14.md,
# Optimization A: `format.ascii_fold_bytes` (frozen production file, never
# edited) loops byte-by-byte in pure Python. This is a candidate-local,
# independent, C-level equivalent: a precomputed 256-byte translation table
# (0x41-0x5A -> +0x20, every other byte unchanged) applied via
# `bytes.translate()` -- a single C call instead of a Python per-byte loop.
# Exhaustive byte-for-byte equivalence against `fmt.ascii_fold_bytes` (all
# 256 byte values, plus mixed-valid-UTF-8 strings) is proven in
# candidate_offline_qualification.py, not merely asserted here. No locale
# dependence, no Unicode .lower()/casefold -- table-driven byte
# substitution only.
_ASCII_FOLD_TRANSLATE_TABLE = bytes(bytearray(
    (b + 0x20) if 0x41 <= b <= 0x5A else b
    for b in range(256)
))


def _ascii_fold_bytes_fast(data):
    return data.translate(_ASCII_FOLD_TRANSLATE_TABLE)


def _compute_embedded_integrity_digest_streaming(buf, digest_field_offset):
    """Byte-for-byte equivalent to `format.compute_embedded_integrity_digest`
    (same three logical pieces: bytes before the digest field, canonical
    zero bytes for the field itself, bytes after the field -- SHA-256 is a
    pure streaming/Merkle-Damgard hash, so `h.update(a); h.update(b)` is
    defined to produce an identical digest to `h.update(a + b)` for any
    split point), but WITHOUT the original's `bytearray(buf)` + `bytes(tmp)`
    double whole-buffer copy. `memoryview` slices of `buf` are views, not
    copies; `hashlib`'s `.update()` accepts any buffer-protocol object
    directly. Equivalence is asserted by `candidate_offline_qualification.py`
    against the real artifact, not merely claimed here."""
    mv = memoryview(buf)
    h = hashlib.sha256()
    h.update(mv[:digest_field_offset])
    h.update(b"\x00" * fmt.SHA256_DIGEST_SIZE)
    h.update(mv[digest_field_offset + fmt.SHA256_DIGEST_SIZE:])
    return h.digest()


def validate_packed(buf):
    """Complete Section 20 (A-J) validation, packed representation. Raises
    `AuthorityUnavailable` on the first violation found (same fail-fast
    contract as the production validator); never returns a partially-valid
    result. Returns `(header, directory)` only -- exactly what
    `bounded_provider.py`'s existing `_validate_complete(buf)` already
    extracts from the production validator's full `_Backing` today (see
    that module's own docstring); this function just never builds the rest
    of the graph in the first place."""

    total_len = len(buf)

    # --- A. Header / Directory / Protected Regions. ---
    if total_len < fmt.HEADER_SIZE:
        _fail("file is shorter than the fixed HEADER size (%d < %d) -- truncated header" % (
            total_len, fmt.HEADER_SIZE,
        ))
    try:
        header = fmt.unpack_header(buf, 0)
    except Exception as exc:
        _fail("failed to unpack HEADER: %r" % (exc,))

    if header.magic != fmt.MAGIC:
        _fail("magic mismatch: expected %r, found %r" % (fmt.MAGIC, header.magic))
    if header.format_contract_version not in fmt.NORMATIVE_ROW_SIZES:
        _fail("unsupported format_contract_version %r" % (header.format_contract_version,))
    if header.authority_semantics_version != fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL:
        _fail("unsupported authority_semantics_version %r" % (header.authority_semantics_version,))
    if header.payload_length != total_len:
        _fail("payload_length (%d) does not match actual file size (%d)" % (
            header.payload_length, total_len,
        ))

    # Same ordering as production: digest checked immediately after minimal
    # header sanity, before any SECTION DIRECTORY row is decoded/checked.
    digest_off = fmt.embedded_integrity_digest_offset()
    recomputed = _compute_embedded_integrity_digest_streaming(buf, digest_off)
    if recomputed != header.embedded_integrity_digest:
        _fail("embedded_integrity_digest mismatch -- file content does not match its own recorded digest")

    normative_row_sizes = fmt.NORMATIVE_ROW_SIZES[header.format_contract_version]

    protected = [(0, fmt.HEADER_SIZE, "HEADER")]

    dir_off = header.section_directory_offset
    dir_row_count = header.section_count
    _check_bounds(dir_off, dir_row_count * fmt.DIRECTORY_ROW_SIZE, total_len, "SECTION DIRECTORY")
    protected.append((dir_off, dir_row_count * fmt.DIRECTORY_ROW_SIZE, "SECTION DIRECTORY"))

    expected_section_ids = set(fmt.SECTION_ORDER)
    if dir_row_count != len(expected_section_ids):
        _fail("section_count %d does not match the expected section set size %d" % (
            dir_row_count, len(expected_section_ids),
        ))

    directory = {}
    regions = list(protected)
    for i in range(dir_row_count):
        try:
            row = fmt.unpack_directory_row(buf, dir_off + i * fmt.DIRECTORY_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack SECTION DIRECTORY row %d: %r" % (i, exc))
        if row.section_id not in expected_section_ids:
            _fail("SECTION DIRECTORY row %d has unrecognized section_id %r" % (i, row.section_id))
        if row.section_id in directory:
            _fail("SECTION DIRECTORY has a duplicate section_id %r" % (row.section_id,))
        directory[row.section_id] = row
        _check_bounds(row.offset, row.length, total_len, "section %s" % fmt.SECTION_NAMES[row.section_id])
        if row.row_count * row.row_size != row.length:
            _fail(
                "section %s: row_count*row_size (%d*%d) != declared length (%d)" % (
                    fmt.SECTION_NAMES[row.section_id], row.row_count, row.row_size, row.length,
                )
            )
        normative_size = normative_row_sizes[row.section_id]
        if row.row_size != normative_size:
            _fail(
                "section %s: file-declared row_size %d does not match this reader's normative "
                "row_size %d for format_contract_version %r -- the reader never decodes using a "
                "file-supplied width" % (
                    fmt.SECTION_NAMES[row.section_id], row.row_size, normative_size,
                    header.format_contract_version,
                )
            )
        regions.append((row.offset, row.length, fmt.SECTION_NAMES[row.section_id]))

    if set(directory.keys()) != expected_section_ids:
        _fail("SECTION DIRECTORY does not contain the exact expected section set")

    regions.sort(key=lambda r: r[0])
    for i in range(1, len(regions)):
        prev_off, prev_len, prev_name = regions[i - 1]
        cur_off, cur_len, cur_name = regions[i]
        if cur_off < prev_off + prev_len:
            _fail("section/region overlap detected: %s [%d,%d) overlaps %s [%d,%d)" % (
                prev_name, prev_off, prev_off + prev_len, cur_name, cur_off, cur_off + cur_len,
            ))

    string_count = directory[fmt.SECTION_STRING_TABLE].row_count
    group_count = directory[fmt.SECTION_GROUP_TABLE].row_count
    occurrence_count = directory[fmt.SECTION_OCCURRENCE_TABLE].row_count
    fold_count = directory[fmt.SECTION_FOLD_TABLE].row_count
    if string_count > fmt.LIMIT_DISTINCT_POOL_STRINGS:
        _fail("declared string count %d exceeds resource limit" % string_count)
    if group_count > fmt.LIMIT_GROUP_COUNT:
        _fail("declared group count %d exceeds resource limit" % group_count)
    if occurrence_count > fmt.LIMIT_OCCURRENCE_COUNT:
        _fail("declared occurrence count %d exceeds resource limit" % occurrence_count)
    if fold_count > fmt.LIMIT_FOLD_COUNT:
        _fail("declared fold count %d exceeds resource limit" % fold_count)

    string_table_off = directory[fmt.SECTION_STRING_TABLE].offset
    pool_off = directory[fmt.SECTION_STRING_POOL].offset
    pool_len = directory[fmt.SECTION_STRING_POOL].length
    if pool_len > fmt.LIMIT_STRING_POOL_TOTAL_BYTES:
        _fail("STRING POOL byte size %d exceeds the resource limit %d" % (
            pool_len, fmt.LIMIT_STRING_POOL_TOTAL_BYTES,
        ))

    # --- B. String Table + STRING POOL: every row's bounds/length/UTF-8
    #     validity is proven for ALL string_count rows, EXACTLY ONCE each
    #     (contained timing correction, Approach A: "one-pass UTF-8
    #     validation, then raw-byte semantics" --
    #     SFM_CGN_R2_PackedValidation_Timing_Correction_ClaudeCode_Prompt_2026-09-14.md).
    #     Profiling (candidate_offline_qualification.py's timing-correction
    #     measurement) proved every later phase (C/H/F below) re-decoded the
    #     SAME string_id's text again -- 221,555 of 221,565 string IDs were
    #     touched more than once, purely to redo a UTF-8 validity check
    #     already proven here. No downstream check in this validator ever
    #     needs DECODED TEXT: full-path uniqueness, fold-key ordering, and
    #     ascii-fold(literal)==fold-key are all byte-level operations (see
    #     the semantic-equivalence argument in the offline qualification
    #     report). So B now ALSO records each validated string's
    #     (pool_offset, length) into compact `array.array('I', ...)`
    #     arrays -- raw C unsigned ints, not Python int/tuple objects, not
    #     decoded strings -- so every later phase can fetch that string's
    #     raw (already-proven-valid) UTF-8 bytes via `string_bytes(id)`
    #     without re-unpacking the STRING TABLE row, re-checking bounds, or
    #     re-decoding. These two arrays are validation-local (like
    #     `groups`/`child_id_index`/`metadata_rows` below) -- 2 * 4 *
    #     string_count bytes (~1.7 MiB for the official Master), discarded
    #     the instant this function returns; not a decoded-string graph. ---
    # Remaining-hotpath correction, Optimization C: `fmt.unpack_string_table_row`
    # wraps a 2-field struct.unpack_from in a namedtuple constructor
    # (measured __new__ overhead across 221,565 calls). Calling the
    # module's own public, pre-built `STRING_TABLE_ROW_STRUCT.unpack_from`
    # directly returns a plain 2-tuple -- identical decoded values, no
    # namedtuple construction, no `fmt.unpack_string_table_row` wrapper
    # call. No check performed by the wrapper is skipped: the wrapper
    # itself never validated anything (only decoded), and every check
    # below is unchanged.
    string_pool_offsets = array.array("I", [0]) * string_count
    string_pool_lengths = array.array("I", [0]) * string_count
    _unpack_string_row = fmt.STRING_TABLE_ROW_STRUCT.unpack_from
    for i in range(string_count):
        st_off = string_table_off + i * fmt.STRING_TABLE_ROW_SIZE
        try:
            s_offset, s_length = _unpack_string_row(buf, st_off)
        except Exception as exc:
            _fail("failed to unpack STRING TABLE row %d: %r" % (i, exc))
        _check_bounds(s_offset, s_length, pool_len, "STRING TABLE row %d" % i)
        if s_length > fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH:
            _fail("STRING TABLE row %d declares length %d exceeding the single-string resource limit %d" % (
                i, s_length, fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH,
            ))
        raw = buf[pool_off + s_offset: pool_off + s_offset + s_length]
        try:
            raw.decode("utf-8")  # validate only; the decoded text itself is never needed again
        except UnicodeDecodeError as exc:
            _fail("STRING TABLE row %d is not valid UTF-8: %r" % (i, exc))
        string_pool_offsets[i] = s_offset
        string_pool_lengths[i] = s_length

    def string_bytes(string_id, what):
        """Fast post-B accessor: this string_id's raw bytes, already proven
        valid UTF-8 by the B-phase pass above -- no STRING TABLE row
        unpack, no bounds re-check, no re-decode. `what` is accepted only
        for a clear error message if `string_id` is itself out of range
        (a genuine corruption the caller must still catch)."""
        if string_id < 0 or string_id >= string_count:
            _fail("string_id %d out of bounds (%s)" % (string_id, what))
        offset = string_pool_offsets[string_id]
        length = string_pool_lengths[string_id]
        return buf[pool_off + offset: pool_off + offset + length]

    # --- C. Group Table + D. CHILD-ID INDEX + E. Metadata Table: fully
    #     materialized (Section 3.4 of the repair spec explicitly allows
    #     this -- bounded by group_count/metadata_row_count, 43/54 for the
    #     official Master, never by occurrence_count/fold_count). This is a
    #     VALIDATION-LOCAL structure only: it is not returned to the caller
    #     and is discarded when this function returns (the caller,
    #     `candidate_packed_provider.BoundedProvider`, re-derives it itself,
    #     lazily, exactly as it already does today for the production
    #     validator's output). ---
    group_table_off = directory[fmt.SECTION_GROUP_TABLE].offset
    groups = []
    for i in range(group_count):
        try:
            row = fmt.unpack_group_table_row(buf, group_table_off + i * fmt.GROUP_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack GROUP TABLE row %d: %r" % (i, exc))
        if row.name_string_id >= string_count:
            _fail("GROUP TABLE row %d: name_string_id %d out of bounds" % (i, row.name_string_id))
        if row.parent_path_id != fmt.ROOT_SENTINEL and row.parent_path_id >= i:
            _fail(
                "GROUP TABLE row %d: parent_path_id %d is not ROOT_SENTINEL and is not < %d "
                "(anti-cycle violation)" % (i, row.parent_path_id, i)
            )
        groups.append(row)

    parentless = [i for i, g in enumerate(groups) if g.parent_path_id == fmt.ROOT_SENTINEL]
    if len(parentless) != 1:
        _fail(
            "GROUP TABLE must have exactly one row with parent_path_id == ROOT_SENTINEL; found %d" % (
                len(parentless),
            )
        )

    declare_orders = [g.declare_order for g in groups]
    if len(set(declare_orders)) != len(declare_orders):
        _fail("GROUP TABLE declare_order values are not globally unique")

    # Path-identity uniqueness needs only BYTE equality (see the timing
    # correction's semantic-equivalence argument: for two independently
    # UTF-8-validated byte strings, byte-equality == decoded-text-equality),
    # so `full_paths` holds raw bytes, never decoded text -- only 43
    # entries either way, but consistent with the rest of this repair.
    full_paths = [None] * group_count
    for i in range(group_count):
        row = groups[i]
        name = string_bytes(row.name_string_id, "group %d name" % i)
        if row.parent_path_id == fmt.ROOT_SENTINEL:
            full_paths[i] = name
        else:
            full_paths[i] = full_paths[row.parent_path_id] + b"/" + name
    if len(set(full_paths)) != len(full_paths):
        _fail("two or more GROUP TABLE rows reconstruct to the same full path")

    child_id_index_off = directory[fmt.SECTION_CHILD_ID_INDEX].offset
    child_index_row_count = directory[fmt.SECTION_CHILD_ID_INDEX].row_count
    expected_child_rows = group_count - len(parentless)
    if child_index_row_count != expected_child_rows:
        _fail(
            "CHILD-ID INDEX row_count %d does not match group_count - parentless_group_count (%d)" % (
                child_index_row_count, expected_child_rows,
            )
        )
    child_id_index = [
        fmt.unpack_child_id_index_row(buf, child_id_index_off + i * fmt.CHILD_ID_INDEX_ROW_SIZE)
        for i in range(child_index_row_count)
    ]

    child_covered = [0] * group_count
    for i, g in enumerate(groups):
        start, count = g.child_index_start, g.child_count
        _check_bounds(start, count, child_index_row_count, "GROUP TABLE row %d child slice" % i)
        prev_sibling_rank = -1
        prev_declare_order = -1
        for k in range(count):
            child_id = child_id_index[start + k]
            if child_id >= group_count:
                _fail("CHILD-ID INDEX entry %d out of bounds (group %d's slice)" % (child_id, i))
            child_covered[child_id] += 1
            child_row = groups[child_id]
            if child_row.parent_path_id != i:
                _fail(
                    "CHILD-ID INDEX entry %d claims parent %d, but that group's own parent_path_id is %d "
                    "(ownership disagreement)" % (child_id, i, child_row.parent_path_id)
                )
            if child_row.sibling_rank != k:
                _fail(
                    "CHILD-ID INDEX slice for group %d: entry at position %d has sibling_rank %d "
                    "(expected dense 0..child_count-1)" % (i, k, child_row.sibling_rank)
                )
            if child_row.sibling_rank <= prev_sibling_rank:
                _fail("CHILD-ID INDEX slice for group %d: sibling_rank does not strictly increase" % i)
            if child_row.declare_order <= prev_declare_order:
                _fail(
                    "CHILD-ID INDEX slice for group %d: declare_order does not increase monotonically "
                    "with sibling_rank" % i
                )
            prev_sibling_rank = child_row.sibling_rank
            prev_declare_order = child_row.declare_order

    for i in range(group_count):
        is_root = groups[i].parent_path_id == fmt.ROOT_SENTINEL
        if is_root and child_covered[i] != 0:
            _fail("group %d is parentless but appears in a CHILD-ID INDEX slice" % i)
        if not is_root and child_covered[i] != 1:
            _fail(
                "group %d is non-root but appears in CHILD-ID INDEX slices %d times (expected exactly 1)" % (
                    i, child_covered[i],
                )
            )

    metadata_table_off = directory[fmt.SECTION_METADATA_TABLE].offset
    metadata_row_count = directory[fmt.SECTION_METADATA_TABLE].row_count
    for g in groups:
        if g.metadata_count > fmt.LIMIT_METADATA_ROWS_PER_GROUP:
            _fail("a GROUP TABLE row declares metadata_count %d exceeding the resource limit" % g.metadata_count)
    metadata_rows = []
    for i in range(metadata_row_count):
        try:
            row = fmt.unpack_metadata_table_row(buf, metadata_table_off + i * fmt.METADATA_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack METADATA TABLE row %d: %r" % (i, exc))
        if row.key_string_id >= string_count or row.value_string_id >= string_count:
            _fail("METADATA TABLE row %d references an out-of-bounds string id" % i)
        metadata_rows.append(row)

    meta_covered = bytearray(metadata_row_count)
    for i, g in enumerate(groups):
        start, count = g.metadata_start, g.metadata_count
        _check_bounds(start, count, metadata_row_count, "GROUP TABLE row %d metadata slice" % i)
        for k in range(count):
            idx = start + k
            if meta_covered[idx]:
                _fail("METADATA TABLE row %d is claimed by more than one group's slice" % idx)
            meta_covered[idx] = 1
            mrow = metadata_rows[idx]
            if mrow.path_id != i:
                _fail(
                    "METADATA TABLE row %d claimed by group %d's slice, but its own path_id is %d" % (
                        idx, i, mrow.path_id,
                    )
                )
            if mrow.source_order != k:
                _fail(
                    "METADATA TABLE slice for group %d: entry at position %d has source_order %d "
                    "(expected dense 0..count-1)" % (i, k, mrow.source_order)
                )
    if 0 in meta_covered:
        _fail("METADATA TABLE has rows not covered by any group's declared slice (gap)")

    # --- F. Occurrence Table + H. Fold Table (decoded once, up front, as in
    #     production, so F's per-occurrence fold check can reference it) +
    #     F continued (exhaustive per-occurrence fold consistency) --
    #     PACKED: no `occurrence_rows`/`fold_rows` Python list is ever built.
    #     `rank_seen_by_path[p]` is a bytearray sized to that group's OWN
    #     declared occ_by_group_count (never occurrence_count-per-group as a
    #     Python int list) -- total bytes across every group sum to
    #     occurrence_count, not occurrence_count Python int objects.
    #
    #     Row-unpack timing correction (second contained correction, per
    #     SFM_CGN_R2_RowUnpack_Timing_Correction_ClaudeCode_Prompt_2026-09-14.md):
    #     profiling proved every fold row was unpacked ~3.0x (H, F, I) and
    #     every occurrence row ~3.0x (F, G, I) -- the SAME packed bytes
    #     re-`struct.unpack`-decoded on every later pass that needed one of
    #     its scalar fields. H's own pass below is the FIRST and ONLY place
    #     each fold row is unpacked: it now ALSO records the 3 scalar
    #     fields F/I need later (fold_key_string_id, occ_index_start,
    #     occ_index_count) into `array.array("I", ...)` columns -- raw C
    #     uint32s, not row objects/tuples/dicts. F's own pass below is the
    #     FIRST and ONLY place each occurrence row is unpacked: it records
    #     the 3 scalar fields G/I need later (path_id, local_rank, fold_id)
    #     the same way (literal_string_id is consumed entirely within F's
    #     own iteration and is never reused, so it is NOT cached). Check
    #     order is UNCHANGED -- H then F then G then I, exactly as before;
    #     G/I below just read these columns instead of re-unpacking. ---
    occurrence_table_off = directory[fmt.SECTION_OCCURRENCE_TABLE].offset
    fold_table_off = directory[fmt.SECTION_FOLD_TABLE].offset

    fold_key_string_id_col = array.array("I", [0]) * fold_count
    occ_index_start_col = array.array("I", [0]) * fold_count
    occ_index_count_col = array.array("I", [0]) * fold_count

    # Remaining-hotpath correction, Optimization C, applied to the two
    # highest-remaining-volume row types (fold: 124,728 rows; occurrence:
    # 128,555 rows) -- same technique as the STRING TABLE above: call the
    # module's own public `FOLD_TABLE_ROW_STRUCT`/`OCCURRENCE_TABLE_ROW_STRUCT`
    # .unpack_from directly for plain tuples, skipping the
    # fmt.unpack_fold_table_row/unpack_occurrence_table_row namedtuple
    # wrappers. Safe because `frow`/`orow` are never used as objects beyond
    # this same iteration (nothing downstream of H or F ever holds the row
    # object itself -- only the scalar columns extracted from it, exactly
    # as before). GROUP TABLE rows are deliberately NOT converted: only 43
    # exist, `groups` is read via attribute access throughout C/D/E/G below,
    # and profiling showed group-row unpacking at ~0.000s -- not worth it.
    _unpack_fold_row = fmt.FOLD_TABLE_ROW_STRUCT.unpack_from
    prev_fold_key_bytes = None
    for i in range(fold_count):
        try:
            f_key_id, f_idx_start, f_idx_count = _unpack_fold_row(buf, fold_table_off + i * fmt.FOLD_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack FOLD TABLE row %d: %r" % (i, exc))
        if f_key_id >= string_count:
            _fail("FOLD TABLE row %d: fold_key_string_id out of bounds" % i)
        if f_idx_count < 1:
            _fail("FOLD TABLE row %d has occ_index_count %d (< 1 is corruption)" % (i, f_idx_count))
        key_bytes = string_bytes(f_key_id, "fold %d key" % i)
        if prev_fold_key_bytes is not None and key_bytes <= prev_fold_key_bytes:
            _fail("FOLD TABLE is not in strict ascending folded-key-byte order at row %d" % i)
        prev_fold_key_bytes = key_bytes
        fold_key_string_id_col[i] = f_key_id
        occ_index_start_col[i] = f_idx_start
        occ_index_count_col[i] = f_idx_count

    path_id_col = array.array("I", [0]) * occurrence_count
    local_rank_col = array.array("I", [0]) * occurrence_count
    fold_id_col = array.array("I", [0]) * occurrence_count

    _unpack_occ_row = fmt.OCCURRENCE_TABLE_ROW_STRUCT.unpack_from
    rank_seen_by_path = [bytearray(g.occ_by_group_count) for g in groups]
    for i in range(occurrence_count):
        try:
            o_literal_id, o_path_id, o_local_rank, o_fold_id = _unpack_occ_row(
                buf, occurrence_table_off + i * fmt.OCCURRENCE_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack OCCURRENCE TABLE row %d: %r" % (i, exc))
        if o_literal_id >= string_count:
            _fail("OCCURRENCE TABLE row %d: literal_string_id out of bounds" % i)
        if o_path_id >= group_count:
            _fail("OCCURRENCE TABLE row %d: path_id out of bounds" % i)
        if o_fold_id >= fold_count:
            _fail("OCCURRENCE TABLE row %d: fold_id out of bounds" % i)

        literal_bytes = string_bytes(o_literal_id, "occurrence %d literal" % i)
        expected_fold_bytes = _ascii_fold_bytes_fast(literal_bytes)
        actual_fold_bytes = string_bytes(fold_key_string_id_col[o_fold_id], "occurrence %d's fold key" % i)
        if expected_fold_bytes != actual_fold_bytes:
            _fail(
                "OCCURRENCE TABLE row %d: ascii_fold(literal) does not match its own fold_id's "
                "folded-key bytes" % i
            )

        p = o_path_id
        r = o_local_rank
        scratch = rank_seen_by_path[p]
        if r < 0 or r >= len(scratch):
            _fail(
                "group %d's declared occ_by_group_count (%d) does not match its actual occurrence "
                "count (local_rank %d out of range for occurrence %d)" % (p, len(scratch), r, i)
            )
        if scratch[r]:
            _fail("occurrences owned by group %d do not form a dense 0..count-1 local_rank run "
                  "(local_rank %d seen twice)" % (p, r))
        scratch[r] = 1
        path_id_col[i] = p
        local_rank_col[i] = r
        fold_id_col[i] = o_fold_id

    for p in range(group_count):
        scratch = rank_seen_by_path[p]
        if scratch and 0 in scratch:
            _fail("group %d declares occ_by_group_count %d but owns zero OCCURRENCE TABLE rows "
                  "(or a gap in its local_rank run)" % (p, len(scratch)))

    # --- G. Occurrence-by-Group Index: complete partition of 0..N-1, using a
    #     `bytearray(occurrence_count)` coverage scratch instead of a Python
    #     `[False] * occurrence_count` list. ---
    occ_by_group_off = directory[fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX].offset
    occ_by_group_row_count = directory[fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX].row_count
    if occ_by_group_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-GROUP INDEX row_count %d != occurrence_count %d" % (
            occ_by_group_row_count, occurrence_count,
        ))
    seen_by_group = bytearray(occurrence_count)
    for i, g in enumerate(groups):
        start, count = g.occ_by_group_start, g.occ_by_group_count
        _check_bounds(start, count, occ_by_group_row_count, "GROUP TABLE row %d occ_by_group slice" % i)
        prev_local_rank = -1
        for k in range(count):
            global_rank = fmt.unpack_occ_by_group_index_row(buf, occ_by_group_off + (start + k) * fmt.OCC_BY_GROUP_INDEX_ROW_SIZE)
            if global_rank >= occurrence_count:
                _fail("OCCURRENCE-BY-GROUP INDEX entry %d out of bounds" % global_rank)
            if seen_by_group[global_rank]:
                _fail("OCCURRENCE-BY-GROUP INDEX: global_rank %d claimed by more than one group's slice" % global_rank)
            seen_by_group[global_rank] = 1
            occ_path_id = path_id_col[global_rank]
            occ_local_rank = local_rank_col[global_rank]
            if occ_path_id != i:
                _fail(
                    "OCCURRENCE-BY-GROUP INDEX: entry %d claimed by group %d's slice, but its own "
                    "path_id is %d" % (global_rank, i, occ_path_id)
                )
            if occ_local_rank <= prev_local_rank:
                _fail("OCCURRENCE-BY-GROUP INDEX slice for group %d: local_rank does not strictly increase" % i)
            prev_local_rank = occ_local_rank
    if 0 in seen_by_group:
        _fail("OCCURRENCE-BY-GROUP INDEX does not cover every occurrence (gap)")

    # --- I. Occurrence-by-Fold Index: same bytearray-coverage technique.
    #     `total_fold_occ_count` is a running scalar accumulated in this
    #     same loop -- no separate `fold_occ_counts = [0] * fold_count`
    #     Python list is built merely to sum it once in J below. ---
    occ_by_fold_off = directory[fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX].offset
    occ_by_fold_row_count = directory[fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX].row_count
    if occ_by_fold_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-FOLD INDEX row_count %d != occurrence_count %d" % (
            occ_by_fold_row_count, occurrence_count,
        ))
    seen_by_fold = bytearray(occurrence_count)
    total_fold_occ_count = 0
    for fid in range(fold_count):
        start = occ_index_start_col[fid]
        count = occ_index_count_col[fid]
        _check_bounds(start, count, occ_by_fold_row_count, "FOLD TABLE row %d occ index slice" % fid)
        for k in range(count):
            global_rank = fmt.unpack_occ_by_fold_index_row(buf, occ_by_fold_off + (start + k) * fmt.OCC_BY_FOLD_INDEX_ROW_SIZE)
            if global_rank >= occurrence_count:
                _fail("OCCURRENCE-BY-FOLD INDEX entry %d out of bounds" % global_rank)
            if seen_by_fold[global_rank]:
                _fail("OCCURRENCE-BY-FOLD INDEX: global_rank %d claimed by more than one fold's slice" % global_rank)
            seen_by_fold[global_rank] = 1
            occ_fold_id = fold_id_col[global_rank]
            if occ_fold_id != fid:
                _fail(
                    "OCCURRENCE-BY-FOLD INDEX: entry %d claimed by fold %d's slice, but its own "
                    "fold_id is %d" % (global_rank, fid, occ_fold_id)
                )
        total_fold_occ_count += count
    if 0 in seen_by_fold:
        _fail("OCCURRENCE-BY-FOLD INDEX does not cover every occurrence (gap)")

    # --- J. Cardinality cross-checks (Section 16). groups/child_id_index
    #     are the only full Python lists retained during validation, and
    #     both are bounded by group_count (43), never occurrence_count. ---
    if sum(g.child_count for g in groups) != child_index_row_count:
        _fail("sum of GROUP TABLE child_count values does not match CHILD-ID INDEX row_count")
    if sum(g.metadata_count for g in groups) != metadata_row_count:
        _fail("sum of GROUP TABLE metadata_count values does not match METADATA TABLE row_count")
    if sum(g.occ_by_group_count for g in groups) != occurrence_count:
        _fail("sum of GROUP TABLE occ_by_group_count values does not match OCCURRENCE TABLE row_count")
    if total_fold_occ_count != occurrence_count:
        _fail("sum of FOLD TABLE occ_index_count values does not match OCCURRENCE TABLE row_count")

    # No `_Backing`, no strings/occurrence_rows/fold_rows/index lists are
    # returned or retained past this point -- `groups`/`child_id_index`/
    # `metadata_rows`/`rank_seen_by_path`/`seen_by_group`/`seen_by_fold` all
    # go out of scope here and are reclaimed by ordinary refcounting the
    # instant this function returns.
    return header, directory
