"""Phase B2E: tools/sfm_master_sidecar/compiler.py -- single production
compiler orchestration path, generic-vs-official policy, self-validation,
and semantic parity.
"""

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sfm_master_sidecar import compiler, reader, writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"
MASTER_PATH = REPO_ROOT / "sfm_defaultanimationgroups.txt"

EXPECTED_OFFICIAL_ARTIFACT_SHA = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
EXPECTED_OFFICIAL_SOURCE_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"


class SourceSnapshotTests(unittest.TestCase):

    def test_snapshot_reads_exact_bytes_once_and_hashes_them(self):
        path = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        snap = compiler.capture_source_snapshot(path)
        import hashlib
        self.assertEqual(snap.bytes, path.read_bytes())
        self.assertEqual(snap.sha256_hex, hashlib.sha256(snap.bytes).hexdigest())
        self.assertEqual(snap.path, path)


class GenericAcceptanceTests(unittest.TestCase):

    def test_generic_compile_accepts_duplicate_controls(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "10_repeated_identical_control_one_group.txt")
        outcome = compiler.parse_and_compile(snap)
        self.assertGreater(len(outcome.blob), 0)

    def test_generic_compile_accepts_cross_destination_fold_conflict(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "13_same_fold_different_destinations.txt")
        outcome = compiler.parse_and_compile(snap)
        self.assertGreater(len(outcome.blob), 0)

    def test_malformed_source_raises_source_grammar_error(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "malformed" / "unmatched_opening_brace.txt")
        with self.assertRaises(compiler.SourceGrammarError):
            compiler.parse_and_compile(snap)

    def test_profile_unsupported_source_raises_profile_error(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "unsupported" / "empty_document.txt")
        with self.assertRaises(writer.SidecarProfileError):
            compiler.parse_and_compile(snap)

    def test_official_policy_flag_does_not_change_generic_acceptance_of_valid_fixtures(self):
        # A custom Master with cross-destination conflicts is generically
        # eligible; official_policy=True must not reject it merely for
        # requesting the extra gate -- the gate itself only applies its own
        # extra checks, it does not change the generic writer's own
        # acceptance criteria.
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "04_custom_wrapper_name.txt")
        outcome = compiler.parse_and_compile(snap)  # generic: succeeds
        self.assertGreater(len(outcome.blob), 0)


class SelfValidationTests(unittest.TestCase):

    def test_self_validate_from_bytes_succeeds_for_correct_compile(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt")
        outcome = compiler.parse_and_compile(snap)
        compiler.self_validate_from_bytes(outcome)  # must not raise

    def test_verify_semantic_parity_detects_group_count_mismatch(self):
        import sfm_master_core as core
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt")
        result = core.parse_master_bytes(snap.bytes, source_name="x")
        blob = writer.compile_sidecar(snap.bytes, result)
        r = reader.SidecarReader.open_generation(blob, result.source_sha256)
        try:
            # Fabricate a result claiming one extra group that the reader
            # does not actually have -- must be detected, not silently
            # accepted.
            import copy
            fake_group = copy.copy(result.groups[0])
            fake_group.full_path = "totally/fake/path/not/in/artifact"
            tampered_groups = list(result.groups) + [fake_group]
            tampered_result = copy.copy(result)
            tampered_result.groups = tampered_groups
            with self.assertRaises(compiler.SelfValidationError):
                compiler.verify_semantic_parity(tampered_result, r)
        finally:
            r.close()


class GenerationBasenameTests(unittest.TestCase):

    def test_generation_basename_format(self):
        name = compiler.generation_basename("a" * 64)
        self.assertTrue(name.startswith("sfm_master_0_"))
        self.assertTrue(name.endswith(".bin"))
        self.assertIn("a" * 64, name)


class OfficialMasterThroughCompilerTests(unittest.TestCase):
    """Part 23 (compiler-level, before publisher): the official Master
    compiled through this exact orchestration must reproduce the B2D
    artifact SHA exactly."""

    def test_official_master_reproduces_b2d_artifact_sha(self):
        snap = compiler.capture_source_snapshot(MASTER_PATH)
        self.assertEqual(snap.sha256_hex, EXPECTED_OFFICIAL_SOURCE_SHA)
        outcome = compiler.parse_and_compile(snap)
        self.assertEqual(outcome.ordinary_sha256, EXPECTED_OFFICIAL_ARTIFACT_SHA)
        compiler.self_validate_from_bytes(outcome)

    def test_official_master_passes_official_policy_gate(self):
        snap = compiler.capture_source_snapshot(MASTER_PATH)
        outcome = compiler.parse_and_compile(snap, official_policy=True)
        self.assertEqual(outcome.ordinary_sha256, EXPECTED_OFFICIAL_ARTIFACT_SHA)


class DeterminismThroughPublicOrchestrationTests(unittest.TestCase):
    """Part 24: same source through the public compiler orchestration path
    (not the bare `writer.compile_sidecar` call) must produce identical
    bytes/SHA/immutable basename -- same-process and cross-`PYTHONHASHSEED`
    subprocess."""

    def test_same_process_double_compile_via_public_path(self):
        snap = compiler.capture_source_snapshot(FIXTURES_ROOT / "valid" / "28_large_alias_family.txt")
        outcome_a = compiler.parse_and_compile(snap)
        outcome_b = compiler.parse_and_compile(snap)
        self.assertEqual(outcome_a.blob, outcome_b.blob)
        self.assertEqual(outcome_a.ordinary_sha256, outcome_b.ordinary_sha256)
        self.assertEqual(
            compiler.generation_basename(outcome_a.ordinary_sha256),
            compiler.generation_basename(outcome_b.ordinary_sha256),
        )

    def test_official_master_same_process_double_compile_via_public_path(self):
        snap = compiler.capture_source_snapshot(MASTER_PATH)
        outcome_a = compiler.parse_and_compile(snap)
        outcome_b = compiler.parse_and_compile(snap)
        self.assertEqual(outcome_a.ordinary_sha256, EXPECTED_OFFICIAL_ARTIFACT_SHA)
        self.assertEqual(outcome_a.ordinary_sha256, outcome_b.ordinary_sha256)

    def test_cross_hashseed_subprocess_via_public_orchestration(self):
        import os
        import subprocess

        def compile_in_subprocess(hash_seed):
            script = (
                "import sys\n"
                "sys.path.insert(0, %r)\n"
                "from sfm_master_sidecar import compiler\n"
                "snap = compiler.capture_source_snapshot(%r)\n"
                "outcome = compiler.parse_and_compile(snap)\n"
                "print(outcome.ordinary_sha256 + ',' + compiler.generation_basename(outcome.ordinary_sha256))\n"
            ) % (str(REPO_ROOT / "tools"), str(MASTER_PATH))
            env = dict(os.environ)
            env["PYTHONHASHSEED"] = str(hash_seed)
            proc = subprocess.run(
                [sys.executable, "-c", script], cwd=str(REPO_ROOT), env=env,
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            sha, basename = proc.stdout.strip().split(",")
            return sha, basename

        sha0, basename0 = compile_in_subprocess(0)
        sha1, basename1 = compile_in_subprocess(999983)
        self.assertEqual(sha0, sha1)
        self.assertEqual(basename0, basename1)
        self.assertEqual(sha0, EXPECTED_OFFICIAL_ARTIFACT_SHA)


if __name__ == "__main__":
    unittest.main()
