"""CLI: python -m driftcheck [--data DIR] [--out DIR] [--fail-on high]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compare import check_corpus, baseline_check, answer_divergence, evaluate
from .report import render


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="driftcheck", description="Find translation drift in help-centre content.")
    p.add_argument("--data", default="data", help="folder with articles.json (+ optional questions.json, planted_issues.json)")
    p.add_argument("--out", default="out")
    p.add_argument("--fail-on", choices=["high", "medium", "low"], help="exit 1 if any finding at/above this severity (for CI)")
    a = p.parse_args(argv)

    data, out = Path(a.data), Path(a.out)
    corpus = json.loads((data / "articles.json").read_text(encoding="utf-8"))
    qpath, tpath = data / "questions.json", data / "planted_issues.json"
    questions = json.loads(qpath.read_text(encoding="utf-8"))["questions"] if qpath.exists() else []
    truth = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else {"issues": []}

    findings = check_corpus(corpus)
    base = baseline_check(corpus)
    ev_tool, ev_base = evaluate(findings, truth), evaluate(base, truth)
    div = answer_divergence(corpus, questions)

    out.mkdir(parents=True, exist_ok=True)
    (out / "findings.json").write_text(json.dumps([f.to_dict() for f in findings], ensure_ascii=False, indent=2), encoding="utf-8")
    titles = {}
    for art in corpus["articles"]:
        if art["locale"] == corpus["source_locale"]:
            first = art["body"].splitlines()[0]
            titles[art["id"]] = first.lstrip("# ").strip()
    (out / "report.html").write_text(render(findings, div, titles, truth.get("known_non_issues", []), ev_tool, ev_base, truth.get("issues", []), corpus), encoding="utf-8")

    print(f"{len(findings)} findings across {len({(f.article, f.locale) for f in findings})} article/locale pairs\n")
    for f in sorted(findings, key=lambda f: ({'high': 0, 'medium': 1, 'low': 2}[f.severity], f.article, f.locale)):
        print(f"  [{f.severity:<6}] {f.article:<16} {f.locale}  {f.type:<15} {f.detail}")
    if div:
        print("\nSame question, different answer by language:")
        for d in div:
            flag = "DIFFERS" if d["diverges"] else "ok     "
            print(f"  {flag} {d['q']:<45} " + "  ".join(f"{k}={v}" for k, v in d["answers"].items()))
    if truth.get("issues", []):
        print(f"\nEval vs planted issues ({ev_tool['planted']}):")
        print(f"  baseline ('older than source'): caught {ev_base['true_positives']} of {ev_base['planted']} planted issues; {ev_base['found']} flagged, {ev_base['true_positives']} real")
        print(f"  driftcheck:                     caught {ev_tool['true_positives']} of {ev_tool['planted']} planted issues; {ev_tool['found']} flagged, {ev_tool['true_positives']} real")
        print(f"  missed: {ev_tool['missed']}")
        print(f"  false positives: {ev_tool['false_positives']}")
    print(f"\nReport: {out / 'report.html'}")

    if a.fail_on:
        rank = {"high": 0, "medium": 1, "low": 2}
        if any(rank[f.severity] <= rank[a.fail_on] for f in findings):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
