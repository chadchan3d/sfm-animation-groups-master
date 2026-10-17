# -*- coding: utf-8 -*-
"""TEST-ONLY consumer-library check under SFM's bundled Python 2.7, run OUTSIDE SFM, read-only,
with -B (ported from P1 p1py27.py 03a0a32c...). The controller places this script next to a
hash-verified, .py-only copy of the unchanged production authority package
(tests/sidecar/qualification/candidate_b2c_correction6/sfm_master_authority_productionized),
tools/sfm_master_sidecar and tools/sfm_master_core.py, so no pre-existing bytecode is loaded.
This qualifies these library paths only -- not Qt, not embedded SFM, not either consumer's UI.

  py27_select.py select <cfg> <out.json>
      observe_master(<cfg>\\sfm_defaultanimationgroups.txt) -> select_sidecar_candidate(
      shipped_root=<cfg>\\sfm_shared_authority) exactly as consumers do.
"""
import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sfm_master_authority_productionized import observation, selection, errors  # noqa: E402


def select(cfg):
    master = os.path.join(cfg, "sfm_defaultanimationgroups.txt")
    auth = os.path.join(cfg, "sfm_shared_authority")
    out = {"python": sys.version.split()[0], "master": os.path.basename(master),
           "package": os.path.dirname(observation.__file__)}
    try:
        h0 = observation.observe_master(master)
        out["observed_sha256"] = h0.sha256
    except errors.MasterUnreadable as e:
        out["classification"] = "MasterUnreadable"
        out["detail"] = str(e)[-300:]
        return out
    diags = []
    try:
        sel = selection.select_sidecar_candidate(h0, shipped_root=auth, diagnostics=diags)
        out["classification"] = "SELECTED"
        out["selected_basename"] = os.path.basename(sel.artifact_path) if hasattr(sel, "artifact_path") else None
        if out["selected_basename"] is None:
            for k in ("path", "candidate_path"):
                if hasattr(sel, k):
                    out["selected_basename"] = os.path.basename(getattr(sel, k))
        try:
            if getattr(sel, "provider", None) is not None:
                sel.provider.close()
        except Exception:
            pass
    except Exception as e:
        out["classification"] = type(e).__name__
        out["detail"] = str(e)[-300:]
    out["diagnostics"] = [
        dict((k, (os.path.basename(v) if k == "candidate_path" else str(v)[:400]))
             for k, v in d.items()) if isinstance(d, dict) else str(d)[:400] for d in diags]
    return out


def main(argv):
    op, cfg, dst = argv[0], argv[1], argv[2]
    try:
        res = select(cfg) if op == "select" else {"error": "unknown op"}
    except Exception:
        res = {"error": traceback.format_exc()[-1500:]}
    with open(dst, "w") as f:
        json.dump(res, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
