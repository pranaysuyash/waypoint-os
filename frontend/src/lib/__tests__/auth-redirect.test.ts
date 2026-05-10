import { describe, expect, it } from "vitest";
import { resolveSafeRedirect } from "../auth-redirect";

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
