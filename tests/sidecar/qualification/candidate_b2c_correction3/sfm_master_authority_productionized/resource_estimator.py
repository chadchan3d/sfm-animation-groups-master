# -*- coding: utf-8 -*-
"""R3-B2C productionized ResourceShape parser + pre-admission resource
estimator. Byte-identical logic to the qualified B2F1F Stage F1/F2
model (`b2f1f_resource_shape_estimator.py`, estimator_model_version
`b2f1f-v1`, unchanged) -- ported into the shared authority package
namespace for the B2C production-candidate integration.

Reads ONLY the fixed HEADER (108 bytes) and SECTION DIRECTORY (28
bytes/section) -- never decodes STRING_POOL, GROUP_TABLE, METADATA_TABLE,
OCCURRENCE_TABLE, or any other section's actual row content. Uses ONLY
sfm_master_sidecar.format's existing, unmodified struct definitions --
no new sidecar fields invented.

STILL A CANDIDATE, ISOLATED under tests/sidecar/qualification/
candidate_b2c/ -- not the frozen production package. `sfm_master_sidecar`
must already be importable by the time this module is imported (the
caller is responsible for this, exactly as sidecar_contract.py already
assumes for its own `from sfm_master_sidecar import ...` -- no
hardcoded sys.path manipulation lives in this module)."""
from sfm_master_sidecar import format as fmt

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
        # Astra second-correction-gate F2/F5: the raw, already-bounds-
        # validated per-section directory rows (section_id -> the
        # unpacked DIRECTORY_ROW_STRUCT namedtuple: offset/length/
        # row_count/row_size), so packed_family_counts.py can safely
        # index into FOLD_TABLE/STRING_TABLE/STRING_POOL WITHOUT
        # re-deriving or re-validating those offsets, and WITHOUT
        # needing a live BoundedProvider (i.e. before the frozen
        # validator ever runs) -- every offset/length here already
        # passed parse_resource_shape's own containment/row-size checks.
        "directory_rows",
    )

    def __init__(self, **kwargs):
        for k in self.__slots__:
            setattr(self, k, kwargs[k])

    def __repr__(self):
        return "ResourceShape(%s)" % ", ".join(
            "%s=%r" % (k, getattr(self, k)) for k in self.__slots__ if k != "directory_rows"
        )


_MAX_PREFLIGHT_REGION_BYTES = 64 * 1024  # explicit small bound (Section 8 "Bounded"), independent of artifact scale

# Astra post-B2C-B correction gate, finding F1: an absolute, independent
# sanity ceiling on runtime_cap_bytes itself, checked before ANY I/O
# happens (not derived from file content, never file-controlled) -- a
# garbage or hostile cap value must never itself become the size of a
# later `f.read(runtime_cap_bytes + 1)` call. Deliberately far above the
# real 16/32 MiB promotion gates (this is not a new production limit,
# only a backstop against a malformed/hostile cap value reaching I/O).
ABSOLUTE_RUNTIME_CAP_CEILING_BYTES = 256 * 1024 * 1024

try:
    _INT_TYPES = (int, long)  # noqa: F821 -- Python 2.7 only
except NameError:
    _INT_TYPES = (int,)


def validate_runtime_cap_bytes(value):
    """F1 repair step 1: validate type/range BEFORE any I/O. Raises
    PreflightCorruptOrIncompatible (never does any file operation) on a
    non-integer, boolean, non-positive, or absurdly large value. Returns
    `value` unchanged on success, so callers can write
    `runtime_cap_bytes = validate_runtime_cap_bytes(runtime_cap_bytes)`."""
    if isinstance(value, bool) or not isinstance(value, _INT_TYPES):
        raise PreflightCorruptOrIncompatible(
            "runtime_cap_bytes must be a plain integer, got %r (%s)" % (value, type(value).__name__)
        )
    if value <= 0:
        raise PreflightCorruptOrIncompatible("runtime_cap_bytes must be positive, got %r" % (value,))
    if value > ABSOLUTE_RUNTIME_CAP_CEILING_BYTES:
        raise PreflightCorruptOrIncompatible(
            "runtime_cap_bytes %r exceeds the absolute sanity ceiling of %r bytes"
            % (value, ABSOLUTE_RUNTIME_CAP_CEILING_BYTES)
        )
    return value


def _validate_header_and_bound_directory_region(header, artifact_bytes):
    """F1 repair steps 2-3, factored out as the SINGLE source of truth so
    no caller can ever compute a directory-region read size without
    these checks having already run. Uses ONLY the fixed-size header
    fields already unpacked (never re-reads the file) plus
    `artifact_bytes` (an OS-level fstat() size, never file content) --
    every check here can run before a single directory-region byte has
    been read. Returns the checked, SAFE region size (HEADER_SIZE up to
    and including the full directory), which is guaranteed to be both
    `<= _MAX_PREFLIGHT_REGION_BYTES` and `<= artifact_bytes`. Raises
    PreflightCorruptOrIncompatible on any violation, before returning
    anything a caller could use to size a read."""
    if header.magic != fmt.MAGIC:
        raise PreflightCorruptOrIncompatible("magic mismatch")
    if header.format_contract_version not in fmt.NORMATIVE_ROW_SIZES:
        raise PreflightCorruptOrIncompatible(
            "unsupported format_contract_version %r" % (header.format_contract_version,)
        )
    # Checked range/overflow: section_count must be exactly the known
    # section set for this format version -- never trust a larger count
    # that could drive an unbounded directory-region read.
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

    # dir_region_size depends only on section_count, which is ALREADY
    # pinned to the exact expected constant by the check above -- it is
    # not independently file-controlled at this point. The genuinely
    # file-controlled, unbounded-in-principle field is
    # section_directory_offset (this is exactly the field Astra's F1
    # reproduction changed to force a ~1.07 GB requested read): checked
    # here, against artifact_bytes, BEFORE it is ever used to size a
    # read, not merely after.
    dir_region_size = header.section_count * fmt.DIRECTORY_ROW_SIZE
    if dir_region_size > _MAX_PREFLIGHT_REGION_BYTES:
        raise PreflightCorruptOrIncompatible(
            "declared section_count implies a directory region larger than the preflight's "
            "own explicit small bound (%d bytes) -- refusing to trust it" % _MAX_PREFLIGHT_REGION_BYTES
        )
    dir_region_end = header.section_directory_offset + dir_region_size
    if dir_region_end > artifact_bytes:
        raise PreflightCorruptOrIncompatible("section directory region extends past artifact_bytes")
    return dir_region_end


def checked_preflight_region_size(header_bytes, artifact_bytes):
    """F1 repair: the ONLY sanctioned way to compute how many bytes a
    real integration should read to call parse_resource_shape. Unlike
    the old, removed, unchecked preflight_region_size (which returned
    section_directory_offset + section_count*DIRECTORY_ROW_SIZE with NO
    validation at all -- the exact defect Astra's F1 reproduction
    exploited), this function runs the COMPLETE header-level bound
    checks first and raises PreflightCorruptOrIncompatible rather than
    ever returning an unchecked value. Callers must treat this
    exception as 'reject before any further read', never fall through
    to a bigger read."""
    if len(header_bytes) < fmt.HEADER_SIZE:
        raise PreflightCorruptOrIncompatible("buffer shorter than fixed header size")
    header = fmt.unpack_header(header_bytes, 0)
    return _validate_header_and_bound_directory_region(header, artifact_bytes)


def parse_resource_shape(buf_or_prefix, artifact_bytes):
    """`buf_or_prefix`: at least the first HEADER_SIZE + (declared
    section_count * DIRECTORY_ROW_SIZE) bytes of the artifact -- callers
    integrating this for real would read exactly that many bytes from an
    already-open handle (same-handle rule, Section 2 of the design doc),
    sized via `checked_preflight_region_size` (never the removed,
    unchecked `preflight_region_size`). This pure function only ever
    indexes into what it is given; it never reads beyond `artifact_bytes`
    (checked) and never touches STRING_POOL/GROUP_TABLE/METADATA_TABLE/
    OCCURRENCE_TABLE row content.

    Raises PreflightCorruptOrIncompatible for any malformed/inconsistent
    header or directory. Never raises PreflightResourceRefusal itself --
    that is the caller's job, after calling the estimator functions below.
    """
    buf = buf_or_prefix
    if len(buf) < fmt.HEADER_SIZE:
        raise PreflightCorruptOrIncompatible("buffer shorter than fixed header size")

    header = fmt.unpack_header(buf, 0)
    normative_sizes = fmt.NORMATIVE_ROW_SIZES.get(header.format_contract_version)
    dir_region_end = _validate_header_and_bound_directory_region(header, artifact_bytes)
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
        directory_rows=rows,
    )


# Astra post-B2C-B correction gate, finding F1: the unchecked
# preflight_region_size(buf_or_header) function that used to live here
# (HEADER_SIZE, then section_directory_offset + section_count*
# DIRECTORY_ROW_SIZE, with ZERO validation) has been REMOVED entirely,
# not merely deprecated -- it was reproducibly exploitable: a corrupted
# section_directory_offset field alone drove a ~1.07 GB requested read
# before any validation ran. checked_preflight_region_size() above is
# the only sanctioned replacement; it performs the complete header-level
# bound checks BEFORE returning any value a caller could use to size a
# read, and raises PreflightCorruptOrIncompatible instead of returning
# an unchecked number.


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


# === Astra SECOND correction gate, re-opening finding F2 ===
# The FIRST correction attempt added a request-aware term, but it was
# still built on the file-wide AVERAGE occurrences-per-fold
# (occurrence_count/fold_count) scaled by the requested fold COUNT --
# never the real, per-family packed counts. Astra reproduced a valid
# artifact with two 20,000-occurrence families plus 20,000 singleton
# families: the file-wide AVERAGE is tiny (dominated by the singletons),
# so a request for ONLY the two huge families was admitted by the
# average-based estimate while its REAL payload badly exceeded the
# retained gate. An average over the WHOLE file can never bound a
# request that concentrates on the file's own most extreme families --
# this is a structural flaw in the model, not a tunable constant.
#
# Repair: the average-based terms below (`_avg_occurrences_per_fold`,
# `_requested_folded_payload_bytes`) are RENAMED and DEMOTED to an
# explicitly-labeled PRELIMINARY, NON-AUTHORITATIVE early filter only
# (see `estimate_retained_preliminary`/`estimate_transient_preliminary`
# below) -- useful for cheap, header+directory-only rejection of an
# obviously-hopeless whole-artifact shape BEFORE the one full bounded
# read even happens (when no per-family information exists yet), but
# NEVER the final admission decision. The PRIMARY, AUTHORITATIVE
# admission function is `evaluate_cumulative_admission` further below,
# which uses REAL packed per-family occurrence counts (via
# packed_family_counts.py, obtained from the fully-read in-memory
# buffer, before any occurrence row is DECODED) summed exactly over the
# ENTIRE requested cohort -- never an average, never extrapolated.
PER_OCCURRENCE_ROW_DICT_OVERHEAD_BYTES = 260  # 4-key dict (literal/destination/global_index/local_index)
PER_OCCURRENCE_ROW_INT_FIELDS_BYTES = 2 * PER_INT_FIELD_BYTES  # global_index, local_index
PER_FOLD_BUCKET_OVERHEAD_BYTES = 80  # folded[fold] = [...] dict-of-list bucket overhead, once per requested fold

# Astra second-correction-gate Section 4: DEMOTED from "primary safety
# proof" to an explicitly SECONDARY, experimental ceiling. It does NOT
# by itself prove resource safety (two families of exactly this size
# can still blow the retained gate together -- see the cumulative
# function below, which is now the actual authority). Retained only as
# an additional fail-closed backstop, enforced from the REAL PACKED
# count (via packed_family_counts.py) BEFORE any occurrence row is
# decoded -- never implying "exactly 20,000 always admits" (the
# cumulative check can still refuse well below this count) and never
# substituting for cumulative byte budgeting. The real canonical
# Master's observed maximum single-family size is 7; this value has NO
# corpus-derived justification -- see the correction report's own
# explicit flag on this point, carried forward unchanged from the first
# correction gate.
MAX_SINGLE_FOLD_OCCURRENCE_ROWS = 20000


def _avg_occurrences_per_fold(shape):
    """PRELIMINARY/NON-AUTHORITATIVE only -- see module-level note above.
    A file-WIDE average can never bound a request concentrated on the
    file's own most extreme families (Astra's exact reproduction)."""
    if shape.fold_count <= 0:
        return 0
    return shape.occurrence_count / float(shape.fold_count)


def _requested_folded_payload_bytes_preliminary(shape, requested_fold_count):
    """PRELIMINARY/NON-AUTHORITATIVE early estimate only, using the
    file-wide average -- see module-level note above for why this can
    never be the final admission decision. Useful only as a cheap,
    header+directory-only, EARLY rejection of an obviously-hopeless
    whole-artifact shape before any per-family information exists."""
    if requested_fold_count <= 0:
        return 0
    effective_folds = min(requested_fold_count, shape.fold_count) if shape.fold_count > 0 else requested_fold_count
    avg_occ = _avg_occurrences_per_fold(shape)
    estimated_occurrence_rows = effective_folds * avg_occ
    per_row_bytes = (
        PER_OCCURRENCE_ROW_DICT_OVERHEAD_BYTES
        + PER_OCCURRENCE_ROW_INT_FIELDS_BYTES
        + 2 * (PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES)  # literal + destination string references
    )
    return int(estimated_occurrence_rows * per_row_bytes + effective_folds * PER_FOLD_BUCKET_OVERHEAD_BYTES)


def _hierarchy_metadata_bytes(shape):
    """The groups/metadata portion of the retained estimate -- EXACT
    from the directory's own row_counts (group_count/metadata_count),
    never averaged, never a function of requested fold count at all.
    Shared, unchanged logic between the preliminary and authoritative
    paths (both need this same real, exact term)."""
    avg_chars = _avg_string_len_chars(shape)
    per_string_bytes = PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES + avg_chars * BYTES_PER_DECODED_CHAR

    per_group_bytes = (
        PER_GROUP_DICT_OVERHEAD_BYTES
        + 4 * PER_INT_FIELD_BYTES
        + per_string_bytes  # name
        + per_string_bytes * FULL_PATH_DEPTH_MULTIPLIER  # full_path (conservative)
        + per_string_bytes  # parent_path
    )
    groups_total = shape.group_count * per_group_bytes

    per_metadata_bytes = PER_METADATA_DICT_OVERHEAD_BYTES + PER_INT_FIELD_BYTES + 2 * per_string_bytes
    metadata_total = shape.metadata_count * per_metadata_bytes + shape.group_count * PER_METADATA_TABLE_DICT_ENTRY_BYTES

    return groups_total + metadata_total


def estimate_retained_preliminary(shape, requested_fold_count=0):
    """RENAMED from the first correction's `estimate_retained` --
    PRELIMINARY, NON-AUTHORITATIVE only (see module-level note above).
    Retained for its legitimate use: a cheap, header+directory-only,
    EARLY rejection filter, before any full read, when no per-family
    packed-count information exists yet. NEVER the final admission
    decision -- callers needing the real, authoritative reservation
    must use `evaluate_cumulative_admission` (below) once real packed
    per-family counts are available."""
    hierarchy_metadata_total = _hierarchy_metadata_bytes(shape)
    folded_payload_total = _requested_folded_payload_bytes_preliminary(shape, requested_fold_count)
    return int(hierarchy_metadata_total + folded_payload_total + FIXED_PAYLOAD_OVERHEAD_BYTES)


# Backward-compatible alias name kept ONLY for any direct caller that
# has not yet been updated to the explicit `_preliminary` name -- new
# code must call `estimate_retained_preliminary` by its real name so the
# "this is not authoritative" fact is visible at every call site.
def estimate_retained(shape, requested_fold_count=0):
    return estimate_retained_preliminary(shape, requested_fold_count=requested_fold_count)


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


def _provider_decode_upper(shape):
    """The provider's own decode-cache cost -- EXACT from directory row
    counts (group_count/metadata_count), never a function of requested
    fold count. Shared, unchanged between preliminary and authoritative
    paths."""
    groups_cache = shape.group_count * (fmt.GROUP_TABLE_ROW_SIZE + GROUP_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES)
    metadata_cache = shape.metadata_count * (fmt.METADATA_TABLE_ROW_SIZE + METADATA_TABLE_ROW_NAMEDTUPLE_OVERHEAD_BYTES)
    string_cache_slots = (shape.group_count + shape.metadata_count) * STRING_CACHE_DICT_SLOT_OVERHEAD_BYTES
    return groups_cache + metadata_cache + string_cache_slots


def estimate_transient_preliminary(shape, runtime_cap_bytes, requested_fold_count=0):
    """RENAMED from the first correction's `estimate_transient` --
    PRELIMINARY, NON-AUTHORITATIVE only; see `estimate_retained_
    preliminary`'s docstring and the module-level note above
    MAX_SINGLE_FOLD_OCCURRENCE_ROWS for why. read_bound = runtime_cap_
    bytes + 1 (B2F1B: Python 2.7's file.read(size) allocates according
    to the REQUESTED size, not the actual bytes returned) -- this part
    remains exact/authoritative regardless of the folded-payload term's
    preliminary status."""
    read_bound = runtime_cap_bytes + 1
    provider_decode_upper = _provider_decode_upper(shape)
    validator_scratch_upper = _validator_scratch_upper(shape)
    projection_upper = estimate_retained_preliminary(shape, requested_fold_count=requested_fold_count)
    return int(
        read_bound + provider_decode_upper + validator_scratch_upper + projection_upper
        + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES + MEASUREMENT_MODEL_GUARD_BYTES
    )


def estimate_transient(shape, runtime_cap_bytes, requested_fold_count=0):
    return estimate_transient_preliminary(shape, runtime_cap_bytes, requested_fold_count=requested_fold_count)


# ===========================================================================
# Astra SECOND correction gate F2 -- THE authoritative, primary admission
# model. Replaces average-family extrapolation with REAL packed
# per-family occurrence counts (from packed_family_counts.py, obtained
# from the fully-read in-memory buffer, before any occurrence row is
# decoded into a Hit/FoldConflict result) summed EXACTLY over the entire
# requested cohort -- across every consumer_kind in one acquisition, and
# combined with the broker's own aggregate ledger (existing retained
# views, other concurrent charges) rather than a single-artifact-in-
# isolation comparison. This is the ONE canonical admission function:
# both the "normal" post-full-read admission AND any snapshot re-
# admission (Astra F5) call THIS SAME function with THE SAME derivation
# logic -- there is no second, reduced-signature admission path
# anywhere in this package.
# ===========================================================================


def estimate_retained_from_packed_counts(shape, packed_family_counts):
    """Real, per-family-exact retained-payload estimate for ONE
    consumer's requested fold set. `packed_family_counts`: {folded_key:
    real_packed_occurrence_count}, as returned by packed_family_counts.
    get_packed_family_counts_batch -- NOT an average, NOT extrapolated;
    every entry is this SPECIFIC fold's REAL count from the FOLD TABLE.
    Astra's own two-large-families reproduction is exactly what this
    fixes: summing REAL per-family counts can never be fooled by other,
    unrelated small/singleton families elsewhere in the same artifact,
    because those families are simply absent from `packed_family_counts`
    (they were never requested)."""
    per_row_bytes = (
        PER_OCCURRENCE_ROW_DICT_OVERHEAD_BYTES
        + PER_OCCURRENCE_ROW_INT_FIELDS_BYTES
        + 2 * PER_STRING_OBJECT_FIXED_OVERHEAD_BYTES
    )
    total_occurrence_rows = sum(packed_family_counts.values())
    folded_payload_total = (
        total_occurrence_rows * per_row_bytes
        + len(packed_family_counts) * PER_FOLD_BUCKET_OVERHEAD_BYTES
    )
    hierarchy_metadata_total = _hierarchy_metadata_bytes(shape)
    return int(hierarchy_metadata_total + folded_payload_total + FIXED_PAYLOAD_OVERHEAD_BYTES)


class CumulativeAdmissionResult(object):
    __slots__ = (
        "admitted", "reason", "per_consumer_retained_bytes", "total_retained_bytes",
        "total_transient_bytes", "aggregate_existing_retained_bytes",
        "max_single_family_count", "max_single_family_fold", "secondary_cap_exceeded",
    )

    def __init__(self, **kwargs):
        for k in self.__slots__:
            setattr(self, k, kwargs.get(k))

    def to_dict(self):
        return dict((k, getattr(self, k)) for k in self.__slots__)


def evaluate_cumulative_admission(shape, per_consumer_packed_family_counts, runtime_cap_bytes,
                                   retained_gate_bytes, transient_gate_bytes,
                                   aggregate_existing_retained_bytes=0,
                                   enforce_secondary_single_family_cap=True):
    """THE canonical, authoritative admission function -- Astra F2 + F5.

    `per_consumer_packed_family_counts`: {consumer_kind: {folded_key:
    real_packed_occurrence_count}} -- one entry per builder/view this
    acquisition will produce; each inner dict comes from
    packed_family_counts.get_packed_family_counts_batch against the
    ACTUAL fully-read buffer.

    `aggregate_existing_retained_bytes`: the broker's own
    AggregateLedger.total_retained_bytes() BEFORE this acquisition's own
    views are added -- so a request that would individually fit but not
    on top of what the process already retains is correctly refused
    (Astra F2's "existing retained views... multiple live leases" ask).

    Conservative by construction: each consumer's own retained cost is
    computed independently and SUMMED (never assuming cross-consumer
    sharing/deduplication) -- this can only over-estimate, never
    under-estimate, the real aggregate cost.

    === Independent-audit NARROW ISSUE D: documented gate semantics ===

    RETAINED GATE (`retained_gate_bytes`, unchanged at 16 MiB): the
    maximum TOTAL retained authority state permitted to exist AFTER this
    acquisition publishes -- `aggregate_existing_retained_bytes +
    total_retained_bytes` (this function's existing `combined_retained_
    bytes`, below). This has always included existing retained state;
    nothing changes here.

    TRANSIENT GATE (`transient_gate_bytes`, unchanged at 32 MiB):
    resolved to interpretation **B** -- total authority-related RESIDENT
    memory pressure during the acquisition window, INCLUDING already-
    retained views, not merely this acquisition's own incoming delta
    (interpretation A). Rationale: every byte counted by `aggregate_
    existing_retained_bytes` is authority-owned memory that is STILL
    resident (not evicted) for the entire duration of a new acquisition
    -- it genuinely contributes to the real peak process memory pressure
    during that window, exactly like this acquisition's own new
    read_bound/provider-decode/validator-scratch/retained terms already
    do. Excluding it would let a process holding a large amount of
    existing retained state admit a large NEW transient acquisition
    whose real concurrent peak (existing + incoming) could exceed the
    32 MiB envelope while the Python-side check itself never saw a
    number bigger than the incoming delta alone -- i.e. the exact class
    of gap Astra's prior wording ("aggregate resident-plus-incoming
    pressure") was asking to close. `aggregate_existing_retained_bytes`
    is therefore now an explicit term in `total_transient_bytes` below,
    not merely in `combined_retained_bytes`. The 16/32 MiB threshold
    CONSTANTS themselves are unchanged; only what feeds the transient
    SUM changed.

    Enforces the SECONDARY single-family cap (Astra Section 4) from the
    REAL packed counts, BEFORE any occurrence row is decoded -- but this
    check is explicitly SECONDARY: passing it does not by itself imply
    admission; the cumulative byte check below still applies and can
    refuse a request that stays under the per-family cap.

    Returns a CumulativeAdmissionResult; never raises directly (callers
    decide how to turn `admitted=False` into an exception)."""
    per_consumer_retained_bytes = {}
    max_single_family_count = 0
    max_single_family_fold = None
    for consumer_kind, packed_counts in per_consumer_packed_family_counts.items():
        for folded_key, count in packed_counts.items():
            if count > max_single_family_count:
                max_single_family_count = count
                max_single_family_fold = (consumer_kind, folded_key)
        per_consumer_retained_bytes[consumer_kind] = estimate_retained_from_packed_counts(shape, packed_counts)

    secondary_cap_exceeded = max_single_family_count > MAX_SINGLE_FOLD_OCCURRENCE_ROWS

    total_retained_bytes = sum(per_consumer_retained_bytes.values())
    combined_retained_bytes = aggregate_existing_retained_bytes + total_retained_bytes

    # Transient peak (Astra Narrow Issue D -- interpretation B, see
    # docstring above): aggregate EXISTING retained state (still
    # resident, not evicted, for the whole acquisition window) +
    # read_bound + provider decode + validator scratch (all exact,
    # shared across every consumer in this ONE acquisition -- decoded
    # once regardless of consumer count) + the retained total for every
    # NEW consumer in this acquisition (all simultaneously live right
    # before provider.close(), per R3-B2F1E's own phase-P5 finding) +
    # fixed margins. `aggregate_existing_retained_bytes` is included
    # here explicitly, not only in `combined_retained_bytes` above --
    # see the docstring's rationale.
    read_bound = runtime_cap_bytes + 1
    provider_decode_upper = _provider_decode_upper(shape)
    validator_scratch_upper = _validator_scratch_upper(shape)
    total_transient_bytes = int(
        aggregate_existing_retained_bytes
        + read_bound + provider_decode_upper + validator_scratch_upper + total_retained_bytes
        + FIXED_TRANSIENT_RUNTIME_OVERHEAD_BYTES + MEASUREMENT_MODEL_GUARD_BYTES
    )

    admitted = True
    reason = None
    if enforce_secondary_single_family_cap and secondary_cap_exceeded:
        admitted = False
        reason = "secondary_single_family_cap_exceeded"
    elif combined_retained_bytes > retained_gate_bytes:
        admitted = False
        reason = "cumulative_retained_exceeds_gate"
    elif total_transient_bytes > transient_gate_bytes:
        admitted = False
        reason = "cumulative_transient_exceeds_gate"

    return CumulativeAdmissionResult(
        admitted=admitted, reason=reason,
        per_consumer_retained_bytes=per_consumer_retained_bytes,
        total_retained_bytes=total_retained_bytes,
        total_transient_bytes=total_transient_bytes,
        aggregate_existing_retained_bytes=aggregate_existing_retained_bytes,
        max_single_family_count=max_single_family_count,
        max_single_family_fold=max_single_family_fold,
        secondary_cap_exceeded=secondary_cap_exceeded,
    )
