"""Tests for tools/sfm_master_core.py -- the Phase B0 shared semantic core.

All fixtures are constructed in-memory (bytes/line lists) and are never the
canonical Master, except test_canonical_master_parity, which only reads it
and additionally asserts the read-only contract (the real file's bytes are
unchanged by parsing).
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402


def fixture_bytes(content: str) -> bytes:
    return content.encode("utf-8")


class ValidMasterParityTests(unittest.TestCase):
    """A. Valid current Master parity."""

    def test_canonical_master_parity(self):
        path = REPO_ROOT / "sfm_defaultanimationgroups.txt"
        before = path.read_bytes()

        result = core.parse_master_bytes(before, source_name=str(path))
        self.assertTrue(result.ok)
        self.assertEqual(len(result.groups), 43)
        self.assertEqual(len(result.occurrences), 128555)
        self.assertEqual(result.grammar_errors, [])
        self.assertEqual(result.unmatched_closes, [])
        self.assertEqual(result.unmatched_opens, [])
        self.assertEqual(result.stack_depth_at_eof, 0)

        # Root order matches the taxonomy order this project's own migration
        # history has independently verified (most recently in the Helpers
        # Pass 1H promotion).
        self.assertEqual(result.root_paths, [
            "groupFile/Face", "groupFile/Body Morphs", "groupFile/Sexual Bones",
            "groupFile/Hair", "groupFile/Clothing", "groupFile/Correctives",
            "groupFile/Helpers", "groupFile/Body", "groupFile/Arms",
            "groupFile/Fingers", "groupFile/Legs", "groupFile/Toes",
            "groupFile/Wings", "groupFile/RigBody", "groupFile/RigArms",
            "groupFile/RigLegs", "groupFile/RigHelpers", "groupFile/Tail",
            "groupFile/Attachments", "groupFile/Other", "groupFile/Useless",
        ])

        families = core.build_fold_families(result.occurrences)
        self.assertEqual(len(families), 124728)
        conflicts = [f for f in families.values() if f.is_conflict]
        self.assertEqual(conflicts, [])
        multi = [f for f in families.values() if len(f.exact_spellings) > 1]
        self.assertEqual(len(multi), 3267)

        # Legacy adapter must produce an identical literal/destination
        # sequence to the rich API -- one parser, two shapes.
        lines = before.decode("utf-8").splitlines()
        legacy = core.parse_structure(lines)
        self.assertEqual(len(legacy.groups), 43)
        self.assertEqual(len(legacy.controls), 128555)
        self.assertEqual(legacy.grammar_errors, [])
        self.assertEqual(
            [o.literal for o in result.occurrences],
            [c[0] for c in legacy.controls],
        )
        self.assertEqual(
            [o.full_path for o in result.occurrences],
            [c[1] for c in legacy.controls],
        )

        after = path.read_bytes()
        self.assertEqual(before, after, "Parsing must never modify the source file.")


class ExactLiteralPreservationTests(unittest.TestCase):
    """B. Exact literal preservation."""

    def _parse(self, content):
        return core.parse_master_bytes(fixture_bytes(content))

    def test_case_punctuation_and_spaces_preserved(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Grp"\n'
            '\t{\n'
            '\t\t"control"\t\t"Arm-Bend-L"\n'
            '\t\t"control"\t\t"Anus/Vag Open Big DP Corr"\n'
            '\t\t"control"\t\t"lowerArm_left"\n'
            '\t\t"control"\t\t"LOWERARM_LEFT"\n'
            '\t\t"control"\t\t"has  double  space"\n'
            '\t}\n'
            '}\n'
        )
        result = self._parse(content)
        self.assertTrue(result.ok)
        literals = [o.literal for o in result.occurrences]
        self.assertEqual(literals, [
            "Arm-Bend-L", "Anus/Vag Open Big DP Corr", "lowerArm_left",
            "LOWERARM_LEFT", "has  double  space",
        ])
        # No character is stripped, cased, or collapsed.
        self.assertIn("has  double  space", literals)


class MetadataPresenceTests(unittest.TestCase):
    """C. Metadata presence -- absence must never be conflated with an
    explicit falsy value."""

    def _one_group(self, extra_lines):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Grp"\n'
            '\t{\n'
            + "".join(f'\t\t{line}\n' for line in extra_lines) +
            '\t\t"control"\t\t"X"\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        return result.groups_by_path["groupFile/Grp"]

    def test_metadata_absent(self):
        grp = self._one_group([])
        self.assertFalse(grp.metadata.present("selectable"))
        self.assertFalse(grp.metadata.present("visible"))
        self.assertFalse(grp.metadata.present("groupColor"))
        self.assertIsNone(grp.metadata.value("selectable"))

    def test_selectable_explicit_0(self):
        grp = self._one_group(['"selectable" "0"'])
        self.assertTrue(grp.metadata.present("selectable"))
        self.assertEqual(grp.metadata.value("selectable"), "0")

    def test_selectable_explicit_1(self):
        grp = self._one_group(['"selectable" "1"'])
        self.assertTrue(grp.metadata.present("selectable"))
        self.assertEqual(grp.metadata.value("selectable"), "1")

    def test_visible_explicit_0(self):
        grp = self._one_group(['"visible" "0"'])
        self.assertTrue(grp.metadata.present("visible"))
        self.assertEqual(grp.metadata.value("visible"), "0")

    def test_visible_explicit_1(self):
        grp = self._one_group(['"visible" "1"'])
        self.assertTrue(grp.metadata.present("visible"))
        self.assertEqual(grp.metadata.value("visible"), "1")

    def test_groupcolor_present(self):
        grp = self._one_group(['"groupColor"\t\t"240 210 255 255"'])
        self.assertTrue(grp.metadata.present("groupColor"))
        self.assertEqual(grp.metadata.value("groupColor"), "240 210 255 255")

    def test_absence_is_not_explicit_zero(self):
        absent = self._one_group([])
        explicit_zero = self._one_group(['"selectable" "0"'])
        self.assertFalse(absent.metadata.present("selectable"))
        self.assertTrue(explicit_zero.metadata.present("selectable"))
        self.assertNotEqual(
            absent.metadata.present("selectable"),
            explicit_zero.metadata.present("selectable"),
        )

    def test_duplicate_metadata_key_not_silently_collapsed(self):
        grp = self._one_group(['"selectable" "0"', '"selectable" "1"'])
        self.assertTrue(grp.metadata.present("selectable"))
        self.assertEqual(grp.metadata.values("selectable"), ["0", "1"])
        # Ambiguous -- the convenience accessor must not silently pick one.
        self.assertIsNone(grp.metadata.value("selectable"))


class OccurrenceOrderTests(unittest.TestCase):
    """D. Occurrence order -- explicit, 0-based, source-order-derived."""

    def test_global_and_local_rank_and_group_order(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"First"\n'
            '\t{\n'
            '\t\t"control"\t\t"A"\n'
            '\t\t"control"\t\t"B"\n'
            '\t}\n'
            '\t"Second"\n'
            '\t{\n'
            '\t\t"control"\t\t"C"\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)

        ranks = {o.literal: (o.global_rank, o.local_rank) for o in result.occurrences}
        self.assertEqual(ranks["A"], (0, 0))
        self.assertEqual(ranks["B"], (1, 1))
        self.assertEqual(ranks["C"], (2, 0))  # local rank resets per group

        self.assertEqual(result.root_paths, ["groupFile/First", "groupFile/Second"])
        first = result.groups_by_path["groupFile/First"]
        second = result.groups_by_path["groupFile/Second"]
        self.assertEqual(first.sibling_rank, 0)
        self.assertEqual(second.sibling_rank, 1)
        self.assertEqual(first.local_occurrence_global_ranks, [0, 1])
        self.assertEqual(second.local_occurrence_global_ranks, [2])

    def test_child_order_reflects_declaration_not_close_order(self):
        # A nested child that CLOSES before a later-declared sibling but was
        # DECLARED after some other content must still be ordered by
        # declaration (open_line), matching this module's documented choice
        # (Phase A flagged the pre-B0 validator's close-order append bug).
        content = (
            'groupFile\n'
            '{\n'
            '\t"Parent"\n'
            '\t{\n'
            '\t\t"ChildA"\n'
            '\t\t{\n'
            '\t\t\t"control"\t\t"a1"\n'
            '\t\t}\n'
            '\t\t"ChildB"\n'
            '\t\t{\n'
            '\t\t\t"control"\t\t"b1"\n'
            '\t\t}\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        parent = result.groups_by_path["groupFile/Parent"]
        self.assertEqual(parent.child_paths, [
            "groupFile/Parent/ChildA", "groupFile/Parent/ChildB",
        ])


class DuplicateOccurrenceTests(unittest.TestCase):
    """E. Duplicate occurrences -- the parser must preserve every occurrence
    even though the current canonical Master has zero duplicates."""

    def test_repeated_exact_literal_both_preserved(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Grp"\n'
            '\t{\n'
            '\t\t"control"\t\t"Dupe"\n'
            '\t\t"control"\t\t"Dupe"\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        dupes = [o for o in result.occurrences if o.literal == "Dupe"]
        self.assertEqual(len(dupes), 2)
        self.assertEqual([o.global_rank for o in dupes], [0, 1])
        self.assertEqual([o.local_rank for o in dupes], [0, 1])


class AsciiFoldFamilyTests(unittest.TestCase):
    """F. ASCII families -- single spelling, same-destination aliases,
    cross-destination aliases (conflict)."""

    def test_single_exact_spelling_no_conflict(self):
        content = (
            'groupFile\n{\n\t"Grp"\n\t{\n\t\t"control"\t\t"OnlyOne"\n\t}\n}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        families = core.build_fold_families(result.occurrences)
        fam = families[core.ascii_fold("OnlyOne")]
        self.assertEqual(fam.exact_spellings, {"OnlyOne"})
        self.assertFalse(fam.is_conflict)

    def test_same_destination_aliases_not_a_conflict(self):
        content = (
            'groupFile\n{\n\t"Grp"\n\t{\n'
            '\t\t"control"\t\t"Foo"\n'
            '\t\t"control"\t\t"foo"\n'
            '\t\t"control"\t\t"FOO"\n'
            '\t}\n}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        families = core.build_fold_families(result.occurrences)
        fam = families["foo"]
        self.assertEqual(fam.exact_spellings, {"Foo", "foo", "FOO"})
        self.assertEqual(fam.destinations, {"groupFile/Grp"})
        self.assertFalse(fam.is_conflict)
        self.assertEqual(len(fam.occurrence_global_ranks), 3)

    def test_cross_destination_aliases_are_a_conflict(self):
        content = (
            'groupFile\n{\n'
            '\t"GrpA"\n\t{\n\t\t"control"\t\t"Bar"\n\t}\n'
            '\t"GrpB"\n\t{\n\t\t"control"\t\t"bar"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        families = core.build_fold_families(result.occurrences)
        fam = families["bar"]
        self.assertEqual(fam.exact_spellings, {"Bar", "bar"})
        self.assertEqual(fam.destinations, {"groupFile/GrpA", "groupFile/GrpB"})
        self.assertTrue(fam.is_conflict)

    def test_exact_spelling_match_inside_conflict_still_a_conflict(self):
        # Even though "Bar" exactly matches one member of the family, the
        # family as a whole must still report as a conflict -- the future
        # lookup rule (Phase A Part 4.8) must never let an exact match
        # silently bypass a still-conflicting fold.
        content = (
            'groupFile\n{\n'
            '\t"GrpA"\n\t{\n\t\t"control"\t\t"Bar"\n\t}\n'
            '\t"GrpB"\n\t{\n\t\t"control"\t\t"bar"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        families = core.build_fold_families(result.occurrences)
        fam = families[core.ascii_fold("Bar")]
        self.assertIn("Bar", fam.exact_spellings)
        self.assertTrue(fam.is_conflict)


class MalformedInputTests(unittest.TestCase):
    """G. Malformed input must fail closed -- no silent partial success."""

    def test_unterminated_quote(self):
        content = (
            'groupFile\n{\n\t"Grp"\n\t{\n'
            '\t\t"control"\t\t"Unterminated\n'
            '\t}\n}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("unrecognized_content", kinds)

    def test_unmatched_open_brace(self):
        # The single "}" present closes "Grp" (innermost-first, as any
        # brace stack must); "groupFile" itself is left open at EOF.
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"control"\t\t"X"\n\t}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        self.assertEqual(result.stack_depth_at_eof, 1)
        self.assertTrue(any(name == "groupFile" for name, _line in result.unmatched_opens))

    def test_unmatched_close_brace(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"control"\t\t"X"\n\t}\n}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        self.assertEqual(len(result.unmatched_closes), 1)

    def test_truncated_nested_group(self):
        content = (
            'groupFile\n{\n\t"Outer"\n\t{\n\t\t"Inner"\n\t\t{\n\t\t\t"control"\t\t"X"\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        self.assertEqual(result.stack_depth_at_eof, 3)  # groupFile, Outer, Inner all unclosed

    def test_brace_without_preceding_name_is_impossible_sequence(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t{\n\t\t\t"control"\t\t"X"\n\t\t}\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("brace_without_name", kinds)

    def test_valid_master_has_zero_grammar_errors(self):
        # Guard against over-tightening: a syntactically ordinary fixture
        # must never trip the new hardening.
        content = (
            'groupFile\n{\n\t"Grp"\n\t{\n'
            '\t\t"groupColor"\t\t"1 2 3 4"\n'
            '\t\t"selectable" "1"\n'
            '\t\t"control"\t\t"Fine"\n'
            '\t}\n}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        self.assertEqual(result.grammar_errors, [])


class TailEofTests(unittest.TestCase):
    """H. A valid final group/control at EOF must survive intact."""

    def test_final_control_and_group_at_eof(self):
        content = (
            'groupFile\n{\n'
            '\t"Grp"\n\t{\n\t\t"control"\t\t"Middle"\n\t}\n'
            '\t"LastGroup"\n\t{\n\t\t"control"\t\t"VeryLastControl"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        last_occ = result.occurrences[-1]
        self.assertEqual(last_occ.literal, "VeryLastControl")
        self.assertEqual(last_occ.full_path, "groupFile/LastGroup")
        self.assertEqual(last_occ.global_rank, len(result.occurrences) - 1)
        self.assertEqual(result.root_paths[-1], "groupFile/LastGroup")

    def test_final_control_no_trailing_newline(self):
        # No trailing "\n" after the final closing brace.
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"control"\t\t"Last"\n\t}\n}'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        self.assertEqual(result.occurrences[-1].literal, "Last")


if __name__ == "__main__":
    unittest.main()
