#!/usr/bin/env python3
"""absence_gate.py — deterministic rail for "the paper never says X". FAIL CLOSED.

The highest-severity problems in a paper are usually things it never says: the missing
baseline, the unreported ablation, the absent limitation. Those findings have no quote to
anchor, so they are exempt from the quote gate -- and would otherwise be completely
ungrounded. This gate is their rail.

POLARITY IS INVERTED RELATIVE TO THE QUOTE GATE, on purpose. The match ladder here is
deliberately LOOSER. For the quote gate, a missed match fails CLOSED (quote unverified).
For an absence gate, a missed match would fail OPEN -- a false "absent" certificate, i.e.
a fabricated silence. So every extra match rung here only ever pushes a finding toward
'present', which DEGRADES it. That is the conservative direction.

What it certifies, honestly: "absent" means none of the probe terms occurs in the source.
It certifies the SEARCH, not the semantics -- a paraphrase outside the probe can still
exist. The steelman panel angle adjudicates the semantic half, using the hit snippets
this script logs as its evidence.

Usage:
    absence_gate.py check --probe "term one" --probe "term two" --probe "t3" --source <paper.txt>
    absence_gate.py batch --findings <findings.json> --source <paper.txt>
    absence_gate.py selftest

Exit 0 = every absence claim certified absent. Exit 2 = at least one degraded. Exit 3 = could not run.
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import (SelfTest, dehyphenate, die, emit, hyphenless, load_json,  # noqa: E402
                     normalize, read_text, tool_sha)

ABSENCE_CLASSES = ("absence-silence", "prior-art-omission", "contribution-undersell")
MIN_TERMS = 3          # a probe this thin invites a narrow search; fail closed below it
SNIPPET_RADIUS = 60
MAX_SNIPPETS = 3


def search_term(term, s_norm, s_dehyph, s_hyphenless):
    """Looser ladder than the quote gate, by design. Every rung can only find MORE."""
    t = normalize(term)
    if not t:
        return None
    for hay in (s_norm, s_dehyph, s_hyphenless):
        probe = t if hay is not s_hyphenless else hyphenless(t)
        i = hay.find(probe)
        if i >= 0:
            lo, hi = max(0, i - SNIPPET_RADIUS), min(len(hay), i + len(probe) + SNIPPET_RADIUS)
            return {"term": term, "snippet": hay[lo:hi]}
    return None


def certify(probe_terms, source):
    """Return (certified, hits). certified in absent|present|thin-probe|no-probe."""
    terms = [x for x in (probe_terms or []) if normalize(x)]
    if not terms:
        return "no-probe", []
    # Dedup on the NORMALIZED form so near-duplicate LLM list items cannot pass the floor.
    seen, uniq = set(), []
    for x in terms:
        k = normalize(x)
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    if len(uniq) < MIN_TERMS:
        return "thin-probe", []
    s_norm = normalize(source)
    s_dehyph = dehyphenate(s_norm)
    s_hyphenless = hyphenless(s_norm)
    hits = []
    for term in uniq:
        h = search_term(term, s_norm, s_dehyph, s_hyphenless)
        if h:
            hits.append(h)
        if len(hits) >= MAX_SNIPPETS:
            break
    return ("present" if hits else "absent"), hits


def cmd_check(args):
    src = read_text(args.source)
    cert, hits = certify(args.probe, src)
    emit({"tool": "absence_gate", "tool_sha": tool_sha(), "certified": cert,
          "terms_searched": len(set(normalize(x) for x in (args.probe or []))),
          "hits": hits}, 0 if cert == "absent" else 2)


def cmd_batch(args):
    findings = load_json(args.findings)
    if isinstance(findings, dict):
        findings = findings.get("findings", [])
    src = read_text(args.source)
    rows, degraded = [], 0
    for f in findings:
        cls = f.get("finding_class", "")
        if cls not in ABSENCE_CLASSES:
            rows.append({"id": f.get("id", "?"), "certified": "not-absence-class",
                         "terms_searched": 0, "hits": []})
            continue
        cert, hits = certify(f.get("absence_probe"), src)
        if cert != "absent":
            degraded += 1
        rows.append({"id": f.get("id", "?"), "certified": cert,
                     "terms_searched": len(set(normalize(x) for x in (f.get("absence_probe") or []))),
                     "hits": hits})
    emit({"tool": "absence_gate", "tool_sha": tool_sha(), "source": args.source,
          "total": len(rows), "degraded": degraded, "results": rows},
         0 if degraded == 0 else 2)


def selftest():
    t = SelfTest("absence_gate")
    src = "We evaluate on CIFAR-10 and report accuracy. No ablation of the loss term is given."
    t.check("truly absent", certify(["human evaluation", "user study", "annotator agreement"], src)[0], "absent")
    t.check("present degrades", certify(["ablation", "user study", "annotator"], src)[0], "present")
    t.check("thin probe fails closed", certify(["ablation", "user study"], src)[0], "thin-probe")
    t.check("no probe fails closed", certify([], src)[0], "no-probe")
    t.check("duplicate terms do not pass the floor",
            certify(["ablation", "Ablation", "ABLATION "], src)[0], "thin-probe")
    # hyphen-insensitivity must only ever push toward 'present'
    t.check("hyphenless rung finds it", certify(["cifar10", "zzz-nope", "qqq-nope"], src)[0], "present")
    t.check("hit snippet returned", bool(certify(["ablation", "aaa", "bbb"], src)[1]), True)
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check"); c.add_argument("--probe", action="append"); c.add_argument("--source", required=True)
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
    except Exception as e:
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
