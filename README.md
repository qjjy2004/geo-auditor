# GEO Auditor · The Agent's Evolving Writing Brain

[![Version](https://img.shields.io/badge/version-v0.6.6-blue)](https://github.com/qjjy2004/geo-auditor/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Test](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml/badge.svg)](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](https://github.com/qjjy2004/geo-auditor)

**Not just a detector. A self-evolving system that trains your AI Agent to write better.**

---

## Why GEO Auditor

Most GEO tools are static checkers: paste → score → done. The score doesn't change the Agent's behavior.

GEO Auditor closes the loop:

```
Agent writes → Detector scores → Agent rewrites → Compare → 
Accumulate experience → Evolve → Generate Agent prompt → 
Agent now writes at higher baseline
```

**The detector itself gets smarter with every rewrite. Your Agent inherits that intelligence.**

---

## Two Ways to Use

### 1. As a Detector (CLI + Web)

```bash
python3 geo_auditor.py --file draft.md
python3 geo_auditor.py --file draft.md --json        # Agent API
python3 geo_auditor.py --compare v1.md v2.md          # Before/after
python3 geo_auditor.py --rewrite-prompt               # LLM rewrite suggestions
```

14 dimensions, 6-signal Anti-AI Voice, bilingual (EN+CN). Zero dependencies.

**CLI + Web — two interfaces, one detector.** The web version (`geo-auditor.html`) runs the full detection engine in-browser with the same 14-dimension + 6-signal Anti-AI Voice model. The CLI (`geo_auditor.py`) adds evolution tracking, Agent training, and config injection features that require filesystem access.

### 2. As an Agent Trainer (Evolution System)

```bash
# Every detection auto-logs to ~/.geo-auditor/evolution.jsonl
python3 geo_auditor.py --file article.md     # auto-logged

# Every comparison logs what improved
python3 geo_auditor.py --compare old.md new.md  # auto-logged

# After 5+ rewrites, evolve
python3 geo_auditor.py --evolve               # proven fixes + stale dims

# Export as Agent system prompt
python3 geo_auditor.py --agent-prompt > ~/.geo-auditor/writing_rules.txt
# → Load this as your Agent's system prompt. Done.
```

---

## Self-Evolution: Detector Learns, Agent Inherits

| Stage | What happens |
|-------|-------------|
| **Detect** | Every detection auto-logs to evolution journal |
| **Rewrite** | Every `--compare` logs per-dimension gains |
| **Evolve** | After 5+ rewrites: analyzes which fixes actually work |
| **Prompt** | Converts proven fixes into Agent-loadable writing rules |

**Example evolution output:**

```
PROVEN FIXES (auto-apply):
  Conclusion-First: 100% success, +8.0 avg gain
  → "Open with direct answer. Use 'Here's the thing:' or '说白了:'"

  EEAT: 100% success, +6.0 avg gain
  → "Mention years of experience + certification + third-party validation"

STALE (don't waste time):
  Anti-AI Voice: 0% success
  → This dimension is content-intrinsic. Focus elsewhere.
```

---

## 14-Dimension Detection + 6-Signal Anti-AI Voice

| Dimension | Max | Signal | Type |
|-----------|-----|--------|------|
| Conclusion-First | 10 | A. Forbidden Patterns | Structural |
| Data Anchors | 10 | B. Banned Vocabulary (50+ words) | Lexical |
| Structure | 8 | C. RLHF Voice (7 patterns) | Register |
| Comparison | 8 | D. Burstiness + Diversity | Rhythm |
| FAQ Module | 8 | E. Opener Repetition | Structural |
| Title Quality | 8 | F. Punctuation Fingerprints | Orthographic |
| Keyword Density | 8 | | |
| Paragraph Length | 6 | | |
| Sources | 6 | | |
| CTA | 4 | | |
| Entity Info | 8 | | |
| EEAT | 8 | | |
| Semantic Match | 4 | | |
| Anti-AI Voice | 4 | | |

**GEO structures (comparisons, FAQ, numbered lists) are boosted — not penalized as AI voice. Design boundary documented in code.**

---

## Design Philosophy

- **Zero API dependency** — pure Python rules engine, works offline
- **Language-agnostic** — auto-detects CN/EN, extracts topic phrases in both
- **Agent-first** — JSON output, config injection, evolution pipeline, Agent prompt export
- **Research-backed** — Anti-AI Voice signals validated against GPTZero, GLTR, Binoculars (ICML 2024), arXiv 2605.19516

---

## Install

```bash
git clone https://github.com/qjjy2004/geo-auditor.git
cd geo-auditor

# CLI: Python 3.7+, zero dependencies
python3 geo_auditor.py --help

# Web: open geo-auditor.html in browser
```

## Quick Start

```bash
# Score a file
python3 geo_auditor.py --file draft.md

# Score text directly
python3 geo_auditor.py "Your content here" --json

# Compare before/after (this also trains the evolution engine)
python3 geo_auditor.py --compare v1.md v2.md

# Export writing rules for your AI Agent
python3 geo_auditor.py --agent-prompt
```

## FAQ

**Is my content sent anywhere?** No. Zero network calls. Everything runs locally.

**What's different from GPTZero / Originality.ai?** They detect AI-generated text. GEO Auditor measures **AI search citation quality** — content that scores well is optimized for being cited by AI search engines (Perplexity, ChatGPT Search, Google AI Overviews, Claude).

**Why zero dependencies?** You should be able to run it anywhere without `pip install`. Python 3.7+ stdlib only.

## Roadmap

- `v0.7` — Multi-file batch analysis
- `v0.8` — Browser extension (one-click audit for any webpage)
- `v0.9` — Markdown export with inline annotations
- `v1.0` — Stable API + documented plugin system

## License

MIT · zhibi · [zhibi.xyz](https://zhibi.xyz)
