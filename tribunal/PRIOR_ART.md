# Prior art — what was taken, what was rejected, and why

TRIBUNAL is a synthesis of four open-source adversarial review systems, read in full before
a line of this system was written. Attribution matters here for the same reason it matters
in a paper: an uncredited idea is a stolen one, and a system that lectures authors about
citation discipline had better keep its own.

Nothing in this repository is copied source. The designs below were studied and
reimplemented; every script here is original and stdlib-only.

---

## `tjhavranek/paper-workshop` (CRUCIBLE) — the spine

The strongest prior art by a wide margin, and the structural ancestor of Acts II–IV.

**Taken:**
- Two deterministic gates with **opposite failure polarities** — a quote gate that fails
  closed on a missed match, an absence gate whose looser ladder can only push a finding
  toward *present*. This is the single best idea in the lineage and it is reproduced here
  in `quote_gate.py` / `absence_gate.py`, sharing one normalization module so they cannot
  drift apart.
- **Verdict aggregation in code, not by an LLM** (`verdict.py majority`), with conservative
  downward severity revision.
- **Fail-closed on dropped verifier rows** — a finding no gate result covers is unverified.
- **`cant-tell` as a rewarded, first-class verdict**, and the ban on confidence scores.
- **Commit-and-reveal blindness** and decorrelation by rival objective function rather than
  job title.
- **A correction-propagation guard**: a chair echoing the id of a rejected finding cannot
  resurrect it, enforced by a code filter rather than a prompt.
- **A steelman angle as a kill switch**, with killed findings preserved and reasoned.
- **`LIMITATIONS.md` as a shipped design asset.** This file exists because that one did.
- The rule that a **text substrate has no pixels**, so "the figure does not render" is an
  extraction artifact and never a finding.

**Rejected / changed:** the surface area (5 modes × 2 registers × economy × span-diet × an
improvement mode) is more configuration than a review system can keep coherent; TRIBUNAL has
five modes and no registers, and mode never changes the rules. Its locator gap is closed here
(see below).

## `wanshuiyin/auto-claude-code-research-in-sleep` (ARIS) — the epistemics

**Taken:**
- **"A loop may DRIVE; it may never ACQUIT."** The Type-A/Type-B split — could a dumb script
  with no taste answer this gate? — is the cleanest formulation of when an agent may judge
  itself, and Constitution §7 is its descendant.
- **The explicit refutation of same-family juries**: "five draws from one distribution is one
  opinion with error bars, not five opinions." This is why TRIBUNAL's best verdict is
  `CLEAN_GIVEN_EVIDENCE` and why `acceptance_status` is permanently `provisional`.
- **Zero-context audit** as a tier stricter than reviewer independence, with a forbidden-input
  list that includes *prior audits*. The adjudicator lane is built on this.
- **`audited_input_hashes` + external rehash → `STALE`** (`doctor.py freshness`).
- **The append-only obligations ledger**, `UNRESOLVED_DISAPPEARANCE`, receipts re-verified
  rather than remembered, and "a waiver is not a resolution" (`ledger.py`).
- **The One Forbidden Loop** — never "edit → re-scan → repeat until clean," because that
  objective function teaches the editor to defeat the detector.
- **Verdict computed by code from model-emitted per-item classifications**, never self-graded.
- **A two-stage evidence gate** with an asymmetric error policy: *a false `verified` is the
  bug this gate must never have* (`evidence_check.py`).
- **Retention over silent removal** for unverifiable citations, and the high-unverified-rate
  alarm as a signal about the corpus rather than the author.
- **Injection pattern discipline**: anchor on attack-specific vocabulary, not bossy English,
  with filler-gap tolerance to defeat evasion (`injection_scan.py`).
- **The seven named numeric failure modes** — inflation, best-seed cherry-pick, config
  mismatch, aggregation mismatch, delta error, caption-table mismatch, scope overclaim — which
  shape the statistician and integrity seats.
- **Six-state verdict semantics** where `NOT_APPLICABLE ≠ SKIP` and `BLOCKED ≠ nothing to
  audit`. TRIBUNAL's `BLOCKED` is that idea: a numeric claim with no raw evidence is not
  "nothing to check," it is "we cannot verify a claim the paper rests on."

**Rejected / changed:** ARIS's power comes from genuine cross-model review, which is
unavailable in a Claude-only installation. TRIBUNAL therefore treats every semantic verdict
as provisional rather than pretending a same-family panel is a jury. Its cross-family socket
is designed in: adding a second-family CLI upgrades verdicts without a rewrite.

## `ecfm/adversarial-review` — the cautionary spine

**Taken:** the red-team / blue-team / adjudicate shape, the anti-over-concession instruction
for the defender ("if an attack claims the scope is too narrow but the paper already states
its scope, the defense is *the paper already addresses this*"), resumable phase orchestration,
and the practice of keeping every stage's prompt as an auditable file.

**Rejected — deliberately and completely:** its central architectural choice. Every agent
after Phase 1 runs with tools stripped, reasoning over a ~150-line lossy summary of the
manuscript. Nothing downstream can return to the source; whatever the inventory agent garbled
becomes ground truth for six rounds of debate, a judge, and the final report. There is no
quote gate, no schema, no uncertainty channel, and no injection defense, so an invented flaw
the blue team cannot rebut — because the blue team also has no tools — ships as a "genuine
gap."

**This is the failure mode TRIBUNAL is built against.** Constitution §9 and
`POISONING_DEFENSE.md` layer 3 exist because of it: *an agent's prose is never another
agent's evidence.* Every seat reads the primary substrate. Nobody reviews a summary.

## `udecode/plate` — mostly what not to do

**Taken:** jurisdictional dedup — every persona ends with a "what you don't flag" list naming
the owning persona, which is cheap and effective and is reproduced in every seat file here.
Also its `autoreview` script's **deterministic scope anchor**: a finding whose file path is
not in the reviewed diff is dropped and the verdict auto-downgraded, which is the same
instinct as `substrate-artifact` rejection.

**Rejected:**
- **Self-reported numeric confidence** (`HIGH (0.80+)`, `MODERATE (0.60–0.79)`). 0.80 versus
  0.79 is a fiction, uncalibrated and unfalsifiable. Banned by Constitution §4.
- **Quoting as a confidence *criterion* rather than a required *artifact*.** A "HIGH
  confidence" finding there can assert "the document says X" without X existing.
- **`Below 0.50: Suppress`.** An uncertain, unconfirmable, potentially critical risk
  *vanishes*. `EPISTEMIC_LADDER.md` inverts this exactly: nothing is suppressed for being
  uncertain; it changes lane, and every `CANT-TELL` must name its resolvent.

---

# What is new here

Three gaps none of the four close:

1. **Locator verification** (`locator_gate.py`). All four verify at most that a quote
   *exists*; none verifies it exists *where the finding says*. paper-workshop names this in
   its own limitations file. A real quote pinned to the wrong span is the signature of an
   agent that recalled a sentence and then guessed where it lived — the first step of a
   hallucination, and it sends the author to the wrong page. TRIBUNAL reports the true span.
2. **Deterministic dedup and corroboration counting** (`verdict.py dedup`). The others dedup
   by LLM instruction or by a free-text bucket key that splits when two seats spell a section
   name differently.
3. **Run-local measured sensitivity** (`canary.py`). Every one of the four ships with zero
   measured effectiveness. TRIBUNAL plants known defects in a shadow copy, scores the fleet
   blind, prints the recall in the deliverable, and **downgrades its own verdict** when the
   fleet cannot find defects someone deliberately planted.

Plus the two features this system was commissioned for: a **graded epistemic ladder** with
routed uncertainty and mandatory resolvents, and a **seven-layer poisoning defense** whose
load-bearing rule is that no agent's prose is ever another agent's evidence.
