# -*- coding: utf-8 -*-
"""Offline qualification of the Session 4 rollback harness (qualification-only).

Runs the ACTUAL harness file against the ACTUAL R15 launcher + private CPM
application (a real ProdWindow) inside the R15 suite's fake SFM game root, under
real PySide/Qt 4.8 (embedded 2.7.5) and the behavioural Qt 4.8 model (2.7.5 and
3.10).

Production code exercised unmodified: ProdWindow.apply_kind/guard,
prod_apply, prod_abort_apply_and_verify, prod_verify_apply_abort_baseline,
prod_live_bindings_for_cached_scope, p03_verify_saved_values,
prod_cpm_authorize_operation, ProdWindow.fit_stage, prod_cpm_open_fit_stage,
prod_apply_match, prod_abort_fit_and_verify, p03_target_matches_baseline,
matches_value, binding_snapshot, fit accounting and the failure dialog.

Stubbed boundaries only (the SFM scene and the authority adapter): side_snapshot,
dme_id, write_side, dm(), same_time_refresh, prod_resolve,
p01_all_supported_flex_bindings, p03_model_animsets, g11a_resolve_target,
g11a_safe_plan, prod_body_source_live_from_baseline, prod_context_token,
prod_validate_context_token, prod_cpm_import_adapter (fake adapter module),
p01_master_path, prod_bs_index_*, and the window's preset-selection helpers.
Mocks cannot qualify real DME Undo/Abort or the real broker; those are
Session 4's live campaigns.

Usage: --phase=run   (internal: --child=<scenario> --qt=<real|model> --root=<dir> [--harness=<path>])
"""
from __future__ import print_function

import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import types

_THIS = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_THIS, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(_REPO, "cpm", "convergence", "tests"))
import test_cpm_app_r15_namespace_isolation as r15  # noqa: E402

HARNESS = os.path.join(_THIS, "CPM_S4_Rollback_Harness.py")
APP = os.path.join(_REPO, "cpm", "app", "SFM_Character_Preset_Manager.py")
FIXTURE_ROOT = os.path.join(r15.tempfile.gettempdir(), "cpm_s4_harness_fixture")
G1 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
APP_SHA = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
MIA = {"animset_name": u"mia1", "checksum": 1153028609, "model": u"models/annoad/foxbase/mia/mia.mdl"}
SOURCE = {"animset_name": u"krystal20201", "checksum": -1441261258,
          "model": u"models/fursonas/starfox/krystal/bodies/krystal2020.mdl"}
T1 = {"name": u"assaultsuitbody1", "checksum": -791536511,
      "model": u"models/fursonas/starfox/krystal/cosmetics/assaultsuitbody.mdl"}
T2 = {"name": u"loinclothbra_chadfix_071", "checksum": 480892851,
      "model": u"models/fursonas/starfox/krystal/cosmetics/loinclothbra_chadfix_07.mdl"}
WRAPPED = ("p03_verify_saved_values", "prod_verify_apply_abort_baseline", "matches_value",
           "p03_target_matches_baseline", "prod_cpm_open_adapter", "prod_cpm_open_fit_stage")
MUTANTS = {
    "predicate_skips_real": ("real = original(*args, **kwargs)             # REAL predicate first",
                             "real = True"),
    "verifier_skips_real": ("real = original(*args, **kwargs)             # REAL verifier first",
                            "real = True"),
}
RESULTS = []
c = r15.c
ANIMSETS = {"mia1": [u"BrowUp", u"Chest", u"Hips"], "src": [u"SrcA", u"SrcB"],
            "t1": [u"FitA", u"FitB"], "t2": [u"LoinA"]}


# ---------------------------------------------------------------- fake scene
class FakeBroker(object):
    def __init__(self):
        self.leases = 0
        self.unreleased = 0
        self.open = 0
        self.opens = 0

    def outstanding_lease_count(self):
        return self.leases

    def unreleased_lease_count(self):
        return self.unreleased

    def provider_counters(self):
        return {"current_open_provider_count": self.open, "total_provider_opens": self.opens,
                "total_provider_closes": self.opens}


class FakeStage(object):
    def __init__(self, broker, generation):
        self.broker = broker
        self.generation = generation
        self.held = True
        broker.leases += 1

    def release(self):
        if self.held:
            self.held = False
            self.broker.leases -= 1
        return None


class Scene(object):
    """DME stand-in: flex values per (animset, literal) plus a native Undo."""

    def __init__(self):
        self.values = {}
        for animset, literals in ANIMSETS.items():
            for i, literal in enumerate(literals):
                self.values[(animset, literal)] = 0.1 * (i + 1)
        self.bindings = {}
        self.undo_open = False
        self.undo_snapshot = None
        self.undo_count = 3
        self.undo_desc = u"Earlier edit"
        self.abort_restores = True
        self.reads = 0
        self.reads_open = 0
        self.reads_after_abort = 0
        self.aborted = False
        self.writes = 0
        self.calls = []
        self.fail_reads_open = False

    def binding(self, animset, literal):
        key = (animset, literal)
        if key not in self.bindings:
            self.bindings[key] = {"literal": literal, "shape": "MONO", "global_key": "%s:%s" % key,
                                  "control": "ctrl:%s:%s" % key,
                                  "sides": [("mono", {"animset": animset, "literal": literal})]}
        return self.bindings[key]

    def side_snapshot(self, control, side):
        self.reads += 1
        if self.undo_open:
            self.reads_open += 1
            if self.fail_reads_open:
                raise RuntimeError("injected scene read failure")
        if self.aborted:
            self.reads_after_abort += 1
        key = "%s:%s" % (side["animset"], side["literal"])
        v = self.values[(side["animset"], side["literal"])]
        return {"source": v, "destination": v, "evaluated": v, "key_count": 1, "is_empty": False,
                "key0_time": 0.0, "key0_value": v, "channel_id": "ch:" + key, "log_id": "log:" + key,
                "layer_id": "layer:" + key, "destination_id": "dst:" + key}

    def write_side(self, binding, side, origin, desired):
        if origin not in ("ONE_KEY_ZERO", "EMPTY"):
            raise RuntimeError("unsupported origin")
        self.values[(side["animset"], side["literal"])] = float(desired)
        self.writes += 1

    # native DataModel
    def StartUndo(self, label, redo):
        self.calls.append(("StartUndo", label))
        self.undo_open = True
        self.aborted = False
        self.undo_snapshot = dict(self.values)
        self.pending = label

    def FinishUndo(self):
        self.calls.append(("FinishUndo",))
        self.undo_open = False
        self.undo_count += 1
        self.undo_desc = self.pending

    def AbortUndoableOperation(self):
        self.calls.append(("Abort",))
        self.undo_open = False
        self.aborted = True
        if self.abort_restores:
            self.values = dict(self.undo_snapshot)

    def IsUndoEnabled(self):
        return True

    def GetUndoItemCount(self):
        return self.undo_count

    def GetUndoDesc(self):
        return self.undo_desc

    def undo(self):
        """Operator Undo of the last committed entry (ordinary Fit only)."""
        self.values = dict(self.last_committed_before)
        self.undo_count -= 1


class FakeAdapterModule(object):
    EXPECTED_API_VERSION = u"1.0.0-b2a"
    EXPECTED_BUILD_ID = u"package-boundary-corrected-2026-09-22"

    class CpmGenerationMismatch(Exception):
        reason = u"generation-mismatch"

    class CpmAuthorityUnavailable(Exception):
        reason = u"unavailable"

    def __init__(self, broker):
        self.broker = broker
        self.opened = 0

    def open_canonical_authority(self, path, is_main_thread_fn=None):
        self.opened += 1
        return FakeAdapter(self.broker)


class FakeAdapter(object):
    def __init__(self, broker):
        self.broker = broker

    def generation_descriptor(self):
        return {"source_sha256": G1, "provider_generation": 1}

    def verify_current_generation(self, expected, literals):
        return {"provider_capture": {"source_sha256": G1, "provider_generation": 1,
                                     "projection_contract": u"cpm_compat_v1"},
                "compatibility_identity": [u"cpm", u"1", u"cpm_compat_v1"]}

    def open_stage(self, expected, literals):
        return FakeStage(self.broker, expected)


# --------------------------------------------------------------- child setup
class S4(object):
    def __init__(self, qt_mode, root, harness=HARNESS):
        harness_bytes = r15._read(harness)          # before the Env's path shim
        self.env = r15.Env(qt_mode, root)
        self.cfg = os.path.join(self.env.game, "usermod", "cfg")
        os.makedirs(self.cfg)
        self.g1 = r15._read(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"))
        assert r15._sha(self.g1) == G1
        self.set_master(self.g1)
        self.public = os.path.join(self.env.root, "public")
        self.s4root = os.path.join(self.public, "Documents", "CPM_Session4")
        os.makedirs(self.s4root)
        os.environ["PUBLIC"] = self.public
        self.harness_path = os.path.join(self.env.menu_dir, "CPM_S4_Rollback_Harness.py")
        with open(self.harness_path, "wb") as f:
            f.write(harness_bytes)
        self.broker = FakeBroker()
        runtime = types.ModuleType("sfm_master_authority_productionized.runtime")
        runtime._broker = self.broker
        sys.modules["sfm_master_authority_productionized.runtime"] = runtime
        sys.modules["sfmApp"].GetHeadTimeInSeconds = lambda: 0.0
        self.env.click()
        self.ns = self.env.module().__dict__
        self.window = self.env.slot()
        self.originals = dict((name, self.ns[name]) for name in WRAPPED)
        self.scene = Scene()
        self.adapter_module = FakeAdapterModule(self.broker)
        self.dialogs = []
        self.install_stubs()
        self.campaign = None

    # -- stubs at the scene / adapter boundary --------------------------------
    def install_stubs(self):
        ns, scene = self.ns, self.scene
        rows = {"mia1": dict(MIA, animset="mia1"), "src": dict(SOURCE, animset="src"),
                "t1": dict(T1, animset="t1"), "t2": dict(T2, animset="t2")}
        ns["side_snapshot"] = scene.side_snapshot
        ns["dme_id"] = lambda obj: u"id:%s" % (obj,)
        ns["write_side"] = scene.write_side
        ns["dm"] = lambda: scene
        ns["same_time_refresh"] = lambda *args: None
        ns["p01_all_supported_flex_bindings"] = lambda animset: [scene.binding(animset, l) for l in ANIMSETS[animset]]
        ns["prod_live_binding_signatures"] = lambda bindings: {"vocabulary_sha256": u"v", "representation_sha256": u"r"}
        ns["prod_binding_descriptor"] = lambda binding: {"literal": binding["literal"], "shape": binding["shape"]}

        def resolve(identity):
            for key in ("mia1", "src"):
                if int(identity.get("checksum")) == rows[key]["checksum"]:
                    return {"animset": key, "gm": None, "model": rows[key]["model"],
                            "checksum": rows[key]["checksum"], "animset_name": rows[key]["animset_name"]}
            raise RuntimeError("unknown model")
        ns["prod_resolve"] = resolve
        ns["p03_model_animsets"] = lambda: [dict(rows["t1"], name=T1["name"]), dict(rows["t2"], name=T2["name"])]
        ns["g11a_resolve_target"] = lambda identity: dict(rows["t1" if identity["name"] == T1["name"] else "t2"])
        ns["prod_context_token"] = lambda identity: {"token": u"ctx", "model": identity.get("model")}
        ns["prod_validate_context_token"] = lambda token: True
        ns["prod_cpm_import_adapter"] = lambda: self.adapter_module
        ns["p01_master_path"] = lambda: os.path.join(self.cfg, "sfm_defaultanimationgroups.txt")
        ns["prod_load_character"] = lambda identity: {}
        if not r15.PY2:
            # The app targets Python 2.7; its perf-diagnostic loggers concatenate
            # bytes under 3.x. Diagnostic-only boundary, stubbed for the 3.10 model
            # run (2.7.5 runs keep them real).
            ns["prod_perf_log"] = lambda *args, **kwargs: None
            ns["astra_perf_timing"] = lambda *args, **kwargs: None
        ns["prod_bs_index_snapshot"] = lambda identity: {"bone_index": {}}
        ns["prod_bs_index_build_plan"] = lambda identity, record, snapshot: {"existing": [], "create": []}
        ns["prod_bs_index_verify_saved"] = lambda record, snapshot: True   # postcommit bone readback (DME)
        ns["prod_body_source_live_from_baseline"] = lambda baseline, scope, authority_context=None, \
            stage_authority=None: {"identity": dict(SOURCE), "provider": stage_authority}
        self.fit_desired = {u"FitA": 0.8, u"FitB": 0.9}
        if self.env.model is not None:
            # The Qt model's QLabel does not retain text; the status label is a
            # display boundary, so record what production writes to it.
            class StatusLabel(object):
                value = u""

                def setText(self, value):
                    StatusLabel.value = value

                def text(self):
                    return StatusLabel.value

                def __getattr__(self, name):
                    return lambda *args, **kwargs: None
            self.window.status = StatusLabel()

        def safe_plan(source, target_row):
            animset = target_row["animset"]
            if animset != "t1":
                raise RuntimeError("Target %r has no established compatible Body mappings." % target_row["name"])
            entries, changed = [], 0
            for literal in ANIMSETS[animset]:
                b = scene.binding(animset, literal)
                snap = ns["binding_snapshot"](b)
                side = b["sides"][0][1]
                desired = self.fit_desired[literal]
                needs = abs(snap["sides"]["mono"]["source"] - desired) > 1e-6
                changed += 1 if needs else 0
                entries.append({"target_binding": b, "target_baseline": snap,
                                "sides": [{"needs_write": needs, "side": side, "side_name": "mono",
                                           "origin": "ONE_KEY_ZERO", "desired": desired,
                                           "baseline": snap["sides"]["mono"]}]})
            return {"identity": dict(T1), "entries": entries, "changed_sides": changed, "warnings": [],
                    "mapping": {"mappings": [1] * len(entries)}}
        ns["g11a_safe_plan"] = safe_plan

    def scope_for(self, identity, animset):
        policy = self.ns["PROD_SEMANTIC_POLICY"]
        revision = self.ns["u"](self.ns["prod_override_revision"]({}))
        descriptors = dict((l, {"literal": l, "shape": "MONO"}) for l in ANIMSETS[animset])
        return {"identity": dict(identity), "live_signature": {"vocabulary_sha256": u"v", "representation_sha256": u"r"},
                "authority": {"provider_sha256": G1, "provider_generation": 1, "semantic_policy_revision": policy,
                              "override_revision": revision},
                "body": descriptors, "expression": dict(descriptors),
                "semantic": {"rows": [{"literal": l} for l in ANIMSETS[animset]]}}

    def set_master(self, data):
        with open(os.path.join(self.cfg, "sfm_defaultanimationgroups.txt"), "wb") as f:
            f.write(data)

    def select(self, gate):
        w = self.window
        w.operation = None
        w.fit_active = False
        w.fit_stage_running = False
        w.closing_requested = False
        w.modal_yield_active = False
        w.scene_activity_suspended = False
        if gate == "A":
            w.identity = dict(MIA)
            w.scope = self.scope_for(MIA, "mia1")
        else:
            w.identity = dict(SOURCE)
            w.scope = self.scope_for(SOURCE, "src")
            w.fit_identity_tokens = [dict(T1), dict(T2)]

    def new_campaign(self, leaf, seed=True):
        folder = os.path.join(self.s4root, leaf)
        os.makedirs(folder)
        if seed:
            for name, rec in (("baseline_inventory.json", {"master_sha256": G1}),
                              ("deploy_before_harness.txt", {"files": []}),
                              ("harness_deploy_record.json", {"ok": True})):
                with open(os.path.join(folder, name), "wb") as f:
                    f.write(json.dumps(rec).encode("utf-8"))
        with open(os.path.join(self.s4root, "ACTIVE_CAMPAIGN.txt"), "wb") as f:
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
        return json.loads(r15._read(path).decode("utf-8"))

    def bindings_original(self):
        return all(self.ns[name] is self.originals[name] for name in WRAPPED)

    def no_wrappers(self):
        return not any(getattr(self.ns.get(name), "_cpm_s4_wrapper_v1", False) for name in WRAPPED)

    def mia(self):
        return dict((l, self.scene.values[("mia1", l)]) for l in ANIMSETS["mia1"])

    def with_modal_closer(self, fn):
        """Real Qt: production dialogs run exec_(); record and close them."""
        if self.env.model is not None:
            return fn()
        QtCore, app = self.env.QtCore, self.env.app

        def closer():
            w = app.activeModalWidget()
            if w is None:
                QtCore.QTimer.singleShot(20, closer)
                return
            try:
                body = w.text() if hasattr(w, "text") else u""
            except Exception:
                body = u""
            self.dialogs.append((r15._TEXT(w.windowTitle()), r15._TEXT(body)))
            w.done(0)
        QtCore.QTimer.singleShot(20, closer)
        return fn()

    # -- production drivers ---------------------------------------------------
    def apply(self, name, values, kind=u"body"):
        """Real ProdWindow.apply_kind -> guard -> prod_apply."""
        record = {"name": name, "kind": kind, "preset_id": u"id-" + name,
                  "values": dict((u"flex." + l, {"representation": u"MONO", "mono": v}) for l, v in values.items())}
        w = self.window
        w.selected = lambda k: {"source": u"v3", "name": name, "record": record}
        w.operation_revalidate = lambda: None
        self.ns["prod_reread_selected_record"] = lambda ident, item, k: record
        self.ns["prod_validate_preset"] = lambda ident, rec, k: True
        before = self.env.log_count(u"PROD_ACTION_ERROR")
        self.with_modal_closer(lambda: w.apply_kind(kind))
        self.env.settle()
        return self.env.log_count(u"PROD_ACTION_ERROR") - before

    def fit(self, targets):
        """Real operation_begin + ProdWindow.fit_stage from index 0."""
        w, ns = self.window, self.ns
        w.operation_revalidate = lambda: None
        assert w.operation_begin(u"Clothing Fit", pin_context=True)
        w.fit_generation += 1
        w.fit_active = True
        w.fit_selected_identities = [dict(t) for t in targets]
        for attr in ("fit_changed", "fit_unchanged", "fit_committed_order", "fit_partial", "fit_skipped",
                     "fit_failed", "fit_unattempted"):
            setattr(w, attr, [])
        w.fit_source_baseline = {"identity": dict(SOURCE)}
        w.fit_authority_context = ns["prod_cpm_authorize_operation"](
            dict(SOURCE), w.scope, ns["P03_KIND_BODY"], u"Clothing Fit")
        w.fit_semantic_generation = G1
        generation = w.fit_generation
        self.with_modal_closer(lambda: w.fit_stage(generation, 0))
        self.env.settle()
        self.env.pump_timers()
        return generation


def armed(s, out):
    return "S4 ARMED" in out


# ------------------------------------------------------------------ scenarios
def scenario_static_pins(s):
    """The harness pins match the real app as compiled by the R15 loader."""
    ns = s.ns
    c("app_build_sha_matches_pin", ns.get("__chadchan3d_cpm_build_sha256__") == APP_SHA)
    src = r15._read(HARNESS).decode("ascii")
    pins = dict((k, int(v)) for k, v in re.findall(r'"(\w+)": (\d+)', src.split("PINS = {")[1].split("}")[0]))
    c("pins_cover_ten_functions", len(pins) == 10, sorted(pins))
    for name, line in sorted(pins.items()):
        fn = ns[name]
        c("pin.%s" % name, fn.__code__.co_firstlineno == line and fn.__globals__ is ns,
          fn.__code__.co_firstlineno)


def scenario_arm_refusals(s):
    ns = s.ns

    def refused(label, setup, undo, gate="A", leaf=None):
        s.select(gate)
        setup()
        if s.campaign is None or leaf:
            s.new_campaign(leaf)
        out = s.run()
        ok = "S4 HARNESS REFUSED" in out and s.rec("s1_arm.json") is None and s.no_wrappers()
        c("refuse.%s" % label, ok, out[-400:])
        undo()

    nothing = lambda: None
    # Pointer / campaign problems.
    s.select("A")
    out = s.run()
    c("refuse.no_pointer", "no ACTIVE_CAMPAIGN.txt" in out and s.bindings_original(), out[-300:])
    os.makedirs(os.path.join(s.s4root, "S4X"))
    with open(os.path.join(s.s4root, "ACTIVE_CAMPAIGN.txt"), "wb") as f:
        f.write(b"S4X")
    out = s.run()
    c("refuse.malformed_leaf", "malformed ACTIVE_CAMPAIGN" in out, out[-300:])
    s.new_campaign("S4A", seed=False)
    out = s.run()
    c("refuse.unseeded_campaign", "baseline_inventory.json missing" in out and s.bindings_original(), out[-300:])
    shutil.rmtree(s.campaign)
    s.campaign = None
    s.new_campaign("S4A_R2")

    build = ns["__chadchan3d_cpm_build_sha256__"]
    refused("wrong_app_build", lambda: ns.__setitem__("__chadchan3d_cpm_build_sha256__", "0" * 64),
            lambda: ns.__setitem__("__chadchan3d_cpm_build_sha256__", build))
    original = ns["matches_value"]
    refused("foreign_binding", lambda: ns.__setitem__("matches_value", lambda a, b: True),
            lambda: ns.__setitem__("matches_value", original))
    moved = types.FunctionType(ns["close_enough"].__code__, ns, "matches_value")
    refused("binding_not_at_pinned_line", lambda: ns.__setitem__("matches_value", moved),
            lambda: ns.__setitem__("matches_value", original))
    refused("live_master_not_g1", lambda: s.set_master(s.g1 + b"\n"), lambda: s.set_master(s.g1))
    refused("cpm_busy", lambda: setattr(s.window, "operation", {"kind": u"Apply"}),
            lambda: setattr(s.window, "operation", None))
    refused("wrong_model", lambda: setattr(s.window, "identity", dict(SOURCE)), nothing)
    refused("scope_not_g1", lambda: s.window.scope["authority"].__setitem__("provider_sha256", "x"), nothing)
    refused("lease_outstanding", lambda: setattr(s.broker, "leases", 1), lambda: setattr(s.broker, "leases", 0))
    refused("provider_open", lambda: setattr(s.broker, "open", 1), lambda: setattr(s.broker, "open", 0))
    s.campaign = None
    refused("fit_target_missing", lambda: setattr(s.window, "fit_identity_tokens", [dict(T1)]), nothing,
            gate="F", leaf="S4F")
    # Positive control: everything valid -> ARM succeeds.
    s.select("A")
    s.campaign = None
    s.new_campaign("S4A_R3")
    out = s.run()
    c("arm.valid_installs_wrappers", armed(s, out) and s.rec("s1_arm.json") is not None
      and not s.bindings_original(), out[-300:])
    arm = s.rec("s1_arm.json") or {}
    c("arm.records_wrapped_names", arm.get("wrapped") == sorted(
        ["p03_verify_saved_values", "prod_cpm_open_adapter", "prod_verify_apply_abort_baseline"]), arm.get("wrapped"))


def apply_scenario(s, scenario, leaf):
    s.select("A")
    if scenario == 1:
        s.new_campaign(leaf)
    pre = s.mia()
    undo_before = s.scene.undo_count
    out = s.run()
    c("s%d.armed" % scenario, armed(s, out), out[-300:])
    errors = s.apply(u"BodyTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3})
    fire = s.rec("s%d_fire.json" % scenario) or {}
    log = s.env.log() or u""
    c("s%d.native_writes_occurred" % scenario, s.scene.writes > 0, s.scene.writes)
    c("s%d.real_predicate_read_scene_inside_open_undo" % scenario, s.scene.reads_open > 0, s.scene.reads_open)
    c("s%d.real_verifier_read_scene_after_abort" % scenario, s.scene.reads_after_abort > 0, s.scene.reads_after_abort)
    c("s%d.authentic_abort" % scenario, ("Abort",) in s.scene.calls and ("FinishUndo",) not in s.scene.calls,
      s.scene.calls)
    c("s%d.values_restored" % scenario, s.mia() == pre, s.mia())
    c("s%d.no_undo_entry" % scenario, s.scene.undo_count == undo_before)
    c("s%d.fire_real_true" % scenario, fire.get("real_result") is True, fire.get("real_result"))
    c("s%d.fire_substitution" % scenario, fire.get("substituted") is (scenario == 2), fire.get("substituted"))
    c("s%d.no_adapter_calls_in_verification" % scenario, fire.get("adapter_calls_during_verification") == 0,
      fire.get("adapter_calls_during_verification"))
    c("s%d.bindings_restored_on_fire" % scenario, s.bindings_original())
    c("s%d.production_abort_log" % scenario, (u"PROD_APPLY_ABORT_VERIFY restored=%r" % (scenario == 1)) in log)
    c("s%d.no_committed_outcome" % scenario, u"PROD_APPLY outcome='committed'" not in log)
    c("s%d.guard_error_once" % scenario, errors == 1, errors)
    if scenario == 2:
        c("s2.recovery_unverified_raised", u"ProdRecoveryUnverifiedError" in log)
    if s.env.model is None:
        title = u"Can't apply preset" if scenario == 1 else u"Recovery could not be verified"
        c("s%d.dialog_title" % scenario, bool(s.dialogs) and s.dialogs[-1][0] == title, s.dialogs)
    out = s.run()
    state = s.rec("s%d_state.json" % scenario) or {}
    c("s%d.state_recorded_ok" % scenario, "S4 RECORDED OK" in out and state.get("status") == "RECORDED_OK",
      [x for x in state.get("checks", []) if not x["ok"]] or out[-400:])
    c("s%d.state_wrappers_absent" % scenario, state.get("wrappers_absent") is True and s.bindings_original())
    s.scene.calls = []
    s.scene.reads_open = s.scene.reads_after_abort = s.scene.writes = 0
    s.scene.aborted = False


def scenario_apply_control_and_gate(s):
    apply_scenario(s, 1, "S4A")
    apply_scenario(s, 2, "S4A")
    out = s.run()
    c("campaign_complete_refuses_further_clicks", "complete or stopped" in out and s.bindings_original(), out[-200:])
    # Ordinary follow-up Apply: committed-verified with one Undo entry.
    before = s.scene.undo_count
    errors = s.apply(u"BodyTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3})
    log = s.env.log() or u""
    c("followup.committed_verified", errors == 0 and u"PROD_APPLY outcome='committed'" in log
      and s.scene.undo_count == before + 1 and abs(s.mia()[u"BrowUp"] - 0.55) < 1e-9)


def scenario_apply_postcommit_not_fired(s):
    """Armed, but the precommit call is made to pass (phase held); the postcommit
    call (opened False) from prod_apply must pass through untouched."""
    s.select("A")
    s.new_campaign("S4A")
    out = s.run()
    c("armed", armed(s, out), out[-300:])
    st = getattr(s.env.app, "_cpm_s4_state_v1")
    st["phase"] = "held"
    seen = {}
    original_mark = s.window.operation_mark_phase

    def mark(phase, detail=None):
        if phase == u"native-commit":
            st["phase"] = "armed"            # re-arm only after FinishUndo
            seen["rearmed"] = True
        return original_mark(phase, detail)
    s.window.operation_mark_phase = mark
    errors = s.apply(u"BodyTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3})
    del s.window.operation_mark_phase
    log = s.env.log() or u""
    c("rearmed_after_commit", seen.get("rearmed") is True)
    c("postcommit_call_passed_through", st.get("passthrough", 0) >= 1 and st.get("phase") == "armed",
      [st.get("passthrough"), st.get("phase")])
    c("apply_committed_verified", errors == 0 and u"PROD_APPLY outcome='committed'" in log)
    c("no_fire_record", s.rec("s1_fire.json") is None)
    c("predicate_still_installed_until_state", not s.bindings_original())
    out = s.run()
    state = s.rec("s1_state.json") or {}
    c("state_invalid_not_fired", state.get("status") == "INVALID" and "S4 INVALID" in out, out[-300:])
    c("state_restored_all", s.bindings_original() and state.get("wrappers_absent") is True)


def scenario_unrelated_callers(s):
    """Wrappers never fire for callers other than the pinned production frames,
    nor for an unarmed preset."""
    ns = s.ns
    s.select("A")
    s.new_campaign("S4A")
    s.run()
    st = getattr(s.env.app, "_cpm_s4_state_v1")
    b = s.scene.binding("mia1", u"Hips")
    accepted = {u"Hips": b}
    preset = {"values": {u"flex.Hips": {"representation": u"MONO", "mono": s.scene.values[("mia1", u"Hips")]}}}
    c("direct_predicate_call_passes_through", ns["p03_verify_saved_values"](accepted, preset) is True
      and st["phase"] == "armed" and st.get("passthrough") == 0)
    # A different preset through the real prod_apply: both calls pass through.
    errors = s.apply(u"Body", {u"BrowUp": 0.45, u"Chest": 0.2, u"Hips": 0.3})
    c("other_preset_not_injected", errors == 0 and st["phase"] == "armed" and st.get("passthrough") == 2,
      [errors, st["phase"], st.get("passthrough")])
    s.run()                                   # STATE: INVALID + restore
    c("restored_after_invalid", s.bindings_original())
    # Fit wrappers: direct calls with Fit armed pass through.
    s.select("F")
    s.campaign = None
    s.new_campaign("S4F")
    s.run()
    st = getattr(s.env.app, "_cpm_s4_state_v1")
    state = s.scene.side_snapshot(None, {"animset": "t1", "literal": u"FitA"})
    c("direct_matches_value_passes_through", ns["matches_value"](state, state["source"]) is True
      and st["phase"] == "armed")
    st["phase"] = "injected"
    plan = ns["g11a_safe_plan"](None, {"animset": "t1", "name": T1["name"]})
    c("direct_target_baseline_passes_through", ns["p03_target_matches_baseline"](plan) is True
      and st.get("fire") is None)
    st["phase"] = "armed"
    s.run()
    c("fit_restored_after_invalid", s.bindings_original())


def scenario_predicate_exception_restores(s):
    s.select("A")
    s.new_campaign("S4A")
    s.run()
    s.scene.fail_reads_open = True
    errors = s.apply(u"BodyTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3})
    s.scene.fail_reads_open = False
    st = getattr(s.env.app, "_cpm_s4_state_v1")
    c("apply_failed_once", errors == 1, errors)
    c("restored_immediately_on_exception", s.bindings_original() and st.get("phase") == "invalid")
    out = s.run()
    state = s.rec("s1_state.json") or {}
    c("state_invalid", state.get("status") == "INVALID" and "S4 INVALID" in out, out[-300:])
    out = s.run()
    c("stopped_campaign_refuses", "complete or stopped" in out, out[-200:])


def fit_scenario(s, scenario):
    s.select("F")
    if scenario == 1:
        s.new_campaign("S4F")
    pre_t1 = dict((l, s.scene.values[("t1", l)]) for l in ANIMSETS["t1"])
    pre_t2 = dict((l, s.scene.values[("t2", l)]) for l in ANIMSETS["t2"])
    undo_before = s.scene.undo_count
    out = s.run()
    c("s%d.armed" % scenario, armed(s, out), out[-300:])
    s.fit([T1, T2])
    fire = s.rec("s%d_fire.json" % scenario) or {}
    log = s.env.log() or u""
    w = s.window
    c("s%d.stage_open_g1" % scenario, (u"PROD_CPM_FIT_STAGE_OPEN index=0 gfit=%s" % G1) in log)
    c("s%d.no_target2_stage" % scenario, u"PROD_CPM_FIT_STAGE_OPEN index=1" not in log)
    c("s%d.native_writes_occurred" % scenario, s.scene.writes > 0, s.scene.writes)
    c("s%d.real_predicate_read_scene_inside_open_undo" % scenario, s.scene.reads_open > 0)
    c("s%d.real_verifier_read_scene_after_abort" % scenario, s.scene.reads_after_abort > 0)
    c("s%d.authentic_abort" % scenario, ("Abort",) in s.scene.calls and ("FinishUndo",) not in s.scene.calls)
    c("s%d.t1_restored" % scenario, dict((l, s.scene.values[("t1", l)]) for l in ANIMSETS["t1"]) == pre_t1)
    c("s%d.t2_untouched" % scenario, dict((l, s.scene.values[("t2", l)]) for l in ANIMSETS["t2"]) == pre_t2)
    c("s%d.no_undo_entry" % scenario, s.scene.undo_count == undo_before)
    c("s%d.lease_held_during_verification" % scenario,
      (fire.get("entry_counters") or {}).get("outstanding_leases") == 1, fire.get("entry_counters"))
    c("s%d.no_adapter_calls_in_verification" % scenario, fire.get("adapter_calls_during_verification") == 0)
    c("s%d.fire_real_true" % scenario, fire.get("real_result") is True)
    c("s%d.fire_substitution" % scenario, fire.get("substituted") is (scenario == 2))
    c("s%d.leases_back_to_zero" % scenario, s.broker.leases == 0, s.broker.leases)
    want = u"abort-unverified" if scenario == 2 else u"not-committed"
    c("s%d.accounting" % scenario, len(w.fit_failed) == 1 and w.fit_failed[0]["verification"] == want
      and w.fit_failed[0]["committed"] is False and w.fit_committed_order == []
      and [t["name"] for t in w.fit_unattempted] == [T2["name"]], [w.fit_failed, w.fit_unattempted])
    c("s%d.production_abort_log" % scenario, (u"PROD_CLOTHING_FIT_ABORT_VERIFY target=" in log)
      and (u"restored=%r" % (scenario == 1)) in log.split(u"PROD_CLOTHING_FIT_ABORT_VERIFY")[-1].split(u"\n")[0])
    if scenario == 2:
        c("s2.failure_dialog_logged", u"recovery_unverified=[u'assaultsuitbody1']" in log
          or u"recovery_unverified=['assaultsuitbody1']" in log)
        if s.env.model is None:
            c("s2.dialog_title", bool(s.dialogs) and s.dialogs[-1][0] == u"Clothing Fit stopped", s.dialogs)
    out = s.run()
    state = s.rec("s%d_state.json" % scenario) or {}
    c("s%d.state_recorded_ok" % scenario, "S4 RECORDED OK" in out and state.get("status") == "RECORDED_OK",
      [x for x in state.get("checks", []) if not x["ok"]] or out[-400:])
    rel = state.get("releases") or []
    c("s%d.exactly_one_release" % scenario, len(rel) == 1 and rel[0].get("result") is None, rel)
    c("s%d.state_wrappers_absent" % scenario, state.get("wrappers_absent") is True and s.bindings_original())
    s.scene.calls = []
    s.scene.reads_open = s.scene.reads_after_abort = s.scene.writes = 0
    s.scene.aborted = False


def scenario_fit_control_and_gate(s):
    fit_scenario(s, 1)
    fit_scenario(s, 2)
    # Ordinary later Fit of target 1: committed, post-stage verified, released.
    before = dict(s.scene.values)
    s.scene.last_committed_before = before
    undo_before = s.scene.undo_count
    s.fit([T1])
    log = s.env.log() or u""
    w = s.window
    c("followup.stage_pass", u"CLOTHING_FIT_STAGE=PASS" in log and u"committed=True" in log)
    c("followup.result_pass", u"CLOTHING_FIT_RESULT=PASS" in log)
    c("followup.released_ok", u"PROD_CPM_FIT_STAGE_RELEASED index=0 ok=True" in log and s.broker.leases == 0)
    c("followup.one_undo_entry", s.scene.undo_count == undo_before + 1)
    s.scene.undo()
    c("followup.undo_restores", s.scene.values == before)


def scenario_expression_shared_path(s):
    """Expression Apply exercises the same prod_apply abort path (no harness)."""
    ns = s.ns
    s.select("A")
    calls = {"n": 0}
    real_open = ns["prod_cpm_open_adapter"]

    def counting():
        calls["n"] += 1
        return real_open()
    ns["prod_cpm_open_adapter"] = counting
    window = {}
    real_verify = ns["prod_verify_apply_abort_baseline"]

    def spy(*args, **kwargs):
        before = calls["n"]
        try:
            return real_verify(*args, **kwargs)
        finally:
            window["during"] = calls["n"] - before
            window["context"] = (kwargs.get("authority_context") or {}).get("master_sha256")
    ns["prod_verify_apply_abort_baseline"] = spy
    real_write = s.scene.write_side
    s.scene.write_side = lambda b, side, origin, desired: real_write(b, side, origin, desired + 0.25)
    ns["write_side"] = s.scene.write_side
    pre = s.mia()
    errors = s.apply(u"ExprTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3}, kind=u"expression")
    log = s.env.log() or u""
    c("expression.verified_rollback", errors == 1 and u"PROD_APPLY_ABORT_VERIFY restored=True" in log
      and s.mia() == pre)
    c("expression.no_adapter_calls_during_rollback_verification", window.get("during") == 0, window)
    c("expression.verification_uses_captured_g1_context", window.get("context") == G1, window)
    s.scene.abort_restores = False
    window.clear()
    errors = s.apply(u"ExprTest", {u"BrowUp": 0.55, u"Chest": 0.2, u"Hips": 0.3}, kind=u"expression")
    log = s.env.log() or u""
    c("expression.unverified_rollback", errors == 1 and u"PROD_APPLY_ABORT_VERIFY restored=False" in log
      and u"ProdRecoveryUnverifiedError" in log)
    c("expression.no_adapter_in_unverified_verification", window.get("during") == 0, window)
    ns["prod_cpm_open_adapter"] = real_open
    ns["prod_verify_apply_abort_baseline"] = real_verify
    ns["write_side"] = real_write


def scenario_mutant(s):
    """Run with a mutated harness; the named check must FAIL (mutation caught)."""
    apply_scenario(s, 1, "S4A")


SCENARIOS = [("static_pins", scenario_static_pins), ("arm_refusals", scenario_arm_refusals),
             ("apply_control_and_gate", scenario_apply_control_and_gate),
             ("apply_postcommit_not_fired", scenario_apply_postcommit_not_fired),
             ("unrelated_callers", scenario_unrelated_callers),
             ("predicate_exception_restores", scenario_predicate_exception_restores),
             ("fit_control_and_gate", scenario_fit_control_and_gate),
             ("expression_shared_path", scenario_expression_shared_path)]


def child_main(scenario, qt_mode, root, harness):
    try:
        s = S4(qt_mode, root, harness)
        dict(SCENARIOS + [("mutant", scenario_mutant)])[scenario](s)
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
          and tree.body[0].name == "_cpm_s4_rollback_harness_v1" and ast.get_docstring(tree) is None)
    body = u"\n".join(l for l in raw.decode("ascii").splitlines() if not l.lstrip().startswith("#"))
    for label, token in (("authority_activation", "perform_g1_to_g2"), ("movefile", "MoveFileEx"),
                         ("publisher", "publish"), ("remove", "os.remove"), ("rename", "os.rename"),
                         ("unlink", "unlink"), ("shutil", "shutil"), ("sys_path", "sys.path"),
                         ("broker_acquire", "acquire"), ("exec", "exec("), ("production_log", "log_line"),
                         ("open_stage_call", "open_stage("), ("authorize_call", "authorize_operation("),
                         ("process_events", "processEvents")):
        check("static.no_%s" % label, token not in body)
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "open"
              and len(n.args) > 1 and (getattr(n.args[1], "s", None) or getattr(n.args[1], "value", None)) == "wb"]
    check("static.single_write_site_is_write_once", len(writes) == 1)
    check("static.predicate_real_before_substitution",
          body.index("# REAL predicate first") < body.index("return False\n            return s4_precommit_predicate"))
    check("static.verifier_real_before_substitution",
          body.index("# REAL verifier first") < body.index("return False if substitute else real"))
    check("static.one_shot_restore_before_real_calls",
          body.index('restore_one(ns, st, spec["predicate"])') < body.index("# REAL predicate first")
          and body.index('restore_one(ns, st, spec["verifier"])') < body.index("# REAL verifier first"))
    check("static.app_sha_pin", APP_SHA in body and r15._sha(r15._read(APP)) == APP_SHA)
    check("static.g1_pin", G1 in body and r15._sha(r15._read(os.path.join(_REPO, "sfm_defaultanimationgroups.txt"))) == G1)
    app_lines = r15._read(APP).decode("utf-8").splitlines()
    pins = dict((k, int(v)) for k, v in re.findall(r'"(\w+)": (\d+)', body.split("PINS = {")[1].split("}")[0]))
    check("static.pins_are_def_lines", len(pins) == 10 and all(
        app_lines[line - 1].startswith("def %s(" % name) for name, line in pins.items()), pins)


def run_child(name, mode, harness=HARNESS, tag=None):
    root = os.path.join(FIXTURE_ROOT, "%s_%s" % (mode, tag or name))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=%s" % name,
                             "--qt=%s" % mode, "--root=%s" % root, "--harness=%s" % harness],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = proc.communicate()[0].decode("utf-8", "replace")
    for line in output.splitlines():
        if line.startswith("R15_CHILD_RESULT "):
            return json.loads(line[len("R15_CHILD_RESULT "):]), output
    return None, output


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if "--child" in args:
        child_main(args["--child"], args["--qt"], args["--root"], args.get("--harness", HARNESS))
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
            records, output = run_child(name, mode)
            if records is None:
                check("%s.%s.child_reported" % (mode, name), False, output[-2000:])
                continue
            for cname, ok, value in records:
                check("%s.%s.%s" % (mode, name, cname), ok, value)
    # Mutation tests: a wrapper that skips the real function must be caught.
    raw = r15._read(HARNESS).decode("ascii")
    expect = {"predicate_skips_real": "s1.real_predicate_read_scene_inside_open_undo",
              "verifier_skips_real": "s1.real_verifier_read_scene_after_abort"}
    for label, (old, new) in sorted(MUTANTS.items()):
        check("mutant.%s.applies" % label, raw.count(old) == 1)
        path = os.path.join(FIXTURE_ROOT, "mutant_%s.py" % label)
        with open(path, "wb") as f:
            f.write(raw.replace(old, new).encode("ascii"))
        records, output = run_child("mutant", "model", harness=path, tag="mutant_" + label)
        failed = [r[0] for r in (records or []) if not r[1]]
        check("mutant.%s.caught" % label, records is not None and expect[label] in failed, failed or output[-800:])
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
