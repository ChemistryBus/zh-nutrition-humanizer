#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确定性润色：只做有依据、可逆、不碰事实的替换。

用法：
    python3 scripts/polish.py 稿子.md                # 输出到 稿子.polished.md，并列出改动
    python3 scripts/polish.py 稿子.md --stdout       # 打到标准输出
    python3 scripts/polish.py 稿子.md --write        # 原地覆盖（会先备份 .bak）
    python3 scripts/polish.py 稿子.md --json         # 机器可读的改动清单

只改五类，全部有标准或语料依据：
    1. 术语误写        维他命→维生素、炭水化合物→碳水化合物、必要氨基酸→必需氨基酸、粗纤维→膳食纤维
    2. 数值区间        5 至 7 → 5～7（GB/T 15835）
    3. 汉字数字＋单位  三百毫克 → 300 mg
    4. 术语层级        能量可利用性 → 能量可用性
    5. 多余空格        数字与单位之间的全角空格、连续空格

不做：同义改写、句式重排、增删句子、动数字。判断类改动留给人和 SKILL.md 的流程。
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TERMS_PATH = HERE.parent / "references" / "terms.json"

CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

UNIT_MAP = [("毫克", "mg"), ("微克", "μg"), ("纳克", "ng"), ("千卡", "kcal"),
            ("千焦", "kJ"), ("毫升", "mL"), ("克", "g")]

# 术语替换：只收确定性错误（与 references/terms.json 的 wrong 同步）
TERM_FIX = [
    (r"维他命", "维生素"),
    (r"炭水化合物", "碳水化合物"),
    (r"必要氨基酸", "必需氨基酸"),
    (r"粗纤维", "膳食纤维"),
    (r"能量可利用性", "能量可用性"),
]


def cn2num(s: str):
    """把 1–999 的汉字数词转成整数；无法解析返回 None。"""
    if not s:
        return None
    if "百" in s:
        head, _, tail = s.partition("百")
        h = CN_DIGITS.get(head, 1) if head else 1
        rest = cn2num(tail) if tail else 0
        return None if rest is None else h * 100 + rest
    if "十" in s:
        head, _, tail = s.partition("十")
        h = CN_DIGITS.get(head, 1) if head else 1
        t = CN_DIGITS.get(tail, 0) if tail else 0
        return h * 10 + t
    if len(s) == 1 and s in CN_DIGITS:
        return CN_DIGITS[s]
    if all(ch in CN_DIGITS for ch in s) and len(s) > 1:
        n = 0
        for ch in s:
            n = n * 10 + CN_DIGITS[ch]
        return n
    return None


def fmt_num(n: int) -> str:
    return str(n)


def split_quotes(text: str):
    """把文本切成 (可改写段, 引号段) 交替，引号内不改。"""
    pattern = re.compile(r"(“[^”]*”|\"[^\"]*\"|「[^」]*」)")
    parts = []
    pos = 0
    for m in pattern.finditer(text):
        parts.append((text[pos:m.start()], True))
        parts.append((m.group(0), False))
        pos = m.end()
    parts.append((text[pos:], True))
    return parts


def fix_segment(seg: str, changes: list):
    # 1 术语
    for pat, rep in TERM_FIX:
        def _rep(m, rep=rep):
            changes.append((m.group(0), rep))
            return rep
        seg = re.sub(pat, _rep, seg)

    # 2 汉字数字区间＋单位：二十到三十克 → 20～30 g（先做，避免被单值规则拆开）
    def cn_range_unit(m):
        a, b = cn2num(m.group(1)), cn2num(m.group(2))
        if not a or not b:
            return m.group(0)
        unit = dict(UNIT_MAP)[m.group(3)]
        new = f"{a}～{b} {unit}"
        changes.append((m.group(0), new))
        return new
    seg = re.sub(r"([一二三四五六七八九十百两]+)(?:到|至)([一二三四五六七八九十百两]+)(毫克|微克|纳克|千卡|千焦|毫升|克)",
                 cn_range_unit, seg)

    # 3 汉字数字＋单位：三百毫克 → 300 mg
    def cn_unit(m):
        n = cn2num(m.group(1))
        if not n:
            return m.group(0)
        unit = dict(UNIT_MAP)[m.group(2)]
        new = f"{n} {unit}"
        changes.append((m.group(0), new))
        return new
    seg = re.sub(r"([一二三四五六七八九十百两]+)(毫克|微克|纳克|千卡|千焦|毫升|克)", cn_unit, seg)

    # 4 百分数区间：20% 至 50% → 20%～50%
    def pct_fix(m):
        new = f"{m.group(1)}%～{m.group(2)}%"
        changes.append((m.group(0), new))
        return new
    seg = re.sub(r"(\d+(?:\.\d+)?)\s*[%％]\s*(?:至|到)\s*(\d+(?:\.\d+)?)\s*[%％]", pct_fix, seg)

    # 5 阿拉伯数字区间：5 至 7 → 5～7
    def range_fix(m):
        new = f"{m.group(1)}～{m.group(2)}"
        changes.append((m.group(0), new))
        return new
    seg = re.sub(r"(\d+)\s*(?:至|到)\s*(\d+)", range_fix, seg)

    # 6 空白
    seg = re.sub(r"(\d)[ \u3000]+(mg|μg|ng|g|kg|kcal|kJ|mL|L|mmol)\b", r"\1 \2", seg)
    seg = re.sub(r"[ \u3000]{2,}", " ", seg)
    return seg


def polish(text: str):
    """返回 (新文本, 改动清单)。跳过 YAML frontmatter。"""
    m = re.match(r"^---\n.*?\n---\n", text, flags=re.S)
    head, body = (text[:m.end()], text[m.end():]) if m else ("", text)
    changes = []
    out = []
    for seg, editable in split_quotes(body):
        out.append(fix_segment(seg, changes) if editable else seg)
    return head + "".join(out), changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    new, changes = polish(text)

    if args.json:
        print(json.dumps({"file": str(path), "changes": changes, "count": len(changes)},
                         ensure_ascii=False, indent=1))
    elif args.stdout:
        sys.stdout.write(new)
    else:
        out = path.with_suffix(path.suffix + ".polished.md") if path.suffix else path.with_name(path.name + ".polished.md")
        out.write_text(new, encoding="utf-8")
        print(f"改动 {len(changes)} 处 → {out}")
        for a, b in changes[:40]:
            print(f"  {a} → {b}")
        if len(changes) > 40:
            print(f"  ……另有 {len(changes) - 40} 处")

    if args.write:
        shutil.copyfile(path, str(path) + ".bak")
        path.write_text(new, encoding="utf-8")
        print(f"已覆盖 {path}（备份 {path}.bak）")


if __name__ == "__main__":
    main()
