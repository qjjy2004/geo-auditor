# GEO Auditor · AI Search Content Quality Detector

**14-dimension detection + research-backed Anti-AI Voice + Agent-driven self-evolution**

---

## Design Philosophy: GEO ≠ AI Voice

Most GEO tools tell you to "write like AI likes it" — structured, templated, formulaic. That works for AI search engines but reads like a robot to humans.

**GEO Auditor solves the contradiction:**

| GEO wants | Anti-AI Voice checks | Conflict? |
|-----------|---------------------|-----------|
| Comparison structure ("A vs B") | ✅ GEO bonus only — not penalized as AI voice | **No** |
| Conclusion-first opening | ✅ GEO bonus only — not flagged | **No** |
| Numbered lists, FAQ format | ✅ GEO bonus only | **No** |
| Banned vocabulary (delve, robust, foster...) | ❌ Research-backed word list — penalized | — |
| RLHF voice ("Let me walk you through...") | — No GEO benefit | ❌ RLHF artifact — penalized | — |
| Punctuation fingerprints (em dashes, curly quotes) | — No GEO benefit | ❌ Statistical AI tell — penalized | — |
| Sentence burstiness (uniform length) | — No GEO benefit | ❌ Metronomic rhythm — penalized | — |

**The insight:** GEO-optimized content doesn't have to sound like AI. Structure for machines, voice for humans. GEO Auditor is the first tool that checks both simultaneously — without penalizing one for the other.

---

## 6-Signal Anti-AI Voice Detection

Backed by research from GPTZero, GLTR, HC3, Binoculars (ICML 2024), and the ai-check taxonomy (50+ papers):

| Signal | What It Detects | Source |
|--------|----------------|--------|
| **A. Forbidden Patterns** | "not X but Y", "isn't X it's Y" structural templates | Research-validated |
| **B. Banned Vocabulary** | 50+ words: delve, leverage, robust, foster, pivotal, multifaceted... | GPTZero + academic consensus |
| **C. RLHF Voice** | "Let me walk you through", "Great question!", "On one hand...on the other" | arXiv 2605.19516 |
| **D. Burstiness + Diversity** | Sentence length variance (SD < 5 = AI), declarative sentence ratio | GPTZero + stylometry |
| **E. Opener Repetition** | Paragraphs starting identically | Stylometric feature |
| **F. Punctuation Fingerprints** | Em dash density (>2/500 chars), semicolons, curly quotes | 2024-2026 research |

---

## Agent-Driven · Self-Evolving

```bash
# Agent injects industry knowledge via config
python3 geo_auditor.py --file draft.md --config industry.json --json

# Compare before/after rewrite
python3 geo_auditor.py --compare v1.md v2.md

# Learn from multiple checks — generate writing strategy
cat results.jsonl | python3 geo_auditor.py --learn
```

Agent workflow: Detect → Get structured hints → Rewrite → Compare → Accumulate → Learn → Adapt template

---

## 14-Dimension Detection

| # | Dimension | Max | What It Checks |
|---|-----------|-----|----------------|
| 1 | Conclusion-First | 10 | Direct answer in first paragraph? |
| 2 | Data Anchors | 10 | Specific numbers + verifiable sources |
| 3 | Structure | 8 | Numbered steps, bullet points |
| 4 | Comparison | 8 | A vs B, numeric contrasts |
| 5 | FAQ Module | 8 | Q&A format sections |
| 6 | Title Quality | 8 | Search intent + number in title |
| 7 | Keyword Density | 8 | Auto-extracted topic phrases ≥3 appearances |
| 8 | Paragraph Length | 6 | Optimal length for AI ingestion |
| 9 | Sources | 6 | Traceable citations |
| 10 | CTA | 4 | End-of-content call to action |
| 11 | Entity Info | 8 | Location, organization, time anchors |
| 12 | EEAT | 8 | Experience, Expertise, Authority, Trust |
| 13 | Semantic Match | 4 | Title-content intent alignment |
| 14 | Anti-AI Voice | 4 | 6-signal detection (see above) |

**100 points total. 85+ = S-grade content AI engines will likely cite.**

---

## Install

```bash
git clone https://github.com/liangjia-tech/geo-auditor.git
cd geo-auditor

# Web: open geo-auditor.html in browser (zero-dependency, local only)

# CLI: Python 3.7+, zero dependencies
python3 geo_auditor.py --help
```

## License

MIT

## Author

良佳科技 · [zhibi.xyz](https://zhibi.xyz)
