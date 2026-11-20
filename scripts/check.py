#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运动营养中文写作品控（v1.0）。零依赖，只报告，不改文件。

用法：
    python3 scripts/check.py 文稿.md
    python3 scripts/check.py 文稿.md --json
    python3 scripts/check.py 文稿.md --explain     # 每条规则附基线证据
    python3 scripts/check.py 文稿.md --threshold 3 # 每千字允许命中数

规则从语料基线来：每条都有“机构文本实测频率”作依据，写在 references/baseline.md。
退出码 1 表示超过阈值。
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 规则表
# (家族, 编号, 名称, 正则, 改法, 基线依据)
RULES = [
    # L 口语降维：机构文本里为零，出现即改
    ("L", "L1", "汉字数字＋计量单位",
     r"(?<![每数若])[一二三四五六七八九十百千两]+(克|毫克|微克|纳克|千卡|毫升|公升|国际单位)"
     r"|[一二三四五六七八九十百]+(到|至)[一二三四五六七八九十百]+(克|毫克|千卡|毫升)",
     "改为阿拉伯数字＋单位：300 mg、5 g/kg/d",
     "机构文本 0 处 / 千字；大模型科普体 2.0 处 / 千字、汉字数字区间 1.2 处 / 千字（GB/T 15835：计量用阿拉伯数字）"),
    ("L", "L2", "第二人称与祈使",
     r"(?<!我)(你|您)(?!们)|别(把|让|忘|指|想|盯|只|在|一|再)",
     "改第三人称陈述：应…、宜…、需…",
     "机构文本 0 处 / 2.5 万字；大模型科普体 0.18 处 / 千字"),
    ("L", "L3", "口语化形容",
     r"(靠谱|划算|省事|扛饿|硬扛|神化|带偏|打折|翻车|踩坑|掉链子|一口气|天花板|拉满|底线)",
     "换书面表述：有效、成本低、依从性差、证据不足",
     "机构文本 0 处 / 千字；大模型科普体 1.5 处 / 千字"),
    ("L", "L4", "比喻实体词",
     r"(钥匙|账本|口粮|弹药|土壤|开关|放大器|垫子|帮手|燃料|武器|拼图|剧本|红灯|主场|保单)",
     "教材体不做比喻；直接写机制或作用位点",
     "机构文本 0 处 / 千字；大模型科普体 1.1 处 / 千字"),
    ("L", "L5", "像／好比／相当于",
     r"(就像是|像是|好比|似乎像|如同|犹如)",
     "删比喻关系，改为定量或机制陈述",
     "机构文本 0.03 处 / 千字；大模型科普体 0.15 处 / 千字"),
    ("L", "L6", "不是X而是Y／并非",
     r"不是[^。]{0,30}而是|并非",
     "改正面直述：写清是什么，不写不是什么",
     "机构文本 0 处 / 千字；大模型文本 0.3 处 / 千字"),
    ("L", "L7", "更X收尾",
     r"更(重要|有效|实际|稳妥|划算|可靠|合理)(?=的|，|。)",
     "删评价性比较，写可验证的差异",
     "机构文本 0 处 / 千字；大模型科普体 1.1 处 / 千字（38% 段落出现）"),

    # T 模板化：机构文本也有，但密度低；按每千字阈值判
    ("T", "T1", "模板机制句",
     r"(其机制在于|其依据在于|其核心在于|作用机制在于|机制上，|其原理在于)",
     "删“其机制在于”，直接写机制本身；一句一个论断",
     "机构文本 0.03 处 / 千字；大模型教材体 1.07 处 / 千字（35 倍）"),
    ("T", "T2", "而非",
     r"而非",
     "改“而不是”或正面陈述；一篇超过 2 次即模板腔",
     "机构文本 0 处 / 千字；大模型教材体 0.95 处 / 千字（31% 段落）"),
    ("T", "T3", "“亦”",
     r"亦(?=[\u4e00-\u9fff])",
     "改“也”或删；“亦”是文言残留，教材正文少用",
     "机构文本 1 处 / 7.1 万字；大模型教材体 0.36 处 / 千字（12% 段落）"),
    ("T", "T4", "宜采用／可采用",
     r"(宜|可)采用",
     "改为具体条件句：当…时，用…",
     "机构文本 0.03 处 / 千字；大模型教材体 0.48 处 / 千字（15% 段落）"),
]

# 密度型规则：段落内超过阈值才计命中（阈值来自机构文本 P90）
DENSITY_RULES = []  # 暂无密度型规则：阈值扫描后“可＋动词”净贡献为零，已删（见 references/rule-audit.md）

# 术语体例（文档级）
TERM_PAIRS = [
    ("碳水化合物", "糖类", "分类层级用碳水化合物；糖指单糖与双糖"),
    ("脂肪", "脂类", "分类语境用脂类，具体物质用脂肪"),
    ("能量", "热量", "正文统一用能量；热量只在引文里保留"),
    ("甘油三酯", "三酰甘油", "同义术语（triacylglycerol）：教材与标准用甘油三酯，三酰甘油是化学同义名；同一文稿择一"),
    ("瘦体重", "去脂体重", "同义术语（lean body mass / fat-free mass）：体重管理指导原则用瘦体重，营养学教材亦用去脂体重；同一文稿择一"),
    ("血糖生成指数", "升糖指数", "GB/T 21922 术语为血糖生成指数（GI）"),
    ("身体活动", "体力活动", "统一为身体活动"),
    ("必需氨基酸", "必要氨基酸", "统一为必需氨基酸"),
]

UNIT_PAIRS = [
    ("g/kg", r"g\s*/\s*kg(?!\s*/)", "g·kg⁻¹", r"g\s*[·・]\s*kg", "相对剂量统一一种写法，建议 g/kg/d"),
    ("kcal", r"kcal", "千焦", r"(千焦|kJ)", "能量单位统一 kcal 或 kJ，并在首现给出换算"),
    ("%", r"%", "％", r"％", "百分号统一半角 %"),
    ("～", r"～", "~", r"~", "数值区间统一用 ～"),
]

# 教材体首现给英文（提示，不计分）
GLOSS_TERMS = [
    ("血糖生成指数", "glycemic index"), ("能量可用性", "energy availability"),
    ("相对能量缺乏", "relative energy deficiency"), ("肌肉蛋白合成", "muscle protein synthesis"),
    ("最大摄氧量", "maximal oxygen uptake"), ("支链氨基酸", "branched-chain amino acid"),
    ("必需氨基酸", "essential amino acid"), ("热适应", "heat acclimation"),
    ("渗透压", "osmolality"), ("膳食纤维", "dietary fiber"),
]


# ---------------------------------------------------------------- 术语表
TERMS_PATH = Path(__file__).resolve().parent.parent / "references" / "terms.json"


def load_terms(path=TERMS_PATH):
    """读术语表。文件缺失时返回空表，检查器仍可运行。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], {}
    terms = data.get("terms", [])
    extra = {"preferred": data.get("preferred", []),
             "abbreviations": data.get("abbreviations", []),
             "units": data.get("units", [])}
    rules = []
    for t in terms:
        for w in t.get("wrong", []):
            rules.append({"term": t["term"], "pattern": w["pattern"], "hint": w["hint"],
                          "definition": t.get("definition", ""), "source": t.get("source", "")})
    return terms, rules, extra


TERMS, TERM_RULES, EXTRA = load_terms()
PREFERRED_TERMS = [(x["variant"], x["canonical"], x["evidence"]) for x in EXTRA["preferred"]]
ABBREVIATIONS = [(x["abbr"], x["cn"]) for x in EXTRA["abbreviations"]]
UNIT_WORDS = [(x["word"], x["to"]) for x in EXTRA["units"]]


def definition_notes(body: str):
    """定义句核对：正文写「X 是指/定义为」时，和标准定义比对数值。

    数值型定义（超重、高血压、中心型肥胖等）能判「写错/漏写」；
    非数值定义只把标准原文摆出来，供人比对。
    """
    issues, notes = [], []
    for t in TERMS:
        if not t.get("definition"):
            continue
        pat = re.escape(t["term"]) + r"[^。]{0,8}(是指|指的是|定义为|系指|称为)([^。]{0,90})"
        for m in re.finditer(pat, body):
            sent = m.group(0)
            std_nums = re.findall(r"\d+(?:\.\d+)?", t["definition"])
            body_nums = re.findall(r"\d+(?:\.\d+)?", sent)
            if std_nums and not set(std_nums) <= set(body_nums):
                issues.append({"group": "K", "id": "K3", "rule": f"定义与标准不一致：{t['term']}",
                               "count": 1, "samples": [sent[:60]],
                               "hint": f"标准定义（{t['source']}）：{t['definition']}",
                               "evidence": "定义句里的数值必须与标准一致；缺号或多号都要核对"})
            else:
                notes.append(f"「{t['term']}」定义句待核；{t['source']}：{t['definition']}")
    return issues, notes



# ---------------------------------------------------------------- 语体档
# 分档数字来自 references/corpus：指南体 = 膳食指南 2022 + 11 份食养指南（81 段）；
# 教材体 = 中国营养科学全书上/下 + DRIs（60 段）。
# 复算：python3 scripts/stats.py references/corpus --by-source
CONNECTIVES = [
    "此外", "同时", "另外", "值得注意", "需要指出", "必须指出", "应当指出",
    "首先", "其次", "再次", "最后", "综上所述", "总而言之", "总之",
    "由此可见", "一方面", "另一方面", "换言之", "也就是说", "具体而言",
    "一般来说", "总体而言", "事实上", "实际上",
    "因此", "因而", "所以", "由于", "因为", "但是", "然而", "不过",
    "如果", "即使", "虽然", "尽管", "随着", "例如", "比如", "其中",
]

PROFILES = {
    "guideline": {"label": "膳食指南体", "n": 81, "sent_med": 41, "sent_p10": 17,
                  "sent_p90": 80, "conn": 2.85, "ying": 4.24, "nums": 31.2},
    "textbook": {"label": "教材体", "n": 60, "sent_med": 49, "sent_p10": 22,
                 "sent_p90": 110, "conn": 3.86, "ying": 2.56, "nums": 44.2},
}
DEFAULT_PROFILE = "guideline"


def doc_style(body: str) -> dict:
    """文档层面的语体指标，用来和所选档位对照。"""
    import statistics
    sents = [nchars(x) for x in re.split(r"(?<=[。！？])", body) if nchars(x) > 1]
    chars = max(nchars(body), 1)
    text = body
    conn = sum(text.count(w) for w in CONNECTIVES)
    ying = len(re.findall(r"(应|宜)(?=[\u4e00-\u9fff])", text))
    nums = len(re.findall(r"\d", text))
    return {
        "sent_med": round(statistics.median(sents), 1) if sents else 0,
        "conn": round(conn / chars * 1000, 2),
        "ying": round(ying / chars * 1000, 2),
        "nums": round(nums / chars * 1000, 1),
    }


def nchars(s: str) -> int:
    return len(re.sub(r"\s", "", s))



def mask_markdown(text: str) -> str:
    """把代码块、行内代码、URL、HTML 标签替换成等长空白，保留换行与段落结构。

    这些位置不该按散文检查：代码里的「维他命」是变量名，URL 里的数字不是剂量。
    """
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))

    text = re.sub(r"^```.*?^```", blank, text, flags=re.S | re.M)
    text = re.sub(r"^~~~.*?^~~~", blank, text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]*`", blank, text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", blank, text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) + " " * (len(m.group(0)) - len(m.group(1))), text)
    text = re.sub(r"https?://\S+", blank, text)
    text = re.sub(r"<[^>\n]+>", blank, text)
    return text

def strip_front_matter(text: str) -> str:
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.S)


def paragraphs(text: str):
    text = re.sub(r"^\s*#+.*$", "", text, flags=re.M)
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# ---------------------------------------------------------------- 检查

def rule_hits(body: str):
    """逐条规则计数。"""
    out = []
    for group, rid, name, pattern, hint, evidence in RULES:
        ms = list(re.finditer(pattern, body))
        if ms:
            out.append({"group": group, "id": rid, "rule": name, "count": len(ms),
                        "samples": [m.group(0)[:16] for m in ms[:3]],
                        "hint": hint, "evidence": evidence})
    for rid, name, pattern, limit, hint, evidence in DENSITY_RULES:
        excess_total = 0
        samples = []
        for p in paragraphs(body):
            n = nchars(p)
            ms = list(re.finditer(pattern, p))
            allowed = int(limit * n / 1000)
            if len(ms) > allowed:
                excess_total += len(ms) - allowed
                samples += [m.group(0)[:16] for m in ms[:2]]
        if excess_total:
            out.append({"group": "T", "id": rid, "rule": name, "count": excess_total,
                        "samples": samples[:3], "hint": hint, "evidence": evidence})
    by_term = {}
    for r in TERM_RULES:
        for m in re.finditer(r["pattern"], body):
            e = by_term.setdefault(r["term"], {"count": 0, "samples": [], "hint": r["hint"],
                                              "source": r["source"]})
            e["count"] += 1
            if len(e["samples"]) < 3:
                e["samples"].append(m.group(0)[:16])
    for term, e in by_term.items():
        out.append({"group": "K", "id": "K1", "rule": f"术语误写：{term}", "count": e["count"],
                    "samples": e["samples"], "hint": e["hint"],
                    "evidence": f"{e['source']}" if e["source"] else "术语表 references/terms.json"})
    return out


def structural_checks(text: str):
    """结构检查。返回 (issues, 段落统计)。"""
    issues = []
    paras = paragraphs(text)
    tails = 0
    for p in paras:
        sents = [s for s in re.split(r"(?<=[。！？])", p) if s.strip()]
        if len(sents) < 3:
            continue
        last = sents[-1].strip()
        # 阈值来自语料：机构文本段末以“这/因此”起句且 ≤30 字者 1/81 段，
        # 大模型负样本 0/50 段 —— 分离度不足，降为提示，不计分。
        if len(last) <= 30 and re.match(r"^(这|因此|可见|说明|总之)", last):
            tails += 1
    if tails:
        issues.append(("P", "P1", "段末总结句（提示）", tails,
                       "看是否只是复述；机构文本偶有，不强制删"))
    ranges = len(re.findall(r"\d+\s*(?:至|到)\s*\d+", text))
    if ranges:
        issues.append(("C", "C1", "数值区间用“至”", ranges,
                       "统一为 ～：3～6 mg/kg。GB/T 15835：数值范围用浪纹线"))

    dash = 0
    for line in text.splitlines():
        if re.search(r"DOI|et al|^\s*\[\d+\]|\[J\]|\[M\]|\[R\]", line):
            continue
        for m in re.finditer(r"(?<![\d.])(\d+(?:\.\d+)?%?)\s*[—–]\s*(\d+(?:\.\d+)?%?)", line):
            a, b = m.group(1).rstrip("%"), m.group(2).rstrip("%")
            if re.fullmatch(r"(19|20)\d{2}", a) and re.fullmatch(r"(19|20)\d{2}", b):
                continue
            dash += 1
    if dash:
        issues.append(("C", "C2", "数值区间用破折号", dash,
                       "统一为 ～：5%～10%、7～9 小时。年份区间（2020—2023）保留破折号"))

    opens = sum(1 for p in paras
                if re.match(r"^(此外|同时|另外|因此|首先|其次|最后|然而|但是|总之|综上)", p))
    return issues, {"paragraphs": len(paras),
                    "open_with_connector": opens,
                    "open_share": round(opens / max(len(paras), 1) * 100, 1)}


def doc_checks(text: str):
    """文档级体例检查：单位、术语、首现英文、首选术语、缩写。返回 (issues, notes)"""
    issues, notes = [], []

    for variant, canonical, why in PREFERRED_TERMS:
        c = text.count(variant)
        if c:
            issues.append({"group": "K", "id": "K2", "rule": f"首选术语：{variant} → {canonical}",
                           "count": c, "samples": [f"{variant}×{c}"],
                           "hint": f"改用「{canonical}」；同一文稿必须统一", "evidence": why})

    used = [(w, u, len(re.findall(r"(?<![毫微千分])" + w, text))) for w, u in UNIT_WORDS]
    used = [(w, u, c) for w, u, c in used if c]
    if used:
        issues.append({"group": "S", "id": "S5", "rule": "汉字计量单位",
                       "count": sum(c for _, _, c in used),
                       "samples": [f"{w}×{c}→{u}" for w, u, c in used],
                       "hint": "改用国际单位：kg / g / kcal / mL",
                       "evidence": "《成人肥胖食养指南（2024年版）》公斤 0 次、kg 23 次；千卡 0 次、kcal 189 次"})

    for abbr, cn in ABBREVIATIONS:
        first = re.search(r"(?<![A-Za-z])" + re.escape(abbr) + r"(?![A-Za-z])", text)
        if not first:
            continue
        window = text[max(0, first.start() - 40): first.start()]
        if cn in window or f"（{abbr}" in text[first.start(): first.start() + 20]:
            continue
        issues.append({"group": "S", "id": "S4", "rule": f"缩写首现未展开：{abbr}",
                       "count": 1, "samples": [abbr],
                       "hint": f"首次出现写「{cn}（{abbr}）」，后文再用缩写",
                       "evidence": "机构文本首现给中文全称；《成人肥胖食养指南》用「内脏脂肪面积（VFA）」格式"})
    for a, pa, b, pb, hint in UNIT_PAIRS:
        ca, cb = len(re.findall(pa, text)), len(re.findall(pb, text))
        if ca and cb:
            issues.append({"group": "S", "id": "S1", "rule": f"单位体例混用：{a} / {b}",
                           "count": 1, "samples": [f"{a}×{ca}", f"{b}×{cb}"],
                           "hint": hint, "evidence": "同一文稿内两种写法并存即不一致"})
    for a, b, hint in TERM_PAIRS:
        ca, cb = text.count(a), text.count(b)
        if ca and cb:
            issues.append({"group": "S", "id": "S2", "rule": f"术语混用：{a} / {b}",
                           "count": 1, "samples": [f"{a}×{ca}", f"{b}×{cb}"],
                           "hint": hint, "evidence": "GB 28050—2025 §2 术语与 DRIs 2023 用语（术语标准原文未入库）"})
    if len(text) > 1500:
        gloss = re.findall(r"[\u4e00-\u9fff]{2,12}（[A-Za-z][^）]{2,40}）", text)
        if not gloss:
            notes.append("全文无“中文（English）”夹注：教材体首现给英文，指南体可免")
        else:
            for cn, en in GLOSS_TERMS:
                if cn in text and en.split()[0] not in text:
                    notes.append(f"“{cn}”未给英文（{en}）")
                    break
    return issues, notes


def analyze(text: str) -> dict:
    body = strip_front_matter(text)
    body = mask_markdown(body)
    chars = nchars(body)
    items = rule_hits(body)
    struct, para_stats = structural_checks(body)
    for group, rid, name, count, hint in struct:
        items.append({"group": group, "id": rid, "rule": name, "count": count,
                      "samples": [], "hint": hint,
                      "evidence": "机构语料段末总结句 0 处 / 8.8 万字；段长 P95 ≈ 650 字"})
    doc_issues, notes = doc_checks(body)
    def_issues, def_notes = definition_notes(body)
    doc_issues += def_issues
    notes = def_notes + notes
    counted = [i for i in items if i["group"] in "LTKC"]
    total = sum(i["count"] for i in counted)
    return {"chars": chars, "total": total,
            "per_kchar": round(total / max(chars, 1) * 1000, 1),
            "items": items, "doc_issues": doc_issues, "notes": notes,
            "paragraphs": para_stats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--threshold", type=float, default=3.0, help="每千字允许命中数")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--explain", action="store_true", help="附基线证据")
    ap.add_argument("--profile", choices=sorted(PROFILES), default=DEFAULT_PROFILE,
                    help="语体档：guideline（默认，膳食指南体）或 textbook（教材体）")
    ap.add_argument("--diff", action="store_true", help="按上下文展示命中，而不是只报计数")
    ap.add_argument("--terms", action="store_true", help="只报术语类：K1/K2 术语、S4 缩写、S5 单位")
    args = ap.parse_args()

    path = Path(args.file)
    res = analyze(path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps({"file": str(path), **res}, ensure_ascii=False, indent=1))
        sys.exit(1 if res["per_kchar"] > args.threshold else 0)

    if args.terms:
        keep = [i for i in res["items"] + res["doc_issues"] if i["id"] in ("K1", "K2", "K3", "S4", "S5")]
        if not keep:
            print(f"术语层未发现问题（{res['chars']} 字）")
            sys.exit(0)
        print(f"术语层命中 {len(keep)} 类 / {sum(i['count'] for i in keep)} 处（{res['chars']} 字）")
        for i in keep:
            print(f"  [{i['id']}] {i['rule']} ×{i['count']}  {'、'.join(i['samples'][:4])}")
            print(f"        → {i['hint']}")
            if args.explain:
                print(f"        依据：{i['evidence']}")
        sys.exit(1)

    prof = PROFILES[args.profile]
    st = doc_style(strip_front_matter(mask_markdown(path.read_text(encoding="utf-8"))))
    print(f"语体档：{prof['label']}（{prof['n']} 段基线）")
    print(f"  句长中位 {st['sent_med']} 字（基线 {prof['sent_p10']}–{prof['sent_p90']}，中位 {prof['sent_med']}）")
    print(f"  连接词 {st['conn']}/千字（基线 {prof['conn']}）")
    print(f"  应/宜 {st['ying']}/千字（基线 {prof['ying']}）")
    print(f"  数字 {st['nums']}/千字（基线 {prof['nums']}）\n")

    print(f"命中 {res['total']} 处 / {res['chars']} 字（{res['per_kchar']} 处每千字）")
    names = {"L": "口语降维", "T": "模板化", "C": "结构", "K": "术语", "S": "体例", "P": "提示"}
    for g in "LTKCP":
        rs = [i for i in res["items"] if i["group"] == g]
        if not rs:
            continue
        print(f"{g} {names[g]} " + "；".join(f"{i['rule']}×{i['count']}" for i in rs))
    if res["doc_issues"]:
        print("S 体例 " + "；".join(f"{i['rule']}" for i in res["doc_issues"]))
    if args.diff:
        body = strip_front_matter(path.read_text(encoding="utf-8"))
        masked = mask_markdown(body)
        print()
        for group, rid, name, pattern, hint, evidence in RULES:
            for m in re.finditer(pattern, masked):
                a, b = max(0, m.start() - 24), min(len(body), m.end() + 24)
                left = body[a:m.start()].replace("\n", " ")
                hit = body[m.start():m.end()]
                right = body[m.end():b].replace("\n", " ")
                print(f"  [{rid}] …{left}**{hit}**{right}…")
        for r in TERM_RULES:
            for m in re.finditer(r["pattern"], masked):
                a, b = max(0, m.start() - 24), min(len(body), m.end() + 24)
                left = body[a:m.start()].replace("\n", " ")
                hit = body[m.start():m.end()]
                right = body[m.end():b].replace("\n", " ")
                print(f"  [K1] …{left}**{hit}**{right}…  → {r['hint']}")
        sys.exit(1 if res["per_kchar"] > args.threshold else 0)

    print()
    for i in res["items"] + res["doc_issues"]:
        s = "、".join(i["samples"]) if i.get("samples") else ""
        print(f"  [{i['id']}] {i['rule']} ×{i['count']}  {s}  → {i['hint']}")
        if args.explain and i.get("evidence"):
            print(f"       依据：{i['evidence']}")
    for n in res["notes"]:
        print(f"  提示：{n}")
    print(f"\n段落 {res['paragraphs']['paragraphs']} 个，"
          f"以连接词起句 {res['paragraphs']['open_with_connector']} 个"
          f"（{res['paragraphs']['open_share']}%，机构文本 7%，不作扣分项）")
    sys.exit(1 if res["per_kchar"] > args.threshold else 0)


if __name__ == "__main__":
    main()
