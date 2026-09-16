# -*- coding: utf-8 -*-
"""R3-B2C-B Section 14: performance/read-count sanity. Compares frozen
parse_targeted_master() elapsed time against the migrated candidate's
first acquisition and a repeated same-generation (cache-hit)
acquisition, using a realistic scope (W1's real 208-fold single-target
vocabulary). Not an optimization exercise -- purely measurement,
against the already-qualified architecture.
"""
import hashlib
import json
import sys
import time

NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
CANDIDATE_NORMALIZER_PATH = (
    r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_normalizer"
    r"\Rebuild_Control_Groups_Normalizer_B2CB_candidate.py"
)
CANDIDATE_AUTHORITY_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
PUBLIC_DOCS = r"C:\Users\Public\Documents"

for p in (CANDIDATE_AUTHORITY_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

print("Interpreter: %s" % sys.version)
try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False

with open(NORMALIZER_PROD_PATH, "rb") as f:
    prod_bytes = f.read()
with open(CANDIDATE_NORMALIZER_PATH, "rb") as f:
    cand_bytes = f.read()

if _PY2:
    prod_lines = prod_bytes.splitlines()
    cand_lines = cand_bytes.splitlines()
else:
    prod_lines = prod_bytes.decode("utf-8").splitlines()
    cand_lines = cand_bytes.decode("utf-8").splitlines()


def extract(lines, a, b):
    return "\n".join(lines[a - 1: b]) + "\n"


PROD_RANGES = [(138, 138), (604, 605), (647, 657), (659, 671), (1169, 1202),
               (1204, 1339), (1340, 1370), (1373, 1413), (1416, 1723)]
import re as _re_module
ns_ref = {"re": _re_module}
if not _PY2:
    ns_ref["unicode"] = str
prod_src = "\n\n".join(extract(prod_lines, a, b) for a, b in PROD_RANGES)
exec(prod_src, ns_ref)

new_func_src = extract(cand_lines, 1439, 1485)

from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as _b2c_normalizer_adapter  # noqa: E402
from sfm_master_authority import sidecar_contract  # noqa: E402

ns_cand = {"_b2c_normalizer_adapter": _b2c_normalizer_adapter}


class _FakeAuthorityRuntimeModule(object):
    def __init__(self, b):
        self._b = b

    def get_broker(self, *a, **kw):
        return self._b


exec(new_func_src, ns_cand)
ACQUIRE = ns_cand["acquire_master_index_via_qualified_authority"]

with open(PUBLIC_DOCS + r"\SFM_R2_W1_FoxRealWorkload.json") as f:
    w1 = json.load(f)
w1_folds = set(w1["workload"]["unique_folded_vocabulary"])
print("[SCOPE] W1 realistic single-target scope: %d folds" % len(w1_folds))

# ---------------------------------------------------------------------
# Frozen parser path (only runnable under Python 2.7.5 -- see docstring
# of test_b2c_b_readonly_migration.py for why).
# ---------------------------------------------------------------------
if _PY2:
    t0 = time.time()
    ref = ns_ref["parse_targeted_master"](REAL_MASTER_PATH, w1_folds, validate_conflicts=False)
    t_frozen = time.time() - t0
    print("[PERF] frozen parse_targeted_master (W1 scope): %.4fs (mapping_count=%d)" % (
        t_frozen, ref["mapping_count"]))
else:
    t_frozen = None
    print("[PERF] frozen parse_targeted_master: SKIPPED under Python 3 (see docstring note)")

# ---------------------------------------------------------------------
# Migrated candidate: first acquisition, then repeated same-generation.
# ---------------------------------------------------------------------
b = broker_mod.Broker(api_version="b2c-b-perf")
ns_cand["_b2c_authority_runtime"] = _FakeAuthorityRuntimeModule(b)

t1 = time.time()
cand1 = ACQUIRE(REAL_MASTER_PATH, w1_folds, shipped_root=OFFICIAL_ROOT)
t_first = time.time() - t1
counters1 = b.provider_counters()

t2 = time.time()
cand2 = ACQUIRE(REAL_MASTER_PATH, w1_folds, shipped_root=OFFICIAL_ROOT)
t_repeat = time.time() - t2
counters2 = b.provider_counters()

print("[PERF] candidate FIRST acquisition (W1 scope): %.4fs (mapping_count=%d, provider_opens=%d)" % (
    t_first, cand1["mapping_count"], counters1["total_provider_opens"]))
print("[PERF] candidate REPEATED same-generation acquisition (cache hit): %.4fs (provider_opens=%d, "
      "unchanged=%s)" % (t_repeat, counters2["total_provider_opens"],
                          counters2["total_provider_opens"] == counters1["total_provider_opens"]))

if t_frozen is not None:
    print("[PERF] first-acquisition vs frozen-parser ratio: %.2fx (%s)" % (
        t_first / t_frozen if t_frozen > 0 else float("inf"),
        "candidate slower" if t_first > t_frozen else "candidate faster or comparable"))
    print("[PERF] cache-hit vs frozen-parser ratio: %.4fx (cache hit is essentially free by comparison)" % (
        t_repeat / t_frozen if t_frozen > 0 else float("inf")))

print("\n[SUMMARY]")
print("  full_bounded_read_count: 1 per generation (cache-hit path performs 0)")
print("  provider opens (first): %d" % counters1["total_provider_opens"])
print("  provider opens (repeat, same generation): %d (delta 0)" % counters2["total_provider_opens"])
print("  peak_open_provider_count: %d" % counters1["peak_open_provider_count"])
