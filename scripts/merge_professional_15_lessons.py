#!/usr/bin/env python3
"""Idempotently merge the 2026-11-16 batch of 15 professional lessons into the live app feed.
Must fail closed on ambiguous section mapping, duplicate IDs, invalid questions.
"""
import json
from pathlib import Path
from datetime import date
import re
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
FEED=ROOT/"academy_content.json"
BATCH=ROOT/"curriculum_batches"
FILES=[
    ("banking","2026_11_16_banking_5.json",5),
    ("financial_accounting","2026_11_16_financial_3.json",3),
    ("intermediate_accounting","2026_11_16_intermediate_4.json",4),
    ("managerial_accounting","2026_11_16_managerial_3.json",3),
]
def norm(value):
    s=str(value or "").strip().lower()
    for a,b in [("أ","ا"),("إ","ا"),("آ","ا"),("ة","ه"),("ى","ي")]:
        s=s.replace(a,b)
    return re.sub(r"\s+"," ",s)

def matches(track,key):
    tid=norm(track.get("id"))
    title=norm(track.get("title"))
    ids={
      "banking":{"banking","banks","bank_accounting","banking_accounting","banking_and_banks"},
      "financial_accounting":{"financial_accounting","financial","financial-accounting"},
      "intermediate_accounting":{"intermediate_accounting","intermediate","intermediate-accounting"},
      "managerial_accounting":{"managerial_accounting","managerial","managerial-accounting"},
    }[key]
    titles={
      "banking":("البنوك","مصرف"),
      "financial_accounting":("المحاسبه الماليه",),
      "intermediate_accounting":("المحاسبه المتوسطه",),
      "managerial_accounting":("المحاسبه الاداريه",),
    }[key]
    if tid in ids:return True
    if key=="banking":return any(t in title for t in titles) and not "معلومات" in title
    return any(t in title for t in titles)

def validate_lesson(lesson):
    assert all(str(lesson.get(k,"")).strip() for k in ("id","code","title"))
    assert isinstance(lesson.get("summary"),list) and len(lesson["summary"])>=3
    assert isinstance(lesson.get("longExplanation"),list) and len(lesson["longExplanation"])>=4
    assert all(len(str(p).strip())>=40 for p in lesson["longExplanation"])
    qs=lesson.get("questions")
    assert isinstance(qs,list) and len(qs)>=5
    assert len({norm(x.get("q")) for x in qs})==len(qs)
    assert len({x["answer"] for x in qs})>=3
    for q in qs:
        assert len(q["options"])==4 and len(set(q["options"]))==4
        assert isinstance(q["answer"],int) and 0<=q["answer"]<=3
        assert len(q["explanation"])>=20

def main():
    app=json.loads(FEED.read_text(encoding="utf-8"))
    tracks=app["tracks"]
    assert isinstance(tracks,list)
    all_ids=[str(l.get("id","")) for t in tracks for l in t["lessons"]]
    before=Counter(all_ids)
    changed=False
    report=[]
    requested=set()
    for key,filename,count in FILES:
        batch=json.loads((BATCH/filename).read_text(encoding="utf-8"))
        assert batch["trackKey"]==key and len(batch["lessons"])==count
        for item in batch["lessons"]:
            validate_lesson(item)
            assert item["id"] not in requested, f"duplicate batch id {item['id']}"
            requested.add(item["id"])
        found=[t for t in tracks if matches(t,key)]
        if len(found)!=1:
            raise RuntimeError(f"Expected exactly one existing section for {key}, found {[(t.get('id'),t.get('title')) for t in found]}. No feed write.")
        track=found[0]
        own={l.get("id"):i for i,l in enumerate(track["lessons"])}
        added=0
        replaced=0
        for item in batch["lessons"]:
            ident=item["id"]
            if ident in before and ident not in own:
                raise RuntimeError(f"ID collision outside section: {ident}")
            if ident in own:
                if track["lessons"][own[ident]]!=item:
                    track["lessons"][own[ident]]=item
                    changed=True
                    replaced+=1
            else:
                track["lessons"].append(item)
                changed=True
                added+=1
        report.append({"section":key,"title":track.get("title"),"added":added,"updated":replaced,"total":len(track["lessons"])})
    if changed:
        app["version"]=int(app.get("version",0))+1
        app["updatedAt"]="2026-11-16"
        FEED.write_text(json.dumps(app,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"changed":changed,"requested_lessons":len(requested),"sections":report,"version":app.get("version")},ensure_ascii=False))
if __name__=="__main__":main()
