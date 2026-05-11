"use client";

import { useSyncExternalStore } from "react";

const subscribeToStaticSnapshot = () => () => {};
const getEmptySnapshot = () => "";

function formatDate(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  if (!dateInput) return "";
  return new Date(dateInput).toLocaleDateString("en-US", options);
}

function formatDateTime(dateInput: string | Date | null | undefined): string {
  if (!dateInput) return "";
  return new Date(dateInput).toLocaleString();
}

function formatTime(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  if (!dateInput) return "";
  return new Date(dateInput).toLocaleTimeString("en-US", options);
}

function useClientDate(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  return useSyncExternalStore(
    subscribeToStaticSnapshot,
    () => formatDate(dateInput, options),
    getEmptySnapshot,
  );
}

function useClientDateTime(
  dateInput: string | Date | null | undefined,
): string {
  return useSyncExternalStore(
    subscribeToStaticSnapshot,
    () => formatDateTime(dateInput),
    getEmptySnapshot,
  );
}

function useClientTime(
  dateInput: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions,
): string {
  return useSyncExternalStore(
    subscribeToStaticSnapshot,
    () => formatTime(dateInput, options),
    getEmptySnapshot,
  );
}

function useClientNow(options?: Intl.DateTimeFormatOptions): string {
  return useSyncExternalStore(
    subscribeToStaticSnapshot,
    () => new Date().toLocaleDateString("en-US", options),
    getEmptySnapshot,
  );
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
