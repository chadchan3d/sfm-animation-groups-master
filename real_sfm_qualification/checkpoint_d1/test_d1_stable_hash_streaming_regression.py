# -*- coding: utf-8 -*-
"""Offline regression for Checkpoint D1-3's corrected `stable_hash()`
(independent-audit correction 2026-09-22, Section 1, defect: the prior
implementation -- `joined = u"\\n".join(sorted(values));
return hashlib.sha256(joined.encode("utf-8")).hexdigest()` -- built ONE
giant joined Unicode string and THEN a second giant encoded byte
string; a real `MemoryError()` was observed inside the `.encode("utf-8")`
step while hashing the 85-target POST fingerprint in Checkpoint D1-2's
own 32-bit qualification-harness process).

Extracts the NEW streaming `stable_hash()` VERBATIM (exact line range,
SHA-256 pinned against the deployed D1-3 script) and compares its
digests against a literal, unmodified reimplementation of the OLD
two-giant-copies algorithm (the "oracle"), across:

  1. an empty list;
  2. a single item;
  3. many (10,000) short Unicode items, including some with non-ASCII
     characters;
  4. representative nested-fingerprint-shaped strings (JSON text of the
     kind `dumps_sorted(capture_snapshot_explicit(...))` actually
     produces -- deeply nested groups/memberships/control lists);
  5. the REAL, already-accepted Checkpoint C1-2 PRE fingerprint data
     (85 real captured targets) fed through the exact call-site
     transformation D1 uses (`[u"%s=%s" % (k, dumps_sorted(v)) for k, v
     in pre_fingerprint.items()]`);
  6. the REAL, already-accepted Checkpoint C1-2 POST fingerprint data
     (85 real captured targets), same transformation;
  7. a large synthetic list (200,000 items) -- exercised ONLY against
     the NEW implementation (the old implementation is not expected to
     safely process an input this large in a 32-bit process; the old
     oracle is compared only "for inputs small enough for the old
     implementation to execute", per the governing correction's own
     scoping).

Every OLD-vs-NEW comparison requires EXACT digest equality (not
"close enough").

Run under real Python 2.7.5. Never launches SFM. Read-only with
respect to the deployed D1-3 script and the existing C1-2 artifact.
"""
import hashlib
import json
import random
import sys

D1_SCRIPT_PATH = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\mainmenu\ChadChan3D\Checkpoint_D1_Historical_All_Shots_Baseline.py"
)
EXPECTED_D1_SCRIPT_SHA256 = (
    "e5df3675e26280ab3ed3a6e54ae1a54d7bd6526c3df22e2bfce59d3b5a2cdf61"
)
C1_JSON_PATH = "C:\\Users\\Public\\Documents\\sfm_checkpoint_c1_baseline_result.json"

# 1-indexed, inclusive. Re-verify with:
#   sed -n '<start>,<end>p' Checkpoint_D1_Historical_All_Shots_Baseline.py
STABLE_HASH_RANGE = (383, 412)

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def old_stable_hash(values):
    """Literal, UNMODIFIED reimplementation of D1-1/D1-2's own prior
    `stable_hash()` -- the exact two-giant-copies algorithm being
    replaced. Kept here only as the digest-equivalence oracle; never
    exec'd from the deployed script (that implementation no longer
    exists there -- this is a faithful, independently-typed copy of
    what it always was, per the unchanged docstring/comment record in
    D1-1/D1-2's own preserved ledger rows)."""
    joined = u"\n".join(sorted(values))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def dumps_sorted(value):
    return json.dumps(value, sort_keys=True)


# Module-level (not inside a function): Python 2's `exec` statement is
# disallowed inside any function that also contains a nested `def`/class
# with free variables -- top-level placement sidesteps it, same as this
# project's other extraction-based harnesses.

with open(D1_SCRIPT_PATH, "rb") as f:
    _data = f.read()
_actual_sha = hashlib.sha256(_data).hexdigest()
check("source.d1_script_sha256_pinned", _actual_sha == EXPECTED_D1_SCRIPT_SHA256, _actual_sha)
if _actual_sha != EXPECTED_D1_SCRIPT_SHA256:
    print("\nRESULT: 1/%d SOME FAILED (SHA mismatch -- refusing to extract from a stale/wrong file)" % (len(RESULTS) + 1))
    sys.exit(1)

_lines = _data.decode("ascii").splitlines()
_start, _end = STABLE_HASH_RANGE
_raw = "\n".join(_lines[_start - 1:_end])
check("source.range_starts_with_expected_def", _raw.strip().startswith("def stable_hash(values):"), _raw.splitlines()[0])

_ns = {"hashlib": hashlib}
exec(compile(_raw, "<stable_hash_extract>", "exec"), _ns)
check("source.extracted_and_exec_ok", "stable_hash" in _ns and callable(_ns["stable_hash"]))
new_stable_hash = _ns["stable_hash"]

# --- 1. Empty list. ---
check("regression.empty_list.old_new_match", new_stable_hash([]) == old_stable_hash([]), (new_stable_hash([]), old_stable_hash([])))
check("regression.empty_list.matches_known_sha256_of_empty_bytes",
      new_stable_hash([]) == hashlib.sha256(b"").hexdigest(), new_stable_hash([]))

# --- 2. Single item. ---
_single = [u"shot3|foxmccouldwm1=some_value"]
check("regression.single_item.old_new_match", new_stable_hash(_single) == old_stable_hash(_single))

# --- 3. Many (10,000) short Unicode items, including non-ASCII. ---
random.seed(20260922)
_many = []
for _i in range(10000):
    if _i % 137 == 0:
        _many.append(u"shot%d|target_\u00e9\u00e8\u00fc_%d=value_%d" % (_i, _i, random.randint(0, 999999)))
    else:
        _many.append(u"shot%d|target%d=value_%d" % (_i, _i, random.randint(0, 999999)))
check("regression.many_unicode_items.old_new_match", new_stable_hash(_many) == old_stable_hash(_many))

# --- 4. Representative nested-fingerprint-shaped strings. ---
def _make_nested_fingerprint_string(seed):
    snap = {
        "shot_name": u"shot%d" % seed,
        "animation_set_name": u"target%d" % seed,
        "rig_status": u"UNRIGGED",
        "control_count": seed % 50,
        "control_names_in_animation_set_order": [u"bone_%d" % i for i in range(seed % 20)],
        "control_types": dict((u"bone_%d" % i, u"DmeTransformControl") for i in range(seed % 20)),
        "groups": dict(
            (u"Group%d" % i, {
                "path": u"Group%d" % i, "name": u"Group%d" % i, "parent_path": u"<ROOT>",
                "visible": True, "effective_visible": True, "selectable": True, "snappable": True,
                "group_color": [255, 128, 64, 255],
                "child_names_in_order": [], "direct_control_names_in_order": [u"bone_%d" % i],
            })
            for i in range(seed % 10)
        ),
        "memberships": dict((u"bone_%d" % i, [u"Group%d" % i]) for i in range(seed % 20)),
        "duplicate_control_names": {}, "duplicate_sibling_groups": [],
        "duplicate_direct_controls": [], "duplicate_memberships": {},
        "rig_recon_exists": False, "master_recon_exists": False,
    }
    return u"shot%d|target%d=%s" % (seed, seed, dumps_sorted(snap))


_nested = [_make_nested_fingerprint_string(i) for i in range(500)]
check("regression.nested_fingerprint_strings.old_new_match", new_stable_hash(_nested) == old_stable_hash(_nested))

# --- 5/6. REAL Checkpoint C1-2 PRE and POST fingerprint data, through
#          the exact call-site transformation D1 uses. ---
with open(C1_JSON_PATH, "rb") as f:
    _c1_data = f.read()
_c1_report = json.loads(_c1_data.decode("utf-8"))
_real_pre_fingerprint = _c1_report["pre_fingerprint"]
_real_post_fingerprint = _c1_report["post_fingerprint"]
check("fixture.real_c1_pre_fingerprint_has_85_targets", len(_real_pre_fingerprint) == 85, len(_real_pre_fingerprint))
check("fixture.real_c1_post_fingerprint_has_85_targets", len(_real_post_fingerprint) == 85, len(_real_post_fingerprint))

_real_pre_values = [u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_pre_fingerprint.items()]
_real_post_values = [u"%s=%s" % (k, dumps_sorted(v)) for k, v in _real_post_fingerprint.items()]

_new_pre_hash = new_stable_hash(_real_pre_values)
_old_pre_hash = old_stable_hash(_real_pre_values)
check("regression.real_c1_pre_fingerprint.old_new_match", _new_pre_hash == _old_pre_hash, (_new_pre_hash, _old_pre_hash))
check("regression.real_c1_pre_fingerprint.matches_c1_own_accepted_hash",
      _new_pre_hash == _c1_report["pre_fingerprint_hash"], (_new_pre_hash, _c1_report["pre_fingerprint_hash"]))

_new_post_hash = new_stable_hash(_real_post_values)
_old_post_hash = old_stable_hash(_real_post_values)
check("regression.real_c1_post_fingerprint.old_new_match", _new_post_hash == _old_post_hash, (_new_post_hash, _old_post_hash))
check("regression.real_c1_post_fingerprint.matches_c1_own_accepted_hash",
      _new_post_hash == _c1_report["post_fingerprint_hash"], (_new_post_hash, _c1_report["post_fingerprint_hash"]))

# --- 7. Large synthetic list (200,000 items) -- NEW implementation
#        only, per the governing correction's own scoping ("provably
#        hash-equivalent to the old implementation for inputs small
#        enough for the old implementation to execute"). This proves
#        the new implementation completes and returns a well-formed
#        digest at a scale well beyond anything D1 itself produces
#        (85 items), without attempting to also run the old two-giant-
#        copies algorithm at this size in this process. ---
_large = [u"synth%d|target%d=value_%d" % (i, i, i * 7919 % 1000003) for i in range(200000)]
_large_hash = new_stable_hash(_large)
check("regression.large_synthetic_list.new_impl_completes_and_returns_valid_digest",
      isinstance(_large_hash, str) and len(_large_hash) == 64, _large_hash)
_large_hash_again = new_stable_hash(list(_large))
check("regression.large_synthetic_list.new_impl_is_deterministic", _large_hash == _large_hash_again)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
if not all(c for _, c in RESULTS):
    sys.exit(1)
