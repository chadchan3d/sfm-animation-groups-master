"""Phase B2B: determinism tests (final spec Section 28).

Normative deterministic identity depends on exactly: source bytes,
format_contract_version, authority_semantics_version -- nothing else.
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sfm_master_core as core  # noqa: E402
from sfm_master_sidecar import writer  # noqa: E402

FIXTURES_ROOT = HERE / "fixtures"
ALL_VALID_ELIGIBLE = [
    "01_minimal_wrapper.txt",
    "06_sibling_groups.txt",
    "13_same_fold_different_destinations.txt",
    "20_non_bmp_text.txt",
    "27_deep_nesting.txt",
    "28_large_alias_family.txt",
]


class SameProcessDeterminismTests(unittest.TestCase):

    def test_double_compile_is_byte_identical(self):
        for name in ALL_VALID_ELIGIBLE:
            with self.subTest(fixture=name):
                data = (FIXTURES_ROOT / "valid" / name).read_bytes()
                result = core.parse_master_bytes(data, source_name=name)
                blob_a = writer.compile_sidecar(data, result)
                blob_b = writer.compile_sidecar(data, result)
                self.assertEqual(blob_a, blob_b)

    def test_double_compile_with_fresh_parse_is_byte_identical(self):
        # re-parsing from scratch each time -- not reusing the same
        # MasterParseResult object -- still must be byte-identical.
        for name in ALL_VALID_ELIGIBLE:
            with self.subTest(fixture=name):
                data = (FIXTURES_ROOT / "valid" / name).read_bytes()
                result_a = core.parse_master_bytes(data, source_name=name)
                result_b = core.parse_master_bytes(data, source_name=name)
                blob_a = writer.compile_sidecar(data, result_a)
                blob_b = writer.compile_sidecar(data, result_b)
                self.assertEqual(blob_a, blob_b)


class CrossProcessHashSeedDeterminismTests(unittest.TestCase):
    """Compile the same fixture in two fresh subprocesses under two
    different PYTHONHASHSEED values; SHA-256 must be identical -- proving
    output bytes never depend on dict/set/hash iteration order."""

    def _compile_in_subprocess(self, fixture_path, hash_seed):
        script = (
            "import sys, hashlib\n"
            "sys.path.insert(0, %r)\n"
            "import sfm_master_core as core\n"
            "from tools.sfm_master_sidecar import writer\n"
            "data = open(%r, 'rb').read()\n"
            "result = core.parse_master_bytes(data, source_name='x')\n"
            "blob = writer.compile_sidecar(data, result)\n"
            "sys.stdout.write(hashlib.sha256(blob).hexdigest())\n"
        ) % (str(REPO_ROOT / "tools"), str(fixture_path))
        import os
        env = dict(**__import__("os").environ)
        env["PYTHONHASHSEED"] = str(hash_seed)
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def test_hash_seed_zero_vs_random_produce_identical_sha256(self):
        fixture = FIXTURES_ROOT / "valid" / "28_large_alias_family.txt"
        digest_seed_0 = self._compile_in_subprocess(fixture, 0)
        digest_seed_other = self._compile_in_subprocess(fixture, 999983)
        self.assertEqual(len(digest_seed_0), 64)
        self.assertEqual(digest_seed_0, digest_seed_other)


if __name__ == "__main__":
    unittest.main()
