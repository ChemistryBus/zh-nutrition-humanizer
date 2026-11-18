# sport-nutrition-humanizer

**中文运动营养写作品控：把 AI 初稿校到中国营养学会教材与国家级食养指南的规范水平。**

不是“让文字更像人写的”，是“让文字达到机构文本的规范”。
仓库里带一份 5.3 万字的权威语料基线，每条规则的阈值都能复算。

[中文](#中文) · [English](#english)

---

## 中文

### 为什么另做一个

现有开源 humanizer 的目标语体是**自然人的写作**：去掉机器腔、允许口语、鼓励个人声音。
本项目的目标语体是**机构文本**：句式规整、术语统一、论断跟着依据走、不抒情不总结。
两者不是程度差别，是方向差别——把教材改成“像人写的”，恰好是失败。

| | 清单型 humanizer | 本项目 |
|---|---|---|
| 目标语体 | 自然人的写作 | 中国营养学会教材、国家卫健委食养指南 |
| 规则来源 | 归纳（维基“AI 写作迹象”一类清单，如 blader/humanizer、stop-slop、Aboudjem、op7418 的中文改编） | 语料统计：141 段权威原文 vs 50 段大模型初稿 |
| 阈值 | 经验设定 | 每条都有实测频率与 P90；误报率、命中密度差可复算 |
| 连接词 | 越少越好 | 机构文本 3.27 处 / 千字；删连接词这条在本语体里**是错的** |
| 数字 | 随意 | 阿拉伯数字＋单位，区间用 `～`（GB/T 15835） |
| 评测 | 主观 | 正负样本各 50 段，密度差 76×、段级误报 4%，拐点阈值可查 |

### 它测什么

四族规则，共 13 条 + 4 项体例（完整表见 `SKILL.md`）：

- **L 口语降维**（7 条）：汉字数字带单位、第二人称与祈使、口语化形容、比喻实体词、像／好比、不是X而是Y、更X收尾。
  机构文本里这些是零，出现即改。
- **T 模板化**（4 条）：其机制在于、而非、亦、宜采用。机构文本也有，但密度低，靠阈值判。
- **C 结构**（1 条）：数值区间用“至”而非“～”。
- **S 体例**（4 项，文档级）：单位混用、术语混用、首现未给英文、段末复述提示。

**不测**：事实一致性、引用真伪、证据等级与论断强度是否匹配。这三项只能人看。

### 安装

```bash
git clone https://github.com/ChemistryBus/sport-nutrition-humanizer.git
cd sport-nutrition-humanizer
python3 scripts/check.py --help 2>/dev/null || python3 scripts/check.py examples/before.md
```

零依赖，Python 3.8+ 即可，不需要 pip 安装任何包。

作为 Claude Code / DSH 技能使用：把仓库放进技能目录即可，SKILL.md 已带 frontmatter。

```bash
cp -r sport-nutrition-humanizer ~/.claude/skills/
# 或
cp -r sport-nutrition-humanizer ~/.dsh/skills/
```

### 使用

```bash
python3 scripts/check.py 稿子.md                 # 命中清单
python3 scripts/check.py 稿子.md --explain       # 每条附语料依据
python3 scripts/check.py 稿子.md --json          # 给下游
python3 scripts/check.py 稿子.md --threshold 3   # 每千字允许命中数（默认 3）
```

输出：

```
命中 6 处 / 2380 字（2.5 处每千字）
L 口语降维 汉字数字＋计量单位×2；第二人称与祈使×1
T 模板化 而非×2
S 体例 术语混用：碳水化合物 / 糖类

  [L1] 汉字数字＋计量单位 ×2  三百毫克、二十克  → 改为阿拉伯数字＋单位
       依据：机构文本 0 处 / 千字；大模型科普体 2.0 处 / 千字
```

退出码 `1` 表示超过阈值，可直接接进 CI：

```yaml
- run: python3 scripts/check.py 10_正文/*.md --threshold 3
```

工作流：机检 → 人工逐条判（改／留／补）→ 按 L→T→C→S 顺序改 → 复跑 → 回读数字与证据等级。

### 评测

```bash
python3 scripts/stats.py references/corpus                  # 八项基线统计
python3 scripts/eval.py --gold eval/gold --neg eval/neg    # 密度差、误报率、阈值扫描
python3 scripts/features.py --gold references/corpus --neg eval/neg   # 候选特征分离度
```

**主结果**（正样本 50 段 / 1.78 万字，负样本 50 段 / 1.64 万字）：

| 指标 | 结果 | 目标 |
|---|---|---|
| 命中密度差 | **76.4×**（机构 0.11 / 千字，AI 8.40 / 千字） | ≥3× |
| 段级误报率 | **4.0%**（2/50） | <15% |
| 段级召回 | **92%**（教材体 88%，科普体 96%） | — |
| 拐点阈值 | 1–2 处 / 千字（J = +0.88）；默认取 3（召回 80%，误报 2%） | — |

阈值扫描曲线、逐规则命中表、消融（去掉“数值区间”规则后密度差 51.8×）、
漏报个案分析，见 **`eval/results.md`**。原始数据在 `eval/sweep.csv` 与 `eval/blind/`。

盲评：20 组改前／改后，A/B 随机、位置均衡，两位独立评分者。结果见 `eval/results.md` §6。

### 仓库结构

```
SKILL.md                  技能主文件：定位、规则、流程、局限
README.md                 本文件（中英）
LICENSE                   MIT（代码）＋语料摘录说明
CHANGELOG.md              版本与决策记录
references/
  baseline.md             八项语料统计、提取路由、复现方法
  rule-audit.md           v0.1 的 25 条规则逐条判（删 17、并 5、留 4、待验证 2）
  ai-tells.md             改前改后对照（20 组，按规则族分组）
  corpus/                 141 段 200–400 字摘录，带出处与页码
eval/
  gold/  neg/  neg_holdout/   评测集（正 50、负 50、留出 28）
  results.md  sweep.csv       结果与阈值曲线
  blind/                      盲评包、答案键、两轮评分
examples/
  before.md  after.md     20 组真实初稿与改写
scripts/
  check.py                机检（零依赖）
  eval.py                 评测：密度差、误报率、阈值扫描
  stats.py                八项基线统计
  features.py             候选特征分离度（规则挖掘用）
.github/ISSUE_TEMPLATE/   误报 / 漏报 / 新规则建议
```

### 语料与许可

- 代码 MIT。
- `references/corpus/`、`eval/gold/` 下是从《中国营养科学全书（第 2 版）》《中国居民膳食指南（2022）》
  《DRIs（2023）》《食养指南》摘出的 200–400 字短段，**逐段标注来源、出版方、页码**，
  只用于语体统计与对照，不整本转载。原书版权归各著作权人，摘录不在 MIT 授权范围内。
- 原始 PDF 不入库。要复现抽样，需本机持有同一批文件，按 `references/baseline.md` §2.1 的窗口重跑。
- 已知缺口：GB/T 21922—2026 术语标准未能入库，术语体例这一项缺标准原文基线。

### 维护

每季度复核一次，流程写在 `CHANGELOG.md` 末尾：

1. 新增 2–3 份当年发布的指南／教材到语料，各取 6–20 段。
2. 跑 `scripts/stats.py`，比对八项指标漂移；超过 20% 的项要查原因。
3. 跑 `scripts/eval.py`，误报率涨过 10% 就窄化对应规则。
4. 有规则长期零命中 → 删；有新特征分离度 ≥3× → 进表并在 `rule-audit.md` 记账。

---

## English

**Chinese-language quality control for sports-nutrition writing: move an AI draft up to the
register of the Chinese Nutrition Society's textbooks and the national dietary-guidance (食养指南) series.**

This is not "make it sound human". The target register is *institutional Chinese*: uniform
terminology, quantities with units, claims followed by evidence, no rhetorical flourishes.
Most open-source humanizers optimize for a different objective (a natural individual voice) —
for a textbook, that is the failure mode.

### What it is calibrated on

- **Corpus baseline**: 141 excerpts (200–400 characters each) from the *Chinese Nutrition Science
  Encyclopedia* (2nd ed.), *Dietary Guidelines for Chinese Residents* (2022), *DRIs* (2023) and
  eleven national dietary-guidance documents, each with publisher and page number.
- **Evaluation**: 50 held-out authoritative paragraphs vs 50 LLM-written paragraphs
  (24 popular-science register, 26 textbook register), plus 28 held-out negatives.

### Results

| Metric | Result | Target |
|---|---|---|
| Hit-density ratio (AI vs institution) | **76.4×** (8.40 vs 0.11 per 1,000 chars) | ≥3× |
| Paragraph-level false-positive rate | **4.0%** (2/50) | <15% |
| Paragraph-level recall | **92%** (textbook 88%, popular 96%) | — |
| Knee of the threshold sweep | 1–2 hits per 1,000 chars (J = +0.88) | — |

### Install and run

```bash
git clone https://github.com/ChemistryBus/sport-nutrition-humanizer.git
cd sport-nutrition-humanizer
python3 scripts/check.py your_draft.md --explain
```

Zero dependencies. Exit code 1 when the draft exceeds 3 hits per 1,000 characters.

### Rules in one line

- **L — colloquial downgrade** (7): Chinese numerals with units, second person/imperatives,
  colloquial adjectives, metaphor nouns, "像/好比", "不是X而是Y", evaluative "更X" endings.
- **T — template phrases** (4): "其机制在于", "而非", "亦", "宜采用".
- **C — structure** (1): numeric ranges written with “至” instead of ～.
- **S — house style** (4, document-level): mixed unit conventions, mixed terminology,
  missing English gloss on first use, paragraph-tail restatement (advisory).

### Licence

Code MIT. Corpus excerpts are short quotations with attribution, not covered by the MIT grant;
copyright remains with the respective publishers.
