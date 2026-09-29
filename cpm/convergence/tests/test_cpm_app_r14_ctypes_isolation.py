# -*- coding: utf-8 -*-
"""R14 -- CPM diagnostic ctypes isolation (offline qualification).

Real-SFM Session 1 showed that CPM's prod_resource_snapshot() sets
argtypes/restype on function objects reached through the process-shared
ctypes.windll, after which the production Normalizer's own
GetProcessMemoryInfo telemetry fails (mem_ok=False).

This suite runs, in one process on Windows under embedded Python 2.7.5 and
desktop Python 3.10:
  * the corrected application prod_resource_snapshot (verbatim extraction);
  * the frozen G18AN baseline prod_resource_snapshot (pre-fix reproduction);
  * the production Normalizer's contextualizer_process_memory_sample and its
    own _ProcessMemoryCountersEx (verbatim extraction from the pinned
    snapshot) as the second in-process consumer.

Only interpreter-independent verdicts go into the digest. Real SFM still
has to confirm Normalizer mem_ok=True with CPM open (Session 1 completion).
"""
import ast
import ctypes
import hashlib
import io
import json
import os
import re
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import test_cpm_app_canonical_route as route  # noqa: E402

PY2 = route.PY2
_TEXT = route._TEXT
check = route.check
RESULTS = route.RESULTS

NORMALIZER_PATH = route.base.NORMALIZER_PATH
NORMALIZER_SHA256 = route.base.NORMALIZER_SHA256
FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_r14_ctypes_isolation")
DIGEST_PY3 = os.path.join(FIXTURE_ROOT, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_ROOT, "digest_py27.json")

SHARED_FUNCTIONS = (("kernel32", "GetCurrentProcess"), ("psapi", "GetProcessMemoryInfo"),
                    ("kernel32", "GetProcessHandleCount"), ("user32", "GetGuiResources"))
# The Normalizer's own sample makes un-prototyped ctypes calls, which are
# valid only in a 32-bit process (SFM and embedded Python 2.7.5 are 32-bit).
# On a 64-bit interpreter the second-consumer checks are not applicable.
ARCH32 = ctypes.sizeof(ctypes.c_void_p) == 4
FIELDS = ("working_set_mb", "private_commit_mb", "pagefile_commit_mb", "handles", "gdi", "user")


class _QtGui(object):
    class QApplication(object):
        @staticmethod
        def instance():
            return None

    class QDialog(object):
        pass


def _text(value):
    try:
        return unicode(value)  # noqa: F821
    except NameError:
        return str(value)


def _snapshot_namespace(source, log):
    ns = {"ctypes": ctypes, "u": _text, "log_line": log.append, "QtGui": _QtGui}
    names = ["PROD_PROCESS_MEMORY_COUNTERS_EX", "prod_resource_snapshot"]
    if "prod_private_windll" in source.top:
        names = ["PROD_PROCESS_MEMORY_COUNTERS_EX", "_PROD_PRIVATE_WINDLL", "prod_private_windll", "prod_resource_snapshot"]
    for name in names:
        route._run_source(source.top_text(name), "extract:%s" % name, ns)
    return ns


def _shared_state():
    out = []
    for dll, fn in SHARED_FUNCTIONS:
        f = getattr(getattr(ctypes.windll, dll), fn)
        out.append((dll, fn, id(f), f.argtypes, f.restype))
    return out


def _restore(state):
    for dll, fn, _, argtypes, restype in state:
        f = getattr(getattr(ctypes.windll, dll), fn)
        f.argtypes = argtypes
        f.restype = restype


def _fields(line):
    values = dict(re.findall(r"(\w+)=(\S+)", line))
    return dict((k, values.get(k)) for k in FIELDS)


def _numeric(fields):
    try:
        return all(v not in (None, "None") and float(v) >= 0 for v in fields.values())
    except ValueError:
        return False


def run_suite():
    app = route.AppSource(route.APP_PATH)
    baseline = route.AppSource(route.BASELINE_PATH)
    with open(route.BASELINE_PATH, "rb") as f:
        check("r14.baseline_byte_identical", hashlib.sha256(f.read()).hexdigest() == route.BASELINE_SHA256)
    normalizer = route.AppSource(NORMALIZER_PATH)
    check("r14.normalizer_pinned", hashlib.sha256(normalizer.raw).hexdigest() == NORMALIZER_SHA256)
    norm_ns = {"ctypes": ctypes}
    for name in ("_ProcessMemoryCountersEx", "contextualizer_process_memory_sample"):
        route._run_source(normalizer.top_text(name), "normalizer:%s" % name, norm_ns)
    normalizer_sample = norm_ns["contextualizer_process_memory_sample"]

    original = _shared_state()
    if not ARCH32:
        check("r14.second_consumer_checks_not_applicable_on_64bit", True,
              u"Normalizer sample is 32-bit-only; covered by the embedded 2.7.5 (32-bit) run")
        normalizer_sample = None
    consumer = (lambda: normalizer_sample()["ok"]) if ARCH32 else (lambda: None)
    if ARCH32:
        check("r14.second_consumer_ok_initially", consumer() is True)

    # Corrected application: fields intact, shared prototypes untouched.
    log = []
    fixed = _snapshot_namespace(app, log)
    fixed["prod_resource_snapshot"](u"r14-fixed-1")
    fixed["prod_resource_snapshot"](u"r14-fixed-2")
    lines = [l for l in log if l.startswith("PROD_RESOURCE ")]
    check("r14.fixed_logs_all_fields", len(lines) == 2 and all(_numeric(_fields(l)) for l in lines),
          None if lines and _numeric(_fields(lines[0])) else [_fields(l) for l in lines])
    check("r14.fixed_no_native_unavailable", not [l for l in log if "PROD_RESOURCE_NATIVE_UNAVAILABLE" in l], log)
    after_fixed = _shared_state()
    check("r14.fixed_shared_prototypes_untouched",
          [(s[0], s[1], s[3], s[4]) for s in after_fixed] == [(s[0], s[1], s[3], s[4]) for s in original])
    if ARCH32:
        check("r14.fixed_second_consumer_ok", consumer() is True)
    private = fixed["prod_private_windll"]
    check("r14.private_handles_cached_and_distinct", private("psapi") is private("psapi")
          and private("psapi") is not ctypes.windll.psapi
          and private("psapi").GetProcessMemoryInfo is not ctypes.windll.psapi.GetProcessMemoryInfo)

    # Pre-fix baseline: the reproduced collision.
    blog = []
    frozen = _snapshot_namespace(baseline, blog)
    try:
        frozen["prod_resource_snapshot"](u"r14-baseline")
        blines = [l for l in blog if l.startswith("PROD_RESOURCE ")]
        check("r14.baseline_logs_same_fields", len(blines) == 1 and set(_fields(blines[0])) == set(FIELDS)
              and _numeric(_fields(blines[0])))
        mutated = _shared_state()
        check("r14.baseline_mutates_shared_prototypes",
              [(s[3], s[4]) for s in mutated] != [(s[3], s[4]) for s in original])
        if ARCH32:
            sample = normalizer_sample()
            check("r14.baseline_breaks_second_consumer", sample["ok"] is False and sample["working_set"] is None)
        # The corrected app still works while the shared prototypes are polluted.
        log2 = []
        fixed2 = _snapshot_namespace(app, log2)
        fixed2["prod_resource_snapshot"](u"r14-fixed-under-pollution")
        check("r14.fixed_independent_of_shared_prototypes",
              _numeric(_fields([l for l in log2 if l.startswith("PROD_RESOURCE ")][0])))
    finally:
        _restore(original)
    if ARCH32:
        check("r14.second_consumer_ok_after_restore", consumer() is True)
    fixed["prod_resource_snapshot"](u"r14-fixed-3")
    check("r14.fixed_again_untouched", [(s[3], s[4]) for s in _shared_state()] == [(s[3], s[4]) for s in original]
          and consumer() in (True, None))

    # No authority/lease/provider/scene/persistence involvement.
    forbidden = set(["get_semantic_provider", "prod_scope", "prod_cpm_open_adapter", "prod_cpm_authorize_operation",
                     "p02_safe_write_json", "sfmApp", "vs", "gc", "same_time_refresh", "prod_resolve"])
    for name in ("prod_private_windll", "prod_resource_snapshot"):
        node = app.top[name][2]
        used = set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
        attrs = set(n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute))
        bad = (used | attrs) & forbidden | set(a for a in attrs if "lease" in a.lower() or "broker" in a.lower())
        check("r14.%s_touches_no_authority_scene_or_persistence" % name, not bad, sorted(bad))
    check("r14.no_authority_runtime_loaded", "sfm_master_authority_productionized.runtime" not in sys.modules)
    diff = [n for n in app.top if n in baseline.top and app.top_text(n) != baseline.top_text(n)
            and n not in (route.EXPECTED_CHANGED_TOP - route.R14_CHANGED_TOP)]
    check("r14.only_prod_resource_snapshot_changed_beyond_convergence", diff == ["prod_resource_snapshot"], diff)


def main():
    phase = None
    for arg in sys.argv[1:]:
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1]
    # No cross-interpreter digest comparison: the check set legitimately
    # differs between the 32-bit (2.7.5) and 64-bit (3.10) runs.
    if phase not in ("run",):
        print("usage: %s --phase=run" % os.path.basename(sys.argv[0]))
        sys.exit(2)
    print("Interpreter: %s" % sys.version.split()[0])
    if not os.path.isdir(FIXTURE_ROOT):
        os.makedirs(FIXTURE_ROOT)
    print("Architecture: %d-bit" % (32 if ARCH32 else 64))
    run_suite()
    route.write_digest(DIGEST_PY27 if PY2 else DIGEST_PY3)
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
