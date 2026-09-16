# -*- coding: utf-8 -*-
"""R3-B2F1F: collect exact 'actual_authoritative_retained_charge' (the
EXISTING system's own post-build AggregateLedger estimate, computed by
the real, unmodified acquire_or_reuse_views path) for every known
fixture -- used ONLY as a calibration/no-underestimation target for the
new pure offline pre-admission estimator. No frozen file modified.
"""
import json
import sys

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
GATE_R2_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)
from sfm_master_authority import broker as broker_mod, projections, errors as authority_errors  # noqa: E402

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
RESULTS_DIR = r"C:\Users\Public\Documents"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"
REAL_MASTER_PATH = r"E:\SFM Animation Group Master\sfm_defaultanimationgroups.txt"
REAL_OFFICIAL_ARTIFACT = GATE_R2_DIR + r"\official_sidecar_artifact.bin"

REAL_LITERALS_FOR_PROJECTION = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
GENEROUS_CAP = 64 * 1024 * 1024  # generous cap so oversized fixtures still let us measure their true payload cost


def main():
    import os
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    targets = [{"name": "official_control", "master_path": REAL_MASTER_PATH,
                "shipped_root": os.path.join(RESULTS_DIR, "%s_stage_official" % HARNESS_TEST_ID)}]
    for m in manifest:
        targets.append({
            "name": m["name"], "master_path": m["master_path"],
            "shipped_root": os.path.join(RESULTS_DIR, "%s_stage_%s" % (HARNESS_TEST_ID, m["name"])),
            "sidecar_bytes": m["sidecar_bytes"],
        })

    out = {}
    for t in targets:
        b = broker_mod.Broker(api_version="b2f1f-ground-truth-%s" % t["name"])
        normalizer_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_LITERALS_FOR_PROJECTION),
            projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION),
        )
        try:
            b.acquire_or_reuse_views(
                t["master_path"], {"normalizer": normalizer_spec},
                shipped_root=t["shipped_root"], runtime_cap_bytes=GENEROUS_CAP,
            )
            ledger = b.ledger_snapshot()
            out[t["name"]] = {"outcome": "accepted", "retained_detached_views": ledger["retained_detached_views"]}
        except authority_errors.BrokerError as exc:
            detail = str(exc)
            # ViewAdmissionRefused messages embed the exact estimated byte
            # count that triggered refusal -- extract it as the
            # "authoritative" figure for calibration purposes.
            import re
            match = re.search(r"admitting a (\d+)-byte view", detail)
            estimated = int(match.group(1)) if match else None
            out[t["name"]] = {"outcome": "refused", "type": type(exc).__name__,
                               "detail": detail, "estimated_bytes_from_refusal": estimated}
        print(t["name"], "->", out[t["name"]])

    with open(RESULTS_DIR + r"\b2f1f_ground_truth.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote", RESULTS_DIR + r"\b2f1f_ground_truth.json")


if __name__ == "__main__":
    main()
