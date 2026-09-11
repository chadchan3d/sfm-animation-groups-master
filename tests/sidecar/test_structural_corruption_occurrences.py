"""Phase B2C Parts 7/8: OCCURRENCE TABLE and OCCURRENCE-BY-GROUP INDEX
(complete partition) structural validation. All mutations are CHECKSUM-VALID.
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


def _mutable(name="06_sibling_groups.txt"):
    data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, name)
    return data, result, MutableSidecar(blob)


def _assert_rejected(test, m, result):
    with test.assertRaises(reader.AuthorityUnavailable):
        reader.SidecarReader.open_generation(m.bytes(), result.source_sha256)


# ---------------------------------------------------------------------------
# Part 7: OCCURRENCE TABLE.
# ---------------------------------------------------------------------------


class OccurrenceTableCorruptionTests(unittest.TestCase):

    def test_invalid_literal_string_id_rejected(self):
        data, result, m = _mutable()
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_occurrence_row(0, literal_string_id=st_count + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_destination_path_id_rejected(self):
        data, result, m = _mutable()
        m.set_occurrence_row(0, path_id=len(result.groups) + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_fold_id_rejected(self):
        data, result, m = _mutable()
        fold_count = len(m.section_bytes(fmt.SECTION_FOLD_TABLE)) // fmt.FOLD_TABLE_ROW_SIZE
        m.set_occurrence_row(0, fold_id=fold_count + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_impossible_local_rank_rejected(self):
        data, result, m = _mutable()
        # Group 1 owns exactly one occurrence (local_rank must be 0); make
        # it claim local_rank 5 instead -- not a dense 0..count-1 run.
        m.set_occurrence_row(0, local_rank=5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_global_rank_is_never_a_stored_field(self):
        # Documented, not silently skipped (Phase B2C Part 7): the
        # OCCURRENCE TABLE row does NOT store global_rank as a field at all
        # -- the row's own physical index IS global_rank (final spec Section
        # 12). There is no separate "wrong global-rank representation" case
        # to construct because there is no such field to corrupt.
        self.assertNotIn("global_rank", fmt.OccurrenceTableRow._fields)

    def test_occurrence_table_row_count_inconsistent_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_OCCURRENCE_TABLE)
        m.set_directory_row(fmt.SECTION_OCCURRENCE_TABLE, row_count=row.row_count + 1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_repeated_exact_literals_remain_legal_not_corruption(self):
        for name in [
            "10_repeated_identical_control_one_group.txt",
            "11_repeated_identical_control_across_groups.txt",
        ]:
            with self.subTest(fixture=name):
                data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, name)
                r = reader.SidecarReader.open_generation(blob, result.source_sha256)
                self.assertTrue(r.is_valid())
                self.assertEqual(r.occurrence_count(), len(result.occurrences))


# ---------------------------------------------------------------------------
# Part 8: OCCURRENCE-BY-GROUP INDEX complete partition.
# ---------------------------------------------------------------------------


class OccurrenceByGroupIndexCorruptionTests(unittest.TestCase):

    def test_duplicate_occurrence_reference_leaves_another_missing_rejected(self):
        data, result, m = _mutable()
        v0 = m.get_occ_by_group_index_entry(0)
        m.set_occ_by_group_index_entry(1, v0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_wrong_occurrence_owner_rejected(self):
        # Occurrence 0 (owned by group 1) is repointed to belong to group 2
        # at the OCCURRENCE TABLE level, while the OCCURRENCE-BY-GROUP INDEX
        # slice for group 1 still references it.
        data, result, m = _mutable()
        m.set_occurrence_row(0, path_id=2, local_rank=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_swapped_occurrence_ownership_rejected(self):
        data, result, m = _mutable()
        v0 = m.get_occ_by_group_index_entry(0)
        v2 = m.get_occ_by_group_index_entry(2)
        m.set_occ_by_group_index_entry(0, v2)
        m.set_occ_by_group_index_entry(2, v0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_gap_between_slices_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(1, occ_by_group_count=0)  # group 1 actually owns 1 occurrence
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_unreachable_trailing_index_row_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(3, occ_by_group_count=0)  # last group's occurrence becomes unreachable
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_overlap_between_slices_rejected(self):
        data, result, m = _mutable()
        r1 = m.get_group_row(1)
        m.set_group_row(2, occ_by_group_start=r1.occ_by_group_start)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_out_of_range_occurrence_id_rejected(self):
        data, result, m = _mutable()
        m.set_occ_by_group_index_entry(0, len(result.occurrences) + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_order_reversal_within_group_rejected(self):
        data, result, m = _mutable("10_repeated_identical_control_one_group.txt")
        v0 = m.get_occ_by_group_index_entry(0)
        v2 = m.get_occ_by_group_index_entry(2)
        m.set_occ_by_group_index_entry(0, v2)
        m.set_occ_by_group_index_entry(2, v0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


if __name__ == "__main__":
    unittest.main()
