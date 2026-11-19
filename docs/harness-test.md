# 各 harness 的一键测试

> 用法：把对应 harness 的那**一整段**复制过去发送即可。单段包含安装、检查、润色、读规则四步，
> 结尾明确要求**只在对话里回复，不生成任何文档**。
> 判据四项：能识别技能、能跑脚本、不改原文件、说得清规则族。

## 通用判据

| # | 判据 | 通过的样子 |
|---|---|---|
| 1 | 技能被识别 | 能说出 `zh-nutrition-humanizer` 及其 description |
| 2 | 能执行脚本 | `scripts/check.py` 报出命中分类与退出码 |
| 3 | 不改原文件 | 没有 `--write`，原文件字节不变 |
| 4 | 规则说得清 | 能说出 L / T / K / C / S 至少三族 |

## Codex

```text
请在本机安装并验证一个技能，按顺序执行，最后只用对话回复，不要生成任何文档或报告文件：
1. 执行 git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.codex/skills/zh-nutrition-humanizer
2. 进入该目录，执行 python3 scripts/check.py examples/before.md，记下退出码和命中的规则分类（L/T/K/C/S）；
3. 执行 python3 scripts/polish.py examples/before.md（不要加 --write），记下改动条数；
4. 读 SKILL.md，用一句话说明它分了哪几族规则、默认语体档是什么。
然后只回复这四行，不要写文件、不要修改我的任何原稿：
技能目录: <路径>
check 退出码: <0 或 1>
polish 改动: <N> 处
规则族: <一句话>
```

## ZCode

```text
请在本机安装并验证一个技能，按顺序执行，最后只用对话回复，不要生成任何文档或报告文件：
1. 执行 git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.zcode/skills/zh-nutrition-humanizer
2. 进入该目录，执行 python3 scripts/check.py examples/before.md，记下退出码和命中的规则分类（L/T/K/C/S）；
3. 执行 python3 scripts/polish.py examples/before.md（不要加 --write），记下改动条数；
4. 读 SKILL.md，用一句话说明它分了哪几族规则、默认语体档是什么。
然后只回复这四行，不要写文件、不要修改我的任何原稿：
技能目录: <路径>
check 退出码: <0 或 1>
polish 改动: <N> 处
规则族: <一句话>
```

## MiniMax

```text
请在本机安装并验证一个技能，按顺序执行，最后只用对话回复，不要生成任何文档或报告文件：
1. 执行 git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.agents/skills/zh-nutrition-humanizer
2. 进入该目录，执行 python3 scripts/check.py examples/before.md，记下退出码和命中的规则分类（L/T/K/C/S）；
3. 执行 python3 scripts/polish.py examples/before.md（不要加 --write），记下改动条数；
4. 读 SKILL.md，用一句话说明它分了哪几族规则、默认语体档是什么。
然后只回复这四行，不要写文件、不要修改我的任何原稿：
技能目录: <路径>
check 退出码: <0 或 1>
polish 改动: <N> 处
规则族: <一句话>
```

## DSH（DeepSeek Harness）

```text
请把 zh-nutrition-humanizer 装进 DSH 技能目录并验证，最后只用对话回复，不要生成文档：
1. 执行 git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.dsh/skills/zh-nutrition-humanizer
2. 执行 cd ~/.dsh/skills/zh-nutrition-humanizer && python3 scripts/check.py examples/before.md
3. 执行 python3 scripts/polish.py examples/before.md（不要加 --write）
4. 读 SKILL.md，说明规则族与默认语体档。
注意：DSH 在会话启动时扫描技能，装完要重开会话才会加载。先回复安装与脚本结果，重开后再说技能是否可见。
只回复四行：技能目录 / check 退出码 / polish 改动条数 / 规则族。
```

## 已经验过的两个

- **Claude Code**：`claude plugin validate .` 通过；`claude --plugin-dir . plugin details zh-nutrition-humanizer`
  显示 `Skills (1)`，无需再测。
- **命令行 / CI**：GitHub Actions 每次推送跑 `validate.py` 与 `doctor.py --ci`。

## 本机现状（2026-11-19）

| harness | 本机 | 状态 |
|---|---|---|
| Claude Code 2.1.228 | 是 | 已验证（plugin validate + 加载 Skills 1） |
| DSH | 是（本会话运行于 DSH） | 目录就绪，需重开会话 |
| Codex / ZCode / MiniMax | 是 | **待测**，复制上面对应那段 |
| Kimi CLI / WorkBuddy | — | 未安装，仅按目录约定整理 |
