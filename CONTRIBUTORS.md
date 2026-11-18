# 作者与致谢

## 人类作者

**ChemistryBus** —— 项目发起、领域判断（哪些规则成立、哪些是我想当然）、语料授权与发布维护。
所有事实性主张与最终取舍由人类作者拍板。

## 工具协作

**DSH（DeepSeek Harness）** —— 在本机运行的编码 agent。2026-11-18 的会话中承担：
语料抽取与抽样、规则实现、评测脚本、盲评包整理、文档初稿与仓库搭建。

## 为什么 Contributors 图里没有 DSH

GitHub 的 Contributors 按「提交作者邮箱所绑定的 GitHub 账号」统计。DSH 没有独立账号，
本项目也不为此注册账号、借用他人邮箱或做任何身份包装——那会污染署名。

署名的实际落点是：

- **每个提交都带 `Co-Authored-By: DSH (DeepSeek Harness) <noreply@deepseek.com>`**，
  在提交列表里显示为第二个头像，与 Claude Code 在同类项目中的显示方式一致；
- **本文档**记录协作范围；
- **README「作者与致谢」** 指向本文档。

仓库自带一条 commit-msg 钩子，新提交会自动补上这行 trailer：

```bash
git config core.hooksPath .githooks   # 克隆后执行一次
```

核对方式：

```bash
git log --format='%an <%ae>%n%b' | grep -c 'Co-Authored-By: DSH'
# 期望输出：等于提交总数
```

## 署名原则

1. **署 harness，不署模型。** 工具名是稳定的，模型版本会换。
2. **不伪造身份。** 不用他人邮箱、不注册马甲账号来凑 Contributors。
3. **分工写清楚。** 哪些判断由人做、哪些执行由工具做，逐项列明。
4. **可核对。** 提交历史与本文档互为佐证。
