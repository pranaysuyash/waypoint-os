import type { AuditLog, FieldChange } from "@/types/audit";

const SENSITIVE_FIELDS = new Set([
  "passport_number",
  "phone_number",
  "email",
  "date_of_birth",
  "payer_name",
]);

function truncateAndMask(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "";
  if (trimmed.length <= 4) return "*".repeat(trimmed.length);
  return `${trimmed.slice(0, 2)}***${trimmed.slice(-2)}`;
}

function redactString(value: string): string {
  const emailPattern = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i;
  const phonePattern = /\b(?:\+?\d[\d\s-]{7,}\d)\b/;
  const passportPattern = /\b[A-Z]\d{6,8}\b/i;
  if (emailPattern.test(value) || phonePattern.test(value) || passportPattern.test(value)) {
    return "[REDACTED]";
  }
  return truncateAndMask(value);
}

function redactPrimitive(value: string | number | null): string | number | null {
  if (value === null) return null;
  if (typeof value === "number") return value;
  return redactString(value);
}

function redactChange(change: FieldChange): FieldChange {
  const shouldRedactField = SENSITIVE_FIELDS.has(change.field);
  return {
    ...change,
    previousValue: shouldRedactField ? redactPrimitive(change.previousValue) : change.previousValue,
    newValue: shouldRedactField ? redactPrimitive(change.newValue) : change.newValue,
    changedByName: truncateAndMask(change.changedByName),
  };
}

export function isDebugJsonAllowed(): boolean {
  return process.env.NEXT_PUBLIC_ALLOW_DEBUG_JSON === "true";
}

export function shouldRedactAuditExport(): boolean {
  return process.env.NEXT_PUBLIC_ALLOW_RAW_AUDIT_EXPORT !== "true";
}

export function redactAuditLog(log: AuditLog): AuditLog {
  return {
    ...log,
    changes: log.changes.map(redactChange),
  };
}

