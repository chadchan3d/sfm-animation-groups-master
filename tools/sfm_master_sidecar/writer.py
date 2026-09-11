# -*- coding: utf-8 -*-
"""Deterministic writer/compiler: MasterParseResult (+ fold families) -> the
experimental packed sidecar bytes. Python 3 ONLY.

Consumes `tools.sfm_master_core.MasterParseResult` / `build_fold_families`
directly -- it does not reimplement parsing, tokenization, ASCII folding, or
fold-family construction. Its own job is limited to: the compiler-level
structural-eligibility gate (final spec Section 3, distinct from
`sfm_master_core`'s own broader `.ok` acceptance), deterministic
serialization into the Section 5 layout, and explicit field-representability
/ resource-limit checks (final spec Sections 17-18) -- raising rather than
masking or truncating any out-of-range value.

Phase B2B scope: no CLI, no manifest, no publisher, no official-Master
sidecar generation lives here -- see
SFM_MASTER_SIDECAR_PHASE_B2B_FORMAT_WRITER_READER_AUDIT.md for what this
phase actually qualifies (round-trip against the small B2A fixture corpus
only).
"""

import os
import sys

_TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import sfm_master_core as core  # noqa: E402

from . import format as fmt  # noqa: E402


class SidecarProfileError(fmt.SidecarFormatError):
    """Compiler-level structural-eligibility refusal (final spec Section 3).
    Never raised by `sfm_master_core` itself and never changes its
    behavior -- this is generic sidecar-compatibility policy layered above
    it."""


class SidecarFieldOverflowError(fmt.SidecarFormatError):
    """A derived value does not fit its normative field width, or exceeds a
    Section 18 resource limit. Always raised, never masked or truncated."""


def _check_u32(value, what):
    if value < 0 or value > fmt.U32_MAX:
        raise SidecarFieldOverflowError(
            "%s value %r does not fit in u32 (field-representability check, final spec Section 17)"
            % (what, value)
        )
    return value


def _check_u64(value, what):
    if value < 0 or value > fmt.U64_MAX:
        raise SidecarFieldOverflowError(
            "%s value %r does not fit in u64 (field-representability check, final spec Section 17)"
            % (what, value)
        )
    return value


def _check_limit(value, limit, what):
    if value > limit:
        raise SidecarFieldOverflowError(
            "%s value %r exceeds Section 18 resource limit %r -- refused before any buffer "
            "was allocated for it" % (what, value, limit)
        )
    return value


def check_compatibility_profile(result):
    """Final spec Section 3's exact refusal sequence. Raises
    `SidecarProfileError` with a message naming the specific reason; returns
    the sole parentless `Group` on success. Never mutates or reinterprets
    `sfm_master_core`'s own result."""
    if not result.ok:
        raise SidecarProfileError("source is not grammatically valid (MasterParseResult.ok is False)")
    parentless = [g for g in result.groups if g.parent_path is None]
    if len(parentless) != 1:
        raise SidecarProfileError(
            "source has %d parentless group(s); the initial sidecar compatibility profile requires "
            "exactly one document/wrapper group" % len(parentless)
        )
    return parentless[0]


class _StringPoolBuilder:
    """Dedup-by-exact-byte-string pool, string_id assigned in strict
    first-seen order under a fully deterministic traversal (never dict/set
    iteration order) -- see `compile_sidecar`'s call sequence for the exact
    traversal this builder is fed in."""

    def __init__(self):
        self._pool = bytearray()
        self._ids = {}
        self.rows = []  # StringTableRow, index == string_id

    def intern(self, s):
        sid = self._ids.get(s)
        if sid is not None:
            return sid
        b = s.encode("utf-8")
        _check_limit(len(b), fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH, "single string byte length")
        offset = len(self._pool)
        _check_u32(offset, "string pool offset")
        _check_u32(len(b), "string length")
        self._pool.extend(b)
        sid = len(self.rows)
        _check_u32(sid, "string_id")
        _check_limit(sid + 1, fmt.LIMIT_DISTINCT_POOL_STRINGS, "distinct pool string count")
        self.rows.append(fmt.StringTableRow(offset=offset, length=len(b)))
        self._ids[s] = sid
        return sid

    def pool_bytes(self):
        _check_limit(len(self._pool), fmt.LIMIT_STRING_POOL_TOTAL_BYTES, "total string pool byte size")
        return bytes(self._pool)


def compile_sidecar(source_bytes, result, fold_families=None):
    """Compile `result` (a `sfm_master_core.MasterParseResult` already
    produced by parsing `source_bytes`) into the experimental packed sidecar
    format. Returns the complete sidecar file content as `bytes`.

    Raises `SidecarProfileError` if the compatibility-profile gate refuses
    the source, or `SidecarFieldOverflowError` if any derived value would
    not fit its normative field or exceeds a Section 18 resource limit.
    Never silently truncates or clamps a value."""
    expected_sha = core.sha256_of_bytes(source_bytes)
    if expected_sha != result.source_sha256:
        raise ValueError(
            "source_bytes does not match result.source_sha256 (%s != %s) -- "
            "result must be sfm_master_core.parse_master_bytes(source_bytes)" % (
                expected_sha, result.source_sha256,
            )
        )

    check_compatibility_profile(result)

    _check_limit(len(source_bytes), fmt.LIMIT_SOURCE_BYTE_SIZE, "source byte size")
    _check_limit(len(result.groups), fmt.LIMIT_GROUP_COUNT, "group count")
    _check_limit(len(result.occurrences), fmt.LIMIT_OCCURRENCE_COUNT, "occurrence count")
    for g in result.groups:
        _check_limit(len(g.metadata.entries), fmt.LIMIT_METADATA_ROWS_PER_GROUP,
                     "metadata rows for group %r" % g.full_path)

    if fold_families is None:
        fold_families = core.build_fold_families(result.occurrences)
    _check_limit(len(fold_families), fmt.LIMIT_FOLD_COUNT, "fold count")

    # `result.groups` is already ordered by declare_order (0-based,
    # contiguous, no gaps -- sfm_master_core assigns one declare_order per
    # declared group via a single monotonic counter), so path_id == row
    # index == declare_order for every group, by construction.
    path_id_by_full_path = {g.full_path: i for i, g in enumerate(result.groups)}
    for i, g in enumerate(result.groups):
        assert g.declare_order == i, "declare_order must equal row index (sfm_master_core invariant)"

    sorted_fold_keys = sorted(fold_families.keys(), key=lambda k: k.encode("utf-8"))
    fold_id_by_key = {k: i for i, k in enumerate(sorted_fold_keys)}

    pool = _StringPoolBuilder()

    # Deterministic first-seen traversal order (final spec Section 28):
    # groups' names, then every group's metadata (key, value) in source
    # order, then every occurrence's literal in global source order, then
    # every fold key in sorted-fold-key-byte order. A string already interned
    # earlier (e.g. a fold key identical to an already-lowercase literal) is
    # deduplicated to its existing string_id, never re-added.
    for g in result.groups:
        pool.intern(g.name)
    for g in result.groups:
        for entry in g.metadata.entries:
            pool.intern(entry.key)
            pool.intern(entry.value)
    for occ in result.occurrences:
        pool.intern(occ.literal)
    for key in sorted_fold_keys:
        pool.intern(key)

    # GROUP TABLE + CHILD-ID INDEX + METADATA TABLE + OCCURRENCE-BY-GROUP INDEX.
    group_rows = []
    child_id_index = []
    metadata_rows = []
    occ_by_group_index = []
    for i, g in enumerate(result.groups):
        name_sid = pool.intern(g.name)
        parent_pid = (
            fmt.ROOT_SENTINEL if g.parent_path is None else path_id_by_full_path[g.parent_path]
        )

        # `g.child_paths` is already ordered by declare_order, which for
        # children of one parent is identical to sibling_rank order
        # (sfm_master_core invariant, verified by B0.1's same-line-sibling
        # tests) -- so this is already the correct CHILD-ID INDEX slice order.
        child_ids = [path_id_by_full_path[c] for c in g.child_paths]
        child_index_start = _check_u32(len(child_id_index), "child_index_start")
        child_id_index.extend(_check_u32(cid, "child_path_id") for cid in child_ids)
        child_count = _check_u32(len(child_ids), "child_count")

        metadata_start = _check_u32(len(metadata_rows), "metadata_start")
        for order, entry in enumerate(g.metadata.entries):
            metadata_rows.append(fmt.MetadataTableRow(
                path_id=_check_u32(i, "metadata path_id"),
                key_string_id=pool.intern(entry.key),
                value_string_id=pool.intern(entry.value),
                source_order=_check_u32(order, "metadata source_order"),
            ))
        metadata_count = _check_u32(len(g.metadata.entries), "metadata_count")

        # `g.local_occurrence_global_ranks` is already ascending (built by
        # sfm_master_core via a single forward pass over `occurrences` in
        # global_rank order), so it is already the correct
        # OCCURRENCE-BY-GROUP INDEX slice order (Section 13: global_rank
        # values permuted into (path_id, local_rank) order).
        occ_by_group_start = _check_u32(len(occ_by_group_index), "occ_by_group_start")
        occ_by_group_index.extend(
            _check_u32(r, "occurrence global_rank") for r in g.local_occurrence_global_ranks
        )
        occ_by_group_count = _check_u32(len(g.local_occurrence_global_ranks), "occ_by_group_count")

        group_rows.append(fmt.GroupTableRow(
            name_string_id=name_sid,
            parent_path_id=parent_pid,
            declare_order=_check_u32(g.declare_order, "declare_order"),
            sibling_rank=_check_u32(g.sibling_rank, "sibling_rank"),
            child_count=child_count,
            child_index_start=child_index_start,
            metadata_start=metadata_start,
            metadata_count=metadata_count,
            occ_by_group_start=occ_by_group_start,
            occ_by_group_count=occ_by_group_count,
        ))

    # OCCURRENCE TABLE -- row index IS global_rank; `result.occurrences` is
    # already in that exact order (0-based, contiguous, by construction).
    occurrence_table_rows = []
    for occ in result.occurrences:
        fold_key = core.ascii_fold(occ.literal)
        occurrence_table_rows.append(fmt.OccurrenceTableRow(
            literal_string_id=pool.intern(occ.literal),
            path_id=_check_u32(path_id_by_full_path[occ.full_path], "occurrence path_id"),
            local_rank=_check_u32(occ.local_rank, "local_rank"),
            fold_id=_check_u32(fold_id_by_key[fold_key], "fold_id"),
        ))

    # FOLD TABLE + OCCURRENCE-BY-FOLD INDEX, sorted by raw folded-key UTF-8
    # bytes; within each fold's slice, ascending global_rank order.
    fold_table_rows = []
    occ_by_fold_index = []
    for key in sorted_fold_keys:
        fam = fold_families[key]
        ranks_sorted = sorted(fam.occurrence_global_ranks)
        assert len(ranks_sorted) >= 1, "a FoldFamily must have at least one occurrence by construction"
        occ_index_start = _check_u32(len(occ_by_fold_index), "occ_index_start")
        occ_by_fold_index.extend(_check_u32(r, "occurrence global_rank") for r in ranks_sorted)
        fold_table_rows.append(fmt.FoldTableRow(
            fold_key_string_id=pool.intern(key),
            occ_index_start=occ_index_start,
            occ_index_count=_check_u32(len(ranks_sorted), "occ_index_count"),
        ))

    # --- Serialize sections, fixed order (final spec Section 5). ---
    string_pool_bytes = pool.pool_bytes()
    string_table_bytes = b"".join(fmt.pack_string_table_row(r) for r in pool.rows)
    group_table_bytes = b"".join(fmt.pack_group_table_row(r) for r in group_rows)
    child_id_index_bytes = b"".join(fmt.pack_child_id_index_row(c) for c in child_id_index)
    metadata_table_bytes = b"".join(fmt.pack_metadata_table_row(r) for r in metadata_rows)
    occurrence_table_bytes = b"".join(fmt.pack_occurrence_table_row(r) for r in occurrence_table_rows)
    occ_by_group_index_bytes = b"".join(fmt.pack_occ_by_group_index_row(r) for r in occ_by_group_index)
    fold_table_bytes = b"".join(fmt.pack_fold_table_row(r) for r in fold_table_rows)
    occ_by_fold_index_bytes = b"".join(fmt.pack_occ_by_fold_index_row(r) for r in occ_by_fold_index)

    sections = [
        (fmt.SECTION_STRING_POOL, string_pool_bytes, len(string_pool_bytes), fmt.STRING_POOL_ROW_SIZE),
        (fmt.SECTION_STRING_TABLE, string_table_bytes, len(pool.rows), fmt.STRING_TABLE_ROW_SIZE),
        (fmt.SECTION_GROUP_TABLE, group_table_bytes, len(group_rows), fmt.GROUP_TABLE_ROW_SIZE),
        (fmt.SECTION_CHILD_ID_INDEX, child_id_index_bytes, len(child_id_index), fmt.CHILD_ID_INDEX_ROW_SIZE),
        (fmt.SECTION_METADATA_TABLE, metadata_table_bytes, len(metadata_rows), fmt.METADATA_TABLE_ROW_SIZE),
        (fmt.SECTION_OCCURRENCE_TABLE, occurrence_table_bytes, len(occurrence_table_rows),
         fmt.OCCURRENCE_TABLE_ROW_SIZE),
        (fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX, occ_by_group_index_bytes, len(occ_by_group_index),
         fmt.OCC_BY_GROUP_INDEX_ROW_SIZE),
        (fmt.SECTION_FOLD_TABLE, fold_table_bytes, len(fold_table_rows), fmt.FOLD_TABLE_ROW_SIZE),
        (fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX, occ_by_fold_index_bytes, len(occ_by_fold_index),
         fmt.OCC_BY_FOLD_INDEX_ROW_SIZE),
    ]

    directory_offset = fmt.HEADER_SIZE
    directory_size = len(sections) * fmt.DIRECTORY_ROW_SIZE
    cursor = directory_offset + directory_size
    directory_rows = []
    section_blobs = []
    for section_id, blob, row_count, row_size in sections:
        offset = _check_u64(cursor, "section offset")
        length = _check_u64(len(blob), "section length")
        _check_u32(row_count, "section row_count")
        _check_u32(row_size, "section row_size")
        if row_count * row_size != length:
            raise SidecarFieldOverflowError(
                "internal invariant violated: section %s row_count*row_size (%d*%d) != length (%d)"
                % (fmt.SECTION_NAMES[section_id], row_count, row_size, length)
            )
        directory_rows.append(fmt.DirectoryRow(
            section_id=section_id, offset=offset, length=length, row_count=row_count, row_size=row_size,
        ))
        section_blobs.append(blob)
        cursor += len(blob)

    payload_length = _check_u64(cursor, "payload_length")
    _check_limit(payload_length, fmt.LIMIT_SIDECAR_BYTE_SIZE, "sidecar byte size")

    header = fmt.Header(
        magic=fmt.MAGIC,
        format_contract_version=fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL,
        authority_semantics_version=fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL,
        source_sha256=bytes.fromhex(result.source_sha256),
        source_byte_length=_check_u64(len(source_bytes), "source_byte_length"),
        payload_length=payload_length,
        section_directory_offset=_check_u64(directory_offset, "section_directory_offset"),
        section_count=_check_u32(len(sections), "section_count"),
        embedded_integrity_digest=b"\x00" * fmt.SHA256_DIGEST_SIZE,
    )
    header_bytes = fmt.pack_header(header)
    assert len(header_bytes) == fmt.HEADER_SIZE
    directory_bytes = b"".join(fmt.pack_directory_row(r) for r in directory_rows)
    assert len(directory_bytes) == directory_size

    buf = bytearray()
    buf.extend(header_bytes)
    buf.extend(directory_bytes)
    for blob in section_blobs:
        buf.extend(blob)
    assert len(buf) == payload_length

    digest = fmt.compute_embedded_integrity_digest(bytes(buf), fmt.embedded_integrity_digest_offset())
    off = fmt.embedded_integrity_digest_offset()
    buf[off:off + fmt.SHA256_DIGEST_SIZE] = digest

    return bytes(buf)
