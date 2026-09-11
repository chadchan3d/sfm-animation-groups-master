"""Phase B2C Part 3: STRING TABLE / STRING POOL structural validation.

All mutations here are CHECKSUM-VALID (digest recomputed after mutation) --
see test_structural_corruption_header.py's module docstring for why that is
the meaningful form for proving structural checks (not the checksum) reject
the corruption.
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


class StringTableCorruptionTests(unittest.TestCase):

    def _assert_rejected(self, m, result):
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(m.bytes(), result.source_sha256)

    def test_string_range_beyond_pool_rejected(self):
        data, result, m = _mutable()
        pool_len = len(m.section_bytes(fmt.SECTION_STRING_POOL))
        m.set_string_table_row(0, offset=pool_len - 1, length=100)
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_no_distinct_before_pool_case_documented(self):
        # STRING TABLE offsets are zero-based unsigned (u32) values relative
        # to the STRING POOL's own start -- there is no representable
        # "negative"/"before the pool" address distinct from an
        # out-of-bounds-beyond-pool one, since 0 already IS the pool's
        # start. `test_string_range_beyond_pool_rejected` above is the one
        # generic out-of-bounds check that covers both conceptual
        # directions; documented explicitly here rather than silently
        # omitted, per Phase B2C Part 3.
        self.assertTrue(True)

    def test_overlapping_string_ranges_not_a_defined_violation(self):
        # The final spec's Section 20.B only requires (1) every string
        # range in-bounds and (2) every referenced range strictly valid
        # UTF-8 -- it does not forbid two DIFFERENT string_ids from
        # referencing overlapping (or identical) byte ranges within the
        # pool. Two IDs happening to share pool bytes is unusual (the
        # writer's own dedup-by-exact-string logic never produces it) but
        # is not itself a checked structural invariant. Verified directly:
        # constructing this exact scenario and confirming the reader does
        # NOT reject it (documented behavior, not a silent gap -- Phase
        # B2C Part 3's "if prohibited" qualifier applies: it is not
        # prohibited).
        data, result, m = _mutable()
        row0 = fmt.unpack_string_table_row(
            m.section_bytes(fmt.SECTION_STRING_TABLE), 0 * fmt.STRING_TABLE_ROW_SIZE
        )
        m.set_string_table_row(1, offset=row0.offset, length=row0.length)
        m.recompute_checksum()
        r = reader.SidecarReader.open_generation(m.bytes(), result.source_sha256)
        self.assertTrue(r.is_valid())

    def test_malformed_utf8_in_pool_rejected(self):
        data, result, m = _mutable()
        row0 = fmt.unpack_string_table_row(m.section_bytes(fmt.SECTION_STRING_TABLE), 0)
        self.assertGreater(row0.length, 0)
        m.patch_string_pool_byte(row0.offset, 0x80)  # lone continuation byte -- invalid UTF-8 start
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_truncated_multibyte_utf8_rejected(self):
        data, result, blob = compiled_fixture(core, writer, FIXTURES_ROOT, "19_non_ascii_bmp_text.txt")
        m = MutableSidecar(blob)
        pool = bytearray(m.section_bytes(fmt.SECTION_STRING_POOL))
        # Search string table rows for one whose pool bytes start with a
        # multi-byte UTF-8 lead byte (0xC0-0xEF), then truncate its declared
        # length so the continuation byte is cut off.
        target_string_id = None
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        for sid in range(st_count):
            row = fmt.unpack_string_table_row(m.section_bytes(fmt.SECTION_STRING_TABLE), sid * fmt.STRING_TABLE_ROW_SIZE)
            if row.length >= 2 and 0xC0 <= pool[row.offset] <= 0xEF:
                target_string_id = (sid, row)
                break
        self.assertIsNotNone(target_string_id, "fixture must contain a multi-byte UTF-8 string")
        sid, row = target_string_id
        m.set_string_table_row(sid, length=1)  # keep only the lead byte
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_invalid_string_id_reference_from_group_table_rejected(self):
        data, result, m = _mutable()
        st_count = len(m.section_bytes(fmt.SECTION_STRING_TABLE)) // fmt.STRING_TABLE_ROW_SIZE
        m.set_group_row(0, name_string_id=st_count)  # one past the end
        m.recompute_checksum()
        self._assert_rejected(m, result)

    def test_string_table_row_count_inconsistent_with_length_rejected(self):
        data, result, m = _mutable()
        _, row = m.directory_row_for(fmt.SECTION_STRING_TABLE)
        m.set_directory_row(fmt.SECTION_STRING_TABLE, row_count=row.row_count + 1)
        m.recompute_checksum()
        self._assert_rejected(m, result)


if __name__ == "__main__":
    unittest.main()
