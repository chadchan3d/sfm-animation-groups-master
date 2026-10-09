# -*- coding: ascii -*-
# K -- integrated CPM/Normalizer product workflow qualification probe.
#
# QUALIFICATION-ONLY. Not product code. Deployed temporarily to the ChadChan3D
# Scripts menu for one K attempt and removed at closeout
# (cpm/qualification/K_INTEGRATED_PRODUCT_WORKFLOW_QUALIFICATION_DESIGN.md).
# Derived from the item-8 probe by a declared delta list (test_cpm_k_tooling.py):
# K pins and attempt root, a read-only broker-diagnostics tail, a free-VAS
# sample and a census of the Normalizer's shared-__main__ names. No other mode.
#
# OBSERVATION ONLY. One menu click appends one JSON record to the active
# attempt's probe.jsonl and writes one write-once scene snapshot file for the
# explicit fixture animation sets present in the current shot. It:
#   - inspects already-loaded modules only; it never constructs a broker,
#     authorizes an operation, opens an adapter/provider/view/stage, evaluates
#     semantic readiness or calls G18AN_POST_FIT_ACTION_STATE's helper;
#   - calls only read accessors (broker counters/ledger/view-cache listing,
#     runtime identity, Qt widget census) and CPM's own pure scene readers
#     (p03_model_animsets, p01_all_supported_flex_bindings, binding_snapshot,
#     dm().GetUndo*) for the explicit fixture animation sets;
#   - installs no wrapper, timer, callback, dialog or hook, sets no attribute
#     on any CPM, Qt or authority object, writes no CPM log line and retains no
#     DME or Qt object after it returns (all names are function locals; the one
#     function name is removed from the shared namespace afterwards);
#   - writes only campaign evidence, under the attempt named by
#     %PUBLIC%\Documents\CPM_K\ACTIVE_ATTEMPT.txt;
#   - records every observation failure explicitly, never as zero/success.
#
# (Comments, not a docstring: a module docstring would rebind __doc__ in SFM's
# shared Scripts-menu namespace.)
#
# Python 2.7 (SFM); also importable under Python 3 for offline qualification.


def _cpm_k_probe_v1():
    import datetime
    import hashlib
    import json
    import os
    import re
    import sys
    import time

    PROBE_VERSION = "cpm-k-probe-1"
    SCHEMA = "cpm-k-probe-record-v1"
    SNAPSHOT_SCHEMA = "cpm-k-scene-snapshot-v1"
    CANDIDATE_APP_SHA256 = "4e35f29242351317f2f961c27e19d66fcd3355cff964b081431fc2fff1f5b9d7"
    LAUNCHER_SHA256 = "996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51"
    MODULE_KEY = "chadchan3d_cpm_app"
    LOADER = "cpm-private-loader-v1"
    WINDOW_ATTR = "_sfm_character_slider_preset_tool_window"
    RUNTIME = "sfm_master_authority_productionized.runtime"
    POINTER = "ACTIVE_ATTEMPT.txt"
    ATTEMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
    HISTORICAL = ("_SEMANTIC_PROVIDER_OPEN_COUNT", "_SEMANTIC_PROVIDER_REUSE_COUNT",
                  "_SEMANTIC_PROVIDER_INVALIDATION_COUNT", "_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT",
                  "_SEMANTIC_PROVIDER_GENERATION")
    # Explicit fixture animation sets (K_FIXTURE_MANIFEST.json); nothing else is snapshotted.
    FIXTURES = (
        ("krystal20201", "models/fursonas/starfox/krystal/bodies/krystal2020.mdl", -1441261258),
        ("assaultsuitbody1", "models/fursonas/starfox/krystal/cosmetics/assaultsuitbody.mdl", -791536511),
        ("loinclothbra_chadfix_071", "models/fursonas/starfox/krystal/cosmetics/loinclothbra_chadfix_07.mdl",
         480892851),
        ("mia1", "models/annoad/foxbase/mia/mia.mdl", 1153028609),
    )
    SIDE_KEYS = ("source", "destination", "evaluated", "key_count", "key0_time", "key0_value", "is_empty")
    MAIN_SENTINELS = ("StartProdTool", "ProdWindow", "prod_cpm_open_adapter", "prod_scope", "log_line",
                      "PROD_RUN_ID", "PROD_OUTPUT_PATH", "_chadchan3d_cpm_launcher_v1")
    # The production Normalizer runs in SFM's shared __main__ (carried K/L note): recorded, never touched.
    NORMALIZER_MAIN_SENTINELS = ("StartRebuildControlGroups", "RebuildControlGroupsProductionRun", "RebuildScopeDialog",
                                 "OUTPUT_PATH", "PRODUCTION_REVISION", "SCOPE_SELECTED", "SCOPE_ALL")
    DIAGNOSTICS_TAIL = 16

    errors = {}

    def text(value):
        try:
            return unicode(value)  # noqa: F821
        except NameError:
            return str(value)
        except Exception:
            return repr(value)

    def hexid(obj):
        return "0x%x" % id(obj)

    def plain(value):
        """Only JSON-native scalars leave the probe; anything else becomes text."""
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value
        try:
            if isinstance(value, long):  # noqa: F821
                return int(value)
        except NameError:
            pass
        return text(value)

    def fail(section, exc):
        errors[section] = text(exc)
        return {"observed": False, "error": text(exc)}

    def sha_file(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # ------------------------------------------------------------- campaign
    def attempt_dir():
        public = os.environ.get("PUBLIC")
        if not public:
            raise RuntimeError("PUBLIC is not set")
        root = os.path.join(public, "Documents", "CPM_K")
        pointer = os.path.join(root, POINTER)
        if not os.path.isfile(pointer):
            raise RuntimeError("no active K attempt (%s missing)" % POINTER)
        with open(pointer, "rb") as f:
            raw = f.read()
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        attempt = raw.decode("ascii").strip()
        if not ATTEMPT_RE.match(attempt):
            raise RuntimeError("malformed %s" % POINTER)
        folder = os.path.join(root, attempt)
        if not os.path.isdir(folder):
            raise RuntimeError("attempt folder %s does not exist" % attempt)
        for required in ("authority_pins.json", "deployment_after.json"):
            if not os.path.isfile(os.path.join(folder, required)):
                raise RuntimeError("attempt %s is not deployed (%s missing)" % (attempt, required))
        if os.path.exists(os.path.join(folder, "SHA256SUMS.txt")):
            raise RuntimeError("attempt %s is sealed (SHA256SUMS.txt exists)" % attempt)
        return attempt, folder

    def next_seq(path):
        if not os.path.isfile(path):
            return 1
        with open(path, "rb") as f:
            data = f.read()
        if data and not data.endswith(b"\n"):
            raise RuntimeError("probe.jsonl does not end with a newline (append-only integrity)")
        return data.count(b"\n") + 1

    def write_once(path, data):
        if os.path.exists(path):
            raise RuntimeError("write-once evidence already exists: %s" % os.path.basename(path))
        with open(path, "wb") as f:
            f.write(data)

    # ------------------------------------------------------------- authority
    def runtime_state():
        runtime = sys.modules.get(RUNTIME)
        if runtime is None:
            return {"observed": True, "runtime_loaded": False, "broker_constructed": False}
        out = {"observed": True, "runtime_loaded": True,
               "runtime_file": text(getattr(runtime, "__file__", None)),
               "api": text(getattr(runtime, "RUNTIME_API_VERSION", None)),
               "build": text(getattr(runtime, "RUNTIME_BUILD_ID", None))}
        for key, name in (("is_canonical", "is_canonical"), ("state", "get_state"),
                          ("actual_origin_dir", "get_actual_origin_dir")):
            try:
                out[key] = plain(getattr(runtime, name)())
            except Exception as exc:
                out[key] = {"observed": False, "error": text(exc)}
                errors["runtime." + key] = text(exc)
        broker = getattr(runtime, "_broker", None)  # the runtime's own singleton; never constructed here
        out["broker_constructed"] = broker is not None
        if broker is None:
            return out
        out["broker_id"] = hexid(broker)
        reads = (("outstanding_leases", lambda: int(broker.outstanding_lease_count())),
                 ("unreleased_lease_registry", lambda: int(broker.unreleased_lease_count())),
                 ("provider_counters", lambda: dict((text(k), plain(v)) for k, v in broker.provider_counters().items())),
                 ("view_cache_entries", lambda: int(broker.view_cache_entry_count())),
                 ("diagnostics_count", lambda: len(broker.recent_diagnostics())))
        for key, read in reads:
            try:
                out[key] = read()
            except Exception as exc:
                out[key] = {"observed": False, "error": text(exc)}
                errors["broker." + key] = text(exc)
        return out

    def broker_detail():
        runtime = sys.modules.get(RUNTIME)
        broker = getattr(runtime, "_broker", None) if runtime is not None else None
        if broker is None:
            return {"observed": True, "broker_constructed": False}
        out = {"observed": True, "broker_constructed": True}
        views = []
        try:
            for view in broker._view_cache.all_views():
                views.append({"consumer_kind": text(view.consumer_kind),
                              "master_sha256": text(view.semantic_generation.master_sha256),
                              "covered_keys": len(view.coverage.covered_keys()),
                              "estimated_bytes": plain(view.estimated_bytes),
                              "live_leases": int(view.live_lease_count()),
                              "stale": bool(view.is_stale())})
            out["views"] = views
        except Exception as exc:
            out["views"] = fail("broker.views", exc)
        served = set()
        try:
            for entry in broker.recent_diagnostics():
                detail = entry.get("detail") or {}
                if isinstance(detail, dict):
                    for key in ("views", "consumers"):
                        for kind in detail.get(key) or []:
                            served.add(text(kind))
            out["consumers_served"] = sorted(served)
        except Exception as exc:
            out["consumers_served"] = fail("broker.consumers_served", exc)
        try:
            tail = []
            for entry in broker.recent_diagnostics()[-DIAGNOSTICS_TAIL:]:
                detail = entry.get("detail") if isinstance(entry, dict) else None
                summary = {}
                if isinstance(detail, dict):
                    for key, value in detail.items():
                        if isinstance(value, (list, tuple)):
                            summary[text(key)] = sorted(text(v) for v in value) if len(value) <= 8 else len(value)
                        elif isinstance(value, dict):
                            summary[text(key)] = {"keys": len(value)}
                        else:
                            summary[text(key)] = plain(value)
                tail.append({"event": text(entry.get("event")) if isinstance(entry, dict) else text(entry),
                             "t": plain(entry.get("t")) if isinstance(entry, dict) else None, "detail": summary})
            out["diagnostics_tail"] = tail
        except Exception as exc:
            out["diagnostics_tail"] = fail("broker.diagnostics_tail", exc)
        try:
            out["ledger"] = json.loads(json.dumps(broker.ledger_snapshot(), default=text))
        except Exception as exc:
            out["ledger"] = fail("broker.ledger", exc)
        return out

    def acquisition_delta(before, after):
        if not (before.get("observed") and after.get("observed")):
            return {"determinable": False, "reason": "broker state not observed"}
        if not before.get("broker_constructed"):
            return {"determinable": True, "probe_constructed_broker": bool(after.get("broker_constructed")),
                    "probe_caused_acquisition": bool(after.get("broker_constructed"))}
        if before.get("broker_id") != after.get("broker_id"):
            return {"determinable": True, "probe_caused_acquisition": True, "reason": "broker identity changed"}
        keys = ("outstanding_leases", "unreleased_lease_registry", "view_cache_entries", "diagnostics_count")
        pc_keys = ("current_open_provider_count", "total_provider_opens", "total_provider_closes")
        for key in keys:
            if not isinstance(before.get(key), int) or not isinstance(after.get(key), int):
                return {"determinable": False, "reason": "%s not observed" % key}
        bpc, apc = before.get("provider_counters"), after.get("provider_counters")
        if not isinstance(bpc, dict) or not isinstance(apc, dict) or "observed" in bpc or "observed" in apc:
            return {"determinable": False, "reason": "provider counters not observed"}
        changed = [k for k in keys if before[k] != after[k]] + [k for k in pc_keys if bpc.get(k) != apc.get(k)]
        return {"determinable": True, "probe_caused_acquisition": bool(changed), "changed": changed}

    # ------------------------------------------------------------- resources
    def process_resources():
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

            class MEMSTAT(ctypes.Structure):
                _fields_ = [
                    ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            # Private library instances: they neither depend on nor alter the
            # prototypes another in-process consumer set on ctypes.windll.
            kernel32 = ctypes.WinDLL("kernel32")
            psapi = ctypes.WinDLL("psapi")
            user32 = ctypes.WinDLL("user32")
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel32.GetProcessHandleCount.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
            kernel32.GetProcessHandleCount.restype = wintypes.BOOL
            user32.GetGuiResources.argtypes = [ctypes.c_void_p, wintypes.DWORD]
            user32.GetGuiResources.restype = wintypes.DWORD
            kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MEMSTAT)]
            kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
            handle = kernel32.GetCurrentProcess()
            counters = PMC()
            counters.cb = ctypes.sizeof(PMC)
            out = {"observed": True}
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                out.update({"private_usage": int(counters.PrivateUsage), "working_set": int(counters.WorkingSetSize),
                            "peak_working_set": int(counters.PeakWorkingSetSize),
                            "pagefile_usage": int(counters.PagefileUsage)})
            else:
                out["memory_error"] = "GetProcessMemoryInfo failed"
                errors["resources.memory"] = out["memory_error"]
            count = wintypes.DWORD(0)
            if kernel32.GetProcessHandleCount(handle, ctypes.byref(count)):
                out["handles"] = int(count.value)
            else:
                out["handles_error"] = "GetProcessHandleCount failed"
                errors["resources.handles"] = out["handles_error"]
            status = MEMSTAT()
            status.dwLength = ctypes.sizeof(MEMSTAT)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                out["total_virtual"] = int(status.ullTotalVirtual)
                out["avail_virtual"] = int(status.ullAvailVirtual)
            else:
                out["vas_error"] = "GlobalMemoryStatusEx failed"
                errors["resources.vas"] = out["vas_error"]
            out["gdi_objects"] = int(user32.GetGuiResources(handle, 0))
            out["user_objects"] = int(user32.GetGuiResources(handle, 1))
            return out
        except Exception as exc:
            return fail("resources", exc)

    # ------------------------------------------------------------- CPM / host
    def qt_app():
        from PySide import QtGui
        return QtGui, QtGui.QApplication.instance()

    def module_state(main_dict, impl_path):
        module = sys.modules.get(MODULE_KEY)
        if module is None:
            return {"observed": True, "present": False}, {}
        ns = getattr(module, "__dict__", {})
        out = {"observed": True, "present": True, "id": hexid(module), "type": text(type(module).__name__),
               "name": text(ns.get("__name__")), "file": text(ns.get("__file__")),
               "file_is_impl_path": ns.get("__file__") == impl_path,
               "loader": text(ns.get("__chadchan3d_cpm_loader__")),
               "loader_is_private_loader": ns.get("__chadchan3d_cpm_loader__") == LOADER,
               "state": text(ns.get("__chadchan3d_cpm_state__")),
               "build_sha256": text(ns.get("__chadchan3d_cpm_build_sha256__")),
               "build_is_candidate": ns.get("__chadchan3d_cpm_build_sha256__") == CANDIDATE_APP_SHA256,
               "run_id": text(ns.get("PROD_RUN_ID")), "output_path": text(ns.get("OUTPUT_PATH")),
               "prod_version": text(ns.get("PROD_VERSION")),
               "startup_state": text((ns.get("PROD_R15_STARTUP") or {}).get("state")),
               "prodwindow_class_id": hexid(ns["ProdWindow"]) if "ProdWindow" in ns else None,
               "startprodtool_id": hexid(ns["StartProdTool"]) if "StartProdTool" in ns else None,
               "module_dict_is_main_dict": ns is main_dict}
        out["historical"] = {"semantic_provider_is_none": ns.get("_SEMANTIC_PROVIDER", None) is None,
                             "semantic_provider_bound": "_SEMANTIC_PROVIDER" in ns}
        for name in HISTORICAL:
            out["historical"][name] = plain(ns[name]) if name in ns else {"observed": False, "error": "absent"}
        others = []
        for key, mod in list(sys.modules.items()):
            if mod is None or mod is module or key == MODULE_KEY:
                continue
            try:
                d = getattr(mod, "__dict__", None)
                if isinstance(d, dict) and "ProdWindow" in d and "StartProdTool" in d:
                    others.append(text(key))
            except Exception:
                continue
        out["other_modules_defining_cpm"] = sorted(others)
        return out, ns

    def window_state(window, ns, main_dict):
        if window is None:
            return {"observed": True, "slot_occupied": False}
        cls = ns.get("ProdWindow")
        out = {"observed": True, "slot_occupied": True, "id": hexid(window),
               "class_name": text(type(window).__name__), "class_module": text(type(window).__module__),
               "owned_by_private_module": bool(cls is not None and isinstance(window, cls))}
        try:
            g = window.render.__func__.__globals__
            out["function_globals_is_private_module"] = bool(ns and g is ns)
            out["function_globals_is_main_dict"] = g is main_dict
        except Exception as exc:
            out["function_globals"] = fail("window.function_globals", exc)
        try:
            from PySide import shiboken
            out["alive"] = bool(shiboken.isValid(window))
        except Exception as exc:
            out["alive"] = fail("window.alive", exc)
        if not out["owned_by_private_module"]:
            return out
        for attr in ("busy", "closing_requested", "modal_yield_active", "scene_activity_suspended", "fit_active",
                     "fit_stage_running", "fit_generation", "_cpm_stale_rebuild_pending"):
            out[attr] = plain(getattr(window, attr, None))
        out["modal_deferred_fit_stage_pending"] = getattr(window, "modal_deferred_fit_stage", None) is not None
        out["fit_semantic_generation"] = plain(getattr(window, "fit_semantic_generation", None))
        out["fit_authority_context_present"] = getattr(window, "fit_authority_context", None) is not None
        out["fit_selected"] = [text((i or {}).get("name")) for i in (getattr(window, "fit_selected_identities", None) or [])]
        accounting = {}
        for attr in ("fit_changed", "fit_unchanged", "fit_partial", "fit_skipped", "fit_failed", "fit_unattempted",
                     "fit_committed_order"):
            value = getattr(window, attr, None)
            accounting[attr] = None if value is None else len(value)
        out["fit_accounting"] = accounting
        operation = getattr(window, "operation", None)
        out["operation"] = None if operation is None else dict(
            (k, plain(operation.get(k))) for k in ("operation_id", "kind", "phase", "native_commit",
                                                   "durable_commit", "closing_requested"))
        identity = getattr(window, "identity", None)
        out["identity"] = None if not isinstance(identity, dict) else dict(
            (k, plain(identity.get(k))) for k in ("animset_name", "model", "checksum"))
        health = getattr(window, "provider_health", None) or {}
        out["provider_health"] = {"status": plain(health.get("status")), "reason": plain(health.get("reason"))}
        scope = getattr(window, "scope", None)
        if isinstance(scope, dict):
            authority = scope.get("authority") or {}
            semantic = scope.get("semantic") or {}
            out["scope"] = {
                "present": True,
                "provider_sha256": plain(authority.get("provider_sha256")),
                "provider_generation": plain(authority.get("provider_generation")),
                "semantic_policy_revision": plain(authority.get("semantic_policy_revision")),
                "override_revision": plain(authority.get("override_revision")),
                "counts": dict((text(k), plain(v)) for k, v in (semantic.get("counts") or {}).items()),
                "body": len(scope.get("body") or {}), "expression": len(scope.get("expression") or {}),
                "unresolved": len(scope.get("unresolved") or []), "conflicts": len(scope.get("conflicts") or []),
                "overrides": len(scope.get("overrides") or {}),
                "provider_kind": plain((scope.get("provider_descriptor") or {}).get("provider_kind"))}
        else:
            out["scope"] = {"present": False}
        try:
            timer = getattr(window, "modal_watch_timer", None)
            out["watcher_active"] = None if timer is None else bool(timer.isActive())
            out["visible"] = bool(window.isVisible())
            out["status_text"] = text(window.status.text())
        except Exception as exc:
            out["qt"] = fail("window.qt", exc)
        return out

    def census(QtGui, app, ns):
        if app is None:
            return {"observed": False, "error": "no QApplication"}
        cls = ns.get("ProdWindow")
        tops = list(app.topLevelWidgets())
        prod = [w for w in tops if type(w).__name__ == "ProdWindow"]
        out = {"observed": True, "prodwindow_toplevel_total": len(prod),
               "prodwindow_toplevel_owned": len([w for w in prod if cls is not None and isinstance(w, cls)]),
               "prodwindow_toplevel_visible": len([w for w in prod if w.isVisible()]),
               "active_watchers": len([w for w in prod if getattr(w, "modal_watch_timer", None) is not None
                                       and w.modal_watch_timer.isActive()])}
        modal = app.activeModalWidget()
        out["active_modal"] = text(type(modal).__name__) if modal is not None else None
        del tops, prod, modal
        return out

    # ------------------------------------------------------------- scene
    def scene_snapshot(ns):
        if not ns or ns.get("__chadchan3d_cpm_state__") != "ready":
            return {"observed": False, "error": "private CPM module not ready (no CPM scene readers)"}
        rows = ns["p03_model_animsets"]()
        present = {}
        sets = {}
        for row in rows:
            name, model, checksum = text(row.get("name")), text(row.get("model")), row.get("checksum")
            for fx_name, fx_model, fx_checksum in FIXTURES:
                if name != fx_name:
                    continue
                matches = model == fx_model and checksum == fx_checksum
                present.setdefault(fx_name, []).append({"model": model, "checksum": plain(checksum),
                                                        "identity_matches": matches})
                if not matches:
                    continue
                literals = {}
                for binding in ns["p01_all_supported_flex_bindings"](row["animset"]):
                    snap = ns["binding_snapshot"](binding)
                    sides = {}
                    for side_name, side in sorted((snap.get("sides") or {}).items()):
                        sides[text(side_name)] = dict((k, plain(side.get(k))) for k in SIDE_KEYS if k in side)
                    literals[text(snap.get("literal"))] = sides
                    del snap
                sets[fx_name] = literals
        del rows
        undo = {}
        data = ns["dm"]()
        for key, method in (("enabled", "IsUndoEnabled"), ("count", "GetUndoItemCount"), ("desc", "GetUndoDesc")):
            try:
                undo[key] = plain(getattr(data, method)())
            except Exception as exc:
                undo[key] = {"observed": False, "error": text(exc)}
                errors["scene.undo." + key] = text(exc)
        del data
        duplicates = sorted(k for k, v in present.items() if len(v) > 1)
        return {"observed": True, "fixtures_present": present, "fixture_sets": sets, "undo": undo,
                "duplicate_fixture_names": duplicates}

    # ------------------------------------------------------------- run
    started = time.time()
    record = {"schema": SCHEMA, "probe": PROBE_VERSION, "wall_time": now(), "epoch": started,
              "pid": os.getpid(), "python": text(sys.version.split()[0])}
    main = sys.modules.get("__main__")
    main_dict = getattr(main, "__dict__", {})
    record["host"] = {"probe_globals_is_main_dict": globals() is main_dict,
                      "cpm_names_in_main": sorted(n for n in MAIN_SENTINELS if n in main_dict),
                      "normalizer_names_in_main": sorted(n for n in NORMALIZER_MAIN_SENTINELS if n in main_dict),
                      "main_dict_size": len(main_dict)}
    try:
        attempt, folder = attempt_dir()
    except Exception as exc:
        sys.stdout.write("CPM_K_PROBE REFUSED: %s (nothing written)\n" % text(exc))
        return
    record["attempt"] = attempt
    record["broker_before"] = runtime_state()
    record["resources"] = process_resources()
    game_root = os.path.dirname(os.path.abspath(sys.executable))
    scripts = os.path.join(game_root, "usermod", "scripts")
    impl_path = os.path.normpath(os.path.abspath(os.path.join(scripts, "ChadChan3D_CPM", "SFM_Character_Preset_Manager.py")))
    menu = os.path.join(scripts, "sfm", "mainmenu", "ChadChan3D")
    identity = {}
    for key, path in (("installed_impl_sha256", impl_path),
                      ("installed_launcher_sha256", os.path.join(menu, "SFM_Character_Preset_Manager.py")),
                      ("installed_probe_sha256", os.path.join(menu, "CPM_K_Probe.py"))):
        try:
            identity[key] = sha_file(path)
        except Exception as exc:
            identity[key] = {"observed": False, "error": text(exc)}
            errors["identity." + key] = text(exc)
    identity["impl_is_candidate"] = identity.get("installed_impl_sha256") == CANDIDATE_APP_SHA256
    identity["launcher_is_pinned"] = identity.get("installed_launcher_sha256") == LAUNCHER_SHA256
    record["identity"] = identity
    try:
        record["module"], ns = module_state(main_dict, impl_path)
    except Exception as exc:
        record["module"], ns = fail("module", exc), {}
    window = None
    try:
        QtGui, app = qt_app()
        window = getattr(app, WINDOW_ATTR, None) if app is not None else None
        record["window"] = window_state(window, ns, main_dict)
        record["census"] = census(QtGui, app, ns)
        del QtGui, app
    except Exception as exc:
        record.setdefault("window", fail("window", exc))
        record.setdefault("census", {"observed": False, "error": text(exc)})
    window = None
    record["broker_detail"] = broker_detail()
    snapshot_name = "probe_%04d.json"
    try:
        seq = next_seq(os.path.join(folder, "probe.jsonl"))
    except Exception as exc:
        sys.stdout.write("CPM_K_PROBE REFUSED: %s (nothing written)\n" % text(exc))
        return
    record["seq"] = seq
    try:
        snap = scene_snapshot(ns)
    except Exception as exc:
        snap = fail("scene", exc)
    snapshot = {"schema": SNAPSHOT_SCHEMA, "seq": seq, "attempt": attempt, "wall_time": record["wall_time"],
                "scene": snap}
    snap = None
    ns = None
    try:
        data = json.dumps(snapshot, indent=1, sort_keys=True, default=text).encode("utf-8")
        snapshot = None
        path = os.path.join(folder, "scene_snapshots", snapshot_name % seq)
        write_once(path, data)
        record["scene_snapshot"] = {"observed": True, "file": "scene_snapshots/" + snapshot_name % seq,
                                    "sha256": hashlib.sha256(data).hexdigest()}
    except Exception as exc:
        record["scene_snapshot"] = fail("scene_snapshot", exc)
    record["broker_after"] = runtime_state()
    record["acquisition_by_probe"] = acquisition_delta(record["broker_before"], record["broker_after"])
    record["errors"] = errors
    record["elapsed_seconds"] = round(time.time() - started, 6)
    line = (json.dumps(record, sort_keys=True, default=text) + "\n").encode("utf-8")
    with open(os.path.join(folder, "probe.jsonl"), "ab") as f:
        f.write(line)
    b, m, w = record["broker_before"], record["module"], record["window"]
    pc = b.get("provider_counters") if isinstance(b.get("provider_counters"), dict) else {}
    sys.stdout.write(
        "CPM_K_PROBE seq=%s attempt=%s impl_is_candidate=%s build_is_candidate=%s module=%s window_owned=%s "
        "leases=%s unreleased=%s open_providers=%s acquisition_by_probe=%s historical_provider_none=%s "
        "errors=%s snapshot=%s\n"
        % (seq, attempt, identity.get("impl_is_candidate"), m.get("build_is_candidate"), m.get("state"),
           w.get("owned_by_private_module"), b.get("outstanding_leases"), b.get("unreleased_lease_registry"),
           pc.get("current_open_provider_count"), record["acquisition_by_probe"].get("probe_caused_acquisition"),
           (m.get("historical") or {}).get("semantic_provider_is_none"), sorted(errors),
           (record.get("scene_snapshot") or {}).get("file")))


try:
    _cpm_k_probe_v1()
finally:
    try:
        del _cpm_k_probe_v1
    except NameError:
        pass
    try:
        __import__("sys").exc_clear()
    except AttributeError:
        pass
