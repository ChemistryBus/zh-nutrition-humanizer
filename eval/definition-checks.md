# K4–K6 误报与覆盖（2026-11-25，v1.16.0）

## 方法

| 集合 | 内容 | 判定 |
|---|---|---|
| 权威定义 | `tests/fixtures/definitions_authoritative.md`，21 条，逐字摘自 GB 13432 / 14880 / 2760 / 28050 / 7718 / 29924 / 24154 / 29922 / 25596 / 22570 / 20371 | K3–K6 应为 0 |
| 语料 | `references/corpus` 全部 141 段（指南体 + 教材体） | K4–K6 应为 0 |
| 正样本 | `tests/fixtures/definition_special_food.md`（结构脱敏） | K4 定义循环、K5 角色错位、K6 标准/范围错位应命中 |

## 结果

```
权威定义 21 条：K4–K6 命中 0
语料 141 段：K4–K6 命中 0
正样本：K1×2、K4×1、K5×1、K6×2
```

## 说明

- K4 只判结构信号（定义循环、来源未配对），不判“这个类别归属对不对”；
- K5 依赖 `standards.json` 的角色表，表外成分只进 notes（待核），不计命中；
- K6 依赖 `three_new.json`，表外公告不判，避免拿不完整数据当依据；
- 误报为 0 是当前样本上的结果，不是普适保证；新增成分/公告后需重跑本页。

复现：

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
