#!/usr/bin/env python3
"""doctor.py — is this installation sound, and is this run still current?

Three jobs:
    selftest   run every gate's embedded adversarial selftest. If one fails, the
               installation is broken and NO run may be trusted -- exit non-zero and say so.
    freshness  rehash every entry in a run's audited_input_hashes. Any drift is STALE:
               the artifact was edited after the audit, and the ruling is void. A hash
               cannot be talked into matching.
    schema     structural validation of the JSON contracts, so a malformed docket or
               findings file blocks the run instead of being half-read by an agent.

NEVER FAIL OPEN. Any internal crash is reported as BLOCKED, never as a pass.

Usage:
    doctor.py selftest
    doctor.py freshness --artifact .tribunal/<run>/DOCKET.json
    doctor.py schema --docket DOCKET.json | --findings findings.json
    doctor.py all --run .tribunal/<run>
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import die, emit, load_json, sha256_file, tool_sha  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = ["_common.py", "quote_gate.py", "absence_gate.py", "locator_gate.py",
         "evidence_check.py", "stat_consistency.py", "citation_gate.py",
         "injection_scan.py", "substrate.py", "verdict.py", "ledger.py", "canary.py"]

FINDING_REQUIRED = ["id", "title", "severity", "epistemic", "finding_class"]
SEVERITIES = {"High", "Medium", "Low"}
EPISTEMIC = {"GROUNDED", "INFERRED", "SUSPECTED", "CANT-TELL·SUBSTRATE",
             "CANT-TELL·COMPETENCE", "CANT-TELL-SUBSTRATE", "CANT-TELL-COMPETENCE",
             "CONTESTED"}
CANT_TELL = {"CANT-TELL·SUBSTRATE", "CANT-TELL·COMPETENCE",
             "CANT-TELL-SUBSTRATE", "CANT-TELL-COMPETENCE"}
BANNED_KEYS = {"confidence", "confidence_score", "probability", "certainty", "score", "odds"}


def run_selftests():
    rows, failed = [], 0
    for t in TOOLS:
        p = os.path.join(HERE, t)
        if not os.path.isfile(p):
            rows.append({"tool": t, "ok": False, "detail": "missing"})
            failed += 1
            continue
        r = subprocess.run([sys.executable, p, "selftest"], capture_output=True, text=True)
        ok = r.returncode == 0
        if not ok:
            failed += 1
        rows.append({"tool": t, "ok": ok,
                     "detail": (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout or r.stderr) else ""})
    return rows, failed


def freshness(artifact):
    data = load_json(artifact)
    hashes = data.get("audited_input_hashes") or {}
    if not hashes:
        return {"status": "BLOCKED", "detail": "artifact declares no audited_input_hashes; "
                                               "an audit that does not bind to its inputs "
                                               "cannot be checked for staleness"}
    stale, gone = [], []
    for path, want in hashes.items():
        if not os.path.isfile(path):
            gone.append(path)
        elif sha256_file(path) != want:
            stale.append(path)
    if gone or stale:
        return {"status": "STALE", "changed": stale, "missing": gone,
                "detail": "the reviewed inputs are no longer what was reviewed; this ruling "
                          "is void and the run must be repeated"}
    return {"status": "CURRENT", "checked": len(hashes)}


def validate_findings(findings):
    problems = []
    seen = set()
    for i, f in enumerate(findings):
        fid = f.get("id", "<no id>")
        for k in FINDING_REQUIRED:
            if not f.get(k):
                problems.append({"finding": fid, "problem": "missing_field:" + k})
        if fid in seen:
            problems.append({"finding": fid, "problem": "duplicate_id"})
        seen.add(fid)
        if f.get("severity") not in SEVERITIES:
            problems.append({"finding": fid, "problem": "bad_severity:%s" % f.get("severity")})
        ep = str(f.get("epistemic", ""))
        if ep not in EPISTEMIC:
            problems.append({"finding": fid, "problem": "bad_epistemic:%s" % ep})
        # Constitution SS4: no numeric confidence anywhere, at any nesting level
        blob = json.dumps(f).lower()
        for k in BANNED_KEYS:
            if '"%s"' % k in blob:
                problems.append({"finding": fid, "problem": "banned_confidence_field:" + k})
        if ep in CANT_TELL and not f.get("resolvent"):
            problems.append({"finding": fid,
                             "problem": "cant_tell_without_resolvent -- void per EPISTEMIC_LADDER"})
        if ep == "INFERRED" and not f.get("inference_chain"):
            problems.append({"finding": fid, "problem": "inferred_without_chain"})
        if ep == "SUSPECTED" and not f.get("why_unanchored"):
            problems.append({"finding": fid, "problem": "suspected_without_why_unanchored"})
        cls = f.get("finding_class", "")
        if cls in ("absence-silence", "prior-art-omission") and len(f.get("absence_probe") or []) < 3:
            problems.append({"finding": fid, "problem": "absence_class_without_probe(min 3 terms)"})
        if f.get("status") == "rejected" and not f.get("reject_reason"):
            problems.append({"finding": fid, "problem": "rejected_without_reason -- nothing "
                                                        "disappears without a recorded reason"})
        _ = i
    return problems


def validate_docket(docket):
    problems = []
    for k in ("run_id", "generated_at", "rows", "counts"):
        if k not in docket:
            problems.append({"docket": k, "problem": "missing_field"})
    for r in docket.get("rows", []):
        if "id" not in r or "kind" not in r or "status" not in r:
            problems.append({"docket": r.get("id", "?"), "problem": "row_missing_required_field"})
    if not docket.get("audited_input_hashes"):
        problems.append({"docket": "audited_input_hashes",
                         "problem": "missing -- the docket must bind to the files it read"})
    return problems


def cmd_all(a):
    out = {"tool": "doctor", "tool_sha": tool_sha(), "python": sys.version.split()[0]}
    rows, failed = run_selftests()
    out["selftests"] = {"failed": failed, "results": rows}
    run = a.run
    if run:
        dpath = os.path.join(run, "DOCKET.json")
        fpath = os.path.join(run, "findings_ledger.json")
        if os.path.isfile(dpath):
            out["docket_schema"] = validate_docket(load_json(dpath))
            out["freshness"] = freshness(dpath)
        if os.path.isfile(fpath):
            fs = load_json(fpath)
            fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
            out["findings_schema"] = validate_findings(fs)
    bad = (failed
           or out.get("freshness", {}).get("status") in ("STALE", "BLOCKED")
           or out.get("docket_schema") or out.get("findings_schema"))
    out["status"] = "BLOCKED" if bad else "OK"
    if failed:
        out["fatal"] = ("a gate selftest failed: this installation is broken and no ruling "
                        "it produces may be trusted")
    emit(out, 0 if out["status"] == "OK" else 2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("selftest")
    fr = sub.add_parser("freshness"); fr.add_argument("--artifact", required=True)
    sc = sub.add_parser("schema"); sc.add_argument("--docket"); sc.add_argument("--findings")
    al = sub.add_parser("all"); al.add_argument("--run")
    a = p.parse_args()
    try:
        if a.cmd == "selftest":
            rows, failed = run_selftests()
            emit({"tool": "doctor.selftest", "tool_sha": tool_sha(), "failed": failed,
                  "results": rows,
                  "fatal": ("a gate selftest failed: this installation is broken"
                            if failed else None)}, 0 if not failed else 2)
        elif a.cmd == "freshness":
            r = freshness(a.artifact)
            r.update({"tool": "doctor.freshness", "tool_sha": tool_sha()})
            emit(r, 0 if r["status"] == "CURRENT" else 2)
        elif a.cmd == "schema":
            probs = []
            if a.docket:
                probs += validate_docket(load_json(a.docket))
            if a.findings:
                fs = load_json(a.findings)
                fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
                probs += validate_findings(fs)
            emit({"tool": "doctor.schema", "tool_sha": tool_sha(),
                  "problems": probs, "ok": not probs}, 0 if not probs else 2)
        elif a.cmd == "all":
            cmd_all(a)
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:                                  # never fail open
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
