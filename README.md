# GEO Auditor · AI Search Content Quality Detector

Not just SEO for AI — detects "AI voice" patterns, built for Agent-driven workflows, works across any language.

## Three Differentiators

### 1. Anti-AI Voice Detection

Every GEO tool helps you please AI. We go the other way — detecting whether your content sounds like a machine wrote it:

- Identifies AI template phrases in English AND Chinese ("furthermore", "in conclusion", "值得注意的是", "综上所述")
- 14-dimension scoring includes a dedicated "Anti-AI Voice" check
- **Human-readable + AI-citable = real GEO**

### 2. Agent-Driven · Self-Evolving

Not just a web tool. CLI version with JSON output means any AI Agent can use it:

```bash
# Hermes / Claude Code / any Agent
python3 geo_auditor.py "your content here"
python3 geo_auditor.py --file article.md --json  # JSON for programmatic parsing
```

Agent workflow loop:

> Detect → Find low dimensions → Auto-rewrite → Re-detect → Compare scores → Learn patterns → Avoid mistakes next time

### 3. Language-Agnostic · Zero Config

No preset industry keywords. No hardcoded jargon. It auto-extracts topic phrases from your content and measures density — works in English, Chinese, or mixed. Just paste and go.

## 14-Dimension Detection

| # | Dimension | Max | What It Checks |
|---|-----------|-----|----------------|
| 1 | Conclusion-First | 10 | Does the first paragraph give a direct answer? |
| 2 | Data Anchors | 10 | Specific numbers + verifiable sources |
| 3 | Structure | 8 | Numbered steps, bullet points |
| 4 | Comparison | 8 | A vs B, contrasts, numeric comparisons |
| 5 | FAQ Module | 8 | Q&A format sections |
| 6 | Title Quality | 8 | Search intent keywords + numbers |
| 7 | Keyword Density | 8 | Auto-detected topic phrases ≥3 appearances |
| 8 | Paragraph Length | 6 | Optimal length for AI ingestion |
| 9 | Sources | 6 | Traceable citations and references |
| 10 | CTA | 4 | End-of-content call to action |
| 11 | Entity Info | 8 | Location, organization, time anchors |
| 12 | EEAT | 8 | Experience, Expertise, Authority, Trust |
| 13 | Semantic Match | 4 | Title-content intent alignment |
| 14 | Anti-AI Voice | 4 | Zero AI-template words |

**100 points total. 85+ = S-grade content AI engines will likely cite.**

## Two Ways to Use

### Web Version

Open `geo-auditor.html` in any browser. Paste content → 14-dimension check → results + suggestions. History stored locally (localStorage), nothing sent to any server.

### CLI (Agent-Friendly)

```bash
# Direct text input
python3 geo_auditor.py "your content text..."

# From file
python3 geo_auditor.py --file article.md

# JSON output for Agent parsing
python3 geo_auditor.py --file article.md --json

# Pipe from stdin
echo "content" | python3 geo_auditor.py --stdin --json
```

## Install

```bash
git clone https://github.com/liangjia-tech/geo-auditor.git
cd geo-auditor

# Web: open geo-auditor.html in browser

# CLI: Python 3.7+, zero dependencies
python3 geo_auditor.py --help
```

## How It Works with AI Agents

This tool is designed for "conversation as interface" — it's not an isolated checker, but a step in an Agent workflow:

1. Agent generates draft → auto-runs CLI detection
2. Score < 80 → Agent rewrites low dimensions → re-detects
3. Compares before/after → records improvement patterns
4. Next time generating content, Agent avoids known issues from patterns

**The tool itself evolves — the detector you use a month from now judges differently than today.**

## License

MIT

## Author

良佳科技 · [zhibi.xyz](https://zhibi.xyz)
