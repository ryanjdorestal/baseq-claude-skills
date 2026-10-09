#!/usr/bin/env python3
"""substrate.py — Act 0 cartography. Builds the addressable substrate every gate reads.

Produces, under <out>/:
    paper.txt              verbatim extracted text -- THE substrate for every quote gate call
    sentence_map.json      disjoint, gapless sentence ranges with char offsets + section
    evidence_manifest.json every raw result/config file with sha256 + size
    substrate_defects.json declared extraction blind spots  <-- the anti-artifact-finding list
    substrate.json         hashes, coverage, extraction path

The defects file exists so that no seat can file "Figure 3 is missing" when the truth is
that text extraction dropped it. Absence from an extraction is an EXTRACTION ARTIFACT, not
a defect in the author's document. Every seat receives this list as a declared blind spot
register, and a finding that contradicts it is void.

Usage:
    substrate.py build --paper <file|dir> [--results <dir>] [--out <dir>]
    substrate.py selftest
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import (SelfTest, die, emit, normalize, read_text, sha256_file,  # noqa: E402
                     sha256_text, tool_sha)
import json  # noqa: E402

TEXT_EXT = {".txt", ".md", ".tex", ".rst", ".org"}
RESULT_EXT = {".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml", ".npy", ".pkl", ".log"}
# executor summaries are FORBIDDEN inputs -- they launder interpretation into evidence
EXCLUDE_NAMES = re.compile(
    r"(EXPERIMENT_LOG|EXPERIMENT_TRACKER|AUTO_REVIEW|NARRATIVE_REPORT|FINDINGS|"
    r"CLAUDE|AGENTS|MEMORY|RULING|TRIBUNAL|notes?)", re.I)

_SENT_END = re.compile(r"(?<=[.!?])[\)\"']*\s+")
_TEX_COMMENT = re.compile(r"(?<!\\)%.*$", re.M)
_TEX_CMD = re.compile(r"\\(?:label|ref|usepackage|documentclass|begin|end)\s*(\[[^\]]*\])?\{[^}]*\}")
# citations survive stripping as [cite:key] anchors: a seat must be able to see WHERE a
# work is cited, and citation_gate.py needs the keys to exist in the substrate at all.
_TEX_CITE = re.compile(r"\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}")
_SECTION = re.compile(r"^\s*(?:\\(?:sub)*section\*?\{([^}]*)\}|#{1,4}\s+(.*)|"
                      r"(\d+(?:\.\d+)*)\s+([A-Z][^\n]{2,60}))\s*$", re.M)


def _extract_pdf(path, defects):
    if not shutil.which("pdftotext"):
        defects.append({"kind": "no-pdf-extractor", "where": path,
                        "detail": "pdftotext not installed; PDF could not be read",
                        "consequence": "no finding may be filed about this file's content"})
        return ""
    try:
        out = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", path, "-"],
                             capture_output=True, timeout=120)
        txt = out.stdout.decode("utf-8", "replace")
        if out.returncode != 0 or not txt.strip():
            defects.append({"kind": "pdf-extraction-failed", "where": path,
                            "detail": out.stderr.decode("utf-8", "replace")[:400],
                            "consequence": "no finding may be filed about this file's content"})
        return txt
    except Exception as e:                                   # noqa: BLE001
        defects.append({"kind": "pdf-extraction-error", "where": path, "detail": str(e)[:400],
                        "consequence": "no finding may be filed about this file's content"})
        return ""


def _strip_tex(text, defects, where):
    n_fig = len(re.findall(r"\\begin\{figure", text))
    n_tab = len(re.findall(r"\\begin\{table", text))
    if n_fig:
        defects.append({"kind": "figures-are-text-only", "where": where,
                        "detail": "%d figure environments; image content is NOT in the substrate" % n_fig,
                        "consequence": "no seat may claim a figure is missing, blank, or fails to render"})
    if n_tab:
        defects.append({"kind": "tables-flattened", "where": where,
                        "detail": "%d table environments; column alignment is lost" % n_tab,
                        "consequence": "cell-position claims must be verified against the source .tex"})
    t = _TEX_COMMENT.sub("", text)
    t = _TEX_CITE.sub(lambda m: "[cite:%s]" % m.group(1).strip(), t)
    t = _TEX_CMD.sub(" ", t)
    t = re.sub(r"\\[a-zA-Z]+\*?", " ", t)
    t = t.replace("{", " ").replace("}", " ").replace("~", " ")
    return t


def collect_paper(paper, defects):
    """Return (text, source_files, extraction_path)."""
    files, chunks, paths = [], [], []
    if os.path.isdir(paper):
        for pat in ("**/*.tex", "**/*.md", "**/*.txt", "**/*.pdf"):
            files += sorted(glob.glob(os.path.join(paper, pat), recursive=True))
        files = [f for f in files if not EXCLUDE_NAMES.search(os.path.basename(f))]
        # main.tex first: it defines document order
        files.sort(key=lambda f: (0 if os.path.basename(f).startswith("main") else 1, f))
    else:
        files = [paper]
    if not files:
        die("substrate_empty: no readable paper files under %s" % paper)
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext == ".pdf":
            chunks.append(_extract_pdf(f, defects)); paths.append("pdftotext -layout")
        elif ext == ".tex":
            chunks.append(_strip_tex(read_text(f), defects, f)); paths.append("tex-strip")
        elif ext in TEXT_EXT:
            chunks.append(read_text(f)); paths.append("verbatim")
        else:
            defects.append({"kind": "unsupported-format", "where": f, "detail": ext,
                            "consequence": "file not in substrate; no finding may cite it"})
            continue
        chunks.append("\n\n")
    text = "".join(chunks)
    if "\ufffd" in text:
        defects.append({"kind": "encoding-damage", "where": "substrate",
                        "detail": "%d replacement characters after decoding" % text.count("\ufffd"),
                        "consequence": "affected spans may be mojibake, not author error"})
    return text, files, "+".join(sorted(set(paths)))


def build_sentence_map(text):
    """Disjoint, gapless sentence ranges. This is what makes locator verification possible."""
    sections, cur = [], "(front matter)"
    for m in _SECTION.finditer(text):
        sections.append((m.start(), (m.group(1) or m.group(2) or
                                     ((m.group(3) or "") + " " + (m.group(4) or "")).strip())))
    rows, pos, idx = [], 0, 0
    for piece in _SENT_END.split(text):
        if not piece.strip():
            pos += len(piece)
            continue
        start = text.find(piece, pos)
        if start < 0:
            start = pos
        end = start + len(piece)
        while sections and sections[0][0] <= start:
            cur = sections.pop(0)[1]
        rows.append({"i": idx, "start": start, "end": end, "section": cur.strip(),
                     "text": piece.strip()})
        idx += 1
        pos = end
    return rows


def collect_evidence(results_dir):
    rows = []
    if not results_dir:
        return rows
    for root, _dirs, files in os.walk(results_dir):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext not in RESULT_EXT or EXCLUDE_NAMES.search(fn):
                continue
            try:
                rows.append({"id": "D-%03d" % (200 + len(rows)), "kind": "evidence-manifest",
                             "path": p, "sha256": sha256_file(p),
                             "bytes": os.path.getsize(p), "status": "present",
                             "provenance": "substrate.py"})
            except OSError as e:
                rows.append({"id": "D-%03d" % (200 + len(rows)), "kind": "evidence-manifest",
                             "path": p, "status": "unreadable", "detail": str(e),
                             "provenance": "substrate.py"})
    return rows


def cmd_build(args):
    out = args.out or ".tribunal/substrate"
    os.makedirs(out, exist_ok=True)
    defects = []
    text, files, path = collect_paper(args.paper, defects)
    if not text.strip():
        die("substrate_empty: extraction produced no text")
    smap = build_sentence_map(text)
    if not smap:
        die("substrate_empty: no sentences segmented")
    evidence = collect_evidence(args.results)
    if not evidence and args.results:
        defects.append({"kind": "no-evidence-files", "where": args.results,
                        "detail": "results directory supplied but contained no readable data files",
                        "consequence": "numeric claims cannot be reconciled; expect BLOCKED"})
    with open(os.path.join(out, "paper.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    for name, obj in (("sentence_map.json", smap),
                      ("evidence_manifest.json", evidence),
                      ("substrate_defects.json", defects)):
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
    meta = {"tool": "substrate", "tool_sha": tool_sha(), "out": out,
            "extraction_path": path, "source_files": files,
            "audited_input_hashes": {f: sha256_file(f) for f in files if os.path.isfile(f)},
            "paper_txt_sha": sha256_text(text),
            "coverage": {"sentences": len(smap), "chars": len(text),
                         "evidence_files": len(evidence)},
            "defects": len(defects)}
    with open(os.path.join(out, "substrate.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    emit(meta, 0)


def selftest():
    t = SelfTest("substrate")
    txt = "1 Introduction\nWe study X. It works well.\n2 Method\nWe do Y. Then Z."
    m = build_sentence_map(txt)
    t.check("segments sentences", len(m) >= 4, True)
    t.check("ranges disjoint+ordered", all(m[i]["end"] <= m[i + 1]["start"] for i in range(len(m) - 1)), True)
    t.check("offsets address real text", txt[m[1]["start"]:m[1]["end"]].strip().startswith("It works"), True)
    t.check("section tracked", "Method" in m[-1]["section"], True)
    d = []
    stripped = _strip_tex("% comment\n\\section{Results}\n\\begin{figure}x\\end{figure}\nWe report 5.", d, "t.tex")
    t.check("tex comment removed", "comment" in stripped, False)
    t.check("figure defect declared", any(x["kind"] == "figures-are-text-only" for x in d), True)
    t.check("prose survives", "We report 5." in stripped, True)
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("--paper", required=True); b.add_argument("--results"); b.add_argument("--out")
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "build":
            cmd_build(a)
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
