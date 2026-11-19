# 各 harness 的安装与验收测试

> 目的：让每个 harness 用「自然语言」装一次、跑一次，并留下可对照的证据。
> 三分钟一项，不需要改配置。

## 通用验收标准（四项全过才算通过）

| # | 判据 | 通过的样子 |
|---|---|---|
| 1 | 技能被识别 | 能说出 `zh-nutrition-humanizer` 及其 description |
| 2 | 能执行脚本 | 跑 `scripts/check.py` 并报出命中项与退出码 |
| 3 | 不改原文件 | 默认只读；除非明确要求，不覆盖用户文件 |
| 4 | 规则说得清 | 能说出至少三个规则族（L 口语 / T 模板 / K 术语 / C 结构 / S 体例） |

## Claude Code（已验证）

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git
claude --plugin-dir ./zh-nutrition-humanizer plugin details zh-nutrition-humanizer
```

预期：`Skills (1) zh-nutrition-humanizer`，always-on ≈140 token。

## Codex

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.codex/skills/zh-nutrition-humanizer
```

把下面这段发给 Codex：

```text
请先确认你能看到名为 zh-nutrition-humanizer 的技能，说出它的 description 前 20 个字。
然后只读地做两件事，把原始输出贴给我：
1. 运行 python3 scripts/check.py examples/before.md，报退出码与命中分类；
2. 运行 python3 scripts/polish.py examples/before.md，报改动条数（不要加 --write）。
最后用一句话说明这套规则分了哪几族。不要修改任何文件的原文。
```

## ZCode

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.zcode/skills/zh-nutrition-humanizer
```

发给 ZCode 的话与 Codex 相同；ZCode 的技能目录是 `~/.zcode/skills/<skill-name>/SKILL.md`，目录名必须是 `zh-nutrition-humanizer`。

## MiniMax

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.agents/skills/zh-nutrition-humanizer
```

发给 MiniMax：

```text
先确认技能 zh-nutrition-humanizer 是否在列表里。在的话，请用它检查 examples/before.md：
只读运行 scripts/check.py，把命中项按族列出，并告诉我每千字命中密度；
再用 scripts/polish.py 输出润色版到临时文件，告诉我改了几处。不要动我的原文件。
```

## DSH（DeepSeek Harness）

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.dsh/skills/zh-nutrition-humanizer
```

DSH 在会话启动时加载技能，**需要重开一个会话**。重开后：

```text
列出你可用的技能里与中文营养写作相关的那个，然后只读检查 examples/before.md，
报告命中密度，并说明 L / T / K 三族分别查什么。
```

## 报告什么

把四行贴回来即可：

```text
harness:
能识别技能: 是/否
check.py 退出码: 0/1
polish.py 改动条数: N
规则族说对几个: N/5
```

## 本机现状（2026-11-19）

| harness | 本机是否安装 | 状态 |
|---|---|---|
| Claude Code 2.1.228 | 是 | 已验证，`plugin validate` + `plugin details` 通过 |
| DSH | 是（本会话即运行于 DSH） | 目录就绪，需重开会话加载 |
| Codex / ZCode / MiniMax | 是（用户确认） | **待测**，按上文四步执行 |
| Kimi CLI / WorkBuddy | — | 未安装，仅按目录约定整理 |

`python3 scripts/doctor.py` 可复核契约、可移植性与本机目录；`--ci` 只跑前两项。
