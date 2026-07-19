import { formatFraction } from "./fractions";
import type { Ingredient } from "./types";

export function scaleQuantity(qty: number | null, base: number, target: number): number | null {
  if (qty === null) return null;
  if (base <= 0) return qty;
  return (qty * target) / base;
}

/** Quantity + unit for display (e.g. "1 ⅓ cup"). Empty string when there is no quantity. */
export function formatQty(ing: Ingredient, base: number, target: number): string {
  const q = scaleQuantity(ing.qty, base, target);
  if (q === null) return "";
  const num = formatFraction(q);
  return ing.unit ? `${num} ${ing.unit}` : num;
}
