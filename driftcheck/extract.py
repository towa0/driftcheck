"""Pulls the things a translation must keep unchanged (numbers with units, links, sections) out of article markdown."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# unit word (lowercased) -> canonical unit. Covers en / fi / sv / de forms used in help copy.
UNIT_WORDS = {
    "kg": "kg",
    "h": "hour", "hour": "hour", "hours": "hour",
    "tunti": "hour", "tuntia": "hour", "tunnin": "hour",
    "timme": "hour", "timmar": "hour", "timmars": "hour",
    "stunde": "hour", "stunden": "hour",
    "min": "minute", "minute": "minute", "minutes": "minute",
    "minuutti": "minute", "minuuttia": "minute", "minuutin": "minute",
    "minuter": "minute", "minuten": "minute",
    "day": "day", "days": "day",
    "päivä": "day", "päivää": "day", "päivän": "day",
    "dag": "day", "dagar": "day", "dagars": "day",
    "tag": "day", "tage": "day", "tagen": "day",
    "eur": "eur", "euro": "eur", "euroa": "eur", "euron": "eur", "€": "eur",
}

NUM = r"\d+(?:[.,]\d+)?"
DIM_RE = re.compile(rf"({NUM})\s*[x×]\s*({NUM})\s*[x×]\s*({NUM})\s*cm", re.I)
EUR_PREFIX_RE = re.compile(rf"(?:€|\bEUR\s?)({NUM})", re.I)
NUM_UNIT_RE = re.compile(rf"({NUM})\s*(€|[A-Za-zÀ-ÿ]+)", re.I)
LINK_RE = re.compile(r"\[([^\]]+)\]\((/[^)\s]+)\)")
HEADING_RE = re.compile(r"^##\s+(.+)$", re.M)


def _num(s: str) -> float:
    return float(s.replace(",", "."))


@dataclass(frozen=True)
class Fact:
    unit: str
    value: str  # normalised string, e.g. "8" / "7.5" / "55x40x23"

    def __str__(self) -> str:
        return f"{self.value} {self.unit}"


@dataclass
class Section:
    heading: str
    text: str
    facts: list[Fact] = field(default_factory=list)


@dataclass
class Extracted:
    title: str
    sections: list[Section]
    links: list[str]  # locale-normalised: "/{loc}/hotel-booking"

    @property
    def facts(self) -> list[Fact]:
        return [f for s in self.sections for f in s.facts]


def _fmt(x: float) -> str:
    return str(int(x)) if x == int(x) else str(x)


def extract_facts(text: str) -> list[Fact]:
    facts: list[Fact] = []
    # 55 x 40 x 23 cm. Runs first and gets blanked, so its numbers aren't read again
    for m in DIM_RE.finditer(text):
        facts.append(Fact("cm", "x".join(_fmt(_num(g)) for g in m.groups())))
    text = DIM_RE.sub(" ", text)
    # €60, EUR 60
    for m in EUR_PREFIX_RE.finditer(text):
        facts.append(Fact("eur", _fmt(_num(m.group(1)))))
    text = EUR_PREFIX_RE.sub(" ", text)
    # 8 kg, 36 tuntia, 60 €, 14 Tagen
    for m in NUM_UNIT_RE.finditer(text):
        unit = UNIT_WORDS.get(m.group(2).lower())
        if unit:
            facts.append(Fact(unit, _fmt(_num(m.group(1)))))
    return facts


def normalise_link(path: str, locale: str) -> str:
    prefix = f"/{locale}/"
    return "/{loc}/" + path[len(prefix):] if path.startswith(prefix) else path


def extract(body: str, locale: str) -> Extracted:
    title_m = re.search(r"^#\s+(.+)$", body, re.M)
    title = title_m.group(1).strip() if title_m else ""
    parts = HEADING_RE.split(body)
    # split keeps the captured ## headings: [preamble, heading, text, heading, text, ...]
    sections = []
    for i in range(1, len(parts), 2):
        heading, text = parts[i].strip(), parts[i + 1]
        sections.append(Section(heading, text.strip(), extract_facts(text)))
    links = [normalise_link(p, locale) for _, p in LINK_RE.findall(body)]
    return Extracted(title, sections, links)
