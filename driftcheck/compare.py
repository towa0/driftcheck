"""Compare each translated article against its source-locale article."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict

from .extract import extract, Extracted

# How much a wrong value hurts a customer who acts on it.
HIGH_IMPACT_UNITS = {"kg", "hour", "minute", "day", "eur", "cm"}

LANG = {"en": "English", "fi": "Finnish", "sv": "Swedish", "de": "German"}


def lang(loc: str) -> str:
    return LANG.get(loc, loc)


def amount(value: str, unit: str) -> str:
    if unit == "eur":
        return f"€{value}"
    word = {"hour": "hours", "minute": "minutes", "day": "days"}.get(unit, unit)
    return f"{value} {word}"


@dataclass
class Finding:
    article: str
    locale: str
    type: str       # value_drift | missing_fact | extra_fact | missing_section | missing_link | broken_link | stale
    severity: str   # high | medium | low
    detail: str

    def to_dict(self):
        return asdict(self)


def _facts_by_unit(ex: Extracted) -> dict[str, Counter]:
    out: dict[str, Counter] = {}
    for f in ex.facts:
        out.setdefault(f.unit, Counter())[f.value] += 1
    return out


def compare_pair(article_id: str, src: dict, tgt: dict, known_paths: set[str]) -> list[Finding]:
    loc = tgt["locale"]
    S, T = lang(src["locale"]), lang(loc)
    s, t = extract(src["body"], src["locale"]), extract(tgt["body"], loc)
    out: list[Finding] = []
    add = lambda typ, sev, d: out.append(Finding(article_id, loc, typ, sev, d))

    # multisets, so a value stated twice in the source must appear twice in the translation
    sf, tf = _facts_by_unit(s), _facts_by_unit(t)
    for unit in sorted(set(sf) | set(tf)):
        sc, tc = sf.get(unit, Counter()), tf.get(unit, Counter())
        only_src = sorted((sc - tc).elements())
        only_tgt = sorted((tc - sc).elements())
        sev = "high" if unit in HIGH_IMPACT_UNITS else "medium"
        paired = min(len(only_src), len(only_tgt))
        for a, b in zip(only_src[:paired], only_tgt[:paired]):
            add("value_drift", sev, f"{S} says {amount(a, unit)}, {T} says {amount(b, unit)}")
        for a in only_src[paired:]:
            add("missing_fact", sev, f"{S} says {amount(a, unit)}; the {T} page has no matching number")
        for b in only_tgt[paired:]:
            add("extra_fact", "medium", f"{T} says {amount(b, unit)}; {S} doesn't")

    if len(t.sections) < len(s.sections):
        add("missing_section", "medium",
            f"{S} page has {len(s.sections)} sections, {T} has {len(t.sections)}")

    sl, tl = Counter(s.links), Counter(t.links)
    for path in sorted((sl - tl).elements()):
        add("missing_link", "medium", f"{S} page links to {path.replace('{loc}', loc)}; {T} page doesn't")
    for path in sorted(set(t.links)):
        if path.startswith("/{loc}/") and path not in known_paths:
            add("broken_link", "high", f"Links to {path.replace('{loc}', loc)}, a page that doesn't exist")

    if tgt["updated"] < src["updated"]:
        add("stale", "low", f"{T} last updated {tgt['updated']}; {S} changed on {src['updated']}")
    return out


def check_corpus(corpus: dict) -> list[Finding]:
    src_loc = corpus["source_locale"]
    known = set(corpus["known_paths"])
    by_id: dict[str, dict[str, dict]] = {}
    for a in corpus["articles"]:
        by_id.setdefault(a["id"], {})[a["locale"]] = a
    findings: list[Finding] = []
    for aid, locs in by_id.items():
        src = locs.get(src_loc)
        if not src:
            continue
        for loc, art in sorted(locs.items()):
            if loc != src_loc:
                findings.extend(compare_pair(aid, src, art, known))
    return findings


def baseline_check(corpus: dict) -> list[Finding]:
    """The simple 'translation older than source' check, used as the baseline."""
    src_loc = corpus["source_locale"]
    src = {a["id"]: a for a in corpus["articles"] if a["locale"] == src_loc}
    return [
        Finding(a["id"], a["locale"], "stale", "low", "older than source")
        for a in corpus["articles"]
        if a["locale"] != src_loc and a["id"] in src and a["updated"] < src[a["id"]]["updated"]
    ]


def answer_divergence(corpus: dict, questions: list[dict]) -> list[dict]:
    """For each customer question: what would an assistant grounded on each locale answer?"""
    rows = []
    arts = {(a["id"], a["locale"]): a for a in corpus["articles"]}
    locales = sorted({a["locale"] for a in corpus["articles"]}, key=lambda l: (l != corpus["source_locale"], l))
    for q in questions:
        answers = {}
        for loc in locales:
            art = arts.get((q["article"], loc))
            if not art:
                answers[loc] = None
                continue
            ex = extract(art["body"], loc)
            secs = ex.sections
            vals = [f.value for f in secs[q["section"]].facts if f.unit == q["unit"]] if q["section"] < len(secs) else []
            answers[loc] = ", ".join(vals) if vals else "—"
        distinct = {v for v in answers.values() if v}
        rows.append({"q": q["q"], "unit": q["unit"], "answers": answers, "diverges": len(distinct) > 1})
    return rows


def evaluate(findings: list[Finding], truth: dict) -> dict:
    """Issue-level precision/recall against planted ground truth."""
    planted = {(i["article"], i["locale"], i["type"]) for i in truth.get("issues", [])}
    found = {(f.article, f.locale, f.type) for f in findings}
    tp = found & planted
    return {
        "planted": len(planted),
        "found": len(found),
        "true_positives": len(tp),
        "false_positives": sorted(found - planted),
        "missed": sorted(planted - found),
        "recall": round(len(tp) / len(planted), 2) if planted else 0.0,
        "precision": round(len(tp) / len(found), 2) if found else 0.0,
    }
