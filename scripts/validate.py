#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""仓库自检：CI 与本地共用。零依赖。

检查五件事：
1. 语料段数与字数在预期范围（防止误删语料）；
2. 每条规则都能编译，规则表没有重复编号；
3. 正样本误报率 <15%，命中密度差 ≥3×；
4. examples/after.md 的 20 段改写后文本段落级零命中；
5. 文档里引用的路径都存在（README / SKILL 的相对链接）。

用法：
    python3 scripts/validate.py
    python3 scripts/validate.py --quiet
"""

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stats import read_segments, nchars  # noqa: E402

spec = importlib.util.spec_from_file_location("check", ROOT / "scripts" / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

FAILED = []


def ok(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}{('  ' + detail) if detail else ''}")
    if not condition:
        FAILED.append(name)


def hits(body):
    total = sum(i["count"] for i in check.rule_hits(body))
    for group, rid, name, count, hint in check.structural_checks(body)[0]:
        if group in "LTC":
            total += count
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    # 1 语料规模
    corpus = read_segments(ROOT / "references" / "corpus")
    chars = sum(nchars(b) for _, b in corpus)
    ok("语料段数 ≥ 130", len(corpus) >= 130, f"{len(corpus)} 段 / {chars} 字")
    ok("语料字数 ≥ 45000", chars >= 45000, f"{chars}")

    # 2 规则表完整性
    ids = [r[1] for r in check.RULES] + [d[0] for d in check.DENSITY_RULES] + ["C1", "P1"]
    ok("规则编号不重复", len(ids) == len(set(ids)), f"{len(ids)} 条")
    bad = []
    for r in check.RULES:
        try:
            re.compile(r[3])
        except re.error as e:  # pragma: no cover
            bad.append(f"{r[1]}: {e}")
    ok("全部正则可编译", not bad, "；".join(bad))

    # 3 评测指标
    gold = read_segments(ROOT / "eval" / "gold")
    neg = read_segments(ROOT / "eval" / "neg")
    g_hits = sum(hits(b) for _, b in gold)
    g_chars = sum(nchars(b) for _, b in gold)
    n_hits = sum(hits(b) for _, b in neg)
    n_chars = sum(nchars(b) for _, b in neg)
    g_density = g_hits / max(g_chars, 1) * 1000
    n_density = n_hits / max(n_chars, 1) * 1000
    ratio = n_density / max(g_density, 1e-6)
    flagged = sum(1 for _, b in gold if hits(b))
    fp = flagged / max(len(gold), 1) * 100
    ok("密度差 ≥ 3×", ratio >= 3, f"{ratio:.1f}×（{g_density:.2f} vs {n_density:.2f}）")
    ok("段级误报率 < 15%", fp < 15, f"{fp:.1f}%（{flagged}/{len(gold)}）")

    # 4 改写示例零命中
    after = (ROOT / "examples" / "after.md").read_text(encoding="utf-8")
    dirty = []
    for m in re.finditer(r"^## (\d{2}) .*?\n\n(.*?)(?=\n## |\n---|\Z)", after, re.S | re.M):
        para = [p for p in m.group(2).strip().split("\n\n") if p.strip()][0]
        if hits(para):
            dirty.append(m.group(1))
    ok("examples/after.md 段落级零命中", not dirty, "、".join(dirty))

    # 5 链式路径存在
    missing = []
    for md in ("README.md", "README.en.md", "SKILL.md"):
        text = (ROOT / md).read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", text):
            if link.startswith(("http", "mailto")):
                continue
            if not (ROOT / link).exists():
                missing.append(f"{md} → {link}")
    ok("文档内相对链接有效", not missing, "；".join(missing[:5]))

    if not args.quiet:
        print()
    if FAILED:
        print(f"失败 {len(FAILED)} 项：" + "、".join(FAILED))
        return 1
    print(f"全部通过（{len(check.RULES)} 条计数规则 + 3 项体例）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
