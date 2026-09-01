"""RQ-01 prototype validation — scratch, not shipped.

Amended rules demonstrating the deterministic ceiling is NOT reached.
Runs the 12 budget fixtures through prototype regexes and scores
amount/currency/scope/flexibility field-level correctness.
"""
import json
import re

CONNECTIVES = r"(?:\s+(?:of|is|was|only|around|about|approx(?:imately)?|roughly|up\s+to|under|no\s+more\s+than|maximum|max(?:imum)?|exactly|at\s+most))*"
UNIT_OPT = r"(?:(?:l|k|m|mn|million|millions|lac|lakh|lakhs|crore|crores|cr|b|bn|billion|billions|thousand))?"
CURRENCY_TOKEN = r"(?:usd|inr|eur|gbp|dollars?|bucks?|euros?|₹|\$|€|£)"
CURRENCY_MAP = {"$": "USD", "usd": "USD", "dollar": "USD", "dollars": "USD", "buck": "USD", "bucks": "USD",
                "€": "EUR", "eur": "EUR", "euro": "EUR", "euros": "EUR", "£": "GBP", "gbp": "GBP",
                "₹": "INR", "inr": "INR"}

# Pattern 1: budget keyword + multi-connective + optional currency either side of amount
P_BUDGET = (rf"\bbudget\b{CONNECTIVES}\s*[:\-]?\s*(?:(?P<curA>{CURRENCY_TOKEN})\s*)?"
            rf"(?P<amt>\d[\d,]*(?:\.\d+)?)\s*{UNIT_OPT}(?:\s*(?P<curB>{CURRENCY_TOKEN}))?")
# Pattern 2: keyword-free anchors (spend/have/between) — range BEFORE unit so
# greedy \s* can't swallow the "and" separator; deliberately NO bare "of" anchor
# (it false-positives on "family of 4")
P_ANCHOR = (rf"(?:between\s+|to\s+spend[,:]?\s*|spend(?:ing)?\s+(?:about\s+|around\s+|roughly\s+)?|have\s+(?:about\s+|around\s+|roughly\s+)?|have\s+)"
            rf"(?P<amt2>\d[\d,]*(?:\.\d+)?)"
            rf"(?:\s+(?:and|to|-)\s+(?P<high2>\d[\d,]*(?:\.\d+)?))?"
            rf"\s*{UNIT_OPT}(?:\s*(?P<curC>{CURRENCY_TOKEN}))?")

def extract(text):
    t = text.lower()
    m = re.search(P_BUDGET, t) or re.search(P_ANCHOR, t)
    if not m:
        return None
    gd = m.groupdict()
    cur = gd.get("curA") or gd.get("curB") or gd.get("curC")
    currency = CURRENCY_MAP.get((cur or "").lower(), "USD")
    amount = gd.get("amt") or gd.get("amt2")
    amount = amount.replace(",", "")
    if gd.get("high2"):
        amount = f"{amount}-{gd['high2']}"
    if re.search(r"\b(a\s+day|per\s+day|a\s+night|per\s+night)\b", t):
        scope = "daily"
        amount = f"{amount}/day"
    elif re.search(r"\bper\s+person\b|\beach\b", t):
        scope = "per_person"
    else:
        scope = "total"
    if re.search(r"\b(max(?:imum)?|only|no\s+more\s+than|exactly|at\s+most)\b", t):
        flex = "firm"
    else:
        # golden convention: unmarked budgets are soft (negotiable) by default
        flex = "soft"
    return {"amount": amount, "currency": currency, "scope": scope, "flexibility": flex}

golden = json.load(open("data/fixtures/budget/golden_dataset.json"))
tp = fn = 0
fully_correct = 0
for item in golden:
    exp = item["expected_extracted_fields"]
    got = extract(item["raw_input"]) or {}
    row = []
    fixture_ok = True
    for field, expected in exp.items():
        actual = got.get(field.replace("budget_", ""))
        if expected is None:
            ok = actual is None
        else:
            ok = actual is not None and str(actual).lower() == str(expected).lower()
        tp += ok
        fn += not ok
        fixture_ok = fixture_ok and ok
        row.append(f"{field.replace('budget_', '')}:{'OK' if ok else f'{expected!r}->{actual!r}'}")
    fully_correct += fixture_ok
    print(f"{'OK  ' if fixture_ok else 'MISS'} {item['fixture_id']}: {'; '.join(row)}")
total = sum(len(i["expected_extracted_fields"]) for i in golden)
print(f"\nfield-level recall: {tp}/{total} = {tp/total:.4f}  |  fixture-level: {fully_correct}/{len(golden)} = {fully_correct/len(golden):.4f}")
