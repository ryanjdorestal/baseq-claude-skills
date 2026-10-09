#!/usr/bin/env python3
"""canary.py — plants known defects so the run measures its own sensitivity.

Every system in this lineage ships with zero measured effectiveness. paper-workshop is the
only one honest enough to say so: "We have not yet published a run on third-party papers
with known/planted flaws scoring recall and false-positive rate. Until that exists, treat
the output as one very thorough opinion, not validated ground truth."

This closes that gap for THIS run, on THIS paper. A shadow copy of the substrate is
mutated with K defects whose locations are known. The same fleet reviews it, blind. The
catch rate goes in the deliverable.

WHY IT MATTERS: a quiet ruling from a fleet that cannot find defects someone deliberately
planted is not evidence of a clean paper -- it is evidence of a blind fleet. verdict.py
downgrades on low sensitivity, and refuses CLEAN_GIVEN_EVIDENCE entirely at zero recall.

THE ANSWER KEY IS A FORBIDDEN INPUT. It never enters a reviewer's context, and no seat is
told a canary run is happening. Deterministic seeding makes runs reproducible without
telling anyone what was planted.

Usage:
    canary.py plant --paper substrate/paper.txt --out canary/paper.txt --key canary/key.json
                    [--n 6] [--seed 1234]
    canary.py score --key canary/key.json --findings canary/findings.json
    canary.py selftest
"""
import argparse
import json
import os
import random
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import SelfTest, die, emit, load_json, normalize, read_text, tool_sha  # noqa: E402

NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,2})?)(?=\s*%|\b)")
CAVEAT = re.compile(r"[^.]*\b(?:however|limitation|caveat|we do not|cannot|only .{0,20}dataset|"
                    r"future work|we did not)\b[^.]*\.", re.I)
CITE = re.compile(r"(?:\\cite[a-zA-Z]*\{|\[cite:\s*)([^}\]]+)[}\]]")
OVERCLAIM = (" Our method consistently outperforms all baselines across every setting and "
             "generalizes without exception.")


def _sentences(text):
    out, pos = [], 0
    for piece in re.split(r"(?<=[.!?])\s+", text):
        if piece.strip():
            i = text.find(piece, pos)
            out.append((i, i + len(piece), piece))
            pos = i + len(piece)
    return out


def plant(text, n=6, seed=1234):
    rng = random.Random(seed)
    sents = _sentences(text)
    key, out, used = [], text, set()

    def record(kind, original, planted, detect, where):
        key.append({"id": "C-%02d" % (len(key) + 1), "kind": kind, "original": original,
                    "planted": planted, "detect": detect, "where": where})

    # 1-2. numeric drift (the bread-and-butter defect: a number that no longer reconciles)
    cands = [(i, s) for i, (_a, _b, s) in enumerate(sents) if NUM.search(s)]
    rng.shuffle(cands)
    for i, s in cands[:max(1, n // 3)]:
        m = NUM.search(s)
        old = m.group(1)
        try:
            new = ("%.*f" % (len(old.split(".")[1]) if "." in old else 0,
                             float(old) * 1.09 + 1.3))
        except ValueError:
            continue
        if new == old:
            continue
        new_s = s[:m.start(1)] + new + s[m.end(1):]
        out = out.replace(s, new_s, 1)
        used.add(i)
        record("numeric-drift", old, new,
               "a reported number inflated by ~10%%; should fail evidence_check or read as "
               "inconsistent with neighbouring values", {"sentence_hint": s[:80]})
        if len([k for k in key if k["kind"] == "numeric-drift"]) >= max(1, n // 3):
            break

    # 3. scope overclaim appended to a real sentence
    free = [(i, s) for i, (_a, _b, s) in enumerate(sents) if i not in used and len(s) > 40]
    if free and len(key) < n:
        i, s = rng.choice(free)
        out = out.replace(s, s.rstrip() + OVERCLAIM, 1)
        used.add(i)
        record("scope-overclaim", "", OVERCLAIM.strip(),
               "an unqualified universal claim ('consistently', 'every setting', 'without "
               "exception') unsupported by any evidence in the paper", {"sentence_hint": s[:80]})

    # 4. deleted caveat -> an ABSENCE defect, which only the absence lane can catch
    cav = CAVEAT.search(out)
    if cav and len(key) < n:
        removed = cav.group(0).strip()
        out = out.replace(removed, "", 1)
        record("deleted-caveat", removed, "",
               "a limitation/caveat sentence was removed; the paper now overclaims by "
               "silence", {"removed_text": removed[:160]})

    # 5. citation swap
    cm = CITE.search(out)
    if cm and len(key) < n:
        old = cm.group(1).split(",")[0].strip()
        new = old + "x"
        # works for both \cite{key} and the substrate's [cite:key] anchor form
        out = out[:cm.start()] + cm.group(0).replace(old, new, 1) + out[cm.end():]
        record("citation-swap", old, new,
               "a citation key that resolves to nothing; citation_gate should report it "
               "unresolved", {"key": new})

    # 6. delta error: a stated relative improvement that does not follow from its operands
    if len(key) < n:
        inject = (" Overall this represents a 41% improvement over the strongest baseline.")
        anchor = sents[-1][2] if sents else ""
        if anchor:
            out = out.replace(anchor, anchor.rstrip() + inject, 1)
            record("delta-error", "", inject.strip(),
                   "a relative-improvement figure that does not follow from any pair of "
                   "reported numbers", {"phrase": "41% improvement"})
    return out, key[:n]


def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9.]+", normalize(s)) if len(w) > 2}


def score(key, findings):
    rows, caught = [], 0
    for k in key:
        needle = str(k.get("planted") or k.get("original") or "")
        hint = " ".join(str(v) for v in (k.get("where") or {}).values())
        # token set from the DEFECT ITSELF only. The `detect` prose is a human hint and
        # must never be matched against -- a finding that merely echoes our own wording
        # is not a catch.
        ktok = _tokens(needle)
        hit = None
        for f in findings:
            blob = normalize(" ".join(str(f.get(x, "")) for x in
                                      ("title", "quote", "detail", "body")) + " " +
                             json.dumps(f.get("locator", {})))
            nn = normalize(needle)
            if nn and nn in blob:                       # finding quotes the defect whole
                hit = f.get("id"); break
            ftok = _tokens(blob)
            if len(ktok) >= 3 and len(ktok & ftok) / len(ktok) >= 0.5:
                hit = f.get("id"); break                # finding quotes a fragment of it
            if hint and normalize(hint[:40]) and normalize(hint[:40]) in blob:
                hit = f.get("id"); break                # finding lands on the same sentence
        if hit:
            caught += 1
        rows.append({"canary": k["id"], "kind": k["kind"], "caught": bool(hit),
                     "caught_by": hit})
    matched = {r["caught_by"] for r in rows if r["caught_by"]}
    unaccounted = [f.get("id") for f in findings if f.get("id") not in matched]
    return {"planted": len(key), "caught": caught,
            "recall": round(caught / len(key), 3) if key else None,
            "by_defect": rows,
            "unaccounted_findings": unaccounted,
            "note": "unaccounted findings are NOT false positives -- the shadow copy still "
                    "contains all of the paper's real defects. Only recall is measurable here."}


def selftest():
    t = SelfTest("canary")
    text = ("We evaluate on two datasets. Accuracy reaches 85.3% on the held-out split. "
            "However, we do not report per-seed variance. "
            "We compare against \\cite{smith2023} and report gains. "
            "The method is trained for 40 epochs with a batch size of 32.")
    out, key = plant(text, n=6, seed=7)
    t.check("planted something", len(key) >= 4, True)
    t.check("text actually changed", out != text, True)
    t.check("numeric drift planted", any(k["kind"] == "numeric-drift" for k in key), True)
    t.check("caveat removed", "we do not report per-seed variance" in out.lower(), False)
    t.check("citation swapped", "smith2023x" in out, True)
    t.check("overclaim present", "without exception" in out, True)
    out2, key2 = plant(text, n=6, seed=7)
    t.check("deterministic under a seed", out2, out)
    t.check("key is deterministic too", key2, key)
    drift = [k for k in key if k["kind"] == "numeric-drift"][0]
    good = [{"id": "F-1", "title": "number does not reconcile",
             "quote": "Accuracy reaches %s" % drift["planted"], "locator": {}},
            {"id": "F-2", "title": "unqualified universal claim",
             "quote": "consistently outperforms all baselines across every setting", "locator": {}}]
    s = score(key, good)
    t.check("catches what was found", s["caught"] >= 2, True)
    t.check("recall computed", 0.0 < s["recall"] <= 1.0, True)
    blind = score(key, [{"id": "F-9", "title": "typo in section 2", "quote": "teh", "locator": {}}])
    t.check("blind fleet scores zero", blind["caught"], 0)
    t.check("unaccounted are not called false positives",
            "false positives" in s["note"], True)
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    pl = sub.add_parser("plant"); pl.add_argument("--paper", required=True)
    pl.add_argument("--out", required=True); pl.add_argument("--key", required=True)
    pl.add_argument("--n", type=int, default=6); pl.add_argument("--seed", type=int, default=1234)
    sc = sub.add_parser("score"); sc.add_argument("--key", required=True)
    sc.add_argument("--findings", required=True)
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "selftest":
            selftest()
        elif a.cmd == "plant":
            text = read_text(a.paper)
            out, key = plant(text, a.n, a.seed)
            os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(out)
            os.makedirs(os.path.dirname(os.path.abspath(a.key)) or ".", exist_ok=True)
            with open(a.key, "w", encoding="utf-8") as fh:
                json.dump(key, fh, indent=2, ensure_ascii=False)
            emit({"tool": "canary.plant", "tool_sha": tool_sha(), "planted": len(key),
                  "out": a.out, "key": a.key,
                  "warning": "the key is a FORBIDDEN INPUT -- it must never enter a reviewer "
                             "context, and no seat may be told a canary run is happening"}, 0)
        elif a.cmd == "score":
            fs = load_json(a.findings)
            fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
            r = score(load_json(a.key), fs)
            r.update({"tool": "canary.score", "tool_sha": tool_sha()})
            emit(r, 0 if r["planted"] and r["caught"] == r["planted"] else 2)
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
