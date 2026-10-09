"""Shared primitives for every TRIBUNAL gate.

Normalization lives here and ONLY here. The quote gate and the absence gate must never
drift apart: if they normalize text differently, an absence probe can certify "absent"
for a term the quote gate would have found, and the system silently fabricates a silence.

Exit-code convention across all tools:
    0  ran, found nothing to flag
    2  ran, FOUND something (unmatched quote, present probe term, inconsistency, hit)
    3  could not run (bad args, missing file, internal error)  -> callers treat as BLOCKING

Exit 2 is EXPECTED OUTPUT, not an error. Never retry on 2. Never fail open on 3.
"""

import hashlib
import json
import os
import re
import sys
import unicodedata

SCHEMA_VERSION = "tribunal@1"

# ---------------------------------------------------------------- normalization

_SMART_QUOTES = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "«": '"', "»": '"', "‹": "'", "›": "'",
}
_DASHES = {
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "―": "-", "−": "-", "－": "-",
}
_SPACES = {
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ",
    " ": " ", " ": " ", " ": " ", " ": " ", " ": " ",
    " ": " ", " ": " ", " ": " ", " ": " ", "　": " ",
    "\t": " ", "\r": " ", "\n": " ", "\v": " ", "\f": " ",
}
# zero-width and soft hyphen: deleted outright, they are PDF extraction litter
_DELETE = ["​", "‌", "‍", "﻿", "­", "⁠"]

_WS_RUN = re.compile(r" {2,}")


def normalize(text, casefold=True):
    """NFKC + quote/dash/space canonicalization + zero-width deletion + whitespace collapse."""
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", str(text))
    for ch in _DELETE:
        t = t.replace(ch, "")
    for src, dst in _SMART_QUOTES.items():
        t = t.replace(src, dst)
    for src, dst in _DASHES.items():
        t = t.replace(src, dst)
    for src, dst in _SPACES.items():
        t = t.replace(src, dst)
    t = _WS_RUN.sub(" ", t).strip()
    return t.casefold() if casefold else t


_HYPHEN_BREAK = re.compile(r"([A-Za-z])- ?([A-Za-z])")


def dehyphenate(text):
    """Rejoin a word split by a hyphen at a (former) PDF line break.

    Deliberately does NOT join a numeric range such as '5- 10': joining it would fabricate
    '510' and let a bogus quote match. The pattern requires letters on both sides.
    """
    prev = None
    out = text
    while out != prev:                       # 'multi- part- word' needs repeated passes
        prev = out
        out = _HYPHEN_BREAK.sub(r"\1\2", out)
    return out


def hyphenless(text):
    """Strip hyphens entirely. Used ONLY by the absence gate, whose match ladder is
    deliberately looser (a missed match there would fail OPEN into a false silence)."""
    return text.replace("-", "")


# ---------------------------------------------------------------- numeric tokens

# Boundary policy: ALLOW-LIST, fail closed. A numeric token counts as a match only when
# flanked by known-safe boundaries. ANY other adjacency -- a digit, a unicode minus, ':',
# '/', a locale grouping separator, an apostrophe (Swiss thousands separator: 1'000) --
# is not safe, so the token fails closed and a human reads the file.
# A false negative is cheap. A false 'verified' is the bug this must never have.
SAFE_BOUNDARY = set(" \t\n\r()[]{}<>,;\"'`|=+*&^$#@!?~" + "“”")
SAFE_BOUNDARY.discard("'")                   # apostrophe is NOT safe: 1'000
SAFE_BOUNDARY_END = SAFE_BOUNDARY | {".", "%"}   # trailing sentence period / percent sign


def _safe_left(s, i):
    return i == 0 or s[i - 1] in SAFE_BOUNDARY


def _safe_right(s, j):
    if j >= len(s):
        return True
    ch = s[j]
    if ch in SAFE_BOUNDARY_END:
        # a trailing '.' is safe only if not followed by a digit ('0.083' vs '0.08.')
        if ch == "." and j + 1 < len(s) and s[j + 1].isdigit():
            return False
        return True
    return False


def find_numeric_token(value, source):
    """True iff `value` occurs in `source` as a standalone numeric literal.

    '0.08' must NOT match inside '0.083'. '73.2' matches '73.20' only via the caller's
    decimal comparison, never via substring.
    """
    v = str(value).strip()
    if not v:
        return False
    start = 0
    while True:
        i = source.find(v, start)
        if i < 0:
            return False
        if _safe_left(source, i) and _safe_right(source, i + len(v)):
            return True
        start = i + 1


def decimal_equal(a, b):
    """Numeric-token equality: 73.2 == 73.20, 73 != 73.5. Returns None if unparseable."""
    from decimal import Decimal, InvalidOperation
    try:
        da, db = Decimal(str(a).strip().rstrip("%")), Decimal(str(b).strip().rstrip("%"))
    except (InvalidOperation, ValueError):
        return None
    return da == db


def rounds_to(raw, displayed):
    """True iff `displayed` is standard rounding of `raw` to displayed precision.

    84.7 -> 84.7 or 85 is legal. 84.7 -> 85.3 is NOT a rounding, it is a mismatch.
    """
    from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
    try:
        r = Decimal(str(raw).strip().rstrip("%"))
        d = Decimal(str(displayed).strip().rstrip("%"))
    except (InvalidOperation, ValueError):
        return None
    exp = d.as_tuple().exponent
    if not isinstance(exp, int):
        return None
    quant = Decimal(1).scaleb(exp)
    return r.quantize(quant, rounding=ROUND_HALF_UP) == d


# ---------------------------------------------------------------- io / provenance

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def sha256_text(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def emit(obj, exit_code=0):
    """Print a JSON result and exit. Never print anything else to stdout: the caller
    relays this verbatim and a stray line corrupts the audit record."""
    obj.setdefault("schema", SCHEMA_VERSION)
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    sys.exit(exit_code)


def die(msg, code=3):
    """Could-not-run. Callers MUST treat this as blocking, never as a pass."""
    sys.stdout.write(json.dumps({"schema": SCHEMA_VERSION, "error": msg,
                                 "status": "could-not-run"}, indent=2) + "\n")
    sys.exit(code)


def tool_sha(path=None):
    p = path or sys.argv[0]
    try:
        return sha256_file(p)[:19]
    except OSError:
        return "sha256:unknown"


# ---------------------------------------------------------------- selftest harness

class SelfTest:
    def __init__(self, name):
        self.name, self.failures, self.count = name, [], 0

    def check(self, label, got, want):
        self.count += 1
        if got != want:
            self.failures.append("%s: got %r, want %r" % (label, got, want))

    def finish(self):
        if self.failures:
            print("FAIL %s (%d/%d)" % (self.name, len(self.failures), self.count))
            for f in self.failures:
                print("   x " + f)
            sys.exit(1)
        print("ok   %s (%d checks)" % (self.name, self.count))
        sys.exit(0)


def selftest_common():
    t = SelfTest("_common")
    t.check("smart quotes fold", normalize("“Hi”"), '"hi"')
    t.check("em dash folds", normalize("a—b"), "a-b")
    t.check("nbsp folds", normalize("a b"), "a b")
    t.check("zero width deleted", normalize("a​b"), "ab")
    t.check("whitespace collapsed", normalize("a   \n b"), "a b")
    t.check("dehyphenate joins word", dehyphenate("multi- part"), "multipart")
    t.check("numeric range NOT joined", dehyphenate("5- 10"), "5- 10")
    t.check("0.08 not inside 0.083", find_numeric_token("0.08", "value 0.083 here"), False)
    t.check("0.08 found standalone", find_numeric_token("0.08", "value 0.08 here"), True)
    t.check("trailing period ok", find_numeric_token("85.3", "was 85.3."), True)
    t.check("apostrophe unsafe", find_numeric_token("000", "1'000"), False)
    t.check("percent boundary ok", find_numeric_token("85.3", "at 85.3% overall"), True)
    t.check("73.2 == 73.20", decimal_equal("73.2", "73.20"), True)
    t.check("73 != 73.5", decimal_equal("73", "73.5"), False)
    t.check("unparseable -> None", decimal_equal("abc", "1"), None)
    t.check("84.7 rounds to 85", rounds_to("84.7", "85"), True)
    t.check("84.7 does NOT round to 85.3", rounds_to("84.7", "85.3"), False)
    t.check("85.28 rounds to 85.3", rounds_to("85.28", "85.3"), True)
    t.finish()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest_common()
    die("_common.py is a library; run `python3 _common.py selftest`")
