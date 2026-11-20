#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地原文库：把权威文件的页级文本存进一个 SQLite，查一次、存一次、不再重复 OCR。

    python3 scripts/source_db.py ingest 文件.pdf          # 文字层可用：直接入库
    python3 scripts/source_db.py ocr 文件.pdf --pages 89-92   # 扫描件：只 OCR 指定页
    python3 scripts/source_db.py search 甘油三酯           # 全库检索，带来源与页码
    python3 scripts/source_db.py stats

设计：
- 只缓存**需要的页**，不整本 OCR；同一页同一引擎只做一次。
- 数据库在 `references/cache/sources.db`，**不进仓库**（.gitignore），也不上传。
- 引用时只取 ≤80 字的句子，连同来源与页码写进 terms.json；不复制正文。
"""

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "references" / "cache" / "sources.db"


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS sources(
      id INTEGER PRIMARY KEY, path TEXT UNIQUE, title TEXT, year TEXT,
      pages INTEGER, sha256 TEXT, layer TEXT, added_at TEXT);
    CREATE TABLE IF NOT EXISTS pages(
      source_id INTEGER, page INTEGER, text TEXT, engine TEXT,
      chars INTEGER, added_at TEXT, PRIMARY KEY(source_id, page));
    CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(text, source_id UNINDEXED, page UNINDEXED);
    """)
    return con


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path: Path):
    """返回 (页数, 文字层字符数前3页, 是否可用)。"""
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else 0
    txt = subprocess.run(["pdftotext", "-f", "1", "-l", "3", str(path), "-"],
                         capture_output=True, text=True).stdout
    chars = len("".join(txt.split()))
    return pages, chars, chars >= 50


def register(con, path: Path, pages: int, layer: str):
    row = con.execute("SELECT id FROM sources WHERE path=?", (str(path),)).fetchone()
    if row:
        return row[0]
    cur = con.execute(
        "INSERT INTO sources(path,title,year,pages,sha256,layer,added_at) VALUES(?,?,?,?,?,?,?)",
        (str(path), path.stem, "", pages, sha256(path), layer,
         datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return cur.lastrowid


def put_page(con, sid, page, text, engine, force=False):
    if not force:
        row = con.execute("SELECT engine FROM pages WHERE source_id=? AND page=?", (sid, page)).fetchone()
        if row:
            return False
    con.execute("DELETE FROM pages WHERE source_id=? AND page=?", (sid, page))
    con.execute("DELETE FROM pages_fts WHERE source_id=? AND page=?", (sid, page))
    con.execute("INSERT INTO pages(source_id,page,text,engine,chars,added_at) VALUES(?,?,?,?,?,?)",
                (sid, page, text, engine, len(text),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
    con.execute("INSERT INTO pages_fts(text,source_id,page) VALUES(?,?,?)", (text, sid, page))
    return True


def ingest(path: Path, force=False):
    pages, chars, ok = probe(path)
    if not ok:
        sys.exit(f"文字层不可用（前3页 {chars} 字）：用 ocr 子命令指定页")
    con = connect()
    sid = register(con, path, pages, "text")
    added = 0
    for i in range(1, pages + 1):
        txt = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(path), "-"],
                             capture_output=True, text=True).stdout
        if put_page(con, sid, i, txt, "pdftotext", force):
            added += 1
    con.commit()
    print(f"{path.name}: {pages} 页，新入库 {added} 页（文字层）")


def ocr_pages(path: Path, spec: str, engine="rapidocr", dpi=300, force=False):
    if engine != "rapidocr":
        sys.exit("目前只实现 rapidocr；MinerU 起来后可加 engine=mineru")
    from rapidocr import RapidOCR
    con = connect()
    pages, _, ok = probe(path)
    sid = register(con, path, pages, "ocr")
    lo, _, hi = spec.partition("-")
    lo = int(lo); hi = int(hi or lo)
    eng = RapidOCR()
    added = 0
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(lo), "-l", str(hi), "-png",
                        str(path), f"{td}/p"], check=True)
        for img in sorted(Path(td).glob("p-*.png")):
            no = int(img.stem.split("-")[1])
            row = con.execute("SELECT 1 FROM pages WHERE source_id=? AND page=?", (sid, no)).fetchone()
            if row and not force:
                continue
            r = eng(str(img))
            text = "".join(r.txts or [])
            put_page(con, sid, no, text, f"rapidocr@{dpi}", force)
            added += 1
    con.commit()
    print(f"{path.name}: OCR {lo}-{hi} 页，新入库 {added} 页（rapidocr {dpi}dpi）")


def search(term: str, limit=20):
    con = connect()
    rows = con.execute("""
        SELECT s.title, p.page, p.text FROM pages_fts f
        JOIN pages p ON p.source_id=f.source_id AND p.page=f.page
        JOIN sources s ON s.id=f.source_id
        WHERE pages_fts MATCH ? LIMIT ?""", (f'"{term}"', limit)).fetchall()
    if not rows:
        print("未命中")
        return
    for title, page, text in rows:
        i = text.find(term)
        ctx = text[max(0, i - 50): i + 70].replace("\n", " ")
        print(f"{title} p{page}：…{ctx}…")


def stats():
    con = connect()
    print("来源：")
    for title, layer, pages, n in con.execute("""
        SELECT s.title, s.layer, s.pages, COUNT(p.page) FROM sources s
        LEFT JOIN pages p ON p.source_id=s.id GROUP BY s.id ORDER BY s.title"""):
        print(f"  {title:<42} {layer:<10} {n}/{pages} 页")
    total = con.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    print(f"合计 {total} 页")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("ingest"); p1.add_argument("file"); p1.add_argument("--force", action="store_true")
    p2 = sub.add_parser("ocr"); p2.add_argument("file"); p2.add_argument("--pages", required=True)
    p2.add_argument("--dpi", type=int, default=300); p2.add_argument("--force", action="store_true")
    p3 = sub.add_parser("search"); p3.add_argument("term"); p3.add_argument("--limit", type=int, default=20)
    sub.add_parser("stats")
    a = ap.parse_args()
    if a.cmd == "ingest":
        ingest(Path(a.file), a.force)
    elif a.cmd == "ocr":
        ocr_pages(Path(a.file), a.pages, dpi=a.dpi, force=a.force)
    elif a.cmd == "search":
        search(a.term, a.limit)
    else:
        stats()


if __name__ == "__main__":
    main()
