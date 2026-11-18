<p align="right"><a href="README.en.md"><img src="https://img.shields.io/badge/English-README-2f81f7?style=flat-square" alt="English"></a></p>

<h1 align="center">zh-nutrition-humanizer</h1>

<p align="center"><strong>中文营养写作品控</strong></p>
<p align="center">不是去 AI 味，是把稿子校到中国营养学会教材与国家级食养指南的规范。</p>
<p align="center"><strong>v1.0.1 — Repository Rename and docarbiter-style Docs</strong></p>

<p align="center">
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml"><img src="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/releases/tag/v1.0.1"><img src="https://img.shields.io/github/v/release/ChemistryBus/zh-nutrition-humanizer?color=blue&cacheSeconds=300" alt="release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.9--3.12-blue" alt="Python 3.8-3.12">
</p>

![zh-nutrition-humanizer 总览](docs/assets/overview-zh.svg)

## 它是什么

humanizer 大多在追「像人写的」。这个不是。

`zh-nutrition-humanizer` 的目标语体是**机构文本**：句式规整、术语统一、剂量带单位、论断跟着依据走、不抒情不总结。它附带一份 5.3 万字的权威语料基线，每条规则的阈值都能用仓库里的脚本复算，而不是一张凭经验写下的清单。

它主要解决四类问题：

- 大模型写营养稿，句式、数字、术语都在，但读起来像科普号；
- 「去 AI 味」的通用技巧（删连接词、拆长句、加口语）用在教材体上会**反向降分**；
- 中文没有公认的 AI 检测标准，凭感觉改，改完没人能复核；
- 语料在本地、版权不能整本转载，所以只能靠 200–400 字摘录建基线。

## 30 秒开始

### 方式一：让 agent 帮你装

把下面这段发给 Claude Code / Codex / DSH：

```text
请先问我是否允许把 zh-nutrition-humanizer 放进技能目录，得到允许后再执行：
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.claude/skills/zh-nutrition-humanizer
安装完成后运行 python3 scripts/check.py examples/before.md --explain，把命中清单给我。
不要改动我的稿子，也不要上传任何文本。
```

### 方式二：手动安装

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git
cd zh-nutrition-humanizer
python3 scripts/check.py examples/before.md --explain
```

零依赖，Python 3.9+（CI 覆盖 3.9 与 3.12），不需要 pip 装任何东西。

### 先试一次机检

```bash
python3 scripts/check.py 你的稿子.md --explain
```

没有稿子？用仓库自带的 20 组真实初稿：

```bash
python3 scripts/check.py examples/before.md     # 预期：10.4 处/千字，退出码 1
python3 scripts/check.py examples/after.md      # 预期：段落级 0 命中（说明性文字除外）
```

## 怎么判

四族规则，12 条计数 + 3 项文档级体例 + 1 项提示。阈值全部来自语料实测。

| 族 | 抓什么 | 机构文本 | 大模型初稿 | 判法 |
|---|---|---|---:|---:|---|
| L 口语降维（7 条） | 汉字数字带单位、第二人称与祈使、口语形容、比喻实体词、像是／好比、不是X而是Y、更X收尾 | 0–0.03 | 0.15–2.0 | 出现即改 |
| T 模板化（4 条） | 其机制在于、而非、亦、宜采用 | 0–0.03 | 0.36–1.07 | 超过密度才改 |
| C 结构（1 条） | 数值区间用「至」 | 0 | 4.52 | 一律改 ～ |
| S 体例（3 项） | 单位混用、术语混用、首现未给英文 | — | — | 逐条列出，不计密度 |

完整规则表见 [`SKILL.md`](SKILL.md)，每条的依据见 [`references/rule-audit.md`](references/rule-audit.md)。

## 适合 / 不适合

**适合**

- 中文营养、运动营养、食养类稿件的交付前检查；
- 书稿正文与公众号版分别过一遍（同一内容，两种语体）；
- 别人或大模型写的稿子要进项目，先过这道门。

**不适合**

- 文学性科普、短视频文案——那是另一套语体，L 族规则会大面积误伤；
- 纯英文稿（用 academic-humanizer）；
- 事实核查、引用真伪、证据等级与论断强度是否匹配——这三项必须人看，机检不碰。

## 证据，不是「AI 概率」

| 指标 | 结果 | 目标 |
|---|---|---|
| 命中密度差 | **74.5×**（机构 0.11 vs 初稿 8.40 处/千字） | ≥3× |
| 段级误报率 | **4.0%**（2/50 段权威原文被标） | <15% |
| 段级召回 | **92%**（教材体 88% / 科普体 96%） | — |
| 阈值拐点 | 1–2 处/千字（J=+0.88），默认取 3 | — |

正样本 50 段（1.78 万字，与建基线的页码不重叠）、负样本 50 段（科普体 24 / 教材体 26）。逐规则表、阈值曲线、消融、漏报分析与三轮盲评在 [`eval/results.md`](eval/results.md)。

盲评最终轮（与仓库文本逐字一致）：科普体改写 **20 胜 0 负**（4.25 vs 2.45），教材体 **16 平**（4.90 vs 4.90）——**教材体 AI 稿只能改体例，改不动语体**。这句是三轮盲评打出来的，第一轮我因为把句子压成电报句被判负 18 次。

## 支持哪些 harness

| 环境 | 用法 |
|---|---|
| 纯命令行 / CI | `python3 scripts/check.py 稿子.md --threshold 3`，退出码 1 即超阈值 |
| Claude Code | 仓库放进 `~/.claude/skills/`，读 `SKILL.md` |
| DSH / Cordis | 放进 `~/.dsh/skills/`，`SKILL.md` 已带 frontmatter |
| 自建流程 | `--json` 输出喂给下游；`scripts/eval.py` 可接入回归测试 |

## 安装选项

| 需求 | 做法 |
|---|---|
| 只想查一篇稿子 | `git clone` 后直接跑 `scripts/check.py`，不安装 |
| 当技能长期用 | 克隆到技能目录，版本用 tag 锁（`git checkout v1.0.1`） |
| 接进 CI | 把 `scripts/check.py` 拷进仓库，或 `git submodule add` |

## 常见问题

**Q：为什么不删「此外／同时」？**
机构文本 3.27 处/千字，大模型教材体 3.57，删连接词不是判别特征。要删的是「由此可见」后面那句复述。

**Q：会不会把好文字改坏？**
会。误报率 4% 就是对权威原文的实测误伤；所以机检只出清单，改不改由人判，规则里也没有一条会动数字。

**Q：能判断一段话是不是 AI 写的吗？**
不能。这里给的是「相对于本语料的偏离度」，不是 AI 概率。中文没有公认的检测基准，任何声称能判的都要看它的正负样本。

**Q：为什么语料只有 200–400 字摘录？**
版权。每段标注来源、出版方、页码，只用于统计与对照，不整本转载；原始 PDF 不入库。

**Q：能用在别的领域吗？**
规则骨架可以，阈值不行。换领域必须重建基线——`scripts/stats.py` 与 `scripts/features.py` 就是干这个的。

## 文档

| 文件 | 内容 |
|---|---|
| [`SKILL.md`](SKILL.md) | 技能主文件：定位、规则表、流程、局限 |
| [`references/baseline.md`](references/baseline.md) | 141 段语料的八项统计、提取路由、复现方法 |
| [`references/rule-audit.md`](references/rule-audit.md) | v0.1 的 25 条规则逐条判（删 17、并 5、留 4、待验证 2） |
| [`references/ai-tells.md`](references/ai-tells.md) | 按规则编号排的对照表 + 七条「什么时候不该改」 |
| [`eval/results.md`](eval/results.md) | 评测报告：密度差、误报率、阈值扫描、漏报、盲评 |
| [`examples/after.md`](examples/after.md) | 20 组真实初稿与改写，数字零改动 |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | 语料来源与版权声明 |

## 许可

代码 MIT，见 [`LICENSE`](LICENSE)。语料摘录不在 MIT 授权范围内，来源与版权见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
