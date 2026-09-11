"""Phase B2C Part 2: HEADER / SECTION DIRECTORY structural validation.

Every mutation here is CHECKSUM-VALID (the embedded integrity digest is
recomputed over the mutated bytes via `corruption_helpers.MutableSidecar.
recompute_checksum`) -- proving the reader's structural checks, not merely
its checksum comparison, catch each defect. See `test_basic_corruption.py`
(Phase B2B) for the CHECKSUM-INVALID contrast cases (wrong magic, bad
checksum, unsupported versions), which are retained unchanged.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(HERE))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402
from corruption_helpers import MutableSidecar, compiled_fixture  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _mutable():
    data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, "06_sibling_groups.txt")
    return data, result, MutableSidecar(blob)


class HeaderDirectoryCorruptionTests(unittest.TestCase):

    def _assert_rejected(self, m, result):
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(m.bytes(), result.source_sha256)

    def test_duplicate_section_id_rejected(self):
        data, result, m = _mutable()
        rows = m.directory_rows()
        idx_child = next(i for i, (o, r) in enumerate(rows) if r.section_id == fmt.SECTION_CHILD_ID_INDEX)
        m.set_directory_row_at_index(idx_child, section_id=fmt.SECTION_OCCURRENCE_BY_GROUP_INDEX)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_missing_required_section_rejected(self):
        # Same underlying mutation as duplicate-section-id: overwriting one
        # section_id with another's necessarily makes the original section
        # ID vanish from the declared set -- both facts are checked, and
        # either one alone is sufficient grounds for rejection.
        data, result, m = _mutable()
        rows = m.directory_rows()
        idx_fold = next(i for i, (o, r) in enumerate(rows) if r.section_id == fmt.SECTION_FOLD_TABLE)
        m.set_directory_row_at_index(idx_fold, section_id=fmt.SECTION_METADATA_TABLE)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_unrecognized_section_id_rejected(self):
        data, result, m = _mutable()
        m.set_directory_row_at_index(0, section_id=999)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_wrong_normative_row_size_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_STRING_TABLE)
        # Halve row_size while doubling row_count to keep row_count*row_size
        # == length intact -- isolates the "file-declared row_size does not
        # match the reader's own normative constant" check specifically.
        m.set_directory_row(fmt.SECTION_STRING_TABLE, row_size=4, row_count=row.row_count * 2)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_section_offset_overlapping_header_rejected(self):
        data, result, m = _mutable()
        m.set_directory_row(fmt.SECTION_GROUP_TABLE, offset=0)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_section_offset_overlapping_directory_rejected(self):
        data, result, m = _mutable()
        header = m.header()
        m.set_directory_row(fmt.SECTION_GROUP_TABLE, offset=header.section_directory_offset)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_section_overlapping_another_section_rejected(self):
        data, result, m = _mutable()
        _, other = m.directory_row_for(fmt.SECTION_FOLD_TABLE)
        m.set_directory_row(fmt.SECTION_GROUP_TABLE, offset=other.offset)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_section_end_past_eof_rejected(self):
        data, result, m = _mutable()
        total_len = len(m.buf)
        _, row = m.directory_row_for(fmt.SECTION_OCCURRENCE_TABLE)
        m.set_directory_row(fmt.SECTION_OCCURRENCE_TABLE, length=total_len + 1000)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_impossible_offset_arithmetic_rejected(self):
        data, result, m = _mutable()
        # A huge, but still u64-representable, offset -- Python's
        # arbitrary-precision ints mean no classic wraparound occurs, but
        # the bounds check (offset + length > payload_length) still must
        # catch this as an impossible range (final spec Section 20.A).
        m.set_directory_row(fmt.SECTION_GROUP_TABLE, offset=2 ** 60)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_row_count_times_row_size_inconsistent_with_length_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_GROUP_TABLE)
        m.set_directory_row(fmt.SECTION_GROUP_TABLE, row_count=row.row_count + 1)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_malformed_directory_cardinality_rejected(self):
        data, result, m = _mutable()
        header = m.header()
        m.set_header_fields(section_count=header.section_count - 1)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_no_reserved_fields_exist_in_this_format(self):
        # Documented, not silently skipped (Phase B2C Part 2): the current
        # HEADER/DIRECTORY layout (final spec Sections 6/7/17) defines no
        # field that is merely reserved-and-must-be-zero -- every field is
        # either meaningful data or the embedded digest (already covered by
        # test_basic_corruption.py's checksum tests). There is nothing for a
        # "nonzero reserved field" test to target in this format version.
        self.assertNotIn("reserved", [f for f in fmt.Header._fields])
        self.assertNotIn("reserved", [f for f in fmt.DirectoryRow._fields])


class PairedChecksumValidVsInvalidTests(unittest.TestCase):
    """Part 21: explicit side-by-side demonstration that the SAME structural
    mutation is rejected via two DIFFERENT mechanisms depending on whether
    the checksum was recomputed -- proving both branches are real and
    distinct, not just "some rejection happened.\""""

    def test_wrong_row_size_checksum_invalid_vs_checksum_valid(self):
        data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, "06_sibling_groups.txt")

        # CHECKSUM INVALID: mutate the field, do NOT recompute the digest.
        m_invalid = MutableSidecar(blob)
        _, row = m_invalid.directory_row_for(fmt.SECTION_STRING_TABLE)
        m_invalid.set_directory_row(fmt.SECTION_STRING_TABLE, row_size=4, row_count=row.row_count * 2)
        with self.assertRaises(reader.AuthorityUnavailable) as ctx_invalid:
            reader.SidecarReader.open_generation(m_invalid.bytes(), result.source_sha256)
        self.assertIn("embedded_integrity_digest", str(ctx_invalid.exception))

        # CHECKSUM VALID (same mutation, digest recomputed): must STILL be
        # rejected, but now at the structural row_size check specifically.
        m_valid = MutableSidecar(blob)
        m_valid.set_directory_row(fmt.SECTION_STRING_TABLE, row_size=4, row_count=row.row_count * 2)
        m_valid.recompute_checksum()
        with self.assertRaises(reader.AuthorityUnavailable) as ctx_valid:
            reader.SidecarReader.open_generation(m_valid.bytes(), result.source_sha256)
        self.assertIn("row_size", str(ctx_valid.exception))
        self.assertNotIn("embedded_integrity_digest", str(ctx_valid.exception))

    def test_self_parent_group_checksum_invalid_vs_checksum_valid(self):
        data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, "06_sibling_groups.txt")

        m_invalid = MutableSidecar(blob)
        m_invalid.set_group_row(1, parent_path_id=1)
        with self.assertRaises(reader.AuthorityUnavailable) as ctx_invalid:
            reader.SidecarReader.open_generation(m_invalid.bytes(), result.source_sha256)
        self.assertIn("embedded_integrity_digest", str(ctx_invalid.exception))

        m_valid = MutableSidecar(blob)
        m_valid.set_group_row(1, parent_path_id=1)
        m_valid.recompute_checksum()
        with self.assertRaises(reader.AuthorityUnavailable) as ctx_valid:
            reader.SidecarReader.open_generation(m_valid.bytes(), result.source_sha256)
        self.assertIn("anti-cycle", str(ctx_valid.exception))


if __name__ == "__main__":
    unittest.main()
