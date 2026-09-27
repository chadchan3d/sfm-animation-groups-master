# -*- coding: utf-8 -*-
"""CPM convergence Step 1 -- Suite 1 foundation tests for the CPM-owned
``cpm_compat_v1`` projection (cpm/convergence/cpm_compat_v1_projection.py).

Three phases, matching the established two-interpreter qualification
shape (compiler tooling is Python-3-only; the runtime package and CPM run
under embedded Python 2.7.5):

  --phase=publish   (Python 3): writes a small synthetic Master into a
      fresh OS temp directory, publishes it with the real
      tools/sfm_master_sidecar publisher, runs the whole suite, and writes
      a canonical result digest.

  --phase=suite     (Python 2.7.5, separate process): runs the same suite
      against the directory the publish phase produced (no recompilation)
      and writes its own digest.

  --phase=compare   (either interpreter): the two digests must be
      identical, check-for-check and value-for-value.

Oracles:
  * frozen G18AN (cpm/baseline, SHA-256 pinned) supplies the fold rule,
    wrapper stripping and ``_answer_from_result``, extracted verbatim from
    pinned line ranges. ``_answer_from_result`` only supports Hit and
    MasterUnknown, so it is the oracle for those cases only; the suite
    asserts it rejects FoldConflict.
  * conflict (multi-destination) families are checked against the
    hand-audited expectations below.

Never launches SFM. Never modifies the canonical Master, the frozen G18AN
baseline, or the shared authority package.
"""
import hashlib
import io
import json
import os
import sys
import tempfile
import textwrap

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CONVERGENCE_DIR = os.path.join(_REPO_ROOT, "cpm", "convergence")
TOOLS_DIR = os.path.join(_REPO_ROOT, "tools")
PACKAGE_ROOT = os.path.join(_REPO_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction6")
G18AN_PATH = os.path.join(_REPO_ROOT, "cpm", "baseline", "SFM_CSP_G18AN_SaveNewCopy.py")
G18AN_SHA256 = "3326024ddecd544ad1e10659bbf7b98420b5f147fca775433878c19fd9e66b3e"

for _p in (TOOLS_DIR, PACKAGE_ROOT, CONVERGENCE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cpm_compat_v1_projection as cpm  # noqa: E402

PY2 = sys.version_info[0] == 2
try:
    _TEXT = unicode  # noqa: F821
except NameError:
    _TEXT = str

FIXTURE_DIR = os.path.join(tempfile.gettempdir(), "cpm_compat_v1_suite1_fixture")
MASTER_PATH = os.path.join(FIXTURE_DIR, "suite1_master.txt")
DIGEST_PY3 = os.path.join(FIXTURE_DIR, "digest_py3.json")
DIGEST_PY27 = os.path.join(FIXTURE_DIR, "digest_py27.json")

MASTER_BODY = (
    u'"groupFile"\n{\n'
    u'\t"Face"\n\t{\n'
    u'\t\t"Eyes"\n\t\t{\n'
    u'\t\t\t"control"\t\t"Blink"\n'
    u'\t\t\t"control"\t\t"Blink"\n'
    u'\t\t\t"control"\t\t"BLINK"\n'
    u'\t\t\t"control"\t\t"Wink"\n'
    u'\t\t}\n'
    u'\t\t"Mouth"\n\t\t{\n'
    u'\t\t\t"control"\t\t"JawOpen"\n'
    u'\t\t\t"control"\t\t"Brow Up"\n'
    u'\t\t\t"control"\t\t"ÑOSE"\n'
    u'\t\t\t"control"\t\t"Ñose"\n'
    u'\t\t}\n'
    u'\t}\n'
    u'\t"Body Morphs"\n\t{\n'
    u'\t\t"control"\t\t"Belly"\n'
    u'\t\t"control"\t\t"wink"\n'
    u'\t}\n'
    u'\t"Clothing"\n\t{\n'
    u'\t\t"Tops"\n\t\t{\n'
    u'\t\t\t"control"\t\t"Shirt"\n'
    u'\t\t}\n'
    u'\t}\n'
    u'\t"Other"\n\t{\n'
    u'\t\t"Misc"\n\t\t{\n'
    u'\t\t\t"Deep"\n\t\t\t{\n'
    u'\t\t\t\t"control"\t\t"Tail"\n'
    u'\t\t\t}\n'
    u'\t\t}\n'
    u'\t}\n'
    u'}\n'
)

QUERY_LITERALS = [
    u"Blink", u"bLiNk", u"BLINK", u"Wink", u"WINK", u"wink", u"JawOpen", u"jawopen",
    u"Brow Up", u"brow up", u"BrowUp", u"Brow  Up", u"ÑOSE", u"Ñose", u"ñose",
    u"Belly", u"Shirt", u"Tail", u"Nonexistent",
]

# Hand-audited against MASTER_BODY above.
def _fam(status, resolved, destinations, spellings, count):
    return {"status": status, "resolved_path": resolved, "destinations": destinations,
            "spellings": spellings, "occurrence_count": count}

_ABSENT = _fam(u"absent", None, [], [], 0)
EXPECTED_FAMILIES = {
    u"blink": _fam(u"resolved", u"Face/Eyes", [u"Face/Eyes"], [u"BLINK", u"Blink"], 3),
    u"wink": _fam(u"conflict", None, [u"Body Morphs", u"Face/Eyes"], [u"Wink", u"wink"], 2),
    u"jawopen": _fam(u"resolved", u"Face/Mouth", [u"Face/Mouth"], [u"JawOpen"], 1),
    u"brow up": _fam(u"resolved", u"Face/Mouth", [u"Face/Mouth"], [u"Brow Up"], 1),
    u"Ñose": _fam(u"resolved", u"Face/Mouth", [u"Face/Mouth"], [u"ÑOSE", u"Ñose"], 2),
    u"belly": _fam(u"resolved", u"Body Morphs", [u"Body Morphs"], [u"Belly"], 1),
    u"shirt": _fam(u"resolved", u"Clothing/Tops", [u"Clothing/Tops"], [u"Shirt"], 1),
    u"tail": _fam(u"resolved", u"Other/Misc/Deep", [u"Other/Misc/Deep"], [u"Tail"], 1),
    u"browup": _ABSENT,
    u"brow  up": _ABSENT,
    u"ñose": _ABSENT,
    u"nonexistent": _ABSENT,
}
EXPECTED_MATCH_KIND = {
    u"Blink": u"exact", u"bLiNk": u"ascii-fold", u"BLINK": u"exact",
    u"Wink": u"exact", u"WINK": u"ascii-fold", u"wink": u"exact",
    u"JawOpen": u"exact", u"jawopen": u"ascii-fold",
    u"Brow Up": u"exact", u"brow up": u"ascii-fold", u"BrowUp": u"none", u"Brow  Up": u"none",
    u"ÑOSE": u"exact", u"Ñose": u"exact", u"ñose": u"none",
    u"Belly": u"exact", u"Shirt": u"exact", u"Tail": u"exact", u"Nonexistent": u"none",
}

PROD_SEMANTIC_POLICY = u"master-category-operation-scope-v1"

RESULTS = []


def check(name, condition, value=None):
    """Records a check. ``value`` must be interpreter-independent data; it
    goes into the cross-interpreter digest."""
    RESULTS.append((name, bool(condition), value))
    print("[%s] %s" % ("PASS" if condition else "FAIL", name))
    if not condition and value is not None:
        print("      value: %r" % (value,))


def expect_raises(name, exc_types, fn, *args):
    try:
        fn(*args)
    except exc_types as exc:
        check(name, True, type(exc).__name__)
        return
    except Exception as exc:  # wrong failure class
        check(name, False, "raised %s: %s" % (type(exc).__name__, exc))
        return
    check(name, False, "did not raise")


def _canon(obj):
    return json.loads(json.dumps(obj, sort_keys=True, default=repr))


# ---------------------------------------------------------------------------
# G18AN oracle (verbatim extraction from pinned ranges)
# ---------------------------------------------------------------------------

_G18AN_RANGES = (
    ("u", 58, 69, "def u(value):"),
    ("provider_constants", 1113, 1117, "SEMANTIC_PROVIDER_CONTRACT = "),
    ("status_constants", 1140, 1159, "SEMANTIC_STATUS_RESOLVED = "),
    ("p01_ascii_fold", 1162, 1171, "def p01_ascii_fold(value):"),
    ("g18an_normalize_sidecar_path", 2259, 2295, "def g18an_normalize_sidecar_path("),
    ("_answer_from_result", 2496, 2588, "    def _answer_from_result("),
)


def load_g18an_oracle():
    with open(G18AN_PATH, "rb") as f:
        raw = f.read()
    sha = hashlib.sha256(raw).hexdigest()
    check("oracle.g18an_sha256_pinned frozen G18AN baseline matches its pinned SHA-256", sha == G18AN_SHA256, sha)
    lines = raw.decode("utf-8").split(u"\n")
    check("oracle.policy_line_pinned G18AN line 18494 defines PROD_SEMANTIC_POLICY",
          lines[18493] == u'PROD_SEMANTIC_POLICY = u"%s"' % PROD_SEMANTIC_POLICY)
    ns = {}
    if not PY2:
        ns["unicode"] = str
        ns["unichr"] = chr
    for label, start, end, head in _G18AN_RANGES:
        block = lines[start - 1:end]
        check("oracle.range_pinned.%s" % label, block[0].startswith(head), block[0])
        text = u"\n".join(block) + u"\n"
        if label == "_answer_from_result":
            text = textwrap.dedent(text)
        exec(compile(text, "G18AN:%s" % label, "exec"), ns)
    return ns


class _OracleSelf(object):
    def __init__(self, wrapper):
        self._wrapper = wrapper


# ---------------------------------------------------------------------------
# Fakes for explicit-result-handling tests (class names are what matter)
# ---------------------------------------------------------------------------

class Hit(object):
    def __init__(self, destination, rows):
        self.destination = destination
        self._rows = rows

    def occurrences(self):
        return list(self._rows)


class FoldConflict(object):
    def __init__(self, destinations, rows):
        self.destinations = set(destinations)
        self._rows = rows

    def occurrences(self):
        return list(self._rows)


class MasterUnknown(object):
    pass


class Surprise(object):
    pass


class _FakeProvider(object):
    def __init__(self, results, wrapper=u"groupFile"):
        self.results = results
        self.wrapper = wrapper
        self.lookup_types = []

    def wrapper_path(self):
        return self.wrapper

    def lookup_fold(self, query):
        self.lookup_types.append(isinstance(query, bytes))
        if not isinstance(query, bytes):
            raise TypeError("lookup_fold requires bytes")
        return self.results[query.decode("utf-8")]


def _row(literal, path):
    return {"literal": literal, "full_path": path, "local_rank": 0, "global_rank": 0}


class _PoisonProvider(object):
    """Proxy over a real provider that returns an unsupported result type
    for one fold, to prove the real broker publishes nothing."""
    def __init__(self, real, poison):
        self._real = real
        self._poison = poison

    def wrapper_path(self):
        return self._real.wrapper_path()

    def lookup_fold(self, query):
        if query == self._poison:
            return Surprise()
        return self._real.lookup_fold(query)


# ---------------------------------------------------------------------------
# Suite sections
# ---------------------------------------------------------------------------

FOLD_CASES = [
    u"Blink", u"BLINK", u"bLiNk", u"ZAza", u"A_Z-09", u"@[`{", u"Brow Up", u"Brow  Up",
    u"\tTab\n", u"ÑOSE", u"Ñose", u"ñose", u"ÀÉÎ", u"İI",
]


def section_fold(oracle):
    from sfm_master_authority_productionized import normalizer_compat_adapter as adapter
    from sfm_master_sidecar import format as fmt
    for literal in FOLD_CASES:
        folded = cpm.cpm_fold(literal)
        tag = literal.encode("unicode_escape").decode("ascii")
        check("fold.g18an_parity %s" % tag, folded == oracle["p01_ascii_fold"](literal), folded)
        check("fold.adapter_parity %s" % tag,
              cpm.fold_to_lookup_bytes(folded) == adapter._ascii_fold_to_bytes(literal))
        check("fold.format_parity %s" % tag,
              cpm.fold_to_lookup_bytes(folded) == fmt.ascii_fold_bytes(literal.encode("utf-8")))
        check("fold.is_text %s" % tag, isinstance(folded, _TEXT))
    check("fold.idempotent", all(cpm.cpm_fold(cpm.cpm_fold(x)) == cpm.cpm_fold(x) for x in FOLD_CASES))
    check("fold.whitespace_preserved", cpm.cpm_fold(u"Brow  Up") == u"brow  up")
    check("fold.non_ascii_untouched", cpm.cpm_fold(u"ÑOSE") == u"Ñose")
    check("fold.bytes_input_decoded_utf8", cpm.cpm_fold(u"ÑOSE".encode("utf-8")) == u"Ñose")


def section_wrapper(oracle):
    norm = oracle["g18an_normalize_sidecar_path"]
    for path in (u"groupFile", u"groupFile/Face", u"groupFile/Face/Eyes", u"groupFile/Body Morphs"):
        check("wrapper.parity %s" % path, cpm._strip_wrapper(u"groupFile", path) == norm(u"groupFile", path))
    for bad in (u"Face/Eyes", u"groupFileX/Face", u"other/groupFile/Face"):
        expect_raises("wrapper.cpm_rejects_outside %s" % bad, (cpm.CpmProjectionError,),
                      cpm._strip_wrapper, u"groupFile", bad)
        expect_raises("wrapper.g18an_rejects_outside %s" % bad, (RuntimeError,), norm, u"groupFile", bad)


def section_explicit_results():
    from sfm_master_authority_productionized import errors, resource_estimator, views
    good = {
        u"a": Hit(u"groupFile/G", [_row(u"A", u"groupFile/G"), _row(u"a", u"groupFile/G")]),
        u"b": FoldConflict([u"groupFile/G", u"groupFile/H"], [_row(u"B", u"groupFile/G"), _row(u"b", u"groupFile/H")]),
        u"c": MasterUnknown(),
    }
    prov = _FakeProvider(good)
    payload, coverage, est = cpm.build_cpm_compat_v1_projection([u"a", u"b", u"c"])(prov)
    fams = payload["families_by_fold"]
    check("explicit.hit_resolved", fams[u"a"] == _fam(u"resolved", u"G", [u"G"], [u"A", u"a"], 2), _canon(fams[u"a"]))
    check("explicit.fold_conflict_conflict",
          fams[u"b"] == _fam(u"conflict", None, [u"G", u"H"], [u"B", u"b"], 2), _canon(fams[u"b"]))
    check("explicit.master_unknown_absent", fams[u"c"] == _ABSENT)
    check("explicit.lookup_boundary_is_bytes", prov.lookup_types == [True] * 3, prov.lookup_types)
    check("explicit.coverage_statuses",
          [coverage.lookup(k).status for k in (u"a", u"b", u"c")] == [views.KNOWN, views.KNOWN, views.MASTER_UNKNOWN])
    check("explicit.estimate_positive_int", isinstance(est, int) and est > 0)

    def run(results, folds, wrapper=u"groupFile"):
        return cpm.build_cpm_compat_v1_projection(folds)(_FakeProvider(results, wrapper))

    E = (cpm.CpmProjectionError,)
    expect_raises("explicit.unknown_result_type_rejected", E, run, {u"x": Surprise()}, [u"x"])
    expect_raises("explicit.hit_without_occurrences_rejected", E, run, {u"x": Hit(u"groupFile/G", [])}, [u"x"])
    expect_raises("explicit.conflict_without_occurrences_rejected", E, run,
                  {u"x": FoldConflict([u"groupFile/G", u"groupFile/H"], [])}, [u"x"])
    expect_raises("explicit.occurrence_fold_mismatch_rejected", E, run,
                  {u"x": Hit(u"groupFile/G", [_row(u"Y", u"groupFile/G")])}, [u"x"])
    expect_raises("explicit.hit_destination_disagrees_rejected", E, run,
                  {u"x": Hit(u"groupFile/H", [_row(u"x", u"groupFile/G")])}, [u"x"])
    expect_raises("explicit.hit_spanning_two_destinations_rejected", E, run,
                  {u"x": Hit(u"groupFile/G", [_row(u"x", u"groupFile/G"), _row(u"X", u"groupFile/H")])}, [u"x"])
    expect_raises("explicit.conflict_single_destination_rejected", E, run,
                  {u"x": FoldConflict([u"groupFile/G"], [_row(u"x", u"groupFile/G"), _row(u"X", u"groupFile/G")])}, [u"x"])
    expect_raises("explicit.conflict_reported_destinations_disagree_rejected", E, run,
                  {u"x": FoldConflict([u"groupFile/G", u"groupFile/Z"], [_row(u"x", u"groupFile/G"), _row(u"X", u"groupFile/H")])}, [u"x"])
    expect_raises("explicit.path_outside_wrapper_rejected", E, run,
                  {u"x": Hit(u"elsewhere/G", [_row(u"x", u"elsewhere/G")])}, [u"x"])
    expect_raises("explicit.empty_wrapper_rejected", E, run, {u"x": MasterUnknown()}, [u"x"], u"")
    cap = resource_estimator.MAX_SINGLE_FOLD_OCCURRENCE_ROWS
    big = [_row(u"x", u"groupFile/G")] * (cap + 1)
    expect_raises("explicit.single_family_cap_enforced", (errors.ResourceAdmissionRefusal,), run,
                  {u"x": Hit(u"groupFile/G", big)}, [u"x"])


def section_builder_contract():
    E = (cpm.CpmProjectionError,)
    folds = frozenset([u"blink", u"wink"])
    builder = cpm.build_cpm_compat_v1_projection(folds)
    check("contract.declared_request_folds", builder.declared_request_folds == folds)
    check("contract.declared_request_scale", builder.declared_request_scale == 2)
    check("contract.valid_builder_accepted", cpm.validate_builder_contract(builder, folds) is None)

    def bare(provider):
        return None
    expect_raises("contract.missing_declared_folds_rejected", E, cpm.validate_builder_contract, bare, folds)
    bare.declared_request_folds = folds
    expect_raises("contract.missing_declared_scale_rejected", E, cpm.validate_builder_contract, bare, folds)
    bare.declared_request_scale = 2
    check("contract.attributes_alone_accepted", cpm.validate_builder_contract(bare, folds) is None)
    expect_raises("contract.folds_disagree_rejected", E, cpm.validate_builder_contract, builder, frozenset([u"blink"]))
    bare.declared_request_scale = 3
    expect_raises("contract.scale_disagrees_rejected", E, cpm.validate_builder_contract, bare, folds)
    expect_raises("contract.unfolded_request_rejected", E, cpm.build_cpm_compat_v1_projection, [u"Blink"])
    expect_raises("contract.unfolded_non_ascii_safe_request_rejected", E, cpm.make_request_specs, [u"ÑOSE"])
    bytes_builder = cpm.build_cpm_compat_v1_projection([b"blink"])
    check("contract.bytes_request_normalized_to_text", bytes_builder.declared_request_folds == frozenset([u"blink"]))
    specs = cpm.make_request_specs(folds)
    check("contract.request_spec_shape", list(specs.keys()) == [cpm.CONSUMER_KIND] and specs[cpm.CONSUMER_KIND][0] == folds)


def section_interpreter_units():
    E = (cpm.CpmProjectionError,)
    payload = {"contract": cpm.PAYLOAD_CONTRACT, "families_by_fold": {u"blink": EXPECTED_FAMILIES[u"blink"]}}
    ans = cpm.interpret_exact_answer(u"Blink", payload)
    check("interp.keys_match_g18an_answer_shape", sorted(ans.keys()) == sorted(cpm._ANSWER_KEYS), sorted(ans.keys()))
    ans["spellings"].append(u"MUTATED")
    ans["destinations"].append(u"MUTATED")
    check("interp.returns_copies_payload_unchanged",
          payload["families_by_fold"][u"blink"]["spellings"] == [u"BLINK", u"Blink"]
          and payload["families_by_fold"][u"blink"]["destinations"] == [u"Face/Eyes"])
    expect_raises("interp.uncovered_fold_raises_not_absent", E, cpm.interpret_exact_answer, u"Zebra", payload)
    expect_raises("interp.foreign_payload_rejected", E, cpm.interpret_exact_answer, u"Blink", {"folded": {}})


def section_identity_units():
    E = (cpm.CpmProjectionError,)
    sha_a = u"a" * 64
    sha_b = u"b" * 64
    ident = cpm.compatibility_identity(sha_a, PROD_SEMANTIC_POLICY)
    check("identity.components", ident == (cpm.COMPATIBILITY_IDENTITY_SCHEMA, sha_a, cpm.CONSUMER_KIND, PROD_SEMANTIC_POLICY),
          _canon(list(ident)))
    check("identity.deterministic", ident == cpm.compatibility_identity(sha_a.upper(), PROD_SEMANTIC_POLICY))
    check("identity.changes_with_master_sha", ident != cpm.compatibility_identity(sha_b, PROD_SEMANTIC_POLICY))
    check("identity.changes_with_policy", ident != cpm.compatibility_identity(sha_a, u"another-policy-v2"))
    check("identity.changes_with_projection",
          ident != cpm.compatibility_identity(sha_a, PROD_SEMANTIC_POLICY, "cpm_compat_v2"))
    expect_raises("identity.short_sha_rejected", E, cpm.compatibility_identity, u"abc", PROD_SEMANTIC_POLICY)
    expect_raises("identity.non_hex_sha_rejected", E, cpm.compatibility_identity, u"g" * 64, PROD_SEMANTIC_POLICY)
    expect_raises("identity.empty_policy_rejected", E, cpm.compatibility_identity, sha_a, u"")


def _master_sha():
    with open(MASTER_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _new_broker(label):
    from sfm_master_authority_productionized import broker as broker_mod
    return broker_mod.Broker(api_version="cpm-compat-v1-suite1-%s" % label)


def _acquire(b, specs):
    return b.acquire_or_reuse_views(MASTER_PATH, specs, shipped_root=FIXTURE_DIR, expected_generation=_master_sha())


def _payload_snapshot(payload):
    return json.dumps(payload, sort_keys=True)


def section_real_broker(oracle):
    from sfm_master_authority_productionized import sidecar_contract, views
    sidecar_contract.ensure_loaded()
    sha = _master_sha()
    folds = cpm.request_folds_for_literals(QUERY_LITERALS)
    check("broker.request_fold_count", len(folds) == 12, len(folds))
    check("broker.request_folds_are_text", all(isinstance(k, _TEXT) for k in folds))

    b = _new_broker("main")
    views_a = _acquire(b, cpm.make_request_specs(folds))
    view = views_a[cpm.CONSUMER_KIND]
    check("broker.view_acquired", view is not None)
    check("broker.provider_closed_after_acquire", b.provider_counters()["current_open_provider_count"] == 0)
    check("broker.validate_view_passes", cpm.validate_view(view, folds) is None)
    check("broker.cache_key_uses_text_folds", view.cache_key() == (sha, None, folds, cpm.CONSUMER_KIND))

    # Payload boundary
    payload = view.payload
    check("payload.top_level_keys", sorted(payload.keys()) == ["contract", "families_by_fold"], sorted(payload.keys()))
    check("payload.family_keys", all(sorted(f.keys()) == sorted(cpm._FAMILY_KEYS) for f in payload["families_by_fold"].values()))
    dump = _payload_snapshot(payload)
    check("payload.no_request_spelling_fields", "query_literal" not in dump and "match_kind" not in dump)
    check("payload.no_master_sha", sha not in dump)
    check("payload.families_match_hand_audit",
          _canon(payload["families_by_fold"]) == _canon(EXPECTED_FAMILIES), _canon(payload["families_by_fold"]))

    # Coverage
    check("coverage.keys_equal_request", view.coverage.covered_keys() == folds)
    check("coverage.compact_no_occurrences",
          all(view.coverage.lookup(k).occurrences is None for k in folds))
    check("coverage.absent_is_master_unknown",
          all((view.coverage.lookup(k).status == views.MASTER_UNKNOWN) == (EXPECTED_FAMILIES[k]["status"] == u"absent")
              for k in folds))
    expect_raises("coverage.uncovered_request_rejected", (cpm.CpmProjectionError,),
                  cpm.validate_view, view, folds | frozenset([u"zebra"]))
    expect_raises("coverage.wrong_consumer_kind_rejected", (cpm.CpmProjectionError,),
                  cpm.validate_view, view, folds, "cpm_compat_v2")

    # Estimate
    est = cpm.estimate_retained_bytes(payload, view.coverage)
    check("estimate.view_charged_with_estimate", view.estimated_bytes == est, [view.estimated_bytes, est])
    check("estimate.exceeds_payload_walk", est > cpm._walk(payload), [est, cpm._walk(payload)])
    check("estimate.value", True, est)

    # Answers vs hand audit
    answers = cpm.interpret_exact_answers(QUERY_LITERALS, payload)
    for literal in QUERY_LITERALS:
        fam = EXPECTED_FAMILIES[cpm.cpm_fold(literal)]
        expected = dict(fam)
        expected["query_literal"] = literal
        expected["match_kind"] = EXPECTED_MATCH_KIND[literal]
        tag = literal.encode("unicode_escape").decode("ascii")
        check("answer.hand_audit %s" % tag, _canon(answers[literal]) == _canon(expected), _canon(answers[literal]))
    expect_raises("answer.uncovered_literal_raises", (cpm.CpmProjectionError,),
                  cpm.interpret_exact_answer, u"Zebra", payload)

    # G18AN Hit/MasterUnknown parity, via a probe builder under a real broker
    oracle_answers = {}
    oracle_rejections = []
    by_fold = {}
    for literal in QUERY_LITERALS:
        by_fold.setdefault(cpm.cpm_fold(literal), []).append(literal)
    answer_fn = oracle["_answer_from_result"]

    def probe(provider):
        me = _OracleSelf(provider.wrapper_path())
        entries = {}
        for folded in sorted(folds):
            result = provider.lookup_fold(cpm.fold_to_lookup_bytes(folded))
            for literal in by_fold[folded]:
                if type(result).__name__ == "FoldConflict":
                    try:
                        answer_fn(me, literal, result)
                        oracle_rejections.append((literal, False))
                    except RuntimeError:
                        oracle_rejections.append((literal, True))
                else:
                    oracle_answers[literal] = answer_fn(me, literal, result)
            entries[folded] = views.CoverageResult(views.MASTER_UNKNOWN, None, None)
        return {"probe": True}, views.CoverageDescriptor(entries), 1024
    probe.declared_request_folds = folds
    probe.declared_request_scale = len(folds)
    b_probe = _new_broker("oracle-probe")
    _acquire(b_probe, {"cpm_oracle_probe": (folds, probe)})
    check("oracle.probe_provider_closed", b_probe.provider_counters()["current_open_provider_count"] == 0)
    conflict_literals = [l for l in QUERY_LITERALS if EXPECTED_FAMILIES[cpm.cpm_fold(l)]["status"] == u"conflict"]
    check("oracle.g18an_rejects_fold_conflict",
          sorted(oracle_rejections) == sorted((l, True) for l in conflict_literals), _canon(sorted(oracle_rejections)))
    parity_literals = [l for l in QUERY_LITERALS if l not in conflict_literals]
    check("oracle.hit_and_unknown_covered", sorted(oracle_answers.keys()) == sorted(parity_literals))
    for literal in parity_literals:
        tag = literal.encode("unicode_escape").decode("ascii")
        check("oracle.g18an_answer_parity %s" % tag,
              _canon(answers[literal]) == _canon(oracle_answers.get(literal)), _canon(oracle_answers.get(literal)))

    # Compatibility identity / descriptor across brokers
    b2 = _new_broker("second")
    view2 = _acquire(b2, cpm.make_request_specs(folds))[cpm.CONSUMER_KIND]
    id1 = cpm.compatibility_identity_for_view(view, PROD_SEMANTIC_POLICY)
    id2 = cpm.compatibility_identity_for_view(view2, PROD_SEMANTIC_POLICY)
    check("identity.equal_across_brokers", id1 == id2, _canon(list(id1)))
    check("identity.payload_equal_across_brokers", _payload_snapshot(view.payload) == _payload_snapshot(view2.payload))
    d1 = cpm.provider_capture_descriptor(view)
    d2 = cpm.provider_capture_descriptor(view2)
    stable = ("provider_contract", "source_sha256", "fold_policy", "provider_generation", "projection_contract")
    check("descriptor.stable_fields_equal_across_brokers", all(d1[k] == d2[k] for k in stable))
    check("descriptor.g18an_capture_fields",
          d1["provider_contract"] == oracle["SEMANTIC_PROVIDER_CONTRACT"]
          and d1["fold_policy"] == oracle["SEMANTIC_PROVIDER_FOLD_POLICY"]
          and d1["source_sha256"] == sha and isinstance(d1["provider_generation"], int))
    check("descriptor.cohort_only_in_diagnostics",
          sorted(d1.keys()) == sorted(stable + ("diagnostics",)) and "broker_cohort_id" in d1["diagnostics"])

    # Same-fold / different-literal reuse (handoff section 20)
    before = _payload_snapshot(view.payload)
    lease_a = b.lease_view(view)
    ans_a = cpm.interpret_exact_answer(u"Blink", view.payload)
    b.release_view_lease(lease_a)
    opens_before = b.provider_counters()["total_provider_opens"]
    reused = _acquire(b, cpm.make_request_specs(folds))[cpm.CONSUMER_KIND]
    check("reuse.same_view_object", reused is view)
    check("reuse.no_provider_open", b.recent_diagnostics()[-1]["event"] == "fully_reused_no_provider_open"
          and b.provider_counters()["total_provider_opens"] == opens_before)
    lease_b = b.lease_view(reused)
    ans_b = cpm.interpret_exact_answer(u"bLiNk", reused.payload)
    b.release_view_lease(lease_b)
    check("reuse.literal_a_exact", ans_a["match_kind"] == u"exact" and ans_a["query_literal"] == u"Blink")
    check("reuse.literal_b_folded", ans_b["match_kind"] == u"ascii-fold" and ans_b["query_literal"] == u"bLiNk")
    check("reuse.same_family_facts",
          all(ans_a[k] == ans_b[k] for k in cpm._FAMILY_KEYS))
    check("reuse.payload_unchanged", _payload_snapshot(reused.payload) == before)
    check("reuse.leases_released", b.outstanding_lease_count() == 0)
    check("reuse.provider_closed", b.provider_counters()["current_open_provider_count"] == 0)

    # v1 / v2 separation
    opens_before = b.provider_counters()["total_provider_opens"]
    v2 = _acquire(b, {"cpm_compat_v2": (folds, cpm.build_cpm_compat_v1_projection(folds))})["cpm_compat_v2"]
    check("separation.v2_not_v1_view", v2 is not view and v2.consumer_kind == "cpm_compat_v2")
    check("separation.v2_opened_provider", b.provider_counters()["total_provider_opens"] == opens_before + 1)
    check("separation.v1_still_reusable", _acquire(b, cpm.make_request_specs(folds))[cpm.CONSUMER_KIND] is view)

    # Fail closed: an unsupported provider result publishes nothing
    b3 = _new_broker("fail-closed")
    real_builder = cpm.build_cpm_compat_v1_projection(folds)

    def poisoned(provider):
        return real_builder(_PoisonProvider(provider, cpm.fold_to_lookup_bytes(u"wink")))
    poisoned.declared_request_folds = folds
    poisoned.declared_request_scale = len(folds)
    expect_raises("failclosed.builder_error_propagates", (cpm.CpmProjectionError,),
                  _acquire, b3, {cpm.CONSUMER_KIND: (folds, poisoned)})
    counters = b3.provider_counters()
    check("failclosed.nothing_published", b3.view_cache_entry_count() == 0)
    check("failclosed.provider_closed",
          counters["current_open_provider_count"] == 0 and counters["total_provider_opens"] == counters["total_provider_closes"])


def run_suite():
    oracle = load_g18an_oracle()
    section_fold(oracle)
    section_wrapper(oracle)
    section_explicit_results()
    section_builder_contract()
    section_interpreter_units()
    section_identity_units()
    section_real_broker(oracle)


def write_digest(path):
    records = [[name, ok, _canon(value)] for name, ok, value in RESULTS]
    body = json.dumps(records, sort_keys=True, ensure_ascii=True, indent=0, separators=(",", ":"))
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_TEXT(body))
    print("digest: %s sha256=%s checks=%d" % (os.path.basename(path),
                                              hashlib.sha256(body.encode("utf-8")).hexdigest(), len(records)))


def _require_setup_checks():
    if not all(r[1] for r in RESULTS):
        print("RESULT: setup failed")
        sys.exit(1)
    del RESULTS[:]


def phase_publish():
    import shutil
    if os.path.isdir(FIXTURE_DIR):
        shutil.rmtree(FIXTURE_DIR)
    os.makedirs(FIXTURE_DIR)
    with open(MASTER_PATH, "wb") as f:
        f.write(MASTER_BODY.encode("utf-8"))
    from sfm_master_sidecar import publisher
    result = publisher.publish(MASTER_PATH, FIXTURE_DIR)
    check("publish.artifact_published", os.path.isfile(str(result.generation_path)))
    check("publish.source_sha_matches", result.source_sha256 == _master_sha())
    _require_setup_checks()  # setup checks are not part of the cross-interpreter digest
    run_suite()
    write_digest(DIGEST_PY3)


def phase_suite():
    check("suite.fixture_present", os.path.isfile(MASTER_PATH) and os.path.isfile(DIGEST_PY3))
    _require_setup_checks()
    run_suite()
    write_digest(DIGEST_PY27 if PY2 else DIGEST_PY3 + ".rerun")


def phase_compare():
    with io.open(DIGEST_PY3, encoding="utf-8") as f:
        a = f.read()
    with io.open(DIGEST_PY27, encoding="utf-8") as f:
        b = f.read()
    ra, rb = json.loads(a), json.loads(b)
    check("compare.same_check_count", len(ra) == len(rb), [len(ra), len(rb)])
    diffs = [x[0] for x, y in zip(ra, rb) if x != y]
    check("compare.identical_results_and_values", a == b, diffs[:10])
    check("compare.all_pass_both", all(x[1] for x in ra) and all(y[1] for y in rb))
    print("py3 digest sha256=%s" % hashlib.sha256(a.encode("utf-8")).hexdigest())
    print("py27 digest sha256=%s" % hashlib.sha256(b.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    phase = None
    for arg in sys.argv[1:]:
        if arg.startswith("--phase="):
            phase = arg.split("=", 1)[1]
    if phase not in ("publish", "suite", "compare"):
        print("usage: %s --phase=publish|suite|compare" % os.path.basename(sys.argv[0]))
        sys.exit(2)
    print("Interpreter: %s" % sys.version.split()[0])
    print("Phase: %s" % phase)
    {"publish": phase_publish, "suite": phase_suite, "compare": phase_compare}[phase]()
    passed = sum(1 for r in RESULTS if r[1])
    print("\nRESULT: %d/%d %s" % (passed, len(RESULTS), "ALL PASS" if passed == len(RESULTS) else "SOME FAILED"))
    if passed != len(RESULTS):
        sys.exit(1)
