#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规则评测：命中密度差、误报率、阈值扫描。

用法：
    python3 scripts/eval.py --gold eval/gold --neg eval/neg
    python3 scripts/eval.py --gold eval/gold --neg eval/neg --sweep 1-8
    python3 scripts/eval.py --gold eval/gold --neg eval/neg --json

定义：
    命中密度   = 命中数 / 千字
    密度差     = 负样本密度 / 正样本密度（越大越好，目标 ≥3）
    段级误报率 = 正样本里至少被标一次的段落占比（越小越好，目标 <15%）
    规则误报率 = 该规则在正样本上的命中 / 该规则全部命中
    拐点       = 在误报率 <15% 的约束下，使 TPR − FPR 最大的阈值

正样本：权威原文（教材、膳食指南、食养指南、DRIs），未参与建基线。
负样本：同主题大模型生成段落（科普体 + 教材体各半）。
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from stats import nchars, read_segments  # noqa: E402

spec = importlib.util.spec_from_file_location("check", HERE / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def segment_hits(body: str):
    """返回 ({规则名: 命中数}, 总命中数)。"""
    per_rule = {}
    total = 0
    for item in check.rule_hits(body):
        per_rule[item["rule"]] = per_rule.get(item["rule"], 0) + item["count"]
        total += item["count"]
    struct, _ = check.structural_checks(body)
    for group, rid, name, count, hint in struct:
        if group not in "LTC":      # 提示类不计入密度
            continue
        per_rule[name] = per_rule.get(name, 0) + count
        total += count
    return per_rule, total


def density(segs):
    total_hits = total_chars = flagged = 0
    per_rule = {}
    for _, body in segs:
        hits, n = segment_hits(body)
        total_hits += n
        total_chars += nchars(body)
        if n:
            flagged += 1
        for k, v in hits.items():
            per_rule[k] = per_rule.get(k, 0) + v
    return {"n": len(segs), "chars": total_chars, "hits": total_hits,
            "per_k": round(total_hits / max(total_chars, 1) * 1000, 2),
            "flagged": flagged,
            "flagged_share": round(flagged / max(len(segs), 1) * 100, 1),
            "per_rule": per_rule}


def sweep(gold, neg, lo, hi):
    gold_d = [segment_hits(b)[1] / max(nchars(b), 1) * 1000 for _, b in gold]
    neg_d = [segment_hits(b)[1] / max(nchars(b), 1) * 1000 for _, b in neg]
    rows = []
    for t in range(lo, hi + 1):
        tpr = sum(1 for d in neg_d if d >= t) / max(len(neg_d), 1)
        fpr = sum(1 for d in gold_d if d >= t) / max(len(gold_d), 1)
        rows.append({"threshold": t, "tpr": round(tpr, 3), "fpr": round(fpr, 3),
                     "youden": round(tpr - fpr, 3)})
    ok = [r for r in rows if r["fpr"] < 0.15]
    knee = max(ok, key=lambda r: r["youden"]) if ok else max(rows, key=lambda r: r["youden"])
    return rows, knee


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True, help="正样本目录")
    ap.add_argument("--neg", required=True, help="负样本目录")
    ap.add_argument("--sweep", default="1-8")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    gold = read_segments(Path(args.gold))
    neg = read_segments(Path(args.neg))
    if not gold or not neg:
        print("正样本或负样本为空", file=sys.stderr)
        sys.exit(2)

    g, n = density(gold), density(neg)
    ratio = round(n["per_k"] / max(g["per_k"], 0.01), 2)
    lo, hi = [int(x) for x in args.sweep.split("-")]
    rows, knee = sweep(gold, neg, lo, hi)

    rules = {}
    for name in set(list(g["per_rule"]) + list(n["per_rule"])):
        rules[name] = {"gold": g["per_rule"].get(name, 0), "neg": n["per_rule"].get(name, 0)}
    data = {"gold": g, "neg": n, "ratio": ratio, "sweep": rows, "knee": knee, "rules": rules}
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return

    print(f"正样本 {g['n']} 段 / {g['chars']} 字；负样本 {n['n']} 段 / {n['chars']} 字\n")
    print(f"命中密度：正样本 {g['per_k']} / 千字，负样本 {n['per_k']} / 千字，"
          f"密度差 {ratio}×（目标 ≥3）")
    print(f"段级误报率：{g['flagged']}/{g['n']} = {g['flagged_share']}%（目标 <15%）")
    print(f"段级召回：负样本 {n['flagged']}/{n['n']} = {n['flagged_share']}%")
    regs = {}
    for meta, body in neg:
        r = meta.get("register", "未标注")
        _, k = segment_hits(body)
        regs.setdefault(r, [0, 0])
        regs[r][0] += 1
        if k:
            regs[r][1] += 1
    for r, (tot, hit) in sorted(regs.items()):
        print(f"  {r}：{hit}/{tot} = {hit/max(tot,1)*100:.0f}%")
    print()

    print("| 规则 | 正样本 | 负样本 | 规则误报率 | 判读 |")
    print("|---|---:|---:|---:|---|")
    for name, d in sorted(rules.items(), key=lambda kv: -(kv[1]["gold"] * 2 + kv[1]["neg"])):
        tot = d["gold"] + d["neg"]
        if tot == 0:
            continue
        fp = d["gold"] / tot
        verdict = "删" if d["neg"] == 0 else ("保留" if fp < 0.15 else "窄化")
        print(f"| {name} | {d['gold']} | {d['neg']} | {fp*100:.0f}% | {verdict} |")

    print("\n阈值扫描（命中 / 千字）\n")
    print("| 阈值 | 召回 TPR | 误报 FPR | Youden J |")
    print("|---:|---:|---:|---:|")
    for r in rows:
        mark = "  ← 拐点" if r["threshold"] == knee["threshold"] else ""
        print(f"| {r['threshold']} | {r['tpr']:.0%} | {r['fpr']:.0%} | {r['youden']:+.2f}{mark} |")
    print(f"\n拐点阈值 {knee['threshold']}：召回 {knee['tpr']:.0%}，误报 {knee['fpr']:.0%}，"
          f"J = {knee['youden']:+.2f}")
    ok_ratio, ok_fp = ratio >= 3, g["flagged_share"] < 15
    print(f"验收：密度差 {ratio}× {'通过' if ok_ratio else '未通过'}；"
          f"段级误报率 {g['flagged_share']}% {'通过' if ok_fp else '未通过'}")


if __name__ == "__main__":
    main()
