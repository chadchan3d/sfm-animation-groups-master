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

Complete validation (Section 20 A-J of the final format spec) is performed
by DELEGATING ENTIRELY to production `reader.py`'s own `_validate_and_decode`
(Gate C0.3 / Astra Round 2 finding: a second, hand-copied validator can
drift from the production integrity contract even if it starts identical
-- there is exactly ONE validation implementation in this codebase, never
two). The full decoded `_Backing` that function returns is used only to
extract `header`/`directory`; every other decoded row/string object it
produced is discarded immediately afterward, never retained as instance
state. Steady-state retained data after admission is exactly:
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
# Complete validation -- delegates ENTIRELY to production reader.py's own
# _validate_and_decode(buf) (Gate C0.3 / Astra Round 2 finding: a
# hand-copied second validator can drift from the production integrity
# contract even if it starts identical). This is the SAME function object
# reader.SidecarReader itself calls -- there is exactly ONE validation
# implementation in this codebase, never two. The full decoded _Backing it
# returns is used ONLY to extract header/directory; every other decoded
# array (strings, groups, occurrence_rows, fold_rows, child_id_index,
# metadata_rows, both index arrays) is discarded the moment this function
# returns, by simply never retaining a reference to "backing" itself past
# this point -- ordinary CPython refcounting reclaims it deterministically
# (no reference cycle survives to require a later gc.collect() call, per
# the C0.3 closure-cycle fix already applied to _validate_and_decode
# itself).
# ---------------------------------------------------------------------------


def _validate_complete(buf):
    backing = prod_reader._validate_and_decode(buf)
    return backing.header, backing.directory


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

    def evict_reusable_cache(self):
        """Gate C1.5 -- clears every RE-DERIVABLE cache (decoded string
        cache, group/metadata cache, per-group full-path cache). Never
        evicts anything a caller could not re-derive identically from the
        still-resident packed backing bytes -- so truth/semantic results
        on reacquisition are unchanged, only slower to re-decode. Never
        touches `self._buf` (the packed backing itself) and never affects
        any already-published ViewEnvelope payload (those are plain dicts,
        independent of this provider's internal caches once returned)."""
        self._require_valid()
        self._string_cache = {}
        self._groups = None
        self._group_full_path_cache = {}
        self._child_index = None
        self._metadata_rows = None

    # -- Gate C0.4/C0.7 resource introspection (qualification-only; never
    # used to change lookup/view semantics, only to REPORT what is
    # currently resident so "bounded" is a measured claim, not an assumed
    # one). --

    def packed_backing_bytes(self):
        """Size of the one immutable byte snapshot this provider holds --
        the floor beneath which retained state can never go while the
        provider remains open."""
        self._require_valid()
        return len(self._buf)

    def string_cache_entry_count(self):
        self._require_valid()
        return len(self._string_cache)

    def string_cache_estimated_bytes(self):
        """Sum of decoded (UTF-8-encoded) byte lengths of every cached
        string, plus a small fixed per-entry estimate for the Python
        object/dict-slot overhead itself. An ESTIMATE for reporting
        purposes, not a byte-exact accounting of CPython's actual unicode
        object representation."""
        self._require_valid()
        PER_ENTRY_OVERHEAD_ESTIMATE = 56  # dict slot + PyUnicodeObject header, approximate
        total = 0
        for s in self._string_cache.values():
            total += len(s.encode("utf-8")) + PER_ENTRY_OVERHEAD_ESTIMATE
        return total

    def group_metadata_cache_populated(self):
        self._require_valid()
        return self._groups is not None and self._metadata_rows is not None

    def group_metadata_cache_estimated_bytes(self):
        """Bounded by group_count/metadata_row_count (43/54 for the
        official Master) -- decoded once, cached, independent of
        occurrence_count/fold_count. 0 if not yet populated."""
        self._require_valid()
        if self._groups is None:
            return 0
        total = len(self._groups) * fmt.GROUP_TABLE_ROW_SIZE
        if self._metadata_rows is not None:
            total += len(self._metadata_rows) * fmt.METADATA_TABLE_ROW_SIZE
        total += len(self._group_full_path_cache) * 64  # rough per-path string estimate
        return total

    def resource_snapshot(self):
        """One consolidated, qualification-only resource-counter dict for
        C0.4's required per-phase cache-counter reporting. This provider
        has NO fold-level/family-level persistent cache (Gate B's own
        finding: every lookup_fold call re-does its own bounded binary
        search and family decode; nothing fold-specific is cached across
        calls) -- reported explicitly as 0/None here rather than omitted,
        so "no cache exists yet at that granularity" is a stated fact, not
        a silent gap."""
        self._require_valid()
        return {
            "packed_backing_bytes": self.packed_backing_bytes(),
            "string_cache_entries": self.string_cache_entry_count(),
            "string_cache_estimated_bytes": self.string_cache_estimated_bytes(),
            "group_metadata_cache_populated": self.group_metadata_cache_populated(),
            "group_metadata_cache_estimated_bytes": self.group_metadata_cache_estimated_bytes(),
            "family_cache_entries": 0,
            "family_cache_estimated_bytes": 0,
            "negative_cache_entries": 0,
        }

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
