"""Phase B2E Parts 17-19/26-27: failure preservation. An existing valid
publication must survive UNCHANGED no matter where in the pipeline a
subsequent failed publish attempt breaks -- source parsing, profile check,
writer compile, reader validation, semantic parity, live-source recheck, or
manifest serialization/replacement. Uses the narrow, test-only
`_fault_hook` parameter (Phase B2E Part 27) -- never a broad public debug
API.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sfm_master_sidecar import compiler, publisher, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"


class FailurePreservationTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="b2e-failpreserve-")
        self.baseline_src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        self.baseline_result = publisher.publish(self.baseline_src, self.tmp)
        self.baseline_manifest_bytes = (Path(self.tmp) / "manifest.json").read_bytes()
        self.baseline_gen_files = sorted(
            p.name for p in Path(self.tmp).iterdir() if p.suffix == ".bin"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _assert_baseline_untouched(self):
        current_manifest = (Path(self.tmp) / "manifest.json").read_bytes()
        self.assertEqual(current_manifest, self.baseline_manifest_bytes, "prior manifest must survive unchanged")
        current_gen_files = sorted(p.name for p in Path(self.tmp).iterdir() if p.suffix == ".bin")
        for name in self.baseline_gen_files:
            self.assertIn(name, current_gen_files, "prior generation must never be removed")
        leftover_tmp = [p.name for p in Path(self.tmp).iterdir() if p.name.startswith(".tmp")]
        self.assertEqual(leftover_tmp, [], "no leftover temp files after a failed publish")


class SourceLevelFailurePreservationTests(FailurePreservationTestCase):

    def test_malformed_source_leaves_baseline_untouched(self):
        with self.assertRaises(compiler.SourceGrammarError):
            publisher.publish(FIXTURES_ROOT / "malformed" / "unmatched_opening_brace.txt", self.tmp)
        self._assert_baseline_untouched()

    def test_profile_unsupported_source_leaves_baseline_untouched(self):
        with self.assertRaises(writer.SidecarProfileError):
            publisher.publish(FIXTURES_ROOT / "unsupported" / "empty_document.txt", self.tmp)
        self._assert_baseline_untouched()


class InjectedStageFailurePreservationTests(FailurePreservationTestCase):
    """Inject a failure at each named point in the transaction (Phase B2E
    Part 27's required hook list) using a NEW, different source than the
    baseline, and confirm the baseline manifest/generation are entirely
    unaffected in every case."""

    STAGES = [
        "before_self_validation",
        "before_generation_publication",
        "after_generation_publication",
        "before_manifest_temp_write",
        "after_manifest_temp_write",
        "before_source_recheck",
        "before_manifest_replace",
    ]

    def _hook_raising_at(self, stage_to_fail):
        def hook(stage):
            if stage == stage_to_fail:
                raise RuntimeError("injected failure at %s" % stage)
        return hook

    def test_injected_failure_at_every_stage_preserves_baseline(self):
        other_src = FIXTURES_ROOT / "valid" / "05_nested_groups.txt"
        for stage in self.STAGES:
            with self.subTest(stage=stage):
                with self.assertRaises(RuntimeError):
                    publisher.publish(other_src, self.tmp, _fault_hook=self._hook_raising_at(stage))
                self._assert_baseline_untouched()

    def test_after_generation_publication_failure_leaves_new_generation_as_harmless_orphan(self):
        # A failure strictly AFTER the new generation file was already
        # promoted to its immutable name is explicitly allowed to leave
        # that generation behind as an orphan (Part 18/33) -- the manifest
        # must still not point at it.
        other_src = FIXTURES_ROOT / "valid" / "05_nested_groups.txt"
        outcome = compiler.parse_and_compile(compiler.capture_source_snapshot(other_src))
        expected_new_gen_name = compiler.generation_basename(outcome.ordinary_sha256)

        with self.assertRaises(RuntimeError):
            publisher.publish(
                other_src, self.tmp, _fault_hook=self._hook_raising_at("after_generation_publication"),
            )

        # the orphan generation file DOES exist now (harmless)...
        self.assertTrue((Path(self.tmp) / expected_new_gen_name).exists())
        # ...but the active manifest still points at the ORIGINAL baseline.
        self._assert_baseline_untouched()
        m = publisher.read_active_manifest(self.tmp)
        self.assertEqual(m.generation_basename, self.baseline_result.generation_basename)


class SourceMutationRaceTests(FailurePreservationTestCase):
    """Part 26: capture source A, mutate the live input to B right before
    the final activation section, require the mismatch is detected and A
    is never activated."""

    def test_source_mutated_before_recheck_aborts_activation(self):
        srcdir = tempfile.mkdtemp(prefix="b2e-race-src-")
        try:
            src_path = Path(srcdir) / "master.txt"
            a_bytes = (FIXTURES_ROOT / "valid" / "05_nested_groups.txt").read_bytes()
            b_bytes = (FIXTURES_ROOT / "valid" / "09_controls_after_nested_child.txt").read_bytes()
            src_path.write_bytes(a_bytes)

            def hook(stage):
                if stage == "before_source_recheck":
                    src_path.write_bytes(b_bytes)

            with self.assertRaises(publisher.SourceMutatedDuringPublicationError):
                publisher.publish(str(src_path), self.tmp, _fault_hook=hook)

            self._assert_baseline_untouched()
        finally:
            shutil.rmtree(srcdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
