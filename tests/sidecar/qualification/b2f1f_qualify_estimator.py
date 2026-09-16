# -*- coding: utf-8 -*-
"""R3-B2F1F Stage F1/F2: qualification matrix + monotonicity/boundary
tests for the pure ResourceShape estimator. No frozen file touched;
pure offline computation.
"""
import json
import os
import sys

sys.path.insert(0, r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\67454949-e69f-4280-93d9-87c1f4464330\scratchpad")
from b2f1f_resource_shape_estimator import (  # noqa: E402
    parse_resource_shape, preflight_region_size, estimate_retained, estimate_transient,
    PreflightCorruptOrIncompatible, ResourceShape, ESTIMATOR_MODEL_VERSION,
    fmt,
)

MiB = 1048576.0
RUNTIME_CAP_16MIB = 16 * 1024 * 1024
RUNTIME_CAP_64MIB = 64 * 1024 * 1024

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
OFFICIAL_ARTIFACT = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r2_formal_deploy\official_sidecar_artifact.bin"
)
GROUND_TRUTH_PATH = r"C:\Users\Public\Documents\b2f1f_ground_truth.json"

# Real-SFM/phase-isolation transient measurements (peak_pagefile delta from
# a clean baseline), recorded exactly as reported in prior B2F/B2F1x
# reports -- used ONLY to confirm no underestimation, never to fit
# coefficients.
KNOWN_TRANSIENT_DELTAS_BYTES = {
    "fixtureA_1p5x": 21753856,  # B2F1E phase-isolation harness, peak_pf delta from P0
    "fixtureB_1p5x": 27017216,
    "fixtureC_1p25x_offline": 40681472,  # B2F1E phase-isolation harness (fresh python.exe process)
    "fixtureC_1p25x_real_sfm": 38858752,  # real-SFM Run 4, S3-baseline peak_pagefile delta
}


def shape_from_artifact(path):
    with open(path, "rb") as f:
        header_bytes = f.read(fmt.HEADER_SIZE)
        region_size = preflight_region_size(header_bytes)
        f.seek(0)
        prefix = f.read(region_size)
    artifact_bytes = os.path.getsize(path)
    return parse_resource_shape(prefix, artifact_bytes)


def main():
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    with open(GROUND_TRUTH_PATH) as f:
        ground_truth = json.load(f)

    targets = [{"name": "official_control", "artifact_path": OFFICIAL_ARTIFACT}]
    for m in manifest:
        targets.append({"name": m["name"], "artifact_path": m["artifact_path"]})

    print("estimator_model_version:", ESTIMATOR_MODEL_VERSION)
    print()
    header = "%-18s %8s %8s %10s %10s %14s %14s %8s   %14s %14s %8s   %s" % (
        "fixture", "groups", "meta", "art_bytes", "gt_out", "gt_retained", "est_retained",
        "ret_ok", "gt_transient", "est_transient", "tr_ok", "admit@16MiB",
    )
    print(header)
    print("-" * len(header))

    rows = []
    any_underestimate = False
    for t in targets:
        shape = shape_from_artifact(t["artifact_path"])
        est_retained = estimate_retained(shape)
        est_transient_16 = estimate_transient(shape, RUNTIME_CAP_16MIB)

        gt = ground_truth.get(t["name"], {})
        if gt.get("outcome") == "accepted":
            gt_retained = gt["retained_detached_views"]
        elif gt.get("outcome") == "refused":
            gt_retained = gt.get("estimated_bytes_from_refusal")
        else:
            gt_retained = None

        ret_ok = "n/a"
        if gt_retained is not None:
            ret_ok = "PASS" if est_retained >= gt_retained else "**UNDERESTIMATE**"
            if est_retained < gt_retained:
                any_underestimate = True

        gt_transient = None
        if t["name"] == "fixtureA_1p5x":
            gt_transient = KNOWN_TRANSIENT_DELTAS_BYTES["fixtureA_1p5x"]
        elif t["name"] == "fixtureB_1p5x":
            gt_transient = KNOWN_TRANSIENT_DELTAS_BYTES["fixtureB_1p5x"]
        elif t["name"] == "fixtureC_1p25x":
            gt_transient = max(
                KNOWN_TRANSIENT_DELTAS_BYTES["fixtureC_1p25x_offline"],
                KNOWN_TRANSIENT_DELTAS_BYTES["fixtureC_1p25x_real_sfm"],
            )

        tr_ok = "n/a"
        if gt_transient is not None:
            tr_ok = "PASS" if est_transient_16 >= gt_transient else "**UNDERESTIMATE**"
            if est_transient_16 < gt_transient:
                any_underestimate = True

        raw_admits_16 = shape.artifact_bytes <= RUNTIME_CAP_16MIB
        retained_admits = est_retained <= 16777216
        transient_admits = est_transient_16 <= 33554432
        admit_16 = "ADMIT" if (raw_admits_16 and retained_admits and transient_admits) else (
            "REFUSE(raw_cap)" if not raw_admits_16 else
            "REFUSE(retained)" if not retained_admits else "REFUSE(transient)"
        )

        print("%-18s %8d %8d %10d %10s %14s %14d %8s   %14s %14d %8s   %s" % (
            t["name"], shape.group_count, shape.metadata_count, shape.artifact_bytes,
            gt.get("outcome", "?"), gt_retained if gt_retained is not None else "-", est_retained, ret_ok,
            gt_transient if gt_transient is not None else "-", est_transient_16, tr_ok, admit_16,
        ))
        rows.append({
            "name": t["name"], "shape": shape.__repr__(), "est_retained": est_retained,
            "gt_retained": gt_retained, "est_transient_16mib": est_transient_16,
            "gt_transient": gt_transient, "admit_at_16mib": admit_16,
        })

    print()
    print("ANY UNDERESTIMATE ACROSS CORPUS:", any_underestimate)

    with open(r"C:\Users\Public\Documents\b2f1f_qualification_matrix.json", "w") as f:
        json.dump(rows, f, indent=2)
    return any_underestimate


if __name__ == "__main__":
    underestimate = main()
    sys.exit(1 if underestimate else 0)
