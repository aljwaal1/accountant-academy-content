#!/usr/bin/env python3
"""Merge approved international banking units into the Academy content feed, idempotently."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "academy_content.json"
UNIT = ROOT / "banking_curriculum" / "unit_01_current_accounts.json"

def main():
    app = json.loads(CONTENT.read_text(encoding="utf-8"))
    source = json.loads(UNIT.read_text(encoding="utf-8"))
    assert isinstance(app.get("tracks"), list)
    assert len(source["lessons"]) == 2
    existing_ids = [str(l.get("id")) for t in app["tracks"] for l in t.get("lessons", [])]
    if len(existing_ids) != len(set(existing_ids)):
        raise RuntimeError("Duplicate existing lesson IDs — manual review required")
    tracks = app["tracks"]
    matching = [t for t in tracks if str(t.get("id","")).lower() in {"banking","banks","bank_accounting","banking_accounting","banking_and_banks"} or "البنوك" in str(t.get("title","")) or "المصرفية" in str(t.get("title",""))]
    if len(matching)>1:
        raise RuntimeError("Ambiguous banking tracks; no changes made")
    if matching:
        track = matching[0]
    else:
        track = {"id":"banking","title":"المحاسبة المصرفية والبنوك التقليدية","subtitle":"عمليات البنوك والدورة المستندية والقيود وفق المنهج الدولي العام","lessons":[]}
        tracks.append(track)
    if not isinstance(track.get("lessons"), list):
        raise RuntimeError("Bank track lessons is not a list")
    current = {l.get("id"):i for i,l in enumerate(track["lessons"])}
    changed = False
    for lesson in source["lessons"]:
        assert len(lesson.get("longExplanation",[])) >= 8
        assert len(lesson.get("summary",[])) >= 3
        assert len(lesson.get("questions",[])) >= 5
        assert len({q["q"] for q in lesson["questions"]}) == len(lesson["questions"])
        for q in lesson["questions"]:
            assert len(q["options"]) == 4 and q["answer"] in range(4) and q["explanation"]
        key = lesson["id"]
        if key in existing_ids and key not in current:
            raise RuntimeError(f"Lesson id already exists in another track: {key}")
        if key in current:
            if track["lessons"][current[key]] != lesson:
                track["lessons"][current[key]] = lesson
                changed = True
        else:
            track["lessons"].append(lesson)
            changed = True
    if changed:
        app["version"] = int(app.get("version",0)) + 1
        app["updatedAt"] = "2026-11-16"
        CONTENT.write_text(json.dumps(app,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"changed":changed,"bank_track":track["id"],"bank_lessons":len(track["lessons"]),"new_unit_lessons":len(source["lessons"]),"version":app.get("version")},ensure_ascii=False))

if __name__ == "__main__":
    main()
