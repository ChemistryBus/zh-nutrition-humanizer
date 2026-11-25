#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""K4/K5/K6：定义结构、角色词、三新食品表述检查。

只报告，不改写；所有判据来自 references/standards.json 与 references/three_new.json。
查不到依据的一律进 notes（待核），不计命中。
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "references"


def _load(name):
    try:
        return json.loads((BASE / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


STANDARDS = _load("standards.json")
THREE_NEW = _load("three_new.json")
ROLES = STANDARDS.get("roles", {})
SOURCES = STANDARDS.get("sources", {})
STOP = {"食品", "营养", "膳食", "人群", "产品", "成分"}


def _sentences(text):
    return [s for s in re.split(r"(?<=[。！？；])", text) if s.strip()]


def _clean_ingredient(s):
    s = s.strip()
    s = re.sub(r"^(辅以|添加|加入|配以|含有)", "", s)
    return s.strip("，。；、 ")


def k4_circular(body):
    """定义循环：句尾核心词在句内已经出现过，且句子是定义式。"""
    issues = []
    for sent in _sentences(body):
        s = sent.strip()
        if not any(k in s for k in ("是指", "指的是", "定义为", "系指", "称为", "制成的", "加工制成")):
            continue
        body_wo = s.rstrip("。.")
        for n in range(10, 3, -1):
            tail = body_wo[-n:]
            if not re.fullmatch(r"[\u4e00-\u9fff]+", tail) or tail in STOP:
                continue
            first = body_wo.find(tail)
            if first != -1 and first < len(body_wo) - n - 4:
                issues.append({
                    "group": "K", "id": "K4", "rule": f"定义循环：句尾「{tail}」已在句内出现",
                    "count": 1, "samples": [s.splitlines()[-1].strip()[:60]],
                    "hint": "定义项不得再出现被定义项；改成“属概念 + 种类差”",
                    "evidence": "定义逻辑：被定义项（definiendum）不得出现在定义项（definiens）中",
                })
                break
    return issues


def k4_sources(body):
    """来源配对：每个化合物应对应一种营养素，且在该营养素的来源表内。"""
    issues, notes = [], []
    for m in re.finditer(r"以([^，。；]{2,80}?)为([^，。；]{2,12}?)来源", body):
        nutrient = m.group(2).strip()
        items = [_clean_ingredient(x) for x in re.split(r"[、，和及]", m.group(1)) if x.strip()]
        known = SOURCES.get(nutrient)
        if not known:
            notes.append(f"「{nutrient}」的来源表未入库，待核：{m.group(0)[:50]}")
            continue
        def norm(x):
            return re.sub(r"^[LD]-", "", x.strip())
        known_n = {norm(x) for x in known}
        bad = [x for x in items if x and norm(x) not in known_n]
        if bad:
            issues.append({
                "group": "K", "id": "K4", "rule": f"来源未配对：{'、'.join(bad)} 不是 {nutrient} 的批准来源",
                "count": 1, "samples": [m.group(0)[:60]],
                "hint": f"{nutrient} 的化合物来源见 GB 14880；不在表内的不能写成来源",
                "evidence": "GB 14880—2012 化合物来源名单",
            })
    return issues, notes


def k5_roles(body):
    """角色词：X 等营养强化剂，X 必须是营养强化剂。"""
    issues, notes = [], []
    pat = r"(?:辅以|添加|加入|配以)?([^，。；]{2,50}?)(?:等|、)[^，。；]{0,10}?营养强化剂"
    for m in re.finditer(pat, body):
        chunk = m.group(1)
        items = [_clean_ingredient(x) for x in re.split(r"[、，和及]", chunk) if x.strip()]
        for it in items:
            role = ROLES.get(it)
            if role and role.get("role") != "营养强化剂":
                issues.append({
                    "group": "K", "id": "K5", "rule": f"角色错位：{it} 是{role['role']}，不是营养强化剂",
                    "count": 1, "samples": [m.group(0)[:60]],
                    "hint": f"按 GB 2760 标为{role['role']}；营养强化剂只指 GB 14880 的化合物来源",
                    "evidence": role.get("source", "GB 2760"),
                })
            elif not role:
                notes.append(f"「{it}」的食品添加剂角色未入库，待核：{role or ''}".strip())
    return issues, notes


def k6_three_new(body):
    """三新食品：公告批准 ≠ GB 14880；使用范围必须跟公告。"""
    issues, notes = [], []
    for item in THREE_NEW.get("items", []):
        name = item.get("name", "")
        if not name or name not in body:
            continue
        sent = next((x for x in _sentences(body) if name in x), "")
        window = sent or name
        if "GB 14880" in window and item.get("category", "").startswith("食品营养强化剂"):
            issues.append({
                "group": "K", "id": "K6", "rule": f"标准错位：{name} 是 {item['announcement']} 批准，不是 GB 14880 已列",
                "count": 1, "samples": [window.strip()[:60]],
                "hint": f"写成「{item['announcement']}批准，使用范围：{item['scope']}」",
                "evidence": item.get("source_url", ""),
            })
        if "各类食品" in window and "仅限" in item.get("scope", ""):
            issues.append({
                "group": "K", "id": "K6", "rule": f"范围错位：{name} 仅限{item['scope']}",
                "count": 1, "samples": [name],
                "hint": "不能写“可用于各类食品”",
                "evidence": item.get("source_url", ""),
            })
        if "新食品原料" in window and item.get("category") == "食品营养强化剂新品种":
            issues.append({
                "group": "K", "id": "K6", "rule": f"类别错位：{name} 是营养强化剂新品种，不是新食品原料",
                "count": 1, "samples": [name],
                "hint": "新食品原料与营养强化剂新品种是两条审批路径",
                "evidence": item.get("source_url", ""),
            })
        if not re.search(r"第\s*\d+\s*号", window):
            notes.append(f"「{name}」未见公告号；引用时写「{item['announcement']}」")
    return issues, notes


def check_definitions(body):
    issues, notes = [], []
    issues += k4_circular(body)
    i, n = k4_sources(body); issues += i; notes += n
    i, n = k5_roles(body); issues += i; notes += n
    i, n = k6_three_new(body); issues += i; notes += n
    return issues, notes
