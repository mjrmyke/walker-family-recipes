# scripts/build_structured.py
"""Write data/structured/<id>.json for every post that can be built deterministically:
  - external JSON-LD ok  -> structure_from_external
  - no recipe available  -> structure_photoonly
Posts whose recipe only exists in Frankie's typed comment are listed as LLM_TODO for
a separate structuring pass (they are NOT written here).
"""
import json
from pipeline.config import DATA, STRUCTURED
from pipeline.structure import structure_from_external, structure_photoonly

SRC = DATA / "posts_sources.json"
EXT = DATA / "external"
COMMENT_MIN = 200  # a comment this long is treated as a real typed recipe (LLM pass)

def main():
    posts = json.load(open(SRC, encoding="utf-8"))
    STRUCTURED.mkdir(parents=True, exist_ok=True)
    ext_ok, photo, llm_todo = 0, 0, []
    for p in posts:
        ext_path = EXT / f"{p['id']}.json"
        ext = json.load(open(ext_path, encoding="utf-8")) if ext_path.exists() else {}
        out = STRUCTURED / f"{p['id']}.json"
        if ext.get("ok"):
            body = structure_from_external(p, ext)
            json.dump(body, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            ext_ok += 1
        elif len((p.get("comment_body") or "").strip()) >= COMMENT_MIN:
            llm_todo.append(p["id"])          # typed recipe -> LLM pass fills this in
        else:
            body = structure_photoonly(p, has_link=bool(p.get("recipe_url")))
            json.dump(body, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            photo += 1
    print(f"external-structured: {ext_ok}")
    print(f"photo-only:          {photo}")
    print(f"LLM_TODO ({len(llm_todo)}): {llm_todo}")

if __name__ == "__main__":
    main()
