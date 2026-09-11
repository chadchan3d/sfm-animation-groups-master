"""Phase B2C: TEST-ONLY structural-corruption mutation framework.

Not part of production code (`tools/sfm_master_sidecar/`) -- this module
exists purely so tests can compile a valid small fixture, then surgically
mutate one specific binary field/section, correctly recompute the embedded
integrity digest (or deliberately NOT recompute it, for the contrasting
"checksum invalid" category), and reopen with the *production* reader to
require rejection.

The whole point (final spec Section 39's checksum-aware doctrine, Phase B2C
Part 1): a test that corrupts bytes WITHOUT recomputing the checksum only
proves checksum validation works. Proving structural validation actually
pulls its own weight requires the CHECKSUM-VALID form -- digest recomputed
over the mutated bytes, so the file "looks" self-consistent by hash, and the
reader must still catch the structural defect on its own.

This module never ships to the embedded runtime and imports whatever it
needs (it doesn't need to be Python-2.7-safe).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sfm_master_sidecar import format as fmt  # noqa: E402


class MutableSidecar(object):
    """A compiled sidecar byte buffer, wrapped for field-level test mutation."""

    def __init__(self, blob):
        self.buf = bytearray(blob)

    def bytes(self):
        return bytes(self.buf)

    # -- Header / Directory --

    def header(self):
        return fmt.unpack_header(bytes(self.buf))

    def set_header_fields(self, **overrides):
        h = self.header()
        kwargs = h._asdict()
        kwargs.update(overrides)
        new_h = fmt.Header(**kwargs)
        self.buf[0:fmt.HEADER_SIZE] = fmt.pack_header(new_h)

    def directory_rows(self):
        """List of (byte_offset_of_row, DirectoryRow)."""
        h = self.header()
        rows = []
        for i in range(h.section_count):
            off = h.section_directory_offset + i * fmt.DIRECTORY_ROW_SIZE
            rows.append((off, fmt.unpack_directory_row(bytes(self.buf), off)))
        return rows

    def directory_row_for(self, section_id):
        for off, row in self.directory_rows():
            if row.section_id == section_id:
                return off, row
        raise KeyError("no directory row for section_id %r" % (section_id,))

    def set_directory_row(self, section_id, **overrides):
        off, row = self.directory_row_for(section_id)
        kwargs = row._asdict()
        kwargs.update(overrides)
        new_row = fmt.DirectoryRow(**kwargs)
        self.buf[off:off + fmt.DIRECTORY_ROW_SIZE] = fmt.pack_directory_row(new_row)

    def set_directory_row_at_index(self, index, **overrides):
        """Mutate the directory row at a raw positional index (needed for
        duplicate/missing-section-id tests, where `section_id` itself is the
        field being overwritten and `directory_row_for` can no longer
        disambiguate by the ORIGINAL section_id after the mutation)."""
        h = self.header()
        off = h.section_directory_offset + index * fmt.DIRECTORY_ROW_SIZE
        row = fmt.unpack_directory_row(bytes(self.buf), off)
        kwargs = row._asdict()
        kwargs.update(overrides)
        new_row = fmt.DirectoryRow(**kwargs)
        self.buf[off:off + fmt.DIRECTORY_ROW_SIZE] = fmt.pack_directory_row(new_row)

    def section_bytes(self, section_id):
        _, row = self.directory_row_for(section_id)
        return bytes(self.buf[row.offset:row.offset + row.length])

    def patch_raw(self, offset, data):
        self.buf[offset:offset + len(data)] = data

    # -- Row-level setters, by section + row index --

    def _row_offset(self, section_id, row_index, row_size):
        _, row = self.directory_row_for(section_id)
        return row.offset + row_index * row_size

    def set_string_table_row(self, string_id, **overrides):
        off = self._row_offset(fmt.SECTION_STRING_TABLE, string_id, fmt.STRING_TABLE_ROW_SIZE)
        old = fmt.unpack_string_table_row(bytes(self.buf), off)
        kwargs = old._asdict()
        kwargs.update(overrides)
        new = fmt.StringTableRow(**kwargs)
        self.buf[off:off + fmt.STRING_TABLE_ROW_SIZE] = fmt.pack_string_table_row(new)

    def set_group_row(self, path_id, **overrides):
        off = self._row_offset(fmt.SECTION_GROUP_TABLE, path_id, fmt.GROUP_TABLE_ROW_SIZE)
        old = fmt.unpack_group_table_row(bytes(self.buf), off)
        kwargs = old._asdict()
        kwargs.update(overrides)
        new = fmt.GroupTableRow(**kwargs)
        self.buf[off:off + fmt.GROUP_TABLE_ROW_SIZE] = fmt.pack_group_table_row(new)

    def get_group_row(self, path_id):
        off = self._row_offset(fmt.SECTION_GROUP_TABLE, path_id, fmt.GROUP_TABLE_ROW_SIZE)
        return fmt.unpack_group_table_row(bytes(self.buf), off)

    def set_child_id_index_entry(self, index, child_path_id):
        off = self._row_offset(fmt.SECTION_CHILD_ID_INDEX, index, fmt.CHILD_ID_INDEX_ROW_SIZE)
        self.buf[off:off + fmt.CHILD_ID_INDEX_ROW_SIZE] = fmt.pack_child_id_index_row(child_path_id)

    def get_child_id_index_entry(self, index):
        off = self._row_offset(fmt.SECTION_CHILD_ID_INDEX, index, fmt.CHILD_ID_INDEX_ROW_SIZE)
        return fmt.unpack_child_id_index_row(bytes(self.buf), off)

    def set_metadata_row(self, index, **overrides):
        off = self._row_offset(fmt.SECTION_METADATA_TABLE, index, fmt.METADATA_TABLE_ROW_SIZE)
        old = fmt.unpack_metadata_table_row(bytes(self.buf), off)
        kwargs = old._asdict()
        kwargs.update(overrides)
        new = fmt.MetadataTableRow(**kwargs)
        self.buf[off:off + fmt.METADATA_TABLE_ROW_SIZE] = fmt.pack_metadata_table_row(new)

    def set_occurrence_row(self, global_rank, **overrides):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_TABLE, global_rank, fmt.OCCURRENCE_TABLE_ROW_SIZE)
        old = fmt.unpack_occurrence_table_row(bytes(self.buf), off)
        kwargs = old._asdict()
        kwargs.update(overrides)
        new = fmt.OccurrenceTableRow(**kwargs)
        self.buf[off:off + fmt.OCCURRENCE_TABLE_ROW_SIZE] = fmt.pack_occurrence_table_row(new)

    def get_occurrence_row(self, global_rank):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_TABLE, global_rank, fmt.OCCURRENCE_TABLE_ROW_SIZE)
        return fmt.unpack_occurrence_table_row(bytes(self.buf), off)

    def set_occ_by_group_index_entry(self, index, global_rank):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX, index, fmt.OCC_BY_GROUP_INDEX_ROW_SIZE)
        self.buf[off:off + fmt.OCC_BY_GROUP_INDEX_ROW_SIZE] = fmt.pack_occ_by_group_index_row(global_rank)

    def get_occ_by_group_index_entry(self, index):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX, index, fmt.OCC_BY_GROUP_INDEX_ROW_SIZE)
        return fmt.unpack_occ_by_group_index_row(bytes(self.buf), off)

    def set_fold_row(self, fold_id, **overrides):
        off = self._row_offset(fmt.SECTION_FOLD_TABLE, fold_id, fmt.FOLD_TABLE_ROW_SIZE)
        old = fmt.unpack_fold_table_row(bytes(self.buf), off)
        kwargs = old._asdict()
        kwargs.update(overrides)
        new = fmt.FoldTableRow(**kwargs)
        self.buf[off:off + fmt.FOLD_TABLE_ROW_SIZE] = fmt.pack_fold_table_row(new)

    def get_fold_row(self, fold_id):
        off = self._row_offset(fmt.SECTION_FOLD_TABLE, fold_id, fmt.FOLD_TABLE_ROW_SIZE)
        return fmt.unpack_fold_table_row(bytes(self.buf), off)

    def set_occ_by_fold_index_entry(self, index, global_rank):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX, index, fmt.OCC_BY_FOLD_INDEX_ROW_SIZE)
        self.buf[off:off + fmt.OCC_BY_FOLD_INDEX_ROW_SIZE] = fmt.pack_occ_by_fold_index_row(global_rank)

    def get_occ_by_fold_index_entry(self, index):
        off = self._row_offset(fmt.SECTION_OCCURRENCE_BY_FOLD_INDEX, index, fmt.OCC_BY_FOLD_INDEX_ROW_SIZE)
        return fmt.unpack_occ_by_fold_index_row(bytes(self.buf), off)

    def patch_string_pool_byte(self, pool_offset, byte_value):
        _, row = self.directory_row_for(fmt.SECTION_STRING_POOL)
        self.buf[row.offset + pool_offset] = byte_value

    # -- Checksum --

    def recompute_checksum(self):
        """CHECKSUM-VALID mutation path: recompute the embedded digest over
        the CURRENT (already-mutated) buffer, so the file is internally
        self-consistent by hash and any rejection that follows can only be
        attributed to a genuine structural check, never the checksum."""
        off = fmt.embedded_integrity_digest_offset()
        digest = fmt.compute_embedded_integrity_digest(bytes(self.buf), off)
        self.buf[off:off + fmt.SHA256_DIGEST_SIZE] = digest

    def corrupt_checksum_only(self):
        """CHECKSUM-INVALID path: leave the (now-stale) digest exactly as it
        was before this mutation, so the file fails at digest comparison --
        the contrasting case, proving the checksum branch alone is also
        exercised distinctly from the structural branch."""
        pass  # no-op by design: caller mutates fields, never calls recompute_checksum()


def compiled_fixture(core, writer, fixtures_root, name):
    """Compile one B2A `valid/` fixture and return (data, result, blob)."""
    path = fixtures_root / "valid" / name
    data = path.read_bytes()
    result = core.parse_master_bytes(data, source_name=name)
    blob = writer.compile_sidecar(data, result)
    return data, result, blob
