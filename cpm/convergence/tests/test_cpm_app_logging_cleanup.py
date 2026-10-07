# -*- coding: utf-8 -*-
"""Handoff section 22 item 7 -- diagnostic/development logging reduction checks.

Design: cpm/qualification/ITEM7_DIAGNOSTIC_LOGGING_REDUCTION_DESIGN.md (sections 3-11).

Preservation is proven by reconstruction: the pinned item-6 app (an explicit,
hash-validated reference path; never the candidate) is parsed under the running
interpreter, the transformations recorded in item7_precleanup_source_manifest.json
(generated before the cleanup edit) are applied to its AST, and the result must
equal the candidate's AST (location-independent ast.dump). Untouched top-level
blocks and ProdWindow members must also be byte-identical, as must
p02_safe_write_json and the G18AN_POST_FIT_ACTION_STATE statement.

Runtime gates execute real production code: authority functions through the
canonical-route harness (real adapter/broker; requires the route suite's
--phase=publish fixtures) and a real ProdWindow through the R15 harness
environment, with a log_line that raises for one selected event at a time.

Usage:
  python test_cpm_app_logging_cleanup.py --reference=<pinned item-6 app>
  python test_cpm_app_logging_cleanup.py --reference=<pinned item-6 app> --write-manifest   # pre-edit only
  internal: --child=<scenario> --qt=<real|model> --root=<dir> --reference=<...> --target=<candidate|reference>
"""
from __future__ import print_function

import ast
import copy
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import tokenize
import types

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
APP_PATH = os.environ.get("CPM_TEST_APP_PATH") or os.path.join(_REPO_ROOT, "cpm", "app", "SFM_Character_Preset_Manager.py")
MANIFEST_PATH = os.path.join(_THIS_DIR, "item7_precleanup_source_manifest.json")
REFERENCE_SHA256 = "1e8668717f9a4a1def0900c6b51e20cb9a7676cc365244eab5c31233f133eeeb"
MANIFEST_SHA256 = "cbb3010b10219588b202c9ec011319962b2aef17742a5f7fa5e6dbb508503d5d"
PY2 = sys.version_info[0] == 2
_TEXT = unicode if PY2 else str  # noqa: F821
RESULTS = []

# --- Approved design inventories ---------------------------------------------
TIMING_HELPERS = {"prod_perf_log": 27, "prod_action_timing": 26, "astra_perf_timing": 24}
TIMER_NAMES = sorted("""t_apply t_apply_ui t_bone_plan t_bone_verify t_bones t_current t_enum t_flex_prepare
t_flex_verify t_fresh_scope t_mutation t_parse t_phase t_plan t_post_snapshot t_prod t_refresh t_render_total
t_scope t_snapshot t_total t_ui_total t_validate t_verify""".split())
TIMER_TOTAL = 72
TOP_REMOVALS = ["prod_perf_seconds", "prod_perf_log", "astra_perf_timing", "prod_action_timing",
                "PROD_PERF_LOGGING", "SEMANTIC_PROVIDER_MODE_SIDECAR", "SEMANTIC_PROVIDER_FORCE_MODE",
                "G18AN_PARITY_SHORTCUT"]
REMOVED_STAGES = ["body-library-begin", "body-library-ready", "expression-library-begin",
                  "expression-library-ready", "library-meta-begin", "library-meta-ready", "library-validated",
                  "preset-ui-begin", "preset-ui-ready", "scope-ui-ready", "fit-ui-ready"]
LOG_REMOVALS = {  # owner -> log keys removed (every occurrence)
    "StartProdTool": ["ARCHITECTURE", "G18AN_ANIMSET_RENAME_RESILIENCE", "G18AN_FOREIGN_MODAL_YIELD",
                      "SIDECAR_STATUS", "G18AN_WINDOW_POLICY", "G18AN_PROVIDER_FORCE_MODE"],
    "tool_window_icon": ["PROD_WINDOW_ICON:embedded-loaded"],
    "prod_bs_index_capture_map": ["Q3_SCALE_CAPTURE_ACCEPT"],
    "ProdWindow.refresh_preset_view": ["PROD_PRESET_UI"],
    "ProdWindow.render": ["PROD_MODEL_SWITCH_STAGE:" + s for s in REMOVED_STAGES],
    "ProdWindow.refresh_fit_candidates": ["CLOTHING_FIT_CANDIDATES"],
    "ProdWindow.clear_model_selection": ["PROD_MODEL_CLEAR"],
    "ProdWindow.save_kind.work": ["PROD_SAVE_POSTWRITE_REFRESH"],
    "ProdWindow.update_kind.work": ["PROD_UPDATE_POSTWRITE_REFRESH"],
    "ProdWindow.toggle_favorite.work": ["PROD_FAVORITE_UI_REFRESH"],
    "ProdWindow.delete_kind.work": ["PROD_DELETE_POSTMOVE_REFRESH"],
    "ProdWindow.open_details.work": ["PROD_DETAILS"],
    "ProdWindow.open_preset_info.work": ["PROD_PRESET_INFO"],
    "ProdWindow.open_help.work": ["PROD_HELP_OPEN"],
}
TRY_REMOVALS = {  # logging-only try/except constructs (first body record key)
    "ProdWindow.operation_begin": "G18AN_OPERATION_PROVIDER_STATE",
    "ProdWindow.operation_end": "G18AN_OPERATION_PROVIDER_STATE",
    "ProdWindow.render": "G18AN_LIVE_SELECTION_PROVIDER_STATE",
    "ProdWindow.closeEvent": "G18AN_CLOSE_PROVIDER_STATE",
}
DIRECT_LOG_REMOVALS = 46
WRAP_OWNERS = {
    "StartProdTool": 8, "p01_master_path": 1, "prod_abort_apply_and_verify": 1, "prod_abort_fit_and_verify": 1,
    "prod_apply": 4, "prod_bs_index_capture_map": 1, "prod_clear_override": 1, "prod_cpm_authorize_operation": 2,
    "prod_cpm_open_fit_stage": 2, "prod_cpm_release_fit_stage": 1, "prod_cpm_scope_generation_stale": 1,
    "prod_cpm_unmigrated_authority": 1, "prod_discover": 2, "prod_move_current_preset_to_trash": 3,
    "prod_operation_event_turn_sample": 1, "prod_prepare_library_root": 2, "prod_probe_semantic_provider": 3,
    "prod_q1_compare_body_capture": 1, "prod_r15_result": 1, "prod_r15_window_decision": 1, "prod_resolve": 1,
    "prod_save": 1, "prod_set_favorite": 1, "prod_set_override": 1, "prod_update_preset": 1,
    "same_time_refresh": 1, "tool_apply_window_icon": 1, "tool_window_icon": 1, "undo_state": 1,
    "ProdWindow.__init__": 1, "ProdWindow.apply_provider_unavailable_to_ui": 1,
    "ProdWindow.clear_model_selection": 1, "ProdWindow.closeEvent": 1, "ProdWindow.fit_finish": 1,
    "ProdWindow.fit_selected": 3, "ProdWindow.fit_show_partial_failure": 1, "ProdWindow.fit_stage": 6,
    "ProdWindow.guard": 4, "ProdWindow.open_master_page": 1, "ProdWindow.operation_begin": 2,
    "ProdWindow.operation_end": 1, "ProdWindow.operation_mark_phase": 1, "ProdWindow.poll_foreign_modal": 2,
    "ProdWindow.populate.work": 1, "ProdWindow.prod_cpm_request_stale_rebuild_if_needed": 1,
    "ProdWindow.prod_cpm_run_stale_rebuild": 1, "ProdWindow.refresh_animset_display_metadata": 1,
    "ProdWindow.reload_library_cache": 1, "ProdWindow.render": 6,
    "ProdWindow.resume_scene_activity_after_foreign_modal": 1, "ProdWindow.review_decision.work": 1,
    "ProdWindow.review_reclassify.work": 1, "ProdWindow.select_model.work": 1,
}
WRAP_TOTAL, WRAP_OWNER_TOTAL = 88, 53
CONSTANT_EXCLUSIONS = 6
EXCLUDED_STATEMENT_KEY = ("ProdWindow.fit_finish", "G18AN_POST_FIT_ACTION_STATE")
EXCLUDED_FUNCTION = "p02_safe_write_json"
PAYLOADS = {
    ("ProdWindow.populate.work", "PROD_MODELS"): (
        u'log_line(\n'
        u'    "PROD_MODELS count=%d initial_index=%d"\n'
        u'    % (\n'
        u'        len(\n'
        u'            self.candidates\n'
        u'        ),\n'
        u'        self.combo.currentIndex(),\n'
        u'    )\n'
        u')\n'),
    ("ProdWindow.fit_finish", "CLOTHING_FIT_RESULT"): None,  # prefix substitution below
}
FIT_RESULT_OLD, FIT_RESULT_NEW = u"CLOTHING_FIT_RESULT=PASS generation=", u"CLOTHING_FIT_RESULT generation="
ITEM7_CHANGED_TOP = ["p01_master_path", "prod_abort_fit_and_verify", "prod_bs_index_capture_map",
                     "prod_bs_index_snapshot", "prod_build_bone_scale_plan", "prod_capture_body_snapshot",
                     "prod_capture_bone_scale_map", "prod_discover", "prod_move_current_preset_to_trash",
                     "prod_operation_event_turn_sample", "prod_prepare_library_root", "prod_q1_compare_body_capture",
                     "prod_resolve", "prod_set_favorite", "prod_validate_bone_scale_map",
                     "prod_verify_bone_scale_map", "same_time_refresh", "tool_apply_window_icon",
                     "tool_window_icon", "undo_state"]
PROTECTED = {  # path -> sha256 of LF-normalized bytes (unchanged by item 7)
    "cpm/app/launcher/SFM_Character_Preset_Manager.py": "996ca483d625d37feb8d8f38a8d13db16f999d4189d98434db9c284a0a458c51",
    "cpm/baseline/SFM_CSP_G18AN_SaveNewCopy.py": "3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e",
    "cpm/convergence/cpm_authority_adapter.py": "e96e21b537b5892fc5c1139b2396bbf5e3ce48a521b45876035d78789f126607",
    "cpm/convergence/cpm_compat_v1_projection.py": "9b077a1baf491262901812620c380a45eeb9cb2bf75ddc28a08ab18612faffc1",
    "audit_external_runtime/Rebuild_Control_Groups_Normalizer.py": "1f4ec5a26605aa90380eb0532fec3915d2cc24a3a20473ed70d57198bd995db7",
    "sfm_defaultanimationgroups.txt": "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93",
    "cpm/convergence/tests/test_cpm_compat_v1_projection.py": "4f9aee8715802a18dbc1ba19afc78bde765adbce542c15e68a2ac9e58b9f054d",
    "cpm/convergence/tests/test_cpm_authority_adapter.py": "513adcb699e86388ea8e114452d5bba9ce12e020ce444a949e6cb1053f14726a",
    "cpm/convergence/tests/test_cpm_app_operation_context.py": "f754c5b43cf75e667847d8ea43614b40c0910ecafa436997d95bebe6acd0a591",
    "cpm/convergence/tests/test_cpm_app_clothing_fit.py": "b64d6ace92d644119d77100f33a76aeede6f0f5a527ef827dfbe4780c8e3b412",
    "cpm/convergence/tests/test_cpm_convergence_gates.py": "a1b2162f4592c3cc2795ca9ebcc82468e54f7b765b26d8df8575dba2634de670",
    "cpm/convergence/tests/test_cpm_app_r14_ctypes_isolation.py": "e9bb5056dd2585703c51c282c974840ec2e795dc3a3d2571232869e754982586",
    "cpm/convergence/tests/test_cpm_app_r15_namespace_isolation.py": "e576bbb6a0c66b967e9ff987c9bd0f302fd0c193bc462c41c4c30154b32d35a9",
    "cpm/convergence/tests/test_cpm_app_authority_cleanup.py": "a3024d3404c3d3db3905218343fdf1e931a58c782e0599d810f55427467820fe",
    "cpm/convergence/tests/item6_precleanup_source_manifest.json": "a92647949f26f02c65497b4f0e808413edbe54af72eec8b1bee65798cdd2c6ae",
    "cpm/qualification/ITEM6_HISTORICAL_AUTHORITY_CLEANUP_DESIGN.md": "d0410ef20ecf8159bc2f75489d298296b1acfa41d28e775a3f9a5bd087aed4b3",
    "cpm/qualification/ITEM6_HISTORICAL_AUTHORITY_CLEANUP_EVIDENCE.md": "8c1480c279fb9cff734c91bb199c2736bf37affecd42b29151fcad5a04ed4d46",
    "real_sfm_qualification/cpm_session1/CPM_Session1_Probe.py": "ce4ace980ee2cf62c43de13a1686152019b025d4f2d776e3c80c45529283c7e3",
}
SHARED_PACKAGE_DIR = "tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized"
SHARED_PACKAGE_DIGEST = ("26d43ff82062d7f9cd5f6edd7a1c2403fa41194d7b0ace8e83316b6ed9ef310f", 24)


def _normalized_file_sha(path):
    with open(path, "rb") as f:
        return _sha_bytes(f.read().replace(b"\r\n", b"\n"))


def _package_digest():
    root = os.path.join(_REPO_ROOT, *SHARED_PACKAGE_DIR.split("/"))
    names = sorted(n for n in os.listdir(root) if n.endswith(".py"))
    h = hashlib.sha256()
    for n in names:
        h.update((SHARED_PACKAGE_DIR + "/" + n).encode("ascii") + b"\0"
                 + _normalized_file_sha(os.path.join(root, n)).encode("ascii") + b"\n")
    return h.hexdigest(), len(names)


def check(name, condition, value=None):
    RESULTS.append((name, bool(condition)))
    print("[%s] %s" % ("PASS" if condition else "FAIL", name))
    if not condition and value is not None:
        print("      value: %r" % (value,))


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- Source structure ----------------------------------------------------------

def _walk(body):
    """(stmt, parent_list) in source order; nested defs/classes are not entered."""
    for stmt in body:
        yield stmt, body
        if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)):
            continue
        for field in ("body", "orelse", "finalbody"):
            sub = getattr(stmt, field, None)
            if isinstance(sub, list):
                for item in _walk(sub):
                    yield item
        for handler in getattr(stmt, "handlers", None) or []:
            for item in _walk(handler.body):
                yield item


def owners(tree):
    out = []

    def nested(fn, path):
        for stmt, _ in _walk(fn.body):
            if isinstance(stmt, ast.FunctionDef):
                qual = path + "." + stmt.name
                out.append((qual, stmt))
                nested(stmt, qual)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out.append((node.name, node))
            nested(node, node.name)
        elif isinstance(node, ast.ClassDef) and node.name == "ProdWindow":
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    qual = "ProdWindow." + member.name
                    out.append((qual, member))
                    nested(member, qual)
    names = [q for q, _ in out]
    if len(names) != len(set(names)):
        raise RuntimeError("ambiguous owner names")
    return out


def _call_name(stmt):
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name):
        return stmt.value.func.id
    return None


def _string_value(node):
    if node is None:
        return None
    if type(node).__name__ == "Str":
        return node.s
    if type(node).__name__ == "Constant" and isinstance(node.value, (str, _TEXT)):
        return node.value
    return None


def _format_string(call):
    arg = call.args[0] if call.args else None
    while isinstance(arg, ast.BinOp):
        arg = arg.left
    return _string_value(arg)


def log_key(call):
    fmt = _format_string(call)
    if fmt is not None:
        m = re.match(r"\s*([A-Za-z0-9_]+)", fmt)
        if not m:
            return "<literal:%s>" % fmt[:12]
        tag = m.group(1)
        if tag == "PROD_MODEL_SWITCH_STAGE":
            return tag + ":" + re.search(r"stage='([^']*)'", fmt).group(1)
        if tag == "PROD_WINDOW_ICON":
            return tag + ":" + re.search(r"status='([^']*)'", fmt).group(1)
        return tag
    arg = call.args[0] if call.args else None
    if isinstance(arg, ast.Name):
        return "<name:%s>" % arg.id
    if isinstance(arg, ast.Call):
        parts, f = [], arg.func
        while isinstance(f, ast.Attribute):
            parts.insert(0, f.attr)
            f = f.value
        if isinstance(f, ast.Name):
            parts.insert(0, f.id)
        return "<call:%s>" % ".".join(parts)
    return "<expr>"


def is_constant_expr(node):
    allowed = ("Constant", "Str", "Num", "Bytes", "BinOp", "Load") + tuple(
        cls.__name__ for cls in (ast.Add, ast.Mult, ast.Mod, ast.Sub))
    return all(type(n).__name__ in allowed for n in ast.walk(node))


def _is_timer(stmt):
    return (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name)
            and stmt.targets[0].id in TIMER_NAMES and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Attribute) and stmt.value.func.attr == "time"
            and isinstance(stmt.value.func.value, ast.Name) and stmt.value.func.value.id == "time"
            and not stmt.value.args)


def _assign_name(stmt):
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        return stmt.targets[0].id
    return None


def _is_bare_raise(stmt):
    return isinstance(stmt, ast.Raise) and getattr(stmt, "exc", None) is None and getattr(stmt, "type", None) is None


def _is_try(stmt):
    return type(stmt).__name__ in ("Try", "TryExcept")


def _logging_only_try(stmt):
    if not _is_try(stmt) or getattr(stmt, "orelse", None) or getattr(stmt, "finalbody", None):
        return None
    if len(stmt.body) != 1 or _call_name(stmt.body[0]) != "log_line":
        return None
    for h in stmt.handlers:
        if not all(_call_name(s) == "log_line" for s in h.body):
            return None
    return log_key(stmt.body[0].value)


def domains(owner_node):
    """Per-owner statement domains: (domain, key) -> [stmt, ...] in source order."""
    out = {}

    def add(domain, key, stmt):
        out.setdefault((domain, key), []).append(stmt)
    for stmt, _ in _walk(owner_node.body):
        name = _call_name(stmt)
        if name in TIMING_HELPERS:
            add("timing", name, stmt)
        elif name == "log_line":
            add("log", log_key(stmt.value), stmt)
        if _is_timer(stmt):
            add("timer", stmt.targets[0].id, stmt)
        elif _assign_name(stmt):
            add("assign", _assign_name(stmt), stmt)
        if _is_bare_raise(stmt):
            add("raise", "bare", stmt)
        key = _logging_only_try(stmt)
        if key is not None:
            add("try", key, stmt)
    return out


def parents(owner_node):
    return dict((id(stmt), body) for stmt, body in _walk(owner_node.body))


# --- Interpreter-independent statement digests --------------------------------

class TokenIndex(object):
    def __init__(self, text):
        self.tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        self.by_start = {}
        for i, tok in enumerate(self.tokens):
            self.by_start.setdefault(tok[2], i)

    def simple_span(self, stmt):
        """Token indexes [i, j) of one simple statement (to NEWLINE or ';')."""
        i = self.by_start.get((stmt.lineno, stmt.col_offset))
        if i is None:
            raise RuntimeError("statement start not found at line %d" % stmt.lineno)
        depth, j = 0, i
        while j < len(self.tokens):
            ttype, tstr = self.tokens[j][0], self.tokens[j][1]
            if ttype == tokenize.OP and tstr in "([{":
                depth += 1
            elif ttype == tokenize.OP and tstr in ")]}":
                depth -= 1
            elif depth == 0 and (ttype == tokenize.NEWLINE or (ttype == tokenize.OP and tstr == ";")):
                break
            j += 1
        return i, j

    def digest(self, stmt):
        if isinstance(stmt, (ast.FunctionDef, ast.ClassDef)) or _is_try(stmt):
            parts = [type(stmt).__name__.replace("TryExcept", "Try")]
            for sub, _ in _walk(stmt.body if not isinstance(stmt, ast.ClassDef) else stmt.body):
                if not (_is_try(sub) or isinstance(sub, (ast.If, ast.For, ast.While, ast.With, ast.FunctionDef,
                                                         ast.ClassDef))):
                    parts.append(self.digest(sub))
            for h in getattr(stmt, "handlers", None) or []:
                for sub, _ in _walk(h.body):
                    if not _is_try(sub):
                        parts.append(self.digest(sub))
            return _sha_text(u"|".join(parts))
        i, j = self.simple_span(stmt)
        return _sha_text(u"\x00".join(t[1] for t in self.tokens[i:j]
                                      if t[0] not in (tokenize.NL, tokenize.COMMENT)))


# --- Block segmentation (byte identity of untouched code) ---------------------

def _is_trivia(line):
    s = line.strip()
    return not s or s.startswith(u"#")


def segments(nodes, lines, lo, hi):
    starts = []
    for i, node in enumerate(nodes):
        if isinstance(node, ast.Expr) and _string_value(node.value) is not None:
            if i != 0:
                raise RuntimeError("unsupported non-leading string statement")
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
        out.append((node, u"\n".join(block) + u"\n"))
    return out


def _node_names(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return ["import:" + ",".join(a.name for a in node.names)]
    return []


def block_map(raw):
    text = raw.decode("utf-8")
    lines = text.split(u"\n")
    tree = ast.parse(raw)
    top = segments(tree.body, lines, 1, len(lines))
    blocks = [(_node_names(n), _sha_text(t), n) for n, t in top]
    cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ProdWindow"][0]
    idx = tree.body.index(cls)
    hi = tree.body[idx + 1].lineno - 1 if idx + 1 < len(tree.body) else len(lines)
    members = [(_node_names(n), _sha_text(t)) for n, t in segments(cls.body, lines, cls.lineno + 1, hi)]
    return blocks, members


# --- Manifest -------------------------------------------------------------------

def build_manifest(ref_raw):
    text = ref_raw.decode("utf-8")
    tree = ast.parse(ref_raw)
    tok = TokenIndex(text)
    own = owners(tree)
    records, problems = [], []

    def rec(op, kind, owner, domain_key, ordinal, stmt, **extra):
        r = {"op": op, "kind": kind, "owner": owner, "domain": domain_key[0], "key": domain_key[1],
             "ordinal": ordinal, "digest": tok.digest(stmt), "line": stmt.lineno}
        r.update(extra)
        records.append(r)
    timing_counts, timer_total, removed_logs, wrapped = {}, 0, 0, {}
    const_excluded = 0
    for qual, node in own:
        dom = domains(node)
        loads = [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)]
        for (domain, key), stmts in sorted(dom.items()):
            if domain == "timing":
                for i, s in enumerate(stmts):
                    rec("delete", "timing-call", qual, (domain, key), i, s)
                timing_counts[key] = timing_counts.get(key, 0) + len(stmts)
            elif domain == "timer":
                timing_loads = sum(1 for (d2, k2), ss in dom.items() if d2 == "timing" for st in ss
                                   for n in ast.walk(st) if isinstance(n, ast.Name) and n.id == key)
                if loads.count(key) != timing_loads:
                    problems.append("timer %s in %s is used outside timing calls" % (key, qual))
                for i, s in enumerate(stmts):
                    rec("delete", "timer-assign", qual, (domain, key), i, s)
                timer_total += len(stmts)
        # Logging-only try constructs.
        if qual in TRY_REMOVALS:
            stmts = dom.get(("try", TRY_REMOVALS[qual]), [])
            if len(stmts) != 1:
                problems.append("expected one logging-only try in %s" % qual)
            for i, s in enumerate(stmts):
                rec("delete", "try-logging", qual, ("try", TRY_REMOVALS[qual]), i, s,
                    records_inside=1 + sum(len(h.body) for h in s.handlers))
                removed_logs += 1 + sum(len(h.body) for h in s.handlers)
        in_removed_try = set(id(x) for (d, k), ss in dom.items() if d == "try" and qual in TRY_REMOVALS
                             and k == TRY_REMOVALS[qual] for t in ss for x, _ in _walk([t]))
        for (domain, key), stmts in sorted(dom.items()):
            if domain != "log":
                continue
            for i, s in enumerate(stmts):
                if id(s) in in_removed_try:
                    continue
                if key in LOG_REMOVALS.get(qual, ()):
                    rec("delete", "log", qual, (domain, key), i, s)
                    removed_logs += 1
                    continue
                if qual not in WRAP_OWNERS:
                    continue
                if (qual, key) == EXCLUDED_STATEMENT_KEY:
                    rec("preserve", "excluded-statement", qual, (domain, key), i, s)
                    continue
                if is_constant_expr(s.value.args[0]):
                    const_excluded += 1
                    continue
                if (qual, key) in PAYLOADS:
                    rec("replace", "payload", qual, (domain, key), i, s)
                if qual == "prod_bs_index_capture_map" and key == "Q3_SCALE_CAPTURE_REJECT":
                    rec("wrap-pair", "wrap", qual, (domain, key), i, s, assign_key="diagnostic", assign_ordinal=0)
                else:
                    rec("wrap", "wrap", qual, (domain, key), i, s)
                wrapped[qual] = wrapped.get(qual, 0) + 1
        if qual == "prod_bs_index_capture_map":
            diag = dom.get(("assign", "diagnostic"), [])
            for i in (2, 3):
                rec("delete", "accept-diagnostic", qual, ("assign", "diagnostic"), i, diag[i])
        if qual == "ProdWindow.refresh_preset_view":
            rec("delete", "kind-label", qual, ("assign", "kind_label"), 0, dom[("assign", "kind_label")][0])
        if qual == "StartProdTool":
            rec("replace", "raise-exc", qual, ("raise", "bare"), 0, dom[("raise", "bare")][0])
    for name in TOP_REMOVALS:
        nodes = [n for n in tree.body if name in _node_names(n)]
        if len(nodes) != 1:
            problems.append("top-level %s not unique" % name)
        records.append({"op": "remove-top", "kind": "definition", "name": name, "digest": tok.digest(nodes[0])
                        if isinstance(nodes[0], ast.FunctionDef) else _sha_text(
                            u"\x00".join(t[1] for t in tok.tokens[slice(*tok.simple_span(nodes[0]))]))})
    imports = [n for n in tree.body if isinstance(n, ast.Import) and [a.name for a in n.names] == ["time"]]
    if len(imports) != 1:
        problems.append("import time not unique")
    records.append({"op": "remove-top", "kind": "import", "name": "import:time"})
    if timing_counts != TIMING_HELPERS:
        problems.append("timing counts %r" % (timing_counts,))
    if timer_total != TIMER_TOTAL:
        problems.append("timer total %d" % timer_total)
    if removed_logs != DIRECT_LOG_REMOVALS:
        problems.append("direct log removals %d" % removed_logs)
    if wrapped != WRAP_OWNERS or sum(wrapped.values()) != WRAP_TOTAL or len(wrapped) != WRAP_OWNER_TOTAL:
        problems.append("wrappers %r" % (sorted(set(wrapped.items()) ^ set(WRAP_OWNERS.items())),))
    if const_excluded != CONSTANT_EXCLUSIONS:
        problems.append("constant exclusions %d" % const_excluded)
    if problems:
        raise RuntimeError("design count/identity mismatch: %s" % "; ".join(problems))
    blocks, members = block_map(ref_raw)
    excluded_fn = [h for names, h, _ in blocks if names == [EXCLUDED_FUNCTION]]
    return {
        "schema": "cpm-item7-precleanup-source-manifest-v1",
        "reference_relative_path": "cpm/app/SFM_Character_Preset_Manager.py",
        "reference_sha256": _sha_bytes(ref_raw),
        "reference_checkpoint": "7b69b520a2472d3700ce347a1d2a59bc98e926f2",
        "identification": ("owner (qualified, nested defs separate) + domain/key + ordinal in source order; "
                           "digest = sha256 of the statement's token text (compound: of its simple statements); "
                           "line numbers are navigation only"),
        "records": records,
        "counts": {"timing_calls": TIMING_HELPERS, "timer_assignments": TIMER_TOTAL,
                   "direct_log_removals": DIRECT_LOG_REMOVALS, "wrappers": WRAP_TOTAL,
                   "wrapper_owners": WRAP_OWNER_TOTAL, "constant_exclusions": CONSTANT_EXCLUSIONS,
                   "top_level_removals": TOP_REMOVALS + ["import:time"]},
        "blocks": [{"names": names, "sha256": h} for names, h, _ in blocks],
        "prodwindow_members": [{"names": names, "sha256": h} for names, h in members],
        "excluded_function_sha256": excluded_fn[0],
        "payloads": {"PROD_MODELS": PAYLOADS[("ProdWindow.populate.work", "PROD_MODELS")],
                     "CLOTHING_FIT_RESULT": [FIT_RESULT_OLD, FIT_RESULT_NEW]},
    }


def write_manifest(reference):
    ref_raw = _read_reference(reference)
    with open(APP_PATH, "rb") as f:
        if _sha_bytes(f.read()) != REFERENCE_SHA256:
            raise SystemExit("REFUSED: the working app is not the pre-item-7 bytes (generate before editing)")
    if os.path.exists(MANIFEST_PATH):
        raise SystemExit("REFUSED: %s already exists (never regenerate it)" % MANIFEST_PATH)
    data = json.dumps(build_manifest(ref_raw), indent=1, sort_keys=True, ensure_ascii=True,
                      separators=(",", ": ")) + "\n"
    with open(MANIFEST_PATH, "wb") as f:
        f.write(data.encode("ascii"))
    print("manifest written: sha256=%s records=%d" % (_sha_bytes(data.encode("ascii")),
                                                      len(json.loads(data)["records"])))


def _read_reference(reference):
    if not reference:
        raise SystemExit("REFUSED: an explicit --reference=<pinned item-6 app> is required")
    with open(reference, "rb") as f:
        raw = f.read()
    if _sha_bytes(raw) != REFERENCE_SHA256:
        raise SystemExit("REFUSED: reference is not the pinned item-6 app (%s)" % _sha_bytes(raw))
    return raw


def load_manifest():
    with open(MANIFEST_PATH, "rb") as f:
        raw = f.read().replace(b"\r\n", b"\n")
    return raw, json.loads(raw.decode("ascii"))


# --- Reconstruction ---------------------------------------------------------------

def _template_try(body):
    node = ast.parse("try:\n    pass\nexcept Exception:\n    pass\n").body[0]
    node.body = list(body)
    return node


def _parse_stmt(text):
    return ast.parse(textwrap.dedent(text)).body[0]


def reconstruct(ref_raw, manifest):
    """Apply the manifest's transformations to the reference AST (this interpreter)."""
    text = ref_raw.decode("utf-8")
    tree = ast.parse(ref_raw)
    tok = TokenIndex(text)
    own = dict(owners(tree))
    located = []
    for r in manifest["records"]:
        if r["op"] == "remove-top":
            continue
        node = own[r["owner"]]
        stmts = domains(node).get((r["domain"], r["key"]), [])
        if r["ordinal"] >= len(stmts):
            raise RuntimeError("record not found: %r" % (r,))
        stmt = stmts[r["ordinal"]]
        if tok.digest(stmt) != r["digest"]:
            raise RuntimeError("record digest mismatch: %r" % (r,))
        pair = None
        if r["op"] == "wrap-pair":
            pair = domains(node)[("assign", r["assign_key"])][r["assign_ordinal"]]
        located.append((r, node, stmt, pair))
    for r, node, stmt, pair in located:
        if r["op"] not in ("delete", "replace"):
            continue
        body = parents(node)[id(stmt)]
        pos = [i for i, s in enumerate(body) if s is stmt][0]
        if r["op"] in ("delete",):
            body.pop(pos)
        elif r["op"] == "replace" and r["kind"] == "payload":
            if r["key"] == "PROD_MODELS":
                body[pos] = _parse_stmt(manifest["payloads"]["PROD_MODELS"])
            else:
                fmt_node = stmt.value.args[0]
                while isinstance(fmt_node, ast.BinOp):
                    fmt_node = fmt_node.left
                old, new = manifest["payloads"]["CLOTHING_FIT_RESULT"]
                value = _string_value(fmt_node)
                if not value.startswith(old):
                    raise RuntimeError("fit result payload not found")
                if type(fmt_node).__name__ == "Str":
                    fmt_node.s = type(fmt_node.s)(new + value[len(old):])
                else:
                    fmt_node.value = new + value[len(old):]
            # a replaced statement may also be wrapped; keep the node identity for the wrap step
            for other in located:
                if other[2] is stmt and other[0]["op"] == "wrap":
                    other[0]["_replacement"] = body[pos]
        elif r["op"] == "replace" and r["kind"] == "raise-exc":
            body[pos] = _parse_stmt(u"raise exc\n")
    for r, node, stmt, pair in located:
        if r["op"] not in ("wrap", "wrap-pair"):
            continue
        target = r.pop("_replacement", None) or stmt
        body = parents(node)[id(stmt)] if target is stmt else [b for b in _bodies_containing(node, target)][0]
        pos = [i for i, s in enumerate(body) if s is target][0]
        if r["op"] == "wrap-pair":
            ppos = [i for i, s in enumerate(body) if s is pair][0]
            if ppos != pos - 1:
                raise RuntimeError("wrap-pair statements are not adjacent")
            body[ppos:pos + 1] = [_template_try([pair, target])]
        else:
            body[pos] = _template_try([target])
    removals = set(r["name"] for r in manifest["records"] if r["op"] == "remove-top")
    tree.body = [n for n in tree.body if not (set(_node_names(n)) & removals)]
    return tree


def _bodies_containing(owner_node, stmt):
    for s, body in _walk(owner_node.body):
        if s is stmt:
            yield body


def dump(tree):
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


# --- Static sections -------------------------------------------------------------------

def section_identity(reference):
    ref_raw = _read_reference(reference)
    check("identity.reference_is_pinned_item6_app", _sha_bytes(ref_raw) == REFERENCE_SHA256)
    man_raw, manifest = load_manifest()
    check("identity.manifest_sha256_pinned", _sha_bytes(man_raw) == MANIFEST_SHA256, _sha_bytes(man_raw))
    check("identity.manifest_generated_from_reference", manifest["reference_sha256"] == REFERENCE_SHA256)
    with open(APP_PATH, "rb") as f:
        cand_raw = f.read()
    check("identity.candidate_is_not_reference", _sha_bytes(cand_raw) != REFERENCE_SHA256)
    for rel, sha in sorted(PROTECTED.items()):
        check("protected.%s" % rel, _normalized_file_sha(os.path.join(_REPO_ROOT, *rel.split("/"))) == sha)
    check("protected.shared_authority_package", _package_digest() == SHARED_PACKAGE_DIGEST, _package_digest())
    return ref_raw, manifest, cand_raw


def compare_candidate(ref_raw, manifest, cand_raw):
    """Reconstruction equality + byte identity of untouched blocks; returns a list of problems."""
    problems = []
    try:
        recon = reconstruct(ref_raw, copy.deepcopy(manifest))
        cand = ast.parse(cand_raw)
    except Exception as exc:  # noqa: BLE001
        return ["reconstruction error: %r" % (exc,)]
    if dump(recon) != dump(cand):
        rb, cb = recon.body, cand.body
        first = next((i for i, (a, b) in enumerate(zip(rb, cb)) if dump(a) != dump(b)), min(len(rb), len(cb)))
        names = _node_names(rb[first]) if first < len(rb) else ["<end>"]
        problems.append("AST differs from reconstruction at top-level #%d %s" % (first, names))
    # Byte identity of untouched blocks.
    touched_top = set(r["owner"].split(".")[0] for r in manifest["records"] if "owner" in r and r["op"] != "preserve")
    removed = set(r["name"] for r in manifest["records"] if r["op"] == "remove-top")
    cand_blocks, cand_members = block_map(cand_raw)
    cand_by_names = dict((tuple(n), h) for n, h, _ in cand_blocks)
    for b in manifest["blocks"]:
        names = tuple(b["names"])
        if set(names) & removed or (names and names[0] in touched_top):
            continue
        if names and cand_by_names.get(names) != b["sha256"]:
            problems.append("untouched block changed: %s" % (names,))
    touched_methods = set(r["owner"].split(".")[1] for r in manifest["records"]
                          if r.get("owner", "").startswith("ProdWindow.") and r["op"] != "preserve")
    cand_m = dict((tuple(n), h) for n, h in cand_members)
    for m in manifest["prodwindow_members"]:
        names = tuple(m["names"])
        if names and names[0] not in touched_methods and cand_m.get(names) != m["sha256"]:
            problems.append("untouched ProdWindow member changed: %s" % (names,))
    excluded = [h for n, h, _ in cand_blocks if n == [EXCLUDED_FUNCTION]]
    if excluded != [manifest["excluded_function_sha256"]]:
        problems.append("%s is not byte-identical" % EXCLUDED_FUNCTION)
    pres = [r for r in manifest["records"] if r["op"] == "preserve"]
    tok = TokenIndex(cand_raw.decode("utf-8"))
    own = dict(owners(cand))
    for r in pres:
        stmts = domains(own[r["owner"]]).get((r["domain"], r["key"]), [])
        if len(stmts) != 1 or tok.digest(stmts[0]) != r["digest"]:
            problems.append("excluded statement %s changed" % r["key"])
        elif any(_is_try(p) and any(x is stmts[0] for x, _ in _walk(p.body))
                 for p, _ in _walk(own[r["owner"]].body)):
            problems.append("excluded statement %s was wrapped" % r["key"])
    return problems


def _wrapper_shape(stmt):
    """Return the wrapped log statement if stmt is exactly an approved diagnostic wrapper."""
    if not _is_try(stmt) or getattr(stmt, "orelse", None) or getattr(stmt, "finalbody", None):
        return None
    if len(stmt.handlers) != 1:
        return None
    h = stmt.handlers[0]
    if not (isinstance(h.type, ast.Name) and h.type.id == "Exception" and h.name is None
            and len(h.body) == 1 and isinstance(h.body[0], ast.Pass)):
        return None
    body = stmt.body
    if len(body) == 1 and _call_name(body[0]) == "log_line":
        return body[0]
    if len(body) == 2 and _assign_name(body[0]) == "diagnostic" and _call_name(body[1]) == "log_line":
        return body[1]
    return None


# Wrapper-shaped statements present before item 7 (R14 resource snapshot; unchanged by item 7).
PREEXISTING_WRAPPER_SHAPES = {"prod_resource_snapshot": 2}


def section_static(ref_raw, manifest, cand_raw):
    recs = manifest["records"]
    check("counts.timing_calls_77", sum(1 for r in recs if r["kind"] == "timing-call") == 77)
    check("counts.timer_assignments_72", sum(1 for r in recs if r["kind"] == "timer-assign") == 72)
    direct = (sum(1 for r in recs if r["kind"] == "log" and r["op"] == "delete")
              + sum(r.get("records_inside", 0) for r in recs if r["kind"] == "try-logging"))
    check("counts.direct_log_removals_46", direct == DIRECT_LOG_REMOVALS, direct)
    check("counts.top_level_removals_8_plus_import",
          sorted(r["name"] for r in recs if r["op"] == "remove-top") == sorted(TOP_REMOVALS + ["import:time"]))
    wraps = [r for r in recs if r["op"] in ("wrap", "wrap-pair")]
    by_owner = {}
    for r in wraps:
        by_owner[r["owner"]] = by_owner.get(r["owner"], 0) + 1
    check("counts.wrappers_88_across_53_owners", len(wraps) == 88 and by_owner == WRAP_OWNERS and len(by_owner) == 53)
    check("counts.payload_substitutions_2", sum(1 for r in recs if r["kind"] == "payload") == 2)
    check("counts.startup_raise_exc_1", sum(1 for r in recs if r["kind"] == "raise-exc") == 1)
    problems = compare_candidate(ref_raw, manifest, cand_raw)
    check("preserve.reconstruction_and_byte_identity", not problems, problems[:8])
    cand = ast.parse(cand_raw)
    own = owners(cand)

    def wrapper_counts(pairs):
        counts = {}
        for qual, node in pairs:
            for stmt, _ in _walk(node.body):
                if _wrapper_shape(stmt) is not None:
                    counts[qual] = counts.get(qual, 0) + 1
        return counts
    # Wrapper-shaped statements that already exist in the pinned item-6 reference (R14's
    # prod_resource_snapshot) are not item-7 wrappers; they must survive unchanged.
    pre = wrapper_counts(owners(ast.parse(ref_raw)))
    check("structure.preexisting_wrapper_shapes_are_r14_only", pre == PREEXISTING_WRAPPER_SHAPES, pre)
    found = wrapper_counts(own)
    for qual, n in pre.items():
        found[qual] = found.get(qual, 0) - n
        if found[qual] == 0:
            del found[qual]
    check("structure.exactly_88_minimal_wrappers_in_the_53_owners", found == WRAP_OWNERS, sorted(
        set(found.items()) ^ set(WRAP_OWNERS.items()))[:6])
    # No surviving unwrapped non-constant log statement in the 53 owners except the excluded one.
    bare = []
    for qual, node in own:
        if qual not in WRAP_OWNERS:
            continue
        wrapped = set(id(_wrapper_shape(s)) for s, _ in _walk(node.body) if _wrapper_shape(s) is not None)
        for stmt, _ in _walk(node.body):
            if _call_name(stmt) == "log_line" and id(stmt) not in wrapped and not is_constant_expr(stmt.value.args[0]) \
                    and (qual, log_key(stmt.value)) != EXCLUDED_STATEMENT_KEY:
                bare.append((qual, log_key(stmt.value)))
    check("structure.no_unwrapped_nonconstant_log_in_owners", not bare, bare[:6])
    names = set(n.id for n in ast.walk(cand) if isinstance(n, ast.Name))
    check("closure.no_reference_to_removed_symbols", not (set(TOP_REMOVALS) | set(["time"])) & names,
          sorted((set(TOP_REMOVALS) | set(["time"])) & names))
    check("closure.no_import_time", not [n for n in cand.body if isinstance(n, ast.Import)
                                         and "time" in [a.name for a in n.names]])
    check("closure.no_timer_assignment", not [s for _, node in own for s, _ in _walk(node.body) if _is_timer(s)])
    check("closure.module_compiles", compile(cand_raw, APP_PATH, "exec") is not None)
    retained = ["PROD_Q1_INDEXED_CAPTURE_PARITY", "prod_q1_compare_body_capture", "semantic_provider_runtime_stats",
                "prod_resource_snapshot", "prod_private_windll", "_PROD_PRIVATE_WINDLL", "undo_state",
                "same_time_refresh", "prod_operation_event_turn_sample", "log_line", "reset_log",
                "_SEMANTIC_PROVIDER", "_SEMANTIC_PROVIDER_OPEN_COUNT"]
    top_names = set(n for node in cand.body for n in _node_names(node))
    check("closure.retained_symbols_present", set(retained) <= top_names, sorted(set(retained) - top_names))
    text = cand_raw.decode("utf-8")
    check("closure.fit_result_new_format", FIT_RESULT_NEW in text and FIT_RESULT_OLD not in text)
    check("closure.prod_models_compact", "PROD_MODELS count=%d initial_index=%d\"" in text
          and "candidates=%r" not in text.split("PROD_MODELS", 1)[1][:200])
    for name in ("prod_r15_window_decision", "prod_cpm_authorize_operation", "prod_cpm_open_fit_stage",
                 "prod_cpm_release_fit_stage", "prod_r15_result"):
        check("coverage.post_baseline_helper_in_reconstruction.%s" % name, name in dict(owners(cand)))
    # Item-6 continuity.
    item6_removed = ["acquire_semantic_provider_for_mode", "SidecarSemanticProvider", "MasterTxtSemanticProvider",
                     "prod_semantic_provider_health_from_descriptor", "semantic_snapshots_for_current_shot"]
    check("item6.removals_still_absent", not set(item6_removed) & top_names)
    gsp = [n for n in cand.body if isinstance(n, ast.FunctionDef) and n.name == "get_semantic_provider"][0]
    check("item6.refusal_stub_unchanged", len(gsp.body) == 1 and isinstance(gsp.body[0], ast.Raise))
    return problems


SENSITIVITY = [
    ("changed_product_predicate", u"        if not self.fit_active", u"        if self.fit_active"),
    ("omitted_release", u"    failure = stage.release()\n", u"    failure = None\n"),
    ("widened_handler", u"            except Exception:\n                pass\n",
     u"            except BaseException:\n                pass\n"),
    ("changed_retained_event", u"PROD_CPM_FIT_STAGE_RELEASED index=%d ok=%r", u"PROD_CPM_FIT_STAGE_RELEASED idx=%d ok=%r"),
    ("deleted_post_fit_readiness", u"\"G18AN_POST_FIT_ACTION_STATE save_body=%r save_expr=%r semantic_ready=%r\"",
     u"\"G18AN_POST_FIT_ACTION_STATE save_body=%r save_expr=%r semantic_ready=%r \""),
    ("altered_p02_safe_write_json", u"def p02_safe_write_json(", u"def p02_safe_write_json( "),
    ("missing_raise_exc", u"            raise exc\n", u"            raise\n"),
    ("edited_post_baseline_helper", u"\"PROD_CPM_OPERATION_AUTHORIZED operation=%r", u"\"PROD_CPM_OPERATION_AUTHORIZED op=%r"),
]


def section_sensitivity(ref_raw, manifest, cand_raw):
    text = cand_raw.decode("utf-8")
    for label, old, new in SENSITIVITY:
        if text.count(old) < 1:
            check("sensitivity.%s.applies" % label, False, old[:60])
            continue
        mutated = text.replace(old, new, 1).encode("utf-8")
        check("sensitivity.%s.rejected" % label, bool(compare_candidate(ref_raw, manifest, mutated)))
    # Wrapped product-coupled readiness statement and an unexpected removal.
    m = re.search(r"\n(\s+)log_line\(\n\s+\"G18AN_POST_FIT_ACTION_STATE[^\n]*\n(?:.*\n){5}\s+\)\n", text)
    if m:
        block = m.group(0)[1:]
        ind = m.group(1)
        wrapped = ind + u"try:\n" + u"".join(u"    " + l + u"\n" for l in block.rstrip(u"\n").split(u"\n")) \
            + ind + u"except Exception:\n" + ind + u"    pass\n"
        check("sensitivity.wrapped_post_fit_readiness.rejected",
              bool(compare_candidate(ref_raw, manifest, text.replace(block, wrapped, 1).encode("utf-8"))))
    else:
        check("sensitivity.wrapped_post_fit_readiness.applies", False)
    check("sensitivity.unexpected_removal.rejected", bool(compare_candidate(
        ref_raw, manifest, re.sub(u"\ndef p01_row_by_literal\\(.*?\n    return matches\\[0\\]\n", u"\n", text,
                                  count=1, flags=re.S).encode("utf-8"))))


# --- Runtime: canonical-route harness with failing diagnostics ---------------------

class InjectedLogFailure(RuntimeError):
    pass


class FailingRepr(_TEXT):
    def __repr__(self):
        raise InjectedLogFailure("repr failure")


def throwing_logger(events, fail_on):
    def log_line(text):
        events.append(_TEXT(text)[:80] if not isinstance(text, Exception) else repr(text))
        if fail_on is not None and _TEXT(text).startswith(fail_on):
            raise InjectedLogFailure("injected diagnostic failure: %s" % fail_on)
        return True
    return log_line


def section_route_runtime(reference):
    import test_cpm_app_canonical_route as route
    if not os.path.isfile(os.path.join(route.LIVE_DIR, route.MASTER_NAME)):
        check("route_runtime.fixtures_published", False, "run test_cpm_app_canonical_route.py --phase=publish first")
        return
    ref_path = os.path.join(route.FIXTURE_ROOT, "item7_reference_app.py")
    with open(ref_path, "wb") as f:
        f.write(_read_reference(reference))
    route.Env.bindings = route._bindings_from_pairs(route.base.LIVE_BINDINGS)
    apps = {"candidate": route.AppSource(APP_PATH), "reference": route.AppSource(ref_path)}

    def namespace(which, fail_on, events):
        ns = route.build_namespace(apps[which])
        ns["log_line"] = throwing_logger(events, fail_on)
        ns["p03_target_bindings"] = lambda animset: [dict(b) for b in route.Env.bindings]
        return ns

    def run(which, fail_on, fn):
        events = []
        ns = namespace(which, fail_on, events)
        try:
            return ("ok", fn(ns)), events
        except Exception as exc:  # noqa: BLE001
            return ("raised", type(exc).__name__, _TEXT(exc)[:120]), events

    def scope_of(ns):
        adapter, health = ns["prod_probe_semantic_provider"](route.IDENTITY)
        return ns["prod_scope"](route.IDENTITY, adapter)

    def authorize(ns, label=u"Apply Preset"):
        return ns["prod_cpm_authorize_operation"](route.IDENTITY, scope_of(ns), ns["P03_KIND_BODY"], label)

    def stage_cycle(ns):
        ctx = ns["prod_cpm_authorize_operation"](route.IDENTITY, scope_of(ns), ns["P03_KIND_BODY"], u"Clothing Fit")
        stage = ns["prod_cpm_open_fit_stage"](ctx, {"animset": object()}, 0)
        gen = stage.generation
        return [gen == ctx["master_sha256"], ns["prod_cpm_release_fit_stage"](stage, 0)]

    def stale_refusal(ns):
        scope = scope_of(ns)
        scope["authority"] = dict(scope["authority"], provider_sha256=u"0" * 64)
        return ns["prod_cpm_authorize_operation"](route.IDENTITY, scope, ns["P03_KIND_BODY"], u"Apply Preset")

    def unmigrated(ns):
        return ns["ProdCpmUnmigratedProvider"]("probe").query_many([u"x"])

    def generation_check(ns):
        ns["prod_cpm_open_adapter"] = lambda: (_ for _ in ()).throw(RuntimeError("adapter down"))
        return ns["prod_cpm_scope_generation_stale"]({"authority": {"provider_sha256": u"x"}})

    def probe_health(ns):
        return route._canon(ns["prod_probe_semantic_provider"](route.IDENTITY)[1])

    def norm(outcome):
        if outcome[0] == "ok":
            return ("ok", route._canon(outcome[1]))
        return outcome
    cases = [
        ("probe_health", probe_health, "PROD_PROVIDER_HEALTH"),
        ("authorize", lambda ns: authorize(ns), "PROD_CPM_OPERATION_AUTHORIZED"),
        ("stage_open_release", stage_cycle, "PROD_CPM_FIT_STAGE_OPEN"),
        ("stage_release", stage_cycle, "PROD_CPM_FIT_STAGE_RELEASED"),
        ("stale_refusal", stale_refusal, "PROD_CPM_OPERATION_AUTHORIZATION_REFUSED"),
        ("unmigrated_refusal", unmigrated, "PROD_CPM_UNMIGRATED_AUTHORITY_REFUSED"),
        ("generation_check_failed", generation_check, "PROD_CPM_GENERATION_CHECK_FAILED"),
    ]
    def idle():
        b = route._broker()
        return (b.outstanding_lease_count(), b.provider_counters()["current_open_provider_count"])
    check("inject.broker_idle_before", idle() == (0, 0), idle())
    for label, fn, event in cases:
        base_out, base_events = run("candidate", None, fn)
        inj_out, inj_events = run("candidate", event, fn)
        emitted = any(e.startswith(event) for e in base_events)
        check("inject.%s.event_emitted" % label, emitted, base_events[-3:])
        check("inject.%s.outcome_unchanged_under_failing_emitter" % label, norm(inj_out) == norm(base_out),
              [norm(base_out), norm(inj_out)])
        check("inject.%s.idle_after" % label, idle() == (0, 0), idle())
    # A diagnostic argument whose repr raises (failure before reaching the sink).
    base_out, _ = run("candidate", None, lambda ns: authorize(ns))
    rep_out, _ = run("candidate", None, lambda ns: authorize(ns, FailingRepr(u"Apply Preset")))
    check("inject.failing_repr_argument_contained", norm(rep_out) == norm(base_out), [norm(base_out), norm(rep_out)])
    check("inject.failing_repr.idle_after", idle() == (0, 0), idle())
    # Reference comparison last: the item-6 reference's uncontained emitters can strand a broker
    # lease (process-wide), so it must not run before any candidate idle check. Informational.
    for label, fn, event in cases:
        ref_out, _ = run("reference", event, fn)
        print("      (reference, %s under the same injection: %s; broker leases/providers after: %r)"
              % (label, norm(ref_out)[0], idle()))
    ref_rep, _ = run("reference", None, lambda ns: authorize(ns, FailingRepr(u"Apply Preset")))
    print("      (reference with the failing repr: %s)" % (norm(ref_rep)[0],))
    route.Env.bindings = []


def _exec_in(code, namespace):
    exec(code, namespace)


def section_real_sink():
    """The real log_line/reset_log contain their own I/O failures."""
    with open(APP_PATH, "rb") as f:
        raw = f.read()
    src = raw.decode("utf-8")
    tree = ast.parse(raw)
    lines = src.split(u"\n")
    ns = {"datetime": __import__("datetime"), "u": _TEXT, "OUTPUT_PATH": "unused"}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in ("log_line", "reset_log"):
            seg = [t for n, t in segments(tree.body, lines, 1, len(lines)) if n is node][0]
            _exec_in(compile(seg, "app:%s" % node.name, "exec"), ns)

    class Broken(object):
        def __init__(self, fail):
            self.fail = fail

        def write(self, data):
            if self.fail == "write":
                raise IOError("write")

        def flush(self):
            if self.fail == "flush":
                raise IOError("flush")

        def close(self):
            if self.fail == "close":
                raise IOError("close")
    # open/write/flush failures report False; a close failure follows a completed write and
    # flush, so the unchanged sink reports True. Every mode must return without raising.
    expected = {"open": False, "write": False, "flush": False, "close": True}
    for fail in ("open", "write", "flush", "close"):
        def opener(path, mode, fail=fail):
            if fail == "open":
                raise IOError("open")
            return Broken(fail)
        ns["open"] = opener
        try:
            result = ns["log_line"](u"X")
            ok = result is expected[fail]
        except Exception:  # noqa: BLE001
            ok = False
        check("sink.log_line_contains_%s_failure" % fail, ok)
        try:
            result = ns["reset_log"]()
            ok = result is expected[fail]
        except Exception:  # noqa: BLE001
            ok = False
        check("sink.reset_log_contains_%s_failure" % fail, ok)


# --- Runtime: real ProdWindow in the R15 environment (child processes) ----------------

def _r15():
    import test_cpm_app_r15_namespace_isolation as r15
    return r15


class WindowEnv(object):
    """A real ProdWindow from the deployed private app, with controlled collaborators."""

    def __init__(self, qt_mode, root, app_bytes, timer_proxy=True):
        r15 = _r15()
        self.r15 = r15
        self.env = r15.Env(qt_mode, root)
        self.env.deploy(impl_bytes=app_bytes)
        self.env.click()
        self.module = self.env.module()
        self.ns = self.module.__dict__
        self.window = self.env.slot()
        self.events = []
        self.fail_on = [None]
        real_qtcore = self.ns["QtCore"]
        scheduled = self.scheduled = []
        fail_schedule = self.fail_schedule = [False]

        class Timer(object):
            @staticmethod
            def singleShot(delay, fn):
                if fail_schedule[0]:
                    raise RuntimeError("scheduling failure")
                scheduled.append((delay, fn))

        class QtCoreProxy(object):
            QTimer = Timer

            def __getattr__(self, name):
                return getattr(real_qtcore, name)
        if timer_proxy:  # records zero-delay scheduling instead of running it
            self.ns["QtCore"] = QtCoreProxy()
        events, fail_on = self.events, self.fail_on

        def log_line(text):
            events.append(_TEXT(text)[:120])
            if fail_on[0] is not None and _TEXT(text).startswith(fail_on[0]):
                raise InjectedLogFailure("injected diagnostic failure: %s" % fail_on[0])
            return True
        self.ns["log_line"] = log_line
        self.ns["prod_context_token"] = lambda identity: {"token": u"ctx"}
        self.ns["prod_validate_context_token"] = lambda token: True
        self.ns["prod_resource_snapshot"] = lambda label: None
        self.status = []
        w = self.window
        real_set_status = w.set_status

        def set_status(text, level=u"neutral"):
            self.status.append((_TEXT(text), level))
            return real_set_status(text, level)
        w.set_status = set_status
        self.dialogs = []
        self.ns["tool_warning_message"] = lambda parent, title, message: self.dialogs.append(_TEXT(title))

    def reset(self):
        w = self.window
        w.operation = None
        w.fit_active = False
        w.closing_requested = False
        w._cpm_stale_rebuild_pending = False
        del self.events[:]
        del self.scheduled[:]
        del self.status[:]
        del self.dialogs[:]
        self.fail_on[0] = None
        self.fail_schedule[0] = False


def scenario_handlers(w):
    """Python-2 handler continuity: guard, operation_begin failure, Fit start/stage failures."""
    ns, win = w.ns, w.window
    out = {}

    def guard_error(fail_on):
        w.reset()
        w.fail_on[0] = fail_on

        def fn():
            raise RuntimeError("product failure")
        win.guard("Apply Body Preset", fn)
        return {"status": w.status[-1:], "dialogs": list(w.dialogs), "operation": win.operation,
                "busy": bool(win.busy)}
    def capture(fn, *args):
        try:
            return fn(*args)
        except Exception as exc:  # noqa: BLE001
            return {"raised": [type(exc).__name__, _TEXT(exc)[:120]]}
    out["action_error_baseline"] = capture(guard_error, None)
    out["action_error_injected"] = capture(guard_error, "PROD_ACTION_ERROR")

    def begin_fail(fail_on):
        w.reset()
        w.fail_on[0] = fail_on
        real = win.operation_begin
        win.operation_begin = lambda label, pin_context=True: (_ for _ in ()).throw(RuntimeError("begin failure"))
        try:
            win.guard("Apply Body Preset", lambda: None)
        finally:
            del win.operation_begin
        return {"status": w.status[-1:], "operation": win.operation}
    out["begin_fail_baseline"] = capture(begin_fail, None)
    out["begin_fail_injected"] = capture(begin_fail, "PROD_OPERATION_BEGIN_FAIL")

    def fit_start(fail_on, identity):
        w.reset()
        w.fail_on[0] = fail_on
        win.fit_checked_identities = lambda: [{"name": u"t", "model": u"m", "checksum": 1}]
        win.identity = identity
        try:
            win.fit_selected()
        finally:
            del win.fit_checked_identities
        return {"status": w.status[-1:], "fit_active": bool(win.fit_active), "operation": win.operation,
                "scheduled": len(w.scheduled)}
    out["fit_start_fail_baseline"] = capture(fit_start, None, None)
    out["fit_start_fail_injected"] = capture(fit_start, "CLOTHING_FIT_START_FAIL", None)

    def fit_stage_fail(fail_on):
        w.reset()
        w.fail_on[0] = fail_on
        assert win.operation_begin(u"Clothing Fit", pin_context=False)
        win.fit_generation += 1
        win.fit_active = True
        win.fit_selected_identities = [{"name": u"t", "model": u"m", "checksum": 1}]
        for attr in ("fit_changed", "fit_unchanged", "fit_committed_order", "fit_partial", "fit_skipped",
                     "fit_failed", "fit_unattempted"):
            setattr(win, attr, [])
        win.operation_revalidate = lambda: None
        real = ns["g11a_resolve_target"]
        ns["g11a_resolve_target"] = lambda identity: (_ for _ in ()).throw(RuntimeError("target vanished"))
        try:
            win.fit_stage(win.fit_generation, 0)
        finally:
            ns["g11a_resolve_target"] = real
            del win.operation_revalidate
        return {"status": w.status[-1:], "fit_active": bool(win.fit_active), "operation": win.operation,
                "failed": [(f["verification"], f["committed"]) for f in win.fit_failed]}
    out["fit_stage_fail_baseline"] = capture(fit_stage_fail, None)
    out["fit_stage_fail_injected"] = capture(fit_stage_fail, "CLOTHING_FIT_FAIL")
    return out


def scenario_fit_finish(w):
    """Real fit_finish -> semantic_provider_ready -> stale-rebuild request."""
    ns, win = w.ns, w.window
    out = {}

    class Adapter(object):
        def generation_descriptor(self):
            return {"source_sha256": u"f" * 64, "provider_generation": 2}
    ns["prod_cpm_open_adapter"] = lambda: Adapter()
    calls = []
    real_ready = type(win).semantic_provider_ready

    def counting_ready(self):
        calls.append(sys._getframe(1).f_code.co_name)
        return real_ready(self)

    def run(closing, fail_schedule, fail_on=None):
        w.reset()
        del calls[:]
        assert win.operation_begin(u"Clothing Fit", pin_context=False)
        win.fit_generation += 1
        win.fit_active = True
        win.closing_requested = closing
        win.fit_selected_identities = [{"name": u"t", "model": u"m", "checksum": 1}]
        for attr in ("fit_changed", "fit_unchanged", "fit_committed_order", "fit_partial", "fit_skipped",
                     "fit_failed", "fit_unattempted"):
            setattr(win, attr, [])
        win.fit_changed = [{"name": u"t"}]
        win.identity = {"model": u"m", "checksum": 1, "animset_name": u"a"}
        win.scope = {"identity": dict(win.identity), "authority": {"provider_sha256": u"0" * 64}}
        win.provider_health = {"status": u"healthy"}
        w.fail_schedule[0] = fail_schedule
        w.fail_on[0] = fail_on
        guard_calls = []
        win.guard = lambda *a, **k: guard_calls.append(a)
        win.semantic_provider_ready = types.MethodType(counting_ready, win) if not PY2 else \
            types.MethodType(counting_ready, win, type(win))
        try:
            win.fit_finish(win.fit_generation)
            raised = None
        except Exception as exc:  # noqa: BLE001
            raised = (type(exc).__name__, _TEXT(exc))
        finally:
            del win.guard
            del win.semantic_provider_ready
            win.closing_requested = False
        result = {"raised": raised, "readiness_calls": len(calls),
                  "readiness_from_fit_finish": calls.count("fit_finish"),
                  "pending": bool(getattr(win, "_cpm_stale_rebuild_pending", False)),
                  "scheduled": [getattr(fn, "__name__", "?") for _, fn in w.scheduled],
                  "operation_ended": win.operation is None, "replays": len(guard_calls),
                  "result_line": [e for e in w.events if e.startswith("CLOTHING_FIT_RESULT")][:1]}
        if win.operation is not None:
            win.operation_end(u"Clothing Fit")
        win.fit_active = False
        return result
    out["stale"] = run(False, False)
    out["stale_result_event_injected"] = run(False, False, "CLOTHING_FIT_RESULT")
    out["schedule_failure"] = run(False, True)
    out["closing"] = run(True, False)   # last: a closing window may finalize at operation end
    return out


def scenario_startup(w):
    """R15 startup outcomes with diagnostic failures (StartProdTool called directly)."""
    ns, module = w.ns, w.module
    out = {}

    def close_window():
        slot = w.env.slot()
        if slot is not None:
            slot.close()
            w.env.settle()

    def start(fail_on=None, prepare_raises=None):
        close_window()
        del w.events[:]
        ns["PROD_R15_STARTUP"]["state"] = ns["PROD_R15_STARTUP_IDLE"]
        w.fail_on[0] = fail_on
        real_prepare = ns["prod_prepare_library_root"]
        if prepare_raises is not None:
            def failing():
                raise prepare_raises
            ns["prod_prepare_library_root"] = failing
        try:
            result = module.StartProdTool()
            escaped = None
        except BaseException as exc:  # noqa: BLE001
            result, escaped = None, exc
        finally:
            ns["prod_prepare_library_root"] = real_prepare
        return result, escaped
    for label, fail_on in (("baseline", None), ("g18an_run", "G18AN_RUN"), ("r15_module", "PROD_R15_MODULE"),
                           ("window_shown", "PROD_WINDOW_SHOWN")):
        result, escaped = start(fail_on)
        out["create_" + label] = {"outcome": (result or {}).get("outcome"), "escaped": repr(escaped) if escaped else None,
                                  "state": ns["PROD_R15_STARTUP"]["state"], "window": w.env.slot() is not None}
    for label, fail_on in (("baseline", None), ("injected", "PROD_OPEN_FAIL")):
        result, escaped = start(fail_on, RuntimeError("library root unavailable"))
        out["open_fail_" + label] = {"outcome": (result or {}).get("outcome"), "code": (result or {}).get("code"),
                                     "state": ns["PROD_R15_STARTUP"]["state"],
                                     "escaped": repr(escaped) if escaped else None}

    class Interrupt(BaseException):
        pass
    for label, fail_on in (("without_log_failure", None), ("with_log_failure", "PROD_OPEN_FAIL")):
        original = Interrupt("original interrupt")
        result, escaped = start(fail_on, original)
        out["interrupt_" + label] = {"same_object": escaped is original, "type": type(escaped).__name__,
                                     "state": ns["PROD_R15_STARTUP"]["state"]}
    close_window()
    return out


CHILD_SCENARIOS = {"handlers": scenario_handlers, "fit_finish": scenario_fit_finish, "startup": scenario_startup}


def child_main(scenario, qt_mode, root, reference, target):
    try:
        app_bytes = _read_reference(reference) if target == "reference" else open(APP_PATH, "rb").read()
        w = WindowEnv(qt_mode, root, app_bytes, timer_proxy=(scenario != "startup"))
        result = CHILD_SCENARIOS[scenario](w)
        payload = {"ok": True, "result": result}
    except BaseException:  # noqa: BLE001
        import traceback
        payload = {"ok": False, "error": traceback.format_exc()[-2000:]}
    sys.stdout.write("ITEM7_CHILD_RESULT " + json.dumps(payload, default=repr, sort_keys=True) + "\n")
    sys.stdout.flush()


def run_child(scenario, mode, reference, target):
    import tempfile
    root = os.path.join(tempfile.gettempdir(), "cpm_item7_window", "%s_%s_%s" % (mode, scenario, target))
    if os.path.isdir(root):
        shutil.rmtree(root)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child=%s" % scenario, "--qt=%s" % mode,
                             "--root=%s" % root, "--reference=%s" % reference, "--target=%s" % target],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = proc.communicate()[0].decode("utf-8", "replace")
    for line in output.splitlines():
        if line.startswith("ITEM7_CHILD_RESULT "):
            return json.loads(line[len("ITEM7_CHILD_RESULT "):])
    return {"ok": False, "error": output[-2000:]}


def section_window_runtime(reference):
    r15 = _r15()
    modes = (["real"] if r15.qt_available() else []) + ["model"]
    print("Qt modes for window gates: %s" % ", ".join(modes))
    for mode in modes:
        res = {}
        for scenario in ("handlers", "fit_finish", "startup"):
            for target in ("candidate", "reference"):
                res[(scenario, target)] = run_child(scenario, mode, reference, target)
                check("%s.%s.%s.child_completed" % (mode, scenario, target), res[(scenario, target)]["ok"],
                      res[(scenario, target)].get("error"))
        c = lambda s: res[(s, "candidate")].get("result") or {}
        rref = lambda s: res[(s, "reference")].get("result") or {}
        h = c("handlers")
        for name in ("action_error", "begin_fail", "fit_start_fail", "fit_stage_fail"):
            check("%s.handlers.%s.continues_like_baseline" % (mode, name),
                  h.get(name + "_injected") == h.get(name + "_baseline") and h.get(name + "_baseline") is not None
                  and "raised" not in h.get(name + "_baseline"),
                  [h.get(name + "_baseline"), h.get(name + "_injected")])
        check("%s.handlers.fit_stage_fail.not_committed_and_ended" % mode,
              h.get("fit_stage_fail_baseline", {}).get("operation") is None
              and h.get("fit_stage_fail_baseline", {}).get("failed") == [["not-committed", False]])
        f = c("fit_finish")
        fr = rref("fit_finish")
        st, st_ref = f.get("stale", {}), fr.get("stale", {})

        def behaviour(r):
            # Everything except the per-run generation counter in the result line.
            return dict((k, v) for k, v in r.items() if k != "result_line")
        # The post-Fit statement evaluates semantic_provider_ready exactly once from fit_finish;
        # operation_end's unchanged action-state refresh accounts for any further calls, so the
        # total must equal the pinned item-6 reference.
        check("%s.fit_finish.readiness_runs_once" % mode, st.get("readiness_from_fit_finish") == 1
              and st.get("readiness_calls") == st_ref.get("readiness_calls"), [st, st_ref])
        check("%s.fit_finish.stale_rebuild_requested" % mode, st.get("pending") is True
              and (st.get("scheduled") or [None])[0] == "prod_cpm_run_stale_rebuild", st)
        check("%s.fit_finish.stale_behaviour_equals_reference" % mode,
              bool(st_ref) and behaviour(st) == behaviour(st_ref), [st, st_ref])
        check("%s.fit_finish.no_replay_and_operation_ended" % mode, st.get("replays") == 0
              and st.get("operation_ended") is True and st.get("raised") is None, st)
        check("%s.fit_finish.new_result_format" % mode, any(e.startswith("CLOTHING_FIT_RESULT generation=")
                                                            for e in st.get("result_line", [])), st.get("result_line"))
        inj = f.get("stale_result_event_injected", {})
        check("%s.fit_finish.result_event_failure_contained" % mode, inj.get("raised") is None
              and inj.get("pending") is True and inj.get("operation_ended") is True
              and behaviour(inj) == behaviour(st), [st, inj])
        clo, clo_ref = f.get("closing", {}), fr.get("closing", {})
        check("%s.fit_finish.readiness_isolated_to_post_fit_statement" % mode,
              clo.get("readiness_from_fit_finish") == 0 and clo.get("operation_ended") is True
              and bool(clo_ref) and behaviour(clo) == behaviour(clo_ref), [clo, clo_ref])
        sf, sf_ref = f.get("schedule_failure", {}), rref("fit_finish").get("schedule_failure", {})
        check("%s.fit_finish.schedule_failure_propagates_like_item6" % mode,
              sf.get("raised") == ["RuntimeError", "scheduling failure"] and sf.get("raised") == sf_ref.get("raised")
              and sf.get("operation_ended") == sf_ref.get("operation_ended"), [sf, sf_ref])
        s = c("startup")
        for label in ("baseline", "g18an_run", "r15_module", "window_shown"):
            v = s.get("create_" + label, {})
            check("%s.startup.create_%s" % (mode, label), v.get("outcome") == "created" and v.get("escaped") is None
                  and v.get("state") == "idle" and v.get("window") is True, v)
        for label in ("baseline", "injected"):
            v = s.get("open_fail_" + label, {})
            check("%s.startup.open_fail_%s_not_stuck" % (mode, label), v.get("outcome") == "failed"
                  and v.get("code") == "open-failed" and v.get("state") == "idle" and v.get("escaped") is None, v)
        for label in ("without_log_failure", "with_log_failure"):
            v = s.get("interrupt_" + label, {})
            check("%s.startup.interrupt_%s_original_escapes" % (mode, label), v.get("same_object") is True
                  and v.get("type") == "Interrupt" and v.get("state") == "idle", v)
        ref_int = rref("startup").get("interrupt_with_log_failure", {})
        print("      (%s reference, interrupt with log failure: escaped original=%s type=%s)"
              % (mode, ref_int.get("same_object"), ref_int.get("type")))


def main():
    args = dict(a.split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    reference = args.get("--reference") or os.environ.get("CPM_ITEM7_REFERENCE_APP")
    if "--child" in args:
        sys.path.insert(0, _THIS_DIR)
        child_main(args["--child"], args["--qt"], args["--root"], reference, args.get("--target", "candidate"))
        return
    if "--write-manifest" in sys.argv[1:]:
        write_manifest(reference)
        return
    print("Interpreter: %s" % sys.version.split()[0])
    ref_raw, manifest, cand_raw = section_identity(reference)
    print("Candidate app sha256: %s" % _sha_bytes(cand_raw))
    section_static(ref_raw, manifest, cand_raw)
    section_sensitivity(ref_raw, manifest, cand_raw)
    section_real_sink()
    section_route_runtime(reference)
    section_window_runtime(reference)
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)


if __name__ == "__main__":
    sys.path.insert(0, _THIS_DIR)
    main()
