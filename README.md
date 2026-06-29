# GEO Auditor · Headlights, Not Rearview Mirror

[![Version](https://img.shields.io/badge/version-v0.7.0-blue)](https://github.com/qjjy2004/geo-auditor/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Test](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml/badge.svg)](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](https://github.com/qjjy2004/geo-auditor)

**Every GEO tool tells you what already happened. GEO Auditor tells you what will happen — before you hit publish.**

---

## The Difference: Rearview Mirror vs Headlights

All GEO monitoring tools work the same way:

```
Define prompts → Run AI search engines → Record: "Was your brand mentioned?"
```

They answer one question: **"Did AI mention my brand?"** — after the fact. Rearview mirrors. They record; they don't need to evolve.

**GEO Auditor answers a different question: "Will AI cite my content?"** — before you publish. It's a headlight. And it gets smarter with every rewrite.

| | Monitoring Tools (Semrush GEO, Otterly, KIME) | GEO Auditor |
|---|---|---|
| **When** | After publishing | Before publishing |
| **What it checks** | "Was my brand in the AI answer?" | "Can AI extract and cite this content?" |
| **Analogy** | Rearview mirror | Headlight |
| **Evolution** | None (just records) | **Core feature** — learns from every rewrite |

---

## v0.7.0: Self-Evolving Content Engine

**Detect → Rewrite → Compare → Learn → Evolve.** Five steps, one closed loop.

```
1. Paste your content → 14-dimension score + AI voice audit
2. One-click AI rewrite (stays on-page) → see what changed
3. Auto-compare old vs new → per-dimension gains highlighted
4. Save → evolution engine updates weights
5. After 8+ rewrites: proven fixes surfaced, stale dimensions retired
```

The detector adapts to what you actually improve — not what a generic algorithm thinks matters.

**New in v0.7.0:**
- **AI Rewrite** — one click, safe rewrite with hard constraints (no fabrication, no keyword stuffing, preserves existing structure)
- **Auto-Compare** — saves trigger automatic before/after comparison; no manual steps
- **Adaptive Scoring** — raw score and evolved score side by side; evolution based on raw score delta only
- **Import/Export** — share evolution data across browsers or team members
- **Bilingual UI Toggle** — 中文/English with one click; auto-detects content language
- **JS Evolution Engine** — works fully in-browser (web version); no server needed

---

## Two Interfaces, One Engine

| Interface | File | What it does |
|-----------|------|-------------|
| **Web** | `geo-auditor.html` | Full engine in-browser: detect, AI rewrite, compare, evolve. Zero server. |
| **CLI** | `geo_auditor.py` | Adds Agent training, config injection, batch processing |

14 dimensions, 6-signal Anti-AI Voice, bilingual (EN + CN), zero dependencies. Both interfaces use the same detection engine.

### CLI Quick Start

```bash
# Score a file
python3 geo_auditor.py --file draft.md

# Agent API (JSON output)
python3 geo_auditor.py --file draft.md --json

# Compare before/after (feeds evolution)
python3 geo_auditor.py --compare v1.md v2.md

# Generate rewrite prompt for LLM
python3 geo_auditor.py --rewrite-prompt

# After 8+ rewrites: evolve
python3 geo_auditor.py --evolve

# Export writing rules for your AI Agent
python3 geo_auditor.py --agent-prompt > ~/.geo-auditor/writing_rules.txt
```

### Agent Training Pipeline

```
Agent writes → Detector scores → Agent rewrites → Compare →
Accumulate experience (≥8 rewrites) → Evolve → Export Agent prompt →
Agent now writes at higher baseline
```

Every detection auto-logs to `~/.geo-auditor/evolution.jsonl`. Every comparison logs per-dimension gains. The evolution engine analyzes what fixes actually work across all your rewrites.

**Example evolution output (after 8+ rewrites):**

```
PROVEN FIXES (auto-apply):
  Conclusion-First: β=0.89, +8.0 avg gain
  → "Open with direct answer. Use 'Here's the thing:' or '说白了:'"

  EEAT: β=0.83, +6.0 avg gain
  → "Mention years of experience + certification + third-party validation"

FRAGILE (works sometimes, check context):
  Keyword Density: β=0.55, variance=12.3
  → Results vary by content length and topic

STALE (don't waste time):
  Anti-AI Voice: β=0.17
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

**GEO structures (comparisons, FAQ, numbered lists) are boosted — not penalized as AI voice.** Design boundary documented in code.

---

## Design Philosophy

- **Zero API dependency** — pure rules engine, works offline, no network calls
- **Language-agnostic** — auto-detects CN/EN, extracts topic phrases in both
- **Agent-first** — JSON output, config injection, evolution pipeline, Agent prompt export
- **Research-backed** — Anti-AI Voice signals validated against GPTZero, GLTR, Binoculars (ICML 2024), arXiv 2605.19516
- **Safe AI rewrite** — hard constraints prevent fabrication, keyword stuffing, structure destruction

---

## Install

```bash
git clone https://github.com/qjjy2004/geo-auditor.git
cd geo-auditor

# CLI: Python 3.7+, zero dependencies
python3 geo_auditor.py --help

# Web: open geo-auditor.html in any browser
# Live demo: https://zhibi.xyz/geo-auditor.html
```

---

## FAQ

**Is my content sent anywhere?** No. Zero network calls. Everything runs locally. The web version stores evolution data in your browser's localStorage — nothing leaves your machine.

**What's different from GPTZero / Originality.ai?** They detect AI-generated text. GEO Auditor measures **AI search citation quality** — content that scores well is optimized for being cited by AI search engines (Perplexity, ChatGPT Search, Google AI Overviews, Claude).

**How is this different from Semrush GEO / Otterly / KIME?** They monitor whether your brand appears in AI answers **after** you publish. GEO Auditor checks whether your content is citable **before** you publish. Rearview mirror vs headlight. Also: GEO Auditor evolves — it learns which writing techniques actually improve scores for your specific content.

**Why zero dependencies?** You should be able to run it anywhere without `pip install`. Python 3.7+ stdlib only.

**Who is this for?** Content teams, SEO agencies, and AI Agent builders who want content that AI search engines actually cite. If you publish content and care whether ChatGPT/Perplexity/Google AI Overviews reference it, this is your pre-flight check.

---

## Roadmap

- `v0.8` — Multi-file batch analysis + Markdown export with inline annotations
- `v0.9` — Browser extension (one-click audit for any webpage while browsing)
- `v1.0` — Stable API + documented plugin system for custom dimensions

---

## License

MIT · [zhibi.xyz](https://zhibi.xyz)
