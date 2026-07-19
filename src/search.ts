import type { Recipe } from "./types";

function haystack(r: Recipe): string {
  return [r.dish, r.title, r.theme, r.track ?? "", ...r.tags, ...r.ingredients.map((i) => i.item)]
    .join(" ")
    .toLowerCase();
}

/** Every whitespace-separated term must appear somewhere in the recipe. Empty query → all. */
export function search(recipes: Recipe[], query: string): Recipe[] {
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (terms.length === 0) return recipes;
  return recipes.filter((r) => {
    const hay = haystack(r);
    return terms.every((t) => hay.includes(t));
  });
}
