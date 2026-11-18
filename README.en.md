<p align="right"><a href="README.md"><img src="https://img.shields.io/badge/Chinese-README-2f81f7?style=flat-square" alt="Chinese"></a></p>

<h1 align="center">zh-nutrition-humanizer</h1>

<p align="center"><strong>Quality control for Chinese nutrition writing</strong></p>
<p align="center">Not "sound human": sound like a Chinese Nutrition Society textbook or a national dietary-guidance document.</p>
<p align="center"><strong>v1.0.1 — Repository Rename and docarbiter-style Docs</strong></p>

<p align="center">
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml"><img src="https://github.com/ChemistryBus/zh-nutrition-humanizer/actions/workflows/validate.yml/badge.svg" alt="validate"></a>
  <a href="https://github.com/ChemistryBus/zh-nutrition-humanizer/releases/tag/v1.0.1"><img src="https://img.shields.io/github/v/release/ChemistryBus/zh-nutrition-humanizer?color=blue&cacheSeconds=300" alt="release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
  <img src="https://img.shields.io/badge/python-3.10--3.12-blue" alt="Python 3.10-3.12">
  <img src="https://img.shields.io/badge/Agent-Skill-111111" alt="Agent Skill">
</p>

![overview](docs/assets/overview-en.svg)

## What it is

Most humanizers chase "sounds human". This one does not.

The target register is **institutional Chinese**: complete predicates, one claim per sentence, terminology per national standards, quantities with units, claims followed by evidence, no rhetorical flourishes. The repository carries a 53,000-character corpus baseline, and every rule threshold can be recomputed with the bundled scripts instead of being a matter of taste.

It addresses four recurring problems:

- LLM-written nutrition prose has the facts and the numbers but reads like a popular-science account;
- generic "de-AI" advice — delete connectives, split long sentences, add colloquialisms — **lowers the score** on textbook-register text;
- Chinese has no accepted AI-detection benchmark, so edits cannot be justified or audited;
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

### Try one check first

```bash
python3 scripts/check.py your_draft.md --explain
```

No draft at hand? Use the 20 real drafts shipped with the repo:

```bash
python3 scripts/check.py examples/before.md     # expect: 10.4 hits per 1,000 chars, exit code 1
python3 scripts/check.py examples/after.md      # expect: zero paragraph-level hits
```

## How it judges

Four families: 12 counted rules, 3 document-level style checks, 1 advisory. Every threshold comes from the corpus.

| Family | Catches | Institution | LLM draft | Verdict |
|---|---|---|---:|---:|---|
| L colloquial (7) | Chinese numerals with units, second person/imperatives, colloquial adjectives, metaphor nouns, "像/好比", "不是X而是Y", evaluative "更X" | 0–0.03 | 0.15–2.0 | fix on sight |
| T template (4) | "其机制在于", "而非", "亦", "宜采用" | 0–0.03 | 0.36–1.07 | fix above a density |
| C structure (1) | numeric ranges written with “至” | 0 | 4.52 | always ～ |
| S style (3) | mixed units, mixed terminology, missing English gloss | — | — | listed, not scored |

Full rule table in [`SKILL.md`](SKILL.md); evidence per rule in [`references/rule-audit.md`](references/rule-audit.md) (Chinese).

## Good fit / bad fit

**Good fit**

- pre-delivery checks on Chinese nutrition and sports-nutrition manuscripts;
- checking the manuscript version and the public-article version separately (same content, two registers);
- gatekeeping drafts written by someone else, or by a model.

**Bad fit**

- literary popular science and short-video copy — different register, the L family will over-fire;
- English-only drafts (use academic-humanizer);
- fact checking, citation authenticity, evidence-grade versus claim strength — all human work, out of scope.

## Evidence, not an "AI probability"

| Metric | Result | Target |
|---|---|---|
| Hit-density ratio | **74.5×** (institution 0.11 vs draft 8.40 per 1,000 chars) | ≥3× |
| Paragraph-level false positives | **4.0%** (2 of 50 authoritative paragraphs flagged) | <15% |
| Paragraph-level recall | **92%** (textbook 88% / popular 96%) | — |
| Threshold knee | 1–2 per 1,000 chars (J = +0.88); default 3 | — |

50 held-out authoritative paragraphs (17,800 chars, disjoint from the baseline pages) against 50 LLM paragraphs (24 popular, 26 textbook). Per-rule table, threshold sweep, ablation, missed cases and three blind-rating rounds are in [`eval/results.md`](eval/results.md) (Chinese).

Final blind round, on the exact repository text: popular-register rewrites **20 wins, 0 losses** (4.25 vs 2.45); textbook-register pairs are **16 ties** (4.90 vs 4.90). In other words: **a textbook-register AI draft can only be fixed at the style level, not the register level.** That conclusion came from the first round, where compressing sentences into telegraph style lost 18 head-to-head comparisons.

## Supported harnesses

| Environment | Usage |
|---|---|
| CLI / CI | `python3 scripts/check.py draft.md --threshold 3`; exit code 1 means over threshold |
| Claude Code | clone into `~/.claude/skills/`, reads `SKILL.md` |
| DSH / Cordis | clone into `~/.dsh/skills/`; `SKILL.md` already has frontmatter |
| Custom pipeline | `--json` output; `scripts/eval.py` works as a regression test |

## Install options

| Need | Do |
|---|---|
| check one draft | clone and run `scripts/check.py`, nothing installed |
| long-term skill | clone into the skills directory and pin a tag (`git checkout v1.0.1`) |
| CI gate | copy `scripts/check.py` into the repo, or add it as a submodule |

## FAQ

**Why not delete “此外／同时”?**
The corpus uses them 3.27 times per 1,000 characters; textbook-register LLM drafts use 3.57. Connectives do not discriminate. What should go is the restatement that follows “由此可见”.

**Will it ruin good prose?**
Sometimes. The 4.0% false-positive rate is the measured cost on authoritative text, which is why the tool only produces a list and a human decides. No rule touches a number.

**Can it tell whether a text was written by AI?**
No. It reports deviation from this corpus, not an AI probability. There is no accepted Chinese benchmark; anyone claiming one should show their positive and negative samples.

**Why only 200–400 character excerpts?**
Copyright. Every excerpt carries source, publisher and page number; nothing is reproduced in full and no source PDF is redistributed.

**Can I use it in another domain?**
The rule skeleton transfers; the thresholds do not. Rebuild the baseline with `scripts/stats.py` and `scripts/features.py`.

## Documents

| File | Content |
|---|---|
| [`SKILL.md`](SKILL.md) | the skill: positioning, rule table, workflow, limitations (Chinese) |
| [`references/baseline.md`](references/baseline.md) | eight statistics over 141 excerpts, extraction routing, reproduction (Chinese) |
| [`references/rule-audit.md`](references/rule-audit.md) | all 25 v0.1 rules audited: 17 deleted, 5 merged, 4 kept, 2 unverified (Chinese) |
| [`references/ai-tells.md`](references/ai-tells.md) | before/after table by rule id, plus seven "do not change" cases (Chinese) |
| [`eval/results.md`](eval/results.md) | evaluation report: density, false positives, sweep, misses, blind ratings (Chinese) |
| [`examples/after.md`](examples/after.md) | 20 real drafts and rewrites, numbers untouched (Chinese) |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | corpus sources and copyright |

## Licence

Code is MIT, see [`LICENSE`](LICENSE). Corpus excerpts are outside the MIT grant; sources and copyright are listed in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
