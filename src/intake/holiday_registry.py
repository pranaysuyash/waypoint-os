"""
src/intake/holiday_registry.py — festival/holiday name resolution for intake
("during Diwali", "after Dasara", "plan by Christmas", "Eid trip").

The geography precedent applied to time: travelers reference festivals, not
calendars. A traveler saying "during Diwali" means a specific date window the
system can resolve deterministically — Diwali 2026 is Nov 8, computed from the
lunar calendar. Hand-rolling that per extractor is exactly the failure mode the
city gazetteer replaced.

Design:
- HOLIDAY_REGISTRY: curated canonical festivals + aliases (regional spellings,
  Hinglish, colloquial) + country scope. This is the NAME data.
- The `holidays` package (pypi, 100+ countries) is the DATE data: authoritative
  per-year computation incl. lunar/movable holidays. Never hand-compute those.
- Curated approximate windows ONLY for month-scale references the package does
  not list (Ramadan is a month, Navratri spans 9 nights) — always flagged
  `approximate: True`, never presented as a precise date.

Resolution precedence: package match (exact year) > curated approximate >
None (abstain honestly).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Optional

# canonical -> {aliases, countries ("*" = globally understood), hint
# substrings for matching `holidays`-package display names, approximate
# fallback (month, day) or (month, "span") with label}. Aliases lowercase.
HOLIDAY_REGISTRY: List[Dict[str, Any]] = [
    {"canonical": "Diwali", "aliases": ["diwali", "deepavali", "dipavali", "festival of lights"], "countries": ["IN", "NP", "SG", "MY", "FJ", "*"], "hints": ["diwali"]},
    {"canonical": "Holi", "aliases": ["holi", "holika dahan"], "countries": ["IN", "NP", "*"], "hints": ["holi"]},
    {"canonical": "Dussehra", "aliases": ["dussehra", "dasara", "dashara", "vijayadashami"], "countries": ["IN", "NP"], "hints": ["dussehra", "dasara"]},
    {"canonical": "Navratri", "aliases": ["navratri", "navaratri"], "countries": ["IN"], "hints": ["navratri"], "approx": (10, "early-to-mid October, shifts with the lunar calendar")},
    {"canonical": "Raksha Bandhan", "aliases": ["raksha bandhan", "rakhi", "rakshabandhan"], "countries": ["IN"], "hints": ["raksha bandhan", "rakhi"]},
    {"canonical": "Karva Chauth", "aliases": ["karva chauth", "karvachauth", "karwa chauth"], "countries": ["IN"], "hints": ["karva"], "approx": (10, "late October / early November, lunar")},
    {"canonical": "Pongal", "aliases": ["pongal"], "countries": ["IN"], "hints": ["pongal"], "approx": (1, "Jan 14-17 (Thai Pongal)")},
    {"canonical": "Makar Sankranti", "aliases": ["makar sankranti", "sankranti"], "countries": ["IN"], "hints": ["sankranti"], "approx": (1, "Jan 14-15")},
    {"canonical": "Lohri", "aliases": ["lohri"], "countries": ["IN"], "hints": ["lohri"], "approx": (1, "Jan 13")},
    {"canonical": "Baisakhi", "aliases": ["baisakhi", "vaisakhi"], "countries": ["IN"], "hints": ["baisakhi", "vaisakhi"], "approx": (4, "Apr 13-14")},
    {"canonical": "Onam", "aliases": ["onam"], "countries": ["IN"], "hints": ["onam"], "approx": (8, "Aug-Sep (Malayalam calendar)")},
    {"canonical": "Buddha Purnima", "aliases": ["buddha purnima", "buddha jayanti", "vesak", "buddha's birthday"], "countries": ["IN"], "hints": ["buddha"]},
    {"canonical": "Mahavir Jayanti", "aliases": ["mahavir jayanti", "mahavir jayanthi"], "countries": ["IN"], "hints": ["mahavira"]},
    {"canonical": "Guru Nanak Jayanti", "aliases": ["guru nanak jayanti", "gurpurab", "guru nanak birthday", "prakash parv"], "countries": ["IN"], "hints": ["guru nanak"]},
    {"canonical": "Ram Navami", "aliases": ["ram navami", "ramnavami"], "countries": ["IN"], "hints": ["ram navami"]},
    {"canonical": "Janmashtami", "aliases": ["janmashtami", "krishna janmashtami", "janmastami"], "countries": ["IN"], "hints": ["janmashtami"]},
    {"canonical": "Maha Shivratri", "aliases": ["maha shivratri", "shivratri", "shivaratri", "mahashivratri"], "countries": ["IN"], "hints": ["shivratri", "shivaratri"]},
    {"canonical": "Eid al-Fitr", "aliases": ["eid al-fitr", "eid ul-fitr", "eid ul fitr", "meethi eid", "small eid", "eid"], "countries": ["IN", "AE", "SA", "ID", "MY", "PK", "*"], "hints": ["eid al-fitr"]},
    {"canonical": "Eid al-Adha", "aliases": ["eid al-adha", "eid ul-adha", "bakrid", "bakr-id", "big eid", "qurbani eid"], "countries": ["IN", "AE", "SA", "ID", "MY", "PK", "*"], "hints": ["eid al-adha"]},
    {"canonical": "Ramadan", "aliases": ["ramadan", "ramzaan", "ramzan", "ramadhan"], "countries": ["*"], "hints": [], "approx": (3, "the Ramadan month, shifts ~11 days earlier each year")},
    {"canonical": "Christmas", "aliases": ["christmas", "xmas", "christmas eve"], "countries": ["*"], "hints": ["christmas"]},
    {"canonical": "Easter", "aliases": ["easter", "easter sunday"], "countries": ["*"], "hints": ["easter"]},
    {"canonical": "New Year", "aliases": ["new year", "new years", "new year's", "new year's eve", "nye", "new year eve"], "countries": ["*"], "hints": ["new year"]},
    {"canonical": "Thanksgiving", "aliases": ["thanksgiving", "turkey day"], "countries": ["US", "CA"], "hints": ["thanksgiving"]},
    {"canonical": "Halloween", "aliases": ["halloween"], "countries": ["US", "CA", "GB", "*"], "hints": ["halloween"]},
    {"canonical": "Valentine's Day", "aliases": ["valentine's day", "valentines day", "valentine day", "valentine's"], "countries": ["*"], "hints": ["valentine"]},
    {"canonical": "Chinese New Year", "aliases": ["chinese new year", "lunar new year", "spring festival", "cny"], "countries": ["SG", "MY", "CN", "TW", "HK", "*"], "hints": ["chinese new year", "lunar new year", "spring festival"]},
    {"canonical": "Songkran", "aliases": ["songkran"], "countries": ["TH"], "hints": ["songkran"], "approx": (4, "Apr 13-15")},
    {"canonical": "Hanukkah", "aliases": ["hanukkah", "hanukah", "chanukah", "festival of lights 8 days"], "countries": ["*"], "hints": ["hanukkah", "chanukah"], "approx": (12, "late Nov-late Dec, lunar")},
    {"canonical": "Obon", "aliases": ["obon", "bon festival"], "countries": ["JP"], "hints": ["obon"], "approx": (8, "mid-August (most regions)")},
    {"canonical": "Golden Week", "aliases": ["golden week"], "countries": ["JP"], "hints": ["golden week"], "approx": (4, "Apr 29-May 5")},
    {"canonical": "Independence Day (India)", "aliases": ["independence day india", "15 august", "15th august"], "countries": ["IN"], "hints": ["independence day"]},
    {"canonical": "Republic Day (India)", "aliases": ["republic day", "26 january", "26th january"], "countries": ["IN"], "hints": ["republic day"]},
    {"canonical": "Good Friday", "aliases": ["good friday"], "countries": ["*"], "hints": ["good friday"]},
]

_ALIAS_INDEX: Dict[str, Dict[str, Any]] = {}
for _entry in HOLIDAY_REGISTRY:
    for _alias in _entry["aliases"]:
        _ALIAS_INDEX.setdefault(_alias, _entry)

# One compiled alternation, word-ish boundaries both sides (aliases may end
# in non-word chars like "'"), longest-first so "eid al-fitr" wins over "eid".
_sorted_aliases = sorted(_ALIAS_INDEX, key=len, reverse=True)
_ALIAS_RE = re.compile(
    r"(?<![a-z0-9])(" + "|".join(re.escape(a) for a in _sorted_aliases) + r")(?![a-z0-9])",
    re.IGNORECASE,
)

_INTAKE_WINDOW_YEARS = 3  # matches _classify_date_year's sane window (X-03)


# Preposition → window-relation semantics (owner's "during this or after
# this"): the word immediately before the festival shapes the window.
_RELATION_RE = re.compile(
    r"\b(during|after|before|by|around|till|until)\s+$",
)


def find_holiday_references(text: str) -> List[Dict[str, Any]]:
    """All holiday references in the text, in order of appearance. Each:
    {canonical, matched, relation, start, end, countries}. `relation` is the
    preposition semantics of the reference: during (default — the festival is
    part of the trip), after, before, by (a deadline = before), around, till,
    until (= before). Pure, no date resolution."""
    refs: List[Dict[str, Any]] = []
    lower = (text or "").lower()
    for m in _ALIAS_RE.finditer(lower):
        entry = _ALIAS_INDEX[m.group(1)]
        lookback = lower[max(0, m.start() - 12): m.start()]
        rel_match = _RELATION_RE.search(lookback)
        relation = rel_match.group(1) if rel_match else "during"
        if relation in ("till", "until", "by"):
            relation = "before"
        refs.append(
            {
                "canonical": entry["canonical"],
                "matched": m.group(0),
                "relation": relation,
                "start": m.start(),
                "end": m.end(),
                "countries": entry["countries"],
            }
        )
    return refs


def _package_dates(countries: List[str], year: int) -> Dict[str, date]:
    """Country holiday dates for one year from the `holidays` package,
    deduplicated by display name across the scope countries."""
    import holidays as holidays_pkg

    merged: Dict[str, date] = {}
    for cc in countries:
        if cc == "*":
            continue
        try:
            for day, name in holidays_pkg.country_holidays(cc, years=year).items():
                merged.setdefault(str(name), day)
        except Exception:
            continue  # unknown country code in scope list — skip, never raise
    return merged


def _name_matches(hints: List[str], display_name: str) -> bool:
    low = display_name.lower()
    return any(h in low for h in hints)


def resolve_holiday_window(
    canonical: str,
    *,
    today: Optional[date] = None,
) -> Optional[Dict[str, Any]]:
    """Nearest FUTURE date window for a canonical festival within the sane
    intake window (current year .. current+3). Precedence: `holidays`-package
    computation (exact) > curated approximate > None.

    Returns {canonical, date_iso, year, country, source, approximate} —
    `approximate` is always False for package results and True for curated
    spans, and the result carries an honest `label` either way.
    """
    entry = next((e for e in HOLIDAY_REGISTRY if e["canonical"] == canonical), None)
    if entry is None:
        return None
    today = today or date.today()
    scope = [c for c in entry["countries"] if c != "*"] or ["IN"]
    for offset in range(0, _INTAKE_WINDOW_YEARS + 1):
        year = today.year + offset
        if entry.get("hints"):
            dates = _package_dates(scope, year)
            hits = [
                (day, name)
                for name, day in dates.items()
                if _name_matches(entry["hints"], name)
            ]
            if hits:
                # Future-only: a package date earlier than today is skipped
                # (the loop's next year provides the correct next occurrence).
                future = [(day, name) for day, name in hits if day >= today]
                if future:
                    day, _name = sorted(future)[0]
                    return {
                        "canonical": canonical,
                        "date_iso": day.isoformat(),
                        "year": day.year,
                        "country": scope[0],
                        "source": "holidays-package",
                        "approximate": False,
                        "label": f"{canonical} {day.year} falls on {day.isoformat()}",
                    }
        approx = entry.get("approx")
        if approx is not None:
            month, label = approx
            anchor = date(year, month, 1)
            if anchor >= today.replace(day=1):
                return {
                    "canonical": canonical,
                    "date_iso": anchor.isoformat(),
                    "year": year,
                    "country": scope[0],
                    "source": "curated-approximate",
                    "approximate": True,
                    "label": f"{canonical} {year}: {label}",
                }
    return None


def is_known_holiday_name(token: str) -> bool:
    """O(1) alias check — the `is_known_city_normalized` analogue."""
    return (token or "").strip().lower() in _ALIAS_INDEX
