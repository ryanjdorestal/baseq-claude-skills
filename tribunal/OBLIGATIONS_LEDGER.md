# The Obligations Ledger

`OBLIGATIONS.jsonl` is the only thing in TRIBUNAL that survives between runs. Everything else
is stateless by design — there is no memory file, no cached summary, no learned prior, and
therefore nowhere for a poisoned assertion to live.

The ledger exists because of one failure mode: **an author edits the paper until the audit
goes quiet, and the quiet is mistaken for a fix.** Deleting an anchored span kills a flag
faster than correcting the number.

So: **the ledger, not the verdict, decides whether the gate opens.**

---

# Shape

One JSON object per line. Append-only. Nothing is ever rewritten or removed.

```json
{"event":"open","finding":"F-007","title":"Reconcile the abstract's 15% with Table 4",
 "severity":"High","run":"2026-08-05-standard","at":"2026-08-05T14:32:07Z"}
{"event":"close","finding":"F-007","fix_type":"number-corrected",
 "evidence":"results/rerun_2026_08_09.json","evidence_sha":"sha256:c9e4…","by":"ryan",
 "at":"2026-08-09T10:02:11Z"}
{"event":"reopen","finding":"F-007","flags":["RECEIPT_INVALID"],
 "note":"evidence_changed_after_closure","at":"2026-08-14T09:15:00Z"}
```

Folded state per finding: `OPEN` · `CLOSED` · `WAIVED`, plus accumulated `flags`.

# Rules, enforced in `tools/ledger.py`

## Append-only

Every event is a new line. `ledger.py` has no code path that edits or deletes one. The full
history of an obligation — including every failed closure — is permanently readable.

## A re-run can open obligations. It can never close them.

`ledger.py sweep` compares a new run's findings against the ledger. New findings open new
obligations. Previously-open obligations still present stay open. And:

## A finding that disappears stays open

If an obligation was `OPEN` and the finding is absent from a later run, the sweep appends a
`reopen` event with the flag **`UNRESOLVED_DISAPPEARANCE`**.

**Rewording the span is not a fix. Deleting the sentence that carried the number is not a
fix.** Both make a finding vanish; neither corrects anything. The only way a finding leaves
the ledger honestly is through a recorded closure with a receipt.

## Every closure needs a receipt

`fix_type` must be one of:

| `fix_type` | What the receipt must be |
|---|---|
| `number-corrected` | The raw file the corrected number came from |
| `analysis-rerun` | The rerun output file |
| `claim-narrowed` | The diff showing the narrowed claim |
| `claim-withdrawn` | The deletion diff — **this is an honest fix**; removing an unsupported claim is a legitimate resolution |
| `evidence-supplied` | The file that was missing when the finding was raised |
| `text-clarified` | The diff, and only for `presentation-defect` findings |

A closure without an existing receipt file is refused outright. `ledger.py close` exits 3.

## `fix_type` is a receipt, not a verdict

The author's label records what the author says they did. It does not adjudicate whether the
fix works — that is the next run's job. **A false label is a permanent false record**, and it
sits in the history forever next to the evidence that contradicts it.

## Receipts are re-verified, not remembered

`ledger.py verify` rehashes every closure receipt. If the evidence file is gone, or its hash
no longer matches what was recorded at closure, the obligation **re-opens** with the flag
`RECEIPT_INVALID`. Editing the evidence after closing an obligation re-opens it. There is no
prompt that makes a hash match.

## A waiver is not a resolution

`ledger.py waive` records a human-attributed, permanent decision to accept a finding as-is.
The original finding snapshot stays immutable beside it. A waived finding is not fixed, is
not gone, and appears in every subsequent ruling under its own heading.

## Escalation on recurrence

An obligation that has been open across three consecutive runs without a recorded fix is
either critical or not real. The ruling says so and demands one of: a closure with a receipt,
an attributed waiver, or a downgrade with a stated reason. **Zombie findings are not
permitted to accumulate quietly.**

---

# Commands

```bash
# open one by hand (usually the sweep does this)
python3 tools/ledger.py open   --ledger OBLIGATIONS.jsonl --finding F-007 \
        --title "…" --severity High --run 2026-08-05-standard

# close with a receipt
python3 tools/ledger.py close  --ledger OBLIGATIONS.jsonl --finding F-007 \
        --fix-type number-corrected --evidence results/rerun.json --by ryan

# accept as-is, permanently and attributably
python3 tools/ledger.py waive  --ledger OBLIGATIONS.jsonl --finding F-007 \
        --by ryan --reason "reviewers accepted the original framing"

# fold a new run in; flags anything that vanished without a fix
python3 tools/ledger.py sweep  --ledger OBLIGATIONS.jsonl \
        --findings .tribunal/<run>/findings_ledger.json --run <run-id>

# rehash every receipt; re-opens anything whose evidence changed
python3 tools/ledger.py verify --ledger OBLIGATIONS.jsonl

# what is still open
python3 tools/ledger.py status --ledger OBLIGATIONS.jsonl
```

Exit `2` from `sweep`, `verify`, or `status` means **there are open obligations or something
re-opened**. That is expected output, not an error.

---

# The rule this file exists to state

> A verdict describes one run. The ledger describes the work. A paper with a quiet ruling and
> six open obligations has not been fixed — it has been reviewed twice.
