# Travel Finance & Accounting — Financial Reporting

> Research document for P&L statements, balance sheets, cash flow statements, tax reports, and financial dashboards.

---

## Key Questions

1. **What financial reports does a travel agency need?**
2. **How do we generate P&L, balance sheet, and cash flow statements?**
3. **What tax reports are required (GST, TDS, TCS, income tax)?**
4. **How do we provide real-time financial dashboards?**
5. **What reporting formats and export capabilities are needed?**

---

## Research Areas

### Financial Statements

```typescript
interface FinancialStatements {
  period: DateRange;
  profitAndLoss: ProfitAndLoss;
  balanceSheet: BalanceSheet;
  cashFlowStatement: CashFlowStatement;
  notes: FinancialNotes;
}

interface ProfitAndLoss {
  revenue: RevenueSection;
  costOfSales: CostSection;
  grossProfit: Money;
  operatingExpenses: ExpenseSection;
  operatingProfit: Money;             // EBITDA
  depreciation: Money;
  interestExpense: Money;
  profitBeforeTax: Money;
  taxExpense: Money;
  netProfit: Money;
}

// P&L Statement — Travel Agency example (Monthly):
// ┌──────────────────────────────────────────┐
// │  Profit & Loss — April 2026              │
// │                                          │
// │  REVENUE                                 │
// │  Tour Package Revenue         ₹15,00,000 │
// │  Air Ticket Commission          ₹3,50,000 │
// │  Visa Processing Fees            ₹1,20,000 │
// │  Insurance Commission              ₹80,000 │
// │  Forex Commission                  ₹45,000 │
// │  Other Revenue                     ₹30,000 │
// │  Total Revenue                 ₹21,25,000 │
// │                                          │
// │  COST OF SALES                           │
// │  Hotel Payments               ₹8,50,000 │
// │  Airline Payments (BSP)       ₹4,20,000 │
// │  Transport Payments            ₹2,10,000 │
// │  Activity Payments             ₹1,05,000 │
// │  Insurance Premiums              ₹60,000 │
// │  Total Cost of Sales          ₹16,45,000 │
// │                                          │
// │  GROSS PROFIT                  ₹4,80,000 │
// │  Gross Margin: 22.6%                     │
// │                                          │
// │  OPERATING EXPENSES                      │
// │  Staff Salaries               ₹2,40,000 │
// │  Agent Commissions              ₹72,000 │
// │  Office Rent                    ₹60,000 │
// │  Marketing & Advertising       ₹45,000 │
// │  Technology & Software          ₹25,000 │
// │  Communication                  ₹12,000 │
// │  Travel & Conveyance            ₹18,000 │
// │  Professional Fees (CA)         ₹15,000 │
// │  Depreciation                   ₹20,000 │
// │  Total Operating Expenses    ₹5,07,000 │
// │                                          │
// │  OPERATING PROFIT (LOSS)       -₹27,000 │
// │  Operating Margin: -1.3% ⚠️             │
// │                                          │
// │  Other Income                             │
// │  Interest Income                  ₹5,000 │
// │                                          │
// │  PROFIT BEFORE TAX             -₹22,000 │
// │  Tax Expense                        ₹0 │
// │                                          │
// │  NET PROFIT (LOSS)            -₹22,000 │
// │  Net Margin: -1.0% ⚠️                   │
// │                                          │
// │  ⚠️ April was loss-making. Cause:        │
// │  Low bookings (off-season start)         │
// │  with high fixed costs.                  │
// │  Recommendation: Reduce marketing spend, │
// │  focus on summer international bookings. │
// └──────────────────────────────────────────┘

interface BalanceSheet {
  assets: AssetSection;
  liabilities: LiabilitySection;
  equity: EquitySection;
}

// Balance Sheet — Travel Agency example:
//
// ASSETS
// Current Assets:
//   Cash & Bank              ₹12,45,000
//   Customer Receivables      ₹3,20,000
//   Supplier Refunds Due      ₹1,50,000
//   Commission Receivable       ₹45,000
//   TDS Receivable              ₹28,000
//   GST Input Credit           ₹1,20,000
//   Advance to Suppliers      ₹4,50,000
//   Prepaid Expenses            ₹35,000
//   Total Current Assets     ₹23,93,000
//
// Fixed Assets:
//   Office Furniture           ₹1,50,000
//   Computers & Equipment      ₹2,40,000
//   Less: Depreciation        (₹1,20,000)
//   Net Fixed Assets           ₹2,70,000
//
// TOTAL ASSETS              ₹26,63,000
//
// LIABILITIES
// Current Liabilities:
//   Supplier Payables          ₹5,80,000
//   Customer Advances          ₹6,50,000
//   GST Payable                  ₹95,000
//   TCS Payable                  ₹42,000
//   TDS Payable                  ₹18,000
//   EPF Payable                  ₹22,000
//   Professional Tax Payable      ₹4,000
//   Total Current Liabilities ₹13,11,000
//
// EQUITY
//   Owner's Capital           ₹10,00,000
//   Retained Earnings          ₹3,52,000
//   Total Equity              ₹13,52,000
//
// TOTAL LIABILITIES + EQUITY ₹26,63,000
//
// Key ratios:
// Current ratio: 23.93L / 13.11L = 1.83 (healthy, > 1.5)
// Quick ratio: (23.93L - 4.5L) / 13.11L = 1.48 (acceptable)
// Debt-to-equity: 13.11L / 13.52L = 0.97 (reasonable)
// Working capital: 23.93L - 13.11L = ₹10.82L (positive)
```

### Tax Reporting Suite

```typescript
interface TaxReporting {
  gst: GSTReports;
  tds: TDSReports;
  tcs: TCSReports;
  incomeTax: IncomeTaxReports;
}

interface GSTReports {
  gstr1Data: GSTR1Report;             // Outward supplies
  gstr3bData: GSTR3BReport;           // Summary return
  gstr9Data: GSTR9Report;             // Annual return
  itcReport: ITCReport;               // Input tax credit summary
  hsnSummary: HSNSummary;             // HSN-wise summary
}

// GST report generation:
//
// GSTR-1 (Outward Supplies) — Auto-generated:
// B2B Invoices:
//   Invoice# | Customer GSTIN | Taxable | CGST | SGST | IGST | Total
//   INV-101  | 27AABCU9603R1  | ₹48,000 | ₹1,200 | ₹1,200 | - | ₹50,400
//   INV-102  | 07AAGCS2345B1  | ₹95,000 | - | - | ₹4,750 | ₹99,750
//
// B2C Small:
//   Rate | Taxable | CGST | SGST | IGST | Total
//   5%   | ₹8,50,000 | ₹21,250 | ₹21,250 | - | ₹8,92,500
//   18%  | ₹1,20,000 | ₹10,800 | ₹10,800 | - | ₹1,41,600
//
// Credit Notes:
//   CN-001 | Refund for cancellation | -₹27,000 | -₹675 | -₹675 | - | -₹28,350
//
// Summary:
// Total taxable value: ₹10,86,000
// Total CGST: ₹32,575
// Total SGST: ₹32,575
// Total IGST: ₹4,750
// Total tax: ₹69,900

interface TDSReports {
  sectionWise: TDSSectionReport[];
  quarterlyReturn: TDSQuarterlyData;
  certificates: TDSCertificate[];
}

// TDS (Tax Deducted at Source) in travel:
// Section 194C: Payment to contractors (transport, event management)
//   TDS @ 1% (if PAN available), 2% if individual/HUF
//   Threshold: ₹30,000 single payment, ₹1,00,000 annual
//
// Section 194H: Commission payment to agents
//   TDS @ 5% on commission > ₹15,000
//
// Section 194J: Professional fees (visa processing, consulting)
//   TDS @ 10% on fees > ₹30,000
//
// Example:
// Agency pays ₹50,000 commission to a sub-agent
// TDS @ 5%: ₹2,500
// Net payment: ₹47,500
// TDS deposited by 7th of following month
// TDS certificate (Form 16A) issued quarterly

interface TCSReports {
  sectionWise: TCSSectionReport[];
  monthlyDeposit: TCSMonthlyData;
  quarterlyReturn: TCSQuarterlyData;
}

// TCS reports generated per month:
// Overseas tour packages (Section 206C(1G)):
// Customer | PAN | Amount | TCS @ 5% | Collected Date
// Rajesh S | ABCP... | ₹3,50,000 | ₹7,500 | Apr 5
// Priya M  | MNPQ... | ₹2,80,000 | ₹0 | Apr 12 (below threshold)
// Total TCS collected: ₹7,500
// TCS deposited: By May 7, 2026
// TCS certificate (Form 27D): Issued by May 22
```

### Financial Dashboards

```typescript
interface FinancialDashboard {
  agencyId: string;
  period: DateRange;
  kpis: FinancialKPI[];
  charts: FinancialChart[];
  alerts: FinancialAlert[];
}

interface FinancialKPI {
  name: string;
  value: Money | number;
  target: Money | number;
  trend: 'up' | 'down' | 'stable';
  changeFromLastPeriod: number;       // %
}

// Financial KPI dashboard:
// ┌──────────────────────────────────────────────────┐
// │  Finance Dashboard — FY 2026-27 YTD (Apr)         │
// │                                                    │
// │  Revenue           ₹21.25L  Target: ₹22L    ↓ 3%  │
// │  Gross Margin      22.6%    Target: 25%     ↓ 2.4% │
// │  Net Margin        -1.0%    Target: 8%      ↓ 9% ⚠️│
// │  Cash Position     ₹12.45L  Target: ₹10L    ↑ 24%  │
// │  Receivables       ₹3.2L    Target: <₹2L   ↑ 60% ⚠️│
// │  Payables          ₹5.8L    Target: <₹5L   ↑ 16%  │
// │                                                    │
// │  Revenue by Service:                               │
// │  ██████████████████████░░░ Packages 71%            │
// │  ████████░░░░░░░░░░░░░░░ Flights   16%             │
// │  ████░░░░░░░░░░░░░░░░░░░ Visa       6%             │
// │  ███░░░░░░░░░░░░░░░░░░░░ Insurance  4%             │
// │  █░░░░░░░░░░░░░░░░░░░░░░ Other      3%             │
// │                                                    │
// │  Monthly Revenue Trend:                             │
// │  Jan: ₹18L  Feb: ₹22L  Mar: ₹28L                  │
// │  Apr: ₹21L  May: (forecast ₹15L) ⚠️               │
// │                                                    │
// │  Alerts:                                            │
// │  ⚠️ April was loss-making. Off-season effect.       │
// │  ⚠️ Receivables growing — follow up on 3 bookings. │
// │  📋 GST return due in 8 days.                       │
// │  📋 BSP settlement ₹3.2L due Thursday.             │
// └──────────────────────────────────────────────────┘

// Report scheduling:
// Daily: Cash position, bank balance, payment alerts
// Weekly: Revenue summary, booking P&L, BSP reconciliation
// Monthly: Full P&L, balance sheet, GST summary, agent commissions
// Quarterly: TDS/TCS returns, audit preparation, financial review
// Annually: Full financial statements, tax filing support, budget planning
//
// Export formats:
// PDF: Formatted reports (P&L, balance sheet, tax summaries)
// Excel: Detailed data with formulas (trial balance, ledger)
// CSV: Raw data for import into Tally/Zoho Books
// JSON: API-accessible data for custom integrations
// XBRL: For listed companies (regulatory filing format)
```

---

## Open Problems

1. **Real-time vs. period accounting** — Travel bookings span weeks/months. Revenue isn't "earned" until trip completes, but cash is received at booking. Accrual vs. cash basis creates different pictures.

2. **Inter-company transactions** — Agencies with multiple branches or subsidiaries need inter-company elimination for consolidated reporting.

3. **Audit trail completeness** — Every financial number in reports must trace back to source transactions. If data enters through manual adjustments, audit trail breaks.

4. **Comparative reporting** — Year-over-year comparison is complicated by changing service mix, pricing, and seasonality. Simple YoY revenue comparison can be misleading.

5. **Multi-entity consolidation** — Agencies operating multiple brands or locations need per-entity and consolidated reporting with inter-company adjustments.

---

## Next Steps

- [ ] Build financial statement generator (P&L, balance sheet, cash flow)
- [ ] Create tax reporting suite (GST, TDS, TCS) with auto-generation
- [ ] Design real-time financial dashboard with KPIs and alerts
- [ ] Build report scheduling with multiple export formats
- [ ] Study financial reporting systems (TallyPrime, Zoho Books, MProfit, QuickBooks India)
