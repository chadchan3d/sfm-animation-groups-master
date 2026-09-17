# -*- coding: utf-8 -*-
"""Astra SECOND correction gate -- Test 2 fixture builder (F8: explicit,
reproducible, repo-relative fixture root; hashes recorded in manifest.json;
no Claude-temp or Public Documents dependence for this gate's OWN new
fixtures). Python 3 only (uses tools/sfm_master_sidecar/compiler.py, which
is itself Python-3-only) -- the fixtures it PRODUCES are then consumed by
both Python 3.10 and real Python 2.7.5 test runs.

Every fixture here is a REAL master.txt compiled through the actual
production pipeline (sfm_master_core.parse_master_bytes -> writer.
compile_sidecar), then self-validated via the real production reader
(compiler.self_validate_from_bytes) -- never a hand-assembled/patched
packed blob for these boundary-row and admission fixtures (Astra's exact
instruction: "Use REAL compiled/validated fixtures").
"""
import hashlib
import json
import os
import shutil
import sys

REPO_ROOT = r"E:\SFM Animation Group Master"
TOOLS_DIR = REPO_ROOT + r"\tools"
FIXROOT = REPO_ROOT + r"\tests\sidecar\qualification\candidate_b2c_correction2\fixtures"

if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from sfm_master_sidecar import compiler  # noqa: E402

if os.path.isdir(FIXROOT):
    shutil.rmtree(FIXROOT)
os.makedirs(FIXROOT)

MANIFEST = {}


def build_and_validate(name, master_text):
    """Compile `master_text` through the real generic compiler path, run
    full self-validation (exhaustive semantic parity, including decoding
    EVERY fold family's occurrences -- this is the one and only place in
    this fixture-build step where that full decode happens; it is fixture
    CONSTRUCTION, not the qualification test's own admission-path
    exercise), then write both the master.txt and the compiled
    .sfmsidecar to the repo-relative fixture root."""
    data = wrap_root(master_text).encode("utf-8")
    snapshot = compiler.SourceSnapshot(path="<synthetic:%s>" % name, data=data)
    outcome = compiler.parse_and_compile(snapshot)
    compiler.self_validate_from_bytes(outcome)

    master_path = os.path.join(FIXROOT, "%s_master.txt" % name)
    artifact_path = os.path.join(FIXROOT, "%s.sfmsidecar" % name)
    with open(master_path, "wb") as f:
        f.write(data)
    with open(artifact_path, "wb") as f:
        f.write(outcome.blob)

    master_sha = hashlib.sha256(data).hexdigest()
    artifact_sha = hashlib.sha256(outcome.blob).hexdigest()
    MANIFEST[name] = {
        "master_path": master_path,
        "artifact_path": artifact_path,
        "master_sha256": master_sha,
        "artifact_sha256": artifact_sha,
        "artifact_bytes": len(outcome.blob),
        "group_count": len(outcome.result.groups),
        "occurrence_count": len(outcome.result.occurrences),
    }
    print("[built] %-28s master_sha=%s artifact_bytes=%d groups=%d occurrences=%d"
          % (name, master_sha[:16], len(outcome.blob), len(outcome.result.groups), len(outcome.result.occurrences)))
    return outcome


def group_with_repeated_control(group_name, literal, count):
    lines = ['"%s"' % group_name, "{"]
    for _ in range(count):
        lines.append('\t"control"\t\t"%s"' % literal)
    lines.append("}")
    return "\n".join(lines) + "\n"


def wrap_root(inner_text):
    """normalizer_compat_adapter's real builder requires exactly one
    root-level group literally named `groupFile` (the sidecar's synthetic
    wrapper for the real Master's outer `groupFile{...}` block) -- every
    fixture used against that adapter must be wrapped this way, matching
    the real production Master's own top-level shape."""
    return '"groupFile"\n{\n' + inner_text + "\n}\n"


# ===========================================================================
# Boundary-row fixtures: exactly 19,999 / 20,000 / 20,001 occurrences of
# ONE fold family (a single repeated exact literal inside one group --
# fully supported by the grammar; see sfm_master_core's own "duplicate
# CONTROL occurrences... remain fully representable" contract).
# ===========================================================================
for n, label in [(19999, "below"), (20000, "at"), (20001, "above")]:
    text = group_with_repeated_control("BoundaryFamilyGroup", "BoundaryOccurrenceControl", n)
    build_and_validate("boundary_%s_%d" % (label, n), text)

# ===========================================================================
# Astra's exact reproduction shape: TWO 20,000-occurrence families +
# 20,000 singleton families (target ~2.0 MB artifact). The average-based
# preliminary estimator sees a low AVERAGE family size (dominated by the
# 20,000 singletons) and would (pre-correction) admit a request for only
# the two large families; the corrected cumulative admission must use the
# REAL per-family packed counts instead.
# ===========================================================================
two_large_lines = ['"AstraReproGroup"', "{"]
two_large_lines.append('\t"control"\t\t"AstraFamilyOne"' + "\n" + ('\t"control"\t\t"AstraFamilyOne"\n' * 19999))
two_large_lines.append('\t"control"\t\t"AstraFamilyTwo"' + "\n" + ('\t"control"\t\t"AstraFamilyTwo"\n' * 19999))
for i in range(20000):
    two_large_lines.append('\t"control"\t\t"AstraSingleton%05d"' % i)
two_large_lines.append("}")
astra_text = "\n".join(two_large_lines) + "\n"
build_and_validate("astra_two_large_families", astra_text)

# ===========================================================================
# Concentrated small vocabulary: few distinct folds, each with many
# occurrences (a small-vocabulary, high-occurrence-density shape distinct
# from the singleton-heavy Astra repro above).
# ===========================================================================
small_vocab_lines = ['"ConcentratedVocabGroup"', "{"]
for word in ("Alpha", "Beta", "Gamma", "Delta", "Epsilon"):
    for _ in range(500):
        small_vocab_lines.append('\t"control"\t\t"%s"' % word)
small_vocab_lines.append("}")
build_and_validate("concentrated_small_vocab", "\n".join(small_vocab_lines) + "\n")

# ===========================================================================
# Long literals: control names near the practical upper end of realistic
# length, to exercise string-pool/table sizing assumptions.
# ===========================================================================
long_lines = ['"LongLiteralGroup"', "{"]
for i in range(200):
    long_lines.append('\t"control"\t\t"%s_%03d"' % ("VeryLongSyntheticControlNameForStringPoolStressTesting" * 3, i))
long_lines.append("}")
build_and_validate("long_literals", "\n".join(long_lines) + "\n")

# ===========================================================================
# Deep hierarchy: many nested groups (stresses group-table/metadata cost
# models beyond a flat, single-group shape).
# ===========================================================================
DEPTH = 60
deep_lines = []
for level in range(DEPTH):
    deep_lines.append('"DeepLevel%03d"' % level)
    deep_lines.append("{")
deep_lines.append('"control"\t\t"DeepestControl"')
for level in range(DEPTH):
    deep_lines.append("}")
build_and_validate("deep_hierarchy", "\n".join(deep_lines) + "\n")

# ===========================================================================
# Dense metadata: many metadata (non-"control") key/value entries per
# group.
# ===========================================================================
dense_meta_lines = ['"DenseMetadataGroup"', "{"]
for i in range(300):
    dense_meta_lines.append('\t"metaKey%03d"\t\t"metaValue%03d"' % (i, i))
dense_meta_lines.append('\t"control"\t\t"DenseMetaControl"')
dense_meta_lines.append("}")
build_and_validate("dense_metadata", "\n".join(dense_meta_lines) + "\n")

with open(os.path.join(FIXROOT, "manifest.json"), "w") as f:
    json.dump(MANIFEST, f, indent=2, sort_keys=True)

print("\nFixture root:", FIXROOT)
print("Manifest written with %d fixtures." % len(MANIFEST))
