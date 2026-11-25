<p align="right"><a href="README.en.md"><img src="https://img.shields.io/badge/English-README-2f81f7?style=flat-square" alt="English"></a></p>

<h1 align="center">zh-nutrition-humanizer</h1>

<p align="center"><strong>中文营养写作的润色与术语校订</strong></p>
<p align="center">对齐政策文件、学会出版物与标准的口吻 · 润色语言，校订术语 · 零依赖</p>
<p align="center"><strong>v1.15.0 — Definitions and Three-New Foods</strong></p>

<p align="center">
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml"><img src="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/releases/tag/v1.15.0"><img src="https://img.shields.io/github/v/release/ChemistryBus/zh-nutrition-humanizer?color=blue&cacheSeconds=300" alt="release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.10--3.12-blue" alt="Python 3.10-3.12">
  <img src="https://img.shields.io/badge/Agent-Skill-111111" alt="Agent Skill">
  <img src="https://img.shields.io/badge/Built%20with-DSH-2f81f7" alt="Built with DSH">
</p>

![zh-nutrition-humanizer 总览](docs/assets/overview-zh.svg)

## 它是什么

humanizer 大多在追「像人写的」。这里追的是另一件事：**中文营养界公开发布文字时的口吻**。

这个口吻不是一种抽象的风格偏好，它由三类文本具体定义：

<table width="100%">
  <thead><tr><th>类别</th><th>代表文本</th><th>它定下了什么</th></tr></thead>
  <tbody>
    <tr><td>国家营养政策文件</td><td>《国民营养计划（2017—2030 年）》、健康中国行动、国家卫生健康委员会食养指南系列（11 份，2023–2026）</td><td>「建议、应、宜、不宜」的用法；面向人群而非面向读者个人</td></tr>
    <tr><td>中国营养学会出版物</td><td>《中国营养科学全书（第 2 版）》、《中国居民膳食指南（2022）》、《中国居民膳食营养素参考摄入量（DRIs，2023）》</td><td>术语层级、定义写法、剂量单位、论断与依据的相对位置</td></tr>
    <tr><td>国家 / 行业 / 地方标准</td><td>GB 24154、GB 28050、GB 7718、WS/T 系列、GB/T 21922—2026 术语标准、地方食养与配餐规范</td><td>量的写法、单位体例、术语与分类边界</td></tr>
    <tr><td colspan="3" width="1200">三类文本并列而非替代：政策文件定口吻，学会出版物定术语与定义，标准定量与单位的写法。</td></tr>
  </tbody>
</table>

本仓库做的，是把这三类文本拆成可测的指标——术语层级、剂量写法、句式长度、依据位置——再用 **141 段、5.3 万字**的语料校准阈值。所以「像不像」不是谁说了算，而是能落到「每千字几次」上。

它主要解决四类问题：

- 大模型写营养稿，事实与数字都对，但口吻不对：像科普号，不像公开发布的文件；
- 「去 AI 味」的通用技巧（删连接词、拆长句、加口语）用在机构文本上会**反向降分**；
- 中文没有公认的 AI 检测标准，凭感觉改，改完没法复核；
- 语料在本地、版权不能整本转载，只能靠 200–400 字摘录建基线。

## 30 秒开始

### 方式一：把仓库地址丢给 agent（推荐）

不用自己配环境。把下面这段发给 Claude Code / Codex / DSH，它会自己 clone、放进技能目录、跑自检：

```text
克隆 https://github.com/ChemistryBus/zh-nutrition-humanizer.git 到你的技能目录
（Claude Code 是 ~/.claude/skills/，DSH 是 ~/.agents/skills/），
运行 python3 scripts/doctor.py --ci 自检，把结果告诉我。
不要改我的稿子，也不要上传任何文本。
```

装完**重开一个会话**，技能就生效了。

### 方式二：一行命令

```bash
curl -fsSL https://raw.githubusercontent.com/ChemistryBus/zh-nutrition-humanizer/main/bootstrap.sh \
  | bash -s -- --harness claude      # 或 dsh / codex / zcode / minimax / workbuddy / kimi
```

脚本做三件事：放进对应技能目录、跑 `doctor.py` 自检、告诉你下一步。重复运行不会覆盖已有目录。

### 方式三：手动

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git
cd zh-nutrition-humanizer
python3 scripts/check.py examples/before.md --explain
```

零依赖，Python 3.10+（CI 覆盖 3.10 与 3.12），不需要 pip 装任何东西。

### 在对话里怎么用

装好之后，直接用自然语言说需求，不用记命令：

> 用 zh-nutrition-humanizer 检查这篇稿子，只读，把命中和依据列出来。

> 这段帮我按机构语体改一版，改完给我三件套：改后文本、改了什么、保真审计。

> 这篇稿子明天要发，先跑一遍术语层，再看看有没有分号和单位问题。

### 先让机器做确定性改动

```bash
python3 scripts/polish.py 你的稿子.md          # 干跑：只列改动，不写文件
python3 scripts/polish.py 你的稿子.md --out 润色版.md   # 写到指定文件
python3 scripts/polish.py 你的稿子.md --write          # 原地覆盖（先备份 .bak）
```

只改五类：术语误写、数值区间「至」、汉字数字带单位、术语层级、多余空格。
引号里的原文不动，数字只做写法转换（三百毫克 → 300 mg），不做同义改写。

### 再跑一次机检

```bash
python3 scripts/check.py 你的稿子.md --explain            # 逐条给依据
python3 scripts/check.py 你的稿子.md --diff               # 按上下文展示命中
python3 scripts/check.py 你的稿子.md --profile textbook   # 换成教材体基线（默认膳食指南体）
python3 scripts/check.py 你的稿子.md --terms              # 只看术语层：首选写法、缩写、单位
python3 scripts/audit.py 你的稿子.md                     # 一页体检报告（支持 .docx）
python3 scripts/audit.py 原稿.md --revised 改后.md        # 体检 + 保真审计 + 待确认问题
python3 scripts/deliver.py 原稿.md 改后.md               # 三件套交付：改后文本 + 改了什么 + 保真审计
python3 scripts/source_db.py search 中心型肥胖            # 查本地原文库（来源 + 页码）
python3 scripts/fidelity.py 原稿.md 改后.md              # 保真审计：数字/引用/限定词有没有动
```

没有稿子？用仓库自带的 20 组真实初稿：

```bash
python3 scripts/check.py examples/before.md     # 预期：10.4 处/千字，退出码 1
python3 scripts/check.py examples/after.md      # 预期：段落级 0 命中（说明性文字除外）
```

## 怎么判

五族规则：L/T/C 是语体与结构（13 条），K 是术语与定义（17 条错误写法 + 2 条首选写法 + 定义句数值核对 + K4 定义结构 / K5 角色词 / K6 三新表述），S 是文档级体例（6 项：单位、术语混用、英文夹注、缩写首现、汉字单位、分号）。

<table width="100%">
  <thead><tr><th>族</th><th>抓什么</th><th>机构文本</th><th>大模型初稿</th><th>判法</th></tr></thead>
  <tbody>
    <tr><td>L 口语降维（7 条）</td><td>汉字数字带单位、第二人称与祈使、口语形容、比喻实体词、像是／好比、不是X而是Y、更X收尾</td><td>0–0.03</td><td>0.15–2.0</td><td>出现即改</td></tr>
    <tr><td>T 模板化（4 条）</td><td>其机制在于、而非、亦、宜采用</td><td>0–0.03</td><td>0.36–1.07</td><td>超过密度才改</td></tr>
    <tr><td>C 结构（2 条）</td><td>数值区间用“至”、用破折号（年份除外）</td><td>0</td><td>4.52</td><td>一律改 ～</td></tr>
    <tr><td>K 术语与定义（17 条错误写法 + 2 条首选 + K4–K6）</td><td>维他命、粗纤维、必要氨基酸、碳水化合物就是糖、脂肪即脂类、特膳食品、中心性肥胖、β氧化；定义循环、来源未配对、角色错位、三新错位</td><td>0</td><td>视稿件</td><td>命中即改；定义与法规类给条款，结论标待核</td></tr>
    <tr><td>S 体例（6 项）</td><td>单位混用、术语混用、首现未给英文、缩写未展开、汉字单位、分号用法</td><td>—</td><td>—</td><td>逐条列出，不计密度</td></tr>
    <tr><td colspan="5" width="1200">每千字为实测值：L 族在机构文本里为 0，T 族有少量正当用法，所以按密度判；K 族是确定性错误，命中即改。</td></tr>
  </tbody>
</table>

### 改前改后

真实初稿，数字不动；20 组完整对照见 [`examples/after.md`](examples/after.md)。

<table width="100%">
  <thead><tr><th>规则</th><th>改前</th><th>改后</th></tr></thead>
  <tbody>
    <tr><td>L1</td><td>每天蛋白质提高到每公斤体重一点六到二点四克</td><td>蛋白质提高到 1.6～2.4 g/kg</td></tr>
    <tr><td>T1</td><td>其核心依据是能量平衡原则，即摄入能量与总能量消耗相抵</td><td>估算以能量平衡为基础：摄入能量与总能量消耗相抵</td></tr>
    <tr><td>C1</td><td>每日 5 至 7 g/kg/d</td><td>每日 5～7 g/kg/d</td></tr>
    <tr><td colspan="3" width="1200">20 组完整对照在 examples/after.md；改写不动数字、单位与证据等级。</td></tr>
  </tbody>
</table>

### 术语与定义怎么查

`references/terms.json` 收录 38 条术语，其中 32 条的定义**逐字引自标准或指南原文**
（GB 28050—2025 §2 共 13 条、GB 13432—2013 §2 共 3 条），其余只收名称与英文，`needs_definition` 标出，不凭记忆补写。

### 标准定义与三新食品

`references/standards.json` 收 13 条定义，逐字引自知识库 PDF，带条款号与文件路径：
GB 13432（特殊膳食用食品、营养素、营养成分）、GB 14880（营养强化剂）、GB 2760（食品添加剂）、
GB 28050（营养标签）、GB 7718（预包装食品）、GB 24154（运动营养食品）、GB 29924（食品添加剂标签）、
GB 25596 / GB 29922（特医）、GB 22570（辅食营养补充品）、GB 20371（植物蛋白）。

`references/three_new.json` 收 13 条与营养写作相关的三新公告（2025 年第 7 号、2026 年第 5/7 号），
每条带公告号、类别、使用范围、来源链接。三新批准按公告范围使用，不等于写进 GB 14880 或 GB 2760。

三条新规则：

- **K4 定义结构**：定义循环（`A 是……A`）、`以 A、B 为 C 来源` 的来源未配对；
- **K5 角色词**：`赤藓糖醇等营养强化剂` —— 赤藓糖醇是甜味剂，不是强化剂；
- **K6 三新表述**：公告批准写成 GB 14880、把新食品原料写成营养强化剂、范围超出公告。

查定义与公告：

```bash
python3 scripts/standards.py 营养强化剂          # 标准定义 + 条款
python3 scripts/standards.py β-丙氨酸 --three-new # 公告号 + 使用范围
```

<table width="100%">
  <thead><tr><th>查什么</th><th>怎么查</th><th>能不能自动改</th></tr></thead>
  <tbody>
    <tr><td>写法错误</td><td>术语表里的错误形式：维他命、粗纤维、必要氨基酸</td><td>能，给出标准写法</td></tr>
    <tr><td>定义错误</td><td>「碳水化合物就是糖」「脂肪即脂类」「营养成分就是营养素」这类方向反了的包含关系</td><td>能，附标准定义与条款号</td></tr>
    <tr><td>定义句待核</td><td>正文出现「X 是指／定义为」时，把标准定义摆出来供比对</td><td>不自动改，人比对</td></tr>
    <tr><td>层级与口径</td><td>同篇混用（碳水／糖类、脂肪／脂类、能量／热量、GI／升糖指数）</td><td>只报，由人判</td></tr>
    <tr><td colspan="3" width="1200">缺口：GB/T 21922—2026 与 GB 28050 引用的 GB/Z 21922 均未入库，涉及它们的术语只能标「待核」。</td></tr>
  </tbody>
</table>

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

<table width="100%">
  <thead><tr><th>指标</th><th>结果</th><th>目标</th></tr></thead>
  <tbody>
    <tr><td>命中密度差</td><td><strong>74.5×</strong>（机构 0.11 vs 初稿 8.40 处/千字）</td><td>≥3×</td></tr>
    <tr><td>段级误报率</td><td><strong>4.0%</strong>（2/50 段权威原文被标）</td><td>&lt;15%</td></tr>
    <tr><td>段级召回</td><td><strong>92%</strong>（教材体 88% / 科普体 96%）</td><td>—</td></tr>
    <tr><td>阈值拐点</td><td>1–2 处/千字（J=+0.88），默认取 3</td><td>—</td></tr>
    <tr><td colspan="3" width="1200">指标定义与复算命令见 eval/results.md；漏报 4/50 的个案分析在同一文件第 7 节。</td></tr>
  </tbody>
</table>

正样本 50 段（1.78 万字，与建基线的页码不重叠）、负样本 50 段（科普体 24 / 教材体 26）。逐规则表、阈值曲线、消融、漏报分析与三轮盲评在 [`eval/results.md`](eval/results.md)。

盲评最终轮（与仓库文本逐字一致）：科普体改写 **20 胜 0 负**（4.25 vs 2.45），教材体 **16 平**（4.90 vs 4.90）——**教材体 AI 稿只能改体例，改不动语体**。这句是三轮盲评打出来的，第一轮我因为把句子压成电报句被判负 18 次。

## 和主流 humanizer 比，差什么、不学什么

高星项目（blader/humanizer 7 万星、Humanizer-zh 2.3 万星、academic-humanizer 5.5 千星）值得学的不是模式数量，是工程层的四件事。逐项对过：

<table width="100%">
  <thead><tr><th>技术</th><th>主流做法</th><th>本项目</th></tr></thead>
  <tbody>
    <tr><td>模式强度排序</td><td>最强的最先改；「单独出现不算」的要多个共现才改</td><td>用每千字阈值近似：L 族出现即改，T 族超密度才改</td></tr>
    <tr><td>文件模式保护</td><td>只改散文，保留代码、数据、frontmatter、链接目标</td><td>v1.3 起 <code>mask_markdown</code>：代码块、行内代码、URL、HTML 标签不参与检查</td></tr>
    <tr><td>声音匹配</td><td>贴 2–3 段自己的文字，按你的节奏改</td><td>不做个人声音；锚是 141 段机构语料，目标是机构口吻</td></tr>
    <tr><td>安装与验证</td><td>npx 一键装、插件清单、doctor</td><td><code>.claude-plugin/plugin.json</code>、<code>scripts/doctor.py</code>、Claude Code 加载实测</td></tr>
    <tr><td colspan="3" width="1200">共性技术在工程层：保护不该改的、装得上、说得清。不在模式数量。</td></tr>
  </tbody>
</table>

还没补的三件：按语体切档（教材体与指南体的阈值不同）、diff 式报告（现在只给清单）、一键安装脚本。

**一条明确不学的**：Humanizer-zh 的 F 类列了「进行＋动词」「四字格排比」「被字句堆叠」等中文病灶。在我们的语料上实测：

<table width="100%">
  <thead><tr><th>特征</th><th>机构文本</th><th>大模型初稿</th><th>结论</th></tr></thead>
  <tbody>
    <tr><td>进行＋动词</td><td>0.81 / 千字</td><td>0.37</td><td>机构文本用得更多，不能当病灶</td></tr>
    <tr><td>四字格排比</td><td>0.71 / 千字</td><td>0.30</td><td>同上</td></tr>
    <tr><td>被字句</td><td>0.47 / 千字</td><td>0.67</td><td>方向对，差距不足以设阈值</td></tr>
    <tr><td colspan="4" width="1200">这些规则校准的是「自然人写作」，不是「机构语体」。照搬会把公文腔当优点改掉，和目标是反的——与「升糖指数」那条同类。</td></tr>
  </tbody>
</table>

## 支持哪些 harness

技能目录放对，`SKILL.md` 自带 frontmatter；Claude Code 另有插件清单，可整包加载。

<table width="100%">
  <thead><tr><th>环境</th><th>技能目录</th><th>实测</th></tr></thead>
  <tbody>
    <tr><td>纯命令行 / CI</td><td>—</td><td>已验证：GitHub Actions 每次推送跑 <code>validate.py</code> 与 <code>doctor.py --ci</code></td></tr>
    <tr><td>Claude Code</td><td><code>~/.claude/skills/</code> 或 <code>--plugin-dir</code></td><td><b>已验证</b>：<code>claude plugin validate</code> 通过，加载后显示 Skills (1)</td></tr>
    <tr><td>Codex</td><td><code>~/.codex/skills/</code></td><td><b>已验证</b>（2026-11-19）：识别技能，check 退出码 1，polish 47 处</td></tr>
    <tr><td>DSH（DeepSeek Harness）</td><td><code>~/.dsh/skills/</code></td><td>目录已就绪（486 个技能）；需放入后重开会话，本会话内无法热加载</td></tr>
    <tr><td>ZCode</td><td><code>~/.zcode/skills/&lt;skill-name&gt;/SKILL.md</code></td><td><b>已验证</b>（2026-11-19）：识别技能，check 1，polish 47 处</td></tr>
    <tr><td>Kimi CLI</td><td><code>~/.kimi/skills/</code> 或 <code>~/.config/agents/skills/</code></td><td>目录约定；本机未装</td></tr>
    <tr><td>MiniMax</td><td><code>~/.agents/skills/</code> 或 <code>~/.config/minimax/skills</code></td><td><b>已验证</b>（2026-11-19）：识别技能，check 1，polish 47 处</td></tr>
    <tr><td>WorkBuddy</td><td><code>~/.workbuddy/skills/</code></td><td>目录约定；未做加载测试</td></tr>
    <tr><td>自建流程</td><td><code>--json</code></td><td>已验证：<code>eval.py</code> 可作回归测试</td></tr>
    <tr><td colspan="3" width="1200">2026-11-19 实测：Claude Code、Codex、ZCode、MiniMax 四台全部通过（识别技能、check 退出码 1、polish 47 处、说得清规则族）。Kimi CLI 与 WorkBuddy 本机未装，只按目录约定整理。逐项话术见 <a href="docs/harness-test.md">docs/harness-test.md</a>。</td></tr>
  </tbody>
</table>

## 安装选项

<table width="100%">
  <thead><tr><th>需求</th><th>做法</th></tr></thead>
  <tbody>
    <tr><td>只想查一篇稿子</td><td><code>git clone</code> 后直接跑 <code>scripts/check.py</code>，不安装</td></tr>
    <tr><td>当技能长期用</td><td>克隆到技能目录，版本用 tag 锁（<code>git checkout v1.15.0</code>）</td></tr>
    <tr><td>接进 CI</td><td>把 <code>scripts/check.py</code> 拷进仓库，或 <code>git submodule add</code></td></tr>
    <tr><td colspan="2" width="1200">安装不需要 pip；长期使用建议锁 tag，升级后重跑 scripts/validate.py。</td></tr>
  </tbody>
</table>

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

**Q：为什么叫 humanizer？**
英文里 humanizer 指把机器文本改得像人写的工具。这里沿用这个词，但目标是反的：不是让它像自然人，而是让它像机构发布的文字。中文标题用「语体校准」，比「人味化」准确。

**Q：术语写错了能改吗？**
能改**已知的错**：维他命→维生素、粗纤维→膳食纤维、必要氨基酸→必需氨基酸，以及「碳水化合物就是糖」「脂肪即脂类」这类方向反了的定义。依据是 `references/terms.json`：38 条术语，32 条定义逐字引自标准或指南原文（GB 28050—2025 §2 共 13 条、GB 13432—2013 §2 共 3 条，其余引自 2023–2025 年食养指南与体重管理文件，页码见 `references/source-map.md`）。
不能判**未知的对错**：术语表没收的写法，只报「同篇混用」；涉及 GB/T 21922—2026 的条目一律标「待核」，因为标准原文没入库。

**Q：和「去 AI 味」的工具有什么不同？**
目标不同。那类工具让文字更像自然人写作，允许口语与个人声音；这里要求更像政策文件、学会出版物与标准，口语与个人声音恰恰是减分项。同一个「删连接词」在这两套目标下结论相反。

## 文档

<table width="100%">
  <thead><tr><th>文件</th><th>内容</th></tr></thead>
  <tbody>
    <tr><td><a href="SKILL.md">SKILL.md</a></td><td>技能主文件：定位、规则表、流程、局限</td></tr>
    <tr><td><a href="references/baseline.md">references/baseline.md</a></td><td>141 段语料的八项统计、提取路由、复现方法</td></tr>
    <tr><td><a href="references/rule-audit.md">references/rule-audit.md</a></td><td>v0.1 的 25 条规则逐条判（删 17、并 5、留 4、待验证 2）</td></tr>
    <tr><td><a href="scripts/deliver.py">scripts/deliver.py</a></td><td>三件套交付：改后文本、改了什么、保真审计与待确认问题</td></tr>
    <tr><td><a href="scripts/fidelity.py">scripts/fidelity.py</a></td><td>保真审计：改稿前后比对数字、引用、限定词、否定、比较方向</td></tr>
    <tr><td><a href="references/decisions-template.md">references/decisions-template.md</a></td><td>写书期决策日志模板：改/留/误报各记一行，月度提名规则</td></tr>
    <tr><td><a href="references/polish-checklist.md">references/polish-checklist.md</a></td><td>润色的八个操作：拆长句、拆分号、去套壳……每条带边界</td></tr>
    <tr><td><a href="references/ai-tells.md">references/ai-tells.md</a></td><td>按规则编号排的对照表 + 七条「什么时候不该改」</td></tr>
    <tr><td><a href="eval/results.md">eval/results.md</a></td><td>评测报告：密度差、误报率、阈值扫描、漏报、盲评</td></tr>
    <tr><td><a href="examples/after.md">examples/after.md</a></td><td>20 组真实初稿与改写，数字零改动</td></tr>
    <tr><td><a href="examples/walkthrough.md">examples/walkthrough.md</a></td><td>一段初稿的全流程：机检 → 机械润色 → 人工改 → 终检</td></tr>
    <tr><td><a href="scripts/audit.py">scripts/audit.py</a></td><td>一页体检：语体对照、术语层、可自动改 vs 需人工、下一步</td></tr>
    <tr><td><a href="docs/real-world-test.md">docs/real-world-test.md</a></td><td>2 万字真实稿的术语层测试：命中、可自动改的、留给人判断的</td></tr>
    <tr><td><a href="docs/harness-test.md">docs/harness-test.md</a></td><td>各 harness 的安装与验收话术</td></tr>
    <tr><td><a href="docs/source-db.md">docs/source-db.md</a></td><td>本地原文库：按需 OCR、页级缓存、FTS 检索，不重复劳动</td></tr>
    <tr><td><a href="references/source-map.md">references/source-map.md</a></td><td>权威来源地图：文件形态、docarbiter 路由、已核对的术语锚点</td></tr>
    <tr><td><a href="references/terms.json">references/terms.json</a></td><td>38 条术语、32 条标准定义、2 条首选写法、7 个缩写、6 个单位写法</td></tr>
    <tr><td><a href="references/standards.json">references/standards.json</a></td><td>13 条标准定义、条款号与文件路径、化合物来源表</td></tr>
    <tr><td><a href="references/three_new.json">references/three_new.json</a></td><td>三新公告：公告号、类别、使用范围、来源链接</td></tr>
    <tr><td><a href="scripts/standards.py">scripts/standards.py</a></td><td>查标准定义与三新公告：术语名 → 定义、条款、范围</td></tr>
    <tr><td><a href="CONTRIBUTORS.md">CONTRIBUTORS.md</a></td><td>作者与致谢：人做什么、工具做什么、署名怎么留痕</td></tr>
    <tr><td><a href="THIRD_PARTY_NOTICES.md">THIRD_PARTY_NOTICES.md</a></td><td>语料来源与版权声明</td></tr>
    <tr><td><a href="scripts/doctor.py">scripts/doctor.py</a></td><td>安装自检：技能契约、可移植性、harness 目录</td></tr>
    <tr><td colspan="2" width="1200">除 README.en.md 与 THIRD_PARTY_NOTICES.md 外，文档正文均为中文。</td></tr>
  </tbody>
</table>

## 作者与致谢

本项目由 **ChemistryBus** 发起并终审，**DSH（DeepSeek Harness）** 执行语料抽取、规则实现、评测与文档初稿。
每个提交都带 `Co-Authored-By: DSH (DeepSeek Harness)`，在提交列表里显示为第二个头像；
GitHub 的 Contributors 图按「提交作者绑定的账号」统计，DSH 没有账号，也不为此注册——
分工与核对方式写在 [`CONTRIBUTORS.md`](CONTRIBUTORS.md)。

## 许可

代码 MIT，见 [`LICENSE`](LICENSE)。语料摘录不在 MIT 授权范围内，来源与版权见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
