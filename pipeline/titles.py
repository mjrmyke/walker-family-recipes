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
