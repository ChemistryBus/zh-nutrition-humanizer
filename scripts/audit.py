#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给一篇真实稿出一页体检报告。

    python3 scripts/audit.py 稿子.md
    python3 scripts/audit.py 稿子.docx          # 需要 python-docx；没装则提示
    python3 scripts/audit.py 稿子.md --out 报告.md

报告内容：语体对照、命中分类、术语层（带依据）、可自动改的与需人工判断的、下一步。
不改原稿；.docx 只读取正文段落。
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as C
import polish as P
import fidelity as F


def read_input(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        try:
            from docx import Document
        except ImportError:
            sys.exit("读 .docx 需要 python-docx：pip install python-docx；或先另存为 .md")
        doc = Document(str(path))
        return "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
    return path.read_text(encoding="utf-8")


def fidelity_section(original: str, revised: str) -> str:
    a, b = F.extract(original), F.extract(revised)
    out = ["## 保真审计（原稿 vs 改后稿）", ""]
    hard = False
    for key, label in (("numbers", "数字"), ("citations", "引用"), ("hedges", "限定词"),
                       ("negations", "否定词"), ("compares", "比较方向")):
        lost, added = a[key] - b[key], b[key] - a[key]
        if lost or added:
            if key in ("numbers", "citations"):
                hard = True
            out.append(f"- **{label}**：丢失 {dict(lost) or '无'}；新增 {dict(added) or '无'}")
    if len(out) == 2:
        out.append("- 六类均未变化。")
    out += ["", "## 待确认问题", ""]
    if hard:
        out.append("- 数字或引用发生变化：先核对是否笔误，再决定是否保留。")
    if (a["hedges"] - b["hedges"]) or (a["negations"] - b["negations"]):
        out.append("- 限定词/否定词有减少：确认是否把「可能/相关」写成了确定结论。")
    if len(out) == 6:
        out.append("- 无。")
    out.append("")
    return "\n".join(out)


def render(text: str, title: str, revised: str = None) -> str:
    body = C.strip_front_matter(text)
    body = C.mask_markdown(body)
    res = C.analyze(text)
    st = C.doc_style(body)
    prof = C.PROFILES[C.DEFAULT_PROFILE]

    out = [f"# 稿件体检：{title}", ""]
    out += ["## 语体对照（默认膳食指南体）", "",
            "| 指标 | 本稿 | 基线 |", "|---|---:|---:|",
            f"| 句长中位 | {st['sent_med']} 字 | {prof['sent_med']}（{prof['sent_p10']}–{prof['sent_p90']}） |",
            f"| 连接词 | {st['conn']}/千字 | {prof['conn']} |",
            f"| 应/宜 | {st['ying']}/千字 | {prof['ying']} |",
            f"| 数字 | {st['nums']}/千字 | {prof['nums']} |",
            "", f"总命中 **{res['total']} 处 / {res['chars']} 字（{res['per_kchar']} 处每千字）**", ""]

    fam = Counter()
    for i in res["items"]:
        fam[i["group"]] += i["count"]
    names = {"L": "L 口语降维", "T": "T 模板化", "C": "C 结构", "K": "K 术语", "P": "P 提示"}
    out += ["| 族 | 命中 |", "|---|---:|"]
    for g in "LTCP":
        if fam.get(g):
            out.append(f"| {names[g]} | {fam[g]} |")
    out.append("")

    term = [i for i in res["items"] + res["doc_issues"] if i["id"] in ("K1", "K2", "S4", "S5")]
    out += ["## 术语层", ""]
    if not term:
        out += ["未发现术语问题。", ""]
    else:
        out += ["| 编号 | 问题 | 次数 | 依据 |", "|---|---|---:|---|"]
        for i in term:
            out.append(f"| {i['id']} | {i['rule']} | {i['count']} | {i['evidence'][:60]} |")
        out.append("")

    new, changes = P.polish(text)
    out += ["## 可自动改 vs 需人工判断", "",
            f"- 机械润色可改 **{len(changes)} 处**（术语误写、区间符号、汉字单位；不碰引号与代码块）",
            f"- 术语层共 **{sum(i['count'] for i in term)} 处**；其中可由 polish 自动改的见下表，其余（缩写补全称、首选写法取舍）留给人",
            ""]

    if changes:
        out += ["| 原写法 | 改法 |", "|---|---|"]
        seen = set()
        for a, b in changes:
            if (a, b) in seen:
                continue
            seen.add((a, b))
            out.append(f"| {a} | {b} |")
            if len(seen) >= 15:
                break
        if len(changes) > 15:
            out.append(f"| …… | 另有 {len(changes) - 15} 处 |")
        out.append("")

    if revised:
        out += [fidelity_section(text, revised)]

    out += ["## 下一步", "",
            "1. 跑 `python3 scripts/polish.py 稿子.md --out 稿子.改.md` 落盘机械改动；",
            "2. 按术语层清单人工补中文全称、统一首选写法；",
            "3. 再跑一次本命令，直到术语层为空；语体层按 `--diff` 逐条判断。", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", metavar="PATH")
    ap.add_argument("--title")
    ap.add_argument("--revised", metavar="PATH", help="改后稿，用于保真审计")
    args = ap.parse_args()
    path = Path(args.file)
    text = read_input(path)
    revised = read_input(Path(args.revised)) if args.revised else None
    report = render(text, args.title or path.stem, revised)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"报告已写入 {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
