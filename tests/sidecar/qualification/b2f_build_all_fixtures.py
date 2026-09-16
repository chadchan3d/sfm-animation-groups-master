# -*- coding: utf-8 -*-
"""R3-B2F: build the full calibrated fixture ladder (3 families x 4 size
points = 12 fixtures), record full structural metrics, and write a JSON
manifest. Every fixture is compiled via the real production pipeline and
self-validated (production-reader exhaustive parity) before being
recorded -- an invalid artifact is never written to the manifest as a
usable fixture.
"""
import json
import os
import sys

sys.path.insert(0, r".")
from generate_fixtures import build_and_measure, FIXROOT

CONFIGS = {
    "A": dict(
        family="A", root_groups=6, depth=3, groups_per_level=4,
        literal_len=200, metadata_len=100, metadata_per_group=2, distinct_literal_pool=100000,
        controls_per_leaf_points={"1.0x": 219, "1.25x": 274, "1.5x": 329, "2.0x": 437},
    ),
    "B": dict(
        family="B", root_groups=6, depth=3, groups_per_level=4,
        literal_len=12, metadata_len=8, metadata_per_group=1, distinct_literal_pool=300000,
        controls_per_leaf_points={"1.0x": 1261, "1.25x": 1576, "1.5x": 1892, "2.0x": 2522},
    ),
    "C": dict(
        family="C", root_groups=8, depth=5, groups_per_level=4,
        literal_len=20, metadata_len=280, distinct_literal_pool=19000,
        hot_literal_fraction=0.3, hot_literal_len=20, controls_per_leaf=93,
        # Recalibrated after discovering (and fixing, in generate_fixtures.py)
        # that metadata values were being deduped to one-per-group by the
        # string pool -- see report Section 3/4 for the exact finding.
        metadata_per_group_points={"1.0x": 4, "1.25x": 7, "1.5x": 10, "2.0x": 15},
    ),
}

all_metrics = []

for point in ("1.0x", "1.25x", "1.5x", "2.0x"):
    cfg = CONFIGS["A"]
    params = dict(
        family="A", root_groups=cfg["root_groups"], depth=cfg["depth"], groups_per_level=cfg["groups_per_level"],
        controls_per_leaf=cfg["controls_per_leaf_points"][point],
        literal_len=cfg["literal_len"], metadata_len=cfg["metadata_len"], metadata_per_group=cfg["metadata_per_group"],
        distinct_literal_pool=cfg["distinct_literal_pool"],
    )
    m = build_and_measure("fixtureA_%s" % point.replace(".", "p"), params)
    m["family"] = "A"
    m["target_ratio"] = point
    all_metrics.append(m)

for point in ("1.0x", "1.25x", "1.5x", "2.0x"):
    cfg = CONFIGS["B"]
    params = dict(
        family="B", root_groups=cfg["root_groups"], depth=cfg["depth"], groups_per_level=cfg["groups_per_level"],
        controls_per_leaf=cfg["controls_per_leaf_points"][point],
        literal_len=cfg["literal_len"], metadata_len=cfg["metadata_len"], metadata_per_group=cfg["metadata_per_group"],
        distinct_literal_pool=cfg["distinct_literal_pool"],
    )
    m = build_and_measure("fixtureB_%s" % point.replace(".", "p"), params)
    m["family"] = "B"
    m["target_ratio"] = point
    all_metrics.append(m)

for point in ("1.0x", "1.25x", "1.5x", "2.0x"):
    cfg = CONFIGS["C"]
    params = dict(
        family="C", root_groups=cfg["root_groups"], depth=cfg["depth"], groups_per_level=cfg["groups_per_level"],
        controls_per_leaf=cfg["controls_per_leaf"],
        literal_len=cfg["literal_len"], metadata_len=cfg["metadata_len"],
        metadata_per_group=cfg["metadata_per_group_points"][point],
        distinct_literal_pool=cfg["distinct_literal_pool"],
        hot_literal_fraction=cfg["hot_literal_fraction"], hot_literal_len=cfg["hot_literal_len"],
    )
    m = build_and_measure("fixtureC_%s" % point.replace(".", "p"), params)
    m["family"] = "C"
    m["target_ratio"] = point
    all_metrics.append(m)

manifest_path = os.path.join(FIXROOT, "fixture_manifest.json")
with open(manifest_path, "w") as f:
    json.dump(all_metrics, f, indent=2)
print("\nwrote manifest:", manifest_path)
print("total fixtures:", len(all_metrics))
