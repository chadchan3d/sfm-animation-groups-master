"""Phase B2A: fixture-manifest-driven contract tests, plus targeted
assertions for the UTF-8/escape and fold-expectation fixtures that need more
than a manifest entry to verify correctly.
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import oracle  # noqa: E402
import sfm_master_core as core  # noqa: E402

MANIFEST_PATH = HERE / "fixture_manifest.json"


def load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def read_fixture(rel_path: str) -> bytes:
    with open(HERE / rel_path, "rb") as f:
        return f.read()


class ManifestDrivenContractTests(unittest.TestCase):
    """One assertion pass per manifest entry, covering Parts 6-8's category
    expectations without hand-writing 40 near-identical test methods."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_manifest_categories_present_and_counted(self):
        self.assertEqual(len(self.manifest["valid"]), 28)
        self.assertEqual(len(self.manifest["unsupported"]), 2)
        self.assertEqual(len(self.manifest["malformed"]), 10)

    def test_valid_fixtures_match_manifest(self):
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["filename"]):
                data = read_fixture(entry["filename"])
                # oracle must not raise for a valid fixture
                o = oracle.scan_bytes(data)
                c = core.parse_master_bytes(data, source_name=entry["filename"])
                self.assertTrue(c.ok, f"{entry['filename']}: expected core.ok True")
                self.assertEqual(entry["expected_core_parse"], "pass")
                self.assertEqual(len(c.groups), entry["expected_group_count"])
                self.assertEqual(len(c.occurrences), entry["expected_control_count"])
                actual_meta = sum(len(g.metadata.entries) for g in c.groups)
                self.assertEqual(actual_meta, entry["expected_metadata_count"])
                self.assertTrue(entry["expected_sidecar_profile_eligible"])
                parentless = [g for g in c.groups if g.parent_path is None]
                self.assertEqual(len(parentless), 1)
                # oracle/core agree on the basic counts too (independence
                # doesn't mean disagreement -- see sec 5 of the spec)
                self.assertEqual(o.group_count(), len(c.groups))
                self.assertEqual(o.control_count(), len(c.occurrences))
                self.assertEqual(o.metadata_count(), actual_meta)

    def test_unsupported_fixtures_are_core_parseable_but_profile_ineligible(self):
        for entry in self.manifest["unsupported"]:
            with self.subTest(fixture=entry["filename"]):
                data = read_fixture(entry["filename"])
                c = core.parse_master_bytes(data, source_name=entry["filename"])
                self.assertTrue(c.ok, "CORE_PARSEABLE: expected core.ok True")
                parentless = [g for g in c.groups if g.parent_path is None]
                self.assertNotEqual(
                    len(parentless), 1,
                    "SIDECAR_PROFILE_UNSUPPORTED: expected parentless count != 1",
                )
                self.assertFalse(entry["expected_sidecar_profile_eligible"])
                # oracle must also handle these without raising -- it is not
                # the compiler's eligibility gate, only a structural scanner
                o = oracle.scan_bytes(data)
                self.assertEqual(len(o.parentless_groups()), len(parentless))

    def test_malformed_fixtures_are_rejected_by_core(self):
        for entry in self.manifest["malformed"]:
            with self.subTest(fixture=entry["filename"]):
                data = read_fixture(entry["filename"])
                self.assertEqual(entry["expected_core_parse"], "fail")
                if entry["expected_core_grammar_error_kinds"] == ["unicode_decode_error"]:
                    with self.assertRaises(UnicodeDecodeError):
                        core.parse_master_bytes(data, source_name=entry["filename"])
                    continue
                c = core.parse_master_bytes(data, source_name=entry["filename"])
                self.assertFalse(c.ok, f"{entry['filename']}: expected core.ok False")
                actual_kinds = sorted(set(e.kind for e in c.grammar_errors))
                if actual_kinds:
                    self.assertEqual(actual_kinds, entry["expected_core_grammar_error_kinds"])
                else:
                    # structural (brace-balance) failures surface via the
                    # unmatched_* / stack_depth_at_eof fields rather than
                    # grammar_errors -- still a real, asserted rejection.
                    self.assertTrue(
                        c.unmatched_closes or c.unmatched_opens or c.stack_depth_at_eof != 0
                    )


class UtfEscapeFixtureTests(unittest.TestCase):
    """Part 9: prove exact-byte round-trip from source bytes, through the
    independent oracle, through sfm_master_core, with no accidental
    transformation introduced by Python source-string interpretation in
    this very test file."""

    def test_escaped_quote_spelling_round_trips_unescaped(self):
        data = read_fixture("fixtures/valid/21_escaped_quote_spelling.txt")
        # Ground truth expectation built directly from raw bytes, not typed
        # as a Python string literal here (avoids this test file's own
        # source-escaping from silently "fixing" the assertion).
        expected = data.decode("utf-8").split('"control"')[1].split('\t\t"', 1)[1].rsplit('"', 1)[0]
        self.assertEqual(expected, 'He said \\"hi\\"')

        o = oracle.scan_bytes(data)
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        self.assertEqual(o.controls[0].token, expected)
        self.assertEqual(c.occurrences[0].literal, expected)
        self.assertEqual(o.controls[0].token, c.occurrences[0].literal)

    def test_escaped_backslash_spelling_round_trips_unescaped(self):
        data = read_fixture("fixtures/valid/22_escaped_backslash_spelling.txt")
        expected = data.decode("utf-8").split('"control"')[1].split('\t\t"', 1)[1].rsplit('"', 1)[0]
        self.assertEqual(expected, 'C:\\\\Path\\\\To\\\\Thing')

        o = oracle.scan_bytes(data)
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        self.assertEqual(o.controls[0].token, expected)
        self.assertEqual(c.occurrences[0].literal, expected)

    def test_non_ascii_bmp_round_trips_exactly(self):
        data = read_fixture("fixtures/valid/19_non_ascii_bmp_text.txt")
        o = oracle.scan_bytes(data)
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        self.assertEqual(o.controls[0].token, c.occurrences[0].literal)
        self.assertEqual(c.occurrences[0].literal, "\u6ce8\u8996TipsParent")
        self.assertEqual(o.groups[1].name, "\u9854")

    def test_non_bmp_round_trips_exactly(self):
        data = read_fixture("fixtures/valid/20_non_bmp_text.txt")
        o = oracle.scan_bytes(data)
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        self.assertEqual(o.controls[0].token, c.occurrences[0].literal)
        self.assertIn("\U0001F600", c.occurrences[0].literal)

    def test_bom_and_no_bom_produce_identical_projections(self):
        bom_data = read_fixture("fixtures/valid/24_bom_source.txt")
        plain_data = read_fixture("fixtures/valid/25_no_bom_source.txt")
        self.assertTrue(bom_data.startswith(b"\xef\xbb\xbf"))
        self.assertFalse(plain_data.startswith(b"\xef\xbb\xbf"))

        o_bom = oracle.scan_bytes(bom_data)
        o_plain = oracle.scan_bytes(plain_data)
        c_bom = core.parse_master_bytes(bom_data)
        c_plain = core.parse_master_bytes(plain_data)

        self.assertEqual([c.token for c in o_bom.controls], [c.token for c in o_plain.controls])
        self.assertEqual(
            [o.literal for o in c_bom.occurrences],
            [o.literal for o in c_plain.occurrences],
        )

    def test_whitespace_inside_literal_is_significant(self):
        data = read_fixture("fixtures/valid/23_whitespace_distinctions.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        literals = [o.literal for o in c.occurrences]
        self.assertIn("has  double  space", literals)
        self.assertIn("has\ttab\tinside", literals)


class DuplicateControlFixtureTests(unittest.TestCase):
    """Duplicate-control fixtures (10, 11) preserved distinctly, not
    collapsed, with correct independent ranks agreeing across oracle/core."""

    def test_repeated_identical_control_one_group(self):
        data = read_fixture("fixtures/valid/10_repeated_identical_control_one_group.txt")
        o = oracle.scan_bytes(data)
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        dupes_o = [x for x in o.controls if x.token == "Dupe"]
        dupes_c = [x for x in c.occurrences if x.literal == "Dupe"]
        self.assertEqual(len(dupes_o), 3)
        self.assertEqual(len(dupes_c), 3)
        self.assertEqual([x.local_rank for x in dupes_o], [0, 1, 2])
        self.assertEqual([x.local_rank for x in dupes_c], [0, 1, 2])
        self.assertEqual([x.global_order for x in dupes_o], [x.global_rank for x in dupes_c])

    def test_repeated_identical_control_across_groups(self):
        data = read_fixture("fixtures/valid/11_repeated_identical_control_across_groups.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        shared = [x for x in c.occurrences if x.literal == "Shared"]
        self.assertEqual(len(shared), 2)
        self.assertEqual({x.full_path for x in shared}, {"groupFile/GrpA", "groupFile/GrpB"})
        self.assertEqual([x.local_rank for x in shared], [0, 0])  # first in each of its own group


class FoldExpectationFixtureTests(unittest.TestCase):
    """Part 10: fold-family expectations for future writer/reader tests.
    The oracle is not fold authority (per module docstring); the small
    ascii_fold_for_test_fixtures helper is used only to state expectations,
    and actual fold-family construction/conflict evidence is independently
    re-verified against sfm_master_core.build_fold_families here."""

    def test_same_destination_family_is_not_a_conflict(self):
        data = read_fixture("fixtures/valid/12_same_fold_same_destination.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        fams = core.build_fold_families(c.occurrences)
        key = oracle.ascii_fold_for_test_fixtures("Foo")
        fam = fams[key]
        self.assertEqual(fam.exact_spellings, {"Foo", "foo", "FOO"})
        self.assertFalse(fam.is_conflict)

    def test_cross_destination_family_is_a_conflict(self):
        data = read_fixture("fixtures/valid/13_same_fold_different_destinations.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        fams = core.build_fold_families(c.occurrences)
        key = oracle.ascii_fold_for_test_fixtures("Bar")
        fam = fams[key]
        self.assertEqual(fam.exact_spellings, {"Bar", "bar"})
        self.assertTrue(fam.is_conflict)

    def test_exact_spelling_inside_conflict_remains_a_conflict(self):
        data = read_fixture("fixtures/valid/14_exact_spelling_inside_conflicting_fold.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        fams = core.build_fold_families(c.occurrences)
        key = oracle.ascii_fold_for_test_fixtures("Baz")
        fam = fams[key]
        self.assertIn("Baz", fam.exact_spellings)
        # A future reader querying the exact spelling "Baz" must still see
        # FOLD_CONFLICT, never a silent Hit -- this fixture exists so that
        # writer/reader tests can exercise exactly this case later.
        self.assertTrue(fam.is_conflict)
        self.assertEqual(len(fam.destinations), 3)

    def test_large_alias_family_all_one_destination(self):
        data = read_fixture("fixtures/valid/28_large_alias_family.txt")
        c = core.parse_master_bytes(data)
        self.assertTrue(c.ok)
        fams = core.build_fold_families(c.occurrences)
        key = oracle.ascii_fold_for_test_fixtures("AliasWord")
        fam = fams[key]
        self.assertEqual(len(fam.exact_spellings), 30)
        self.assertFalse(fam.is_conflict)


if __name__ == "__main__":
    unittest.main()
