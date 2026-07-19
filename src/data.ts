import raw from "./data/recipes.json";
import type { Recipe } from "./types";

export const recipes = raw as Recipe[];

/** All tags, most-used first (ties alphabetical). */
export function allTags(): string[] {
  const counts = new Map<string, number>();
  for (const r of recipes) {
    for (const t of r.tags) counts.set(t, (counts.get(t) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([t]) => t);
}

export function byId(id: string): Recipe | undefined {
  return recipes.find((r) => r.id === id);
}
