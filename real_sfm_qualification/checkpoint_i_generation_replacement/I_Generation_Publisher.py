# -*- coding: utf-8 -*-
"""
I_Generation_Publisher -- REPO-SIDE ONLY. Python 3 only.

CORRECTION ROUND 1 (2026-09-25, independent review, BLOCKER 11): this
module is NEVER copied to the live SFM MAINMENU directory. It imports
the real, accepted tools/sfm_master_sidecar compiler/publisher/manifest
package via an EXPLICITLY VALIDATED repo root passed by the caller --
never a relative-path guess derived from this file's own location
(which would silently break if this file were ever copied elsewhere,
exactly the ambiguity the review flagged). validate_repo_root() requires
tools/sfm_master_sidecar/publisher.py to actually exist under the given
root before anything else is attempted.

This module imports I_Generation_Helper (the SFM-deployable core) as a
sibling for its own shared primitives (hash-gated Master mutation,
inventory capture/compare, sidecar removal, G2 construction, path
binding) -- it does not duplicate them.

CORRECTION ROUND 2 (2026-09-25, independent review): a second
independent review found that round 1's own INSTRUCTIONS.md falsely
documented publish_g2_with_record() as performing the live G1->G2
Master replacement -- it never did, and never called
perform_g1_to_g2_replacement(). This module is now restructured into an
explicit TWO-PHASE architecture (R2 BLOCKER 1):

  Phase A (prepare + publish G2 AUTHORITY, never touches live Master):
    construct_and_write_g2_source() -- constructs G2 bytes ITSELF from
      exact canonical G1 bytes (R2 BLOCKER 2: no manually-supplied
      --g2-source ever accepted again);
    write_g2_plan_record() -- an immutable PLAN record, written BEFORE
      the first live authority mutation (R2 BLOCKER 7), containing every
      fact independently derivable from the already-accepted, read-only
      check_only() operation alone -- including the exact expected
      sidecar SHA-256 (check_only's own ordinary_sha256, which manifest.
      py's build_manifest_dict() sets as sidecar_sha256 = outcome.
      ordinary_sha256 -- confirmed by direct source inspection, so this
      is the REAL eventual sidecar hash, not a guess) and the exact
      expected generation basename (compiler.generation_basename(
      ordinary_sha256), the same deterministic formula publish() itself
      uses);
    publish_g2_with_record() -- consumes the plan record but never
      blindly trusts it: every fact is RE-DERIVED fresh, right now,
      against the actual current bytes, before anything is published.
    prepare_and_publish_g2() -- convenience wrapper chaining all three,
      in this exact order.

  Phase B (ACTIVATE the live G2 Master -- the ONLY function in this
  entire deliverable that ever calls perform_g1_to_g2_replacement()):
    activate_g2_master() -- binds master_path/authority_dir to the I1
      baseline inventory (R2 BLOCKER 5) before trusting them for
      anything, verifies the live Master is currently exact G1,
      re-derives G2 from the CURRENT live G1 bytes and confirms it
      matches the publication record's own G2 hash, confirms the exact
      recorded G2 authority artifact exists and matches, THEN performs
      the one sanctioned, hash-gated, atomic G1->G2 replacement, and
      writes an immutable ACTIVATION record. A failure at ANY step
      before the atomic replacement itself leaves both the live Master
      and every already-written record (plan + publication) untouched
      and independently recoverable (R2 BLOCKER 7); a failure of the
      atomic replacement itself is guaranteed (by I_Generation_Helper's
      own MoveFileExW contract) to leave the live Master untouched too.

  finalize_restoration() -- (R2 BLOCKERS 5/8) now also binds
  master_path/authority_dir to the I1 baseline inventory before trusting
  them for any write, and independently RE-VERIFIES the publication
  record (re-derived G1+LF hash, safe basename, exact on-disk sidecar
  SHA, recorded semantic parity) immediately before it is ever allowed
  to authorize a sidecar deletion -- a tampered or wrong publication
  record can no longer authorize any deletion merely because the file
  exists.

CORRECTION ROUND 3 (2026-09-25, third independent review):
  R3 BLOCKER 1: Phase A is ITSELF a live mutation (it writes a sidecar
    and replaces manifest.json) -- write_g2_plan_record() now ALSO
    requires the I1 baseline inventory, validates baseline_inventory's
    own recorded master_sha256 == canonical G1, and records both the
    baseline Master path and baseline authority path INTO the plan
    record itself, before any authority-directory write. publish_g2_
    with_record() then binds the CALLER's actual output_dir to the
    plan's own recorded baseline authority path immediately before
    calling publish_generation() -- a wrong output_dir STOPs before the
    first authority-directory write, creating/modifying nothing there.
  R3 BLOCKER 2/3: finalize_restoration() now takes an explicit
    plan_record parameter (publication_record is now OPTIONAL, may be
    None) and independently RE-DERIVES G2 identity as G1+LF from the
    G1 bytes it already verified -- never from publication_record's own
    claimed g2_source_sha256 (R3 BLOCKER 3) -- so a corrupt/tampered
    publication record, or one that never got written at all because
    Phase A's own publication-record write failed AFTER publish_
    generation() had already mutated the authority directory, can
    never prevent safe G2->G1 Master restoration. The new
    _determine_sidecar_removal() recovers the sidecar's own identity
    from EITHER record independently (the plan record, written before
    any mutation, is an equally valid anchor), and NEVER guesses when
    the two disagree on that identity -- deletion is refused outright
    in that case (R3 BLOCKER 3).
  R3 BLOCKER 4: I_Generation_Helper.py's own CLI no longer exposes any
    mutation subcommand at all (not even the narrow, hash-gated ones) --
    activate_g2_master() in THIS module is now literally the only
    external G1->G2 activation surface.
  R3 BLOCKER 5: see the new, separate Checkpoint_I_Restoration_Verify.py
    for verifying recovery after an EARLY-ABORTED campaign (one that
    never reached the primary checkpoint's own scheduled
    i_08_finalize_verify snapshot).

Run under an ordinary Python 3 interpreter, from the repository root
(never inside SFM):
  python I_Generation_Publisher.py <op> --repo-root <path> ...
"""
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import I_Generation_Helper as igen  # noqa: E402


class GenerationPublisherError(Exception):
    pass


def _require_python3():
    if sys.version_info[0] < 3:
        raise GenerationPublisherError(
            "I_Generation_Publisher.py requires Python 3 -- it imports the "
            "real, accepted, Python-3-only tools/sfm_master_sidecar "
            "package. It must never be run inside SFM's embedded Python "
            "2.7.5 interpreter, and this module is never deployed there."
        )


def validate_repo_root(repo_root):
    """Explicit, validated repo root -- never guessed from this file's
    own location. Requires tools/sfm_master_sidecar/publisher.py to
    actually exist under it before anything else is attempted."""
    _require_python3()
    candidate = os.path.join(repo_root, "tools", "sfm_master_sidecar", "publisher.py")
    if not os.path.isfile(candidate):
        raise GenerationPublisherError(
            "repo_root %r does not contain tools/sfm_master_sidecar/"
            "publisher.py (%r not found) -- refusing to guess; pass the "
            "real repository root explicitly via --repo-root."
            % (repo_root, candidate)
        )
    return repo_root


def _import_sidecar_tools(repo_root):
    validate_repo_root(repo_root)
    tools_parent = os.path.join(repo_root, "tools")
    if tools_parent not in sys.path:
        sys.path.insert(0, tools_parent)
    from sfm_master_sidecar import publisher as _publisher
    return _publisher


def _import_sidecar_compiler(repo_root):
    validate_repo_root(repo_root)
    tools_parent = os.path.join(repo_root, "tools")
    if tools_parent not in sys.path:
        sys.path.insert(0, tools_parent)
    from sfm_master_sidecar import compiler as _compiler
    return _compiler


def _import_semantic_core(repo_root):
    validate_repo_root(repo_root)
    tools_parent = os.path.join(repo_root, "tools")
    if tools_parent not in sys.path:
        sys.path.insert(0, tools_parent)
    import sfm_master_core as core
    return core


# ---------------------------------------------------------------------
# BLOCKER 7 (round 1): semantic-count summary and a stronger
# deterministic semantic digest, both computed directly from the
# already-accepted compiler's own parsed result object -- no new parser.
# ---------------------------------------------------------------------
def compute_semantic_counts_and_digest(repo_root, outcome_result):
    core = _import_semantic_core(repo_root)
    fams = core.build_fold_families(outcome_result.occurrences)
    counts = {
        "groups": len(outcome_result.groups),
        "occurrences": len(outcome_result.occurrences),
        "folds": len(fams),
    }
    groups_repr = sorted(
        (g.full_path, g.parent_path, g.declare_order, g.sibling_rank)
        for g in outcome_result.groups
    )
    occ_repr = sorted(
        (o.literal, o.full_path, o.local_rank, o.global_rank)
        for o in outcome_result.occurrences
    )
    digest_source = repr((groups_repr, occ_repr)).encode("utf-8")
    semantic_digest = hashlib.sha256(digest_source).hexdigest()
    return counts, semantic_digest


def check_only_source(repo_root, source_path, official_policy=False):
    """Wraps the real, accepted publisher.check_only() -- establishes
    parse success, profile eligibility, deterministic compilation,
    reader structural validation, source binding, and semantic parity,
    without touching any output namespace. Also returns semantic counts,
    a deterministic semantic digest (BLOCKER 7, round 1), and the
    compiled artifact's own ordinary_sha256 -- which IS the real,
    eventual sidecar file's own content hash once published (manifest.py
    sets sidecar_sha256 = outcome.ordinary_sha256), letting a caller
    derive the exact expected sidecar identity and generation basename
    WITHOUT ever writing to an output directory (R2 BLOCKER 7)."""
    publisher = _import_sidecar_tools(repo_root)
    result = publisher.check_only(source_path, official_policy=official_policy)
    outcome = result.outcome
    counts, semantic_digest = compute_semantic_counts_and_digest(repo_root, outcome.result)
    return {
        "ordinary_sha256": outcome.ordinary_sha256,
        "source_sha256": outcome.snapshot.sha256_hex,
        "source_byte_length": len(outcome.snapshot.bytes),
        "counts": counts,
        "semantic_digest": semantic_digest,
    }


def compare_semantic_parity(check_result_a, check_result_b):
    """BLOCKER 7 (round 1): proves two check_only_source() results
    describe semantically-identical Masters (same group/occurrence/
    fold-family counts AND the same deterministic semantic digest)
    despite different SHA-256 source hashes."""
    counts_a = check_result_a["counts"]
    counts_b = check_result_b["counts"]
    return {
        "groups_equal": counts_a["groups"] == counts_b["groups"],
        "occurrences_equal": counts_a["occurrences"] == counts_b["occurrences"],
        "folds_equal": counts_a["folds"] == counts_b["folds"],
        "semantic_digest_equal": check_result_a["semantic_digest"] == check_result_b["semantic_digest"],
        "source_sha256_differs": check_result_a["source_sha256"] != check_result_b["source_sha256"],
        "all_parity_checks_pass": (
            counts_a["groups"] == counts_b["groups"]
            and counts_a["occurrences"] == counts_b["occurrences"]
            and counts_a["folds"] == counts_b["folds"]
            and check_result_a["semantic_digest"] == check_result_b["semantic_digest"]
            and check_result_a["source_sha256"] != check_result_b["source_sha256"]
        ),
    }


def publish_generation(repo_root, source_path, output_dir, official_policy=True):
    """Wraps the real, accepted publisher.publish()."""
    publisher = _import_sidecar_tools(repo_root)
    result = publisher.publish(source_path, output_dir, official_policy=official_policy)
    return {
        "generation_basename": result.generation_basename,
        "generation_path": str(result.generation_path),
        "manifest_path": str(result.manifest_path),
        "reused": result.reused,
        "ordinary_sha256": result.ordinary_sha256,
        "source_sha256": result.source_sha256,
    }


def read_active_manifest_full(repo_root, output_dir):
    publisher = _import_sidecar_tools(repo_root)
    manifest = publisher.read_active_manifest(output_dir)
    if manifest is None:
        return None
    return {
        "generation_basename": manifest.generation_basename,
        "sidecar_sha256": manifest.sidecar_sha256,
        "source_sha256": manifest.source_sha256,
        "source_byte_length": manifest.source_byte_length,
        "format_contract_version": manifest.format_contract_version,
        "authority_semantics_version": manifest.authority_semantics_version,
        "counts": manifest.counts,
    }


def _write_record_once(path, record):
    if os.path.exists(path):
        raise GenerationPublisherError(
            "refusing to overwrite an existing record at %r" % (path,)
        )
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(json.dumps(record, indent=2, sort_keys=True).encode("utf-8"))
    os.rename(tmp_path, path)


# ---------------------------------------------------------------------
# R2 BLOCKER 1/2 -- PHASE A, step 1: construct G2 bytes ITSELF, from
# exact canonical G1 bytes. The operator/caller may NEVER supply a
# manually-prepared G2 file for real qualification use again. Touches
# only a new evidence file -- no live Master and no authority-directory
# mutation occurs here.
# ---------------------------------------------------------------------
def construct_and_write_g2_source(g1_source_path, g2_source_out_path,
                                   expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    g1_bytes = igen._read_bytes(g1_source_path)
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    if g1_sha.lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "construct_and_write_g2_source: g1_source_path %r hashes to "
            "%r, not the expected canonical G1 %r."
            % (g1_source_path, g1_sha, expected_g1_sha256)
        )
    g2_bytes = igen.construct_g2_bytes(g1_bytes)
    if not igen.g2_bytes_are_exact_g1_plus_one_lf(g1_bytes, g2_bytes):
        raise GenerationPublisherError(
            "construct_and_write_g2_source: internally constructed G2 "
            "bytes failed their own exact-G1-plus-one-LF self-check."
        )
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    if os.path.exists(g2_source_out_path):
        raise GenerationPublisherError(
            "construct_and_write_g2_source: refusing to overwrite an "
            "existing file at %r." % (g2_source_out_path,)
        )
    tmp_path = g2_source_out_path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(g2_bytes)
    os.rename(tmp_path, g2_source_out_path)
    return {
        "g1_source_path": g1_source_path,
        "g1_source_sha256": g1_sha,
        "g2_source_path": g2_source_out_path,
        "g2_source_sha256": g2_sha,
        "g2_source_byte_length": len(g2_bytes),
    }


# ---------------------------------------------------------------------
# R2 BLOCKER 7 -- PHASE A, step 2: an immutable PLAN/PREPARATION record,
# written BEFORE the first live authority mutation (before
# publish_generation() ever writes into the output directory). Every
# field is independently derivable from the already-accepted, read-only
# check_only() operation alone -- so a failure anywhere in step 3
# (publish_g2_with_record) never leaves recovery dependent on a record
# that had not yet been created.
#
# R3 BLOCKER 1: also requires the I1 baseline inventory and records its
# own recorded Master/authority paths into the plan itself -- the
# earliest point at which the intended destination can be pinned, BEFORE
# any authority-directory write. publish_g2_with_record() re-checks the
# CALLER's actual output_dir against these plan-recorded paths
# immediately before it ever calls publish_generation().
# ---------------------------------------------------------------------
def write_g2_plan_record(repo_root, g1_source_path, g2_source_path, plan_out_path, baseline_inventory,
                          expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    baseline_master_sha = (baseline_inventory or {}).get("master_sha256")
    if (baseline_master_sha or "").lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "write_g2_plan_record: baseline_inventory's own recorded "
            "master_sha256 %r does not match the expected canonical G1 "
            "%r -- refusing to plan against an untrusted baseline."
            % (baseline_master_sha, expected_g1_sha256)
        )
    check_g1 = check_only_source(repo_root, g1_source_path)
    check_g2 = check_only_source(repo_root, g2_source_path)
    if check_g1["source_sha256"].lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "write_g2_plan_record: g1_source_path does not hash to the "
            "expected canonical G1 -- refusing to plan."
        )
    g1_bytes = igen._read_bytes(g1_source_path)
    g2_bytes = igen._read_bytes(g2_source_path)
    if not igen.g2_bytes_are_exact_g1_plus_one_lf(g1_bytes, g2_bytes):
        raise GenerationPublisherError(
            "write_g2_plan_record: g2_source_path is not exactly g1 "
            "bytes + one ASCII LF -- refusing to plan."
        )
    parity = compare_semantic_parity(check_g1, check_g2)
    if not parity["all_parity_checks_pass"]:
        raise GenerationPublisherError(
            "write_g2_plan_record: G1/G2 semantic parity check failed "
            "before any publication was ever attempted: %r" % (parity,)
        )
    compiler = _import_sidecar_compiler(repo_root)
    expected_basename = compiler.generation_basename(check_g2["ordinary_sha256"])

    plan = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "g1_source_path": g1_source_path,
        "g1_source_sha256": check_g1["source_sha256"],
        "g2_source_path": g2_source_path,
        "expected_g2_source_sha256": check_g2["source_sha256"],
        "expected_g2_source_byte_length": check_g2["source_byte_length"],
        "expected_semantic_parity": parity,
        "expected_sidecar_ordinary_sha256": check_g2["ordinary_sha256"],
        "expected_generation_basename": expected_basename,
        "baseline_master_path": baseline_inventory.get("master_path"),
        "baseline_authority_dir": baseline_inventory.get("authority_dir"),
        "check_only_g1_result": check_g1,
        "check_only_g2_result": check_g2,
    }
    _write_record_once(plan_out_path, plan)
    return plan


# ---------------------------------------------------------------------
# R2 BLOCKER 1 -- PHASE A, step 3 (publication). Consumes an
# ALREADY-WRITTEN plan record but never blindly trusts it -- every fact
# is RE-DERIVED fresh, right now, against the actual current bytes.
# Does NOT touch the live Master (see activate_g2_master() below for
# the separate, explicit Phase B Master-activation step).
# ---------------------------------------------------------------------
def publish_g2_with_record(repo_root, plan_record_path, output_dir, record_out_path,
                            expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    with open(plan_record_path, "rb") as f:
        plan_record = json.loads(f.read().decode("utf-8"))

    g1_source_path = plan_record["g1_source_path"]
    g2_source_path = plan_record["g2_source_path"]

    g1_bytes = igen._read_bytes(g1_source_path)
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    if g1_sha.lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: g1_source_path %r does not hash to "
            "the expected canonical G1 %r." % (g1_source_path, expected_g1_sha256)
        )
    if g1_sha.lower() != plan_record["g1_source_sha256"].lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: g1_source_path %r has DRIFTED since "
            "the plan record was written (then %r, now %r) -- refusing "
            "to publish against a stale plan."
            % (g1_source_path, plan_record["g1_source_sha256"], g1_sha)
        )

    g2_bytes = igen._read_bytes(g2_source_path)
    if not igen.g2_bytes_are_exact_g1_plus_one_lf(g1_bytes, g2_bytes):
        raise GenerationPublisherError(
            "publish_g2_with_record: g2_source_path %r is not exactly "
            "g1 bytes + one ASCII LF." % (g2_source_path,)
        )
    g2_sha = hashlib.sha256(g2_bytes).hexdigest()
    if g2_sha.lower() != plan_record["expected_g2_source_sha256"].lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: g2_source_path %r has DRIFTED since "
            "the plan record was written (then %r, now %r) -- refusing "
            "to publish against a stale plan."
            % (g2_source_path, plan_record["expected_g2_source_sha256"], g2_sha)
        )

    check_g1 = check_only_source(repo_root, g1_source_path)
    check_g2 = check_only_source(repo_root, g2_source_path)
    parity = compare_semantic_parity(check_g1, check_g2)
    if not parity["all_parity_checks_pass"]:
        raise GenerationPublisherError(
            "publish_g2_with_record: G1/G2 semantic parity check failed "
            "immediately before publication was attempted: %r" % (parity,)
        )

    # R3 BLOCKER 1: Phase A is itself a live mutation (it writes a
    # sidecar and replaces manifest.json) -- bind output_dir to the
    # plan's own recorded baseline authority path BEFORE publish_
    # generation() is ever permitted to run. A wrong output_dir STOPs
    # here, before the first authority-directory write.
    plan_baseline_authority_dir = plan_record.get("baseline_authority_dir")
    if not igen.path_matches_baseline(output_dir, plan_baseline_authority_dir):
        raise GenerationPublisherError(
            "publish_g2_with_record: output_dir %r does not match the "
            "plan record's own recorded baseline authority path %r -- "
            "STOP, before any authority-directory write."
            % (output_dir, plan_baseline_authority_dir)
        )

    publish_result = publish_generation(repo_root, g2_source_path, output_dir)
    if publish_result["source_sha256"].lower() != g2_sha.lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: publish result source_sha256 %r does "
            "not match the independently computed G2 sha %r."
            % (publish_result["source_sha256"], g2_sha)
        )
    if publish_result["generation_basename"] != plan_record["expected_generation_basename"]:
        raise GenerationPublisherError(
            "publish_g2_with_record: actual published generation_basename "
            "%r does not match the plan record's independently-derived "
            "expected_generation_basename %r."
            % (publish_result["generation_basename"], plan_record["expected_generation_basename"])
        )

    active_manifest = read_active_manifest_full(repo_root, output_dir)
    if active_manifest is None:
        raise GenerationPublisherError(
            "publish_g2_with_record: no active manifest found immediately "
            "after publishing G2."
        )
    if active_manifest["source_sha256"].lower() != g2_sha.lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: active manifest source_sha256 does "
            "not match G2 immediately after publish."
        )
    if active_manifest["generation_basename"] != publish_result["generation_basename"]:
        raise GenerationPublisherError(
            "publish_g2_with_record: active manifest generation_basename "
            "does not match the publish result."
        )

    sidecar_path = os.path.join(output_dir, publish_result["generation_basename"])
    sidecar_sha_on_disk = igen.sha256_file(sidecar_path)
    if sidecar_sha_on_disk.lower() != plan_record["expected_sidecar_ordinary_sha256"].lower():
        raise GenerationPublisherError(
            "publish_g2_with_record: the real published sidecar's on-disk "
            "SHA-256 %r does not match the plan record's independently "
            "pre-derived expected_sidecar_ordinary_sha256 %r."
            % (sidecar_sha_on_disk, plan_record["expected_sidecar_ordinary_sha256"])
        )

    record = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "plan_record_path": plan_record_path,
        "plan_record_sha256": igen.sha256_file(plan_record_path),
        "g1_source_sha256": g1_sha,
        "g2_source_sha256": g2_sha,
        "g2_source_byte_length": len(g2_bytes),
        "g2_generation_basename": publish_result["generation_basename"],
        "g2_sidecar_sha256": sidecar_sha_on_disk,
        "manifest_sha256_after_publication": igen.sha256_file(os.path.join(output_dir, "manifest.json")),
        "manifest_source_sha256": active_manifest["source_sha256"],
        "manifest_generation_basename": active_manifest["generation_basename"],
        "publish_result": publish_result,
        "check_only_g1_result": check_g1,
        "check_only_g2_result": check_g2,
        "semantic_parity": parity,
    }
    _write_record_once(record_out_path, record)
    return record


def prepare_and_publish_g2(repo_root, g1_source_path, g2_source_out_path, plan_out_path,
                            output_dir, record_out_path, baseline_inventory,
                            expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    """R2 BLOCKER 1, Phase A end-to-end: construct G2 -> write the plan
    record (before any authority mutation, now baseline-path-bound per
    R3 BLOCKER 1) -> publish + publication record, in this exact order.
    Never touches the live Master."""
    source_facts = construct_and_write_g2_source(g1_source_path, g2_source_out_path, expected_g1_sha256)
    write_g2_plan_record(
        repo_root, g1_source_path, source_facts["g2_source_path"], plan_out_path, baseline_inventory,
        expected_g1_sha256,
    )
    publication_record = publish_g2_with_record(repo_root, plan_out_path, output_dir, record_out_path, expected_g1_sha256)
    return {
        "g2_source_facts": source_facts,
        "plan_record_path": plan_out_path,
        "publication_record": publication_record,
    }


# ---------------------------------------------------------------------
# R2 BLOCKER 1 -- PHASE B: the ONLY function in this entire deliverable
# that ever calls igen.perform_g1_to_g2_replacement(), i.e. the ONLY
# function that ever actually switches the LIVE canonical Master from
# G1 to G2. Deliberately separate from Phase A -- publish/record first,
# live Master activation second (R2 BLOCKER 7) -- so a failure here
# always has an already-written, independently recoverable G2 identity
# (the plan record + publication record) to fall back on.
# ---------------------------------------------------------------------
def activate_g2_master(master_path, authority_dir, baseline_inventory, publication_record,
                        activation_out_path, expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    # R2 BLOCKER 7: activation must never be attempted without prior,
    # independently recoverable G2 publication evidence -- refuse
    # immediately, before any path/hash check, if no valid publication
    # record was supplied at all.
    if not publication_record or "g2_source_sha256" not in publication_record:
        raise GenerationPublisherError(
            "activate_g2_master: no valid G2 publication record supplied "
            "-- activation must never be attempted before Phase A "
            "(prepare_and_publish_g2) has succeeded and produced one. "
            "STOP, no write performed."
        )

    # R2 BLOCKER 5: bind every path to the I1 baseline inventory BEFORE
    # trusting it for any read used for a mutation decision.
    baseline_master_path = (baseline_inventory or {}).get("master_path")
    baseline_authority_dir = (baseline_inventory or {}).get("authority_dir")
    master_path_matches_baseline = igen.path_matches_baseline(master_path, baseline_master_path)
    authority_dir_matches_baseline = igen.path_matches_baseline(authority_dir, baseline_authority_dir)
    if not master_path_matches_baseline:
        raise GenerationPublisherError(
            "activate_g2_master: supplied master_path %r does not match "
            "the I1 baseline inventory's recorded Master path %r -- STOP, "
            "no write performed." % (master_path, baseline_master_path)
        )
    if not authority_dir_matches_baseline:
        raise GenerationPublisherError(
            "activate_g2_master: supplied authority_dir %r does not "
            "match the I1 baseline inventory's recorded authority path "
            "%r -- STOP, no write performed." % (authority_dir, baseline_authority_dir)
        )

    pre_activation_master_sha256 = igen.sha256_file(master_path)
    if pre_activation_master_sha256.lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "activate_g2_master: live Master at %r is not exactly the "
            "expected canonical G1 (%r observed) -- STOP, no write "
            "performed." % (master_path, pre_activation_master_sha256)
        )

    g1_bytes = igen._read_bytes(master_path)
    rederived_g2_bytes = igen.construct_g2_bytes(g1_bytes)
    rederived_g2_sha256 = hashlib.sha256(rederived_g2_bytes).hexdigest()
    expected_g2_sha256 = publication_record["g2_source_sha256"]
    if rederived_g2_sha256.lower() != expected_g2_sha256.lower():
        raise GenerationPublisherError(
            "activate_g2_master: G2 re-derived from the CURRENT live G1 "
            "bytes hashes to %r, which does not match the publication "
            "record's own g2_source_sha256 %r -- STOP, no write "
            "performed." % (rederived_g2_sha256, expected_g2_sha256)
        )

    basename = publication_record.get("g2_generation_basename")
    if not (basename and igen.is_safe_bare_basename(basename)):
        raise GenerationPublisherError(
            "activate_g2_master: publication record's generation_basename "
            "%r is missing or unsafe -- STOP, no write performed." % (basename,)
        )
    sidecar_path = os.path.join(authority_dir, basename)
    if not os.path.isfile(sidecar_path):
        raise GenerationPublisherError(
            "activate_g2_master: the exact G2 authority artifact %r "
            "recorded by Phase A publication does not exist -- STOP, no "
            "write performed." % (sidecar_path,)
        )
    sidecar_sha_on_disk = igen.sha256_file(sidecar_path)
    if sidecar_sha_on_disk.lower() != (publication_record.get("g2_sidecar_sha256") or "").lower():
        raise GenerationPublisherError(
            "activate_g2_master: the G2 authority artifact's current "
            "on-disk SHA-256 %r does not match the publication record's "
            "recorded g2_sidecar_sha256 %r -- STOP, no write performed."
            % (sidecar_sha_on_disk, publication_record.get("g2_sidecar_sha256"))
        )

    operation_record = igen.perform_g1_to_g2_replacement(master_path, expected_g1_sha256)

    post_activation_master_sha256 = igen.sha256_file(master_path)
    success = (post_activation_master_sha256.lower() == expected_g2_sha256.lower())

    result = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "master_path": master_path,
        "authority_dir": authority_dir,
        "baseline_master_path": baseline_master_path,
        "baseline_authority_dir": baseline_authority_dir,
        "path_binding_checks": {
            "master_path_matches_baseline": master_path_matches_baseline,
            "authority_dir_matches_baseline": authority_dir_matches_baseline,
        },
        "expected_g1_sha256": expected_g1_sha256,
        "pre_activation_master_sha256": pre_activation_master_sha256,
        "rederived_g2_sha256": rederived_g2_sha256,
        "publication_record_g2_source_sha256": expected_g2_sha256,
        "operation_record": operation_record,
        "post_activation_master_sha256": post_activation_master_sha256,
        "success": success,
    }
    if not success:
        # Unreachable in practice -- perform_g1_to_g2_replacement()
        # already raises on any post-write mismatch -- but never write a
        # record claiming success that was not independently confirmed.
        raise GenerationPublisherError(
            "activate_g2_master: post-activation Master hash %r does not "
            "match the expected G2 %r -- refusing to report success; no "
            "activation record written." % (post_activation_master_sha256, expected_g2_sha256)
        )
    _write_record_once(activation_out_path, result)
    return result


# ---------------------------------------------------------------------
# R2 BLOCKER 8: independently re-verify the publication record BEFORE it
# is ever allowed to authorize a sidecar deletion. Never trusts an
# arbitrary/tampered record merely because the file exists -- every
# field checked here is either independently re-derived or re-observed
# right now, never taken on the record's own word alone.
# ---------------------------------------------------------------------
def _revalidate_publication_record_before_sidecar_deletion(publication_record, g1_bytes,
                                                             expected_g1_sha256, authority_dir):
    checks = {}
    record_g1_sha = publication_record.get("g1_source_sha256")
    checks["record_g1_sha_equals_canonical_g1"] = (
        isinstance(record_g1_sha, str) and record_g1_sha.lower() == expected_g1_sha256.lower()
    )

    rederived_g2_bytes = igen.construct_g2_bytes(g1_bytes)
    rederived_g2_sha = hashlib.sha256(rederived_g2_bytes).hexdigest()
    record_g2_sha = publication_record.get("g2_source_sha256")
    checks["rederived_g1_plus_lf_matches_record_g2_sha"] = (
        isinstance(record_g2_sha, str) and rederived_g2_sha.lower() == record_g2_sha.lower()
    )

    basename = publication_record.get("g2_generation_basename")
    checks["basename_is_safe"] = bool(basename) and igen.is_safe_bare_basename(basename)

    sidecar_exists = False
    sidecar_sha_matches = False
    if checks["basename_is_safe"]:
        sidecar_path = os.path.join(authority_dir, basename)
        sidecar_exists = os.path.isfile(sidecar_path)
        if sidecar_exists:
            try:
                actual_sha = igen.sha256_file(sidecar_path)
                sidecar_sha_matches = (
                    actual_sha.lower() == (publication_record.get("g2_sidecar_sha256") or "").lower()
                )
            except Exception:
                sidecar_sha_matches = False
    checks["exact_named_current_sidecar_exists"] = sidecar_exists
    checks["exact_current_sidecar_sha_matches_record"] = sidecar_sha_matches

    parity = publication_record.get("semantic_parity") or {}
    checks["recorded_semantic_parity_is_pass"] = parity.get("all_parity_checks_pass") is True

    checks["all_checks_pass"] = all(bool(v) for v in checks.values())
    return checks


# ---------------------------------------------------------------------
# R3 BLOCKER 2: determines whether -- and via which independently-
# verified source -- a G2 sidecar may safely be removed, WITHOUT
# requiring a publication record to exist at all (it may be absent
# because Phase A's own publication-record write failed AFTER
# publish_generation() had already mutated the authority directory --
# exactly the failure window R3 BLOCKER 2 closes). The plan record
# (written BEFORE any authority mutation, R2 BLOCKER 7) is an equally
# valid, independently-verifiable anchor for the sidecar's own expected
# identity (basename + ordinary/sidecar SHA), since both were computed
# from the SAME read-only check_only() operation the publication record
# itself would have recorded.
#
# R3 BLOCKER 3 (interaction): when BOTH records exist but disagree on
# the sidecar's own identity (basename or expected SHA), this NEVER
# guesses which one is authoritative -- it refuses deletion outright.
# When they agree on identity, EITHER source independently passing its
# own revalidation is sufficient to authorize deletion -- a tampered
# field in one record (e.g. a corrupted g2_source_sha256) does not
# block a cleanup the other, still-valid source confirms is correct.
# ---------------------------------------------------------------------
def _determine_sidecar_removal(authority_dir, g1_bytes, derived_g2_sha, plan_record, publication_record,
                                expected_g1_sha256):
    result = {"action": "skip", "basename": None, "expected_sha": None, "source": None, "reason": None,
              "checks": {}}

    pub_ok = False
    pub_basename = None
    pub_sha = None
    if publication_record is not None:
        pub_checks = _revalidate_publication_record_before_sidecar_deletion(
            publication_record, g1_bytes, expected_g1_sha256, authority_dir,
        )
        result["checks"]["publication_record_revalidation"] = pub_checks
        pub_ok = pub_checks["all_checks_pass"]
        pub_basename = publication_record.get("g2_generation_basename")
        pub_sha = publication_record.get("g2_sidecar_sha256")

    plan_ok = False
    plan_basename = None
    plan_sha = None
    if plan_record is not None:
        plan_checks = {}
        plan_checks["plan_g1_sha_matches_canonical"] = (
            (plan_record.get("g1_source_sha256") or "").lower() == expected_g1_sha256.lower()
        )
        plan_checks["plan_g2_sha_matches_derived"] = (
            (plan_record.get("expected_g2_source_sha256") or "").lower() == derived_g2_sha.lower()
        )
        parity = plan_record.get("expected_semantic_parity") or {}
        plan_checks["plan_semantic_parity_is_pass"] = parity.get("all_parity_checks_pass") is True
        plan_basename = plan_record.get("expected_generation_basename")
        plan_checks["plan_basename_is_safe"] = bool(plan_basename) and igen.is_safe_bare_basename(plan_basename)
        sidecar_exists = False
        sidecar_matches = False
        if plan_checks["plan_basename_is_safe"]:
            sidecar_path = os.path.join(authority_dir, plan_basename)
            sidecar_exists = os.path.isfile(sidecar_path)
            if sidecar_exists:
                try:
                    actual_sha = igen.sha256_file(sidecar_path)
                    sidecar_matches = (
                        actual_sha.lower() == (plan_record.get("expected_sidecar_ordinary_sha256") or "").lower()
                    )
                except Exception:
                    sidecar_matches = False
        plan_checks["exact_named_current_sidecar_exists"] = sidecar_exists
        plan_checks["exact_current_sidecar_sha_matches_plan"] = sidecar_matches
        plan_checks["all_checks_pass"] = all(bool(v) for v in plan_checks.values())
        result["checks"]["plan_record_revalidation"] = plan_checks
        plan_ok = plan_checks["all_checks_pass"]
        plan_sha = plan_record.get("expected_sidecar_ordinary_sha256")

    if publication_record is not None and plan_record is not None:
        if pub_basename != plan_basename or (pub_sha or "").lower() != (plan_sha or "").lower():
            result["reason"] = (
                "publication record and plan record disagree on the "
                "sidecar's own identity (basename or expected SHA) -- "
                "refusing to guess which is authoritative, no deletion."
            )
            return result
        if pub_ok or plan_ok:
            result["action"] = "remove"
            result["source"] = "publication_and_plan"
            result["basename"] = pub_basename
            result["expected_sha"] = pub_sha
        else:
            result["reason"] = (
                "both publication and plan records present but BOTH "
                "failed independent revalidation"
            )
        return result

    if publication_record is not None:
        if pub_ok:
            result["action"] = "remove"
            result["source"] = "publication_record"
            result["basename"] = pub_basename
            result["expected_sha"] = pub_sha
        else:
            result["reason"] = (
                "publication record present but failed independent "
                "revalidation, and no plan record was supplied to "
                "corroborate"
            )
        return result

    if plan_record is not None:
        if plan_ok:
            result["action"] = "remove"
            result["source"] = "plan_record"
            result["basename"] = plan_basename
            result["expected_sha"] = plan_sha
        else:
            result["reason"] = "plan record present but failed independent revalidation"
        return result

    result["reason"] = (
        "neither a publication record nor a plan record was supplied -- "
        "no sidecar identity known"
    )
    return result


# ---------------------------------------------------------------------
# BLOCKER 8/9 (round 1), hardened per R2 BLOCKERS 5/8 and R3 BLOCKERS
# 2/3: mandatory restoration/finalization. Usable even if I2 never
# began, AND even if Phase A's own publication-record write failed
# after publish_generation() had already mutated the authority
# directory -- only requires a live Master that is currently exact G1
# or the INDEPENDENTLY RE-DERIVED G2 (G1 + one ASCII LF, never the
# publication record's own claimed g2_source_sha256 -- R3 BLOCKER 3).
# ---------------------------------------------------------------------
def finalize_restoration(repo_root, master_path, authority_dir, g1_source_path, plan_record, publication_record,
                          baseline_inventory, finalization_out_path,
                          expected_g1_sha256=igen.EXPECTED_CANONICAL_G1_MASTER_SHA256):
    # R2 BLOCKER 5: bind paths to the I1 baseline inventory BEFORE
    # trusting them for any write.
    baseline_master_path = (baseline_inventory or {}).get("master_path")
    baseline_authority_dir = (baseline_inventory or {}).get("authority_dir")
    master_path_matches_baseline = igen.path_matches_baseline(master_path, baseline_master_path)
    authority_dir_matches_baseline = igen.path_matches_baseline(authority_dir, baseline_authority_dir)
    if not master_path_matches_baseline:
        raise GenerationPublisherError(
            "finalize_restoration: master_path %r does not match the I1 "
            "baseline inventory's recorded Master path %r -- STOP, no "
            "write performed." % (master_path, baseline_master_path)
        )
    if not authority_dir_matches_baseline:
        raise GenerationPublisherError(
            "finalize_restoration: authority_dir %r does not match the "
            "I1 baseline inventory's recorded authority path %r -- STOP, "
            "no write performed." % (authority_dir, baseline_authority_dir)
        )

    current_sha = igen.sha256_file(master_path)
    result = {
        "wall_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epoch": time.time(),
        "master_path": master_path,
        "authority_dir": authority_dir,
        "path_binding_checks": {
            "master_path_matches_baseline": master_path_matches_baseline,
            "authority_dir_matches_baseline": authority_dir_matches_baseline,
        },
        "observed_master_sha256_at_start": current_sha,
    }

    g1_bytes = igen._read_bytes(g1_source_path)
    g1_sha = hashlib.sha256(g1_bytes).hexdigest()
    if g1_sha.lower() != expected_g1_sha256.lower():
        raise GenerationPublisherError(
            "finalize_restoration: g1_source_path does not hash to the "
            "expected canonical G1 -- STOP, no write performed."
        )

    # R3 BLOCKER 3: independently re-derive G2 identity from the G1 bytes
    # ALREADY verified above -- never trust publication_record's own
    # claimed g2_source_sha256 for the Master-restoration decision. A
    # corrupt/tampered publication record must not prevent safe G2->G1
    # restoration.
    derived_g2_bytes = igen.construct_g2_bytes(g1_bytes)
    derived_g2_sha = hashlib.sha256(derived_g2_bytes).hexdigest()
    result["derived_g2_sha256"] = derived_g2_sha

    corroboration = {}
    if plan_record is not None:
        corroboration["plan_g2_sha_matches_derived"] = (
            (plan_record.get("expected_g2_source_sha256") or "").lower() == derived_g2_sha.lower()
        )
    if publication_record is not None:
        corroboration["publication_g2_sha_matches_derived"] = (
            (publication_record.get("g2_source_sha256") or "").lower() == derived_g2_sha.lower()
        )
    result["g2_identity_corroboration"] = corroboration

    if current_sha.lower() == expected_g1_sha256.lower():
        result["master_restore_performed"] = False
        result["master_restore_reason"] = "already exact G1"
    elif current_sha.lower() == derived_g2_sha.lower():
        restore_record = igen.perform_g2_to_g1_restoration(
            master_path, g1_bytes, derived_g2_sha, expected_g1_sha256,
        )
        result["master_restore_performed"] = True
        result["master_restore_record"] = restore_record
    else:
        raise GenerationPublisherError(
            "finalize_restoration: live Master hash %r is neither the "
            "expected G1 %r nor the independently re-derived G2 (G1+LF) "
            "%r -- STOP, no write performed." % (current_sha, expected_g1_sha256, derived_g2_sha)
        )

    republish_result = publish_generation(repo_root, g1_source_path, authority_dir)
    result["g1_republish_result"] = republish_result

    # R3 BLOCKER 2: recover the sidecar's own identity from EITHER the
    # publication record OR the plan record (written before any
    # authority mutation, so it survives a publication-record write
    # failure) -- never require the publication record merely to
    # recover from a Phase-A partial failure. R3 BLOCKER 3: disagreement
    # between the two never authorizes a guess.
    removal_plan = _determine_sidecar_removal(
        authority_dir, g1_bytes, derived_g2_sha, plan_record, publication_record, expected_g1_sha256,
    )
    result["sidecar_removal_plan"] = removal_plan
    if removal_plan["action"] == "remove" and os.path.isfile(os.path.join(authority_dir, removal_plan["basename"] or "")):
        removal_record = igen.remove_exact_sidecar(authority_dir, removal_plan["basename"], removal_plan["expected_sha"])
        result["g2_sidecar_removed"] = True
        result["g2_sidecar_removal_record"] = removal_record
    else:
        result["g2_sidecar_removed"] = False
        result["g2_sidecar_removal_note"] = removal_plan.get("reason") or "sidecar already absent -- nothing to remove"

    final_inventory = igen.capture_live_state_inventory(master_path, authority_dir)
    comparison = igen.compare_inventories(baseline_inventory, final_inventory)
    result["final_inventory"] = final_inventory
    result["comparison_to_pre_i_baseline"] = comparison
    result["exact_match"] = comparison["exact_match"]

    _write_record_once(finalization_out_path, result)
    return result


# ---------------------------------------------------------------------
# CLI dispatcher.
# ---------------------------------------------------------------------
def _cli_main(argv):
    import argparse

    parser = argparse.ArgumentParser(
        description="Repo-side-only Python 3 publisher/finalizer for roadmap item I."
    )
    parser.add_argument("--repo-root", required=True)
    sub = parser.add_subparsers(dest="op")

    p_check = sub.add_parser("check-only")
    p_check.add_argument("--source", required=True)
    p_check.add_argument("--out", required=True)

    p_prep = sub.add_parser("prepare-publish-g2")
    p_prep.add_argument("--g1-source", required=True)
    p_prep.add_argument("--g2-source-out", required=True)
    p_prep.add_argument("--plan-out", required=True)
    p_prep.add_argument("--output-dir", required=True)
    p_prep.add_argument("--record-out", required=True)
    p_prep.add_argument("--baseline-inventory", required=True)

    p_activate = sub.add_parser("activate-g2")
    p_activate.add_argument("--master", required=True)
    p_activate.add_argument("--authority-dir", required=True)
    p_activate.add_argument("--baseline-inventory", required=True)
    p_activate.add_argument("--publication-record", required=True)
    p_activate.add_argument("--out", required=True)

    p_finalize = sub.add_parser("finalize")
    p_finalize.add_argument("--master", required=True)
    p_finalize.add_argument("--authority-dir", required=True)
    p_finalize.add_argument("--g1-source", required=True)
    p_finalize.add_argument("--plan-record", required=False, default=None)
    p_finalize.add_argument("--publication-record", required=False, default=None)
    p_finalize.add_argument("--baseline-inventory", required=True)
    p_finalize.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    validate_repo_root(args.repo_root)

    if args.op == "check-only":
        result = check_only_source(args.repo_root, args.source)
        with open(args.out, "wb") as f:
            f.write(json.dumps(result, indent=2, sort_keys=True).encode("utf-8"))
    elif args.op == "prepare-publish-g2":
        with open(args.baseline_inventory, "rb") as f:
            baseline_inventory = json.loads(f.read().decode("utf-8"))
        result = prepare_and_publish_g2(
            args.repo_root, args.g1_source, args.g2_source_out, args.plan_out,
            args.output_dir, args.record_out, baseline_inventory,
        )
    elif args.op == "activate-g2":
        with open(args.baseline_inventory, "rb") as f:
            baseline_inventory = json.loads(f.read().decode("utf-8"))
        with open(args.publication_record, "rb") as f:
            publication_record = json.loads(f.read().decode("utf-8"))
        result = activate_g2_master(
            args.master, args.authority_dir, baseline_inventory, publication_record, args.out,
        )
    elif args.op == "finalize":
        plan_record = None
        if args.plan_record:
            with open(args.plan_record, "rb") as f:
                plan_record = json.loads(f.read().decode("utf-8"))
        publication_record = None
        if args.publication_record:
            with open(args.publication_record, "rb") as f:
                publication_record = json.loads(f.read().decode("utf-8"))
        with open(args.baseline_inventory, "rb") as f:
            baseline_inventory = json.loads(f.read().decode("utf-8"))
        result = finalize_restoration(
            args.repo_root, args.master, args.authority_dir, args.g1_source,
            plan_record, publication_record, baseline_inventory, args.out,
        )
    else:
        parser.print_help()
        return 2

    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv[1:]))
