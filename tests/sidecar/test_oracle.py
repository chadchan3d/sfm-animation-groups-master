"""Phase B2A: oracle self-discipline tests.

Prove the independent oracle (tests/sidecar/oracle.py) is not merely a
counter -- it must detect a semantic change (omission, reassignment,
reordering) even when a naive count-only comparison would not."""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import oracle  # noqa: E402


BASE = (
    'groupFile\n{\n'
    '\t"GrpA"\n\t{\n'
    '\t\t"selectable" "1"\n'
    '\t\t"visible" "0"\n'
    '\t\t"control"\t\t"First"\n'
    '\t\t"control"\t\t"Second"\n'
    '\t\t"control"\t\t"Third"\n'
    '\t}\n'
    '\t"GrpB"\n\t{\n'
    '\t\t"control"\t\t"Fourth"\n'
    '\t}\n'
    '}\n'
)


def scan(text: str) -> oracle.OracleResult:
    return oracle.scan_bytes(text.encode("utf-8"))


class SelfDisciplineTests(unittest.TestCase):

    def test_A_remove_middle_control_changes_projection(self):
        baseline = scan(BASE)
        mutated_text = BASE.replace('\t\t"control"\t\t"Second"\n', '')
        mutated = scan(mutated_text)

        self.assertEqual(baseline.control_count(), 4)
        self.assertEqual(mutated.control_count(), 3)
        self.assertNotEqual(
            [c.token for c in baseline.controls],
            [c.token for c in mutated.controls],
        )
        self.assertNotIn("Second", [c.token for c in mutated.controls])

    def test_B_replace_control_with_duplicate_same_count_still_differs(self):
        baseline = scan(BASE)
        # "Second" replaced by another "First" -- total count is UNCHANGED,
        # but the exact sequence of literals must differ, and the omitted
        # literal ("Second") must be detectably missing.
        mutated_text = BASE.replace(
            '\t\t"control"\t\t"Second"\n', '\t\t"control"\t\t"First"\n'
        )
        mutated = scan(mutated_text)

        self.assertEqual(baseline.control_count(), mutated.control_count())
        self.assertNotEqual(
            [c.token for c in baseline.controls],
            [c.token for c in mutated.controls],
        )
        self.assertIn("Second", [c.token for c in baseline.controls])
        self.assertNotIn("Second", [c.token for c in mutated.controls])
        self.assertEqual(mutated.literal_multiplicity()["First"], 2)

    def test_C_reorder_metadata_changes_projection(self):
        baseline = scan(BASE)
        swapped_text = BASE.replace(
            '\t\t"selectable" "1"\n\t\t"visible" "0"\n',
            '\t\t"visible" "0"\n\t\t"selectable" "1"\n',
        )
        swapped = scan(swapped_text)

        base_meta = baseline.metadata_by_path()["groupFile/GrpA"]
        swapped_meta = swapped.metadata_by_path()["groupFile/GrpA"]
        base_order = [(m.key, m.local_order) for m in base_meta]
        swapped_order = [(m.key, m.local_order) for m in swapped_meta]
        self.assertNotEqual(base_order, swapped_order)
        # same set of keys/values, only order differs
        self.assertEqual(
            sorted((m.key, m.value) for m in base_meta),
            sorted((m.key, m.value) for m in swapped_meta),
        )

    def test_D_reorder_groups_changes_projection(self):
        baseline = scan(BASE)
        # swap GrpA and GrpB's entire declaration order
        swapped_text = (
            'groupFile\n{\n'
            '\t"GrpB"\n\t{\n'
            '\t\t"control"\t\t"Fourth"\n'
            '\t}\n'
            '\t"GrpA"\n\t{\n'
            '\t\t"selectable" "1"\n'
            '\t\t"visible" "0"\n'
            '\t\t"control"\t\t"First"\n'
            '\t\t"control"\t\t"Second"\n'
            '\t\t"control"\t\t"Third"\n'
            '\t}\n'
            '}\n'
        )
        swapped = scan(swapped_text)

        base_names = [g.name for g in sorted(baseline.groups, key=lambda g: g.declare_order)]
        swapped_names = [g.name for g in sorted(swapped.groups, key=lambda g: g.declare_order)]
        self.assertNotEqual(base_names, swapped_names)
        self.assertEqual(set(base_names), set(swapped_names))

    def test_E_remove_final_tail_item_changes_coverage(self):
        baseline = scan(BASE)
        without_tail_text = BASE.replace(
            '\t"GrpB"\n\t{\n\t\t"control"\t\t"Fourth"\n\t}\n', ''
        )
        without_tail = scan(without_tail_text)

        self.assertEqual(baseline.last_control().token, "Fourth")
        self.assertNotEqual(without_tail.last_control().token, "Fourth")
        self.assertEqual(without_tail.last_control().token, "Third")
        self.assertEqual(without_tail.group_count(), baseline.group_count() - 1)


class OracleIndependenceSmokeTests(unittest.TestCase):
    """Not a self-discipline test -- a minimal sanity check that the oracle
    module itself does not import production semantic code. Checks actual
    `import`/`from ... import` statements via the AST, not prose mentions in
    comments/docstrings (the module docstring legitimately discusses
    sfm_master_core.py by name when explaining the independence boundary)."""

    def test_oracle_module_does_not_import_production_core(self):
        import ast

        oracle_path = HERE / "oracle.py"
        tree = ast.parse(oracle_path.read_text(encoding="utf-8"), filename=str(oracle_path))
        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names.add(node.module.split(".")[0])

        forbidden = {"sfm_master_core", "validate_master"}
        self.assertFalse(
            imported_names & forbidden,
            f"oracle.py must not import any of {forbidden} -- independence boundary violated "
            f"(found imports: {imported_names})",
        )


if __name__ == "__main__":
    unittest.main()
