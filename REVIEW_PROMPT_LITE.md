Review this single-file Python tool. Lightweight pass — 5 checks only.

1. Does main() have any naked print() that should be _safe_print()? Grep for `print(` in main(), ignore stderr.

2. All open() calls have encoding='utf-8'?

3. All json.loads() wrapped in try/except? Three call sites: --history branch, evolve_detector, show_evolution_log.

4. Run `python3 geo_auditor.py "test" --json` — valid JSON output, no crash?

5. Clean code scan: dead `return analysis`, unused `Optional` import, version string stuck at old number?

Report only what's broken. No praise, no summary table.
