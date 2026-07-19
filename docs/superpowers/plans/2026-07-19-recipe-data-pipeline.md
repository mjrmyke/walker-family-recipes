# Recipe Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a committed, self-contained dataset — `src/data/recipes.json` plus vendored `public/images/*.webp` — from Frankie's 52-weeks-of-cooking/baking Reddit posts, structured richly enough to power the website (structured ingredients, steps, tags, week+date).

**Architecture:** A Python package of small, TDD'd pure transforms (title parsing, image-URL resolution, ingredient/quantity parsing, fraction formatting, tag assignment, schema validation) plus a set of operational scripts/steps. Reddit blocks all automated HTTP (403), so **the harvest is performed by Claude driving the existing Playwright MCP browser** (logged-in session), saving raw JSON to `data/raw/` (git-ignored). Pure Python then filters, downloads/optimizes images, and assembles the final JSON. The free-text recipe (which lives in Frankie's comment, not the post body) is structured by a Claude pass validated against a strict schema.

**Tech Stack:** Python 3.14 (`C:\Python314\python.exe`), pytest, Pillow (WebP), requests. Playwright via MCP (Claude-driven). No external LLM API key required — structuring is done by Claude/subagents against `schema.validate()`.

**Conventions:** All commands call the venv interpreter directly as `.venv/Scripts/python.exe` (works in both PowerShell and the Bash tool; no activation needed). Windows shell is PowerShell-primary; the Bash tool is also available (POSIX). Commit after every task.

---

## File Structure

```
walker-family-recipes/
  pipeline/
    __init__.py
    config.py          # subreddits, paths, constants
    titles.py          # is_recipe_post(), parse_title() -> week/theme/dish/track
    slugs.py           # build_slug()
    images.py          # resolve_image_urls(), imgur helpers, is_placeholder_size(), to_webp()
    ingredients.py     # parse_quantity(), parse_ingredient_line() -> {qty,unit,item,note}
    fractions.py       # format_fraction() (culinary fraction snapping)
    tags.py            # TAG_VOCAB, assign_tags()
    schema.py          # RECIPE_SCHEMA, validate_recipe()
    assemble.py        # merge posts + structured -> recipes list; sort; write JSON
  scripts/
    filter_posts.py    # data/raw/submitted-*.json -> data/posts.json (kept posts)
    download_images.py # data/posts.json -> public/images/*.webp, updates image paths
    build_recipes.py   # posts + data/structured/*.json -> src/data/recipes.json
  data/
    raw/               # GIT-IGNORED: submitted-*.json, comments/<id>.json (Playwright dumps)
    posts.json         # committed: filtered post metadata
    structured/        # committed: <id>.json structured recipe bodies (Claude, spot-checked)
  public/images/       # committed: vendored .webp
  src/data/recipes.json# committed: FINAL output the website will import
  tests/
    test_titles.py test_slugs.py test_images.py test_ingredients.py
    test_fractions.py test_tags.py test_schema.py test_assemble.py
  requirements.txt
  pytest.ini
```

---

## Task 1: Python project scaffold

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `pipeline/__init__.py`, `pipeline/config.py`
- Create dirs: `data/raw/`, `data/structured/`, `tests/`, `public/images/`, `src/data/`

- [ ] **Step 1: Create `requirements.txt`**

```
pytest==8.*
Pillow==11.*
requests==2.*
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 3: Create `pipeline/__init__.py`** (empty file).

- [ ] **Step 4: Create `pipeline/config.py`**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
STRUCTURED = DATA / "structured"
POSTS_JSON = DATA / "posts.json"
IMAGES_DIR = ROOT / "public" / "images"
RECIPES_JSON = ROOT / "src" / "data" / "recipes.json"

RECIPE_SUBREDDITS = {"52weeksofcooking", "52weeksofbaking"}
REDDIT_USER = "Frankiieee"
IMGUR_PLACEHOLDER_SIZE = (161, 81)  # imgur "removed" image returns HTTP 200 at this size
```

- [ ] **Step 5: Create the directory tree and `.gitkeep`s**

Run:
```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
mkdir -p data/raw data/structured tests public/images src/data
touch data/structured/.gitkeep public/images/.gitkeep
```
Expected: pip installs pytest, Pillow, requests without error.

- [ ] **Step 6: Verify pytest runs (no tests yet)**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `no tests ran` (exit 5) — confirms pytest is wired.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pytest.ini pipeline/ data/structured/.gitkeep public/images/.gitkeep
git commit -m "chore: scaffold Python pipeline package"
```

---

## Task 2: Title parsing (`pipeline/titles.py`)

Parses `Week 28: Wild West - Cornbread and Baked Beans` into parts, detects the optional
`(Meta: <Track>)` suffix, and rejects non-recipe posts (recaps, removed, off-topic).

**Files:**
- Create: `pipeline/titles.py`
- Test: `tests/test_titles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_titles.py
from pipeline.titles import parse_title, is_recipe_post

def test_parses_basic_title():
    r = parse_title("Week 28: Wild West - Cornbread and Baked Beans")
    assert r == {"week": 28, "theme": "Wild West",
                 "dish": "Cornbread and Baked Beans", "track": None}

def test_parses_meta_track():
    r = parse_title("Week 52: X, Y, and Z - Zesty Italian Chicken Sliders (Meta: Mindful Meals)")
    assert r["week"] == 52
    assert r["theme"] == "X, Y, and Z"
    assert r["dish"] == "Zesty Italian Chicken Sliders"
    assert r["track"] == "Mindful Meals"

def test_rejects_recap_and_removed():
    assert parse_title("Week 1 - 52: Challenge Complete for 2025!") is None
    assert is_recipe_post("52weeksofcooking", "[ Removed by moderator ]") is False
    assert is_recipe_post("excel", "Week 1: X - Y") is False

def test_accepts_valid_recipe_post():
    assert is_recipe_post("52weeksofcooking",
                          "Week 3: Contrasts - Tacos Two Ways") is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_titles.py -v`
Expected: FAIL (ImportError / module not found).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/titles.py
import re
from pipeline.config import RECIPE_SUBREDDITS

# "Week 28: Theme - Dish" with optional trailing "(Meta: Track)"
_PATTERN = re.compile(
    r"^Week\s+(?P<week>\d{1,2})\s*:\s*(?P<theme>.+?)\s+-\s+(?P<dish>.+?)"
    r"(?:\s*\(Meta:\s*(?P<track>[^)]+)\))?\s*$"
)

def parse_title(title: str):
    """Return {week, theme, dish, track} or None if it isn't a weekly recipe title."""
    m = _PATTERN.match(title.strip())
    if not m:
        return None
    return {
        "week": int(m.group("week")),
        "theme": m.group("theme").strip(),
        "dish": m.group("dish").strip(),
        "track": (m.group("track") or "").strip() or None,
    }

def is_recipe_post(subreddit: str, title: str) -> bool:
    """A post we keep: right subreddit AND a parseable weekly-recipe title."""
    if subreddit not in RECIPE_SUBREDDITS:
        return False
    return parse_title(title) is not None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_titles.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/titles.py tests/test_titles.py
git commit -m "feat: parse weekly recipe titles + filter non-recipe posts"
```

---

## Task 3: Slug builder (`pipeline/slugs.py`)

Stable, filesystem-safe slugs for ids and image filenames.

**Files:**
- Create: `pipeline/slugs.py`
- Test: `tests/test_slugs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_slugs.py
from pipeline.slugs import build_slug

def test_slug_basic():
    assert build_slug("Cornbread and Baked Beans") == "cornbread-and-baked-beans"

def test_slug_strips_punctuation_and_case():
    assert build_slug("Chili's Baby Back Ribs!") == "chilis-baby-back-ribs"

def test_slug_collapses_spaces_and_ampersand():
    assert build_slug("Mac  &  Cheese") == "mac-and-cheese"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_slugs.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/slugs.py
import re

def build_slug(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_slugs.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/slugs.py tests/test_slugs.py
git commit -m "feat: build stable slugs for ids and image filenames"
```

---

## Task 4: Image URL resolution (`pipeline/images.py`, part 1)

Turns a post's `url` (+ Reddit gallery metadata) into an ordered list of downloadable direct
image URLs. Pure logic only; downloading/encoding is Task 8.

**Files:**
- Create: `pipeline/images.py`
- Test: `tests/test_images.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_images.py
from pipeline.images import resolve_image_urls, is_placeholder_size

def test_direct_reddit_image():
    assert resolve_image_urls("https://i.redd.it/abc123.jpeg", {}) == \
        ["https://i.redd.it/abc123.jpeg"]

def test_imgur_single():
    assert resolve_image_urls("https://imgur.com/VE91MNZ", {}) == \
        ["https://i.imgur.com/VE91MNZ.jpeg"]

def test_imgur_single_with_ext():
    assert resolve_image_urls("https://imgur.com/VE91MNZ.png", {}) == \
        ["https://i.imgur.com/VE91MNZ.png"]

def test_reddit_gallery_uses_media_metadata():
    post = {
        "is_gallery": True,
        "media_metadata": {
            "aaa": {"s": {"u": "https://preview.redd.it/aaa.jpg?width=1200&amp;s=x"}},
            "bbb": {"s": {"u": "https://preview.redd.it/bbb.jpg?width=1200&amp;s=y"}},
        },
        "gallery_data": {"items": [{"media_id": "aaa"}, {"media_id": "bbb"}]},
    }
    assert resolve_image_urls("https://www.reddit.com/gallery/xyz", post) == [
        "https://preview.redd.it/aaa.jpg?width=1200&s=x",
        "https://preview.redd.it/bbb.jpg?width=1200&s=y",
    ]

def test_placeholder_size_detection():
    assert is_placeholder_size((161, 81)) is True
    assert is_placeholder_size((1200, 900)) is False
    assert is_placeholder_size((30, 20)) is True   # suspiciously tiny
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_images.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/images.py
import re
from pipeline.config import IMGUR_PLACEHOLDER_SIZE

_IMGUR_ALBUM = re.compile(r"imgur\.com/(?:a|gallery)/(\w+)")
_IMGUR_SINGLE = re.compile(r"imgur\.com/(\w+)(\.\w+)?$")

def _clean(u: str) -> str:
    return u.replace("&amp;", "&")

def resolve_image_urls(url: str, post: dict) -> list[str]:
    """Ordered list of direct, downloadable image URLs for a post.

    Album resolution (imgur.com/a/<id>) requires the album's member ids, which are
    fetched during harvest and attached to `post['imgur_album_images']`. If absent,
    the album id is returned as a marker for the harvest step to fill in.
    """
    # Reddit native gallery
    if post.get("is_gallery") and post.get("media_metadata"):
        order = [it["media_id"] for it in post.get("gallery_data", {}).get("items", [])]
        return [_clean(post["media_metadata"][mid]["s"]["u"]) for mid in order
                if mid in post["media_metadata"]]

    # Direct reddit image
    if "i.redd.it/" in url:
        return [url]

    # imgur album -> use pre-fetched member images if harvest attached them
    m = _IMGUR_ALBUM.search(url)
    if m:
        imgs = post.get("imgur_album_images")
        if imgs:
            return imgs
        return [f"imgur-album:{m.group(1)}"]  # marker; harvest resolves this

    # imgur single
    m = _IMGUR_SINGLE.search(url)
    if m:
        ext = m.group(2) or ".jpeg"
        return [f"https://i.imgur.com/{m.group(1)}{ext}"]

    return [url]  # already-direct or unknown; downloader will validate

def is_placeholder_size(size: tuple[int, int]) -> bool:
    """True if a decoded image is the imgur 'removed' placeholder or suspiciously tiny."""
    if size == IMGUR_PLACEHOLDER_SIZE:
        return True
    w, h = size
    return w < 64 or h < 64
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_images.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/images.py tests/test_images.py
git commit -m "feat: resolve post URLs to downloadable image URLs"
```

---

## Task 5: Ingredient & quantity parsing (`pipeline/ingredients.py`)

Parses a single ingredient line into `{qty, unit, item, note}`. Handles unicode fractions,
mixed numbers (`1 1/2`), ranges (`2-3`, takes the low value), and "to taste" (qty=None).

**Files:**
- Create: `pipeline/ingredients.py`
- Test: `tests/test_ingredients.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ingredients.py
import math
from pipeline.ingredients import parse_quantity, parse_ingredient_line

def test_parse_quantity_forms():
    assert parse_quantity("2") == 2.0
    assert parse_quantity("1/2") == 0.5
    assert parse_quantity("1 1/2") == 1.5
    assert math.isclose(parse_quantity("⅔"), 2/3, abs_tol=1e-3)
    assert parse_quantity("2-3") == 2.0            # range -> low end
    assert parse_quantity("") is None

def test_line_qty_unit_item():
    assert parse_ingredient_line("2 cups flour") == \
        {"qty": 2.0, "unit": "cup", "item": "flour", "note": None}

def test_line_unicode_and_note():
    assert parse_ingredient_line("½ cup sugar, packed") == \
        {"qty": 0.5, "unit": "cup", "item": "sugar", "note": "packed"}

def test_line_no_unit():
    assert parse_ingredient_line("3 eggs") == \
        {"qty": 3.0, "unit": None, "item": "eggs", "note": None}

def test_line_to_taste():
    assert parse_ingredient_line("Salt to taste") == \
        {"qty": None, "unit": None, "item": "Salt", "note": "to taste"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_ingredients.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/ingredients.py
import re

_UNICODE_FRAC = {"½":.5,"⅓":1/3,"⅔":2/3,"¼":.25,"¾":.75,"⅛":.125,"⅜":.375,"⅝":.625,"⅞":.875}

# canonical unit -> accepted spellings
_UNITS = {
    "cup": ["cups", "cup", "c"],
    "tsp": ["teaspoons", "teaspoon", "tsp", "tsps"],
    "tbsp": ["tablespoons", "tablespoon", "tbsp", "tbsps", "tbs"],
    "oz": ["ounces", "ounce", "oz"],
    "lb": ["pounds", "pound", "lbs", "lb"],
    "g": ["grams", "gram", "g"],
    "kg": ["kilograms", "kilogram", "kg"],
    "ml": ["milliliters", "milliliter", "ml"],
    "l": ["liters", "liter", "l"],
    "clove": ["cloves", "clove"],
    "can": ["cans", "can"],
    "pinch": ["pinches", "pinch"],
}
_UNIT_LOOKUP = {spell: canon for canon, spells in _UNITS.items() for spell in spells}

def parse_quantity(text: str):
    text = text.strip()
    if not text:
        return None
    text = text.split("-")[0].split("–")[0].strip()  # ranges -> low end
    total = 0.0
    matched = False
    for tok in text.split():
        if tok in _UNICODE_FRAC:
            total += _UNICODE_FRAC[tok]; matched = True
        elif re.fullmatch(r"\d+/\d+", tok):
            n, d = tok.split("/"); total += int(n) / int(d); matched = True
        elif re.fullmatch(r"\d+(\.\d+)?", tok):
            total += float(tok); matched = True
        else:
            break
    return total if matched else None

def parse_ingredient_line(line: str):
    line = line.strip().lstrip("-•*").strip()
    note = None
    if "," in line:
        line, note = [p.strip() for p in line.split(",", 1)]
    # leading quantity: digits, unicode fractions, slashes, ranges
    m = re.match(r"^([\d\s./⅛¼⅜½⅝¾⅞–-]+)\s*(.*)$", line)
    qty, rest = None, line
    if m and parse_quantity(m.group(1)) is not None:
        qty = parse_quantity(m.group(1)); rest = m.group(2).strip()
    # unit
    unit = None
    parts = rest.split()
    if parts and parts[0].lower() in _UNIT_LOOKUP:
        unit = _UNIT_LOOKUP[parts[0].lower()]; rest = " ".join(parts[1:])
    # trailing "to taste" becomes a note
    if not note and rest.lower().endswith("to taste"):
        rest = rest[: -len("to taste")].strip(); note = "to taste"
    return {"qty": qty, "unit": unit, "item": rest.strip(), "note": note}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_ingredients.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/ingredients.py tests/test_ingredients.py
git commit -m "feat: parse ingredient lines into structured qty/unit/item/note"
```

---

## Task 6: Fraction formatting (`pipeline/fractions.py`)

Snaps a scaled decimal to a nice culinary fraction (⅛ ¼ ⅓ ½ ⅔ ¾ ⅞), carrying to whole
numbers. Mirrors the mockup's formatter; the website will re-implement this in TS with the
same cases (documented in Plan 2).

**Files:**
- Create: `pipeline/fractions.py`
- Test: `tests/test_fractions.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fractions.py
from pipeline.fractions import format_fraction

def test_wholes():
    assert format_fraction(2.0) == "2"
    assert format_fraction(0.0) == "0"

def test_common_fractions():
    assert format_fraction(0.5) == "½"
    assert format_fraction(2/3) == "⅔"
    assert format_fraction(1/3) == "⅓"

def test_mixed_numbers():
    assert format_fraction(1.5) == "1 ½"
    assert format_fraction(1 + 1/3) == "1 ⅓"

def test_snaps_to_nearest_nice_fraction():
    assert format_fraction(0.34) == "⅓"     # 0.34 -> 1/3
    assert format_fraction(0.99) == "1"     # carries up
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_fractions.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/fractions.py
import math

_NICE = [(0.0, ""), (0.125, "⅛"), (0.25, "¼"), (1/3, "⅓"), (0.5, "½"),
         (2/3, "⅔"), (0.75, "¾"), (0.875, "⅞"), (1.0, "")]

def format_fraction(x: float) -> str:
    whole = math.floor(x + 1e-9)
    frac = x - whole
    value, label = min(_NICE, key=lambda p: abs(frac - p[0]))
    if abs(value - 1.0) < 1e-9:        # snapped up to next whole
        whole += 1; label = ""
    if label == "":
        return str(whole)
    return f"{whole} {label}" if whole else label
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_fractions.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/fractions.py tests/test_fractions.py
git commit -m "feat: culinary fraction formatter"
```

---

## Task 7: Tag vocabulary & assignment (`pipeline/tags.py`)

Suggests tags from dish/theme/ingredient text against a controlled vocabulary, so tags stay
consistent and clickable. The Claude structuring pass (Task 10) may refine these; this gives a
deterministic baseline and is the source of truth for the allowed vocabulary.

**Files:**
- Create: `pipeline/tags.py`
- Test: `tests/test_tags.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tags.py
from pipeline.tags import assign_tags, TAG_VOCAB

def test_protein_from_ingredients():
    tags = assign_tags(dish="Chicken Fajitas", theme="World Cup",
                       ingredient_items=["chicken breast", "peppers", "onion"])
    assert "chicken" in tags
    assert "mexican" in tags        # fajitas -> mexican cuisine keyword

def test_dessert_course():
    tags = assign_tags(dish="Peach Pie", theme="Gardening",
                       ingredient_items=["peaches", "flour", "butter", "sugar"])
    assert "dessert" in tags

def test_all_tags_are_in_vocab():
    tags = assign_tags(dish="Carne Asada Tacos", theme="Symmetry",
                       ingredient_items=["skirt steak", "lime", "cilantro"])
    assert set(tags).issubset(set(TAG_VOCAB))
    assert "beef" in tags
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_tags.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/tags.py

# keyword -> canonical tag. First matching keyword adds the tag.
_KEYWORDS = {
    # protein
    "chicken": "chicken", "beef": "beef", "steak": "beef", "carne": "beef",
    "burger": "beef", "pork": "pork", "bacon": "pork", "carnitas": "pork",
    "shrimp": "seafood", "fish": "seafood", "salmon": "seafood", "egg": "egg",
    # course
    "pie": "dessert", "cake": "dessert", "cookie": "dessert", "ice cream": "dessert",
    "brownie": "dessert", "mousse": "dessert", "cupcake": "dessert",
    "bread": "bread", "naan": "bread", "roll": "bread", "biscuit": "bread",
    "soup": "soup", "ramen": "soup", "hot pot": "soup", "stew": "soup",
    "salad": "salad", "taco": "mexican", "fajita": "mexican", "asada": "mexican",
    "sauce": "sauce", "dip": "sauce", "chimichurri": "sauce",
    # cuisine
    "ramen ": "japanese", "sushi": "japanese", "plov": "central-asian",
    "shish": "middle-eastern", "taouk": "middle-eastern",
    # attribute
    "grill": "grill", "skewer": "grill", "baked": "baked",
}

TAG_VOCAB = sorted(set(_KEYWORDS.values()) | {
    "chicken", "beef", "pork", "seafood", "egg", "vegetarian",
    "dessert", "bread", "soup", "salad", "sauce", "side", "main",
    "mexican", "italian", "japanese", "middle-eastern", "central-asian",
    "grill", "baked", "quick",
})

def assign_tags(dish: str, theme: str, ingredient_items: list[str]) -> list[str]:
    haystack = " ".join([dish, theme, *ingredient_items]).lower()
    tags = []
    for kw, tag in _KEYWORDS.items():
        if kw.strip() in haystack and tag not in tags:
            tags.append(tag)
    return sorted(tags)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_tags.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/tags.py tests/test_tags.py
git commit -m "feat: controlled tag vocabulary + keyword-based tag assignment"
```

---

## Task 8: Recipe schema & validation (`pipeline/schema.py`)

Defines the shape of one record in `recipes.json` and validates it. This is the contract the
structuring pass (Task 10) and the website (Plan 2) both rely on.

**Files:**
- Create: `pipeline/schema.py`
- Test: `tests/test_schema.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema.py
import pytest
from pipeline.schema import validate_recipe

VALID = {
    "id": "wc-2026-w28", "week": 28, "year": 2026, "date": "2026-07-13",
    "theme": "Wild West", "title": "Cornbread and Baked Beans",
    "dish": "Cornbread & Baked Beans", "subreddit": "52weeksofcooking",
    "track": None, "redditUrl": "https://reddit.com/x", "sourceUrl": None,
    "description": "Skillet cornbread with baked beans.",
    "image": "images/week-28-cornbread.webp", "gallery": [],
    "servings": 6,
    "ingredients": [{"qty": 1.0, "unit": "cup", "item": "cornmeal", "note": None}],
    "steps": ["Heat oven to 400F."], "tags": ["side", "bread"], "notes": None,
}

def test_valid_recipe_passes():
    validate_recipe(VALID)   # should not raise

def test_missing_field_fails():
    bad = {k: v for k, v in VALID.items() if k != "servings"}
    with pytest.raises(ValueError, match="servings"):
        validate_recipe(bad)

def test_bad_tag_fails():
    bad = {**VALID, "tags": ["not-a-real-tag"]}
    with pytest.raises(ValueError, match="tag"):
        validate_recipe(bad)

def test_empty_steps_fails():
    bad = {**VALID, "steps": []}
    with pytest.raises(ValueError, match="steps"):
        validate_recipe(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_schema.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/schema.py
from pipeline.tags import TAG_VOCAB

_REQUIRED = ["id", "week", "year", "date", "theme", "title", "dish", "subreddit",
             "track", "redditUrl", "sourceUrl", "description", "image", "gallery",
             "servings", "ingredients", "steps", "tags", "notes"]

def validate_recipe(r: dict) -> None:
    for f in _REQUIRED:
        if f not in r:
            raise ValueError(f"missing field: {f}")
    if not isinstance(r["servings"], int) or r["servings"] <= 0:
        raise ValueError("servings must be a positive int")
    if not r["steps"]:
        raise ValueError("steps must be non-empty")
    if not r["ingredients"]:
        raise ValueError("ingredients must be non-empty")
    for ing in r["ingredients"]:
        if set(ing) != {"qty", "unit", "item", "note"}:
            raise ValueError(f"ingredient keys wrong: {ing}")
        if not ing["item"]:
            raise ValueError("ingredient item empty")
    for t in r["tags"]:
        if t not in TAG_VOCAB:
            raise ValueError(f"unknown tag: {t}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_schema.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add pipeline/schema.py tests/test_schema.py
git commit -m "feat: recipe schema validation"
```

---

## Task 9: Harvest posts + comments (operational — Claude drives Playwright)

Reddit 403s scripts, so this is executed by Claude via the Playwright MCP browser, saving raw
JSON to `data/raw/` (git-ignored). No unit test — verified by the filter script's output.

- [ ] **Step 1: Harvest all submission pages**

Using the Playwright MCP browser, navigate to
`https://www.reddit.com/user/Frankiieee/submitted/.json?limit=100&raw_json=1`, read
`document.body.innerText`, and save it to `data/raw/submitted-1.json`. If the JSON's
`data.after` is non-null, navigate to the same URL with `&after=<cursor>` and save
`data/raw/submitted-2.json`; repeat until `after` is null.

- [ ] **Step 2: Filter kept posts → `data/posts.json`**

Create `scripts/filter_posts.py`:

```python
# scripts/filter_posts.py
import json, glob
from pipeline.config import RAW, POSTS_JSON
from pipeline.titles import is_recipe_post, parse_title
from pipeline.slugs import build_slug
from datetime import datetime, timezone

def main():
    posts = []
    for path in sorted(glob.glob(str(RAW / "submitted-*.json"))):
        blob = json.load(open(path, encoding="utf-8"))
        for child in blob["data"]["children"]:
            d = child["data"]
            if not is_recipe_post(d["subreddit"], d["title"]):
                continue
            parsed = parse_title(d["title"])
            year = datetime.fromtimestamp(d["created_utc"], timezone.utc).year
            posts.append({
                "id": f"{'wc' if d['subreddit']=='52weeksofcooking' else 'wb'}"
                      f"-{year}-w{parsed['week']}",
                "week": parsed["week"], "year": year,
                "date": datetime.fromtimestamp(d["created_utc"], timezone.utc)
                        .strftime("%Y-%m-%d"),
                "theme": parsed["theme"], "dish": parsed["dish"],
                "title": d["title"], "track": parsed["track"],
                "subreddit": d["subreddit"],
                "redditUrl": "https://www.reddit.com" + d["permalink"],
                "permalink": d["permalink"], "url": d["url"],
                "slug": build_slug(parsed["dish"]),
                "num_comments": d["num_comments"],
                "media_metadata": d.get("media_metadata"),
                "gallery_data": d.get("gallery_data"),
                "is_gallery": d.get("is_gallery", False),
            })
    posts.sort(key=lambda p: (p["year"], p["week"]))
    json.dump(posts, open(POSTS_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"kept {len(posts)} recipe posts")

if __name__ == "__main__":
    main()
```

Run: `.venv/Scripts/python.exe scripts/filter_posts.py`
Expected: prints `kept N recipe posts` (N ≈ 110–150); `data/posts.json` created.

- [ ] **Step 3: Harvest each post's comments (Frankie's recipe)**

For each post in `data/posts.json`, drive the Playwright browser to
`https://www.reddit.com{permalink}.json?raw_json=1`, and save the full JSON to
`data/raw/comments/<id>.json`. For imgur *album* urls (`imgur.com/a/<id>`), also open the
album page in the browser, collect the member image URLs, and write them back into the
matching post in `data/posts.json` under an `imgur_album_images` key — that is exactly where
`resolve_image_urls` (Task 4) and `download_images.py` (Task 11) look for them.

- [ ] **Step 4: Commit the filtered posts (raw stays git-ignored)**

```bash
git add scripts/filter_posts.py data/posts.json
git commit -m "feat: harvest + filter Frankie's recipe posts"
```

---

## Task 10: Structure recipe bodies (operational — Claude + schema gate)

Convert each post's Frankie comment into a structured body validated by `schema.validate_recipe`.
Executed by Claude (optionally fanned out with subagents); the schema is the quality gate.

- [ ] **Step 1: For each `data/raw/comments/<id>.json`, extract Frankie's comment**

Select the top-level comment authored by `Frankiieee` (fallback: the longest Frankie comment).
That comment's markdown body is the recipe source text. Capture any recipe URL it links as
`sourceUrl`.

- [ ] **Step 2: Produce `data/structured/<id>.json`**

For each recipe, write a JSON file with exactly these keys (the post-level fields come from
`posts.json` in Task 11, so structured files hold only the body):

```json
{
  "id": "wc-2026-w28",
  "description": "One-line card blurb.",
  "servings": 6,
  "ingredients": [{"qty": 1.0, "unit": "cup", "item": "cornmeal", "note": null}],
  "steps": ["Heat oven to 400F...", "..."],
  "tags": ["side", "bread"],
  "sourceUrl": null,
  "notes": null
}
```

Rules: use `pipeline.ingredients.parse_ingredient_line` as the starting point for each
ingredient (correct obvious misreads by hand); `tags` MUST be a subset of `pipeline.tags.TAG_VOCAB`
(seed with `assign_tags`, then refine); if servings is unstated, estimate 4 and set
`"notes": "servings estimated"`. Keep `qty` as an exact decimal.

- [ ] **Step 3: Validate every structured file**

Create `scripts/validate_structured.py`:

```python
# scripts/validate_structured.py
import json, glob, sys
from pipeline.config import STRUCTURED, POSTS_JSON
from pipeline.schema import validate_recipe

def main():
    posts = {p["id"]: p for p in json.load(open(POSTS_JSON, encoding="utf-8"))}
    errors = 0
    for path in sorted(glob.glob(str(STRUCTURED / "*.json"))):
        body = json.load(open(path, encoding="utf-8"))
        post = posts.get(body["id"])
        if not post:
            print(f"{path}: no matching post id"); errors += 1; continue
        merged = {**post, **body, "image": "images/placeholder.webp", "gallery": []}
        merged.setdefault("track", post.get("track"))
        try:
            validate_recipe(merged)
        except ValueError as e:
            print(f"{path}: {e}"); errors += 1
    print(f"validated {len(glob.glob(str(STRUCTURED / '*.json')))} files, {errors} errors")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
```

Run: `.venv/Scripts/python.exe scripts/validate_structured.py`
Expected: `... 0 errors` (exit 0). Fix any reported file and re-run.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate_structured.py data/structured/
git commit -m "feat: structured recipe bodies (schema-validated)"
```

---

## Task 11: Download & optimize images (`scripts/download_images.py` + `images.py` part 2)

**Files:**
- Modify: `pipeline/images.py` (add `to_webp`)
- Create: `scripts/download_images.py`
- Test: extend `tests/test_images.py`

- [ ] **Step 1: Write the failing test for `to_webp`**

```python
# add to tests/test_images.py
from pathlib import Path
from PIL import Image
from pipeline.images import to_webp, is_placeholder_size

def test_to_webp_resizes_and_saves(tmp_path):
    src = tmp_path / "src.png"
    Image.new("RGB", (2000, 1500), "orange").save(src)
    out = tmp_path / "out.webp"
    size = to_webp(src.read_bytes(), out, max_width=1200)
    assert out.exists()
    assert size[0] == 1200                     # width capped
    assert not is_placeholder_size(size)
    assert Image.open(out).format == "WEBP"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_images.py::test_to_webp_resizes_and_saves -v`
Expected: FAIL (no attribute `to_webp`).

- [ ] **Step 3: Add `to_webp` to `pipeline/images.py`**

```python
# append to pipeline/images.py
import io
from pathlib import Path
from PIL import Image

def to_webp(raw: bytes, out_path: Path, max_width: int = 1200) -> tuple[int, int]:
    """Decode bytes, downscale to max_width, save as WebP. Returns final (w, h)."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if img.width > max_width:
        h = round(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "WEBP", quality=82, method=6)
    return img.size
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_images.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Create `scripts/download_images.py`**

```python
# scripts/download_images.py
import json, sys
import requests
from PIL import Image
import io
from pipeline.config import POSTS_JSON, IMAGES_DIR, DATA
from pipeline.images import resolve_image_urls, to_webp, is_placeholder_size

UA = {"User-Agent": "Mozilla/5.0 (walker-family-recipes image fetch)"}

def fetch(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200 and r.content:
            return r.content
    except requests.RequestException:
        pass
    return None

def main():
    posts = json.load(open(POSTS_JSON, encoding="utf-8"))
    updates = {}
    for p in posts:
        urls = resolve_image_urls(p["url"], p)
        saved = []
        for i, url in enumerate(urls):
            if url.startswith("imgur-album:"):
                print(f"{p['id']}: unresolved album {url} (harvest album images)"); continue
            raw = fetch(url)
            if not raw:
                print(f"{p['id']}: download failed {url}"); continue
            try:
                size = Image.open(io.BytesIO(raw)).size
            except Exception:
                print(f"{p['id']}: not an image {url}"); continue
            if is_placeholder_size(size):
                print(f"{p['id']}: placeholder/tiny image skipped {url}"); continue
            name = f"{p['slug']}-{p['id']}" + ("" if i == 0 else f"-{i}") + ".webp"
            to_webp(raw, IMAGES_DIR / name, max_width=1200)
            saved.append(f"images/{name}")
        if saved:
            updates[p["id"]] = {"image": saved[0], "gallery": saved[1:]}
        else:
            updates[p["id"]] = {"image": None, "gallery": []}
            print(f"{p['id']}: NO IMAGE")
    json.dump(updates, open(DATA / "image_map.json", "w", encoding="utf-8"), indent=2)
    missing = [k for k, v in updates.items() if not v["image"]]
    print(f"images done; {len(missing)} recipes missing images: {missing}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the downloader**

Run: `.venv/Scripts/python.exe scripts/download_images.py`
Expected: `public/images/*.webp` populated; `data/image_map.json` written; a printed list of
any recipes missing images (resolve those albums via Task 9 Step 3, or accept the emoji
fallback the website provides).

- [ ] **Step 7: Commit**

```bash
git add pipeline/images.py tests/test_images.py scripts/download_images.py data/image_map.json public/images
git commit -m "feat: download + optimize recipe images to WebP"
```

---

## Task 12: Assemble `recipes.json` (`pipeline/assemble.py` + `scripts/build_recipes.py`)

**Files:**
- Create: `pipeline/assemble.py`
- Create: `scripts/build_recipes.py`
- Test: `tests/test_assemble.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assemble.py
from pipeline.assemble import merge_recipe

POST = {"id": "wc-2026-w28", "week": 28, "year": 2026, "date": "2026-07-13",
        "theme": "Wild West", "title": "Cornbread and Baked Beans",
        "dish": "Cornbread & Baked Beans", "subreddit": "52weeksofcooking",
        "track": None, "redditUrl": "https://reddit.com/x"}
BODY = {"id": "wc-2026-w28", "description": "Skillet cornbread.", "servings": 6,
        "ingredients": [{"qty": 1.0, "unit": "cup", "item": "cornmeal", "note": None}],
        "steps": ["Bake."], "tags": ["side", "bread"], "sourceUrl": None, "notes": None}
IMG = {"image": "images/x.webp", "gallery": []}

def test_merge_produces_full_valid_record():
    r = merge_recipe(POST, BODY, IMG)
    assert r["id"] == "wc-2026-w28"
    assert r["description"] == "Skillet cornbread."
    assert r["image"] == "images/x.webp"
    assert r["servings"] == 6
    # merge_recipe validates internally; reaching here means it passed
    assert set(r["ingredients"][0]) == {"qty", "unit", "item", "note"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_assemble.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Write `pipeline/assemble.py`**

```python
# pipeline/assemble.py
from pipeline.schema import validate_recipe

def merge_recipe(post: dict, body: dict, img: dict) -> dict:
    r = {
        "id": post["id"], "week": post["week"], "year": post["year"],
        "date": post["date"], "theme": post["theme"], "title": post["title"],
        "dish": post["dish"], "subreddit": post["subreddit"],
        "track": post.get("track"), "redditUrl": post["redditUrl"],
        "sourceUrl": body.get("sourceUrl"), "description": body["description"],
        "image": img.get("image") or "images/placeholder.webp",
        "gallery": img.get("gallery", []), "servings": body["servings"],
        "ingredients": body["ingredients"], "steps": body["steps"],
        "tags": body["tags"], "notes": body.get("notes"),
    }
    validate_recipe(r)
    return r
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_assemble.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Write `scripts/build_recipes.py`**

```python
# scripts/build_recipes.py
import json
from pipeline.config import POSTS_JSON, STRUCTURED, RECIPES_JSON, DATA
from pipeline.assemble import merge_recipe

def main():
    posts = {p["id"]: p for p in json.load(open(POSTS_JSON, encoding="utf-8"))}
    imgs = json.load(open(DATA / "image_map.json", encoding="utf-8"))
    out = []
    for pid, post in posts.items():
        body_path = STRUCTURED / f"{pid}.json"
        if not body_path.exists():
            print(f"skip {pid}: no structured body"); continue
        body = json.load(open(body_path, encoding="utf-8"))
        out.append(merge_recipe(post, body, imgs.get(pid, {})))
    out.sort(key=lambda r: (r["year"], r["week"]))
    RECIPES_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(RECIPES_JSON, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"wrote {len(out)} recipes to {RECIPES_JSON}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Build and verify**

Run: `.venv/Scripts/python.exe scripts/build_recipes.py`
Expected: `wrote N recipes to .../src/data/recipes.json`. Every record passed
`validate_recipe` (build fails loudly otherwise).

- [ ] **Step 7: Commit**

```bash
git add pipeline/assemble.py scripts/build_recipes.py tests/test_assemble.py src/data/recipes.json
git commit -m "feat: assemble validated recipes.json"
```

---

## Task 13: Full pipeline check + spot-check

- [ ] **Step 1: Run the whole test suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass.

- [ ] **Step 2: Spot-check the dataset against source posts**

Open `src/data/recipes.json` and pick 5 recipes across cooking + baking. For each, open its
`redditUrl` and confirm: dish/theme/week/date correct, ingredients & steps match Frankie's
comment, image is the right dish (not a placeholder), tags are sensible. Fix the relevant
`data/structured/<id>.json` and re-run Tasks 10 Step 3 → 12 Step 6 as needed.

- [ ] **Step 3: Print a coverage summary**

Run:
```bash
.venv/Scripts/python.exe -c "import json; r=json.load(open('src/data/recipes.json',encoding='utf-8')); print('recipes:',len(r)); print('no image:',[x['id'] for x in r if x['image'].endswith('placeholder.webp')]); import collections; print(collections.Counter(t for x in r for t in x['tags']))"
```
Expected: recipe count ≈ posts kept; short/empty missing-image list; a sensible tag distribution.

- [ ] **Step 4: Commit any fixes**

```bash
git add data/structured src/data/recipes.json public/images
git commit -m "chore: spot-check corrections to recipe dataset"
```

---

## Done / Handoff to Plan 2

At completion this repo contains a committed, validated `src/data/recipes.json` and vendored
`public/images/*.webp`. Plan 2 (the website) will `import` that JSON and re-implement
`format_fraction` in TypeScript using the same cases from `tests/test_fractions.py`.
