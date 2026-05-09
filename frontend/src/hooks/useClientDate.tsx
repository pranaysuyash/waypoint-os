"use client";

import { useState, useEffect } from "react";

function useClientDate(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  const [formatted, setFormatted] = useState("");
  useEffect(() => {
    if (!dateInput) {
      setFormatted("");
      return;
    }
    const d = new Date(dateInput);
    setFormatted(d.toLocaleDateString("en-US", options));
  }, [dateInput]);
  return formatted;
}

function useClientDateTime(
  dateInput: string | Date | null | undefined,
): string {
  const [formatted, setFormatted] = useState("");
  useEffect(() => {
    if (!dateInput) {
      setFormatted("");
      return;
    }
    const d = new Date(dateInput);
    setFormatted(d.toLocaleString());
  }, [dateInput]);
  return formatted;
}

function useClientTime(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  const [formatted, setFormatted] = useState("");
  useEffect(() => {
    if (!dateInput) {
      setFormatted("");
      return;
    }
    const d = new Date(dateInput);
    setFormatted(d.toLocaleTimeString("en-US", options));
  }, [dateInput]);
  return formatted;
}

function useClientNow(options?: Intl.DateTimeFormatOptions): string {
  const [value, setValue] = useState("");
  useEffect(() => {
    setValue(new Date().toLocaleDateString("en-US", options));
  }, []);
  return value;
}

// ─── Component wrappers for use in JSX (avoids inline hook calls) ───

export function ClientDate({
  value,
  options,
}: {
  value: string | Date | null | undefined;
  options?: Intl.DateTimeFormatOptions;
}) {
  return <>{useClientDate(value, options)}</>;
}

export function ClientDateTime({
  value,
}: {
  value: string | Date | null | undefined;
}) {
  return <>{useClientDateTime(value)}</>;
}

export function ClientTime({
  value,
  options,
}: {
  value: string | Date | null | undefined;
  options?: Intl.DateTimeFormatOptions;
}) {
  return <>{useClientTime(value, options)}</>;
}

export function ClientNow({
  options,
}: {
  options?: Intl.DateTimeFormatOptions;
}) {
  return <>{useClientNow(options)}</>;
}
