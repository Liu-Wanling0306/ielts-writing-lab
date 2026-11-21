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

# Validate the independent complex-sentence training content.
sentences = load("data/sentence-training.json") or {}
lesson_ids = set()
exercise_total = 0
for lesson in sentences.get("lessons", []):
    lesson_id = lesson.get("id", "")
    if not lesson_id or lesson_id in lesson_ids:
        problems.append("sentence-training: 单元id缺失或重复")
    lesson_ids.add(lesson_id)
    for key in ("title", "category", "scope", "goal", "principle"):
        if not lesson.get(key, "").strip():
            problems.append(f"sentence-training/{lesson_id}: 缺少{key}")
    for key in ("steps", "rules", "examples", "mistakes"):
        if not lesson.get(key):
            problems.append(f"sentence-training/{lesson_id}: 缺少{key}")
    exercises = lesson.get("exercises", [])
    if not 5 <= len(exercises) <= 8:
        problems.append(f"sentence-training/{lesson_id}: 每类应有5至8题")
    exercise_ids = set()
    for exercise in exercises:
        if not exercise.get("id") or exercise["id"] in exercise_ids:
            problems.append(f"sentence-training/{lesson_id}: 题目id缺失或重复")
        exercise_ids.add(exercise.get("id"))
        for key in ("cn", "hint", "answer", "explanation", "task"):
            if not exercise.get(key, "").strip():
                problems.append(f"sentence-training/{lesson_id}: 迁移题缺少{key}")
    exercise_total += len(exercises)
for example in sentences.get("case_study", []) + [example for lesson in sentences.get("lessons", []) for example in lesson.get("examples", [])]:
    for key in ("en", "cn", "main", "antecedent", "connector", "clause", "role"):
        if not example.get(key, "").strip():
            problems.append(f"sentence-training: 例句拆解缺少{key}")
    if example.get("clause", "") not in example.get("en", ""):
        problems.append("sentence-training: 从句高亮与例句不一致")
    if len(example.get("split", [])) != 2:
        problems.append("sentence-training: 例句应包含两句还原示范")
if len(lesson_ids) != 8 or len(sentences.get("case_study", [])) != 4:
    problems.append("sentence-training: 应包含8个单元和4个流程图导读例句")

# The editable grammar source must stay identical to the standalone offline page.
import re
grammar = load("data/grammar-review.json") or {}
try:
    html = open(os.path.join(ROOT, "grammar-review.html"), encoding="utf-8").read()
    embedded = json.loads(re.search(r'<script id="grammarData" type="application/json">(.*?)</script>', html, re.S).group(1))
    if embedded != grammar:
        problems.append("grammar-review: HTML内嵌内容与JSON源数据不同步")
except Exception as e:
    problems.append(f"grammar-review: 无法读取内嵌数据（{e}）")
grammar_ids = set()
if len(grammar.get("lessons", [])) != 12:
    problems.append("grammar-review: 应包含12专题")
for lesson in grammar.get("lessons", []):
    if len(lesson.get("exercises", [])) != 9:
        problems.append("grammar-review: 每专题应包含9题")
    for q in lesson.get("exercises", []):
        if not q.get("id") or q["id"] in grammar_ids:
            problems.append("grammar-review: 练习ID缺失或重复")
        grammar_ids.add(q.get("id"))
        if not all(q.get(k) for k in ("prompt", "answer")):
            problems.append("grammar-review: 题干或答案缺失")
        if q.get("type") == "gap" and not q.get("accepted"):
            problems.append("grammar-review: 填空缺少可接受答案")

if problems:
    print("❌ 有 %d 个问题：" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"✅ 数据没问题：{len(ids)} 篇文章，版本 {index.get('version')}；复合句型 {len(lesson_ids)} 类 / {exercise_total} 题")
