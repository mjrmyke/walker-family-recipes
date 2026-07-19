# scripts/fetch_external.py
"""Fetch each external recipe URL and extract its JSON-LD Recipe.

Writes data/external/<id>.json for every post that has a recipe_url. Records failures
(blocked/no-LD) so they can be retried via the browser. Deterministic, no LLM.
"""
import json, time, sys
import requests
from pipeline.config import DATA
from pipeline.recipe_ld import extract_recipe_ld
from pipeline.recipe_wprm import extract_recipe_wprm

SRC = DATA / "posts_sources.json"
OUT = DATA / "external"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    src = json.load(open(SRC, encoding="utf-8"))
    retry_only = "--retry" in sys.argv
    todo = [p for p in src if p.get("recipe_url")]
    ok = fail = skipped = 0
    failures = []
    for i, p in enumerate(todo, 1):
        out_path = OUT / f"{p['id']}.json"
        if retry_only and out_path.exists():
            prev = json.load(open(out_path, encoding="utf-8"))
            if prev.get("ok"):
                skipped += 1
                continue
        url = p["recipe_url"].rstrip(").,]")
        rec = {"id": p["id"], "recipe_url": url, "ok": False, "reason": None}
        try:
            r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
            rec["http_status"] = r.status_code
            if r.status_code == 200:
                data = extract_recipe_ld(r.text)
                src_kind = "ld"
                if not (data and (data["ingredients"] or data["steps"])):
                    data = extract_recipe_wprm(r.text)   # fallback to WPRM HTML
                    src_kind = "wprm"
                if data and (data["ingredients"] or data["steps"]):
                    rec.update(data); rec["ok"] = True; rec["extractor"] = src_kind
                else:
                    rec["reason"] = "no-recipe-ld-or-wprm"
            else:
                rec["reason"] = f"http-{r.status_code}"
        except requests.RequestException as e:
            rec["reason"] = f"error:{type(e).__name__}"
        json.dump(rec, open(OUT / f"{p['id']}.json", "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        if rec["ok"]:
            ok += 1
        else:
            fail += 1
            failures.append((p["id"], p["recipe_url"], rec["reason"]))
        print(f"[{i}/{len(todo)}] {'OK ' if rec['ok'] else 'XX '} {p['id']}  "
              f"{rec.get('extractor') or rec.get('reason') or ''}")
        time.sleep(0.6)
    print(f"\nDONE: {ok} ok, {fail} failed, {skipped} skipped (already ok)")
    if failures:
        print("FAILURES:")
        for fid, u, why in failures:
            print(f"  {fid:14} {why:16} {u}")

if __name__ == "__main__":
    main()
