import { expect, test } from "vitest";
import { scaleQuantity, formatQty } from "../src/scale";
import type { Ingredient } from "../src/types";

test("scales linearly and passes null through", () => {
  expect(scaleQuantity(2, 6, 12)).toBe(4);
  expect(scaleQuantity(null, 6, 12)).toBe(null);
  expect(scaleQuantity(1, 0, 12)).toBe(1); // guard against divide-by-zero base
});

test("formats scaled quantity with unit", () => {
  const sugar: Ingredient = { qty: 2 / 3, unit: "cup", item: "sugar", note: null };
  expect(formatQty(sugar, 6, 12)).toBe("1 ⅓ cup");
});

test("no quantity → empty string (note shown elsewhere)", () => {
  const salt: Ingredient = { qty: null, unit: null, item: "salt", note: "to taste" };
  expect(formatQty(salt, 6, 12)).toBe("");
});
