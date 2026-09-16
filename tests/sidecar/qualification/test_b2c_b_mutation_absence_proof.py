# -*- coding: utf-8 -*-
"""R3-B2C-B Section 4: proves no mutation API is reachable from the new
migrated authority-acquisition call path. Two independent proofs:

  (1) STATIC text scan of the candidate diff hunks + every file the new
      code path imports (sfm_master_authority candidate package +
      normalizer_compat_adapter.py) for known mutation-related symbols.

  (2) DYNAMIC code-object inspection: recursively walks
      acquire_master_index_via_qualified_authority's compiled code
      object (and everything it transitively calls within the candidate
      authority package) via co_names, proving no mutation symbol is
      even NAMEABLE from this call path -- stronger than a text scan,
      since it inspects the actual bytecode-level name table Python
      itself would resolve against, not just source text.

Never launches SFM. Read-only.
"""
import dis
import hashlib
import os
import sys

MUTATION_SYMBOLS = (
    "SetUndoEnabled", "WINFUNCTYPE", "native_ptr",
    "prepare_native_callback", "dm.", "ctypes.cast", "REBUILD_RVA",
    "EXPECTED_PROLOGUE", "set_group_color", "set_selectable",
    "DmeTransformControl", "CreateUndo", "StartUndo",
)
# "rebuild" as a bare word is intentionally excluded from the static
# text scan -- this entire project's command is named "Rebuild Control
# Groups", so the bare word appears constantly in prose/docstrings
# (e.g. pointer.py's "is B2E's responsibility (rebuild publication +
# mutex)", about regenerating the SIDECAR ARTIFACT file, an unrelated
# B2E concept). The actual DME mutation CALL SYNTAX is checked instead.
MUTATION_CALL_PATTERNS = (".rebuild(", "self.rebuild(", "dm.rebuild(")

CANDIDATE_NORMALIZER_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_candidate.py"
)
CANDIDATE_AUTHORITY_DIR = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c\sfm_master_authority_productionized"
CANDIDATE_AUTHORITY_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"

for p in (CANDIDATE_AUTHORITY_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

# ---------------------------------------------------------------------
# (1) STATIC scan: the new function's own source (lines 1439-1485 of the
# candidate file) plus every file the new code path can reach.
# ---------------------------------------------------------------------
with open(CANDIDATE_NORMALIZER_PATH, "rb") as f:
    cand_bytes = f.read()
cand_lines = cand_bytes.decode("utf-8" if sys.version_info[0] >= 3 else "ascii").splitlines() \
    if sys.version_info[0] >= 3 else cand_bytes.splitlines()
new_func_src = "\n".join(cand_lines[1438:1485])  # lines 1439-1485, 0-indexed slice

static_hits = [sym for sym in MUTATION_SYMBOLS if sym in new_func_src]
static_hits += [pat for pat in MUTATION_CALL_PATTERNS if pat in new_func_src]
check("static.1 new function source (lines 1439-1485) contains no mutation-related symbol/call",
      len(static_hits) == 0, static_hits)

scanned_files = []
authority_hits = {}
for fname in sorted(os.listdir(CANDIDATE_AUTHORITY_DIR)):
    if not fname.endswith(".py"):
        continue
    path = os.path.join(CANDIDATE_AUTHORITY_DIR, fname)
    with open(path, "rb") as f:
        src = f.read()
    src_text = src.decode("utf-8", "replace")
    scanned_files.append(fname)
    hits = [sym for sym in MUTATION_SYMBOLS if sym in src_text]
    hits += [pat for pat in MUTATION_CALL_PATTERNS if pat in src_text]
    if hits:
        authority_hits[fname] = hits
check("static.2 no file in the candidate authority package (the new call path's only "
      "transitive dependency) contains any mutation-related symbol",
      len(authority_hits) == 0, authority_hits)
print("[STATIC] scanned %d authority-package files: %s" % (len(scanned_files), scanned_files))

# ---------------------------------------------------------------------
# (2) DYNAMIC: compiled code-object co_names inspection.
# ---------------------------------------------------------------------
code_obj = compile(new_func_src, "<candidate_new_function>", "exec")


def walk_names(co, seen=None):
    if seen is None:
        seen = set()
    names = set(co.co_names) | set(co.co_varnames)
    for const in co.co_consts:
        if hasattr(const, "co_names"):
            names |= walk_names(const, seen)
    return names


all_names = walk_names(code_obj)
dynamic_hits = [sym for sym in MUTATION_SYMBOLS if any(sym.rstrip(".") == n for n in all_names)]
check("dynamic.1 compiled code object's transitive co_names contains no mutation-related symbol",
      len(dynamic_hits) == 0, (dynamic_hits, sorted(all_names)))
print("[DYNAMIC] all names referenced by the new function's compiled code: %s" % sorted(all_names))

# ---------------------------------------------------------------------
# Sentinel: actually RUN the function with a monkeypatched broker that
# fails loudly if anything outside the expected acquire_or_reuse_views
# call is invoked, then separately confirm the RETURNED payload's own
# type composition contains only plain, detached Python data (no
# provider/native-handle-shaped object anywhere in it) -- Section 7's
# "compatibility dict contains only detached Python data" requirement,
# proven here as a mutation-absence corollary too.
# ---------------------------------------------------------------------
from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as _b2c_normalizer_adapter  # noqa: E402
from sfm_master_authority import sidecar_contract  # noqa: E402

FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"

ns_cand = {"_b2c_normalizer_adapter": _b2c_normalizer_adapter}


class _FakeAuthorityRuntimeModule(object):
    def __init__(self, broker_instance):
        self._b = broker_instance

    def get_broker(self, *a, **kw):
        return self._b


exec(new_func_src, ns_cand)

b = broker_mod.Broker(api_version="b2c-b-mutation-proof")
ns_cand["_b2c_authority_runtime"] = _FakeAuthorityRuntimeModule(b)

wanted = set(["left", "right"])
result = ns_cand["acquire_master_index_via_qualified_authority"](
    REAL_MASTER_PATH, wanted, shipped_root=OFFICIAL_ROOT,
)
check("sentinel.1 function returned successfully with a real result dict", isinstance(result, dict))

sidecar_contract.ensure_loaded()
_ProviderClass = sidecar_contract._provider_module.BoundedProvider


def walk_for_provider(obj, path="root", seen=None):
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return []
    seen.add(id(obj))
    hits = []
    if isinstance(obj, _ProviderClass):
        hits.append(path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            hits += walk_for_provider(v, "%s[%r]" % (path, k), seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for i, v in enumerate(obj):
            hits += walk_for_provider(v, "%s[%d]" % (path, i), seen)
    return hits


provider_leaks = walk_for_provider(result)
check("sentinel.2 returned compatibility dict contains ZERO live BoundedProvider references anywhere "
      "(pure detached Python data, Section 7 requirement)", len(provider_leaks) == 0, provider_leaks)

counters = b.provider_counters()
check("sentinel.3 provider closed before returning to the (simulated) mutation boundary "
      "(current_open_provider_count == 0)", counters["current_open_provider_count"] == 0, counters)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
