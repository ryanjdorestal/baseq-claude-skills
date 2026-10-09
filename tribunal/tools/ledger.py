#!/usr/bin/env python3
"""ledger.py — the append-only obligations ledger. Re-running can OPEN, never CLOSE.

The ledger exists because of one failure mode: an author edits the paper until the audit
goes quiet, and the quiet is mistaken for a fix. Deleting an anchored span kills a flag
faster than correcting the number.

Rules enforced here in code, not in prose:
  * APPEND-ONLY. Every event is a new line. Nothing is ever rewritten or deleted.
  * A finding that DISAPPEARS from a later run stays OPEN and gains UNRESOLVED_DISAPPEARANCE.
    Rewording the span is not a fix.
  * `claim-withdrawn` IS an honest fix -- deleting an unsupported claim is a legitimate
    resolution -- but it requires the deletion diff as evidence.
  * A WAIVER IS NOT A RESOLUTION. It is human-attributed, permanent, and the original
    finding snapshot stays immutable beside it.
  * RECEIPTS ARE RE-VERIFIED, NOT REMEMBERED. On every later gate the evidence file must
    still exist and still hash to what was recorded at closure. Edit the evidence after
    closing and the obligation RE-OPENS.
  * The author's fix_type label is a RECEIPT, NOT A VERDICT. A false label is a permanent
    false record.

Usage:
    ledger.py open   --ledger L.jsonl --finding F-001 --title "..." --severity High --run R1
    ledger.py close  --ledger L.jsonl --finding F-001 --fix-type number-corrected
                     --evidence results/rerun.json --by "ryan"
    ledger.py waive  --ledger L.jsonl --finding F-001 --by "ryan" --reason "..."
    ledger.py sweep  --ledger L.jsonl --findings current_run.json --run R2
    ledger.py verify --ledger L.jsonl
    ledger.py status --ledger L.jsonl
    ledger.py selftest
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import SelfTest, die, emit, load_json, sha256_file, tool_sha  # noqa: E402

FIX_TYPES = ("number-corrected", "analysis-rerun", "claim-narrowed", "claim-withdrawn",
             "evidence-supplied", "text-clarified")
EVIDENCE_REQUIRED = set(FIX_TYPES)          # every closure needs a receipt, no exceptions


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append(path, event):
    event.setdefault("at", _now())
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_events(path):
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def state(events):
    """Fold the append-only log into current obligation state."""
    st = {}
    for e in events:
        fid = e.get("finding")
        if not fid:
            continue
        cur = st.setdefault(fid, {"finding": fid, "status": "OPEN", "flags": [],
                                  "history": [], "snapshot": None})
        cur["history"].append(e)
        kind = e.get("event")
        if kind == "open":
            cur["status"] = "OPEN"
            cur["snapshot"] = cur["snapshot"] or {k: e.get(k) for k in
                                                  ("title", "severity", "run", "at")}
        elif kind == "close":
            cur["status"] = "CLOSED"
            cur["closure"] = {"fix_type": e.get("fix_type"), "evidence": e.get("evidence"),
                              "evidence_sha": e.get("evidence_sha"), "by": e.get("by"),
                              "at": e.get("at")}
        elif kind == "waive":
            cur["status"] = "WAIVED"
            cur["waiver"] = {"by": e.get("by"), "reason": e.get("reason"), "at": e.get("at")}
        elif kind == "reopen":
            cur["status"] = "OPEN"
            for f in e.get("flags", []):
                if f not in cur["flags"]:
                    cur["flags"].append(f)
    return st


def cmd_open(a):
    ev = append(a.ledger, {"event": "open", "finding": a.finding, "title": a.title,
                           "severity": a.severity, "run": a.run})
    emit({"tool": "ledger.open", "tool_sha": tool_sha(), "event": ev}, 0)


def cmd_close(a):
    if a.fix_type not in FIX_TYPES:
        die("bad_fix_type:%s (allowed: %s)" % (a.fix_type, ", ".join(FIX_TYPES)))
    if a.fix_type in EVIDENCE_REQUIRED and not a.evidence:
        die("evidence_required: fix_type '%s' cannot close without a receipt file" % a.fix_type)
    if not os.path.isfile(a.evidence):
        die("evidence_missing:%s -- a receipt that does not exist cannot close anything" % a.evidence)
    ev = append(a.ledger, {"event": "close", "finding": a.finding, "fix_type": a.fix_type,
                           "evidence": a.evidence, "evidence_sha": sha256_file(a.evidence),
                           "by": a.by,
                           "note": "fix_type is a receipt, not a verdict; a false label is a "
                                   "permanent false record"})
    emit({"tool": "ledger.close", "tool_sha": tool_sha(), "event": ev}, 0)


def cmd_waive(a):
    ev = append(a.ledger, {"event": "waive", "finding": a.finding, "by": a.by,
                           "reason": a.reason,
                           "note": "a waiver is not a resolution; the original finding stands"})
    emit({"tool": "ledger.waive", "tool_sha": tool_sha(), "event": ev}, 0)


def cmd_sweep(a):
    """Compare a new run's findings against the ledger. Opens new obligations; flags any
    previously-open obligation that has VANISHED rather than been fixed."""
    fs = load_json(a.findings)
    fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
    present = {f.get("id") for f in fs}
    titles = {f.get("id"): f.get("title") for f in fs}
    st = state(read_events(a.ledger))
    opened, disappeared = [], []
    for fid in present:
        if fid not in st:
            append(a.ledger, {"event": "open", "finding": fid, "title": titles.get(fid),
                              "severity": next((f.get("severity") for f in fs if f.get("id") == fid), None),
                              "run": a.run})
            opened.append(fid)
    for fid, cur in st.items():
        if cur["status"] == "OPEN" and fid not in present:
            append(a.ledger, {"event": "reopen", "finding": fid, "run": a.run,
                              "flags": ["UNRESOLVED_DISAPPEARANCE"],
                              "note": "this finding vanished from a later run without a "
                                      "recorded fix; rewording the span is not a fix"})
            disappeared.append(fid)
    emit({"tool": "ledger.sweep", "tool_sha": tool_sha(), "run": a.run,
          "opened": opened, "unresolved_disappearance": disappeared,
          "still_open": [f for f, c in state(read_events(a.ledger)).items() if c["status"] == "OPEN"]},
         0 if not disappeared else 2)


def cmd_verify(a):
    """Re-verify every closure receipt. Editing the evidence after closing RE-OPENS."""
    st = state(read_events(a.ledger))
    broken = []
    for fid, cur in st.items():
        c = cur.get("closure")
        if cur["status"] != "CLOSED" or not c:
            continue
        path, want = c.get("evidence"), c.get("evidence_sha")
        if not path or not os.path.isfile(path):
            broken.append({"finding": fid, "why": "evidence_gone", "evidence": path})
        elif sha256_file(path) != want:
            broken.append({"finding": fid, "why": "evidence_changed_after_closure",
                           "evidence": path})
    for b in broken:
        append(a.ledger, {"event": "reopen", "finding": b["finding"],
                          "flags": ["RECEIPT_INVALID"], "note": b["why"]})
    emit({"tool": "ledger.verify", "tool_sha": tool_sha(), "checked": len(st),
          "reopened": broken}, 0 if not broken else 2)


def cmd_status(a):
    st = state(read_events(a.ledger))
    buckets = {"OPEN": [], "CLOSED": [], "WAIVED": []}
    for fid, cur in sorted(st.items()):
        buckets.setdefault(cur["status"], []).append(
            {"finding": fid, "flags": cur["flags"], "snapshot": cur["snapshot"]})
    emit({"tool": "ledger.status", "tool_sha": tool_sha(),
          "open": buckets["OPEN"], "closed": buckets["CLOSED"], "waived": buckets["WAIVED"],
          "gate": "OPEN obligations block the gate; the ledger decides, not the verdict"},
         0 if not buckets["OPEN"] else 2)


def selftest():
    import tempfile
    t = SelfTest("ledger")
    d = tempfile.mkdtemp()
    L = os.path.join(d, "L.jsonl")
    ev = os.path.join(d, "rerun.json")
    with open(ev, "w") as fh:
        fh.write('{"acc": 85.28}')
    append(L, {"event": "open", "finding": "F-001", "title": "x", "severity": "High", "run": "R1"})
    t.check("opens", state(read_events(L))["F-001"]["status"], "OPEN")
    append(L, {"event": "close", "finding": "F-001", "fix_type": "number-corrected",
               "evidence": ev, "evidence_sha": sha256_file(ev), "by": "ryan"})
    t.check("closes with receipt", state(read_events(L))["F-001"]["status"], "CLOSED")
    # tamper with the receipt: the obligation must re-open
    with open(ev, "w") as fh:
        fh.write('{"acc": 99.9}')
    st = state(read_events(L))
    c = st["F-001"]["closure"]
    t.check("tampered receipt detected", sha256_file(ev) == c["evidence_sha"], False)
    append(L, {"event": "reopen", "finding": "F-001", "flags": ["RECEIPT_INVALID"]})
    st = state(read_events(L))
    t.check("re-opens on tamper", st["F-001"]["status"], "OPEN")
    t.check("flag recorded", "RECEIPT_INVALID" in st["F-001"]["flags"], True)
    # disappearance
    append(L, {"event": "open", "finding": "F-002", "title": "y", "severity": "High", "run": "R1"})
    append(L, {"event": "reopen", "finding": "F-002", "flags": ["UNRESOLVED_DISAPPEARANCE"]})
    t.check("disappearance keeps it open", state(read_events(L))["F-002"]["status"], "OPEN")
    t.check("disappearance flagged",
            "UNRESOLVED_DISAPPEARANCE" in state(read_events(L))["F-002"]["flags"], True)
    # waiver is not a resolution
    append(L, {"event": "waive", "finding": "F-002", "by": "ryan", "reason": "accepted risk"})
    st = state(read_events(L))
    t.check("waived is its own state", st["F-002"]["status"], "WAIVED")
    t.check("original snapshot immutable", st["F-002"]["snapshot"]["severity"], "High")
    t.check("history is append-only", len(st["F-002"]["history"]), 3)
    t.check("nothing was deleted", len(read_events(L)), 6)
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    o = sub.add_parser("open")
    for f in ("finding", "title", "severity", "run"):
        o.add_argument("--" + f, required=(f == "finding"))
    o.add_argument("--ledger", required=True)
    c = sub.add_parser("close"); c.add_argument("--ledger", required=True)
    c.add_argument("--finding", required=True); c.add_argument("--fix-type", required=True)
    c.add_argument("--evidence", required=True); c.add_argument("--by", required=True)
    w = sub.add_parser("waive"); w.add_argument("--ledger", required=True)
    w.add_argument("--finding", required=True); w.add_argument("--by", required=True)
    w.add_argument("--reason", required=True)
    s = sub.add_parser("sweep"); s.add_argument("--ledger", required=True)
    s.add_argument("--findings", required=True); s.add_argument("--run", required=True)
    v = sub.add_parser("verify"); v.add_argument("--ledger", required=True)
    st = sub.add_parser("status"); st.add_argument("--ledger", required=True)
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        fn = {"open": cmd_open, "close": cmd_close, "waive": cmd_waive, "sweep": cmd_sweep,
              "verify": cmd_verify, "status": cmd_status}.get(a.cmd)
        if a.cmd == "selftest":
            selftest()
        elif fn:
            fn(a)
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
