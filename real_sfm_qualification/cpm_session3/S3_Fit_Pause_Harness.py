# -*- coding: ascii -*-
# CPM real-SFM Session 3 -- Clothing Fit generation-interruption pause harness.
#
# QUALIFICATION-ONLY. Not product code. Deployed temporarily to the ChadChan3D
# Scripts menu for Session 3 and removed afterwards (SESSION3_RUNBOOK.md).
#
# One state-driven menu script. The campaign folder is named by
# %PUBLIC%\Documents\CPM_Session3\ACTIVE_CAMPAIGN.txt.
#   no harness_arm_record.json                         -> ARM
#   arm + valid pause + resume records, no undo record -> SNAPSHOT
#   anything else                                      -> REFUSE
# Visible result: "S3 ARMED", "S3 UNDO SNAPSHOT WRITTEN" or "S3 HARNESS REFUSED".
#
# ARM installs a one-shot wrapper as an instance attribute on the live CPM
# window's fit_stage. Index 0 passes straight through. At target-2 entry
# (index 1 of the next Fit) the wrapper disarms itself, then:
#   B. gates the target-1 boundary (committed target 1, no stage running,
#      leases / unreleased / open providers 0, Gfit == G1, live Master G1,
#      target-1 values changed by the commit);
#   A. shows a parentless application-modal pause dialog and runs CPM's own
#      foreign-modal watcher once (poll_foreign_modal), then requires: the
#      dialog is the active modal widget, modal_yield_active and
#      scene_activity_suspended are True;
#   only then calls the UNMODIFIED ProdWindow.fit_stage(window, generation, 1),
#   which takes production's G18AN_MODAL_DEFER_FIT branch.
# Any failure records INVALID and never invokes target 2.
#
# The harness never writes authority files and never calls the broker; it only
# reads broker counters, CPM window fields and DME values (read-only helpers of
# the private CPM module). Continue is enabled only on a valid pause and closes
# the dialog only after exact G2 activation is proven by the campaign records.
#
# (Comments, not a docstring: a module docstring would rebind __doc__ in SFM's
# shared Scripts-menu namespace.)


def _cpm_s3_fit_pause_harness_v1():
    import datetime
    import hashlib
    import json
    import numbers
    import os
    import sys
    import time
    import traceback

    from PySide import QtCore
    from PySide import QtGui

    G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
    G2 = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
    G1_SIDECAR = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
    G2_SIDECAR = "cd370f67bfd4db6a17fdc3d425ffae6934ad223c2f5519eda99e3f5b2264ffe3"
    MODULE_KEY = "chadchan3d_cpm_app"
    LOADER = "cpm-private-loader-v1"
    WINDOW_ATTR = "_sfm_character_slider_preset_tool_window"
    RUNTIME = "sfm_master_authority_productionized.runtime"
    DIALOG_ATTR = "_cpm_s3_pause_dialog_v1"
    NOTICE_ATTR = "_cpm_s3_harness_notice_v1"
    WRAPPER_MARK = "_cpm_s3_wrapper_v1"
    SOURCE = {"animset_name": u"krystal20201", "checksum": -1441261258,
              "model": u"models/fursonas/starfox/krystal/bodies/krystal2020.mdl"}
    TARGET1 = {"name": u"assaultsuitbody1", "checksum": -791536511,
               "model": u"models/fursonas/starfox/krystal/cosmetics/assaultsuitbody.mdl"}
    TARGET2 = {"name": u"loinclothbra_chadfix_071", "checksum": 480892851,
               "model": u"models/fursonas/starfox/krystal/cosmetics/loinclothbra_chadfix_07.mdl"}
    EPS = 1.0e-5
    state = {}

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

    def show_notice(message):
        try:
            sys.stdout.write("[CPM S3 harness] %s\n" % (message,))
        except Exception:
            pass
        try:
            app = QtGui.QApplication.instance()
            box = getattr(app, NOTICE_ATTR, None)
            if box is None:
                box = QtGui.QMessageBox()
                box.setWindowTitle("CPM Session 3 harness")
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

    def game_root():
        return os.path.dirname(os.path.abspath(sys.executable))

    def master_path():
        return os.path.join(game_root(), "usermod", "cfg", "sfm_defaultanimationgroups.txt")

    def campaign_dir():
        public = os.environ.get("PUBLIC")
        if not public:
            raise RuntimeError("PUBLIC is not set")
        root = os.path.join(public, "Documents", "CPM_Session3")
        pointer = os.path.join(root, "ACTIVE_CAMPAIGN.txt")
        if not os.path.isfile(pointer):
            raise RuntimeError("no ACTIVE_CAMPAIGN.txt (run S3-Activate)")
        with open(pointer, "rb") as f:
            leaf = f.read().decode("utf-8").strip()
        if not leaf or os.sep in leaf or "/" in leaf or leaf in (".", ".."):
            raise RuntimeError("malformed ACTIVE_CAMPAIGN.txt")
        folder = os.path.join(root, leaf)
        if not os.path.isdir(folder):
            raise RuntimeError("campaign folder missing: %s" % (leaf,))
        return folder

    def paths(folder):
        return dict((k, os.path.join(folder, v)) for k, v in (
            ("baseline", "baseline_inventory.json"), ("deploy", "deploy_before_harness.txt"),
            ("deployed", "harness_deploy_record.json"), ("arm", "harness_arm_record.json"),
            ("pause", "harness_pause_record.json"), ("resume", "harness_resume_record.json"),
            ("undo", "harness_undo_snapshot.json"), ("plan", "g2_plan_record.json"),
            ("publication", "g2_publication_record.json"), ("activation", "g2_activation_record.json"),
            ("post_switch", "post_switch_inventory.json")))

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
        return ns, app, window, cls

    def broker_counters():
        runtime = sys.modules.get(RUNTIME)
        broker = getattr(runtime, "_broker", None) if runtime is not None else None
        if broker is None:
            raise RuntimeError("canonical broker not constructed")
        return {"broker_id": "0x%x" % id(broker),
                "outstanding_leases": int(broker.outstanding_lease_count()),
                "unreleased_leases": int(broker.unreleased_lease_count()),
                "open_providers": int(broker.provider_counters().get("current_open_provider_count"))}

    def same_target(a, b):
        return (text(a.get("name")) == text(b.get("name")) and text(a.get("model")) == text(b.get("model"))
                and int(a.get("checksum")) == int(b.get("checksum")))

    def snapshot_target1(ns):
        """Read-only per-binding values of target 1 via CPM's own read helpers."""
        row = ns["g11a_resolve_target"](dict(TARGET1))
        bindings = ns["p01_all_supported_flex_bindings"](row["animset"])
        out = {}
        for binding in bindings:
            snap = ns["binding_snapshot"](binding)
            sides = {}
            for side_name, side in sorted((snap.get("sides") or {}).items()):
                sides[text(side_name)] = dict(
                    (k, side.get(k)) for k in ("source", "destination", "evaluated", "key_count",
                                                "key0_time", "key0_value", "is_empty") if k in side)
            out[text(snap.get("literal"))] = sides
        if not out:
            raise RuntimeError("target 1 has no readable flex bindings")
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
        """Literals whose recorded per-side values differ (tolerance 1e-5)."""
        return [literal for literal in sorted(set(a) | set(b))
                if not same_values(a.get(literal), b.get(literal))]

    def fit_facts(window):
        return {"fit_active": bool(window.fit_active), "fit_generation": int(window.fit_generation),
                "operation_kind": text((window.operation or {}).get("kind")) if window.operation is not None else None,
                "fit_stage_running": bool(window.fit_stage_running),
                "gfit": text(getattr(window, "fit_semantic_generation", None)),
                "committed": [dict(item) for item in (window.fit_committed_order or [])],
                "selected": [dict(item) for item in (window.fit_selected_identities or [])],
                "modal_yield_active": bool(window.modal_yield_active),
                "scene_activity_suspended": bool(window.scene_activity_suspended),
                "modal_deferred_fit_stage": window.modal_deferred_fit_stage,
                "closing_requested": bool(window.closing_requested)}

    # ------------------------------------------------------------- pause/resume
    def make_dialog(app, valid_text, invalid):
        dialog = QtGui.QDialog()
        dialog.setObjectName("cpm_s3_pause_dialog")
        dialog.setWindowTitle("CPM Session 3 -- INVALID" if invalid else "CPM Session 3 -- Fit paused")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        layout = QtGui.QVBoxLayout(dialog)
        label = QtGui.QLabel(valid_text)
        label.setWordWrap(True)
        layout.addWidget(label)
        button = QtGui.QPushButton("Continue")
        button.setEnabled(False)
        layout.addWidget(button)
        dialog.setMinimumWidth(460)
        setattr(app, DIALOG_ATTR, dialog)
        return dialog, label, button

    def on_continue():
        dialog, label = state.get("dialog"), state.get("label")
        p = state["paths"]
        try:
            if os.path.exists(p["resume"]):
                return
            problems = []
            live = sha_file(master_path())
            if live != G2:
                problems.append("live Master is not exact G2 (%s)" % live[:12])
            if not os.path.isfile(p["activation"]):
                problems.append("g2_activation_record.json missing")
            else:
                act = read_json(p["activation"])
                if not (act.get("success") is True and act.get("pre_activation_master_sha256") == G1
                        and act.get("post_activation_master_sha256") == G2):
                    problems.append("activation record does not prove G1 -> exact G2")
            if not os.path.isfile(p["post_switch"]):
                problems.append("post_switch_inventory.json missing")
            else:
                inv = read_json(p["post_switch"])
                sidecars = sorted(text(s.get("sha256")).lower() for s in inv.get("sidecars") or [])
                if inv.get("master_sha256") != G2 or sidecars != sorted([G1_SIDECAR, G2_SIDECAR]):
                    problems.append("post-switch inventory is not exact G2")
            if problems:
                label.setText(u"Continue REFUSED -- the Fit stays paused.\n\n" + u"\n".join(problems)
                              + u"\n\nIf S3-Switch printed STOP: do NOT continue. Close SFM without saving "
                                u"and follow the shell's recovery instruction.")
                return
            write_once(p["resume"], {"schema": "cpm-s3-resume-v1", "wall_time": now(), "epoch": time.time(),
                                     "live_master_sha256": live, "activation_record_sha256": sha_file(p["activation"]),
                                     "post_switch_inventory_sha256": sha_file(p["post_switch"])})
            dialog.hide()
            sys.stdout.write("[CPM S3 harness] S3 RESUMED: exact G2 proven; CPM resumes the Fit.\n")
        except Exception as exc:
            try:
                label.setText(u"Continue REFUSED -- harness error: %s" % (text(exc),))
            except Exception:
                pass

    def intercept(original, window, generation, index, arm):
        p = state["paths"]
        failures = []
        record = {"schema": "cpm-s3-pause-v1", "wall_time": now(), "epoch": time.time(),
                  "generation": generation, "index": index, "original_invoked": False}
        ns, app = state["ns"], QtGui.QApplication.instance()
        # --- B: target-1 boundary -------------------------------------------
        try:
            facts = fit_facts(window)
            record["fit_before"] = facts
            if not facts["fit_active"] or facts["operation_kind"] != u"Clothing Fit":
                failures.append("Fit not active as a Clothing Fit operation")
            if len(facts["selected"]) != 2 or not same_target(facts["selected"][0], TARGET1) \
                    or not same_target(facts["selected"][1], TARGET2):
                failures.append("selected targets are not exactly [target 1, target 2]")
            if len(facts["committed"]) != 1 or not same_target(facts["committed"][0], TARGET1):
                failures.append("committed targets are not exactly [target 1]")
            if facts["fit_stage_running"]:
                failures.append("fit_stage_running is True")
            if facts["gfit"] != G1:
                failures.append("Gfit is not G1")
            counters = broker_counters()
            record["broker"] = counters
            for key in ("outstanding_leases", "unreleased_leases", "open_providers"):
                if counters[key] != 0:
                    failures.append("%s = %d" % (key, counters[key]))
            live = sha_file(master_path())
            record["live_master_sha256"] = live
            if live != G1:
                failures.append("live Master is not G1")
            post = snapshot_target1(ns)
            record["target1_post_commit"] = post
            changed = differing(arm["target1_pre_fit"], post)
            record["target1_changed_literals"] = changed
            if not changed:
                failures.append("target-1 values unchanged by the commit")
        except Exception:
            failures.append("boundary gate error: " + traceback.format_exc()[-600:])
        if failures:
            record["status"] = "INVALID"
            record["failures"] = failures
            write_once(p["pause"], record)
            dialog, label, button = make_dialog(app, u"INVALID -- the boundary gate failed; target 2 was NOT "
                                                     u"invoked.\n\nDo NOT run S3-Switch. Close SFM without saving, "
                                                     u"then run S2-VerifyUntouched.\n\n" + u"\n".join(failures), True)
            state["dialog"] = dialog
            dialog.show()
            return
        # --- A: fail-closed modal establishment -----------------------------
        dialog, label, button = make_dialog(app, u"Establishing the Session 3 pause ...", False)
        state["dialog"], state["label"], state["button"] = dialog, label, button
        try:
            dialog.show()
            window.poll_foreign_modal()
            modal_facts = {"dialog_is_active_modal": app.activeModalWidget() is dialog,
                           "modal_yield_active": bool(window.modal_yield_active),
                           "scene_activity_suspended": bool(window.scene_activity_suspended)}
            record["modal"] = modal_facts
            for key, ok in sorted(modal_facts.items()):
                if not ok:
                    failures.append("modal gate: %s is False" % key)
        except Exception:
            failures.append("modal gate error: " + traceback.format_exc()[-600:])
        if failures:
            record["status"] = "INVALID"
            record["failures"] = failures
            write_once(p["pause"], record)
            label.setText(u"INVALID -- the modal pause was not established; target 2 was NOT invoked.\n\n"
                          u"Do NOT run S3-Switch. Close SFM without saving, then run S2-VerifyUntouched.\n\n"
                          + u"\n".join(failures))
            dialog.setWindowTitle("CPM Session 3 -- INVALID")
            return
        # --- production deferral (unmodified fit_stage) ----------------------
        try:
            record["original_invoked"] = True
            original(window, generation, index)
            deferred = window.modal_deferred_fit_stage
            record["modal_deferred_fit_stage"] = deferred
            if tuple(deferred or ()) != (generation, index):
                failures.append("production did not defer target 2: %r" % (deferred,))
            record["fit_after"] = fit_facts(window)
        except Exception:
            failures.append("deferral error: " + traceback.format_exc()[-600:])
        record["status"] = "INVALID" if failures else "PAUSED_VALID"
        record["failures"] = failures
        write_once(p["pause"], record)
        if failures:
            label.setText(u"INVALID -- production deferral not proven.\n\nDo NOT run S3-Switch. Close SFM "
                          u"without saving, then run S2-VerifyUntouched.\n\n" + u"\n".join(failures))
            dialog.setWindowTitle("CPM Session 3 -- INVALID")
            return
        label.setText(u"S3 PAUSED (valid). Target 1 committed; target 2 is deferred by CPM.\n\n"
                      u"In the shell run:  S3-Switch $E3\n"
                      u"Wait for S2 PHASE A OK and S2 G2 ACTIVE OK, then click Continue.\n\n"
                      u"If the shell prints STOP: do NOT click Continue. Close SFM without saving and "
                      u"follow the shell's instruction.")
        button.setEnabled(True)
        button.clicked.connect(on_continue)
        sys.stdout.write("[CPM S3 harness] S3 PAUSED (valid)\n")

    # ------------------------------------------------------------------- modes
    def mode_arm(folder, p):
        ns, app, window, cls = cpm()
        problems = []
        for key in ("baseline", "deploy", "deployed"):
            if not os.path.isfile(p[key]):
                problems.append("%s record missing" % key)
        for key in ("plan", "publication", "activation", "post_switch", "pause", "resume", "undo"):
            if os.path.exists(p[key]):
                problems.append("%s record already exists" % key)
        if WRAPPER_MARK in window.__dict__ or "fit_stage" in window.__dict__:
            problems.append("a fit_stage wrapper is already installed")
        live = sha_file(master_path())
        if live != G1:
            problems.append("live Master is not G1")
        if os.path.isfile(p["baseline"]) and read_json(p["baseline"]).get("master_sha256") != G1:
            problems.append("baseline inventory is not G1")
        facts = fit_facts(window)
        if facts["fit_active"] or window.operation is not None or facts["fit_stage_running"]:
            problems.append("CPM is busy (Fit or operation active)")
        if facts["closing_requested"] or facts["modal_yield_active"] or facts["scene_activity_suspended"]:
            problems.append("CPM window is closing or yielding")
        if app.activeModalWidget() is not None:
            problems.append("a modal dialog is active")
        identity = window.identity or {}
        if not (text(identity.get("model")) == SOURCE["model"] and int(identity.get("checksum") or 0) == SOURCE["checksum"]):
            problems.append("selected model is not the Session 3 source (krystal20201)")
        scope = window.scope or {}
        if text((scope.get("authority") or {}).get("provider_sha256")) != G1:
            problems.append("selected scope is not G1")
        tokens = [dict(t) for t in (window.fit_identity_tokens or [])]
        for target, label in ((TARGET1, "target 1"), (TARGET2, "target 2")):
            if not any(same_target(t, target) for t in tokens):
                problems.append("%s is not a Fit candidate" % label)
        counters = None
        try:
            counters = broker_counters()
            for key in ("outstanding_leases", "unreleased_leases", "open_providers"):
                if counters[key] != 0:
                    problems.append("%s = %d" % (key, counters[key]))
        except Exception as exc:
            problems.append(text(exc))
        pre = None
        try:
            pre = snapshot_target1(ns)
        except Exception as exc:
            problems.append("target-1 snapshot failed: %s" % text(exc))
        if problems:
            raise RuntimeError("; ".join(problems))
        arm = {"schema": "cpm-s3-arm-v1", "wall_time": now(), "epoch": time.time(), "pid": os.getpid(),
               "campaign": os.path.basename(folder), "live_master_sha256": live,
               "module": {"id": "0x%x" % id(sys.modules[MODULE_KEY]), "run_id": text(ns.get("PROD_RUN_ID")),
                          "build_sha256": text(ns.get("__chadchan3d_cpm_build_sha256__"))},
               "window_id": "0x%x" % id(window), "fit_generation_at_arm": int(window.fit_generation),
               "fires_on": {"generation": int(window.fit_generation) + 1, "index": 1},
               "source": SOURCE, "target1": TARGET1, "target2": TARGET2, "broker": counters,
               "target1_pre_fit": pre}
        write_once(p["arm"], arm)
        original = cls.fit_stage
        fire_generation = int(window.fit_generation) + 1

        def s3_fit_stage(generation, index):
            if index != 1 or generation != fire_generation:
                return original(window, generation, index)
            for attr in ("fit_stage", WRAPPER_MARK):
                window.__dict__.pop(attr, None)
            try:
                return intercept(original, window, generation, index, arm)
            except Exception:
                try:
                    sys.stdout.write("[CPM S3 harness] intercept error (target 2 NOT invoked):\n%s\n"
                                     % traceback.format_exc())
                except Exception:
                    pass
                return None

        state.update({"ns": ns, "paths": p})
        window.fit_stage = s3_fit_stage
        window.__dict__[WRAPPER_MARK] = True
        return "S3 ARMED: next Fit pauses at target 2 (generation %d). Campaign %s." % (
            fire_generation, os.path.basename(folder))

    def mode_snapshot(folder, p):
        ns, app, window, cls = cpm()
        arm, pause = read_json(p["arm"]), read_json(p["pause"])
        if window.fit_active or window.operation is not None:
            raise RuntimeError("CPM is busy; wait for the Fit to end")
        snap = snapshot_target1(ns)
        undo_vs_pre = differing(arm["target1_pre_fit"], snap)
        undo_vs_post = differing(pause["target1_post_commit"], snap)
        restored = not undo_vs_pre and bool(undo_vs_post)
        write_once(p["undo"], {"schema": "cpm-s3-undo-snapshot-v1", "wall_time": now(), "epoch": time.time(),
                               "target1_after_undo": snap, "differs_from_pre_fit": undo_vs_pre,
                               "differs_from_post_commit": undo_vs_post, "undo_restored_pre_fit": restored})
        return "S3 UNDO SNAPSHOT WRITTEN: target 1 %s its pre-Fit values." % (
            "RESTORED to" if restored else "does NOT match")

    # ------------------------------------------------------------------- entry
    try:
        folder = campaign_dir()
        p = paths(folder)
        has = dict((k, os.path.exists(v)) for k, v in p.items())
        if not has["arm"]:
            message = mode_arm(folder, p)
        elif has["pause"] and has["resume"] and not has["undo"] \
                and read_json(p["pause"]).get("status") == "PAUSED_VALID":
            message = mode_snapshot(folder, p)
        else:
            raise RuntimeError("state is inconsistent or already complete (%s)" % (
                ", ".join(sorted(k for k in ("arm", "pause", "resume", "undo") if has[k])) or "none"))
    except Exception as exc:
        message = "S3 HARNESS REFUSED: %s" % (text(exc),)
    show_notice(message)


try:
    _cpm_s3_fit_pause_harness_v1()
finally:
    try:
        del _cpm_s3_fit_pause_harness_v1
    except NameError:
        pass
