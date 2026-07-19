# Walker Family Recipes — Design

**Date:** 2026-07-19
**Status:** Approved (design), pending implementation plan

## 1. Summary

A private, static, searchable cookbook website for the Walker family's "52 weeks of
cooking & baking" recipes, originally posted by **Frankie** (Reddit user `Frankiieee`)
in r/52weeksofcooking and r/52weeksofbaking. Each recipe is presented as a card (photo +
short description). Opening a card shows the full recipe with **checkbox ingredients** and
a **sliding serving-size scaler** that recomputes ingredient quantities live. The site is
searchable by free text and filterable by **suggested tags** (e.g. "chicken" → every chicken
dish).

Primary use case: **finding and cooking recipes** — phone-friendly, in the kitchen.

## 2. Goals & Non-Goals

**Goals**
- Show every real recipe from both subreddits (all tracks) as a browsable card grid.
- Rich, structured recipe data: description, image(s), ingredients, steps, tags, week + date.
- Live search + tag filtering.
- Ingredient checkboxes (check off while shopping/cooking).
- Sliding servings scaler that scales ingredient quantities.
- Dark-mode, warm "cookbook" aesthetic; responsive/mobile-first.
- Self-contained: images vendored into the repo (no external hotlinks).
- Runs locally, reachable on the home LAN (wife can view on her phone).

**Non-Goals (for now)**
- No public internet deployment (kept local/LAN only for this phase).
- No user accounts, comments, ratings, or backend server.
- No in-browser data editing / admin UI (deferred — see Phase 4).
- No meal planning, shopping-list export, or nutrition data.

## 3. Key Decisions (locked)

| Decision | Choice |
| --- | --- |
| Project name | `walker-family-recipes` |
| Stack | Vite + TypeScript static SPA (no framework), plain JS/DOM rendering |
| Hosting | Local only, LAN-accessible via `vite --host` |
| Data richness | LLM-extracted **structured** ingredients (qty/unit/item), steps, tags |
| Images | **Downloaded & vendored** into the repo (optimized `.webp`) |
| Scope | All cooking + baking recipes, all tracks; exclude recap/off-topic posts |
| Theme | Dark mode, warm palette |
| Servings scaler | **Slider** (continuous), not preset buttons |
| Tag filtering | AND semantics (recipe must match all selected tags); **empty selection = show all** |
| Recipe metadata | Show **week + full date** (from post `created_utc`) |
| Git | Private repo (`walker-family-recipes`), independent of the parent `local-dev` repo |

## 4. Architecture — two independent parts

The system splits cleanly into a **data pipeline** (run occasionally, offline) and the
**website** (static, consumes the pipeline's output). The only interface between them is
`recipes.json` + the `public/images/` directory. Either side can be rebuilt without touching
the other. The website never contacts Reddit.

```
Reddit (Frankie's posts + comments)
        │  [Playwright browser session — bypasses Reddit's bot 403s]
        ▼
┌─────────────────────────────────────┐
│  PART A: Data pipeline (Python)      │
│  1. Harvest posts (paginated JSON)   │
│  2. Fetch each post's comments       │
│  3. Resolve + download images        │
│  4. LLM-structure recipe text        │
│  5. Auto-tag                         │
└─────────────────────────────────────┘
        │  writes
        ▼
   recipes.json  +  public/images/*.webp
        │  read at load
        ▼
┌─────────────────────────────────────┐
│  PART B: Website (Vite + TS SPA)     │
│  card grid · search · tag filter ·   │
│  recipe view · checkboxes · scaler   │
└─────────────────────────────────────┘
```

### 4.1 Why Playwright for harvesting
`curl`, `old.reddit.com`, and the WebFetch tool all receive **HTTP 403** from Reddit's bot
protection. A real, logged-in browser session (the existing Playwright MCP setup) reaches
Reddit's public JSON API (`/user/Frankiieee/submitted/.json`, `/<permalink>/.json`) reliably.
The pipeline drives that browser to pull JSON, then processes it in Python.

## 5. Data pipeline (Part A)

Language: **Python 3.14** (per environment). Runs as a sequence of scripts / a small package
under `pipeline/`. Intermediate artifacts cached under `data/raw/` (git-ignored) so steps are
re-runnable without re-scraping.

### 5.1 Harvest posts
- Page through `https://www.reddit.com/user/Frankiieee/submitted/.json?limit=100&after=<cursor>`
  via the Playwright browser until `after` is null. (~130–150 posts total.)
- **Filter to keep** posts where `subreddit ∈ {52weeksofcooking, 52weeksofbaking}` AND the
  title matches the `Week N: <Theme> - <Dish>` pattern.
- **Filter out** recap posts (titles like "Week 1 - 52", "Challenge Complete"), moderator-
  removed posts, and anything off-topic (e.g. the stray r/excel post).

### 5.2 Fetch recipe text from comments
- Each post body is empty; the recipe is in **Frankie's own comment**. For each kept post,
  fetch `<permalink>.json` and select the top-level comment authored by `Frankiieee`
  (fallback: the longest comment by Frankie if multiple).
- Also capture any recipe URL Frankie links in that comment (`sourceUrl`).

### 5.3 Resolve & download images
- Image sources seen: `i.redd.it` (direct), imgur **single** (`imgur.com/<id>`), imgur
  **albums** (`imgur.com/a/<id>`), and Reddit galleries.
- **Resolve rules:**
  - `i.redd.it/<x>.jpg` → download directly.
  - `imgur.com/<id>` → `https://i.imgur.com/<id>.jpeg`.
  - `imgur.com/a/<id>` (album) → resolve to member images (imgur page/API); take the first
    as the card/hero image, keep the rest as `gallery[]`.
  - Reddit gallery → use `media_metadata` to get each image URL.
- **Validation:** imgur returns its "image does not exist / removed" placeholder with **HTTP
  200**, so status code is not enough. Reject images whose decoded dimensions match the known
  imgur placeholder (161×81) or that are suspiciously tiny; fall back to the Reddit preview
  thumbnail, then to a themed emoji placeholder.
- Download once, re-encode to optimized `.webp` (a reasonable max width, e.g. 1200px, plus a
  smaller card variant), write to `public/images/`. Filenames derived from a stable slug
  (e.g. `week-28-cornbread-and-baked-beans.webp`).

### 5.4 Structure the recipe text (LLM)
- For each recipe, an LLM pass converts Frankie's free-text comment into the structured schema
  (§6): parse ingredient lines into `{qty, unit, item, note}`, split method into ordered
  `steps[]`, infer `servings`, write a one-line card `description`, and carry over `notes`
  (tips, "(fail)", substitutions).
- **Quantity model:** store `qty` as an exact value (integer, decimal, or rational). The
  website's display formatter snaps scaled amounts to nice culinary fractions
  (⅛ ¼ ⅓ ½ ⅔ ¾ ⅞) — critical because recipes use thirds constantly.
- Output is **spot-checked** by a human before publish (the LLM can misread messy comments).

### 5.5 Auto-tagging
- Derive `tags[]` from ingredients + dish + theme using a controlled vocabulary so tags stay
  consistent and clickable. Facets:
  - **Protein:** chicken, beef, pork, seafood, egg, vegetarian, vegan
  - **Course:** dessert, bread, soup, salad, main, side, sauce, drink, breakfast
  - **Cuisine:** mexican, italian, japanese, syrian, indian, … (from theme/dish)
  - **Attribute:** quick, grill, baked, no-bake, spicy, kid-friendly
- Tags are suggested by the pipeline and editable in the spot-check.

### 5.6 Output
- `recipes.json` (array of Recipe objects, §6) written to the site's data directory.
- `public/images/` populated. Both committed to the repo (site is self-contained).

## 6. Data model (`recipes.json`)

```jsonc
{
  "id": "wc-2026-w28",              // stable id: subreddit + year + week
  "week": 28,
  "year": 2026,
  "date": "2026-07-13",            // from post created_utc
  "theme": "Wild West",
  "title": "Cornbread and Baked Beans",
  "dish": "Cornbread & Baked Beans",
  "subreddit": "52weeksofcooking", // cooking | baking
  "track": "Mindful Meals",        // optional meta-track label, may be null
  "redditUrl": "https://www.reddit.com/r/52weeksofcooking/comments/1uwt4j3/…",
  "sourceUrl": "https://…",        // recipe link Frankie shared, if any (nullable)
  "description": "Skillet cornbread with smoky baked beans.",
  "image": "images/week-28-cornbread-and-baked-beans.webp",
  "gallery": ["images/…-2.webp"],  // optional extra photos
  "servings": 6,
  "ingredients": [
    { "qty": 1,      "unit": "cup", "item": "cornmeal",      "note": null },
    { "qty": 0.6667, "unit": "cup", "item": "sugar",         "note": null },
    { "qty": 1,      "unit": null,  "item": "egg",           "note": "beaten" }
  ],
  "steps": [ "Heat oven to 400°F…", "Whisk dry ingredients…" ],
  "tags": ["side", "bread", "vegetarian"],
  "notes": "Frankie's tip: add a little honey butter on top."
}
```

- `ingredients[].qty` is nullable (e.g. "salt to taste").
- Scaling multiplies every non-null `qty` by `targetServings / servings`.

## 7. Website (Part B)

Vite + TypeScript, no UI framework. Renders from `recipes.json` fetched at startup. All
interaction is client-side; no backend.

### 7.1 Structure / modules
- `data.ts` — load & type `recipes.json`; build the tag index.
- `search.ts` — text filter over title/dish/theme/ingredients/tags.
- `filter.ts` — tag filtering (AND; empty = all) + combine with search text.
- `cards.ts` — render the card grid.
- `recipe.ts` — render the recipe detail view (route/modal).
- `scaler.ts` — servings slider + fraction-snapping quantity formatter.
- `checklist.ts` — ingredient checkbox state (persisted per recipe in `localStorage`).
- `main.ts` — wire it together, handle routing (hash-based).

### 7.2 UI
- **Header:** title + subtitle.
- **Controls:** search input; tag rail (clickable chips, multi-select, "clear all" when
  active).
- **Card grid:** responsive `auto-fill` grid. Card = image, theme badge, dish name, month +
  year, one-line description, tag chips.
- **Recipe view:** hero image (+ gallery), `Week N · Theme · full date · subreddit`, servings
  **slider** with live multiplier readout, **ingredient checkboxes** with scaled quantities,
  numbered method, link to the original Reddit post (and `sourceUrl` if present).
- **Empty state:** search/filter with no matches shows a friendly "no recipes" message.

### 7.3 Behavior details
- Tag filter is **AND**; **no tags selected shows all recipes**. Search text ANDs with tags.
- Servings slider range spans roughly base→8× (min 1–2, max ~48); quantities recompute on
  `input`. Formatter snaps to culinary fractions.
- Checkbox state persists per-recipe in `localStorage`, with a "reset" affordance.
- Fully usable one-handed on a phone.

### 7.4 Running it
- `npm run dev -- --host` (or `vite preview --host`) → reachable at
  `http://<machine-lan-ip>:5173` from any device on the home network.

## 8. Testing

- **Pipeline:** unit tests for the pure transforms — title parsing (`Week N: Theme - Dish`),
  image-URL resolution rules, imgur-placeholder detection, ingredient/quantity parsing,
  fraction formatting. A small fixture set of real comments.
- **Website:** unit tests for `search`, `filter` (incl. empty-selection = all), and the
  scaler's fraction-snapping formatter (½, ⅓, ⅔ cases). Light DOM/render smoke test.
- **Manual:** spot-check the generated `recipes.json` against several original posts; verify
  LAN access from a phone.

## 9. Phases

1. **Pipeline v1 — harvest:** posts + Frankie's comments + images → raw dataset (`data/raw/`).
2. **Enrichment:** LLM structuring + auto-tagging → `recipes.json` (human spot-check).
3. **Website:** cards, search, tags, checkboxes, sliding scaler, dark theme; LAN-serve.
4. **(Later) Update path:** documented re-run of the pipeline to add new weekly recipes;
   optionally a simple local edit workflow. Possible future public deployment.

## 10. Risks & mitigations

- **Reddit blocks automation** → use the logged-in Playwright browser; cache raw JSON so we
  don't re-hit Reddit; add polite delays.
- **Image link rot / imgur removals** → vendor images locally; detect the 200-OK placeholder
  by dimensions; graceful fallbacks (Reddit preview → emoji).
- **Messy free-text recipes** → LLM structuring + mandatory human spot-check; keep a link to
  the original post as source of truth.
- **Scaling misrepresents fractions** → store exact `qty`; snap only at display time to
  culinary fractions including thirds.
- **Ambiguous servings** → default a sensible base (e.g. 4–6) when the comment omits it; note
  it as an estimate.
