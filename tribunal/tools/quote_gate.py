#!/usr/bin/env python3
"""quote_gate.py — deterministic grounding of every quote. FAIL CLOSED.

An LLM verifier shares the hallucination it is checking. So the match call is made by a
script, not by a model. A near-miss is a miss: the author's text must contain the quote.
That strictness is the point -- it converts "I'm fairly sure the paper says..." into a
checkable fact.

What it deliberately does NOT do: paraphrase-match, fuzzy-match, or judge meaning. It also
does not verify that the quote sits WHERE the finding says -- that is locator_gate.py.

Usage:
    quote_gate.py check   --quote "<text>" --source <paper.txt>
    quote_gate.py batch   --findings <findings.json> --source <paper.txt>
    quote_gate.py selftest

Exit 0 = every quote matched. Exit 2 = at least one did not (EXPECTED OUTPUT, not an
error -- do not retry, relay the JSON verbatim). Exit 3 = could not run.
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import (SelfTest, dehyphenate, die, emit, load_json, normalize,  # noqa: E402
                     read_text, tool_sha)

# Classes whose evidence IS an absence: they have no quote to anchor and are routed to
# absence_gate.py instead. They are NEVER demoted for being unquotable.
ABSENCE_EXEMPT = {"absence-silence", "prior-art-omission"}


def check(quote, source, casefold=True):
    """Return (matched, how). An empty quote is NOT a match -- fail CLOSED.

    The absence exemption needs finding_class, so it is the CALLER's job (see cmd_batch).
    An empty quote on a non-absence finding must fail, never be waved through.
    """
    nq = normalize(quote, casefold)
    if nq == "":
        return False, "empty-quote"
    ns = normalize(source, casefold)
    if nq in ns:
        return True, "normalized"
    if dehyphenate(nq) in dehyphenate(ns):
        return True, "dehyphenated"
    return False, "none"


def cmd_check(args):
    src = read_text(args.source)
    matched, how = check(args.quote, src)
    emit({"tool": "quote_gate", "tool_sha": tool_sha(), "matched": matched, "how": how,
          "source": args.source}, 0 if matched else 2)


def cmd_batch(args):
    findings = load_json(args.findings)
    if isinstance(findings, dict):
        findings = findings.get("findings", [])
    src = read_text(args.source)
    rows, unmatched = [], 0
    for f in findings:
        fid = f.get("id", "?")
        cls = f.get("finding_class", "")
        quote = f.get("quote", "") or ""
        if cls in ABSENCE_EXEMPT:
            # Exempt ONLY when the quote is genuinely empty. A non-empty quote on an
            # absence finding is still gated -- no exemption abuse.
            if normalize(quote) == "":
                rows.append({"id": fid, "matched": True, "how": "exempt-absence",
                             "finding_class": cls})
                continue
        matched, how = check(quote, src)
        if not matched:
            unmatched += 1
        rows.append({"id": fid, "matched": matched, "how": how, "finding_class": cls})
    emit({"tool": "quote_gate", "tool_sha": tool_sha(), "source": args.source,
          "total": len(rows), "unmatched": unmatched, "results": rows},
         0 if unmatched == 0 else 2)


def selftest():
    t = SelfTest("quote_gate")
    src = "We observe a 15% improvement over the strong-\nest baseline in Table 4."
    t.check("exact", check("15% improvement", src)[0], True)
    t.check("smart quote folds", check("15% improvement", src.replace("15%", "15%"))[0], True)
    t.check("line-break hyphen rejoined", check("strongest baseline", src)[0], True)
    t.check("near miss is a miss", check("16% improvement", src)[0], False)
    t.check("empty fails closed", check("", src), (False, "empty-quote"))
    t.check("whitespace-insensitive", check("improvement   over", src)[0], True)
    t.check("paraphrase rejected", check("we see a fifteen percent gain", src)[0], False)
    # a numeric range must not be silently joined into a matchable token
    t.check("range not joined", check("510", "seeds 5- 10 were used")[0], False)
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check"); c.add_argument("--quote", required=True); c.add_argument("--source", required=True)
    b = sub.add_parser("batch"); b.add_argument("--findings", required=True); b.add_argument("--source", required=True)
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "check":
            cmd_check(a)
        elif a.cmd == "batch":
            cmd_batch(a)
        elif a.cmd == "selftest":
            selftest()
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:                      # never fail open
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
