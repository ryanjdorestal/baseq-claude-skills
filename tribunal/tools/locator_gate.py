#!/usr/bin/env python3
"""locator_gate.py — verifies the quote is WHERE the finding says it is.

Every prior system in this lineage verifies at most that a quote EXISTS. None verifies
that it exists where the finding claims. paper-workshop names this gap in its own
LIMITATIONS.md: "A real quote pinned to the wrong locator (a misattributed section, a
transposed line) passes the deterministic rail and is caught only by the LLM verification
angles, not by code."

This closes it. A real quote with a wrong locator is not a small clerical slip: it is the
signature of an agent that recalled a sentence and then guessed where it lived. That guess
is the first step of a hallucination, and it sends the author to the wrong page.

Verdicts:
    in-span       quote occurs inside the claimed sentence range          -> keep
    out-of-span   quote occurs, but ELSEWHERE (true range reported)       -> degrade + correct
    no-quote      quote occurs nowhere (quote_gate.py owns this failure)  -> degrade
    no-map        no sentence range supplied, or map missing              -> degrade
    exempt        absence-class finding with an empty quote               -> keep

Usage:
    locator_gate.py batch --findings <f.json> --source <paper.txt> --map <sentence_map.json>
    locator_gate.py selftest
"""
import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import (SelfTest, dehyphenate, die, emit, load_json, normalize,  # noqa: E402
                     read_text, tool_sha)

EXEMPT_CLASSES = {"absence-silence", "prior-art-omission", "substrate-defect", "seat-failure"}
SLACK = 1          # a quote may bleed one sentence past the claimed range; more is a miss


def _hay(s):
    n = normalize(s)
    return n, dehyphenate(n)


def locate(quote, source, smap):
    """Return (verdict, true_range|None). Pure function; no IO."""
    nq, dq = _hay(quote)
    if not nq:
        return "no-quote", None
    ns, ds = _hay(source)
    if nq not in ns and dq not in ds:
        return "no-quote", None
    # find the true sentence range by scanning the map
    hits = []
    for row in smap:
        rn, rd = _hay(row.get("text", ""))
        if nq and (nq in rn or dq in rd):
            hits.append(row["i"])
    if not hits:
        # the quote spans a sentence boundary: walk windows
        for start in range(len(smap)):
            acc = ""
            for j in range(start, min(start + 6, len(smap))):
                acc += " " + smap[j].get("text", "")
                an, ad = _hay(acc)
                if nq in an or dq in ad:
                    hits = list(range(start, j + 1))
                    break
            if hits:
                break
    if not hits:
        return "no-map", None
    return "found", [min(hits), max(hits)]


def judge(finding, source, smap):
    cls = finding.get("finding_class", "")
    quote = finding.get("quote") or ""
    if cls in EXEMPT_CLASSES and not normalize(quote):
        return {"verdict": "exempt", "true_range": None}
    loc = (finding.get("locator") or {})
    claimed = loc.get("sentence_range")
    verdict, true_range = locate(quote, source, smap)
    if verdict in ("no-quote",):
        return {"verdict": "no-quote", "true_range": None}
    if verdict == "no-map":
        return {"verdict": "no-map", "true_range": None,
                "detail": "quote exists in the substrate but could not be placed in the sentence map"}
    if not (isinstance(claimed, (list, tuple)) and len(claimed) == 2
            and all(isinstance(x, int) for x in claimed)):
        return {"verdict": "no-map", "true_range": true_range,
                "detail": "finding supplied no usable sentence_range"}
    lo, hi = min(claimed), max(claimed)
    tlo, thi = true_range
    if tlo >= lo - SLACK and thi <= hi + SLACK:
        return {"verdict": "in-span", "true_range": true_range}
    return {"verdict": "out-of-span", "true_range": true_range,
            "claimed_range": [lo, hi],
            "detail": "quote is real but lives at sentences %d-%d, not %d-%d" % (tlo, thi, lo, hi)}


def cmd_batch(args):
    findings = load_json(args.findings)
    if isinstance(findings, dict):
        findings = findings.get("findings", [])
    src = read_text(args.source)
    smap = load_json(args.map)
    rows, degraded = [], 0
    for f in findings:
        r = judge(f, src, smap)
        r["id"] = f.get("id", "?")
        if r["verdict"] not in ("in-span", "exempt"):
            degraded += 1
        rows.append(r)
    emit({"tool": "locator_gate", "tool_sha": tool_sha(), "total": len(rows),
          "degraded": degraded, "results": rows}, 0 if degraded == 0 else 2)


def selftest():
    t = SelfTest("locator_gate")
    src = "Alpha claim here. Beta claim here. Gamma claim here. Delta claim here."
    smap = [{"i": 0, "text": "Alpha claim here."}, {"i": 1, "text": "Beta claim here."},
            {"i": 2, "text": "Gamma claim here."}, {"i": 3, "text": "Delta claim here."}]
    ok = judge({"quote": "Beta claim", "locator": {"sentence_range": [1, 1]}}, src, smap)
    t.check("correct locator passes", ok["verdict"], "in-span")
    bad = judge({"quote": "Beta claim", "locator": {"sentence_range": [3, 3]}}, src, smap)
    t.check("real quote wrong place caught", bad["verdict"], "out-of-span")
    t.check("true range reported", bad["true_range"], [1, 1])
    t.check("no quote in doc", judge({"quote": "Omega claim",
                                      "locator": {"sentence_range": [0, 0]}}, src, smap)["verdict"], "no-quote")
    t.check("missing range degrades", judge({"quote": "Beta claim", "locator": {}}, src, smap)["verdict"], "no-map")
    t.check("absence class exempt", judge({"quote": "", "finding_class": "absence-silence"},
                                          src, smap)["verdict"], "exempt")
    t.check("non-empty quote on absence class still gated",
            judge({"quote": "Beta claim", "finding_class": "absence-silence",
                   "locator": {"sentence_range": [3, 3]}}, src, smap)["verdict"], "out-of-span")
    span = judge({"quote": "Beta claim here. Gamma claim", "locator": {"sentence_range": [1, 2]}}, src, smap)
    t.check("cross-sentence quote placed", span["verdict"], "in-span")
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("batch")
    b.add_argument("--findings", required=True); b.add_argument("--source", required=True)
    b.add_argument("--map", required=True)
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "batch":
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
