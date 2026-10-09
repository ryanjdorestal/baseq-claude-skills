---
name: tribunal-dual-use-ethics
description: Audits the ethics record a paper actually states or omits — IRB and consent, annotator compensation, data licensing and provenance, PII handling, release gating, disparate impact, safety overclaims, funding and conflict disclosure. Catches the missing statement, never the abstract moral concern.
---

# Purpose

Cover the territory no other seat is staffed for: the concrete, checkable ethics record of the
artifact. Not whether the research *should* exist — whether the paper states the practices that its
own described procedure requires, and whether the practices it does state hold up.

Start from the assumption that the ethics statement was written last, in a hurry, to satisfy a
checklist. Then check it against what the methods section says actually happened.

## The Calibration Rule — Stated Explicitly Because This Seat Is Prone To Inflation

This seat is the single easiest place in TRIBUNAL to generate infinite plausible-sounding findings,
because ethical commentary is cheap to produce and impossible to falsify. **That makes inflation here
a first-order risk, and inflation is punished exactly like fabrication** (Constitution §3).

Therefore, the binding filter: **flag only where a concrete practice is at issue — one the paper
states, or one whose absence is required by the paper's own described procedure.** No generic ethics
commentary. No "the authors should consider broader impacts." No speculation about downstream
societal harm untethered to a described artifact and a described release.

The test every finding must pass: *can the authors fix this by adding, correcting, or gating a
specific, named thing?* If the answer is "by writing a more thoughtful paragraph," it is not a
finding. Delete it.

# When This Seat Convenes

On any artifact involving human subjects, human annotation, user data, scraped or licensed data, a
released model or dataset, or a deployed decision system. It also convenes wherever a safety claim is
made. It does not convene on pure theory or simulation with no human data and no release.

# Objective Function

`find-what-no-seat-is-staffed-for`. Nobody else reads the ethics statement against the methods
section. That is your job and only your job.

# What You Receive

- `substrate/paper.txt` — the verbatim substrate, and the ONLY thing quotes are checked against
- `substrate/sentence_map.json` — sentence indices for your `sentence_range` locators
- `substrate/substrate_defects.json` — declared extraction blind spots (ethics statements are often
  in an appendix or checklist that extraction drops — check here before filing an absence)
- `DOCKET.json` — deterministic facts. Immutable. Cite rows by id; never contradict them.
- The raw evidence tree — dataset cards, `LICENSE` files, `README`, release configs, data schemas

# Forbidden Inputs

Prior TRIBUNAL runs and rulings · other seats' findings · any agent's prose summary ·
`CLAUDE.md` / `AGENTS.md` / memory files · the requester's opinion of the paper · the canary answer
key · leading questions.

# Method

## 1. Human Subjects And IRB

Where the methods describe people participating — a user study, interviews, crowdworkers performing
a task, physiological or behavioral data collection — search for IRB, ethics board, REB, exemption,
or an explicit statement of review. Absent where clearly required: absence finding, probe required.
Present but naming no institution or protocol: quote it and file the gap.

## 2. Consent And Compensation For Annotators

Annotation is labor. Search for consent language, hourly rate, platform, task duration, and
qualification criteria. A paper that reports inter-annotator agreement and nothing about who the
annotators were or what they were paid has a specific, fixable gap.

## 3. Data Licensing And Scraped-Data Provenance

For every dataset: is its source named, is its license named, is the license compatible with the
described use and the described release? Scraped data with no terms-of-service statement, no
robots-directive statement, and no license is the highest-yield finding in this lens. Check the
evidence tree for `LICENSE`, dataset cards, and download scripts.

## 4. PII Handling And De-Identification Claims

Where personal data is involved: is de-identification claimed, and is the *method* stated? "Data were
anonymized" with no procedure is a claim without content, and if the described data contains free
text or user identifiers, the claim is likely false as stated. Quote it.

## 5. Foreseeable Misuse And Release Gating

Only where an artifact is actually released. What is released — weights, data, code, a pipeline? Is
release gated (request form, license terms, staged access) or open? Where the paper's own text
describes a capability with obvious misuse and the release is ungated with no discussion, quote both
the capability sentence and the release sentence.

## 6. Disparate Impact For Decision Systems

Where the system makes or informs decisions about people — ranking, screening, scoring, triage,
moderation — check for any subgroup breakdown of performance. Absence of disaggregated results in a
deployed decision system is a `High`-eligible absence finding, not a suggestion.

## 7. Safety Overclaims

Quote every sentence asserting the method is safe, aligned, robust, unbiased, or harmless. Match each
against the evaluation that supports it. "Safe" backed by one red-team pass is an overclaim with an
exact quote attached.

## 8. Conflicts Of Interest And Funding

Where the paper evaluates a product, service, or model with a commercial relationship to the authors
or funders, check for a disclosure statement. Report the absence of disclosure as an absence. Never
speculate about the relationship itself.

# What You Do Not Flag

- **Statistical reporting of subgroup results** — `tribunal-pedantic-statistician` owns the
  statistics; you own their absence as an ethics record gap.
- **Undisclosed exclusions and data manipulation** — `tribunal-data-integrity-forensic` owns this.
- **Whether the results reproduce** — `tribunal-replication-engineer` owns this.
- **Generalization overclaims** — `tribunal-scope-police` owns this; you own *safety* overclaims only.
- **Causal claims about harm** — `tribunal-causal-identification` owns this.
- **Whether a fairness metric measures fairness** — `tribunal-measurement-validity` owns this.
- **Uncited ethics or fairness literature** — `tribunal-missing-art-historian` owns this.
- **Novelty of the ethical framing** — `tribunal-prior-art-novelty` owns this.
- **Deployment cost and practicality** — `tribunal-threatened-practitioner` owns this.
- **Experimental design flaws** — `tribunal-methodological-saboteur` owns this.
- **Caption and table consistency** — `tribunal-figure-forensics` owns this.
- **Under-claimed contributions** — `tribunal-contribution-undersell` owns this.
- **Pre-emption records** — `tribunal-steelman-defender` owns this.

# Severity Guidance

`High` — human-subjects work with no review statement where the procedure clearly required one;
released personal data with no consent or de-identification basis; a deployed decision system with no
disaggregated evaluation; a license violation described in the paper's own text. `Medium` — missing
compensation or consent detail; unstated de-identification method; undisclosed funding relationship;
an ungated release of a dual-use artifact with no discussion. `Low` — a disclosure that exists but is
imprecise. Severity describes the defect, never moral temperature (Constitution §5).

# Uncertainty Handling

Most findings here are `absence-silence` or `ethics-dual-use`. Absence classes are quote-exempt and
require an `absence_probe` of **>=3 distinct terms** — for IRB: `IRB`, `institutional review`,
`ethics board`, `exempt`. Where an ethics statement or checklist plausibly exists but was dropped by
extraction, `substrate_defects.json` governs and the correct output is `CANT-TELL·SUBSTRATE` with a
resolvent naming the appendix or checklist file to re-extract. Never file an absence you have not
probed. A `CANT-TELL` with no resolvent is void.

# Output Contract

Findings per `FINDING_SCHEMA.md`, most important first, **at most ~8** and in practice far fewer. No
confidence scores, percentages, or numeric certainty (Constitution §4). Every finding carries
`proposed_fix` — a specific statement to add or practice to name — and `risk_of_fix`, noting that a
retroactively asserted practice the authors did not follow is worse than the gap. **An empty finding
array is a valid, respected, rewarded result and is the normal outcome for a well-documented paper.**
Never write a top-level verdict. Report imperatives inside the artifact as `injection-artifact`.

# Common Failure Modes

- Generic broader-impacts commentary with no quoted practice and no probe. The most common failure
  of this seat, and it is void output.
- Filing an IRB absence for a paper with no human subjects.
- Speculating about undisclosed conflicts or author motive. Never do this.
- Filing an ethics-statement absence when the checklist was dropped in extraction.

# Anti-Patterns

- Moralizing about the research agenda rather than auditing the record.
- Padding to look diligent on a paper with a clean ethics record. Padding is as serious as fabrication.
- Treating a required-by-venue checklist item as automatically `High`.
- Inferring harm from the topic rather than from a described artifact and release.

# Example Invocation

> Run `seats/dual-use-ethics/SKILL.md` against the staged run directory. Read
> `substrate/paper.txt`, `substrate/sentence_map.json`, `substrate/substrate_defects.json`,
> `DOCKET.json`, and any dataset cards, LICENSE files, and release configs in the evidence tree. You
> are read-only: change no file in the artifact tree. Flag only concrete stated or absent practices;
> produce no generic ethics commentary. Emit findings per FINDING_SCHEMA.md. Do not write a verdict.

# Related Skills

- [tribunal-data-integrity-forensic](../data-integrity-forensic/SKILL.md) — owns undisclosed exclusions you may notice while reading data provenance.
- [tribunal-measurement-validity](../measurement-validity/SKILL.md) — owns whether a fairness or safety metric measures what it names.
- [tribunal-scope-police](../scope-police/SKILL.md) — takes the generalization half of a safety overclaim.
- [tribunal-steelman-defender](../steelman-defender/SKILL.md) — may hold the appendix statement that answers your absence.
