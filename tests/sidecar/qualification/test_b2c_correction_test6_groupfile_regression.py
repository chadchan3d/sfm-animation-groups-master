# -*- coding: utf-8 -*-
"""R3-B2C-B Section 10: permanent regression test for the groupFile
synthetic-wrapper bug found during B2C-A. Proves normalizer_compat_
adapter.py's wrapper-stripping fix generalizes beyond the real canonical
Master's specific shape (21 top-level siblings under one wrapper) by
also testing a STRUCTURALLY DIFFERENT synthetic fixture (6 top-level
siblings, 3+ levels of nesting, generic non-whitelisted metadata keys)
-- both under Python 2.7.5 (full ref-vs-candidate hash comparison,
parse_targeted_master genuinely runnable) and Python 3.10 (candidate-
only structural checks; parse_targeted_master's own tokenizer cannot run
under Python 3 -- see normalizer_compat_adapter.py's module docstring).
"""
import hashlib
import json
import os
import sys

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
CANDIDATE_AUTHORITY_ROOT = r"E:\SFM Animation Group Master\tests\sidecar\qualification\candidate_b2c_correction"
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"

SYNTHETIC_MASTER = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixtureA_1p0x_master.txt"
)
SYNTHETIC_SIDECAR = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixtureA_1p0x.sfmsidecar"
)

for p in (CANDIDATE_AUTHORITY_ROOT, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)
try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False

with open(NORMALIZER_PROD_PATH, "rb") as f:
    normalizer_bytes = f.read()
check("baseline.1 production Normalizer matches pinned SHA-256",
      hashlib.sha256(normalizer_bytes).hexdigest() == "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e")

with open(SYNTHETIC_MASTER, "rb") as f:
    synthetic_bytes = f.read()
synthetic_sha = hashlib.sha256(synthetic_bytes).hexdigest()
check("baseline.2 synthetic fixture Master hashed", len(synthetic_sha) == 64)
check("baseline.3 synthetic fixture has a real groupFile wrapper at top of file (text-level check)",
      synthetic_bytes.lstrip()[:9] == b"groupFile")

if _PY2:
    lines = normalizer_bytes.splitlines()
else:
    lines = normalizer_bytes.decode("utf-8").splitlines()


def extract(first_line, last_line):
    return "\n".join(lines[first_line - 1: last_line]) + "\n"


PROD_RANGES = [
    (138, 138), (604, 605), (647, 657), (659, 671),
    (1169, 1202), (1204, 1339), (1340, 1370), (1373, 1413), (1416, 1723),
]
prod_src = "\n\n".join(extract(a, b) for a, b in PROD_RANGES)
import re as _re_module
ns_ref = {"re": _re_module}
if not _PY2:
    ns_ref["unicode"] = str
exec(prod_src, ns_ref)


class _AllFolds(object):
    def __contains__(self, x):
        return True


from sfm_master_authority import sidecar_contract  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as adapter  # noqa: E402

sidecar_contract.ensure_loaded()
provider = sidecar_contract._provider_module.BoundedProvider.open_path(SYNTHETIC_SIDECAR, synthetic_sha)
try:
    groups = list(provider.iter_groups())
    root_level = [g for g in groups if g["parent_path"] is None]
    check("wrapper.1 synthetic fixture's provider exposes exactly one root-level group "
          "(the compiler's synthetic groupFile wrapper)", len(root_level) == 1, root_level)
    check("wrapper.2 that root-level group is literally named 'groupFile'",
          len(root_level) == 1 and root_level[0]["name"] == u"groupFile", root_level)

    all_synth_folds = set(
        (ns_ref["ascii_fold"](occ["literal"]) if _PY2 else occ["literal"].lower())
        for occ in provider.iter_occurrences()
    )
    check("wrapper.3 discovered a plausible fold count for the synthetic fixture", len(all_synth_folds) > 0, len(all_synth_folds))

    builder = adapter.build_targeted_master_compatible_projection(all_synth_folds)
    cand, _cov, _est = builder(provider)
finally:
    provider.close()

# The adapter must NEVER surface the wrapper itself as a group.
check("wrapper.4 adapter's group_metadata does NOT contain a phantom 'groupFile' entry",
      u"groupFile" not in cand["group_metadata"])
check("wrapper.5 adapter's group_sibling_order['<ROOT>'] does NOT contain 'groupFile'",
      u"groupFile" not in cand["group_sibling_order"].get(u"<ROOT>", []))
check("wrapper.6 adapter's group_metadata count equals real provider group count minus the wrapper "
      "(no phantom Nth group)", len(cand["group_metadata"]) == len(groups) - 1,
      (len(cand["group_metadata"]), len(groups)))
check("wrapper.7 no group_metadata full_path or group_sibling_order key retains a 'groupFile/' prefix",
      all(not k.startswith(u"groupFile/") and k != u"groupFile" for k in cand["group_metadata"])
      and all(not k.startswith(u"groupFile/") and k != u"groupFile" for k in cand["group_sibling_order"]),
      [k for k in list(cand["group_metadata"].keys()) + list(cand["group_sibling_order"].keys())
       if k.startswith(u"groupFile/") or k == u"groupFile"])
check("wrapper.8 no occurrence destination retains a 'groupFile/' prefix",
      all(not row["destination"].startswith(u"groupFile/") and row["destination"] != u"groupFile"
          for rows in cand["folded"].values() for row in rows))

if _PY2:
    ref = ns_ref["parse_targeted_master"](SYNTHETIC_MASTER, _AllFolds(), validate_conflicts=False)

    def canon(m):
        return {
            "mapping_count": m["mapping_count"], "destination_count": m["destination_count"],
            "folded": m["folded"], "exact_literals": sorted(m["exact_literals"]),
            "group_sibling_order": m["group_sibling_order"], "group_metadata": m["group_metadata"],
        }

    def sha_of(o):
        s = json.dumps(o, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(s.encode("utf-8") if isinstance(s, unicode) else s).hexdigest()  # noqa: F821

    ref_c, cand_c = canon(ref), canon(cand)
    for comp in ("mapping_count", "destination_count", "folded", "exact_literals",
                 "group_sibling_order", "group_metadata"):
        check("wrapper.9.%s exact hash match (synthetic fixture, real Python 2.7.5)" % comp,
              sha_of(ref_c[comp]) == sha_of(cand_c[comp]))
    check("wrapper.9.combined exact hash match (synthetic fixture, real Python 2.7.5)",
          sha_of(ref_c) == sha_of(cand_c))
    print("[SYNTHETIC] mapping_count=%d/%d destination_count=%d/%d groups(ref)=%d groups(cand)=%d" % (
        ref["mapping_count"], cand["mapping_count"], ref["destination_count"], cand["destination_count"],
        len(ref["group_metadata"]), len(cand["group_metadata"])))
else:
    print("[SYNTHETIC] (Python 3, candidate-only) mapping_count=%d destination_count=%d groups=%d "
          "-- ref-vs-candidate hash comparison only runs under real Python 2.7.5, see docstring" % (
              cand["mapping_count"], cand["destination_count"], len(cand["group_metadata"])))

# ---------------------------------------------------------------------
# Real canonical Master re-confirmation (already proven in B2C-A;
# re-run here as part of B2C-B's permanent regression, Python 2.7.5 only
# for the ref-vs-candidate comparison; candidate-only structural check
# under Python 3).
# ---------------------------------------------------------------------
with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
real_master_sha = hashlib.sha256(real_master_bytes).hexdigest()
check("real.1 real canonical Master matches pinned SHA-256", real_master_sha == REAL_MASTER_PINNED_SHA256)

provider2 = sidecar_contract._provider_module.BoundedProvider.open_path(
    OFFICIAL_ROOT + r"\official.sfmsidecar", real_master_sha)
try:
    real_groups = list(provider2.iter_groups())
    real_root_level = [g for g in real_groups if g["parent_path"] is None]
    check("real.2 real Master's provider also exposes exactly one root-level 'groupFile' wrapper",
          len(real_root_level) == 1 and real_root_level[0]["name"] == u"groupFile", real_root_level)
    real_all_folds = set(
        (ns_ref["ascii_fold"](occ["literal"]) if _PY2 else occ["literal"].lower())
        for occ in provider2.iter_occurrences())
    real_builder = adapter.build_targeted_master_compatible_projection(real_all_folds)
    real_cand, _c2, _e2 = real_builder(provider2)
finally:
    provider2.close()
check("real.3 real Master adapter output has no phantom 'groupFile' group",
      u"groupFile" not in real_cand["group_metadata"])
check("real.4 real Master adapter group_metadata count == 42 (21 confirmed in B2C-A + verified here again)",
      len(real_cand["group_metadata"]) == 42, len(real_cand["group_metadata"]))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
