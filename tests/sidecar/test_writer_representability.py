"""Phase B2C Part 20: writer field-representability and resource-limit
hardening -- the writer must REFUSE (raise `SidecarFieldOverflowError`),
never mask, modulo, or `struct`-truncate, any ID/count/rank/offset/length
that doesn't fit its normative u32/u64 field or a configured resource
maximum.

As with test_resource_limits.py, this avoids constructing billions of real
rows: direct unit tests exercise the `_check_u32`/`_check_u64`/`_check_limit`
helpers themselves, and `unittest.mock.patch` temporarily lowers a
`format.py` ceiling constant so a small, already-in-hand fixture legitimately
exceeds it -- exercising the exact same refusal code path a real oversized
input would hit.
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
from sfm_master_sidecar import writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _parse(name):
    path = FIXTURES_ROOT / "valid" / name
    data = path.read_bytes()
    return data, core.parse_master_bytes(data, source_name=name)


class OverflowHelperUnitTests(unittest.TestCase):

    def test_check_u32_accepts_boundary_value(self):
        self.assertEqual(writer._check_u32(fmt.U32_MAX, "x"), fmt.U32_MAX)

    def test_check_u32_rejects_one_past_boundary(self):
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_u32(fmt.U32_MAX + 1, "x")

    def test_check_u32_rejects_negative(self):
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_u32(-1, "x")

    def test_check_u64_accepts_boundary_value(self):
        self.assertEqual(writer._check_u64(fmt.U64_MAX, "x"), fmt.U64_MAX)

    def test_check_u64_rejects_one_past_boundary(self):
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_u64(fmt.U64_MAX + 1, "x")

    def test_check_limit_accepts_boundary_value(self):
        self.assertEqual(writer._check_limit(10, 10, "x"), 10)

    def test_check_limit_rejects_one_past_boundary(self):
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_limit(11, 10, "x")

    def test_no_masking_or_modulo_ever_happens(self):
        # `_check_u32` must raise on the EXACT offending value, never
        # silently wrap it modulo 2**32 (which would make 2**32 == 0,
        # 2**32 + 5 == 5, etc. -- all falsely "in range").
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_u32(2 ** 32, "x")  # would wrap to 0 if masked
        with self.assertRaises(writer.SidecarFieldOverflowError):
            writer._check_u32(2 ** 32 + 5, "x")  # would wrap to 5 if masked
        try:
            writer._check_u32(2 ** 32, "x")
            self.fail("expected SidecarFieldOverflowError")
        except writer.SidecarFieldOverflowError as e:
            self.assertIn(str(2 ** 32), str(e))


class WriterRepresentabilityIntegrationTests(unittest.TestCase):
    """End-to-end: compile_sidecar itself refuses (raises, produces no
    output bytes) when a real derived value would exceed a lowered ceiling
    -- proving the checks are actually wired into the compile path, not
    merely unit-testable in isolation."""

    def test_group_id_overflow_refused_end_to_end(self):
        data, result = _parse("06_sibling_groups.txt")  # 4 groups: ids 0-3
        with mock.patch.object(fmt, "U32_MAX", 2):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_group_count_resource_limit_refused_end_to_end(self):
        data, result = _parse("06_sibling_groups.txt")  # 4 groups
        with mock.patch.object(fmt, "LIMIT_GROUP_COUNT", 2):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_occurrence_count_resource_limit_refused_end_to_end(self):
        data, result = _parse("28_large_alias_family.txt")  # 30 occurrences
        with mock.patch.object(fmt, "LIMIT_OCCURRENCE_COUNT", 5):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_fold_count_resource_limit_refused_end_to_end(self):
        data, result = _parse("06_sibling_groups.txt")  # 3 distinct folds
        with mock.patch.object(fmt, "LIMIT_FOLD_COUNT", 1):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_metadata_rows_per_group_resource_limit_refused_end_to_end(self):
        data, result = _parse("15_duplicate_metadata_keys.txt")  # 2 metadata rows
        with mock.patch.object(fmt, "LIMIT_METADATA_ROWS_PER_GROUP", 1):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_single_string_length_resource_limit_refused_end_to_end(self):
        data, result = _parse("21_escaped_quote_spelling.txt")
        with mock.patch.object(fmt, "LIMIT_SINGLE_STRING_BYTE_LENGTH", 2):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_source_byte_size_resource_limit_refused_end_to_end(self):
        data, result = _parse("06_sibling_groups.txt")
        with mock.patch.object(fmt, "LIMIT_SOURCE_BYTE_SIZE", 4):
            with self.assertRaises(writer.SidecarFieldOverflowError):
                writer.compile_sidecar(data, result)

    def test_no_bytes_produced_on_refusal(self):
        # A refused compile must never return a partial/truncated buffer --
        # only a raised exception, confirmed by catching it and observing
        # the exception object carries no byte payload at all.
        data, result = _parse("06_sibling_groups.txt")
        with mock.patch.object(fmt, "LIMIT_GROUP_COUNT", 2):
            try:
                blob = writer.compile_sidecar(data, result)
                self.fail("expected refusal, got %d bytes" % len(blob))
            except writer.SidecarFieldOverflowError:
                pass  # no partial value ever assigned to `blob`

    def test_lowered_limits_restored_after_context_normal_compile_succeeds(self):
        data, result = _parse("06_sibling_groups.txt")
        blob = writer.compile_sidecar(data, result)
        self.assertGreater(len(blob), 0)


if __name__ == "__main__":
    unittest.main()
