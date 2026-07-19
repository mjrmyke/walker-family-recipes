import type { Recipe } from "./types";

export type SortMode = "newest" | "oldest" | "az";

/** Returns a new sorted array (does not mutate input). */
export function sortRecipes(list: Recipe[], mode: SortMode): Recipe[] {
  const arr = [...list];
  if (mode === "az") return arr.sort((a, b) => a.dish.localeCompare(b.dish));
  // date is YYYY-MM-DD, so string compare = chronological
  arr.sort((a, b) => a.date.localeCompare(b.date) || a.week - b.week);
  if (mode === "newest") arr.reverse();
  return arr;
}
