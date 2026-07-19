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
