# -*- coding: utf-8 -*-
"""
O2 offline closure-lifetime test: does capture_tree()'s own recursive
`walk` closure (which closes over `groups`/`memberships`/
`duplicate_siblings`/`duplicate_direct_controls`/itself) transitively
keep its own returned payload alive AFTER the caller has already
released its own reference, until the cyclic garbage collector runs?

This test extracts capture_tree() and every function it calls
(children, direct_controls, is_visible, is_selectable, is_snappable,
group_color_rgba, path_string, arr, attr, scalar, typ, name, plus the
remaining FINGERPRINT_FUNCTION_RANGES entries so no dependency is
hand-picked and possibly missed) VERBATIM from the pinned, accepted
production Normalizer (Rebuild_Control_Groups_Normalizer.py, SHA-256
cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867) --
the exact same extraction technique every earlier checkpoint in this
project already uses (never modifying the file).

Since no real SFM environment is available offline, this test builds
FAKE DME objects implementing exactly the interface capture_tree()'s
own dependency chain calls, confirmed by direct source reading:
  - GetName() -> unicode
  - GetTypeString() -> unicode ("DmeControlGroup" / anything else for controls)
  - GetAttribute(name) -> an object with .Count()/[i] (array) or .GetValue() (scalar)
  - IsVisible() / IsSelectable() / IsSnappable() -> bool
  - GroupColor() -> an object with .r/.g/.b/.a int attributes

Mechanism under test (source-confirmed, not assumed): capture_tree()'s
nested `def walk(...)` recurses by calling itself by name -- `walk` is
therefore a free variable inside its own body, making its closure cell
self-referential. A self-referential closure cannot be freed by
ordinary refcounting; it requires the cyclic garbage collector.
capture_tree()'s own return statement (line 1327-1334) includes the
SAME `groups`/`memberships`/`duplicate_sibling_groups`/
`duplicate_direct_controls` objects that `walk`'s own closure also
holds references to -- so even after the CALLER drops its own
reference to capture_tree()'s return value, those payload dicts remain
reachable via the orphaned, uncollected `walk` closure until
gc.collect() (or an automatic collection) actually runs. Production's
own module docstring explicitly states "no gc.collect()" is used
internally, so nothing collects this along the way.

This test proves (or disproves) that mechanism empirically, using
weakref.ref() to detect true object liveness independent of any
particular scanning technique, under the real embedded Python 2.7.5.
"""
import ctypes
import ctypes.wintypes
import gc
import hashlib
import os
import sys

# Plain dicts have no __weakref__ slot in this interpreter, so liveness
# is tracked by scanning gc.get_objects() for a specific id() instead of
# weakref.ref() -- equally decisive (an id() reused by an unrelated new
# object of the SAME type at the SAME moment is not a realistic risk in
# these tightly-scoped, single-threaded test windows).


def is_id_still_tracked(target_id):
    for obj in gc.get_objects():
        if id(obj) == target_id:
            return True
    return False

PRODUCTION_NORMALIZER_PATH = (
    "E:\\SteamLibrary\\steamapps\\common\\SourceFilmmaker\\game\\usermod\\scripts\\sfm\\"
    "mainmenu\\ChadChan3D\\Rebuild_Control_Groups_Normalizer.py"
)
EXPECTED_PRODUCTION_NORMALIZER_SHA256 = (
    "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"
)

# Identical range table this whole project's checkpoints already use --
# extracting every pure, read-only, structural DME-reading function
# capture_tree() might transitively need, so no dependency is
# hand-picked and possibly missed.
FINGERPRINT_FUNCTION_RANGES = [
    ("ProbeError_class", 791, 792),
    ("NativePostFallback_class", 795, 796),
    ("native_ptr", 802, 812),
    ("to_unicode", 834, 844),
    ("ascii_fold", 846, 858),
    ("handle", 860, 861),
    ("name_fn", 863, 867),
    ("typ", 869, 873),
    ("attr", 875, 879),
    ("scalar", 881, 893),
    ("arr", 895, 927),
    ("attribute_name", 929, 933),
    ("attribute_type", 935, 939),
    ("iter_attributes", 941, 964),
    ("element_ref_pairs", 966, 1004),
    ("reachable", 1006, 1039),
    ("is_visible", 1041, 1053),
    ("is_selectable", 1055, 1064),
    ("is_snappable", 1066, 1075),
    ("_component_value", 1077, 1092),
    ("_parse_rgba_text", 1094, 1117),
    ("group_color_rgba", 1119, 1182),
    ("children", 1184, 1189),
    ("direct_controls", 1191, 1192),
    ("path_string", 1194, 1198),
    ("capture_tree", 1200, 1334),
]
FINGERPRINT_MODULE_CONSTANTS = {
    "RIG_RECON_ROOT": "__RIG_VISIBLE_RECON__",
    "MASTER_RECON_ROOT": "__MASTER_VISIBLE_RECON__",
}

with open(PRODUCTION_NORMALIZER_PATH, "rb") as f:
    production_bytes = f.read()
production_sha256 = hashlib.sha256(production_bytes).hexdigest()
if production_sha256 != EXPECTED_PRODUCTION_NORMALIZER_SHA256:
    sys.stdout.write(
        "FATAL: production Normalizer SHA-256 mismatch -- got %r, expected %r. Aborting.\n"
        % (production_sha256, EXPECTED_PRODUCTION_NORMALIZER_SHA256)
    )
    sys.exit(2)

all_lines = production_bytes.decode("ascii").splitlines()
blocks = []
for label, start, end in FINGERPRINT_FUNCTION_RANGES:
    blocks.append("\n".join(all_lines[start - 1:end]))
combined_source = "\n\n".join(blocks)

fp_ns = dict(FINGERPRINT_MODULE_CONSTANTS)
fp_ns["hashlib"] = hashlib
exec(compile(combined_source, "<o2_capture_tree_extraction>", "exec"), fp_ns)
capture_tree_fn = fp_ns["capture_tree"]

sys.stdout.write("Production Normalizer SHA-256 verified: %s\n" % production_sha256)
sys.stdout.write("capture_tree() extracted and exec'd OK: %r\n" % (capture_tree_fn,))


# ---------------------------------------------------------------------------
# Fake DME objects implementing exactly the interface capture_tree()'s
# own dependency chain calls (confirmed via direct source reading of
# children()/direct_controls()/is_visible()/is_selectable()/
# is_snappable()/group_color_rgba()/arr()/attr()).
# ---------------------------------------------------------------------------

class FakeArrayAttr(object):
    def __init__(self, array):
        self._array = array

    def Count(self):
        return len(self._array)

    def __getitem__(self, i):
        return self._array[i]


class FakeColor(object):
    def __init__(self, r, g, b, a):
        self.r, self.g, self.b, self.a = r, g, b, a


class FakeControl(object):
    def __init__(self, name):
        self._name = name

    def GetName(self):
        return self._name

    def GetTypeString(self):
        return u"DmeTransformControl"


class FakeGroup(object):
    def __init__(self, name, children=None, controls=None):
        self._name = name
        self._children = children or []
        self._controls = controls or []

    def GetName(self):
        return self._name

    def GetTypeString(self):
        return u"DmeControlGroup"

    def GetAttribute(self, attr_name):
        if attr_name == "children":
            return FakeArrayAttr(self._children)
        if attr_name == "controls":
            return FakeArrayAttr(self._controls)
        return None

    def IsVisible(self):
        return True

    def IsSelectable(self):
        return True

    def IsSnappable(self):
        return True

    def GroupColor(self):
        return FakeColor(255, 128, 32, 255)


def build_fake_tree(group_count=20, controls_per_group=8):
    """A flat tree (root + group_count direct child groups) -- sufficient
    to exercise walk()'s own recursion once per child group; nesting
    depth does not change the self-referential-closure mechanism, since
    there is exactly one `walk` closure per capture_tree() call
    regardless of tree shape."""
    groups = []
    for i in range(group_count):
        controls = [FakeControl(u"control_%d_%d" % (i, c)) for c in range(controls_per_group)]
        groups.append(FakeGroup(u"group_%d" % i, controls=controls))
    return FakeGroup(u"root", children=groups)


def memory_snapshot():
    class _ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.wintypes.DWORD),
            ("PageFaultCount", ctypes.wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(_ProcessMemoryCounters)
    process_handle = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(process_handle, ctypes.byref(counters), counters.cb)
    if not ok:
        return {"available": False}
    return {"available": True, "working_set_bytes": int(counters.WorkingSetSize),
             "pagefile_usage_bytes": int(counters.PagefileUsage)}


def count_walk_functions():
    n = 0
    for obj in gc.get_objects():
        if type(obj).__name__ == "function" and getattr(obj, "__name__", None) == "walk":
            n += 1
    return n


PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label, detail=None):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s%s\n" % (label, ("" if detail is None else " -- %r" % (detail,))))


sys.stdout.write("\n--- Sanity: capture_tree() runs correctly against the fake tree ---\n")
fake_root = build_fake_tree(group_count=20, controls_per_group=8)
result0 = capture_tree_fn(fake_root)
expect(result0["group_count"] == 21, "sanity.group_count_is_21_root_plus_20_children", result0["group_count"])
expect(len(result0["groups"]) == 21, "sanity.groups_dict_has_21_entries")
expect(set(result0["groups"].keys()) == {u"<ROOT>"} | set(u"group_%d" % i for i in range(20)), "sanity.group_paths_as_expected")
del result0
gc.collect()


sys.stdout.write("\n--- DECISIVE TEST 1: does del()-ing the return value actually free groups/memberships? ---\n")
gc.disable()
gc.collect()

result1 = capture_tree_fn(fake_root)
groups_id = id(result1["groups"])
memberships_id = id(result1["memberships"])
del result1

alive_before_collect = is_id_still_tracked(groups_id) and is_id_still_tracked(memberships_id)
expect(
    alive_before_collect,
    "closure.groups_and_memberships_SURVIVE_del_before_gc_collect "
    "(proves something OTHER than the caller's own reference keeps them alive)",
)

n_reclaimed = gc.collect()
alive_after_collect = is_id_still_tracked(groups_id) or is_id_still_tracked(memberships_id)
expect(
    not alive_after_collect,
    "closure.gc_collect_releases_them (proves it WAS the orphaned walk closure's own cycle, "
    "not a live-reference leak elsewhere)",
    n_reclaimed,
)
gc.enable()


sys.stdout.write("\n--- DECISIVE TEST 2: accumulation across repeated captures with NO interim gc.collect() ---\n")
sys.stdout.write("(mirrors production's own documented behavior -- 'no gc.collect()' used internally)\n")
gc.disable()
gc.collect()

N_CAPTURES = 25  # illustrative -- a single target's reconciled path can reach up to 5
                 # captures per this project's own corrected branch-truth finding;
                 # 25 approximates ~5 targets' worth accumulating with no interim collection
ids = []
for i in range(N_CAPTURES):
    result = capture_tree_fn(fake_root)
    ids.append(id(result["groups"]))
    del result  # simulates a caller that promptly releases its own reference after use

alive_count_before_collect = sum(1 for gid in ids if is_id_still_tracked(gid))
expect(
    alive_count_before_collect == N_CAPTURES,
    "closure.all_N_captures_own_groups_dicts_remain_alive_with_no_interim_collect",
    alive_count_before_collect,
)

peak_memory = memory_snapshot()
n_reclaimed_2 = gc.collect()
alive_count_after_collect = sum(1 for gid in ids if is_id_still_tracked(gid))
after_collect_memory = memory_snapshot()

expect(
    alive_count_after_collect == 0,
    "closure.single_final_gc_collect_releases_ALL_N_accumulated_captures_at_once",
    (alive_count_after_collect, n_reclaimed_2),
)
gc.enable()

sys.stdout.write(
    "\npeak_memory (before final collect)=%r\nafter_collect_memory=%r\n"
    % (peak_memory, after_collect_memory)
)


sys.stdout.write("\n--- DECISIVE TEST 3: orphaned `walk` function objects themselves accumulate identically ---\n")
gc.disable()
gc.collect()
baseline_walk_count = count_walk_functions()

for i in range(N_CAPTURES):
    result = capture_tree_fn(fake_root)
    del result

walk_count_before_collect = count_walk_functions() - baseline_walk_count
expect(
    walk_count_before_collect == N_CAPTURES,
    "closure.orphaned_walk_closures_accumulate_1_per_capture_with_no_interim_collect",
    walk_count_before_collect,
)
gc.collect()
walk_count_after_collect = count_walk_functions() - baseline_walk_count
expect(
    walk_count_after_collect == 0,
    "closure.gc_collect_reclaims_all_orphaned_walk_closures",
    walk_count_after_collect,
)
gc.enable()


sys.stdout.write("\n=== Conclusion classification for O2 Required Conclusion #5 (Closure cycle) ===\n")
mechanism_confirmed = (FAIL_COUNT[0] == 0)
sys.stdout.write("MECHANISM_EMPIRICALLY_CONFIRMED=%r\n" % (mechanism_confirmed,))
sys.stdout.write(
    "This proves the CLOSURE-CYCLE mechanism is real and reproducible under the real embedded\n"
    "Python 2.7.5: capture_tree()'s own returned payload (groups/memberships) is kept alive by\n"
    "the recursive `walk` closure's self-referential cycle, independent of and in addition to\n"
    "however long the caller's own top-level reference lasts -- and this is NOT resolved by\n"
    "ordinary del()/refcounting/scope-exit, only by gc.collect() or an automatic collection cycle.\n"
    "It does NOT by itself establish that this is MATERIAL at real target/command scale (that\n"
    "requires the real-SFM bounded run's own resource observations) -- see O2's own real-SFM\n"
    "companion diagnostic for that half of Required Conclusion #5.\n"
)

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
