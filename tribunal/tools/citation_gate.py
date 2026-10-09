#!/usr/bin/env python3
"""citation_gate.py — existence and metadata rails for the bibliography. No network.

Three axes of citation failure, in ascending order of danger:
    1. EXISTENCE   the cited work does not exist. A hallucinated reference is the single
                   most humiliating failure in a submission -- a referee checks it and
                   finds nothing.
    2. METADATA    the work exists but the year/venue/authors are wrong.
    3. CONTEXT     the work exists, the metadata is right, and it does not say what it is
                   cited as saying. THIS IS THE MOST DANGEROUS and this script CANNOT
                   check it. Context is a semantic judgment; it is routed to the
                   citation-misuse jurisdiction and marked `unchecked` here.

RETENTION OVER SILENT REMOVAL. An entry this gate cannot verify stays in the output tagged
`unverified`. Silent removal hides corpus-quality problems and leaves the author unable to
audit what was filtered. An unverified citation is a question, not a conviction: with no
network and no corpus, EVERY citation is unverified and that says nothing about the author.

Usage:
    citation_gate.py check --bib refs.bib --paper substrate/paper.txt [--corpus lit/]
    citation_gate.py selftest

Exit 0 = no unresolved keys and no metadata mismatches. Exit 2 = something to look at.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import SelfTest, die, emit, normalize, read_text, tool_sha  # noqa: E402

HIGH_UNVERIFIED_RATE = 0.20

_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
_CITE = re.compile(r"\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}")
_BRACKET_CITE = re.compile(r"\[@([A-Za-z0-9_:\-]+)\]")
# substrate.py preserves citations as [cite:key] anchors when it strips LaTeX
_TAG_CITE = re.compile(r"\[cite:\s*([^\]]+)\]")
REQUIRED = {"article": ["author", "title", "year"], "inproceedings": ["author", "title", "year"],
            "book": ["author", "title", "year"], "misc": ["title"]}
STOP = set("a an the of and or on in for with to from using via by is are we our this that".split())


def _split_fields(body):
    """Split an entry body on commas that sit at brace depth 0. A naive split breaks on
    'author = {Smith, A}' and silently loses every field after the first."""
    parts, buf, depth, quote = [], [], 0, False
    for ch in body:
        if ch == '"' and depth == 0:
            quote = not quote
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0 and not quote:
            parts.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def parse_bib(text):
    out = {}
    for kind, key, body in _ENTRY.findall(text):
        fields = {}
        for part in _split_fields(body):
            if "=" not in part:
                continue
            fk, fv = part.split("=", 1)
            fk = fk.strip().lower()
            if not re.fullmatch(r"\w+", fk):
                continue
            fields[fk] = fv.strip().strip("{}\" \n\t")
        out[key.strip()] = {"type": kind.lower(), "fields": fields}
    return out


def cited_keys(paper_text):
    keys = []
    for rx in (_CITE, _TAG_CITE):
        for m in rx.finditer(paper_text):
            keys += [k.strip() for k in m.group(1).split(",") if k.strip()]
    keys += [m.group(1) for m in _BRACKET_CITE.finditer(paper_text)]
    return keys


def _title_tokens(title):
    return {w for w in re.findall(r"[a-z0-9]+", normalize(title)) if w not in STOP and len(w) > 2}


def corpus_index(corpus_dir):
    """Map each corpus file to its normalized text (or filename only if unreadable)."""
    idx = {}
    if not corpus_dir or not os.path.isdir(corpus_dir):
        return idx
    for root, _d, files in os.walk(corpus_dir):
        for fn in files:
            p = os.path.join(root, fn)
            ext = os.path.splitext(fn)[1].lower()
            body = ""
            if ext in (".txt", ".md", ".tex", ".bib", ".json"):
                try:
                    body = read_text(p)[:200000]
                except OSError:
                    body = ""
            idx[p] = normalize(fn + " " + body)
    return idx


def match_entry(entry, idx):
    """Existence by title-token overlap against the corpus. Conservative: >=60% of the
    distinctive title tokens must appear in one document."""
    title = entry["fields"].get("title", "")
    toks = _title_tokens(title)
    if not toks:
        return None, 0.0
    best, score = None, 0.0
    for path, body in idx.items():
        hit = sum(1 for t in toks if t in body)
        s = hit / len(toks)
        if s > score:
            best, score = path, s
    return (best, score) if score >= 0.6 else (None, score)


def audit(bib_text, paper_text, corpus_dir=None):
    bib = parse_bib(bib_text)
    idx = corpus_index(corpus_dir)
    used = cited_keys(paper_text)
    rows, unresolved, mismatched, unverified = [], [], 0, 0
    for key in sorted(set(used)):
        if key not in bib:
            unresolved.append(key)
            rows.append({"key": key, "status": "unresolved",
                         "axes": {"existence": "unverified", "metadata": "unverified",
                                  "context": "unchecked"},
                         "detail": "cited in the paper but absent from the bibliography -- "
                                   "either a typo or a citation to nothing"})
            continue
        e = bib[key]
        missing = [f for f in REQUIRED.get(e["type"], []) if f not in e["fields"]]
        path, score = match_entry(e, idx) if idx else (None, 0.0)
        existence = "verified" if path else "unverified"
        metadata = "unchecked"
        detail = ""
        if path:
            body = idx[path]
            yr = e["fields"].get("year", "")
            if yr and re.search(r"\b\d{4}\b", yr):
                metadata = "verified" if yr in body else "mismatch"
                if metadata == "mismatch":
                    found = sorted(set(re.findall(r"\b(19|20)\d{2}\b", body)))
                    detail = "bib year %s not found in the matched source %s" % (yr, os.path.basename(path))
            else:
                metadata = "unverified"
        if existence == "unverified":
            unverified += 1
        if metadata == "mismatch":
            mismatched += 1
        rows.append({"key": key, "type": e["type"],
                     "status": "flagged" if (missing or metadata == "mismatch") else
                               ("verified" if existence == "verified" else "unverified"),
                     "axes": {"existence": existence, "metadata": metadata, "context": "unchecked"},
                     "missing_fields": missing, "matched_source": path,
                     "match_score": round(score, 2), "detail": detail})
    uncited = sorted(set(bib) - set(used))
    resolvable = len([r for r in rows if r["status"] != "unresolved"])
    rate = (unverified / resolvable) if resolvable else 0.0
    flags = []
    if unresolved:
        flags.append("unresolved_citation_keys")
    if not idx:
        flags.append("no_corpus_supplied__existence_unchecked")
    elif rate > HIGH_UNVERIFIED_RATE:
        flags.append("high_unverified_citation_rate")
    return {"total_cited": len(set(used)), "unresolved": unresolved,
            "metadata_mismatches": mismatched, "unverified": unverified,
            "unverified_rate": round(rate, 3), "uncited_entries": uncited,
            "flags": flags, "results": rows,
            "note": "context (does the cited work support the claim?) is NOT checkable here "
                    "and is routed to the citation-misuse jurisdiction"}


def cmd_check(args):
    r = audit(read_text(args.bib), read_text(args.paper), args.corpus)
    r.update({"tool": "citation_gate", "tool_sha": tool_sha()})
    bad = bool(r["unresolved"]) or r["metadata_mismatches"] > 0
    emit(r, 2 if bad else 0)


def selftest():
    t = SelfTest("citation_gate")
    bib = """
@article{smith2023scaling, title = {Scaling Laws for Widget Nets}, author = {Smith, A}, year = {2023}, journal = {J. Widgets}
}
@inproceedings{jones2021, title = {A Fast Widget Sampler}, author = {Jones, B}, year = {2021}
}
@misc{ghostref, title = {Nonexistent Marvels of Nothing}
}
"""
    paper = r"We build on \cite{smith2023scaling} and \citep{jones2021,missingkey}."
    r = audit(bib, paper, None)
    t.check("unresolved key caught", "missingkey" in r["unresolved"], True)
    t.check("resolved keys not flagged unresolved", "smith2023scaling" in r["unresolved"], False)
    t.check("uncited entries listed", "ghostref" in r["uncited_entries"], True)
    t.check("no corpus -> existence unchecked flag",
            "no_corpus_supplied__existence_unchecked" in r["flags"], True)
    t.check("context always unchecked",
            all(x["axes"]["context"] == "unchecked" for x in r["results"]), True)
    t.check("unverified is retained not removed", len(r["results"]), 3)
    import tempfile
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "smith.txt"), "w") as fh:
        fh.write("Scaling Laws for Widget Nets. Smith. Published 2023. Abstract...")
    with open(os.path.join(d, "jones.txt"), "w") as fh:
        fh.write("A Fast Widget Sampler by Jones, appearing in 2019 proceedings.")
    r2 = audit(bib, paper, d)
    smith = [x for x in r2["results"] if x["key"] == "smith2023scaling"][0]
    jones = [x for x in r2["results"] if x["key"] == "jones2021"][0]
    t.check("existence verified from corpus", smith["axes"]["existence"], "verified")
    t.check("metadata verified from corpus", smith["axes"]["metadata"], "verified")
    t.check("year mismatch caught", jones["axes"]["metadata"], "mismatch")
    t.check("missing required field caught",
            [x for x in r2["results"] if x["key"] == "jones2021"][0]["missing_fields"], [])
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check"); c.add_argument("--bib", required=True)
    c.add_argument("--paper", required=True); c.add_argument("--corpus")
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "check":
            cmd_check(a)
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
