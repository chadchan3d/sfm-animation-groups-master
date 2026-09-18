# -*- coding: utf-8 -*-
"""Independent-audit targeted correction -- Test E: semantic regression.

Re-runs (against candidate_b2c_correction5, not "unrelated historical
campaigns") the exact preserved evidence Section 1 asks to retain: full-
corpus parser/adapter semantic equivalence (canonical combined hash
unchanged), W1/W2 scope equivalence, groupFile-wrapper regression, and
provider-closed-at-would-be-mutation-boundary. W3 remains explicitly
UNKNOWN. Under real Python 2.7.5 this is the full ref-vs-candidate hash
comparison; under Python 3 it is candidate-only structural/compatibility
evidence (parse_targeted_master's own tokenizer cannot run under Python 3
-- unchanged, pre-existing constraint, not something this correction
round touches).

Astra Narrow Issue E: candidate/tools roots derived from `__file__`; the
real canonical Master, real production Normalizer, real official
artifact, and historical W1/W2 capture paths remain explicit test
inputs, exactly as Issue E itself distinguishes ("installed SFM paths...
keep them as explicit test/runtime inputs").
"""
import hashlib
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION3_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction5")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
FIXROOT_AB = os.path.join(CORRECTION3_ROOT, "fixtures_ab")

for p in (CORRECTION3_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Explicit test/runtime inputs (installed SFM paths / real canonical
# artifacts) -- Issue E does not ask these to be parameterized away.
NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
NORMALIZER_PINNED_SHA256 = "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"
PUBLIC_DOCS = r"C:\Users\Public\Documents"
EXPECTED_CANONICAL_HASH = "3c806e2d3f7a07267961dd970d35595feaf54e6a6a7ee3fd7179337615d010e2"

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(NORMALIZER_PROD_PATH, "rb") as f:
    normalizer_prod_bytes = f.read()
check("identity.1 production Normalizer matches pinned SHA-256",
      hashlib.sha256(normalizer_prod_bytes).hexdigest() == NORMALIZER_PINNED_SHA256)
with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
real_master_sha = hashlib.sha256(real_master_bytes).hexdigest()
check("identity.2 real canonical Master matches pinned SHA-256", real_master_sha == REAL_MASTER_PINNED_SHA256)

try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False

lines = normalizer_prod_bytes.splitlines() if _PY2 else normalizer_prod_bytes.decode("utf-8").splitlines()


def extract(a, b):
    return "\n".join(lines[a - 1: b]) + "\n"


PROD_RANGES = [
    (138, 138), (604, 605), (647, 657), (659, 671),
    (1169, 1202), (1204, 1339), (1340, 1370), (1373, 1413), (1416, 1723),
]
prod_src = "\n\n".join(extract(a, b) for a, b in PROD_RANGES)
import re as _re_module  # noqa: E402
ns_ref = {"re": _re_module}
if not _PY2:
    ns_ref["unicode"] = str
exec(prod_src, ns_ref)
check("extract.1 parse_targeted_master extracted from PRODUCTION and exec'd", "parse_targeted_master" in ns_ref)

from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
sidecar_contract.ensure_loaded()


class _AllFolds(object):
    def __contains__(self, x):
        return True


def canon(m):
    return {
        "mapping_count": m["mapping_count"], "destination_count": m["destination_count"],
        "folded": m["folded"], "exact_literals": sorted(m["exact_literals"]),
        "group_sibling_order": m["group_sibling_order"], "group_metadata": m["group_metadata"],
    }


def canon_json(o):
    return json.dumps(o, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


try:
    _text_type = unicode  # noqa: F821
except NameError:
    _text_type = str


def sha_of(obj):
    s = canon_json(obj)
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, _text_type) else s).hexdigest()


# ===========================================================================
# Full-corpus canonical combined hash -- must remain UNCHANGED.
# ===========================================================================
print("\n=== Full-corpus canonical hash ===")
ref_full = ns_ref["parse_targeted_master"](REAL_MASTER_PATH, _AllFolds(), validate_conflicts=False) if _PY2 else None

provider_full = sidecar_contract._provider_module.BoundedProvider.open_path(
    OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
try:
    # Always the REAL extracted ascii_fold (ASCII-only A-Z->a-z fold),
    # regardless of interpreter -- pure string logic with no py2-only
    # syntax, so there is no reason to substitute Python's Unicode-aware
    # str.lower() here (which is NOT equivalent and would corrupt the
    # exact-hash comparison for any non-ASCII literal).
    all_real_folds = set(ns_ref["ascii_fold"](occ["literal"]) for occ in provider_full.iter_occurrences())
    builder_full = adapter.build_targeted_master_compatible_projection(all_real_folds)
    cand_full, _cov, _est = builder_full(provider_full)
finally:
    provider_full.close()

cand_full_hash = sha_of(canon(cand_full))
print("[FULL HASH] adapter (correction5) : %s" % cand_full_hash)
print("[EXPECTED]  canonical             : %s" % EXPECTED_CANONICAL_HASH)
if _PY2:
    ref_full_hash = sha_of(canon(ref_full))
    print("[FULL HASH] parse_targeted_master : %s" % ref_full_hash)
    check("fullcorpus.0 ref == adapter (correction5) exactly", ref_full_hash == cand_full_hash)
    check("fullcorpus.1 ref hash equals the canonical recorded hash", ref_full_hash == EXPECTED_CANONICAL_HASH)
check("fullcorpus.2 adapter (correction5) hash equals the canonical recorded hash",
      cand_full_hash == EXPECTED_CANONICAL_HASH, cand_full_hash)

# ===========================================================================
# W1/W2 real command-scope equivalence.
# ===========================================================================
print("\n=== W1/W2 scope equivalence ===")
with open(os.path.join(PUBLIC_DOCS, "SFM_R2_W1_FoxRealWorkload.json")) as f:
    w1 = json.load(f)
w1_folds = set(w1["workload"]["unique_folded_vocabulary"])
with open(os.path.join(PUBLIC_DOCS, "SFM_R2_W2_SixTargetRealWorkload.json")) as f:
    w2 = json.load(f)
w2_folds = set(w2["workload"]["union_folded_vocabulary"])

for label, folds in (("W1", w1_folds), ("W2", w2_folds)):
    provider = sidecar_contract._provider_module.BoundedProvider.open_path(
        OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
    try:
        builder = adapter.build_targeted_master_compatible_projection(folds)
        cand, _c, _e = builder(provider)
    finally:
        provider.close()
    cand_hash = sha_of(canon(cand))
    if _PY2:
        ref = ns_ref["parse_targeted_master"](REAL_MASTER_PATH, folds, validate_conflicts=False)
        ref_hash = sha_of(canon(ref))
        check("%s.0 ref == adapter (correction5) exactly" % label, ref_hash == cand_hash)
    print("[%s] mapping_count=%d destination_count=%d folds=%d" % (
        label, cand["mapping_count"], cand["destination_count"], len(folds)))
    check("%s.1 candidate output structurally well-formed" % label,
          cand["mapping_count"] > 0 and cand["destination_count"] > 0)

# ===========================================================================
# groupFile-wrapper regression (reusing this round's own generation_a
# fixture -- already groupFile-wrapped by build_test_ab_fixtures_
# correction5.py; preserves the same invariant correction2's dedicated
# deep_hierarchy fixture already established, not re-derived here).
# ===========================================================================
print("\n=== groupFile wrapper regression ===")
with open(os.path.join(FIXROOT_AB, "manifest.json")) as f:
    ab_manifest = json.load(f)
ga = ab_manifest["generation_a"]
with open(os.path.join(FIXROOT_AB, ga["master_relative_path"]), "rb") as f:
    ga_master_bytes = f.read()
ga_sha = hashlib.sha256(ga_master_bytes).hexdigest()
gp = sidecar_contract._provider_module.BoundedProvider.open_path(
    os.path.join(FIXROOT_AB, ga["artifact_relative_path"]), ga_sha)
try:
    groups = list(gp.iter_groups())
    root_level = [g for g in groups if g["parent_path"] is None]
    check("wrapper.0 exactly one root-level group", len(root_level) == 1, root_level)
    check("wrapper.1 that root-level group is literally named 'groupFile'",
          len(root_level) == 1 and root_level[0]["name"] == u"groupFile", root_level)
    all_folds_ga = set(occ["literal"].lower() for occ in gp.iter_occurrences())
    builder_ga = adapter.build_targeted_master_compatible_projection(all_folds_ga)
    cand_ga, _c2, _e2 = builder_ga(gp)
finally:
    gp.close()
check("wrapper.2 adapter output has no phantom 'groupFile' group", u"groupFile" not in cand_ga["group_metadata"])

# ===========================================================================
# Provider-closed-at-would-be-mutation-boundary: candidate3's acquisition
# function still references no native/DME mutation symbol, and every
# provider opened above was closed before this point (finally blocks).
# ===========================================================================
_mutation_markers = ("CDmeAnimationSet", "AddChannel", "dm.CreateElement", "vs.mutate")
with open(os.path.join(
        _THIS_DIR, "candidate_b2c_correction5_normalizer",
        "Rebuild_Control_Groups_Normalizer_B2CB_correction5_candidate.py"), "rb") as f:
    _cand_bytes = f.read()
_cand_text = _cand_bytes.decode("utf-8") if not _PY2 else _cand_bytes
check("mutation.0 the candidate Normalizer file references no native/DME mutation symbol",
      not any(m in _cand_text for m in _mutation_markers))

print("\n[NOTE] W3 (72-shot) remains explicitly UNKNOWN -- not re-derived, not force-substituted, "
      "consistent with every prior gate in this project.")

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
