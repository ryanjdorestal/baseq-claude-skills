# Limitations — what a TRIBUNAL ruling does not establish

This file is a design asset, not a disclaimer. A review system that cannot state what it has
failed to prove is asking to be trusted on vibes. Read this before you act on a ruling, and
quote from it in §16 of every ruling.

---

## 1. This fleet cannot acquit. Nothing here is an acceptance.

TRIBUNAL runs on a single model family. N agreeing Claudes are **correlated same-family
blindness wearing a jury costume** — their agreement is evidence of shared training priors,
not of correctness. Five draws from one distribution is one opinion with error bars.

`CLEAN_GIVEN_EVIDENCE` means *no flag was found in the evidence at hand*. It does not mean
the paper is correct, novel, well-designed, or publishable. Installing a second model family
would upgrade the epistemics; until then, every semantic verdict is `provisional`.

## 2. No measured recall against real-world defects

The canary lane measures recall against **defects this system planted**, on **this paper**,
in **this run**. That is a live sensitivity check, and it is strictly better than nothing —
but planted defects are not the defects a real referee finds, and a fleet can be excellent at
catching a drifted number while blind to a broken identification strategy.

There is no published evaluation of TRIBUNAL against third-party papers with known flaws,
and therefore **no false-positive rate at all**. Treat a ruling as one very thorough hostile
opinion, not as validated ground truth.

## 3. Coverage means examined, not correct

A jurisdiction reported as reviewed was *attended to*. It was not *proven sound*. A flaw can
sit inside a covered span, read by a seat that did not recognize it. Coverage is a claim
about attention, and attention is not competence.

## 4. The gates certify search, not semantics

- The **quote gate** proves a string is in the substrate. It does not prove the finding built
  on that string is right, or that the quote means in context what the finding says it means.
- The **absence gate** proves *the probe terms* do not occur. A paraphrase outside the probe
  can still exist. That is why a steelman angle sits on top of it.
- The **locator gate** proves the quote sits in the claimed span. It does not prove the
  section label is right, or that the span is the relevant one.
- **`evidence_check`** proves a number exists in a file. It says nothing about whether that
  number supports the claim attached to it — that is the "wrong-but-real" class, and only a
  reviewer lane touches it.
- **`stat_consistency`** proves reported statistics can or cannot coexist. GRIMMER here is
  the first-order sum-of-squares reachability test, not the full variance-granularity proof:
  it catches gross impossibility, not every violation.
- **`citation_gate`** cannot check the axis that matters most — whether a cited work actually
  supports the claim it is cited for. With no corpus supplied it cannot check existence
  either, and every entry is honestly `unverified`, which says nothing about the author.

## 5. The gates run behind an agent relay

A script produces JSON; an agent relays it. Fail-closed handling of dropped rows means a bad
relay can only **degrade** findings, never manufacture a pass. But the audit record still
depends on the relay being honest about what the script printed, and nothing in this system
can prove an agent actually ran the command it reports running.

## 6. "The seat read the substrate" is instruction-graded, not enforced

Nothing here can prove a seat read the paper rather than confabulating from a filename. The
gates make confabulation **detectable** — an ungrounded quote fails — but not impossible. A
seat that only ever emits `SUSPECTED` findings could in principle never open the file.

## 7. The injection scanner is a blacklist, not a sandbox

A clean scan means "no known-bad strings," never "safe." Novel phrasing gets through. The
layer that catches what the regex misses is the constitutional rule that imperatives inside
evidence are never obeyed — and **that rule is instruction-graded**. `POISONING_DEFENSE.md`
states this in full.

## 8. Same-family decorrelation is a design bet

Rival objective functions, blind commit-and-reveal, distinct evidence diets, and a steelman
seat that is paid to disagree all reduce correlation between seats. None of it eliminates a
shared blind spot, and none of it has been measured.

## 9. Severity calibration can only move downward

The panel may lower a severity; it may not raise one. A systematically deflating fleet has no
automatic upward correction — an angle arguing for higher severity leaves a note for the
chair and nothing more. This is deliberate (inflation is the more common failure) and it is
still a gap.

## 10. The text substrate has no pixels

Figures are read as captions and surrounding prose. Image content, plot geometry, axis
rendering, image manipulation, and duplicated panels are **entirely outside scope**. Every
extraction blind spot is declared in `substrate_defects.json`, and a finding that contradicts
that file is void — which protects against false positives and guarantees false negatives in
exactly that region.

## 11. No network, unless you supply the corpus

Citation existence is checked against what you stage. Nothing is fetched. A hallucinated
citation in a paper whose corpus you did not supply will be reported as `unverified`, which
is an honest non-answer, not a detection.

## 12. Act V audits a rebuttal; it cannot verify the science of one

The rebuttal lane checks that referee points are answered, that fix claims carry receipts,
and that a response does not overclaim what a diff did. Whether the new analysis is *correct*
is a fresh review, not a rebuttal audit.

---

# The honest one-liner

> TRIBUNAL makes it hard to deliver an ungrounded criticism, easy to see what was not
> checked, and impossible to call the result an acceptance. It does not make the review
> correct.
