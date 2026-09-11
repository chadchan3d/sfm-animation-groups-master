"""Phase B2C Part 19: reader-side resource-limit rejection, BEFORE any
buffer/list is allocated sized from a declared count -- for group count,
occurrence count, fold count, metadata-rows-per-group, string count,
single-string length, and string-pool total byte size.

Constructing an actual multi-gigabyte fixture to genuinely exceed these
limits (2^24 groups, 2^28 occurrences, 512 MiB pool, etc.) is explicitly
against this phase's own instruction ("do not deliberately allocate huge
memory"). Instead, each test temporarily lowers the relevant
`tools.sfm_master_sidecar.format` LIMIT_* constant to a value a small,
already-compiled fixture legitimately exceeds, and confirms the reader
rejects it at the resource-limit check -- exercising the exact same check
code path a real oversized-but-internally-consistent file would hit,
without the memory cost. The limit constant is always restored in a
`finally` block (or via `unittest.mock.patch`) so no other test observes a
mutated global.

Field representability (Section 17, whether a value even FITS its normative
field width) is a different, already-covered concern (see
test_format_layout.py and test_structural_corruption_header.py's overflow
checks / test_writer_representability.py) -- never conflated with these
resource-limit (Section 18, "is this value small enough to be worth
attempting at all") checks.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(HERE))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import format as fmt  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402
from corruption_helpers import compiled_fixture  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compile(name):
    return compiled_fixture(core, writer, FIXTURES_ROOT, name)


class ResourceLimitRejectionTests(unittest.TestCase):

    def test_group_count_over_limit_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")  # 4 groups
        with mock.patch.object(fmt, "LIMIT_GROUP_COUNT", 2):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)
        # limit restored -- the same fixture opens fine again.
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        self.assertTrue(r.is_valid())

    def test_occurrence_count_over_limit_rejected(self):
        data, result, blob = _compile("28_large_alias_family.txt")  # 30 occurrences
        with mock.patch.object(fmt, "LIMIT_OCCURRENCE_COUNT", 5):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_fold_count_over_limit_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")  # 3 distinct folds
        with mock.patch.object(fmt, "LIMIT_FOLD_COUNT", 1):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_string_count_over_limit_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        with mock.patch.object(fmt, "LIMIT_DISTINCT_POOL_STRINGS", 1):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_metadata_rows_per_group_over_limit_rejected(self):
        data, result, blob = _compile("15_duplicate_metadata_keys.txt")  # 2 metadata rows on one group
        with mock.patch.object(fmt, "LIMIT_METADATA_ROWS_PER_GROUP", 1):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_single_string_length_over_limit_rejected(self):
        data, result, blob = _compile("21_escaped_quote_spelling.txt")
        with mock.patch.object(fmt, "LIMIT_SINGLE_STRING_BYTE_LENGTH", 2):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_string_pool_total_bytes_over_limit_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        with mock.patch.object(fmt, "LIMIT_STRING_POOL_TOTAL_BYTES", 4):
            with self.assertRaises(reader.AuthorityUnavailable):
                reader.SidecarReader.open_generation(blob, result.source_sha256)

    def test_reader_query_length_over_limit_rejected(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        with self.assertRaises(ValueError):
            r.lookup_fold(b"x" * (fmt.LIMIT_READER_QUERY_BYTE_LENGTH + 1))
        # exactly at the limit must still be accepted (boundary check, not
        # off-by-one) -- resolves MasterUnknown since it's gibberish, but
        # must not raise on length grounds.
        res = r.lookup_fold(b"x" * fmt.LIMIT_READER_QUERY_BYTE_LENGTH)
        self.assertIsInstance(res, reader.MasterUnknown)

    def test_resource_limit_checks_run_before_the_per_row_decode_loop(self):
        # Structural proof, not just behavioral: the resource-limit checks
        # in reader.py's _validate_and_decode appear in source order BEFORE
        # the loops that build `strings`/`groups`/etc. lists sized from
        # those counts -- inspected directly here so a future edit that
        # accidentally reorders them is caught.
        import inspect
        src = inspect.getsource(reader._validate_and_decode)
        limit_check_pos = src.index("LIMIT_DISTINCT_POOL_STRINGS")
        string_decode_loop_pos = src.index("for i in range(string_count):")
        self.assertLess(limit_check_pos, string_decode_loop_pos)

        group_limit_pos = src.index("LIMIT_GROUP_COUNT")
        group_decode_loop_pos = src.index("for i in range(group_count):")
        self.assertLess(group_limit_pos, group_decode_loop_pos)


if __name__ == "__main__":
    unittest.main()
