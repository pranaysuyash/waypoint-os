#!/usr/bin/env python3
"""
Waypoint OS Financial Model
Run: python3 tools/financial_model.py
Edit assumptions in the CONFIG section and re-run to see updated projections.
"""

from datetime import datetime

# ============================================================
# CONFIG — Edit these values to run different scenarios
# ============================================================

# Year 1: new customers per month (Months 1-12)
Y1_NEW_CUSTOMERS = [0, 0, 2, 3, 4, 5, 5, 6, 6, 7, 7, 5]

# Year 2: new customers per month
Y2_NEW_CUSTOMERS = [8, 9, 10, 12, 14, 15, 16, 17, 18, 20, 22, 18]

# Year 3: new customers per month
Y3_NEW_CUSTOMERS = [22, 25, 28, 32, 35, 38, 42, 45, 48, 52, 55, 48]

# Blended ARPU by year
Y1_ARPU = 3500
Y2_ARPU = 4500
Y3_ARPU = 5500

# Churn rates by year
Y1_CHURN = 0.03
Y2_CHURN = 0.03
Y3_CHURN = 0.025

# Fixed monthly costs (INR)
MONTHLY_FIXED = 21000

# Variable cost per customer per month (INR)
VAR_COST_PER_CUSTOMER = 500

# USD conversion
USD_RATE = 83

# Unit economics by tier
TIERS = [
    ("Solo",    999,   0.70, 0.05, 833),
    ("Core",    6000,  0.80, 0.03, 2500),
    ("Scale",   12000, 0.85, 0.02, 10000),
    ("Blended", 3500,  0.80, 0.03, 2880),
]

# Scenarios for stress test
SCENARIOS = [
    ("Worst",        5,  2000, 0.07),
    ("Conservative", 8,  2500, 0.05),
    ("Base",         15, 3500, 0.03),
    ("Optimistic",   30, 5000, 0.01),
]

# ============================================================
# MODEL (no need to edit below this line)
# ============================================================

def project_monthly(new_customers, arpu, churn):
    active = 0
    customers, revenue = [], []
    for m in new_customers:
        active = int(active * (1 - churn) + m)
        customers.append(active)
        revenue.append(int(active * arpu))
    return customers, revenue

def project_year(nc, arpu, churn, start):
    a = start
    tot = 0
    for m in nc:
        a = int(a * (1 - churn) + m)
        tot += int(a * arpu)
    return a, tot

def run():
    print("=" * 70)
    print(" WAYPOINT OS — FINANCIAL MODEL")
    print(f" Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f" 1 USD = INR {USD_RATE}")
    print("=" * 70)

    # 1. Core Revenue Model
    print("\n" + "=" * 70)
    print(" 1. CORE REVENUE MODEL (YEAR 1)")
    print("=" * 70)

    y1_cust, y1_mrr = project_monthly(Y1_NEW_CUSTOMERS, Y1_ARPU, Y1_CHURN)
    y1_cum = sum(y1_mrr)

    print(f"\n{'Mon':>3} {'New':>4} {'Active':>6} {'MRR':>9} {'ARR':>10}")
    print("-" * 36)
    for i in range(12):
        print(f"{i+1:>3} {Y1_NEW_CUSTOMERS[i]:>4} {y1_cust[i]:>6} {y1_mrr[i]:>8,} {y1_mrr[i]*12:>9,}")

    print(f"\nYear 1 Exit: {y1_cust[-1]} customers")
    print(f"Month 12 MRR: INR {y1_mrr[-1]:,}")
    print(f"Month 12 ARR: INR {y1_mrr[-1]*12:,}")
    print(f"Y1 Cumulative Revenue: INR {y1_cum:,}")

    # 2. Unit Economics
    print("\n" + "=" * 70)
    print(" 2. UNIT ECONOMICS BY TIER")
    print("=" * 70)

    print(f"\n{'Tier':>8} {'ARPU':>7} {'GM':>5} {'Churn':>6} {'LTV':>10} {'CAC':>8} {'LTV/CAC':>8} {'Payback':>8}")
    print("-" * 62)
    for name, arpu, gm, churn, cac in TIERS:
        ltv = int(arpu * gm / churn)
        ratio = ltv / cac
        payback = cac / (arpu * gm)
        print(f"{name:>8} {arpu:>6,} {gm:>4.0%} {churn:>5.1%} {ltv:>9,} {cac:>7,} {ratio:>6.1f}x {payback:>6.1f}m")

    # 3. Three-Year Projection
    print("\n" + "=" * 70)
    print(" 3. THREE-YEAR PROJECTION")
    print("=" * 70)

    y2e, y2r = project_year(Y2_NEW_CUSTOMERS, Y2_ARPU, Y2_CHURN, y1_cust[-1])
    y3e, y3r = project_year(Y3_NEW_CUSTOMERS, Y3_ARPU, Y3_CHURN, y2e)

    y2arr = int(y2r / 12 * 12)
    y3arr = int(y3r / 12 * 12)

    print(f"\n{'Year':>4} {'Cust':>8} {'Revenue':>14} {'ARR':>14} {'ARR($)':>10}")
    print("-" * 52)
    print(f"{'Y1':>4} {y1_cust[-1]:>8} {y1_cum:>12,} {y1_mrr[-1]*12:>12,} {y1_mrr[-1]*12/USD_RATE:>8,.0f}")
    print(f"{'Y2':>4} {y2e:>8} {y2r:>12,} {y2arr:>12,} {y2arr/USD_RATE:>8,.0f}")
    print(f"{'Y3':>4} {y3e:>8} {y3r:>12,} {y3arr:>12,} {y3arr/USD_RATE:>8,.0f}")

    # 4. Scenario Stress Test
    print("\n" + "=" * 70)
    print(" 4. SCENARIO STRESS TEST (YEAR 3 EXIT)")
    print("=" * 70)

    for name, npm, arpu, churn in SCENARIOS:
        a = 0
        r = 0
        for _ in range(36):
            a = int(a * (1 - churn) + npm)
            r += int(a * arpu)
        arr = a * arpu * 12
        print(f"\n{name:>15}: {npm}/mo @ INR{arpu:,}, {churn*100:.0f}% churn")
        print(f"  Customers: {a:,} | ARR: INR{arr:>12,} | ARR($): ${arr/USD_RATE:>10,.0f} | Rev: INR{r:>12,}")

    # 5. Breakeven
    print("\n" + "=" * 70)
    print(" 5. BREAKEVEN ANALYSIS")
    print("=" * 70)

    be = MONTHLY_FIXED / (Y1_ARPU - VAR_COST_PER_CUSTOMER)
    print(f"\nBreakeven at {be:.1f} customers")

    all_new = Y1_NEW_CUSTOMERS + Y2_NEW_CUSTOMERS + Y3_NEW_CUSTOMERS
    a = 0
    cr = cc = 0
    be_m = None
    for m in range(36):
        a = int(a * 0.97 + all_new[m])
        r = a * Y1_ARPU
        c = MONTHLY_FIXED + a * VAR_COST_PER_CUSTOMER
        cr += r
        cc += c
        if cr >= cc and be_m is None:
            be_m = m + 1

    if be_m:
        print(f"Base case breakeven: Month {be_m}")
        print(f"36mo net profit: INR {cr-cc:,.0f}")

    # 6. Churn Sensitivity
    print("\n" + "=" * 70)
    print(" 6. CHURN SENSITIVITY (Core INR6,000, 80% GM)")
    print("=" * 70)
    for c in [1, 2, 3, 4, 5, 7, 10]:
        print(f"  {c:>2}%/mo -> LTV: INR{int(6000*0.80/(c/100)):>9,}")

    # 7. Cash Flow
    print("\n" + "=" * 70)
    print(" 7. YEAR 1 CASH FLOW (INR)")
    print("=" * 70)
    cum = 0
    for i in range(12):
        cost = MONTHLY_FIXED + y1_cust[i] * VAR_COST_PER_CUSTOMER
        net = y1_mrr[i] - cost
        cum += net
        print(f"  M{i+1:>2}: +INR{y1_mrr[i]:>8,}  -INR{cost:>8,}  =INR{net:>8,}  Cum:INR{cum:>9,}")

    # 8. Sensitivity Table
    print("\n" + "=" * 70)
    print(" 8. SENSITIVITY — Y3 ARR (INR Lakhs) @ INR3,500 ARPU")
    print("=" * 70)
    print(f"{'Churn':>6}", end="")
    for n in [5, 10, 15, 20, 30]:
        print(f"{n:>8}/mo", end="")
    print()
    for c in [1, 2, 3, 5, 7]:
        print(f"{c:>3}%/mo", end="")
        for n in [5, 10, 15, 20, 30]:
            a = 0
            for _ in range(36):
                a = int(a * (1 - c/100) + n)
            print(f"{a*3500*12/100000:>8.1f}L", end="")
        print()

    print("\n" + "=" * 70)
    print(" MODEL COMPLETE")
    print("  To re-run with different assumptions, edit the")
    print("  CONFIG section at the top of this script.")
    print("=" * 70)

if __name__ == "__main__":
    run()
