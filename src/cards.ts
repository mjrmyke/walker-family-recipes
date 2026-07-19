import type { Recipe } from "./types";
import { monthYear, emojiFor, escapeHtml, hasRealImage, asset } from "./util";

function badges(r: Recipe): string {
  // The theme (the week's assignment) always shows; photo-only gets an extra marker.
  const theme = `<div class="badge">${escapeHtml(r.theme)}</div>`;
  const photo = r.photoOnly ? `<div class="badge photo">photo only</div>` : "";
  return theme + photo;
}

function thumb(r: Recipe): string {
  if (hasRealImage(r)) {
    return `<img src="${asset(r.image)}" alt="${escapeHtml(r.dish)}" loading="lazy"
        onerror="this.remove()"><div class="emo">${emojiFor(r)}</div>${badges(r)}`;
  }
  return `<div class="emo">${emojiFor(r)}</div>${badges(r)}`;
}

export function recipeCard(r: Recipe): string {
  return `<div class="card" data-id="${r.id}">
    <div class="thumb">${thumb(r)}</div>
    <div class="cbody">
      <div class="theme">Week ${r.week} · ${escapeHtml(r.theme)}</div>
      <h3>${escapeHtml(r.dish)}</h3>
      <div class="when">${monthYear(r.date)}</div>
      <p>${escapeHtml(r.description)}</p>
      <div class="cchips">${r.tags.map((t) => `<span>${t}</span>`).join("")}</div>
    </div>
  </div>`;
}

export function renderGrid(container: HTMLElement, list: Recipe[]): void {
  container.innerHTML = list.length
    ? list.map(recipeCard).join("")
    : `<div class="empty">No recipes match. Try clearing a tag or your search.</div>`;
}
