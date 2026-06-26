import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "academy_content.json"
ADD = ROOT / "pending" / "academy_content_v20_additions_2026-06-26_run4.json"

content = json.loads(MAIN.read_text(encoding="utf-8"))
additions = json.loads(ADD.read_text(encoding="utf-8"))

existing_ids = {
    lesson.get("id")
    for track in content.get("tracks", [])
    for lesson in track.get("lessons", [])
}

added = []
for add_track in additions.get("tracks", []):
    target = next((t for t in content.get("tracks", []) if t.get("id") == add_track.get("id")), None)
    if target is None:
        continue
    for lesson in add_track.get("lessons", []):
        if lesson.get("id") not in existing_ids:
            target.setdefault("lessons", []).append(lesson)
            existing_ids.add(lesson.get("id"))
            added.append(lesson.get("id"))

content["version"] = max(int(content.get("version", 0)) + 1, int(additions.get("targetVersion", 0)))
content["updatedAt"] = additions.get("updatedAt", content.get("updatedAt"))

MAIN.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Added {len(added)} lessons:")
for lesson_id in added:
    print("-", lesson_id)
print("New version:", content["version"])
