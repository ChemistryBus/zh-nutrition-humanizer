#!/usr/bin/env python3
"""K4/K5/K6 回归：fixture 必中，60 段语料不误报。"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class DefinitionChecks(unittest.TestCase):
    def test_three_new_schema(self):
        import json
        data = json.loads((ROOT / "references/three_new.json").read_text(encoding="utf-8"))
        pairs = [(x["announcement"], x["name"]) for x in data["items"]]
        self.assertEqual(len(pairs), len(set(pairs)), "同一公告内名称重复")
        for x in data["items"]:
            for k in ("announcement", "category", "name", "scope", "source_url"):
                self.assertTrue(x.get(k), f"{x.get('name')} 缺 {k}")

    def test_fixture_hits_four(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check.py"),
             str(ROOT / "tests/fixtures/definition_special_food.md")],
            capture_output=True, text=True, check=False).stdout
        for key in ("定义循环", "角色错位", "标准错位", "范围错位"):
            self.assertIn(key, out)

    def test_authoritative_definitions_clean(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from definition_checks import check_definitions
        text = (ROOT / "tests/fixtures/definitions_authoritative.md").read_text(encoding="utf-8")
        issues, _ = check_definitions(text)
        self.assertEqual(issues, [], f"权威定义误报：{[i['rule'] for i in issues]}")

    def test_audit_has_definition_section(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts/audit.py"),
             str(ROOT / "tests/fixtures/definition_special_food.md")],
            capture_output=True, text=True, check=False).stdout
        self.assertIn("## 定义与法规", out)
        self.assertIn("K4", out)

    def test_no_false_positive_on_corpus_sample(self):
        files = sorted((ROOT / "references/corpus").rglob("*.md"))[:30]
        for f in files:
            out = subprocess.run(
                [sys.executable, str(ROOT / "scripts/check.py"), str(f)],
                capture_output=True, text=True, check=False).stdout
            for key in ("[K4]", "[K5]", "[K6]"):
                self.assertNotIn(key, out, f"{f} 出现 {key} 误报")


if __name__ == "__main__":
    unittest.main()
