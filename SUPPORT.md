# Support

## Getting Help

**Best way:** [Open an issue](https://github.com/qjjy2004/geo-auditor/issues) — tag it with `question`.

**Quick questions:** [Discussions](https://github.com/qjjy2004/geo-auditor/discussions) (if enabled) or email dev@zhibi.xyz.

## Common Issues

Before opening an issue, check:

1. **Python version:** `python3 --version` — must be 3.7+
2. **Zero dependencies:** GEO Auditor uses only Python stdlib. No `pip install` needed.
3. **Encoding:** On Windows, use `chcp 65001` before running for proper CJK/emoji support.
4. **File not found:** Use absolute paths or run from the project directory.

## FAQ

**Q: Does GEO Auditor send my content anywhere?**
A: No. It's a local Python script with zero network calls. Everything stays on your machine.

**Q: What's the difference between CLI and Web versions?**
A: Same detection engine. Web (`geo-auditor.html`) works in-browser. CLI (`geo_auditor.py`) adds evolution tracking, Agent training, and config injection.

**Q: How is this different from GPTZero / Originality.ai?**
A: GEO Auditor measures **AI search citation quality** (GEO), not AI text probability. Content that scores low on Anti-AI Voice but high on structure and data anchors is optimized for AI search — that's the design intent.
