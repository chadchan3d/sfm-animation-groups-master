# -*- coding: utf-8 -*-
"""GATE C0.2 -- QUALIFICATION-ONLY explicit Normalizer-compatible source
profile check. NOT production code, NOT a binary-format change, NOT a
Normalizer change. Defines, as an executable, testable boundary, exactly
which sources the Normalizer adapter is claimed to support -- everything
else is explicitly refused rather than silently accepted or silently
normalized.

Per Astra Round 2 / Gate C0 findings:
  - the real Normalizer's tokenizer (`stream_tokens`) resolves backslash
    escapes (\\n -> newline, \\t -> tab, any other \\X -> literal X);
  - the generic shared core (`sfm_master_core`) and this sidecar's own
    tokenizer preserve backslash spelling verbatim (no escape resolution);
  - the real official Master contains zero backslash bytes, so this
    divergence is real but currently dormant for that one source;
  - the Normalizer's own parser requires the literal top-level wrapper name
    `groupFile` (`if take() != "groupFile": raise ProbeError(...)`).

This module does not change how the generic compiler/reader parse or
represent ANY source -- it only decides, before ever handing a source to
the Normalizer-view builder, whether that source is inside the declared
Normalizer-compatible profile. A refused source is refused explicitly
(raises `NormalizerSourceProfileRefused`) -- it is never silently accepted,
never silently unescaped/renamed, and never collapses into `MasterUnknown`.
"""

REQUIRED_WRAPPER = u"groupFile"


class NormalizerSourceProfileRefused(Exception):
    """Raised when a source falls outside the declared Normalizer-compatible
    profile. Distinct from `MasterUnknown` (an authoritative "not present"
    answer) and from `AuthorityUnavailable` (a corrupted/closed provider) --
    this is a THIRD, explicit category: "this source was never accepted as
    Normalizer-compatible in the first place." """


def check_normalizer_source_profile(source_bytes, wrapper_name):
    """`source_bytes`: the raw Master source bytes (as read from disk,
    before any parsing). `wrapper_name`: the top-level group name the
    generic compiler/reader already determined for this source (obtained
    independently of this check -- this function does not parse anything
    itself).

    Raises `NormalizerSourceProfileRefused` if:
      (a) the wrapper is not exactly `groupFile` (the Normalizer's own
          parser hard-requires this literal name); or
      (b) the raw source contains any backslash byte (0x5C) -- the one
          concrete, currently-real divergence between the Normalizer's own
          tokenizer and the generic/sidecar tokenizer's escape handling.

    Does not inspect anything else, does not attempt to detect every
    theoretically possible divergence -- only the two established,
    evidence-backed ones. Silence (no exception) means the source is
    declared inside the current Normalizer-compatible profile; it does not
    mean "provably identical to the Normalizer in every respect."
    """
    if wrapper_name != REQUIRED_WRAPPER:
        raise NormalizerSourceProfileRefused(
            "Normalizer adapter profile requires wrapper %r, found %r -- "
            "refused before any view construction, not silently accepted "
            "or renamed." % (REQUIRED_WRAPPER, wrapper_name)
        )
    if b"\\" in source_bytes:
        raise NormalizerSourceProfileRefused(
            "Normalizer adapter profile refuses any source containing a "
            "backslash byte: the real Normalizer's own tokenizer resolves "
            "backslash escapes (\\n/\\r/\\t/other) while the generic "
            "sidecar tokenizer preserves backslash spelling verbatim -- "
            "this source's escape interpretation would diverge between "
            "the two paths. Refused explicitly, not silently unescaped."
        )
