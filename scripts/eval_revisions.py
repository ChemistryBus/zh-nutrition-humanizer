#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用作者自己的修订记录评测检查器：作者改过的段落，工具抓到了多少。

    python3 scripts/eval_revisions.py 初稿.md 定稿.md

方法：
1. 按段落对齐两份稿子（difflib，按文本相似度）；
2. 「改过的段落」= 对齐后发生替换/删除/新增的段落；
3. 对初稿的每个段落跑检查器，看是否有命中；
4. 统计段落级召回与误报，以及每条规则在「改过 / 没改」段落上的分布。

注意：作者的改动包含事实增删与结构调整，不全是语体问题，所以召回天然偏低；
这个数字用来看「工具能不能帮上忙」，不是用来看「作者改得对不对」。
"""

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check as C


def sentences(text: str):
    """切成句子，跳过标题、表格、参考文献。"""
    text = re.sub(r"^#+ .*$", "", text, flags=re.M)
    text = re.sub(r"^\|.*$", "", text, flags=re.M)
    text = re.sub(r"^\[\d+\].*$", "", text, flags=re.M)
    out = []
    for s in re.split(r"(?<=[。！？])", text):
        s = s.strip()
        if len(re.sub(r"\s", "", s)) >= 12:
            out.append(s)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("final")
    args = ap.parse_args()

    base = sentences(Path(args.baseline).read_text(encoding="utf-8"))
    final = sentences(Path(args.final).read_text(encoding="utf-8"))

    sm = difflib.SequenceMatcher(None, base, final)
    changed, unchanged = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            unchanged.extend(base[i1:i2])
        elif tag == "replace":
            changed.extend(base[i1:i2])
        elif tag == "delete":
            changed.extend(base[i1:i2])

    def hits(p):
        r = C.analyze(p)
        return {i["id"] for i in r["items"] + r["doc_issues"] if i["group"] in "LTCKS" and i["id"] != "P1"}

    fc = Counter(); fu = Counter()
    hit_c = hit_u = 0
    for p in changed:
        h = hits(p)
        if h:
            hit_c += 1
            fc.update(h)
    for p in unchanged:
        h = hits(p)
        if h:
            hit_u += 1
            fu.update(h)

    print(f"句子对齐：初稿 {len(base)} 句，定稿 {len(final)} 句")
    print(f"作者改过的句子：{len(changed)}，其中被工具命中：{hit_c}（{hit_c / max(len(changed),1) * 100:.1f}%）")
    print(f"作者没动的句子：{len(unchanged)}，其中被工具命中：{hit_u}（{hit_u / max(len(unchanged),1) * 100:.1f}%）")
    print("\n规则在「改过」句子上的命中次数（top）：")
    for rid, n in fc.most_common(10):
        print(f"  {rid:<4} {n}")
    print("\n规则在「没动」句子上的命中次数（top，误报风险）：")
    for rid, n in fu.most_common(10):
        print(f"  {rid:<4} {n}")


if __name__ == "__main__":
    main()
