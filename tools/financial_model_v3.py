#!/usr/bin/env python3
"""
Waypoint OS — Interactive Financial Model
Run: python3 tools/financial_model.py

CHANGE the numbers in SCENARIOS below and re-run to see what happens.
"""

from datetime import datetime

USD_RATE = 93  # INR per USD

# ============================================================
# SCENARIOS — Edit these, re-run, compare
# ============================================================

SCENARIOS = [
    {
        "name": "A: All base plan, no extras",
        "arpu": 1860,          # $20 base, 1 owner + 3 seats
        "churn_pct": 5.0,      # % leave each month
    },
    {
        "name": "B: Base + some seat packs",
        "arpu": 3000,          # ~$32 — some customers buy extra seats
        "churn_pct": 4.0,
    },
    {
        "name": "C: Base + seats + 1 add-on",
        "arpu": 4500,          # ~$48 — seats + one add-on module
        "churn_pct": 3.0,
    },
    {
        "name": "D: Full stack (seats + add-ons)",
        "arpu": 6000,          # ~$65 — most customers on upgrades
        "churn_pct": 2.5,
    },
]

# ============================================================
# COSTS
# ============================================================

# Fixed monthly (pay even with 0 customers)
FIXED_COSTS = {
    "hosting": 10000,         # Vercel + DB. Can start cheaper.
    "llm_base": 2000,         # Minimum LLM usage (testing, dev)
    "tools": 3000,            # Sentry free tier, email, analytics free tier
}
FIXED_MONTHLY = sum(FIXED_COSTS.values())

# Variable per customer per month
# LLM: say ~2,000-3,000 tokens per inquiry, 50-100 inquiries/mo per customer
# At ~$5/M input + $15/M output tokens = ~$0.025/inquiry
# 100 inquiries × $0.025 = $2.50 = ~₹233/mo per customer
# Using cheaper models (Gemini Flash, DeepSeek) can cut this further
VAR_COSTS = {
    "llm_per_customer": 150,  # AI usage per customer/mo
    "infra_per_customer": 100, # Extra storage, bandwidth
    "support_per_customer": 150, # Your time
}
VAR_COST = sum(VAR_COSTS.values())

ONE_TIME = 100000  # Setup: deploy + legal + branding

# ============================================================
# REPORT
# ============================================================

def run():
    print("=" * 68)
    print(" WAYPOINT OS — WHAT-IF FINANCIAL MODEL")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M')} | USD = ₹{USD_RATE}")
    print("=" * 68)

    print(f"\n📋 COSTS")
    print(f"   Fixed/mo: ₹{FIXED_MONTHLY:,} (hosting ₹{FIXED_COSTS['hosting']:,}"
          f" + LLM base ₹{FIXED_COSTS['llm_base']:,}"
          f" + tools ₹{FIXED_COSTS['tools']:,})")
    print(f"   Variable/customer: ₹{VAR_COST}/mo"
          f" (LLM ₹{VAR_COSTS['llm_per_customer']}"
          f" + infra ₹{VAR_COSTS['infra_per_customer']}"
          f" + support ₹{VAR_COSTS['support_per_customer']})")
    print(f"   One-time: ₹{ONE_TIME:,} (${ONE_TIME/USD_RATE:.0f})")
    print(f"   Breakeven customers: {FIXED_MONTHLY//2000} (at ₹2K ARPU)")
    print(f"                          {FIXED_MONTHLY//4000} (at ₹4K ARPU)")
    print(f"                          {FIXED_MONTHLY//6000} (at ₹6K ARPU)")

    print(f"\n📊 SCENARIO COMPARISON (at 50 customers — about 1 year in)")
    print(f"{'Name':>32} {'ARPU':>7} {'Churn':>7} {'MRR':>9} {'ARR':>11} {'ARR($)':>9} {'LTV':>10} {'CAC':>8} {'LTV/CAC':>7}")
    print("-" * 102)

    for s in SCENARIOS:
        arpu = s["arpu"]
        churn = s["churn_pct"] / 100
        cac = _estimate_cac(churn)
        customers = 50
        mrr = customers * arpu
        arr = mrr * 12
        gp = arpu - VAR_COST  # gross profit per customer
        ltv = int(gp / churn)
        ratio = ltv / cac if cac > 0 else 0

        print(f"{s['name']:>32} ₹{arpu:>5,} {churn*100:>5.1f}%"
              f" ₹{mrr:>7,} ₹{arr:>9,} ${arr/USD_RATE:>7,}"
              f" ₹{ltv:>8,} ₹{cac:>6,} {ratio:>5.1f}x")

    print(f"\n🔍 WHAT-IF: WHAT HAPPENS AT DIFFERENT CUSTOMER COUNTS?")
    print(f"(Using Scenario B: ₹3,000 ARPU, 4% churn)")
    print(f"{'Customers':>10} {'MRR':>9} {'ARR':>11} {'ARR($)':>9} {'Monthly Cost':>13} {'Net/mo':>9} {'Cumulative':>12}")
    print("-" * 75)

    arpu = 3000
    churn = 0.04
    cum = -ONE_TIME

    for count in [5, 10, 20, 30, 50, 75, 100, 150, 200]:
        mrr = count * arpu
        cost = FIXED_MONTHLY + count * VAR_COST
        net = mrr - cost

        # Simple cumulative estimate
        if count <= 50:
            cum += net

        print(f"{count:>10} ₹{mrr:>7,} ₹{mrr*12:>9,} ${mrr*12/USD_RATE:>7,}"
              f" ₹{cost:>11,} ₹{net:>7,} ₹{cum:>10,}")

    print(f"\n📉 CHURN SENSITIVITY (at ₹3,000 ARPU)")
    print(f"{'Monthly Churn':>14} {'Annual Loss':>13} {'Customer LTV':>13} {'What it means':>30}")
    print("-" * 72)
    for c in [1, 2, 3, 4, 5, 7, 10]:
        churn = c / 100
        annual_loss = (1 - (1-churn)**12) * 100
        ltv = int((arpu - VAR_COST) / churn)
        note = "Good" if c <= 2 else "OK" if c <= 4 else "Fix this" if c <= 7 else "Critical"
        print(f"{c:>6}%/mo {annual_loss:>10.1f}% ₹{ltv:>10,} {note:>30}")

    print(f"\n📐 FORMULAS (so you can calculate your own)")
    print(f"   ARPU = Average Revenue Per User = total monthly revenue ÷ customers")
    print(f"   MRR  = Monthly Recurring Revenue = customers × ARPU")
    print(f"   ARR  = Annual Recurring Revenue = MRR × 12")
    print(f"   Churn = % of customers who leave each month")
    print(f"   LTV  = Lifetime Value = (ARPU - variable costs) ÷ churn rate")
    print(f"   CAC  = Customer Acquisition Cost = total sales spend ÷ customers gained")
    print(f"   LTV/CAC = how many times your investment comes back. > 3x is healthy.")
    print(f"   Payback = months to recover CAC = CAC ÷ (ARPU - variable costs)")

def _estimate_cac(churn):
    """Rough CAC by channel quality — lower churn channels cost more to acquire."""
    if churn <= 0.02: return 8000    # Referral/host agency — high trust, low churn, higher CAC
    if churn <= 0.03: return 4000    # LinkedIn/content
    if churn <= 0.04: return 2000    # Facebook/WhatsApp organic
    if churn <= 0.05: return 1500    # Low-effort channels
    return 1000                       # High-churn channels (cheap but not sticky)

if __name__ == "__main__":
    run()
