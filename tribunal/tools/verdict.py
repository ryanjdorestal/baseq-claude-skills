#!/usr/bin/env python3
"""verdict.py — dedup, panel aggregation, and the top-level ruling. Computed, never felt.

Constitution SS8: agents emit PER-ITEM CLASSIFICATIONS; scripts map classifications to
verdicts. No seat, no panel angle, no adjudicator and no chair assigns the top-level
verdict. An agent that writes one has violated the constitution and its output is void.

Three subcommands:
    dedup   deterministic merge of findings by class + locator overlap + numeric token
    panel   majority aggregation of blind verification verdicts, conservative-downward
    rule    the run's verdict, from the docket + gated findings + adjudicator + canaries

THE VERDICT VOCABULARY CONTAINS NO 'PASS'. This fleet is single-family and may never
acquit (Constitution SS7). The best attainable outcome is CLEAN_GIVEN_EVIDENCE: "no flag
was found in the evidence at hand." It is not an acceptance and must never be printed,
summarized or paraphrased as one.

Usage:
    verdict.py dedup --findings f.json [--out merged.json]
    verdict.py panel --findings f.json --verdicts panel.json [--out judged.json]
    verdict.py rule  --docket DOCKET.json --findings judged.json
                     [--adjudication adj.json] [--sensitivity sens.json]
    verdict.py selftest
"""
import argparse
import json
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import SelfTest, die, emit, load_json, normalize, tool_sha  # noqa: E402

SEV_ORDER = {"Low": 0, "Medium": 1, "High": 2}
SEV_NAME = {v: k for k, v in SEV_ORDER.items()}
NON_BLOCKING_CLASSES = {"contribution-undersell", "presentation-defect"}
PIPELINE_CLASSES = {"substrate-defect", "injection-artifact", "seat-failure"}
MAX_HIGH = 7


# ------------------------------------------------------------------------- dedup

def _key(f):
    cls = f.get("finding_class", "")
    loc = f.get("locator") or {}
    rng = loc.get("sentence_range") or []
    span = tuple(sorted(rng)) if len(rng) == 2 else None
    num = normalize(str(f.get("numeric_token", "")))
    return cls, span, num


def _overlap(a, b):
    if not a or not b:
        return False
    return not (a[1] < b[0] or b[1] < a[0])


def dedup(findings):
    merged, order = [], []
    for f in findings:
        cls, span, num = _key(f)
        hit = None
        for m in merged:
            mcls, mspan, mnum = _key(m)
            if cls != mcls:
                continue
            if num and mnum and num == mnum:
                hit = m; break
            if _overlap(span, mspan):
                hit = m; break
        if hit is None:
            g = dict(f)
            g.setdefault("corroborated_by", [])
            if f.get("emitted_by") and f["emitted_by"] not in g["corroborated_by"]:
                g["corroborated_by"].append(f["emitted_by"])
            g.setdefault("merged_from", [])
            merged.append(g)
            order.append(g["id"])
            continue
        # merge: higher severity wins, evidence is the union, corroboration accumulates
        if SEV_ORDER.get(f.get("severity"), 0) > SEV_ORDER.get(hit.get("severity"), 0):
            hit["severity"] = f["severity"]
            hit["title"] = f.get("title", hit.get("title"))
        for s in ([f.get("emitted_by")] if f.get("emitted_by") else []):
            if s not in hit["corroborated_by"]:
                hit["corroborated_by"].append(s)
        hit["merged_from"] = sorted(set(hit.get("merged_from", []) + [f.get("id")]))
        if f.get("quote") and f["quote"] not in (hit.get("quote") or ""):
            hit.setdefault("additional_quotes", []).append(f["quote"])
    return merged


# ------------------------------------------------------------------------- panel

def majority(verdicts_for_angle):
    """upheld | upheld-with-revision | rejected | unresolved. cant-tell is FAIL CLOSED:
    it never counts toward upholding, so an unsure panel cannot carry a finding."""
    v = list(verdicts_for_angle)
    if not v:
        return "unresolved"
    rej = sum(1 for x in v if x == "rejected")
    rev = sum(1 for x in v if x == "upheld-with-revision")
    up = sum(1 for x in v if x == "upheld") + rev
    if rej == 0 and up == 0:
        return "unresolved"
    if rej >= up and rej > 0:
        return "rejected"
    return "upheld-with-revision" if rev > up / 2 else "upheld"


def apply_panel(findings, panel_rows):
    """panel_rows: [{finding_id, angle, verdict, severity_revision?, note?}]"""
    by_id = {}
    for r in panel_rows:
        by_id.setdefault(r["finding_id"], []).append(r)
    out = []
    for f in findings:
        g = dict(f)
        rows = by_id.get(f["id"], [])
        angles = {}
        for r in rows:
            angles.setdefault(r["angle"], []).append(r.get("verdict", "cant-tell"))
        per_angle = {a: majority(vs) for a, vs in angles.items()}
        g["panel"] = {"per_angle": per_angle, "n_verdicts": len(rows)}
        # FAIL CLOSED: a finding no angle covered is never a silent keep
        if not per_angle:
            g["status"] = "rejected"
            g["reject_reason"] = "no verification angle covered this finding (fail closed)"
            out.append(g); continue
        if any(v == "rejected" for v in per_angle.values()):
            killed = [a for a, v in per_angle.items() if v == "rejected"]
            g["status"] = "rejected"
            g["reject_reason"] = "rejected by angle(s): " + ", ".join(sorted(killed))
        elif all(v == "unresolved" for v in per_angle.values()):
            g["status"] = "contested"
            g["epistemic"] = "CONTESTED"
        else:
            g["status"] = "delivered"
        # severity may only be revised DOWNWARD by the panel; upward is a note for the chair
        revs = [r.get("severity_revision") for r in rows if r.get("severity_revision")]
        if revs:
            low = min(SEV_ORDER.get(x, 2) for x in revs)
            if low < SEV_ORDER.get(g.get("severity", "Low"), 0):
                g["severity_revised_from"] = g.get("severity")
                g["severity"] = SEV_NAME[low]
            elif low > SEV_ORDER.get(g.get("severity", "Low"), 0):
                g.setdefault("panel_notes", []).append(
                    "an angle argued for HIGHER severity; not applied automatically")
        out.append(g)
    return out


# -------------------------------------------------------------------------- rule

def rule(docket, findings, adjudication=None, sensitivity=None):
    reasons, blocking = [], list((docket or {}).get("blocking", []))
    counts = {"High": 0, "Medium": 0, "Low": 0}
    delivered = [f for f in findings if f.get("status") == "delivered"]
    for f in delivered:
        if f.get("finding_class") in PIPELINE_CLASSES:
            continue
        counts[f.get("severity", "Low")] = counts.get(f.get("severity", "Low"), 0) + 1
    unresolved_substrate = [f for f in findings
                            if str(f.get("epistemic", "")).startswith("CANT-TELL")
                            and f.get("status") != "rejected"]
    adj = adjudication or {}
    still_unresolved = int(adj.get("still_unresolved", 0))
    sens = sensitivity or {}
    planted, caught = int(sens.get("planted", 0)), int(sens.get("caught", 0))
    low_sensitivity = bool(planted) and (caught / planted) < 0.6

    if any(str(b).startswith("gate_internal_error") or b == "substrate_empty" for b in blocking):
        verdict = "ERROR"; reasons.append("a gate could not run; never fail open")
    elif blocking:
        verdict = "BLOCKED"; reasons += ["docket blocking condition: " + str(b) for b in blocking]
    elif counts["High"] > 0 or still_unresolved > 0:
        verdict = "HARD_FLAGS"
        if counts["High"]:
            reasons.append("%d High-severity finding(s) survived verification" % counts["High"])
        if still_unresolved:
            reasons.append("%d attack point(s) the paper could not answer" % still_unresolved)
    elif counts["Medium"] > 0 or counts["Low"] > 0 or unresolved_substrate:
        verdict = "SOFT_FLAGS"
        reasons.append("%d Medium and %d Low finding(s)" % (counts["Medium"], counts["Low"]))
        if unresolved_substrate:
            reasons.append("%d question(s) could not be resolved from the evidence supplied"
                           % len(unresolved_substrate))
    else:
        verdict = "CLEAN_GIVEN_EVIDENCE"
        reasons.append("no flag found in the evidence at hand -- this is NOT an acceptance")

    if low_sensitivity and verdict in ("CLEAN_GIVEN_EVIDENCE", "SOFT_FLAGS"):
        reasons.append("LOW-SENSITIVITY: the fleet caught only %d of %d planted defects; "
                       "a quiet ruling from a fleet that cannot find known defects is not "
                       "evidence of a clean paper" % (caught, planted))
        verdict = "REVIEW_UNAVAILABLE" if caught == 0 else verdict

    if counts["High"] > MAX_HIGH:
        reasons.append("severity inflation guard: %d High findings exceeds the cap of %d; "
                       "downgrade or justify in the ruling" % (counts["High"], MAX_HIGH))

    return {"verdict": verdict,
            "review_independence": "same-family",
            "acceptance_status": "provisional",
            "counts": counts,
            "delivered": len(delivered),
            "rejected": len([f for f in findings if f.get("status") == "rejected"]),
            "contested": len([f for f in findings if f.get("status") == "contested"]),
            "unresolved_uncertainty": len(unresolved_substrate),
            "sensitivity": {"planted": planted, "caught": caught,
                            "low_sensitivity": low_sensitivity},
            "reasons": reasons,
            "disclaimer": "CLEAN_GIVEN_EVIDENCE means no flag was found in the evidence at "
                          "hand. It is not a pass, an acceptance, or an acquittal. A "
                          "single-model-family fleet cannot acquit its own work."}


def selftest():
    t = SelfTest("verdict")
    f1 = {"id": "F-001", "finding_class": "numeric-mismatch", "severity": "Medium",
          "locator": {"sentence_range": [10, 11]}, "emitted_by": "stat"}
    f2 = {"id": "F-002", "finding_class": "numeric-mismatch", "severity": "High",
          "locator": {"sentence_range": [11, 12]}, "emitted_by": "saboteur"}
    f3 = {"id": "F-003", "finding_class": "scope-overclaim", "severity": "Low",
          "locator": {"sentence_range": [10, 11]}, "emitted_by": "scope"}
    m = dedup([f1, f2, f3])
    t.check("overlapping same-class merged", len(m), 2)
    t.check("higher severity wins", m[0]["severity"], "High")
    t.check("corroboration accumulates", sorted(m[0]["corroborated_by"]), ["saboteur", "stat"])
    t.check("different class not merged", m[1]["finding_class"], "scope-overclaim")
    t.check("majority upheld", majority(["upheld", "upheld", "rejected"]), "upheld")
    t.check("tie goes to rejected", majority(["upheld", "rejected"]), "rejected")
    t.check("cant-tell fails closed", majority(["cant-tell", "cant-tell"]), "unresolved")
    t.check("revision majority", majority(["upheld-with-revision", "upheld-with-revision", "upheld"]),
            "upheld-with-revision")
    judged = apply_panel([dict(f1)], [{"finding_id": "F-001", "angle": "logic", "verdict": "upheld"},
                                      {"finding_id": "F-001", "angle": "steelman", "verdict": "rejected"}])
    t.check("any rejecting angle kills", judged[0]["status"], "rejected")
    t.check("kill reason recorded", "steelman" in judged[0]["reject_reason"], True)
    uncovered = apply_panel([dict(f1)], [])
    t.check("uncovered finding fails closed", uncovered[0]["status"], "rejected")
    down = apply_panel([dict(f2)], [{"finding_id": "F-002", "angle": "sev", "verdict": "upheld",
                                     "severity_revision": "Low"}])
    t.check("panel may lower severity", down[0]["severity"], "Low")
    up = apply_panel([dict(f1)], [{"finding_id": "F-001", "angle": "sev", "verdict": "upheld",
                                   "severity_revision": "High"}])
    t.check("panel may not raise severity", up[0]["severity"], "Medium")
    t.check("upward argument recorded as a note", bool(up[0].get("panel_notes")), True)
    r = rule({"blocking": []}, [{"status": "delivered", "severity": "High"}])
    t.check("high -> HARD_FLAGS", r["verdict"], "HARD_FLAGS")
    t.check("never acquits", r["acceptance_status"], "provisional")
    t.check("clean is not a pass", rule({"blocking": []}, [])["verdict"], "CLEAN_GIVEN_EVIDENCE")
    t.check("docket can block alone",
            rule({"blocking": ["numeric_claims_present_no_raw_evidence"]}, [])["verdict"], "BLOCKED")
    t.check("gate crash is ERROR not pass",
            rule({"blocking": ["gate_internal_error:ValueError"]}, [])["verdict"], "ERROR")
    t.check("blind fleet cannot deliver a clean ruling",
            rule({"blocking": []}, [], None, {"planted": 5, "caught": 0})["verdict"], "REVIEW_UNAVAILABLE")
    t.check("weak fleet flagged",
            rule({"blocking": []}, [], None, {"planted": 5, "caught": 2})["sensitivity"]["low_sensitivity"],
            True)
    t.check("unanswered attack point forces HARD_FLAGS",
            rule({"blocking": []}, [], {"still_unresolved": 1})["verdict"], "HARD_FLAGS")
    t.finish()


def _write(path, obj):
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dedup"); d.add_argument("--findings", required=True); d.add_argument("--out")
    pa = sub.add_parser("panel"); pa.add_argument("--findings", required=True)
    pa.add_argument("--verdicts", required=True); pa.add_argument("--out")
    ru = sub.add_parser("rule"); ru.add_argument("--docket", required=True)
    ru.add_argument("--findings", required=True); ru.add_argument("--adjudication")
    ru.add_argument("--sensitivity"); ru.add_argument("--out")
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "selftest":
            selftest()
        elif a.cmd == "dedup":
            fs = load_json(a.findings)
            fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
            m = dedup(fs)
            _write(a.out, m)
            emit({"tool": "verdict.dedup", "tool_sha": tool_sha(), "in": len(fs),
                  "out": len(m), "findings": m}, 0)
        elif a.cmd == "panel":
            fs = load_json(a.findings)
            fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
            vs = load_json(a.verdicts)
            vs = vs.get("verdicts", vs) if isinstance(vs, dict) else vs
            j = apply_panel(fs, vs)
            _write(a.out, j)
            emit({"tool": "verdict.panel", "tool_sha": tool_sha(),
                  "delivered": sum(1 for x in j if x["status"] == "delivered"),
                  "rejected": sum(1 for x in j if x["status"] == "rejected"),
                  "findings": j}, 0)
        elif a.cmd == "rule":
            fs = load_json(a.findings)
            fs = fs.get("findings", fs) if isinstance(fs, dict) else fs
            r = rule(load_json(a.docket), fs,
                     load_json(a.adjudication) if a.adjudication else None,
                     load_json(a.sensitivity) if a.sensitivity else None)
            r.update({"tool": "verdict.rule", "tool_sha": tool_sha()})
            _write(a.out, r)
            emit(r, 0 if r["verdict"] in ("CLEAN_GIVEN_EVIDENCE", "SOFT_FLAGS") else 2)
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
