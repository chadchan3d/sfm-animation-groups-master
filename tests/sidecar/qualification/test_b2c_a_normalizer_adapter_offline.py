# -*- coding: utf-8 -*-
"""R3-B2C-A: offline structural qualification of normalizer_compat_
adapter.build_targeted_master_compatible_projection, run through a real
Broker.acquire_cohort() against the REAL canonical Master and the REAL
official shipped artifact (read-only). Checks internal structural
self-consistency of the adapter's parse_targeted_master()-compatible
output (hierarchy completeness, no duplicate/orphan groups, GLOBAL count
sanity, requested-literal coverage) -- NOT a byte-for-byte diff against
parse_targeted_master() itself (that requires real Python 2.7 or real
SFM; see normalizer_compat_adapter.py's module docstring). Never
launches SFM, never modifies the real Master or any production file.
"""
import os
import sys

CANDIDATE_TEST_ROOT = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\67454949-e69f-4280-93d9-87c1f4464330\scratchpad\candidate_b2c_test_root"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"

for p in (CANDIDATE_TEST_ROOT, GATE_R2_DIR, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as adapter  # noqa: E402

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = os.path.join(FIXROOT_B2A, "shipped_root_valid")
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

REAL_LITERALS = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
NONEXISTENT_LITERAL = "ThisControlDoesNotExistAnywhereInTheMaster_XYZ123"


def ascii_fold(s):
    out = []
    for ch in s:
        o = ord(ch)
        out.append(chr(o + 32) if 65 <= o <= 90 else ch)
    return u"".join(out)


import hashlib
with open(REAL_MASTER_PATH, "rb") as f:
    real_master_bytes = f.read()
check("baseline.1 real canonical Master matches pinned SHA",
      hashlib.sha256(real_master_bytes).hexdigest() == REAL_MASTER_SHA)

wanted_folds = set(ascii_fold(lit) for lit in REAL_LITERALS)

b = broker_mod.Broker(api_version="test-b2c-adapter")
builder = adapter.build_targeted_master_compatible_projection(wanted_folds)
detached = b.acquire_cohort(REAL_MASTER_PATH, {"normalizer_compat": builder}, shipped_root=OFFICIAL_ROOT)
check("acquire.1 acquisition succeeded", "normalizer_compat" in detached)
master = detached["normalizer_compat"].payload

# ---------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------
required_keys = {"mapping_count", "destination_count", "folded", "exact_literals",
                  "group_sibling_order", "group_metadata"}
check("shape.1 payload has exactly the parse_targeted_master-compatible key set",
      set(master.keys()) == required_keys, set(master.keys()))
check("shape.2 mapping_count is a positive int", isinstance(master["mapping_count"], int) and master["mapping_count"] > 0,
      master["mapping_count"])
check("shape.3 destination_count is a positive int", isinstance(master["destination_count"], int) and master["destination_count"] > 0,
      master["destination_count"])

# ---------------------------------------------------------------------
# Hierarchy self-consistency (group_sibling_order vs group_metadata)
# ---------------------------------------------------------------------
gso = master["group_sibling_order"]
gmeta = master["group_metadata"]

check("hier.1 <ROOT> sentinel key exists in group_sibling_order", u"<ROOT>" in gso)

meta_paths = set(gmeta.keys())
# every non-<ROOT> key in group_sibling_order must be a real group (have metadata)
non_root_sibling_keys = set(gso.keys()) - {u"<ROOT>"}
check("hier.2 every group_sibling_order key (except <ROOT>) is a real group with metadata",
      non_root_sibling_keys == meta_paths,
      (non_root_sibling_keys - meta_paths, meta_paths - non_root_sibling_keys))

check("hier.2b destination_count does not exceed the total real group count",
      master["destination_count"] <= len(meta_paths), (master["destination_count"], len(meta_paths)))

# every group appears in exactly one parent's sibling list, exactly once
reconstructed_children = {}
for parent, children in gso.items():
    for name in children:
        full = name if parent == u"<ROOT>" else parent + u"/" + name
        reconstructed_children.setdefault(full, []).append(parent)

check("hier.3 every real group is listed as a child exactly once (no orphans, no duplicates)",
      set(reconstructed_children.keys()) == meta_paths
      and all(len(v) == 1 for v in reconstructed_children.values()),
      {k: v for k, v in reconstructed_children.items() if len(v) != 1} or
      (set(reconstructed_children.keys()) ^ meta_paths))

# metadata field shape
bad_meta_shape = []
for full_path, meta in gmeta.items():
    expected = {"path", "groupColor_raw", "selectable_raw", "visible_raw", "snappable_raw",
                "group_color_explicit", "selectable_explicit", "selectable_authority"}
    if set(meta.keys()) != expected:
        bad_meta_shape.append(full_path)
        continue
    if meta["path"] != full_path:
        bad_meta_shape.append(full_path)
        continue
    if meta["selectable_authority"] not in ("CANONICAL_NATIVE_POST_DEFAULT", "EXPLICIT_MASTER_FIELD"):
        bad_meta_shape.append(full_path)
check("hier.4 every group_metadata entry has the exact expected field set and self-consistent 'path'",
      len(bad_meta_shape) == 0, bad_meta_shape[:10])

# selectable_authority consistency with selectable_explicit presence
bad_authority = [
    full_path for full_path, meta in gmeta.items()
    if (meta["selectable_authority"] == "EXPLICIT_MASTER_FIELD") != (meta["selectable_explicit"] is not None)
]
check("hier.5 selectable_authority == EXPLICIT_MASTER_FIELD iff selectable_explicit is not None",
      len(bad_authority) == 0, bad_authority[:10])

# any real groupColor found -> must be a well-formed 4-int RGBA list, each 0-255
bad_color = [
    (full_path, meta["group_color_explicit"]) for full_path, meta in gmeta.items()
    if meta["group_color_explicit"] is not None and (
        not isinstance(meta["group_color_explicit"], list)
        or len(meta["group_color_explicit"]) != 4
        or any((c < 0 or c > 255) for c in meta["group_color_explicit"])
    )
]
check("hier.6 every parsed group_color_explicit is a well-formed 4-component 0-255 RGBA list",
      len(bad_color) == 0, bad_color[:5])
groups_with_color = [fp for fp, m in gmeta.items() if m["group_color_explicit"] is not None]
check("hier.6b at least one real group actually has an explicit groupColor (parser exercised on real data)",
      len(groups_with_color) > 0, len(groups_with_color))

groups_with_explicit_selectable = [fp for fp, m in gmeta.items() if m["selectable_explicit"] is not None]
print("[INFO] groups with explicit selectable: %d" % len(groups_with_explicit_selectable))

# ---------------------------------------------------------------------
# Requested-literal coverage
# ---------------------------------------------------------------------
folded_out = master["folded"]
exact_literals = master["exact_literals"]

missing = []
for lit in REAL_LITERALS:
    folded = ascii_fold(lit)
    if folded not in folded_out:
        missing.append(lit)
        continue
    rows = folded_out[folded]
    if not any(r["literal"] == lit for r in rows):
        missing.append(lit)
check("coverage.1 every real requested literal resolved to a non-empty occurrence row",
      len(missing) == 0, missing)

check("coverage.2 every real requested literal appears in exact_literals",
      all(lit in exact_literals for lit in REAL_LITERALS),
      [lit for lit in REAL_LITERALS if lit not in exact_literals])

check("coverage.3 the nonexistent literal's fold has NO entry in 'folded' (matches parse_targeted_master's "
      "own 'no entry for MasterUnknown' contract, never an empty-list placeholder)",
      ascii_fold(NONEXISTENT_LITERAL) not in folded_out, ascii_fold(NONEXISTENT_LITERAL) in folded_out)

# occurrence row field shape + index sanity
bad_rows = []
for folded, rows in folded_out.items():
    for r in rows:
        if set(r.keys()) != {"literal", "destination", "global_index", "local_index"}:
            bad_rows.append((folded, r))
            continue
        if not (isinstance(r["global_index"], int) and r["global_index"] >= 0):
            bad_rows.append((folded, r))
        if not (isinstance(r["local_index"], int) and r["local_index"] >= 0):
            bad_rows.append((folded, r))
check("coverage.4 every occurrence row has the exact expected field set with sane non-negative indices",
      len(bad_rows) == 0, bad_rows[:5])

# global_index values must be globally unique across the WHOLE requested set
all_global_indices = [r["global_index"] for rows in folded_out.values() for r in rows]
check("coverage.5 global_index values are globally unique (one occurrence table row per index)",
      len(all_global_indices) == len(set(all_global_indices)), len(all_global_indices) - len(set(all_global_indices)))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
