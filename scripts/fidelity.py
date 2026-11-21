#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""保真审计：改了文字之后，核对事实层有没有被动过。

    python3 scripts/fidelity.py 原稿.md 改后.md
    python3 scripts/fidelity.py 原稿.md 改后.md --json

比对六类：数字、单位、引用、否定、限定（可能/相关/显著…）、比较方向。
任何一类在改后消失或新增，都会列出来；数字或引用有变化时退出码 1。

这是 humanizer 最容易出事的环节：改得顺了，顺手把「可能」改成「会」、
把「相关」改成「导致」、把 5% 写成 5.0%。这个脚本把这类改动拦下来。
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

NUM = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|kcal|kJ|mg|g|kg|mL|L|cm|mm|mmHg|kg/m²|小时|分钟|天|周|个月|年|岁|次|份|倍)?")
CITE = re.compile(r"\[\d+(?:[-,–]\d+)?\]|（[^）]{0,20}\d{4}[^）]{0,10}）|\([^)]{0,20}\d{4}[^)]{0,10}\)")
HEDGE = ["可能", "或许", "提示", "相关", "倾向于", "有待", "尚不", "据估计", "约", "左右"]
NEG = ["不", "无", "未", "非", "缺乏", "排除"]
COMPARE = ["高于", "低于", "增加", "减少", "上升", "下降", "升高", "降低", "优于", "劣于"]


def extract(text: str):
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    return {
        "numbers": Counter(NUM.findall(body)),
        "citations": Counter(CITE.findall(body)),
        "hedges": Counter(w for w in HEDGE if w in body),
        "negations": Counter(w for w in NEG if w in body),
        "compares": Counter(w for w in COMPARE if w in body),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("revised")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    a = extract(Path(args.original).read_text(encoding="utf-8"))
    b = extract(Path(args.revised).read_text(encoding="utf-8"))

    report = {}
    hard = False
    for key, label in (("numbers", "数字"), ("citations", "引用"),
                       ("hedges", "限定词"), ("negations", "否定词"), ("compares", "比较方向")):
        lost = a[key] - b[key]
        added = b[key] - a[key]
        if lost or added:
            report[label] = {"lost": dict(lost), "added": dict(added)}
        if key in ("numbers", "citations") and (lost or added):
            hard = True

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        if not report:
            print("保真审计通过：数字、引用、限定、否定、比较方向均未变化")
        for label, d in report.items():
            print(f"[{label}]")
            if d["lost"]:
                print(f"  丢失/改掉：{d['lost']}")
            if d["added"]:
                print(f"  新增/改成：{d['added']}")
        print("\n说明：限定词与否定词的变化需要人工确认；数字与引用变化直接判失败。")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
