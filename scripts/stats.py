#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料基线统计（八项指标）。零依赖。

用法：
    python3 scripts/stats.py references/corpus            # 全部语料
    python3 scripts/stats.py references/corpus --json
    python3 scripts/stats.py references/corpus --by-source
    python3 scripts/stats.py references/corpus --compare references/negatives

语料文件格式（references/corpus/<source>/seg_NNN.md）：

    ---
    source: 中国居民膳食指南（2022）
    pages: "120-121"
    slice: middle
    ---
    正文一段，200–400 字。

输出八项：
    1 平均句长与分布
    2 连接词每千字频率
    3 每段句数
    4 第一人称使用
    5 数字与单位写法
    6 术语写法
    7 论断与依据的相对位置
    8 段落是否用连接词起句
"""

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- 文本工具

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CJK_GAP = re.compile(r"(?<=[\u4e00-\u9fff，。、；：！？（）“”《》])\s+(?=[\u4e00-\u9fff，。、；：！？（）“”《》])")
SENT_SPLIT = re.compile(r"(?<=[。！？!?])")
HEAD_RE = re.compile(r"^\s*#")
TABLE_RE = re.compile(r"<table|^\|")


def nchars(s: str) -> int:
    """字数：去掉所有空白后的字符数（与 check.py 一致）。"""
    return len(re.sub(r"\s", "", s))


def cjk_ratio(s: str) -> float:
    t = nchars(s)
    return len(CJK_RE.findall(s)) / max(t, 1)


def clean(text: str) -> str:
    """去 markdown 残留、去中文之间的换行空格、去表格块。"""
    text = re.sub(r"<table.*?</table>", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.M)
    text = CJK_GAP.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def read_segments(path: Path):
    """读 corpus / negatives 目录，返回 [(meta, body)]。"""
    out = []
    for f in sorted(path.rglob("*.md")):
        raw = f.read_text(encoding="utf-8")
        meta, body = {}, raw
        m = re.match(r"---\s*\n(.*?)\n---\s*\n", raw, flags=re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            body = raw[m.end():]
        body = clean(body)
        if nchars(body) >= 80:
            meta["_file"] = str(f.relative_to(path))
            out.append((meta, body))
    return out


def sentences(para: str):
    return [s.strip() for s in SENT_SPLIT.split(para) if nchars(s) > 1]


# ---------------------------------------------------------------- 词表

STRONG_CONN = [
    "此外", "同时", "另外", "值得注意", "需要指出", "必须指出", "应当指出",
    "首先", "其次", "再次", "最后", "综上所述", "总而言之", "总之",
    "由此可见", "一方面", "另一方面", "换言之", "也就是说", "具体而言",
    "一般来说", "总体而言", "事实上", "实际上",
]
LOGIC_CONN = [
    "因此", "因而", "所以", "由于", "因为", "但是", "然而", "不过",
    "如果", "即使", "虽然", "尽管", "随着", "例如", "比如", "其中",
]
ALL_CONN = STRONG_CONN + LOGIC_CONN

EVIDENCE_RE = re.compile(
    r"(研究(表明|发现|显示)|动物(实验|试验)|细胞(实验|试验)|Meta\s*[- ]?分析|荟萃分析|"
    r"系统(评价|综述)|队列研究|随机对照|指南(推荐|建议|指出)|标准(规定|要求)|"
    r"数据(显示|表明)|见表|如表|依据|来源[:：]|〔[ⅠⅡⅢⅣ]〕|\[\d+\]|（[A-Z][^）]{2,40}\d{4})"
)

UNIT_PATTERNS = [
    ("g/kg/d", r"g\s*/\s*kg\s*/\s*d"),
    ("g/kg", r"g\s*/\s*kg(?!\s*/)"),
    ("g·kg⁻¹", r"g\s*[·・]\s*kg"),
    ("g", r"(?<![a-zA-Z/·])g(?![a-zA-Z/])"),
    ("mg", r"(?<![a-zA-Z])mg(?![a-zA-Z])"),
    ("μg", r"μ\s*g|ug(?![a-zA-Z])"),
    ("kcal", r"kcal"),
    ("kJ", r"kJ"),
    ("mL/L", r"m[lL]|(?<![a-zA-Z])[lL](?![a-zA-Z])"),
    ("百分号 %", r"%"),
    ("中文克/毫克", r"克|毫克|千卡|毫升"),
]

# (首选写法, 首选正则, 变体写法, 变体正则)
TERM_PAIRS = [
    ("碳水化合物", r"碳水化合物", "糖类", r"糖类"),
    ("脂肪", r"脂肪", "脂类", r"脂类"),
    ("能量", r"能量", "热量", r"热量"),
    ("蛋白质", r"蛋白质", "蛋白（单用）", r"蛋白(?!质)"),
    ("维生素 D", r"维生素\s*D", "维生素D（无空格）", r"维生素D"),
    ("血糖生成指数", r"血糖生成指数", "升糖指数", r"升糖指数"),
    ("身体活动", r"身体活动", "体力活动", r"体力活动"),
]

RANGE_DASH = [("～", r"(?<=\d)\s*～\s*(?=\d)"), ("~", r"(?<=\d)\s*~\s*(?=\d)"),
              ("—", r"(?<=\d)\s*—\s*(?=\d)"), ("-", r"(?<=\d)-(?=\d)"),
              ("至／到", r"(?<=\d)\s*(?:至|到)\s*(?=\d)")]


# ---------------------------------------------------------------- 指标

def metric_sentences(segs):
    lens = []
    for _, body in segs:
        for s in sentences(body):
            lens.append(nchars(s))
    if not lens:
        return {}
    buckets = [(0, 15), (16, 25), (26, 35), (36, 45), (46, 60), (61, 10**6)]
    hist = Counter()
    for L in lens:
        for lo, hi in buckets:
            if lo <= L <= hi:
                hist[f"{lo}–{hi if hi < 10**6 else '+'}"] += 1
                break
    return {
        "n_sentences": len(lens),
        "mean": round(statistics.mean(lens), 1),
        "median": statistics.median(lens),
        "p10": sorted(lens)[int(len(lens) * 0.1)],
        "p90": sorted(lens)[min(len(lens) - 1, int(len(lens) * 0.9))],
        "hist": {k: v for k, v in hist.items()},
    }


def metric_connectors(segs):
    text = "\n".join(b for _, b in segs)
    total = nchars(text)
    strong = Counter()
    logic = Counter()
    for w in STRONG_CONN:
        c = text.count(w)
        if c:
            strong[w] = c
    for w in LOGIC_CONN:
        c = text.count(w)
        if c:
            logic[w] = c
    s_sum, l_sum = sum(strong.values()), sum(logic.values())
    return {
        "chars": total,
        "strong_total": s_sum,
        "strong_per_k": round(s_sum / max(total, 1) * 1000, 2),
        "logic_total": l_sum,
        "logic_per_k": round(l_sum / max(total, 1) * 1000, 2),
        "all_per_k": round((s_sum + l_sum) / max(total, 1) * 1000, 2),
        "strong_top": strong.most_common(10),
        "logic_top": logic.most_common(10),
    }


def metric_para_sentences(segs):
    counts = [len(sentences(b)) for _, b in segs]
    lens = [nchars(b) for _, b in segs]
    if not counts:
        return {}
    return {
        "n_paras": len(counts),
        "mean_sent": round(statistics.mean(counts), 1),
        "median_sent": statistics.median(counts),
        "mean_chars": round(statistics.mean(lens), 1),
        "median_chars": statistics.median(lens),
        "over_400": sum(1 for L in lens if L > 400),
    }


def metric_first_person(segs):
    text = "\n".join(b for _, b in segs)
    total = nchars(text)
    we = len(re.findall(r"(?<!我)(我们|咱们)", text))
    wo = len(re.findall(r"我国", text))
    me = len(re.findall(r"本人|笔者", text))
    return {
        "chars": total,
        "我们/咱们": we,
        "我国(机构自称)": wo,
        "本人/笔者": me,
        "我们_per_100k": round(we / max(total, 1) * 100000, 1),
        "share_paras_with_我们": round(
            sum(1 for _, b in segs if re.search(r"(?<!我)(我们|咱们)", b)) / max(len(segs), 1) * 100, 1
        ),
    }


def metric_numbers(segs):
    text = "\n".join(b for _, b in segs)
    total = nchars(text)
    units = {}
    for name, pat in UNIT_PATTERNS:
        units[name] = len(re.findall(pat, text))
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    spaced = len(re.findall(r"\d\s+(?:g|mg|kg|kcal|kJ|ml|mL|L)(?![a-zA-Z])", text))
    attached = len(re.findall(r"\d(?:g|mg|kg|kcal|kJ|ml|mL|L)(?![a-zA-Z])", text))
    dashes = {name: len(re.findall(pat, text)) for name, pat in RANGE_DASH}
    pct = {"%": text.count("%"), "％": text.count("％")}
    gkg = units["g/kg/d"] + units["g/kg"]
    gkg_dot = units["g·kg⁻¹"]
    return {
        "chars": total,
        "numbers": len(nums),
        "numbers_per_k": round(len(nums) / max(total, 1) * 1000, 1),
        "units": units,
        "num_unit_attached": attached,
        "num_unit_spaced": spaced,
        "dashes": dashes,
        "percent": pct,
        "gkg_vs_dot": {"g/kg": gkg, "g·kg⁻¹": gkg_dot},
        "mixed_units_in_same_source": None,  # 由 by_source 计算
    }


def metric_terms(segs):
    text = "\n".join(b for _, b in segs)
    rows = []
    for a, ra, b, rb in TERM_PAIRS:
        ca, cb = len(re.findall(ra, text)), len(re.findall(rb, text))
        rows.append({"preferred": a, "variant": b, "preferred_n": ca, "variant_n": cb,
                     "variant_share": round(cb / max(ca + cb, 1) * 100, 1)})
    return rows


def metric_evidence(segs):
    pos = Counter()
    with_ev = 0
    for _, body in segs:
        m = EVIDENCE_RE.search(body)
        if not m:
            continue
        with_ev += 1
        r = m.start() / max(len(body), 1)
        pos["前1/3" if r < 0.34 else "中1/3" if r < 0.67 else "后1/3"] += 1
    return {
        "n_paras": len(segs),
        "with_evidence": with_ev,
        "share_with_evidence": round(with_ev / max(len(segs), 1) * 100, 1),
        "position": dict(pos),
    }


def metric_para_open(segs):
    hits = Counter()
    n = 0
    for _, body in segs:
        head = body[:6]
        n += 1
        for w in ALL_CONN:
            if head.startswith(w):
                hits[w] += 1
                break
    return {
        "n_paras": n,
        "open_with_connector": sum(hits.values()),
        "share": round(sum(hits.values()) / max(n, 1) * 100, 1),
        "top": hits.most_common(8),
    }


# ---------------------------------------------------------------- 渲染

def render(segs, name="corpus"):
    s1 = metric_sentences(segs)
    s2 = metric_connectors(segs)
    s3 = metric_para_sentences(segs)
    s4 = metric_first_person(segs)
    s5 = metric_numbers(segs)
    s6 = metric_terms(segs)
    s7 = metric_evidence(segs)
    s8 = metric_para_open(segs)
    out = []
    a = out.append
    a(f"# 基线统计：{name}\n")
    a(f"- 段落数：{s3.get('n_paras')}")
    a(f"- 字数：{s2['chars']}")
    a(f"- 句数：{s1.get('n_sentences')}\n")

    a("## 1 平均句长与分布\n")
    a(f"均值 {s1.get('mean')} 字，中位数 {s1.get('median')}，P10 {s1.get('p10')}，P90 {s1.get('p90')}\n")
    a("| 句长区间 | 句数 | 占比 |")
    a("|---|---:|---:|")
    for k, v in s1.get("hist", {}).items():
        a(f"| {k} | {v} | {v/max(s1['n_sentences'],1)*100:.1f}% |")
    a("")

    a("## 2 连接词频率（每千字）\n")
    a(f"强路标 {s2['strong_total']} 次 / {s2['strong_per_k']} 每千字；"
      f"逻辑连接 {s2['logic_total']} 次 / {s2['logic_per_k']} 每千字；合计 {s2['all_per_k']}\n")
    a("| 强路标 | 次 |  | 逻辑连接 | 次 |")
    a("|---|---:|---|---|---:|")
    for i in range(max(len(s2["strong_top"]), len(s2["logic_top"]))):
        l = s2["strong_top"][i] if i < len(s2["strong_top"]) else ("", "")
        r = s2["logic_top"][i] if i < len(s2["logic_top"]) else ("", "")
        a(f"| {l[0]} | {l[1]} |  | {r[0]} | {r[1]} |")
    a("")

    a("## 3 每段句数\n")
    a(f"均值 {s3.get('mean_sent')} 句，中位数 {s3.get('median_sent')}；"
      f"段均 {s3.get('mean_chars')} 字，中位数 {s3.get('median_chars')} 字；"
      f"超过 400 字的段 {s3.get('over_400')} 个\n")

    a("## 4 第一人称\n")
    a(f"「我们/咱们」{s4['我们/咱们']} 次（{s4['我们_per_100k']} / 10 万字），"
      f"出现该词的段落占 {s4['share_paras_with_我们']}%；"
      f"「我国」{s4['我国(机构自称)']} 次；「本人/笔者」{s4['本人/笔者']} 次\n")

    a("## 5 数字与单位写法\n")
    a(f"数字 {s5['numbers']} 个（{s5['numbers_per_k']} 每千字）；"
      f"数单位紧连 {s5['num_unit_attached']} 处，空格分隔 {s5['num_unit_spaced']} 处\n")
    a("| 单位 | 次 |")
    a("|---|---:|")
    for k, v in s5["units"].items():
        if v:
            a(f"| {k} | {v} |")
    a("")
    a(f"区间符号：" + "，".join(f"{k} {v}" for k, v in s5["dashes"].items() if v))
    a(f"百分号：% {s5['percent']['%']}，％ {s5['percent']['％']}\n")

    a("## 6 术语写法\n")
    a("| 首选 | 次数 | 变体 | 次数 | 变体占比 |")
    a("|---|---:|---|---:|---:|")
    for r in s6:
        a(f"| {r['preferred']} | {r['preferred_n']} | {r['variant']} | {r['variant_n']} | {r['variant_share']}% |")
    a("")

    a("## 7 论断与依据的相对位置\n")
    a(f"带依据标记的段落 {s7['with_evidence']}/{s7['n_paras']}（{s7['share_with_evidence']}%）；"
      f"首个依据标记的位置：" + "，".join(f"{k} {v}" for k, v in s7["position"].items()))
    a("")

    a("## 8 段落是否用连接词起句\n")
    a(f"{s8['open_with_connector']}/{s8['n_paras']} 段（{s8['share']}%）以连接词起句；"
      + "，".join(f"{k} {v}" for k, v in s8["top"]))
    return "\n".join(out), {"1_sentences": s1, "2_connectors": s2, "3_paras": s3,
                            "4_first_person": s4, "5_numbers": s5, "6_terms": s6,
                            "7_evidence": s7, "8_para_open": s8}


def by_source(segs):
    groups = defaultdict(list)
    for meta, body in segs:
        groups[meta.get("source", meta.get("_file", "?").split("/")[0])].append((meta, body))
    rows = []
    for name, g in sorted(groups.items()):
        text = "\n".join(b for _, b in g)
        rows.append({
            "source": name,
            "paras": len(g),
            "chars": nchars(text),
            "mean_sent": round(statistics.mean([nchars(s) for _, b in g for s in sentences(b)] or [0]), 1),
            "conn_per_k": round(sum(text.count(w) for w in ALL_CONN) / max(nchars(text), 1) * 1000, 2),
            "evid_share": metric_evidence(g)["share_with_evidence"],
            "open_share": metric_para_open(g)["share"],
            "gkg": len(re.findall(UNIT_PATTERNS[1][1], text)),
            "gkg_dot": len(re.findall(UNIT_PATTERNS[2][1], text)),
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--by-source", action="store_true")
    ap.add_argument("--compare", help="对照目录（如 AI 负样本）")
    args = ap.parse_args()

    segs = read_segments(Path(args.path))
    if not segs:
        print("没有可统计的段落", file=sys.stderr)
        sys.exit(2)

    md, data = render(segs, args.path)
    if args.compare:
        neg = read_segments(Path(args.compare))
        md_n, data_n = render(neg, f"{args.compare}（对照）")
        md = md + "\n\n---\n\n" + md_n
        data = {"gold": data, "neg": data_n}
    if args.by_source:
        rows = by_source(segs)
        md += "\n\n## 分来源\n\n| 来源 | 段 | 字 | 均句长 | 连接词/千字 | 带依据% | 连接词起句% | g/kg | g·kg⁻¹ |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        for r in rows:
            md += (f"| {r['source']} | {r['paras']} | {r['chars']} | {r['mean_sent']} | "
                   f"{r['conn_per_k']} | {r['evid_share']} | {r['open_share']} | {r['gkg']} | {r['gkg_dot']} |\n")
        data["by_source"] = rows

    print(json.dumps(data, ensure_ascii=False, indent=1) if args.json else md)


if __name__ == "__main__":
    main()
