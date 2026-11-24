import copy
import json
import re
from pathlib import Path
from collections import Counter

p=Path("academy_content.json")
app=json.loads(p.read_text(encoding="utf-8"))
original=copy.deepcopy(app)
draft=json.loads(Path("pending/beginners_story_full_24.json").read_text(encoding="utf-8"))
def norm(s):
    return re.sub(r"[^\w\s]", "", str(s).translate(str.maketrans("أإآةى","اااهي"))).strip().lower()
tracks=[t for t in app["tracks"] if "مبتد" in norm(t.get("title","")) or t.get("id") in {"beginner_accounting","accounting_for_beginners","beginners","accounting_beginners"}]
assert len(tracks)==1
t=tracks[0]
old=t["lessons"]
assert len(old) in (16,24), len(old)
assert len(draft["lessons"])==24
# Preserve existing IDs by semantic topic rather than by positional index.
mapping={0:0,1:1,2:2,3:4,4:5,5:6,6:13,7:10,8:12,9:11,10:16,12:9,13:17,14:21,15:23}
# Old payroll lesson is superseded by the expanded syllabus. Its ID is retired.
existing={l["id"]:l for l in old}
new=[]
for i,item in enumerate(draft["lessons"]):
    title=item["title"]
    if i<3: title=["📚 ","⚖️ ","💰 "][i]+title
    qs=item["questions"]
    assert len(qs)==5 and len({q["answer"] for q in qs})>=3
    assert all(len(q["options"])==4 and len(set(q["options"]))==4 and 0<=q["answer"]<4 and len(q["explanation"])>=20 for q in qs)
    assert len(item["summary"])>=3 and len(item["longExplanation"])>=4
    if len(old)==16:
        source=next((j for j,k in mapping.items() if k==i),None)
        lesson=copy.deepcopy(old[source]) if source is not None else {}
    else:
        assert norm(old[i]["title"])==norm(title)
        lesson=copy.deepcopy(old[i])
    if not lesson:
        lesson={"id":f"beginner_story_{i+1:02d}","code":f"BEGIN-{i+1:02d}","standardCode":"","level":"مبتدئ","estimatedMinutes":15}
    for key in ("summary","longExplanation","questions"): lesson[key]=item[key]
    lesson["title"]=title
    new.append(lesson)
t["lessons"]=new
assert len(new)==24 and len({l["id"] for l in new})==24
other=[x for x in app["tracks"] if x is not t]
assert other==[x for x in original["tracks"] if x["id"]!=t["id"]]
otherids={l["id"] for x in other for l in x["lessons"]}
assert not otherids.intersection(l["id"] for l in new)
if app!=original:
    app["version"]=int(app["version"])+1
    app["updatedAt"]="2026-11-24"
    p.write_text(json.dumps(app,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Beginner lessons:",len(new),"Questions:",sum(len(l["questions"]) for l in new),"Other sections unchanged:",len(other))
