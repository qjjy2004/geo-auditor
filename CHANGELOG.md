# GEO Auditor — Version History

## v0.6.6 (2026-06-22) — Density Scoring

**Problem**: Long articles automatically scored high due to absolute hit counting. A 20KB article scored 74 A (higher than 10KB Simon Willison blog at 57 B).

**Fix**: Replaced absolute thresholds with density-based scoring (hits per 100 sentences). Diminishing returns curve:
- <15 sentences: conservative absolute fallback (1 hit = 25%, 2 = 50%, 3 = 75%, 4+ = full)
- ≥15 sentences: density curve with 65% benchmark at "B-grade" reference level

**Dimensions affected**: Structure, Comparison, FAQ Module, Sources, CTA.

**Calibration**: Benchmarks set using Simon Willison's blog (simonwillison.net, Dec 2024) as B-grade reference (~65% of max score).

**Results** (7-article test suite):
| Article | v0.6.5 | v0.6.6 | Change |
|---------|--------|--------|--------|
| Ticketmaster (20KB) | 74 A | 54 B | -20 |
| Simon Willison (10KB) | 57 B | 53 B | -4 |
| TypeScript README (3.5KB) | 55 B | 41 C | -14 |
| AI filler (1.4KB) | 43 C | 43 C | 0 |

**Also**: Added `weeks` to data units list. Added 4 test samples + 7 JSON results + calibration report.

---

## v0.6.5 (2026-06-22) — DeepSeek Pro Audit: 13 Bug Fixes

External audit by DeepSeek Pro found 8 bugs (2 HIGH, 2 MEDIUM, 4 LOW). Second pass found 5 more. All fixed.

### HIGH
- **Bug 1: Detection learning path broken.** `log_detection()` wrote key `'dims'` (dict format). `evolve_detector()` read key `'dimensions'` (list format). Detection-based evolution was dead code since v0.6.3. Unified to `'dimensions': [{n, s, m}, ...]`.
- **Bug 2: Python GEO patterns missing `re.IGNORECASE`/`re.MULTILINE`.** Python and JS versions scored English content differently. JS had `/gi` flags, Python did not. "First/Second/Third" matched JS but not Python. Added flags to: Structure, Comparison, FAQ, Title Quality, CTA, Sources, EEAT, Semantic Match (10 total).

### MEDIUM
- **Bug 3: Chinese burstiness broken.** `s.split()` returns ~1 "word" per Chinese sentence. Burstiness always ≈0. Now detects CJK (>30% hanzi) and uses character count instead.
- **Bug 4: `_safe_print` missing 5 emoji mappings.** `--evolve`/`--evolution-log` crashed on Windows cp936 terminals. Added 💤🔄🔧📝👀🔗 to emoji_map.

### LOW
- **Bug 5**: Added missing `dimension_principles` entries (Paragraph Length, Anti-AI Voice)
- **Bug 6/8**: Semantic Match icon changed from 🎯 to 🔗 (was duplicate with CTA)
- **Bug 7**: Removed redundant `import sys` in `_safe_print` except block

---

## v0.6.4 (2026-06-22) — GPT Audit Round 2

### Fixed
- **Global 5-rewrite gate removed**: `--evolve` with <5 rewrites now outputs `insufficient_data` (weight 1.0) instead of crashing with error.
- **Classification order**: Detection-sourced stale (`obs >= 10, missing >= 80%`) moved before rewrite-attempt gate. No longer blocked by `rw_attempts < 5`.
- **Field name mismatch**: 5 references to old `success_rate`/`avg_gain` → `beta_success_rate`/`avg_delta` in `_format_evolution()` and `generate_agent_prompt()`.
- **Dead parameter**: Removed unused `min_entries` from `evolve_detector()`.

---

## v0.6.3 (2026-06-22) — GPT Audit: Evolution Refactor

### Problems 2+3+4 (GPT audit)
- **Dual-source signals**: `evolve_detector()` now collects from BOTH detection logs (missing_rate, mean_ratio, variance) AND rewrite logs (improve_rate, avg_delta). Previously only used rewrite labels.
- **Sample size gates**: insufficient_data (<5 rewrites), proven (≥8, β≥80%, Δ≥5), fragile (≥8, high variance or 40-80%), stale (≥10 detections missing≥80% OR ≥8 rewrites β<20%). β-smoothed: (successes+1)/(attempts+2).
- **True weight multipliers**: Weights range 0.75-1.25. Score = Σ(ratio × weight × max_score). Outputs both `raw_pct` and `adaptive_pct`. No more force-to-60% or floor-at-70%.

### Weight persistence fix (GPT audit follow-up)
- `evolved_dim_weights` was generated AFTER snapshot write, causing `evolution_state.json` to always store empty weights. Same text scored identical across 3 rounds (29→29→29). Fixed: weights generated before snapshot, stored directly in state file.

---

## v0.6.2 (2026-06-22) — Evolution Feedback Loop

- `--evolve` produces `evolved_dim_weights` (stale=0.75, proven=1.05, fragile=1.15)
- `detect()` auto-loads weights from `~/.geo-auditor/evolution_state.json`
- `--evolution-log` shows active weight distribution + history
- `_safe_print()` handles Windows cp936 terminal emoji crashes

---

## v0.6.1 (2026-06-22) — Claude Code Audit: 22+10 Fixes

Two-round Claude Opus 4.7 audit. 19 critical fixes + 10 follow-up patches. CLI and HTML engines aligned as equal interfaces. Key improvements: emoji-safe printing, keyword scoring logic, encoding consistency.

---

## v0.6.0 (2026-06-22) — Initial Release Candidate

- 14-dimension detection engine (GEO + Anti-AI Voice)
- 6-signal Anti-AI Voice (banned words, RLHF, burstiness, diversity, openers, punctuation)
- Agent config injection (`--config`), compare mode (`--compare`), rewrite prompts
- HTML + CLI dual interface, bilingual (EN/CN)
- Evolution system: auto-log detection, evolution log, snapshots
- Built-in commercialization survey (3rd detection, localStorage, privacy-first)
