#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「三件套」交付一篇改稿：改后文本 + 改了什么 + 保真审计（含待确认问题）。

    python3 scripts/deliver.py 原稿.md 改后.md
    python3 scripts/deliver.py 原稿.md 改后.md --out 交付.md

只做汇总，不改任何文字。改写由人/agent 完成，这里负责把「改了什么、有没有动事实、
还有什么要作者拍板」三件事一次说清，避免只丢一版新稿过去。
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as C
import fidelity as F


def rule_counts(text):
    r = C.analyze(text)
    c = Counter()
    for i in r["items"] + r["doc_issues"]:
        if i["group"] in "LTCKS" and i["id"] != "P1":
            c[i["id"]] += i["count"]
    return c


def build(original: str, revised: str) -> str:
    before, after = rule_counts(original), rule_counts(revised)
    a, b = F.extract(original), F.extract(revised)

    out = ["## 改后文本", "", revised.strip(), "", "## 改了什么", ""]
    fixed = {k: before[k] - after.get(k, 0) for k in before if before[k] > after.get(k, 0)}
    remain = {k: after[k] for k in after if after[k] > 0}
    if fixed:
        out.append("已消除：" + "、".join(f"{k}×{v}" for k, v in sorted(fixed.items())))
    if remain:
        out.append("仍有命中：" + "、".join(f"{k}×{v}" for k, v in sorted(remain.items())))
    if not fixed and not remain:
        out.append("机检层无变化。")
    out.append("")

    out += ["## 保真审计", ""]
    hard = False
    rows = []
    for key, label in (("numbers", "数字"), ("citations", "引用"), ("hedges", "限定词"),
                       ("negations", "否定词"), ("compares", "比较方向")):
        lost, added = a[key] - b[key], b[key] - a[key]
        if lost or added:
            if key in ("numbers", "citations"):
                hard = True
            rows.append(f"| {label} | {dict(lost) or '无'} | {dict(added) or '无'} |")
    if rows:
        out += ["| 类别 | 丢失/改掉 | 新增/改成 |", "|---|---|---|"] + rows
    else:
        out.append("六类均未变化：数字、引用、限定词、否定词、比较方向。")
    out.append("")

    out += ["## 待确认问题", ""]
    qs = []
    if hard:
        qs.append("数字或引用发生变化，请核对是否为笔误。")
    if a["hedges"] - b["hedges"]:
        qs.append(f"限定词减少：{dict(a['hedges'] - b['hedges'])}。确认没有把「可能/相关」写成确定结论。")
    if a["negations"] - b["negations"]:
        qs.append(f"否定词减少：{dict(a['negations'] - b['negations'])}。确认没有删掉「不/未/无」的限定。")
    if a["compares"] != b["compares"]:
        qs.append("比较方向有变化，请确认没有把「高于/低于」写反。")
    out += [f"- {q}" for q in qs] if qs else ["- 无。"]
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("revised")
    ap.add_argument("--out", metavar="PATH")
    args = ap.parse_args()
    text = build(Path(args.original).read_text(encoding="utf-8"),
                 Path(args.revised).read_text(encoding="utf-8"))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
