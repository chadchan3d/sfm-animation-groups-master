I need you to maintain my SFM animation-groups master file located here:

E:\SFM Animation Group Master\sfm\\\_defaultanimationgroups.txt

This is a precision text-editing task. The existing Master file is authoritative. The goal is to eliminate prediction-based editing errors by performing every modification through deterministic Python code, validating the actual file written to disk, and always continuing from the same canonical Master filepath.

**\*\*# 1. Canonical Working File\*\***

The exact Master filepath I give you is the **\*\*\\\*\\\*single canonical working file\\\*\\\*\*\***.

After every successful edit:

\\\* that same filepath must contain the newest validated state

\\\* that same filepath becomes the source for the next edit

\\\* do not create a sequence of \\\`v2\\\`, \\\`v3\\\`, \\\`v4\\\` working Masters unless I explicitly ask for versioned exports

Temporary files and backups are safety mechanisms only. They are not alternate working Masters.

Every new edit request must begin by re-reading the canonical Master from disk.

Do not rely on conversation memory, an old in-memory copy, a previous temporary file, or a backup to determine current state.

The file itself is the source of truth.

**\*\*# 1a. External Reference Files (Non-Canonical)\*\***

reference\sfm_defaultanimationgroups_silkworm.txt is a read-only external reference Master ("Silkworm's Master"), representing Silkworm's **\*\*January 31, 2026 update\*\***. No separate version identifier is present. It exists for comparison and historical/hierarchy confirmation only.

\* sfm_defaultanimationgroups.txt remains the single canonical Master.

\* The Silkworm reference file is never edited, normalized, reformatted, or validated using canonical-Master syntax rules (tab separators, indentation depth, encoding, or newline-style requirements).

\* The Silkworm file is never used as the source for ordinary edits to the canonical Master.

\* It may be consulted when I explicitly request comparison, historical evidence, or confirmation of intended SFM group hierarchy, or when this contract specifically requires reference validation, such as diagnosing a structural hierarchy anomaly.

\* Differences between Silkworm and the canonical Master in capitalization, separators, newline style, directives, group structure, or formatting are not defects to reconcile automatically.

\* The presence of this reference file does not weaken or modify the single-canonical-Master rule in Section 1.

**\*\*# 2. Programmatic Editing Only\*\***

For every modification:

1\\. Re-read the current canonical Master from disk.

2\\. Inspect and parse it.

3\\. Determine the requested structural operation.

4\\. Write or use a local Python script to perform that operation.

5\\. Execute the script against the current canonical Master.

6\\. Write the candidate result to a temporary file.

7\\. Re-open that temporary file from disk.

8\\. Run independent validation against the actual temporary file.

9\\. If validation passes, replace the canonical Master with the validated candidate.

10\\. Re-open the newly replaced canonical Master and run final sanity checks.

11\\. Report the machine-derived validation results.

Do not rewrite or regenerate the Master through ordinary LLM text generation.

Do not manually reproduce large sections of the file.

Prefer reusable deterministic Python helpers over brittle one-off text replacements.

**\*\*# 3. Preserve Everything Not Explicitly Changed\*\***

The existing file is authoritative.

Unless I explicitly request otherwise, preserve:

\\\* encoding

\\\* newline style

\\\* comments

\\\* blank lines

\\\* capitalization

\\\* spelling

\\\* punctuation

\\\* underscores

\\\* spaces inside control names

\\\* existing control order

\\\* existing group order

\\\* leading indentation

\\\* tabs versus spaces

\\\* unrelated whitespace

\\\* all unrelated lines

Do not run a formatter.

Do not normalize the file.

Do not clean up unrelated content merely because it looks inconsistent.

**\*\*# 4. Exact Control Syntax\*\***

A control line has this syntax:

\\\`\\\`\\\`text

"control"       "NAME"

\\\`\\\`\\\`

There are exactly **\*\*\\\*\\\*two literal tab characters\\\*\\\*\*\*** between \\\`"control"\\\` and \\\`"NAME"\\\`.

Conceptually:

\\\`\\\`\\\`python

'"control"\t\t"NAME"'

\\\`\\\`\\\`

These two separator tabs are independent of the leading indentation before \\\`"control"\\\`.

Do not replace required tabs with spaces.

**\*\*# 5. Structural Indentation Rule\*\***

Indentation follows group nesting depth.

For a group:

\\\`\\\`\\\`text

\\\<GROUP\\\_INDENT>"GroupName"

\\\<GROUP\\\_INDENT>{

\\\<GROUP\\\_INDENT + 1 TAB>"control"     "NAME"

\\\<GROUP\\\_INDENT>}

\\\`\\\`\\\`

Therefore:

\\\* the group name uses its current indentation

\\\* the group's opening \\\`{\\\` uses the same indentation

\\\* the group's matching closing \\\`}\\\` uses the same indentation

\\\* every direct member of that group uses exactly **\*\*\\\*\\\*one additional leading tab\\\*\\\*\*\***

Direct members include:

\\\* \\\`"control"\\\` lines

\\\* \\\`"groupColor"\\\` lines

\\\* child group names

A child group's own braces use the same indentation as the child group name, and its contents gain another tab.

Example:

\\\`\\\`\\\`text

    "RigArms"

    {

        "control"       "Example"

        "ChildGroup"

        {

            "control"       "Example2"

        }

    }

\\\`\\\`\\\`

Here:

\\\`\\\`\\\`text

RigArms                = 1 leading tab

direct RigArms members = 2 leading tabs

ChildGroup             = 2 leading tabs

ChildGroup members     = 3 leading tabs

\\\`\\\`\\\`

When inserting a direct member:

\\\`\\\`\\\`python

content\\\_indent = group\\\_indent + "\t"

\\\`\\\`\\\`

Do not infer indentation from an arbitrary nearby control because it may belong to a nested child group.

For an empty group:

\\\`\\\`\\\`python

content\\\_indent = opening\\\_brace\\\_indent + "\t"

\\\`\\\`\\\`

If I explicitly request:

\\\`\\\`\\\`text

three leading tabs

\\\`\\\`\\\`

or:

\\\`\\\`\\\`text

four leading tabs

\\\`\\\`\\\`

that explicit instruction overrides the structural default for those named lines.

For example, four leading tabs means:

\\\`\\\`\\\`python

'\t\t\t\t"control"\t\t"NAME"'

\\\`\\\`\\\`

**\*\*# 6. Exact Group-Color Syntax\*\***

A group-color line has this syntax:

\\\`\\\`\\\`text

"groupColor"        "R G B A"

\\\`\\\`\\\`

There are exactly **\*\*\\\*\\\*two literal tabs\\\*\\\*\*\*** between \\\`"groupColor"\\\` and the quoted RGBA value.

Example:

\\\`\\\`\\\`text

"groupColor"        "255 128 32 255"

\\\`\\\`\\\`

The leading indentation follows the same structural rule as controls.

A \\\`groupColor\\\` is a direct member of its group, so it receives exactly one additional leading tab beyond the group's indentation.

Example:

\\\`\\\`\\\`text

    "Eyes"

    {

        "groupColor"        "255 128 32 255"

        "control"       "Example"

    }

\\\`\\\`\\\`

When I instruct you to add or set a \\\`groupColor\\\`:

\\\* it must be the first content line immediately after the target group's opening \\\`{\\\`

\\\* do not place it at the bottom

\\\* do not place it after controls

\\\* do not add a second \\\`groupColor\\\` if one already exists

\\\* if one already exists, replace its value unless I explicitly say otherwise

\\\* after the operation, the target group must contain exactly one \\\`groupColor\\\`

**\*\*# 7. Parse Groups Structurally\*\***

Never identify group boundaries using a naive search for the next \\\`{\\\` or \\\`}\\\`.

The file contains nested groups.

Your Python parser must identify:

1\\. the requested group

2\\. its opening brace

3\\. its matching closing brace

4\\. its nesting depth

5\\. its direct contents

Use brace depth or an equivalent structural parsing method.

The closing brace for a group is the brace that returns to the nesting depth that existed before that group's opening \\\`{\\\`.

Do not mistake a nested child group's closing brace for the target group's closing brace.

When useful, identify a group by its full path:

\\\`\\\`\\\`text

Face > Eyes

\\\`\\\`\\\`

rather than only:

\\\`\\\`\\\`text

Eyes

\\\`\\\`\\\`

If a requested group name resolves to more than one possible group and I have not given enough information to distinguish them:

**\*\*\\\*\\\*STOP.\\\*\\\*\*\***

Report the ambiguity.

Do not guess.

**\*\*## Hierarchy Validation\*\***

Balanced brace counts are necessary but not sufficient for structural correctness.

For structural validation:

\* record each named group's full parent path

\* compare parsed brace nesting with indentation depth

\* detect any group whose parsed parent conflicts with its apparent structural indentation

\* identify the first point where parsed hierarchy and indentation diverge

\* do not repair a missing or misplaced brace merely by making the global brace counts balance

\* preserve existing group parent paths unless I explicitly request a hierarchy change

\* for ordinary edits, every unaffected named group must retain the same full parent path before and after the edit

If a structural brace anomaly is detected:

1\. Do not repair it automatically.

2\. Identify the first location where the parsed nesting depth diverges from the file's established indentation/group hierarchy.

3\. Inspect the transition immediately before that divergence.

4\. A group whose indentation indicates it is a sibling must not silently become a child merely because an earlier closing brace is missing.

5\. Where an authoritative reference Master is available, use it to confirm intended group hierarchy before proposing a structural repair.

6\. Show the proposed exact brace insertion/removal location and the resulting before/after hierarchy.

7\. STOP and wait for explicit approval before performing the structural repair.

Example:

\`\`\`text

Expected:

groupFile > RigLegs

Invalid unintended result:

groupFile > RigArms > RigLegs

\`\`\`

The second structure is a failure even if total \`{\` and \`}\` counts are balanced.

After the canonical Master is structurally valid, ordinary edits must preserve:

\`\`\`text

[ ] Equal opening and closing brace counts

[ ] Stack depth = 0 at EOF

[ ] No brace underflow

[ ] Intended group parent paths

[ ] Unaffected named groups retain their prior parent paths

[ ] Parsed nesting and structural indentation remain consistent

\`\`\`

**\*\*# 8. Default Placement for New Controls\*\***

Unless I explicitly specify another location:

\\\* a genuinely new control goes at the absolute bottom of the target group

\\\* "bottom" means immediately before that target group's matching closing brace

\\\* it must be a direct member of that group

\\\* it must not accidentally be inserted into a child group

\\\* it must not appear after the closing brace

\\\* it must use the target group's direct-content indentation

\\\* do not sort or reorganize other controls

**\*\*# 9. Absolute Duplicate Rule\*\***

Exact control lines must not have duplicates.

An exact control literal belongs in one location in the Master.

For every control involved in an operation, search the **\*\*\\\*\\\*entire file\\\*\\\*\*\***, not merely the destination group.

Before adding:

1\\. count the exact literal globally

2\\. determine whether it already exists

3\\. do not blindly append another copy

After editing:

\\\`\\\`\\\`text

final global occurrence count = exactly 1

\\\`\\\`\\\`

for every control touched by the operation.

A count of:

\\\`\\\`\\\`text

0

\\\`\\\`\\\`

means the control is missing.

A count greater than:

\\\`\\\`\\\`text

1

\\\`\\\`\\\`

means the control is duplicated.

Either condition is a failed edit.

See also Section 24 for the related native-Rebuild casefold check, which governs cross-path distribution of case-equivalent spellings rather than exact-string duplication.

**\*\*# 10. Move Operations\*\***

A move means:

\\\`\\\`\\\`text

REMOVE OLD OCCURRENCE

\\+

INSERT SAME CONTROL AT NEW LOCATION

\\\`\\\`\\\`

It never means:

\\\`\\\`\\\`text

COPY OLD OCCURRENCE

\\+

APPEND SECOND COPY

\\\`\\\`\\\`

For every move:

1\\. locate every exact existing occurrence globally

2\\. confirm the source condition is understood

3\\. remove the old occurrence

4\\. insert one occurrence at the requested destination

5\\. re-open the candidate file

6\\. verify the exact literal appears once globally

7\\. verify that one occurrence is at the requested destination

Do not consider a move successful merely because the new copy exists.

The old location must also be checked.

**\*\*# 11. Named Block Moves\*\***

If I give you several exact control names and tell you to move them as a block, treat the request as:

**\*\*\\\*\\\*EXTRACT → REMOVE → INSERT → VERIFY\\\*\\\*\*\***

Procedure:

1\\. Resolve every requested literal exactly.

2\\. Preserve every literal exactly as written.

3\\. Remove the previous occurrence of every block member.

4\\. Insert the entire block once at the requested destination.

5\\. Preserve the exact internal order I supplied.

6\\. Verify the block is contiguous.

7\\. Verify every member appears exactly once globally.

8\\. Verify none remain at their previous locations.

Do not:

\\\* alphabetize unless explicitly requested

\\\* normalize spelling

\\\* normalize capitalization

\\\* interleave existing controls into the block

\\\* leave old copies behind

\\\* append duplicates

\\\* divide the block unless explicitly instructed

If I say:

\\\`\\\`\\\`text

Move this whole block to the bottom of Clothing

\\\`\\\`\\\`

the result must structurally be:

\\\`\\\`\\\`text

"Clothing"

{

    ...existing Clothing content...

    ...entire requested block...

}

\\\`\\\`\\\`

The entire requested stack must be together at the bottom.

It is not sufficient for those controls merely to occur somewhere inside Clothing.

**\*\*# 12. Literal Strings Are Authoritative\*\***

Never correct a control name because it appears misspelled.

Examples of literals that may intentionally look unusual include:

\\\`\\\`\\\`text

Hearth

REyecose

chick

\\\`\\\`\\\`

If that is the actual literal, preserve it.

Do not infer that:

\\\`\\\`\\\`text

Hearth

\\\`\\\`\\\`

should be:

\\\`\\\`\\\`text

Heart

\\\`\\\`\\\`

Case is significant.

Spaces are significant.

Underscores are significant.

Numbers are significant.

Punctuation is significant.

Do not substitute a visually similar or semantically similar control.

Case significance here concerns literal preservation during edits: never rewrite a control's case while transcribing or moving it. It does not mean case differences justify placing case-equivalent spellings at different taxonomy destinations — see Section 24.

**\*\*# 13. Exact-Line Matching\*\***

When I provide:

\\\`\\\`\\\`text

"control"       "NAME"

\\\`\\\`\\\`

treat the quoted control literal as exact.

When checking duplicates, distinguish between:

\\\`\\\`\\\`text

"control"       "NAME"

\\\`\\\`\\\`

and any similar but non-identical names.

Do not use loose substring matching to determine whether an exact control already exists.

A search for:

\\\`\\\`\\\`text

Heart

\\\`\\\`\\\`

must not be treated as proof about:

\\\`\\\`\\\`text

Hearth

\\\`\\\`\\\`

Use exact comparisons for editing and validation.

**\*\*# 14. Assertions Before Writing\*\***

Before changing the file, assert every assumption required by the requested operation.

Examples:

\\\`\\\`\\\`text

Target group exists

Target group is structurally unambiguous

Brace structure is parseable

Expected source control exists for a move

Requested destination can be identified

Requested block members can all be resolved

\\\`\\\`\\\`

If a required assertion fails:

**\*\*\\\*\\\*STOP WITHOUT PROMOTING THE CANDIDATE.\\\*\\\*\*\***

Report exactly what failed.

Do not make a best guess.

**\*\*# 15. Atomic Write Workflow\*\***

The canonical Master must remain safe throughout each operation.

For every edit:

1\\. Read the current canonical Master from disk.

2\\. Perform the requested transformation in memory.

3\\. Write the candidate to a temporary file, for example:

\\\`\\\`\\\`text

sfm\\\_defaultanimationgroups.txt.tmp

\\\`\\\`\\\`

4\\. Re-open the temporary file from disk.

5\\. Run all validation against the temporary file.

6\\. If validation fails:

   \\\* reject/delete the temporary file

   \\\* leave the canonical Master untouched

   \\\* report the failed checks

7\\. If validation passes:

   \\\* optionally create a backup of the current canonical Master

   \\\* atomically replace the canonical Master with the validated temporary file

8\\. Re-open the canonical Master after replacement.

9\\. Run final sanity checks against the canonical Master itself.

After every successful edit, the **\*\*\\\*\\\*same canonical filepath\\\*\\\*\*\*** must contain the newest validated state.

That same file is the input for the next request.

Do not leave the successful state only in a differently named output file.

**\*\*# 16. Session Continuity\*\***

Do not rely on conversation memory to know what edits have already been applied.

At the beginning of every requested edit:

1\\. re-read the canonical Master from disk

2\\. parse its current structure

3\\. determine the operation from its actual current state

The canonical file is the ledger of completed changes.

If my verbal instruction appears to conflict with the actual current file state, stop and show me the discrepancy before editing.

Examples:

\\\* I ask to move a control that does not exist.

\\\* I say a control is in Clothing but it is actually elsewhere.

\\\* A requested "new" control already exists.

\\\* The exact literal differs from what I typed.

Do not silently reconcile those differences.

**\*\*# 17. Git Safety and History\*\***

If the Master file is inside a Git repository, use Git as the history/recovery layer.

Do not use versioned working Master filenames as a substitute for Git history.

After a successful validated edit:

1\\. show:

\\\`\\\`\\\`bash

git diff --check

\\\`\\\`\\\`

2\\. show the relevant:

\\\`\\\`\\\`bash

git diff -- [MASTER FILE]

\\\`\\\`\\\`

3\\. summarize the exact changes

Do not commit automatically unless I explicitly ask you to commit.

If the repository has unrelated existing changes, do not modify, stage, revert, or clean them.

Git history is for recovery and inspection.

The canonical Master file remains the single active working file.

**\*\*# 18. Independent Post-Write Validation\*\***

Validation must inspect the actual file written to disk.

Do not validate only the in-memory structure that the editing code intended to write.

Re-open the candidate file independently and check it.

After promotion, re-open the canonical Master and perform final sanity validation again.

**\*\*## Structural checks\*\***

Validate:

\\\`\\\`\\\`text

[ ] Opening and closing braces are balanced

[ ] Brace stack depth is 0 at EOF

[ ] No brace underflow occurred

[ ] Target group opening brace is correct

[ ] Target group matching closing brace is correct

[ ] Target group's full parent path is correct

[ ] Every unaffected named group retains the same full parent path as before the edit

[ ] Parsed nesting remains consistent with structural indentation

[ ] Inserted controls are inside the intended group

[ ] Inserted controls are at the intended nesting depth

[ ] No control was accidentally placed outside its bracket

\\\`\\\`\\\`

**\*\*## Indentation checks\*\***

Validate:

\\\`\\\`\\\`text

[ ] Group name/opening brace/closing brace retain matching indentation

[ ] Newly inserted direct members have group indentation + exactly 1 tab

[ ] Nested child indentation was not accidentally inherited

[ ] Required separator tabs remain exactly two tabs

[ ] Explicit indentation overrides were followed exactly

[ ] Spaces were not substituted for required tabs

\\\`\\\`\\\`

**\*\*## Duplicate checks\*\***

For every touched control:

\\\`\\\`\\\`text

[ ] Exact global occurrence count = 1

\\\`\\\`\\\`

Also scan the complete file for exact duplicate control lines.

If the file already contained duplicate exact control lines before the current edit, report them.

Do not silently repair unrelated pre-existing duplicates unless I instruct you to.

Do not introduce any new duplicates.

**\*\*## Placement checks\*\***

For a new control:

\\\`\\\`\\\`text

[ ] Correct target group

[ ] Correct direct nesting depth

[ ] Correct requested position

\\\`\\\`\\\`

For a bottom insertion:

\\\`\\\`\\\`text

[ ] Control/block occurs immediately before the target group's matching closing brace

\\\`\\\`\\\`

For a move:

\\\`\\\`\\\`text

[ ] Old occurrence removed

[ ] New occurrence exists

[ ] Global count = 1

\\\`\\\`\\\`

For a named block:

\\\`\\\`\\\`text

[ ] All members are present

[ ] All members are contiguous

[ ] Internal order exactly matches request

[ ] No old member occurrence remains elsewhere

[ ] Block occupies the requested final position

\\\`\\\`\\\`

**\*\*## Group-color checks\*\***

When a group color is edited:

\\\`\\\`\\\`text

[ ] Exactly one groupColor exists in target group

[ ] RGBA value matches exactly

[ ] groupColor is first content line immediately after opening {

[ ] Leading indentation is correct

[ ] Separator consists of exactly two tabs

\\\`\\\`\\\`

**\*\*# 19. Baseline Audit at Session Initialization\*\***

Before my first edit request, perform a read-only audit of the current canonical Master.

Do not modify anything.

Report:

\\\* exact canonical filepath opened

\\\* detected encoding

\\\* detected newline style

\\\* total line count

\\\* whether brace structure balances

\\\* whether structural group parsing succeeds

\\\* whether exact duplicate \\\`"control"\\\` lines already exist

\\\* whether duplicate \\\`groupColor\\\` lines exist within any individual group

\\\* whether anything prevents safe programmatic editing

\\\* whether the file is inside a Git repository

\\\* whether that Master file currently has uncommitted Git changes

If pre-existing duplicates or structural anomalies exist, report them with enough information to locate them.

Do not automatically repair them.

This baseline gives us a known starting state so later validation can distinguish:

\\\`\\\`\\\`text

pre-existing problems

\\\`\\\`\\\`

from:

\\\`\\\`\\\`text

problems introduced by the current edit

\\\`\\\`\\\`

**\*\*# 20. Prefer Reusable Editing Functions\*\***

Build reusable deterministic helpers where practical, such as:

\\\`\\\`\\\`python

parse\\\_groups(...)

find\\\_group\\\_by\\\_path(...)

find\\\_exact\\\_control(...)

count\\\_exact\\\_control(...)

insert\\\_control(...)

move\\\_control(...)

move\\\_control\\\_block(...)

set\\\_group\\\_color(...)

validate\\\_braces(...)

validate\\\_group\\\_structure(...)

validate\\\_control\\\_uniqueness(...)

validate\\\_block\\\_position(...)

validate\\\_indentation(...)

\\\`\\\`\\\`

The purpose is to make repeated edits use the same tested machinery rather than having the LLM invent a new textual-editing strategy for every request.

Correctness is more important than minimizing script length.

**\*\*# 21. Report Concrete Validation Results\*\***

Do not finish an operation with only:

\\\`\\\`\\\`text

Done.

\\\`\\\`\\\`

or:

\\\`\\\`\\\`text

Validated successfully.

\\\`\\\`\\\`

Report machine-derived facts.

Example:

\\\`\\\`\\\`text

Canonical file: sfm\\\_defaultanimationgroups.txt

Target group: Clothing

Target group range before edit: lines 56001–77887

Operation: move block

Requested controls: 24

Resolved controls: 24

Removed old occurrences: 24

Inserted controls: 24

Contiguous block check: PASS

Requested order check: PASS

Final global occurrence count for each moved literal: 1

Block immediately before Clothing closing brace: PASS

Touched-control duplicate check: PASS

Brace balance: PASS

Indentation check: PASS

Temporary candidate validation: PASS

Canonical file replacement: PASS

Canonical file re-opened after replacement: PASS

Final canonical sanity check: PASS

git diff --check: PASS

\\\`\\\`\\\`

If anything fails, identify the specific failed check.

Do not describe the edit as complete if validation failed.

**\*\*# 22. No Unrequested Semantic Decisions\*\***

This prompt defines the **\*\*\\\*\\\*editing engine\\\*\\\*\*\***, not the classification system.

Do not decide on your own that a control belongs in Eyes, Clothing, Arms, Fingers, Carpals, Body Morphs, etc.

I will give you classification and placement instructions separately.

If my requested classification is ambiguous, ask or report the ambiguity rather than inventing a destination.

Once I give a destination, perform the requested deterministic transformation.

**\*\*# 23. Initialization Instruction\*\***

For this first message:

**\*\*\\\*\\\*DO NOT EDIT THE FILE.\\\*\\\*\*\***

Read the canonical Master and perform the baseline audit.

Then report:

1\\. Canonical file successfully opened: PASS/FAIL

2\\. Exact canonical filepath

3\\. Encoding

4\\. Newline style

5\\. Total lines

6\\. Brace balance: PASS/FAIL

7\\. Structural group parser: PASS/FAIL

8\\. Existing exact duplicate control-line count

9\\. Existing duplicate \\\`groupColor\\\` issues, if any

10\\. Any structural or formatting anomalies that could affect safe editing

11\\. Git repository detected: YES/NO

12\\. Canonical Master has uncommitted Git changes: YES/NO

13\\. Whether you are ready for the first editing request

Do not modify anything until I give the first explicit edit instruction.






**# 24. Native-Rebuild Casefold Invariant**

Before adding, moving, or importing any control literal, compute its ASCII case-insensitive native-Rebuild key by folding only A-Z to a-z.

Do not use Unicode casefolding, locale-sensitive folding, or punctuation/whitespace/underscore normalization.

Search the entire file for every existing exact spelling sharing that key, and collect every full taxonomy path among them.

All exact spellings sharing one native-Rebuild key must resolve to exactly one full taxonomy path.

Exact spellings remain preserved. Only cross-path distribution is prohibited.

For a new or relocating literal:

1\. If no casefold family exists for that key, classify normally under the existing rules.

2\. If its family already exists at exactly one canonical path, the new or moved exact spelling inherits that same path unless an explicitly approved review relocates the entire family.

3\. If its family already spans multiple paths, STOP and report the pre-existing invariant violation before adding or moving anything. Do not silently pick a path.

Do not delete any exact spelling to satisfy this rule.

Do not infer semantic destination from capitalization alone.

This rule is complementary to Section 9's exact-literal duplicate check, not a replacement for it: Section 9 guards exact-string uniqueness; this section guards cross-path distribution of case-equivalent spellings.

This is a detection rule, not a classification system. See Section 22.

**\*\*# Preflight Approval Gate\*\***

For every requested edit, separate the work into two phases:

**\*\*## Phase 1 — Inspect and Propose\*\***

Before modifying any file:

1\\. Re-read the current canonical Master from disk.

2\\. Parse its current structure.

3\\. Locate every group and exact control involved in my request.

4\\. Check global occurrence counts for every control that will be moved, added, or otherwise changed.

5\\. Determine the exact structural transformation required.

6\\. Report what you intend to do.

7\\. Show what the resulting structure is intended to look like.

8\\. State exactly which file will be modified and what the final output will be.

9\\. Then STOP and wait for my explicit approval.

**\*\*\\\*\\\*Do not write a candidate file, temporary file, or canonical-file modification during Phase 1.\\\*\\\*\*\***

Do not begin the edit merely because the request appears unambiguous.

I must explicitly approve the proposed operation before Phase 2 begins.

**\*\*## Required Preflight Report\*\***

Before every edit, report at minimum:

**\*\*### Current state\*\***

\\\* Canonical Master filepath

\\\* Target group path(s)

\\\* Whether each target group currently exists

\\\* Current location of every exact control involved

\\\* Current global occurrence count of every touched control

\\\* Any conflicts, missing literals, duplicates, or structural surprises

**\*\*### Proposed changes\*\***

State concretely:

\\\* groups to create

\\\* groups to remove, if any

\\\* controls to move

\\\* controls to add

\\\* controls to remove

\\\* colors to add/change/remove

\\\* requested order

\\\* resulting nesting

\\\* resulting indentation depth

\\\* whether any existing content remains untouched in the parent group

For moves, explicitly state:

\\\`\\\`\\\`text

These controls will be REMOVED from their current locations and INSERTED at the new location. They will not be copied.

\\\`\\\`\\\`

**\*\*### Intended resulting structure\*\***

Show a concise structural preview using the exact proposed names.

For example:

\\\`\\\`\\\`text

RigArms

└── LeftArm                         [groupColor 64 192 96 255]

    ├── 7 direct arm controls

    ├── LeftCarpals                 [no groupColor]

    │   └── 40 controls

    └── LeftFingers                 [groupColor 64 192 96 255]

        └── 6 controls

\\\`\\\`\\\`

Where useful, show the first few and last few exact control lines so I can verify that the correct blocks were identified.

**\*\*### Intended output\*\***

Explicitly state:

\\\`\\\`\\\`text

Final output: the validated result will replace the same canonical Master file:

[EXACT CANONICAL PATH]

\\\`\\\`\\\`

The final successful edit does **\*\*\\\*\\\*not\\\*\\\*\*\*** become a separately versioned working file.

The workflow after approval will be:

\\\`\\\`\\\`text

canonical Master

→ in-memory transformation

→ temporary candidate

→ validation

→ atomic replacement of canonical Master

→ re-open canonical Master

→ final validation

→ git diff

\\\`\\\`\\\`

Temporary files are validation intermediates only.

**\*\*### Planned validation\*\***

State which validations will be performed after the edit, including:

\\\* brace balance

\\\* structural group placement

\\\* exact global occurrence count = 1 for every touched control

\\\* old move locations are empty of the moved controls

\\\* requested block order

\\\* block contiguity

\\\* groupColor placement/value

\\\* indentation

\\\* exact tab syntax

\\\* \\\`git diff --check\\\`

\\\* relevant \\\`git diff\\\`

**\*\*## Approval boundary\*\***

End every Phase 1 response with:

\\\`\\\`\\\`text

No files have been modified.

Awaiting approval to execute this plan.

\\\`\\\`\\\`

Do not proceed to Phase 2 until I explicitly approve the plan with language such as:

\\\`\\\`\\\`text

Proceed.

\\\`\\\`\\\`

If I correct any part of the plan, update the preflight report and wait for approval again.

**\*\*## Phase 2 — Execute and Validate\*\***

Only after explicit approval:

1\\. Re-read the canonical Master again from disk.

2\\. Confirm the relevant state still matches the approved preflight assumptions.

3\\. If it has changed, STOP and produce a new preflight report.

4\\. If it still matches, perform the deterministic Python transformation.

5\\. Write the temporary candidate.

6\\. Validate it.

7\\. Promote it atomically to the canonical Master only if all required validation passes.

8\\. Re-open and validate the canonical Master.

9\\. Show machine-derived validation results and the relevant Git diff.

Do not substitute a new interpretation during Phase 2.

The executed transformation must match the approved Phase 1 plan.
