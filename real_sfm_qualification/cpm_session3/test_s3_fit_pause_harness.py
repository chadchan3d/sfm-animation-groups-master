# -*- coding: utf-8 -*-
"""Offline qualification of the Session 3 Fit pause harness (qualification-only).

Runs the ACTUAL harness file against the ACTUAL R15 launcher + private CPM
application (a real ProdWindow) inside the R15 suite's fake SFM game root, under
real PySide/Qt 4.8 (embedded 2.7.5) and the behavioural Qt 4.8 model (2.7.5 and
3.10). Production code exercised unmodified: ProdWindow.fit_stage's
G18AN_MODAL_DEFER_FIT branch, poll_foreign_modal and the watcher's resume.

Stubbed boundaries only: the scene-read helpers used for value snapshots
(g11a_resolve_target / p01_all_supported_flex_bindings / binding_snapshot), the
canonical broker's counters, and the campaign records the shell would write.
Mocks cannot qualify the real Fit, real DME values or the real authority switch;
those are Session 3's live campaign.

Usage: --phase=run   (internal: --child=<scenario> --qt=<real|model> --root=<dir>)
"""
from __future__ import print_function

import ast
import io
import json
import os
import shutil
import subprocess
import sys
import types

_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(_REPO, "cpm", "convergence", "tests"))
import test_cpm_app_r15_namespace_isolation as r15  # noqa: E402

HARNESS = os.path.join(_THIS, "S3_Fit_Pause_Harness.py")
FIXTURE_ROOT = os.path.join(r15.tempfile.gettempdir(), "cpm_s3_harness_fixture")
G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
G2 = "54413b6ca618f73733b6624e1d2411a6cfb00a24489330ccbfc153760f3486e7"
G1_SIDECAR = "bcd9764105f92ce87fb84053d591ec40c51bc8f482584be1c373c1726305750b"
G2_SIDECAR = "cd370f67bfd4db6a17fdc3d425ffae6934ad223c2f5519eda99e3f5b2264ffe3"
SOURCE = {"animset_name": u"krystal20201", "checksum": -1441261258,
          "model": u"models/fursonas/starfox/krystal/bodies/krystal2020.mdl"}
T1 = {"name": u"assaultsuitbody1", "checksum": -791536511,
      "model": u"models/fursonas/starfox/krystal/cosmetics/assaultsuitbody.mdl"}
T2 = {"name": u"loinclothbra_chadfix_071", "checksum": 480892851,
      "model": u"models/fursonas/starfox/krystal/cosmetics/loinclothbra_chadfix_07.mdl"}
RESULTS = []
c = r15.c


# ---------------------------------------------------------------- child setup
class FakeBroker(object):
    def __init__(self):
        self.leases = 0
        self.unreleased = 0
        self.open = 0

    def outstanding_lease_count(self):
        return self.leases

    def unreleased_lease_count(self):
        return self.unreleased

    def provider_counters(self):
        return {"current_open_provider_count": self.open, "total_provider_opens": 1}


class S3(object):
    def __init__(self, qt_mode, root):
        self.env = r15.Env(qt_mode, root)
        self.cfg = os.path.join(self.env.game, "usermod", "cfg")
        os.makedirs(self.cfg)
        self.g1 = r15._read(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"))
        assert r15._sha(self.g1) == G1
        self.set_master(self.g1)
        self.public = os.path.join(self.env.root, "public")
        self.s3root = os.path.join(self.public, "Documents", "CPM_Session3")
        os.makedirs(self.s3root)
        os.environ["PUBLIC"] = self.public
        self.harness_path = os.path.join(self.env.menu_dir, "S3_Fit_Pause_Harness.py")
        shutil.copyfile(HARNESS, self.harness_path)
        self.broker = FakeBroker()
        runtime = types.ModuleType("sfm_master_authority_productionized.runtime")
        runtime._broker = self.broker
        sys.modules["sfm_master_authority_productionized.runtime"] = runtime
        self.values = {"v": 0.0}
        self.snapshot_error = [False]
        self.env.click()
        self.ns = self.env.module().__dict__
        self.window = self.env.slot()
        self.ns["g11a_resolve_target"] = self._resolve
        self.ns["p01_all_supported_flex_bindings"] = lambda animset: [{"literal": u"BodyFlex"}]
        self.ns["binding_snapshot"] = lambda b: {"literal": b["literal"], "sides": {
            "value": {"source": self.values["v"], "destination": self.values["v"], "evaluated": self.values["v"],
                      "key_count": 1, "key0_time": 0.0, "key0_value": self.values["v"], "is_empty": False}}}
        self.reset_window()
        self.campaign = None

    def _resolve(self, identity):
        if self.snapshot_error[0]:
            raise RuntimeError("injected snapshot failure")
        assert identity["name"] == T1["name"]
        return {"animset": "target1-animset"}

    def set_master(self, data):
        with open(os.path.join(self.cfg, "sfm_defaultanimationgroups.txt"), "wb") as f:
            f.write(data)

    def reset_window(self):
        w = self.window
        for attr in ("fit_stage", "_cpm_s3_wrapper_v1", "poll_foreign_modal"):
            w.__dict__.pop(attr, None)
        w.identity = dict(SOURCE)
        w.scope = {"identity": dict(SOURCE), "authority": {"provider_sha256": G1}}
        w.fit_identity_tokens = [dict(T1), dict(T2)]
        w.fit_generation = 0
        w.fit_active = False
        w.operation = None
        w.fit_stage_running = False
        w.fit_selected_identities = []
        w.fit_committed_order = []
        w.fit_semantic_generation = None
        w.modal_deferred_fit_stage = None
        self.broker.leases = self.broker.unreleased = self.broker.open = 0
        self.values["v"] = 0.0
        self.snapshot_error[0] = False

    def new_campaign(self, leaf, seed=True):
        folder = os.path.join(self.s3root, leaf)
        os.makedirs(folder)
        if seed:
            for name, rec in (("baseline_inventory.json", {"master_sha256": G1}),
                              ("deploy_before_harness.txt", {"files": []}),
                              ("harness_deploy_record.json", {"ok": True})):
                with open(os.path.join(folder, name), "wb") as f:
                    f.write(json.dumps(rec).encode("utf-8"))
        with open(os.path.join(self.s3root, "ACTIVE_CAMPAIGN.txt"), "wb") as f:
            f.write(leaf.encode("utf-8"))
        self.campaign = folder
        return folder

    def run(self):
        """One Scripts-menu run of the deployed harness in SFM's shared host dict."""
        code = compile(r15._read(self.harness_path), self.harness_path, "exec", 0, True)
        buf = io.StringIO() if not r15.PY2 else r15._Py2Buffer()
        old = sys.stdout
        sys.stdout = buf
        try:
            r15._host_exec(code, self.env.host)
        finally:
            sys.stdout = old
        return buf.getvalue()

    def rec(self, name):
        path = os.path.join(self.campaign, name)
        if not os.path.isfile(path):
            return None
        raw = r15._read(path)
        return json.loads(raw.decode("utf-8"))

    def fire_state(self, gen=1):
        w = self.window
        w.fit_active = True
        w.fit_generation = gen
        w.operation = {"kind": u"Clothing Fit", "operation_id": 9, "phase": u"stage"}
        w.fit_selected_identities = [dict(T1), dict(T2)]
        w.fit_committed_order = [dict(T1)]
        w.fit_stage_running = False
        w.fit_semantic_generation = G1
        self.values["v"] = 0.5   # target 1 changed by its commit

    def dialog(self):
        return getattr(self.env.app, "_cpm_s3_pause_dialog_v1", None)

    def clear_modal(self):
        d = self.dialog()
        if d is not None:
            d.hide()
        self.env.pump_timers()
        self.window.modal_yield_active = False
        self.window.scene_activity_suspended = False

    def defer_count(self, gen, index):
        return self.env.log_count(u"G18AN_MODAL_DEFER_FIT generation=%d index=%d" % (gen, index))

    def write_switch_records(self, activate_master=True):
        g2 = self.g1 + b"\n"
        assert r15._sha(g2) == G2
        if activate_master:
            self.set_master(g2)
        for name, rec in (("g2_activation_record.json", {"success": True, "pre_activation_master_sha256": G1,
                                                         "post_activation_master_sha256": G2}),
                          ("post_switch_inventory.json", {"master_sha256": G2, "sidecars": [
                              {"sha256": G1_SIDECAR}, {"sha256": G2_SIDECAR}]})):
            with open(os.path.join(self.campaign, name), "wb") as f:
                f.write(json.dumps(rec).encode("utf-8"))


def armed(s, out):
    return "S3 ARMED" in out and s.rec("harness_arm_record.json") is not None


# -------------------------------------------------------------------- scenarios
def scenario_arm_refusals(s):
    out = s.run()
    c("refuse.no_campaign_pointer", "S3 HARNESS REFUSED" in out and "ACTIVE_CAMPAIGN" in out, out.strip())
    cases = [
        ("fit_active", lambda: setattr(s.window, "fit_active", True)),
        ("operation_active", lambda: setattr(s.window, "operation", {"kind": u"Body Save"})),
        ("master_not_g1", lambda: s.set_master(s.g1 + b"\n")),
        ("lease_held", lambda: setattr(s.broker, "leases", 1)),
        ("unreleased", lambda: setattr(s.broker, "unreleased", 1)),
        ("open_provider", lambda: setattr(s.broker, "open", 1)),
        ("scope_not_g1", lambda: s.window.scope["authority"].__setitem__("provider_sha256", G2)),
        ("wrong_source", lambda: s.window.identity.__setitem__("model", u"models/other.mdl")),
        ("target_missing", lambda: setattr(s.window, "fit_identity_tokens", [dict(T1)])),
        ("snapshot_fails", lambda: s.snapshot_error.__setitem__(0, True)),
        ("plan_record_exists", lambda: open(os.path.join(s.campaign, "g2_plan_record.json"), "wb").close()),
        ("deploy_record_missing", lambda: os.remove(os.path.join(s.campaign, "harness_deploy_record.json"))),
    ]
    for i, (label, perturb) in enumerate(cases):
        s.reset_window()
        s.set_master(s.g1)
        s.new_campaign("R%02d" % i)
        perturb()
        out = s.run()
        c("refuse.arm_%s" % label, "S3 HARNESS REFUSED" in out and s.rec("harness_arm_record.json") is None
          and "fit_stage" not in s.window.__dict__, out.strip()[-200:])
    s.reset_window()
    s.set_master(s.g1)
    s.new_campaign("OK")
    out = s.run()
    c("arm.ok", armed(s, out) and "fit_stage" in s.window.__dict__, out.strip())
    arm = s.rec("harness_arm_record.json")
    c("arm.record_fields", arm["fires_on"] == {"generation": 1, "index": 1} and arm["live_master_sha256"] == G1
      and arm["target1_pre_fit"]["BodyFlex"]["value"]["source"] == 0.0 and arm["broker"]["outstanding_leases"] == 0)
    out = s.run()
    c("refuse.rearm_without_pause", "S3 HARNESS REFUSED" in out and "inconsistent" in out, out.strip())


def scenario_valid_pause(s):
    s.new_campaign("S3")
    s.run()
    cfg_before = sorted(os.listdir(s.cfg))
    # Index 0 and other generations pass straight through to production.
    s.fire_state(gen=1)
    s.window.scene_activity_suspended = True
    s.window.fit_stage(1, 0)
    c("passthrough.index0_reaches_production_defer", s.window.modal_deferred_fit_stage == (1, 0)
      and s.defer_count(1, 0) == 1 and s.rec("harness_pause_record.json") is None and "fit_stage" in s.window.__dict__)
    s.window.scene_activity_suspended = False
    s.window.modal_deferred_fit_stage = None
    s.window.fit_stage(7, 1)
    c("passthrough.other_generation_not_intercepted", s.rec("harness_pause_record.json") is None
      and "fit_stage" in s.window.__dict__ and s.dialog() is None)
    # Target-2 entry of the armed Fit.
    s.fire_state(gen=1)
    s.window.fit_stage(1, 1)
    pause = s.rec("harness_pause_record.json")
    d = s.dialog()
    c("pause.valid", pause is not None and pause["status"] == "PAUSED_VALID" and pause["failures"] == [], pause and pause.get("failures"))
    c("pause.wrapper_disarmed", "fit_stage" not in s.window.__dict__ and "_cpm_s3_wrapper_v1" not in s.window.__dict__)
    c("pause.modal_gate_facts", pause["modal"] == {"dialog_is_active_modal": True, "modal_yield_active": True,
                                                   "scene_activity_suspended": True})
    c("pause.dialog_is_active_modal", d is not None and s.env.app.activeModalWidget() is d)
    c("pause.production_yield_and_defer", s.window.modal_yield_active and s.window.scene_activity_suspended
      and s.window.modal_deferred_fit_stage == (1, 1) and s.defer_count(1, 1) == 1
      and s.env.log_count(u"G18AN_MODAL_YIELD_ENTER") == 1 and not s.window.isVisible())
    c("pause.original_invoked_once", pause["original_invoked"] is True and pause["modal_deferred_fit_stage"] == [1, 1])
    c("pause.boundary_recorded", pause["broker"] == {"broker_id": pause["broker"]["broker_id"], "outstanding_leases": 0,
                                                     "unreleased_leases": 0, "open_providers": 0}
      and pause["live_master_sha256"] == G1 and pause["target1_changed_literals"] == [u"BodyFlex"]
      and pause["fit_before"]["gfit"] == G1 and not pause["fit_before"]["fit_stage_running"])
    if s.env.model is None:
        buttons = [b for b in d.findChildren(s.env.QtGui.QPushButton)]
        c("pause.continue_enabled", len(buttons) == 1 and buttons[0].isEnabled())
    button = [b for b in d.findChildren(s.env.QtGui.QPushButton)][0] if s.env.model is None else None
    clicker = (lambda: button.click()) if button is not None else _model_click(s)
    # Continue refused while the Master is still G1.
    clicker()
    s.env.settle(2)
    c("continue.refused_without_exact_g2", s.rec("harness_resume_record.json") is None
      and s.env.app.activeModalWidget() is d and s.window.modal_deferred_fit_stage == (1, 1))
    # Valid switch records but the live Master still G1 -> still refused.
    s.write_switch_records(activate_master=False)
    clicker()
    s.env.settle(2)
    c("continue.refused_while_live_master_g1", s.rec("harness_resume_record.json") is None
      and s.env.app.activeModalWidget() is d)
    # Exact G2 proven -> Continue closes the dialog; production resumes target 2.
    s.set_master(s.g1 + b"\n")
    calls = []
    s.window.fit_stage = lambda g, i: calls.append((g, i))
    clicker()
    resume = s.rec("harness_resume_record.json")
    c("continue.records_exact_g2", resume is not None and resume["live_master_sha256"] == G2)
    s.env.pump_timers(6)
    c("resume.production_watcher_resumes_target2", calls == [(1, 1)] and s.env.log_count(u"G18AN_MODAL_YIELD_EXIT") == 1
      and s.env.log_count(u"G18AN_MODAL_RESUME_FIT generation=1 index=1") == 1 and s.env.app.activeModalWidget() is None,
      [calls, s.env.log_count(u"G18AN_MODAL_YIELD_EXIT")])
    s.window.__dict__.pop("fit_stage", None)
    c("authority.harness_wrote_no_cfg_files", sorted(os.listdir(s.cfg)) == cfg_before)
    # SNAPSHOT after Undo (values back to pre-Fit).
    s.window.fit_active = False
    s.window.operation = None
    s.values["v"] = 0.0
    out = s.run()
    undo = s.rec("harness_undo_snapshot.json")
    c("snapshot.written_restored", "S3 UNDO SNAPSHOT WRITTEN" in out and "RESTORED" in out
      and undo["undo_restored_pre_fit"] is True and undo["differs_from_pre_fit"] == [], out.strip())
    out = s.run()
    c("refuse.after_complete", "S3 HARNESS REFUSED" in out and "already complete" in out, out.strip())


def _model_click(s):
    def click():
        d = s.dialog()
        for child in d._model_children:
            for grandchild in getattr(child, "_model_children", []):
                pass
        buttons = [w for w in s.env.model.widgets if type(w).__name__ == "QPushButton" and w._model_parent is None]
        buttons[-1].click()
    return click


def scenario_snapshot_not_restored(s):
    s.new_campaign("S3")
    s.run()
    s.fire_state(gen=1)
    s.window.fit_stage(1, 1)
    s.write_switch_records()
    s.window.fit_stage = lambda g, i: None
    if s.env.model is None:
        [b for b in s.dialog().findChildren(s.env.QtGui.QPushButton)][0].click()
    else:
        _model_click(s)()
    s.env.pump_timers(6)
    s.window.__dict__.pop("fit_stage", None)
    s.window.fit_active = False
    s.window.operation = None
    s.values["v"] = 0.5   # Undo did not restore
    out = s.run()
    undo = s.rec("harness_undo_snapshot.json")
    c("snapshot.not_restored_reported", "S3 UNDO SNAPSHOT WRITTEN" in out and "does NOT match" in out
      and undo["undo_restored_pre_fit"] is False and undo["differs_from_pre_fit"] == [u"BodyFlex"])


def scenario_boundary_failures(s):
    cases = [
        ("committed_wrong", lambda: setattr(s.window, "fit_committed_order", []), "committed targets"),
        ("selected_wrong", lambda: setattr(s.window, "fit_selected_identities", [dict(T2), dict(T1)]), "selected targets"),
        ("stage_running", lambda: setattr(s.window, "fit_stage_running", True), "fit_stage_running"),
        ("lease", lambda: setattr(s.broker, "leases", 1), "outstanding_leases = 1"),
        ("unreleased", lambda: setattr(s.broker, "unreleased", 1), "unreleased_leases = 1"),
        ("open_provider", lambda: setattr(s.broker, "open", 1), "open_providers = 1"),
        ("gfit_not_g1", lambda: setattr(s.window, "fit_semantic_generation", G2), "Gfit is not G1"),
        ("target1_unchanged", lambda: s.values.__setitem__("v", 0.0), "unchanged by the commit"),
        ("master_not_g1", lambda: s.set_master(s.g1 + b"\n"), "live Master is not G1"),
        ("snapshot_error", lambda: s.snapshot_error.__setitem__(0, True), "boundary gate error"),
        ("operation_not_fit", lambda: setattr(s.window, "operation", {"kind": u"Body Save"}), "Clothing Fit operation"),
    ]
    for i, (label, perturb, expect) in enumerate(cases):
        s.clear_modal()
        s.reset_window()
        s.set_master(s.g1)
        s.new_campaign("B%02d" % i)
        out = s.run()
        before = s.defer_count(1, 1)
        s.fire_state(gen=1)
        perturb()
        s.window.fit_stage(1, 1)
        pause = s.rec("harness_pause_record.json")
        c("boundary.%s.invalid_target2_not_invoked" % label, armed(s, out) and pause is not None
          and pause["status"] == "INVALID" and pause["original_invoked"] is False
          and any(expect in f for f in pause["failures"]) and s.window.modal_deferred_fit_stage is None
          and s.defer_count(1, 1) == before and "modal" not in pause,
          pause and pause.get("failures"))
        c("boundary.%s.wrapper_disarmed" % label, "fit_stage" not in s.window.__dict__)
        out2 = s.run()
        c("boundary.%s.harness_then_refuses" % label, "S3 HARNESS REFUSED" in out2)


def scenario_modal_failures(s):
    QtGui, QtCore = s.env.QtGui, s.env.QtCore
    real_poll = type(s.window).poll_foreign_modal
    others = []

    def other_modal_on_top():
        other = QtGui.QDialog()
        other.setWindowModality(QtCore.Qt.ApplicationModal)
        other.show()
        others.append(other)
        real_poll(s.window)
    cases = [("no_watcher_effect", lambda: None, "modal_yield_active is False"),
             ("other_modal_on_top", other_modal_on_top, "dialog_is_active_modal is False")]
    for i, (label, poll, expect) in enumerate(cases):
        s.clear_modal()
        s.reset_window()
        s.new_campaign("A%02d" % i)
        s.run()
        before = s.defer_count(1, 1)
        s.fire_state(gen=1)
        s.window.poll_foreign_modal = poll
        s.window.fit_stage(1, 1)
        pause = s.rec("harness_pause_record.json")
        c("modal.%s.invalid_target2_not_invoked" % label, pause is not None and pause["status"] == "INVALID"
          and pause["original_invoked"] is False and any(expect in f for f in pause["failures"])
          and s.window.modal_deferred_fit_stage is None and s.defer_count(1, 1) == before,
          pause and pause.get("failures"))
        s.window.__dict__.pop("poll_foreign_modal", None)
        for o in others:
            o.hide()
        del others[:]


SCENARIOS = [("arm_refusals", scenario_arm_refusals), ("valid_pause", scenario_valid_pause),
             ("snapshot_not_restored", scenario_snapshot_not_restored),
             ("boundary_failures", scenario_boundary_failures), ("modal_failures", scenario_modal_failures)]


def child_main(scenario, qt_mode, root):
    try:
        s = S3(qt_mode, root)
        dict(SCENARIOS)[scenario](s)
    except BaseException:
        import traceback
        c("scenario_completed", False, traceback.format_exc()[-1500:])
    else:
        c("scenario_completed", True)
    sys.stdout.write("R15_CHILD_RESULT " + json.dumps(r15.CHILD_RESULTS) + "\n")
    sys.stdout.flush()


# ------------------------------------------------------------------ static
def check(name, ok, value=None):
    RESULTS.append((name, bool(ok), value))
    print("[%s] %s" % ("PASS" if ok else "FAIL", name))
    if not ok and value is not None:
        print("      value: %r" % (value,))


def static_harness():
    raw = r15._read(HARNESS)
    check("static.ascii_lf", all(ord(ch) < 128 for ch in raw.decode("latin-1")) and b"\r" not in raw)
    tree = ast.parse(raw)
    check("static.one_function_and_guarded_call", len(tree.body) == 2 and isinstance(tree.body[0], ast.FunctionDef)
          and tree.body[0].name == "_cpm_s3_fit_pause_harness_v1" and ast.get_docstring(tree) is None)
    body = u"\n".join(l for l in raw.decode("ascii").splitlines() if not l.lstrip().startswith("#"))
    for label, token in (("authority_activation", "perform_g1_to_g2"), ("movefile", "MoveFileEx"),
                         ("publisher", "publish"), ("remove", "os.remove"), ("rename", "os.rename"),
                         ("unlink", "unlink"), ("shutil", "shutil"), ("sys_path", "sys.path"),
                         ("broker_acquire", "acquire"), ("adapter", "prod_cpm_"), ("exec", "exec(")):
        check("static.no_%s" % label, token not in body)
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"
              and len(n.args) > 1 and (getattr(n.args[1], "s", None) or getattr(n.args[1], "value", None)) == "wb"]
    check("static.single_write_site_is_write_once", len(writes) == 1)
    check("static.original_called_only_after_modal_gate", body.index("original(window, generation, index)")
          > body.index("modal gate: %s is False"))


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if "--child" in args:
        child_main(args["--child"], args["--qt"], args["--root"])
        return
    print("Interpreter: %s" % sys.version.split()[0])
    static_harness()
    modes = (["real"] if r15.qt_available() else []) + ["model"]
    print("Qt modes: %s" % ", ".join(modes))
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    for mode in modes:
        for name, _ in SCENARIOS:
            root = os.path.join(FIXTURE_ROOT, "%s_%s" % (mode, name))
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=%s" % name,
                                     "--qt=%s" % mode, "--root=%s" % root],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
            output = proc.communicate()[0].decode("utf-8", "replace")
            records = None
            for line in output.splitlines():
                if line.startswith("R15_CHILD_RESULT "):
                    records = json.loads(line[len("R15_CHILD_RESULT "):])
            if records is None:
                check("%s.%s.child_reported" % (mode, name), False, output[-2000:])
                continue
            for cname, ok, value in records:
                check("%s.%s.%s" % (mode, name, cname), ok, value)
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
