# -*- coding: utf-8 -*-
"""R3-B2F Section 3/4: synthetic enlarged Master fixture generator, using
ONLY the real production compiler pipeline (sfm_master_core +
sfm_master_sidecar.writer, via compiler.py) to produce genuinely valid
artifacts -- never a hand-crafted binary. Every fixture is compiled,
self-validated (production reader parity), and additionally validated
through the FINAL R3-A2B contract before being accepted as a usable
resource-test fixture.
"""
import hashlib
import json
import os
import sys

TOOLS_DIR = r"E:\SFM Animation Group Master\tools"
sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, r"E:\SFM Animation Group Master")

from sfm_master_sidecar import compiler, mutex_publisher  # noqa: E402
import sfm_master_core as core  # noqa: E402

FIXROOT = r"C:\Users\Eman\AppData\Local\Temp\claude\E--SFM-Animation-Group-Master\scratch_r3b2f\fixtures"
os.makedirs(FIXROOT, exist_ok=True)

REAL_ARTIFACT_BYTES = 9506244
REAL_MASTER_SHA = "ac45e5c1cd45d55b3af95747c97d2f8e93eda4f4fe4fec63e97d62828c904d93"


def _quote(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def build_master_text(
    family, root_groups, depth, groups_per_level, controls_per_leaf,
    literal_len, metadata_len, metadata_per_group, distinct_literal_pool,
    hot_literal_fraction=0.0, hot_literal_len=None,
):
    """Deterministic synthetic Master generator. Builds a single
    `groupFile { ... }` wrapper containing `root_groups` top-level groups,
    each recursively nested to `depth` levels with `groups_per_level`
    children per level; leaf groups get `controls_per_leaf` control
    occurrences plus `metadata_per_group` metadata entries.

    Literal generation: a pool of `distinct_literal_pool` distinct base
    literals (each `literal_len` characters) is cycled through for control
    occurrences -- reusing the SAME literal at multiple destinations
    deliberately creates ASCII-fold families spanning >1 destination
    (still valid grammar/semantics; `writer.compile_sidecar` represents
    fold conflicts, never rejects them). `hot_literal_fraction`, if > 0,
    additionally forces that fraction of ALL occurrences to reuse ONE
    single shared "hot" literal (`hot_literal_len` characters) -- this is
    Fixture C's large-fold-family-cardinality stress lever.
    """
    lines = []
    lines.append("groupFile")
    lines.append("{")

    literal_counter = [0]
    group_counter = [0]
    occ_counter = [0]

    def make_literal(idx):
        # deterministic, length-padded literal, distinct per idx within
        # the pool, cycling through `distinct_literal_pool` distinct values.
        pool_idx = idx % distinct_literal_pool
        base = "Ctrl_%s_%06d" % (family, pool_idx)
        pad_needed = max(0, literal_len - len(base))
        return base + ("X" * pad_needed)

    hot_literal = None
    if hot_literal_fraction > 0:
        hot_literal = "HotFold_%s" % family
        hot_literal = hot_literal + ("Y" * max(0, (hot_literal_len or literal_len) - len(hot_literal)))

    def emit_group(name, cur_depth, indent):
        group_counter[0] += 1
        pad = "\t" * indent
        lines.append(pad + _quote(name))
        lines.append(pad + "{")
        for m in range(metadata_per_group):
            key = "meta%d" % m
            # Distinct per (group, entry) -- NOT deduped away by the string
            # pool -- so metadata_per_group actually scales pool bytes
            # linearly, rather than every entry in a group sharing one
            # interned value string.
            val = ("V%s_%06d_%04d_" % (family, group_counter[0], m)) + ("Z" * max(0, metadata_len))
            lines.append(pad + "\t" + _quote(key) + "\t\t" + _quote(val))
        if cur_depth >= depth:
            for c in range(controls_per_leaf):
                use_hot = hot_literal is not None and (occ_counter[0] % 1000) < int(hot_literal_fraction * 1000)
                if use_hot:
                    lit = hot_literal
                else:
                    lit = make_literal(literal_counter[0])
                    literal_counter[0] += 1
                occ_counter[0] += 1
                lines.append(pad + "\t" + _quote("control") + "\t\t" + _quote(lit))
        else:
            for g in range(groups_per_level):
                emit_group("%s_D%d_G%d" % (name, cur_depth, g), cur_depth + 1, indent + 1)
        lines.append(pad + "}")

    for r in range(root_groups):
        emit_group("Root_%s_%d" % (family, r), 1, 1)

    lines.append("}")
    lines.append("")
    text = "\n".join(lines)
    return text.encode("utf-8"), group_counter[0], occ_counter[0]


def build_and_measure(name, params):
    text_bytes, approx_groups, approx_occs = build_master_text(**params)
    master_path = os.path.join(FIXROOT, "%s_master.txt" % name)
    with open(master_path, "wb") as f:
        f.write(text_bytes)

    snapshot = compiler.capture_source_snapshot(master_path)
    result = core.parse_master_bytes(snapshot.bytes, source_name=master_path)
    if not result.ok:
        errs = "; ".join("%s@%d: %s" % (e.kind, e.line, e.message) for e in result.grammar_errors[:5])
        raise RuntimeError("fixture %s: grammar invalid: %s" % (name, errs))

    outcome = compiler.parse_and_compile(snapshot)
    compiler.self_validate_from_bytes(outcome)  # production-reader exhaustive parity, offline

    artifact_path = os.path.join(FIXROOT, "%s.sfmsidecar" % name)
    with open(artifact_path, "wb") as f:
        f.write(outcome.blob)

    fams = core.build_fold_families(result.occurrences)
    largest_family = max((len(f.occurrence_global_ranks) for f in fams.values()), default=0)
    hierarchy_depth = max((g.depth for g in result.groups), default=0)
    metadata_count = sum(len(g.metadata.entries) for g in result.groups)

    metrics = {
        "name": name,
        "master_path": master_path,
        "artifact_path": artifact_path,
        "master_bytes": len(text_bytes),
        "sidecar_bytes": len(outcome.blob),
        "ratio_to_official": len(outcome.blob) / float(REAL_ARTIFACT_BYTES),
        "string_count": len(set(o.literal for o in result.occurrences)
                             | set(g.name for g in result.groups)
                             | set(e.key for g in result.groups for e in g.metadata.entries)
                             | set(e.value for g in result.groups for e in g.metadata.entries)),
        "group_count": len(result.groups),
        "fold_family_count": len(fams),
        "occurrence_count": len(result.occurrences),
        "metadata_count": metadata_count,
        "hierarchy_depth": hierarchy_depth,
        "largest_fold_family_cardinality": largest_family,
        "artifact_sha256": hashlib.sha256(outcome.blob).hexdigest(),
        "source_sha256": outcome.result.source_sha256,
    }
    print("%-24s master=%9d bytes  sidecar=%10d bytes (%.2fx)  strings~=%7d groups=%5d folds=%7d occs=%8d meta=%6d depth=%d maxfam=%d" % (
        name, metrics["master_bytes"], metrics["sidecar_bytes"], metrics["ratio_to_official"],
        metrics["string_count"], metrics["group_count"], metrics["fold_family_count"],
        metrics["occurrence_count"], metrics["metadata_count"], metrics["hierarchy_depth"],
        metrics["largest_fold_family_cardinality"],
    ))
    return metrics


if __name__ == "__main__":
    print("Probing parameter scale for each family before building the full ladder...\n")
