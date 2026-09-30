# -*- coding: utf-8 -*-
"""CPM Convergence -- Real-SFM Qualification Session 1 probe (test-only).

A MAINMENU script the operator runs at each Session 1 checkpoint, in the same
SFM process as the converged CPM application (and, for C10, the production
Normalizer). Each run appends one JSON line to
<PUBLIC>/Documents/CPM_Session1_Probe.jsonl and prints a short summary.

Read-only by default. It never constructs a broker: it reads the canonical
runtime only if it is already loaded, and inspects broker state through
public read accessors plus the runtime's own singleton reference. It never
calls a CPM action, writes presets, or touches the scene.

The one deliberate, bounded exception is the timing block. It runs only
when the CPM window is idle (no operation, no Fit, scope present) and after
the lease/provider baseline has already been recorded. It then calls the
app's own prod_cpm_authorize_operation (a bounded expected-generation read
with lease release) 3 times, and opens and releases one adapter stage over
the scope's Body vocabulary 3 times. These are the same read-only
authority calls the product makes; they write nothing.

Probe v3 (CPM R15 Session 1 addendum) adds observation only: the menu
execution dictionary, the private chadchan3d_cpm_app module identity, window
ownership and function-global ownership, a CPM window / watcher / launch-
notice census, the deployed launcher and implementation SHA-256, and process
handle / GDI / USER counts. The v2 timing block is disabled in v3: its
authority calls would confound the addendum's "no authority acquisition
caused merely by reuse" evidence.

One opt-in harness action exists for addendum step 8 (controlled launcher
refusal). Only while the file <PUBLIC>/Documents/CPM_R15_NOTICE_HARNESS.txt
exists, each probe run toggles a hidden, parentless placeholder QDialog in
the CPM window slot: it installs one when the slot is empty and removes its
own placeholder when present. It never touches a CPM window, the broker,
authority or the scene.

Python 2.7 (SFM). Not product code; not part of the shipping layout.
"""
import datetime
import json
import os
import sys
import tempfile
import time

PROBE_VERSION = u"cpm-session1-probe-3"  # 3: R15 observation; timing disabled
CPM_WINDOW_ATTR = "_sfm_character_slider_preset_tool_window"
RUNTIME_MODULE = "sfm_master_authority_productionized.runtime"
R15_MODULE_KEY = "chadchan3d_cpm_app"
R15_NOTICE_ATTR = "_chadchan3d_cpm_launch_notice_v1"
R15_NOTICE_NAME = "chadchan3d_cpm_launch_notice_v1"
R15_HARNESS_NAME = "cpm_r15_notice_harness_placeholder"
R15_MAIN_SENTINELS = ("StartProdTool", "ProdWindow", "prod_cpm_open_adapter", "prod_scope", "log_line",
                      "PROD_RUN_ID", "PROD_OUTPUT_PATH", "_chadchan3d_cpm_launcher_v1")
TIMING_ENABLED = False  # v3: observation only (see module docstring)


def _report_path():
    public = os.environ.get("PUBLIC") or tempfile.gettempdir()
    folder = os.path.join(public, "Documents")
    if not os.path.isdir(folder):
        folder = public
    return os.path.join(folder, "CPM_Session1_Probe.jsonl")


def _text(value):
    try:
        return unicode(value)  # noqa: F821
    except Exception:
        return repr(value)


def _deep_size(obj, seen=None):
    """Recursive sys.getsizeof over plain containers (logical estimate of a
    detached Python structure; not native/VAS memory)."""
    if seen is None:
        seen = set()
    marker = id(obj)
    if marker in seen:
        return 0
    seen.add(marker)
    size = sys.getsizeof(obj, 0)
    if isinstance(obj, dict):
        for k, v in obj.items():
            size += _deep_size(k, seen) + _deep_size(v, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for v in obj:
            size += _deep_size(v, seen)
    return size


def _process_memory():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        # Private library instances: ctypes.windll.* function objects are
        # process-shared, and another in-process consumer (the CPM app) sets
        # its own argtypes on GetProcessMemoryInfo. A private WinDLL has its
        # own prototypes, so this neither depends on nor alters theirs.
        kernel32 = ctypes.WinDLL("kernel32")
        psapi = ctypes.WinDLL("psapi")
        kernel32.GetCurrentProcess.argtypes = []
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = PMC()
        counters.cb = ctypes.sizeof(PMC)
        handle = kernel32.GetCurrentProcess()
        ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
        if not ok:
            return {"error": u"GetProcessMemoryInfo failed"}
        out = {
            "working_set": int(counters.WorkingSetSize),
            "peak_working_set": int(counters.PeakWorkingSetSize),
            "private_usage": int(counters.PrivateUsage),
            "peak_pagefile_usage": int(counters.PeakPagefileUsage),
        }
        try:
            user32 = ctypes.WinDLL("user32")
            kernel32.GetProcessHandleCount.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
            kernel32.GetProcessHandleCount.restype = wintypes.BOOL
            user32.GetGuiResources.argtypes = [ctypes.c_void_p, wintypes.DWORD]
            user32.GetGuiResources.restype = wintypes.DWORD
            count = wintypes.DWORD(0)
            if kernel32.GetProcessHandleCount(handle, ctypes.byref(count)):
                out["handles"] = int(count.value)
            out["gdi_objects"] = int(user32.GetGuiResources(handle, 0))
            out["user_objects"] = int(user32.GetGuiResources(handle, 1))
        except Exception as exc:
            out["os_counters_error"] = _text(exc)
        return out
    except Exception as exc:
        return {"error": _text(exc)}


def _broker_state():
    runtime = sys.modules.get(RUNTIME_MODULE)
    if runtime is None:
        return {"runtime_loaded": False}
    out = {
        "runtime_loaded": True,
        "runtime_file": _text(getattr(runtime, "__file__", None)),
        "api": _text(getattr(runtime, "RUNTIME_API_VERSION", None)),
        "build": _text(getattr(runtime, "RUNTIME_BUILD_ID", None)),
        "is_canonical": bool(runtime.is_canonical()),
        "state": _text(runtime.get_state()),
    }
    broker = getattr(runtime, "_broker", None)  # the runtime's own singleton; never constructed here
    out["broker_constructed"] = broker is not None
    if broker is None:
        return out
    out["broker_id"] = u"0x%x" % id(broker)
    out["outstanding_leases"] = int(broker.outstanding_lease_count())
    out["unreleased_lease_registry"] = int(broker.unreleased_lease_count())
    out["provider_counters"] = dict((k, v) for k, v in broker.provider_counters().items())
    out["view_cache_entries"] = int(broker.view_cache_entry_count())
    views = []
    try:
        for view in broker._view_cache.all_views():
            views.append({
                "consumer_kind": _text(view.consumer_kind),
                "master_sha256_prefix": _text(view.semantic_generation.master_sha256)[:12],
                "covered_keys": len(view.coverage.covered_keys()),
                "estimated_bytes": int(view.estimated_bytes or 0),
                "live_leases": int(view.live_lease_count()),
                "stale": bool(view.is_stale()),
            })
    except Exception as exc:
        views = [{"error": _text(exc)}]
    out["views"] = views
    out["consumer_kinds"] = sorted(set(v.get("consumer_kind") for v in views if "consumer_kind" in v))
    # Consumers this broker served, from its own diagnostics history (survives
    # cache eviction): cohort_acquired lists views; full reuse lists consumers.
    served = set()
    try:
        for entry in broker.recent_diagnostics():
            detail = entry.get("detail") or {}
            for key in ("views", "consumers"):
                for kind in (detail.get(key) or []) if isinstance(detail, dict) else []:
                    served.add(_text(kind))
    except Exception as exc:
        served.add(u"error:" + _text(exc))
    out["consumers_served"] = sorted(served)
    try:
        out["ledger"] = broker.ledger_snapshot()
    except Exception as exc:
        out["ledger"] = {"error": _text(exc)}
    return out


def _cpm_window():
    try:
        from PySide import QtGui
    except Exception:
        return None
    app = QtGui.QApplication.instance()
    if app is None:
        return None
    return getattr(app, CPM_WINDOW_ATTR, None)


def _cpm_state(window):
    if window is None:
        return {"window": False}
    try:
        g = window.render.__func__.__globals__
    except Exception:
        g = {}
    scope = getattr(window, "scope", None)
    out = {
        "window": True,
        "converged_app": "prod_cpm_open_adapter" in g and "prod_cpm_authorize_operation" in g
                         and "prod_cpm_open_fit_stage" in g,
        "prod_version": _text(g.get("PROD_VERSION")),
        "historical_provider_open": g.get("_SEMANTIC_PROVIDER") is not None,
        "historical_provider_open_count": g.get("_SEMANTIC_PROVIDER_OPEN_COUNT"),
        "identity": _text(getattr(window, "identity", None)),
        "operation_active": getattr(window, "operation", None) is not None,
        "fit_active": bool(getattr(window, "fit_active", False)),
        "fit_generation": getattr(window, "fit_generation", None),
        "fit_semantic_generation_prefix": _text(getattr(window, "fit_semantic_generation", None))[:12],
        "fit_authority_context_present": getattr(window, "fit_authority_context", None) is not None,
        "provider_health": _text((getattr(window, "provider_health", None) or {}).get("status")),
        "scope_present": isinstance(scope, dict),
    }
    if isinstance(scope, dict):
        out["scope_generation_prefix"] = _text((scope.get("authority") or {}).get("provider_sha256"))[:12]
        out["scope_counts"] = dict((scope.get("semantic") or {}).get("counts") or {})
        out["scope_expression"] = len(scope.get("expression") or {})
        out["scope_body"] = len(scope.get("body") or {})
        out["scope_unresolved"] = len(scope.get("unresolved") or [])
        out["scope_conflicts"] = len(scope.get("conflicts") or [])
        out["scope_overrides"] = len(scope.get("overrides") or {})
        out["scope_deep_bytes"] = _deep_size(scope)
        out["scope_provider_kind"] = _text((scope.get("provider_descriptor") or {}).get("provider_kind"))
    modules = {}
    for name in ("cpm_authority_adapter", "cpm_compat_v1_projection"):
        mod = sys.modules.get(name)
        modules[name] = _text(getattr(mod, "__file__", None)) if mod is not None else None
    out["cpm_modules"] = modules
    return out, g


def _file_sha256(path):
    try:
        import hashlib
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as exc:
        return u"unreadable: " + _text(exc)


def _qt_alive(obj):
    try:
        from PySide import shiboken
        return bool(shiboken.isValid(obj))
    except Exception:
        return None


def _r15_state(window):
    """Observation only: host dictionary, private module, window ownership,
    CPM object census, deployed hashes."""
    main = sys.modules.get("__main__")
    main_dict = getattr(main, "__dict__", {})
    out = {
        "probe_globals_is_main_dict": globals() is main_dict,
        "probe_name": _text(globals().get("__name__")),
        "main_dict_id": u"0x%x" % id(main_dict),
        "main_dict_size": len(main_dict),
        "cpm_names_in_main": sorted(n for n in R15_MAIN_SENTINELS if n in main_dict),
    }
    game_root = os.path.dirname(os.path.abspath(sys.executable))
    launcher_path = os.path.join(game_root, "usermod", "scripts", "sfm", "mainmenu", "ChadChan3D",
                                 "SFM_Character_Preset_Manager.py")
    impl_path = os.path.normpath(os.path.abspath(os.path.join(game_root, "usermod", "scripts", "ChadChan3D_CPM",
                                                              "SFM_Character_Preset_Manager.py")))
    out["deployed_launcher_sha256"] = _file_sha256(launcher_path)
    out["deployed_impl_sha256"] = _file_sha256(impl_path)
    module = sys.modules.get(R15_MODULE_KEY)
    ns = getattr(module, "__dict__", {}) if module is not None else {}
    out["module"] = {
        "present": module is not None,
        "type": _text(type(module).__name__),
        "id": (u"0x%x" % id(module)) if module is not None else None,
        "name": _text(ns.get("__name__")),
        "file": _text(ns.get("__file__")),
        "file_is_deterministic_impl_path": ns.get("__file__") == impl_path,
        "loader": _text(ns.get("__chadchan3d_cpm_loader__")),
        "build_sha256": _text(ns.get("__chadchan3d_cpm_build_sha256__")),
        "state": _text(ns.get("__chadchan3d_cpm_state__")),
        "run_id": _text(ns.get("PROD_RUN_ID")),
        "output_path": _text(ns.get("OUTPUT_PATH")),
        "startup_state": _text((ns.get("PROD_R15_STARTUP") or {}).get("state")),
        "prodwindow_class_id": (u"0x%x" % id(ns["ProdWindow"])) if "ProdWindow" in ns else None,
        "startprodtool_id": (u"0x%x" % id(ns["StartProdTool"])) if "StartProdTool" in ns else None,
        "historical_provider_open_count": ns.get("_SEMANTIC_PROVIDER_OPEN_COUNT"),
    }
    cls = ns.get("ProdWindow")
    win = {"slot_occupied": window is not None}
    if window is not None:
        try:
            g = window.render.__func__.__globals__
        except Exception:
            g = None
        try:
            object_name = _text(window.objectName())
        except Exception:
            object_name = None
        win.update({
            "id": u"0x%x" % id(window),
            "class_module": _text(type(window).__module__),
            "owned_by_private_module": bool(cls is not None and isinstance(window, cls)),
            "alive": _qt_alive(window),
            "harness_placeholder": object_name == R15_HARNESS_NAME,
            "function_globals_is_private_module": bool(g is not None and g is ns),
            "function_globals_is_main_dict": bool(g is not None and g is main_dict),
            "function_globals_name": _text((g or {}).get("__name__")),
        })
        for attr in ("closing_requested", "modal_yield_active"):
            win[attr] = getattr(window, attr, None)
        try:
            win["visible"] = bool(window.isVisible())
            timer = getattr(window, "modal_watch_timer", None)
            win["watcher_active"] = bool(timer.isActive()) if timer is not None else None
        except Exception as exc:
            win["qt_error"] = _text(exc)
    out["window"] = win
    census = {}
    try:
        from PySide import QtGui
        app = QtGui.QApplication.instance()
        tops = list(app.topLevelWidgets()) if app is not None else []
        prod = [w for w in tops if type(w).__name__ == "ProdWindow"]
        census["prodwindow_toplevel_total"] = len(prod)
        census["prodwindow_toplevel_owned"] = len([w for w in prod if cls is not None and isinstance(w, cls)])
        census["prodwindow_toplevel_visible"] = len([w for w in prod if w.isVisible()])
        census["active_watchers"] = len([w for w in prod if getattr(w, "modal_watch_timer", None) is not None
                                         and w.modal_watch_timer.isActive()])
        notices = [w for w in tops if isinstance(w, QtGui.QMessageBox) and w.objectName() == R15_NOTICE_NAME]
        census["launch_notices"] = len(notices)
        census["launch_notices_visible"] = len([w for w in notices if w.isVisible()])
        slot = getattr(app, R15_NOTICE_ATTR, None) if app is not None else None
        if slot is None:
            census["notice_slot"] = None
        else:
            census["notice_slot"] = {"type": _text(type(slot).__name__)}
            try:
                census["notice_slot"].update({"object_name": _text(slot.objectName()), "modal": bool(slot.isModal()),
                                              "visible": bool(slot.isVisible())})
            except Exception as exc:
                census["notice_slot"]["error"] = _text(exc)
        modal = app.activeModalWidget() if app is not None else None
        census["active_modal"] = _text(type(modal).__name__) if modal is not None else None
    except Exception as exc:
        census["error"] = _text(exc)
    out["census"] = census
    return out


def _harness_flag_path():
    return os.path.join(os.path.dirname(_report_path()), "CPM_R15_NOTICE_HARNESS.txt")


def _notice_harness():
    """Addendum step 8 only (opt-in by flag file). Toggles a hidden, parentless
    placeholder in the CPM window slot; never touches a CPM window."""
    if not os.path.isfile(_harness_flag_path()):
        return {"enabled": False}
    try:
        from PySide import QtGui
        app = QtGui.QApplication.instance()
        current = getattr(app, CPM_WINDOW_ATTR, None)
        if current is None:
            placeholder = QtGui.QDialog()
            placeholder.setObjectName(R15_HARNESS_NAME)
            setattr(app, CPM_WINDOW_ATTR, placeholder)
            return {"enabled": True, "action": u"installed-placeholder"}
        if isinstance(current, QtGui.QDialog) and current.objectName() == R15_HARNESS_NAME:
            setattr(app, CPM_WINDOW_ATTR, None)
            current.deleteLater()
            return {"enabled": True, "action": u"removed-placeholder"}
        return {"enabled": True, "action": u"none: CPM window slot occupied; close CPM first"}
    except Exception as exc:
        return {"enabled": True, "action": u"error", "error": _text(exc)}


def _timing(window, g):
    if not TIMING_ENABLED:
        return {"skipped": u"disabled in probe v3 (R15 addendum: observation only)"}
    scope = getattr(window, "scope", None)
    if (window is None or not isinstance(scope, dict) or getattr(window, "operation", None) is not None
            or getattr(window, "fit_active", False) or "prod_cpm_authorize_operation" not in g):
        return {"skipped": u"CPM not idle with a scope"}
    identity = dict(window.identity)
    out = {"authorize_seconds": [], "stage_open_release_seconds": []}
    for _ in range(3):
        started = time.time()
        g["prod_cpm_authorize_operation"](identity, scope, None, u"session1-probe")
        out["authorize_seconds"].append(round(time.time() - started, 6))
    literals = sorted((scope.get("body") or {}).keys())
    expected = (scope.get("authority") or {}).get("provider_sha256")
    for _ in range(3):
        started = time.time()
        stage = g["prod_cpm_open_adapter"]().open_stage(expected, literals)
        stage.release()
        out["stage_open_release_seconds"].append(round(time.time() - started, 6))
    out["stage_literals"] = len(literals)
    return out


def run():
    record = {
        "probe": PROBE_VERSION,
        "at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "python": _text(sys.version.split()[0]),
        "memory_before": _process_memory(),
        "broker_before": _broker_state(),
    }
    window = _cpm_window()
    state = _cpm_state(window)
    if isinstance(state, tuple):
        record["cpm"], g = state
    else:
        record["cpm"], g = state, {}
    try:
        record["timing"] = _timing(window, g)
    except Exception as exc:
        record["timing"] = {"error": _text(exc)}
    record["broker_after_timing"] = _broker_state()
    try:
        record["r15"] = _r15_state(window)
    except Exception as exc:
        record["r15"] = {"error": _text(exc)}
    record["r15_harness"] = _notice_harness()
    record["memory_after"] = _process_memory()
    path = _report_path()
    try:
        seq = 1
        if os.path.isfile(path):
            with open(path, "rb") as f:
                seq = sum(1 for _ in f) + 1
        record["seq"] = seq
        with open(path, "ab") as f:
            f.write((json.dumps(record, sort_keys=True, default=_text) + "\n").encode("utf-8"))
    except Exception as exc:
        record["write_error"] = _text(exc)
    b = record["broker_before"]
    c = record["cpm"]
    print("CPM_SESSION1_PROBE seq=%s broker=%s leases=%s open_providers=%s views=%s kinds=%s "
          "cpm_window=%s converged=%s scope=%s historical_open=%s report=%s"
          % (record.get("seq"), b.get("broker_id"), b.get("outstanding_leases"),
             (b.get("provider_counters") or {}).get("current_open_provider_count"), b.get("view_cache_entries"),
             b.get("consumer_kinds"), c.get("window"), c.get("converged_app"), c.get("scope_present"),
             c.get("historical_provider_open"), path))
    r = record.get("r15") or {}
    rm, rw, rc = r.get("module") or {}, r.get("window") or {}, r.get("census") or {}
    print("CPM_R15_PROBE module_state=%s module_id=%s window_owned=%s globals_private=%s cpm_names_in_main=%s "
          "prodwindows=%s watchers=%s notices=%s harness=%s"
          % (rm.get("state"), rm.get("id"), rw.get("owned_by_private_module"),
             rw.get("function_globals_is_private_module"), r.get("cpm_names_in_main"),
             rc.get("prodwindow_toplevel_total"), rc.get("active_watchers"), rc.get("launch_notices"),
             (record.get("r15_harness") or {}).get("action")))
    return record


run()
