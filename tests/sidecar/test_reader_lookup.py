"""Phase B2B: targeted lookup-semantics tests (final spec Section 24) beyond
what the exhaustive round-trip test already covers -- MasterUnknown, the
exact-spelling-inside-a-still-conflicting-family rule, and open-mode
authority restrictions.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


def _compile(name):
    path = FIXTURES_ROOT / "valid" / name
    data = path.read_bytes()
    result = core.parse_master_bytes(data, source_name=name)
    blob = writer.compile_sidecar(data, result)
    return data, result, blob


class MasterUnknownTests(unittest.TestCase):

    def test_query_with_no_matching_fold_is_master_unknown(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        res = r.lookup_fold(b"ThisLiteralDoesNotExistAnywhere")
        self.assertIsInstance(res, reader.MasterUnknown)

    def test_master_unknown_never_substituted_for_a_real_error(self):
        # A malformed/oversized query must raise, never resolve to
        # MasterUnknown (final spec Section 4/24 -- explicit non-conflation).
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        with self.assertRaises(ValueError):
            r.lookup_fold(b"x" * 5000)
        with self.assertRaises(TypeError):
            r.lookup_fold("not-bytes")


class MalformedQueryEncodingTests(unittest.TestCase):
    """Gate A1 correction: malformed UTF-8 query bytes must raise an
    input/query error (ValueError, via UnicodeDecodeError -- a ValueError
    subclass, so no new exception class was introduced) BEFORE ASCII
    folding / binary search / absence classification -- never
    `MasterUnknown`, `Hit`, or `FoldConflict`. This is a distinct case from
    a well-formed-but-absent query, which must still resolve to
    `MasterUnknown` exactly as before."""

    # Representative malformed sequences (Part 5.D of the Gate A1 task):
    MALFORMED_CASES = {
        "isolated_continuation_byte": b"\x80",
        "truncated_multibyte_sequence": b"\xc2",
        "invalid_leading_byte": b"\xff",
        "invalid_continuation_sequence": b"\xc2\x20",
    }

    def test_A_valid_ascii_bytes_hit_unchanged(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        res = r.lookup_fold(result.occurrences[0].literal.encode("utf-8"))
        self.assertIsInstance(res, reader.Hit)

    def test_B_valid_non_ascii_utf8_unchanged_no_casefold_substitution(self):
        data, result, blob = _compile("19_non_ascii_bmp_text.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        literal = u"注視TipsParent"
        res = r.lookup_fold(literal.encode("utf-8"))
        self.assertIsInstance(res, reader.Hit)
        # ASCII-only folding: the non-ASCII kanji bytes must pass through
        # completely unchanged in the returned fold_key; only "TipsParent"'s
        # ASCII letters may have been case-folded.
        self.assertTrue(res.fold_key.startswith(u"注視".encode("utf-8")))

    def test_C_valid_absent_query_is_master_unknown(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        res = r.lookup_fold(b"ThisLiteralDoesNotExistAnywhereValidAscii")
        self.assertIsInstance(res, reader.MasterUnknown)

    def test_D_malformed_utf8_raises_value_error_never_master_unknown(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for name, malformed in self.MALFORMED_CASES.items():
            with self.subTest(case=name):
                # assertRaises itself fails the test (loudly, showing
                # whatever the block actually returned) if no exception is
                # raised -- no separate manual "no exception" check needed.
                with self.assertRaises(ValueError) as ctx:
                    r.lookup_fold(malformed)
                # Assert the SPECIFIC contract, not merely "some exception":
                # malformed UTF-8 must raise UnicodeDecodeError specifically
                # (itself a ValueError subclass -- the existing query-error
                # philosophy, no new exception class).
                self.assertIsInstance(ctx.exception, UnicodeDecodeError)

    def test_E_wrong_type_unchanged(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        with self.assertRaises(TypeError):
            r.lookup_fold("not-bytes")

    def test_F_oversized_unchanged(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        with self.assertRaises(ValueError):
            r.lookup_fold(b"x" * 5000)

    def test_G_conflict_family_unchanged(self):
        data, result, blob = _compile("13_same_fold_different_destinations.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        res = r.lookup_fold(b"Bar")
        self.assertIsInstance(res, reader.FoldConflict)

    def test_H_exact_spelling_inside_conflict_unchanged(self):
        data, result, blob = _compile("14_exact_spelling_inside_conflicting_fold.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for occ in result.occurrences:
            with self.subTest(literal=occ.literal):
                res = r.lookup_fold(occ.literal.encode("utf-8"))
                self.assertIsInstance(res, reader.FoldConflict)

    def test_I_ascii_case_variants_unchanged(self):
        data, result, blob = _compile("12_same_fold_same_destination.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for occ in result.occurrences:
            with self.subTest(literal=occ.literal):
                res = r.lookup_fold(occ.literal.encode("utf-8"))
                self.assertIsInstance(res, reader.Hit)

    def test_malformed_query_never_collapses_into_valid_absent_result(self):
        """Explicit, impossible-to-silently-regress distinction (Part 6):
        a WELL-FORMED absent query resolves to MasterUnknown; a MALFORMED
        query of comparable/shorter length raises UnicodeDecodeError. The
        two must never be conflated -- this asserts both outcomes side by
        side against the SAME open provider."""
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)

        valid_absent = r.lookup_fold(b"ValidAsciiButAbsentFromThisFixture")
        self.assertIsInstance(valid_absent, reader.MasterUnknown)

        with self.assertRaises(UnicodeDecodeError):
            r.lookup_fold(b"\x80")


class ExactSpellingInsideConflictTests(unittest.TestCase):

    def test_exact_spelling_matching_one_member_is_still_a_conflict(self):
        # final spec Section 24: "destination_count > 1 -> FoldConflict
        # (even if the query's exact spelling matches one specific member)".
        data, result, blob = _compile("14_exact_spelling_inside_conflicting_fold.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for occ in result.occurrences:
            with self.subTest(literal=occ.literal):
                res = r.lookup_fold(occ.literal.encode("utf-8"))
                self.assertIsInstance(res, reader.FoldConflict)
                self.assertEqual(len(res.destinations), 3)

    def test_same_destination_family_is_a_hit_not_a_conflict(self):
        data, result, blob = _compile("12_same_fold_same_destination.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        for occ in result.occurrences:
            with self.subTest(literal=occ.literal):
                res = r.lookup_fold(occ.literal.encode("utf-8"))
                self.assertIsInstance(res, reader.Hit)


class OpenModeAuthorityTests(unittest.TestCase):

    def test_unbound_open_refuses_lookup_fold(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation_unbound(blob)
        with self.assertRaises(reader.AuthorityUnavailable):
            r.lookup_fold(b"a")

    def test_unbound_open_still_permits_diagnostic_inspection(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation_unbound(blob)
        self.assertEqual(r.group_count(), len(result.groups))
        self.assertEqual(r.occurrence_count(), len(result.occurrences))

    def test_bound_open_permits_lookup_fold(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        res = r.lookup_fold(result.occurrences[0].literal.encode("utf-8"))
        self.assertIsInstance(res, reader.Hit)

    def test_source_binding_mismatch_raises_before_returning_a_handle(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        wrong_sha = "0" * 64
        with self.assertRaises(reader.SourceMismatchError):
            reader.SidecarReader.open_generation(blob, wrong_sha)

    def test_source_binding_is_case_insensitive_hex_comparison(self):
        data, result, blob = _compile("06_sibling_groups.txt")
        r = reader.SidecarReader.open_generation(blob, result.source_sha256.upper())
        self.assertTrue(r.is_valid())


if __name__ == "__main__":
    unittest.main()
