# driftcheck

A translated help page can quietly stop saying the same thing as the original.

All data in `data/` is synthetic. I wrote it for a made-up airline and invented the values. Not Finnair content, not scraped, not affiliated. I don't know how Finnair's help pages are actually written or translated.

This finds where pages drift: a different number, a dropped section, a missing or dead link, a translation older than its source. Then, for a list of customer questions, it shows where the pages give different numbers as the answer.

Why bother: an AI support assistant that answers from help pages in many languages can only be as consistent as those pages. If the Swedish page says 7.5 kg and the English one says 8 kg, an assistant reading them could give two answers. Both "grounded".

Why Finnair comes up: their assistant Sisu "draws its answers directly from the latest content on the Finnair website", in 15 languages ([Finnair Blue Wings, Sisu article](https://www.finnair.com/en/bluewings/world-of-finnair/meet-finnair-s-ai-customer-service-assistant--sisu-4261942), published 28 Apr 2026, updated 15 Jun 2026).

## Run

```bash
python3 -m driftcheck                 # writes out/report.html + out/findings.json
python3 -m driftcheck --fail-on high  # exits 1 on high-severity findings, so it can be used as a CI check
python3 -m unittest discover -s tests -t .
```

I ran it with Python 3.10.10 and 3.12.10. Stdlib only. No network, no API keys.

## What it checks

| Check | How |
|---|---|
| Value drift | Numbers + units pulled out of each section (kg, cm, €, hours, minutes, days in en/fi/sv/de forms, decimal commas handled) and compared as multisets vs the source |
| Missing fact | Source states a value the translation doesn't |
| Missing section | Fewer `##` sections than the source |
| Missing / broken link | Internal links normalised across locales (`/fi/x` ≈ `/en/x`) and checked against known pages |
| Stale | Translation `updated` older than source. The simple check, and the baseline I compare against |
| Answer divergence | For a list of customer questions I wrote, reads the answer value from each locale's page |

## Result, on a test set I wrote myself

5 articles in 4 languages, 11 problems I planted. I wrote both the problems and the tool, so this only shows it works as designed. It says nothing about real content.

| | Planted problems found | Flags that were real problems |
|---|---|---|
| "Translation older than source" check | 2 of 11 | 2 of 2 |
| driftcheck | 10 of 11 | 10 of 11 |

- The one it missed I planted to be uncatchable by number checks: the Swedish refunds page says non-refundable tickets *can* be refunded. No number changed, so the tool didn't see it.
- One flag is wrong. The Finnish page says "kolme viikkoa" (three weeks) where English says "21 days". Correct, but there's no number, so it got flagged. I wrote that page that way on purpose, to see how the tool handles numbers written as words.

## Known limits

- Only en/fi/sv/de, and only kg, cm, €, hours, minutes and days.
- A comma is always read as a decimal mark, so an English "€1,000" comes out as 1.
- Ranges like "2–3 days" only pick up the 3.
- Questions are answered from a section by its position, so a dropped or reordered section gets read wrong.
- Sections are only counted, not matched. Drop one and add another and it passes.
- Links into another locale (a Finnish page linking to `/en/...`) aren't checked.
- Staleness compares dates as strings, so they have to be ISO `YYYY-MM-DD`.

## Layout

```
driftcheck/extract.py   fact/link/section extraction (regex + a unit table for en/fi/sv/de)
driftcheck/compare.py   pairwise comparison, baseline, answer divergence, eval
driftcheck/report.py    static HTML report
driftcheck/__main__.py  CLI
data/articles.json      synthetic corpus
data/planted_issues.json ground truth
data/questions.json     customer questions → (article, section, unit)
tests/                  extraction tests, plus a check of the result above
```

## If I kept going

- Read from a CMS export or API instead of JSON. Run it on publish.
- A second pass with an LLM for meaning drift, like the Swedish refunds page. Only on pairs the number checks call clean.
- Number words per language ("three weeks", "kolme viikkoa").
- Turn every divergent question into a regression test for the assistant.
