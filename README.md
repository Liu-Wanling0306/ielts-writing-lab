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
