# Recipe Website Implementation Plan (Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A dark-mode, LAN-served static SPA over `src/data/recipes.json` — searchable, tag-filterable card grid; recipe view with ingredient checkboxes and a sliding servings scaler.

**Architecture:** Vite + TypeScript, no UI framework. Pure-logic modules (search, filter, fraction scaling) are TDD'd with Vitest; rendering is plain DOM. Hash-based routing (`#/recipe/<id>`). The approved mockup (`.superpowers/brainstorm/.../card-mockup-v3.html`) is the visual reference — port its CSS/markup.

**Tech Stack:** Vite 5, TypeScript, Vitest. Node 24 (installed). Run on LAN via `vite --host`.

**Design (locked from the approved mockup):** dark warm palette; card = image/theme badge/dish/date/description/tag chips; controls = search input + tag rail (multi-select, AND semantics, empty = all, "clear all"); recipe view = hero image, `Week N · Theme · date · subreddit`, servings slider (2→48) with live fraction-snapped quantities, tap-to-check ingredients (persist in localStorage), numbered steps, source links. photoOnly recipes render as image + "View recipe →" (external `sourceUrl`) / "View on Reddit", with cook UI hidden.

---

## File Structure
```
walker-family-recipes/
  package.json  vite.config.ts  tsconfig.json  index.html
  public/images/…                      # already present (vendored webp)
  src/
    data/recipes.json                  # already present
    types.ts        # Recipe, Ingredient
    data.ts         # load recipes.json, build tag list
    fractions.ts    # formatFraction (mirror of Python)
    scale.ts        # scaleQuantity + format
    search.ts       # text filter
    filter.ts       # tag filter (AND, empty=all) + search combine
    cards.ts        # grid render
    recipe.ts       # detail view render
    checklist.ts    # localStorage checkbox state
    router.ts       # hash routing
    main.ts         # wire together
    style.css       # ported from mockup
  test/
    fractions.test.ts  search.test.ts  filter.test.ts  scale.test.ts
```

---

## Task 1: Scaffold Vite + TS + Vitest

**Files:** Create `package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.ts`, `src/style.css`

- [ ] **Step 1:** From repo root, scaffold and install:
```bash
npm create vite@latest . -- --template vanilla-ts   # if dir non-empty, keep existing files
npm install
npm install -D vitest
```
If `npm create` refuses (non-empty dir), instead create the files by hand (steps below) and `npm install`.

- [ ] **Step 2:** `package.json` scripts:
```json
{ "scripts": { "dev": "vite --host", "build": "vite build", "preview": "vite preview --host", "test": "vitest run" } }
```

- [ ] **Step 3:** Add `"test": "vitest run"` works: `npm test` → "no test files" (exit 0 acceptable until tests exist).

- [ ] **Step 4:** Ensure `src/data/recipes.json` and `public/images/` are served (they already exist). Vite serves `public/` at `/`, so image paths `images/x.webp` resolve at `/images/x.webp`. `recipes.json` is imported from `src/data/`.

- [ ] **Step 5: Commit** `chore: scaffold vite+ts recipe site`.

## Task 2: Types + data loader (`src/types.ts`, `src/data.ts`)
- [ ] Define `Ingredient {qty:number|null; unit:string|null; item:string; note:string|null}` and `Recipe` (all fields from recipes.json incl `photoOnly`).
- [ ] `data.ts`: `import recipes from "./data/recipes.json"` (enable `resolveJsonModule`), export typed `recipes: Recipe[]` and `allTags(): string[]` (sorted unique tags, by frequency).
- [ ] Commit.

## Task 3: Fraction formatter (`src/fractions.ts`) — TDD
Port the Python `format_fraction`. Test the SAME cases as `tests/test_fractions.py`.
- [ ] **Test** `test/fractions.test.ts`:
```ts
import { expect, test } from "vitest";
import { formatFraction } from "../src/fractions";
test("wholes", () => { expect(formatFraction(2)).toBe("2"); expect(formatFraction(0)).toBe("0"); });
test("fractions", () => { expect(formatFraction(0.5)).toBe("½"); expect(formatFraction(2/3)).toBe("⅔"); expect(formatFraction(1/3)).toBe("⅓"); });
test("mixed", () => { expect(formatFraction(1.5)).toBe("1 ½"); expect(formatFraction(1+1/3)).toBe("1 ⅓"); });
test("snaps", () => { expect(formatFraction(0.34)).toBe("⅓"); expect(formatFraction(0.99)).toBe("1"); });
```
- [ ] Run → fails. Implement snapping to nearest of `{0,⅛,¼,⅓,½,⅔,¾,⅞,1}` with carry. Run → passes. Commit.

## Task 4: Scaling (`src/scale.ts`) — TDD
- [ ] `scaleQuantity(qty:number|null, base:number, target:number): number|null` = qty * target/base (null→null).
- [ ] `formatQty(ing, base, target): string` = `formatFraction(scaled)` + ` ` + unit (or "" when qty null → note like "to taste").
- [ ] Test: `formatQty({qty:2/3,unit:"cup",item:"sugar",note:null}, 6, 12)` → `"1 ⅓ cup"`; null qty → shows note. Commit.

## Task 5: Search + filter (`src/search.ts`, `src/filter.ts`) — TDD
- [ ] `search(recipes, q)`: case-insensitive match over dish/title/theme/tags/ingredient items. Empty q → all.
- [ ] `filterByTags(recipes, tags:Set<string>)`: recipe must contain ALL selected tags (AND). Empty set → all.
- [ ] `apply(recipes, q, tags)` combines both (AND).
- [ ] Tests incl: empty tags returns all; two tags = intersection; search matches an ingredient; combined narrows. Implement. Commit.

## Task 6: Card grid (`src/cards.ts`)
- [ ] `renderCards(container, recipes)`: build the mockup card markup (image with `loading="lazy"`, theme badge, dish, `Mon YYYY` from `date`, description, tag chips). Image `src="/${recipe.image}"`; on error, swap to a themed emoji placeholder. Clicking a card sets `location.hash = '#/recipe/'+id`.
- [ ] A results count line ("Showing N of 179" / "Showing all"). Commit.

## Task 7: Recipe detail (`src/recipe.ts`, `src/checklist.ts`)
- [ ] `renderRecipe(container, recipe)`: hero image, `Week N · Theme · <formatted date> · r/<subreddit>`, then:
  - If `photoOnly`: show note + buttons — "View recipe →" (`sourceUrl`, if present) and "View on Reddit" (`redditUrl`). No cook UI.
  - Else: servings slider (min 1, max 48, value=servings) with live readout `N (×M)`; ingredient `<li>` list where each row shows `formatQty(...)` + item (+ note) and toggles a checked class on click; numbered steps; source links.
- [ ] `checklist.ts`: persist checked ingredient indices per recipe id in `localStorage` (`checked:<id>`), restore on render, "reset" clears. Slider `input` re-renders quantities live (checked state preserved).
- [ ] Commit.

## Task 8: Router + main (`src/router.ts`, `src/main.ts`, `src/style.css`)
- [ ] `router.ts`: on `hashchange`/load — `#/recipe/<id>` → detail view (with a "← Back" link to `#/`); otherwise the index (controls + grid). 
- [ ] `main.ts`: build header + controls (search input, tag rail from `allTags()`), maintain `{q, activeTags}` state, re-render grid on change; render "clear all" when tags active; handle empty-state message.
- [ ] `style.css`: port the mockup's dark palette + all component styles (cards, chips, slider, ingredient rows, detail).
- [ ] Commit.

## Task 9: Run, verify on the app, screenshot
- [ ] `npm run dev -- --host`; open `http://localhost:5173`.
- [ ] With the Playwright browser: load the site, screenshot the grid; click the "chicken" tag → verify grid narrows to chicken dishes; open a recipe; drag the servings slider → verify quantities scale; check an ingredient → verify it persists across a slider change; open a photoOnly recipe → verify link buttons and no cook UI. Fix any issues.
- [ ] Print the LAN URL (`http://<machine-ip>:5173`) for phone access.
- [ ] Commit.

## Task 10: Final review + finish
- [ ] Full `npm test` green; `npm run build` succeeds.
- [ ] Final code review of `src/`. Address findings. Merge `feat/data-pipeline` → `master` (or open for user review).
