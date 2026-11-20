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
import subprocess
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

    # 5 术语规则：fixture 能抓、正样本不误报
    fixture = ROOT / "tests" / "fixtures" / "terms_bad.md"
    if fixture.exists():
        k = sum(i["count"] for i in check.rule_hits(fixture.read_text(encoding="utf-8"))
                if i["group"] == "K")
        ok("术语样例命中 ≥5", k >= 5, f"{k} 处")
    k_gold = sum(i["count"] for _, b in gold for i in check.rule_hits(b) if i["group"] == "K")
    ok("正样本术语误报 = 0", k_gold == 0, f"{k_gold} 处")

    # 6 润色工具：样例输出稳定，且不改变任何数值
    sys.path.insert(0, str(ROOT / "scripts"))
    import polish as polisher
    src = (ROOT / "tests" / "fixtures" / "polish_in.md").read_text(encoding="utf-8")
    exp = (ROOT / "tests" / "fixtures" / "polish_expected.md").read_text(encoding="utf-8")
    got, ch = polisher.polish(src)
    ok("润色输出与样例一致", got == exp, f"{len(ch)} 处改动")
    code_src = (ROOT / "tests" / "fixtures" / "polish_code_in.md").read_text(encoding="utf-8")
    code_exp = (ROOT / "tests" / "fixtures" / "polish_code_expected.md").read_text(encoding="utf-8")
    ok("润色不碰代码块", polisher.polish(code_src)[0] == code_exp)
    once = polisher.polish(src)[0]
    ok("润色幂等", polisher.polish(once)[0] == once)

    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        f = Path(td) / "d.md"
        f.write_text("赛前 5 至 7 天\n", encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "polish.py"), str(f)],
                       capture_output=True, timeout=60)
        ok("润色默认干跑不写文件", sorted(x.name for x in Path(td).iterdir()) == ["d.md"])

    from collections import Counter
    lost = Counter(re.findall(r"\d+(?:\.\d+)?", src)) - Counter(re.findall(r"\d+(?:\.\d+)?", got))
    ok("润色不丢失原有数值", not lost, "；".join(f"{k}×{v}" for k, v in lost.items()))

    # 7 真实稿术语层：1106 稿的问题类型
    real = (ROOT / "tests" / "fixtures" / "real_terms.md").read_text(encoding="utf-8")
    r = check.analyze(real)
    ids = {}
    for i in r["items"] + r["doc_issues"]:
        ids.setdefault(i["id"], 0)
        ids[i["id"]] += i["count"]
    ok("真实稿：首选术语命中", ids.get("K2") == 2, f"K2={ids.get('K2')}")
    ok("真实稿：缩写首现命中", ids.get("S4") == 4, f"S4={ids.get('S4')}")
    ok("真实稿：汉字单位命中", ids.get("S5") == 3, f"S5={ids.get('S5')}")
    ok("真实稿：破折号区间命中", ids.get("C2") == 5, f"C2={ids.get('C2')}")

    # 8 BMI 阈值混淆
    bmi = (ROOT / "tests" / "fixtures" / "bmi_thresholds.md").read_text(encoding="utf-8")
    rb = check.analyze(bmi)
    k1 = sum(i["count"] for i in rb["items"] + rb["doc_issues"] if i["id"] == "K1")
    ok("BMI 阈值错写被捕获", k1 == 2, f"K1={k1}")

    # 9 定义句数值核对
    dfn = (ROOT / "tests" / "fixtures" / "definitions.md").read_text(encoding="utf-8")
    rd = check.analyze(dfn)
    k3 = sum(i["count"] for i in rd["items"] + rd["doc_issues"] if i["id"] == "K3")
    ok("定义句数值错写被捕获", k3 == 2, f"K3={k3}")

    # 10 体检报告可运行
    import subprocess as _sp
    r = _sp.run([sys.executable, str(ROOT / "scripts" / "audit.py"),
                 str(ROOT / "examples" / "before.md")], capture_output=True, text=True, timeout=120)
    ok("audit.py 能出报告", r.returncode == 0 and "术语层" in r.stdout, r.stderr[:80])

    # 11 链式路径存在
    missing = []
    for md in ("README.md", "README.en.md", "SKILL.md", "THIRD_PARTY_NOTICES.md", "examples/walkthrough.md", "docs/harness-test.md", "references/source-map.md", "docs/real-world-test.md"):
        text = (ROOT / md).read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)#]+?)(?:#[^)]*)?\)", text)
        links += re.findall(r'(?:href|src)="([^"#]+?)"', text)
        for link in links:
            if link.startswith(("http", "mailto", "#")):
                continue
            if not (ROOT / link).exists():
                missing.append(f"{md} → {link}")
    ok("文档内相对链接有效", not missing, "；".join(missing[:5]))

    if not args.quiet:
        print()
    if FAILED:
        print(f"失败 {len(FAILED)} 项：" + "、".join(FAILED))
        return 1
    print(f"全部通过（{len(check.RULES) + 2} 条语体/结构规则 + {len(check.TERM_RULES)} 条术语规则 + 5 项体例"
          f" + 术语层：首选术语 {len(check.PREFERRED_TERMS)}、缩写 {len(check.ABBREVIATIONS)}、单位 {len(check.UNIT_WORDS)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
