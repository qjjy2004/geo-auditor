Review GEO Auditor v0.6.1 — lightweight pass only.

Don't read every line. Check these 5 things:

1. Does main() have any naked print() that should be _safe_print()? Grep for `print(` in main(), ignore stderr lines.

2. Do all file opens use encoding='utf-8'? Grep `open(` in geo_auditor.py.

3. Is there any json.loads() without try/except? Grep `json.loads` — all 3 call sites should be guarded.

4. Run once: `python3 geo_auditor.py "test content" --json` — does it output valid JSON without crashing?

5. Quick scan: any remaining `return analysis` dead code, `from typing import Optional` unused imports, or version strings stuck at "0.6.0"?

That's it. Report only what's broken. No praise, no summary table.
