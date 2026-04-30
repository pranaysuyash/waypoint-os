#!/usr/bin/env python3
"""
Waypoint OS Financial Model — v2 (Corrected Assumptions)
Based on: 70% Solo (₹999), 20% Core (₹6,000), 10% Scale (₹12,000)
LLM costs at old rates, ₹30K fixed, ₹1L one-time, USD 93
Run: python3 tools/financial_model_v2.py
"""

from datetime import datetime

# Plan mix
SOLO_PCT, CORE_PCT, SCALE_PCT = 0.70, 0.20, 0.10
BLENDED_ARPU = int(SOLO_PCT * 999 + CORE_PCT * 6000 + SCALE_PCT * 12000)
BLENDED_CHURN = SOLO_PCT * 0.05 + CORE_PCT * 0.03 + SCALE_PCT * 0.02

Y1_NEW = [0, 0, 3, 4, 5, 6, 7, 8, 9, 10, 10, 8]
Y2_NEW = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 25]
Y3_NEW = [30, 33, 36, 40, 44, 48, 52, 56, 60, 65, 70, 60]

FIXED = 30000
VAR = 600
ONE_TIME = 100000
USD = 93

TIERS = [
    ("Solo", 999, 0.70, 0.05, 833),
    ("Core", 6000, 0.80, 0.03, 2500),
    ("Scale", 12000, 0.85, 0.02, 10000),
    ("Blended", BLENDED_ARPU, 0.75, BLENDED_CHURN, 2000),
]

def pm(nc, arpu, ch):
    a, cust, rev = 0, [], []
    for m in nc:
        a = int(a * (1 - ch) + m)
        cust.append(a)
        rev.append(int(a * arpu))
    return cust, rev

def py(nc, arpu, ch, start):
    a, tot = start, 0
    for m in nc:
        a = int(a * (1 - ch) + m)
        tot += int(a * arpu)
    return a, tot

def run():
    print("=" * 62)
    print(f" WAYPOINT OS v2 — Corrected Assumptions")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M')} | USD = ₹{USD}")
    print("=" * 62)

    y1c, y1r = pm(Y1_NEW, BLENDED_ARPU, BLENDED_CHURN)
    y1_rev = sum(y1r)
    y2e, y2r = py(Y2_NEW, BLENDED_ARPU, BLENDED_CHURN, y1c[-1])
    y3e, y3r = py(Y3_NEW, BLENDED_ARPU, BLENDED_CHURN, y2e)

    print(f"\nMix: {SOLO_PCT*100:.0f}% Solo / {CORE_PCT*100:.0f}% Core / {SCALE_PCT*100:.0f}% Scale")
    print(f"Blended ARPU: ₹{BLENDED_ARPU:,} | Churn: {BLENDED_CHURN:.1%}")
    print(f"Fixed: ₹{FIXED:,}/mo | Variable: ₹{VAR}/cust | One-time: ₹{ONE_TIME:,}")

    print(f"\n{'Year':>4} {'Cust':>7} {'Rev':>13} {'ARR':>13} {'ARR($)':>9}")
    print("-" * 48)
    print(f"{'1':>4} {y1c[-1]:>7} {y1_rev:>11,} {y1r[-1]*12:>11,} {y1r[-1]*12/USD:>7,.0f}")
    print(f"{'2':>4} {y2e:>7} {y2r:>11,} {y2r//12*12:>11,} {y2r//12*12/USD:>7,.0f}")
    print(f"{'3':>4} {y3e:>7} {y3r:>11,} {y3r//12*12:>11,} {y3r//12*12/USD:>7,.0f}")

    print(f"\nTier Economics:")
    print(f"{'Tier':>8} {'ARPU':>7} {'LTV':>10} {'CAC':>8} {'LTV/CAC':>8}")
    for t in TIERS:
        gp = t[1] - VAR
        ltv = int(gp / t[3])
        ratio = ltv / t[4]
        print(f"{t[0]:>8} ₹{t[1]:>5,} ₹{ltv:>8,} ₹{t[4]:>6,} {ratio:>6.1f}x")

    be = FIXED / (BLENDED_ARPU - VAR)
    print(f"\nBreakeven: {be:.0f} customers | Cash needed: ₹1,00,000 ($1,075)")

if __name__ == "__main__":
    run()
