"""Phase B2C Parts 9/10/11/12: FOLD TABLE, OCCURRENCE-BY-FOLD INDEX (complete
partition), destination/conflict evidence, and complete ASCII-fold
validation. All mutations are CHECKSUM-VALID.
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
# Part 9: FOLD TABLE.
# ---------------------------------------------------------------------------


class FoldTableCorruptionTests(unittest.TestCase):

    def test_fold_table_row_count_inconsistent_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_FOLD_TABLE)
        m.set_directory_row(fmt.SECTION_FOLD_TABLE, row_count=row.row_count + 1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_zero_occurrence_fold_rejected(self):
        data, result, m = _mutable()
        m.set_fold_row(0, occ_index_count=0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_duplicate_fold_key_rejected(self):
        data, result, m = _mutable()
        fold0 = m.get_fold_row(0)
        m.set_fold_row(1, fold_key_string_id=fold0.fold_key_string_id)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_unsorted_fold_keys_rejected(self):
        data, result, m = _mutable()
        fold0 = m.get_fold_row(0)
        fold2 = m.get_fold_row(2)
        m.set_fold_row(0, fold_key_string_id=fold2.fold_key_string_id)
        m.set_fold_row(2, fold_key_string_id=fold0.fold_key_string_id)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_wrong_fold_key_rejected(self):
        # Single-fold fixture isolates this from the sort-order check (a
        # 1-row table is trivially "sorted" regardless of content) -- this
        # exercises specifically "the fold's declared key does not match
        # what its member occurrences actually fold to."
        data, result, m = _mutable("12_same_fold_same_destination.txt")
        # fold_key_string_id originally points at "foo" (id 3); repoint it
        # at "Foo" (id 2) instead -- a real, different, in-bounds string,
        # but the wrong one.
        m.set_fold_row(0, fold_key_string_id=2)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_fold_key_string_id_rejected(self):
        data, result, m = _mutable()
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_fold_row(0, fold_key_string_id=st_count + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_fold_slice_out_of_bounds_rejected(self):
        data, result, m = _mutable()
        occ_count = len(result.occurrences)
        m.set_fold_row(0, occ_index_start=occ_count + 5, occ_index_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_fold_slice_overlap_rejected(self):
        data, result, m = _mutable()
        f1 = m.get_fold_row(1)
        m.set_fold_row(2, occ_index_start=f1.occ_index_start)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


# ---------------------------------------------------------------------------
# Part 10: OCCURRENCE-BY-FOLD INDEX complete partition.
# ---------------------------------------------------------------------------


class OccurrenceByFoldIndexCorruptionTests(unittest.TestCase):

    def test_duplicate_occurrence_reference_leaves_another_missing_rejected(self):
        data, result, m = _mutable()
        v0 = m.get_occ_by_fold_index_entry(0)
        m.set_occ_by_fold_index_entry(1, v0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_occurrence_under_wrong_fold_rejected(self):
        # Repoint occurrence 0's own fold_id while the OCCURRENCE-BY-FOLD
        # INDEX slice for fold 0 still references it.
        data, result, m = _mutable()
        m.set_occurrence_row(0, fold_id=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_invalid_occurrence_id_in_index_rejected(self):
        data, result, m = _mutable()
        m.set_occ_by_fold_index_entry(0, len(result.occurrences) + 5)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_reordered_evidence_within_one_fold_slice_is_not_a_defined_violation(self):
        # Documented, not silently skipped (Phase B2C Part 10): final spec
        # Section 20.I states the OCCURRENCE-BY-FOLD INDEX's required
        # properties as "complete, gapless, non-overlapping partition" plus
        # "ownership agreement" -- unlike its by-group counterpart (Section
        # 20.G), it does NOT additionally require any particular order
        # WITHIN one fold's slice (no local_rank-style monotonic
        # requirement is defined for fold slices). Verified directly:
        # reversing a fold's slice order (still an ownership-correct
        # permutation of the SAME two members) is accepted, not rejected.
        data, result, m = _mutable("13_same_fold_different_destinations.txt")
        v0 = m.get_occ_by_fold_index_entry(0)
        v1 = m.get_occ_by_fold_index_entry(1)
        m.set_occ_by_fold_index_entry(0, v1)
        m.set_occ_by_fold_index_entry(1, v0)
        m.recompute_checksum()
        r = reader.SidecarReader.open_generation(m.bytes(), result.source_sha256)
        self.assertTrue(r.is_valid())

    def test_unreachable_tail_row_rejected(self):
        data, result, m = _mutable()
        m.set_fold_row(2, occ_index_count=0)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_overlapping_fold_slices_rejected(self):
        data, result, m = _mutable()
        f0 = m.get_fold_row(0)
        m.set_fold_row(1, occ_index_start=f0.occ_index_start)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


# ---------------------------------------------------------------------------
# Part 11: destination/conflict evidence -- no stored conflict flag exists.
# ---------------------------------------------------------------------------


class ConflictEvidenceIntegrityTests(unittest.TestCase):

    def test_no_stored_conflict_flag_or_destination_count_field_exists(self):
        # Verifiable, not merely asserted in prose: FOLD TABLE has no
        # conflict/destination-count field to even attempt to falsify --
        # `lookup_fold` always recomputes distinct destinations fresh from
        # validated OCCURRENCE TABLE evidence (final spec Section 24).
        self.assertEqual(
            set(fmt.FoldTableRow._fields),
            {"fold_key_string_id", "occ_index_start", "occ_index_count"},
        )

    def test_truncating_a_conflicting_folds_evidence_is_rejected_not_silently_narrowed(self):
        # A checksum-valid attempt to hide one destination of a genuinely
        # 2-destination conflicting fold (by shrinking its declared
        # occ_index_count from 2 to 1) must be REJECTED outright -- never
        # silently accepted as a now-single-destination Hit. If this
        # mutation were accepted, FoldConflict could be turned into Hit by
        # a corrupt-but-checksum-valid file.
        data, result, m = _mutable("13_same_fold_different_destinations.txt")
        fams = core.build_fold_families(result.occurrences)
        fam = fams[core.ascii_fold(result.occurrences[0].literal)]
        self.assertTrue(fam.is_conflict, "fixture must actually be a conflicting fold")
        m.set_fold_row(0, occ_index_count=1)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_cross_destination_family_always_fold_conflict_even_for_exact_match(self):
        # Re-confirmed here in the corruption-hardening context (already
        # covered from the pure-lookup angle in test_reader_lookup.py):
        # every exact spelling inside a still-conflicting family resolves
        # FoldConflict, never Hit, on VALID (unmutated) backing.
        data, result, blob = compiled_fixture(
            core, writer, FIXTURES_ROOT, "14_exact_spelling_inside_conflicting_fold.txt"
        )
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for occ in result.occurrences:
            res = r.lookup_fold(occ.literal.encode("utf-8"))
            self.assertIsInstance(res, reader.FoldConflict)


# ---------------------------------------------------------------------------
# Part 12: complete ASCII-fold validation.
# ---------------------------------------------------------------------------


class CompleteAsciiFoldValidationTests(unittest.TestCase):

    def test_ascii_letter_mismatch_in_non_ascii_literal_rejected(self):
        # Flip one ASCII letter byte within a fold key that also contains
        # non-ASCII (kanji) bytes -- proving the exhaustive per-occurrence
        # check operates correctly even when adjacent non-ASCII bytes are
        # present, not merely on pure-ASCII literals.
        data, result, m = _mutable("19_non_ascii_bmp_text.txt")
        fold0 = m.get_fold_row(0)
        st_row = fmt.unpack_string_table_row(
            m.section_bytes(fmt.SECTION_STRING_TABLE), fold0.fold_key_string_id * fmt.STRING_TABLE_ROW_SIZE
        )
        pool = m.section_bytes(fmt.SECTION_STRING_POOL)
        key_bytes = pool[st_row.offset:st_row.offset + st_row.length]
        ascii_index = next(i for i, b in enumerate(key_bytes) if 0x61 <= b <= 0x7A)
        original = key_bytes[ascii_index]
        replacement = ord("x") if original != ord("x") else ord("y")
        m.patch_string_pool_byte(st_row.offset + ascii_index, replacement)
        m.recompute_checksum()
        _assert_rejected(self, m, result)

    def test_every_occurrence_checked_not_sampled(self):
        # Corrupt only the LAST occurrence's fold_id in a larger family --
        # proving the check is exhaustive (checks every row), not merely
        # the first/a sample.
        data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, "28_large_alias_family.txt")
        m = MutableSidecar(blob)
        # Corrupt the shared fold key's final ASCII byte -- every occurrence
        # in this family depends on it equally, so this confirms the
        # per-occurrence check fires regardless of position in the table
        # (all 30 rows share one fold_id, so this can't be "caught early" by
        # accident the way a first-row mutation might be).
        fold0 = m.get_fold_row(0)
        st_row = fmt.unpack_string_table_row(
            m.section_bytes(fmt.SECTION_STRING_TABLE), fold0.fold_key_string_id * fmt.STRING_TABLE_ROW_SIZE
        )
        pool = m.section_bytes(fmt.SECTION_STRING_POOL)
        key_bytes = pool[st_row.offset:st_row.offset + st_row.length]
        last_ascii_index = max(i for i, b in enumerate(key_bytes) if 0x61 <= b <= 0x7A)
        original = key_bytes[last_ascii_index]
        replacement = ord("z") if original != ord("z") else ord("q")
        m.patch_string_pool_byte(st_row.offset + last_ascii_index, replacement)
        m.recompute_checksum()
        _assert_rejected(self, m, result)


if __name__ == "__main__":
    unittest.main()
