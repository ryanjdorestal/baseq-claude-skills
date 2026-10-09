#!/usr/bin/env python3
"""evidence_check.py — does the number in the paper exist in the raw data? FAIL CLOSED.

Stage 1 of a two-stage evidence gate:
    stage 1  THIS SCRIPT      deterministic, no model, fail-closed
             catches HALLUCINATION -- cited path missing, or cited value not in the source.
    stage 2  the reviewer     catches WRONG-BUT-REAL -- the number IS in the file, but it
             lanes            does not support the claim it is attached to.

A `verified` from stage 1 means ONLY that the cited evidence exists. It NEVER means the
claim holds. The pre-check DRIVES a gate; it cannot ACQUIT a claim.

CONSERVATIVE BY DESIGN. It favours false-negative over false-positive: when in doubt it
returns not-verified and lets a human read the file. A false `verified` is the one bug
this gate must never have.

Usage:
    evidence_check.py check --value 85.3 --file results/eval.json [--path $.eval.accuracy]
    evidence_check.py batch --claims claims.json --root .
    evidence_check.py selftest

claims.json: [{"id","value","file","path"(optional),"allow_rounding"(default true)}]
Exit 0 = all verified. Exit 2 = at least one is not (EXPECTED). Exit 3 = could not run.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import (SelfTest, decimal_equal, die, emit, find_numeric_token,  # noqa: E402
                     load_json, normalize, read_text, rounds_to, tool_sha)


def _walk_json(obj, want, allow_rounding, trail="$"):
    """Yield (path, value) for every scalar in the structure that matches `want`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_json(v, want, allow_rounding, trail + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_json(v, want, allow_rounding, trail + "[%d]" % i)
    else:
        if isinstance(obj, bool) or obj is None:
            return
        if isinstance(obj, (int, float)) or (isinstance(obj, str) and obj.strip()):
            eq = decimal_equal(obj, want)
            if eq:
                yield trail, obj, "exact"
            elif allow_rounding and rounds_to(obj, want):
                yield trail, obj, "rounded"


def _dig(obj, dotted):
    """Resolve a simple $.a.b[0] path. Returns (found, value)."""
    cur, tok = obj, dotted.lstrip("$").lstrip(".")
    if not tok:
        return True, obj
    for part in tok.replace("]", "").replace("[", ".").split("."):
        if part == "":
            continue
        if isinstance(cur, dict):
            if part not in cur:
                return False, None
            cur = cur[part]
        elif isinstance(cur, list):
            if not part.isdigit() or int(part) >= len(cur):
                return False, None
            cur = cur[int(part)]
        else:
            return False, None
    return True, cur


def check_claim(value, file_path, json_path=None, allow_rounding=True, root="."):
    p = file_path if os.path.isabs(file_path) else os.path.join(root, file_path)
    if not os.path.isfile(p):
        return {"status": "path_missing", "detail": "no such file: %s" % file_path}
    ext = os.path.splitext(p)[1].lower()
    if ext in (".json", ".jsonl"):
        try:
            if ext == ".jsonl":
                data = [json.loads(l) for l in read_text(p).splitlines() if l.strip()]
            else:
                data = json.loads(read_text(p))
        except Exception as e:                                  # noqa: BLE001
            return {"status": "unparseable", "detail": "%s: %s" % (type(e).__name__, e)}
        if json_path:
            found, got = _dig(data, json_path)
            if not found:
                return {"status": "value_not_found",
                        "detail": "path %s not present in %s" % (json_path, file_path)}
            if decimal_equal(got, value):
                return {"status": "verified", "match_class": "exact",
                        "evidence_value": got, "evidence_path": json_path}
            if allow_rounding and rounds_to(got, value):
                return {"status": "verified", "match_class": "rounded",
                        "evidence_value": got, "evidence_path": json_path,
                        "detail": "%s is standard rounding of %s" % (value, got)}
            return {"status": "value_not_found", "match_class": "mismatch",
                    "evidence_value": got, "evidence_path": json_path,
                    "detail": "file holds %s, paper claims %s" % (got, value)}
        hits = list(_walk_json(data, value, allow_rounding))
        if not hits:
            return {"status": "value_not_found",
                    "detail": "%s occurs nowhere in %s" % (value, file_path)}
        if len(hits) > 1:
            paths = [h[0] for h in hits[:6]]
            return {"status": "ambiguous_mapping", "candidates": paths,
                    "detail": "%d locations hold this value; the finding must name one" % len(hits)}
        path, got, cls = hits[0]
        return {"status": "verified", "match_class": cls, "evidence_value": got,
                "evidence_path": path}
    # text-ish source (csv/tsv/log/yaml): standalone numeric-token search only
    try:
        text = normalize(read_text(p), casefold=False)
    except Exception as e:                                      # noqa: BLE001
        return {"status": "unparseable", "detail": str(e)}
    if find_numeric_token(str(value), text):
        return {"status": "verified", "match_class": "exact", "evidence_path": "(text scan)"}
    return {"status": "value_not_found",
            "detail": "%s not found as a standalone token in %s" % (value, file_path)}


def cmd_check(args):
    r = check_claim(args.value, args.file, args.path, not args.no_rounding, args.root)
    r.update({"tool": "evidence_check", "tool_sha": tool_sha(),
              "value": args.value, "file": args.file})
    emit(r, 0 if r["status"] == "verified" else 2)


def cmd_batch(args):
    claims = load_json(args.claims)
    if isinstance(claims, dict):
        claims = claims.get("claims", [])
    rows, bad = [], 0
    counts = {}
    for c in claims:
        r = check_claim(c.get("value"), c.get("file", ""), c.get("path"),
                        c.get("allow_rounding", True), args.root)
        r["id"] = c.get("id", "?")
        r["value"] = c.get("value")
        r["file"] = c.get("file")
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        if r["status"] != "verified":
            bad += 1
        rows.append(r)
    emit({"tool": "evidence_check", "tool_sha": tool_sha(), "root": args.root,
          "total": len(rows), "not_verified": bad, "counts": counts, "results": rows},
         0 if bad == 0 else 2)


def selftest():
    import tempfile
    t = SelfTest("evidence_check")
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "eval.json"), "w") as fh:
        json.dump({"eval": {"accuracy": 85.28, "f1": 0.732}, "runs": [1, 2, 3]}, fh)
    with open(os.path.join(d, "log.csv"), "w") as fh:
        fh.write("seed,acc\n0,73.20\n1,71.4\n")
    t.check("exact via path", check_claim("85.28", "eval.json", "$.eval.accuracy", root=d)["status"], "verified")
    t.check("legal rounding", check_claim("85.3", "eval.json", "$.eval.accuracy", root=d)["match_class"], "rounded")
    t.check("illegal rounding caught",
            check_claim("85.9", "eval.json", "$.eval.accuracy", root=d)["status"], "value_not_found")
    t.check("rounding refusable",
            check_claim("85.3", "eval.json", "$.eval.accuracy", allow_rounding=False, root=d)["status"],
            "value_not_found")
    t.check("missing path", check_claim("1", "eval.json", "$.nope.here", root=d)["status"], "value_not_found")
    t.check("missing file", check_claim("1", "ghost.json", root=d)["status"], "path_missing")
    t.check("text scan token", check_claim("73.20", "log.csv", root=d)["status"], "verified")
    t.check("substring not a match", check_claim("73.2", "log.csv", root=d)["status"], "value_not_found")
    t.check("free search finds unique", check_claim("0.732", "eval.json", root=d)["status"], "verified")
    t.check("unparseable json", (lambda: (open(os.path.join(d, "bad.json"), "w").write("{oops"),
                                          check_claim("1", "bad.json", root=d)["status"])[1])(), "unparseable")
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    c = sub.add_parser("check")
    c.add_argument("--value", required=True); c.add_argument("--file", required=True)
    c.add_argument("--path"); c.add_argument("--root", default="."); c.add_argument("--no-rounding", action="store_true")
    b = sub.add_parser("batch"); b.add_argument("--claims", required=True); b.add_argument("--root", default=".")
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
