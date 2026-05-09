"use client";

import { useState, useEffect } from "react";

export function useClientDate(
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

export function useClientDateTime(
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

export function useClientTime(
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

export function useClientDateString(): string {
  const [value, setValue] = useState("");
  useEffect(() => {
    setValue(new Date().toISOString());
  }, []);
  return value;
}

export function useClientNow(options?: Intl.DateTimeFormatOptions): string {
  const [value, setValue] = useState("");
  useEffect(() => {
    setValue(new Date().toLocaleDateString("en-US", options));
  }, []);
  return value;
}

export function useClientRelativeTime(dateInput: string | Date): string {
  const [text, setText] = useState("");
  useEffect(() => {
    const diff = Date.now() - new Date(dateInput).getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days === 0) setText("today");
    else if (days === 1) setText("yesterday");
    else if (days < 7) setText(`${days} days ago`);
    else setText(`${Math.floor(days / 7)} weeks ago`);
  }, [dateInput]);
  return text;
}
