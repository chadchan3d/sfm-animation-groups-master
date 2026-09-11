"""Phase B0.1 tests: source-completeness hardening and wrapper/path-identity
corrections identified by Astra's external review of the B1 design.

These are additive to tests/test_sfm_master_core.py (B0), which continues to
pass unmodified -- this file only covers the new B0.1 findings.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402


def fixture_bytes(content: str) -> bytes:
    return content.encode("utf-8")


class WrapperPreservationTests(unittest.TestCase):
    """A. Wrapper preservation -- a custom wrapper name is ordinary semantic
    data, not disposable syntax, and is never hardcoded to "groupFile"."""

    def test_custom_wrapper_name_and_metadata_and_control_retained(self):
        content = (
            'MyCustomDoc\n'
            '{\n'
            '\t"selectable" "1"\n'
            '\t"control"\t\t"WrapperOwnedControl"\n'
            '\t"Taxonomy"\n'
            '\t{\n'
            '\t\t"control"\t\t"Nested"\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)

        self.assertEqual(result.wrapper_paths, ["MyCustomDoc"])
        wrapper = result.groups_by_path["MyCustomDoc"]
        self.assertEqual(wrapper.name, "MyCustomDoc")
        self.assertIsNone(wrapper.parent_path)
        self.assertTrue(wrapper.metadata.present("selectable"))
        self.assertEqual(wrapper.metadata.value("selectable"), "1")

        wrapper_owned = [o for o in result.occurrences if o.full_path == "MyCustomDoc"]
        self.assertEqual([o.literal for o in wrapper_owned], ["WrapperOwnedControl"])

        # Nested full path includes the exact custom wrapper name.
        self.assertIn("MyCustomDoc/Taxonomy", result.groups_by_path)
        nested = [o for o in result.occurrences if o.literal == "Nested"]
        self.assertEqual(nested[0].full_path, "MyCustomDoc/Taxonomy")

        self.assertEqual(result.root_paths, ["MyCustomDoc/Taxonomy"])


class DanglingTokenTests(unittest.TestCase):
    """B. Dangling token must fail, not be silently discarded."""

    def test_orphan_word_token(self):
        content = (
            '"groupFile"\n{\n'
            '\t"A"\n\t{\n\t\t"control" "x"\n\t}\n'
            '\torphan\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("dangling_token", kinds)


class BarePropertyValueTests(unittest.TestCase):
    """C. Bare/unquoted metadata-like forms must fail explicitly."""

    def test_fully_bare_pair(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\tvisible 0\n\t\t"control" "x"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("bare_property_value_pair", kinds)

    def test_unquoted_key_quoted_value(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\tvisible "0"\n\t\t"control" "x"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("unquoted_metadata_key", kinds)

    def test_quoted_key_unquoted_value(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"visible" 0\n\t\t"control" "x"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("unquoted_metadata_value", kinds)

    def test_wellformed_quoted_metadata_still_passes(self):
        # Guard against over-tightening.
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"visible" "0"\n\t\t"control" "x"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        self.assertEqual(result.groups_by_path["groupFile/Grp"].metadata.value("visible"), "0")


class DuplicateSiblingGroupTests(unittest.TestCase):
    """D. Duplicate sibling group names must fail, never overwrite/merge."""

    def test_duplicate_sibling_group_name_rejected(self):
        content = (
            'groupFile\n{\n'
            '\t"A"\n\t{\n\t\t"control" "x1"\n\t}\n'
            '\t"A"\n\t{\n\t\t"control" "x2"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        dup_errors = [e for e in result.grammar_errors if e.kind == "duplicate_group_path"]
        self.assertEqual(len(dup_errors), 1)
        self.assertIn("groupFile/A", dup_errors[0].message)
        # Both declarations' controls are still individually visible in the
        # raw evidence (not merged away) -- x1 and x2 both parsed.
        literals = {o.literal for o in result.occurrences}
        self.assertEqual(literals, {"x1", "x2"})


class SlashInGroupNameTests(unittest.TestCase):
    """E. A "/" inside a group name is rejected -- ambiguous path identity."""

    def test_slash_in_name_rejected(self):
        content = 'groupFile\n{\n\t"A/B"\n\t{\n\t\t"control" "x"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertFalse(result.ok)
        kinds = {e.kind for e in result.grammar_errors}
        self.assertIn("slash_in_group_name", kinds)


class DuplicateControlOccurrenceStillAllowedTests(unittest.TestCase):
    """F. Duplicate CONTROL occurrences remain fully representable -- this is
    a distinct rule from duplicate GROUP paths (E/D above)."""

    def test_duplicate_control_literal_not_a_grammar_error(self):
        content = 'groupFile\n{\n\t"Grp"\n\t{\n\t\t"control" "Dupe"\n\t\t"control" "Dupe"\n\t}\n}\n'
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        dupes = [o for o in result.occurrences if o.literal == "Dupe"]
        self.assertEqual(len(dupes), 2)
        self.assertEqual([o.global_rank for o in dupes], [0, 1])
        self.assertEqual([o.local_rank for o in dupes], [0, 1])


class CrossDestinationFoldFamilyStillAllowedTests(unittest.TestCase):
    """G. Cross-destination ASCII-fold conflicts remain representable at the
    parser level -- rejecting these is validator/official policy, not a
    grammar rule."""

    def test_cross_destination_fold_is_not_a_grammar_error(self):
        content = (
            'groupFile\n{\n'
            '\t"GrpA"\n\t{\n\t\t"control" "Bar"\n\t}\n'
            '\t"GrpB"\n\t{\n\t\t"control" "bar"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        fams = core.build_fold_families(result.occurrences)
        fam = fams["bar"]
        self.assertTrue(fam.is_conflict)


class SameLineEncounterOrderTests(unittest.TestCase):
    """H. Same-line sibling groups must order by true token-encounter order,
    not by open_line (which is not unique) and not by close-order."""

    def test_same_line_siblings_ordered_by_declaration(self):
        content = (
            'groupFile\n{\n'
            '\t"First"\n\t{\n\t\t"control" "a"\n\t}\t"Second"\n\t{\n\t\t"control" "b"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        # "First" closes and "Second" opens on the SAME source line.
        first = result.groups_by_path["groupFile/First"]
        second = result.groups_by_path["groupFile/Second"]
        self.assertEqual(first.close_line, second.name_line)  # confirms the same-line setup
        self.assertLess(first.declare_order, second.declare_order)
        self.assertEqual(result.root_paths, ["groupFile/First", "groupFile/Second"])
        self.assertEqual(first.sibling_rank, 0)
        self.assertEqual(second.sibling_rank, 1)

    def test_three_groups_declared_on_one_line_preserve_declaration_order(self):
        content = (
            'groupFile\n{\n'
            '\t"A"\t{\t"control" "a"\t}\t"B"\t{\t"control" "b"\t}\t"C"\t{\t"control" "c"\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        self.assertEqual(result.root_paths, ["groupFile/A", "groupFile/B", "groupFile/C"])
        ranks = [result.groups_by_path[p].sibling_rank for p in result.root_paths]
        self.assertEqual(ranks, [0, 1, 2])


class UnknownWellFormedMetadataTests(unittest.TestCase):
    """I. An unknown-but-well-formed metadata key is preserved, not rejected
    and not semantically interpreted -- distinct from malformed token
    structure (C above)."""

    def test_unknown_key_preserved_with_order_and_duplicates(self):
        content = (
            'groupFile\n{\n\t"Grp"\n\t{\n'
            '\t\t"someFutureKey"\t\t"alpha"\n'
            '\t\t"someFutureKey"\t\t"beta"\n'
            '\t\t"control" "x"\n'
            '\t}\n}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        grp = result.groups_by_path["groupFile/Grp"]
        self.assertTrue(grp.metadata.present("someFutureKey"))
        self.assertEqual(grp.metadata.values("someFutureKey"), ["alpha", "beta"])


class EofFinalEntryTests(unittest.TestCase):
    """J. Valid final structure at EOF survives exactly, post-hardening."""

    def test_final_group_and_control_survive(self):
        content = (
            'groupFile\n{\n'
            '\t"Grp"\n\t{\n\t\t"control" "Middle"\n\t}\n'
            '\t"LastGroup"\n\t{\n\t\t"control" "VeryLast"\n\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        self.assertEqual(result.occurrences[-1].literal, "VeryLast")
        self.assertEqual(result.root_paths[-1], "groupFile/LastGroup")


class ParentValidityTests(unittest.TestCase):
    """Parent relationships come from parsed structure (the stack at close
    time), never from string-splitting `full_path`."""

    def test_parent_path_matches_structural_nesting(self):
        content = (
            'groupFile\n{\n'
            '\t"Outer"\n\t{\n'
            '\t\t"Inner"\n\t\t{\n\t\t\t"control" "x"\n\t\t}\n'
            '\t}\n'
            '}\n'
        )
        result = core.parse_master_bytes(fixture_bytes(content))
        self.assertTrue(result.ok)
        outer = result.groups_by_path["groupFile/Outer"]
        inner = result.groups_by_path["groupFile/Outer/Inner"]
        self.assertEqual(outer.parent_path, "groupFile")
        self.assertEqual(inner.parent_path, "groupFile/Outer")
        self.assertIsNone(result.groups_by_path["groupFile"].parent_path)


class CanonicalMasterRegressionTest(unittest.TestCase):
    """Full canonical-Master regression after B0.1 hardening."""

    def test_canonical_master_unchanged(self):
        path = REPO_ROOT / "sfm_defaultanimationgroups.txt"
        before = path.read_bytes()
        result = core.parse_master_bytes(before, source_name=str(path))
        self.assertTrue(result.ok)
        self.assertEqual(len(result.groups), 43)
        self.assertEqual(len(result.occurrences), 128555)
        self.assertEqual(result.wrapper_paths, ["groupFile"])
        self.assertEqual(len(result.root_paths), 21)
        families = core.build_fold_families(result.occurrences)
        self.assertEqual(len(families), 124728)
        after = path.read_bytes()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
