import { describe, expect, it } from "vitest";
import { getPasswordStrength } from "../password-strength";

describe("getPasswordStrength", () => {
  it("classifies weak passwords", () => {
    expect(getPasswordStrength("").label).toBe("Weak");
    expect(getPasswordStrength("abc").label).toBe("Weak");
  });

  it("classifies fair and good passwords", () => {
    expect(getPasswordStrength("abcdefgh").label).toBe("Fair");
    expect(getPasswordStrength("Abcdefgh1").label).toBe("Good");
  });

  it("classifies strong passwords", () => {
    expect(getPasswordStrength("Abcd1234!xyz").label).toBe("Strong");
  });
});
