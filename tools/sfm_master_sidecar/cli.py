# -*- coding: utf-8 -*-
"""Public compiler CLI. Python 3 only.

    python -m tools.sfm_master_sidecar.cli MASTER_TXT --output OUTPUT_DIR [--check-only] [--official-policy]

Depends on nothing beyond the standard library plus this package's own
modules -- no Git, no Claude Code, no SFM installation, no repository
current working directory, and no hardcoded official source SHA. Every
path is taken explicitly from the command line and resolved relative to the
CALLER's cwd (ordinary `argparse`/`pathlib` behavior), never relative to
this package's own location.

Exit-code contract (Phase B2E Part 31):
    0  success
    2  usage / input path error (bad arguments, source file not found)
    3  source grammar / sidecar-profile rejection
    4  compilation / self-validation / semantic-parity failure
    5  publication / locking failure
"""

import argparse
import sys

from . import compiler
from . import publisher


EXIT_SUCCESS = 0
EXIT_USAGE = 2
EXIT_SOURCE_REJECTED = 3
EXIT_COMPILE_FAILED = 4
EXIT_PUBLICATION_FAILED = 5


def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="python -m tools.sfm_master_sidecar.cli",
        description="Compile an SFM Master TXT into the experimental packed sidecar format.",
    )
    p.add_argument("source", help="path to the Master TXT to compile")
    p.add_argument("--output", required=False, default=None,
                    help="output namespace directory (required unless --check-only)")
    p.add_argument("--check-only", action="store_true",
                    help="parse/compile/self-validate only; never touches --output, never publishes")
    p.add_argument("--official-policy", action="store_true",
                    help="additionally require tools/validate_master.py's official-release policy to PASS")
    p.add_argument("--lock-timeout", type=float, default=30.0,
                    help="seconds to wait for the publisher lock before failing (default: 30)")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    if not args.check_only and not args.output:
        sys.stderr.write("error: --output is required unless --check-only is given\n")
        return EXIT_USAGE

    try:
        with open(args.source, "rb"):
            pass
    except OSError as exc:
        sys.stderr.write("error: cannot open source path %r: %s\n" % (args.source, exc))
        return EXIT_USAGE

    try:
        if args.check_only:
            result = publisher.check_only(args.source, official_policy=args.official_policy)
            outcome = result.outcome
            sys.stdout.write(
                "CHECK-ONLY OK: source_sha256=%s groups=%d occurrences=%d sidecar_sha256=%s "
                "sidecar_bytes=%d\n" % (
                    outcome.snapshot.sha256_hex, len(outcome.result.groups), len(outcome.result.occurrences),
                    outcome.ordinary_sha256, len(outcome.blob),
                )
            )
            return EXIT_SUCCESS

        pub_result = publisher.publish(
            args.source, args.output, official_policy=args.official_policy, lock_timeout=args.lock_timeout,
        )
        sys.stdout.write(
            "PUBLISHED: generation=%s reused=%s manifest=%s\n" % (
                pub_result.generation_basename, pub_result.reused, pub_result.manifest_path,
            )
        )
        return EXIT_SUCCESS

    except compiler.SourceGrammarError as exc:
        sys.stderr.write("error: source rejected (grammar): %s\n" % exc)
        return EXIT_SOURCE_REJECTED
    except Exception as exc:
        from . import writer as writer_module
        if isinstance(exc, writer_module.SidecarProfileError):
            sys.stderr.write("error: source rejected (sidecar profile): %s\n" % exc)
            return EXIT_SOURCE_REJECTED
        if isinstance(exc, compiler.OfficialPolicyRejectedError):
            sys.stderr.write("error: source rejected (official policy): %s\n" % exc)
            return EXIT_SOURCE_REJECTED
        if isinstance(exc, compiler.SelfValidationError):
            sys.stderr.write("error: compilation self-validation failed: %s\n" % exc)
            return EXIT_COMPILE_FAILED
        if isinstance(exc, writer_module.SidecarFieldOverflowError):
            sys.stderr.write("error: compilation failed (field/resource limit): %s\n" % exc)
            return EXIT_COMPILE_FAILED
        if isinstance(exc, publisher.PublicationError):
            sys.stderr.write("error: publication failed: %s\n" % exc)
            return EXIT_PUBLICATION_FAILED
        # Anything else is unexpected -- surface it plainly rather than
        # misclassifying it under one of the above codes.
        sys.stderr.write("error: unexpected failure: %r\n" % (exc,))
        return EXIT_PUBLICATION_FAILED if not args.check_only else EXIT_COMPILE_FAILED


if __name__ == "__main__":
    sys.exit(main())
