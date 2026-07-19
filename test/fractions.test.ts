import { expect, test } from "vitest";
import { formatFraction } from "../src/fractions";

test("whole numbers", () => {
  expect(formatFraction(2)).toBe("2");
  expect(formatFraction(0)).toBe("0");
});

test("common fractions", () => {
  expect(formatFraction(0.5)).toBe("½");
  expect(formatFraction(2 / 3)).toBe("⅔");
  expect(formatFraction(1 / 3)).toBe("⅓");
});

test("mixed numbers", () => {
  expect(formatFraction(1.5)).toBe("1 ½");
  expect(formatFraction(1 + 1 / 3)).toBe("1 ⅓");
});

test("snaps to nearest and carries up", () => {
  expect(formatFraction(0.34)).toBe("⅓");
  expect(formatFraction(0.99)).toBe("1");
});
