#!/usr/bin/env python3
"""上传前检查数据：python3 check.py
每篇文章必须有下面这些字段；目录 data/index.json 里的 id 必须和 data/articles/ 下的文件一一对应。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REQUIRED = ["id", "type", "title", "group", "question", "logic",
            "source_nine", "source_seven", "meta", "vocab", "preferred", "source_note"]
TYPES = {"小作文", "大作文"}

problems = []
def load(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        problems.append(f"{path}: 读不出来（{e}）")
        return None

index = load("data/index.json") or {"articles": []}
ids = index.get("articles", [])
if len(ids) != len(set(ids)):
    problems.append("data/index.json: 有重复的 id")

files = {f[:-5] for f in os.listdir(os.path.join(ROOT, "data/articles")) if f.endswith(".json")}
for missing in sorted(set(ids) - files):
    problems.append(f"目录里有 {missing}，但 data/articles/{missing}.json 不存在")
for extra in sorted(files - set(ids)):
    problems.append(f"data/articles/{extra}.json 存在，但目录 data/index.json 里没列它（页面上不会显示）")

for i in ids:
    if i not in files:
        continue
    a = load(f"data/articles/{i}.json")
    if a is None:
        continue
    for k in REQUIRED:
        if k not in a:
            problems.append(f"{i}.json: 缺字段 {k}")
    if a.get("id") != i:
        problems.append(f"{i}.json: 文件名和里面的 id（{a.get('id')}）不一致")
    if a.get("type") not in TYPES:
        problems.append(f"{i}.json: type 只能是 小作文 或 大作文，现在是 {a.get('type')!r}")
    if not (i.startswith("t1-") or i.startswith("t2-")):
        problems.append(f"{i}.json: id 要以 t1-（小作文）或 t2-（大作文）开头")

# All selectable editions must support the same complete training flow.
for i in ids:
    if i not in files:
        continue
    a = load(f"data/articles/{i}.json")
    if not a:
        continue
    for edition in ("nine", "seven"):
        if not a.get("meta", {}).get(edition + "_complete"):
            continue
        paragraphs = a.get("source_" + edition, [])
        if len(paragraphs) < 4:
            problems.append(f"{i}/{edition}: 完整版本至少需要4段")
        for n, paragraph in enumerate(paragraphs):
            if not paragraph.get("en", "").strip() or not paragraph.get("cn", "").strip():
                problems.append(f"{i}/{edition}/段{n+1}: 缺少英文或中文")
        exercises = a.get("transfer", {}).get(edition, [])
        if len(exercises) < 3:
            problems.append(f"{i}/{edition}: 至少需要3道搭配迁移题")
        exercise_ids = [x.get("id") for x in exercises]
        if len(exercise_ids) != len(set(exercise_ids)):
            problems.append(f"{i}/{edition}: 迁移题id重复")
        for exercise in exercises:
            n = exercise.get("source_paragraph", -1)
            if not 0 <= n < len(paragraphs):
                problems.append(f"{i}/{edition}: 迁移题出处段落无效")
                continue
            source = paragraphs[n]["en"]
            phrase = exercise.get("source_phrase", "")
            if not phrase or phrase.lower() not in source.lower() or exercise.get("source") != source:
                problems.append(f"{i}/{edition}: 迁移搭配未对应到范文出处")
            if not all(exercise.get(k, "").strip() for k in ("phrase", "cn", "answer")):
                problems.append(f"{i}/{edition}: 迁移题缺少搭配、中文题目或参考答案")
            if any(exercise.get("answer", "") in p["en"] for p in paragraphs):
                problems.append(f"{i}/{edition}: 迁移题不能直接复用范文原句")

for name in ["essays", "errors", "connectors", "connector-library"]:
    load(f"data/{name}.json")

if problems:
    print("❌ 有 %d 个问题：" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"✅ 数据没问题：{len(ids)} 篇文章，版本 {index.get('version')}")
