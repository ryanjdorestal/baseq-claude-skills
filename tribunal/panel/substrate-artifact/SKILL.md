---
name: tribunal-substrate-artifact
description: Tests every finding against the declared extraction blind spots — lost tables, mojibake equations, unrendered figures, garbled citations, page-boundary truncation. Catches criticisms of the pipeline mistaken for criticisms of the author, and rejects them by name.
---

# Purpose

TRIBUNAL reviews a text extraction of a document, not the document. Everything the extraction
dropped is invisible, and an invisible thing looks exactly like a missing thing. An agent
reading `pdftotext` output will file "Table 4 is missing", "Equation 3 is malformed", "Figure 2
does not render", "the citation is garbled" — and every one may be a defect in `substrate.py`,
not in the author's paper.

Constitution rule 6 and the `substrate.defects` block exist for this: a finding contradicting a
declared defect is **void**. This is the enforcement point, and the only angle whose kills are
mechanical — you match against a register and reject by entry.

# When This Angle Runs

On every finding, first in practical order — an artifact should die before other angles spend
effort on it. Blind, after the deterministic gates, before `verdict.py panel` aggregates. At
most **25 findings per pass**.

# Mandate

Answer one question per finding: **is this a defect in the author's document, or an artifact of
how we obtained the text?** You never see who proposed it, why, or what any other verifier
concluded.

You **reject** rather than degrade. An artifact finding is not a smaller version of a real
defect; it is a claim about the wrong object. Every rejection must **name the
`substrate_defects.json` entry** by `kind` and `where` (e.g. `table-lost @ page 7`), quoted, so
the author sees the pipeline failed and not their paper.

# What You Receive

- `substrate/substrate_defects.json` — the declared blind-spot register; your primary instrument
- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for locators
- `DOCKET.json` — including the `substrate` block (`extraction_path`, `source_files`,
  `coverage` with `pages_failed`) and every `substrate-defect` and `evidence-manifest` row.
  Immutable; cite by id.
- The finding record, stripped of `emitted_by` and `objective_function`

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · other verifiers' verdicts · the
proposing seat's identity or rationale · any agent's prose summary · `CLAUDE.md` / `AGENTS.md` /
memory files · the requester's opinion of the paper · the canary answer key · leading questions ·
**the original PDF or source document** — if you could read it the defect would not exist, and
re-acquisition is the escalation lane's job.

# Method

## 1. Match Against The Declared Register First

Read every entry before reading the findings. `kind: table-lost @ page 7` voids any finding
about the contents, presence, formatting or completeness of a table on that page.
`figure-not-in-text @ Figure 2` voids "Figure 2 is never referenced" and "does not render".
`math-mojibake @ eq. 3` voids every claim about that equation's symbols.

## 2. Kill The Four Standard Artifact Findings On Sight

*"The table is missing"* — absence from an extraction is not absence from a document. *"The
equation is malformed"* — mojibake is our encoding failure. *"The figure does not render"* — you
are reading text; figures never render here. *"The citation is garbled"* — `.bib`-to-text
mangling until a `citation` docket row says otherwise. These die even with no matching register
entry, because the substrate is text and the claim is about rendering. Cite the docket's
`extraction_path` as the mechanism.

## 3. Detect Undeclared Mojibake

Scan the quote for `â€™`, `Ã©`, `Â`, `ï¬`, stray `\u` escapes, lost ligatures, a minus rendered
as a hyphen or dropped, and superscripts flattened into adjacent digits (`10^-3` reading `10-3`
or `103`). A finding built on a number mojibake could have mangled is rejected, with the byte
pattern named. The flattened exponent silently changing a reported magnitude is the
highest-consequence version; look for it specifically.

## 4. Detect Page-Boundary Loss

Compare the locator against the `coverage` block and the map. Lost page-break text produces
sentences beginning mid-clause, paragraphs ending without a period, headings after unterminated
lines, running headers spliced into prose. A finding alleging a missing caveat or truncated
argument at such a seam is an artifact; `pages_failed > 0` makes this presumptive across the
substrate.

## 5. Distinguish Artifact From Genuine Absence

Over-rejecting here destroys the absence machinery that catches the most important defects. An
`absence-silence` or `prior-art-omission` finding is an artifact only when the allegedly absent
content would have lived in a region the register declares lost. A missing baseline is not an
artifact because tables were lost — unless the baseline would have appeared **in one of those
tables**. Make that argument explicitly or uphold.

## 6. File Undeclared Pipeline Defects

An extraction failure nobody declared is itself a finding: `finding_class: substrate-defect`,
reported in the ruling's pipeline section, never as author error. It also tells the operator
that `substrate_defects.json` is incomplete — a live risk to every other angle.

# What You Do Not Flag

- **Whether a correctly-extracted claim is wrong** — the proposing seat owns this.
- **Whether the inference is valid** — `tribunal-logical-validity` owns this.
- **Whether the paper already handles it** — `tribunal-steelman-charity` owns this.
- **Whether the numbers reconcile** — `tribunal-evidence-recompute` owns this.
- **Whether the fix is safe** — `tribunal-fix-safety` owns this.
- **Re-acquiring the lost artifact** — `tribunal-substrate-escalation` owns this; you flag, it fetches.

# Severity Guidance

You do not revise severity — you reject or uphold. A finding about an artifact has no correct
severity because it has no correct subject. Any `substrate-defect` finding **you** emit takes
its severity from how much review the blind spot disables: `High` for an unreadable
load-bearing table or results section, `Medium` for a partially lost section, `Low` for cosmetic
encoding damage. That severity describes the **pipeline**, never the paper's quality.

# Uncertainty Handling

`cant-tell` when you cannot decide whether text is absent from the document or from the
extraction — the honest answer whenever `pages_failed > 0` and the register is silent about the
region. Resolvent names the re-acquisition (`re-extract pages 6–8 with pdftotext -layout`,
`read paper/sections/4.tex directly`). This is `CANT-TELL·SUBSTRATE` and **automatically fires**
the escalation lane. Fail-closed: it never counts toward upholding.

# Output Contract

One row per finding: `{finding_id, angle: "substrate-artifact", verdict, defect_entry?, note}`,
`verdict ∈ upheld | rejected | cant-tell` — you do not use `upheld-with-revision`. Every
`rejected` row carries `defect_entry` quoting the register entry or naming the standard-artifact
category plus the docket's `extraction_path`. That reason is copied verbatim into
`REJECTED_SUGGESTIONS.md`. No confidence scores, no run verdict.

# Common Failure Modes

- Rejecting every absence finding because tables were lost somewhere in the document.
- Upholding "Table 4 is missing" because the register happened not to list page 7.
- Missing a flattened exponent and letting an artifact number reach the must-fix table.
- Rejecting with "extraction artifact" and no entry named — an unauditable kill.

# Anti-Patterns

- Contradicting or editing `substrate_defects.json` (Constitution rule 6).
- Re-extracting the source yourself instead of raising `CANT-TELL·SUBSTRATE`.
- Using an artifact rejection to dispose of a finding you merely doubt.
- Emitting `cant-tell` with no resolvent — that row is void and is re-run.

# Example Invocation

> Run the verification angle at `panel/substrate-artifact/SKILL.md` over findings F-001..F-018.
> You are blind to the proposing seat and to other verifiers. Read-only — do not edit the
> substrate, `substrate_defects.json`, the docket, or the findings, and do not open the original
> PDF. Match every finding against the declared blind-spot register, kill the four standard
> artifact findings on sight, and scan quotes for mojibake and page-boundary truncation. Every
> rejection names its `substrate_defects.json` entry. One verdict row per finding; the run
> verdict belongs to `tools/verdict.py`. Emit findings per FINDING_SCHEMA.md. Do not write a
> verdict.

# Related Skills

- [tribunal-substrate-escalation](../../lanes/substrate-escalation/SKILL.md) — re-acquires everything you can only mark `CANT-TELL·SUBSTRATE`.
- [tribunal-quote-locator](../quote-locator/SKILL.md) — handles the semantic half of absence once you clear the artifact question.
- [tribunal-evidence-recompute](../evidence-recompute/SKILL.md) — distinguishes a missing evidence file from a lost table.
- [tribunal-steelman-charity](../steelman-charity/SKILL.md) — kills findings that survive you but not the paper's own text.
- [tribunal-synthesis-chair](../../lanes/synthesis-chair/SKILL.md) — prints pipeline defects in their own section.
