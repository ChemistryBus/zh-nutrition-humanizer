# 本地原文库：不重复 OCR，也不整本 OCR

## 先回答：全书 OCR 有必要吗

**整本没必要。** 上册 1058 页、下册同量级、DRIs 655 页，按 rapidocr 的速度是数小时；
而且这本书是双栏扫描，OCR 会串行，整本的错误率不可接受。

**按需 OCR 有必要。** 术语核对只需要「几页原文 + 页码」。目录里有页码、语料摘录有页码、
真实稿的话题也能指向章节。所以正确做法是**页级缓存**：用到哪页 OCR 哪页，存一次，下次直接查。

## 设计

`scripts/source_db.py` + `references/cache/sources.db`（SQLite）：

| 表 | 存什么 |
|---|---|
| `sources` | 文件路径、标题、页数、sha256、文字层状态 |
| `pages` | 来源、页码、页文本、引擎（pdftotext / rapidocr@300）、字符数 |
| `pages_fts` | FTS5 全文索引，按术语秒查 |

- **文字层可用**的文件（食养指南、体重管理文件）→ `ingest`，`pdftotext` 逐页入库，不 OCR；
- **扫描件**（全书、DRIs）→ `ocr --pages 89-92`，只做指定页；
- 同一来源同一页已有记录就跳过，**不会重复 OCR**；`--force` 才重做；
- 查询走 FTS5：`search 甘油三酯` → 来源 + 页码 + 上下文。

## 用法

```bash
python3 scripts/source_db.py ingest 食养指南.pdf
python3 scripts/source_db.py ocr 全书_上册.pdf --pages 89-92
python3 scripts/source_db.py search 中心型肥胖
python3 scripts/source_db.py stats
```

## 为什么不放进仓库

`references/cache/` 已进 `.gitignore`。库里是**整页正文**，属于出版社版权；仓库里只放
≤80 字的定义摘录与页码（`terms.json` 与 `source-map.md`）。库是本机工具，不是分发内容。

## 现在库里有什么

- 10 份文字层文件，508 页（食养指南 8 份、体重管理指导原则、核心知识、中国成人体重管理指南）；
- 全书上册 89–92 页（脂类章节开头，OCR）；
- 三份 2026 扫描件（肌少症、脑卒中、骨质疏松症）各 p.1–8（OCR）。

## 下一步

- 需要新术语时先 `search`，库里没有再用 `ocr` 补页；
- 2026 年三份扫描件（肌少症、脑卒中、骨质疏松）按同样方式按需补；
- MinerU server 正常后，全书可按章批量补，engine 标 `mineru`，与 rapidocr 的页并存可对比。
