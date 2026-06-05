import { describe, expect, it } from "vitest";
import { percent } from "./progress";

describe("percent", () => {
  it("returns 0 when total is zero", () => {
    expect(percent(3, 0)).toBe(0);
  });
  it("computes a rounded percentage", () => {
    expect(percent(1, 3)).toBe(33);
    expect(percent(2, 4)).toBe(50);
  });
  it("clamps to 100", () => {
    expect(percent(5, 4)).toBe(100);
  });
});
