# Walker Family Recipes

A private, searchable cookbook of Frankie's *52 weeks of cooking & baking* recipes
(Reddit `Frankiieee`, r/52weeksofcooking + r/52weeksofbaking). Dark-mode card grid with
search, tag filters, ingredient checkboxes, and a sliding servings scaler.

**179 recipes** (126 fully cookable with structured ingredients/steps, 53 photo/link-only),
each with a vendored photo. Runs locally / on your home network — no cloud, no accounts.

## Run it

```bash
npm install
npm run dev -- --host
```

Then open **http://localhost:5173** on this machine, or from a phone/tablet on the same
Wi-Fi use the `Network:` URL Vite prints (e.g. `http://192.168.1.125:5173`).

For a faster production build:

```bash
npm run build          # outputs to dist/
npm run preview -- --host
```

## Tests

```bash
npm test                                   # website logic (Vitest)
.venv/Scripts/python.exe -m pytest -q      # data pipeline (pytest)
```

## How it's built

Two independent parts (see `docs/superpowers/`):

- **Data pipeline** (`pipeline/`, `scripts/`, Python): harvests Reddit posts + Frankie's
  recipe comments via a logged-in browser, extracts external recipes (schema.org JSON-LD →
  WP Recipe Maker HTML → WebFetch → browser), downloads/optimizes images, and writes the
  structured, schema-validated `src/data/recipes.json`.
- **Website** (`src/`, Vite + TypeScript): a static SPA that reads `recipes.json`. No backend.

## Updating the data (later)

Re-run the pipeline from the repo root (with the Python venv and the Playwright browser
available) to refresh or add recipes:

```bash
# 1. harvest (drives the logged-in browser — see scripts/ + the pipeline plan)
# 2. PYTHONPATH=. .venv/Scripts/python.exe scripts/filter_posts.py
# 3. PYTHONPATH=. .venv/Scripts/python.exe scripts/match_sources.py
# 4. PYTHONPATH=. .venv/Scripts/python.exe scripts/fetch_external.py
# 5. PYTHONPATH=. .venv/Scripts/python.exe scripts/download_images.py
# 6. PYTHONPATH=. .venv/Scripts/python.exe scripts/build_structured.py
# 7. PYTHONPATH=. .venv/Scripts/python.exe scripts/build_recipes.py
```

Full step-by-step in `docs/superpowers/plans/2026-07-19-recipe-data-pipeline.md`.
