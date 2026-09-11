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
