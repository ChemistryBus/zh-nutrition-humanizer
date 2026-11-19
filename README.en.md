<p align="right"><a href="README.md"><img src="https://img.shields.io/badge/Chinese-README-2f81f7?style=flat-square" alt="Chinese"></a></p>

<h1 align="center">zh-nutrition-humanizer</h1>

<p align="center"><strong>Language polishing and terminology correction for Chinese nutrition writing</strong></p>
<p align="center">Match the tone of policy documents, learned-society books and standards · polish language, correct terms · zero dependencies</p>
<p align="center"><strong>v1.2.1 — Percentage Ranges</strong></p>

<p align="center">
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml"><img src="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/releases/tag/v1.2.1"><img src="https://img.shields.io/github/v/release/ChemistryBus/zh-nutrition-humanizer?color=blue&cacheSeconds=300" alt="release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.10--3.12-blue" alt="Python 3.10-3.12">
  <img src="https://img.shields.io/badge/Agent-Skill-111111" alt="Agent Skill">
  <img src="https://img.shields.io/badge/Built%20with-DSH-2f81f7" alt="Built with DSH">
</p>

![overview](docs/assets/overview-en.svg)

## What it is

Most humanizers chase "sounds like a person". This one chases something else: **the voice Chinese nutrition institutions publish in**.

That voice is not a matter of taste. It is specified by three bodies of text:

<table width="100%">
  <thead><tr><th>Class</th><th>Representative texts</th><th>What it fixes</th></tr></thead>
  <tbody>
    <tr><td>National nutrition policy</td><td>National Nutrition Plan (2017–2030); Healthy China Action; the National Health Commission dietary-guidance series (11 documents, 2023–2026)</td><td>How 应 / 宜 / 不宜 / 建议 are used; addressed to a population, not to a reader</td></tr>
    <tr><td>Chinese Nutrition Society books</td><td><em>Encyclopedia of Nutrition Science</em> (2nd ed.); <em>Dietary Guidelines for Chinese Residents</em> (2022); <em>DRIs</em> (2023)</td><td>Terminology hierarchy, definition style, dose units, where evidence sits relative to a claim</td></tr>
    <tr><td>National, industry and local standards</td><td>GB 24154, GB 28050, GB 7718, the WS/T series, GB/T 21922—2026 terminology, local dietary-guidance specifications</td><td>How quantities are written, unit conventions, terminology and category boundaries</td></tr>
    <tr><td colspan="3" width="1200">The three bodies are parallel, not substitutes: policy fixes the voice, learned-society books fix terminology and definitions, standards fix quantities and units.</td></tr>
  </tbody>
</table>

What this repository does is turn that voice into measurable features — terminology level, quantity formatting, sentence length, evidence position — and calibrate the thresholds on **141 excerpts, 53,000 characters**. "Does it read right" becomes "how many hits per 1,000 characters", which anyone can check.

It addresses four recurring problems:

- an LLM-written nutrition draft can have every fact and number right and still read like a popular-science account rather than a published document;
- generic "de-AI" advice — delete connectives, split long sentences, add colloquialisms — **lowers the score** on institutional text;
- there is no accepted Chinese AI-detection benchmark, so edits cannot be justified or audited;
- the source corpus is local and copyrighted, so the baseline has to be built from 200–400 character excerpts.

## 30-second start

### Option 1: let an agent install it

Paste this into Claude Code / Codex / DSH:

```text
Ask me first whether zh-nutrition-humanizer may go into my skills directory; only then run:
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git ~/.claude/skills/zh-nutrition-humanizer
When done, run python3 scripts/check.py examples/before.md --explain and show me the hit list.
Do not modify my drafts and do not upload any text.
```

### Option 2: manual install

```bash
git clone https://github.com/ChemistryBus/zh-nutrition-humanizer.git
cd zh-nutrition-humanizer
python3 scripts/check.py examples/before.md --explain
```

Zero dependencies, Python 3.10+ (CI covers 3.10 and 3.12); nothing to pip install.

### Let the machine make the deterministic edits

```bash
python3 scripts/polish.py your_draft.md        # writes your_draft.md.polished.md and lists every change
```

Five kinds only: misspelled terms, numeric ranges written with 至, Chinese numerals with units,
term level, redundant spaces. Text inside quotation marks is untouched; numbers change notation
(三百毫克 → 300 mg), never value.

### Then run the checker

```bash
python3 scripts/check.py your_draft.md --explain
```

No draft at hand? Use the 20 real drafts shipped with the repo:

```bash
python3 scripts/check.py examples/before.md     # expect: 10.4 hits per 1,000 chars, exit code 1
python3 scripts/check.py examples/after.md      # expect: zero paragraph-level hits
```

## How it judges

Five families: L/T/C are register and structure (12 rules), K is terminology (14 patterns across 11 terms), S is document-level style (3 checks).

<table width="100%">
  <thead><tr><th>Family</th><th>Catches</th><th>Institution</th><th>LLM draft</th><th>Verdict</th></tr></thead>
  <tbody>
    <tr><td>L colloquial (7)</td><td>Chinese numerals with units, second person and imperatives, colloquial adjectives, metaphor nouns, 「像是／好比」, 「不是X而是Y」, evaluative 「更X」 endings</td><td>0–0.03</td><td>0.15–2.0</td><td>fix on sight</td></tr>
    <tr><td>T template (4)</td><td>「其机制在于」, 「而非」, 「亦」, 「宜采用」</td><td>0–0.03</td><td>0.36–1.07</td><td>fix above a density</td></tr>
    <tr><td>C structure (1)</td><td>numeric ranges written with 「至」 instead of ～</td><td>0</td><td>4.52</td><td>always ～</td></tr>
    <tr><td>K terminology (14)</td><td>维他命, 粗纤维, 必要氨基酸, "carbs are sugar", "fat is lipid", "nutritional component is nutrient"…</td><td>0</td><td>draft-dependent</td><td>fix on sight, standard text cited</td></tr>
    <tr><td>S style (3)</td><td>mixed units, mixed terminology, missing English gloss</td><td>—</td><td>—</td><td>listed, not scored</td></tr>
    <tr><td colspan="5" width="1200">Values are measured. The L family is zero in institutional text; the T family has legitimate uses, so it is judged by density. K rules are definite errors: fix on sight.</td></tr>
  </tbody>
</table>

### What a diff looks like

Real drafts, numbers untouched; all 20 pairs in [`examples/after.md`](examples/after.md).

<table width="100%">
  <thead><tr><th>Rule</th><th>Before</th><th>After</th></tr></thead>
  <tbody>
    <tr><td>L1</td><td>每天蛋白质提高到每公斤体重一点六到二点四克</td><td>蛋白质提高到 1.6～2.4 g/kg</td></tr>
    <tr><td>T1</td><td>其核心依据是能量平衡原则，即摄入能量与总能量消耗相抵</td><td>估算以能量平衡为基础：摄入能量与总能量消耗相抵</td></tr>
    <tr><td>C1</td><td>每日 5 至 7 g/kg/d</td><td>每日 5～7 g/kg/d</td></tr>
    <tr><td colspan="3" width="1200">All 20 pairs are in examples/after.md; rewrites never touch numbers, units or evidence grades.</td></tr>
  </tbody>
</table>

### How terminology and definitions are checked

`references/terms.json` holds 22 terms. Sixteen carry definitions quoted verbatim from the standards
(13 in GB 28050—2025 §2, 3 in GB 13432—2013 §2); the rest carry names and English only, marked
`needs_definition`, and no definition is written from memory.

<table width="100%">
  <thead><tr><th>Check</th><th>How</th><th>Auto-fix?</th></tr></thead>
  <tbody>
    <tr><td>Wrong form</td><td>Error forms in the term table: 维他命, 粗纤维, 必要氨基酸</td><td>Yes, suggests the standard form</td></tr>
    <tr><td>Wrong definition</td><td>Reversed inclusion such as "carbs are sugar", "fat is lipid", "nutritional component is nutrient"</td><td>Yes, with the standard definition and clause</td></tr>
    <tr><td>Definition under review</td><td>When the text says "X 是指 / defined as", the standard definition is printed for comparison</td><td>No, human compares</td></tr>
    <tr><td>Level and usage</td><td>Mixed usage inside one document (碳水化合物/糖类, 脂肪/脂类, 能量/热量, GI/升糖指数)</td><td>Reported only</td></tr>
    <tr><td colspan="3" width="1200">Gap: GB/T 21922—2026 and GB/Z 21922 (referenced by GB 28050) are not in the corpus, so terms that depend on them are marked "to verify".</td></tr>
  </tbody>
</table>

Full rule table in [`SKILL.md`](SKILL.md) (Chinese); rule evidence in [`references/rule-audit.md`](references/rule-audit.md).

## Good fit / bad fit

**Good fit**

- pre-delivery checks on Chinese nutrition, sports-nutrition and dietary-guidance manuscripts;
- checking the manuscript version and the public-article version separately (same content, two registers);
- gatekeeping drafts written by someone else, or by a model.

**Bad fit**

- literary popular science and short-video copy — different register, the L family will over-fire;
- English-only drafts (use academic-humanizer);
- fact checking, citation authenticity, evidence grade versus claim strength — all human work, out of scope.

## Evidence, not an "AI probability"

<table width="100%">
  <thead><tr><th>Metric</th><th>Result</th><th>Target</th></tr></thead>
  <tbody>
    <tr><td>Hit-density ratio</td><td><strong>74.5×</strong> (institution 0.11 vs draft 8.40 per 1,000 chars)</td><td>≥3×</td></tr>
    <tr><td>Paragraph false positives</td><td><strong>4.0%</strong> (2 of 50 authoritative paragraphs flagged)</td><td>&lt;15%</td></tr>
    <tr><td>Paragraph recall</td><td><strong>92%</strong> (textbook 88% / popular 96%)</td><td>—</td></tr>
    <tr><td>Threshold knee</td><td>1–2 per 1,000 chars (J = +0.88); default 3</td><td>—</td></tr>
    <tr><td colspan="3" width="1200">Metric definitions and recomputation commands are in eval/results.md; the 4/50 missed cases are in section 7.</td></tr>
  </tbody>
</table>

50 held-out authoritative paragraphs (17,755 characters, page ranges disjoint from the baseline) against 50 LLM paragraphs (24 popular, 26 textbook). Per-rule table, threshold sweep, ablation, missed cases and three blind-rating rounds are in [`eval/results.md`](eval/results.md) (Chinese).

Final blind round, on the exact repository text: popular-register rewrites **20 wins, 0 losses** (4.25 vs 2.45); textbook-register pairs are **16 ties** (4.90 vs 4.90). In other words: **a textbook-register AI draft can only be fixed at the style level, not the register level.** That conclusion came from round one, where compressing sentences into telegraph style lost 18 of 18 comparisons.

## Supported harnesses

Drop the directory in the right place; `SKILL.md` already carries frontmatter, no configuration needed.

<table width="100%">
  <thead><tr><th>Environment</th><th>Skills directory</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>CLI / CI</td><td>—</td><td><code>python3 scripts/check.py draft.md --threshold 3</code>; exit code 1 means over threshold</td></tr>
    <tr><td>Claude Code</td><td><code>~/.claude/skills/</code></td><td>copy the directory; reads <code>SKILL.md</code></td></tr>
    <tr><td>Codex</td><td><code>~/.codex/skills/</code></td><td>same; name the skill explicitly when several are installed</td></tr>
    <tr><td>DSH (DeepSeek Harness)</td><td><code>~/.dsh/skills/</code></td><td>same; frontmatter ready</td></tr>
    <tr><td>ZCode</td><td><code>~/.zcode/skills/&lt;skill-name&gt;/SKILL.md</code></td><td>user-level directory; the directory name is the skill name</td></tr>
    <tr><td>Kimi CLI</td><td><code>~/.kimi/skills/</code> or <code>~/.config/agents/skills/</code></td><td>the second is a shared directory usable by several harnesses</td></tr>
    <tr><td>MiniMax</td><td><code>~/.agents/skills/</code> or <code>~/.config/minimax/skills</code></td><td>project-level: <code>.agents/skills</code></td></tr>
    <tr><td>WorkBuddy</td><td><code>~/.workbuddy/skills/</code></td><td>project-level: <code>.codebuddy/skills/</code> (inherited from the CodeBuddy core)</td></tr>
    <tr><td>Custom pipeline</td><td>—</td><td>consume <code>--json</code>; <code>scripts/eval.py</code> works as a regression test</td></tr>
    <tr><td colspan="3" width="1200">Directory names follow each harness's own documentation; the table reflects conventions as of November 2026.</td></tr>
  </tbody>
</table>

Directory names follow each harness's own documentation; the table reflects the conventions as of November 2026.

## Install options

<table width="100%">
  <thead><tr><th>Need</th><th>Do</th></tr></thead>
  <tbody>
    <tr><td>check one draft</td><td>clone and run <code>scripts/check.py</code>; nothing installed</td></tr>
    <tr><td>long-term skill</td><td>clone into the skills directory and pin a tag (<code>git checkout v1.2.1</code>)</td></tr>
    <tr><td>CI gate</td><td>copy <code>scripts/check.py</code> into the repo, or add it as a submodule</td></tr>
    <tr><td colspan="2" width="1200">Nothing to pip install. For long-term use, pin a tag and re-run scripts/validate.py after upgrading.</td></tr>
  </tbody>
</table>

## FAQ

**Why not delete 「此外／同时」?**
The corpus uses them 3.27 times per 1,000 characters; textbook-register LLM drafts use 3.57. Connectives do not discriminate. What should go is the restatement that follows 「由此可见」.

**Will it ruin good prose?**
Sometimes. The 4.0% false-positive rate is the measured cost on authoritative text, which is why the tool only produces a list and a human decides. No rule touches a number.

**Can it tell whether a text was written by AI?**
No. It reports deviation from this corpus, not an AI probability. There is no accepted Chinese benchmark; anyone claiming one should show their positive and negative samples.

**Why only 200–400 character excerpts?**
Copyright. Every excerpt carries source, publisher and page number; nothing is reproduced in full and no source PDF is redistributed.

**Can I use it in another domain?**
The rule skeleton transfers; the thresholds do not. Rebuild the baseline with `scripts/stats.py` and `scripts/features.py`.

**Why "humanizer"?**
In English a humanizer makes machine text read like a person wrote it. This repository keeps the word but inverts the goal: the target is not a natural individual but an institution publishing. The Chinese title uses 「语体校准」 (register calibration), which is more accurate than "humanising".

**Can it fix a wrong technical term?**
It fixes *known* errors: 维他命→维生素, 粗纤维→膳食纤维, 必要氨基酸→必需氨基酸, and reversed definitions such as "carbs are sugar" or "fat is lipid". The authority is `references/terms.json`: 22 terms, 16 definitions quoted verbatim (13 from GB 28050—2025 §2, 3 from GB 13432—2013 §2).
It cannot judge *unknown* correctness: terms outside the table are only checked for mixed usage inside one document, and anything depending on GB/T 21922—2026 is marked "to verify" because the standard text is not in the corpus.

**How is this different from "de-AI" tools?**
Different objective. Those tools make text read like a natural individual — colloquialisms and personal voice are assets. Here the targets are policy documents, learned-society books and standards, where colloquialisms and personal voice are deductions. The same "delete connectives" advice points in opposite directions under the two objectives.

## Documents

<table width="100%">
  <thead><tr><th>File</th><th>Content</th></tr></thead>
  <tbody>
    <tr><td><a href="SKILL.md">SKILL.md</a></td><td>the skill: positioning, rule table, workflow, limitations (Chinese)</td></tr>
    <tr><td><a href="references/baseline.md">references/baseline.md</a></td><td>eight statistics over 141 excerpts, extraction routing, reproduction (Chinese)</td></tr>
    <tr><td><a href="references/rule-audit.md">references/rule-audit.md</a></td><td>all 25 v0.1 rules audited: 17 deleted, 5 merged, 4 kept, 2 unverified (Chinese)</td></tr>
    <tr><td><a href="references/ai-tells.md">references/ai-tells.md</a></td><td>before/after table by rule id, plus seven "do not change" cases (Chinese)</td></tr>
    <tr><td><a href="eval/results.md">eval/results.md</a></td><td>evaluation report: density, false positives, sweep, misses, blind ratings (Chinese)</td></tr>
    <tr><td><a href="examples/after.md">examples/after.md</a></td><td>20 real drafts and rewrites, numbers untouched (Chinese)</td></tr>
    <tr><td><a href="references/terms.json">references/terms.json</a></td><td>22 terms; 16 definitions quoted from GB 28050—2025 / GB 13432—2013</td></tr>
    <tr><td><a href="CONTRIBUTORS.md">CONTRIBUTORS.md</a></td><td>authors and credits: who decided what, how attribution is recorded</td></tr>
    <tr><td><a href="THIRD_PARTY_NOTICES.md">THIRD_PARTY_NOTICES.md</a></td><td>corpus sources and copyright</td></tr>
    <tr><td colspan="2" width="1200">All documents are in Chinese except README.en.md and THIRD_PARTY_NOTICES.md.</td></tr>
  </tbody>
</table>

## Authors and credits

Initiated and signed off by **ChemistryBus**; corpus extraction, rule implementation, evaluation and
first drafts by **DSH (DeepSeek Harness)**. Every commit carries
`Co-Authored-By: DSH (DeepSeek Harness)`, which renders as a second avatar in the commit list.
GitHub's Contributors panel counts commit authors with linked accounts; DSH has none, and none was
invented — the division of work and the audit command are in [`CONTRIBUTORS.md`](CONTRIBUTORS.md).

## Licence

Code is MIT, see [`LICENSE`](LICENSE). Corpus excerpts are outside the MIT grant; sources and copyright are listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
