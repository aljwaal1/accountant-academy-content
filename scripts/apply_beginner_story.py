import json, copy, re
from pathlib import Path
from collections import Counter
p=Path("academy_content.json")
app=json.loads(p.read_text(encoding="utf-8"))
original=copy.deepcopy(app)
draft=json.loads(Path("pending/beginners_story_draft_2026_11_24.json").read_text(encoding="utf-8"))
def norm(s):
    return re.sub(r"[^\w\s]", "", str(s).translate(str.maketrans("أإآةى","اااهي"))).strip().lower()
tracks=[t for t in app["tracks"] if ("مبتد" in norm(t.get("title","")) or t.get("id") in {"beginner_accounting","accounting_for_beginners","beginners","accounting_beginners"})]
assert len(tracks)==1, [(t.get("id"),t.get("title")) for t in app["tracks"]]
t=tracks[0]
aliases=[["ما المحاسبة","ما هي المحاسبة","ماهي المحاسبة","مقدمة في المحاسبة","مفهوم المحاسبة","مدخل إلى المحاسبة"],["الفرق بين الأصول والالتزامات وحقوق الملكية","المعادلة المحاسبية","معادلة المحاسبة","معادلة الميزانية"],["الإيرادات والمصروفات","الايرادات والمصروفات","المصروفات والإيرادات"]]
used=set()
for item,names in zip(draft["lessons"],aliases):
    found=[l for l in t["lessons"] if any(norm(n) in norm(l.get("title","")) for n in names)]
    assert len(found)==1, (item["title"],[l.get("title") for l in t["lessons"]])
    old=found[0]
    assert old["id"] not in used
    used.add(old["id"])
    qs=item["questions"]
    assert len(qs)==5 and len({q["answer"] for q in qs})>=3
    assert all(len(q["options"])==4 and len(set(q["options"]))==4 and 0<=q["answer"]<4 and len(q["explanation"])>=20 for q in qs)
    for key in ("title","summary","longExplanation","questions"): old[key]=item[key]
assert [x for x in app["tracks"] if x is not t]==[x for x in original["tracks"] if x["id"]!=t["id"]]
assert Counter(l["id"] for x in app["tracks"] for l in x["lessons"])==Counter(l["id"] for x in original["tracks"] for l in x["lessons"])
if app!=original:
    app["version"]=int(app["version"])+1
    app["updatedAt"]="2026-11-24"
    p.write_text(json.dumps(app,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Updated lesson IDs:",sorted(used))
