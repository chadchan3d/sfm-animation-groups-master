"""Phase B2E: public CLI -- check-only, publish, exit-status contract,
outside-repository usability, and source immutability.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TOOLS_DIR))

from sfm_master_sidecar.cli import (  # noqa: E402
    EXIT_COMPILE_FAILED, EXIT_PUBLICATION_FAILED, EXIT_SOURCE_REJECTED, EXIT_SUCCESS, EXIT_USAGE, main,
)

FIXTURES_ROOT = HERE / "fixtures"


def _run_cli(args, cwd=None, env=None):
    """Runs the CLI as a real subprocess (`python -m ...`), exactly the
    documented invocation, not by calling `main()` in-process."""
    full_env = dict(os.environ)
    # `tools` itself (not `tools/sfm_master_sidecar`) must be importable as
    # a namespace package for `python -m tools.sfm_master_sidecar.cli` to
    # resolve -- so PYTHONPATH must contain the REPO ROOT, not `tools/`
    # itself. (Also needs `sfm_master_core.py`, which lives directly under
    # `tools/`, importable via `compiler.py`'s own sys.path insertion.)
    full_env["PYTHONPATH"] = str(REPO_ROOT)
    if env:
        full_env.update(env)
    proc = subprocess.run(
        [sys.executable, "-m", "tools.sfm_master_sidecar.cli"] + args,
        cwd=cwd or str(REPO_ROOT),
        env=full_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc


class ExitStatusContractTests(unittest.TestCase):

    def test_success_check_only(self):
        proc = _run_cli([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"), "--check-only"])
        self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
        self.assertIn("CHECK-ONLY OK", proc.stdout)

    def test_usage_error_missing_source(self):
        proc = _run_cli(["/definitely/does/not/exist.txt", "--check-only"])
        self.assertEqual(proc.returncode, EXIT_USAGE, proc.stderr)

    def test_usage_error_missing_output_for_publish(self):
        proc = _run_cli([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt")])
        self.assertEqual(proc.returncode, EXIT_USAGE, proc.stderr)

    def test_source_rejected_malformed(self):
        proc = _run_cli([str(FIXTURES_ROOT / "malformed" / "unmatched_opening_brace.txt"), "--check-only"])
        self.assertEqual(proc.returncode, EXIT_SOURCE_REJECTED, proc.stderr)

    def test_source_rejected_profile_unsupported(self):
        proc = _run_cli([str(FIXTURES_ROOT / "unsupported" / "empty_document.txt"), "--check-only"])
        self.assertEqual(proc.returncode, EXIT_SOURCE_REJECTED, proc.stderr)

    def test_publish_success(self):
        with tempfile.TemporaryDirectory() as out:
            proc = _run_cli([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"), "--output", out])
            self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
            self.assertIn("PUBLISHED", proc.stdout)
            self.assertTrue((Path(out) / "manifest.json").exists())


class CheckOnlyDoesNotTouchOutputTests(unittest.TestCase):

    def test_check_only_leaves_no_generation_or_manifest_anywhere(self):
        with tempfile.TemporaryDirectory() as out:
            proc = _run_cli([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"), "--check-only", "--output", out])
            self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
            self.assertEqual(list(Path(out).iterdir()), [])


class OutsideRepositoryCliTests(unittest.TestCase):
    """Part 30: invoke with a working directory OUTSIDE the repository,
    explicit absolute source/output paths. Module discovery via PYTHONPATH
    is documented as a separate concern from source/output path
    independence -- the cwd itself must not matter for the OPERATION."""

    def test_cli_succeeds_with_cwd_outside_repository(self):
        outside_cwd = tempfile.mkdtemp(prefix="b2e-outside-cwd-")
        out_dir = tempfile.mkdtemp(prefix="b2e-outside-out-")
        try:
            source_abs = str((FIXTURES_ROOT / "valid" / "06_sibling_groups.txt").resolve())
            proc = _run_cli(
                [source_abs, "--output", out_dir],
                cwd=outside_cwd,  # NOT the repository, NOT a subdirectory of it
            )
            self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
            self.assertTrue((Path(out_dir) / "manifest.json").exists())
        finally:
            shutil.rmtree(outside_cwd, ignore_errors=True)
            shutil.rmtree(out_dir, ignore_errors=True)

    def test_cli_check_only_succeeds_with_cwd_outside_repository(self):
        outside_cwd = tempfile.mkdtemp(prefix="b2e-outside-cwd2-")
        try:
            source_abs = str((FIXTURES_ROOT / "valid" / "06_sibling_groups.txt").resolve())
            proc = _run_cli([source_abs, "--check-only"], cwd=outside_cwd)
            self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
        finally:
            shutil.rmtree(outside_cwd, ignore_errors=True)


class SourceImmutabilityTests(unittest.TestCase):

    def _hash(self, path):
        import hashlib
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def test_check_only_never_modifies_source(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        before = self._hash(src)
        proc = _run_cli([str(src), "--check-only"])
        self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
        self.assertEqual(self._hash(src), before)

    def test_successful_publish_never_modifies_source(self):
        src = FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"
        before = self._hash(src)
        with tempfile.TemporaryDirectory() as out:
            proc = _run_cli([str(src), "--output", out])
            self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
        self.assertEqual(self._hash(src), before)

    def test_failed_publish_never_modifies_source(self):
        src = FIXTURES_ROOT / "malformed" / "unmatched_opening_brace.txt"
        before = self._hash(src)
        with tempfile.TemporaryDirectory() as out:
            proc = _run_cli([str(src), "--output", out])
            self.assertEqual(proc.returncode, EXIT_SOURCE_REJECTED, proc.stderr)
        self.assertEqual(self._hash(src), before)

    def test_official_master_source_unmodified_by_check_only(self):
        official = REPO_ROOT / "sfm_defaultanimationgroups.txt"
        before = self._hash(official)
        proc = _run_cli([str(official), "--check-only"], cwd=str(REPO_ROOT))
        self.assertEqual(proc.returncode, EXIT_SUCCESS, proc.stderr)
        self.assertEqual(self._hash(official), before)


class InProcessMainTests(unittest.TestCase):
    """A few direct `main(argv)` calls (in-process, faster) to exercise the
    exit-code mapping surface without subprocess overhead for every case."""

    def test_main_returns_int(self):
        code = main([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt"), "--check-only"])
        self.assertEqual(code, EXIT_SUCCESS)

    def test_main_usage_missing_output(self):
        code = main([str(FIXTURES_ROOT / "valid" / "06_sibling_groups.txt")])
        self.assertEqual(code, EXIT_USAGE)


if __name__ == "__main__":
    unittest.main()
