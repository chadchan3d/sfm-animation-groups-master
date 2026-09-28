# -*- coding: utf-8 -*-
"""CPM convergence Step 2a -- offline qualification of the CPM canonical
authority adapter (cpm/convergence/cpm_authority_adapter.py), including the
Suite 1 snapshot/signature parity items Step 1 deferred.

Phases (same two-interpreter technique as Step 1):

  --phase=publish  (Python 3): builds fixture Masters in an OS temp
      directory, publishes them with the real tools/sfm_master_sidecar
      publisher, runs the suite, writes a result digest.
  --phase=suite    (Python 2.7.5, separate process): runs the same suite
      against the published fixtures, writes its own digest.
  --phase=compare: the two digests must be identical.

Oracles, extracted verbatim from pinned line ranges:
  * frozen G18AN baseline -- semantic_snapshot_from_live_vocabulary,
    semantic_snapshot_signature, semantic_snapshot_for_model_row,
    prod_pure_semantic_row, prod_provider_capture, the legacy provider-health
    predicate, and _answer_from_result (Hit/MasterUnknown only);
  * qualified production Normalizer snapshot -- the sys.executable MAINMENU
    locator.
Conflict answers use independent hand-audited expectations.

Never launches SFM. Never modifies the canonical Master, the frozen G18AN
baseline, the Normalizer, or the shared authority package.
"""
import gc
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import textwrap

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
# Test-only override so sensitivity runs can point at perturbed scratch copies.
MODULE_DIR = os.environ.get("CPM_TEST_MODULE_DIR") or os.path.join(_REPO_ROOT, "cpm", "convergence")
TOOLS_DIR = os.path.join(_REPO_ROOT, "tools")
PACKAGE_PARENT = os.path.join(_REPO_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction6")
G18AN_PATH = os.path.join(_REPO_ROOT, "cpm", "baseline", "SFM_CSP_G18AN_SaveNewCopy.py")
G18AN_SHA256 = "3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e"
NORMALIZER_PATH = os.path.join(_REPO_ROOT, "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py")
NORMALIZER_SHA256 = "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7"

for _p in (TOOLS_DIR, PACKAGE_PARENT, MODULE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpm_compat_v1_projection as cpm  # noqa: E402
import cpm_authority_adapter as adapter_mod  # noqa: E402

PY2 = sys.version_info[0] == 2
try:
    _TEXT = unicode  # noqa: F821
except NameError:
    _TEXT = str

FIXTURE_ROOT = os.path.join(tempfile.gettempdir(), "cpm_authority_adapter_step2a_fixture")
G1_DIR = os.path.join(FIXTURE_ROOT, "g1")
G2_DIR = os.path.join(FIXTURE_ROOT, "g2")
LIVE_DIR = os.path.join(FIXTURE_ROOT, "live")
CORRUPT_DIR = os.path.join(FIXTURE_ROOT, "corrupt")
MASTER_NAME = "sfm_defaultanimationgroups.txt"
DIGEST_PY3 = os.path.join(FIXTURE_ROOT, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_ROOT, "digest_py27.json")

MASTER_G1 = (
    u'"groupFile"\n{\n'
    u'\t"Face"\n\t{\n'
    u'\t\t"Eyes"\n\t\t{\n'
    u'\t\t\t"control"\t\t"Blink"\n'
    u'\t\t\t"control"\t\t"Blink"\n'
    u'\t\t\t"control"\t\t"BLINK"\n'
    u'\t\t\t"control"\t\t"Wink"\n'
    u'\t\t}\n'
    u'\t\t"Mouth"\n\t\t{\n'
    u'\t\t\t"control"\t\t"JawOpen"\n'
    u'\t\t\t"control"\t\t"Brow Up"\n'
    u'\t\t\t"control"\t\t"ÑOSE"\n'
    u'\t\t\t"control"\t\t"Ñose"\n'
    u'\t\t\t"control"\t\t"Smile"\n'
    u'\t\t}\n'
    u'\t}\n'
    u'\t"Body Morphs"\n\t{\n'
    u'\t\t"control"\t\t"Belly"\n'
    u'\t\t"control"\t\t"wink"\n'
    u'\t\t"control"\t\t"Chest"\n'
    u'\t\t"control"\t\t"Hips"\n'
    u'\t}\n'
    u'\t"Clothing"\n\t{\n'
    u'\t\t"control"\t\t"Skirt"\n'
    u'\t\t"Tops"\n\t\t{\n'
    u'\t\t\t"control"\t\t"Shirt"\n'
    u'\t\t}\n'
    u'\t}\n'
    u'\t"Other"\n\t{\n'
    u'\t\t"Misc"\n\t\t{\n'
    u'\t\t\t"Deep"\n\t\t\t{\n'
    u'\t\t\t\t"control"\t\t"Tail"\n'
    u'\t\t\t}\n'
    u'\t\t}\n'
    u'\t}\n'
    u'}\n'
)
# The corrupt fixture uses its own Master generation so no cached view of G1
# can satisfy it (the broker cache is keyed by Master SHA, not by location).
MASTER_CORRUPT = MASTER_G1.replace(u'\t\t"control"\t\t"Hips"\n', u'\t\t"control"\t\t"Hips"\n\t\t"control"\t\t"CorruptOnly"\n')
MASTER_G2 = MASTER_G1.replace(u'\t\t"control"\t\t"Hips"\n', u'\t\t"control"\t\t"Hips"\n\t\t"control"\t\t"Thigh"\n')
# Hand count of MASTER_G1: 16 control occurrences in 12 fold families.
G1_OCCURRENCES = 16
G1_FOLD_FAMILIES = 12

# Synthetic live FLEX bindings (literal, shape). Deliberately unsorted.
LIVE_BINDINGS = [
    (u"Tail", u"tail"), (u"Blink", u"blink"), (u"WINK", u"wink_u"), (u"bLiNk", u"blink_mixed"),
    (u"Wink", u"wink"), (u"jawopen", u"jaw"), (u"Brow Up", u"brow"), (u"Brow  Up", u"brow2"),
    (u"ÑOSE", u"nose"), (u"ñose", u"nose_lower"), (u"Belly", u"belly"), (u"chest", u"chest"),
    (u"Hips", u"hips_a"), (u"Hips", u"hips_b"), (u"Smile", u"smile"), (u"Smile", u"smile"),
    (u"Skirt", u"skirt"), (u"Shirt", u"shirt"), (u"Ghost", u"ghost"),
]


def _bindings(pairs):
    return [{"literal": lit, "shape": shape} for lit, shape in pairs]


def _live_literals():
    return sorted(set(lit for lit, _ in LIVE_BINDINGS))


# Hand-audited snapshot expectations: literal -> (status, match_kind, class, operation)
EXPECTED_ROWS = {
    u"Belly": (u"resolved", u"exact", u"body-morphs", u"body"),
    u"Blink": (u"resolved", u"exact", u"face", u"expression"),
    u"Brow  Up": (u"absent", u"none", u"master-miss", u"unresolved"),
    u"Brow Up": (u"resolved", u"exact", u"face", u"expression"),
    u"Ghost": (u"absent", u"none", u"master-miss", u"unresolved"),
    u"Hips": (u"resolved", u"exact", u"body-morphs", u"unresolved"),
    u"Shirt": (u"resolved", u"exact", u"other", u"excluded-other"),
    u"Skirt": (u"resolved", u"exact", u"other", u"excluded-other"),
    u"Smile": (u"resolved", u"exact", u"face", u"unresolved"),
    u"Tail": (u"resolved", u"exact", u"other", u"excluded-other"),
    u"WINK": (u"conflict", u"ascii-fold", u"master-conflict", u"unresolved"),
    u"Wink": (u"conflict", u"exact", u"master-conflict", u"unresolved"),
    u"bLiNk": (u"resolved", u"ascii-fold", u"face", u"expression"),
    u"chest": (u"resolved", u"ascii-fold", u"body-morphs", u"body"),
    u"jawopen": (u"resolved", u"ascii-fold", u"face", u"expression"),
    u"ÑOSE": (u"resolved", u"exact", u"face", u"expression"),
    u"ñose": (u"absent", u"none", u"master-miss", u"unresolved"),
}
EXPECTED_COUNTS = {
    "supported_bindings": 19, "unique_literals": 17, "resolved_face": 6, "resolved_body_morphs": 3,
    "resolved_other": 3, "miss": 3, "conflict": 2, "authority_unavailable": 0, "binding_ambiguous": 2,
    "folded_resolved": 3, "expression_eligible": 5, "body_eligible": 2,
}
# Hand-audited conflict answers (G18AN's adapter cannot produce these).
CONFLICT_ANSWERS = {
    u"Wink": {"query_literal": u"Wink", "status": u"conflict", "match_kind": u"exact", "resolved_path": None,
              "destinations": [u"Body Morphs", u"Face/Eyes"], "spellings": [u"Wink", u"wink"], "occurrence_count": 2},
    u"WINK": {"query_literal": u"WINK", "status": u"conflict", "match_kind": u"ascii-fold", "resolved_path": None,
              "destinations": [u"Body Morphs", u"Face/Eyes"], "spellings": [u"Wink", u"wink"], "occurrence_count": 2},
}

RESULTS = []


def check(name, condition, value=None):
    RESULTS.append((name, bool(condition), value))
    print("[%s] %s" % ("PASS" if condition else "FAIL", name))
    if not condition and value is not None:
        print("      value: %r" % (value,))


def _canon(obj):
    return json.loads(json.dumps(obj, sort_keys=True, default=repr))


def expect_unavailable(name, fn, reason_prefix, exc_type=None):
    """The call must raise CpmAuthorityUnavailable (or ``exc_type``) with
    a reason starting with ``reason_prefix``."""
    wanted = exc_type or adapter_mod.CpmAuthorityUnavailable
    try:
        fn()
    except wanted as exc:
        check(name, _TEXT(exc.reason).startswith(reason_prefix), _TEXT(exc.reason))
        return exc
    except Exception as exc:
        check(name, False, "raised %s" % type(exc).__name__)
        return None
    check(name, False, "did not raise")
    return None


# ---------------------------------------------------------------------------
# Verbatim oracle extraction
# ---------------------------------------------------------------------------

G18AN_RANGES = (
    ("u", 58, 69, "def u(value):"),
    ("provider_constants", 1113, 1117, "SEMANTIC_PROVIDER_CONTRACT = "),
    ("status_constants", 1140, 1159, "SEMANTIC_STATUS_RESOLVED = "),
    ("g18an_normalize_sidecar_path", 2259, 2295, "def g18an_normalize_sidecar_path("),
    ("_answer_from_result", 2496, 2588, "    def _answer_from_result("),
    ("p01_is_face_path", 3455, 3459, "def p01_is_face_path(path):"),
    ("body_morphs_constant", 3760, 3760, "SEMANTIC_BODY_MORPHS_PATH = "),
    ("semantic_is_body_morph_path", 3763, 3766, "def semantic_is_body_morph_path(path):"),
    ("semantic_snapshot_from_live_vocabulary", 3769, 3862, "def semantic_snapshot_from_live_vocabulary("),
    ("semantic_snapshot_signature", 3865, 3882, "def semantic_snapshot_signature(snapshot):"),
    ("semantic_snapshot_for_model_row", 3885, 3923, "def semantic_snapshot_for_model_row("),
    ("health_thresholds", 18504, 18506, "PROD_MASTER_HEALTH_MIN_OCCURRENCES = 1000"),
    ("prod_semantic_provider_health_from_descriptor", 18517, 18610, "def prod_semantic_provider_health_from_descriptor("),
    ("prod_pure_semantic_row", 19113, 19164, "def prod_pure_semantic_row(row):"),
    ("prod_provider_capture", 20041, 20055, "def prod_provider_capture(provider_or_descriptor):"),
    ("p03_unmapped_relevant_controls", 7225, 7323, "def p03_unmapped_relevant_controls("),
)


def _read_pinned(path, sha, label):
    with open(path, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    check("oracle.%s_sha256_pinned" % label, digest == sha, digest)
    return raw.decode("utf-8").split(u"\n")


class _NotCalled(Exception):
    pass


def _forbidden(*args, **kwargs):
    raise _NotCalled("development authority path was called")


def load_g18an_oracle():
    lines = _read_pinned(G18AN_PATH, G18AN_SHA256, "g18an")
    ns = {"hashlib": hashlib, "get_semantic_provider": _forbidden}
    if not PY2:
        ns["unicode"] = str
        ns["unichr"] = chr
    for label, start, end, head in G18AN_RANGES:
        block = lines[start - 1:end]
        check("oracle.g18an_range_pinned.%s" % label, block[0].startswith(head), block[0])
        text = u"\n".join(block) + u"\n"
        if label == "_answer_from_result":
            text = textwrap.dedent(text)
        exec(compile(text, "G18AN:%s" % label, "exec"), ns)
    return ns


def load_normalizer_locator():
    lines = _read_pinned(NORMALIZER_PATH, NORMALIZER_SHA256, "normalizer")
    start, end = 257, 281
    block = lines[start - 1:end]
    check("oracle.normalizer_range_pinned", block[0].startswith(u"def _authority_locate_mainmenu_dir():")
          and block[-1].strip() == u")", block[-1])
    return u"\n".join(block) + u"\n"


class _FakeSys(object):
    def __init__(self, executable):
        self.executable = executable


def normalizer_locate(source, executable):
    ns = {"os": os, "sys": _FakeSys(executable)}
    exec(compile(source, "Normalizer:_authority_locate_mainmenu_dir", "exec"), ns)
    return ns["_authority_locate_mainmenu_dir"]()


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _copy_dir_files(src, dst):
    if not os.path.isdir(dst):
        os.makedirs(dst)
    for name in os.listdir(dst):
        os.remove(os.path.join(dst, name))
    for name in os.listdir(src):
        shutil.copyfile(os.path.join(src, name), os.path.join(dst, name))


def _sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _live_master():
    return os.path.join(LIVE_DIR, MASTER_NAME)


def _runtime():
    from sfm_master_authority_productionized import runtime
    return runtime


def _broker():
    return _runtime().get_broker()


def _make_adapter(root_dir=None, broker=None):
    root = root_dir or LIVE_DIR
    return adapter_mod.CpmAuthorityAdapter(
        broker or _broker(), os.path.join(root, MASTER_NAME), shipped_root=root,
        runtime_identity={"runtime_api_version": u"1.0.0-b2a", "runtime_build_id": u"package-boundary-corrected-2026-09-22"})


def _no_outstanding(label):
    b = _broker()
    counters = b.provider_counters()
    check("retention.%s.no_outstanding_lease" % label, b.outstanding_lease_count() == 0)
    check("retention.%s.no_open_provider" % label, counters["current_open_provider_count"] == 0)


_ALLOWED_STATE_TYPES = (type(None), bool, int, float, str, _TEXT, bytes)


def _state_is_detached(obj):
    def ok(value):
        if isinstance(value, dict):
            return all(ok(k) and ok(v) for k, v in value.items())
        if isinstance(value, (list, tuple)):
            return all(ok(v) for v in value)
        return isinstance(value, _ALLOWED_STATE_TYPES)
    return all(ok(v) for k, v in vars(obj).items() if k != "_broker")


def _tb_holds_view_or_lease(tb):
    from sfm_master_authority_productionized import views
    while tb is not None:
        for value in tb.tb_frame.f_locals.values():
            if isinstance(value, (views.DetachedView, views.ViewLease)):
                return True
        tb = tb.tb_next
    return False


# ---------------------------------------------------------------------------
# Part A -- bootstrap
# ---------------------------------------------------------------------------

EXECUTABLE_FIXTURES = [
    os.path.join(os.sep, "fixture", "SourceFilmmaker", "game", "sfm.exe"),
    os.path.join(os.sep, "fixture", "Path With Spaces", "game", "sfm.exe"),
    os.path.join("relative", "game", "sfm.exe"),
    os.path.join(os.sep, "fixture", "a", "..", "game", "sfm.exe"),
]


def section_bootstrap():
    from sfm_master_authority_productionized import bootstrap as authority_bootstrap
    source = load_normalizer_locator()
    saved = sys.executable
    try:
        for i, exe in enumerate(EXECUTABLE_FIXTURES):
            cpm_dir = adapter_mod.locate_mainmenu_dir(exe)
            norm_dir = normalizer_locate(source, exe)
            sys.executable = exe
            pkg_dir = authority_bootstrap.bootstrap_import_path()
            sys.executable = saved
            check("bootstrap.formula_equals_normalizer fixture%d" % i, cpm_dir == norm_dir)
            check("bootstrap.formula_equals_package_bootstrap fixture%d" % i, cpm_dir == pkg_dir)
            check("bootstrap.formula_suffix fixture%d" % i,
                  cpm_dir.replace(os.sep, "/").endswith("game/usermod/scripts/sfm/mainmenu/ChadChan3D"))
    finally:
        sys.executable = saved
    check("bootstrap.default_uses_sys_executable",
          adapter_mod.locate_mainmenu_dir() == adapter_mod.locate_mainmenu_dir(sys.executable))

    runtime = _runtime()
    main_thread = lambda: True  # noqa: E731
    broker, identity = adapter_mod.canonical_bootstrap(PACKAGE_PARENT, main_thread)
    check("bootstrap.canonical_broker_obtained", broker is runtime.get_broker())
    check("bootstrap.identity", identity == {"runtime_api_version": u"1.0.0-b2a",
                                             "runtime_build_id": u"package-boundary-corrected-2026-09-22",
                                             "runtime_module": u"sfm_master_authority_productionized.runtime"},
          _canon(identity))
    broker2, _ = adapter_mod.canonical_bootstrap(PACKAGE_PARENT, main_thread)
    check("bootstrap.no_second_broker", broker2 is broker)
    check("bootstrap.runtime_module_canonical", runtime.is_canonical()
          and sys.modules[adapter_mod.RUNTIME_MODULE_NAME] is runtime)

    expect_unavailable("bootstrap.origin_mismatch_rejected",
                       lambda: adapter_mod.canonical_bootstrap(os.path.join(FIXTURE_ROOT, "elsewhere"), main_thread),
                       u"origin-mismatch")

    def patched(attr, value, fn):
        missing = object()
        old = getattr(runtime, attr, missing)
        if value is missing:
            delattr(runtime, attr)
        else:
            setattr(runtime, attr, value)
        try:
            return fn()
        finally:
            if old is missing:
                if hasattr(runtime, attr):
                    delattr(runtime, attr)
            else:
                setattr(runtime, attr, old)

    boot = lambda: adapter_mod.canonical_bootstrap(PACKAGE_PARENT, main_thread)  # noqa: E731
    expect_unavailable("bootstrap.api_mismatch_rejected",
                       lambda: patched("RUNTIME_API_VERSION", "9.9.9", boot), u"api-mismatch")
    expect_unavailable("bootstrap.build_mismatch_rejected",
                       lambda: patched("RUNTIME_BUILD_ID", "other-build", boot), u"build-mismatch")
    check("bootstrap.build_restored", runtime.RUNTIME_BUILD_ID == adapter_mod.EXPECTED_BUILD_ID)
    expect_unavailable("bootstrap.non_canonical_module_rejected",
                       lambda: patched("is_canonical", lambda: False, boot), u"module-identity")

    def failing_get_broker(**kwargs):
        raise RuntimeError("fixture broker construction failure")
    expect_unavailable("bootstrap.get_broker_failure_rejected",
                       lambda: patched("get_broker", failing_get_broker, boot), u"broker-unavailable")
    check("bootstrap.state_restored_after_failures", adapter_mod.canonical_bootstrap(PACKAGE_PARENT, main_thread)[0] is broker)


def section_no_development_paths():
    import ast
    forbidden = ("MasterTxtSemanticProvider", "SidecarSemanticProvider", "get_semantic_provider",
                 "acquire_semantic_provider_for_mode", "SEMANTIC_PROVIDER_MODE", "execfile",
                 "g18an_verified_sidecar_paths", "g18an_import_frozen_sidecar_provider", "G18AN_PARITY_SHORTCUT")
    for name in ("cpm_authority_adapter.py", "cpm_compat_v1_projection.py"):
        with open(os.path.join(MODULE_DIR, name), "rb") as f:
            tree = ast.parse(f.read())
        idents = set()
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                idents.add(node.id)
            elif isinstance(node, ast.Attribute):
                idents.add(node.attr)
            elif isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").split(".")[0])
        check("nodev.%s.no_development_identifiers" % name, not (idents & set(forbidden)), sorted(idents & set(forbidden)))
        check("nodev.%s.imports_only_canonical" % name,
              imports <= set(["os", "sys", "cpm_compat_v1_projection", "sfm_master_authority_productionized"]),
              sorted(imports))
    check("nodev.no_g18an_module_loaded", not any("G18AN" in (m or "") for m in list(sys.modules.keys())))


# ---------------------------------------------------------------------------
# Parts B-E, G -- facade, lease, validation, descriptor
# ---------------------------------------------------------------------------

def section_facade(oracle):
    adapter = _make_adapter()
    sha1 = _sha_file(_live_master())
    desc = adapter.generation_descriptor()
    check("descriptor.pins_current_generation", desc["source_sha256"] == sha1 and adapter.pinned_generation() == sha1)
    check("descriptor.provider_generation_stable_1", desc["provider_generation"] == 1)
    check("descriptor.no_whole_master_counts",
          not any(k in desc for k in ("occurrence_count", "fold_family_count", "group_count", "destination_count")))
    check("descriptor.fields", sorted(desc.keys()) == sorted([
        "provider_contract", "provider_kind", "source_sha256", "fold_policy", "provider_generation",
        "projection_contract", "consumer_kind", "semantic_policy_revision", "runtime_api_version",
        "runtime_build_id", "valid"]), sorted(desc.keys()))
    check("descriptor.detached_text_only", all(isinstance(v, (_TEXT, int, bool)) for v in desc.values()))
    check("descriptor.no_paths", not any(isinstance(v, _TEXT) and (os.sep in v or "/" in v) for v in desc.values()))
    capture = oracle["prod_provider_capture"](adapter)
    check("descriptor.g18an_provider_capture_via_provider", capture == {
        "provider_contract": u"sfm-character-semantic-provider-v1", "source_sha256": sha1,
        "fold_policy": u"ascii-a-z-v1", "provider_generation": 1}, _canon(capture))
    check("descriptor.g18an_provider_capture_via_dict", oracle["prod_provider_capture"](desc) == capture)
    check("descriptor.values_match_g18an_constants",
          desc["provider_contract"] == oracle["SEMANTIC_PROVIDER_CONTRACT"]
          and desc["fold_policy"] == oracle["SEMANTIC_PROVIDER_FOLD_POLICY"])

    opens_before = _broker().provider_counters()["total_provider_opens"]
    answers = adapter.query_many(_live_literals())
    check("facade.answers_for_every_literal", sorted(answers.keys()) == _live_literals())
    _no_outstanding("query_many")
    check("retention.adapter_state_detached", _state_is_detached(adapter), sorted(vars(adapter).keys()))
    answers2 = adapter.query_many(_live_literals())
    check("facade.repeat_query_reuses_view", _broker().provider_counters()["total_provider_opens"] == opens_before + 1
          and _broker().recent_diagnostics()[-1]["event"] == "fully_reused_no_provider_open")
    check("facade.repeat_query_identical", _canon(answers2) == _canon(answers))
    answers2[u"Blink"]["spellings"].append(u"MUTATED")
    check("facade.answers_are_copies", u"MUTATED" not in adapter.query_many([u"Blink"])[u"Blink"]["spellings"])
    _no_outstanding("repeat")
    gc.collect()
    from sfm_master_authority_productionized import views
    leaked = [o for o in gc.get_referrers(adapter) if isinstance(o, (views.DetachedView, views.ViewLease))]
    check("retention.no_view_or_lease_refers_to_adapter", not leaked)
    return adapter, answers


class _ProxyBroker(object):
    """Wraps the real canonical broker; each test overrides one method."""

    def __init__(self, real, **overrides):
        self._real = real
        self._overrides = overrides

    def __getattr__(self, name):
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._real, name)


class _FakeView(object):
    def __init__(self, sha, payload, coverage, consumer_kind=cpm.CONSUMER_KIND, valid=True):
        from sfm_master_authority_productionized import views, descriptors
        self.semantic_generation = descriptors.SemanticGeneration(
            effective_master_path=u"fixture", master_sha256=sha, master_byte_length=1,
            authority_semantics_version=None, projection_contract_version=None)
        self.payload = payload
        self.coverage = coverage
        self.consumer_kind = consumer_kind
        self.authorization = views.LiveAuthorizationToken(sha)
        if not valid:
            self.authorization.invalidate()
        self.admission_id = 0


def _fake_broker_for(view):
    real = _broker()
    released = []
    return _ProxyBroker(
        real,
        acquire_or_reuse_views=lambda *a, **k: {cpm.CONSUMER_KIND: view},
        lease_view=lambda v: ("fake-lease", v),
        release_view_lease=lambda lease: released.append(lease),
    ), released


def section_failure_mapping():
    from sfm_master_authority_productionized import views
    sha = _sha_file(_live_master())
    folds = cpm.request_folds_for_literals([u"Blink", u"Ghost"])
    check("failure.fixture_sha_is_live_generation", sha == _sha_file(os.path.join(G1_DIR, MASTER_NAME)))
    good_payload, good_cov = good_projection(folds)

    def run_with(view, label, prefix):
        broker, released = _fake_broker_for(view)
        adp = _make_adapter(broker=broker)
        expect_unavailable("failure.%s" % label, lambda: adp.query_many([u"Blink", u"Ghost"]), prefix)
        check("failure.%s.lease_released" % label, len(released) == 1)
        check("failure.%s.adapter_state_detached" % label, _state_is_detached(adp))

    ok_view = _FakeView(sha, good_payload, good_cov)
    broker, released = _fake_broker_for(ok_view)
    adp = _make_adapter(broker=broker)
    check("failure.control_fake_view_accepted", sorted(adp.query_many([u"Blink", u"Ghost"]).keys()) == [u"Blink", u"Ghost"])

    run_with(_FakeView(sha, good_payload, good_cov, valid=False), "revoked_authorization", u"authorization-invalid")
    run_with(_FakeView(sha, good_payload, good_cov, consumer_kind="normalizer_compat"), "wrong_consumer", u"projection-invalid")
    wrong_contract = dict(good_payload)
    wrong_contract["contract"] = u"cpm-compat-v0"
    run_with(_FakeView(sha, wrong_contract, good_cov), "wrong_contract", u"projection-invalid")
    omitted_payload = {"contract": good_payload["contract"],
                       "families_by_fold": {u"blink": good_payload["families_by_fold"][u"blink"]}}
    omitted_cov = views.CoverageDescriptor({u"blink": good_cov.lookup(u"blink")})
    run_with(_FakeView(sha, omitted_payload, omitted_cov), "omitted_coverage", u"projection-invalid")
    uncovered_cov = views.CoverageDescriptor({u"blink": good_cov.lookup(u"blink"),
                                              u"ghost": views.CoverageResult(views.UNCOVERED, None, None)})
    run_with(_FakeView(sha, good_payload, uncovered_cov), "uncovered_state", u"projection-invalid")
    mismatch_cov = views.CoverageDescriptor({u"blink": views.CoverageResult(views.MASTER_UNKNOWN, None, None),
                                             u"ghost": good_cov.lookup(u"ghost")})
    run_with(_FakeView(sha, good_payload, mismatch_cov), "coverage_payload_disagree", u"projection-invalid")
    run_with(_FakeView(sha, {"contract": u"cpm-compat-v1", "families_by_fold": [1, 2]}, good_cov), "malformed_payload", u"projection-invalid")
    broken = {"contract": good_payload["contract"], "families_by_fold": dict(good_payload["families_by_fold"])}
    blink = dict(broken["families_by_fold"][u"blink"])
    del blink["spellings"]
    broken["families_by_fold"][u"blink"] = blink
    run_with(_FakeView(sha, broken, good_cov), "interpretation_failure", u"projection-invalid")
    run_with(_FakeView(u"f" * 64, good_payload, good_cov), "view_generation_differs", u"generation-mismatch")

    missing_broker = _ProxyBroker(_broker(), acquire_or_reuse_views=lambda *a, **k: {})
    expect_unavailable("failure.view_missing", lambda: _make_adapter(broker=missing_broker).query_many([u"Blink"]), u"view-missing")

    def refuse(view):
        raise RuntimeError("fixture lease refusal")
    refusing = _ProxyBroker(_broker(), lease_view=refuse)
    expect_unavailable("failure.lease_refused", lambda: _make_adapter(broker=refusing).query_many([u"Blink"]), u"lease-refused")
    _no_outstanding("lease_refused")

    real = _broker()

    def failing_release(lease):
        raise RuntimeError("fixture release failure")
    before_registry = real.unreleased_lease_count()
    releasing = _ProxyBroker(real, release_view_lease=failing_release)
    expect_unavailable("failure.lease_release_failure", lambda: _make_adapter(broker=releasing).query_many([u"Blink"]),
                       u"lease-release-failed")
    check("failure.lease_release_failure.durably_registered", real.unreleased_lease_count() == before_registry + 1)
    real.retry_unreleased_leases()
    check("failure.lease_release_failure.reconciled", real.unreleased_lease_count() == before_registry)
    _no_outstanding("after_release_reconcile")

    # Exceptions carry no view/lease through traceback frames or context
    # (real DetachedView/ViewLease objects: the validation failure happens
    # after a real lease was taken).
    adp = _make_adapter(broker=_dropping_fold_broker(u"ghost"))
    try:
        adp.query_many([u"Blink", u"Ghost"])
        held = None
    except adapter_mod.CpmAuthorityUnavailable as exc:
        tb = sys.exc_info()[2]
        held = _tb_holds_view_or_lease(tb)
        context = getattr(exc, "__context__", None)
        cause = getattr(exc, "__cause__", None)
        tb = None
    check("retention.failure_traceback_holds_no_view_or_lease", held is False)
    check("retention.failure_has_no_exception_context", context is None and cause is None)

    corrupt = _make_adapter(CORRUPT_DIR)
    exc = expect_unavailable("failure.invalid_authority_rejected", lambda: corrupt.query_many([u"Blink"]), u"acquisition-failed:")
    check("failure.invalid_authority_reason", exc is not None, exc.reason if exc is not None else None)
    _no_outstanding("invalid_authority")
    missing = adapter_mod.CpmAuthorityAdapter(_broker(), os.path.join(FIXTURE_ROOT, "absent", MASTER_NAME),
                                              shipped_root=os.path.join(FIXTURE_ROOT, "absent"))
    expect_unavailable("failure.unreadable_master_rejected", missing.generation_descriptor, u"observation-failed")


class _NamedBase(object):
    pass


def _Named(name):
    return type(name, (_NamedBase,), {})()


def good_projection(folds):
    """A well-formed cpm_compat_v1 payload/coverage built by the Step 1
    builder from a stub provider (Blink resolved x3, everything else
    MasterUnknown). Used only to construct fake views for failure tests."""
    class _Stub(object):
        def wrapper_path(self):
            return u"groupFile"

        def lookup_fold(self, query):
            if query == b"blink":
                hit = _Named("Hit")
                hit.destination = u"groupFile/Face/Eyes"
                rows = [{"literal": s, "full_path": u"groupFile/Face/Eyes"} for s in (u"Blink", u"Blink", u"BLINK")]
                hit.occurrences = lambda: list(rows)
                return hit
            return _Named("MasterUnknown")
    payload, coverage, _ = cpm.build_cpm_compat_v1_projection(folds)(_Stub())
    return payload, coverage


# ---------------------------------------------------------------------------
# Parts F, J -- health, small Master, advisory
# ---------------------------------------------------------------------------

def section_health(oracle):
    adapter = _make_adapter()
    health = adapter.assess_health(_live_literals())
    check("health.small_valid_master_healthy", health["status"] == u"healthy", health.get("reason"))
    check("health.reason", health["reason"] == u"canonical-admission-and-view-validated")
    check("health.small_master_below_legacy_thresholds",
          G1_OCCURRENCES < oracle["PROD_MASTER_HEALTH_MIN_OCCURRENCES"]
          and G1_FOLD_FAMILIES < oracle["PROD_MASTER_HEALTH_MIN_FOLD_FAMILIES"])
    legacy_descriptor = {"valid": True, "provider_kind": oracle["SEMANTIC_PROVIDER_KIND_MASTER_SIDECAR"],
                         "occurrence_count": G1_OCCURRENCES, "fold_family_count": G1_FOLD_FAMILIES}
    legacy = oracle["prod_semantic_provider_health_from_descriptor"](legacy_descriptor)
    check("health.legacy_gate_would_reject_same_master", legacy["status"] == u"degraded"
          and legacy["reason"] == u"master-too-small", _canon([legacy["status"], legacy["reason"]]))
    legacy_on_adapter = oracle["prod_semantic_provider_health_from_descriptor"](adapter.generation_descriptor())
    check("health.legacy_gate_not_applicable_to_adapter_descriptor",
          legacy_on_adapter["reason"] == u"provider-kind-not-qualified")
    check("health.advisory_counts", health["advisory"] == {
        "requested_literal_count": 17, "master_unknown_literal_count": 3, "many_unrecognized": False},
        _canon(health["advisory"]))
    many = [u"Unknown%02d" % i for i in range(25)] + [u"Blink"]
    many_health = adapter.assess_health(many)
    check("health.many_unrecognized_is_advisory_only", many_health["status"] == u"healthy"
          and many_health["advisory"]["many_unrecognized"] is True)
    ghost = adapter.query_many([u"Ghost"])[u"Ghost"]
    check("health.healthy_master_unknown_is_genuine_absence",
          ghost["status"] == u"absent" and ghost["match_kind"] == u"none")
    wink = adapter.query_many([u"Wink"])[u"Wink"]
    check("health.healthy_conflict_is_not_absence", wink["status"] == u"conflict")
    bad = _make_adapter(CORRUPT_DIR).assess_health([u"Blink"])
    check("health.invalid_authority_unavailable", bad["status"] == u"unavailable" and bad["descriptor"] is None
          and bad["reason"].startswith(u"acquisition-failed:"), _canon([bad["status"], bad["reason"]]))
    uncovered_broker = _dropping_fold_broker(u"ghost")
    uncovered = _make_adapter(broker=uncovered_broker).assess_health([u"Blink", u"Ghost"])
    check("health.uncovered_request_unavailable", uncovered["status"] == u"unavailable"
          and uncovered["reason"] == u"projection-invalid", _canon([uncovered["status"], uncovered["reason"]]))
    _no_outstanding("health")


def _dropping_fold_broker(dropped):
    """Real broker, but the published view silently omits one requested
    fold (a real Uncovered request)."""
    real = _broker()

    def acquire(master_path, specs, **kwargs):
        (kind, (folds, _)), = list(specs.items())
        narrowed = frozenset(folds) - frozenset([dropped])
        return real.acquire_or_reuse_views(master_path, {kind: (narrowed, cpm.build_cpm_compat_v1_projection(narrowed))}, **kwargs)
    return _ProxyBroker(real, acquire_or_reuse_views=acquire)


# ---------------------------------------------------------------------------
# Part H -- freshness
# ---------------------------------------------------------------------------

def section_freshness():
    literals = [u"Blink", u"Ghost", u"Wink"]
    sha1 = _sha_file(os.path.join(G1_DIR, MASTER_NAME))
    sha2 = _sha_file(os.path.join(G2_DIR, MASTER_NAME))
    adapter = _make_adapter()
    check("freshness.fixture_generations_differ", sha1 != sha2 and _sha_file(_live_master()) == sha1)
    prov = adapter.verify_current_generation(sha1, literals)
    check("freshness.same_generation_succeeds", prov["compatibility_identity"] == cpm.compatibility_identity(
        sha1, adapter_mod.CPM_SEMANTIC_POLICY_REVISION))
    check("freshness.provenance_detached", sorted(prov.keys()) == ["compatibility_identity", "provider_capture"]
          and "diagnostics" not in prov["provider_capture"] and prov["provider_capture"]["provider_generation"] == 1)
    adapter.verify_current_generation(sha1, literals)
    check("freshness.same_generation_cache_hit", _broker().recent_diagnostics()[-1]["event"] == "fully_reused_no_provider_open")
    adapter.generation_descriptor()
    _copy_dir_files(G2_DIR, LIVE_DIR)
    try:
        expect_unavailable("freshness.changed_generation_mismatch",
                           lambda: adapter.verify_current_generation(sha1, literals), u"generation-mismatch",
                           adapter_mod.CpmGenerationMismatch)
        expect_unavailable("freshness.pinned_query_rejects_new_generation",
                           lambda: adapter.query_many(literals), u"generation-mismatch", adapter_mod.CpmGenerationMismatch)
        check("freshness.pin_not_moved_to_g2", adapter.pinned_generation() == sha1)
        prov2 = adapter.verify_current_generation(sha2, literals)
        check("freshness.new_generation_verifiable_explicitly", prov2["compatibility_identity"][1] == sha2)
        _no_outstanding("freshness_g2")
        stale_dir = os.path.join(FIXTURE_ROOT, "stale")
        _copy_dir_files(G1_DIR, stale_dir)
        shutil.copyfile(os.path.join(G2_DIR, MASTER_NAME), os.path.join(stale_dir, MASTER_NAME))
        stale = _make_adapter(stale_dir)
        # A fold set never acquired for G2, so no cached G2 view can answer it.
        exc = expect_unavailable("freshness.stale_sidecar_unavailable", lambda: stale.query_many([u"Tail", u"Thigh"]),
                                 u"acquisition-failed:")
        check("freshness.stale_sidecar_reason", exc is not None, exc.reason if exc is not None else None)
    finally:
        _copy_dir_files(G1_DIR, LIVE_DIR)
    check("freshness.g1_restored", _sha_file(_live_master()) == sha1)
    check("freshness.g1_verifiable_again", adapter.verify_current_generation(sha1, literals)["compatibility_identity"][1] == sha1)
    try:
        adapter.verify_current_generation(u"xyz", literals)
        rejected = False
    except cpm.CpmProjectionError:
        rejected = True
    check("freshness.invalid_expected_sha_rejected", rejected)
    _no_outstanding("freshness")


# ---------------------------------------------------------------------------
# Part I -- snapshot / signature parity
# ---------------------------------------------------------------------------

def oracle_answers_via_real_broker(oracle, literals):
    """G18AN _answer_from_result applied to real provider results under the
    real broker (Hit/MasterUnknown). FoldConflict literals are recorded as
    rejected by G18AN."""
    from sfm_master_authority_productionized import views
    folds = cpm.request_folds_for_literals(literals)
    by_fold = {}
    for lit in literals:
        by_fold.setdefault(cpm.cpm_fold(lit), []).append(lit)
    out = {}
    rejected = []

    class _Self(object):
        pass

    def probe(provider):
        me = _Self()
        me._wrapper = provider.wrapper_path()
        entries = {}
        for folded in sorted(folds):
            result = provider.lookup_fold(cpm.fold_to_lookup_bytes(folded))
            for lit in by_fold[folded]:
                if type(result).__name__ == "FoldConflict":
                    try:
                        oracle["_answer_from_result"](me, lit, result)
                    except RuntimeError:
                        rejected.append(lit)
                else:
                    out[lit] = oracle["_answer_from_result"](me, lit, result)
            entries[folded] = views.CoverageResult(views.MASTER_UNKNOWN, None, None)
        return {"probe": True}, views.CoverageDescriptor(entries), 1024
    probe.declared_request_folds = folds
    probe.declared_request_scale = len(folds)
    _broker().acquire_or_reuse_views(_live_master(), {"cpm_step2a_oracle_probe": (folds, probe)},
                                     shipped_root=LIVE_DIR, expected_generation=_sha_file(_live_master()))
    return out, sorted(rejected)


def section_snapshot_parity(oracle, adapter_answers):
    literals = _live_literals()
    oracle_answers, rejected = oracle_answers_via_real_broker(oracle, literals)
    check("parity.g18an_rejects_conflict_results", rejected == sorted(CONFLICT_ANSWERS.keys()), _canon(rejected))
    expected_answers = dict(oracle_answers)
    expected_answers.update(CONFLICT_ANSWERS)
    check("parity.oracle_covers_all_literals", sorted(expected_answers.keys()) == literals)
    for lit in literals:
        tag = lit.encode("unicode_escape").decode("ascii")
        check("parity.answer %s" % tag, _canon(adapter_answers[lit]) == _canon(expected_answers[lit]),
              _canon(adapter_answers[lit]))

    bindings = _bindings(LIVE_BINDINGS)
    snap_fn = oracle["semantic_snapshot_from_live_vocabulary"]
    sig_fn = oracle["semantic_snapshot_signature"]
    snap_expected = snap_fn(bindings, expected_answers)
    snap_adapter = snap_fn(bindings, adapter_answers)
    check("parity.snapshot_identical", _canon(snap_adapter) == _canon(snap_expected))
    sig_expected = sig_fn(snap_expected)
    sig_adapter = sig_fn(snap_adapter)
    # G18AN hashes repr(rows); repr of text differs between Python 2 and 3,
    # so the signature VALUE is interpreter-specific (the Python 2.7.5 value
    # is the one real SFM produces). Equality is checked per interpreter;
    # the raw value is printed, not placed in the cross-interpreter digest.
    check("parity.signature_identical", sig_adapter == sig_expected)
    print("      semantic_snapshot_signature (%s) = %s" % (sys.version.split()[0], sig_adapter))
    pure_expected = [oracle["prod_pure_semantic_row"](r) for r in snap_expected["rows"]]
    pure_adapter = [oracle["prod_pure_semantic_row"](r) for r in snap_adapter["rows"]]
    check("parity.pure_rows_identical", _canon(pure_adapter) == _canon(pure_expected))
    check("parity.counts_hand_audit", snap_adapter["counts"] == EXPECTED_COUNTS, _canon(snap_adapter["counts"]))
    check("parity.accepted_expression", snap_adapter["accepted_expression_literals"] ==
          [u"Blink", u"Brow Up", u"bLiNk", u"jawopen", u"ÑOSE"], _canon(snap_adapter["accepted_expression_literals"]))
    check("parity.accepted_body", snap_adapter["accepted_body_literals"] == [u"Belly", u"chest"],
          _canon(snap_adapter["accepted_body_literals"]))
    rows = dict((r["literal"], r) for r in snap_adapter["rows"])
    for lit, (status, match, cls, op) in sorted(EXPECTED_ROWS.items()):
        r = rows[lit]
        tag = lit.encode("unicode_escape").decode("ascii")
        check("parity.row_hand_audit %s" % tag,
              (r["semantic_status"], r["match_kind"], r["semantic_class"], r["operation"]) == (status, match, cls, op),
              _canon([r["semantic_status"], r["match_kind"], r["semantic_class"], r["operation"]]))
    check("parity.row_order_sorted", [r["literal"] for r in snap_adapter["rows"]] == literals)
    check("parity.ambiguity_and_shapes", rows[u"Hips"]["binding_ambiguous"] and rows[u"Hips"]["live_shapes"] == [u"hips_a", u"hips_b"]
          and rows[u"Smile"]["live_binding_count"] == 2 and rows[u"Smile"]["live_shapes"] == [u"smile"])
    check("parity.spellings_destinations", rows[u"bLiNk"]["master_spellings"] == [u"BLINK", u"Blink"]
          and rows[u"Wink"]["destinations"] == [u"Body Morphs", u"Face/Eyes"] and rows[u"Wink"]["resolved_path"] is None
          and rows[u"Tail"]["resolved_path"] == u"Other/Misc/Deep" and rows[u"Skirt"]["resolved_path"] == u"Clothing")
    check("parity.duplicate_occurrences_counted", adapter_answers[u"Blink"]["occurrence_count"] == 3)

    shuffled = list(reversed(bindings))
    check("parity.input_order_independent", sig_fn(snap_fn(shuffled, adapter_answers)) == sig_adapter)
    bumped = dict((k, dict(v)) for k, v in adapter_answers.items())
    bumped[u"Blink"]["occurrence_count"] = 99
    check("parity.occurrence_count_not_in_signature", sig_fn(snap_fn(bindings, bumped)) == sig_adapter)
    flipped = dict((k, dict(v)) for k, v in adapter_answers.items())
    flipped[u"bLiNk"]["match_kind"] = u"exact"
    check("parity.signature_detects_match_kind_change", sig_fn(snap_fn(bindings, flipped)) != sig_adapter)
    reordered = dict((k, dict(v)) for k, v in adapter_answers.items())
    reordered[u"bLiNk"]["spellings"] = list(reversed(reordered[u"bLiNk"]["spellings"]))
    check("parity.signature_detects_spelling_order_change", sig_fn(snap_fn(bindings, reordered)) != sig_adapter)

    # The real G18AN semantic_snapshot_for_model_row consumes the adapter unchanged.
    oracle["p01_all_supported_flex_bindings"] = lambda animset: _bindings(LIVE_BINDINGS)
    adapter = _make_adapter()
    row = {"animset": object(), "model": u"models/fixture.mdl", "checksum": 1, "animset_name": u"fixture", "gm": None}
    result = oracle["semantic_snapshot_for_model_row"](row, adapter)
    check("parity.g18an_snapshot_for_model_row_accepts_adapter", result["signature"] == sig_adapter)
    check("parity.g18an_snapshot_for_model_row_descriptor", result["provider_descriptor"] == adapter.generation_descriptor())
    try:
        oracle["semantic_snapshot_for_model_row"](row, None)
        called = False
    except _NotCalled:
        called = True
    check("parity.oracle_harness_blocks_global_provider", called)
    _no_outstanding("snapshot_for_model_row")

    # Same-fold / different-exact-query reuse, carried through to the G18AN
    # snapshot: B is answered from the cached family view A acquired.
    reuse = _make_adapter()
    reuse.query_many([u"Blink"])
    opens = _broker().provider_counters()["total_provider_opens"]
    answer_b = reuse.query_many([u"bLiNk"])
    check("parity.reuse_no_provider_open", _broker().provider_counters()["total_provider_opens"] == opens
          and _broker().recent_diagnostics()[-1]["event"] == "fully_reused_no_provider_open")
    b_bindings = _bindings([(u"bLiNk", u"blink_mixed")])
    check("parity.reuse_snapshot_signature_matches_oracle",
          sig_fn(snap_fn(b_bindings, answer_b)) == sig_fn(snap_fn(b_bindings, {u"bLiNk": expected_answers[u"bLiNk"]}))
          and answer_b[u"bLiNk"]["match_kind"] == u"ascii-fold")

    # Fit target-side warning parity: the real G18AN classifier, fed by the
    # adapter vs. by oracle answers (exact Body Morphs / Clothing only).
    class _OracleProvider(object):
        def query_many(self, literals):
            return dict((lit, dict(expected_answers[lit])) for lit in literals)
    targets = [{"literal": lit, "shape": u"t_" + lit, "global_key": u"k%02d" % i}
               for i, lit in enumerate([u"Belly", u"Skirt", u"Shirt", u"Tail", u"Wink", u"Ghost", u"chest", u"Hips"])]
    mapping = {"mappings": [{"target": {"global_key": u"k07"}}]}
    warn_fn = oracle["p03_unmapped_relevant_controls"]
    via_adapter = warn_fn({"provider": _make_adapter()}, targets, mapping)
    via_oracle = warn_fn({"provider": _OracleProvider()}, targets, mapping)
    check("parity.fit_warning_matches_oracle", _canon(via_adapter) == _canon(via_oracle))
    check("parity.fit_warning_hand_audit", [(r["master_path"], r["literal"]) for r in via_adapter] ==
          [(u"Body Morphs", u"Belly"), (u"Body Morphs", u"chest"), (u"Clothing", u"Skirt")], _canon(via_adapter))
    _no_outstanding("fit_warning")


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def run_suite():
    oracle = load_g18an_oracle()
    section_bootstrap()
    section_no_development_paths()
    adapter, answers = section_facade(oracle)
    section_failure_mapping()
    section_health(oracle)
    section_freshness()
    section_snapshot_parity(oracle, answers)
    _no_outstanding("suite_end")


def write_digest(path):
    records = [[name, ok, _canon(value)] for name, ok, value in RESULTS]
    body = json.dumps(records, sort_keys=True, ensure_ascii=True, indent=0, separators=(",", ":"))
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_TEXT(body))
    print("digest: %s sha256=%s checks=%d" % (os.path.basename(path),
                                              hashlib.sha256(body.encode("utf-8")).hexdigest(), len(records)))


def _require_setup_checks():
    if not all(r[1] for r in RESULTS):
        print("RESULT: setup failed")
        sys.exit(1)
    del RESULTS[:]


def _write_master(directory, body):
    os.makedirs(directory)
    path = os.path.join(directory, MASTER_NAME)
    with open(path, "wb") as f:
        f.write(body.encode("utf-8"))
    return path


def phase_publish():
    if os.path.isdir(FIXTURE_ROOT):
        shutil.rmtree(FIXTURE_ROOT)
    os.makedirs(FIXTURE_ROOT)
    from sfm_master_sidecar import publisher
    for directory, body in ((G1_DIR, MASTER_G1), (G2_DIR, MASTER_G2)):
        result = publisher.publish(_write_master(directory, body), directory)
        check("publish.%s" % os.path.basename(directory), os.path.isfile(str(result.generation_path)))
    _copy_dir_files(G1_DIR, LIVE_DIR)
    result = publisher.publish(_write_master(CORRUPT_DIR, MASTER_CORRUPT), CORRUPT_DIR)
    check("publish.corrupt_source", os.path.isfile(str(result.generation_path)))
    artifacts = [n for n in os.listdir(CORRUPT_DIR) if n.endswith(".sfmsidecar")]
    check("publish.corrupt_fixture_artifact", len(artifacts) == 1)
    path = os.path.join(CORRUPT_DIR, artifacts[0])
    with open(path, "rb") as f:
        data = bytearray(f.read())
    data[len(data) // 2] ^= 0xFF
    with open(path, "wb") as f:
        f.write(bytes(data))
    _require_setup_checks()
    run_suite()
    write_digest(DIGEST_PY3)


def phase_suite():
    check("suite.fixture_present", os.path.isfile(_live_master()) and os.path.isfile(DIGEST_PY3))
    _require_setup_checks()
    run_suite()
    write_digest(DIGEST_PY27 if PY2 else DIGEST_PY3 + ".rerun")


def phase_compare():
    with io.open(DIGEST_PY3, encoding="utf-8") as f:
        a = f.read()
    with io.open(DIGEST_PY27, encoding="utf-8") as f:
        b = f.read()
    ra, rb = json.loads(a), json.loads(b)
    check("compare.same_check_count", len(ra) == len(rb), [len(ra), len(rb)])
    check("compare.identical_results_and_values", a == b, [x[0] for x, y in zip(ra, rb) if x != y][:10])
    check("compare.all_pass_both", all(x[1] for x in ra) and all(y[1] for y in rb))
    print("py3 digest sha256=%s" % hashlib.sha256(a.encode("utf-8")).hexdigest())
    print("py27 digest sha256=%s" % hashlib.sha256(b.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    phase = None
    for arg in sys.argv[1:]:
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1]
    if phase not in ("publish", "suite", "compare"):
        print("usage: %s --phase=publish|suite|compare" % os.path.basename(sys.argv[0]))
        sys.exit(2)
    print("Interpreter: %s" % sys.version.split()[0])
    print("Phase: %s" % phase)
    {"publish": phase_publish, "suite": phase_suite, "compare": phase_compare}[phase]()
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)
