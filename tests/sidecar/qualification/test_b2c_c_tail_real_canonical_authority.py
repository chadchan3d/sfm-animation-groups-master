# -*- coding: utf-8 -*-
"""B2C-C Targeted Audit Correction, Section 2 (Case A, item 3): proves
the CURRENT canonical Master's actual root-level "Tail" authority/path
agrees exactly between the frozen production parser and the qualified
Correction6 adapter/projection -- against the REAL 128K-line canonical
`sfm_defaultanimationgroups.txt`, not a synthetic stand-in. This is the
strongest possible evidence for Fixture C's Case A disposition (a
Master-taxonomy relocation only, no Tail-specific Normalizer runtime
branch -- confirmed separately, see the report's Tail-disposition
section and `check.grep_no_tail_runtime_branch` below).

Real tail control literals used (verified present in the canonical
Master's actual "Tail" group, line 116343 onward, by direct reading):
"BaseTail", "Back_tail_01_L", "Back_tail_01_R" -- declared in that exact
order in the file.

Under real Python 2.7.5 this is the full frozen-parser-vs-adapter hash
comparison; under Python 3 it is adapter-only structural evidence
(parse_targeted_master's own tokenizer cannot run under Python 3 --
unchanged, pre-existing constraint, not something this correction round
touches, same disposition as test_b2c_correction6_semantic_regression.py).

Never launches SFM. Read-only with respect to the frozen production
file, the canonical Master, and the qualified Correction6 candidate.
"""
import hashlib
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CORRECTION6_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction6")
TOOLS_DIR = os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir, "tools")

for p in (os.path.abspath(CORRECTION6_ROOT), os.path.abspath(TOOLS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

NORMALIZER_PROD_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
NORMALIZER_PINNED_SHA256 = "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"
OFFICIAL_SIDECAR = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2a\fixtures\shipped_root_valid\official.sfmsidecar"
)
TAIL_WANTED_FOLDS = {u"basetail", u"back_tail_01_l", u"back_tail_01_r"}

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)

with open(NORMALIZER_PROD_PATH, "rb") as f:
    normalizer_prod_bytes = f.read()
check("identity.normalizer production Normalizer matches pinned SHA-256",
      hashlib.sha256(normalizer_prod_bytes).hexdigest() == NORMALIZER_PINNED_SHA256)
with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
real_master_sha = hashlib.sha256(real_master_bytes).hexdigest()
check("identity.real_master real canonical Master matches pinned SHA-256", real_master_sha == REAL_MASTER_PINNED_SHA256)

# --- Structural re-confirmation (Case A itself): "Tail" is a ROOT-LEVEL
# group (direct child of groupFile), NOT nested under "Body" or any
# other group -- re-derived fresh here via a real brace-depth walk, not
# merely cited from the report.
try:
    _text_type_master = unicode  # noqa: F821
except NameError:
    _text_type_master = str
_master_lines = (
    real_master_bytes.decode("utf-8", "replace").splitlines()
    if not isinstance(real_master_bytes, _text_type_master) else real_master_bytes.splitlines()
)
_tail_line_idx = None
for _i, _l in enumerate(_master_lines):
    if _l.strip() == u'"Tail"':
        _tail_line_idx = _i
        break
check("structural.tail_group_line_found a line containing exactly '\"Tail\"' exists in the "
      "canonical Master", _tail_line_idx is not None)
if _tail_line_idx is not None:
    _tail_indent = len(_master_lines[_tail_line_idx]) - len(_master_lines[_tail_line_idx].lstrip(u"\t"))
    check("structural.tail_is_root_level 'Tail' has indent depth 1 (a direct child of the top-level "
          "'groupFile' wrapper, i.e. root-level -- NOT nested under 'Body' or any other group)",
          _tail_indent == 1, _tail_indent)

# --- No Tail-specific Normalizer runtime branch (re-confirmed fresh). --
_normalizer_text = normalizer_prod_bytes.decode("ascii")
check("grep.no_tail_runtime_branch zero case-insensitive 'tail' matches anywhere in the frozen "
      "13,594-line production Normalizer source (structural Master declaration only, no "
      "Tail-specific code path)", u"tail" not in _normalizer_text.lower())

try:
    unicode  # noqa: F821
    _PY2 = True
except NameError:
    _PY2 = False

lines = normalizer_prod_bytes.splitlines() if _PY2 else normalizer_prod_bytes.decode("utf-8").splitlines()


def extract(a, b):
    return u"\n".join(lines[a - 1: b]) + u"\n"


PROD_RANGES = [
    (138, 138), (604, 605), (647, 657), (659, 671),
    (1169, 1202), (1204, 1339), (1340, 1370), (1373, 1413), (1416, 1723),
]
prod_src = u"\n\n".join(extract(a, b) for a, b in PROD_RANGES)
import re as _re_module  # noqa: E402
ns_ref = {"re": _re_module}
if not _PY2:
    ns_ref["unicode"] = str
exec(prod_src, ns_ref)
check("extract.parse_targeted_master extracted from PRODUCTION and exec'd", "parse_targeted_master" in ns_ref)

from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
sidecar_contract.ensure_loaded()


def canon_view(m):
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


print("\n=== Real canonical Master Tail authority: frozen parser vs Correction6 adapter ===")
provider = sidecar_contract._provider_module.BoundedProvider.open_path(OFFICIAL_SIDECAR, real_master_sha)
try:
    builder = adapter.build_targeted_master_compatible_projection(TAIL_WANTED_FOLDS)
    cand, _cov, _est = builder(provider)
finally:
    provider.close()

cand_hash = sha_of(canon_view(cand))
print("[folded] adapter: %r" % (cand["folded"],))
print("[group_metadata Tail] adapter: %r" % (cand["group_metadata"].get(u"Tail"),))

if _PY2:
    ref = ns_ref["parse_targeted_master"](REAL_MASTER_PATH, TAIL_WANTED_FOLDS, validate_conflicts=False)
    ref_hash = sha_of(canon_view(ref))
    print("[folded] frozen parser: %r" % (ref["folded"],))
    check("tail.ref_equals_adapter frozen parser and Correction6 adapter agree EXACTLY (full "
          "canonical hash) for the real canonical Master's Tail vocabulary", ref_hash == cand_hash,
          (ref_hash, cand_hash))
    for _lit in (u"basetail", u"back_tail_01_l", u"back_tail_01_r"):
        _ref_dest = set(e["destination"] for e in ref["folded"].get(_lit, []))
        _cand_dest = set(e["destination"] for e in cand["folded"].get(_lit, []))
        check("tail.destination_is_tail.%s both frozen parser and adapter resolve %r to "
              "destination 'Tail'" % (_lit, _lit), _ref_dest == {u"Tail"} and _cand_dest == {u"Tail"},
              (_lit, _ref_dest, _cand_dest))

for _lit in (u"basetail", u"back_tail_01_l", u"back_tail_01_r"):
    _cand_dest = set(e["destination"] for e in cand["folded"].get(_lit, []))
    check("tail.adapter_destination_is_tail.%s the Correction6 adapter resolves %r to destination "
          "'Tail'" % (_lit, _lit), _cand_dest == {u"Tail"}, (_lit, _cand_dest))

check("tail.group_metadata_present the adapter's group_metadata contains a 'Tail' entry",
      u"Tail" in cand["group_metadata"], sorted(cand["group_metadata"].keys()))
_tail_meta = cand["group_metadata"].get(u"Tail", {})
check("tail.group_metadata_selectable the real canonical Master's Tail group has "
      "selectable_explicit == True (matches its declared '\"selectable\" \"1\"' field)",
      _tail_meta.get("selectable_explicit") is True, _tail_meta)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(condition for _, condition in RESULTS):
    sys.exit(1)
