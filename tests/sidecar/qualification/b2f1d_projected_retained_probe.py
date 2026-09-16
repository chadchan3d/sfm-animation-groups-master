# -*- coding: utf-8 -*-
"""R3-B2F1D Section 1: recompute the CURRENT exact projected/logical
retained-view charge for fixtureC_1p25x offline (no real SFM needed --
the aggregate ledger's retained_detached_views figure is a pure-Python
logical estimate computed by memory_accounting.py/views.py, not an OS
memory measurement). Uses a FRESH Broker, the real acquire_or_reuse_views
path, against fixtureC_1p25x's own staged artifact -- same call pattern
Run 4 will use, under the 16 MiB cap. Does not require SFM.
"""
import json
import sys

B2A_DEPLOY_DIR = (
    r"E:\SteamLibrary\steamapps\common\SourceFilmmaker\game\usermod\scripts\sfm"
    r"\gate_r3_b2a_broker_deploy"
)
sys.path.insert(0, B2A_DEPLOY_DIR)
from sfm_master_authority import broker as broker_mod, projections, errors as authority_errors  # noqa: E402

MANIFEST_PATH = (
    r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master"
    r"\scratch_r3b2f\fixtures\fixture_manifest.json"
)
RESULTS_DIR = r"C:\Users\Public\Documents"
HARNESS_TEST_ID = "CGN_R3_B2F_CustomSidecarResourceQualification_Harness_01"

REAL_LITERALS_FOR_PROJECTION = ["left", "right", "Left PupilDown", "Right PupilDown", "Left PupilGrow"]
REAL_CSP_VOCAB_FOR_PROJECTION = ["Left PupilLeft", "Right PupilLeft", "Left PupilRight"]

RUNTIME_CAP_BYTES = 16 * 1024 * 1024


def main():
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    m = next(x for x in manifest if x["name"] == "fixtureC_1p25x")

    import os
    stage_dir = os.path.join(RESULTS_DIR, "%s_stage_fixtureC_1p25x" % HARNESS_TEST_ID)
    fx = {"master_path": m["master_path"], "shipped_root": stage_dir, "sidecar_bytes": m["sidecar_bytes"]}

    b = broker_mod.Broker(api_version="b2f1d-offline-projection-probe")

    normalizer_spec = (
        frozenset(projections._ascii_fold(l) for l in REAL_LITERALS_FOR_PROJECTION),
        projections.build_normalizer_like_projection(REAL_LITERALS_FOR_PROJECTION),
    )
    try:
        views1 = b.acquire_or_reuse_views(
            fx["master_path"], {"normalizer": normalizer_spec},
            shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_BYTES,
        )
        outcome1 = "accepted"
        detail1 = None
    except authority_errors.BrokerError as exc:
        outcome1 = "refused"
        detail1 = "%s: %s" % (type(exc).__name__, exc)

    print("=== after Normalizer acquisition ===")
    print("outcome:", outcome1, detail1)
    print("ledger_snapshot:", json.dumps(b.ledger_snapshot(), indent=2))
    print("provider_counters:", b.provider_counters())
    print("view_cache_entry_count:", b.view_cache_entry_count())

    if outcome1 == "accepted":
        csp_spec = (
            frozenset(projections._ascii_fold(l) for l in REAL_CSP_VOCAB_FOR_PROJECTION),
            projections.build_character_preset_like_projection(REAL_CSP_VOCAB_FOR_PROJECTION),
        )
        try:
            views2 = b.acquire_or_reuse_views(
                fx["master_path"], {"csp": csp_spec},
                shipped_root=fx["shipped_root"], runtime_cap_bytes=RUNTIME_CAP_BYTES,
            )
            outcome2 = "accepted"
            detail2 = None
        except authority_errors.BrokerError as exc:
            outcome2 = "refused"
            detail2 = "%s: %s" % (type(exc).__name__, exc)

        print()
        print("=== after CSP acquisition (S5-equivalent) ===")
        print("outcome:", outcome2, detail2)
        ledger = b.ledger_snapshot()
        print("ledger_snapshot:", json.dumps(ledger, indent=2))
        print("provider_counters:", b.provider_counters())
        print("view_cache_entry_count:", b.view_cache_entry_count())
        total = sum(ledger.values())
        print()
        print("TOTAL logical retained charge (sum of all ledger categories):", total)
        print("16 MiB retained gate:", 16 * 1024 * 1024)
        print("distance below gate:", 16 * 1024 * 1024 - total)
        print("PASS" if total <= 16 * 1024 * 1024 else "FAIL", "vs retained gate")


if __name__ == "__main__":
    main()
