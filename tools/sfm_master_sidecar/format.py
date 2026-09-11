# -*- coding: utf-8 -*-
"""Experimental packed binary format: constants, struct layouts, versions,
section IDs, sentinels, and checksum/fold helpers only.

Python 2.7 AND Python 3 compatible. Imports nothing beyond the standard
library, and nothing from `tools.sfm_master_core`, `writer`, or any test/CLI
code -- this module is part of the runtime-safe surface a real embedded SFM
Python 2.7 interpreter must be able to import (Phase B2B Part 1 / final spec
Section 27, "Python-2.7 Runtime Boundary").

No I/O, no file/bytes-buffer validation logic lives here -- that is
`reader.py`'s job. This module is purely the byte format expressed as code:
struct format strings, fixed widths, section identifiers, and the two
byte-level helpers (`ascii_fold_bytes`, `sha256_of_bytes_zeroed`) whose exact
behavior the format's correctness depends on.

Normative source: SFM_MASTER_SIDECAR_PHASE_B1_2_FINAL_IMPLEMENTATION_SPEC.md
sections 5-19. Field widths/order here are transcribed from that document's
Section 17 field-width table verbatim -- do not reinterpret or simplify.
"""

import hashlib
import struct
from collections import namedtuple

# ---------------------------------------------------------------------------
# Identity / versioning.
# ---------------------------------------------------------------------------

MAGIC = b"SFMMSTR\x00"  # 8 bytes exactly.
assert len(MAGIC) == 8

# Experimental identifiers (final spec Section 5/44): NOT "1". A real format
# freeze to a stable v1 happens only after Gate 1A+1B+1C ("Final Gate 1") and
# a Gate 2 embedded-SFM measurement -- explicitly out of scope for Phase B2B.
FORMAT_CONTRACT_VERSION_EXPERIMENTAL = 0
AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL = 0

# Sentinel for "this group has no parent" in GROUP TABLE.parent_path_id
# (final spec Section 9/17).
ROOT_SENTINEL = 0xFFFFFFFF

U32_MAX = 0xFFFFFFFF
U64_MAX = 0xFFFFFFFFFFFFFFFF

SHA256_DIGEST_SIZE = 32

# ---------------------------------------------------------------------------
# Resource limits (final spec Section 18). These bound what the WRITER may
# attempt to compile and what the READER will accept as even plausible
# before allocating any buffer sized from a file-declared count -- never
# used to "correct" or clamp a value, only to refuse before allocation.
# ---------------------------------------------------------------------------

LIMIT_SOURCE_BYTE_SIZE = 512 * 1024 * 1024
LIMIT_SIDECAR_BYTE_SIZE = 512 * 1024 * 1024
LIMIT_GROUP_COUNT = 1 << 24
LIMIT_OCCURRENCE_COUNT = 1 << 28
LIMIT_FOLD_COUNT = 1 << 28
LIMIT_DISTINCT_POOL_STRINGS = 1 << 28
LIMIT_STRING_POOL_TOTAL_BYTES = 512 * 1024 * 1024
LIMIT_SINGLE_STRING_BYTE_LENGTH = 1 * 1024 * 1024
LIMIT_METADATA_ROWS_PER_GROUP = 1 << 16
LIMIT_READER_QUERY_BYTE_LENGTH = 4096

# ---------------------------------------------------------------------------
# Section identifiers -- fixed normative order (final spec Section 5).
# INVENTORY FOOTER and per-fold conflict_flag were removed per Astra's
# adopted simplification and do not exist as sections here.
# ---------------------------------------------------------------------------

SECTION_STRING_POOL = 0
SECTION_STRING_TABLE = 1
SECTION_GROUP_TABLE = 2
SECTION_CHILD_ID_INDEX = 3
SECTION_METADATA_TABLE = 4
SECTION_OCCURRENCE_TABLE = 5
SECTION_OCCURRENCE_BY_GROUP_INDEX = 6
SECTION_FOLD_TABLE = 7
SECTION_OCCURRENCE_BY_FOLD_INDEX = 8

SECTION_ORDER = (
    SECTION_STRING_POOL,
    SECTION_STRING_TABLE,
    SECTION_GROUP_TABLE,
    SECTION_CHILD_ID_INDEX,
    SECTION_METADATA_TABLE,
    SECTION_OCCURRENCE_TABLE,
    SECTION_OCCURRENCE_BY_GROUP_INDEX,
    SECTION_FOLD_TABLE,
    SECTION_OCCURRENCE_BY_FOLD_INDEX,
)

SECTION_NAMES = {
    SECTION_STRING_POOL: "STRING_POOL",
    SECTION_STRING_TABLE: "STRING_TABLE",
    SECTION_GROUP_TABLE: "GROUP_TABLE",
    SECTION_CHILD_ID_INDEX: "CHILD_ID_INDEX",
    SECTION_METADATA_TABLE: "METADATA_TABLE",
    SECTION_OCCURRENCE_TABLE: "OCCURRENCE_TABLE",
    SECTION_OCCURRENCE_BY_GROUP_INDEX: "OCCURRENCE_BY_GROUP_INDEX",
    SECTION_FOLD_TABLE: "FOLD_TABLE",
    SECTION_OCCURRENCE_BY_FOLD_INDEX: "OCCURRENCE_BY_FOLD_INDEX",
}

# ---------------------------------------------------------------------------
# Struct layouts. All little-endian, no exceptions (final spec Section 6).
# ---------------------------------------------------------------------------

# HEADER (final spec Section 6 / 17).
HEADER_STRUCT = struct.Struct(
    "<8sII32sQQQI32s"
    # magic, format_contract_version, authority_semantics_version,
    # source_sha256, source_byte_length, payload_length,
    # section_directory_offset, section_count, embedded_integrity_digest
)
HEADER_SIZE = HEADER_STRUCT.size  # 108 bytes

Header = namedtuple(
    "Header",
    [
        "magic",
        "format_contract_version",
        "authority_semantics_version",
        "source_sha256",
        "source_byte_length",
        "payload_length",
        "section_directory_offset",
        "section_count",
        "embedded_integrity_digest",
    ],
)


def pack_header(h):
    return HEADER_STRUCT.pack(
        h.magic,
        h.format_contract_version,
        h.authority_semantics_version,
        h.source_sha256,
        h.source_byte_length,
        h.payload_length,
        h.section_directory_offset,
        h.section_count,
        h.embedded_integrity_digest,
    )


def unpack_header(buf, offset=0):
    fields = HEADER_STRUCT.unpack_from(buf, offset)
    return Header(*fields)


# SECTION DIRECTORY row (final spec Section 7 / 17): one row per section.
DIRECTORY_ROW_STRUCT = struct.Struct("<IQQII")  # section_id, offset, length, row_count, row_size
DIRECTORY_ROW_SIZE = DIRECTORY_ROW_STRUCT.size  # 28 bytes

DirectoryRow = namedtuple(
    "DirectoryRow", ["section_id", "offset", "length", "row_count", "row_size"]
)


def pack_directory_row(r):
    return DIRECTORY_ROW_STRUCT.pack(r.section_id, r.offset, r.length, r.row_count, r.row_size)


def unpack_directory_row(buf, offset=0):
    fields = DIRECTORY_ROW_STRUCT.unpack_from(buf, offset)
    return DirectoryRow(*fields)


# STRING TABLE row (final spec Section 8 / 17): (offset, length) into the
# STRING POOL. STRING POOL itself is a raw contiguous UTF-8 byte blob with no
# row structure of its own; per-section `row_count * row_size == length`
# (Section 20.A) is satisfied generically for it by treating it as
# byte-granular: row_size = 1, row_count = its own byte length.
STRING_TABLE_ROW_STRUCT = struct.Struct("<II")  # offset, length
STRING_TABLE_ROW_SIZE = STRING_TABLE_ROW_STRUCT.size  # 8 bytes
STRING_POOL_ROW_SIZE = 1

StringTableRow = namedtuple("StringTableRow", ["offset", "length"])


def pack_string_table_row(r):
    return STRING_TABLE_ROW_STRUCT.pack(r.offset, r.length)


def unpack_string_table_row(buf, offset=0):
    fields = STRING_TABLE_ROW_STRUCT.unpack_from(buf, offset)
    return StringTableRow(*fields)


# GROUP TABLE row (final spec Section 9 / 17). `path_id` is the row index,
# not a stored field.
GROUP_TABLE_ROW_STRUCT = struct.Struct("<IIIIIIIIII")
GROUP_TABLE_ROW_SIZE = GROUP_TABLE_ROW_STRUCT.size  # 40 bytes

GroupTableRow = namedtuple(
    "GroupTableRow",
    [
        "name_string_id",
        "parent_path_id",
        "declare_order",
        "sibling_rank",
        "child_count",
        "child_index_start",
        "metadata_start",
        "metadata_count",
        "occ_by_group_start",
        "occ_by_group_count",
    ],
)


def pack_group_table_row(r):
    return GROUP_TABLE_ROW_STRUCT.pack(
        r.name_string_id,
        r.parent_path_id,
        r.declare_order,
        r.sibling_rank,
        r.child_count,
        r.child_index_start,
        r.metadata_start,
        r.metadata_count,
        r.occ_by_group_start,
        r.occ_by_group_count,
    )


def unpack_group_table_row(buf, offset=0):
    fields = GROUP_TABLE_ROW_STRUCT.unpack_from(buf, offset)
    return GroupTableRow(*fields)


# CHILD-ID INDEX row (final spec Section 10 / 17): flat u32 array.
CHILD_ID_INDEX_ROW_STRUCT = struct.Struct("<I")
CHILD_ID_INDEX_ROW_SIZE = CHILD_ID_INDEX_ROW_STRUCT.size  # 4 bytes


def pack_child_id_index_row(child_path_id):
    return CHILD_ID_INDEX_ROW_STRUCT.pack(child_path_id)


def unpack_child_id_index_row(buf, offset=0):
    return CHILD_ID_INDEX_ROW_STRUCT.unpack_from(buf, offset)[0]


# METADATA TABLE row (final spec Section 11 / 17).
METADATA_TABLE_ROW_STRUCT = struct.Struct("<IIII")  # path_id, key_string_id, value_string_id, source_order
METADATA_TABLE_ROW_SIZE = METADATA_TABLE_ROW_STRUCT.size  # 16 bytes

MetadataTableRow = namedtuple(
    "MetadataTableRow", ["path_id", "key_string_id", "value_string_id", "source_order"]
)


def pack_metadata_table_row(r):
    return METADATA_TABLE_ROW_STRUCT.pack(r.path_id, r.key_string_id, r.value_string_id, r.source_order)


def unpack_metadata_table_row(buf, offset=0):
    fields = METADATA_TABLE_ROW_STRUCT.unpack_from(buf, offset)
    return MetadataTableRow(*fields)


# OCCURRENCE TABLE row (final spec Section 12 / 17). Row index IS global_rank.
OCCURRENCE_TABLE_ROW_STRUCT = struct.Struct("<IIII")  # literal_string_id, path_id, local_rank, fold_id
OCCURRENCE_TABLE_ROW_SIZE = OCCURRENCE_TABLE_ROW_STRUCT.size  # 16 bytes

OccurrenceTableRow = namedtuple(
    "OccurrenceTableRow", ["literal_string_id", "path_id", "local_rank", "fold_id"]
)


def pack_occurrence_table_row(r):
    return OCCURRENCE_TABLE_ROW_STRUCT.pack(r.literal_string_id, r.path_id, r.local_rank, r.fold_id)


def unpack_occurrence_table_row(buf, offset=0):
    fields = OCCURRENCE_TABLE_ROW_STRUCT.unpack_from(buf, offset)
    return OccurrenceTableRow(*fields)


# OCCURRENCE-BY-GROUP INDEX row (final spec Section 13 / 17): flat u32 array
# of global_rank values.
OCC_BY_GROUP_INDEX_ROW_STRUCT = struct.Struct("<I")
OCC_BY_GROUP_INDEX_ROW_SIZE = OCC_BY_GROUP_INDEX_ROW_STRUCT.size  # 4 bytes


def pack_occ_by_group_index_row(global_rank):
    return OCC_BY_GROUP_INDEX_ROW_STRUCT.pack(global_rank)


def unpack_occ_by_group_index_row(buf, offset=0):
    return OCC_BY_GROUP_INDEX_ROW_STRUCT.unpack_from(buf, offset)[0]


# FOLD TABLE row (final spec Section 14 / 17). No conflict_flag / no
# destination_count -- conflict is always freshly recomputed (Section 24).
FOLD_TABLE_ROW_STRUCT = struct.Struct("<III")  # fold_key_string_id, occ_index_start, occ_index_count
FOLD_TABLE_ROW_SIZE = FOLD_TABLE_ROW_STRUCT.size  # 12 bytes

FoldTableRow = namedtuple(
    "FoldTableRow", ["fold_key_string_id", "occ_index_start", "occ_index_count"]
)


def pack_fold_table_row(r):
    return FOLD_TABLE_ROW_STRUCT.pack(r.fold_key_string_id, r.occ_index_start, r.occ_index_count)


def unpack_fold_table_row(buf, offset=0):
    fields = FOLD_TABLE_ROW_STRUCT.unpack_from(buf, offset)
    return FoldTableRow(*fields)


# OCCURRENCE-BY-FOLD INDEX row (final spec Section 15 / 17): flat u32 array
# of global_rank values.
OCC_BY_FOLD_INDEX_ROW_STRUCT = struct.Struct("<I")
OCC_BY_FOLD_INDEX_ROW_SIZE = OCC_BY_FOLD_INDEX_ROW_STRUCT.size  # 4 bytes


def pack_occ_by_fold_index_row(global_rank):
    return OCC_BY_FOLD_INDEX_ROW_STRUCT.pack(global_rank)


def unpack_occ_by_fold_index_row(buf, offset=0):
    return OCC_BY_FOLD_INDEX_ROW_STRUCT.unpack_from(buf, offset)[0]


# The reader's OWN normative row_size per section, keyed by
# format_contract_version. This is the decoding authority (final spec
# Section 7's correction) -- a file's own declared row_size is only ever
# cross-checked against this table, never used to decode.
NORMATIVE_ROW_SIZES = {
    FORMAT_CONTRACT_VERSION_EXPERIMENTAL: {
        SECTION_STRING_POOL: STRING_POOL_ROW_SIZE,
        SECTION_STRING_TABLE: STRING_TABLE_ROW_SIZE,
        SECTION_GROUP_TABLE: GROUP_TABLE_ROW_SIZE,
        SECTION_CHILD_ID_INDEX: CHILD_ID_INDEX_ROW_SIZE,
        SECTION_METADATA_TABLE: METADATA_TABLE_ROW_SIZE,
        SECTION_OCCURRENCE_TABLE: OCCURRENCE_TABLE_ROW_SIZE,
        SECTION_OCCURRENCE_BY_GROUP_INDEX: OCC_BY_GROUP_INDEX_ROW_SIZE,
        SECTION_FOLD_TABLE: FOLD_TABLE_ROW_SIZE,
        SECTION_OCCURRENCE_BY_FOLD_INDEX: OCC_BY_FOLD_INDEX_ROW_SIZE,
    }
}


# ---------------------------------------------------------------------------
# Byte-level helpers whose exact behavior the format depends on.
# ---------------------------------------------------------------------------


def ascii_fold_bytes(data):
    """Fold ONLY ASCII bytes 0x41-0x5A ('A'-'Z') to +0x20 ('a'-'z'). Every
    other byte, including every byte of a multi-byte UTF-8 sequence, passes
    through unchanged. Provably equivalent to `sfm_master_core.ascii_fold`
    applied before UTF-8 encoding (final spec Section 4's ASCII-fold/UTF-8
    compatibility proof: ASCII byte values 0x41-0x5A never occur as part of
    a multi-byte UTF-8 sequence). Works identically under Python 2.7 (where
    `data` is a `str`/bytes object) and Python 3 (`bytes`)."""
    out = bytearray(data)
    for i in range(len(out)):
        c = out[i]
        if 0x41 <= c <= 0x5A:
            out[i] = c + 0x20
    return bytes(out)


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def sha256_digest(data):
    return hashlib.sha256(data).digest()


def compute_embedded_integrity_digest(buf, digest_field_offset):
    """Return the SHA-256 digest (32 raw bytes) of `buf` with the
    `embedded_integrity_digest` field's own SHA256_DIGEST_SIZE bytes at
    `digest_field_offset` zeroed for the duration of the computation. `buf`
    is never mutated -- the zeroing is performed on a temporary copy."""
    tmp = bytearray(buf)
    tmp[digest_field_offset:digest_field_offset + SHA256_DIGEST_SIZE] = b"\x00" * SHA256_DIGEST_SIZE
    return hashlib.sha256(bytes(tmp)).digest()


# Byte offset of `embedded_integrity_digest` within the packed HEADER --
# computed once here (not re-derived ad hoc by callers) since both writer
# and reader must agree on it exactly.
_EMBEDDED_DIGEST_FIELD_OFFSET = HEADER_STRUCT.size - SHA256_DIGEST_SIZE


def embedded_integrity_digest_offset():
    return _EMBEDDED_DIGEST_FIELD_OFFSET


class SidecarFormatError(Exception):
    """Base class for every exception this package raises. Not itself an
    `AuthorityUnavailable` -- `reader.py` defines that hierarchy, since
    "authority" is a reader-lifetime concept this module has no notion of."""
