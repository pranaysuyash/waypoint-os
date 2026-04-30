#!/usr/bin/env python3
"""
Waypoint OS Financial Model — v1 (Original Assumptions)
Shows the initial baseline model before correction.
Run: python3 tools/financial_model_v1.py
"""

from datetime import datetime

Y1_NEW = [0, 0, 2, 3, 4, 5, 5, 6, 6, 7, 7, 5]
Y2_NEW = [8, 9, 10, 12, 14, 15, 16, 17, 18, 20, 22, 18]
Y3_NEW = [22, 25, 28, 32, 35, 38, 42, 45, 48, 52, 55, 48]

# Original assumptions
Y1_ARPU = 3500
Y2_ARPU = 4500
Y3_ARPU = 5500
Y1_CHURN = 0.03
Y2_CHURN = 0.03
Y3_CHURN = 0.025
MONTHLY_FIXED = 21000
VAR_COST = 500
USD_RATE = 83

def project_monthly(nc, arpu, churn):
    a = 0
    cust, rev = [], []
    for m in nc:
        a = int(a * (1 - churn) + m)
        cust.append(a)
        rev.append(int(a * arpu))
    return cust, rev

def project_year(nc, arpu, churn, start):
    a = start
    tot = 0
    for m in nc:
        a = int(a * (1 - churn) + m)
        tot += int(a * arpu)
    return a, tot

def run():
    print("=" * 65)
    print(" WAYPOINT OS — FINANCIAL MODEL v1 (Original)")
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f" USD/INR: {USD_RATE}")
    print("=" * 65)

    # Year 1
    y1c, y1r = project_monthly(Y1_NEW, Y1_ARPU, Y1_CHURN)
    y1_rev = sum(y1r)
    print(f"\nYear 1: {y1c[-1]} customers, ARR ₹{y1r[-1]*12:,}")

    # Three-year
    y2e, y2r = project_year(Y2_NEW, Y2_ARPU, Y2_CHURN, y1c[-1])
    y3e, y3r = project_year(Y3_NEW, Y3_ARPU, Y3_CHURN, y2e)
    y3arr = y3r // 12 * 12

    print(f"\n{'Year':>4} {'Cust':>8} {'Revenue':>14} {'ARR':>14} {'ARR($)':>10}")
    print("-" * 52)
    print(f"{'Y1':>4} {y1c[-1]:>8} {y1_rev:>12,} {y1r[-1]*12:>12,} {y1r[-1]*12/USD_RATE:>8,.0f}")
    print(f"{'Y2':>4} {y2e:>8} {y2r:>12,} {y2r//12*12:>12,} {y2r//12*12/USD_RATE:>8,.0f}")
    print(f"{'Y3':>4} {y3e:>8} {y3r:>12,} {y3arr:>12,} {y3arr/USD_RATE:>8,.0f}")

    # Unit economics
    print(f"\nUnit Economics (Blended @ ₹{Y1_ARPU} ARPU, {Y1_CHURN*100:.0f}% churn):")
    ltv = int(Y1_ARPU / VAR_COST * Y1_ARPU)
    print(f"  LTV: ₹{ltv:,} | CAC: ₹1,500 | LTV/CAC: {ltv/1500:.1f}x | Payback: {1500/Y1_ARPU:.1f}m")

    # Breakeven
    be = MONTHLY_FIXED / (Y1_ARPU - VAR_COST)
    print(f"  Breakeven: {be:.1f} customers")
    print(f"  Cash needed: ~₹66,000 (~$795)")
    print(f"  Profitable from: Month 6")

if __name__ == "__main__":
    run()
