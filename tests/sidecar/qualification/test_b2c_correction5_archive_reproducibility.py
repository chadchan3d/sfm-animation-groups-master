# -*- coding: utf-8 -*-
"""Final targeted infrastructure correction -- Test 3 / BLOCKER 3
regression probe: immutable-archive reproducibility. THIS TEST IS
PERMANENT (Section 5 of the governing prompt) -- re-run it, unmodified,
after every future checkpoint commit.

Two real mechanisms are exercised:

1. The frozen validator/provider (`candidate_packed_validator_r3a2b.py`,
   `candidate_packed_provider_r3a2b.py`) ARE already tracked at HEAD, so
   this test runs a REAL `git archive --worktree-attributes HEAD` on
   them (never a plain filesystem copy, which could never reproduce the
   zip-extraction line-ending quirk this test exists to catch), extracts
   the resulting zip, and re-hashes -- proving the `.gitattributes`
   `text eol=lf` rule actually fixes the archive/pin mismatch the
   independent re-audit reproduced (`--worktree-attributes` reads this
   session's in-progress `.gitattributes` even before it is committed;
   once committed, a plain `git archive <SHA>` reproduces the same
   result without that flag).

2. `candidate_b2c_correction5/` and its fixtures are NOT YET committed
   (this implementation phase is explicitly forbidden from staging/
   committing) -- `git archive` cannot include untracked content, so
   this test instead copies the current working-tree candidate into a
   completely fresh, differently-rooted directory (the same "extracted
   archive root" simulation Test D already established) and runs the
   REST of Section 5's checklist against THAT copy. Once correction5 is
   actually committed at a future checkpoint, re-running this SAME test
   file will additionally exercise the real `git archive <SHA>` path for
   the fixtures too (this test detects whether the candidate is tracked
   and reports which mode it ran in -- never silently substituting one
   for the other without saying so).
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(_THIS_DIR, os.pardir, os.pardir, os.pardir))
CORRECTION5_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction5")
CORRECTION5_NORMALIZER_ROOT = os.path.join(_THIS_DIR, "candidate_b2c_correction5_normalizer")
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")

RESULTS = []


def check(name, condition, detail=None):
    RESULTS.append((name, condition))
    print("[%s] %s%s" % ("PASS" if condition else "FAIL", name, ("" if condition else " -- %r" % (detail,))))


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO_ROOT)


print("Interpreter: %s" % sys.version)

VALIDATOR_PIN = "74fe8d9655018a9450d0803018d61e42ec3d17b2947b60915df6b598ffc1563f"
PROVIDER_PIN = "d6ef96502194c15e594b3e5754e2f5826af1d0ec01b0b358fff08598f7e6b677"
VALIDATOR_REL = "tests/sidecar/qualification/candidate_packed_validator_r3a2b.py"
PROVIDER_REL = "tests/sidecar/qualification/candidate_packed_provider_r3a2b.py"

# ===========================================================================
# Part 1: REAL git archive of the already-tracked validator/provider,
# with --worktree-attributes so this session's in-progress .gitattributes
# is honored even pre-commit.
# ===========================================================================
print("\n=== Part 1: real git-archive reproduction (validator/provider) ===")
ARCHIVE_TMP = tempfile.mkdtemp(prefix="b2c_correction5_archive_")
zip_path = os.path.join(ARCHIVE_TMP, "probe.zip")
head_sha = git("rev-parse", "HEAD").decode("ascii").strip()
git("archive", "--format=zip", "--worktree-attributes", "-o", zip_path, "HEAD", "--", VALIDATOR_REL, PROVIDER_REL)
extract_dir = os.path.join(ARCHIVE_TMP, "extracted")
os.makedirs(extract_dir)
subprocess.check_call(["tar", "-xf", zip_path, "-C", extract_dir])

with open(os.path.join(extract_dir, VALIDATOR_REL), "rb") as f:
    archived_validator_sha = hashlib.sha256(f.read()).hexdigest()
with open(os.path.join(extract_dir, PROVIDER_REL), "rb") as f:
    archived_provider_sha = hashlib.sha256(f.read()).hexdigest()

print("[archive] HEAD=%s validator_sha=%s provider_sha=%s" % (head_sha, archived_validator_sha, archived_provider_sha))
check("part1.0 archived validator bytes match the contract-pinned SHA-256 exactly "
      "(the exact mismatch the independent re-audit reproduced)",
      archived_validator_sha == VALIDATOR_PIN, archived_validator_sha)
check("part1.1 archived provider bytes match the contract-pinned SHA-256 exactly",
      archived_provider_sha == PROVIDER_PIN, archived_provider_sha)
shutil.rmtree(ARCHIVE_TMP, ignore_errors=True)

# ===========================================================================
# Part 2: is candidate_b2c_correction5 itself tracked yet? Detect and
# report the mode -- never silently substitute one proof for the other.
# ===========================================================================
tracked_files = git("ls-files", "--", "tests/sidecar/qualification/candidate_b2c_correction5").decode("utf-8").strip()
CANDIDATE4_IS_TRACKED = bool(tracked_files)
print("\n[mode] candidate_b2c_correction5 tracked in git: %s" % CANDIDATE4_IS_TRACKED)
if CANDIDATE4_IS_TRACKED:
    print("[mode] running the FULL real `git archive HEAD` path for the candidate + fixtures too.")
else:
    print("[mode] candidate_b2c_correction5 is NOT yet committed (this implementation phase forbids "
          "staging/committing) -- falling back to a fresh-root WORKING-TREE COPY simulation for the "
          "candidate + fixtures below. Re-run this SAME test file after the next checkpoint commit to "
          "additionally exercise the real git-archive path for the fixtures.")

FRESH_ROOT = tempfile.mkdtemp(prefix="b2c_correction5_freshroot_")
check("part2.0 fresh root is not under the original repo path",
      not FRESH_ROOT.lower().startswith(REPO_ROOT.lower()))

if CANDIDATE4_IS_TRACKED:
    zip2 = os.path.join(FRESH_ROOT, "full.zip")
    # sidecar_contract.py resolves the frozen validator/provider as
    # SIBLINGS of the candidate root -- must be included in the SAME
    # archive alongside the candidate itself, or ensure_loaded() cannot
    # find them from the fresh extraction.
    git("archive", "--format=zip", "--worktree-attributes", "-o", zip2, "HEAD", "--",
        "tests/sidecar/qualification/candidate_b2c_correction5",
        "tests/sidecar/qualification/candidate_b2c_correction5_normalizer", "tools",
        VALIDATOR_REL, PROVIDER_REL)
    subprocess.check_call(["tar", "-xf", zip2, "-C", FRESH_ROOT])
    fresh_correction5 = os.path.join(FRESH_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction5")
    fresh_normalizer = os.path.join(FRESH_ROOT, "tests", "sidecar", "qualification", "candidate_b2c_correction5_normalizer")
    fresh_tools = os.path.join(FRESH_ROOT, "tools")
else:
    fresh_qual_dir = os.path.join(FRESH_ROOT, "tests", "sidecar", "qualification")
    os.makedirs(fresh_qual_dir)
    fresh_correction5 = os.path.join(fresh_qual_dir, "candidate_b2c_correction5")
    fresh_normalizer = os.path.join(fresh_qual_dir, "candidate_b2c_correction5_normalizer")
    fresh_tools = os.path.join(FRESH_ROOT, "tools")
    shutil.copytree(CORRECTION5_ROOT, fresh_correction5, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(CORRECTION5_NORMALIZER_ROOT, fresh_normalizer, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(TOOLS_DIR, fresh_tools, ignore=shutil.ignore_patterns("__pycache__"))
    # sidecar_contract.py resolves the frozen validator/provider as
    # SIBLINGS of the candidate root (two levels up from
    # sfm_master_authority_productionized/) -- copy them into the same
    # relative position under the fresh root.
    for rel in (VALIDATOR_REL, PROVIDER_REL):
        shutil.copy(os.path.join(REPO_ROOT, rel), os.path.join(fresh_qual_dir, os.path.basename(rel)))

check("part2.1 fresh copy contains the candidate authority package",
      os.path.isdir(os.path.join(fresh_correction5, "sfm_master_authority")))

# ===========================================================================
# Part 3: A/B Master hashes vs manifest/embedded-source SHAs, from the
# FRESH copy (never the original working tree).
# ===========================================================================
print("\n=== Part 3: A/B Master hashes vs manifest ===")
fresh_fixtures_ab = os.path.join(fresh_correction5, "fixtures_ab")
with open(os.path.join(fresh_fixtures_ab, "manifest.json")) as f:
    manifest = json.load(f)

for role in ("generation_a", "generation_b"):
    entry = manifest[role]
    master_path = os.path.join(fresh_fixtures_ab, entry["master_relative_path"])
    with open(master_path, "rb") as f:
        master_bytes = f.read()
    actual_sha = hashlib.sha256(master_bytes).hexdigest()
    check("part3.%s.0 fresh-copy Master bytes are pure LF (no CR byte)" % role, b"\r" not in master_bytes)
    check("part3.%s.1 fresh-copy Master hash matches the manifest's own recorded source SHA-256" % role,
          actual_sha == entry["master_sha256"], (actual_sha, entry["master_sha256"]))

    # ===================================================================
    # Part 4 (interleaved): validate the sidecar against the archived/
    # copied Master, using ONLY paths under the fresh root.
    # ===================================================================
    sys.path_snapshot = list(sys.path)
    for p in (fresh_correction5, fresh_tools):
        if p not in sys.path:
            sys.path.insert(0, p)
    for name in list(sys.modules.keys()):
        if name == "sfm_master_authority_productionized" or name.startswith("sfm_master_authority_productionized."):
            del sys.modules[name]
    from sfm_master_authority_productionized import sidecar_contract  # noqa: E402
    sidecar_contract.ensure_loaded()
    check("part4.%s.0 sidecar_contract resolved its validator/provider/tools paths under the FRESH "
          "root, never the original repo path" % role,
          sidecar_contract.FINAL_R3A2B_VALIDATOR_PATH.lower().startswith(FRESH_ROOT.lower())
          and sidecar_contract._GATE_R2_DEPLOY_DIR.lower().startswith(FRESH_ROOT.lower()),
          (sidecar_contract.FINAL_R3A2B_VALIDATOR_PATH, sidecar_contract._GATE_R2_DEPLOY_DIR))
    artifact_path = os.path.join(fresh_fixtures_ab, entry["artifact_relative_path"])
    provider = sidecar_contract._provider_module.BoundedProvider.open_path(artifact_path, entry["master_sha256"])
    try:
        groups = list(provider.iter_groups())
        check("part4.%s.1 the sidecar validates against its archived/copied Master (source_sha256 "
              "matches, provider opened successfully)" % role, len(groups) >= 1, len(groups))
    finally:
        provider.close()

# ===========================================================================
# Part 5: run the decisive valid A/B generation test from the fresh root.
# ===========================================================================
print("\n=== Part 5: decisive A/B generation test, from the fresh root ===")
for name in list(sys.modules.keys()):
    if name == "sfm_master_authority_productionized" or name.startswith("sfm_master_authority_productionized."):
        del sys.modules[name]
from sfm_master_authority_productionized import broker as broker_mod  # noqa: E402
from sfm_master_authority_productionized import normalizer_compat_adapter as adapter  # noqa: E402
from sfm_master_authority_productionized import errors  # noqa: E402

GEN_A = manifest["generation_a"]["master_sha256"]
GEN_B = manifest["generation_b"]["master_sha256"]
with open(os.path.join(fresh_fixtures_ab, manifest["generation_a"]["master_relative_path"]), "rb") as f:
    MASTER_A_BYTES = f.read()
with open(os.path.join(fresh_fixtures_ab, manifest["generation_b"]["master_relative_path"]), "rb") as f:
    MASTER_B_BYTES = f.read()
mutable_master = os.path.join(FRESH_ROOT, "mutable_master.txt")
shipped_root = os.path.join(fresh_fixtures_ab, manifest["shared_shipped_root_relative_path"])
wanted = frozenset([b"left", b"right"])
request_specs = {"normalizer": (wanted, adapter.build_targeted_master_compatible_projection(wanted))}

with open(mutable_master, "wb") as f:
    f.write(MASTER_A_BYTES)
b_fresh = broker_mod.Broker(api_version="test-archive-repro-fresh")
before_entries = b_fresh.view_cache_entry_count()

with open(mutable_master, "wb") as f:
    f.write(MASTER_B_BYTES)
try:
    b_fresh.acquire_or_reuse_views(mutable_master, request_specs, shipped_root=shipped_root, expected_generation=GEN_A)
    outcome = "admitted"
except errors.AuthorityChangedDuringAcquisition as exc:
    outcome = "AuthorityChangedDuringAcquisition: %s" % exc
after_entries = b_fresh.view_cache_entry_count()

check("part5.0 expected A + current B (valid sidecar B present) rejects BEFORE cache publication, "
      "from the fresh/extracted root", outcome.startswith("AuthorityChangedDuringAcquisition"), outcome)
check("part5.1 no SidecarMissing substitute outcome", "SidecarMissing" not in outcome)
check("part5.2 cache/generation state unchanged on mismatch", after_entries == before_entries,
      (before_entries, after_entries))

shutil.rmtree(FRESH_ROOT, ignore_errors=True)

print("\nRESULT: %d/%d %s" % (
    sum(1 for _, c in RESULTS if c), len(RESULTS),
    "ALL PASS" if all(c for _, c in RESULTS) else "SOME FAILED"
))
