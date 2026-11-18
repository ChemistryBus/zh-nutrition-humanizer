#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选特征挖掘：在同一语料上比较「机构文本」与「大模型文本」。

用法：
    python3 scripts/features.py --gold references/corpus --neg eval/neg
    python3 scripts/features.py --gold references/corpus --neg eval/neg --min-ratio 2

输出每千字频率、出现该特征的段落占比、分离度，用于决定一条候选规则
值不值得写进 check.py。零依赖。
"""

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from stats import nchars, read_segments  # noqa: E402

# 候选特征：(家族, 名称, 正则, 预期方向)
#   inst = 机构文本里更多；llm = 大模型文本里更多；any = 方向未定
CANDIDATES = [
    ("口语", "别/不必祈使", r"(?<![特区级类个])别[把让忘指想]", "llm"),
    ("口语", "语气词", r"(嘛|呗|啦|哈|呀|哦)(?=[，。！？]|$)", "llm"),
    ("口语", "其实/说实话", r"(其实|说实话|说白了|老实说)", "llm"),
    ("口语", "挺/特/蛮", r"(挺[好难多]|特别[好难多]|蛮[好难多]|超[好难多])", "llm"),
    ("口语", "口语副词", r"(很容易|往往就|就会|才能|才不至于|反而更)", "llm"),
    ("口语", "第二人称", r"(你|您)(?!们)", "llm"),
    ("口语", "建议第二人称", r"建议你|如果你|你自己的", "llm"),
    ("口语", "口语化形容", r"(靠谱|划算|省事|稳住|扛饿|神化|带偏|硬扛|落地|打折|翻车|踩坑)", "llm"),
    ("比喻", "像/好比/相当于", r"(就像是|像是|好比|相当于|如同|犹如)", "llm"),
    ("比喻", "实体化名词", r"(钥匙|账本|口粮|燃料|垫子|帮手|保险|开关|放大器|信号|土壤|弹药|武器)", "llm"),
    ("结构", "破折号", r"——", "llm"),
    ("结构", "反问/感叹", r"[？！](?![）)])", "llm"),
    ("结构", "不是X而是Y", r"不是.{0,30}而是", "llm"),
    ("结构", "真正的X是", r"真正(的)?[^，。]{0,10}(是|在)", "llm"),
    ("结构", "才是/关键是", r"(才是|关键在|重点是|说白了)", "llm"),
    ("数字", "汉字数字+计量单位", r"[一二三四五六七八九十百千两]+(克|毫克|千卡|毫升|升|国际单位|克每)", "llm"),
    ("数字", "汉字数字区间", r"[一二三四五六七八九十]+\s*(到|至)\s*[一二三四五六七八九十]+\s*(克|毫克|千卡|毫升|餐|次|周|天)", "llm"),
    ("数字", "阿拉伯数字", r"\d", "inst"),
    ("数字", "数单位紧连", r"\d(?:g|mg|kg|kcal|kJ|ml|mL|L)(?![a-zA-Z])", "inst"),
    ("数字", "相对剂量 g/kg", r"g\s*/\s*kg", "inst"),
    ("数字", "百分号", r"%", "inst"),
    ("规范", "中文全称（英文）", r"[\u4e00-\u9fff]{2,12}（[A-Za-z][^）]{1,30}）", "inst"),
    ("规范", "见表/如表", r"(见表|如表|表\s*\d)", "inst"),
    ("规范", "年份出处", r"（\s*\d{4}\s*年\s*[^）]{0,20}）|《[^》]{4,40}》", "inst"),
    ("规范", "依据/根据", r"(依据|根据|按照|参照)", "inst"),
    ("连接", "此外/同时/另外", r"(此外|同时|另外)[，,]", "inst"),
    ("连接", "因此/所以", r"(因此|因而|所以)[，,]", "inst"),
    ("连接", "值得注意/需要指出", r"(值得注意|需要指出|应当指出)", "inst"),
    ("连接", "首先其次", r"(首先|其次|再次)[，,]", "inst"),
    ("连接", "综上/总之", r"(综上所述|总而言之|总之)", "inst"),
    ("连接", "不仅而且", r"不仅.{0,40}(而且|还|也)", "inst"),
    ("评价", "具有重要意义", r"(具有|有着)(重要|深远|积极)(的)?(意义|作用|影响)", "inst"),
    ("评价", "发挥作用", r"发挥(重要|积极|关键)?作用", "inst"),
    ("评价", "提供参考", r"提供(了)?(有益|重要)?(的)?(参考|借鉴)", "inst"),
    ("领域", "营销词", r"(神器|燃脂|暴涨|秒杀|必备|天花板|王炸|硬核|拉满)", "llm"),
    ("领域", "绝对化", r"(科学证明|彻底解决|一定能|百分百|毫无疑问|万能)", "llm"),
    ("领域", "无出处归属", r"(有研究(表明|显示|发现)|数据显示|专家指出|科学家发现)", "llm"),
    ("句式", "句末评价", r"[，,](这|那)(才|就)?(是|意味着)[^。]{0,20}。", "llm"),
    ("句式", "段末一句话", r"(.{10,40})[。！]\s*$", "any"),
]


def rate(segs, pat):
    hits = 0
    flagged = 0
    for _, b in segs:
        c = len(re.findall(pat, b))
        hits += c
        if c:
            flagged += 1
    chars = sum(nchars(b) for _, b in segs)
    return hits, hits / max(chars, 1) * 1000, flagged / max(len(segs), 1) * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--neg", required=True)
    ap.add_argument("--min-ratio", type=float, default=0.0)
    args = ap.parse_args()

    gold = read_segments(Path(args.gold))
    neg = read_segments(Path(args.neg))
    print(f"正样本 {len(gold)} 段 / {sum(nchars(b) for _, b in gold)} 字；"
          f"负样本 {len(neg)} 段 / {sum(nchars(b) for _, b in neg)} 字\n")
    print("| 家族 | 特征 | 正/千字 | 负/千字 | 倍数 | 正段占比 | 负段占比 | 分离 |")
    print("|---|---|---:|---:|---:|---:|---:|---|")
    rows = []
    for fam, name, pat, direction in CANDIDATES:
        gh, gr, gf = rate(gold, pat)
        nh, nr, nf = rate(neg, pat)
        ratio = (nr / gr) if gr > 0 else (999 if nr > 0 else 0)
        if direction == "inst":
            ratio = (gr / nr) if nr > 0 else (999 if gr > 0 else 0)
        rows.append((fam, name, gr, nr, ratio, gf, nf, direction))
    for fam, name, gr, nr, ratio, gf, nf, direction in sorted(rows, key=lambda r: -r[4]):
        if ratio < args.min_ratio:
            continue
        flag = "★" if ratio >= 3 else ""
        print(f"| {fam} | {name} | {gr:.2f} | {nr:.2f} | {ratio:.1f}× {flag} | "
              f"{gf:.0f}% | {nf:.0f}% | {direction} |")


if __name__ == "__main__":
    main()
