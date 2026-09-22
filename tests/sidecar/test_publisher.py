"""Phase B2E: tools/sfm_master_sidecar/publisher.py -- check-only, the full
publication transaction, generation identity/reuse/collision, manifest
readback, and OS-lock crash-safety. All filesystem output uses
`tempfile.TemporaryDirectory` -- nothing persists.
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

from sfm_master_sidecar import compiler, manifest, publisher, reader  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"
MASTER_PATH = REPO_ROOT / "sfm_defaultanimationgroups.txt"
EXPECTED_OFFICIAL_ARTIFACT_SHA = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"


class TempNamespaceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="b2e-pub-")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    @property
    def output_dir(self):
        return self._tmp


class CheckOnlyTests(TempNamespaceTestCase):

    def test_check_only_valid_source_succeeds_with_no_filesystem_output(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        result = publisher.check_only(src)
        self.assertEqual(len(result.outcome.result.groups), 4)
        # no output_dir was even passed -- check-only touches no filesystem
        # namespace at all.

    def test_check_only_malformed_source_fails(self):
        src = FIXTURES_ROOT / "malformed" / "unmatched_opening_brace.txt"
        with self.assertRaises(compiler.SourceGrammarError):
            publisher.check_only(src)

    def test_check_only_profile_unsupported_source_fails(self):
        src = FIXTURES_ROOT / "unsupported" / "multiple_parentless_groups.txt"
        from sfm_master_sidecar import writer
        with self.assertRaises(writer.SidecarProfileError):
            publisher.check_only(src)

    def test_check_only_cross_destination_conflict_succeeds(self):
        src = FIXTURES_ROOT / "valid" / "13_same_fold_different_destinations.txt"
        result = publisher.check_only(src)
        self.assertGreater(len(result.outcome.blob), 0)

    def test_check_only_never_touches_an_output_directory(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        before = sorted(Path(self.output_dir).iterdir())
        publisher.check_only(src)  # note: no output_dir argument exists on check_only at all
        after = sorted(Path(self.output_dir).iterdir())
        self.assertEqual(before, after)
        self.assertEqual(before, [])


class PublicationTransactionTests(TempNamespaceTestCase):

    def test_publish_creates_generation_and_manifest(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        result = publisher.publish(src, self.output_dir)
        self.assertFalse(result.reused)
        self.assertTrue(result.generation_path.exists())
        self.assertTrue(result.manifest_path.exists())

    def test_manifest_content_matches_published_generation(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        result = publisher.publish(src, self.output_dir)
        m = publisher.read_active_manifest(self.output_dir)
        self.assertEqual(m.generation_basename, result.generation_basename)
        self.assertEqual(m.sidecar_sha256, result.ordinary_sha256)
        self.assertEqual(m.source_sha256, result.source_sha256)

    def test_no_leftover_temp_files_after_successful_publish(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        publisher.publish(src, self.output_dir)
        names = [p.name for p in Path(self.output_dir).iterdir()]
        self.assertFalse(any(n.startswith(".tmp") for n in names))


class GenerationReusePartTests(TempNamespaceTestCase):

    def test_publishing_identical_source_twice_reuses_generation(self):
        src = FIXTURES_ROOT / "valid" / "28_large_alias_family.txt"
        r1 = publisher.publish(src, self.output_dir)
        r2 = publisher.publish(src, self.output_dir)
        self.assertFalse(r1.reused)
        self.assertTrue(r2.reused)
        self.assertEqual(r1.generation_basename, r2.generation_basename)
        self.assertEqual(r1.ordinary_sha256, r2.ordinary_sha256)
        # Package-Boundary Correction (2026-09-21): immutable generation
        # suffix changed to ".sfmsidecar" (was ".bin").
        gen_files = [p for p in Path(self.output_dir).iterdir() if p.suffix == ".sfmsidecar"]
        self.assertEqual(len(gen_files), 1, "no duplicate generation churn")

    def test_generation_collision_with_different_bytes_is_refused(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        outcome = compiler.parse_and_compile(compiler.capture_source_snapshot(src))
        gen_name = compiler.generation_basename(outcome.ordinary_sha256)
        # Pre-place DIFFERENT bytes under the immutable name the real
        # compile would produce -- simulates corruption/tampering (a real
        # SHA-256 collision is not constructible; this tests the same
        # "different bytes under the same immutable name" refusal path
        # regardless of how that state arose).
        (Path(self.output_dir) / gen_name).write_bytes(b"not the real sidecar content")
        with self.assertRaises(publisher.GenerationCollisionError):
            publisher.publish(src, self.output_dir)
        # the tampered file must survive untouched -- never overwritten.
        self.assertEqual((Path(self.output_dir) / gen_name).read_bytes(), b"not the real sidecar content")


class ManifestReadbackTests(TempNamespaceTestCase):

    def test_readback_proves_self_consistent_namespace(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        publisher.publish(src, self.output_dir)

        m = publisher.read_active_manifest(self.output_dir)
        gen_path = manifest.resolve_generation_path(self.output_dir, m)
        self.assertTrue(Path(gen_path).exists())

        import hashlib
        actual_sha = hashlib.sha256(Path(gen_path).read_bytes()).hexdigest()
        self.assertEqual(actual_sha, m.sidecar_sha256)

        r = reader.SidecarReader.open_generation_path(gen_path, m.source_sha256)
        try:
            self.assertTrue(r.is_valid())
        finally:
            r.close()

    def test_no_manifest_yet_returns_none(self):
        self.assertIsNone(publisher.read_active_manifest(self.output_dir))


class OfficialMasterThroughPublisherTests(TempNamespaceTestCase):

    def test_official_master_publishes_with_expected_artifact_sha(self):
        result = publisher.publish(MASTER_PATH, self.output_dir)
        self.assertEqual(result.ordinary_sha256, EXPECTED_OFFICIAL_ARTIFACT_SHA)
        self.assertIn(EXPECTED_OFFICIAL_ARTIFACT_SHA, result.generation_basename)


if __name__ == "__main__":
    unittest.main()
