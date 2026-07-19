import { expect, test } from "vitest";
import { sortRecipes } from "../src/sort";
import type { Recipe } from "../src/types";

function mk(id: string, dish: string, date: string, week: number): Recipe {
  return {
    id, week, year: Number(date.slice(0, 4)), date, theme: "T", title: dish, dish,
    subreddit: "52weeksofcooking", track: null, redditUrl: "", sourceUrl: null,
    description: "", image: "", gallery: [], servings: 4,
    ingredients: [], steps: [], tags: [], notes: null, photoOnly: false, postings: [],
  };
}

const data = [
  mk("a", "Banana Bread", "2024-02-01", 5),
  mk("c", "Apple Pie", "2026-01-01", 52),
  mk("b", "Carne Asada", "2025-06-15", 24),
];

test("newest first (by date desc)", () => {
  expect(sortRecipes(data, "newest").map((r) => r.id)).toEqual(["c", "b", "a"]);
});

test("oldest first (by date asc)", () => {
  expect(sortRecipes(data, "oldest").map((r) => r.id)).toEqual(["a", "b", "c"]);
});

test("A–Z by dish", () => {
  expect(sortRecipes(data, "az").map((r) => r.dish)).toEqual([
    "Apple Pie", "Banana Bread", "Carne Asada",
  ]);
});

test("does not mutate input", () => {
  const copy = [...data];
  sortRecipes(data, "newest");
  expect(data).toEqual(copy);
});
