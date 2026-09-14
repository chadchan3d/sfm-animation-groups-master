# -*- coding: utf-8 -*-
"""R1 -- QUALIFICATION-ONLY, read-only oracle importer for the REAL Normalizer
and the REAL T120/T130 live-lineage source files. NOT production code. Never
imported by `tools/sfm_master_sidecar/*.py`, never imported by the production
Normalizer itself.

Why this exists: the real `Rebuild_Control_Groups_Normalizer.py` and the real
`SFM_20260910_T130_LiveTrigger20sOrdinaryUseRequalification.py` both import
`sfmApp`/`vs`/`PySide` at module level because they are written to run inside
embedded SFM. Desktop qualification has none of those. Rather than mirror or
re-transcribe the manual/live consumer functions (`parse_targeted_master`,
`master_lookup`, `validate_master_subset_conflicts`, `t120_parse_master`,
`t120_master_lookup`, `t130_t95_master_from_t120`, ...) -- which the R1 brief
explicitly forbids -- this module installs minimal placeholder modules into
`sys.modules` for exactly the three embedded-only dependencies, then imports
the REAL, UNMODIFIED source files by their exact file path. Every function
byte this module hands back to a caller is the real file's own compiled code
object; nothing here re-implements consumer semantics.

Inside real embedded SFM (the Python 2.7 probe, see
`r1_embedded_probe.py`), `sfmApp`/`vs`/`PySide` are the REAL modules already
provided by the host -- this stubbing path is never used there; the real
files are imported directly with no placeholder involved.

The placeholder modules expose only the small surface actually touched at
IMPORT time (module-level attribute access, e.g. class definitions that
reference `QtCore.QObject` as a base class) -- never enough to make any
DME-touching function actually work off-target. Every consumer function this
module exposes for R1 (`parse_targeted_master`, `master_lookup`,
`validate_master_subset_conflicts`, `to_unicode`, `ascii_fold`,
`parse_master_rgba_text`, `parse_master_bool_text`, `ProbeError`,
`t120_parse_master`, `t120_master_lookup`, `t120_ascii_fold`,
`t130_t95_master_from_t120`) was independently verified (by direct source
reading) to depend only on stdlib + pure local helpers -- never on
sfmApp/vs/PySide -- so stubbing those three names is sufficient for these
specific functions to execute exactly as they do in production."""

import importlib.util
import sys
import types


class _StubQObject(object):
    def __init__(self, *a, **kw):
        pass


class _StubMeta(type):
    """Metaclass so CLASS-level attribute access on `_StubAnything` (e.g. a
    real class referencing `QtCore.Qt.DirectConnection` at class-definition
    time) also resolves to a harmless placeholder instead of AttributeError."""
    def __getattr__(cls, item):
        return _StubAnything


class _StubAnything(object, metaclass=_StubMeta):
    """A harmless placeholder usable as a base class (it IS a class, so it
    satisfies Python's class-bases protocol directly), a callable, or an
    attribute target. `import`-time module code in the real Normalizer/T130
    files references many QtCore/QtGui/sfmApp/vs names purely as class
    -definition bases or decorator-style calls; none of the R1 consumer
    functions this module exposes (verified by direct source reading) touch
    any of them at call time."""
    def __init__(self, *a, **kw):
        pass

    def __call__(self, *a, **kw):
        return _StubAnything()

    def __getattr__(self, item):
        return _StubAnything()


class _AutoStubModule(types.ModuleType):
    """A module whose every missing attribute resolves to the harmless
    `_StubAnything` CLASS instead of raising AttributeError -- so
    `import`-time references like `class Foo(QtGui.QDialog):` (a base class
    for embedded-UI code this module never instantiates for real) succeed
    without having to enumerate every Qt/sfmApp/vs symbol by name."""
    def __getattr__(self, item):
        return _StubAnything


def _install_stub(name, attrs=None):
    if name in sys.modules:
        return sys.modules[name]
    mod = _AutoStubModule(name)
    for k, v in (attrs or {}).items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


def install_embedded_stub_modules():
    """Idempotent. Installs the minimal sfmApp/vs/PySide placeholders needed
    for the real Normalizer/T130 files to import successfully on a desktop
    Python. No-op (and harmless) if genuine SFM modules are already present
    (i.e., if this ever ran inside real SFM)."""
    qtcore = _install_stub("PySide.QtCore", {
        "QObject": _StubQObject,
        "QTimer": type("QTimer", (object,), {"singleShot": staticmethod(lambda *a, **kw: None)}),
    })
    qtgui = _install_stub("PySide.QtGui", {"QWidget": _StubQObject})
    pyside = _install_stub("PySide", {"QtCore": qtcore, "QtGui": qtgui})
    sys.modules.setdefault("PySide.QtCore", qtcore)
    sys.modules.setdefault("PySide.QtGui", qtgui)
    _install_stub("sfmApp")
    _install_stub("sfmClipEditor")
    _install_stub("vs")


def _load_module_from_path(module_name, file_path, suppress_trailing_call=None):
    """Reads the exact file bytes and executes them into a fresh module
    namespace. If `suppress_trailing_call` is given and the file's last
    non-blank source line is EXACTLY that bare call (e.g.
    `StartRebuildControlGroups()`), that ONE line is dropped before
    compiling -- these Main-Menu-script files unconditionally invoke their
    own entry point at import time (they are designed to be `exec`'d as a
    script, never imported as a library), which would otherwise run the
    real command against the placeholder sfmApp/vs objects the moment this
    oracle loader imports them. Every other byte of the file, including
    every function/class body, is compiled and executed completely
    unmodified -- this never edits the on-disk file and never changes any
    consumer function's behavior; it only prevents an oracle import from
    accidentally auto-invoking the whole command."""
    install_embedded_stub_modules()
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    if suppress_trailing_call is not None:
        stripped = source.rstrip()
        last_line = stripped.rsplit("\n", 1)[-1].strip()
        if last_line == suppress_trailing_call:
            source = stripped[: -len(last_line)]
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    sys.modules[module_name] = module
    code = compile(source, file_path, "exec")
    exec(code, module.__dict__)
    return module


def load_real_normalizer(normalizer_path):
    """Imports the REAL, unmodified, currently-installed
    `Rebuild_Control_Groups_Normalizer.py` by exact file path (with only its
    own bare top-level `StartRebuildControlGroups()` entry-point call
    suppressed -- see `_load_module_from_path`). Returns the live module
    object -- callers use its real
    `parse_targeted_master`/`master_lookup`/`validate_master_subset_conflicts`/
    `ProbeError`/`to_unicode`/`ascii_fold`/`parse_master_rgba_text`/
    `parse_master_bool_text` directly, as read-only oracles."""
    return _load_module_from_path(
        "_r1_real_normalizer_oracle", normalizer_path,
        suppress_trailing_call="StartRebuildControlGroups()",
    )


def load_real_t130(t130_path):
    """Imports the REAL, unmodified T130 live-lineage source file (which also
    contains the T120 functions it builds on) by exact file path. Returns the
    live module object -- callers use its real
    `t120_parse_master`/`t120_master_lookup`/`t120_ascii_fold`/
    `t120_sha256`/`t130_t95_master_from_t120`/`ProbeError` directly, as
    read-only oracles."""
    return _load_module_from_path(
        "_r1_real_t130_oracle", t130_path, suppress_trailing_call="install_t121()",
    )
