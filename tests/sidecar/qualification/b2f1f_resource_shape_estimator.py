# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F1: pure, test-only ResourceShape parser + pre-admission
resource estimator. Reads ONLY the fixed HEADER (108 bytes) and SECTION
DIRECTORY (28 bytes/section) -- never decodes STRING_POOL, GROUP_TABLE,
METADATA_TABLE, OCCURRENCE_TABLE, or any other section's actual row
content. Uses ONLY sfm_master_sidecar.format's existing, unmodified
struct definitions (HEADER_STRUCT, DIRECTORY_ROW_STRUCT, section IDs) --
no new sidecar fields invented.

NOT wired into any production/frozen code. NOT authorized for
integration -- offline derivation/qualification only, per
R3_B2F1F_Alternative_D_PreAdmission_Estimator_Design_2026-09-16.md
Stage F1.
"""
import sys

sys.path.insert(0, r"E:\SFM Animation Group Master\tools")
from sfm_master_sidecar import format as fmt  # noqa: E402

ESTIMATOR_MODEL_VERSION = "b2f1f-v1"

# ---------------------------------------------------------------------------
# Errors -- distinguishing corruption/incompatibility from resource refusal,
# exactly as the design mandates (Section 7/Section 3 "Parser safety").
# ---------------------------------------------------------------------------


class PreflightCorruptOrIncompatible(Exception):
    """Malformed header/directory structure, or an unsupported format/
    estimator version -- NEVER a resource-refusal outcome."""


class PreflightResourceRefusal(Exception):
    """A structurally valid, parseable candidate whose conservative
    estimate exceeds a resource gate. Carries a diagnostic payload dict
    on .diagnostics -- never collapsed into corruption/missing/generic
    authority-unavailable."""

    def __init__(self, reason, diagnostics):
        super(PreflightResourceRefusal, self).__init__(reason)
        self.reason = reason
        self.diagnostics = diagnostics


# ---------------------------------------------------------------------------
# ResourceShape -- pure structural facts, no payload content.
# ---------------------------------------------------------------------------

class ResourceShape(object):
    __slots__ = (
        "artifact_bytes", "format_contract_version", "source_byte_length",
        "group_count", "metadata_count", "occurrence_count", "fold_count",
        "string_count", "string_pool_bytes", "group_table_bytes",
        "metadata_table_bytes", "occurrence_table_bytes", "fold_table_bytes",
        "child_id_index_bytes", "occ_by_group_index_bytes", "occ_by_fold_index_bytes",
    )

    def __init__(self, **kwargs):
        for k in self.__slots__:
            setattr(self, k, kwargs[k])

    def __repr__(self):
        return "ResourceShape(%s)" % ", ".join("%s=%r" % (k, getattr(self, k)) for k in self.__slots__)


_MAX_PREFLIGHT_REGION_BYTES = 64 * 1024  # explicit small bound (Section 8 "Bounded"), independent of artifact scale


def parse_resource_shape(buf_or_prefix, artifact_bytes):
    """`buf_or_prefix`: at least the first HEADER_SIZE + (declared
    section_count * DIRECTORY_ROW_SIZE) bytes of the artifact -- callers
    integrating this for real would read exactly that many bytes from an
    already-open handle (same-handle rule, Section 2 of the design doc).
    This pure function only ever indexes into what it is given; it never
    reads beyond `artifact_bytes` (checked) and never touches STRING_POOL/
    GROUP_TABLE/METADATA_TABLE/OCCURRENCE_TABLE row content.

    Raises PreflightCorruptOrIncompatible for any malformed/inconsistent
    header or directory. Never raises PreflightResourceRefusal itself --
    that is the caller's job, after calling the estimator functions below.
    """
    buf = buf_or_prefix
    if len(buf) < fmt.HEADER_SIZE:
        raise PreflightCorruptOrIncompatible("buffer shorter than fixed header size")

    header = fmt.unpack_header(buf, 0)
    if header.magic != fmt.MAGIC:
        raise PreflightCorruptOrIncompatible("magic mismatch")
    if header.format_contract_version not in fmt.NORMATIVE_ROW_SIZES:
        raise PreflightCorruptOrIncompatible(
            "unsupported format_contract_version %r" % (header.format_contract_version,)
        )
    # Checked range/overflow: section_count must be exactly the known
    # section set for this format version -- never trust a larger count
    # that could drive an unbounded directory-region read.
    normative_sizes = fmt.NORMATIVE_ROW_SIZES[header.format_contract_version]
    if header.section_count != len(fmt.SECTION_ORDER):
        raise PreflightCorruptOrIncompatible(
            "section_count %r does not match the %d sections this format version defines"
            % (header.section_count, len(fmt.SECTION_ORDER))
        )
    if header.section_directory_offset < fmt.HEADER_SIZE:
        raise PreflightCorruptOrIncompatible("section_directory_offset overlaps the fixed header")
    if header.source_byte_length > fmt.LIMIT_SOURCE_BYTE_SIZE:
        raise PreflightCorruptOrIncompatible("source_byte_length exceeds the format's own absolute ceiling")
    if artifact_bytes > fmt.LIMIT_SIDECAR_BYTE_SIZE:
        raise PreflightCorruptOrIncompatible("artifact_bytes exceeds the format's own absolute ceiling")

    dir_region_size = header.section_count * fmt.DIRECTORY_ROW_SIZE
    # Checked addition -- overflow-safe in Python (ints are arbitrary
    # precision), but still explicitly bounded against the buffer/artifact
    # size rather than trusted.
    dir_region_end = header.section_directory_offset + dir_region_size
    if dir_region_end > artifact_bytes:
        raise PreflightCorruptOrIncompatible("section directory region extends past artifact_bytes")
    if dir_region_size > _MAX_PREFLIGHT_REGION_BYTES:
        raise PreflightCorruptOrIncompatible(
            "declared section_count implies a directory region larger than the preflight's "
            "own explicit small bound (%d bytes) -- refusing to trust it" % _MAX_PREFLIGHT_REGION_BYTES
        )
    if dir_region_end > len(buf):
        raise PreflightCorruptOrIncompatible(
            "caller-supplied prefix buffer does not contain the full declared directory region"
        )

    rows = {}
    seen_ids = set()
    for i in range(header.section_count):
        row_off = header.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE
        row = fmt.unpack_directory_row(buf, row_off)
        if row.section_id not in fmt.SECTION_NAMES:
            raise PreflightCorruptOrIncompatible("unknown section_id %r" % (row.section_id,))
        if row.section_id in seen_ids:
            raise PreflightCorruptOrIncompatible("duplicate section_id %r in directory" % (row.section_id,))
        seen_ids.add(row.section_id)
        # Section-offset + section-size overflow/containment checks --
        # every section's declared [offset, offset+length) must lie fully
        # within the artifact, and its row_size must match the format's
        # own normative row size for that section (never trust the file's
        # own declared row_size to decode with -- format.py's own rule).
        if row.offset > artifact_bytes or row.length > artifact_bytes:
            raise PreflightCorruptOrIncompatible("section %r offset/length individually exceeds artifact_bytes" % (row.section_id,))
        section_end = row.offset + row.length
        if section_end > artifact_bytes:
            raise PreflightCorruptOrIncompatible("section %r [offset, offset+length) exceeds artifact_bytes" % (row.section_id,))
        expected_row_size = normative_sizes.get(row.section_id)
        if row.section_id != fmt.SECTION_STRING_POOL and expected_row_size != row.row_size:
            raise PreflightCorruptOrIncompatible(
                "section %r declared row_size %r does not match the format's normative row_size %r"
                % (row.section_id, row.row_size, expected_row_size)
            )
        if row.row_size != 0 and row.row_count * row.row_size != row.length:
            raise PreflightCorruptOrIncompatible(
                "section %r row_count*row_size (%d) does not match declared length (%d)"
                % (row.section_id, row.row_count * row.row_size, row.length)
            )
        rows[row.section_id] = row

    for sid in fmt.SECTION_ORDER:
        if sid not in rows:
            raise PreflightCorruptOrIncompatible("directory is missing required section_id %r" % (sid,))

    return ResourceShape(
        artifact_bytes=artifact_bytes,
        format_contract_version=header.format_contract_version,
        source_byte_length=header.source_byte_length,
        group_count=rows[fmt.SECTION_GROUP_TABLE].row_count,
        metadata_count=rows[fmt.SECTION_METADATA_TABLE].row_count,
        occurrence_count=rows[fmt.SECTION_OCCURRENCE_TABLE].row_count,
        fold_count=rows[fmt.SECTION_FOLD_TABLE].row_count,
        string_count=rows[fmt.SECTION_STRING_TABLE].row_count,
        string_pool_bytes=rows[fmt.SECTION_STRING_POOL].length,
        group_table_bytes=rows[fmt.SECTION_GROUP_TABLE].length,
        metadata_table_bytes=rows[fmt.SECTION_METADATA_TABLE].length,
        occurrence_table_bytes=rows[fmt.SECTION_OCCURRENCE_TABLE].length,
        fold_table_bytes=rows[fmt.SECTION_FOLD_TABLE].length,
        child_id_index_bytes=rows[fmt.SECTION_CHILD_ID_INDEX].length,
        occ_by_group_index_bytes=rows[fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX].length,
        occ_by_fold_index_bytes=rows[fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX].length,
    )


def preflight_region_size(buf_or_header):
    """How many bytes a real integration needs to read to call
    parse_resource_shape: HEADER_SIZE, then re-read once more with the
    declared section_directory_offset + section_count*DIRECTORY_ROW_SIZE
    once the header is known. Exposed so an integration can size its own
    single same-handle read precisely."""
    header = fmt.unpack_header(buf_or_header, 0)
    return header.section_directory_offset + header.section_count * fmt.DIRECTORY_ROW_SIZE


# ---------------------------------------------------------------------------
# Estimator -- structurally derived from the ACTUAL builder/provider code
# (projections.build_normalizer_like_projection, candidate_packed_provider
# _r3a2b.BoundedProvider.iter_groups/_ensure_groups/_ensure_metadata), not a
# statistical fit. Every constant below is a ROUND, DELIBERATELY
# CONSERVATIVE per-object/per-byte overhead figure for CPython 2.7.5
# 32-bit, chosen to be at or above the largest plausible real overhead
# for that construct, then verified empirically in Section "qualification
# matrix" below to never underestimate any known sample.
# ---------------------------------------------------------------------------

# -- Retained (projection payload) model --
# projections.build_normalizer_like_projection's payload = {
#   "groups": list of group_count dicts, each with 7 fields
#     (path_id:int, name:str, full_path:str, parent_path_id:int,
#      parent_path:str-or-None, declare_order:int, sibling_rank:int),
#   "metadata_by_path": dict of group_count keys -> list of that group's
#     metadata dicts (metadata_count total dicts across all groups), each
#     with 3 fields (key:str, value:str, source_order:int),
#   "lookup_results": tiny, bounded by the fixed literal/vocabulary list
#     length (<=~10 in every real caller) -- negligible, ignored,
#   "wrapper_path": one string -- negligible.
# }
# Per-group dict overhead: a 7-key dict (~280-360 bytes for a small
# CPython 2.7 dict) + 4 int fields (~24 bytes each, since path_id/
# parent_path_id/declare_order/sibling_rank are frequently outside the
# small-int cache) + up to 3 string fields (name, full_path, parent_path)
# whose average length is bounded by string_pool_bytes/string_count
# (average decoded string size) -- full_path additionally concatenates
# ancestor names, conservatively modeled as up to 4x the average string
# length to account for hierarchy depth, since depth is not itself a
# directly available header/directory field.
PER_GROUP_DICT_OVERHEAD_BYTES = 400
PER_INT_FIELD_BYTES = 28
PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES = 60  # PyUnicodeObject header, narrow (UCS-2) CPython 2.7 build
BYTES_PER_DECODED_CHAR = 2
FULL_PATH_DEPTH_MULTIPLIER = 4  # conservative: full_path may repeat ancestor name lengths up to this factor

# Per-metadata-entry dict: 3-key dict (~250 bytes) + 1 int + 2 strings
# (key, value).
PER_METADATA_DICT_OVERHEAD_BYTES = 280
PER_METADATA_TABLE_DICT_ENTRY_BYTES = 80  # metadata_by_path's own dict-of-lists bucket/list overhead per group

FIXED_PAYLOAD_OVERHEAD_BYTES = 4096  # wrapper_path/lookup_results/dict-of-dicts scaffolding, generously rounded


def _avg_string_len_chars(shape):
    if shape.string_count <= 0:
        return 0
    return max(1, shape.string_pool_bytes // shape.string_count)


def estimate_retained(shape):
    """Conservative upper bound (bytes) on the retained detached-view
    payload a Normalizer-like acquisition produces for this shape. Must
    never fall below the EXISTING system's own authoritative post-build
    AggregateLedger estimate (`_estimate_payload_bytes`) for any known
    sample -- verified in the qualification matrix, not assumed."""
    avg_chars = _avg_string_len_chars(shape)
    per_string_bytes = PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES + avg_chars * BYTES_PER_DECODED_CHAR

    # Per group: dict + 4 ints + name string + full_path string (up to
    # FULL_PATH_DEPTH_MULTIPLIER x an average string) + parent_path string.
    per_group_bytes = (
        PER_GROUP_DICT_OVERHEAD_BYTES
        + 4 * PER_INT_FIELD_BYTES
        + per_string_bytes  # name
        + per_string_bytes * FULL_PATH_DEPTH_MULTIPLIER  # full_path (conservative)
        + per_string_bytes  # parent_path
    )
    groups_total = shape.group_count * per_group_bytes

    # Per metadata entry: dict + 1 int + key string + value string, plus
    # the metadata_by_path dict-of-lists bucket overhead once per group.
    per_metadata_bytes = PER_METADATA_DICT_OVERHEAD_BYTES + PER_INT_FIELD_BYTES + 2 * per_string_bytes
    metadata_total = shape.metadata_count * per_metadata_bytes + shape.group_count * PER_METADATA_TABLE_DICT_ENTRY_BYTES

    return int(groups_total + metadata_total + FIXED_PAYLOAD_OVERHEAD_BYTES)


# -- Transient model --
# transient_upper = read_bound + provider_decode_upper + projection_upper
#                   + fixed_overhead_upper
# Only SIMULTANEOUSLY peak-live state (per R3-B2F1E's phase P5 finding:
# provider._buf + provider._groups/_metadata_rows + the payload being
# built are all live at once, right before provider.close()).
GROUP_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES = 120  # namedtuple instance overhead beyond its own packed row bytes
METADATA_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES = 90
STRING_CACHE_DICT_SLOT_OVERHEAD_BYTES = 72  # int key + dict slot; string VALUE objects are shared by reference
                                             # with the payload (provider._string() caches and returns the SAME
                                             # object), so only the dict-slot/key overhead is extra here, never
                                             # double-counting the string content itself.
FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES = 2 * 1024 * 1024  # module import / infra / interpreter overhead margin
# Explicit measurement/model guard (design doc Section 4.2's own listed
# term) -- covers per-loop-iteration transient garbage during the
# validator's array-construction loops and other small effects not
# individually modeled above. Calibrated so NO known sample in the
# qualification corpus is underestimated (see qualification matrix);
# not a statistical fit of the whole model, only this one explicit
# safety-margin term.
MEASUREMENT_MODEL_GUARD_BYTES = 4 * 1024 * 1024

# -- Validator scratch model (candidate_packed_validator_r3a2b.py's own
# Section 20 A-J complete structural validation, which runs INSIDE
# BoundedProvider.open_path -- before the projection builder is ever
# called, but while the just-read buffer is still fully live). Read
# directly from the validator's own source (array.array allocations are
# exact C-level byte costs, not estimates):
#   path_id_col, local_rank_col, fold_id_col: array.array("I") x3,
#     each 4 bytes/occurrence            -> 12 bytes/occurrence
#   fold_key_string_id_col, occ_index_start_col, occ_index_count_col:
#     array.array("I") x3, each 4 bytes/fold -> 12 bytes/fold
#   rank_seen_by_path: one bytearray per group, combined length exactly
#     occurrence_count bytes, plus one bytearray object header per group
#   string_pool_offsets, string_pool_lengths: array.array("I") x2,
#     each 4 bytes/string                -> 8 bytes/string
# This scratch is allocated and freed entirely within validate_packed(),
# strictly before the projection builder runs -- but it is simultaneously
# live with the just-read packed buffer, and is the DOMINANT reason a
# high-occurrence/high-string-count shape (e.g. Family B) peaks higher
# than its group/metadata-driven payload alone would suggest.
BYTES_PER_OCCURRENCE_VALIDATOR_SCRATCH = 12 + 1  # 3 u32 columns + 1 rank_seen_by_path byte
BYTES_PER_FOLD_VALIDATOR_SCRATCH = 12
BYTES_PER_STRING_VALIDATOR_SCRATCH = 8
BYTEARRAY_OBJECT_OVERHEAD_BYTES = 56  # per rank_seen_by_path bytearray instance, one per group


def _validator_scratch_upper(shape):
    return (
        shape.occurrence_count * BYTES_PER_OCCURRENCE_VALIDATOR_SCRATCH
        + shape.fold_count * BYTES_PER_FOLD_VALIDATOR_SCRATCH
        + shape.string_count * BYTES_PER_STRING_VALIDATOR_SCRATCH
        + shape.group_count * BYTEARRAY_OBJECT_OVERHEAD_BYTES
    )


def estimate_transient(shape, runtime_cap_bytes):
    """Conservative upper bound (bytes) on the peak process memory delta
    during one Normalizer-like acquisition of this shape, under the given
    runtime_cap_bytes. For the current frozen bounded-read implementation,
    read_bound = runtime_cap_bytes + 1 (B2F1B: Python 2.7's file.read(size)
    allocates according to the REQUESTED size, not the actual bytes
    returned)."""
    read_bound = runtime_cap_bytes + 1

    # provider._groups: group_count GroupTableRow namedtuples.
    groups_cache = shape.group_count * (fmt.GROUP_TABLE_ROW_SIZE + GROUP_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES)
    # provider._metadata_rows: metadata_count MetadataTableRow namedtuples.
    metadata_cache = shape.metadata_count * (fmt.METADATA_TABLE_ROW_SIZE + METADATA_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES)
    # provider._group_full_path_cache + provider._string_cache: up to
    # group_count + metadata_count distinct decoded strings referenced
    # (names + values are mostly-unique in the worst case); charge only
    # the dict-slot overhead here since string CONTENT is shared by
    # reference with the payload's own strings (not double-counted).
    string_cache_slots = (shape.group_count + shape.metadata_count) * STRING_CACHE_DICT_SLOT_OVERHEAD_BYTES

    provider_decode_upper = groups_cache + metadata_cache + string_cache_slots
    validator_scratch_upper = _validator_scratch_upper(shape)

    projection_upper = estimate_retained(shape)

    return int(
        read_bound + provider_decode_upper + validator_scratch_upper + projection_upper
        + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES + MEASUREMENT_MODEL_GUARD_BYTES
    )
