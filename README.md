# VLM Daily

每天自动从 [arXiv](https://arxiv.org/) 抓取 **VLM（Vision-Language Model）相关论文**，为每篇生成标题、作者、原始英文摘要和链接，并发布成一个公开网页。

🌐 **在线网页**： `https://<你的用户名>.github.io/vlm-daily/`
（部署后把 `<你的用户名>` 换成你的 GitHub 用户名。）

## 工作方式

- **GitHub Actions** 每天 01:00 UTC（≈ 北京 09:00）在云端自动运行 `vlm_daily.py`，你的电脑无需开机。
- 脚本查询 arXiv，筛选出最近的 VLM 相关论文，去重后渲染成 HTML，写入 `docs/`。
- 变更被自动提交回仓库，**GitHub Pages** 从 `main` 分支的 `/docs` 目录发布网页。
- 简介直接使用 arXiv 原始英文摘要，**不需要任何 API key，无费用**。

## 本地手动运行

无需安装任何依赖（纯 Python 标准库，Python 3.9+）：

```bash
python vlm_daily.py
```

然后用浏览器打开 `docs/index.html` 查看。

## 自定义

编辑 [`config.py`](config.py)：

| 参数 | 说明 |
| --- | --- |
| `CATEGORIES` | 搜索的 arXiv 分类（如 `cs.CV`、`cs.CL`） |
| `KEYWORDS` | 关键词（同时用于查询和相关性二次筛选） |
| `MAX_PAPERS` | 每天最多展示的论文数（默认 20） |
| `DAYS_WINDOW` | 只保留最近几天提交的论文（默认 2） |
| `FETCH_BATCH` | 每次向 arXiv 请求的候选数量 |

改定时时间：编辑 [`.github/workflows/daily.yml`](.github/workflows/daily.yml) 里的 `cron` 表达式（UTC 时间）。

## 文件说明

- `vlm_daily.py` — 主脚本：抓取 → 去重 → 渲染 HTML。
- `config.py` — 可调参数。
- `docs/` — 生成的网页（GitHub Pages 根目录）。
- `data/seen_ids.json` — 已展示论文的 ID，用于跨天去重（会被提交回仓库）。
- `.github/workflows/daily.yml` — 每日定时的 GitHub Actions 工作流。
