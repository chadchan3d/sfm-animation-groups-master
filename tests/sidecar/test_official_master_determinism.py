"""Phase B2D Part 5: repeated deterministic full official-Master builds --
same-process double-compile, and cross-`PYTHONHASHSEED`-subprocess compiles.
"""

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import official_master_fixture as fx  # noqa: E402


class SameProcessDeterminismTests(unittest.TestCase):

    def test_double_compile_official_master_byte_identical(self):
        from sfm_master_sidecar import writer

        data = fx.load_source_bytes()
        result = fx.core_parse_result()
        blob_a = writer.compile_sidecar(data, result)
        blob_b = writer.compile_sidecar(data, result)
        self.assertEqual(blob_a, blob_b)
        self.assertEqual(blob_a, fx.compiled_artifact_bytes())

    def test_double_compile_with_independent_fresh_parse_byte_identical(self):
        import sfm_master_core as core
        from sfm_master_sidecar import writer

        data = fx.load_source_bytes()
        result_a = core.parse_master_bytes(data, source_name="fresh-a")
        result_b = core.parse_master_bytes(data, source_name="fresh-b")
        blob_a = writer.compile_sidecar(data, result_a)
        blob_b = writer.compile_sidecar(data, result_b)
        self.assertEqual(blob_a, blob_b)


class CrossProcessHashSeedDeterminismTests(unittest.TestCase):
    """Compile the entire official Master in fresh subprocesses under two
    different PYTHONHASHSEED values; SHA-256 must be identical."""

    def _compile_official_master_in_subprocess(self, hash_seed):
        script = (
            "import sys, hashlib\n"
            "sys.path.insert(0, %r)\n"
            "import sfm_master_core as core\n"
            "from tools.sfm_master_sidecar import writer\n"
            "data = open(%r, 'rb').read()\n"
            "result = core.parse_master_bytes(data, source_name='x')\n"
            "blob = writer.compile_sidecar(data, result)\n"
            "sys.stdout.write(hashlib.sha256(blob).hexdigest() + ',' + str(len(blob)))\n"
        ) % (str(REPO_ROOT / "tools"), str(fx.MASTER_PATH))
        import os
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = str(hash_seed)
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sha, length = proc.stdout.strip().split(",")
        return sha, int(length)

    def test_two_different_hash_seeds_produce_identical_official_artifact(self):
        sha0, len0 = self._compile_official_master_in_subprocess(0)
        sha1, len1 = self._compile_official_master_in_subprocess(999983)
        self.assertEqual(len(sha0), 64)
        self.assertEqual(sha0, sha1)
        self.assertEqual(len0, len1)
        self.assertEqual(len0, len(fx.compiled_artifact_bytes()))
        self.assertEqual(sha0, hashlib.sha256(fx.compiled_artifact_bytes()).hexdigest())
        print("\n[B2D determinism] official artifact SHA-256 identical across PYTHONHASHSEED=0 and "
              "PYTHONHASHSEED=999983: %s (%d bytes)" % (sha0, len0))

    def test_no_claim_of_cross_python_version_determinism(self):
        # Documented, not silently assumed: only ONE Python 3 interpreter
        # (this environment's) is actually available to test against --
        # cross-Python-3-minor-version and cross-OS determinism (final spec
        # Section 38's Gate 1A requirement: "at least two distinct Python 3
        # minor-version/OS environments") remain untested and are NOT
        # claimed here.
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
