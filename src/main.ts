import "./style.css";
import { recipes, allTags, byId } from "./data";
import { apply } from "./filter";
import { sortRecipes, type SortMode } from "./sort";
import { renderGrid } from "./cards";
import { renderRecipe } from "./recipe";
import { escapeHtml } from "./util";

const app = document.querySelector<HTMLElement>("#app")!;

const TAGS = allTags();
const TAG_COUNTS = new Map<string, number>();
for (const r of recipes) for (const t of r.tags) TAG_COUNTS.set(t, (TAG_COUNTS.get(t) ?? 0) + 1);

const state = { q: "", tags: new Set<string>(), sort: "newest" as SortMode };

function renderIndex(): void {
  app.innerHTML = `<div class="wrap">
    <header class="site">
      <h1 id="home">🍳 Walker Family Recipes</h1>
      <span class="sub">52 weeks of cooking &amp; baking</span>
    </header>
    <div class="controls">
      <div class="searchrow">
        <input class="search" id="search" placeholder="Search recipes, ingredients, themes…"
               value="${escapeHtml(state.q)}" autocomplete="off">
        <select class="sort" id="sort" aria-label="Sort recipes">
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
          <option value="az">A–Z</option>
        </select>
      </div>
      <div class="tags" id="tags"></div>
    </div>
    <div class="count" id="count"></div>
    <div class="grid" id="grid"></div>
  </div>`;

  const grid = app.querySelector<HTMLElement>("#grid")!;
  const count = app.querySelector<HTMLElement>("#count")!;
  const tagsEl = app.querySelector<HTMLElement>("#tags")!;
  const searchEl = app.querySelector<HTMLInputElement>("#search")!;
  const sortEl = app.querySelector<HTMLSelectElement>("#sort")!;
  sortEl.value = state.sort;

  const drawTags = () => {
    tagsEl.innerHTML =
      TAGS.map(
        (t) =>
          `<span class="chip ${state.tags.has(t) ? "on" : ""}" data-tag="${t}">${t}<span class="n">${TAG_COUNTS.get(t)}</span></span>`,
      ).join("") +
      (state.tags.size ? `<span class="clear" id="clear">clear all</span>` : "");
  };

  const update = () => {
    const list = sortRecipes(apply(recipes, state.q, state.tags), state.sort);
    const active = [...state.tags];
    count.innerHTML =
      state.q || active.length
        ? `Showing ${list.length} of ${recipes.length}` +
          (active.length ? ` · ${active.map((t) => `<b>${t}</b>`).join(" + ")}` : "")
        : `Showing all ${recipes.length} recipes`;
    renderGrid(grid, list);
    drawTags();
  };

  searchEl.addEventListener("input", () => {
    state.q = searchEl.value;
    update();
  });
  sortEl.addEventListener("change", () => {
    state.sort = sortEl.value as SortMode;
    update();
  });
  tagsEl.addEventListener("click", (e) => {
    const chip = (e.target as HTMLElement).closest<HTMLElement>(".chip");
    if (chip) {
      const t = chip.dataset.tag!;
      state.tags.has(t) ? state.tags.delete(t) : state.tags.add(t);
      update();
      return;
    }
    if ((e.target as HTMLElement).id === "clear") {
      state.tags.clear();
      update();
    }
  });
  grid.addEventListener("click", (e) => {
    const card = (e.target as HTMLElement).closest<HTMLElement>(".card");
    if (card) location.hash = `#/recipe/${encodeURIComponent(card.dataset.id!)}`;
  });
  app.querySelector("#home")!.addEventListener("click", () => {
    state.q = "";
    state.tags.clear();
    if (location.hash === "#/" || location.hash === "") update();
    else location.hash = "#/";
  });

  update();
}

function route(): void {
  const m = location.hash.match(/^#\/recipe\/(.+)$/);
  if (m) {
    const r = byId(decodeURIComponent(m[1]));
    if (r) {
      window.scrollTo(0, 0);
      app.innerHTML = `<div class="wrap"></div>`;
      renderRecipe(app.querySelector<HTMLElement>(".wrap")!, r);
      return;
    }
  }
  renderIndex();
}

window.addEventListener("hashchange", route);
route();
