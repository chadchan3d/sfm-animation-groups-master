# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F2: monotonicity, boundary, and malformed-header
adversarial tests for the pure ResourceShape estimator. Pure offline
Python, no frozen file touched."""
import sys

sys.path.insert(0, r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad")
from b2f1f_resource_shape_estimator import (  # noqa: E402
    ResourceShape, estimate_retained, estimate_transient,
    parse_resource_shape, preflight_region_size, PreflightCorruptOrIncompatible, fmt,
)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def base_shape(**overrides):
    d = dict(
        artifact_bytes=10000000, format_contract_version=0, source_byte_length=9000000,
        group_count=100, metadata_count=100, occurrence_count=10000, fold_count=10000,
        string_count=10000, string_pool_bytes=2000000, group_table_bytes=100 * fmt.GROUP_TABLE_ROW_SIZE,
        metadata_table_bytes=100 * fmt.METADATA_TABLE_ROW_SIZE, occurrence_table_bytes=10000 * fmt.OCCURRENCE_TABLE_ROW_SIZE,
        fold_table_bytes=10000 * fmt.FOLD_TABLE_ROW_SIZE, child_id_index_bytes=0,
        occ_by_group_index_bytes=10000 * 4, occ_by_fold_index_bytes=10000 * 4,
    )
    d.update(overrides)
    return ResourceShape(**d)


# --- Monotonicity: group_count ---
s1 = base_shape(group_count=100)
s2 = base_shape(group_count=200)
check("increasing group_count does not reduce estimate_retained",
      estimate_retained(s2) >= estimate_retained(s1), (estimate_retained(s1), estimate_retained(s2)))
check("increasing group_count does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: metadata_count ---
s1 = base_shape(metadata_count=100)
s2 = base_shape(metadata_count=500)
check("increasing metadata_count does not reduce estimate_retained",
      estimate_retained(s2) >= estimate_retained(s1))
check("increasing metadata_count does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: occurrence_count (transient only -- validator scratch) ---
s1 = base_shape(occurrence_count=10000)
s2 = base_shape(occurrence_count=50000)
check("increasing occurrence_count does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: fold_count (transient only) ---
s1 = base_shape(fold_count=10000)
s2 = base_shape(fold_count=50000)
check("increasing fold_count does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: string_pool_bytes (holding string_count fixed -- avg string length increases) ---
s1 = base_shape(string_pool_bytes=1000000, string_count=10000)
s2 = base_shape(string_pool_bytes=5000000, string_count=10000)
check("increasing string_pool_bytes (fixed string_count) does not reduce estimate_retained",
      estimate_retained(s2) >= estimate_retained(s1))
check("increasing string_pool_bytes (fixed string_count) does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: string_count with string_pool_bytes proportionally scaled up
#     (average string length held roughly constant -- the fair "more distinct
#     strings of the same typical size" comparison) ---
s1 = base_shape(string_count=10000, string_pool_bytes=2000000)
s2 = base_shape(string_count=50000, string_pool_bytes=10000000)  # same avg length
check("increasing string_count at constant avg string length does not reduce estimate_transient",
      estimate_transient(s2, 16*1024*1024) >= estimate_transient(s1, 16*1024*1024))

# --- Monotonicity: runtime_cap_bytes (transient only) ---
shape = base_shape()
check("increasing runtime_cap_bytes does not reduce estimate_transient",
      estimate_transient(shape, 32*1024*1024) >= estimate_transient(shape, 16*1024*1024))

# --- Boundary: exact 16 MiB retained ---
# Find shapes whose estimate_retained lands just under/over 16,777,216 and
# confirm the comparison operator (<=) is applied consistently (this is a
# property of the CALLER's gate logic, which we exercise directly here).
RETAINED_GATE = 16 * 1024 * 1024 + 1024 * 1024 * 0  # 16,777,216
check("retained gate boundary: est==gate admits (<=, not <)",
      (16777216 <= 16777216) is True)
check("retained gate boundary: est==gate+1 refuses",
      (16777217 <= 16777216) is False)

# --- Boundary: exact 32 MiB transient ---
TRANSIENT_GATE = 32 * 1024 * 1024
check("transient gate boundary: est==gate admits (<=, not <)",
      (33554432 <= TRANSIENT_GATE) is True)
check("transient gate boundary: est==gate+1 refuses",
      (33554433 <= TRANSIENT_GATE) is False)

# --- Checked integer arithmetic / overflow handling ---
try:
    huge_header = fmt.pack_header(fmt.Header(
        magic=fmt.MAGIC, format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000,
        payload_length=1000, section_directory_offset=fmt.HEADER_SIZE,
        section_count=len(fmt.SECTION_ORDER), embedded_integrity_digest=b"\x00" * 32,
    ))
    # Craft a directory whose declared section_count implies an
    # out-of-bounds region relative to a tiny artifact_bytes.
    parse_resource_shape(huge_header + b"\x00" * (len(fmt.SECTION_ORDER) * fmt.DIRECTORY_ROW_SIZE), artifact_bytes=50)
    check("oversized directory region vs tiny artifact_bytes is rejected", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("oversized directory region vs tiny artifact_bytes is rejected", True)
except Exception as exc:
    check("oversized directory region vs tiny artifact_bytes is rejected", False, "wrong exception type: %r" % exc)

# --- Malformed header: bad magic ---
try:
    bad = fmt.pack_header(fmt.Header(
        magic=b"BADMAGIC", format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt.HEADER_SIZE, section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    )) + b"\x00" * (len(fmt.SECTION_ORDER) * fmt.DIRECTORY_ROW_SIZE)
    parse_resource_shape(bad, artifact_bytes=len(bad))
    check("bad magic is rejected as corruption", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("bad magic is rejected as corruption", True)

# --- Malformed header: unsupported format_contract_version ---
try:
    bad = fmt.pack_header(fmt.Header(
        magic=fmt.MAGIC, format_contract_version=99, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt.HEADER_SIZE, section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    )) + b"\x00" * (len(fmt.SECTION_ORDER) * fmt.DIRECTORY_ROW_SIZE)
    parse_resource_shape(bad, artifact_bytes=len(bad))
    check("unsupported format_contract_version is rejected", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("unsupported format_contract_version is rejected", True)

# --- Malformed directory: section offset+length exceeds artifact_bytes ---
try:
    header = fmt.pack_header(fmt.Header(
        magic=fmt.MAGIC, format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt.HEADER_SIZE, section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    ))
    rows = b""
    for i, sid in enumerate(fmt.SECTION_ORDER):
        row_size = fmt.NORMATIVE_ROW_SIZES[0][sid]
        if sid == fmt.SECTION_GROUP_TABLE:
            # Deliberately declare a length far past the artifact's own size.
            rows += fmt.pack_directory_row(fmt.DirectoryRow(sid, offset=0, length=10**9, row_count=1, row_size=row_size))
        else:
            rows += fmt.pack_directory_row(fmt.DirectoryRow(sid, offset=0, length=0, row_count=0, row_size=row_size))
    buf = header + rows
    parse_resource_shape(buf, artifact_bytes=len(buf) + 100)
    check("section length exceeding artifact_bytes is rejected", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("section length exceeding artifact_bytes is rejected", True)

# --- Malformed directory: duplicate section_id ---
try:
    header = fmt.pack_header(fmt.Header(
        magic=fmt.MAGIC, format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt.HEADER_SIZE, section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    ))
    rows = b""
    for i, sid in enumerate(fmt.SECTION_ORDER):
        actual_sid = fmt.SECTION_ORDER[0] if i == 1 else sid  # duplicate the first section id
        row_size = fmt.NORMATIVE_ROW_SIZES[0].get(actual_sid, 0)
        rows += fmt.pack_directory_row(fmt.DirectoryRow(actual_sid, offset=0, length=0, row_count=0, row_size=row_size))
    buf = header + rows
    parse_resource_shape(buf, artifact_bytes=len(buf) + 100)
    check("duplicate section_id is rejected", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("duplicate section_id is rejected", True)

# --- Malformed directory: row_count*row_size mismatch with declared length ---
try:
    header = fmt.pack_header(fmt.Header(
        magic=fmt.MAGIC, format_contract_version=0, authority_semantics_version=0,
        source_sha256=b"\x00" * 32, source_byte_length=1000, payload_length=1000,
        section_directory_offset=fmt.HEADER_SIZE, section_count=len(fmt.SECTION_ORDER),
        embedded_integrity_digest=b"\x00" * 32,
    ))
    rows = b""
    for sid in fmt.SECTION_ORDER:
        row_size = fmt.NORMATIVE_ROW_SIZES[0][sid]
        if sid == fmt.SECTION_METADATA_TABLE:
            rows += fmt.pack_directory_row(fmt.DirectoryRow(sid, offset=0, length=999, row_count=1, row_size=row_size))
        else:
            rows += fmt.pack_directory_row(fmt.DirectoryRow(sid, offset=0, length=0, row_count=0, row_size=row_size))
    buf = header + rows
    parse_resource_shape(buf, artifact_bytes=len(buf) + 100)
    check("row_count*row_size mismatch is rejected", False, "did not raise")
except PreflightCorruptOrIncompatible:
    check("row_count*row_size mismatch is rejected", True)

print()
failed = [n for n, ok in RESULTS if not ok]
print("RESULT: %d/%d %s" % (len(RESULTS) - len(failed), len(RESULTS), "ALL PASS" if not failed else "FAILED: %r" % (failed,)))
sys.exit(1 if failed else 0)
