import type { Recipe } from "./types";
import { monthYear, emojiFor, escapeHtml, hasRealImage } from "./util";

function thumb(r: Recipe): string {
  const badge = r.photoOnly
    ? `<div class="badge photo">photo</div>`
    : `<div class="badge">${escapeHtml(r.theme)}</div>`;
  if (hasRealImage(r)) {
    return `<img src="/${r.image}" alt="${escapeHtml(r.dish)}" loading="lazy"
        onerror="this.remove()"><div class="emo">${emojiFor(r)}</div>${badge}`;
  }
  return `<div class="emo">${emojiFor(r)}</div>${badge}`;
}

export function recipeCard(r: Recipe): string {
  return `<div class="card" data-id="${r.id}">
    <div class="thumb">${thumb(r)}</div>
    <div class="cbody">
      <div class="theme">${escapeHtml(r.theme)}</div>
      <h3>${escapeHtml(r.dish)}</h3>
      <div class="when">Week ${r.week} · ${monthYear(r.date)}</div>
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
