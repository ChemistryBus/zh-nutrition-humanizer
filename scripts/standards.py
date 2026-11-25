#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查标准定义与三新公告。零依赖。

    python3 scripts/standards.py 营养强化剂
    python3 scripts/standards.py β-丙氨酸 --three-new
    python3 scripts/standards.py --list
"""

import argparse
import json
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "references"


def load(name):
    return json.loads((REF / name).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="术语名或三新名称")
    ap.add_argument("--three-new", action="store_true", help="查三新公告")
    ap.add_argument("--list", action="store_true", help="列出全部条目")
    args = ap.parse_args()

    if args.three_new:
        items = load("three_new.json")["items"]
        if args.list or not args.query:
            for x in items:
                print(f"{x['announcement']}  {x['category']}  {x['name']}  |  {x['scope']}")
            return
        hit = [x for x in items if args.query in x["name"] or args.query.lower() in x["name"].lower()]
        for x in hit:
            print(f"{x['name']}（{x['en']}）")
            print(f"  公告：{x['announcement']}（{x['date']}）")
            print(f"  类别：{x['category']}")
            print(f"  范围：{x['scope']}")
            print(f"  来源：{x['source_url']}")
        if not hit:
            print(f"未收录「{args.query}」；三新公告按年份补，查不到标待核。")
        return

    data = load("standards.json")
    stds = data["standards"]
    if args.list or not args.query:
        for x in stds:
            print(f"{x['id']} §{x['clause']}  {x['term']}  ({x['en']})")
        return
    hit = [x for x in stds if args.query in x["term"] or args.query in x.get("en", "")]
    for x in hit:
        print(f"{x['term']}（{x['en']}）")
        print(f"  定义：{x['definition']}")
        print(f"  出处：{x['id']} §{x['clause']}")
        if x.get("scope"):
            print(f"  范围：{x['scope']}")
        print(f"  文件：{x['file']}")
    if not hit:
        print(f"未收录「{args.query}」；查不到标待核，不凭记忆补写。")


if __name__ == "__main__":
    main()
