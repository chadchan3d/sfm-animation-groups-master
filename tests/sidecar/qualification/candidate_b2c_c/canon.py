# -*- coding: utf-8 -*-
"""Canonicalization for hashing plan-layer outputs. Recursively
converts any `set`/`frozenset` into a SORTED list (never trusts raw set
iteration order, which is hash-seed-dependent) before handing off to
`json.dumps(..., sort_keys=True)`. No object addresses or timestamps
ever appear in these structures (verified: `classify_production`/
`order_candidate_rows_by_policy`/`derive_generic_uniformity_plan`/
`preflight_reconciliation_plan_pure` return only plain dict/list/str/
int/bool/None values -- no live object references, by construction of
the plan-layer scope decision itself)."""
import hashlib
import json


def _canon(obj):
    if isinstance(obj, (set, frozenset)):
        return sorted(_canon(x) for x in obj)
    if isinstance(obj, dict):
        return dict((k, _canon(v)) for k, v in obj.items())
    if isinstance(obj, (list, tuple)):
        return [_canon(x) for x in obj]
    return obj


def canonical_json(obj):
    canon = _canon(obj)
    s = json.dumps(canon, sort_keys=True, ensure_ascii=True, separators=(",", ":"), default=repr)
    return s


def sha_of(obj):
    s = canonical_json(obj)
    try:
        text_type = unicode  # noqa: F821 -- Python 2 only
    except NameError:
        text_type = str
    if isinstance(s, text_type):
        s = s.encode("utf-8")
    return hashlib.sha256(s).hexdigest()
