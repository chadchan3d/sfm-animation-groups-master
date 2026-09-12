# -*- coding: utf-8 -*-
"""Embedded-runtime-safe reader for the experimental packed sidecar format.

Python 2.7 AND Python 3 compatible. Imports nothing beyond the standard
library and `format` (this package's sibling module) -- never
`tools.sfm_master_core`, never `writer` (Python-3-only), never test/CLI
code. This is the module a real Python 2.7 embedded-SFM interpreter must be
able to import and use.

Implements, per SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md:
  - Section 20 complete (non-sampled) structural validation, A through J.
  - Section 21 source binding (`open_generation` vs `open_generation_unbound`).
  - Section 22 backing: Candidate A only (whole file read into one immutable
    in-memory buffer at open time; every later query answered from that same
    buffer).
  - Section 23 reader lifetime: VALID / INVALID / CLEANED, with the
    corrected (B1.2a) `close()` contract -- invalidation and resource
    cleanup are tracked as independent facts.
  - Section 24 lookup semantics: HIT / FOLD_CONFLICT / MASTER_UNKNOWN.

Materialization choice (Section 26, deliberately unresolved by the spec,
resolved here for this implementation): `Hit`/`FoldConflict` are eagerly
materialized, already-known, non-authoritative copies at the moment
`lookup_fold` returns them -- they remain readable even after the provider
is later invalidated/closed (one of the two permitted kinds the final spec
names in Section 23's dependent-view paragraph). `iter_groups`/
`iter_occurrences`/`iter_metadata`, by contrast, are the other permitted
kind: lazy, provider-backed generators that re-check provider validity on
every step and raise `AuthorityUnavailable` on the next step after
invalidation.
"""

import binascii

from . import format as fmt


# ---------------------------------------------------------------------------
# Exceptions / result values.
# ---------------------------------------------------------------------------


class SidecarError(Exception):
    """Base class for every exception this module raises."""


class AuthorityUnavailable(SidecarError):
    """Raised whenever an authority query cannot be serviced: structural
    corruption, an unsupported/mismatched version, a closed or invalidated
    provider, a used-after-parent-closed view, or an unbound handle used
    where authority is required. Never a substitute for `MasterUnknown`."""


class SourceMismatchError(AuthorityUnavailable):
    """`open_generation`'s `expected_source_sha256` did not match the
    sidecar's embedded `source_sha256` header field."""


class Hit(object):
    """A fold query resolved to exactly one destination. Already-materialized
    (Section 26/23): safe to read after the provider that produced it is
    later invalidated or closed."""

    __slots__ = ("fold_key", "destination", "_occurrences")

    def __init__(self, fold_key, destination, occurrences):
        self.fold_key = fold_key
        self.destination = destination
        self._occurrences = occurrences

    def occurrences(self):
        """The COMPLETE evidence for this fold family (every alias/occurrence
        at this one destination) -- never a partial/path-truncated slice."""
        return list(self._occurrences)

    def __repr__(self):
        return "Hit(fold_key=%r, destination=%r, n=%d)" % (
            self.fold_key, self.destination, len(self._occurrences),
        )


class FoldConflict(object):
    """A fold query resolved to more than one distinct destination.
    Already-materialized, same posture as `Hit`."""

    __slots__ = ("fold_key", "destinations", "_occurrences")

    def __init__(self, fold_key, destinations, occurrences):
        self.fold_key = fold_key
        self.destinations = set(destinations)
        self._occurrences = occurrences

    def occurrences(self):
        """The COMPLETE evidence across every destination this fold spans."""
        return list(self._occurrences)

    def __repr__(self):
        return "FoldConflict(fold_key=%r, destinations=%r, n=%d)" % (
            self.fold_key, sorted(self.destinations), len(self._occurrences),
        )


class MasterUnknown(object):
    """A successful, valid, source-bound lookup against backing whose folded
    identity genuinely does not exist. Reserved EXCLUSIVELY for this case --
    never substituted for any corruption/mismatch/closed-provider
    condition (those all raise `AuthorityUnavailable` instead)."""

    __slots__ = ("fold_key",)

    def __init__(self, fold_key):
        self.fold_key = fold_key

    def __repr__(self):
        return "MasterUnknown(fold_key=%r)" % (self.fold_key,)


# ---------------------------------------------------------------------------
# Backing: the fully-decoded, fully-validated in-memory representation of one
# opened generation (Candidate A -- see module docstring).
# ---------------------------------------------------------------------------


class _Backing(object):
    __slots__ = (
        "header", "directory", "strings", "groups", "child_id_index",
        "metadata_rows", "occurrence_rows", "occ_by_group_index",
        "fold_rows", "occ_by_fold_index",
    )


def _coerce_bytes(data):
    """Explicit BYTES entry point. `data` is ALWAYS treated as already-loaded
    complete sidecar artifact bytes -- never opened, never interpreted as a
    filesystem path, regardless of its Python type or Python version. Raises
    `TypeError` if it is not actually `bytes`/`bytearray` (defense-in-depth
    only -- callers of the explicit bytes entry points are expected to
    already know they hold bytes; this never attempts to guess otherwise)."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(
            "open_generation_bytes()/open_generation_unbound_bytes() require bytes or bytearray, "
            "got %r -- use open_generation_path()/open_generation_unbound_path() for a filesystem path" % (
                type(data),
            )
        )
    return bytes(data)


def _read_path(path):
    """Explicit PATH entry point. `path` is ALWAYS opened as a filesystem
    path in binary mode and read completely -- never interpreted as raw
    artifact bytes, regardless of its Python type or Python version. This is
    the ONLY function in this module that ever calls `open()` on its
    argument; there is no type-based dispatch anywhere in this file (the
    final spec's Correction: under Python 2.7, `bytes is str`, so an
    ordinary path string is indistinguishable from raw artifact bytes by
    type alone -- the input MODE must be chosen explicitly by the caller,
    never inferred)."""
    f = open(path, "rb")
    try:
        return f.read()
    finally:
        f.close()


def _fail(message):
    raise AuthorityUnavailable(message)


def _check_bounds(offset, length, container_length, what):
    if offset < 0 or length < 0 or offset + length > container_length:
        _fail("%s out of bounds (offset=%r length=%r container_length=%r)" % (
            what, offset, length, container_length,
        ))


def _validate_and_decode(buf):
    """Full Section 20 (A-J) validation, performed once at open time, plus
    eager decode of every section into plain Python lists (a deliberate,
    documented implementation choice for this small-fixture phase -- see
    module docstring). Raises `AuthorityUnavailable` (or `SourceMismatchError`,
    though that is checked by the caller after this returns) on the first
    violation found; never returns a partially-valid `_Backing`."""

    total_len = len(buf)

    # --- A. Header / Directory / Protected Regions. ---
    if total_len < fmt.HEADER_SIZE:
        _fail("file is shorter than the fixed HEADER size (%d < %d) -- truncated header" % (
            total_len, fmt.HEADER_SIZE,
        ))
    try:
        header = fmt.unpack_header(buf, 0)
    except Exception as exc:  # struct.error and friends
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

    # Embedded integrity digest is checked here -- immediately after the
    # header itself is minimally sane, and BEFORE any SECTION DIRECTORY row
    # is decoded or structurally checked (Phase B2C finding: digest
    # computation only needs the whole buffer, never the directory's own
    # content, so there is no reason to defer it behind directory-row
    # checks). This ordering is what makes the final spec Section 39
    # checksum-aware doctrine's two forms actually distinct in practice: a
    # CHECKSUM-INVALID mutation (digest left stale) now always fails HERE,
    # at the digest comparison, regardless of what else about the file was
    # also mutated; a CHECKSUM-VALID mutation (digest correctly recomputed
    # over the mutated bytes) passes this check and must be caught by a
    # later, specific structural check instead -- proving that check pulls
    # real independent weight. Before this fix, a directory-row-level
    # mutation (e.g. a wrong row_size) could be caught by the structural
    # check below even with a stale digest, making the digest branch
    # unreachable for that class of mutation.
    digest_off = fmt.embedded_integrity_digest_offset()
    recomputed = fmt.compute_embedded_integrity_digest(buf, digest_off)
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

    def section_bytes(section_id):
        row = directory[section_id]
        return buf[row.offset:row.offset + row.length]

    def section_row_count(section_id):
        return directory[section_id].row_count

    # --- Resource-limit bounds BEFORE allocating any buffer sized from a
    # declared count (Section 18's explicit ordering requirement). ---
    string_count = section_row_count(fmt.SECTION_STRING_TABLE)
    group_count = section_row_count(fmt.SECTION_GROUP_TABLE)
    occurrence_count = section_row_count(fmt.SECTION_OCCURRENCE_TABLE)
    fold_count = section_row_count(fmt.SECTION_FOLD_TABLE)
    if string_count > fmt.LIMIT_DISTINCT_POOL_STRINGS:
        _fail("declared string count %d exceeds resource limit" % string_count)
    if group_count > fmt.LIMIT_GROUP_COUNT:
        _fail("declared group count %d exceeds resource limit" % group_count)
    if occurrence_count > fmt.LIMIT_OCCURRENCE_COUNT:
        _fail("declared occurrence count %d exceeds resource limit" % occurrence_count)
    if fold_count > fmt.LIMIT_FOLD_COUNT:
        _fail("declared fold count %d exceeds resource limit" % fold_count)

    # --- B. String Table + STRING POOL. ---
    pool = section_bytes(fmt.SECTION_STRING_POOL)
    pool_len = len(pool)
    if pool_len > fmt.LIMIT_STRING_POOL_TOTAL_BYTES:
        _fail("STRING POOL byte size %d exceeds the resource limit %d" % (
            pool_len, fmt.LIMIT_STRING_POOL_TOTAL_BYTES,
        ))
    string_table_blob = section_bytes(fmt.SECTION_STRING_TABLE)
    strings = []
    for i in range(string_count):
        try:
            row = fmt.unpack_string_table_row(string_table_blob, i * fmt.STRING_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack STRING TABLE row %d: %r" % (i, exc))
        _check_bounds(row.offset, row.length, pool_len, "STRING TABLE row %d" % i)
        if row.length > fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH:
            _fail("STRING TABLE row %d declares length %d exceeding the single-string resource limit %d" % (
                i, row.length, fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH,
            ))
        raw = pool[row.offset:row.offset + row.length]
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail("STRING TABLE row %d is not valid UTF-8: %r" % (i, exc))
        strings.append(s)

    # --- C. Group Table (structural checks; partition/child-index checks
    # continue in the CHILD-ID INDEX block below, per D). ---
    group_table_blob = section_bytes(fmt.SECTION_GROUP_TABLE)
    groups = []
    for i in range(group_count):
        try:
            row = fmt.unpack_group_table_row(group_table_blob, i * fmt.GROUP_TABLE_ROW_SIZE)
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

    # Path-identity uniqueness: reconstruct every full path and confirm none
    # collide (a full O(n) check, not assumed true because the compiler is
    # trusted).
    full_paths = [None] * group_count

    def full_path_of(idx, _seen=None):
        if full_paths[idx] is not None:
            return full_paths[idx]
        row = groups[idx]
        name = strings[row.name_string_id]
        if row.parent_path_id == fmt.ROOT_SENTINEL:
            fp = name
        else:
            fp = full_path_of(row.parent_path_id) + "/" + name
        full_paths[idx] = fp
        return fp

    for i in range(group_count):
        full_path_of(i)
    if len(set(full_paths)) != len(full_paths):
        _fail("two or more GROUP TABLE rows reconstruct to the same full path")

    # --- D. Index slice partitioning: CHILD-ID INDEX over non-root groups. ---
    child_id_index_blob = section_bytes(fmt.SECTION_CHILD_ID_INDEX)
    child_index_row_count = section_row_count(fmt.SECTION_CHILD_ID_INDEX)
    expected_child_rows = group_count - len(parentless)
    if child_index_row_count != expected_child_rows:
        _fail(
            "CHILD-ID INDEX row_count %d does not match group_count - parentless_group_count (%d)" % (
                child_index_row_count, expected_child_rows,
            )
        )
    child_id_index = []
    for i in range(child_index_row_count):
        child_id_index.append(fmt.unpack_child_id_index_row(child_id_index_blob, i * fmt.CHILD_ID_INDEX_ROW_SIZE))

    child_seen = [False] * child_index_row_count if False else None  # placeholder, unused
    child_covered = [0] * group_count  # coverage count per group (must end up == 1 for non-root, 0 for root)
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

    # --- E. Metadata Table partition. ---
    metadata_table_blob = section_bytes(fmt.SECTION_METADATA_TABLE)
    metadata_row_count = section_row_count(fmt.SECTION_METADATA_TABLE)
    for g in groups:
        if g.metadata_count > fmt.LIMIT_METADATA_ROWS_PER_GROUP:
            _fail("a GROUP TABLE row declares metadata_count %d exceeding the resource limit" % g.metadata_count)
    metadata_rows = []
    for i in range(metadata_row_count):
        try:
            row = fmt.unpack_metadata_table_row(metadata_table_blob, i * fmt.METADATA_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack METADATA TABLE row %d: %r" % (i, exc))
        if row.key_string_id >= string_count or row.value_string_id >= string_count:
            _fail("METADATA TABLE row %d references an out-of-bounds string id" % i)
        metadata_rows.append(row)

    meta_covered = [False] * metadata_row_count
    for i, g in enumerate(groups):
        start, count = g.metadata_start, g.metadata_count
        _check_bounds(start, count, metadata_row_count, "GROUP TABLE row %d metadata slice" % i)
        for k in range(count):
            idx = start + k
            if meta_covered[idx]:
                _fail("METADATA TABLE row %d is claimed by more than one group's slice" % idx)
            meta_covered[idx] = True
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
    if not all(meta_covered):
        _fail("METADATA TABLE has rows not covered by any group's declared slice (gap)")

    # --- F. Occurrence Table. ---
    occurrence_table_blob = section_bytes(fmt.SECTION_OCCURRENCE_TABLE)
    occurrence_rows = []
    for i in range(occurrence_count):
        try:
            row = fmt.unpack_occurrence_table_row(occurrence_table_blob, i * fmt.OCCURRENCE_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack OCCURRENCE TABLE row %d: %r" % (i, exc))
        if row.literal_string_id >= string_count:
            _fail("OCCURRENCE TABLE row %d: literal_string_id out of bounds" % i)
        if row.path_id >= group_count:
            _fail("OCCURRENCE TABLE row %d: path_id out of bounds" % i)
        if row.fold_id >= fold_count:
            _fail("OCCURRENCE TABLE row %d: fold_id out of bounds" % i)
        occurrence_rows.append(row)

    # --- H. Fold Table (decoded here so F's per-occurrence fold check can
    # reference it; ordering/occ_index_count checks happen below). ---
    fold_table_blob = section_bytes(fmt.SECTION_FOLD_TABLE)
    fold_rows = []
    for i in range(fold_count):
        try:
            row = fmt.unpack_fold_table_row(fold_table_blob, i * fmt.FOLD_TABLE_ROW_SIZE)
        except Exception as exc:
            _fail("failed to unpack FOLD TABLE row %d: %r" % (i, exc))
        if row.fold_key_string_id >= string_count:
            _fail("FOLD TABLE row %d: fold_key_string_id out of bounds" % i)
        if row.occ_index_count < 1:
            _fail("FOLD TABLE row %d has occ_index_count %d (< 1 is corruption)" % (i, row.occ_index_count))
        fold_rows.append(row)

    prev_key_bytes = None
    for i, row in enumerate(fold_rows):
        key_bytes = strings[row.fold_key_string_id].encode("utf-8")
        if prev_key_bytes is not None and key_bytes <= prev_key_bytes:
            _fail("FOLD TABLE is not in strict ascending folded-key-byte order at row %d" % i)
        prev_key_bytes = key_bytes

    # F, continued: exhaustive per-occurrence fold consistency.
    local_rank_by_path = {}
    for i, row in enumerate(occurrence_rows):
        literal_bytes = strings[row.literal_string_id].encode("utf-8")
        expected_fold_bytes = fmt.ascii_fold_bytes(literal_bytes)
        actual_fold_bytes = strings[fold_rows[row.fold_id].fold_key_string_id].encode("utf-8")
        if expected_fold_bytes != actual_fold_bytes:
            _fail(
                "OCCURRENCE TABLE row %d: ascii_fold(literal) does not match its own fold_id's "
                "folded-key bytes" % i
            )
        local_rank_by_path.setdefault(row.path_id, []).append(row.local_rank)

    for path_id, ranks in local_rank_by_path.items():
        if sorted(ranks) != list(range(len(ranks))):
            _fail("occurrences owned by group %d do not form a dense 0..count-1 local_rank run" % path_id)
        if groups[path_id].occ_by_group_count != len(ranks):
            _fail(
                "group %d's declared occ_by_group_count (%d) does not match its actual occurrence "
                "count (%d)" % (path_id, groups[path_id].occ_by_group_count, len(ranks))
            )
    for i, g in enumerate(groups):
        if g.occ_by_group_count > 0 and i not in local_rank_by_path:
            _fail("group %d declares occ_by_group_count %d but owns zero OCCURRENCE TABLE rows" % (
                i, g.occ_by_group_count,
            ))

    # --- G. Occurrence-by-Group Index: complete partition of 0..N-1. ---
    occ_by_group_blob = section_bytes(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX)
    occ_by_group_row_count = section_row_count(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX)
    if occ_by_group_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-GROUP INDEX row_count %d != occurrence_count %d" % (
            occ_by_group_row_count, occurrence_count,
        ))
    occ_by_group_index = [
        fmt.unpack_occ_by_group_index_row(occ_by_group_blob, i * fmt.OCC_BY_GROUP_INDEX_ROW_SIZE)
        for i in range(occ_by_group_row_count)
    ]
    seen_by_group = [False] * occurrence_count
    for i, g in enumerate(groups):
        start, count = g.occ_by_group_start, g.occ_by_group_count
        _check_bounds(start, count, occ_by_group_row_count, "GROUP TABLE row %d occ_by_group slice" % i)
        prev_local_rank = -1
        for k in range(count):
            global_rank = occ_by_group_index[start + k]
            if global_rank >= occurrence_count:
                _fail("OCCURRENCE-BY-GROUP INDEX entry %d out of bounds" % global_rank)
            if seen_by_group[global_rank]:
                _fail("OCCURRENCE-BY-GROUP INDEX: global_rank %d claimed by more than one group's slice" % global_rank)
            seen_by_group[global_rank] = True
            orow = occurrence_rows[global_rank]
            if orow.path_id != i:
                _fail(
                    "OCCURRENCE-BY-GROUP INDEX: entry %d claimed by group %d's slice, but its own "
                    "path_id is %d" % (global_rank, i, orow.path_id)
                )
            if orow.local_rank <= prev_local_rank:
                _fail("OCCURRENCE-BY-GROUP INDEX slice for group %d: local_rank does not strictly increase" % i)
            prev_local_rank = orow.local_rank
    if not all(seen_by_group):
        _fail("OCCURRENCE-BY-GROUP INDEX does not cover every occurrence (gap)")

    # --- I. Occurrence-by-Fold Index: complete partition of 0..N-1. ---
    occ_by_fold_blob = section_bytes(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX)
    occ_by_fold_row_count = section_row_count(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX)
    if occ_by_fold_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-FOLD INDEX row_count %d != occurrence_count %d" % (
            occ_by_fold_row_count, occurrence_count,
        ))
    occ_by_fold_index = [
        fmt.unpack_occ_by_fold_index_row(occ_by_fold_blob, i * fmt.OCC_BY_FOLD_INDEX_ROW_SIZE)
        for i in range(occ_by_fold_row_count)
    ]
    seen_by_fold = [False] * occurrence_count
    fold_occ_counts = [0] * fold_count
    for fid, frow in enumerate(fold_rows):
        start, count = frow.occ_index_start, frow.occ_index_count
        _check_bounds(start, count, occ_by_fold_row_count, "FOLD TABLE row %d occ index slice" % fid)
        for k in range(count):
            global_rank = occ_by_fold_index[start + k]
            if global_rank >= occurrence_count:
                _fail("OCCURRENCE-BY-FOLD INDEX entry %d out of bounds" % global_rank)
            if seen_by_fold[global_rank]:
                _fail("OCCURRENCE-BY-FOLD INDEX: global_rank %d claimed by more than one fold's slice" % global_rank)
            seen_by_fold[global_rank] = True
            orow = occurrence_rows[global_rank]
            if orow.fold_id != fid:
                _fail(
                    "OCCURRENCE-BY-FOLD INDEX: entry %d claimed by fold %d's slice, but its own "
                    "fold_id is %d" % (global_rank, fid, orow.fold_id)
                )
        fold_occ_counts[fid] = count
    if not all(seen_by_fold):
        _fail("OCCURRENCE-BY-FOLD INDEX does not cover every occurrence (gap)")

    # --- J. Cardinality cross-checks (Section 16). ---
    if sum(g.child_count for g in groups) != child_index_row_count:
        _fail("sum of GROUP TABLE child_count values does not match CHILD-ID INDEX row_count")
    if sum(g.metadata_count for g in groups) != metadata_row_count:
        _fail("sum of GROUP TABLE metadata_count values does not match METADATA TABLE row_count")
    if sum(g.occ_by_group_count for g in groups) != occurrence_count:
        _fail("sum of GROUP TABLE occ_by_group_count values does not match OCCURRENCE TABLE row_count")
    if sum(fold_occ_counts) != occurrence_count:
        _fail("sum of FOLD TABLE occ_index_count values does not match OCCURRENCE TABLE row_count")

    backing = _Backing()
    backing.header = header
    backing.directory = directory
    backing.strings = strings
    backing.groups = groups
    backing.child_id_index = child_id_index
    backing.metadata_rows = metadata_rows
    backing.occurrence_rows = occurrence_rows
    backing.occ_by_group_index = occ_by_group_index
    backing.fold_rows = fold_rows
    backing.occ_by_fold_index = occ_by_fold_index
    return backing


# ---------------------------------------------------------------------------
# Public reader.
# ---------------------------------------------------------------------------


class SidecarReader(object):
    """One opened sidecar generation. Never constructed directly -- use one
    of the explicit entry points below.

    Input-mode contract (corrected -- see the module's Python-2.7 path/bytes
    input fix): every entry point's NAME states, explicitly, whether its
    argument is a filesystem path or already-loaded artifact bytes. There is
    NO entry point that infers this from the argument's Python type --
    under Python 2.7, `bytes is str`, so an ordinary path string is
    indistinguishable from raw artifact bytes by type alone, and any
    type-based dispatch is therefore genuinely ambiguous on that runtime,
    not merely inconvenient.

        open_generation_bytes(data, expected_source_sha256)         -- bytes, authority-bound
        open_generation_path(path, expected_source_sha256)          -- path, authority-bound
        open_generation_unbound_bytes(data)                         -- bytes, diagnostic-only
        open_generation_unbound_path(path)                          -- path, diagnostic-only

    `open_generation(...)` and `open_generation_unbound(...)` remain, as
    explicitly documented BYTES-ONLY aliases for `open_generation_bytes`/
    `open_generation_unbound_bytes` (never a path, on any Python version,
    regardless of argument type) -- kept for backward compatibility with
    existing callers that already only ever pass bytes. New code should
    prefer the explicit `_bytes`/`_path` names."""

    STATE_VALID = "VALID"
    STATE_INVALID = "INVALID"
    STATE_CLEANED = "CLEANED"

    def __init__(self):
        raise TypeError("use one of SidecarReader.open_generation_bytes(...)/open_generation_path(...)/"
                         "open_generation_unbound_bytes(...)/open_generation_unbound_path(...)")

    @classmethod
    def _open_from_buf(cls, buf, expected_source_sha256, bound):
        backing = _validate_and_decode(buf)
        if bound:
            actual_hex = binascii.hexlify(backing.header.source_sha256).decode("ascii").lower()
            if actual_hex != expected_source_sha256.lower():
                raise SourceMismatchError(
                    "expected source_sha256 %s, sidecar header declares %s" % (
                        expected_source_sha256, actual_hex,
                    )
                )
        self = cls.__new__(cls)
        self._backing = backing
        self._bound = bound
        self._state = cls.STATE_VALID
        self._path_cache = {}
        return self

    @classmethod
    def open_generation_unbound_bytes(cls, data):
        """Diagnostic open from already-loaded artifact BYTES. Performs the
        full Section 20 structural validation but does NOT verify the
        sidecar matches any particular source. NOT authority-usable --
        `lookup_fold` (and any other authority query) raises
        `AuthorityUnavailable` on a handle opened this way (Section 21).
        `data` is never interpreted as a filesystem path."""
        return cls._open_from_buf(_coerce_bytes(data), None, bound=False)

    @classmethod
    def open_generation_unbound_path(cls, path):
        """Diagnostic open from a filesystem PATH, read in binary mode.
        Same diagnostic-only (not authority-usable) contract as
        `open_generation_unbound_bytes`. `path` is always opened as a file;
        never interpreted as raw artifact bytes."""
        return cls._open_from_buf(_read_path(path), None, bound=False)

    @classmethod
    def open_generation_bytes(cls, data, expected_source_sha256):
        """Authority-bound open from already-loaded artifact BYTES. Raises
        `SourceMismatchError` (a subclass of `AuthorityUnavailable`) before
        returning a usable handle if the sidecar's embedded `source_sha256`
        does not match `expected_source_sha256` (a lowercase or uppercase
        hex string). `data` is never interpreted as a filesystem path."""
        return cls._open_from_buf(_coerce_bytes(data), expected_source_sha256, bound=True)

    @classmethod
    def open_generation_path(cls, path, expected_source_sha256):
        """Authority-bound open from a filesystem PATH, read in binary mode.
        Same source-binding contract as `open_generation_bytes`. `path` is
        always opened as a file; never interpreted as raw artifact bytes."""
        return cls._open_from_buf(_read_path(path), expected_source_sha256, bound=True)

    @classmethod
    def open_generation_unbound(cls, data):
        """Legacy alias for `open_generation_unbound_bytes` -- explicitly
        BYTES-ONLY, on every Python version, regardless of `data`'s type.
        Never guesses, never accepts a path. Prefer
        `open_generation_unbound_bytes`/`open_generation_unbound_path`
        explicitly in new code."""
        return cls.open_generation_unbound_bytes(data)

    @classmethod
    def open_generation(cls, data, expected_source_sha256):
        """Legacy alias for `open_generation_bytes` -- explicitly
        BYTES-ONLY, on every Python version, regardless of `data`'s type.
        Never guesses, never accepts a path. Prefer `open_generation_bytes`/
        `open_generation_path` explicitly in new code."""
        return cls.open_generation_bytes(data, expected_source_sha256)

    # -- Lifetime --

    def _require_valid(self):
        if self._state != self.STATE_VALID:
            raise AuthorityUnavailable("provider is not VALID (state=%s)" % self._state)

    def _require_bound_and_valid(self):
        self._require_valid()
        if not self._bound:
            raise AuthorityUnavailable(
                "this handle was opened via an unbound diagnostic entry point "
                "(open_generation_unbound_bytes/open_generation_unbound_path/open_generation_unbound); "
                "authority queries require an authority-bound open "
                "(open_generation_bytes/open_generation_path/open_generation)"
            )

    def is_valid(self):
        return self._state == self.STATE_VALID

    def _invalidate(self, reason):
        """Fatal-condition transition VALID -> INVALID. Resource cleanup is
        deferred to `close()` (the other of the two permitted Section 23
        strategies) -- this method never releases `_backing` itself."""
        if self._state == self.STATE_VALID:
            self._state = self.STATE_INVALID

    def force_invalidate_for_testing(self, reason="test-forced invalidation"):
        """Test-only fault-injection hook for the Section 23 / final spec
        Section 41 required invalidate-close-close lifecycle test. Not part
        of the normal authority surface."""
        self._invalidate(reason)

    def close(self):
        """Idempotent. Releases owned resources whether called from VALID or
        INVALID; harmless no-op once CLEANED; never restores authority."""
        if self._state == self.STATE_CLEANED:
            return
        self._backing = None
        self._path_cache = None
        self._state = self.STATE_CLEANED

    # -- Inspection (diagnostic; permitted on unbound handles) --

    def group_count(self):
        self._require_valid()
        return len(self._backing.groups)

    def occurrence_count(self):
        self._require_valid()
        return len(self._backing.occurrence_rows)

    def fold_count(self):
        self._require_valid()
        return len(self._backing.fold_rows)

    def source_sha256_hex(self):
        self._require_valid()
        return binascii.hexlify(self._backing.header.source_sha256).decode("ascii")

    def wrapper_path(self):
        self._require_valid()
        for i, g in enumerate(self._backing.groups):
            if g.parent_path_id == fmt.ROOT_SENTINEL:
                return self.group_full_path(i)
        raise AssertionError("a validated backing must have exactly one parentless group")

    def group_full_path(self, path_id):
        self._require_valid()
        cache = self._path_cache
        if path_id in cache:
            return cache[path_id]
        row = self._backing.groups[path_id]
        name = self._backing.strings[row.name_string_id]
        if row.parent_path_id == fmt.ROOT_SENTINEL:
            fp = name
        else:
            fp = self.group_full_path(row.parent_path_id) + "/" + name
        cache[path_id] = fp
        return fp

    def iter_groups(self):
        """Lazy, provider-backed: re-checks provider validity on every
        step (Section 23's "outstanding lazy result... fails on next
        access"), including the very first step (the check must happen
        before `self._backing` is ever touched, since a generator's body
        does not execute at all until the first `next()` call)."""
        i = 0
        while True:
            self._require_valid()
            if i >= len(self._backing.groups):
                return
            row = self._backing.groups[i]
            yield {
                "path_id": i,
                "name": self._backing.strings[row.name_string_id],
                "full_path": self.group_full_path(i),
                "parent_path_id": row.parent_path_id,
                "parent_path": (
                    None if row.parent_path_id == fmt.ROOT_SENTINEL
                    else self.group_full_path(row.parent_path_id)
                ),
                "declare_order": row.declare_order,
                "sibling_rank": row.sibling_rank,
            }
            i += 1

    def iter_occurrences(self):
        """Lazy, provider-backed (see `iter_groups`): the validity check
        happens before `self._backing` is ever touched on every step,
        including the first."""
        i = 0
        while True:
            self._require_valid()
            if i >= len(self._backing.occurrence_rows):
                return
            row = self._backing.occurrence_rows[i]
            yield {
                "global_rank": i,
                "literal": self._backing.strings[row.literal_string_id],
                "full_path": self.group_full_path(row.path_id),
                "local_rank": row.local_rank,
            }
            i += 1

    def iter_metadata(self, path_id):
        """Lazy, provider-backed (see `iter_groups`). `path_id` is a group's
        row index (as yielded by `iter_groups`), not a path string."""
        self._require_valid()
        row = self._backing.groups[path_id]
        start, count = row.metadata_start, row.metadata_count
        for k in range(count):
            self._require_valid()
            mrow = self._backing.metadata_rows[start + k]
            yield {
                "key": self._backing.strings[mrow.key_string_id],
                "value": self._backing.strings[mrow.value_string_id],
                "source_order": mrow.source_order,
            }

    # -- Authority: fold lookup (Section 24) --

    def lookup_fold(self, query):
        """`query` is a UTF-8-encoded byte string (the literal to look up,
        NOT pre-folded -- folding happens here, at the byte level). Returns
        `Hit`, `FoldConflict`, or `MasterUnknown`. Raises
        `AuthorityUnavailable` for a closed/invalidated/unbound provider or
        a malformed/oversized query -- never returns `MasterUnknown` for
        those cases."""
        self._require_bound_and_valid()
        if not isinstance(query, (bytes, bytearray)):
            raise TypeError("lookup_fold requires a UTF-8-encoded bytes query, got %r" % type(query))
        query = bytes(query)
        if len(query) > fmt.LIMIT_READER_QUERY_BYTE_LENGTH:
            raise ValueError(
                "query length %d exceeds the maximum reader query byte length %d" % (
                    len(query), fmt.LIMIT_READER_QUERY_BYTE_LENGTH,
                )
            )
        # Gate A1 correction: `query` must be validated as strict, exact
        # UTF-8 BEFORE ASCII folding / binary search / absence
        # classification -- malformed bytes are an input/query error
        # (ValueError, via the same UnicodeDecodeError the STRING TABLE's
        # own decode step already uses for stored-string corruption, since
        # UnicodeDecodeError IS a ValueError subclass -- no new exception
        # class, matching the existing TypeError/ValueError query-boundary
        # philosophy exactly), never a silently-accepted "absent" query.
        # The decoded value itself is discarded: folding still operates on
        # the original bytes, unchanged from before this correction -- this
        # is a validation-only step, not a decoding/normalization step.
        query.decode("utf-8")
        folded = fmt.ascii_fold_bytes(query)

        backing = self._backing
        fold_rows = backing.fold_rows
        lo, hi = 0, len(fold_rows)
        found = -1
        while lo < hi:
            mid = (lo + hi) // 2
            mid_bytes = backing.strings[fold_rows[mid].fold_key_string_id].encode("utf-8")
            if mid_bytes < folded:
                lo = mid + 1
            elif mid_bytes > folded:
                hi = mid
            else:
                found = mid
                break

        if found < 0:
            return MasterUnknown(folded)

        frow = fold_rows[found]
        ranks = backing.occ_by_fold_index[frow.occ_index_start:frow.occ_index_start + frow.occ_index_count]
        destinations = set()
        occs = []
        for gr in ranks:
            orow = backing.occurrence_rows[gr]
            path = self.group_full_path(orow.path_id)
            destinations.add(path)
            occs.append({
                "literal": backing.strings[orow.literal_string_id],
                "full_path": path,
                "local_rank": orow.local_rank,
                "global_rank": gr,
            })

        if len(destinations) > 1:
            return FoldConflict(folded, destinations, occs)
        return Hit(folded, next(iter(destinations)), occs)
