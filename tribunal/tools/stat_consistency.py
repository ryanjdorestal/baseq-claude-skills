#!/usr/bin/env python3
"""stat_consistency.py — arithmetic that a paper cannot argue with. Pure stdlib.

Checks a reported statistic against itself. No model opinion is involved and none is
accepted: either the numbers can coexist or they cannot.

    GRIM              can mean M arise from N integer responses at d decimals?
    GRIMMER           can SD coexist with that mean and N? (first-order sum-of-squares)
    sd-range          is SD possible given a bounded scale and the reported mean?
    percent-vs-n      can p% arise from N cases?
    delta-recompute   does the claimed improvement match the two numbers it is computed from?
    p-value-recompute does the reported p match the reported test statistic and df?
    rounding-legality is the displayed value a legal rounding of the raw value?

`insufficient_data` is a first-class outcome and is reported as a MISSING-REPORTING fact,
never as an inconsistency. A paper that does not report N cannot be convicted of GRIM.

Usage:
    stat_consistency.py grim        --mean 3.42 --n 25 [--decimals auto] [--items 1]
    stat_consistency.py grimmer     --mean 3.42 --sd 1.11 --n 25
    stat_consistency.py sd-range    --mean 3.42 --sd 2.9 --n 25 --min 1 --max 5
    stat_consistency.py percent     --percent 37.5 --n 25
    stat_consistency.py delta       --before 75.6 --after 85.3 --claimed 15 [--kind relative]
    stat_consistency.py pvalue      --test t --stat 2.13 --df 48 --reported 0.03
    stat_consistency.py batch       --checks checks.json
    stat_consistency.py selftest

Exit 0 = all consistent. Exit 2 = at least one inconsistent (EXPECTED). Exit 3 = could not run.
"""
import argparse
import math
import sys
from decimal import Decimal

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from _common import SelfTest, die, emit, load_json, rounds_to, tool_sha  # noqa: E402


# ------------------------------------------------------------------ distributions

def _betacf(a, b, x, itmax=300, eps=3e-12):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d, h = 1.0 / d, 1.0 / d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta I_x(a,b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log1p(-x))
    front = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                          + b * math.log1p(-x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def gammainc_upper(s, x, itmax=500, eps=1e-12):
    """Regularized upper incomplete gamma Q(s,x)."""
    if x < 0 or s <= 0:
        return float("nan")
    if x == 0:
        return 1.0
    if x < s + 1.0:                                   # series for P, then complement
        ap, total, term = s, 1.0 / s, 1.0 / s
        for _ in range(itmax):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * eps:
                break
        return 1.0 - total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    b, c, d = x + 1.0 - s, 1e300, 1.0 / (x + 1.0 - s)
    h = d
    for i in range(1, itmax + 1):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return math.exp(-x + s * math.log(x) - math.lgamma(s)) * h


def p_from_t(t, df):
    return betainc(df / 2.0, 0.5, df / (df + t * t))            # two-tailed


def p_from_f(f, df1, df2):
    return betainc(df2 / 2.0, df1 / 2.0, df2 / (df2 + df1 * f))  # upper tail


def p_from_chi2(x, df):
    return gammainc_upper(df / 2.0, x / 2.0)


def p_from_r(r, n):
    if abs(r) >= 1.0 or n <= 2:
        return float("nan")
    return p_from_t(abs(r) * math.sqrt((n - 2) / (1 - r * r)), n - 2)


def p_from_z(z):
    return math.erfc(abs(z) / math.sqrt(2.0))                    # two-tailed


# ------------------------------------------------------------------ checks

def _decimals(value):
    exp = Decimal(str(value)).as_tuple().exponent
    return -exp if isinstance(exp, int) and exp < 0 else 0


def grim(mean, n, decimals=None, items=1):
    """Granularity-Related Inconsistency of Means. n*items must be a modest integer count."""
    if n is None or n <= 0:
        return {"check": "GRIM", "status": "insufficient_data", "detail": "N not reported"}
    d = _decimals(mean) if decimals is None else int(decimals)
    total_obs = int(n) * int(items)
    if total_obs > 10 ** (d + 3):
        return {"check": "GRIM", "status": "not_applicable",
                "detail": "N=%d too large for granularity at %d dp to constrain the mean" % (total_obs, d)}
    q = 10 ** d
    target = round(float(mean) * q)
    # candidate integer sums whose mean rounds to the reported value
    lo = math.floor((target - 0.5) / q * total_obs)
    hi = math.ceil((target + 0.5) / q * total_obs)
    for s in range(lo - 1, hi + 2):
        if s < 0:
            continue
        if round(round(s / total_obs, d) * q) == target:
            return {"check": "GRIM", "status": "consistent", "witness_sum": s,
                    "detail": "sum %d over %d observations yields %s" % (s, total_obs, mean)}
    near = sorted({round(s / total_obs, d) for s in range(max(0, lo - 2), hi + 3)})
    cand = [x for x in near if abs(x - float(mean)) < 2.0 / q][:4]
    return {"check": "GRIM", "status": "inconsistent",
            "detail": "no integer sum over %d observations yields mean %s at %d dp; nearest are %s"
                      % (total_obs, mean, d, cand)}


def grimmer(mean, sd, n):
    """First-order GRIMMER: the implied sum of squares must be reachable by integers.

    Honest scope: this is the sum-of-squares reachability test, not the full GRIMMER
    variance-granularity proof. It catches gross impossibility, not every violation.
    """
    if not n or n < 2:
        return {"check": "GRIMMER", "status": "insufficient_data", "detail": "N missing or < 2"}
    dm, ds = _decimals(mean), _decimals(sd)
    lo_m, hi_m = float(mean) - 0.5 / 10 ** dm, float(mean) + 0.5 / 10 ** dm
    lo_s, hi_s = max(0.0, float(sd) - 0.5 / 10 ** ds), float(sd) + 0.5 / 10 ** ds
    lo_ss = (n - 1) * lo_s ** 2 + n * lo_m ** 2
    hi_ss = (n - 1) * hi_s ** 2 + n * hi_m ** 2
    if math.floor(hi_ss) >= math.ceil(lo_ss):
        return {"check": "GRIMMER", "status": "consistent",
                "detail": "implied sum of squares interval [%.4f, %.4f] contains an integer" % (lo_ss, hi_ss)}
    return {"check": "GRIMMER", "status": "inconsistent",
            "detail": "implied sum of squares interval [%.4f, %.4f] contains no integer; "
                      "mean %s and SD %s cannot both be right at N=%d" % (lo_ss, hi_ss, mean, sd, n)}


def sd_range(mean, sd, n, lo, hi):
    """On a bounded scale the SD cannot exceed sqrt((hi-M)(M-lo)) * sqrt(n/(n-1))."""
    if None in (mean, sd, n, lo, hi) or n < 2:
        return {"check": "sd-range", "status": "insufficient_data",
                "detail": "need mean, sd, N>=2 and scale bounds"}
    if not (lo <= mean <= hi):
        return {"check": "sd-range", "status": "inconsistent",
                "detail": "mean %s lies outside the reported scale [%s, %s]" % (mean, lo, hi)}
    cap = math.sqrt((hi - mean) * (mean - lo)) * math.sqrt(n / (n - 1.0))
    if sd <= cap + 1e-9:
        return {"check": "sd-range", "status": "consistent",
                "detail": "SD %.4f <= maximum possible %.4f" % (sd, cap)}
    return {"check": "sd-range", "status": "inconsistent",
            "detail": "SD %.4f exceeds the maximum possible %.4f for mean %s on [%s, %s] at N=%d"
                      % (sd, cap, mean, lo, hi, n)}


def percent_vs_n(percent, n, decimals=None):
    if not n or n <= 0:
        return {"check": "percent-vs-n", "status": "insufficient_data", "detail": "N not reported"}
    d = _decimals(percent) if decimals is None else int(decimals)
    for k in range(0, int(n) + 1):
        if round(100.0 * k / n, d) == round(float(percent), d):
            return {"check": "percent-vs-n", "status": "consistent", "witness_count": k,
                    "detail": "%d of %d = %s%%" % (k, n, percent)}
    return {"check": "percent-vs-n", "status": "inconsistent",
            "detail": "no whole number of cases out of %d yields %s%% at %d dp" % (n, percent, d)}


def delta(before, after, claimed, kind="relative", tolerance=0.05):
    if before in (None, 0) or after is None or claimed is None:
        return {"check": "delta-recompute", "status": "insufficient_data",
                "detail": "need before, after and the claimed delta"}
    rel = (after - before) / abs(before) * 100.0
    absolute = after - before
    got = rel if kind == "relative" else absolute
    if abs(got - claimed) <= tolerance:
        return {"check": "delta-recompute", "status": "consistent",
                "recomputed": round(got, 4), "kind": kind}
    other = absolute if kind == "relative" else rel
    hint = ""
    if abs(other - claimed) <= tolerance:
        hint = (" -- but it DOES match the %s difference; the paper is likely mislabelling "
                "percentage points as percent" % ("absolute" if kind == "relative" else "relative"))
    return {"check": "delta-recompute", "status": "inconsistent",
            "recomputed": round(got, 4), "claimed": claimed, "kind": kind,
            "detail": "%s change from %s to %s is %.4f, not %s%s" % (kind, before, after, got, claimed, hint)}


def pvalue(test, stat, reported, df=None, df2=None, n=None, tolerance_factor=2.0):
    test = (test or "").lower()
    try:
        if test == "t":
            p = p_from_t(abs(float(stat)), float(df))
        elif test == "f":
            p = p_from_f(float(stat), float(df), float(df2))
        elif test in ("chi2", "chisq", "x2"):
            p = p_from_chi2(float(stat), float(df))
        elif test == "r":
            p = p_from_r(float(stat), int(n))
        elif test == "z":
            p = p_from_z(float(stat))
        else:
            return {"check": "p-value-recompute", "status": "not_applicable",
                    "detail": "unsupported test '%s' (t|F|chi2|r|z)" % test}
    except (TypeError, ValueError):
        return {"check": "p-value-recompute", "status": "insufficient_data",
                "detail": "missing df / n for a %s test" % test}
    if p != p:                                                    # NaN
        return {"check": "p-value-recompute", "status": "insufficient_data",
                "detail": "statistic out of domain"}
    d = _decimals(reported)
    band = 0.5 / 10 ** d * tolerance_factor if d else 0.005 * tolerance_factor
    ok = abs(p - float(reported)) <= max(band, p * 0.02)
    row = {"check": "p-value-recompute", "recomputed_p": round(p, 6), "reported_p": reported,
           "status": "consistent" if ok else "inconsistent"}
    if not ok:
        crosses = (p > 0.05) != (float(reported) > 0.05)
        row["detail"] = ("%s(%s)=%s implies p=%.5g, paper reports %s%s"
                         % (test, df if df is not None else n, stat, p, reported,
                            "  -- AND THE DISCREPANCY CROSSES 0.05" if crosses else ""))
        row["crosses_significance_threshold"] = crosses
    return row


CHECKS = {"grim": lambda a: grim(a["mean"], a.get("n"), a.get("decimals"), a.get("items", 1)),
          "grimmer": lambda a: grimmer(a["mean"], a["sd"], a.get("n")),
          "sd-range": lambda a: sd_range(a["mean"], a["sd"], a.get("n"), a.get("min"), a.get("max")),
          "percent": lambda a: percent_vs_n(a["percent"], a.get("n"), a.get("decimals")),
          # NB: in batch mode `kind` names the CHECK, so the relative/absolute selector is
          # read from `delta_kind`. Reusing `kind` here silently computed absolute deltas.
          "delta": lambda a: delta(a["before"], a["after"], a["claimed"],
                                   a.get("delta_kind", a.get("kind") if a.get("kind") in
                                         ("relative", "absolute") else "relative")),
          "pvalue": lambda a: pvalue(a.get("test"), a.get("stat"), a.get("reported"),
                                     a.get("df"), a.get("df2"), a.get("n")),
          "rounding": lambda a: {"check": "rounding-legality",
                                 "status": "consistent" if rounds_to(a["raw"], a["displayed"])
                                 else "inconsistent",
                                 "detail": "%s -> %s" % (a["raw"], a["displayed"])}}


def cmd_batch(args):
    checks = load_json(args.checks)
    if isinstance(checks, dict):
        checks = checks.get("checks", [])
    rows, bad = [], 0
    for c in checks:
        kind = c.get("kind", "")
        fn = CHECKS.get(kind)
        if not fn:
            rows.append({"id": c.get("id", "?"), "check": kind, "status": "not_applicable",
                         "detail": "unknown check kind"})
            continue
        try:
            r = fn(c)
        except KeyError as e:
            r = {"check": kind, "status": "insufficient_data", "detail": "missing field %s" % e}
        r["id"] = c.get("id", "?")
        if r["status"] == "inconsistent":
            bad += 1
        rows.append(r)
    emit({"tool": "stat_consistency", "tool_sha": tool_sha(), "total": len(rows),
          "inconsistent": bad, "results": rows}, 0 if bad == 0 else 2)


def selftest():
    t = SelfTest("stat_consistency")
    t.check("GRIM catches impossible mean", grim(3.42, 25)["status"], "inconsistent")
    t.check("GRIM accepts possible mean", grim(3.44, 25)["status"], "consistent")
    t.check("GRIM without N is insufficient, not guilty", grim(3.42, None)["status"], "insufficient_data")
    t.check("GRIMMER accepts a real pair", grimmer(3.0, 1.0, 10)["status"], "consistent")
    t.check("sd-range catches impossible SD", sd_range(4.8, 2.5, 30, 1, 5)["status"], "inconsistent")
    t.check("sd-range accepts plausible SD", sd_range(3.0, 1.0, 30, 1, 5)["status"], "consistent")
    t.check("mean outside scale caught", sd_range(6.0, 1.0, 30, 1, 5)["status"], "inconsistent")
    t.check("percent impossible for N", percent_vs_n(37.5, 25)["status"], "inconsistent")
    t.check("percent possible for N", percent_vs_n(36.0, 25)["status"], "consistent")
    t.check("delta caught", delta(75.6, 85.3, 15)["status"], "inconsistent")
    t.check("delta recomputed", round(delta(75.6, 85.3, 15)["recomputed"], 1), 12.8)
    t.check("delta ok", delta(75.6, 85.3, 12.83)["status"], "consistent")
    t.check("absolute-vs-relative hint", "percentage points" in (delta(50.0, 60.0, 10)["detail"]), True)
    t.check("t p-value ok", pvalue("t", 2.131, 0.05, df=15)["status"], "consistent")
    t.check("t p-value caught", pvalue("t", 1.2, 0.03, df=15)["status"], "inconsistent")
    t.check("significance crossing flagged",
            pvalue("t", 1.2, 0.03, df=15)["crosses_significance_threshold"], True)
    t.check("chi2 sane", abs(p_from_chi2(3.84, 1) - 0.05) < 0.002, True)
    t.check("F sane", abs(p_from_f(4.35, 1, 20) - 0.05) < 0.01, True)
    t.check("z sane", abs(p_from_z(1.96) - 0.05) < 0.001, True)
    t.check("r routes through t", pvalue("r", 0.5, 0.049, n=16)["status"], "consistent")
    t.check("unsupported test not guilty", pvalue("wilcoxon", 1, 0.05)["status"], "not_applicable")
    t.finish()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd")
    g = sub.add_parser("grim"); g.add_argument("--mean", type=float, required=True)
    g.add_argument("--n", type=int, required=True); g.add_argument("--decimals", type=int)
    g.add_argument("--items", type=int, default=1)
    gm = sub.add_parser("grimmer"); gm.add_argument("--mean", type=float, required=True)
    gm.add_argument("--sd", type=float, required=True); gm.add_argument("--n", type=int, required=True)
    sr = sub.add_parser("sd-range")
    for f in ("mean", "sd", "min", "max"):
        sr.add_argument("--" + f, type=float, required=True)
    sr.add_argument("--n", type=int, required=True)
    pc = sub.add_parser("percent"); pc.add_argument("--percent", type=float, required=True)
    pc.add_argument("--n", type=int, required=True); pc.add_argument("--decimals", type=int)
    dl = sub.add_parser("delta")
    for f in ("before", "after", "claimed"):
        dl.add_argument("--" + f, type=float, required=True)
    dl.add_argument("--kind", default="relative", choices=["relative", "absolute"])
    pv = sub.add_parser("pvalue"); pv.add_argument("--test", required=True)
    pv.add_argument("--stat", type=float, required=True); pv.add_argument("--reported", type=float, required=True)
    pv.add_argument("--df", type=float); pv.add_argument("--df2", type=float); pv.add_argument("--n", type=int)
    b = sub.add_parser("batch"); b.add_argument("--checks", required=True)
    sub.add_parser("selftest")
    a = p.parse_args()
    try:
        if a.cmd == "selftest":
            selftest()
        elif a.cmd == "batch":
            cmd_batch(a)
        elif a.cmd in CHECKS:
            r = CHECKS[a.cmd](vars(a))
            r.update({"tool": "stat_consistency", "tool_sha": tool_sha()})
            emit(r, 0 if r["status"] != "inconsistent" else 2)
        else:
            p.print_help(); sys.exit(3)
    except SystemExit:
        raise
    except Exception as e:
        die("internal_error:%s:%s" % (type(e).__name__, e))


if __name__ == "__main__":
    main()
