# Same question, different number depending on language

If a help page says one thing in English and something else in Swedish, a chatbot that reads both could give different answers depending on which language you ask in.

I built a small tool to catch that. Everything here uses help pages I wrote myself for a made-up airline. No Finnair content or data. I don't know how Finnair's help pages are actually written or translated.

## What the tool does

- Compares each translated help page with the English one.
- Points out where they disagree: a different number, a missing section, a missing or dead link, or a page that wasn't updated after the English one changed.
- Shows where the pages give different numbers for the same customer question.

## What I found, on a test set I wrote myself

I wrote the same 5 help pages (cabin baggage, online check-in, meals and hotels during delays, refunds, delayed baggage) in English, Finnish, Swedish and German. Then I put mistakes in some of them on purpose. The Swedish cabin-baggage page, for example, says 7.5 kg where the English says 8 kg.

I wrote both the mistakes and the tool, so this only shows the tool does what I designed it to do. It says nothing about real help pages.

The tool found every mistake but one, and I planted that one so number checks couldn't catch it. It also flagged one page that was fine. The simple check, "is the translation older than the English page?", found only the two pages that were out of date. It missed the wrong numbers. Those pages weren't old. Just wrong.

## Limits

- It misses changes in meaning. My Swedish refunds page says non-refundable tickets *can* be refunded, the opposite of the English. No number changed, so the tool didn't notice. A person, or a language model, would have to read for that.
- It can flag correct pages. My Finnish delayed-baggage page says "three weeks" in words where the English says "21 days". That's correct, but the tool only looks for numbers, so it reported a missing deadline. I wrote that page that way on purpose, to see how the tool handles numbers written as words.
- It only knows English, Finnish, Swedish and German, and only a few kinds of numbers: weights, sizes, prices, hours, minutes and days.

## An open question

If you run a help centre in more than one language: do the versions ever disagree like this? Or does your translation setup already stop it?

## How to see it

Open `out/report.html` in a browser (it works on a phone). To rerun it: `python3 -m driftcheck`.

---

## Sources and evidence

Why I picked this problem. These are public sources only. Where a source is weak, I say so.

| Topic | What the source says | Source and date | Source type |
|---|---|---|---|
| Finnair's chatbot reads the website | Sisu "draws its answers directly from the latest content on the Finnair website". It answers in 15 languages and serves 2,000–4,000 customers a day. Finnair notes it can occasionally get things wrong. | [Finnair Blue Wings, Sisu article](https://www.finnair.com/en/bluewings/world-of-finnair/meet-finnair-s-ai-customer-service-assistant--sisu-4261942), published 28 Apr 2026, updated 15 Jun 2026 | First-party |
| Booking lookups and name spelling | The same article says lookups can fail if the last name isn't typed exactly as booked, including Nordic letters. | Same as above | First-party |
| Many versions of the same page | The same Finnair article appears under many country/language addresses, e.g. `/de-de/`, `/at-de/`, `/ch-de/`, `/fi-en/`, `/se-sv/`, `/fi-sv/`. | finnair.com URLs seen in search results, Nov 2026 | My observation of URLs only |
| AI in customer service is a priority | "AI-driven customer service solutions" named as part of 2026 plans. | [Finnair Q4 2025 release](https://investors.finnair.com/files/documents/Finnair%20Q4%202025.pdf), 11 Feb 2026 | First-party |
| Disruption notices are written per event | E.g. a notice for Helsinki airspace restrictions, saying rebooking "could take longer than usual". | [Finnair travel update](https://www.finnair.com/ee-et/lennuinfo/arhiivitud-reisiinfo/effects-of-the-helsinki-airport-airspace-restrictions-on-our-flights-on-15-may-2026-4288562), 15 May 2026 | First-party |
| Check-in trouble in the app | One reviewer: "Probably the worst app for checking in". Forum users describe check-in failing and the app losing an upcoming flight. | [App Store reviews (Estonia)](https://apps.apple.com/ee/app/id933867978?l=en-gb), undated; [FlyerTalk thread](https://www.flyertalk.com/forum/finnair-finnair-plus/1845468-ay-108-printerfriendly.html), Sep–Oct 2025 | Anecdotal |
| Different channels, different info | One traveller: the app showed 3 free bags, the e-ticket 2, the airport counter allowed 1. | [FlyerTalk post](https://www.flyertalk.com/forum/36645944-post1.html), undated | Anecdotal, single post |

### All sources
- [Meet Finnair's AI customer service assistant, Sisu](https://www.finnair.com/en/bluewings/world-of-finnair/meet-finnair-s-ai-customer-service-assistant--sisu-4261942) (28 Apr 2026, updated 15 Jun 2026)
- [Finnair Q4 2025 financial statements release](https://investors.finnair.com/files/documents/Finnair%20Q4%202025.pdf) (11 Feb 2026)
- [Helsinki airspace restrictions travel update](https://www.finnair.com/ee-et/lennuinfo/arhiivitud-reisiinfo/effects-of-the-helsinki-airport-airspace-restrictions-on-our-flights-on-15-may-2026-4288562) (15 May 2026)
- [Finnair app, App Store (Estonia)](https://apps.apple.com/ee/app/id933867978?l=en-gb) (anecdotal)
- [FlyerTalk Finnair thread](https://www.flyertalk.com/forum/finnair-finnair-plus/1845468-ay-108-printerfriendly.html) (anecdotal, Sep–Oct 2025)
- [FlyerTalk bag-charge post](https://www.flyertalk.com/forum/36645944-post1.html) (anecdotal)
