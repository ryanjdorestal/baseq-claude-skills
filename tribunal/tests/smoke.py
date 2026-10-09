#!/usr/bin/env python3
"""End-to-end smoke run over tests/fixtures/. Every assertion below is a guarantee
TRIBUNAL claims to make; if one fails, the claim is false and the installation is broken.

    python3 tests/smoke.py

Exit 0 = every guarantee held. Exit 1 = at least one did not.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
FIX = os.path.join(ROOT, "tests", "fixtures")
PY = sys.executable

FAILS = []
N = [0]


def check(label, got, want):
    N[0] += 1
    if got != want:
        FAILS.append("%s\n      got:  %r\n      want: %r" % (label, got, want))
        print("   x %s" % label)
    else:
        print("   . %s" % label)


def run(*args, **kw):
    r = subprocess.run([PY] + list(args), capture_output=True, text=True, cwd=kw.get("cwd", FIX))
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        out = {"_raw": r.stdout, "_err": r.stderr}
    return r.returncode, out


def main():
    work = tempfile.mkdtemp(prefix="tribunal-smoke-")
    sub = os.path.join(work, "substrate")
    print("\n=== ACT 0  cartography ===")
    rc, r = run(os.path.join(TOOLS, "substrate.py"), "build", "--paper", "paper",
                "--results", "results", "--out", sub)
    check("substrate builds", rc, 0)
    check("sentences segmented", r["coverage"]["sentences"] > 10, True)
    check("evidence files manifested", r["coverage"]["evidence_files"], 1)
    check("inputs are hash-bound", bool(r["audited_input_hashes"]), True)
    defects = json.load(open(os.path.join(sub, "substrate_defects.json")))
    check("table extraction declared as a blind spot",
          any(d["kind"] == "tables-flattened" for d in defects), True)

    rc, r = run(os.path.join(TOOLS, "injection_scan.py"), "scan",
                "--file", "paper/main.tex", "--quarantine-out", os.path.join(work, "q"))
    check("injection found in the manuscript", rc, 2)
    check("it is the reviewer-addressed comment",
          any("mark resolved" in h["match"] or "verified" in h["match"] for h in r["results"]), True)
    san = open(os.path.join(work, "q", "main.tex.sanitized")).read()
    check("payload is replaced by a visible marker", "[BLOCKED:" in san, True)
    check("payload no longer reachable by a prompt", "mark resolved" in san, False)

    print("\n=== ACT I  the docket ===")
    rc, ev = run(os.path.join(TOOLS, "evidence_check.py"), "batch",
                 "--claims", "claims.json", "--root", ".")
    check("evidence gate reports findings via exit 2", rc, 2)
    by = {x["id"]: x for x in ev["results"]}
    check("legal rounding verified (85.3 <- 85.28)", by["D-041"]["status"], "verified")
    check("rounding class recorded", by["D-041"]["match_class"], "rounded")
    check("second legal rounding verified", by["D-042"]["status"], "verified")
    check("exact integer verified", by["D-043"]["status"], "verified")
    check("fabricated number caught", by["D-044"]["status"], "value_not_found")
    check("missing evidence file caught", by["D-045"]["status"], "path_missing")

    rc, st = run(os.path.join(TOOLS, "stat_consistency.py"), "batch", "--checks", "stat_checks.json")
    check("stat gate reports findings via exit 2", rc, 2)
    sby = {x["id"]: x for x in st["results"]}
    check("GRIM catches the impossible mean", sby["D-071"]["status"], "inconsistent")
    check("GRIM clears the possible mean", sby["D-075"]["status"], "consistent")
    check("impossible percentage caught", sby["D-072"]["status"], "inconsistent")
    check("overstated improvement caught", sby["D-073"]["status"], "inconsistent")
    check("recomputed delta is 12.8", round(sby["D-073"]["recomputed"], 1), 12.8)
    check("impossible p-value caught", sby["D-074"]["status"], "inconsistent")
    check("significance crossing flagged",
          sby["D-074"].get("crosses_significance_threshold"), True)
    check("plausible SD cleared", sby["D-076"]["status"], "consistent")

    rc, cg = run(os.path.join(TOOLS, "citation_gate.py"), "check", "--bib", "refs.bib",
                 "--paper", os.path.join(sub, "paper.txt"), "--corpus", "lit")
    cby = {x["key"]: x for x in cg["results"]}
    check("existing cite verified from the corpus",
          cby["smith2023scaling"]["axes"]["existence"], "verified")
    check("uncorroborated cite retained, not removed",
          cby["jones2021"]["axes"]["existence"], "unverified")
    check("uncited bib entry surfaced", "neverCited" in cg["uncited_entries"], True)
    check("context axis is never claimed",
          all(x["axes"]["context"] == "unchecked" for x in cg["results"]), True)

    print("\n=== ACT III  gates on a seat's output ===")
    smap = json.load(open(os.path.join(sub, "sentence_map.json")))
    real = next(s for s in smap if "15%" in s["text"] or "15\\%" in s["text"])
    findings = [
        {"id": "F-001", "title": "Reconcile the 15% claim with the results",
         "severity": "High", "epistemic": "GROUNDED", "finding_class": "numeric-mismatch",
         "quote": "improvement over the strongest baseline",
         "locator": {"file": "substrate/paper.txt", "sentence_range": [real["i"], real["i"]]},
         "numeric_token": "15"},
        {"id": "F-002", "title": "Fabricated quote must not survive",
         "severity": "High", "epistemic": "GROUNDED", "finding_class": "unsupported-claim",
         "quote": "we prove optimality under all distributions",
         "locator": {"file": "substrate/paper.txt", "sentence_range": [1, 1]}},
        {"id": "F-003", "title": "Real quote pinned to the wrong place",
         "severity": "Medium", "epistemic": "GROUNDED", "finding_class": "scope-overclaim",
         "quote": "improvement over the strongest baseline",
         "locator": {"file": "substrate/paper.txt",
                     "sentence_range": [real["i"] + 8, real["i"] + 8]}},
        {"id": "F-004", "title": "No robustness evaluation is reported",
         "severity": "Medium", "epistemic": "GROUNDED", "finding_class": "absence-silence",
         "quote": "", "absence_probe": ["adversarial robustness", "distribution shift",
                                        "corruption benchmark"]},
        {"id": "F-005", "title": "Absence claim refuted by the paper's own text",
         "severity": "Medium", "epistemic": "GROUNDED", "finding_class": "absence-silence",
         "quote": "", "absence_probe": ["cross-lingual", "multilingual", "future work"]},
        {"id": "F-006", "title": "Cannot tell without the human-study file",
         "severity": "High", "epistemic": "CANT-TELL·SUBSTRATE",
         "finding_class": "statistical-inconsistency", "quote": "",
         "resolvent": "results/human_study.json — per-annotator ratings for the N=25 study"},
        {"id": "F-007", "title": "Uncertain finding with no resolvent is void",
         "severity": "Medium", "epistemic": "CANT-TELL·SUBSTRATE",
         "finding_class": "unsupported-claim", "quote": ""},
        {"id": "F-008", "title": "Confidence scores are banned",
         "severity": "Low", "epistemic": "SUSPECTED", "finding_class": "presentation-defect",
         "quote": "", "why_unanchored": "pattern only", "confidence": 0.82},
    ]
    fpath = os.path.join(work, "findings.json")
    json.dump(findings, open(fpath, "w"), indent=2)

    rc, qg = run(os.path.join(TOOLS, "quote_gate.py"), "batch", "--findings", fpath,
                 "--source", os.path.join(sub, "paper.txt"))
    q = {x["id"]: x for x in qg["results"]}
    check("real quote passes", q["F-001"]["matched"], True)
    check("fabricated quote fails", q["F-002"]["matched"], False)
    check("absence class is quote-exempt", q["F-004"]["how"], "exempt-absence")

    rc, lg = run(os.path.join(TOOLS, "locator_gate.py"), "batch", "--findings", fpath,
                 "--source", os.path.join(sub, "paper.txt"),
                 "--map", os.path.join(sub, "sentence_map.json"))
    lo = {x["id"]: x for x in lg["results"]}
    check("correct locator passes", lo["F-001"]["verdict"], "in-span")
    check("REAL QUOTE, WRONG PLACE is caught", lo["F-003"]["verdict"], "out-of-span")
    check("and the true location is reported back", lo["F-003"]["true_range"], [real["i"], real["i"]])

    rc, ag = run(os.path.join(TOOLS, "absence_gate.py"), "batch", "--findings", fpath,
                 "--source", os.path.join(sub, "paper.txt"))
    a = {x["id"]: x for x in ag["results"]}
    check("genuine silence certified absent", a["F-004"]["certified"], "absent")
    check("false silence degraded to present", a["F-005"]["certified"], "present")
    check("and the refuting snippet is returned", bool(a["F-005"]["hits"]), True)

    print("\n=== schema enforcement ===")
    rc, sc = run(os.path.join(TOOLS, "doctor.py"), "schema", "--findings", fpath)
    probs = {(p["finding"], p["problem"].split(" ")[0]) for p in sc["problems"]}
    check("resolventless CANT-TELL is void",
          ("F-007", "cant_tell_without_resolvent") in probs, True)
    check("numeric confidence field is rejected",
          ("F-008", "banned_confidence_field:confidence") in probs, True)
    check("valid findings raise no schema problem",
          any(p[0] == "F-001" for p in probs), False)

    print("\n=== panel + verdict ===")
    panel = [{"finding_id": "F-001", "angle": "quote-locator", "verdict": "upheld"},
             {"finding_id": "F-001", "angle": "logical-validity", "verdict": "upheld"},
             {"finding_id": "F-002", "angle": "quote-locator", "verdict": "rejected"},
             {"finding_id": "F-004", "angle": "steelman-charity", "verdict": "cant-tell"}]
    ppath = os.path.join(work, "panel.json")
    json.dump(panel, open(ppath, "w"), indent=2)
    jpath = os.path.join(work, "judged.json")
    rc, pj = run(os.path.join(TOOLS, "verdict.py"), "panel", "--findings", fpath,
                 "--verdicts", ppath, "--out", jpath)
    j = {x["id"]: x for x in pj["findings"]}
    check("verified finding is delivered", j["F-001"]["status"], "delivered")
    check("gate-failed finding is rejected", j["F-002"]["status"], "rejected")
    check("rejection carries a reason", bool(j["F-002"]["reject_reason"]), True)
    check("all-cant-tell becomes CONTESTED, not delivered", j["F-004"]["status"], "contested")
    check("UNJUDGED finding fails closed to rejected", j["F-006"]["status"], "rejected")

    dpath = os.path.join(work, "DOCKET.json")
    json.dump({"run_id": "smoke", "generated_at": "2026-08-05T00:00:00Z", "rows": [],
               "counts": {}, "audited_input_hashes": {}, "blocking": []}, open(dpath, "w"))
    rc, v = run(os.path.join(TOOLS, "verdict.py"), "rule", "--docket", dpath, "--findings", jpath)
    check("a surviving High forces HARD_FLAGS", v["verdict"], "HARD_FLAGS")
    check("never claims independence it does not have", v["review_independence"], "same-family")
    check("acceptance is always provisional", v["acceptance_status"], "provisional")

    json.dump({"run_id": "s", "generated_at": "x", "rows": [], "counts": {},
               "audited_input_hashes": {},
               "blocking": ["numeric_claims_present_no_raw_evidence"]}, open(dpath, "w"))
    rc, v2 = run(os.path.join(TOOLS, "verdict.py"), "rule", "--docket", dpath, "--findings", jpath)
    check("docket alone can block a run", v2["verdict"], "BLOCKED")

    print("\n=== canary sensitivity ===")
    cpath, kpath = os.path.join(work, "canary.txt"), os.path.join(work, "key.json")
    rc, cp = run(os.path.join(TOOLS, "canary.py"), "plant", "--paper",
                 os.path.join(sub, "paper.txt"), "--out", cpath, "--key", kpath, "--n", "5",
                 "--seed", "42")
    check("defects planted", cp["planted"] >= 4, True)
    blind = os.path.join(work, "blind.json")
    json.dump([{"id": "F-90", "title": "typo", "quote": "teh"}], open(blind, "w"))
    rc, sc2 = run(os.path.join(TOOLS, "canary.py"), "score", "--key", kpath, "--findings", blind)
    check("a blind fleet scores zero recall", sc2["caught"], 0)
    spath = os.path.join(work, "sens.json")
    json.dump({"planted": sc2["planted"], "caught": 0}, open(spath, "w"))
    json.dump({"run_id": "s", "generated_at": "x", "rows": [], "counts": {},
               "audited_input_hashes": {}, "blocking": []}, open(dpath, "w"))
    empty = os.path.join(work, "empty.json")
    json.dump([], open(empty, "w"))
    rc, v3 = run(os.path.join(TOOLS, "verdict.py"), "rule", "--docket", dpath,
                 "--findings", empty, "--sensitivity", spath)
    check("a blind fleet cannot deliver a clean ruling", v3["verdict"], "REVIEW_UNAVAILABLE")

    print("\n=== staleness ===")
    art = os.path.join(work, "TRIBUNAL.json")
    tex = os.path.join(FIX, "paper", "main.tex")
    sys.path.insert(0, TOOLS)
    from _common import sha256_file                                 # noqa: E402
    json.dump({"audited_input_hashes": {tex: sha256_file(tex)}}, open(art, "w"))
    rc, f1 = run(os.path.join(TOOLS, "doctor.py"), "freshness", "--artifact", art)
    check("unedited inputs read CURRENT", f1["status"], "CURRENT")
    json.dump({"audited_input_hashes": {tex: "sha256:" + "0" * 64}}, open(art, "w"))
    rc, f2 = run(os.path.join(TOOLS, "doctor.py"), "freshness", "--artifact", art)
    check("an edited input voids the ruling", f2["status"], "STALE")

    print("\n=== obligations ledger ===")
    L = os.path.join(work, "OBLIGATIONS.jsonl")
    run(os.path.join(TOOLS, "ledger.py"), "sweep", "--ledger", L, "--findings", jpath, "--run", "r1")
    gone = os.path.join(work, "gone.json")
    json.dump([f for f in findings if f["id"] != "F-001"], open(gone, "w"))
    rc, sw = run(os.path.join(TOOLS, "ledger.py"), "sweep", "--ledger", L,
                 "--findings", gone, "--run", "r2")
    check("a finding that vanishes stays open", "F-001" in sw["unresolved_disappearance"], True)
    rc, stt = run(os.path.join(TOOLS, "ledger.py"), "status", "--ledger", L)
    check("open obligations block the gate", rc, 2)
    f1row = [o for o in stt["open"] if o["finding"] == "F-001"][0]
    check("disappearance is flagged permanently",
          "UNRESOLVED_DISAPPEARANCE" in f1row["flags"], True)

    print("\n" + "=" * 62)
    if FAILS:
        print("FAILED %d of %d guarantees\n" % (len(FAILS), N[0]))
        for f in FAILS:
            print("  x " + f)
        sys.exit(1)
    print("ok  all %d guarantees held" % N[0])


if __name__ == "__main__":
    main()
