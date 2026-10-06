# -*- coding: ascii -*-
# CPM real-SFM Session 4 -- forced rollback-verification qualification harness.
#
# QUALIFICATION-ONLY. Not product code. Deployed temporarily to the ChadChan3D
# Scripts menu for Session 4 and removed afterwards (SESSION4_RUNBOOK.md).
#
# One state-driven menu script. The campaign folder is named by
# %PUBLIC%\Documents\CPM_Session4\ACTIVE_CAMPAIGN.txt; its leaf selects the gate:
#   S4A[_Rn] -> Body Apply (fixture mia1, preset BodyTest)
#   S4F[_Rn] -> Clothing Fit (krystal20201 -> assaultsuitbody1, loinclothbra_chadfix_071)
# Scenario 1 is the CONTROL, scenario 2 the GATE. Per menu click:
#   no s1_arm                      -> ARM scenario 1
#   s1_arm, no s1_state            -> STATE scenario 1
#   s1_state RECORDED_OK, no s2_arm -> ARM scenario 2
#   s2_arm, no s2_state            -> STATE scenario 2
#   anything else                  -> REFUSE
#
# ARM verifies the pinned private-app build and every original function
# object, then rebinds a few names in the private module namespace with
# one-shot wrappers (there is no narrower seam inside the open Undo):
#   precommit predicate  (Apply p03_verify_saved_values / Fit matches_value):
#     fires only from prod_apply / prod_apply_match with the Undo open
#     (caller local opened is True) for the armed preset / target; it calls the
#     REAL predicate first, records its result, restores its own binding, then
#     returns False -> production raises its own precommit error, runs its own
#     Abort and its own rollback verifier.
#   rollback verifier    (prod_verify_apply_abort_baseline /
#     p03_target_matches_baseline): fires only from production's abort helper
#     after the injection; calls the REAL verifier first, records it, restores
#     every binding, then returns the real result (CONTROL) or False (GATE).
#   observers (pass-through): prod_cpm_open_adapter (call counter) and, for Fit,
#     prod_cpm_open_fit_stage (counts release() calls of the armed stage).
# The harness never writes authority files, never acquires authority, never
# writes production log lines and never edits product files.
#
# (Comments, not a docstring: a module docstring would rebind __doc__ in SFM's
# shared Scripts-menu namespace.)


def _cpm_s4_rollback_harness_v1():
    import datetime
    import hashlib
    import json
    import numbers
    import os
    import re
    import sys
    import time
    import traceback
    import types

    from PySide import QtCore
    from PySide import QtGui

    G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
    APP_SHA = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
    MODULE_KEY = "chadchan3d_cpm_app"
    LOADER = "cpm-private-loader-v1"
    WINDOW_ATTR = "_sfm_character_slider_preset_tool_window"
    RUNTIME = "sfm_master_authority_productionized.runtime"
    STATE_ATTR = "_cpm_s4_state_v1"
    NOTICE_ATTR = "_cpm_s4_harness_notice_v1"
    WRAP_MARK = "_cpm_s4_wrapper_v1"
    # def-line numbers in the pinned app build (APP_SHA).
    PINS = {"p03_verify_saved_values": 6091, "matches_value": 868,
            "p03_target_matches_baseline": 7612, "prod_verify_apply_abort_baseline": 27557,
            "prod_abort_apply_and_verify": 27668, "prod_abort_fit_and_verify": 27724,
            "prod_apply": 27774, "prod_apply_match": 28445,
            "prod_cpm_open_adapter": 18691, "prod_cpm_open_fit_stage": 18942}
    MIA = {"animset_name": u"mia1", "checksum": 1153028609, "model": u"models/annoad/foxbase/mia/mia.mdl"}
    PRESET = u"BodyTest"
    SOURCE = {"animset_name": u"krystal20201", "checksum": -1441261258,
              "model": u"models/fursonas/starfox/krystal/bodies/krystal2020.mdl"}
    TARGET1 = {"name": u"assaultsuitbody1", "checksum": -791536511,
               "model": u"models/fursonas/starfox/krystal/cosmetics/assaultsuitbody.mdl"}
    TARGET2 = {"name": u"loinclothbra_chadfix_071", "checksum": 480892851,
               "model": u"models/fursonas/starfox/krystal/cosmetics/loinclothbra_chadfix_07.mdl"}
    GATES = {
        "A": {"label": "Apply", "predicate": "p03_verify_saved_values",
              "predicate_caller": "prod_apply", "verifier": "prod_verify_apply_abort_baseline",
              "verifier_caller": "prod_abort_apply_and_verify",
              "observers": ["prod_cpm_open_adapter"]},
        "F": {"label": "Clothing Fit", "predicate": "matches_value",
              "predicate_caller": "prod_apply_match", "verifier": "p03_target_matches_baseline",
              "verifier_caller": "prod_abort_fit_and_verify",
              "observers": ["prod_cpm_open_adapter", "prod_cpm_open_fit_stage"]},
    }
    SCENARIOS = {1: "CONTROL", 2: "GATE"}
    # Production's own status copy for each scenario (prefix match).
    STATUS = {("A", 1): u"Preset could not be applied safely. This preset was not applied.",
              ("A", 2): u"Preset Apply failed and recovery could not be verified.",
              ("F", 1): u"Clothing Fit could not finish. Nothing changed.",
              ("F", 2): u"Clothing Fit stopped. Recovery of the failed target could not be verified."}
    EPS = 1.0e-5

    # ---------------------------------------------------------------- helpers
    def now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def text(value):
        try:
            return unicode(value)  # noqa: F821
        except NameError:
            return str(value)
        except Exception:
            return repr(value)

    def sha_file(path):
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def read_json(path):
        with open(path, "rb") as f:
            raw = f.read()
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        return json.loads(raw.decode("utf-8"))

    def write_once(path, record):
        if os.path.exists(path):
            raise RuntimeError("write-once evidence already exists: %s" % (path,))
        data = json.dumps(record, indent=2, sort_keys=True, default=text)
        with open(path, "wb") as f:
            f.write(data.encode("utf-8"))

    def say(message):
        try:
            sys.stdout.write("[CPM S4 harness] %s\n" % (message,))
        except Exception:
            pass

    def show_notice(message):
        say(message)
        try:
            app = QtGui.QApplication.instance()
            box = getattr(app, NOTICE_ATTR, None)
            if box is None:
                box = QtGui.QMessageBox()
                box.setWindowTitle("CPM Session 4 harness")
                box.setStandardButtons(QtGui.QMessageBox.Ok)
                box.setModal(False)
                box.setWindowModality(QtCore.Qt.NonModal)
                box.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
                setattr(app, NOTICE_ATTR, box)
            box.setText(message)
            box.show()
            box.raise_()
        except Exception:
            pass

    def master_path():
        game = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(game, "usermod", "cfg", "sfm_defaultanimationgroups.txt")

    def campaign():
        public = os.environ.get("PUBLIC")
        if not public:
            raise RuntimeError("PUBLIC is not set")
        root = os.path.join(public, "Documents", "CPM_Session4")
        pointer = os.path.join(root, "ACTIVE_CAMPAIGN.txt")
        if not os.path.isfile(pointer):
            raise RuntimeError("no ACTIVE_CAMPAIGN.txt (run S4-Activate)")
        with open(pointer, "rb") as f:
            leaf = f.read().decode("utf-8").strip()
        match = re.match(r"^S4([AF])(_R[2-9])?$", leaf)
        if not match:
            raise RuntimeError("malformed ACTIVE_CAMPAIGN.txt (%r)" % (leaf,))
        folder = os.path.join(root, leaf)
        if not os.path.isdir(folder):
            raise RuntimeError("campaign folder missing: %s" % (leaf,))
        return folder, leaf, match.group(1)

    def rec_path(folder, scenario, kind):
        return os.path.join(folder, "s%d_%s.json" % (scenario, kind))

    def cpm():
        module = sys.modules.get(MODULE_KEY)
        ns = getattr(module, "__dict__", None)
        if not ns or ns.get("__chadchan3d_cpm_loader__") != LOADER or ns.get("__chadchan3d_cpm_state__") != "ready":
            raise RuntimeError("private CPM module is not ready")
        app = QtGui.QApplication.instance()
        window = getattr(app, WINDOW_ATTR, None)
        cls = ns.get("ProdWindow")
        if window is None or cls is None or not isinstance(window, cls):
            raise RuntimeError("no CPM window owned by the private module")
        return module, ns, app, window

    def get_state():
        return getattr(QtGui.QApplication.instance(), STATE_ATTR, None)

    def set_state(value):
        setattr(QtGui.QApplication.instance(), STATE_ATTR, value)

    def broker_counters():
        runtime = sys.modules.get(RUNTIME)
        broker = getattr(runtime, "_broker", None) if runtime is not None else None
        if broker is None:
            raise RuntimeError("canonical broker not constructed")
        pc = broker.provider_counters()
        return {"broker_id": "0x%x" % id(broker),
                "outstanding_leases": int(broker.outstanding_lease_count()),
                "unreleased_leases": int(broker.unreleased_lease_count()),
                "open_providers": int(pc.get("current_open_provider_count")),
                "total_provider_opens": pc.get("total_provider_opens"),
                "total_provider_closes": pc.get("total_provider_closes")}

    def safe_counters():
        try:
            return broker_counters()
        except Exception as exc:
            return {"error": text(exc)}

    def undo_facts(ns):
        data = ns["dm"]()
        out = {}
        for key, method in (("enabled", "IsUndoEnabled"), ("count", "GetUndoItemCount"), ("desc", "GetUndoDesc")):
            try:
                value = getattr(data, method)()
                out[key] = value if isinstance(value, (bool, int, float)) else text(value)
            except Exception as exc:
                out[key] = "error: %s" % text(exc)
        return out

    def same_identity(a, b):
        try:
            return (text(a.get("name") or a.get("animset_name")) == text(b.get("name") or b.get("animset_name"))
                    and text(a.get("model")) == text(b.get("model"))
                    and int(a.get("checksum")) == int(b.get("checksum")))
        except Exception:
            return False

    def code_of(fn):
        return getattr(fn, "__code__", None)

    def original_problems(ns, name):
        fn = ns.get(name)
        if not isinstance(fn, types.FunctionType):
            return "%s is not a plain function" % name
        if getattr(fn, WRAP_MARK, False):
            return "%s is already a Session 4 wrapper" % name
        if fn.__name__ != name or getattr(fn, "__globals__", None) is not ns:
            return "%s is not the private module's own function" % name
        if code_of(fn).co_firstlineno != PINS[name]:
            return "%s is not at its pinned definition (line %d, expected %d)" % (
                name, code_of(fn).co_firstlineno, PINS[name])
        return None

    def snapshot_animset(ns, animset):
        """Read-only per-binding values via CPM's own read helpers."""
        out = {}
        for binding in ns["p01_all_supported_flex_bindings"](animset):
            snap = ns["binding_snapshot"](binding)
            sides = {}
            for side_name, side in sorted((snap.get("sides") or {}).items()):
                sides[text(side_name)] = dict(
                    (k, side.get(k)) for k in ("source", "destination", "evaluated", "key_count",
                                                "key0_time", "key0_value", "is_empty") if k in side)
            out[text(snap.get("literal"))] = sides
        if not out:
            raise RuntimeError("no readable flex bindings")
        return out

    def is_number(value):
        return isinstance(value, numbers.Number) and not isinstance(value, bool)

    def same_values(sa, sb):
        if sa is None or sb is None or set(sa) != set(sb):
            return False
        for side in sa:
            va, vb = sa[side] or {}, sb[side] or {}
            if set(va) != set(vb):
                return False
            for key in va:
                x, y = va[key], vb[key]
                if is_number(x) and is_number(y):
                    if abs(float(x) - float(y)) > EPS:
                        return False
                elif x != y:
                    return False
        return True

    def differing(a, b):
        return [literal for literal in sorted(set(a) | set(b)) if not same_values(a.get(literal), b.get(literal))]

    def scene_snapshot(ns, gate):
        if gate == "A":
            return {"mia1": snapshot_animset(ns, ns["prod_resolve"](dict(MIA))["animset"])}
        return {"target1": snapshot_animset(ns, ns["g11a_resolve_target"](dict(TARGET1))["animset"]),
                "target2": snapshot_animset(ns, ns["g11a_resolve_target"](dict(TARGET2))["animset"])}

    def window_facts(window):
        facts = {"operation": None if window.operation is None else text(window.operation.get("kind")),
                 "fit_active": bool(window.fit_active), "fit_stage_running": bool(window.fit_stage_running),
                 "closing_requested": bool(window.closing_requested),
                 "modal_yield_active": bool(window.modal_yield_active),
                 "scene_activity_suspended": bool(window.scene_activity_suspended)}
        try:
            facts["status_text"] = text(window.status.text())
        except Exception:
            facts["status_text"] = None
        for name in ("fit_committed_order", "fit_failed", "fit_unattempted", "fit_skipped", "fit_partial",
                     "fit_changed", "fit_selected_identities"):
            try:
                facts[name] = [dict(item) for item in (getattr(window, name, None) or [])]
            except Exception:
                facts[name] = "unreadable"
        facts["gfit"] = text(getattr(window, "fit_semantic_generation", None))
        return facts

    # ------------------------------------------------------- binding control
    def restore_all(ns, st):
        restored = []
        for name in list(st.get("installed") or []):
            original = st["originals"][name]
            if ns.get(name) is not original:
                ns[name] = original
            restored.append(name)
        st["installed"] = []
        return restored

    def restore_one(ns, st, name):
        if name in (st.get("installed") or []):
            ns[name] = st["originals"][name]
            st["installed"].remove(name)

    def caller_is(st, name, depth=2):
        try:
            frame = sys._getframe(depth)
        except Exception:
            return None
        if frame.f_code is st["caller_codes"].get(name):
            return frame
        return None

    def finish_fire(ns, st, record):
        """Restore every binding, write the fire record once, mark fired."""
        record["restored_on_fire"] = restore_all(ns, st)
        record["bindings_after_fire_are_originals"] = all(
            ns.get(name) is st["originals"][name] for name in st["originals"])
        st["phase"] = "fired"
        st["fire"] = record
        try:
            write_once(st["paths"]["fire"], record)
        except Exception as exc:
            st.setdefault("errors", []).append("fire record: %s" % text(exc))

    def make_wrappers(ns, st, gate, scenario):
        spec = GATES[gate]
        wrappers = {}

        def adapter_counter(original):
            def s4_prod_cpm_open_adapter(*args, **kwargs):
                st["adapter_calls"] = st.get("adapter_calls", 0) + 1
                return original(*args, **kwargs)
            return s4_prod_cpm_open_adapter
        wrappers["prod_cpm_open_adapter"] = adapter_counter

        def stage_observer(original):
            def s4_prod_cpm_open_fit_stage(fit_context, target_row, index):
                stage = original(fit_context, target_row, index)
                try:
                    if st.get("phase") == "armed" and st.get("stage_id") is None and index == 0:
                        window = st["window"]
                        selected = (window.fit_selected_identities or [])
                        if selected and same_identity(selected[0], TARGET1) \
                                and text(getattr(stage, "generation", None)) == G1:
                            release = stage.release
                            releases = st["releases"]

                            def s4_counted_release():
                                entry = {"wall_time": now(), "counters_before": safe_counters()}
                                releases.append(entry)
                                result = release()
                                entry["result"] = None if result is None else text(result)
                                entry["counters_after"] = safe_counters()
                                return result
                            stage.release = s4_counted_release
                            st["stage_id"] = "0x%x" % id(stage)
                            st["stage_opened"] = {"wall_time": now(), "index": index,
                                                  "generation": text(stage.generation),
                                                  "counters": safe_counters()}
                except Exception as exc:
                    st.setdefault("errors", []).append("stage observer: %s" % text(exc))
                return stage
            return s4_prod_cpm_open_fit_stage
        wrappers["prod_cpm_open_fit_stage"] = stage_observer

        def predicate(original):
            def s4_precommit_predicate(*args, **kwargs):
                frame = caller_is(st, spec["predicate_caller"]) if st.get("phase") == "armed" else None
                if frame is None:
                    return original(*args, **kwargs)
                loc = frame.f_locals
                facts = {"wall_time": now(), "caller": spec["predicate_caller"],
                         "caller_opened": loc.get("opened")}
                try:
                    if gate == "A":
                        record = loc.get("record") or {}
                        context = loc.get("authority_context") or {}
                        built = loc.get("built") or {}
                        gated = (loc.get("opened") is True and text(record.get("name")) == PRESET
                                 and loc.get("kind") == ns.get("P03_KIND_BODY")
                                 and same_identity(loc.get("identity") or {}, MIA))
                        facts.update({"preset": text(record.get("name")), "kind": text(loc.get("kind")),
                                      "authority_master_sha256": text(context.get("master_sha256")),
                                      "authority_operation": text(context.get("operation")),
                                      "changed_sides": built.get("changed_sides")})
                    else:
                        plan = loc.get("plan") or {}
                        window = st["window"]
                        gated = (loc.get("opened") is True and same_identity(plan.get("identity") or {}, TARGET1)
                                 and st.get("stage_id") is not None and bool(window.fit_stage_running)
                                 and text(getattr(window, "fit_semantic_generation", None)) == G1)
                        facts.update({"target": dict(plan.get("identity") or {}),
                                      "changed_sides": plan.get("changed_sides"),
                                      "gfit": text(getattr(window, "fit_semantic_generation", None))})
                except Exception as exc:
                    gated = False
                    facts["gate_error"] = text(exc)
                if not gated:
                    st["passthrough"] = st.get("passthrough", 0) + 1
                    return original(*args, **kwargs)
                restore_one(ns, st, spec["predicate"])          # one-shot
                try:
                    real = original(*args, **kwargs)             # REAL predicate first
                except BaseException as exc:
                    st["phase"] = "invalid"
                    st.setdefault("errors", []).append("real precommit predicate raised %r" % (exc,))
                    restore_all(ns, st)
                    raise
                facts["real_result"] = real
                # No Undo/DataModel reads here: the native Undo is still open.
                facts["counters"] = safe_counters()
                facts["adapter_calls"] = st.get("adapter_calls", 0)
                facts["releases_so_far"] = len(st.get("releases") or [])
                st["injection"] = facts
                if real is not True:
                    st["phase"] = "invalid"
                    st.setdefault("errors", []).append("real precommit predicate returned %r" % (real,))
                    restore_all(ns, st)
                    return real
                st["phase"] = "injected"
                return False
            return s4_precommit_predicate
        wrappers[spec["predicate"]] = predicate

        def verifier(original):
            def s4_rollback_verifier(*args, **kwargs):
                frame = caller_is(st, spec["verifier_caller"]) if st.get("phase") == "injected" else None
                if frame is None:
                    return original(*args, **kwargs)
                restore_one(ns, st, spec["verifier"])           # one-shot
                record = {"schema": "cpm-s4-fire-v1", "gate": gate, "scenario": scenario,
                          "scenario_kind": SCENARIOS[scenario], "injection": st.get("injection"),
                          "verifier": spec["verifier"], "verifier_caller": spec["verifier_caller"],
                          "entry_wall_time": now(), "entry_undo": undo_facts(ns),
                          "entry_counters": safe_counters(),
                          "entry_releases": len(st.get("releases") or [])}
                calls_before = st.get("adapter_calls", 0)
                try:
                    real = original(*args, **kwargs)             # REAL verifier first
                except BaseException as exc:
                    record.update({"real_result": None, "real_exception": repr(exc),
                                   "adapter_calls_during_verification": st.get("adapter_calls", 0) - calls_before,
                                   "exit_counters": safe_counters(), "returned": "re-raised real exception"})
                    finish_fire(ns, st, record)
                    raise
                substitute = (scenario == 2)
                record.update({"real_result": real, "real_exception": None,
                               "adapter_calls_during_verification": st.get("adapter_calls", 0) - calls_before,
                               "exit_counters": safe_counters(), "exit_wall_time": now(),
                               "substituted": substitute,
                               "returned": False if substitute else real})
                finish_fire(ns, st, record)
                return False if substitute else real
            return s4_rollback_verifier
        wrappers[spec["verifier"]] = verifier

        names = [spec["predicate"], spec["verifier"]] + list(spec["observers"])
        return dict((name, wrappers[name]) for name in names)

    # ------------------------------------------------------------------- modes
    def mode_arm(folder, leaf, gate, scenario):
        module, ns, app, window = cpm()
        old = get_state()
        problems = []
        if old is not None and old.get("installed"):
            restored = restore_all(ns, old)
            problems.append("Session 4 wrappers were still installed and have been restored (%s)" % ", ".join(restored))
        set_state(None)
        for name in ("baseline_inventory.json", "deploy_before_harness.txt", "harness_deploy_record.json"):
            if not os.path.isfile(os.path.join(folder, name)):
                problems.append("%s missing" % name)
        if os.path.isfile(os.path.join(folder, "baseline_inventory.json")) \
                and read_json(os.path.join(folder, "baseline_inventory.json")).get("master_sha256") != G1:
            problems.append("baseline inventory is not G1")
        for kind in ("arm", "fire", "state"):
            if os.path.exists(rec_path(folder, scenario, kind)):
                problems.append("s%d_%s.json already exists" % (scenario, kind))
        if scenario == 2:
            first = rec_path(folder, 1, "state")
            if not os.path.isfile(first) or read_json(first).get("status") != "RECORDED_OK":
                problems.append("scenario 1 is not RECORDED_OK")
        if text(ns.get("__chadchan3d_cpm_build_sha256__")) != APP_SHA:
            problems.append("private app build is not the pinned %s" % APP_SHA[:12])
        for name in sorted(PINS):
            issue = original_problems(ns, name)
            if issue:
                problems.append(issue)
        live = sha_file(master_path())
        if live != G1:
            problems.append("live Master is not G1")
        facts = window_facts(window)
        if facts["operation"] is not None or facts["fit_active"] or facts["fit_stage_running"]:
            problems.append("CPM is busy")
        if facts["closing_requested"] or facts["modal_yield_active"] or facts["scene_activity_suspended"]:
            problems.append("CPM window is closing or yielding")
        if app.activeModalWidget() is not None:
            problems.append("a modal dialog is open")
        identity = window.identity or {}
        expected = MIA if gate == "A" else SOURCE
        if not (text(identity.get("model")) == expected["model"]
                and int(identity.get("checksum") or 0) == expected["checksum"]):
            problems.append("selected model is not %s" % expected["animset_name"])
        if text(((window.scope or {}).get("authority") or {}).get("provider_sha256")) != G1:
            problems.append("selected scope is not G1")
        if gate == "F":
            tokens = [dict(t) for t in (window.fit_identity_tokens or [])]
            for target, label in ((TARGET1, "target 1"), (TARGET2, "target 2")):
                if not any(same_identity(t, target) for t in tokens):
                    problems.append("%s is not a Fit candidate" % label)
        counters = None
        try:
            counters = broker_counters()
            for key in ("outstanding_leases", "unreleased_leases", "open_providers"):
                if counters[key] != 0:
                    problems.append("%s = %d" % (key, counters[key]))
        except Exception as exc:
            problems.append(text(exc))
        snapshot = undo = None
        try:
            snapshot = scene_snapshot(ns, gate)
            undo = undo_facts(ns)
        except Exception as exc:
            problems.append("scene snapshot failed: %s" % text(exc))
        if problems:
            raise RuntimeError("; ".join(problems))
        spec = GATES[gate]
        st = {"campaign": leaf, "gate": gate, "scenario": scenario, "phase": "armed",
              "module_id": id(module), "window": window, "window_id": "0x%x" % id(window),
              "originals": {}, "installed": [], "adapter_calls": 0, "releases": [], "stage_id": None,
              "passthrough": 0, "paths": {"fire": rec_path(folder, scenario, "fire")},
              "caller_codes": dict((name, code_of(ns[name])) for name in
                                   (spec["predicate_caller"], spec["verifier_caller"]))}
        arm = {"schema": "cpm-s4-arm-v1", "wall_time": now(), "epoch": time.time(), "pid": os.getpid(),
               "campaign": leaf, "gate": gate, "scenario": scenario, "scenario_kind": SCENARIOS[scenario],
               "live_master_sha256": live, "app_build_sha256": APP_SHA,
               "module": {"id": "0x%x" % id(module), "run_id": text(ns.get("PROD_RUN_ID"))},
               "window_id": st["window_id"], "identity": dict(identity), "broker": counters,
               "undo": undo, "scene": snapshot, "pins": PINS,
               "wrapped": [], "fixture": {"preset": PRESET, "source": MIA} if gate == "A"
               else {"source": SOURCE, "target1": TARGET1, "target2": TARGET2}}
        wrappers = make_wrappers(ns, st, gate, scenario)
        try:
            for name, factory in sorted(wrappers.items()):
                original = ns[name]
                wrapper = factory(original)
                setattr(wrapper, WRAP_MARK, True)
                st["originals"][name] = original
                ns[name] = wrapper
                st["installed"].append(name)
            arm["wrapped"] = sorted(st["installed"])
            write_once(rec_path(folder, scenario, "arm"), arm)
        except BaseException:
            restore_all(ns, st)
            raise
        set_state(st)
        if gate == "A":
            action = "In CPM click Apply Preset with BodyTest selected."
        else:
            action = "In CPM check assaultsuitbody1 and loinclothbra_chadfix_071, then Fit Selected to Model."
        return "S4 ARMED: %s %s (scenario %d). %s" % (spec["label"], SCENARIOS[scenario], scenario, action)

    def expected_checks(gate, scenario, st, fire, facts, undo_ok, scene_ok, counters, wrappers_absent):
        checks = []

        def add(name, ok):
            checks.append({"check": name, "ok": bool(ok)})
        injection = (st.get("injection") or {})
        add("injection_fired_inside_open_undo", injection.get("caller_opened") is True)
        add("real_precommit_predicate_true", injection.get("real_result") is True)
        add("rollback_verifier_fired", fire is not None)
        add("real_rollback_verification_true", fire is not None and fire.get("real_result") is True)
        add("substitution_matches_scenario", fire is not None and fire.get("substituted") is (scenario == 2))
        add("no_adapter_calls_during_rollback_verification",
            fire is not None and fire.get("adapter_calls_during_verification") == 0)
        add("wrappers_absent", wrappers_absent)
        add("undo_count_and_desc_unchanged", undo_ok)
        add("scene_values_equal_pre_arm", scene_ok)
        add("idle_counters_zero", all(counters.get(k) == 0 for k in
                                      ("outstanding_leases", "unreleased_leases", "open_providers")))
        add("cpm_idle", facts["operation"] is None and not facts["fit_active"] and not facts["fit_stage_running"])
        add("production_status_copy", text(facts.get("status_text") or u"").startswith(STATUS[(gate, scenario)]))
        if gate == "A":
            add("authorized_under_g1", injection.get("authority_master_sha256") == G1)
            add("writes_planned", (injection.get("changed_sides") or 0) > 0)
        else:
            add("stage_opened_under_g1", (st.get("stage_opened") or {}).get("generation") == G1)
            add("stage_lease_held_during_rollback_verification",
                fire is not None and (fire.get("entry_counters") or {}).get("outstanding_leases") == 1)
            add("no_release_before_rollback_verification", fire is not None and fire.get("entry_releases") == 0)
            add("stage_released_exactly_once", len(st.get("releases") or []) == 1)
            add("release_returned_ok", len(st.get("releases") or []) == 1
                and st["releases"][0].get("result") is None)
            add("target2_never_skipped_or_failed", not any(
                same_identity(item.get("identity") or {}, TARGET2)
                for item in (facts.get("fit_failed") or []) + (facts.get("fit_skipped") or [])))
            failed = facts.get("fit_failed") or []
            want = u"abort-unverified" if scenario == 2 else u"not-committed"
            add("target1_failed_as_%s" % want.replace("-", "_"), len(failed) == 1
                and same_identity(failed[0].get("identity") or {}, TARGET1)
                and failed[0].get("committed") is False and failed[0].get("verification") == want)
            add("nothing_committed", facts.get("fit_committed_order") == [])
            unattempted = facts.get("fit_unattempted") or []
            add("target2_unattempted", len(unattempted) == 1 and same_identity(unattempted[0], TARGET2))
        return checks

    def mode_state(folder, leaf, gate, scenario):
        module, ns, app, window = cpm()
        st = get_state()
        if app.activeModalWidget() is not None:
            raise RuntimeError("a dialog is still open: click its OK first, then run the harness again")
        facts = window_facts(window)
        if facts["operation"] is not None or facts["fit_active"] or facts["fit_stage_running"]:
            raise RuntimeError("CPM is still busy; wait, then run the harness again")
        arm = read_json(rec_path(folder, scenario, "arm"))
        record = {"schema": "cpm-s4-state-v1", "wall_time": now(), "epoch": time.time(), "campaign": leaf,
                  "gate": gate, "scenario": scenario, "scenario_kind": SCENARIOS[scenario]}
        invalid = []
        record["restored_at_state"] = restore_all(ns, st) if st is not None else []
        if st is None or st.get("campaign") != leaf or st.get("scenario") != scenario:
            invalid.append("no armed harness state in this SFM process for this scenario")
            st = {"originals": {}, "installed": []}
        if st.get("phase") != "fired":
            invalid.append("injection did not complete (phase=%r)" % (st.get("phase"),))
        wrappers_absent = all(not getattr(ns.get(name), WRAP_MARK, False) for name in PINS) and all(
            ns.get(name) is original for name, original in (st.get("originals") or {}).items())
        record["wrappers_absent"] = wrappers_absent
        counters = safe_counters()
        undo = undo_facts(ns)
        scene = scene_snapshot(ns, gate)
        scene_diff = dict((key, differing(arm["scene"][key], scene.get(key) or {})) for key in arm["scene"])
        undo_ok = undo.get("count") == arm["undo"].get("count") and undo.get("desc") == arm["undo"].get("desc")
        record.update({"counters": counters, "undo": undo, "undo_at_arm": arm["undo"], "scene_diff": scene_diff,
                       "window": facts, "injection": st.get("injection"), "fire": st.get("fire"),
                       "releases": st.get("releases"), "stage_opened": st.get("stage_opened"),
                       "stage_id": st.get("stage_id"), "adapter_calls_total": st.get("adapter_calls"), "passthrough_calls": st.get("passthrough"),
                       "harness_errors": st.get("errors") or []})
        checks = expected_checks(gate, scenario, st, st.get("fire"), facts, undo_ok,
                                 not any(scene_diff.values()), counters, wrappers_absent)
        record["checks"] = checks
        failed = [c["check"] for c in checks if not c["ok"]]
        if invalid:
            record["status"] = "INVALID"
            record["invalid"] = invalid
        elif failed or st.get("errors"):
            record["status"] = "RECORDED_CHECK_FAILED"
        else:
            record["status"] = "RECORDED_OK"
        write_once(rec_path(folder, scenario, "state"), record)
        set_state(None)
        label = "%s %s (scenario %d)" % (GATES[gate]["label"], SCENARIOS[scenario], scenario)
        if record["status"] == "RECORDED_OK":
            follow = ("Next: run the harness again to ARM scenario 2." if scenario == 1
                      else "Next: the ordinary follow-up step in the runbook.")
            return "S4 RECORDED OK: %s. %s" % (label, follow)
        if record["status"] == "INVALID":
            return "S4 INVALID: %s -- %s. STOP: close SFM without saving (runbook recovery)." % (
                label, "; ".join(invalid))
        return "S4 CHECK FAILED: %s -- %s. STOP: close SFM without saving (runbook recovery)." % (
            label, ", ".join(failed + (st.get("errors") or [])))

    # ------------------------------------------------------------------- entry
    try:
        folder, leaf, gate = campaign()
        has = dict(((s, k), os.path.exists(rec_path(folder, s, k))) for s in (1, 2) for k in ("arm", "state"))
        if not has[(1, "arm")]:
            message = mode_arm(folder, leaf, gate, 1)
        elif not has[(1, "state")]:
            message = mode_state(folder, leaf, gate, 1)
        elif not has[(2, "arm")] and read_json(rec_path(folder, 1, "state")).get("status") == "RECORDED_OK":
            message = mode_arm(folder, leaf, gate, 2)
        elif has[(2, "arm")] and not has[(2, "state")]:
            message = mode_state(folder, leaf, gate, 2)
        else:
            raise RuntimeError("campaign %s is complete or stopped" % (leaf,))
    except Exception as exc:
        message = "S4 HARNESS REFUSED: %s" % (text(exc),)
        try:
            leftover = get_state()
            module = sys.modules.get(MODULE_KEY)
            if leftover is not None and leftover.get("installed") and module is not None \
                    and leftover.get("phase") != "armed":
                restore_all(module.__dict__, leftover)
        except Exception:
            pass
    show_notice(message)


try:
    _cpm_s4_rollback_harness_v1()
finally:
    try:
        del _cpm_s4_rollback_harness_v1
    except NameError:
        pass
