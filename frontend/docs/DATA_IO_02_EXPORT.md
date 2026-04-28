# Data Import, Export & Migration — Export System

> Research document for data export, report generation, format options, and scheduled exports.

---

## Key Questions

1. **What data do agents and admins need to export regularly?**
2. **What export formats serve different use cases?**
3. **How do we handle large exports without timeout?**
4. **What's the scheduled export model?**
5. **How do exports integrate with accounting and compliance systems?**

---

## Research Areas

### Export Model

```typescript
interface DataExport {
  exportId: string;
  name: string;
  type: ExportType;
  format: ExportFormat;
  filters: ExportFilter[];
  columns: ExportColumn[];
  sortBy: string;
  status: ExportStatus;
  rowCount: number;
  fileSize: string;
  downloadUrl?: string;
  expiresAt?: Date;
  createdAt: Date;
  createdBy: string;
}

type ExportType =
  | 'customers'                      // Customer directory
  | 'bookings'                       // Booking ledger
  | 'payments'                       // Payment records
  | 'trips'                          // Trip summaries
  | 'suppliers'                      // Supplier directory
  | 'invoices'                       // Invoice register
  | 'commission'                     // Commission statements
  | 'gst_report'                     // GST filing data
  | 'tcs_report'                     // TCS collection report
  | 'financial_summary'              // P&L, revenue summary
  | 'agent_performance'              // Agent productivity report
  | 'customer_feedback'              // Reviews and ratings
  | 'supplier_performance'           // Supplier scorecards
  | 'audit_trail'                    // Audit log export
  | 'custom';                        // User-defined export

type ExportFormat =
  | 'xlsx'                           // Excel (most popular in India)
  | 'csv'                            // CSV (system integration)
  | 'pdf'                            // PDF (reports, invoices)
  | 'json'                           // JSON (API, backup)
  | 'xml'                            // XML (legacy system integration)
  | 'ofx'                            // OFX (accounting software)
  | 'gst_chn';                       // GST portal compatible format

// Export use cases:
// Accountant: "Export all payments for March in Excel for GST filing"
// Agent: "Export my customer list for follow-up calls"
// Admin: "Export booking summary for quarterly business review"
// Compliance: "Export audit trail for the last 6 months"
// Owner: "Export P&L report for investor meeting"
```

### Export Configuration

```typescript
interface ExportColumn {
  field: string;
  header: string;
  width?: number;
  format?: ColumnFormat;
  aggregation?: AggregationType;
}

type ColumnFormat =
  | { type: 'date'; format: string }
  | { type: 'currency'; symbol: string; decimals: number }
  | { type: 'number'; decimals: number; thousandsSeparator: boolean }
  | { type: 'percentage'; decimals: number }
  | { type: 'phone'; countryCode: string }
  | { type: 'boolean'; trueLabel: string; falseLabel: string }
  | { type: 'enum'; mapping: Record<string, string> };

// Example: Payment export for GST filing
// Columns:
// - Invoice Number (text)
// - Invoice Date (date: DD/MM/YYYY)
// - Customer Name (text)
// - Customer GSTIN (text)
// - SAC Code (text) — Service Accounting Code for travel
// - Taxable Amount (currency: ₹, 2 decimals)
// - CGST (currency: ₹, 2 decimals)
// - SGST (currency: ₹, 2 decimals)
// - IGST (currency: ₹, 2 decimals)
// - Total Invoice Amount (currency: ₹, 2 decimals)
// - Payment Status (enum: {"paid": "Paid", "pending": "Pending"})

interface ExportFilter {
  field: string;
  operator: 'eq' | 'neq' | 'in' | 'between' | 'gt' | 'lt' | 'contains';
  value: unknown;
}

// Common filter presets:
// "This month" → payment.date BETWEEN [2026-04-01, 2026-04-30]
// "My customers" → customer.agent_id = current_agent
// "GST filing Q4" → invoice.date BETWEEN [2026-01-01, 2026-03-31]
// "Overdue payments" → payment.due_date < today AND payment.status = 'pending'
```

### Scheduled Exports

```typescript
interface ScheduledExport {
  scheduleId: string;
  name: string;
  exportConfig: DataExport;
  schedule: ExportSchedule;
  recipients: ExportRecipient[];
  lastRunAt?: Date;
  nextRunAt: Date;
  active: boolean;
}

interface ExportSchedule {
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  dayOfWeek?: number;                // For weekly
  dayOfMonth?: number;               // For monthly
  time: string;                      // "06:00" (run early morning)
  timezone: string;
}

interface ExportRecipient {
  type: 'email' | 'slack' | 'sftp' | 'google_drive' | 'whatsapp';
  address: string;                   // Email, channel, path
  format: ExportFormat;
}

// Scheduled export examples:
// Daily booking summary → Email to operations team at 7 AM
// Weekly agent performance → Email to team lead every Monday
// Monthly GST report → Email to accountant on 1st of each month
// Quarterly financial summary → Email + Google Drive for owner
// Daily payment reconciliation → SFTP to accounting system at midnight

// Delivery methods:
// Email: Attached file (max 25MB) or download link (for larger files)
// Slack: Post to channel with summary + download link
// SFTP: Upload to remote server for accounting system ingestion
// Google Drive: Upload to shared folder
// WhatsApp: Summary text with download link (not the file itself)
```

### Report-Grade Exports

```typescript
interface ReportExport {
  reportId: string;
  template: ReportTemplate;
  parameters: ReportParameter[];
  output: ReportOutput;
}

interface ReportTemplate {
  name: string;
  description: string;
  sections: ReportSection[];
  pageLayout: PageLayout;
  header: ReportHeader;
  footer: ReportFooter;
}

// Report-grade export features:
// - Formatted headers and footers with company branding
// - Page numbers and section breaks
// - Charts and visualizations embedded
// - Summary tables with subtotals
// - Conditional formatting (red for overdue, green for paid)
// - Print-optimized layout (A4, landscape)
// - Password protection for sensitive reports

// India-specific export requirements:
// GST Return (GSTR-1 format):
//   - Specific column order and formatting
//   - SAC codes for travel services (9985 series)
//   - Separate sections for B2B and B2C invoices
//   - Must match portal upload format
//
// TCS Report:
//   - Collected under section 206C(1G) for overseas travel
//   - 5% on amounts above ₹7L (LRS)
//   - PAN-wise breakdown required
//   - Quarterly filing with income tax portal
//
// Tourism Ministry report (for licensed agencies):
//   - Monthly tourist statistics
//   - Foreign exchange earnings
//   - Domestic vs. international breakdown
```

---

## Open Problems

1. **Export consistency** — The same export run at different times may show different data (bookings updated between runs). Need point-in-time snapshots for financial exports.

2. **Format compatibility** — Excel versions differ (xlsx vs xls), date formats vary by locale, number formatting is inconsistent. Need strict format specifications.

3. **Sensitive data handling** — Exports contain PII (names, phones, passport numbers). Need access control, encryption, and expiry on download links.

4. **Large export performance** — Exporting 100K+ bookings with joins to customers, payments, and suppliers. Need query optimization and streaming output.

5. **Export auditability** — Who exported what and when? Financial data exports should be logged for compliance. Need export audit trail.

---

## Next Steps

- [ ] Design export pipeline with streaming for large datasets
- [ ] Build GST-compatible export templates
- [ ] Create scheduled export system with multi-format delivery
- [ ] Design export access control and audit logging
- [ ] Study export UX (Stripe exports, QuickBooks reports, Zoho Books)
