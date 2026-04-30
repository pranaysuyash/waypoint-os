#!/usr/bin/env python3
"""
Waypoint OS Financial Model — v4 (PLG-Informed)
Run: python3 tools/financial_model_v4.py

New in v4: PLG growth curves, viral coefficients, self-serve vs sales-assisted mix.
Edit SCENARIOS to test different assumptions.
"""

from datetime import datetime

USD_RATE = 93

# ============================================================
# PLG GROWTH CONFIG
# ============================================================
# With PLG, growth compounds because:
# 1. Each customer refers ~X others (viral coefficient)
# 2. Self-serve funnel converts visitors without sales calls
# 3. Host agency partnerships onboard many at once

# Growth modes
GROWTH_MODES = {
    "founder-led": {
        "label": "Founder-Led (no PLG)",
        "monthly_new_base": 5,    # New customers/mo (steady, manual)
        "viral_coefficient": 0.0,  # No viral effects
        "self_serve_pct": 0.0,     # All customers need founder contact
    },
    "organic-plg": {
        "label": "Organic PLG",
        "monthly_new_base": 5,     # Base organic
        "viral_coefficient": 0.1,  # 10% of customers refer someone
        "self_serve_pct": 0.3,     # 30% sign up without founder
    },
    "host-partner": {
        "label": "Host Agency Powered",
        "monthly_new_base": 8,     # Higher base from partner channel
        "viral_coefficient": 0.15, # Agencies refer other agencies
        "self_serve_pct": 0.5,     # 50% self-serve
        "partner_batch_size": 50,  # One host = 50 agents at once
        "partner_months": [4, 9],  # Partners come online in months 4 and 9
    },
    "full-plg": {
        "label": "Full PLG + Viral + Partners",
        "monthly_new_base": 10,
        "viral_coefficient": 0.25, # 25% refer someone
        "self_serve_pct": 0.6,     # 60% self-serve
        "partner_batch_size": 100,
        "partner_months": [3, 6, 10],
    },
}

# ============================================================
# PRICING SCENARIOS
# ============================================================

PRICING_SCENARIOS = [
    {
        "name": "A: Base only ($20)",
        "arpu": 1860,
        "churn_pct": 5.0,
        "note": "No upgrades, no add-ons",
    },
    {
        "name": "B: Base + some seat packs",
        "arpu": 3000,
        "churn_pct": 4.0,
        "note": "~30% buy extra seats",
    },
    {
        "name": "C: Base + seats + 1 add-on",
        "arpu": 4500,
        "churn_pct": 3.0,
        "note": "Seats + flight tracking add-on",
    },
    {
        "name": "D: Full stack",
        "arpu": 6500,
        "churn_pct": 2.5,
        "note": "Multiple seats + 2 add-ons",
    },
]

# ============================================================
# COSTS
# ============================================================

# Fixed monthly
FIXED = 15000         # Hosting, LLM base, tools

# Variable per customer per month
LLM_COST = 150        # AI tokens per customer
INFRA_COST = 100      # Storage, bandwidth
SUPPORT_COST = 150    # Your time answering questions
RETENTION_COST = 200  # Customer success — onboarding calls, check-ins, churn reduction
VAR = LLM_COST + INFRA_COST + SUPPORT_COST + RETENTION_COST

# Retention effectiveness: how much does ₹200/mo reduce churn?
# 0.4 = 40% reduction in churn (e.g., 5% → 3%)
# Requires investment of RETENTION_COST per customer per month to get this effect
RETENTION_CHURN_REDUCTION = 0.4  # 0.0 = no effect, 0.5 = cuts churn in half

ONE_TIME = 100000

# ============================================================
# SIMULATION
# ============================================================

def simulate(growth_key, pricing_key, months=36):
    """Run a full simulation for a given growth mode + pricing scenario."""

    g = GROWTH_MODES[growth_key]
    p = next(s for s in PRICING_SCENARIOS if s["name"] == pricing_key)

    arpu = p["arpu"]
    base_churn = p["churn_pct"] / 100
    # Retention investment reduces churn by the configured factor
    churn = base_churn * (1 - RETENTION_CHURN_REDUCTION)
    vc = g["viral_coefficient"]
    self_serve = g["self_serve_pct"]
    base = g["monthly_new_base"]

    # Growth starts slow (founder does everything), shifts to PLG over time
    customers = [0]  # month 0
    revenue = [0]
    new_customers_list = []

    for m in range(1, months + 1):
        # Growth accelerator: PLG effects compound
        plg_factor = min(1.0, m / 18)  # Ramps up over 18 months

        # Current customers who can refer
        current = customers[-1]

        # New from referrals
        referrals = int(current * vc * plg_factor / 12)  # per month avg

        # New from self-serve
        self_serve_new = int(base * self_serve * plg_factor)

        # New from founder/sales (declines as PLG takes over)
        founder_new = max(1, int(base * (1 - self_serve * plg_factor)))

        # Partner batch drops
        partner_new = 0
        if "partner_months" in g and m in g["partner_months"]:
            partner_new = g["partner_batch_size"]

        total_new = referrals + self_serve_new + founder_new + partner_new
        new_customers_list.append(total_new)

        # Apply churn + add new
        next_cust = int(current * (1 - churn) + total_new)
        customers.append(next_cust)
        revenue.append(int(next_cust * arpu))

    return {
        "customers": customers[1:],  # month 1-36
        "revenue": revenue[1:],
        "new_per_month": new_customers_list,
        "final_customers": customers[-1],
        "final_mrr": revenue[-1],
        "final_arr": revenue[-1] * 12,
        "total_revenue_36mo": sum(revenue[1:]),
    }

# ============================================================
# REPORT
# ============================================================

def run():
    print("=" * 72)
    print(" WAYPOINT OS — v6: PLG + Retention + Churn Feedback")
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 72)

    print(f"\n📋 COSTS")
    print(f"   Fixed: ₹{FIXED:,}/mo | Variable: ₹{VAR}/cust/mo | One-time: ₹{ONE_TIME:,}")

    print(f"\n📊 PLG GROWTH MODES")
    for key, g in GROWTH_MODES.items():
        print(f"   {g['label']:>30}: {g['monthly_new_base']} base/mo"
              f" | viral: {g['viral_coefficient']:.0%}"
              f" | self-serve: {g['self_serve_pct']:.0%}"
              + (f" | partners: yes" if "partner_batch_size" in g else ""))

    print(f"\n📈 GROWTH COMPARISON (at Pricing Scenario C: ₹4,500 ARPU, 3% churn)")
    print(f"{'Growth Mode':>30} {'Y1 Cust':>8} {'Y3 Cust':>8} {'Y3 MRR':>10} {'Y3 ARR':>12} {'ARR($)':>9} {'36mo Rev':>14}")
    print("-" * 95)

    for key in ["founder-led", "organic-plg", "host-partner", "full-plg"]:
        r = simulate(key, "C: Base + seats + 1 add-on")
        y3_mrr = r["revenue"][35]
        y3_arr = y3_mrr * 12
        y1_cust = r["customers"][11] if len(r["customers"]) > 11 else 0
        print(f"{GROWTH_MODES[key]['label']:>30}"
              f" {y1_cust:>8} {r['final_customers']:>8}"
              f" ₹{y3_mrr:>8,} ₹{y3_arr:>10,} ${y3_arr/USD_RATE:>7,}"
              f" ₹{r['total_revenue_36mo']:>11,}")

    print(f"\n💲 PRICING SCENARIO COMPARISON (at Full PLG growth)")
    print(f"{'Pricing':>32} {'Y3 Cust':>8} {'Y3 MRR':>10} {'Y3 ARR':>12} {'ARR($)':>9} {'LTV':>10}")
    print("-" * 86)

    for p in PRICING_SCENARIOS:
        r = simulate("full-plg", p["name"])
        reduced_churn = (p["churn_pct"] / 100) * (1 - RETENTION_CHURN_REDUCTION)
        ltv = int((p["arpu"] - VAR) / reduced_churn)
        effective_churn = (p["churn_pct"] / 100) * (1 - RETENTION_CHURN_REDUCTION)
        print(f"{p['name']:>32} {r['final_customers']:>8}"
              f" ₹{r['final_mrr']:>8,} ₹{r['final_arr']:>10,} ${r['final_arr']/USD_RATE:>7,}"
              f" {effective_churn*100:>5.1f}% ₹{ltv:>8,}")

    print(f"\n🔍 YEAR-BY-YEAR (Full PLG / Pricing C)")
    r = simulate("full-plg", "C: Base + seats + 1 add-on")
    print(f"{'Year':>6} {'New Cust':>10} {'Total Cust':>12} {'MRR':>10} {'ARR':>12}")
    print("-" * 52)
    for yr in range(3):
        start_m = yr * 12
        end_m = start_m + 11
        y_cust = r["customers"][end_m]
        y_new = sum(r["new_per_month"][start_m:end_m+1])
        y_mrr = r["revenue"][end_m]
        y_arr = y_mrr * 12
        print(f"  Year {yr+1}: {y_new:>8} {y_cust:>10} ₹{y_mrr:>7,} ₹{y_arr:>9,}")

    total_rev = r["total_revenue_36mo"]
    total_cost = FIXED * 36 + sum(r["customers"][m] * VAR for m in range(36)) + ONE_TIME
    print(f"\n💰 PROFITABILITY")
    print(f"   36mo Revenue: ₹{total_rev:>12,} (${total_rev/USD_RATE:>9,})")
    print(f"   36mo Cost:    ₹{total_cost:>12,} (${total_cost/USD_RATE:>9,})")
    print(f"   36mo Profit:  ₹{total_rev - total_cost:>12,} (${(total_rev - total_cost)/USD_RATE:>9,})")

    be_mo = None
    cum = -ONE_TIME
    for m in range(36):
        cost = FIXED + r["customers"][m] * VAR
        net = r["revenue"][m] - cost
        cum += net
        if cum >= 0 and be_mo is None:
            be_mo = m + 1
            print(f"\n   Breakeven: Month {be_mo} (cumulative cash positive)")
            print(f"   Customers at breakeven: {r['customers'][m]}")

if __name__ == "__main__":
    run()
