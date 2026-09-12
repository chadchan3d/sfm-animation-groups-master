# -*- coding: utf-8 -*-
"""GATE B -- QUALIFICATION-ONLY bounded-materialization sidecar provider
("S1"). NOT production code. Never imported by
`tools/sfm_master_sidecar/*.py`, never imported by the production Normalizer.

Backing choice (Gate B Part 4, explicit): the SIMPLEST backing that tests
bounded MATERIALIZATION -- an immutable complete byte snapshot, same
principle as production Candidate A. This module does not implement
Candidate B (file-backed reads) or Candidate C (mmap); it isolates exactly
one variable versus the qualified production reader: whether the FULL
row/string Python object graph is eagerly decoded and retained, or whether
only a bounded, on-demand subset is decoded and cached.

Complete validation (Section 20 A-J of the final format spec) is still
performed in full, with no sampling, exactly as production `reader.py`'s
`_validate_and_decode` performs it -- transcribed here faithfully (same
checks, same order; see `tools/sfm_master_sidecar/reader.py` for the
production original) -- but the decoded row/string objects created during
that one-time pass are discarded immediately afterward, never retained as
instance state. Steady-state retained data after admission is exactly:
the raw immutable byte buffer, the parsed HEADER, and the parsed SECTION
DIRECTORY (9 small rows) -- nothing else, until a caller actually requests
something, at which point only the bounded subset needed for that request
is decoded and cached.

Preserves exactly: literal semantics, ASCII-fold semantics (byte-level,
identical to `format.ascii_fold_bytes`), complete fold-family evidence
(every occurrence sharing a queried fold, never a partial slice), conflict
semantics (Hit/FoldConflict/MasterUnknown, recomputed per query, never
cached), occurrence global/local ranks, group hierarchy/sibling order,
metadata presence/value, strict UTF-8 (Gate A1's query-boundary
correction preserved exactly), source binding, checksum/integrity, and a
close/invalidation contract sufficient for this qualification (VALID ->
CLEANED, idempotent, post-close access raises).
"""

import os
import bisect

# NOTE: this module does NOT set up sys.path itself -- the caller (desktop
# test harness or embedded-SFM probe deployment) is responsible for ensuring
# `sfm_master_sidecar` is importable before this module is imported, exactly
# like every other qualification module in this package. A hardcoded
# absolute path here would silently bypass whatever runtime copy (deployed
# and SHA-verified for embedded use) the caller intended to exercise.
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader as prod_reader  # noqa: E402 -- shared result/exception classes only

AuthorityUnavailable = prod_reader.AuthorityUnavailable
SourceMismatchError = prod_reader.SourceMismatchError
Hit = prod_reader.Hit
FoldConflict = prod_reader.FoldConflict
MasterUnknown = prod_reader.MasterUnknown


def _fail(message):
    raise AuthorityUnavailable(message)


def _check_bounds(offset, length, container_length, what):
    if offset < 0 or length < 0 or offset + length > container_length:
        _fail("%s out of bounds (offset=%r length=%r container_length=%r)" % (
            what, offset, length, container_length,
        ))


def _read_path(path):
    f = open(path, "rb")
    try:
        return f.read()
    finally:
        f.close()


def _coerce_bytes(data):
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("bounded provider requires bytes or bytearray, got %r" % (type(data),))
    return bytes(data)


# ---------------------------------------------------------------------------
# Complete validation (Section 20 A-J), faithfully transcribed from
# production reader.py's `_validate_and_decode`. Every decoded row/string
# object created here is LOCAL to this function and is never retained --
# once this function returns, only `header` and `directory` survive.
# ---------------------------------------------------------------------------


def _validate_complete(buf):
    total_len = len(buf)

    if total_len < fmt.HEADER_SIZE:
        _fail("file is shorter than the fixed HEADER size (%d < %d)" % (total_len, fmt.HEADER_SIZE))
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
        _fail("payload_length (%d) does not match actual file size (%d)" % (header.payload_length, total_len))

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
        row = fmt.unpack_directory_row(buf, dir_off + i * fmt.DIRECTORY_ROW_SIZE)
        if row.section_id not in expected_section_ids:
            _fail("SECTION DIRECTORY row %d has unrecognized section_id %r" % (i, row.section_id))
        if row.section_id in directory:
            _fail("SECTION DIRECTORY has a duplicate section_id %r" % (row.section_id,))
        directory[row.section_id] = row
        _check_bounds(row.offset, row.length, total_len, "section %s" % fmt.SECTION_NAMES[row.section_id])
        if row.row_count * row.row_size != row.length:
            _fail("section %s: row_count*row_size != declared length" % fmt.SECTION_NAMES[row.section_id])
        normative_size = normative_row_sizes[row.section_id]
        if row.row_size != normative_size:
            _fail("section %s: file-declared row_size mismatch" % fmt.SECTION_NAMES[row.section_id])
        regions.append((row.offset, row.length, fmt.SECTION_NAMES[row.section_id]))

    if set(directory.keys()) != expected_section_ids:
        _fail("SECTION DIRECTORY does not contain the exact expected section set")

    regions.sort(key=lambda r: r[0])
    for i in range(1, len(regions)):
        prev_off, prev_len, prev_name = regions[i - 1]
        cur_off, cur_len, cur_name = regions[i]
        if cur_off < prev_off + prev_len:
            _fail("section/region overlap detected: %s overlaps %s" % (prev_name, cur_name))

    def section_bytes(section_id):
        row = directory[section_id]
        return buf[row.offset:row.offset + row.length]

    def section_row_count(section_id):
        return directory[section_id].row_count

    string_count = section_row_count(fmt.SECTION_STRING_TABLE)
    group_count = section_row_count(fmt.SECTION_GROUP_TABLE)
    occurrence_count = section_row_count(fmt.SECTION_OCCURRENCE_TABLE)
    fold_count = section_row_count(fmt.SECTION_FOLD_TABLE)
    if string_count > fmt.LIMIT_DISTINCT_POOL_STRINGS:
        _fail("declared string count exceeds resource limit")
    if group_count > fmt.LIMIT_GROUP_COUNT:
        _fail("declared group count exceeds resource limit")
    if occurrence_count > fmt.LIMIT_OCCURRENCE_COUNT:
        _fail("declared occurrence count exceeds resource limit")
    if fold_count > fmt.LIMIT_FOLD_COUNT:
        _fail("declared fold count exceeds resource limit")

    pool = section_bytes(fmt.SECTION_STRING_POOL)
    pool_len = len(pool)
    if pool_len > fmt.LIMIT_STRING_POOL_TOTAL_BYTES:
        _fail("STRING POOL byte size exceeds the resource limit")
    string_table_blob = section_bytes(fmt.SECTION_STRING_TABLE)
    strings = []
    for i in range(string_count):
        row = fmt.unpack_string_table_row(string_table_blob, i * fmt.STRING_TABLE_ROW_SIZE)
        _check_bounds(row.offset, row.length, pool_len, "STRING TABLE row %d" % i)
        if row.length > fmt.LIMIT_SINGLE_STRING_BYTE_LENGTH:
            _fail("STRING TABLE row %d exceeds the single-string resource limit" % i)
        raw = pool[row.offset:row.offset + row.length]
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            _fail("STRING TABLE row %d is not valid UTF-8: %r" % (i, exc))
        strings.append(s)

    group_table_blob = section_bytes(fmt.SECTION_GROUP_TABLE)
    groups = []
    for i in range(group_count):
        row = fmt.unpack_group_table_row(group_table_blob, i * fmt.GROUP_TABLE_ROW_SIZE)
        if row.name_string_id >= string_count:
            _fail("GROUP TABLE row %d: name_string_id out of bounds" % i)
        if row.parent_path_id != fmt.ROOT_SENTINEL and row.parent_path_id >= i:
            _fail("GROUP TABLE row %d: anti-cycle violation" % i)
        groups.append(row)

    parentless = [i for i, g in enumerate(groups) if g.parent_path_id == fmt.ROOT_SENTINEL]
    if len(parentless) != 1:
        _fail("GROUP TABLE must have exactly one parentless row; found %d" % len(parentless))
    declare_orders = [g.declare_order for g in groups]
    if len(set(declare_orders)) != len(declare_orders):
        _fail("GROUP TABLE declare_order values are not globally unique")

    full_paths = [None] * group_count

    def full_path_of(idx):
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

    child_id_index_blob = section_bytes(fmt.SECTION_CHILD_ID_INDEX)
    child_index_row_count = section_row_count(fmt.SECTION_CHILD_ID_INDEX)
    expected_child_rows = group_count - len(parentless)
    if child_index_row_count != expected_child_rows:
        _fail("CHILD-ID INDEX row_count mismatch")
    child_id_index = [
        fmt.unpack_child_id_index_row(child_id_index_blob, i * fmt.CHILD_ID_INDEX_ROW_SIZE)
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
                _fail("CHILD-ID INDEX entry out of bounds")
            child_covered[child_id] += 1
            child_row = groups[child_id]
            if child_row.parent_path_id != i:
                _fail("CHILD-ID INDEX ownership disagreement")
            if child_row.sibling_rank != k:
                _fail("CHILD-ID INDEX sibling_rank not dense")
            if child_row.sibling_rank <= prev_sibling_rank:
                _fail("CHILD-ID INDEX sibling_rank does not strictly increase")
            if child_row.declare_order <= prev_declare_order:
                _fail("CHILD-ID INDEX declare_order does not increase with sibling_rank")
            prev_sibling_rank = child_row.sibling_rank
            prev_declare_order = child_row.declare_order
    for i in range(group_count):
        is_root = groups[i].parent_path_id == fmt.ROOT_SENTINEL
        if is_root and child_covered[i] != 0:
            _fail("root group appears in CHILD-ID INDEX")
        if not is_root and child_covered[i] != 1:
            _fail("non-root group covered %d times (expected 1)" % child_covered[i])

    metadata_table_blob = section_bytes(fmt.SECTION_METADATA_TABLE)
    metadata_row_count = section_row_count(fmt.SECTION_METADATA_TABLE)
    for g in groups:
        if g.metadata_count > fmt.LIMIT_METADATA_ROWS_PER_GROUP:
            _fail("metadata_count exceeds resource limit")
    metadata_rows = [
        fmt.unpack_metadata_table_row(metadata_table_blob, i * fmt.METADATA_TABLE_ROW_SIZE)
        for i in range(metadata_row_count)
    ]
    for i, row in enumerate(metadata_rows):
        if row.key_string_id >= string_count or row.value_string_id >= string_count:
            _fail("METADATA TABLE row %d references an out-of-bounds string id" % i)
    meta_covered = [False] * metadata_row_count
    for i, g in enumerate(groups):
        start, count = g.metadata_start, g.metadata_count
        _check_bounds(start, count, metadata_row_count, "GROUP TABLE row %d metadata slice" % i)
        for k in range(count):
            idx = start + k
            if meta_covered[idx]:
                _fail("METADATA TABLE row claimed by more than one slice")
            meta_covered[idx] = True
            mrow = metadata_rows[idx]
            if mrow.path_id != i:
                _fail("METADATA TABLE ownership disagreement")
            if mrow.source_order != k:
                _fail("METADATA TABLE source_order not dense")
    if not all(meta_covered):
        _fail("METADATA TABLE has uncovered rows")

    occurrence_table_blob = section_bytes(fmt.SECTION_OCCURRENCE_TABLE)
    occurrence_rows = []
    for i in range(occurrence_count):
        row = fmt.unpack_occurrence_table_row(occurrence_table_blob, i * fmt.OCCURRENCE_TABLE_ROW_SIZE)
        if row.literal_string_id >= string_count:
            _fail("OCCURRENCE TABLE row %d: literal_string_id out of bounds" % i)
        if row.path_id >= group_count:
            _fail("OCCURRENCE TABLE row %d: path_id out of bounds" % i)
        if row.fold_id >= fold_count:
            _fail("OCCURRENCE TABLE row %d: fold_id out of bounds" % i)
        occurrence_rows.append(row)

    fold_table_blob = section_bytes(fmt.SECTION_FOLD_TABLE)
    fold_rows = []
    for i in range(fold_count):
        row = fmt.unpack_fold_table_row(fold_table_blob, i * fmt.FOLD_TABLE_ROW_SIZE)
        if row.fold_key_string_id >= string_count:
            _fail("FOLD TABLE row %d: fold_key_string_id out of bounds" % i)
        if row.occ_index_count < 1:
            _fail("FOLD TABLE row %d has occ_index_count < 1" % i)
        fold_rows.append(row)

    prev_key_bytes = None
    for i, row in enumerate(fold_rows):
        key_bytes = strings[row.fold_key_string_id].encode("utf-8")
        if prev_key_bytes is not None and key_bytes <= prev_key_bytes:
            _fail("FOLD TABLE not in strict ascending order at row %d" % i)
        prev_key_bytes = key_bytes

    local_rank_by_path = {}
    for i, row in enumerate(occurrence_rows):
        literal_bytes = strings[row.literal_string_id].encode("utf-8")
        expected_fold_bytes = fmt.ascii_fold_bytes(literal_bytes)
        actual_fold_bytes = strings[fold_rows[row.fold_id].fold_key_string_id].encode("utf-8")
        if expected_fold_bytes != actual_fold_bytes:
            _fail("OCCURRENCE TABLE row %d: ascii_fold mismatch" % i)
        local_rank_by_path.setdefault(row.path_id, []).append(row.local_rank)
    for path_id, ranks in local_rank_by_path.items():
        if sorted(ranks) != list(range(len(ranks))):
            _fail("group %d local_rank not dense" % path_id)
        if groups[path_id].occ_by_group_count != len(ranks):
            _fail("group %d occ_by_group_count mismatch" % path_id)
    for i, g in enumerate(groups):
        if g.occ_by_group_count > 0 and i not in local_rank_by_path:
            _fail("group %d declares occurrences but owns none" % i)

    occ_by_group_blob = section_bytes(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX)
    occ_by_group_row_count = section_row_count(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX)
    if occ_by_group_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-GROUP INDEX row_count mismatch")
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
                _fail("OCCURRENCE-BY-GROUP INDEX entry out of bounds")
            if seen_by_group[global_rank]:
                _fail("OCCURRENCE-BY-GROUP INDEX duplicate coverage")
            seen_by_group[global_rank] = True
            orow = occurrence_rows[global_rank]
            if orow.path_id != i:
                _fail("OCCURRENCE-BY-GROUP INDEX ownership disagreement")
            if orow.local_rank <= prev_local_rank:
                _fail("OCCURRENCE-BY-GROUP INDEX local_rank does not strictly increase")
            prev_local_rank = orow.local_rank
    if not all(seen_by_group):
        _fail("OCCURRENCE-BY-GROUP INDEX has a gap")

    occ_by_fold_blob = section_bytes(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX)
    occ_by_fold_row_count = section_row_count(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX)
    if occ_by_fold_row_count != occurrence_count:
        _fail("OCCURRENCE-BY-FOLD INDEX row_count mismatch")
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
                _fail("OCCURRENCE-BY-FOLD INDEX entry out of bounds")
            if seen_by_fold[global_rank]:
                _fail("OCCURRENCE-BY-FOLD INDEX duplicate coverage")
            seen_by_fold[global_rank] = True
            orow = occurrence_rows[global_rank]
            if orow.fold_id != fid:
                _fail("OCCURRENCE-BY-FOLD INDEX ownership disagreement")
        fold_occ_counts[fid] = count
    if not all(seen_by_fold):
        _fail("OCCURRENCE-BY-FOLD INDEX has a gap")

    if sum(g.child_count for g in groups) != child_index_row_count:
        _fail("child_count cardinality mismatch")
    if sum(g.metadata_count for g in groups) != metadata_row_count:
        _fail("metadata_count cardinality mismatch")
    if sum(g.occ_by_group_count for g in groups) != occurrence_count:
        _fail("occ_by_group_count cardinality mismatch")
    if sum(fold_occ_counts) != occurrence_count:
        _fail("fold occ_index_count cardinality mismatch")

    # Every decoded object above (strings, groups, occurrence_rows, fold_rows,
    # child_id_index, metadata_rows, both index arrays) goes out of scope
    # HERE -- only header/directory survive into the returned tuple.
    return header, directory


class BoundedProvider(object):
    """Qualification-only bounded-materialization provider ("S1"). Complete
    immutable byte-snapshot backing (Gate B Part 4); complete validation with
    no retained decoded graph (Part 5); on-demand, cached, bounded decoding
    of exactly what a caller requests (Part 3/6)."""

    STATE_VALID = "VALID"
    STATE_CLEANED = "CLEANED"

    def __init__(self):
        raise TypeError("use BoundedProvider.open_bytes(...)/open_path(...)")

    @classmethod
    def _open_from_buf(cls, buf, expected_source_sha256, bound):
        header, directory = _validate_complete(buf)
        if bound:
            import binascii
            actual_hex = binascii.hexlify(header.source_sha256).decode("ascii").lower()
            if actual_hex != expected_source_sha256.lower():
                raise SourceMismatchError(
                    "expected source_sha256 %s, sidecar header declares %s" % (
                        expected_source_sha256, actual_hex,
                    )
                )
        self = cls.__new__(cls)
        self._buf = buf  # the ONLY large retained object -- the immutable snapshot itself
        self._header = header
        self._directory = directory
        self._string_cache = {}
        self._groups = None          # lazily decoded, bounded by group_count (43 for the official Master)
        self._group_full_path_cache = {}
        self._child_index = None     # lazily decoded, bounded by group_count - 1
        self._metadata_rows = None   # lazily decoded, bounded by metadata_row_count (54 for the official Master)
        self._state = cls.STATE_VALID
        return self

    @classmethod
    def open_bytes(cls, data, expected_source_sha256):
        return cls._open_from_buf(_coerce_bytes(data), expected_source_sha256, bound=True)

    @classmethod
    def open_path(cls, path, expected_source_sha256):
        return cls._open_from_buf(_read_path(path), expected_source_sha256, bound=True)

    def _require_valid(self):
        if self._state != self.STATE_VALID:
            _fail("provider is not VALID (state=%s)" % self._state)

    def is_valid(self):
        return self._state == self.STATE_VALID

    def close(self):
        if self._state == self.STATE_CLEANED:
            return
        self._buf = None
        self._string_cache = None
        self._groups = None
        self._group_full_path_cache = None
        self._child_index = None
        self._metadata_rows = None
        self._state = self.STATE_CLEANED

    # -- bounded, cached, on-demand section access --

    def _section(self, section_id):
        row = self._directory[section_id]
        return self._buf[row.offset:row.offset + row.length]

    def _string(self, string_id):
        cached = self._string_cache.get(string_id)
        if cached is not None:
            return cached
        st_row_off = string_id * fmt.STRING_TABLE_ROW_SIZE
        st_blob = self._buf[
            self._directory[fmt.SECTION_STRING_TABLE].offset + st_row_off:
            self._directory[fmt.SECTION_STRING_TABLE].offset + st_row_off + fmt.STRING_TABLE_ROW_SIZE
        ]
        row = fmt.unpack_string_table_row(st_blob, 0)
        pool_off = self._directory[fmt.SECTION_STRING_POOL].offset
        raw = self._buf[pool_off + row.offset: pool_off + row.offset + row.length]
        s = raw.decode("utf-8")
        self._string_cache[string_id] = s
        return s

    def _ensure_groups(self):
        """Bounded by group_count (43 for the official Master), NOT by
        occurrence_count (128,555) or fold_count (124,728) -- this is the
        "static hierarchy/metadata" the Normalizer contract needs (Gate B
        Part 6), decoded once and cached, independent of how many folds are
        ever requested."""
        if self._groups is not None:
            return
        group_count = self._directory[fmt.SECTION_GROUP_TABLE].row_count
        group_table_blob = self._section(fmt.SECTION_GROUP_TABLE)
        groups = []
        for i in range(group_count):
            groups.append(fmt.unpack_group_table_row(group_table_blob, i * fmt.GROUP_TABLE_ROW_SIZE))
        self._groups = groups

    def group_count(self):
        self._require_valid()
        self._ensure_groups()
        return len(self._groups)

    def occurrence_count(self):
        self._require_valid()
        return self._directory[fmt.SECTION_OCCURRENCE_TABLE].row_count

    def fold_count(self):
        self._require_valid()
        return self._directory[fmt.SECTION_FOLD_TABLE].row_count

    def wrapper_path(self):
        self._require_valid()
        self._ensure_groups()
        for i, g in enumerate(self._groups):
            if g.parent_path_id == fmt.ROOT_SENTINEL:
                return self.group_full_path(i)
        _fail("no parentless group found")

    def group_full_path(self, path_id):
        self._require_valid()
        self._ensure_groups()
        cached = self._group_full_path_cache.get(path_id)
        if cached is not None:
            return cached
        row = self._groups[path_id]
        name = self._string(row.name_string_id)
        if row.parent_path_id == fmt.ROOT_SENTINEL:
            fp = name
        else:
            fp = self.group_full_path(row.parent_path_id) + "/" + name
        self._group_full_path_cache[path_id] = fp
        return fp

    def iter_groups(self):
        self._require_valid()
        self._ensure_groups()
        for i, row in enumerate(self._groups):
            yield {
                "path_id": i,
                "name": self._string(row.name_string_id),
                "full_path": self.group_full_path(i),
                "parent_path_id": row.parent_path_id,
                "parent_path": (
                    None if row.parent_path_id == fmt.ROOT_SENTINEL
                    else self.group_full_path(row.parent_path_id)
                ),
                "declare_order": row.declare_order,
                "sibling_rank": row.sibling_rank,
            }

    def _ensure_metadata(self):
        """Bounded by metadata_row_count (54 for the official Master) --
        also fixed/small, independent of requested fold count."""
        if self._metadata_rows is not None:
            return
        metadata_row_count = self._directory[fmt.SECTION_METADATA_TABLE].row_count
        blob = self._section(fmt.SECTION_METADATA_TABLE)
        rows = []
        for i in range(metadata_row_count):
            rows.append(fmt.unpack_metadata_table_row(blob, i * fmt.METADATA_TABLE_ROW_SIZE))
        self._metadata_rows = rows

    def iter_metadata(self, path_id):
        self._require_valid()
        self._ensure_groups()
        self._ensure_metadata()
        row = self._groups[path_id]
        start, count = row.metadata_start, row.metadata_count
        for k in range(count):
            mrow = self._metadata_rows[start + k]
            yield {
                "key": self._string(mrow.key_string_id),
                "value": self._string(mrow.value_string_id),
                "source_order": mrow.source_order,
            }

    def lookup_fold(self, query):
        """Bounded fold lookup: binary search touches only O(log fold_count)
        rows/strings, never the whole FOLD TABLE; a HIT/FoldConflict decodes
        only that ONE fold's complete occurrence family (bounded by the
        requested family's own size), never all 128,555 occurrences."""
        self._require_valid()
        if not isinstance(query, (bytes, bytearray)):
            raise TypeError("lookup_fold requires bytes")
        query = bytes(query)
        if len(query) > fmt.LIMIT_READER_QUERY_BYTE_LENGTH:
            raise ValueError("query too long")
        query.decode("utf-8")  # Gate A1 strict-encoding boundary, preserved exactly
        folded = fmt.ascii_fold_bytes(query)

        fold_count = self.fold_count()
        fold_table_off = self._directory[fmt.SECTION_FOLD_TABLE].offset

        def fold_row_at(i):
            blob = self._buf[fold_table_off + i * fmt.FOLD_TABLE_ROW_SIZE:
                              fold_table_off + (i + 1) * fmt.FOLD_TABLE_ROW_SIZE]
            return fmt.unpack_fold_table_row(blob, 0)

        lo, hi = 0, fold_count
        found = -1
        while lo < hi:
            mid = (lo + hi) // 2
            mid_row = fold_row_at(mid)
            mid_bytes = self._string(mid_row.fold_key_string_id).encode("utf-8")
            if mid_bytes < folded:
                lo = mid + 1
            elif mid_bytes > folded:
                hi = mid
            else:
                found = mid
                break
        if found < 0:
            return MasterUnknown(folded)

        frow = fold_row_at(found)
        occ_by_fold_off = self._directory[fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX].offset
        occurrence_table_off = self._directory[fmt.SECTION_OCCURRENCE_TABLE].offset

        destinations = set()
        occs = []
        for k in range(frow.occ_index_count):
            idx_off = occ_by_fold_off + (frow.occ_index_start + k) * fmt.OCC_BY_FOLD_INDEX_ROW_SIZE
            gr = fmt.unpack_occ_by_fold_index_row(self._buf, idx_off)
            occ_off = occurrence_table_off + gr * fmt.OCCURRENCE_TABLE_ROW_SIZE
            orow = fmt.unpack_occurrence_table_row(self._buf, occ_off)
            path = self.group_full_path(orow.path_id)
            destinations.add(path)
            occs.append({
                "literal": self._string(orow.literal_string_id),
                "full_path": path,
                "local_rank": orow.local_rank,
                "global_rank": gr,
            })
        if len(destinations) > 1:
            return FoldConflict(folded, destinations, occs)
        return Hit(folded, next(iter(destinations)), occs)

    def destination_count(self):
        """GLOBAL count of distinct destinations owning >=1 occurrence,
        derived ENTIRELY from the small, cached GROUP TABLE
        (`occ_by_group_count > 0` per group) -- never touches the
        occurrence table at all. Bounded by group_count, not
        occurrence_count."""
        self._require_valid()
        self._ensure_groups()
        return sum(1 for g in self._groups if g.occ_by_group_count > 0)

    def iter_occurrences(self):
        """DIAGNOSTIC / CROSS-CHECK ONLY -- NOT part of the bounded path.

        Full O(occurrence_count) decode of every occurrence row, exposed
        ONLY so the already-Gate-A2-qualified generic
        `build_compatibility_view()` reference implementation can be run
        against this provider too, as a slow-but-obviously-correct
        cross-check for `bounded_view.build_view_bounded()`'s fast,
        per-fold-bounded output. Never call this from the bounded path
        itself, and never use it as evidence of S1's own steady-state
        cost -- doing so would defeat the entire point of Gate B."""
        self._require_valid()
        occurrence_table_off = self._directory[fmt.SECTION_OCCURRENCE_TABLE].offset
        occurrence_count = self.occurrence_count()
        i = 0
        while True:
            self._require_valid()
            if i >= occurrence_count:
                return
            off = occurrence_table_off + i * fmt.OCCURRENCE_TABLE_ROW_SIZE
            row = fmt.unpack_occurrence_table_row(self._buf, off)
            yield {
                "global_rank": i,
                "literal": self._string(row.literal_string_id),
                "full_path": self.group_full_path(row.path_id),
                "local_rank": row.local_rank,
            }
            i += 1
