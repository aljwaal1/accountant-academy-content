# -*- coding: utf-8 -*-
"""
دمج آمن لإضافات run5 داخل academy_content.json.
الاستخدام من جذر المستودع:
python pending/merge_academy_content_v20_run5.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "academy_content.json"
ADDITIONS_PATH = ROOT / "pending" / "academy_content_v20_additions_2026-06-26_run5.json"

with CONTENT_PATH.open("r", encoding="utf-8") as f:
    content = json.load(f)

with ADDITIONS_PATH.open("r", encoding="utf-8") as f:
    additions = json.load(f)

existing_ids = set()
existing_codes_titles = set()
for track in content.get("tracks", []):
    for lesson in track.get("lessons", []):
        existing_ids.add(lesson.get("id"))
        existing_codes_titles.add((lesson.get("code"), lesson.get("title")))

added = []
skipped = []
for add_track in additions.get("tracks", []):
    target_track = next((t for t in content.get("tracks", []) if t.get("id") == add_track.get("id")), None)
    if target_track is None:
        content.setdefault("tracks", []).append({
            "id": add_track.get("id"),
            "title": add_track.get("id", "").upper(),
            "subtitle": "",
            "lessons": []
        })
        target_track = content["tracks"][-1]

    for lesson in add_track.get("lessons", []):
        key = (lesson.get("code"), lesson.get("title"))
        if lesson.get("id") in existing_ids or key in existing_codes_titles:
            skipped.append(lesson.get("id"))
            continue
        target_track.setdefault("lessons", []).append(lesson)
        existing_ids.add(lesson.get("id"))
        existing_codes_titles.add(key)
        added.append(lesson.get("id"))

content["version"] = max(int(content.get("version", 0)) + 1, int(additions.get("targetVersion", 0)))
content["updatedAt"] = additions.get("updatedAt", content.get("updatedAt"))

with CONTENT_PATH.open("w", encoding="utf-8") as f:
    json.dump(content, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("Added:", len(added), added)
print("Skipped:", len(skipped), skipped)
print("New version:", content["version"])
