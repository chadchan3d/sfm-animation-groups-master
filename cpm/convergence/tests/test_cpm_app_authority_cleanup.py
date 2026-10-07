# -*- coding: utf-8 -*-
"""Handoff section 22 item 6 -- historical authority cleanup checks.

Design: cpm/qualification/ITEM6_HISTORICAL_AUTHORITY_CLEANUP_DESIGN.md (sections 5, 7, 8).

Preservation is proven against item6_precleanup_source_manifest.json, generated
from the exact pre-cleanup app bytes (9a78fc96...) before the cleanup edit:
every surviving top-level block and ProdWindow member must keep its pre-cleanup
content and order; only the approved removals disappear; only the approved
exception is added; the snapshot helper differs only by the one approved branch
replacement. The real refusal stub and snapshot helper are executed (not the
canonical-route test's forbidden sentinels).

Usage:
  python test_cpm_app_authority_cleanup.py                  # run the checks
  python test_cpm_app_authority_cleanup.py --write-manifest # pre-cleanup bytes only
"""
from __future__ import print_function

import ast
import copy
import hashlib
import io
import json
import os
import re
import sys
import tokenize

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
APP_PATH = os.environ.get("CPM_TEST_APP_PATH") or os.path.join(_REPO_ROOT, "cpm", "app", "SFM_Character_Preset_Manager.py")
MANIFEST_PATH = os.path.join(_THIS_DIR, "item6_precleanup_source_manifest.json")
PRE_CLEANUP_SHA256 = "9a78fc9692cfa3cae5f3d8443a6c95537248c348d0cd4230c7ba744d99e77900"
MANIFEST_SHA256 = "a92647949f26f02c65497b4f0e808413edbe54af72eec8b1bee65798cdd2c6ae"
PY2 = sys.version_info[0] == 2
_TEXT = unicode if PY2 else str  # noqa: F821

# --- Approved dispositions (design sections 5 and 7) -------------------------
REMOVED_TOP = [
    "p01_ascii_fold", "p01_tokenize_master", "p01_parse_occurrences", "SemanticProvider",
    "MasterTxtSemanticProvider", "g18p_sha256_file", "g18p_sidecar_deploy_dir", "g18p_find_sidecar_artifact",
    "g18p_sidecar_dependency_discovery", "g18an_find_file_by_sha", "g18an_verified_sidecar_paths",
    "g18an_import_frozen_sidecar_provider", "g18an_normalize_sidecar_path", "SidecarSemanticProvider",
    "g18an_ascii_case_variant", "g18an_semantic_parity_for_row", "g18an_scope_decision_view",
    "g18an_scope_signature", "g18an_accepted_from_scope", "g18an_flex_plan_signature", "g18an_preset_decisions",
    "g18an_clothing_plan_signature", "g18an_clothing_decisions", "g18an_decision_parity_for_row",
    "acquire_semantic_provider_for_mode", "invalidate_semantic_provider", "p01_provider_answer_signature",
    "p01_synthetic_provider_contract", "semantic_snapshots_for_current_shot",
    "prod_semantic_provider_health_from_descriptor", "prod_provider_health_selftest",
]
REMOVED_CONSTANTS = [
    "SEMANTIC_PROVIDER_MODE_TXT", "SEMANTIC_PROVIDER_MODE_AUTO", "G18P_MASTER_SHA256",
    "G18P_SIDECAR_ARTIFACT_SHA256", "G18P_SIDECAR_FORMAT_SHA256", "G18P_R1D_VALIDATOR_SHA256",
    "G18P_R1D_PROVIDER_SHA256", "PROD_MASTER_HEALTH_MIN_OCCURRENCES", "PROD_MASTER_HEALTH_MIN_FOLD_FAMILIES",
    "P01SemanticProvider", "P01MasterTxtProvider",
]
REMOVED_METHODS = ["g18an_run_decision_parity"]
CHANGED_TOP = ["get_semantic_provider", "semantic_snapshot_for_model_row"]
ADDED_TOP = ["ProdHistoricalAuthorityDisabled"]
RETAINED_CONSTANTS = [
    "SEMANTIC_PROVIDER_MODE_SIDECAR", "SEMANTIC_PROVIDER_FORCE_MODE", "G18AN_PARITY_SHORTCUT",
    "SEMANTIC_PROVIDER_KIND_MASTER_TXT", "SEMANTIC_PROVIDER_KIND_MASTER_SIDECAR", "P01_PROVIDER_KIND",
    "SEMANTIC_PROVIDER_CONTRACT", "SEMANTIC_PROVIDER_FOLD_POLICY", "SEMANTIC_PROVIDER_MASTER_FILENAME",
    "SEMANTIC_STATUS_RESOLVED", "SEMANTIC_STATUS_CONFLICT", "SEMANTIC_STATUS_ABSENT", "SEMANTIC_STATUS_UNAVAILABLE",
    "SEMANTIC_MATCH_EXACT", "SEMANTIC_MATCH_FOLDED", "SEMANTIC_MATCH_NONE", "P01_PROVIDER_CONTRACT",
    "P01_FOLD_POLICY", "P01_MASTER_FILENAME", "P01_STATUS_RESOLVED", "P01_STATUS_CONFLICT", "P01_STATUS_ABSENT",
    "P01_STATUS_UNAVAILABLE", "P01_MATCH_EXACT", "P01_MATCH_FOLDED", "P01_MATCH_NONE",
    "_SEMANTIC_PROVIDER", "_SEMANTIC_PROVIDER_OPEN_COUNT", "_SEMANTIC_PROVIDER_REUSE_COUNT",
    "_SEMANTIC_PROVIDER_INVALIDATION_COUNT", "_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT",
    "_SEMANTIC_PROVIDER_GENERATION", "PROD_Q1_INDEXED_CAPTURE_PARITY", "PROD_MASTER_REVIEW_WARNING_THRESHOLD",
    "PROD_MASTER_PROVIDER_WARNING_COPY", "PROD_MASTER_REVIEW_WARNING_COPY", "PROD_SEMANTIC_POLICY",
    "P01_MODEL_PATH", "P01_MODEL_CHECKSUM",
]
RETAINED_TOP = ["get_semantic_provider", "semantic_snapshot_for_model_row", "semantic_provider_runtime_stats",
                "ProdCpmUnmigratedProvider", "prod_cpm_unmigrated_authority", "ProdCpmAuthorityNotMigrated",
                "p01_master_path", "prod_provider_capture", "p02_complete_scope", "g11a_source", "StartProdTool"]
DISABLED_MESSAGE = u"Historical semantic-provider acquisition is disabled; use the canonical CPM authority route."
MISSING_PROVIDER_MESSAGE = u"Semantic snapshot requires an explicitly supplied authority provider."
SNAPSHOT_ORIGINAL_BRANCH = (u"    if provider is None:\n"
                            u"        provider = get_semantic_provider()\n")
SNAPSHOT_REPLACEMENT_BRANCH = (u"    if provider is None:\n"
                               u"        raise RuntimeError(\n"
                               u"            \"%s\"\n"
                               u"        )\n" % MISSING_PROVIDER_MESSAGE)
OTHER_CPM_EXCEPTIONS = ["ProdCpmAuthorityBootstrapError", "ProdCpmAuthorityNotMigrated",
                        "ProdCpmOperationAuthorityError", "ProdCpmFitStop", "ProdRecoveryUnverifiedError"]

RESULTS = []


def check(name, condition, value=None):
    RESULTS.append((name, bool(condition)))
    print("[%s] %s" % ("PASS" if condition else "FAIL", name))
    if not condition and value is not None:
        print("      value: %r" % (value,))


# --- Source segmentation (interpreter-independent) ---------------------------

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_text_statement(node):
    value = getattr(node, "value", None)
    return isinstance(node, ast.Expr) and type(value).__name__ in ("Str", "Constant") and isinstance(
        getattr(value, "s", getattr(value, "value", None)), (_TEXT, str))


def _is_trivia(line):
    stripped = line.strip()
    return not stripped or stripped.startswith(u"#")


def _segments(nodes, lines, lo, hi):
    """(node, start, text) for each node of a body spanning lines lo..hi.

    A node ends where the next begins; leading and trailing blank/comment-only
    lines are trimmed, so inter-block comments belong to no block. Python 2.7
    reports a multi-line string statement at its last line, so a leading string
    statement starts at the region start; any other string statement is
    unsupported (fail loudly rather than hash interpreter-dependent text)."""
    starts = []
    for i, node in enumerate(nodes):
        if _is_text_statement(node):
            if i != 0:
                raise RuntimeError("unsupported non-leading string statement at line %d" % node.lineno)
            start = lo
        else:
            start = node.lineno
            if getattr(node, "decorator_list", None):
                start = min([d.lineno for d in node.decorator_list] + [start])
        starts.append(start)
    out = []
    for i, node in enumerate(nodes):
        end = starts[i + 1] - 1 if i + 1 < len(nodes) else hi
        block = lines[starts[i] - 1:end]
        while block and _is_trivia(block[0]):
            block.pop(0)
        while block and _is_trivia(block[-1]):
            block.pop()
        out.append((node, starts[i], u"\n".join(block) + u"\n"))
    return out


def _describe(node, text):
    if isinstance(node, ast.FunctionDef):
        kind, names = "def", [node.name]
    elif isinstance(node, ast.ClassDef):
        kind, names = "class", [node.name]
    elif isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
        kind, names = "assign", [t.id for t in node.targets]
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        kind, names = "import", [a.asname or a.name for a in node.names]
    else:
        kind, names = "other", []
    return {"kind": kind, "names": names, "head": text.split(u"\n")[0].strip()[:100], "sha256": _sha(text)}


class Source(object):
    def __init__(self, raw):
        self.raw = raw
        self.lines = raw.decode("utf-8").split(u"\n")
        self.tree = ast.parse(raw)
        self.top = _segments(self.tree.body, self.lines, 1, len(self.lines))
        self.by_name = {}
        for i, (node, start, text) in enumerate(self.top):
            for name in _describe(node, text)["names"]:
                self.by_name[name] = (node, start, text, i)

    def describe_top(self):
        return [_describe(node, text) for node, _, text in self.top]

    def class_members(self, name):
        node, start, text, i = self.by_name[name]
        hi = self.top[i + 1][1] - 1 if i + 1 < len(self.top) else len(self.lines)
        first = node.body[0]
        header_lines = self.lines[start - 1:(first.lineno if not _is_text_statement(first) else node.lineno + 1) - 1]
        header = u"\n".join(l for l in header_lines if not _is_trivia(l)) + u"\n"
        members = _segments(node.body, self.lines, node.lineno + 1, hi)
        return _sha(header), [_describe(n, t) for n, _, t in members], dict(
            (_describe(n, t)["names"][0], t) for n, _, t in members if _describe(n, t)["names"])


def build_manifest(raw):
    src = Source(raw)
    header_sha, members, _ = src.class_members("ProdWindow")
    return {
        "schema": "cpm-item6-precleanup-source-manifest-v1",
        "app_relative_path": "cpm/app/SFM_Character_Preset_Manager.py",
        "app_sha256": hashlib.sha256(raw).hexdigest(),
        "segmentation": ("top-level statements and ProdWindow members in source order; each block runs from "
                         "its start (decorators included) to the next statement, with leading/trailing blank "
                         "and comment-only lines trimmed; sha256 of the UTF-8 block text; line numbers are "
                         "not recorded"),
        "top_level": src.describe_top(),
        "classes": {"ProdWindow": {"header_sha256": header_sha, "members": members}},
        "approved": {
            "removed_top": REMOVED_TOP, "removed_constants": REMOVED_CONSTANTS,
            "removed_methods": REMOVED_METHODS, "changed_top": CHANGED_TOP, "added_top": ADDED_TOP,
            "snapshot_branch": {"original": SNAPSHOT_ORIGINAL_BRANCH, "replacement": SNAPSHOT_REPLACEMENT_BRANCH},
            "disabled_message": DISABLED_MESSAGE, "missing_provider_message": MISSING_PROVIDER_MESSAGE,
        },
    }


def write_manifest():
    with open(APP_PATH, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PRE_CLEANUP_SHA256:
        raise SystemExit("REFUSED: the app is not the exact pre-cleanup bytes (%s)" % digest)
    if os.path.exists(MANIFEST_PATH):
        raise SystemExit("REFUSED: %s already exists (never regenerate it)" % MANIFEST_PATH)
    data = json.dumps(build_manifest(raw), indent=1, sort_keys=True, ensure_ascii=True,
                      separators=(",", ": ")) + "\n"
    with open(MANIFEST_PATH, "wb") as f:
        f.write(data.encode("ascii"))
    print("manifest written: sha256=%s" % hashlib.sha256(data.encode("ascii")).hexdigest())


# --- Checks -----------------------------------------------------------------

def _removed_entry(entry):
    if entry["kind"] in ("def", "class") and entry["names"][0] in REMOVED_TOP:
        return True
    return entry["kind"] == "assign" and entry["names"] and set(entry["names"]) <= set(REMOVED_CONSTANTS)


def section_manifest():
    with open(MANIFEST_PATH, "rb") as f:
        raw = f.read().replace(b"\r\n", b"\n")   # immune to checkout line-ending conversion
    check("manifest.sha256_pinned", hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256,
          hashlib.sha256(raw).hexdigest())
    manifest = json.loads(raw.decode("ascii"))
    approved = manifest["approved"]
    check("manifest.generated_from_precleanup_app", manifest["app_sha256"] == PRE_CLEANUP_SHA256)
    check("manifest.approved_sets_match_design",
          approved["removed_top"] == REMOVED_TOP and approved["removed_constants"] == REMOVED_CONSTANTS
          and approved["removed_methods"] == REMOVED_METHODS and approved["changed_top"] == CHANGED_TOP
          and approved["added_top"] == ADDED_TOP
          and approved["snapshot_branch"] == {"original": SNAPSHOT_ORIGINAL_BRANCH,
                                              "replacement": SNAPSHOT_REPLACEMENT_BRANCH}
          and approved["disabled_message"] == DISABLED_MESSAGE
          and approved["missing_provider_message"] == MISSING_PROVIDER_MESSAGE)
    pre_names = [n for e in manifest["top_level"] for n in e["names"]]
    check("manifest.every_removal_present_before_cleanup",
          all(pre_names.count(n) == 1 for n in REMOVED_TOP + REMOVED_CONSTANTS + CHANGED_TOP)
          and not set(ADDED_TOP) & set(pre_names))
    check("manifest.parity_method_present_before_cleanup",
          [m["names"] for m in manifest["classes"]["ProdWindow"]["members"]].count(REMOVED_METHODS) == 1)
    return manifest


def section_preservation(manifest, src):
    check("candidate.is_not_precleanup_bytes", hashlib.sha256(src.raw).hexdigest() != PRE_CLEANUP_SHA256)
    pre = manifest["top_level"]
    removed = [e for e in pre if _removed_entry(e)]
    check("removal.exact_count", len(removed) == len(REMOVED_TOP) + len(REMOVED_CONSTANTS),
          [e["names"] for e in removed])
    expected = []
    for entry in pre:
        if _removed_entry(entry):
            continue
        if entry["names"] == ["get_semantic_provider"]:
            expected.append({"kind": "class", "names": ADDED_TOP, "sha256": None})
        expected.append(entry)
    cand = src.describe_top()
    shape = lambda seq: [(e["kind"], tuple(e["names"]), e["head"] if e["kind"] == "other" else None) for e in seq]
    exp_shape = [(e["kind"], tuple(e["names"]), e.get("head") if e["kind"] == "other" else None) for e in expected]
    check("preserve.top_level_sequence_exact", shape(cand) == exp_shape,
          [x for x in zip(shape(cand), exp_shape) if x[0] != x[1]][:5] or (len(cand), len(exp_shape)))
    skip = set(CHANGED_TOP) | set(ADDED_TOP) | set(["ProdWindow"])
    drift = [e["names"] or e["head"] for c, e in zip(cand, expected)
             if not (set(e["names"]) & skip) and c["sha256"] != e["sha256"]]
    check("preserve.surviving_top_level_content_unchanged", shape(cand) == exp_shape and not drift, drift[:10])
    # ProdWindow: only the parity method disappears.
    header_sha, members, member_text = src.class_members("ProdWindow")
    pre_cls = manifest["classes"]["ProdWindow"]
    exp_members = [m for m in pre_cls["members"] if m["names"] != REMOVED_METHODS]
    check("preserve.prodwindow_header_unchanged", header_sha == pre_cls["header_sha256"])
    check("preserve.prodwindow_only_parity_method_removed",
          [(m["kind"], m["names"], m["sha256"]) for m in members]
          == [(m["kind"], m["names"], m["sha256"]) for m in exp_members],
          [m["names"] for m, e in zip(members, exp_members) if m != e][:5])
    # The snapshot helper differs only by the approved branch replacement.
    _, _, text, _ = src.by_name["semantic_snapshot_for_model_row"]
    pre_entry = [e for e in pre if e["names"] == ["semantic_snapshot_for_model_row"]][0]
    check("preserve.snapshot_replacement_applied_once",
          text.count(SNAPSHOT_REPLACEMENT_BRANCH) == 1 and SNAPSHOT_ORIGINAL_BRANCH not in text)
    check("preserve.snapshot_reverses_to_precleanup",
          _sha(text.replace(SNAPSHOT_REPLACEMENT_BRANCH, SNAPSHOT_ORIGINAL_BRANCH)) == pre_entry["sha256"])
    return text


def section_structure(src):
    exc = src.by_name.get("ProdHistoricalAuthorityDisabled", (None,))[0]
    stub = src.by_name["get_semantic_provider"][0]
    check("struct.exception_is_direct_runtimeerror_subclass",
          isinstance(exc, ast.ClassDef) and len(exc.bases) == 1 and isinstance(exc.bases[0], ast.Name)
          and exc.bases[0].id == "RuntimeError" and not exc.decorator_list
          and not getattr(exc, "keywords", None))
    body = [n for n in (exc.body if exc is not None else []) if not _is_text_statement(n)]
    check("struct.exception_has_no_custom_behavior", exc is not None and len(body) <= 1
          and all(isinstance(n, ast.Pass) for n in body))
    order = [e["names"] for e in src.describe_top()]
    check("struct.exception_defined_immediately_before_stub",
          order.index(ADDED_TOP) + 1 == order.index(["get_semantic_provider"]))
    args = stub.args
    check("struct.stub_zero_argument_signature",
          not args.args and args.vararg is None and args.kwarg is None and not args.defaults
          and not getattr(args, "kwonlyargs", []) and not stub.decorator_list)
    stmts = [n for n in stub.body if not _is_text_statement(n)]
    raise_ok = False
    if len(stmts) == 1 and isinstance(stmts[0], ast.Raise):
        call = getattr(stmts[0], "exc", None) or getattr(stmts[0], "type", None)
        arg = call.args[0] if isinstance(call, ast.Call) and len(call.args) == 1 else None
        raise_ok = (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "ProdHistoricalAuthorityDisabled" and not call.keywords
                    and arg is not None and getattr(arg, "s", getattr(arg, "value", None)) == DISABLED_MESSAGE)
    check("struct.stub_is_single_unconditional_raise", raise_ok)
    names = set(n.id for n in ast.walk(stub) if isinstance(n, ast.Name))
    check("struct.stub_no_globals_dispatch_or_io",
          not [n for n in ast.walk(stub) if isinstance(n, (ast.Global, ast.If, ast.Call)) and n is not
               (getattr(stmts[0], "exc", None) or getattr(stmts[0], "type", None))]
          and names == set(["ProdHistoricalAuthorityDisabled"]), sorted(names))


class _Probe(object):
    def __init__(self):
        self.events = []

    def recorder(self, label):
        def f(*args, **kwargs):
            self.events.append(label)
            raise AssertionError("unexpected call: %s" % label)
        return f


def _exec(text, ns, label):
    exec(compile(text, label, "exec"), ns)


def section_stub_runtime(src):
    probe = _Probe()
    builtins_mod = __import__("__builtin__" if PY2 else "builtins")
    fake_builtins = dict(vars(builtins_mod))
    fake_builtins["open"] = probe.recorder("open")
    fake_builtins["__import__"] = probe.recorder("__import__")
    if PY2:
        fake_builtins["file"] = probe.recorder("file")
        fake_builtins["execfile"] = probe.recorder("execfile")
    state = {"_SEMANTIC_PROVIDER": None, "_SEMANTIC_PROVIDER_OPEN_COUNT": 0, "_SEMANTIC_PROVIDER_REUSE_COUNT": 0,
             "_SEMANTIC_PROVIDER_INVALIDATION_COUNT": 0, "_SEMANTIC_PROVIDER_PRODUCTION_PARSE_COUNT": 0,
             "_SEMANTIC_PROVIDER_GENERATION": 0}
    ns = dict(state)
    ns["__builtins__"] = fake_builtins
    for name in ("log_line", "prod_cpm_open_adapter", "prod_cpm_import_adapter", "acquire_semantic_provider_for_mode",
                 "SidecarSemanticProvider", "MasterTxtSemanticProvider", "p01_master_path"):
        ns[name] = probe.recorder(name)
    _exec(src.by_name["ProdHistoricalAuthorityDisabled"][2], ns, "app:ProdHistoricalAuthorityDisabled")
    _exec(src.by_name["get_semantic_provider"][2], ns, "app:get_semantic_provider")
    exc_type = ns["ProdHistoricalAuthorityDisabled"]
    caught = None
    for _ in range(2):  # repeated calls stay refusals, with no state
        try:
            ns["get_semantic_provider"]()
        except Exception as exc:  # noqa: BLE001
            caught = exc
    check("stub.raises_dedicated_exception", type(caught) is exc_type and exc_type.__bases__ == (RuntimeError,))
    check("stub.fixed_message", caught is not None and _TEXT(caught) == DISABLED_MESSAGE, _TEXT(caught))
    check("stub.no_io_import_log_or_acquisition", probe.events == [], probe.events)
    check("stub.historical_state_untouched", all(ns[k] == v for k, v in state.items()))
    check("stub.not_a_current_authority_failure", not any(
        n in src.by_name and n != "ProdHistoricalAuthorityDisabled" for n in []) and all(
        not (isinstance(src.by_name[n][0], ast.ClassDef)
             and "ProdHistoricalAuthorityDisabled" in [getattr(b, "id", None) for b in src.by_name[n][0].bases])
        for n in OTHER_CPM_EXCEPTIONS if n in src.by_name))
    return ns


def section_snapshot_runtime(src, helper_text):
    import test_cpm_app_canonical_route as route
    app = route.AppSource(APP_PATH)
    ns = route.build_namespace(app)          # candidate semantic helpers, extracted unmodified
    _exec(src.by_name["ProdHistoricalAuthorityDisabled"][2], ns, "app:ProdHistoricalAuthorityDisabled")
    _exec(src.by_name["get_semantic_provider"][2], ns, "app:get_semantic_provider")   # the REAL stub
    opened = []
    ns["prod_cpm_open_adapter"] = lambda *a, **k: opened.append(a) or (_ for _ in ()).throw(AssertionError("opened"))
    reference = dict(ns)
    _exec(helper_text.replace(SNAPSHOT_REPLACEMENT_BRANCH, SNAPSHOT_ORIGINAL_BRANCH), reference,
          "precleanup:semantic_snapshot_for_model_row")
    face = None
    for candidate in (u"face", u"Face", u"groupFile > Face", u"groupFile > Face > Eyes", u"Face > Eyes"):
        try:
            if ns["p01_is_face_path"](candidate):
                face = candidate
                break
        except Exception:  # noqa: BLE001
            pass
    check("snapshot.fixture_face_path_found", face is not None)
    body = ns["SEMANTIC_BODY_MORPHS_PATH"]
    route.Env.bindings = route._bindings_from_pairs([
        (u"FaceA", u"MONO"), (u"BodyA", u"MONO"), (u"OtherA", u"MONO"), (u"MissA", u"MONO"),
        (u"ConfA", u"MONO"), (u"FoldA", u"STEREO"), (u"Dup", u"MONO"), (u"Dup", u"STEREO"), (u"NoAns", u"MONO")])
    answers = {
        u"FaceA": {"status": ns["P01_STATUS_RESOLVED"], "match_kind": ns["P01_MATCH_EXACT"], "resolved_path": face,
                   "destinations": [face], "spellings": [u"FaceA"]},
        u"BodyA": {"status": ns["P01_STATUS_RESOLVED"], "match_kind": ns["P01_MATCH_EXACT"], "resolved_path": body,
                   "destinations": [body], "spellings": [u"BodyA"]},
        u"OtherA": {"status": ns["P01_STATUS_RESOLVED"], "match_kind": ns["P01_MATCH_EXACT"],
                    "resolved_path": u"groupFile > Unrelated", "destinations": [], "spellings": []},
        u"MissA": {"status": ns["P01_STATUS_ABSENT"], "match_kind": ns["P01_MATCH_NONE"], "resolved_path": None},
        u"ConfA": {"status": ns["P01_STATUS_CONFLICT"], "match_kind": ns["P01_MATCH_NONE"], "resolved_path": None,
                   "destinations": [face, body]},
        u"FoldA": {"status": ns["P01_STATUS_RESOLVED"], "match_kind": ns["P01_MATCH_FOLDED"], "resolved_path": body,
                   "destinations": [body], "spellings": [u"folda"]},
        u"Dup": {"status": ns["P01_STATUS_RESOLVED"], "match_kind": ns["P01_MATCH_EXACT"], "resolved_path": face},
    }

    class Provider(object):
        def __init__(self, valid=True):
            self.valid = valid
            self.queries = []

        def generation_descriptor(self):
            return {"valid": self.valid, "source_sha256": u"fixture", "provider_generation": 1}

        def query_many(self, literals):
            self.queries.append(list(literals))
            return dict((k, copy.deepcopy(v)) for k, v in answers.items() if k in literals)

    row = {"animset": object(), "model": u"models/fixture.mdl", "checksum": 7, "animset_name": u"fixture", "gm": None}
    missing = None
    try:
        ns["semantic_snapshot_for_model_row"](row)
    except Exception as exc:  # noqa: BLE001
        missing = exc
    check("snapshot.missing_provider_explicit_refusal",
          type(missing) is RuntimeError and _TEXT(missing) == MISSING_PROVIDER_MESSAGE, repr(missing))
    check("snapshot.missing_provider_never_reaches_stub_or_opener",
          not isinstance(missing, ns["ProdHistoricalAuthorityDisabled"]) and opened == [])
    for label, bad_row in (("none_row", None), ("no_animset", {"animset": None})):
        got = [None, None]
        for i, fn in enumerate((ns["semantic_snapshot_for_model_row"], reference["semantic_snapshot_for_model_row"])):
            try:
                fn(bad_row)
            except Exception as exc:  # noqa: BLE001
                got[i] = (type(exc).__name__, _TEXT(exc))
        check("snapshot.%s_precedes_provider_check_as_before" % label, got[0] == got[1] and got[0] is not None, got)
    for valid in (True, False):
        p_new, p_old = Provider(valid), Provider(valid)
        outcome = []
        for fn, p in ((ns["semantic_snapshot_for_model_row"], p_new),
                      (reference["semantic_snapshot_for_model_row"], p_old)):
            try:
                result = fn(row, p)
                result = dict(result)
                result["provider"] = result["provider"] is p
                outcome.append(("ok", route._canon(result)))
            except Exception as exc:  # noqa: BLE001
                outcome.append((type(exc).__name__, _TEXT(exc)))
        check("snapshot.supplied_provider_identical_to_precleanup_%s" % ("valid" if valid else "invalid"),
              outcome[0] == outcome[1] and p_new.queries == p_old.queries, outcome[0][:1])
    check("snapshot.supplied_provider_path_opens_nothing", opened == [])
    route.Env.bindings = []


def section_closure(src):
    removed = set(REMOVED_TOP) | set(REMOVED_CONSTANTS) | set(REMOVED_METHODS)
    text = src.raw.decode("utf-8")
    name_hits, string_hits, comment_hits = [], [], []
    readline = io.StringIO(text).readline
    word = re.compile(r"\b(%s)\b" % "|".join(sorted(removed, key=len, reverse=True)))
    for tok in tokenize.generate_tokens(readline):
        if tok[0] == tokenize.NAME and tok[1] in removed:
            name_hits.append((tok[2][0], tok[1]))
        elif tok[0] == tokenize.STRING and word.search(tok[1]):
            string_hits.append(tok[2][0])
        elif tok[0] == tokenize.COMMENT and word.search(tok[1]):
            comment_hits.append(tok[2][0])
    check("closure.no_reference_to_removed_names", not name_hits, name_hits[:10])
    check("closure.no_string_reference_to_removed_names", not string_hits, string_hits[:10])
    check("closure.no_comment_reference_to_removed_names", not comment_hits, comment_hits[:10])
    check("closure.no_top_level_binding_of_removed_names", not removed & set(src.by_name))
    check("closure.retained_constants_present", all(n in src.by_name for n in RETAINED_CONSTANTS),
          [n for n in RETAINED_CONSTANTS if n not in src.by_name])
    check("closure.retained_definitions_present", all(n in src.by_name for n in RETAINED_TOP),
          [n for n in RETAINED_TOP if n not in src.by_name])
    _, _, members = src.class_members("ProdWindow")
    check("closure.parity_method_absent", "g18an_run_decision_parity" not in members)
    check("closure.parity_shortcut_attribute_retained",
          sum(t.count(u"self.g18an_parity_shortcut = None") for t in members.values()) == 1)
    check("closure.module_compiles", compile(src.raw, APP_PATH, "exec") is not None)
    # Production reachability: StartProdTool and every ProdWindow method.
    top_nodes = dict((n, v[0]) for n, v in src.by_name.items())
    frontier = set(n.id for n in ast.walk(top_nodes["StartProdTool"]) if isinstance(n, ast.Name))
    for node in top_nodes["ProdWindow"].body:
        frontier |= set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))
    reached, stack = set(), list(frontier)
    while stack:
        name = stack.pop()
        if name in reached or name not in top_nodes or name == "ProdWindow":
            continue
        reached.add(name)
        stack.extend(n.id for n in ast.walk(top_nodes[name]) if isinstance(n, ast.Name))
    check("reach.refusal_stub_unreachable_from_production", "get_semantic_provider" not in reached)
    check("reach.legacy_entrypoints_unreachable", not set(["p02_complete_scope", "g11a_source"]) & reached)
    check("reach.canonical_route_reachable",
          set(["prod_cpm_open_adapter", "prod_scope", "prod_probe_semantic_provider",
               "prod_cpm_authorize_operation", "prod_cpm_open_fit_stage"]) <= reached)
    callers = sorted(n for n, node in top_nodes.items()
                     if n != "get_semantic_provider"
                     and "get_semantic_provider" in set(x.id for x in ast.walk(node) if isinstance(x, ast.Name)))
    check("reach.only_legacy_callers_reference_stub", not set(callers) & reached, callers)
    print("      (legacy, unreachable callers ending at the refusal stub: %s)" % ", ".join(callers))
    tree_imports = [n for n in ast.walk(src.tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    bad = [getattr(n, "module", None) or n.names[0].name for n in tree_imports
           if any(tag in (getattr(n, "module", None) or n.names[0].name or "").lower()
                  for tag in ("baseline", "g18an", "qualification", "candidate_", "test"))]
    check("closure.no_production_import_of_reference_machinery", not bad, bad)


def main():
    if "--write-manifest" in sys.argv[1:]:
        write_manifest()
        return
    print("Interpreter: %s" % sys.version.split()[0])
    with open(APP_PATH, "rb") as f:
        src = Source(f.read())
    print("Candidate app sha256: %s" % hashlib.sha256(src.raw).hexdigest())
    manifest = section_manifest()
    helper_text = section_preservation(manifest, src)
    section_structure(src)
    section_stub_runtime(src)
    section_snapshot_runtime(src, helper_text)
    section_closure(src)
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    sys.path.insert(0, _THIS_DIR)
    main()
