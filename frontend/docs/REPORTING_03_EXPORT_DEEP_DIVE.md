# Reporting Module — Export Deep Dive

> Excel, CSV, PDF export formats, template-based reports, and download management

---

## Document Overview

**Series:** Reporting Module | **Document:** 3 of 4 | **Focus:** Export Formats

**Related Documents:**
- [01: Technical Deep Dive](./REPORTING_01_TECHNICAL_DEEP_DIVE.md) — Report engine architecture
- [02: UX/UI Deep Dive](./REPORTING_02_UX_UI_DEEP_DIVE.md) — Report builder interface
- [04: Scheduling Deep Dive](./REPORTING_04_SCHEDULING_DEEP_DIVE.md) — Automated reports

---

## Table of Contents

1. [Export Architecture](#1-export-architecture)
2. [CSV Export](#2-csv-export)
3. [Excel Export](#3-excel-export)
4. [PDF Export](#4-pdf-export)
5. [Template-Based Reports](#5-template-based-reports)
6. [Async Export & Job Queue](#6-async-export--job-queue)
7. [Download Management](#7-download-management)

---

## 1. Export Architecture

### 1.1 System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          EXPORT ARCHITECTURE                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                         EXPORT REQUEST                                │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Report Data  │  │ Format       │  │ Options      │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  └──────────────────────────────┬───────────────────────────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────▼───────────────────────────────────────┐ │
│  │                       EXPORT ORCHESTRATOR                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Validation   │  │ Format Check │  │ Size Est.    │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │           Route to appropriate exporter              │             │ │
│  │  │  • Small data (< 1000 rows): Sync export             │             │ │
│  │  │  • Large data (> 1000 rows): Async job queue         │             │ │
│  │  └──────┬──────────────────────────────────────────────┘             │ │
│  └─────────┼──────────────────────────────────────────────────────────┘ │
│            │                                                           │
│    ┌───────┴────────┬────────────────┬────────────────┐                │
│    ▼                ▼                ▼                ▼                │
│  ┌────────┐    ┌────────┐      ┌────────┐      ┌────────┐              │
│  │  CSV   │    │ EXCEL  │      │  PDF   │      │TEMPLATE│              │
│  │Exporter│    │Exporter│      │Exporter│      │Exporter│              │
│  └───┬────┘    └───┬────┘      └───┬────┘      └───┬────┘              │
│      │             │                │                │                  │
│      └─────────────┴────────────────┴────────────────┘                  │
│                             │                                           │
│  ┌──────────────────────────▼───────────────────────────────────────┐   │
│  │                       STORAGE LAYER                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ S3 / GCS     │  │ Local Cache  │  │ CDN (Public) │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Export Request Model

```typescript
// Export request interface
interface ExportRequest {
  reportId: string;
  format: ExportFormat;
  options: ExportOptions;
  userId: string;
  agencyId: string;
}

type ExportFormat = 'csv' | 'xlsx' | 'pdf';

interface ExportOptions {
  // Data options
  limit?: number;
  offset?: number;
  includeHeaders?: boolean;
  includeTotals?: boolean;

  // Formatting options
  dateFormat?: string;
  numberFormat?: string;
  currency?: string;

  // Excel-specific
  sheetName?: string;
  freezeHeader?: boolean;
  autoFilter?: boolean;
  columnWidths?: 'auto' | number[];

  // PDF-specific
  template?: string;
  orientation?: 'portrait' | 'landscape';
  pageSize?: 'A4' | 'Letter' | 'Legal';
  fitToPage?: boolean;
  includeCharts?: boolean;

  // Delivery options
  filename?: string;
  email?: boolean;
  emailRecipients?: string[];
}

// Export result
interface ExportResult {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  format: ExportFormat;
  filename: string;
  url?: string;
  expiresAt?: number;
  size?: number;
  rowCount?: number;
  error?: string;
}
```

### 1.3 Export Orchestrator

```typescript
// Export orchestrator
class ExportOrchestrator {
  private exporters: Map<ExportFormat, Exporter>;
  private jobQueue: ExportJobQueue;
  private storage: ExportStorage;

  constructor() {
    this.exporters = new Map([
      ['csv', new CSVExporter()],
      ['xlsx', new ExcelExporter()],
      ['pdf', new PDFExporter()],
    ]);
    this.jobQueue = new ExportJobQueue();
    this.storage = new ExportStorage();
  }

  async export(request: ExportRequest): Promise<ExportResult> {
    // Validate request
    this.validateRequest(request);

    // Get report data
    const data = await this.fetchReportData(request);

    // Estimate size
    const estimatedSize = this.estimateSize(data, request.format);

    // Route to sync or async
    if (estimatedSize < 100000 && data.rows.length < 1000) {
      return await this.exportSync(data, request);
    } else {
      return await this.exportAsync(data, request);
    }
  }

  private async exportSync(
    data: QueryResult,
    request: ExportRequest
  ): Promise<ExportResult> {
    const exporter = this.exporters.get(request.format)!;
    const buffer = await exporter.export(data, request.options);
    const filename = this.generateFilename(request);

    // Store file
    const url = await this.storage.store(filename, buffer, {
      contentType: this.getContentType(request.format),
      expiresIn: 86400, // 24 hours
    });

    return {
      jobId: uuid(),
      status: 'completed',
      format: request.format,
      filename,
      url,
      expiresAt: Date.now() + 86400000,
      size: buffer.length,
      rowCount: data.rows.length,
    };
  }

  private async exportAsync(
    data: QueryResult,
    request: ExportRequest
  ): Promise<ExportResult> {
    const jobId = uuid();

    // Enqueue job
    await this.jobQueue.add({
      id: jobId,
      type: 'export',
      data,
      format: request.format,
      options: request.options,
      userId: request.userId,
      agencyId: request.agencyId,
    });

    return {
      jobId,
      status: 'pending',
      format: request.format,
      filename: this.generateFilename(request),
    };
  }

  private validateRequest(request: ExportRequest): void {
    if (!this.exporters.has(request.format)) {
      throw new Error(`Unsupported format: ${request.format}`);
    }

    // Check user permissions
    // Check rate limits
  }

  private async fetchReportData(request: ExportRequest): Promise<QueryResult> {
    const engine = new ReportEngine();
    return await engine.executeReportById(request.reportId, {
      limit: request.options.limit,
      offset: request.options.offset,
    });
  }

  private estimateSize(data: QueryResult, format: ExportFormat): number {
    const bytesPerRow = {
      csv: 100,
      xlsx: 200,
      pdf: 500,
    };
    return data.rows.length * bytesPerRow[format];
  }

  private generateFilename(request: ExportRequest): string {
    const timestamp = new Date().toISOString().split('T')[0];
    const ext = this.getFileExtension(request.format);
    return `report_${request.reportId}_${timestamp}${ext}`;
  }

  private getContentType(format: ExportFormat): string {
    const types = {
      csv: 'text/csv',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    };
    return types[format];
  }

  private getFileExtension(format: ExportFormat): string {
    return `.${format}`;
  }
}
```

---

## 2. CSV Export

### 2.1 CSV Exporter Implementation

```typescript
// CSV exporter
class CSVExporter implements Exporter {
  async export(data: QueryResult, options: ExportOptions = {}): Promise<Buffer> {
    const rows: string[][] = [];

    // Add headers
    if (options.includeHeaders !== false) {
      rows.push(data.columns.map(col => col.displayName || col.name));
    }

    // Add data rows
    for (const row of data.rows) {
      rows.push(data.columns.map(col => this.formatValue(row[col.name], col, options)));
    }

    // Add totals row if requested
    if (options.includeTotals) {
      rows.push(this.calculateTotals(data, options));
    }

    // Convert to CSV string
    const csv = this.stringify(rows);

    return Buffer.from(csv, 'utf-8');
  }

  private formatValue(value: any, column: Column, options: ExportOptions): string {
    if (value === null || value === undefined) {
      return '';
    }

    // Apply formatting based on column type
    switch (column.dataType) {
      case 'number':
        return this.formatNumber(value, column, options);

      case 'date':
        return this.formatDate(value, options);

      case 'boolean':
        return value ? 'Yes' : 'No';

      default:
        return String(value);
    }
  }

  private formatNumber(value: number, column: Column, options: ExportOptions): string {
    const formatted = value.toLocaleString('en-US', {
      minimumFractionDigits: column.decimals || 2,
      maximumFractionDigits: column.decimals || 2,
    });

    // Escape if contains comma
    if (formatted.includes(',')) {
      return `"${formatted}"`;
    }

    return formatted;
  }

  private formatDate(value: Date | string, options: ExportOptions): string {
    const date = value instanceof Date ? value : new Date(value);
    const format = options.dateFormat || 'YYYY-MM-DD';

    if (format === 'YYYY-MM-DD') {
      return date.toISOString().split('T')[0];
    }

    return date.toLocaleDateString();
  }

  private calculateTotals(data: QueryResult, options: ExportOptions): string[] {
    const totals: string[] = [];

    for (const column of data.columns) {
      if (column.type === 'measure') {
        const sum = data.rows.reduce((acc, row) => acc + (row[column.name] || 0), 0);
        totals.push(this.formatValue(sum, column, options));
      } else {
        totals.push('Total');
      }
    }

    return totals;
  }

  private stringify(rows: string[][]): string {
    return rows.map(row =>
      row.map(cell => {
        // Escape and quote cells containing quotes, commas, or newlines
        if (cell.includes('"') || cell.includes(',') || cell.includes('\n')) {
          return `"${cell.replace(/"/g, '""')}"`;
        }
        return cell;
      }).join(',')
    ).join('\n');
  }
}
```

### 2.2 CSV Options UI

```typescript
// CSV export configuration UI
interface CSVExportOptionsProps {
  onExport: (options: ExportOptions) => void;
  onCancel: () => void;
}

export const CSVExportOptions: React.FC<CSVExportOptionsProps> = ({
  onExport,
  onCancel,
}) => {
  const [options, setOptions] = useState<ExportOptions>({
    includeHeaders: true,
    includeTotals: false,
    dateFormat: 'YYYY-MM-DD',
    numberFormat: '1,234.56',
  });

  return (
    <Dialog>
      <DialogTitle>Export as CSV</DialogTitle>

      <DialogContent>
        <FormField label="Include Headers">
          <Toggle
            checked={options.includeHeaders}
            onChange={(includeHeaders) => setOptions({ ...options, includeHeaders })}
          />
        </FormField>

        <FormField label="Include Totals Row">
          <Toggle
            checked={options.includeTotals}
            onChange={(includeTotals) => setOptions({ ...options, includeTotals })}
          />
        </FormField>

        <FormField label="Date Format">
          <Select
            value={options.dateFormat}
            onChange={(dateFormat) => setOptions({ ...options, dateFormat })}
          >
            <option value="YYYY-MM-DD">2026-04-25</option>
            <option value="DD/MM/YYYY">25/04/2026</option>
            <option value="MM/DD/YYYY">04/25/2026</option>
            <option value="DD-MM-YYYY">25-04-2026</option>
          </Select>
        </FormField>

        <FormField label="Number Format">
          <Select
            value={options.numberFormat}
            onChange={(numberFormat) => setOptions({ ...options, numberFormat })}
          >
            <option value="1,234.56">1,234.56</option>
            <option value="1.234,56">1.234,56</option>
            <option value="1234.56">1234.56</option>
          </Select>
        </FormField>

        <FormField label="Filename">
          <Input
            value={options.filename || ''}
            onChange={(filename) => setOptions({ ...options, filename })}
            placeholder="report.csv"
          />
        </FormField>
      </DialogContent>

      <DialogActions>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onExport(options)}>Export</Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 3. Excel Export

### 3.1 Excel Exporter Implementation

```typescript
import ExcelJS from 'exceljs';

// Excel exporter
class ExcelExporter implements Exporter {
  async export(data: QueryResult, options: ExportOptions = {}): Promise<Buffer> {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet(options.sheetName || 'Report');

    // Set column widths
    if (options.columnWidths && Array.isArray(options.columnWidths)) {
      worksheet.columns = options.columnWidths.map(width => ({ width }));
    } else if (options.columnWidths === 'auto') {
      worksheet.columns = data.columns.map(col => ({
        key: col.name,
        width: Math.max(col.displayName.length, 15),
      }));
    }

    // Define header style
    const headerStyle = {
      font: { bold: true, color: { argb: 'FFFFFFFF' } },
      fill: {
        type: 'pattern' as const,
        pattern: 'solid',
        fgColor: { argb: 'FF4472C4' },
      },
      border: {
        top: { style: 'thin' },
        left: { style: 'thin' },
        bottom: { style: 'thin' },
        right: { style: 'thin' },
      },
    };

    // Add headers
    if (options.includeHeaders !== false) {
      const headerRow = worksheet.addRow(
        data.columns.map(col => col.displayName || col.name)
      );
      headerRow.eachCell(cell => {
        cell.style = headerStyle;
      });
    }

    // Add data rows
    const dataStartRow = options.includeHeaders !== false ? 2 : 1;

    for (const row of data.rows) {
      const excelRow = worksheet.addRow(
        data.columns.map(col => this.formatCellValue(row[col.name], col, options))
      );

      // Apply number formats
      excelRow.eachCell((cell, colNumber) => {
        const column = data.columns[colNumber - 1];
        cell.numFmt = this.getNumberFormat(column, options);
      });
    }

    // Add totals row if requested
    if (options.includeTotals) {
      const totalsRow = worksheet.addRow(
        this.calculateTotals(data, options)
      );
      totalsRow.font = { bold: true };
      totalsRow.fill = {
        type: 'pattern' as const,
        pattern: 'solid',
        fgColor: { argb: 'FFE7E6E6' },
      };
    }

    // Freeze header row
    if (options.freezeHeader !== false && options.includeHeaders !== false) {
      worksheet.views = [{ state: 'frozen', xSplit: 0, ySplit: 1 }];
    }

    // Add auto filter
    if (options.autoFilter !== false && options.includeHeaders !== false) {
      worksheet.autoFilter = {
        from: 'A1',
        to: `${String.fromCharCode(64 + data.columns.length)}${data.rows.length + 1}`,
      };
    }

    // Add conditional formatting for measures
    this.addConditionalFormatting(worksheet, data, dataStartRow);

    // Generate buffer
    const buffer = await workbook.xlsx.writeBuffer();
    return Buffer.from(buffer);
  }

  private formatCellValue(value: any, column: Column, options: ExportOptions): any {
    if (value === null || value === undefined) {
      return '';
    }

    if (column.dataType === 'date') {
      return new Date(value);
    }

    return value;
  }

  private getNumberFormat(column: Column, options: ExportOptions): string {
    if (column.dataType === 'number') {
      if (column.format === 'currency') {
        const currency = options.currency || 'USD';
        return `${currency} #,##0.00`;
      }
      if (column.format === 'percent') {
        return '0.00%';
      }
      return '#,##0.00';
    }

    if (column.dataType === 'date') {
      return options.dateFormat === 'DD/MM/YYYY'
        ? 'dd/mm/yyyy'
        : 'yyyy-mm-dd';
    }

    return '@';
  }

  private addConditionalFormatting(
    worksheet: ExcelJS.Worksheet,
    data: QueryResult,
    startRow: number
  ): void {
    // Add color scale for numeric columns
    data.columns.forEach((col, colIndex) => {
      if (col.type === 'measure') {
        const columnLetter = String.fromCharCode(65 + colIndex);
        const range = `${columnLetter}${startRow}:${columnLetter}${startRow + data.rows.length - 1}`;

        worksheet.addConditionalFormatting({
          ref: range,
          rules: [
            {
              type: 'colorScale',
              colorScale: {
                minimum: { color: 'FFFFFF', type: 'min' },
                midpoint: { color: 'FFD9E1F2', type: 'percent', value: 50 },
                maximum: { color: 'FF305496', type: 'max' },
              },
            },
          ],
        });
      }
    });
  }
}
```

### 3.2 Multi-Sheet Excel Export

```typescript
// Multi-sheet export for dashboards
class MultiSheetExcelExporter {
  async exportDashboard(
    dashboard: DashboardConfig,
    data: Record<string, QueryResult>,
    options: ExportOptions = {}
  ): Promise<Buffer> {
    const workbook = new ExcelJS.Workbook();

    // Add overview sheet
    this.addOverviewSheet(workbook, dashboard, data);

    // Add sheets for each widget
    for (const widget of dashboard.widgets) {
      const widgetData = data[widget.id];
      if (!widgetData) continue;

      const worksheet = workbook.addWorksheet(widget.title);

      // Add widget title and metadata
      worksheet.addRow([widget.title]);
      worksheet.lastRow!.font = { bold: true, size: 14 };
      worksheet.addRow([]);

      if (widget.description) {
        worksheet.addRow([widget.description]);
        worksheet.addRow([]);
      }

      // Export data
      const exporter = new ExcelExporter();
      await this.exportToWorksheet(worksheet, widgetData, options);
    }

    // Add summary sheet
    this.addSummarySheet(workbook, dashboard, data);

    const buffer = await workbook.xlsx.writeBuffer();
    return Buffer.from(buffer);
  }

  private addOverviewSheet(
    workbook: ExcelJS.Workbook,
    dashboard: DashboardConfig,
    data: Record<string, QueryResult>
  ): void {
    const worksheet = workbook.addWorksheet('Overview', { tabColor: { argb: 'FF4472C4' } });

    // Dashboard title
    worksheet.addRow([dashboard.name]);
    worksheet.lastRow!.font = { bold: true, size: 16 };
    worksheet.addRow([]);

    // Metadata
    worksheet.addRow(['Exported:', new Date().toLocaleString()]);
    worksheet.addRow(['Widgets:', dashboard.widgets.length]);
    worksheet.addRow([]);

    // Widget list
    worksheet.addRow(['Widget', 'Type', 'Rows']);
    worksheet.lastRow!.font = { bold: true };

    for (const widget of dashboard.widgets) {
      const widgetData = data[widget.id];
      worksheet.addRow([
        widget.title,
        widget.visualization.type,
        widgetData?.rows.length || 0,
      ]);
    }

    // Column widths
    worksheet.getColumn(1).width = 30;
    worksheet.getColumn(2).width = 15;
    worksheet.getColumn(3).width = 10;
  }

  private addSummarySheet(
    workbook: ExcelJS.Workbook,
    dashboard: DashboardConfig,
    data: Record<string, QueryResult>
  ): void {
    const worksheet = workbook.addWorksheet('Summary', { tabColor: { argb: 'FF70AD47' } });

    // KPI summary
    worksheet.addRow(['Key Metrics']);
    worksheet.lastRow!.font = { bold: true, size: 14 };
    worksheet.addRow([]);

    for (const widget of dashboard.widgets) {
      if (widget.visualization.type === 'kpi') {
        const widgetData = data[widget.id];
        if (widgetData && widgetData.rows.length > 0) {
          const value = widgetData.rows[0][widget.visualization.yAxis];
          worksheet.addRow([widget.title, value]);
        }
      }
    }
  }
}
```

### 3.3 Excel Export Options UI

```typescript
// Excel export configuration UI
export const ExcelExportOptions: React.FC<{
  onExport: (options: ExportOptions) => void;
  onCancel: () => void;
  hasMultipleWidgets?: boolean;
}> = ({ onExport, onCancel, hasMultipleWidgets }) => {
  const [options, setOptions] = useState<ExportOptions>({
    includeHeaders: true,
    includeTotals: true,
    freezeHeader: true,
    autoFilter: true,
    columnWidths: 'auto',
    includeCharts: true,
  });

  return (
    <Dialog>
      <DialogTitle>Export as Excel</DialogTitle>

      <DialogContent>
        <FormField label="Sheet Name">
          <Input
            value={options.sheetName || ''}
            onChange={(sheetName) => setOptions({ ...options, sheetName })}
            placeholder="Report"
          />
        </FormField>

        <FormField label="Options">
          <CheckboxGroup
            value={Object.entries(options)
              .filter(([_, v]) => v === true)
              .map(([k]) => k)}
            onChange={(keys) => {
              const newOptions = { ...options };
              Object.keys(newOptions).forEach(k => {
                if (typeof newOptions[k] === 'boolean') {
                  newOptions[k] = keys.includes(k);
                }
              });
              setOptions(newOptions);
            }}
            options={[
              { value: 'includeHeaders', label: 'Include column headers' },
              { value: 'includeTotals', label: 'Include totals row' },
              { value: 'freezeHeader', label: 'Freeze header row' },
              { value: 'autoFilter', label: 'Enable auto-filter' },
            ]}
          />
        </FormField>

        <FormField label="Column Widths">
          <RadioGroup
            value={options.columnWidths}
            onChange={(columnWidths) => setOptions({ ...options, columnWidths })}
            options={[
              { value: 'auto', label: 'Auto-fit content' },
              { value: 15, label: 'Fixed (15)' },
              { value: 20, label: 'Fixed (20)' },
            ]}
          />
        </FormField>

        {hasMultipleWidgets && (
          <FormField label="Multiple Widgets">
            <CheckboxGroup
              value={options.includeCharts ? ['includeCharts'] : []}
              onChange={(keys) => setOptions({
                ...options,
                includeCharts: keys.includes('includeCharts'),
              })}
              options={[
                { value: 'includeCharts', label: 'Include charts as images' },
                { value: 'separateSheets', label: 'Each widget on separate sheet' },
              ]}
            />
          </FormField>
        )}

        <FormField label="Filename">
          <Input
            value={options.filename || ''}
            onChange={(filename) => setOptions({ ...options, filename })}
            placeholder="report.xlsx"
          />
        </FormField>
      </DialogContent>

      <DialogActions>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onExport(options)}>Export</Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 4. PDF Export

### 4.1 PDF Exporter Implementation

```typescript
import PDFDocument from 'pdfkit';
import SVGtoPDF from 'svg-to-pdfkit';

// PDF exporter
class PDFExporter implements Exporter {
  async export(data: QueryResult, options: ExportOptions = {}): Promise<Buffer> {
    const doc = new PDFDocument({
      size: options.pageSize || 'A4',
      layout: options.orientation || 'portrait',
      margins: { top: 50, bottom: 50, left: 50, right: 50 },
      bufferPages: true,
    });

    // Register fonts
    this.registerFonts(doc);

    // Add header
    this.addHeader(doc, options);

    // Add title
    doc.fontSize(18).font('Helvetica-Bold').text(options.title || 'Report', { align: 'center' });
    doc.moveDown();

    // Add metadata
    this.addMetadata(doc, data);

    // Add summary if available
    if (options.includeSummary) {
      this.addSummary(doc, data);
      doc.moveDown();
    }

    // Add table
    await this.addTable(doc, data, options);

    // Add charts if requested
    if (options.includeCharts && data.charts) {
      await this.addCharts(doc, data.charts);
    }

    // Add footer
    this.addFooter(doc, options);

    // Generate buffer
    const buffers: Buffer[] = [];
    doc.on('data', buffers.push.bind(buffers));
    doc.end();

    return await new Promise<Buffer>((resolve) => {
      doc.on('end', () => resolve(Buffer.concat(buffers)));
    });
  }

  private registerFonts(doc: PDFKit.PDFDocument): void {
    // Register custom fonts if needed
    // doc.registerFont('CustomFont', 'path/to/font.ttf');
  }

  private addHeader(doc: PDFKit.PDFDocument, options: ExportOptions): void {
    // Add logo if available
    if (options.logo) {
      doc.image(options.logo, 50, 30, { width: 80 });
    }

    // Add header line
    doc.moveTo(50, 80)
       .lineTo(545, 80)
       .strokeColor('#CCCCCC')
       .lineWidth(1)
       .stroke();
  }

  private addMetadata(doc: PDFKit.PDFDocument, data: QueryResult): void {
    doc.fontSize(10).font('Helvetica');
    doc.text(`Generated: ${new Date().toLocaleString()}`, { align: 'right' });
    doc.text(`Total Records: ${data.rows.length.toLocaleString()}`, { align: 'right' });
    doc.moveDown();
  }

  private async addTable(
    doc: PDFKit.PDFDocument,
    data: QueryResult,
    options: ExportOptions
  ): Promise<void> {
    const columnWidths = this.calculateColumnWidths(data, doc.page.width - 100);
    const rowHeight = 25;
    const headerHeight = 30;

    // Table header
    let y = doc.y;

    // Draw header background
    doc.fillColor('#4472C4')
       .rect(50, y, doc.page.width - 100, headerHeight)
       .fill();

    // Draw header text
    doc.fillColor('FFFFFF')
       .fontSize(10)
       .font('Helvetica-Bold');

    let x = 50;
    for (let i = 0; i < data.columns.length; i++) {
      const col = data.columns[i];
      doc.text(col.displayName || col.name, x + 5, y + 10, {
        width: columnWidths[i] - 10,
        align: 'left',
      });
      x += columnWidths[i];
    }

    y += headerHeight;

    // Table rows
    doc.fillColor('#000000').font('Helvetica').fontSize(9);

    for (const row of data.rows) {
      // Check for page break
      if (y + rowHeight > doc.page.height - 50) {
        doc.addPage();
        y = 50;
      }

      // Alternate row background
      if ((data.rows.indexOf(row) % 2) === 1) {
        doc.fillColor('#F2F2F2')
           .rect(50, y, doc.page.width - 100, rowHeight)
           .fill();
        doc.fillColor('#000000');
      }

      // Draw cell values
      x = 50;
      for (let i = 0; i < data.columns.length; i++) {
        const col = data.columns[i];
        const value = this.formatValue(row[col.name], col, options);
        doc.text(value, x + 5, y + 5, {
          width: columnWidths[i] - 10,
          align: col.dataType === 'number' ? 'right' : 'left',
        });
        x += columnWidths[i];
      }

      y += rowHeight;
    }

    // Add totals row if requested
    if (options.includeTotals) {
      y = doc.y + 10;

      doc.fillColor('#E7E6E6')
         .rect(50, y, doc.page.width - 100, rowHeight)
         .fill();
      doc.fillColor('#000000').font('Helvetica-Bold');

      x = 50;
      for (let i = 0; i < data.columns.length; i++) {
        const col = data.columns[i];
        const value = col.type === 'measure'
          ? this.calculateTotal(data, col.name, options)
          : 'Total';
        doc.text(value, x + 5, y + 5, {
          width: columnWidths[i] - 10,
          align: col.dataType === 'number' ? 'right' : 'left',
        });
        x += columnWidths[i];
      }
    }

    doc.y = y + rowHeight + 20;
  }

  private async addCharts(
    doc: PDFKit.PDFDocument,
    charts: ChartData[]
  ): Promise<void> {
    for (const chart of charts) {
      // Check for page break
      if (doc.y > doc.page.height - 300) {
        doc.addPage();
      }

      // Add chart title
      doc.fontSize(14).font('Helvetica-Bold').text(chart.title);
      doc.moveDown();

      // Convert chart SVG to PDF
      const svg = chart.svg;
      SVGtoPDF(doc, svg, 50, doc.y, {
        width: doc.page.width - 100,
        preserveAspectRatio: 'xMidYMid meet',
      });

      doc.y += 300;
      doc.moveDown();
    }
  }

  private addFooter(doc: PDFKit.PDFDocument, options: ExportOptions): void {
    const range = doc.bufferedPageRange();
    const totalPages = range.start + range.count;

    for (let i = range.start; i < range.start + range.count; i++) {
      doc.switchToPage(i);

      // Footer line
      doc.moveTo(50, doc.page.height - 30)
         .lineTo(545, doc.page.height - 30)
         .strokeColor('#CCCCCC')
         .lineWidth(1)
         .stroke();

      // Page number
      doc.fontSize(9)
         .fillColor('#666666')
         .text(
           `Page ${i + 1} of ${totalPages}`,
           50,
           doc.page.height - 25,
           { align: 'center' }
         );

      // Footer text
      if (options.footerText) {
        doc.text(options.footerText, 545, doc.page.height - 25, { align: 'right' });
      }
    }
  }

  private calculateColumnWidths(data: QueryResult, pageWidth: number): number[] {
    const totalWidth = pageWidth;
    const perColumn = totalWidth / data.columns.length;

    return data.columns.map(col => {
      // Measure-based width calculation
      const maxWidth = Math.max(
        col.displayName.length * 7,
        20
      );
      return Math.min(maxWidth, perColumn);
    });
  }

  private formatValue(value: any, column: Column, options: ExportOptions): string {
    // Similar to Excel/CSV formatting
    if (value === null || value === undefined) return '';
    if (column.dataType === 'number') {
      return value.toLocaleString('en-US', {
        minimumFractionDigits: column.decimals || 2,
        maximumFractionDigits: column.decimals || 2,
      });
    }
    if (column.dataType === 'date') {
      return new Date(value).toLocaleDateString();
    }
    return String(value);
  }

  private calculateTotal(data: QueryResult, column: string, options: ExportOptions): string {
    const col = data.columns.find(c => c.name === column);
    if (!col || col.type !== 'measure') return '';

    const sum = data.rows.reduce((acc, row) => acc + (row[column] || 0), 0);
    return this.formatValue(sum, col, options);
  }
}
```

### 4.2 Template-Based PDF

```typescript
// Template-based PDF generation
class TemplatePDFExporter {
  private templates: Map<string, PDFTemplate> = new Map();

  async export(
    data: QueryResult,
    templateId: string,
    options: ExportOptions = {}
  ): Promise<Buffer> {
    const template = await this.loadTemplate(templateId);

    const doc = new PDFDocument({
      size: template.pageSize || 'A4',
      layout: template.orientation || 'portrait',
    });

    // Apply template structure
    for (const section of template.sections) {
      await this.renderSection(doc, section, data, options);
    }

    const buffers: Buffer[] = [];
    doc.on('data', buffers.push.bind(buffers));
    doc.end();

    return await new Promise<Buffer>((resolve) => {
      doc.on('end', () => resolve(Buffer.concat(buffers)));
    });
  }

  private async renderSection(
    doc: PDFKit.PDFDocument,
    section: TemplateSection,
    data: QueryResult,
    options: ExportOptions
  ): Promise<void> {
    switch (section.type) {
      case 'header':
        this.renderHeader(doc, section, data);
        break;

      case 'title':
        this.renderTitle(doc, section, data);
        break;

      case 'table':
        await this.renderTable(doc, section, data, options);
        break;

      case 'chart':
        await this.renderChart(doc, section, data);
        break;

      case 'summary':
        this.renderSummary(doc, section, data);
        break;

      case 'footer':
        this.renderFooter(doc, section, data);
        break;
    }
  }

  private renderHeader(doc: PDFKit.PDFDocument, section: TemplateSection, data: QueryResult): void {
    // Render header from template
    if (section.content.logo) {
      doc.image(section.content.logo, section.x || 50, section.y || 30, {
        width: section.content.logoWidth || 80,
      });
    }

    if (section.content.title) {
      doc.fontSize(section.content.fontSize || 16)
         .font(section.content.font || 'Helvetica-Bold')
         .text(section.content.title, section.x || 150, section.y || 40);
    }
  }

  private async loadTemplate(templateId: string): Promise<PDFTemplate> {
    // Load from database or file system
    if (this.templates.has(templateId)) {
      return this.templates.get(templateId)!;
    }

    const template = await db.pdfTemplates.findOne({ id: templateId });
    if (!template) {
      throw new Error(`Template not found: ${templateId}`);
    }

    this.templates.set(templateId, template);
    return template;
  }
}

// PDF template schema
interface PDFTemplate {
  id: string;
  name: string;
  description?: string;
  pageSize?: 'A4' | 'Letter' | 'Legal';
  orientation?: 'portrait' | 'landscape';
  sections: TemplateSection[];
}

interface TemplateSection {
  type: 'header' | 'title' | 'table' | 'chart' | 'summary' | 'footer';
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  content: any;
}
```

### 4.3 PDF Export Options UI

```typescript
// PDF export configuration UI
export const PDFExportOptions: React.FC<{
  onExport: (options: ExportOptions) => void;
  onCancel: () => void;
  templates?: PDFTemplate[];
}> = ({ onExport, onCancel, templates = [] }) => {
  const [options, setOptions] = useState<ExportOptions>({
    includeHeaders: true,
    includeTotals: true,
    includeSummary: true,
    includeCharts: true,
    orientation: 'portrait',
    pageSize: 'A4',
  });

  return (
    <Dialog>
      <DialogTitle>Export as PDF</DialogTitle>

      <DialogContent>
        {templates.length > 0 && (
          <FormField label="Template">
            <TemplateSelector
              templates={templates}
              value={options.template}
              onChange={(template) => setOptions({ ...options, template })}
            />
          </FormField>
        )}

        <FormField label="Page Size">
          <Select
            value={options.pageSize}
            onChange={(pageSize) => setOptions({ ...options, pageSize })}
          >
            <option value="A4">A4 (210 × 297 mm)</option>
            <option value="Letter">Letter (8.5 × 11 in)</option>
            <option value="Legal">Legal (8.5 × 14 in)</option>
          </Select>
        </FormField>

        <FormField label="Orientation">
          <SegmentedControl
            value={options.orientation}
            onChange={(orientation) => setOptions({ ...options, orientation })}
            options={[
              { value: 'portrait', label: 'Portrait' },
              { value: 'landscape', label: 'Landscape' },
            ]}
          />
        </FormField>

        <FormField label="Include">
          <CheckboxGroup
            value={Object.entries(options)
              .filter(([_, v]) => v === true && typeof v === 'boolean')
              .map(([k]) => k)}
            onChange={(keys) => {
              const newOptions = { ...options };
              Object.keys(newOptions).forEach(k => {
                if (typeof newOptions[k] === 'boolean') {
                  newOptions[k] = keys.includes(k);
                }
              });
              setOptions(newOptions);
            }}
            options={[
              { value: 'includeHeaders', label: 'Column headers' },
              { value: 'includeTotals', label: 'Totals row' },
              { value: 'includeSummary', label: 'Summary section' },
              { value: 'includeCharts', label: 'Charts' },
            ]}
          />
        </FormField>

        <FormField label="Footer Text (Optional)">
          <Input
            value={options.footerText || ''}
            onChange={(footerText) => setOptions({ ...options, footerText })}
            placeholder="Confidential - Internal Use Only"
          />
        </FormField>

        <FormField label="Filename">
          <Input
            value={options.filename || ''}
            onChange={(filename) => setOptions({ ...options, filename })}
            placeholder="report.pdf"
          />
        </FormField>
      </DialogContent>

      <DialogActions>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onExport(options)}>Export</Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 5. Template-Based Reports

### 5.1 Template System

```typescript
// Report template manager
class ReportTemplateManager {
  async createTemplate(template: PDFTemplate): Promise<PDFTemplate> {
    return await db.pdfTemplates.insert(template);
  }

  async updateTemplate(id: string, updates: Partial<PDFTemplate>): Promise<PDFTemplate> {
    return await db.pdfTemplates.update(id, updates);
  }

  async deleteTemplate(id: string): Promise<void> {
    await db.pdfTemplates.delete(id);
  }

  async listTemplates(agencyId: string): Promise<PDFTemplate[]> {
    return await db.pdfTemplates.find({ agencyId });
  }

  async getTemplate(id: string): Promise<PDFTemplate> {
    return await db.pdfTemplates.findOne({ id });
  }
}

// Template builder UI
export const TemplateBuilder: React.FC<{
  template?: PDFTemplate;
  onSave: (template: PDFTemplate) => Promise<void>;
  onCancel: () => void;
}> = ({ template, onSave, onCancel }) => {
  const [sections, setSections] = useState<TemplateSection[]>(
    template?.sections || []
  );

  const addSection = (type: TemplateSection['type']) => {
    const newSection: TemplateSection = {
      type,
      id: uuid(),
    };
    setSections([...sections, newSection]);
  };

  const updateSection = (id: string, updates: Partial<TemplateSection>) => {
    setSections(sections.map(s =>
      s.id === id ? { ...s, ...updates } : s
    ));
  };

  const removeSection = (id: string) => {
    setSections(sections.filter(s => s.id !== id));
  };

  return (
    <div className={styles.templateBuilder}>
      <div className={styles.preview}>
        <PDFPreview sections={sections} />
      </div>

      <div className={styles.controls}>
        <SectionList
          sections={sections}
          onAdd={addSection}
          onUpdate={updateSection}
          onRemove={removeSection}
        />
      </div>
    </div>
  );
};
```

### 5.2 Built-in Templates

```typescript
// Standard report templates
const standardTemplates: Record<string, PDFTemplate> = {
  simple: {
    id: 'simple',
    name: 'Simple Report',
    pageSize: 'A4',
    orientation: 'portrait',
    sections: [
      {
        type: 'header',
        content: { logo: '/assets/logo.png', title: 'Report' },
      },
      {
        type: 'title',
        content: { fontSize: 18, font: 'Helvetica-Bold' },
      },
      {
        type: 'table',
        content: { includeHeaders: true, stripeRows: true },
      },
      {
        type: 'footer',
        content: { showPageNumbers: true },
      },
    ],
  },

  detailed: {
    id: 'detailed',
    name: 'Detailed Report',
    pageSize: 'A4',
    orientation: 'portrait',
    sections: [
      {
        type: 'header',
        content: {
          logo: '/assets/logo.png',
          title: 'Detailed Report',
          showDate: true,
        },
      },
      {
        type: 'title',
        content: { fontSize: 20, font: 'Helvetica-Bold' },
      },
      {
        type: 'summary',
        content: { includeKPIs: true },
      },
      {
        type: 'table',
        content: { includeHeaders: true, stripeRows: true, includeTotals: true },
      },
      {
        type: 'chart',
        content: { includeAllCharts: true },
      },
      {
        type: 'footer',
        content: {
          showPageNumbers: true,
          text: 'Confidential - Internal Use Only',
        },
      },
    ],
  },

  invoice: {
    id: 'invoice',
    name: 'Invoice Style',
    pageSize: 'A4',
    orientation: 'portrait',
    sections: [
      {
        type: 'header',
        content: {
          logo: '/assets/logo.png',
          showInvoiceNumber: true,
        },
      },
      {
        type: 'title',
        content: { fontSize: 16, font: 'Helvetica-Bold' },
      },
      {
        type: 'table',
        content: {
          includeHeaders: true,
          includeTotals: true,
          columnAlignment: 'right',
        },
      },
      {
        type: 'footer',
        content: {
          showPaymentTerms: true,
          showContactInfo: true,
        },
      },
    ],
  },
};
```

---

## 6. Async Export & Job Queue

### 6.1 Job Queue Implementation

```typescript
// Export job queue
import Queue from 'bull';

interface ExportJob {
  id: string;
  type: 'export';
  data: QueryResult;
  format: ExportFormat;
  options: ExportOptions;
  userId: string;
  agencyId: string;
  priority?: number;
  attempts?: number;
}

class ExportJobQueue {
  private queue: Queue.Queue<ExportJob>;
  private storage: ExportStorage;

  constructor() {
    this.queue = new Queue('exports', {
      redis: {
        host: process.env.REDIS_HOST,
        port: parseInt(process.env.REDIS_PORT || '6379'),
      },
      defaultJobOptions: {
        attempts: 3,
        backoff: { type: 'exponential', delay: 5000 },
        removeOnComplete: 100,
        removeOnFail: 500,
      },
    });

    this.storage = new ExportStorage();
    this.setupProcessors();
  }

  private setupProcessors(): void {
    this.queue.process('export', 5, async (job) => {
      return await this.processExportJob(job);
    });

    // Handle job completion
    this.queue.on('completed', async (job, result) => {
      await this.notifyUser(job.data.userId, {
        type: 'export_complete',
        jobId: job.id,
        result,
      });
    });

    // Handle job failure
    this.queue.on('failed', async (job, error) => {
      await this.notifyUser(job.data.userId, {
        type: 'export_failed',
        jobId: job.id,
        error: error.message,
      });
    });
  }

  async add(job: ExportJob): Promise<void> {
    await this.queue.add('export', job, {
      jobId: job.id,
      priority: job.priority || 0,
    });
  }

  async getJob(jobId: string): Promise<ExportJobStatus> {
    const job = await this.queue.getJob(jobId);
    if (!job) {
      throw new Error('Job not found');
    }

    const state = await job.getState();
    return {
      id: job.id,
      status: state as ExportJobStatus['status'],
      progress: job.progress(),
      result: job.returnvalue,
      failedReason: job.failedReason,
    };
  }

  private async processExportJob(job: Queue.Job<ExportJob>): Promise<ExportResult> {
    const { data, format, options } = job.data;

    // Update progress
    job.progress(10);

    // Get exporter
    const exporter = this.getExporter(format);

    // Generate export
    job.progress(50);
    const buffer = await exporter.export(data, options);

    // Store file
    job.progress(75);
    const filename = this.generateFilename(job.data);
    const url = await this.storage.store(filename, buffer, {
      contentType: this.getContentType(format),
      expiresIn: 604800, // 7 days
    });

    job.progress(100);

    return {
      jobId: job.id,
      status: 'completed',
      format,
      filename,
      url,
      expiresAt: Date.now() + 604800000,
      size: buffer.length,
      rowCount: data.rows.length,
    };
  }

  private getExporter(format: ExportFormat): Exporter {
    const exporters: Record<ExportFormat, Exporter> = {
      csv: new CSVExporter(),
      xlsx: new ExcelExporter(),
      pdf: new PDFExporter(),
    };
    return exporters[format];
  }

  private generateFilename(job: ExportJob): string {
    const timestamp = new Date().toISOString().split('T')[0];
    return `export_${job.id}_${timestamp}.${job.format}`;
  }

  private getContentType(format: ExportFormat): string {
    const types = {
      csv: 'text/csv',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    };
    return types[format];
  }

  private async notifyUser(userId: string, notification: any): Promise<void> {
    // Send in-app notification
    await notificationService.send(userId, {
      type: notification.type,
      title: notification.type === 'export_complete'
        ? 'Export Ready'
        : 'Export Failed',
      body: notification.type === 'export_complete'
        ? `Your ${notification.result.format} export is ready for download.`
        : `Your export could not be completed: ${notification.error}`,
      data: {
        jobId: notification.jobId,
        url: notification.result?.url,
      },
    });
  }
}
```

### 6.2 Export Status Tracking

```typescript
// Export status hook
export function useExportJob(jobId: string) {
  const [status, setStatus] = useState<ExportJobStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const pollStatus = async () => {
      try {
        const result = await api.get(`/exports/${jobId}/status`);
        if (!cancelled) {
          setStatus(result);
          setLoading(false);

          // Continue polling if not complete
          if (result.status === 'pending' || result.status === 'processing') {
            setTimeout(pollStatus, 2000);
          }
        }
      } catch (error) {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    pollStatus();

    return () => {
      cancelled = true;
    };
  }, [jobId]);

  return { status, loading };
}

// Export progress component
export const ExportProgress: React.FC<{ jobId: string }> = ({ jobId }) => {
  const { status, loading } = useExportJob(jobId);

  if (loading) {
    return <Spinner />;
  }

  if (!status) {
    return <EmptyState message="Export not found" />;
  }

  return (
    <div className={styles.exportProgress}>
      {status.status === 'completed' ? (
        <ExportReady result={status.result!} />
      ) : status.status === 'failed' ? (
        <ExportFailed error={status.failedReason} />
      ) : (
        <ExportInProgress progress={status.progress} />
      )}
    </div>
  );
};

const ExportReady: React.FC<{ result: ExportResult }> = ({ result }) => {
  return (
    <div className={styles.exportReady}>
      <CheckCircleIcon className={styles.icon} />
      <h3>Export Ready!</h3>
      <p>{result.filename}</p>
      <p className={styles.meta}>
        {formatBytes(result.size)} • {result.rowCount} rows
      </p>
      <Button onClick={() => window.open(result.url, '_blank')}>
        Download
      </Button>
      <p className={styles.expiry}>
        Expires {new Date(result.expiresAt!).toLocaleString()}
      </p>
    </div>
  );
};

const ExportInProgress: React.FC<{ progress: number }> = ({ progress }) => {
  return (
    <div className={styles.exportInProgress}>
      <Spinner />
      <h3>Generating Export...</h3>
      <ProgressBar value={progress} max={100} />
      <p>{Math.round(progress)}% complete</p>
    </div>
  );
};
```

---

## 7. Download Management

### 7.1 Download Center

```typescript
// Download center component
export const DownloadCenter: React.FC = () => {
  const [downloads, setDownloads] = useState<DownloadItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDownloads();
  }, []);

  const loadDownloads = async () => {
    setLoading(true);
    try {
      const result = await api.get('/exports/downloads');
      setDownloads(result);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (item: DownloadItem) => {
    if (item.status === 'completed') {
      window.open(item.url, '_blank');
    } else {
      showToast('Export not ready yet', 'warning');
    }
  };

  const handleDelete = async (itemId: string) => {
    await api.delete(`/exports/downloads/${itemId}`);
    setDownloads(downloads.filter(d => d.id !== itemId));
  };

  return (
    <div className={styles.downloadCenter}>
      <div className={styles.header}>
        <h2>Downloads</h2>
        <Button variant="secondary" onClick={loadDownloads}>
          <RefreshIcon /> Refresh
        </Button>
      </div>

      {loading ? (
        <Spinner />
      ) : downloads.length === 0 ? (
        <EmptyState
          icon="download"
          message="No recent exports"
        />
      ) : (
        <div className={styles.downloadList}>
          {downloads.map(item => (
            <DownloadItem
              key={item.id}
              item={item}
              onDownload={() => handleDownload(item)}
              onDelete={() => handleDelete(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const DownloadItem: React.FC<{
  item: DownloadItem;
  onDownload: () => void;
  onDelete: () => void;
}> = ({ item, onDownload, onDelete }) => {
  const isExpired = item.expiresAt && Date.now() > item.expiresAt;

  return (
    <div className={cn(styles.downloadItem, { [styles.expired]: isExpired })}>
      <div className={styles.fileIcon}>
        <FileIcon format={item.format} />
      </div>

      <div className={styles.fileInfo}>
        <div className={styles.fileName}>{item.filename}</div>
        <div className={styles.fileMeta}>
          {formatBytes(item.size)} • {new Date(item.createdAt).toLocaleString()}
          {isExpired && <span className={styles.expiredBadge}>Expired</span>}
        </div>
      </div>

      <div className={styles.status}>
        {item.status === 'completed' && !isExpired && (
          <Button size="sm" onClick={onDownload}>
            <DownloadIcon /> Download
          </Button>
        )}
        {item.status === 'pending' && (
          <Badge variant="info">Pending</Badge>
        )}
        {item.status === 'processing' && (
          <Badge variant="info">Processing...</Badge>
        )}
        {item.status === 'failed' && (
          <Badge variant="error">Failed</Badge>
        )}
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={onDelete}
        className={styles.deleteButton}
      >
        <TrashIcon />
      </Button>
    </div>
  );
};
```

### 7.2 Export Storage

```typescript
// Export storage abstraction
class ExportStorage {
  private s3: AWS.S3;
  private cdnDomain: string;

  constructor() {
    this.s3 = new AWS.S3({
      region: process.env.AWS_REGION,
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      },
    });
    this.cdnDomain = process.env.CDN_DOMAIN || '';
  }

  async store(
    filename: string,
    buffer: Buffer,
    options: StorageOptions
  ): Promise<string> {
    const key = this.generateKey(filename);

    await this.s3.putObject({
      Bucket: process.env.S3_EXPORT_BUCKET!,
      Key: key,
      Body: buffer,
      ContentType: options.contentType,
      Expires: new Date(options.expiresIn * 1000 + Date.now()),
    }).promise();

    // Return CDN URL if configured
    if (this.cdnDomain) {
      return `https://${this.cdnDomain}/${key}`;
    }

    // Return presigned URL
    return this.s3.getSignedUrl('getObject', {
      Bucket: process.env.S3_EXPORT_BUCKET!,
      Key: key,
      Expires: options.expiresIn / 1000,
    });
  }

  async get(key: string): Promise<Buffer> {
    const result = await this.s3.getObject({
      Bucket: process.env.S3_EXPORT_BUCKET!,
      Key: key,
    }).promise();

    return result.Body as Buffer;
  }

  async delete(key: string): Promise<void> {
    await this.s3.deleteObject({
      Bucket: process.env.S3_EXPORT_BUCKET!,
      Key: key,
    }).promise();
  }

  private generateKey(filename: string): string {
    const date = new Date();
    return `exports/${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}/${filename}`;
  }
}
```

---

## Summary

The export system provides flexible, performant data export capabilities:

| Component | Purpose |
|-----------|---------|
| **CSV Export** | Simple, universal format with customizable delimiters |
| **Excel Export** | Rich formatting, multi-sheet, conditional formatting |
| **PDF Export** | Printable reports with headers, footers, charts |
| **Template System** | Branded, reusable report templates |
| **Async Jobs** | Background processing for large exports |
| **Download Center** | Centralized export management |

**Key Takeaways:**
- Route small exports to sync processing, large to async queue
- Support template-based PDF generation for branded reports
- Provide progress tracking for long-running exports
- Store files in S3/GCS with CDN delivery
- Set expiration dates for security
- Include proper formatting for dates, numbers, currency

---

**Related:** [04: Scheduling Deep Dive](./REPORTING_04_SCHEDULING_DEEP_DIVE.md) → Automated reports, subscriptions, and delivery
