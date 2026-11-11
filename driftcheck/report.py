"""Plain-language HTML report. No JS, no external files, readable on a phone."""
from __future__ import annotations

import html

from .compare import lang, amount

SEV_ORDER = {"high": 0, "medium": 1, "low": 2}
TYPE_LABEL = {
    "value_drift": "Different number",
    "missing_fact": "Number missing",
    "extra_fact": "Extra number",
    "missing_section": "Section missing",
    "missing_link": "Link missing",
    "broken_link": "Link to a page that doesn't exist",
    "stale": "Not updated since the English page changed",
}

CSS = """
*{box-sizing:border-box}
body{font:16px/1.55 system-ui,-apple-system,sans-serif;margin:0 auto;max-width:760px;padding:1.25rem;color:#111;background:#fff}
h1{font-size:1.35rem;line-height:1.3;margin:0 0 .75rem}
h2{font-size:1.05rem;margin:1.75rem 0 .4rem}
p,ul{margin:.4rem 0}
ul{padding-left:1.2rem}
.note{color:#555;font-size:.9rem}
.wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;padding:.45rem .5rem;border-bottom:1px solid #e3e3e3;vertical-align:top}
th{background:#f6f6f6;font-weight:600}
tr.diff td{background:#fff3f3}
.high{color:#a4001c;font-weight:600}.medium{color:#8a4b00}.low{color:#555}
.wrong{color:#555;font-style:italic}
@media (max-width:600px){
 table,tbody,tr,td{display:block;width:100%}
 tr:first-child{display:none}
 tr{border:1px solid #e3e3e3;border-radius:6px;margin:.6rem 0;padding:.3rem .5rem}
 td{border:0;padding:.2rem 0}
 td[data-l]::before{content:attr(data-l) ": ";font-weight:600;color:#333}
 td.q{font-weight:600}
}
"""


def _e(x) -> str:
    return html.escape(str(x))


def _ans(v, unit: str) -> str:
    if v in (None, "—"):
        return "no number"
    return ", ".join(amount(x, unit) for x in v.split(", "))


def render(findings, divergence, titles: dict[str, str], known_non_issues: list[dict],
           ev_tool: dict, ev_base: dict, issues: list[dict], corpus: dict) -> str:
    n_pages = len({a["id"] for a in corpus["articles"]})
    names = [lang(l) for l in dict.fromkeys(a["locale"] for a in corpus["articles"])]
    langs = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else "".join(names)
    wrong = {(n["article"], n["locale"]): n["what"] for n in known_non_issues}
    locs = list(divergence[0]["answers"].keys()) if divergence else []

    uncatchable = {(i["article"], i["locale"], i["type"]) for i in issues if not i.get("detectable", True)}
    missed = [tuple(m) for m in ev_tool["missed"]]
    miss_note = (" The one it missed I planted so number checks couldn't catch it."
                 if len(missed) == 1 and missed[0] in uncatchable else "")
    result = (
        f"<p>I wrote the same {n_pages} help pages in {langs}, and put {ev_tool['planted']} mistakes in them on purpose. "
        "I wrote both the mistakes and the tool, so this only shows the tool works as designed. It says nothing about real help pages. "
        f"The tool caught {ev_tool['true_positives']} of {ev_tool['planted']}.{miss_note} "
        f"It flagged {ev_tool['found']} things, and {ev_tool['true_positives']} of those were real. "
        f"The simple check, “is the translation older than the English page?”, caught {ev_base['true_positives']} of {ev_base['planted']}.</p>"
        if ev_tool["planted"] else "<p>No planted mistakes to compare against.</p>"
    )

    qrows = "".join(
        f"<tr class='{'diff' if d['diverges'] else ''}'><td class='q'>{_e(d['q'])}</td>"
        + "".join(f"<td data-l='{_e(lang(l))}'>{_e(_ans(d['answers'][l], d['unit']))}</td>" for l in locs)
        + "</tr>"
        for d in divergence
    )
    frows = "".join(
        f"<tr><td data-l='How much it matters' class='{f.severity}'>{f.severity}</td><td data-l='Page'>{_e(titles.get(f.article, f.article))}</td>"
        f"<td data-l='Language'>{_e(lang(f.locale))}</td><td data-l='Problem'>{_e(TYPE_LABEL.get(f.type, f.type))}</td><td data-l='Details'>{_e(f.detail)}"
        + (f"<br><span class='wrong'>This flag is wrong. {_e(wrong[(f.article, f.locale)])}</span>"
           if (f.article, f.locale) in wrong and f.type == "missing_fact" else "")
        + "</td></tr>"
        for f in sorted(findings, key=lambda f: (SEV_ORDER[f.severity], f.article, f.locale))
    )

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Same question, different number by language</title><style>{CSS}</style></head><body>

<h1>If the English and Swedish help pages disagree, a chatbot that reads both could give two different answers.</h1>
<p class="note">Everything below uses help pages I wrote myself for a made-up airline. No Finnair content or data.</p>

<h2>What the tool does</h2>
<ul>
<li>Compares each translated help page with the English one.</li>
<li>Points out where they disagree: a different number, a missing section, a missing or dead link, or a page that wasn't updated after the English one changed.</li>
<li>Shows where the pages give different numbers for the same customer question.</li>
</ul>

<h2>What I found, on a test set I wrote myself</h2>
{result}

<h2>Limits</h2>
<ul>
<li>It misses changes in meaning. My Swedish refunds page says non-refundable tickets <i>can</i> be refunded, the opposite of the English. No number changed, so the tool didn't notice.</li>
<li>It can flag correct pages. My Finnish page says “three weeks” in words where the English says “21 days”. That's correct, but the tool only looks for numbers, so it reported a missing deadline. I wrote that page that way on purpose, to see how the tool handles numbers written as words.</li>
</ul>

<h2>An open question</h2>
<p>If you run a help centre in more than one language: do the versions ever disagree like this? Or does your translation setup already stop it?</p>

<h2>Same question, different number</h2>
<p class="note">The number each language's page gives as the answer. Shaded rows differ between languages.</p>
<div class="wrap"><table><tr><th>Question</th>{''.join(f'<th>{_e(lang(l))}</th>' for l in locs)}</tr>{qrows}</table></div>

<h2>Everything the tool flagged</h2>
<div class="wrap"><table><tr><th>How much it matters</th><th>Page</th><th>Language</th><th>Problem</th><th>Details</th></tr>{frows}</table></div>
</body></html>"""
