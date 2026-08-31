"""Tests for tools/validate_master.py.

All fixtures are written to isolated temporary files inside a
TemporaryDirectory and are never the canonical Master. The one test that
reads the real canonical Master (test_canonical_master_passes) only reads
it; every test in this module additionally asserts that the validator
never modifies the bytes of whatever file it was pointed at.
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import validate_master  # noqa: E402


def write_fixture(tmp_dir, name, content):
    path = Path(tmp_dir) / name
    path.write_bytes(content.encode("utf-8"))
    return path


class ValidateMasterTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_dir = self._tmp.name

    # ------------------------------------------------------------------
    # TEST 1 - PASS: case variants sharing one path
    # ------------------------------------------------------------------
    def test_same_path_case_variants_pass(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Hand_r"\n'
            '\t\t"control"\t\t"hand_r"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "pass_same_path.txt", content)
        report = validate_master.validate(path)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["cross_path_family_count"], 0)
        self.assertEqual(report["exact_duplicate_count"], 0)
        self.assertTrue(report["structural_parse_pass"])

    # ------------------------------------------------------------------
    # TEST 2 - FAIL: case variants spanning different paths
    # ------------------------------------------------------------------
    def test_cross_path_case_variants_fail(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"hand_r"\n'
            '\t}\n'
            '\t"RigArms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Hand_r"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "fail_cross_path.txt", content)
        report = validate_master.validate(path)
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(report["cross_path_family_count"], 1)

        cross_failures = [f for f in report["failures"] if f["kind"] == "cross_path_casefold"]
        self.assertEqual(len(cross_failures), 1)
        family = cross_failures[0]["evidence"][0]
        self.assertEqual(family["key"], "hand_r")
        self.assertEqual(family["distinct_path_count"], 2)

        literals = {m["literal"] for m in family["members"]}
        paths = {m["path"] for m in family["members"]}
        self.assertEqual(literals, {"hand_r", "Hand_r"})
        self.assertEqual(paths, {"groupFile/Arms", "groupFile/RigArms"})
        for m in family["members"]:
            self.assertIsInstance(m["line"], int)
            self.assertGreater(m["line"], 0)

        # No suggested-fix / repair language should ever appear.
        text = validate_master.format_report(report)
        self.assertNotIn("Suggested fix", text)
        self.assertIn("No suggested fix", text)
        self.assertIn("No files have been modified.", text)

    # ------------------------------------------------------------------
    # TEST 3 - FAIL: exact duplicate literal
    # ------------------------------------------------------------------
    def test_exact_duplicate_fail(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Elbow_r"\n'
            '\t\t"control"\t\t"Elbow_r"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "fail_exact_dup.txt", content)
        report = validate_master.validate(path)
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(report["exact_duplicate_count"], 1)
        dup_failures = [f for f in report["failures"] if f["kind"] == "exact_duplicate"]
        self.assertEqual(len(dup_failures), 1)
        entry = dup_failures[0]["evidence"][0]
        self.assertEqual(entry["literal"], "Elbow_r")
        self.assertEqual(len(entry["occurrences"]), 2)

    # ------------------------------------------------------------------
    # TEST 4 - PASS: punctuation remains distinct (no normalization)
    # ------------------------------------------------------------------
    def test_punctuation_distinction_pass(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"foo-bar"\n'
            '\t\t"control"\t\t"foo_bar"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "pass_punctuation.txt", content)
        report = validate_master.validate(path)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["cross_path_family_count"], 0)
        self.assertEqual(report["unique_ascii_fold_keys"], 2)

    # ------------------------------------------------------------------
    # TEST 5 - PASS: ASCII-only fold (no broad Unicode casefold equivalence)
    # ------------------------------------------------------------------
    def test_ascii_only_fold_pass(self):
        # Greek capital OMEGA (U+03A9) and lowercase omega (U+03C9) are
        # Unicode-casefold-equivalent but fall entirely outside ASCII A-Z,
        # so a correct ASCII-only fold must leave them as distinct keys.
        content = (
            'groupFile\n'
            '{\n'
            '\t"Body Morphs"\n'
            '\t{\n'
            '\t\t"control"\t\t"Ω_test"\n'
            '\t}\n'
            '\t"Clothing"\n'
            '\t{\n'
            '\t\t"control"\t\t"ω_test"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "pass_ascii_only.txt", content)
        report = validate_master.validate(path)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["cross_path_family_count"], 0)
        self.assertEqual(
            validate_master.ascii_fold("Ω_test"),
            "Ω_test",
            "Non-ASCII characters must never be folded.",
        )
        self.assertEqual(
            validate_master.ascii_fold("ω_test"),
            "ω_test",
        )
        self.assertEqual(validate_master.ascii_fold("HAND_R"), "hand_r")

    # ------------------------------------------------------------------
    # TEST 6 - Structural failure (unmatched brace)
    # ------------------------------------------------------------------
    def test_structural_failure(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Hand_r"\n'
            '}\n'  # missing closing brace for "Arms"; only groupFile closes
        )
        path = write_fixture(self.tmp_dir, "fail_structural.txt", content)
        report = validate_master.validate(path)
        self.assertNotEqual(report["exit_code"], 0)
        self.assertFalse(report["structural_parse_pass"])
        structural_failures = [f for f in report["failures"] if f["kind"] == "structural_parse"]
        self.assertEqual(len(structural_failures), 1)

    # ------------------------------------------------------------------
    # TEST 7 - Current canonical Master integration test
    # ------------------------------------------------------------------
    def test_canonical_master_passes(self):
        path = validate_master.default_master_path()
        self.assertTrue(path.exists(), f"Canonical Master not found at {path}")
        report = validate_master.validate(path)
        self.assertTrue(report["structural_parse_pass"])
        self.assertEqual(report["exact_duplicate_count"], 0)
        self.assertEqual(report["cross_path_family_count"], 0)
        self.assertEqual(report["exit_code"], 0)

    # ------------------------------------------------------------------
    # Parser safeguard: only the exact key "control" contributes controls.
    # groupColor/selectable and any other metadata key must be ignored.
    # ------------------------------------------------------------------
    def test_non_control_metadata_keys_excluded(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"RightFingers"\n'
            '\t{\n'
            '\t\t"selectable"\t"1"\n'
            '\t\t"groupColor"\t\t"255 128 128 255"\n'
            '\t\t"control"\t\t"bip_thumb_0_r"\n'
            '\t}\n'
            '\t"RightCarpals"\n'
            '\t{\n'
            '\t\t"selectable"\t"0"\n'
            '\t\t"control"\t\t"RIG_Carpal0_R"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "metadata_keys.txt", content)
        report = validate_master.validate(path)
        # Only the two "control" lines should be counted; groupColor and
        # selectable must never enter the control inventory.
        self.assertEqual(report["control_count"], 2)
        self.assertEqual(report["unique_exact_literals"], 2)
        self.assertEqual(report["exit_code"], 0)

        parsed = validate_master.parse_structure(content.splitlines())
        literals = {lit for lit, _, _ in parsed.controls}
        self.assertEqual(literals, {"bip_thumb_0_r", "RIG_Carpal0_R"})
        self.assertNotIn("1", literals)
        self.assertNotIn("0", literals)
        self.assertNotIn("255 128 128 255", literals)

    # ------------------------------------------------------------------
    # Read-only regression: validating must never change the target bytes.
    # ------------------------------------------------------------------
    def test_validation_does_not_modify_passing_fixture(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Hand_r"\n'
            '\t\t"control"\t\t"hand_r"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "readonly_pass.txt", content)
        before = path.read_bytes()
        report = validate_master.validate(path)
        after = path.read_bytes()
        self.assertEqual(before, after, "Validator must not modify a passing target file.")
        self.assertEqual(report["exit_code"], 0)

    def test_validation_does_not_modify_failing_fixture(self):
        content = (
            'groupFile\n'
            '{\n'
            '\t"Arms"\n'
            '\t{\n'
            '\t\t"control"\t\t"hand_r"\n'
            '\t}\n'
            '\t"RigArms"\n'
            '\t{\n'
            '\t\t"control"\t\t"Hand_r"\n'
            '\t}\n'
            '}\n'
        )
        path = write_fixture(self.tmp_dir, "readonly_fail.txt", content)
        before = path.read_bytes()
        report = validate_master.validate(path)
        after = path.read_bytes()
        self.assertEqual(before, after, "Validator must not modify a failing target file, even on FAIL.")
        self.assertEqual(report["exit_code"], 1)

    def test_validation_does_not_modify_canonical_master(self):
        path = validate_master.default_master_path()
        self.assertTrue(path.exists(), f"Canonical Master not found at {path}")
        before = path.read_bytes()
        validate_master.validate(path)
        after = path.read_bytes()
        self.assertEqual(before, after, "Validator must never modify the canonical Master.")


if __name__ == "__main__":
    unittest.main()
