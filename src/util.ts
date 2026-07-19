import type { Recipe } from "./types";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_FULL = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

export function monthYear(date: string): string {
  const [y, m] = date.split("-").map(Number);
  return `${MONTHS[(m || 1) - 1]} ${y}`;
}

export function fullDate(date: string): string {
  const [y, m, d] = date.split("-").map(Number);
  return `${MONTHS_FULL[(m || 1) - 1]} ${d}, ${y}`;
}

const EMOJI: [string, string][] = [
  ["dessert", "🍰"], ["bread", "🍞"], ["soup", "🍲"], ["salad", "🥗"], ["chicken", "🍗"],
  ["beef", "🥩"], ["pork", "🥓"], ["seafood", "🦐"], ["egg", "🍳"], ["sauce", "🥫"],
  ["mexican", "🌮"], ["italian", "🍝"], ["japanese", "🍜"], ["grill", "🔥"],
];

export function emojiFor(r: Recipe): string {
  for (const [tag, e] of EMOJI) if (r.tags.includes(tag)) return e;
  return "🍽️";
}

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

export function hasRealImage(r: Recipe): boolean {
  return !!r.image && !r.image.endsWith("placeholder.webp");
}
