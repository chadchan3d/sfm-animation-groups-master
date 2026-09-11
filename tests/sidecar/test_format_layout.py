"""Phase B2B: pure layout/constants tests for
tools/sfm_master_sidecar/format.py -- no writer/reader I/O involved.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sfm_master_sidecar import format as fmt  # noqa: E402


class FormatConstantsTests(unittest.TestCase):

    def test_magic_is_eight_bytes(self):
        self.assertEqual(len(fmt.MAGIC), 8)

    def test_experimental_versions_are_not_one(self):
        self.assertNotEqual(fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL, 1)
        self.assertNotEqual(fmt.AUTHORITY_SEMANTICS_VERSION_EXPERIMENTAL, 1)

    def test_section_order_has_nine_sections(self):
        self.assertEqual(len(fmt.SECTION_ORDER), 9)
        self.assertEqual(len(set(fmt.SECTION_ORDER)), 9)

    def test_header_size_matches_field_width_table(self):
        # magic(8) + fmt_ver(4) + auth_ver(4) + sha256(32) + src_len(8)
        # + payload_len(8) + dir_offset(8) + section_count(4) + digest(32)
        expected = 8 + 4 + 4 + 32 + 8 + 8 + 8 + 4 + 32
        self.assertEqual(fmt.HEADER_SIZE, expected)

    def test_directory_row_size(self):
        # section_id(4) + offset(8) + length(8) + row_count(4) + row_size(4)
        self.assertEqual(fmt.DIRECTORY_ROW_SIZE, 4 + 8 + 8 + 4 + 4)

    def test_row_sizes_default_to_u32_fields(self):
        self.assertEqual(fmt.STRING_TABLE_ROW_SIZE, 8)
        self.assertEqual(fmt.GROUP_TABLE_ROW_SIZE, 40)
        self.assertEqual(fmt.CHILD_ID_INDEX_ROW_SIZE, 4)
        self.assertEqual(fmt.METADATA_TABLE_ROW_SIZE, 16)
        self.assertEqual(fmt.OCCURRENCE_TABLE_ROW_SIZE, 16)
        self.assertEqual(fmt.OCC_BY_GROUP_INDEX_ROW_SIZE, 4)
        self.assertEqual(fmt.FOLD_TABLE_ROW_SIZE, 12)
        self.assertEqual(fmt.OCC_BY_FOLD_INDEX_ROW_SIZE, 4)

    def test_root_sentinel_is_u32_max(self):
        self.assertEqual(fmt.ROOT_SENTINEL, 0xFFFFFFFF)

    def test_normative_row_sizes_cover_every_section_for_experimental_version(self):
        table = fmt.NORMATIVE_ROW_SIZES[fmt.FORMAT_CONTRACT_VERSION_EXPERIMENTAL]
        self.assertEqual(set(table.keys()), set(fmt.SECTION_ORDER))


class AsciiFoldBytesTests(unittest.TestCase):

    def test_folds_only_ascii_upper(self):
        self.assertEqual(fmt.ascii_fold_bytes(b"ABCxyz123"), b"abcxyz123")

    def test_non_ascii_utf8_bytes_pass_through_unchanged(self):
        # U+00C9 'E9' in UTF-8 is 0xC3 0x89 -- neither byte is in 0x41-0x5A,
        # so both must pass through unchanged (Section 4's compatibility
        # proof -- ASCII byte values never occur inside a multi-byte
        # sequence).
        s = "CafÉ".encode("utf-8")  # "CafÉ"
        folded = fmt.ascii_fold_bytes(s)
        self.assertEqual(folded, b"caf" + "É".encode("utf-8"))

    def test_matches_core_ascii_fold_after_utf8_encoding(self):
        import sfm_master_core as core

        samples = ["Hello_World", "注視TipsParent", "MiXeD_123_\U0001F600", ""]
        for s in samples:
            with self.subTest(s=s):
                expected = core.ascii_fold(s).encode("utf-8")
                actual = fmt.ascii_fold_bytes(s.encode("utf-8"))
                self.assertEqual(actual, expected)


class EmbeddedIntegrityDigestTests(unittest.TestCase):

    def test_digest_computation_zeroes_only_the_digest_field_and_restores_buffer(self):
        buf = bytearray(fmt.HEADER_SIZE + 16)
        off = fmt.embedded_integrity_digest_offset()
        buf[off:off + 32] = bytes(range(32))
        original = bytes(buf)
        digest = fmt.compute_embedded_integrity_digest(bytes(buf), off)
        self.assertEqual(len(digest), 32)
        # original buffer must be untouched (function operates on a copy)
        self.assertEqual(bytes(buf), original)

    def test_digest_changes_if_any_other_byte_changes(self):
        buf1 = bytearray(fmt.HEADER_SIZE)
        buf2 = bytearray(fmt.HEADER_SIZE)
        buf2[5] ^= 0xFF
        off = fmt.embedded_integrity_digest_offset()
        d1 = fmt.compute_embedded_integrity_digest(bytes(buf1), off)
        d2 = fmt.compute_embedded_integrity_digest(bytes(buf2), off)
        self.assertNotEqual(d1, d2)

    def test_digest_is_stable_regardless_of_prior_digest_field_content(self):
        off = fmt.embedded_integrity_digest_offset()
        buf1 = bytearray(fmt.HEADER_SIZE)
        buf2 = bytearray(fmt.HEADER_SIZE)
        buf2[off:off + 32] = b"\xff" * 32  # different garbage in the digest field itself
        d1 = fmt.compute_embedded_integrity_digest(bytes(buf1), off)
        d2 = fmt.compute_embedded_integrity_digest(bytes(buf2), off)
        self.assertEqual(d1, d2)


if __name__ == "__main__":
    unittest.main()
