import { describe, expect, it } from "vitest";
import { formatAuthRedirectLabel, resolveSafeRedirect } from "../auth-redirect";

describe("resolveSafeRedirect", () => {
  it("returns fallback for empty values", () => {
    expect(resolveSafeRedirect(undefined, "/overview")).toBe("/overview");
    expect(resolveSafeRedirect(null, "/overview")).toBe("/overview");
    expect(resolveSafeRedirect("", "/overview")).toBe("/overview");
  });

  it("allows safe internal paths", () => {
    expect(resolveSafeRedirect("/trips")).toBe("/trips");
    expect(resolveSafeRedirect("/reviews?tab=open")).toBe("/reviews?tab=open");
    expect(resolveSafeRedirect("/inbox#priority")).toBe("/inbox#priority");
  });

  it("blocks auth-page loops", () => {
    expect(resolveSafeRedirect("/login?redirect=/overview")).toBe("/overview");
    expect(resolveSafeRedirect("/signup?invite=abc")).toBe("/overview");
  });

  it("blocks external and protocol-relative redirects", () => {
    expect(resolveSafeRedirect("https://evil.com")).toBe("/overview");
    expect(resolveSafeRedirect("//evil.com/path")).toBe("/overview");
  });
});

describe("formatAuthRedirectLabel", () => {
  it("formats known app routes as operator-facing labels", () => {
    expect(formatAuthRedirectLabel("/overview")).toBe("Overview");
    expect(formatAuthRedirectLabel("/trips")).toBe("Trips in Planning");
    expect(formatAuthRedirectLabel("/trips/123?tab=reviews&mode=full")).toBe("Trips in Planning");
    expect(formatAuthRedirectLabel("/reviews?status=pending")).toBe("Quote Review");
  });

  it("formats workbench tab context without exposing query strings", () => {
    expect(formatAuthRedirectLabel("/workbench?draft=new&tab=safety")).toBe("New Inquiry - Risk Review");
    expect(formatAuthRedirectLabel("/workbench?draft=new&tab=intake")).toBe("New Inquiry");
  });

  it("formats settings tab context", () => {
    expect(formatAuthRedirectLabel("/settings?tab=people")).toBe("Settings - People");
  });

  it("uses the safe fallback label for unsafe redirects", () => {
    expect(formatAuthRedirectLabel("https://evil.com")).toBe("Overview");
  });
});
