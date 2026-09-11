"""Phase B2C Parts 4/5/6: GROUP TABLE, CHILD-ID INDEX, and METADATA TABLE
structural validation. All mutations are CHECKSUM-VALID.
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
# Part 4: GROUP TABLE.
# ---------------------------------------------------------------------------


class GroupTableCorruptionTests(unittest.TestCase):

    def test_invalid_parent_group_id_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(1, parent_path_id=len(result.groups) + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_self_parent_rejected(self):
        # Canonical anti-cycle case; also demonstrated in
        # test_structural_corruption_header.py's checksum-valid/invalid pair.
        data, result, m = _mutable()
        m.set_group_row(2, parent_path_id=2)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_forward_reference_parent_rejected(self):
        # parent_path_id must be < path_id -- a forward reference (pointing
        # at a LATER row) is also an anti-cycle violation, distinct from
        # exact self-reference.
        data, result, m = _mutable()
        m.set_group_row(1, parent_path_id=3)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_duplicate_canonical_path_rejected(self):
        data, result, m = _mutable()
        row1 = m.get_group_row(1)
        row2 = m.get_group_row(2)
        m.set_group_row(2, name_string_id=row1.name_string_id)  # same parent (wrapper), same name
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_name_string_id_rejected(self):
        data, result, m = _mutable()
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_group_row(1, name_string_id=st_count + 10)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_duplicate_declare_order_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(2, declare_order=m.get_group_row(1).declare_order)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_inconsistent_sibling_rank_rejected(self):
        # Swap sibling_rank between two siblings WITHOUT touching the
        # CHILD-ID INDEX array's own physical order -- the index slice
        # expects strictly increasing sibling_rank matching its own
        # position, so this desynchronizes them.
        data, result, m = _mutable()
        r1 = m.get_group_row(1)
        r2 = m.get_group_row(2)
        m.set_group_row(1, sibling_rank=r2.sibling_rank)
        m.set_group_row(2, sibling_rank=r1.sibling_rank)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_metadata_slice_out_of_bounds_rejected(self):
        data, result, m = _mutable()
        md_count = len(m.section_bytes(fmt.SECTION_METADATA_TABLE)) // fmt.METADATA_TABLE_ROW_SIZE
        m.set_group_row(0, metadata_start=md_count + 1, metadata_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_occurrence_by_group_slice_out_of_bounds_rejected(self):
        data, result, m = _mutable()
        occ_count = len(result.occurrences)
        m.set_group_row(1, occ_by_group_start=occ_count + 5, occ_by_group_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_zero_parentless_groups_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(0, parent_path_id=1)  # wrapper now claims a parent -- 0 parentless rows
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_two_parentless_groups_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(1, parent_path_id=fmt.ROOT_SENTINEL)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


# ---------------------------------------------------------------------------
# Part 5: CHILD-ID INDEX.
# ---------------------------------------------------------------------------


class ChildIdIndexCorruptionTests(unittest.TestCase):

    def test_wrong_child_index_row_count_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_CHILD_ID_INDEX)
        m.set_directory_row(fmt.SECTION_CHILD_ID_INDEX, row_count=row.row_count - 1, length=row.length - 4)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_parentless_wrapper_appears_as_a_child_rejected(self):
        data, result, m = _mutable()
        m.set_child_id_index_entry(0, 0)  # wrapper (group 0) listed as a child
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_duplicate_child_reference_leaves_another_missing_rejected(self):
        # In a fixed-size complete-partition array, any duplicate reference
        # necessarily leaves some other non-root group uncovered -- both
        # invariants ("duplicate child reference" and "non-parentless group
        # missing") are violated by this single, minimal mutation.
        data, result, m = _mutable()
        v1 = m.get_child_id_index_entry(1)
        m.set_child_id_index_entry(2, v1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_child_id_rejected(self):
        data, result, m = _mutable()
        m.set_child_id_index_entry(0, len(result.groups) + 1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_child_assigned_under_wrong_parent_rejected(self):
        data, result, m = _mutable("05_nested_groups.txt")
        # B's (group 2) slice should reference C (group 3); point it at A
        # (group 1) instead -- A's real parent is the wrapper (0), not B (2).
        m.set_child_id_index_entry(2, 1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_group_child_slice_gap_rejected(self):
        data, result, m = _mutable()
        m.set_group_row(0, child_count=2)  # wrapper actually has 3 children
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_group_child_slice_overlap_rejected(self):
        data, result, m = _mutable("05_nested_groups.txt")
        # Make B's (group 2) slice start coincide with A's (group 1) slice
        # start -- both then claim the same CHILD-ID INDEX position.
        a_row = m.get_group_row(1)
        m.set_group_row(2, child_index_start=a_row.child_index_start)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_child_slice_out_of_bounds_rejected(self):
        data, result, m = _mutable()
        child_count = len(m.section_bytes(fmt.SECTION_CHILD_ID_INDEX)) // fmt.CHILD_ID_INDEX_ROW_SIZE
        m.set_group_row(0, child_index_start=child_count, child_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


# ---------------------------------------------------------------------------
# Part 6: METADATA TABLE.
# ---------------------------------------------------------------------------


class MetadataTableCorruptionTests(unittest.TestCase):

    def test_invalid_key_string_id_rejected(self):
        data, result, m = _mutable("15_duplicate_metadata_keys.txt")
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_metadata_row(0, key_string_id=st_count + 3)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_value_string_id_rejected(self):
        data, result, m = _mutable("15_duplicate_metadata_keys.txt")
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_metadata_row(0, value_string_id=st_count + 3)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_metadata_slice_gap_rejected(self):
        data, result, m = _mutable("15_duplicate_metadata_keys.txt")
        # "Grp" (group 1) actually owns 2 metadata rows; declare only 1.
        m.set_group_row(1, metadata_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_metadata_slice_overlap_multiply_owned_rejected(self):
        data, result, m = _mutable("15_duplicate_metadata_keys.txt")
        # Wrapper (group 0) falsely claims Grp's (group 1) metadata row 0 too.
        m.set_group_row(0, metadata_start=0, metadata_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_metadata_source_order_not_dense_rejected(self):
        data, result, m = _mutable("15_duplicate_metadata_keys.txt")
        m.set_metadata_row(1, source_order=5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_legal_metadata_semantics_are_never_rejected_as_corruption(self):
        # Duplicate keys, unknown keys, an explicit "0" value, and an empty
        # value are all legal per sfm_master_core -- confirm none of them
        # are ever misclassified as structural corruption.
        for name in [
            "15_duplicate_metadata_keys.txt",
            "16_metadata_value_zero.txt",
            "17_unknown_metadata_key.txt",
            "18_empty_metadata_value.txt",
        ]:
            with self.subTest(fixture=name):
                data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, name)
                r = reader.SidecarReader.open_generation(blob, result.source_sha256)
                self.assertTrue(r.is_valid())


if __name__ == "__main__":
    unittest.main()
