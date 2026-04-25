# Reporting Module — Scheduling Deep Dive

> Automated reports, subscriptions, cron-based scheduling, and delivery channels

---

## Document Overview

**Series:** Reporting Module | **Document:** 4 of 4 | **Focus:** Scheduling & Automation

**Related Documents:**
- [01: Technical Deep Dive](./REPORTING_01_TECHNICAL_DEEP_DIVE.md) — Report engine architecture
- [02: UX/UI Deep Dive](./REPORTING_02_UX_UI_DEEP_DIVE.md) — Report builder interface
- [03: Export Deep Dive](./REPORTING_03_EXPORT_DEEP_DIVE.md) — Export formats

---

## Table of Contents

1. [Scheduled Reports Architecture](#1-scheduled-reports-architecture)
2. [Cron-Based Scheduling](#2-cron-based-scheduling)
3. [Subscription Management](#3-subscription-management)
4. [Delivery Channels](#4-delivery-channels)
5. [Report Versioning](#5-report-versioning)
6. [Failure Handling & Retries](#6-failure-handling--retries)
7. [Scheduling UI](#7-scheduling-ui)

---

## 1. Scheduled Reports Architecture

### 1.1 System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         SCHEDULED REPORTS SYSTEM                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                       SCHEDULE DEFINITION                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Report ID    │  │ Schedule     │  │ Delivery     │               │ │
│  │  │ Parameters   │  │ (Cron)       │  │ Channels     │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  └──────────────────────────────┬───────────────────────────────────────┘ │
│                                 │                                         │
│  ┌──────────────────────────────▼───────────────────────────────────────┐ │
│  │                         SCHEDULER SERVICE                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Cron Parser  │  │ Job Queue    │  │ Next Run     │               │ │
│  │  │             │  │ (Bull/Redis) │  │ Calculator   │               │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │           Schedule executor triggers at             │             │ │
│  │  │           configured times                          │             │ │
│  │  └──────┬──────────────────────────────────────────────┘             │ │
│  └─────────┼──────────────────────────────────────────────────────────┘ │
│            │                                                           │
│  ┌─────────▼─────────────────────────────────────────────────────────┐ │
│  │                       EXECUTION ENGINE                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Fetch Report │  │ Apply Params │  │ Generate     │               │ │
│  │  │ Definition   │  │ (Date Range) │  │ Export       │               │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │              Store in history / version             │             │ │
│  │  └──────┬──────────────────────────────────────────────┘             │ │
│  └─────────┼──────────────────────────────────────────────────────────┘ │
│            │                                                           │
│  ┌─────────▼─────────────────────────────────────────────────────────┐ │
│  │                       DELIVERY SERVICE                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │ │
│  │  │ Email        │  │ In-App       │  │ Webhook      │               │ │
│  │  │ (SMTP/SendGrid│ │ Notification │  │ (HTTP POST)  │               │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │ │
│  │         │                  │                  │                       │ │
│  │  ┌──────▼──────────────────▼──────────────────▼───────┐             │ │
│  │  │              Track delivery status                 │             │ │
│  │  └────────────────────────────────────────────────────┘             │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Schedule Definition Model

```typescript
// Scheduled report configuration
interface ScheduledReport {
  id: string;
  name: string;
  description?: string;

  // Report to execute
  reportId: string;
  reportVersion?: number;

  // Schedule
  schedule: ScheduleConfig;

  // Parameters for report execution
  parameters: ReportParameters;

  // Output configuration
  output: OutputConfig;

  // Delivery
  delivery: DeliveryConfig;

  // Metadata
  createdBy: string;
  agencyId: string;
  createdAt: number;
  updatedAt: number;
  active: boolean;

  // Execution tracking
  lastRunAt?: number;
  nextRunAt: number;
  runCount: number;
}

interface ScheduleConfig {
  type: 'cron' | 'interval' | 'once';
  expression?: string; // Cron expression for type 'cron'
  interval?: number; // Minutes for type 'interval'
  timezone: string;
  startDate?: number;
  endDate?: number;
}

interface ReportParameters {
  dateRange?: {
    type: 'dynamic' | 'fixed';
    value?: DateRange;
    dynamicType?: 'today' | 'yesterday' | 'last_7_days' | 'last_30_days' | 'this_month' | 'last_month' | 'this_quarter' | 'last_quarter' | 'this_year' | 'last_year';
  };
  filters?: Record<string, any>;
  limit?: number;
}

interface OutputConfig {
  format: ExportFormat;
  template?: string;
  includeCharts?: boolean;
  filename?: string;
}

interface DeliveryConfig {
  channels: DeliveryChannel[];
  subject?: string;
  message?: string;
}

interface DeliveryChannel {
  type: 'email' | 'in_app' | 'webhook';
  config: EmailConfig | InAppConfig | WebhookConfig;
}

interface EmailConfig {
  to: string[];
  cc?: string[];
  bcc?: string[];
  replyTo?: string;
}

interface InAppConfig {
  users: string[]; // User IDs
}

interface WebhookConfig {
  url: string;
  headers?: Record<string, string>;
  method?: 'POST' | 'PUT';
}
```

### 1.3 Scheduler Service

```typescript
// Scheduler service
import { CronJob } from 'cron';
import Queue from 'bull';

class ReportScheduler {
  private jobs: Map<string, CronJob> = new Map();
  private executionQueue: Queue;
  private db: Database;

  constructor() {
    this.executionQueue = new Queue('scheduled-reports', {
      redis: { host: process.env.REDIS_HOST, port: 6379 },
    });

    this.setupProcessor();
    this.initializeJobs();
  }

  private setupProcessor(): void {
    this.executionQueue.process(5, async (job) => {
      return await this.executeScheduledReport(job.data);
    });

    this.executionQueue.on('completed', async (job, result) => {
      await this.updateJobStatus(job.data.scheduleId, 'completed', result);
    });

    this.executionQueue.on('failed', async (job, error) => {
      await this.updateJobStatus(job.data.scheduleId, 'failed', { error: error.message });
    });
  }

  async initializeJobs(): Promise<void> {
    const schedules = await this.db.scheduledReports.find({ active: true });

    for (const schedule of schedules) {
      await this.scheduleJob(schedule);
    }
  }

  async scheduleJob(schedule: ScheduledReport): Promise<void> {
    // Stop existing job if present
    if (this.jobs.has(schedule.id)) {
      this.jobs.get(schedule.id)!.stop();
    }

    const cronJob = new CronJob(
      schedule.schedule.expression!,
      async () => {
        await this.executionQueue.add({
          scheduleId: schedule.id,
          reportId: schedule.reportId,
          parameters: schedule.parameters,
          output: schedule.output,
          delivery: schedule.delivery,
        });
      },
      null, // onComplete
      true, // start
      schedule.schedule.timezone
    );

    this.jobs.set(schedule.id, cronJob);

    // Calculate next run time
    const nextRun = this.getNextRunTime(schedule);
    await this.db.scheduledReports.update(schedule.id, {
      nextRunAt: nextRun,
    });
  }

  async unscheduleJob(scheduleId: string): Promise<void> {
    const job = this.jobs.get(scheduleId);
    if (job) {
      job.stop();
      this.jobs.delete(scheduleId);
    }
  }

  async createSchedule(schedule: Omit<ScheduledReport, 'id' | 'createdAt' | 'updatedAt' | 'nextRunAt' | 'runCount'>): Promise<ScheduledReport> {
    const newSchedule: ScheduledReport = {
      ...schedule,
      id: uuid(),
      createdAt: Date.now(),
      updatedAt: Date.now(),
      nextRunAt: this.getNextRunTime(schedule),
      runCount: 0,
    };

    await this.db.scheduledReports.insert(newSchedule);

    if (newSchedule.active) {
      await this.scheduleJob(newSchedule);
    }

    return newSchedule;
  }

  async updateSchedule(scheduleId: string, updates: Partial<ScheduledReport>): Promise<ScheduledReport> {
    const schedule = await this.db.scheduledReports.findOne({ id: scheduleId });
    if (!schedule) {
      throw new Error('Schedule not found');
    }

    const updated = { ...schedule, ...updates, updatedAt: Date.now() };

    await this.db.scheduledReports.update(scheduleId, updated);

    // Reschedule if active
    if (updated.active) {
      await this.scheduleJob(updated);
    } else {
      await this.unscheduleJob(scheduleId);
    }

    return updated;
  }

  async deleteSchedule(scheduleId: string): Promise<void> {
    await this.unscheduleJob(scheduleId);
    await this.db.scheduledReports.delete(scheduleId);
  }

  private getNextRunTime(schedule: ScheduledReport): number {
    if (!schedule.active) {
      return 0;
    }

    const cronExpression = schedule.schedule.expression;
    const timezone = schedule.schedule.timezone;

    try {
      const parser = require('cron-parser');
      const interval = parser.parseExpression(cronExpression, {
        tz: timezone,
        currentDate: new Date(),
      });

      return interval.next().toDate().getTime();
    } catch (error) {
      console.error('Invalid cron expression:', cronExpression);
      return 0;
    }
  }

  private async executeScheduledReport(data: any): Promise<ExecutionResult> {
    const { scheduleId, reportId, parameters, output, delivery } = data;

    // Resolve dynamic date ranges
    const resolvedParams = this.resolveParameters(parameters);

    // Execute report
    const engine = new ReportEngine();
    const reportData = await engine.executeReportById(reportId, {
      parameters: resolvedParams,
    });

    // Generate export
    const exporter = this.getExporter(output.format);
    const buffer = await exporter.export(reportData, output);

    // Store export
    const storage = new ExportStorage();
    const url = await storage.store(
      output.filename || this.generateFilename(reportId, output.format),
      buffer,
      { contentType: this.getContentType(output.format), expiresIn: 604800 }
    );

    // Deliver to channels
    const deliveryResults = await this.deliverReport({
      url,
      format: output.format,
      filename: output.filename,
      size: buffer.length,
      delivery,
    });

    // Update run count
    await this.db.scheduledReports.update(scheduleId, {
      lastRunAt: Date.now(),
      nextRunAt: this.getNextRunTime(await this.db.scheduledReports.findOne({ id: scheduleId })),
      runCount: { $increment: 1 },
    });

    return {
      scheduleId,
      executedAt: Date.now(),
      url,
      delivery: deliveryResults,
    };
  }

  private resolveParameters(parameters: ReportParameters): ReportParameters {
    const resolved = { ...parameters };

    if (parameters.dateRange?.type === 'dynamic') {
      const now = new Date();
      const range = this.calculateDynamicRange(parameters.dateRange.dynamicType!, now);
      resolved.dateRange = { type: 'fixed', value: range };
    }

    return resolved;
  }

  private calculateDynamicRange(type: string, now: Date): DateRange {
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfDay = (date: Date) => new Date(date.getFullYear(), date.getMonth(), date.getDate());

    switch (type) {
      case 'today':
        return { start: today, end: new Date(today.getTime() + 86400000 - 1) };

      case 'yesterday':
        const yesterday = new Date(today.getTime() - 86400000);
        return { start: yesterday, end: new Date(today.getTime() - 1) };

      case 'last_7_days':
        return {
          start: new Date(today.getTime() - 7 * 86400000),
          end: new Date(today.getTime() + 86400000 - 1),
        };

      case 'last_30_days':
        return {
          start: new Date(today.getTime() - 30 * 86400000),
          end: new Date(today.getTime() + 86400000 - 1),
        };

      case 'this_month':
        return {
          start: new Date(now.getFullYear(), now.getMonth(), 1),
          end: new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59),
        };

      case 'last_month':
        return {
          start: new Date(now.getFullYear(), now.getMonth() - 1, 1),
          end: new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59),
        };

      case 'this_quarter':
        const quarter = Math.floor(now.getMonth() / 3);
        return {
          start: new Date(now.getFullYear(), quarter * 3, 1),
          end: new Date(now.getFullYear(), quarter * 3 + 3, 0, 23, 59, 59),
        };

      case 'last_quarter':
        const lastQuarter = Math.floor(now.getMonth() / 3) - 1;
        const year = lastQuarter < 0 ? now.getFullYear() - 1 : now.getFullYear();
        const adjustedQuarter = lastQuarter < 0 ? lastQuarter + 4 : lastQuarter;
        return {
          start: new Date(year, adjustedQuarter * 3, 1),
          end: new Date(year, adjustedQuarter * 3 + 3, 0, 23, 59, 59),
        };

      case 'this_year':
        return {
          start: new Date(now.getFullYear(), 0, 1),
          end: new Date(now.getFullYear(), 11, 31, 23, 59, 59),
        };

      case 'last_year':
        return {
          start: new Date(now.getFullYear() - 1, 0, 1),
          end: new Date(now.getFullYear() - 1, 11, 31, 23, 59, 59),
        };

      default:
        return { start: today, end: new Date(today.getTime() + 86400000 - 1) };
    }
  }

  private async deliverReport(package: ReportPackage): Promise<DeliveryResult[]> {
    const results: DeliveryResult[] = [];

    for (const channel of package.delivery.channels) {
      try {
        switch (channel.type) {
          case 'email':
            results.push(await this.deliverEmail(package, channel.config as EmailConfig));
            break;
          case 'in_app':
            results.push(await this.deliverInApp(package, channel.config as InAppConfig));
            break;
          case 'webhook':
            results.push(await this.deliverWebhook(package, channel.config as WebhookConfig));
            break;
        }
      } catch (error) {
        results.push({
          channel: channel.type,
          status: 'failed',
          error: error.message,
        });
      }
    }

    return results;
  }

  private async deliverEmail(package: ReportPackage, config: EmailConfig): Promise<DeliveryResult> {
    const emailService = new EmailService();

    await emailService.send({
      to: config.to,
      cc: config.cc,
      bcc: config.bcc,
      replyTo: config.replyTo,
      subject: package.delivery.subject || 'Your Scheduled Report',
      template: 'scheduled_report',
      data: {
        filename: package.filename,
        url: package.url,
        format: package.format,
        size: package.size,
      },
      attachments: [
        {
          filename: package.filename,
          url: package.url,
        },
      ],
    });

    return {
      channel: 'email',
      status: 'delivered',
      recipients: config.to.length,
    };
  }

  private async deliverInApp(package: ReportPackage, config: InAppConfig): Promise<DeliveryResult> {
    for (const userId of config.users) {
      await notificationService.send(userId, {
        type: 'scheduled_report',
        title: package.delivery.subject || 'Scheduled Report Ready',
        body: `Your scheduled report "${package.filename}" is ready for download.`,
        data: {
          url: package.url,
          filename: package.filename,
          format: package.format,
        },
      });
    }

    return {
      channel: 'in_app',
      status: 'delivered',
      recipients: config.users.length,
    };
  }

  private async deliverWebhook(package: ReportPackage, config: WebhookConfig): Promise<DeliveryResult> {
    const response = await fetch(config.url, {
      method: config.method || 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      body: JSON.stringify({
        filename: package.filename,
        url: package.url,
        format: package.format,
        size: package.size,
        generatedAt: Date.now(),
      }),
    });

    if (!response.ok) {
      throw new Error(`Webhook failed: ${response.status}`);
    }

    return {
      channel: 'webhook',
      status: 'delivered',
    };
  }

  private async updateJobStatus(scheduleId: string, status: string, result: any): Promise<void> {
    await this.db.reportExecutionHistory.insert({
      scheduleId,
      status,
      result,
      executedAt: Date.now(),
    });
  }

  private getExporter(format: ExportFormat): Exporter {
    const exporters = {
      csv: new CSVExporter(),
      xlsx: new ExcelExporter(),
      pdf: new PDFExporter(),
    };
    return exporters[format];
  }

  private getContentType(format: ExportFormat): string {
    const types = {
      csv: 'text/csv',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    };
    return types[format];
  }

  private generateFilename(reportId: string, format: ExportFormat): string {
    const date = new Date().toISOString().split('T')[0];
    return `report_${reportId}_${date}.${format}`;
  }
}
```

---

## 2. Cron-Based Scheduling

### 2.1 Cron Expression Builder

```typescript
// Cron expression builder UI
interface CronExpression {
  minute: string | number;
  hour: string | number;
  dayOfMonth: string | number;
  month: string | number;
  dayOfWeek: string | number;
}

// Preset schedules
const schedulePresets: Array<{
  id: string;
  label: string;
  expression: string;
  description: string;
}> = [
  { id: 'hourly', label: 'Hourly', expression: '0 * * * *', description: 'At minute 0 of every hour' },
  { id: 'daily_6am', label: 'Daily (6 AM)', expression: '0 6 * * *', description: 'At 6:00 AM every day' },
  { id: 'daily_9am', label: 'Daily (9 AM)', expression: '0 9 * * *', description: 'At 9:00 AM every day' },
  { id: 'weekly_mon', label: 'Weekly (Monday)', expression: '0 9 * * 1', description: 'At 9:00 AM on Monday' },
  { id: 'monthly_1st', label: 'Monthly (1st)', expression: '0 9 1 * *', description: 'At 9:00 AM on the 1st of month' },
  { id: 'quarterly', label: 'Quarterly', expression: '0 9 1 1,4,7,10 *', description: 'At 9:00 AM on 1st of quarter' },
  { id: 'weekdays', label: 'Weekdays', expression: '0 9 * * 1-5', description: 'At 9:00 AM on weekdays' },
];

// Cron builder component
export const CronBuilder: React.FC<{
  value: string;
  onChange: (expression: string) => void;
  timezone?: string;
  onTimezoneChange?: (timezone: string) => void;
}> = ({ value, onChange, timezone = 'UTC', onTimezoneChange }) => {
  const [mode, setMode] = useState<'preset' | 'custom'>('preset');

  const parsed = parseCronExpression(value);

  return (
    <div className={styles.cronBuilder}>
      <SegmentedControl
        value={mode}
        onChange={setMode}
        options={[
          { value: 'preset', label: 'Presets' },
          { value: 'custom', label: 'Custom' },
        ]}
      />

      {mode === 'preset' ? (
        <PresetSelector
          value={value}
          onChange={onChange}
          presets={schedulePresets}
        />
      ) : (
        <CustomCronBuilder
          value={parsed}
          onChange={(cron) => onChange(buildCronExpression(cron))}
        />
      )}

      <div className={styles.timezoneSelector}>
        <label>Timezone</label>
        <TimezoneSelector
          value={timezone}
          onChange={onTimezoneChange || (() => {})}
        />
      </div>

      <div className={styles.preview}>
        <label>Preview</label>
        <CronPreview expression={value} timezone={timezone} />
      </div>
    </div>
  );
};

// Custom cron builder
const CustomCronBuilder: React.FC<{
  value: CronExpression;
  onChange: (value: CronExpression) => void;
}> = ({ value, onChange }) => {
  return (
    <div className={styles.customBuilder}>
      <CronField
        label="Minute"
        value={value.minute}
        options={minuteOptions}
        onChange={(minute) => onChange({ ...value, minute })}
      />

      <CronField
        label="Hour"
        value={value.hour}
        options={hourOptions}
        onChange={(hour) => onChange({ ...value, hour })}
      />

      <CronField
        label="Day of Month"
        value={value.dayOfMonth}
        options={dayOfMonthOptions}
        onChange={(dayOfMonth) => onChange({ ...value, dayOfMonth })}
      />

      <CronField
        label="Month"
        value={value.month}
        options={monthOptions}
        onChange={(month) => onChange({ ...value, month })}
      />

      <CronField
        label="Day of Week"
        value={value.dayOfWeek}
        options={dayOfWeekOptions}
        onChange={(dayOfWeek) => onChange({ ...value, dayOfWeek })}
      />
    </div>
  );
};

// Cron field selector
const CronField: React.FC<{
  label: string;
  value: string | number;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string | number) => void;
}> = ({ label, value, options, onChange }) => {
  return (
    <div className={styles.cronField}>
      <label>{label}</label>
      <Select value={String(value)} onChange={(v) => onChange(v)}>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </Select>
    </div>
  );
};

// Cron options
const minuteOptions = [
  { value: '*', label: 'Every minute' },
  { value: '0', label: 'At minute 0' },
  { value: '15', label: 'At minute 15' },
  { value: '30', label: 'At minute 30' },
  { value: '45', label: 'At minute 45' },
  ...Array.from({ length: 60 }, (_, i) => ({ value: String(i), label: `At minute ${i}` })),
];

const hourOptions = [
  { value: '*', label: 'Every hour' },
  { value: '0', label: 'Midnight (12 AM)' },
  { value: '6', label: '6 AM' },
  { value: '9', label: '9 AM' },
  { value: '12', label: 'Noon (12 PM)' },
  { value: '18', label: '6 PM' },
  ...Array.from({ length: 24 }, (_, i) => ({
    value: String(i),
    label: `${i}:00 (${i === 0 ? 12 : i > 12 ? i - 12 : i} ${i < 12 ? 'AM' : 'PM'})`,
  })),
];

const dayOfMonthOptions = [
  { value: '*', label: 'Every day' },
  { value: '1', label: '1st' },
  { value: 'L', label: 'Last day of month' },
  ...Array.from({ length: 31 }, (_, i) => ({ value: String(i + 1), label: `${i + 1}${getOrdinal(i + 1)}` })),
];

const monthOptions = [
  { value: '*', label: 'Every month' },
  { value: '1', label: 'January' },
  { value: '2', label: 'February' },
  { value: '3', label: 'March' },
  { value: '4', label: 'April' },
  { value: '5', label: 'May' },
  { value: '6', label: 'June' },
  { value: '7', label: 'July' },
  { value: '8', label: 'August' },
  { value: '9', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
];

const dayOfWeekOptions = [
  { value: '*', label: 'Every day' },
  { value: '0', label: 'Sunday' },
  { value: '1', label: 'Monday' },
  { value: '2', label: 'Tuesday' },
  { value: '3', label: 'Wednesday' },
  { value: '4', label: 'Thursday' },
  { value: '5', label: 'Friday' },
  { value: '6', label: 'Saturday' },
  { value: '1-5', label: 'Weekdays' },
  { value: '0,6', label: 'Weekends' },
];

function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return (s[(v - 20) % 10] || s[v] || s[0]);
}

// Cron preview (next run times)
const CronPreview: React.FC<{
  expression: string;
  timezone: string;
}> = ({ expression, timezone }) => {
  const [nextRuns, setNextRuns] = useState<Date[]>([]);

  useEffect(() => {
    try {
      const parser = require('cron-parser');
      const interval = parser.parseExpression(expression, { tz: timezone });

      const runs: Date[] = [];
      for (let i = 0; i < 5; i++) {
        runs.push(interval.next().toDate());
      }
      setNextRuns(runs);
    } catch (error) {
      setNextRuns([]);
    }
  }, [expression, timezone]);

  return (
    <div className={styles.cronPreview}>
      <strong>Next runs:</strong>
      {nextRuns.length === 0 ? (
        <p className={styles.error}>Invalid cron expression</p>
      ) : (
        <ul>
          {nextRuns.map((run, i) => (
            <li key={i}>
              {run.toLocaleString('en-US', { timeZone: timezone })}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
```

### 2.2 Schedule Validation

```typescript
// Schedule validation
class ScheduleValidator {
  validate(schedule: ScheduleConfig): ValidationResult {
    const errors: string[] = [];

    // Validate cron expression
    if (schedule.type === 'cron') {
      if (!schedule.expression) {
        errors.push('Cron expression is required');
      } else if (!this.isValidCronExpression(schedule.expression)) {
        errors.push('Invalid cron expression');
      }
    }

    // Validate interval
    if (schedule.type === 'interval') {
      if (!schedule.interval || schedule.interval < 1) {
        errors.push('Interval must be at least 1 minute');
      }
    }

    // Validate timezone
    if (!this.isValidTimezone(schedule.timezone)) {
      errors.push('Invalid timezone');
    }

    // Validate date range
    if (schedule.startDate && schedule.endDate) {
      if (schedule.startDate >= schedule.endDate) {
        errors.push('Start date must be before end date');
      }
    }

    // Validate start date is in the future for new schedules
    if (schedule.startDate && schedule.startDate < Date.now()) {
      errors.push('Start date must be in the future');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  private isValidCronExpression(expression: string): boolean {
    try {
      const parser = require('cron-parser');
      parser.parseExpression(expression);
      return true;
    } catch {
      return false;
    }
  }

  private isValidTimezone(timezone: string): boolean {
    try {
      Intl.DateTimeFormat(undefined, { timeZone: timezone });
      return true;
    } catch {
      return false;
    }
  }

  // Check for conflicting schedules
  async checkConflicts(
    schedule: ScheduleConfig,
    reportId: string,
    excludeId?: string
  ): Promise<ConflictWarning[]> {
    const conflicts: ConflictWarning[] = [];

    // Find schedules with similar times for the same report
    const existing = await db.scheduledReports.find({
      reportId,
      id: { $ne: excludeId },
      active: true,
    });

    for (const existingSchedule of existing) {
      if (this.schedulesConflict(schedule, existingSchedule.schedule)) {
        conflicts.push({
          type: 'similar_schedule',
          message: `Similar to existing schedule "${existingSchedule.name}"`,
          existingScheduleId: existingSchedule.id,
        });
      }
    }

    return conflicts;
  }

  private schedulesConflict(a: ScheduleConfig, b: ScheduleConfig): boolean {
    // Simple conflict detection: same cron expression and timezone
    if (a.type === 'cron' && b.type === 'cron') {
      return a.expression === b.expression && a.timezone === b.timezone;
    }

    // For intervals, check if one is a multiple of the other
    if (a.type === 'interval' && b.type === 'interval') {
      const gcd = (a: number, b: number) => b === 0 ? a : gcd(b, a % b);
      const commonInterval = gcd(a.interval!, b.interval!);
      return commonInterval === Math.min(a.interval!, b.interval!);
    }

    return false;
  }
}
```

---

## 3. Subscription Management

### 3.1 Subscription Model

```typescript
// Report subscription (user subscribes to a report)
interface ReportSubscription {
  id: string;
  userId: string;
  reportId: string;
  schedule: ScheduleConfig;
  output: OutputConfig;
  delivery: {
    type: 'email' | 'in_app';
    config: EmailConfig | InAppConfig;
  };
  active: boolean;
  createdAt: number;
  updatedAt: number;
  lastDeliveryAt?: number;
  nextDeliveryAt: number;
}

// Subscription manager
class SubscriptionManager {
  private scheduler: ReportScheduler;

  async subscribe(subscription: Omit<ReportSubscription, 'id' | 'createdAt' | 'updatedAt' | 'nextDeliveryAt'>): Promise<ReportSubscription> {
    // Check if user already has a subscription to this report
    const existing = await this.findSubscription(subscription.userId, subscription.reportId);
    if (existing) {
      throw new Error('Already subscribed to this report');
    }

    const newSubscription: ReportSubscription = {
      ...subscription,
      id: uuid(),
      createdAt: Date.now(),
      updatedAt: Date.now(),
      nextDeliveryAt: this.scheduler.getNextRunTime({
        schedule: subscription.schedule,
        active: true,
      } as any),
    };

    await db.reportSubscriptions.insert(newSubscription);

    // Register with scheduler
    if (newSubscription.active) {
      await this.scheduler.scheduleJob({
        id: newSubscription.id,
        reportId: newSubscription.reportId,
        schedule: newSubscription.schedule,
        parameters: {},
        output: newSubscription.output,
        delivery: {
          channels: [newSubscription.delivery],
        },
        active: true,
        createdBy: newSubscription.userId,
        agencyId: '', // Will be filled in
        createdAt: newSubscription.createdAt,
        updatedAt: newSubscription.updatedAt,
      });
    }

    return newSubscription;
  }

  async unsubscribe(subscriptionId: string, userId: string): Promise<void> {
    const subscription = await db.reportSubscriptions.findOne({ id: subscriptionId, userId });
    if (!subscription) {
      throw new Error('Subscription not found');
    }

    await db.reportSubscriptions.update(subscriptionId, { active: false });
    await this.scheduler.unscheduleJob(subscriptionId);
  }

  async updateSubscription(
    subscriptionId: string,
    userId: string,
    updates: Partial<ReportSubscription>
  ): Promise<ReportSubscription> {
    const subscription = await db.reportSubscriptions.findOne({ id: subscriptionId, userId });
    if (!subscription) {
      throw new Error('Subscription not found');
    }

    const updated = { ...subscription, ...updates, updatedAt: Date.now() };
    await db.reportSubscriptions.update(subscriptionId, updated);

    // Reschedule
    if (updated.active) {
      await this.scheduler.scheduleJob({
        id: updated.id,
        reportId: updated.reportId,
        schedule: updated.schedule,
        parameters: {},
        output: updated.output,
        delivery: { channels: [updated.delivery] },
        active: true,
        createdBy: updated.userId,
        agencyId: '',
        createdAt: updated.createdAt,
        updatedAt: updated.updatedAt,
      });
    } else {
      await this.scheduler.unscheduleJob(updated.id);
    }

    return updated;
  }

  async getUserSubscriptions(userId: string): Promise<ReportSubscription[]> {
    return await db.reportSubscriptions.find({ userId, active: true });
  }

  private async findSubscription(userId: string, reportId: string): Promise<ReportSubscription | null> {
    return await db.reportSubscriptions.findOne({ userId, reportId, active: true });
  }
}
```

### 3.2 Subscription UI

```typescript
// Subscribe to report button
export const SubscribeButton: React.FC<{ reportId: string; reportName: string }> = ({
  reportId,
  reportName,
}) => {
  const [subscribed, setSubscribed] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const user = useAuthStore(state => state.user);

  useEffect(() => {
    checkSubscription();
  }, [reportId]);

  const checkSubscription = async () => {
    const sub = await api.get(`/reports/${reportId}/subscription`);
    setSubscribed(!!sub);
  };

  const handleSubscribe = async (config: SubscriptionConfig) => {
    await api.post(`/reports/${reportId}/subscribe`, config);
    setSubscribed(true);
    setDialogOpen(false);
    showToast(`Subscribed to "${reportName}"`, 'success');
  };

  const handleUnsubscribe = async () => {
    await api.delete(`/reports/${reportId}/subscription`);
    setSubscribed(false);
    showToast(`Unsubscribed from "${reportName}"`, 'info');
  };

  return (
    <>
      {subscribed ? (
        <Button variant="secondary" onClick={handleUnsubscribe}>
          <BellOffIcon /> Unsubscribe
        </Button>
      ) : (
        <Button onClick={() => setDialogOpen(true)}>
          <BellIcon /> Subscribe
        </Button>
      )}

      {dialogOpen && (
        <SubscriptionDialog
          reportId={reportId}
          reportName={reportName}
          onSubscribe={handleSubscribe}
          onClose={() => setDialogOpen(false)}
        />
      )}
    </>
  );
};

// Subscription configuration dialog
const SubscriptionDialog: React.FC<{
  reportId: string;
  reportName: string;
  onSubscribe: (config: SubscriptionConfig) => Promise<void>;
  onClose: () => void;
}> = ({ reportId, reportName, onSubscribe, onClose }) => {
  const [schedule, setSchedule] = useState<ScheduleConfig>({
    type: 'cron',
    expression: '0 9 * * *', // Daily at 9 AM
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  const [output, setOutput] = useState<OutputConfig>({
    format: 'xlsx',
  });

  const [delivery, setDelivery] = useState<DeliveryConfig>({
    channels: [{
      type: 'email',
      config: {
        to: [useAuthStore.getState().user!.email],
      },
    }],
  });

  const handleSubmit = async () => {
    await onSubscribe({ schedule, output, delivery });
  };

  return (
    <Dialog>
      <DialogTitle>Subscribe to "{reportName}"</DialogTitle>

      <DialogContent>
        <FormField label="Schedule">
          <CronBuilder
            value={schedule.expression!}
            onChange={(expression) => setSchedule({ ...schedule, expression })}
            timezone={schedule.timezone}
            onTimezoneChange={(timezone) => setSchedule({ ...schedule, timezone })}
          />
        </FormField>

        <FormField label="Format">
          <Select
            value={output.format}
            onChange={(format) => setOutput({ ...output, format })}
          >
            <option value="xlsx">Excel</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </Select>
        </FormField>

        <FormField label="Email To">
          <Input
            type="email"
            value={delivery.channels[0].config.to[0] || ''}
            onChange={(to) => setDelivery({
              channels: [{
                type: 'email',
                config: { to: [to] },
              }],
            })}
          />
        </FormField>
      </DialogContent>

      <DialogActions>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit}>Subscribe</Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

## 4. Delivery Channels

### 4.1 Email Delivery

```typescript
// Email template for scheduled reports
const scheduledReportEmailTemplate = `
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #4472C4; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
    .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }
    .button { display: inline-block; padding: 12px 24px; background: #4472C4; color: white; text-decoration: none; border-radius: 4px; }
    .footer { text-align: center; margin-top: 20px; color: #999; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{reportName}}</h1>
      <p>Scheduled Report</p>
    </div>
    <div class="content">
      <p>Your scheduled report is ready.</p>

      <p><strong>Report:</strong> {{reportName}}</p>
      <p><strong>Generated:</strong> {{generatedAt}}</p>
      <p><strong>Format:</strong> {{format}}</p>
      <p><strong>Size:</strong> {{size}}</p>

      <p>
        <a href="{{downloadUrl}}" class="button">Download Report</a>
      </p>

      <p>This report will expire in 7 days.</p>
    </div>
    <div class="footer">
      <p>To manage your subscriptions, visit your account settings.</p>
    </div>
  </div>
</body>
</html>
`;

// Email delivery service
class EmailDeliveryService {
  private sendGrid: SendGrid;
  private templates: Map<string, string> = new Map();

  constructor() {
    this.sendGrid = new SendGrid(process.env.SENDGRID_API_KEY);
    this.templates.set('scheduled_report', scheduledReportEmailTemplate);
  }

  async sendScheduledReport(package: {
    reportName: string;
    url: string;
    filename: string;
    format: string;
    size: number;
    recipient: string;
  }): Promise<void> {
    const template = this.templates.get('scheduled_report')!;

    const html = template
      .replace('{{reportName}}', package.reportName)
      .replace('{{generatedAt}}', new Date().toLocaleString())
      .replace('{{format}}', package.format.toUpperCase())
      .replace('{{size}}', formatBytes(package.size))
      .replace('{{downloadUrl}}', package.url)
      .replace('{{filename}}', package.filename);

    await this.sendGrid.send({
      to: package.recipient,
      from: 'reports@travelagent.com',
      subject: `Your Scheduled Report: ${package.reportName}`,
      html,
      attachments: [
        {
          filename: package.filename,
          url: package.url,
        },
      ],
    });
  }
}
```

### 4.2 Webhook Delivery

```typescript
// Webhook delivery with retry
class WebhookDeliveryService {
  async deliver(url: string, payload: any, options: WebhookOptions = {}): Promise<WebhookResult> {
    const maxRetries = options.maxRetries || 3;
    const timeout = options.timeout || 30000;

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          return {
            success: true,
            statusCode: response.status,
            attempt,
          };
        }

        lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);

        // Don't retry client errors
        if (response.status >= 400 && response.status < 500) {
          return {
            success: false,
            statusCode: response.status,
            attempt,
            error: lastError.message,
          };
        }

        // Retry server errors with backoff
        if (attempt < maxRetries) {
          await this.backoff(attempt);
        }
      } catch (error) {
        lastError = error as Error;

        if (attempt < maxRetries) {
          await this.backoff(attempt);
        }
      }
    }

    return {
      success: false,
      attempt: maxRetries,
      error: lastError?.message || 'Unknown error',
    };
  }

  private backoff(attempt: number): Promise<void> {
    // Exponential backoff: 2^attempt seconds, max 60 seconds
    const delay = Math.min(Math.pow(2, attempt) * 1000, 60000);
    return new Promise(resolve => setTimeout(resolve, delay));
  }

  // Verify webhook endpoint
  async verify(url: string): Promise<boolean> {
    try {
      const response = await fetch(url, {
        method: 'HEAD',
        signal: AbortSignal.timeout(10000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}
```

---

## 5. Report Versioning

### 5.1 Version Tracking

```typescript
// Report version history
interface ReportVersion {
  id: string;
  reportId: string;
  version: number;
  definition: ReportDefinition;
  createdBy: string;
  createdAt: number;
  description?: string;
}

class ReportVersionManager {
  async createVersion(
    reportId: string,
    definition: ReportDefinition,
    userId: string,
    description?: string
  ): Promise<ReportVersion> {
    // Get current version number
    const latest = await this.getLatestVersion(reportId);
    const nextVersion = (latest?.version || 0) + 1;

    const version: ReportVersion = {
      id: uuid(),
      reportId,
      version: nextVersion,
      definition,
      createdBy: userId,
      createdAt: Date.now(),
      description,
    };

    await db.reportVersions.insert(version);

    return version;
  }

  async getLatestVersion(reportId: string): Promise<ReportVersion | null> {
    return await db.reportVersions.findOne(
      { reportId },
      { sort: { version: -1 } }
    );
  }

  async getVersion(reportId: string, version: number): Promise<ReportVersion | null> {
    return await db.reportVersions.findOne({ reportId, version });
  }

  async listVersions(reportId: string): Promise<ReportVersion[]> {
    return await db.reportVersions.find(
      { reportId },
      { sort: { version: -1 } }
    );
  }

  async rollback(reportId: string, version: number, userId: string): Promise<ReportVersion> {
    const targetVersion = await this.getVersion(reportId, version);
    if (!targetVersion) {
      throw new Error('Version not found');
    }

    // Create new version with old definition
    return await this.createVersion(
      reportId,
      targetVersion.definition,
      userId,
      `Rollback to version ${version}`
    );
  }
}
```

### 5.2 Scheduled Report Versioning

```typescript
// Pin scheduled reports to specific report versions
interface ScheduledReportVersion {
  scheduledReportId: string;
  reportVersion: number;
  pinnedAt: number;
  pinnedBy: string;
}

class ScheduledReportVersionManager {
  // When a report is updated, decide whether to update scheduled reports
  async handleReportUpdate(
    reportId: string,
    newVersion: number,
    updateOption: 'auto' | 'manual' | 'pin'
  ): Promise<void> {
    const scheduledReports = await db.scheduledReports.find({
      reportId,
      active: true,
    });

    for (const scheduled of scheduledReports) {
      switch (updateOption) {
        case 'auto':
          // Automatically use new version
          await db.scheduledReports.update(scheduled.id, {
            reportVersion: newVersion,
          });
          break;

        case 'pin':
          // Keep current version
          await db.scheduledReportVersions.insert({
            scheduledReportId: scheduled.id,
            reportVersion: scheduled.reportVersion || 1,
            pinnedAt: Date.now(),
            pinnedBy: 'system',
          });
          break;

        case 'manual':
          // Notify owner to decide
          await this.notifyVersionConflict(scheduled, newVersion);
          break;
      }
    }
  }

  private async notifyVersionConflict(scheduled: ScheduledReport, newVersion: number): Promise<void> {
    await notificationService.send(scheduled.createdBy, {
      type: 'report_version_conflict',
      title: 'Report Updated',
      body: `Report "${scheduled.name}" has been updated to version ${newVersion}. ` +
            `Your scheduled report is using version ${scheduled.reportVersion || 1}. ` +
            `Review and update if needed.`,
      data: {
        scheduledReportId: scheduled.id,
        reportId: scheduled.reportId,
        currentVersion: scheduled.reportVersion || 1,
        newVersion,
      },
    });
  }
}
```

---

## 6. Failure Handling & Retries

### 6.1 Retry Strategy

```typescript
// Retry configuration for scheduled reports
interface RetryConfig {
  maxRetries: number;
  backoffType: 'exponential' | 'linear' | 'fixed';
  initialDelay: number; // milliseconds
  maxDelay: number; // milliseconds
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  backoffType: 'exponential',
  initialDelay: 60000, // 1 minute
  maxDelay: 3600000, // 1 hour
};

class RetryHandler {
  async executeWithRetry<T>(
    fn: () => Promise<T>,
    config: RetryConfig = defaultRetryConfig
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;

        if (attempt < config.maxRetries) {
          const delay = this.calculateDelay(attempt, config);
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  private calculateDelay(attempt: number, config: RetryConfig): number {
    let delay: number;

    switch (config.backoffType) {
      case 'exponential':
        delay = config.initialDelay * Math.pow(2, attempt);
        break;

      case 'linear':
        delay = config.initialDelay * (attempt + 1);
        break;

      case 'fixed':
        delay = config.initialDelay;
        break;

      default:
        delay = config.initialDelay;
    }

    return Math.min(delay, config.maxDelay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 6.2 Failure Notifications

```typescript
// Handle scheduled report failures
class FailureHandler {
  async handleFailure(scheduleId: string, error: Error, attempt: number): Promise<void> {
    const schedule = await db.scheduledReports.findOne({ id: scheduleId });
    if (!schedule) return;

    // Log failure
    await db.reportExecutionHistory.insert({
      scheduleId,
      status: 'failed',
      error: error.message,
      attempt,
      executedAt: Date.now(),
    });

    // Check if this is the final failure
    const maxRetries = 3;
    if (attempt >= maxRetries) {
      await this.notifyFinalFailure(schedule, error);
    }
  }

  private async notifyFinalFailure(schedule: ScheduledReport, error: Error): Promise<void> {
    await notificationService.send(schedule.createdBy, {
      type: 'scheduled_report_failed',
      title: 'Scheduled Report Failed',
      body: `Your scheduled report "${schedule.name}" has failed after multiple attempts. ` +
            `Error: ${error.message}`,
      data: {
        scheduledReportId: schedule.id,
        error: error.message,
      },
      priority: 'high',
    });

    // Also send email
    await emailService.send({
      to: [await this.getUserEmail(schedule.createdBy)],
      subject: `Scheduled Report Failed: ${schedule.name}`,
      template: 'scheduled_report_failed',
      data: {
        reportName: schedule.name,
        error: error.message,
      },
    });
  }

  private async getUserEmail(userId: string): Promise<string> {
    const user = await db.users.findOne({ id: userId });
    return user?.email || '';
  }
}
```

---

## 7. Scheduling UI

### 7.1 Schedule Configuration Panel

```typescript
// Schedule configuration panel
export const ScheduleConfigPanel: React.FC<{
  schedule: ScheduledReport;
  onUpdate: (updates: Partial<ScheduledReport>) => Promise<void>;
  onToggleActive: () => Promise<void>;
}> = ({ schedule, onUpdate, onToggleActive }) => {
  const [editing, setEditing] = useState(false);

  return (
    <div className={styles.schedulePanel}>
      <div className={styles.header}>
        <div>
          <h3>{schedule.name}</h3>
          <p className={styles.scheduleInfo}>
            {formatSchedule(schedule.schedule)}
          </p>
        </div>
        <Switch
          checked={schedule.active}
          onChange={onToggleActive}
          label={schedule.active ? 'Active' : 'Paused'}
        />
      </div>

      <div className={styles.stats}>
        <Stat
          label="Last Run"
          value={schedule.lastRunAt ? formatDate(schedule.lastRunAt) : 'Never'}
        />
        <Stat
          label="Next Run"
          value={schedule.nextRunAt ? formatDate(schedule.nextRunAt) : 'N/A'}
        />
        <Stat
          label="Total Runs"
          value={schedule.runCount}
        />
      </div>

      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => setEditing(true)}>
          <SettingsIcon /> Configure
        </Button>
        <Button
          variant="secondary"
          onClick={async () => {
            await api.post(`/scheduled-reports/${schedule.id}/run-now`);
            showToast('Report queued for generation', 'success');
          }}
        >
          <PlayIcon /> Run Now
        </Button>
        <Button
          variant="ghost"
          onClick={async () => {
            await api.get(`/scheduled-reports/${schedule.id}/history`);
            // Show history dialog
          }}
        >
          <HistoryIcon /> History
        </Button>
      </div>

      {editing && (
        <ScheduleEditDialog
          schedule={schedule}
          onClose={() => setEditing(false)}
          onSave={async (updates) => {
            await onUpdate(updates);
            setEditing(false);
          }}
        />
      )}
    </div>
  );
};

// Format schedule for display
function formatSchedule(schedule: ScheduleConfig): string {
  if (schedule.type === 'cron') {
    return formatCronExpression(schedule.expression!);
  }
  if (schedule.type === 'interval') {
    return `Every ${schedule.interval} minute${schedule.interval! > 1 ? 's' : ''}`;
  }
  return 'Once';
}

function formatCronExpression(expression: string): string {
  const presets: Record<string, string> = {
    '0 * * * *': 'Hourly',
    '0 0 * * *': 'Daily at midnight',
    '0 9 * * *': 'Daily at 9 AM',
    '0 9 * * 1': 'Weekly on Monday at 9 AM',
    '0 9 1 * *': 'Monthly on the 1st at 9 AM',
    '0 9 1 1,4,7,10 *': 'Quarterly at 9 AM',
  };

  if (presets[expression]) {
    return presets[expression];
  }

  try {
    const parser = require('cron-parser');
    const interval = parser.parseExpression(expression);
    return `Next: ${interval.next().toDate().toLocaleString()}`;
  } catch {
    return expression;
  }
}
```

### 7.2 Schedule Edit Dialog

```typescript
// Edit scheduled report dialog
const ScheduleEditDialog: React.FC<{
  schedule: ScheduledReport;
  onClose: () => void;
  onSave: (updates: Partial<ScheduledReport>) => Promise<void>;
}> = ({ schedule, onClose, onSave }) => {
  const [name, setName] = useState(schedule.name);
  const [scheduleConfig, setScheduleConfig] = useState(schedule.schedule);
  const [output, setOutput] = useState(schedule.output);
  const [delivery, setDelivery] = useState(schedule.delivery);

  const handleSave = async () => {
    await onSave({
      name,
      schedule: scheduleConfig,
      output,
      delivery,
    });
  };

  return (
    <Dialog>
      <DialogTitle>Edit Scheduled Report</DialogTitle>

      <DialogContent>
        <FormField label="Name">
          <Input value={name} onChange={setName} />
        </FormField>

        <FormField label="Schedule">
          <CronBuilder
            value={scheduleConfig.expression!}
            onChange={(expression) => setScheduleConfig({ ...scheduleConfig, expression })}
            timezone={scheduleConfig.timezone}
          />
        </FormField>

        <FormField label="Output Format">
          <Select
            value={output.format}
            onChange={(format) => setOutput({ ...output, format })}
          >
            <option value="xlsx">Excel</option>
            <option value="csv">CSV</option>
            <option value="pdf">PDF</option>
          </Select>
        </FormField>

        <FormField label="Email Recipients">
          <Input
            value={delivery.channels[0]?.config.to?.join(', ') || ''}
            onChange={(to) => setDelivery({
              channels: [{
                type: 'email',
                config: { to: to.split(',').map(s => s.trim()) },
              }],
            })}
            placeholder="email1@example.com, email2@example.com"
          />
        </FormField>
      </DialogContent>

      <DialogActions>
        <Button variant="secondary" onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave}>Save Changes</Button>
      </DialogActions>
    </Dialog>
  );
};
```

### 7.3 Execution History

```typescript
// Execution history component
export const ExecutionHistory: React.FC<{ scheduleId: string }> = ({ scheduleId }) => {
  const [history, setHistory] = useState<ExecutionRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [scheduleId]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api.get(`/scheduled-reports/${scheduleId}/history`);
      setHistory(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.executionHistory}>
      <h4>Execution History</h4>

      {loading ? (
        <Spinner />
      ) : history.length === 0 ? (
        <EmptyState message="No executions yet" />
      ) : (
        <table className={styles.historyTable}>
          <thead>
            <tr>
              <th>Time</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Recipients</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.map(record => (
              <tr key={record.id}>
                <td>{formatDateTime(record.executedAt)}</td>
                <td>
                  <StatusBadge status={record.status} />
                </td>
                <td>{record.duration ? `${record.duration}ms` : '-'}</td>
                <td>{record.recipients || '-'}</td>
                <td>
                  {record.result?.url && (
                    <Button size="sm" variant="ghost" as="a" href={record.result.url} target="_blank">
                      <DownloadIcon />
                    </Button>
                  )}
                  {record.status === 'failed' && (
                    <Button size="sm" variant="ghost" onClick={() => showError(record.error)}>
                      <InfoIcon />
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
```

---

## Summary

The scheduling system enables automated report delivery:

| Component | Purpose |
|-----------|---------|
| **Cron Scheduling** | Flexible time-based triggers using cron expressions |
| **Dynamic Date Ranges** | Auto-calculating relative dates (today, last_month, etc.) |
| **Subscription Management** | User self-service report subscriptions |
| **Delivery Channels** | Email, in-app, webhook delivery |
| **Version Pinning** | Scheduled reports use specific report versions |
| **Retry Logic** | Exponential backoff for transient failures |
| **Failure Notifications** | Alert owners when reports fail |

**Key Takeaways:**
- Use cron expressions for flexible scheduling
- Support dynamic date ranges for recurring reports
- Allow users to subscribe/unsubscribe to reports
- Pin scheduled reports to specific report versions
- Implement retry with exponential backoff
- Notify on failures after max retries
- Track execution history for audit trail

---

**Reporting Module Series Complete!** All 4 documents now available.
