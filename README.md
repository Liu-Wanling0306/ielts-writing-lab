# IELTS Writing Lab

网址：https://liu-wanling0306.github.io/ielts-writing-lab/
推送到 `main` 分支后，1–2 分钟自动上线。

## 文件

| 文件 | 作用 |
|---|---|
| `index.html` | 页面骨架、密码框、加载数据 |
| `app.css` | 样式 |
| `app.js` | 界面逻辑 |
| `data/index.json` | 目录：列出所有文章 id，页面按这个顺序显示 |
| `data/articles/<id>.json` | 一篇一个文件 |
| `data/essays.json` `errors.json` `connectors.json` `connector-library.json` | 作文档案、错题、衔接词、表达库 |
| `check.py` | 上传前检查数据 |

## 加一篇范文

1. 复制一个同类文件，例如 `data/articles/t2-40.json` 另存为 `t2-41.json`，改内容，`id` 改成 `t2-41`
2. 在 `data/index.json` 的 `articles` 列表里加 `"t2-41"`
3. 运行 `python3 check.py`，看到 ✅ 再推送

规则：
- 小作文 id 以 `t1-` 开头，大作文以 `t2-` 开头
- 已有文章的 id 不要改：个人进度按 id 记在浏览器里，改了会丢

## 本地预览

```
python3 -m http.server 8000 --bind 127.0.0.1
```

然后打开 http://127.0.0.1:8000 。不能直接双击 `index.html` 打开，浏览器不允许本地文件读取 `data/` 里的文件。

## v1.4 学习流程

- 前三个模块按同一版本的全部段落显示，包括引言、全部细节/主体段和结尾；没有预设挖空标记的段落会从原文中补选练习词组。
- 第四模块为重点搭配迁移：每题提供范文搭配出处、新情境中文题目及英文参考答案。题目保存在文章 JSON 的 `transfer.nine` / `transfer.seven`，对应当前选择的版本。
- 每道小作文的题目旁可上传 PNG、JPEG、WebP 或 GIF 图表（每张不超过10 MB）。图片按文章 ID 保存于浏览器 IndexedDB，刷新和切换题目不会丢失。图片不会自动提交到 GitHub，换浏览器前请导出 JSON 备份；备份可同时恢复训练答案和图表。
- `python3 check.py` 检查所有可选版本的段落、中英文内容、迁移题及其范文出处。来源本身残缺的版本继续禁用，不补写冒充原文。

## v1.5 复合句型训练

新增独立导航“复合句型训练”，共8类、每类6题。`data/sentence-training.json`保存结构原理、对照例句、句子拆解、易错辨析与迁移练习。四个罐头流程图练习句作为总导读。

练习输入及自查记录复用现有草稿和完成记录，支持刷新恢复、JSON导出及导入。核对标记是用户自查，不是自动语法评分；编辑已核对的句子会取消旧标记，提示重新核对。
