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

for name in ["essays", "errors", "connectors", "connector-library"]:
    load(f"data/{name}.json")

if problems:
    print("❌ 有 %d 个问题：" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"✅ 数据没问题：{len(ids)} 篇文章，版本 {index.get('version')}")
