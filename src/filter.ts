import type { Recipe } from "./types";
import { search } from "./search";

/** Recipe must contain ALL selected tags (AND). Empty selection → all. */
export function filterByTags(recipes: Recipe[], tags: Set<string>): Recipe[] {
  if (tags.size === 0) return recipes;
  return recipes.filter((r) => [...tags].every((t) => r.tags.includes(t)));
}

/** Tag filter AND text search combined. */
export function apply(recipes: Recipe[], query: string, tags: Set<string>): Recipe[] {
  return search(filterByTags(recipes, tags), query);
}
