# GEO Auditor Test Samples

Four English articles used for calibration and regression testing.

| Sample | Source | Chars | Grade | Purpose |
|--------|--------|-------|-------|---------|
| simon_willison_blog.txt | simonwillison.net (Dec 2024) | 10K | B (53) | High-quality human writing benchmark |
| typescript_readme.txt | GitHub: microsoft/TypeScript | 3.5K | C (41) | Technical documentation, medium density |
| ai_generated_filler.txt | Synthetic | 1.4K | C (43) | AI-generated with formulaic Q&A, tests Anti-AI Voice |
| ticketmaster_reverse_engineering.txt | conduition.io (Feb 2024) | 20K | B (54) | Long-form tech article, tests length normalization |

## Scoring calibration

Density-based dimensions use Simon's blog as the "B-grade" benchmark (~65% score).
Short texts (<15 sentences) use conservative absolute fallback.

Run: `python3 geo_auditor.py -f test_samples/<file>.txt --json`
