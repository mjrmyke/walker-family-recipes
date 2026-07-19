import type { Recipe } from "./types";
import { formatQty } from "./scale";
import { fullDate, emojiFor, escapeHtml, hasRealImage, asset } from "./util";
import { getChecked, setChecked, resetChecked } from "./checklist";

function hero(r: Recipe): string {
  if (hasRealImage(r)) {
    return `<img src="${asset(r.image)}" alt="${escapeHtml(r.dish)}" onerror="this.remove()">
      <div class="emo">${emojiFor(r)}</div>`;
  }
  return `<div class="emo">${emojiFor(r)}</div>`;
}

function sourceLinks(r: Recipe, primaryLabel: string): string {
  const parts = [
    r.sourceUrl
      ? `<a class="primary" href="${escapeHtml(r.sourceUrl)}" target="_blank" rel="noopener">${primaryLabel}</a>`
      : "",
    `<a href="${escapeHtml(r.redditUrl)}" target="_blank" rel="noopener">Frankie's Reddit post</a>`,
  ];
  return `<div class="links">${parts.join("")}</div>`;
}

export function renderRecipe(container: HTMLElement, r: Recipe): void {
  const meta = `Week ${r.week} · <b>${escapeHtml(r.theme)}</b> · ${fullDate(r.date)} · r/${escapeHtml(r.subreddit)}`;

  let body: string;
  if (r.photoOnly) {
    body = `<p class="photo-note">${escapeHtml(r.notes || "Photo only — see the original post.")}</p>
      ${sourceLinks(r, "View recipe →")}`;
  } else {
    body = `<div class="cols">
      <div>
        <div class="scaler">
          <div class="top"><b>Servings</b>
            <span class="val"><strong id="sv">${r.servings}</strong> <span class="mult" id="mult"></span></span>
          </div>
          <input type="range" id="slider" min="1" max="48" value="${r.servings}">
          <div class="ticks"><span>1</span><span>12</span><span>24</span><span>36</span><span>48</span></div>
        </div>
        <h4 class="sec">Ingredients — tap to check off <span class="reset" id="reset">reset</span></h4>
        <ul class="ing" id="ing"></ul>
      </div>
      <div>
        <h4 class="sec">Method</h4>
        <ol class="steps">${r.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ol>
        ${r.notes ? `<p class="photo-note">${escapeHtml(r.notes)}</p>` : ""}
        ${sourceLinks(r, "Full recipe source →")}
      </div>
    </div>`;
  }

  container.innerHTML = `<a class="back" href="#/">← All recipes</a>
    <div class="detail">
      <div class="hero">${hero(r)}</div>
      <div class="dbody">
        <h2>${escapeHtml(r.dish)}</h2>
        <div class="meta">${meta}</div>
        <p class="desc">${escapeHtml(r.description)}</p>
        ${body}
      </div>
    </div>`;

  if (r.photoOnly) return;

  const slider = container.querySelector<HTMLInputElement>("#slider")!;
  const ing = container.querySelector<HTMLElement>("#ing")!;
  const sv = container.querySelector<HTMLElement>("#sv")!;
  const mult = container.querySelector<HTMLElement>("#mult")!;

  const draw = () => {
    const target = Number(slider.value);
    const m = target / r.servings;
    sv.textContent = String(target);
    mult.textContent = m === 1 ? "(1× · base recipe)" : `(${Math.round(m * 100) / 100}×)`;
    slider.style.setProperty("--fill", `${((target - 1) / (48 - 1)) * 100}%`);
    const checked = getChecked(r.id);
    ing.innerHTML = r.ingredients
      .map((i, idx) => {
        const q = formatQty(i, r.servings, target);
        const note = i.note ? ` <span class="note">(${escapeHtml(i.note)})</span>` : "";
        return `<li data-idx="${idx}" class="${checked.has(idx) ? "checked" : ""}">
          <span class="box">✓</span><span class="qty">${q}</span>
          <span>${escapeHtml(i.item)}${note}</span></li>`;
      })
      .join("");
  };
  draw();

  slider.addEventListener("input", draw);
  ing.addEventListener("click", (e) => {
    const li = (e.target as HTMLElement).closest("li");
    if (!li) return;
    const idx = Number(li.dataset.idx);
    const on = !li.classList.contains("checked");
    li.classList.toggle("checked", on);
    setChecked(r.id, idx, on);
  });
  container.querySelector("#reset")!.addEventListener("click", () => {
    resetChecked(r.id);
    draw();
  });
}
