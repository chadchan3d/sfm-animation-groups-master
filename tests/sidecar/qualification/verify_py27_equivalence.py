# -*- coding: utf-8 -*-
"""R3-B2C-A evidence-gap closure #1: real Python 2.7.5 equivalence proof
between the frozen production parse_targeted_master() and the new
normalizer_compat_adapter.build_targeted_master_compatible_projection(),
run against the REAL canonical Master and REAL official shipped
artifact. Must be executed with:

  E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\sdktools\\python\\2.7\\win32\\python.exe

parse_targeted_master (and its real dependencies: ProbeError, to_unicode,
ascii_fold, BufferedChars, stream_tokens, parse_master_bool_text,
parse_master_rgba_text, READ_BLOCK) are extracted VERBATIM by exact line
range from the real, hash-verified production file and exec()'d in an
isolated namespace -- never retyped/reimplemented, and the surrounding
13,594-line file (with its real-SFM-only module-scope side effects,
ifm.dll discovery etc.) is never imported. Read-only against the real
Master and real official artifact throughout; writes nothing.
"""
import hashlib
import json
import sys

NORMALIZER_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Rebuild_Control_Groups_Normalizer.py"
)
NORMALIZER_PINNED_SHA256 = "6656aa9022d458c22c2549da5dfdc14539a572d91200c3f0f459c1453dfd092e"

REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_MASTER_PINNED_SHA256 = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"

CANDIDATE_TEST_ROOT = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\67454949-e69f-4280-93d9-87c1f4464330\scratchpad\candidate_b2c_test_root"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
FIXROOT_B2A = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2a\fixtures"
OFFICIAL_ROOT = FIXROOT_B2A + r"\shipped_root_valid"

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


print("Interpreter: %s" % sys.version)
check("interpreter.1 running under Python 2.7", sys.version_info[0] == 2 and sys.version_info[1] == 7)

# ---------------------------------------------------------------------
# Identity: re-hash the real production Normalizer + real canonical
# Master, independently, under THIS interpreter, before extracting
# anything from either.
# ---------------------------------------------------------------------
with open(NORMALIZER_PATH, "rb") as f:
    normalizer_bytes = f.read()
normalizer_sha = hashlib.sha256(normalizer_bytes).hexdigest()
check("identity.1 production Normalizer matches pinned SHA-256 (re-hashed under real Python 2.7.5)",
      normalizer_sha == NORMALIZER_PINNED_SHA256, normalizer_sha)

with open(REAL_MASTER_PATH, "rb") as f:
    master_bytes = f.read()
master_sha = hashlib.sha256(master_bytes).hexdigest()
check("identity.2 real canonical Master matches pinned SHA-256 (re-hashed under real Python 2.7.5)",
      master_sha == REAL_MASTER_PINNED_SHA256, master_sha)

# ---------------------------------------------------------------------
# Extract the EXACT (verbatim, byte-identical) line ranges for
# parse_targeted_master and its real dependencies. Line numbers were
# located via grep against the SAME pinned-SHA file (see B2C-A report).
# ---------------------------------------------------------------------
lines = normalizer_bytes.splitlines()  # tolerant of \r\n vs \n, never leaves a stray \r on a line


def extract(first_line, last_line, label):
    # first_line/last_line are 1-based, inclusive (as reported by the
    # Read tool / grep -n).
    chunk = "\n".join(lines[first_line - 1: last_line]) + "\n"
    print("[EXTRACT] %s: lines %d-%d (%d bytes)" % (label, first_line, last_line, len(chunk)))
    return chunk

RANGES = [
    (138, 138, "READ_BLOCK"),
    (604, 605, "ProbeError"),
    (647, 657, "to_unicode"),
    (659, 671, "ascii_fold"),
    (1169, 1202, "BufferedChars"),
    (1204, 1339, "stream_tokens"),
    (1340, 1370, "parse_master_bool_text"),
    (1373, 1413, "parse_master_rgba_text"),
    (1416, 1723, "parse_targeted_master"),
]

extracted_src = "\n\n".join(extract(a, b, label) for a, b, label in RANGES)

extracted_src_sha = hashlib.sha256(extracted_src.encode("utf-8") if isinstance(extracted_src, unicode) else extracted_src).hexdigest()
print("[EXTRACT] combined extracted source SHA-256: %s" % extracted_src_sha)

# Sanity: each extracted range must start with the expected def/class/
# constant token and must not accidentally include the NEXT construct's
# header (would indicate a wrong line boundary).
expected_head = {
    "READ_BLOCK": "READ_BLOCK",
    "ProbeError": "class ProbeError",
    "to_unicode": "def to_unicode",
    "ascii_fold": "def ascii_fold",
    "BufferedChars": "class BufferedChars",
    "stream_tokens": "def stream_tokens",
    "parse_master_bool_text": "def parse_master_bool_text",
    "parse_master_rgba_text": "def parse_master_rgba_text",
    "parse_targeted_master": "def parse_targeted_master",
}
bad_heads = []
for a, b, label in RANGES:
    chunk = extract(a, b, label)
    if not chunk.lstrip().startswith(expected_head[label]):
        bad_heads.append(label)
check("extract.1 every extracted range starts with its expected def/class/constant token",
      len(bad_heads) == 0, bad_heads)

import re as _re_module

ns = {"re": _re_module}  # the original file imports `re` once at module
                          # scope (used inside parse_master_rgba_text);
                          # extracting only these function BODIES means
                          # that module-level import must be supplied
                          # here explicitly -- the function logic itself
                          # is untouched.
exec(extracted_src, ns)
check("extract.2 parse_targeted_master extracted and exec'd without error", "parse_targeted_master" in ns)


class _AllFolds(object):
    def __contains__(self, x):
        return True


master_ref = ns["parse_targeted_master"](REAL_MASTER_PATH, _AllFolds(), validate_conflicts=False)
check("ref.1 parse_targeted_master ran against the real Master", isinstance(master_ref, dict))
print("[REF] mapping_count=%d destination_count=%d groups=%d folds=%d" % (
    master_ref["mapping_count"], master_ref["destination_count"],
    len(master_ref["group_metadata"]), len(master_ref["folded"]),
))

# ---------------------------------------------------------------------
# Adapter side: build the SAME full wanted_folds set (every fold that
# exists in the real official artifact), using the SAME extracted
# ascii_fold() so both sides use byte-identical fold logic, then run
# normalizer_compat_adapter through a real Broker.acquire_cohort().
# ---------------------------------------------------------------------
for p in (CANDIDATE_TEST_ROOT, GATE_R2_DIR, TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from sfm_master_authority import sidecar_contract  # noqa: E402
from sfm_master_authority import broker as broker_mod  # noqa: E402
from sfm_master_authority import normalizer_compat_adapter as adapter  # noqa: E402

sidecar_contract.ensure_loaded()
official_artifact_path = OFFICIAL_ROOT + r"\official.sfmsidecar"
provider = sidecar_contract._provider_module.BoundedProvider.open_path(official_artifact_path, master_sha)
try:
    all_folds = set(ns["ascii_fold"](occ["literal"]) for occ in provider.iter_occurrences())
    check("adapter.0 discovered a plausible number of distinct folds from the real artifact",
          len(all_folds) > 0 and len(all_folds) <= master_ref["mapping_count"], len(all_folds))

    # This full-fold-universe request (124,728 folds at once) is NOT a
    # realistic production access pattern -- production always uses a
    # small per-command wanted_folds scope (a few dozen literals). It
    # deliberately exceeds the 16 MiB retained-promotion gate, so the
    # builder is called DIRECTLY against the already-open provider here
    # (bypassing Broker.acquire_cohort's view-cache admission step) to
    # isolate exactly what this evidence gap is about: the BUILDER
    # FUNCTION's output correctness, not the admission-gate policy
    # (already independently proven correct by the B2B-equivalent
    # eviction.*/memory.* suite).
    builder = adapter.build_targeted_master_compatible_projection(all_folds)
    master_adapter, _coverage, _estimated_bytes = builder(provider)
finally:
    provider.close()

check("adapter.1 builder ran directly against the real Master + real official artifact", isinstance(master_adapter, dict))
print("[ADAPTER] mapping_count=%d destination_count=%d groups=%d folds=%d" % (
    master_adapter["mapping_count"], master_adapter["destination_count"],
    len(master_adapter["group_metadata"]), len(master_adapter["folded"]),
))

# ---------------------------------------------------------------------
# Canonicalization + hashing. Preserves LIST ORDER exactly as produced
# by each side (so occurrence ordering and group_sibling_order ordering
# are part of the hash, not normalized away); only the inherently
# unordered `exact_literals` SET is sorted before serialization, since
# neither implementation claims any order for it.
# ---------------------------------------------------------------------
def canon(master):
    return {
        "mapping_count": master["mapping_count"],
        "destination_count": master["destination_count"],
        "folded": master["folded"],
        "exact_literals": sorted(master["exact_literals"]),
        "group_sibling_order": master["group_sibling_order"],
        "group_metadata": master["group_metadata"],
    }


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha_of(obj):
    s = canon_json(obj)
    return hashlib.sha256(s.encode("utf-8") if isinstance(s, unicode) else s).hexdigest()


ref_canon = canon(master_ref)
adapter_canon = canon(master_adapter)

COMPONENTS = ["mapping_count", "destination_count", "folded", "exact_literals",
              "group_sibling_order", "group_metadata"]

print("\n=== Component hashes ===")
component_mismatches = []
for comp in COMPONENTS:
    h_ref = sha_of(ref_canon[comp])
    h_adapter = sha_of(adapter_canon[comp])
    match = h_ref == h_adapter
    if not match:
        component_mismatches.append(comp)
    print("[%s] %-20s ref=%s adapter=%s" % ("PASS" if match else "FAIL", comp, h_ref, h_adapter))
    RESULTS.append(("component.%s exact hash match" % comp, match))

full_h_ref = sha_of(ref_canon)
full_h_adapter = sha_of(adapter_canon)
check("full.1 COMBINED canonical structure hash matches exactly (mapping_count, destination_count, "
      "folded, exact_literals, group_sibling_order, group_metadata -- including list order)",
      full_h_ref == full_h_adapter, (full_h_ref, full_h_adapter))

print("\n[FULL HASH] parse_targeted_master : %s" % full_h_ref)
print("[FULL HASH] adapter                : %s" % full_h_adapter)

# ---------------------------------------------------------------------
# If anything mismatched, drill down to the first differing key/index
# for diagnosis.
# ---------------------------------------------------------------------
if component_mismatches:
    print("\n=== MISMATCH DIAGNOSIS ===")
    for comp in component_mismatches:
        rv = ref_canon[comp]
        av = adapter_canon[comp]
        if isinstance(rv, dict):
            rkeys = set(rv.keys())
            akeys = set(av.keys())
            if rkeys != akeys:
                print("%s: KEY SET DIFFERS. ref-only=%r adapter-only=%r" % (
                    comp, sorted(rkeys - akeys)[:10], sorted(akeys - rkeys)[:10]))
            for k in sorted(rkeys & akeys):
                if rv[k] != av[k]:
                    print("%s[%r]: ref=%r" % (comp, k, rv[k]))
                    print("%s[%r]: adapter=%r" % (comp, k, av[k]))
                    break
        else:
            print("%s: ref=%r" % (comp, rv))
            print("%s: adapter=%r" % (comp, av))

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
