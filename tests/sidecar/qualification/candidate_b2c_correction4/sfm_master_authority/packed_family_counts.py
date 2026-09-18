# -*- coding: utf-8 -*-
"""Astra second-correction-gate F2/F5: real PACKED per-family occurrence
counts, obtained BEFORE any decoded family expansion AND before the
frozen structural validator (`candidate_packed_validator.validate_packed`)
ever runs -- satisfying Astra's explicit "refusal happens from resource
admission BEFORE validator/projection expansion" requirement.

Operates directly on `(buf, shape)` -- the raw, already-fully-read
in-memory buffer plus a `resource_estimator.ResourceShape` (which now
carries `directory_rows`, the already-bounds-validated per-section
directory rows `parse_resource_shape` produced) -- NEVER a live
`BoundedProvider` instance. This is deliberate: `BoundedProvider.
_open_from_buf` runs the frozen structural validator as an unavoidable
part of construction, so obtaining packed counts via a real provider
instance would require running that validator FIRST, which is exactly
the ordering Astra's test 3 (F5) explicitly checks is NOT the case.

Every offset/length this module indexes into (FOLD_TABLE, STRING_TABLE,
STRING_POOL) has ALREADY passed `parse_resource_shape`'s own
containment/row-size/row-count checks (each section's `[offset,
offset+length)` verified to lie within `artifact_bytes`, `row_size`
verified against the format's own normative value) -- so duplicating
just the read-only binary-search + string-resolution logic here,
against the raw buffer, is safe: it can only read bytes already proven
to lie within the buffer's own real bounds, never index outside them.

Deliberately reaches into `fmt`'s own struct-unpacking helpers, the same
way the frozen provider's own `lookup_fold`/`_string` methods do --
consistent with this codebase's established pattern of candidate-side
introspection into the packed format's own on-disk structures for
read-only purposes.
"""
from sfm_master_sidecar import format as fmt

try:
    _TEXT_TYPES = (str, unicode)  # noqa: F821 -- Python 2.7 only
except NameError:
    _TEXT_TYPES = (str,)


def _to_folded_bytes(folded):
    return folded.encode("utf-8") if isinstance(folded, _TEXT_TYPES) else folded


def _resolve_string(buf, shape, string_id):
    """Byte-for-byte equivalent of BoundedProvider._string(), operating
    on the raw buffer + already-validated directory rows instead of a
    live provider's cached instance state."""
    st_row = shape.directory_rows[fmt.SECTION_STRING_TABLE]
    st_off = st_row.offset + string_id * fmt.STRING_TABLE_ROW_SIZE
    st_blob = buf[st_off: st_off + fmt.STRING_TABLE_ROW_SIZE]
    row = fmt.unpack_string_table_row(st_blob, 0)
    pool_row = shape.directory_rows[fmt.SECTION_STRING_POOL]
    raw = buf[pool_row.offset + row.offset: pool_row.offset + row.offset + row.length]
    return raw.decode("utf-8")


def get_packed_family_occurrence_count(buf, shape, folded_query):
    """Returns the REAL packed `occ_index_count` for `folded_query` (an
    already-ASCII-folded literal) if present in the FOLD TABLE, or 0 if
    genuinely absent (MasterUnknown) -- WITHOUT decoding a single
    occurrence row, and WITHOUT ever constructing a BoundedProvider or
    running the frozen validator. Byte-for-byte equivalent binary search
    to BoundedProvider.lookup_fold, stopping the instant the matching
    fold row's own occ_index_count field is available."""
    folded_bytes = _to_folded_bytes(folded_query)
    fold_table_row = shape.directory_rows[fmt.SECTION_FOLD_TABLE]
    fold_count = fold_table_row.row_count
    fold_table_off = fold_table_row.offset

    def fold_row_at(i):
        blob = buf[fold_table_off + i * fmt.FOLD_TABLE_ROW_SIZE:
                    fold_table_off + (i + 1) * fmt.FOLD_TABLE_ROW_SIZE]
        return fmt.unpack_fold_table_row(blob, 0)

    lo, hi = 0, fold_count
    while lo < hi:
        mid = (lo + hi) // 2
        mid_row = fold_row_at(mid)
        mid_bytes = _resolve_string(buf, shape, mid_row.fold_key_string_id).encode("utf-8")
        if mid_bytes < folded_bytes:
            lo = mid + 1
        elif mid_bytes > folded_bytes:
            hi = mid
        else:
            return fold_row_at(mid).occ_index_count
    return 0


def get_packed_family_counts_batch(buf, shape, folded_queries):
    """{folded_query: packed_occurrence_count} for every entry in
    `folded_queries` -- one bounded binary search per distinct query,
    against the raw buffer, before validation or decode."""
    return dict((q, get_packed_family_occurrence_count(buf, shape, q)) for q in folded_queries)
