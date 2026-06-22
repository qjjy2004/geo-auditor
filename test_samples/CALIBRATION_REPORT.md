# GEO Auditor v0.6.6 — Density Scoring Calibration Report

**Date**: 2026-06-22
**Method**: 7 English articles of varying quality, length, and style scored with density-based v0.6.6 engine.

---

## Summary

```
  HIGH (B): ██████████████████████████████████████████████████ 53-54
MEDIUM (C): ████████████████████████████████                   41-43
   LOW (C): ████████████████████████████                       36-38
```

Score range: **36-54** across 7 articles. No article scored above 54 or below 36.
Anti-AI Voice correctly identified AI-generated content (1/4) vs human writing (3-4/4).

---

## Detailed Results

### 1. Simon Willison Blog — 53 B (high-quality human)
- Source: simonwillison.net, Dec 2024
- 9,955 chars, 86 sentences
- Strengths: Anti-AI Voice 4/4, Data Anchors 8/10, Sources 6/6
- Weakness: Structure 4/8 (narrative style), Title 1/8 (no keyword title)

### 2. Ticketmaster Reverse Engineering — 54 B (long-form tech)
- Source: conduition.io, Feb 2024
- 19,964 chars, 204 sentences
- Strengths: Data Anchors 10/10, Entity Info 8/8, Structure 6/8
- Weakness: Title 1/8, FAQ 1/8, Comparison 2/8

### 3. Microfeatures Blog — 42 C (tech blog, flagged AI vocabulary)
- Source: danilafe.com
- 18,306 chars, 164 sentences
- Strengths: Sources 6/6, Keyword Density 8/8
- Weakness: Anti-AI Voice 1/4 (17 AI vocabulary hits), Structure 2/8
- Note: Real human writer using AI-common vocabulary patterns.

### 4. AI-Generated Filler — 43 C (synthetic)
- 1,420 chars, 15 sentences
- Strengths: FAQ 8/8 (2 Q&A pairs), Title 6/8, Keyword Density 6/8
- Weakness: Anti-AI Voice 1/4 (17 AI hits), Data Anchors 2/10
- Note: Formulaic Q&A structure correctly flagged by Anti-AI Voice.

### 5. TypeScript README — 41 C (technical documentation)
- Source: GitHub microsoft/TypeScript
- 3,471 chars, 84 sentences
- Strengths: Conclusion-First 6/10, Paragraph Length 4/6
- Weakness: Keyword Density 2/8, Sources 1/6, CTA 1/4

### 6. SEO Spam — 38 C (keyword-stuffed human spam)
- Synthetic: "Best Seismic Bracing Solutions 2026"
- 1,250 chars, 28 sentences
- Strengths: Keyword Density 8/8, Title 5/8, Anti-AI Voice 3/4 (human)
- Weakness: Data Anchors 0/10, Structure 1/8

### 7. Scott Alexander (Slate Star Codex) — 36 C (literary essay)
- Source: slatestarcodex.com, 2020
- 13,109 chars, 105 sentences
- Strengths: Anti-AI Voice 4/4 (zero AI signals), Entity Info 6/8
- Weakness: Structure 3/8, Data Anchors 4/10, Keyword Density 2/8, Title 1/8
- Note: Brilliant writer, but not writing for GEO. Lowest score = least AI-search-optimized.

---

## Key Findings

### Length inflation eliminated
v0.6.5 (absolute counts): Ticketmaster 74 A, TypeScript README 55 B
v0.6.6 (density-based): Ticketmaster 54 B, TypeScript README 41 C
→ 20KB article dropped 20 points. No automatic "long = good" bias.

### GEO ≠ writing quality
Scott Alexander (best writer) scored lowest (36). SEO spam scored higher (38).
The tool measures GEO optimization, not prose quality.

### Anti-AI Voice discriminates well
- Human articles: 3-4/4
- AI-generated: 1/4
- False positive: Microfeatures blog (real human, 1/4) — uses AI-common vocabulary
- False negative: None observed

### Density benchmarks
Calibrated with Simon Willison's blog as "B-grade reference" (~65% of max):
- Structure: bench=12 hits/100 sent
- Comparison: bench=6 hits/100 sent
- FAQ: bench=8 hits/100 sent
- Sources: bench=18 hits/100 sent
- CTA: bench=12 hits/100 sent
- Short text threshold: <15 sentences uses conservative absolute fallback

---

## Raw JSON Results
Full per-article JSON outputs are saved alongside this report:
- `simon_willison_blog_result.json`
- `ticketmaster_article_result.json`
- `en_microfeatures_result.json`
- `en_low_result.json` (AI filler)
- `en_medium_result.json` (TypeScript README)
- `en_seo_spam_result.json`
- `en_slate_result.json` (Scott Alexander)
