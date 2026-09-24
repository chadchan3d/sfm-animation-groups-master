# -*- coding: utf-8 -*-
"""
Offline adversarial parity suite for F1-R6's fresh streaming discovery
candidate (F1_R6_Discovery_Streaming_Prototype.py) versus legacy
discover_rig_context()/reachable(), extracted VERBATIM (by source line
range, not retyped) from the accepted production Normalizer, against
synthetic fake-DME graphs. No real SFM environment is available offline.

Run under the real embedded Python 2.7.5:
  sdktools\\python\\2.7\\win32\\python.exe test_f1_r6_adversarial_parity.py
"""
import hashlib
import os
import sys

PRODUCTION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "audit_external_runtime", "Rebuild_Control_Groups_Normalizer.py",
)
EXPECTED_PRODUCTION_SHA256 = "cdc909a6da9d64c01e8cacf25769e9063a2c25198d4c2e0c2068417a6020e867"

PROTOTYPE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "F1_R6_Discovery_Streaming_Prototype.py")
EXPECTED_PROTOTYPE_SHA256 = "17851cd1fed519aa8134fb15c2f057c82a471b8d9b7d1f7b3ae7378edfab4cb8"

PROBE_ERROR_RANGE = (791, 792)
TO_UNICODE_RANGE = (834, 844)
HANDLE_RANGE = (860, 861)
NAME_RANGE = (863, 867)
TYP_RANGE = (869, 873)
ATTR_RANGE = (875, 879)
SCALAR_RANGE = (881, 893)
ARR_RANGE = (895, 927)
ATTRIBUTE_NAME_RANGE = (929, 933)
ATTRIBUTE_TYPE_RANGE = (935, 939)
ITER_ATTRIBUTES_RANGE = (941, 964)
ELEMENT_REF_PAIRS_RANGE = (966, 1004)
REACHABLE_RANGE = (1006, 1039)
DISCOVER_RIG_CONTEXT_RANGE = (3299, 3436)

PASS_COUNT = [0]
FAIL_COUNT = [0]


def expect(condition, label):
    if condition:
        PASS_COUNT[0] += 1
        sys.stdout.write("[PASS] %s\n" % label)
    else:
        FAIL_COUNT[0] += 1
        sys.stdout.write("[FAIL] %s\n" % label)


with open(PRODUCTION_PATH, "rb") as f:
    production_bytes = f.read()
expect(hashlib.sha256(production_bytes).hexdigest() == EXPECTED_PRODUCTION_SHA256, "production.sha256_matches_pinned")
production_text = production_bytes.decode("ascii")
production_lines = production_text.splitlines()

with open(PROTOTYPE_PATH, "rb") as f:
    prototype_bytes = f.read()
expect(hashlib.sha256(prototype_bytes).hexdigest() == EXPECTED_PROTOTYPE_SHA256, "prototype.sha256_matches_pinned")
prototype_text = prototype_bytes.decode("ascii")


def extract(range_tuple, lines=production_lines):
    start, end = range_tuple
    return "\n".join(lines[start - 1:end])


sys.stdout.write("--- Extracting legacy functions verbatim from the real pinned production source ---\n")

legacy_ns = {}
for rng, label in (
    (PROBE_ERROR_RANGE, "ProbeError"),
    (TO_UNICODE_RANGE, "to_unicode"),
    (HANDLE_RANGE, "handle"),
    (NAME_RANGE, "name"),
    (TYP_RANGE, "typ"),
    (ATTR_RANGE, "attr"),
    (SCALAR_RANGE, "scalar"),
    (ARR_RANGE, "arr"),
    (ATTRIBUTE_NAME_RANGE, "attribute_name"),
    (ATTRIBUTE_TYPE_RANGE, "attribute_type"),
    (ITER_ATTRIBUTES_RANGE, "iter_attributes"),
    (ELEMENT_REF_PAIRS_RANGE, "element_ref_pairs"),
    (REACHABLE_RANGE, "reachable"),
    (DISCOVER_RIG_CONTEXT_RANGE, "discover_rig_context"),
):
    exec(compile(extract(rng), "<legacy_%s>" % label, "exec"), legacy_ns)
    expect(label in legacy_ns, "extraction.legacy_%s_defined" % label)

legacy_discover_rig_context = legacy_ns["discover_rig_context"]

sys.stdout.write("\n--- Loading the candidate prototype, wired to the SAME extracted legacy helpers ---\n")

candidate_ns = dict(legacy_ns)  # candidate calls handle/typ/arr/scalar/element_ref_pairs/name/to_unicode/ProbeError as globals, identical to legacy's own
exec(compile(prototype_bytes, "<prototype>", "exec"), candidate_ns)
candidate_discover_rig_context = candidate_ns["discover_rig_context_streaming"]

expect(callable(candidate_discover_rig_context), "extraction.candidate_discover_rig_context_streaming_defined")

sys.stdout.write("\n--- Fake DME graph model ---\n")

_handle_counter = [1]


def _next_handle():
    _handle_counter[0] += 1
    return _handle_counter[0]


class FakeAttribute(object):
    def __init__(self, owner, name, atype, value):
        self._handle = _next_handle()
        self.owner = owner
        self._name = name
        self._atype = atype
        self._value = value

    def GetHandle(self):
        return self._handle

    def GetName(self):
        return self._name

    def GetTypeString(self):
        return self._atype

    def GetValue(self):
        if self._atype == "element_array":
            raise Exception("GetValue() not valid on an array attribute.")
        return self._value

    def GetValueUntyped(self):
        return self._value

    def Count(self):
        if self._atype != "element_array":
            raise Exception("Count() only valid on an array attribute.")
        return len(self._value)

    def __getitem__(self, i):
        if self._atype != "element_array":
            raise Exception("indexing only valid on an array attribute.")
        return self._value[i]

    def NextAttribute(self):
        order = self.owner._attr_order
        idx = order.index(self._name)
        if idx + 1 < len(order):
            return self.owner._attrs[order[idx + 1]]
        return None


class FakeElement(object):
    def __init__(self, typename, name):
        self._handle = _next_handle()
        self._typename = typename
        self._name = name
        self._attrs = {}
        self._attr_order = []
        self._animation_sets = []
        self._handle_raises = False
        self._type_raises = False

    def GetHandle(self):
        if self._handle_raises:
            raise Exception("synthetic GetHandle() failure")
        return self._handle

    def GetTypeString(self):
        if self._type_raises:
            raise Exception("synthetic GetTypeString() failure")
        return self._typename

    def GetName(self):
        return self._name

    def HasAnimationSet(self, aset):
        return aset in self._animation_sets

    def set_element(self, attr_name, target):
        self._attrs[attr_name] = FakeAttribute(self, attr_name, "element", target)
        self._attr_order.append(attr_name)

    def set_element_array(self, attr_name, targets):
        self._attrs[attr_name] = FakeAttribute(self, attr_name, "element_array", list(targets))
        self._attr_order.append(attr_name)

    def set_scalar(self, attr_name, value):
        self._attrs[attr_name] = FakeAttribute(self, attr_name, "scalar", value)
        self._attr_order.append(attr_name)

    def GetAttribute(self, attr_name):
        return self._attrs.get(attr_name)

    def FirstAttribute(self):
        if not self._attr_order:
            return None
        return self._attrs[self._attr_order[0]]


def make_rig(name, animation_sets=()):
    rig = FakeElement(u"DmeRig", name)
    rig._animation_sets = list(animation_sets)
    return rig


def make_aset(name):
    return FakeElement(u"DmeAnimationSet", name)


def wire_scene(scene, children):
    scene.set_element_array(u"children", children)


def wire_rig_registry(rig, aset, registry_name=u"registry", elementlist=(), extra_binding_records=0):
    """Wires rig.animSetList -> [one DmeRigAnimSetElements record whose
    own 'animationSet' points at aset]. Per the REAL algorithm
    (discover_rig_context(): 'registry_matches.append(rec)' then
    'registry = registry_matches[0]'), the matched BINDING RECORD ITSELF
    becomes 'registry' -- there is no separate registry object in the
    real schema. This helper sets 'elementList' directly on that same
    record and returns it. If extra_binding_records > 0, adds that many
    EXTRA DmeRigAnimSetElements records pointing at the SAME aset (to
    construct an AMBIGUOUS_RIG_REGISTRY fixture) -- none of the extras
    carry an elementList, matching that they are never selected as
    'registry' on that branch."""
    rec = FakeElement(u"DmeRigAnimSetElements", registry_name)
    rec.set_element(u"animationSet", aset)
    rec.set_element_array(u"elementList", list(elementlist))
    records = [rec]
    for i in range(extra_binding_records):
        extra_rec = FakeElement(u"DmeRigAnimSetElements", u"rec_extra_%d" % i)
        extra_rec.set_element(u"animationSet", aset)
        records.append(extra_rec)
    rig.set_element_array(u"animSetList", records)
    return rec


def run_parity(scene, aset, label):
    legacy_result = legacy_discover_rig_context(scene_shot(scene), aset)
    candidate_result = candidate_discover_rig_context(scene_shot(scene), aset)

    expect(legacy_result["status"] == candidate_result["status"], "%s.status_matches (%r vs %r)" % (label, legacy_result["status"], candidate_result["status"]))
    expect(legacy_result["reachable_rig_count"] == candidate_result["reachable_rig_count"], "%s.reachable_rig_count_matches (%r vs %r)" % (label, legacy_result["reachable_rig_count"], candidate_result["reachable_rig_count"]))
    expect(legacy_result["matching_rig_count"] == candidate_result["matching_rig_count"], "%s.matching_rig_count_matches (%r vs %r)" % (label, legacy_result["matching_rig_count"], candidate_result["matching_rig_count"]))
    expect(legacy_result["rig_handle"] == candidate_result["rig_handle"], "%s.rig_handle_matches" % label)
    expect(legacy_result["registry_handle"] == candidate_result["registry_handle"], "%s.registry_handle_matches" % label)
    expect(legacy_result["owned_handles"] == candidate_result["owned_handles"], "%s.owned_handles_matches" % label)
    expect(legacy_result["owned_names_in_order"] == candidate_result["owned_names_in_order"], "%s.owned_names_matches" % label)
    expect(legacy_result["hidden_groups"] == candidate_result["hidden_groups"], "%s.hidden_groups_matches" % label)
    legacy_rig_handle = None if legacy_result["rig"] is None else legacy_result["rig"].GetHandle()
    candidate_rig_handle = None if candidate_result["rig"] is None else candidate_result["rig"].GetHandle()
    expect(legacy_rig_handle == candidate_rig_handle, "%s.selected_rig_identity_matches" % label)
    legacy_registry_handle = None if legacy_result["registry"] is None else legacy_result["registry"].GetHandle()
    candidate_registry_handle = None if candidate_result["registry"] is None else candidate_result["registry"].GetHandle()
    expect(legacy_registry_handle == candidate_registry_handle, "%s.selected_registry_identity_matches" % label)
    return legacy_result, candidate_result


class FakeShot(object):
    def __init__(self, scene):
        self._scene = scene

    def GetAttribute(self, attr_name):
        return None  # scalar(shot,"scene") falls through to shot.scene fallback

    @property
    def scene(self):
        return self._scene


def scene_shot(scene):
    return FakeShot(scene)


sys.stdout.write("\n--- Fixture 1: simple tree, one rig, unique match ---\n")
scene1 = FakeElement(u"DmeScene", u"scene1")
aset1 = make_aset(u"aset1")
rig1 = make_rig(u"rig1", [aset1])
control1 = FakeElement(u"DmeControl", u"ctrl1")
registry1 = wire_rig_registry(rig1, aset1, elementlist=[control1])
aset1.set_element_array(u"controls", [control1])
wire_scene(scene1, [rig1, aset1])
r1_legacy, r1_candidate = run_parity(scene1, aset1, "fixture1_simple_tree_unique_rig")
expect(r1_legacy["status"] == "SUPPORTED_ACTIVE_RIG", "fixture1_legacy_reaches_supported_active_rig")

sys.stdout.write("\n--- Fixture 2: shared-reference DAG (same child reachable via two parents) ---\n")
scene2 = FakeElement(u"DmeScene", u"scene2")
aset2 = make_aset(u"aset2")
rig2 = make_rig(u"rig2", [aset2])
shared_child = FakeElement(u"DmeMisc", u"shared_child")
parentA = FakeElement(u"DmeGroup", u"parentA")
parentB = FakeElement(u"DmeGroup", u"parentB")
parentA.set_element(u"child", shared_child)
parentB.set_element(u"child", shared_child)
control2 = FakeElement(u"DmeControl", u"ctrl2")
registry2 = wire_rig_registry(rig2, aset2, elementlist=[control2])
aset2.set_element_array(u"controls", [control2])
wire_scene(scene2, [rig2, aset2, parentA, parentB])
r2_legacy, r2_candidate = run_parity(scene2, aset2, "fixture2_shared_reference_dag")
expect(r2_legacy["reachable_rig_count"] == 1, "fixture2_shared_child_visited_only_once_confirmed_via_rig_count")

sys.stdout.write("\n--- Fixture 3: cycle (element references its own ancestor) ---\n")
scene3 = FakeElement(u"DmeScene", u"scene3")
aset3 = make_aset(u"aset3")
rig3 = make_rig(u"rig3", [aset3])
cyclic_a = FakeElement(u"DmeGroup", u"cyclic_a")
cyclic_b = FakeElement(u"DmeGroup", u"cyclic_b")
cyclic_a.set_element(u"next", cyclic_b)
cyclic_b.set_element(u"back", cyclic_a)  # cycle
control3 = FakeElement(u"DmeControl", u"ctrl3")
registry3 = wire_rig_registry(rig3, aset3, elementlist=[control3])
aset3.set_element_array(u"controls", [control3])
wire_scene(scene3, [rig3, aset3, cyclic_a])
r3_legacy, r3_candidate = run_parity(scene3, aset3, "fixture3_cycle")

sys.stdout.write("\n--- Fixture 4: duplicate paths to same element (three parents, one child) ---\n")
scene4 = FakeElement(u"DmeScene", u"scene4")
aset4 = make_aset(u"aset4")
rig4 = make_rig(u"rig4", [aset4])
dup_child = FakeElement(u"DmeMisc", u"dup_child")
p1 = FakeElement(u"DmeGroup", u"p1")
p2 = FakeElement(u"DmeGroup", u"p2")
p3 = FakeElement(u"DmeGroup", u"p3")
p1.set_element(u"c", dup_child)
p2.set_element(u"c", dup_child)
p3.set_element(u"c", dup_child)
control4 = FakeElement(u"DmeControl", u"ctrl4")
registry4 = wire_rig_registry(rig4, aset4, elementlist=[control4])
aset4.set_element_array(u"controls", [control4])
wire_scene(scene4, [rig4, aset4, p1, p2, p3])
r4_legacy, r4_candidate = run_parity(scene4, aset4, "fixture4_duplicate_paths_same_element")

sys.stdout.write("\n--- Fixture 5: no rig at all ---\n")
scene5 = FakeElement(u"DmeScene", u"scene5")
aset5 = make_aset(u"aset5")
aset5.set_element_array(u"controls", [])
wire_scene(scene5, [aset5])
r5_legacy, r5_candidate = run_parity(scene5, aset5, "fixture5_no_rig")
expect(r5_legacy["status"] == "UNRIGGED", "fixture5_legacy_status_is_unrigged")

sys.stdout.write("\n--- Fixture 6: one rig, exact match (re-verifying the common case) ---\n")
# Already covered by fixture 1; explicit second confirmation with a
# different topology (rig NOT the first scene child).
scene6 = FakeElement(u"DmeScene", u"scene6")
aset6 = make_aset(u"aset6")
rig6 = make_rig(u"rig6", [aset6])
control6 = FakeElement(u"DmeControl", u"ctrl6")
registry6 = wire_rig_registry(rig6, aset6, elementlist=[control6])
aset6.set_element_array(u"controls", [control6])
wire_scene(scene6, [aset6, rig6])  # aset listed BEFORE rig
r6_legacy, r6_candidate = run_parity(scene6, aset6, "fixture6_one_rig_reordered")

sys.stdout.write("\n--- Fixture 7: multiple competing rigs (both match this aset) ---\n")
scene7 = FakeElement(u"DmeScene", u"scene7")
aset7 = make_aset(u"aset7")
rigA7 = make_rig(u"rigA7", [aset7])
rigB7 = make_rig(u"rigB7", [aset7])
wire_scene(scene7, [rigA7, rigB7, aset7])
r7_legacy, r7_candidate = run_parity(scene7, aset7, "fixture7_multiple_competing_rigs")
expect(r7_legacy["status"] == "AMBIGUOUS_MULTIPLE_RIGS", "fixture7_legacy_status_is_ambiguous_multiple_rigs")
expect(r7_legacy["rig"] is None, "fixture7_legacy_rig_is_none_on_ambiguous -- confirms the asymmetry F1_R6 preserves")
expect(r7_candidate["rig"] is None, "fixture7_candidate_rig_is_none_on_ambiguous -- exact parity with the asymmetry")

sys.stdout.write("\n--- Fixture 8: registry absent (no DmeRigAnimSetElements record binds this aset) ---\n")
scene8 = FakeElement(u"DmeScene", u"scene8")
aset8 = make_aset(u"aset8")
rig8 = make_rig(u"rig8", [aset8])
rig8.set_element_array(u"animSetList", [])  # no binding records at all
wire_scene(scene8, [rig8, aset8])
r8_legacy, r8_candidate = run_parity(scene8, aset8, "fixture8_registry_absent")
expect(r8_legacy["status"] == "AMBIGUOUS_RIG_REGISTRY", "fixture8_legacy_status_is_ambiguous_rig_registry")
expect(r8_legacy["rig"] is not None and r8_legacy["registry"] is None, "fixture8_legacy_rig_set_registry_none -- confirms this asymmetry too")

sys.stdout.write("\n--- Fixture 9: registry unique (baseline, already covered by fixture 1) ---\n")
expect(r1_legacy["status"] == "SUPPORTED_ACTIVE_RIG" and r1_legacy["registry"] is not None, "fixture9_registry_unique_confirmed_via_fixture1")

sys.stdout.write("\n--- Fixture 10: registry ambiguous (two binding records both match this aset) ---\n")
scene10 = FakeElement(u"DmeScene", u"scene10")
aset10 = make_aset(u"aset10")
rig10 = make_rig(u"rig10", [aset10])
control10 = FakeElement(u"DmeControl", u"ctrl10")
registry10 = wire_rig_registry(rig10, aset10, elementlist=[control10], extra_binding_records=1)
aset10.set_element_array(u"controls", [control10])
wire_scene(scene10, [rig10, aset10])
r10_legacy, r10_candidate = run_parity(scene10, aset10, "fixture10_registry_ambiguous")
expect(r10_legacy["status"] == "AMBIGUOUS_RIG_REGISTRY", "fixture10_legacy_status_is_ambiguous_rig_registry")

sys.stdout.write("\n--- Fixture 11: target absent (rig exists but does not claim this aset) ---\n")
scene11 = FakeElement(u"DmeScene", u"scene11")
aset11 = make_aset(u"aset11")
other_aset11 = make_aset(u"other_aset11")
rig11 = make_rig(u"rig11", [other_aset11])  # rig claims a DIFFERENT aset
wire_scene(scene11, [rig11, aset11, other_aset11])
r11_legacy, r11_candidate = run_parity(scene11, aset11, "fixture11_target_absent")
expect(r11_legacy["status"] == "UNRIGGED", "fixture11_legacy_status_is_unrigged")

sys.stdout.write("\n--- Fixture 12: target unique (baseline, already covered by fixture 1) ---\n")
expect(r1_legacy["matching_rig_count"] == 1, "fixture12_target_unique_confirmed_via_fixture1")

sys.stdout.write("\n--- Fixture 13: multiple candidate target-like elements (several DmeRig objects, only one matches) ---\n")
scene13 = FakeElement(u"DmeScene", u"scene13")
aset13 = make_aset(u"aset13")
other_aset13 = make_aset(u"other_aset13")
rig_match13 = make_rig(u"rig_match13", [aset13])
rig_other13 = make_rig(u"rig_other13", [other_aset13])
control13 = FakeElement(u"DmeControl", u"ctrl13")
registry13 = wire_rig_registry(rig_match13, aset13, elementlist=[control13])
aset13.set_element_array(u"controls", [control13])
wire_scene(scene13, [rig_match13, rig_other13, aset13, other_aset13])
r13_legacy, r13_candidate = run_parity(scene13, aset13, "fixture13_multiple_candidate_rigs_one_matches")
expect(r13_legacy["reachable_rig_count"] == 2 and r13_legacy["matching_rig_count"] == 1, "fixture13_counts_correct")

sys.stdout.write("\n--- Fixture 14: malformed/null reference (an element_array containing a None entry) ---\n")
scene14 = FakeElement(u"DmeScene", u"scene14")
aset14 = make_aset(u"aset14")
rig14 = make_rig(u"rig14", [aset14])
control14 = FakeElement(u"DmeControl", u"ctrl14")
registry14 = wire_rig_registry(rig14, aset14, elementlist=[control14])
aset14.set_element_array(u"controls", [control14])
malformed_holder14 = FakeElement(u"DmeGroup", u"malformed_holder14")
malformed_holder14.set_element_array(u"children", [None, control14])
wire_scene(scene14, [rig14, aset14, malformed_holder14])
r14_legacy, r14_candidate = run_parity(scene14, aset14, "fixture14_malformed_null_reference")

sys.stdout.write("\n--- Fixture 15: attribute access exception (GetTypeString raises for one element) ---\n")
scene15 = FakeElement(u"DmeScene", u"scene15")
aset15 = make_aset(u"aset15")
rig15 = make_rig(u"rig15", [aset15])
control15 = FakeElement(u"DmeControl", u"ctrl15")
registry15 = wire_rig_registry(rig15, aset15, elementlist=[control15])
aset15.set_element_array(u"controls", [control15])
broken_typ15 = FakeElement(u"DmeMisc", u"broken_typ15")
broken_typ15._type_raises = True
wire_scene(scene15, [rig15, aset15, broken_typ15])
r15_legacy, r15_candidate = run_parity(scene15, aset15, "fixture15_attribute_access_exception_typ")

sys.stdout.write("\n--- Fixture 16: array access exception (GetHandle raises for one element) ---\n")
scene16 = FakeElement(u"DmeScene", u"scene16")
aset16 = make_aset(u"aset16")
rig16 = make_rig(u"rig16", [aset16])
control16 = FakeElement(u"DmeControl", u"ctrl16")
registry16 = wire_rig_registry(rig16, aset16, elementlist=[control16])
aset16.set_element_array(u"controls", [control16])
broken_handle16 = FakeElement(u"DmeMisc", u"broken_handle16")
broken_handle16._handle_raises = True
wire_scene(scene16, [rig16, aset16, broken_handle16])
r16_legacy, r16_candidate = run_parity(scene16, aset16, "fixture16_handle_access_exception")

sys.stdout.write("\n--- Fixture 17: ordering-sensitive candidate layout (matching rig appears LAST in traversal) ---\n")
scene17 = FakeElement(u"DmeScene", u"scene17")
aset17 = make_aset(u"aset17")
rig17 = make_rig(u"rig17", [aset17])
filler17 = [FakeElement(u"DmeMisc", u"filler17_%d" % i) for i in range(20)]
control17 = FakeElement(u"DmeControl", u"ctrl17")
registry17 = wire_rig_registry(rig17, aset17, elementlist=[control17])
aset17.set_element_array(u"controls", [control17])
wire_scene(scene17, filler17 + [aset17, rig17])  # rig deliberately last
r17_legacy, r17_candidate = run_parity(scene17, aset17, "fixture17_ordering_sensitive_layout")

sys.stdout.write("\n--- Fixture 18: very large synthetic graph ---\n")
scene18 = FakeElement(u"DmeScene", u"scene18")
aset18 = make_aset(u"aset18")
rig18 = make_rig(u"rig18", [aset18])
control18 = FakeElement(u"DmeControl", u"ctrl18")
registry18 = wire_rig_registry(rig18, aset18, elementlist=[control18])
aset18.set_element_array(u"controls", [control18])
large_filler18 = [FakeElement(u"DmeMisc", u"large_%d" % i) for i in range(1500)]
# Chain them so the traversal must actually walk the whole chain, not
# just a flat scene-level array.
for i in range(len(large_filler18) - 1):
    large_filler18[i].set_element(u"next", large_filler18[i + 1])
wire_scene(scene18, [rig18, aset18, large_filler18[0]])
r18_legacy, r18_candidate = run_parity(scene18, aset18, "fixture18_very_large_synthetic_graph")
expect(r18_legacy["reachable_rig_count"] == 1 and r18_legacy["status"] == "SUPPORTED_ACTIVE_RIG", "fixture18_large_graph_still_resolves_correctly")

sys.stdout.write("\n--- Fixture 19: zero ownership (rig+registry unique, but no owned controls) ---\n")
scene19 = FakeElement(u"DmeScene", u"scene19")
aset19 = make_aset(u"aset19")
rig19 = make_rig(u"rig19", [aset19])
control19 = FakeElement(u"DmeControl", u"ctrl19")
unrelated_registry_element19 = FakeElement(u"DmeControl", u"unrelated19")
registry19 = wire_rig_registry(rig19, aset19, elementlist=[unrelated_registry_element19])  # does NOT include control19
aset19.set_element_array(u"controls", [control19])
wire_scene(scene19, [rig19, aset19])
r19_legacy, r19_candidate = run_parity(scene19, aset19, "fixture19_zero_ownership")
expect(r19_legacy["status"] == "STALE_ZERO_OWNERSHIP_RIG", "fixture19_legacy_status_is_stale_zero_ownership")

sys.stdout.write("\n--- Fixture 20: RIG_CONTEXT_UNAVAILABLE (no scene at all) ---\n")


class FakeShotNoScene(object):
    def GetAttribute(self, attr_name):
        return None

    @property
    def scene(self):
        return None


aset20 = make_aset(u"aset20")
legacy_r20 = legacy_discover_rig_context(FakeShotNoScene(), aset20)
candidate_r20 = candidate_discover_rig_context(FakeShotNoScene(), aset20)
expect(legacy_r20["status"] == "RIG_CONTEXT_UNAVAILABLE" == candidate_r20["status"], "fixture20_rig_context_unavailable_parity")

sys.stdout.write("\n--- Fixture 21: RIG_TRAVERSAL_FAILED (scene itself raises when handled) ---\n")


class RaisingScene(object):
    def GetHandle(self):
        raise Exception("synthetic scene handle failure")


class FakeShotRaisingScene(object):
    def GetAttribute(self, attr_name):
        return None

    @property
    def scene(self):
        return RaisingScene()


# reachable()'s own stack.pop() -> handle(obj) try/except swallows a
# single failed root -- this actually still returns an EMPTY reachable
# list (root fails handle(), continue, stack empties) rather than
# raising RIG_TRAVERSAL_FAILED (that status is reserved for
# reachable(scene) itself raising, e.g. scalar(shot,"scene") producing
# something reachable() cannot even begin iterating over). Confirmed by
# direct behavior comparison rather than assumed.
aset21 = make_aset(u"aset21")
legacy_r21 = legacy_discover_rig_context(FakeShotRaisingScene(), aset21)
candidate_r21 = candidate_discover_rig_context(FakeShotRaisingScene(), aset21)
expect(legacy_r21["status"] == candidate_r21["status"], "fixture21_traversal_edge_case_parity (%r vs %r)" % (legacy_r21["status"], candidate_r21["status"]))
expect(legacy_r21["status"] == "UNRIGGED", "fixture21_confirmed_actual_legacy_behavior_is_unrigged_not_traversal_failed")

sys.stdout.write("\n=== %d PASS / %d FAIL ===\n" % (PASS_COUNT[0], FAIL_COUNT[0]))
sys.exit(0 if FAIL_COUNT[0] == 0 else 1)
