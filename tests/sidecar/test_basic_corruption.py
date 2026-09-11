"""Phase B2B: BASIC corruption tests only (final spec Section 39's full
Gate 1B corruption matrix -- every Section 20.A-J check individually
exercised with checksum-valid/checksum-invalid pairs -- is explicitly
Phase B2C's job, not this phase's). This file covers exactly the cases
Phase B2B's own scope lists: wrong magic, unsupported format/authority
version, bad embedded checksum, truncated header/file, and source-binding
mismatch (the last is also covered from the lookup-semantics angle in
test_reader_lookup.py; here it is one more entry in the corruption list for
completeness).
"""

import struct
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compiled_blob():
    path = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
    data = path.read_bytes()
    result = core.parse_master_bytes(data, source_name="06")
    blob = writer.compile_sidecar(data, result)
    return data, result, blob


class BasicCorruptionTests(unittest.TestCase):

    def setUp(self):
        self.data, self.result, self.blob = _compiled_blob()

    def _open_mutated(self, mutate):
        b = bytearray(self.blob)
        mutate(b)
        return reader.SidecarReader.open_generation(bytes(b), self.result.source_sha256)

    def test_wrong_magic_rejected(self):
        with self.assertRaises(reader.AuthorityUnavailable):
            self._open_mutated(lambda b: b.__setitem__(slice(0, 8), b"XXXXXXXX"))

    def test_unsupported_format_contract_version_rejected(self):
        def mutate(b):
            struct.pack_into("<I", b, 8, 0xDEADBEEF & 0x7FFFFFFF)
        with self.assertRaises(reader.AuthorityUnavailable):
            self._open_mutated(mutate)

    def test_unsupported_authority_semantics_version_rejected(self):
        def mutate(b):
            struct.pack_into("<I", b, 12, 0xDEADBEEF & 0x7FFFFFFF)
        with self.assertRaises(reader.AuthorityUnavailable):
            self._open_mutated(mutate)

    def test_bad_embedded_checksum_rejected(self):
        def mutate(b):
            off = fmt.embedded_integrity_digest_offset()
            b[off] ^= 0xFF
        with self.assertRaises(reader.AuthorityUnavailable):
            self._open_mutated(mutate)

    def test_truncated_header_rejected(self):
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(self.blob[:50], self.result.source_sha256)

    def test_zero_byte_file_rejected(self):
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(b"", self.result.source_sha256)

    def test_truncated_file_mid_section_rejected(self):
        truncated = self.blob[:len(self.blob) - 10]
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(truncated, self.result.source_sha256)

    def test_source_binding_mismatch_rejected(self):
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(self.blob, "f" * 64)

    def test_payload_length_mismatch_rejected(self):
        # Append a trailing byte -- payload_length no longer matches actual
        # file size, so this must be caught even before digest recomputation
        # would independently also fail.
        with self.assertRaises(reader.AuthorityUnavailable):
            reader.SidecarReader.open_generation(self.blob + b"\x00", self.result.source_sha256)

    def test_each_corruption_variant_still_valid_original_unaffected(self):
        # Sanity: the ORIGINAL, unmutated blob must still open fine after
        # all the above mutation attempts on independent copies (proves the
        # mutations above operate on copies, never the shared fixture blob).
        r = reader.SidecarReader.open_generation(self.blob, self.result.source_sha256)
        self.assertTrue(r.is_valid())


if __name__ == "__main__":
    unittest.main()
