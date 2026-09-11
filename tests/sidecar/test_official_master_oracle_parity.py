"""Phase B2A, Part 13: one explicit, complete (not sampled) parity test
comparing the independent oracle against tools/sfm_master_core.py for the
entire official canonical Master.

This is the highest-value single test in the B2A corpus: if the qualified
core and the independently-implemented oracle ever disagree on the real
128,555-occurrence Master, that is a STOP-and-report condition (Phase B2A
Part 19), not something either side should be adjusted to paper over.
"""

import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import oracle  # noqa: E402
import sfm_master_core as core  # noqa: E402

MASTER_PATH = REPO_ROOT / "sfm_defaultanimationgroups.txt"


class OfficialMasterOracleParityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(MASTER_PATH, "rb") as f:
            cls.data = f.read()

        t0 = time.time()
        cls.oracle_result = oracle.scan_bytes(cls.data)
        cls.oracle_seconds = time.time() - t0

        t1 = time.time()
        cls.core_result = core.parse_master_bytes(cls.data, source_name=str(MASTER_PATH))
        cls.core_seconds = time.time() - t1

        print(f"\n[B2A parity] oracle scan: {cls.oracle_seconds:.2f}s, "
              f"core parse: {cls.core_seconds:.2f}s")

    def test_core_parses_cleanly(self):
        self.assertTrue(self.core_result.ok)

    def test_top_level_counts_match(self):
        self.assertEqual(len(self.oracle_result.groups), 43)
        self.assertEqual(len(self.core_result.groups), 43)
        self.assertEqual(len(self.oracle_result.controls), 128555)
        self.assertEqual(len(self.core_result.occurrences), 128555)
        o_meta = self.oracle_result.metadata_count()
        c_meta = sum(len(g.metadata.entries) for g in self.core_result.groups)
        self.assertEqual(o_meta, 54)
        self.assertEqual(c_meta, 54)
        self.assertEqual(o_meta, c_meta)

    def test_wrapper_identity(self):
        parentless = self.oracle_result.parentless_groups()
        self.assertEqual(len(parentless), 1)
        self.assertEqual(parentless[0].name, "groupFile")
        self.assertEqual(self.core_result.wrapper_paths, ["groupFile"])

    def test_full_group_parity(self):
        """Exhaustive -- every one of the 43 groups, not a sample."""
        o_by_path = {g.full_path: g for g in self.oracle_result.groups}
        c_by_path = self.core_result.groups_by_path

        self.assertEqual(set(o_by_path.keys()), set(c_by_path.keys()))

        o_decl_order = [g.full_path for g in sorted(self.oracle_result.groups, key=lambda g: g.declare_order)]
        c_decl_order = [g.full_path for g in sorted(self.core_result.groups, key=lambda g: g.declare_order)]
        self.assertEqual(o_decl_order, c_decl_order)

        for path, og in o_by_path.items():
            cg = c_by_path[path]
            with self.subTest(path=path):
                self.assertEqual(og.name, cg.name)
                self.assertEqual(og.parent_path, cg.parent_path)
                self.assertEqual(og.sibling_index, cg.sibling_rank)
                self.assertEqual(og.declare_order, cg.declare_order)

                # ancestry parity: reconstruct core's ancestry via its own
                # parent chain and compare exact name sequence
                core_ancestry_paths = []
                cur = cg.parent_path
                while cur is not None:
                    core_ancestry_paths.append(cur)
                    cur = c_by_path[cur].parent_path
                core_ancestry_paths.reverse()
                core_ancestry_names = [c_by_path[p].name for p in core_ancestry_paths]
                self.assertEqual(list(og.ancestry), core_ancestry_names)

    def test_full_control_parity(self):
        """Exhaustive -- every one of the 128,555 occurrences, not a sample."""
        o_controls = self.oracle_result.controls
        c_controls = self.core_result.occurrences
        self.assertEqual(len(o_controls), len(c_controls))

        mismatches = []
        for oc, cc in zip(o_controls, c_controls):
            if (oc.token, oc.owning_path, oc.local_rank, oc.global_order) != (
                cc.literal, cc.full_path, cc.local_rank, cc.global_rank
            ):
                mismatches.append((oc, cc))
                if len(mismatches) > 5:
                    break
        self.assertEqual(mismatches, [], f"first mismatches: {mismatches[:5]}")

    def test_full_metadata_parity(self):
        """Exhaustive over every group's metadata slice."""
        o_by_path = self.oracle_result.metadata_by_path()
        c_by_path = {
            g.full_path: g.metadata.entries
            for g in self.core_result.groups if g.metadata.entries
        }
        self.assertEqual(set(o_by_path.keys()), set(c_by_path.keys()))
        for path, oentries in o_by_path.items():
            with self.subTest(path=path):
                centries = c_by_path[path]
                self.assertEqual(len(oentries), len(centries))
                o_sorted = sorted(oentries, key=lambda e: e.local_order)
                for oe, ce in zip(o_sorted, centries):
                    self.assertEqual((oe.key, oe.value), (ce.key, ce.value))

    def test_runtime_is_practical(self):
        # Generous ceiling for "practical on a normal development machine"
        # (Part 14) -- not a tight performance assertion, just a guard
        # against a pathological accidental O(n^2) regression.
        self.assertLess(self.oracle_seconds, 30.0)
        self.assertLess(self.core_seconds, 30.0)


if __name__ == "__main__":
    unittest.main()
