# Astra O1 Audit Prompt

Read `ASTRA_O1_REVIEW_ENTRYPOINT.md` first for orientation, baseline commit, governing rule, and the
starting manifest. This document is the audit instruction itself.

## Core instruction

> Audit this repository commit directly. Treat the commit as the immutable review baseline. Read O1
> first, then independently inspect every production source file and dependency necessary to verify or
> challenge its findings. Do not rely on O1's characterization where direct source inspection can
> answer the question.

Baseline commit: `dc92623f17c6b151b7bf5f6ed4ab65cb3f1e29ea`

Start with `real_sfm_qualification/o1_audit/O1_REBUILD_NORMALIZER_MATERIAL_REDUNDANCY_AUDIT.md`, then
go to the actual source it cites — `audit_external_runtime/Rebuild_Control_Groups_Normalizer.py` and
the authority/broker/integration files listed in the entrypoint's starting manifest. Where O1 cites a
line number or a function's behavior, verify it against the real file at this commit rather than
trusting the description.

## Governing optimization rule (repeated, applies to every answer below)

> Tangible savings, demonstrated redundancy, zero functional compromise.

No micro-optimization campaign, no functionality reduction, no semantic weakening, no validation
reduction, no model-support reduction, no stale caching. No implementation is authorized by this
review — this is an audit of an audit.

## Questions Astra must answer

1. **Did O1 miss any material redundancies or lifetime problems?**
2. **Are any O1 candidates falsely labeled redundant despite correctness dependencies?**
3. **Are there important Rebuild/Normalizer overlaps O1 missed?**
4. **Are any proposed measurement directions unsafe or misleading?**
5. **Which candidates, if any, deserve runtime measurement only?**

## Per-candidate classification

For each of O1's three candidates — (1) the retained/dead `self.work` `aset` reference, (2) repeated
full recursive semantic-tree captures, (3) unconditional warm-path classification/planning/composer —
classify it as exactly one of:

- `STRONG MEASUREMENT CANDIDATE`
- `PLAUSIBLE BUT NEEDS MORE STATIC PROOF`
- `LOW-VALUE / REJECT`
- `UNSAFE DIRECTION`

Also identify any material candidates O1 missed entirely, with the same evidentiary standard O1 itself
was held to (exact file:line citations, a stated correctness dependency, and what proof would be
required before any change).

## Explicitly out of scope for this review

Do not:

- Write or propose code fixes.
- Edit production, integration, or lifecycle code.
- Design optimizations prematurely.
- Rank candidates numerically (use the four-category classification above instead).
- Chase trivial/cosmetic savings that fail the governing optimization rule.

## Reporting

Return findings as a structured response addressing the five core questions and the per-candidate
classification above, each claim grounded in exact file:line citations from the repository at the
baseline commit — not from `O1`'s own prose, and not from any summary document.
