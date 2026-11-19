#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安装与 harness 兼容性自检。

用法：
    python3 scripts/doctor.py            # 自检 + 探测本机 harness
    python3 scripts/doctor.py --json

检查三件事：
    1. 技能契约：SKILL.md frontmatter、name 与目录名一致、必备文件齐全；
    2. 可移植性：把仓库复制到临时目录后，三个入口脚本仍能跑；
    3. harness：Claude Code 用官方命令真实加载一次；其余按目录约定探测并标注状态。
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["SKILL.md", "README.md", "README.en.md", "LICENSE",
            "scripts/check.py", "scripts/polish.py", "scripts/eval.py",
            "references/terms.json", "references/corpus", "examples/after.md"]

HARNESS = [
    ("Claude Code", "~/.claude/skills/", "claude"),
    ("Codex", "~/.codex/skills/", "~/.codex"),
    ("DSH (DeepSeek Harness)", "~/.dsh/skills/", "~/.dsh"),
    ("ZCode", "~/.zcode/skills/", "~/.zcode"),
    ("Kimi CLI", "~/.kimi/skills/ 或 ~/.config/agents/skills/", "~/.kimi"),
    ("MiniMax", "~/.agents/skills/ 或 ~/.config/minimax/skills", "~/.agents"),
    ("WorkBuddy", "~/.workbuddy/skills/", "~/.workbuddy"),
]


def read_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def run(cmd, cwd=None, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ci", action="store_true", help="只查契约与可移植性，跳过本机 harness")
    args = ap.parse_args()

    checks = []

    def ok(name, cond, detail=""):
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    # 1 技能契约
    fm = read_frontmatter((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    ok("SKILL.md 有 name", bool(fm.get("name")), fm.get("name", ""))
    ok("name 与目录名一致", fm.get("name") == ROOT.name,
       f"{fm.get('name')} vs {ROOT.name}——harness 按目录名识别技能，不一致时把目录改名为 {fm.get('name')}")
    ok("description 存在且 ≥ 40 字", len(fm.get("description", "")) >= 40,
       f"{len(fm.get('description', ''))} 字")
    missing = [f for f in REQUIRED if not (ROOT / f).exists()]
    ok("必备文件齐全", not missing, "、".join(missing))

    # 2 可移植性：复制到临时目录后运行
    with tempfile.TemporaryDirectory() as td:
        dst = Path(td) / "zh-nutrition-humanizer"
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.bak"))
        code, out = run([sys.executable, "scripts/check.py", "examples/before.md"],
                        cwd=dst, timeout=60)
        ok("临时目录内 check.py 可运行", code == 1, f"exit={code}")
        code2, out2 = run([sys.executable, "scripts/validate.py"], cwd=dst, timeout=120)
        ok("临时目录内 validate.py 通过", code2 == 0, out2.strip().splitlines()[-1] if out2 else "")

    # 3 Claude Code 真实加载（--ci 跳过）
    harness = []
    if not args.ci:
        code, out = run(["claude", "plugin", "validate", "."], cwd=ROOT, timeout=60)
        ok("Claude Code: plugin validate", "passed" in out.lower() or code == 0,
           out.strip().splitlines()[-1] if out else "")
        code, out = run(["claude", "--plugin-dir", ".", "plugin", "details", fm.get("name", ROOT.name)],
                        cwd=ROOT, timeout=60)
        loaded = "Skills (1)" in out
        ok("Claude Code: 技能被识别", loaded,
           "Skills (1) " + ROOT.name if loaded else (out.strip().splitlines()[-1] if out else ""))

    # 4 harness 目录探测
    for name, rel, probe in ([] if args.ci else HARNESS):
        p = Path(rel.replace("~", str(Path.home())).split(" 或 ")[0].strip())
        installed = p.exists()
        harness.append({"name": name, "dir": rel, "exists": installed})
    dsh_skills = Path.home() / ".dsh" / "skills"
    ok("DSH: 技能目录存在", args.ci or dsh_skills.exists(),
       f"{len(list(dsh_skills.iterdir())) if dsh_skills.exists() else 0} 个已装技能（需复制后重开会话才加载）")

    if args.json:
        print(json.dumps({"checks": checks, "harness": harness}, ensure_ascii=False, indent=1))
    else:
        for c in checks:
            print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['name']}"
                  + (f"  {c['detail']}" if c["detail"] else ""))
        print("\nharness 目录：")
        for h in harness:
            state = "存在" if h["exists"] else "未安装"
            print(f"  {h['name']:<24} {h['dir']:<38} {state}")
        print("\n说明：本脚本只对 Claude Code 做真实加载（Skills 1）；Codex / ZCode / MiniMax / DSH"
              " 的实测结果见 docs/harness-test.md。")
        failed = [c for c in checks if not c["pass"]]
        print(f"\n结果：{len(checks) - len(failed)}/{len(checks)} 通过")
        if failed:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
