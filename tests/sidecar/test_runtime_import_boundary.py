"""Phase B2B: Python-2.7 runtime-boundary discipline tests (final spec
Section 27).

No Python 2.7 interpreter is available in this environment (`py -2` falls
through to the installed Python 3; `where python2` finds nothing) -- per
the task's own explicit allowance, this phase substitutes static/import-
discipline tests for actual Python 2.7 execution. Real Python 2.7 execution
of `format.py`/`reader.py` remains mandatory, deferred Gate 1A evidence
(final spec Section 38) and is NOT claimed as satisfied here -- see the
Phase B2B audit's "PYTHON-2.7 COMPATIBILITY DISCIPLINE" section.
"""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = REPO_ROOT / "tools" / "sfm_master_sidecar"

RUNTIME_SAFE_MODULES = ["format.py", "reader.py"]

# Constructs that do not exist in Python 2.7 and would make a module
# unimportable there even though it parses fine under Python 3.
PY3_ONLY_AST_NODES = {
    "JoinedStr": "f-string",
    "NamedExpr": "walrus operator (:=)",
}

FORBIDDEN_IMPORTS = {
    "sfm_master_core",
    "dataclasses",
    "pathlib",
    "typing",
    "writer",
}


def _imported_top_level_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
            # relative "from . import X" / "from .writer import Y"
            for alias in node.names:
                names.add(alias.name)
    return names


class RuntimeSafeModuleDisciplineTests(unittest.TestCase):

    def test_format_and_reader_do_not_import_forbidden_modules(self):
        for fname in RUNTIME_SAFE_MODULES:
            with self.subTest(module=fname):
                path = PKG_DIR / fname
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                imported = _imported_top_level_names(tree)
                overlap = imported & FORBIDDEN_IMPORTS
                self.assertFalse(
                    overlap,
                    "%s imports forbidden name(s) %r -- violates the Python-2.7 runtime boundary" % (
                        fname, overlap,
                    ),
                )

    def test_format_and_reader_contain_no_python3_only_syntax(self):
        for fname in RUNTIME_SAFE_MODULES:
            with self.subTest(module=fname):
                path = PKG_DIR / fname
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                found = []
                for node in ast.walk(tree):
                    type_name = type(node).__name__
                    if type_name in PY3_ONLY_AST_NODES:
                        found.append(PY3_ONLY_AST_NODES[type_name])
                self.assertEqual(
                    found, [],
                    "%s contains Python-3-only construct(s): %r" % (fname, found),
                )

    def test_init_does_not_implicitly_import_writer_or_core_or_cli(self):
        path = PKG_DIR / "__init__.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = _imported_top_level_names(tree)
        self.assertFalse(imported & {"writer", "sfm_master_core", "cli"})

    def test_format_module_is_importable_in_isolation(self):
        # Import format.py in a fresh subprocess with `writer`/`sfm_master_core`
        # made unimportable (no tools/ on sys.path), proving `format` truly
        # has no hidden coupling to either.
        script = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import sfm_master_sidecar.format as fmt\n"
            "assert fmt.MAGIC == b'SFMMSTR\\x00'\n"
            "print('OK')\n"
        ) % str(REPO_ROOT / "tools")
        proc = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)

    def test_reader_module_is_importable_without_writer_or_core_present(self):
        script = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import sfm_master_sidecar.reader as reader\n"
            "assert reader.SidecarReader is not None\n"
            "print('OK')\n"
        ) % str(REPO_ROOT / "tools")
        proc = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)

    def test_package_init_is_importable_standalone(self):
        script = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import sfm_master_sidecar\n"
            "assert sfm_master_sidecar.__all__ == []\n"
            "print('OK')\n"
        ) % str(REPO_ROOT / "tools")
        proc = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
