import { expect, test } from "vitest";
import { search } from "../src/search";
import { filterByTags, apply } from "../src/filter";
import type { Recipe } from "../src/types";

function mk(id: string, dish: string, tags: string[], items: string[] = []): Recipe {
  return {
    id, week: 1, year: 2025, date: "2025-01-01", theme: "T", title: dish, dish,
    subreddit: "52weeksofcooking", track: null, redditUrl: "", sourceUrl: null,
    description: "", image: "", gallery: [], servings: 4,
    ingredients: items.map((i) => ({ qty: null, unit: null, item: i, note: null })),
    steps: [], tags, notes: null, photoOnly: false,
  };
}

const data = [
  mk("a", "Chicken Fajitas", ["chicken", "mexican"], ["chicken", "peppers"]),
  mk("b", "Beef Tacos", ["beef", "mexican"], ["ground beef"]),
  mk("c", "Peach Pie", ["dessert"], ["peaches", "flour"]),
];

test("empty tag set returns all", () => {
  expect(filterByTags(data, new Set()).length).toBe(3);
});

test("tags are AND (intersection)", () => {
  expect(filterByTags(data, new Set(["mexican"])).map((r) => r.id)).toEqual(["a", "b"]);
  expect(filterByTags(data, new Set(["mexican", "chicken"])).map((r) => r.id)).toEqual(["a"]);
});

test("search matches dish and ingredients, all terms required", () => {
  expect(search(data, "").length).toBe(3);
  expect(search(data, "peppers").map((r) => r.id)).toEqual(["a"]);
  expect(search(data, "beef tacos").map((r) => r.id)).toEqual(["b"]);
  expect(search(data, "peach flour").map((r) => r.id)).toEqual(["c"]);
});

test("apply combines tags AND search", () => {
  expect(apply(data, "fajitas", new Set(["mexican"])).map((r) => r.id)).toEqual(["a"]);
});
