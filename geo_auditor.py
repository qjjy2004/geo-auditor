#!/usr/bin/env python3
"""
GEO Auditor — AI Search Content Quality Detector
14-dimension check + anti-AI-voice + self-evolving via Agent

Usage:
  python3 geo_auditor.py "your content text"
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json
  echo "content" | python3 geo_auditor.py --stdin

Agent integration:
  python3 geo_auditor.py --file output.md --json 2>/dev/null
  # Returns JSON: {pct, grade, total, maxTotal, dimensions: [...], suggestions: [...]}
"""

import re
import sys
import json
import argparse
from collections import Counter
from typing import Optional

VERSION = "1.1.0"

# ════════════════════════════════════
# Universal entity patterns (not industry-specific)
# ════════════════════════════════════
ENTITY_PATTERNS = [
    # Location names
    re.compile(r'province|city|county|district|state|China|US|UK|Japan|Korea|India|'
               r'Beijing|Shanghai|Shenzhen|Guangzhou|Hangzhou|Nanjing|Tokyo|London|NY|'
               r'省|市|区|县|江苏|浙江|广东|北京|上海|深圳|南京|杭州|广州'),
    # Organization types
    re.compile(r'company|corp|inc|ltd|group|university|institute|hospital|school|agency|'
               r'公司|集团|大学|学院|医院|学校|机构|部门|单位|工厂|实验室'),
    # Time / era anchors
    re.compile(r'\d{4}年|\d{4}-\d{2}|since\s+\d{4}|for\s+\d+\s+years|'
               r'做了?\d+年|干了?\d+年|\d+年.*经验'),
]

# ════════════════════════════════════
# AI-voice detection patterns
# ════════════════════════════════════
AI_FORBIDDEN = [
    re.compile(r'not.{0,15}but'),
    re.compile(r"isn't.{0,10}it's"),
    re.compile(r'not only.{0,10}but also'),
    re.compile(r'it.{0,10}goes without saying'),
    re.compile(r'不是.{0,15}而是'),
    re.compile(r'并非.{0,10}而是'),
    re.compile(r'不仅是.{0,10}更是'),
]

AI_WASTE = [
    # English AI tells
    'furthermore', 'moreover', 'consequently', 'nevertheless', 'in conclusion',
    'it is worth noting', 'it should be noted', 'as previously mentioned',
    'in summary', 'to summarize', 'as we can see', 'without a doubt',
    'undeniably', 'it is important to', 'one might argue',
    # Chinese AI tells
    '此外', '而且', '因此', '然而', '综上所述', '可以说', '在某种程度上',
    '往往', '一定的', '值得注意的是', '更为关键的是', '总而言之',
    '众所周知', '不可否认', '毋庸置疑', '总的来看', '总的来讲',
]


def count_pattern(text: str, pattern) -> int:
    """Count regex matches"""
    return len(re.findall(pattern, text))


def count_keyword(text: str, keyword: str) -> int:
    """Count keyword occurrences (escape regex special chars)"""
    escaped = re.escape(keyword)
    return len(re.findall(escaped, text))


def extract_topic_phrases(text: str, top_n: int = 5) -> list:
    """Auto-extract topic bigrams/trigrams (handles both EN + CN)"""
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
    words = clean.split()

    # If mainly Chinese (CJK > 40%), use character-level n-grams
    cjk_chars = sum(1 for c in clean if '\u4e00' <= c <= '\u9fff')
    total_chars = len(clean.replace(' ', ''))
    is_cn = total_chars > 0 and cjk_chars / total_chars > 0.4

    stops = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
             'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
             'and', 'or', 'but', 'not', 'this', 'that', 'it', 'as',
             '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
             '一', '个', '上', '也', '很', '到', '说', '要', '去', '你',
             '会', '着', '没有', '看', '好', '自己', '这', '他', '她', '们',
             '还', '把', '被', '让', '给', '从', '向', '对', '与', '为',
             '吗', '呢', '吧', '啊', '哦', '嗯', '么', '那', '什么', '怎么'}

    candidates = []

    if is_cn and len(clean) >= 8:
        # Chinese: extract 2-4 char substrings that appear 2+ times
        cn_text = ''.join(c for c in clean if '\u4e00' <= c <= '\u9fff')
        for wlen in [4, 3, 2]:
            seen = {}
            for i in range(len(cn_text) - wlen + 1):
                chunk = cn_text[i:i+wlen]
                if chunk not in stops:
                    seen[chunk] = seen.get(chunk, 0) + 1
            for chunk, count in seen.items():
                if count >= 2:
                    candidates.append((chunk, count))
    else:
        # English: bigram extraction
        if len(words) >= 3:
            for i in range(len(words) - 1):
                bigram = f'{words[i]} {words[i+1]}'
                if words[i] not in stops and words[i+1] not in stops:
                    if len(bigram.replace(' ', '')) >= 4:
                        candidates.append((bigram, 1))
            # Count
            from collections import Counter
            counts = Counter()
            for phrase, _ in candidates:
                counts[phrase] += 1
            candidates = [(p, c) for p, c in counts.items() if c >= 2]

    candidates.sort(key=lambda x: -x[1])
    return [phrase for phrase, count in candidates[:top_n]]


def detect(text: str) -> dict:
    """Core detection engine — 14 dimensions, 100 points"""
    lines = text.split('\n')
    title = lines[0] if len(lines[0]) < 80 else ''
    body = '\n'.join(lines[1:]) if title else text
    ft = text  # full text

    dims = []
    total = 0
    max_total = 100

    # 1. Conclusion-First 10
    first_para = (body.strip().split('\n')[0] if body.strip() else '')[:120]
    has_conclusion = bool(re.search(
        r'answer|conclusion|core|key|bottom.line|the.point|simply.put|heres.the.thing|'
        r'答案|结论|核心|关键|说白了|说真的|直接|就是|一句话',
        first_para)) and len(first_para) >= 25
    cf = 10 if has_conclusion else (6 if len(first_para) >= 20 else 2)
    cf_d = ('Clear opening — AI can extract immediately'
            if cf >= 9 else ('Has intro but lead with answer next time'
            if cf >= 5 else 'Missing conclusion — AI prefers answer-first'))
    dims.append({'n': 'Conclusion-First', 's': cf, 'm': 10, 'd': cf_d, 'icon': '📍'})
    total += cf

    # 2. Data Anchors 10
    nm = count_pattern(ft, r'\d+\.?\d*\s*(?:billion|million|thousand|hundred|'
                       r'%|USD|EUR|CNY|¥|\$|€|kg|km|mm|cm|m|t|℃|°F|'
                       r'years|months|days|hours|times|users|people|'
                       r'亿|万|千|百|元|套|个|次|年|月|日|条|家|N·m|kN|MPa|吨)')
    sm = count_pattern(ft, r'reference|source|citation|standard|spec|according.to|'
                       r'reported.by|study|survey|research|data.from|'
                       r'参考|来源|标准|规范|据.*显示|第.*条')
    if nm >= 4 and sm >= 2: da = 10
    elif nm >= 3: da = 7
    elif nm >= 2: da = 5
    elif nm >= 1: da = 2
    else: da = 0
    da_d = (f'{nm} data pts + {sm} refs. Excellent'
            if da >= 9 else (f'{nm} data pts. Decent'
            if da >= 5 else 'Add specific numbers and sources'))
    dims.append({'n': 'Data Anchors', 's': da, 'm': 10, 'd': da_d, 'icon': '📊'})
    total += da

    # 3. Structure / Steps 8
    st = count_pattern(body, r'first|second|third|finally|step\s*\d|'
                       r'第[一二三四五六七八九十\d]|步骤|首先|然后|其次|最后|'
                       r'第一|第二|第三|\d+[\.、\)]\s*\S')
    bu = count_pattern(body, r'^[\-\*•]\s')
    total_struct = st + bu
    if total_struct >= 4: ss = 8
    elif total_struct >= 2: ss = 6
    elif total_struct >= 1: ss = 3
    else: ss = 1
    ss_d = (f'{st} steps + {bu} bullets. Well structured'
            if ss >= 7 else ('Has basic structure'
            if ss >= 4 else 'Add numbered steps or bullet points'))
    dims.append({'n': 'Structure', 's': ss, 'm': 8, 'd': ss_d, 'icon': '🔢'})
    total += ss

    # 4. Comparison 8
    cm = count_pattern(ft, r'vs|versus|compared|unlike|differs|difference|'
                       r'better.than|worse.than|rather.than|instead.of|'
                       r'对比|相比|不同于|区别|差异|比.*更|而不是|而非|优于|不如')
    # Numeric contrast: "45 degrees vs 30 degrees" pattern
    cm_num = count_pattern(ft, r'\d+\s*(?:%|degrees|times|years|days|倍|度).{0,30}'
                           r'\d+\s*(?:%|degrees|times|years|days|倍|度)')
    total_cm = cm + cm_num
    if total_cm >= 3: cs = 8
    elif total_cm >= 1: cs = 5
    else: cs = 2
    cs_d = (f'{total_cm} comparisons. Strong'
            if cs >= 7 else (f'{total_cm} comparison(s). Add more A vs B'
            if cs >= 4 else 'Missing comparison — add contrasts'))
    dims.append({'n': 'Comparison', 's': cs, 'm': 8, 'd': cs_d, 'icon': '⚖️'})
    total += cs

    # 5. FAQ Module 8
    qa = count_pattern(body, r'Q[：:]\s|A[：:]\s|Q&A|FAQ|问[：:]|答[：:]|常见问题')
    if qa >= 4: qs = 8
    elif qa >= 2: qs = 6
    elif qa >= 1: qs = 3
    else: qs = 1
    qs_d = (f'{qa} Q&A pairs. Rich FAQ'
            if qs >= 6 else ('Has Q&A elements'
            if qs >= 3 else 'Add 2-3 Q&As — AI loves answering questions'))
    dims.append({'n': 'FAQ Module', 's': qs, 'm': 8, 'd': qs_d, 'icon': '❓'})
    total += qs

    # 6. Title Quality 8
    hk = len(title) > 0
    hi = bool(re.search(r'how|what|why|which|when|where|who|guide|tutorial|tips|'
                        r'怎么|如何|什么|哪|为什么|多少|吗|教程|指南|攻略|方法|技巧|案例',
                        title))
    hn = bool(re.search(r'\d', title))
    if hk and hi and hn: tq = 8
    elif hk and hi: tq = 6
    elif hk and hn: tq = 5
    elif hk: tq = 3
    else: tq = 1
    tq_d = ('Title has search intent + number — ideal'
            if tq >= 7 else ('Good, add a number'
            if tq >= 5 else ('Add search intent keywords'
            if tq >= 2 else 'No valid title detected')))
    dims.append({'n': 'Title Quality', 's': tq, 'm': 8, 'd': tq_d, 'icon': '📌'})
    total += tq

    # 7. Keyword Density 8 (auto-extract topic words)
    topic_phrases = extract_topic_phrases(body)
    kw_score = 0
    kw_top = ''
    for phrase in topic_phrases:
        c = sum(1 for _ in re.finditer(re.escape(phrase), ft))
        if c >= 3:
            kw_score = 8
            kw_top = phrase
            break
        elif c >= 2 and kw_score < 6:
            kw_score = 6
            kw_top = phrase
        elif c >= 1 and kw_score < 4:
            kw_score = 4
            kw_top = phrase
    if not kw_score:
        kw_score = 2
        kw_top = '(auto-detect failed)'
    kw_d = (f'"{kw_top}" well covered (≥3x)'
            if kw_score >= 7 else (f'"{kw_top}" appears {kw_score//2-1}x — aim for 3-5x'
            if kw_score >= 4 else 'Topic keywords sparse or undetectable'))
    dims.append({'n': 'Keyword Density', 's': kw_score, 'm': 8, 'd': kw_d, 'icon': '🔑'})
    total += kw_score

    # 8. Paragraph Length 6
    paras = [p for p in body.split('\n\n') if p.strip()]
    avg_len = sum(len(p) for p in paras) / max(len(paras), 1)
    if 30 <= avg_len <= 150: pl = 6
    elif 15 <= avg_len <= 300: pl = 4
    else: pl = 2
    pl_d = (f'Avg {round(avg_len)} chars/para. Good rhythm'
            if pl >= 5 else ('Paragraphs a bit long/short'
            if pl >= 3 else 'Adjust paragraph length'))
    dims.append({'n': 'Paragraph Length', 's': pl, 'm': 6, 'd': pl_d, 'icon': '📏'})
    total += pl

    # 9. Source Traceability 6
    rf = count_pattern(ft, r'reference|source|citation|according.to|study|survey|'
                       r'published|reported|data.from|verified.by|link|'
                       r'参考|来源|引用|据.*显示|检测报告|调查|研究表明')
    if rf >= 3: rs = 6
    elif rf >= 1: rs = 4
    else: rs = 1
    rs_d = (f'{rf} traceable sources. Credible'
            if rs >= 5 else ('Has some sources — add more'
            if rs >= 3 else 'Add citations or data sources'))
    dims.append({'n': 'Sources', 's': rs, 'm': 6, 'd': rs_d, 'icon': '📖'})
    total += rs

    # 10. CTA 4
    ct = count_pattern(ft, r'subscribe|follow|share|comment|contact|reach.out|try|'
                       r'sign.up|download|learn.more|get.started|'
                       r'私信|联系|咨询|关注|扫描|点击|评论|加微信|打电话|聊聊')
    cc = 4 if ct >= 1 else 1
    cc_d = 'Has call-to-action' if ct >= 1 else 'Add a CTA at the end'
    dims.append({'n': 'CTA', 's': cc, 'm': 4, 'd': cc_d, 'icon': '🎯'})
    total += cc

    # 11. Entity Info 8
    ent_score = sum(1 for p in ENTITY_PATTERNS if p.search(ft))
    if ent_score >= 3: ent_score = 8
    elif ent_score >= 2: ent_score = 6
    elif ent_score >= 1: ent_score = 3
    else: ent_score = 1
    ent_d = ('Rich location/org/time info'
             if ent_score >= 6 else ('Has basic entity info'
             if ent_score >= 3 else 'Add location and organization names'))
    dims.append({'n': 'Entity Info', 's': ent_score, 'm': 8, 'd': ent_d, 'icon': '🏢'})
    total += ent_score

    # 12. EEAT Authority 8
    eeat = 0
    # Experience signals (verb-before-number pattern: "做了12年")
    if re.search(r'\d+[\s\-]*(?:years|年).*(?:experience|经验|in\s|of\s)', ft):
        eeat += 3
    elif re.search(r'(?:做了?|干了?|跑过|从业|入行|从事).{0,15}\d+\s*年|'
                   r'\d+\s*年.{0,15}(?:经验|经历|从业|入行)', ft):
        eeat += 3
    # Expertise / credentials
    if re.search(r'certified|licensed|PhD|degree|expert|professional|'
                 r'认证|资质|专业|工程师|博士|证书', ft):
        eeat += 3
    # Trust / third-party validation
    if re.search(r'reviewed|verified|tested|published|peer|audited|'
                 r'检测报告|型式检验|第三方|验证|审核|认证', ft):
        eeat += 2
    if eeat >= 6: eeat = 8
    elif eeat >= 4: eeat = 6
    elif eeat >= 2: eeat = 4
    else: eeat = 2
    eeat_d = ('Strong E-E-A-T signals'
              if eeat >= 7 else ('Decent authority'
              if eeat >= 5 else 'Add experience/credentials/citations'))
    dims.append({'n': 'EEAT', 's': eeat, 'm': 8, 'd': eeat_d, 'icon': '🛡️'})
    total += eeat

    # 13. Semantic Match 4
    sem = 0
    if re.search(r'how|what|why|which|when|where|who|'
                 r'怎么|如何|什么|哪|为什么|多少|吗', title):
        sem += 2
    if re.search(r'because|therefore|reason|answer|key|core|'
                 r'因为|所以|原因|答案|关键|核心', body[:200]):
        sem += 2
    sem_d = ('Title-content intent aligned'
             if sem >= 3 else ('Partial match'
             if sem >= 1 else 'Title and content intent mismatch'))
    dims.append({'n': 'Semantic Match', 's': sem, 'm': 4, 'd': sem_d, 'icon': '🎯'})
    total += sem

    # 14. Anti-AI Voice 4
    ai_hits = 0
    for pat in AI_FORBIDDEN:
        ai_hits += len(pat.findall(ft))
    for w in AI_WASTE:
        ai_hits += count_keyword(ft, w)
    if ai_hits == 0: deai = 4
    elif ai_hits <= 2: deai = 3
    elif ai_hits <= 5: deai = 1
    else: deai = 0
    deai_d = ('Zero AI-template words — authentic voice'
              if ai_hits == 0 else (f'{ai_hits} AI-tells, acceptable'
              if ai_hits <= 2 else f'{ai_hits} AI-template words — rewrite naturally'))
    dims.append({'n': 'Anti-AI Voice', 's': deai, 'm': 4, 'd': deai_d, 'icon': '🤖'})
    total += deai

    # Summary
    pct = round(total / max_total * 100)
    if pct >= 85: grade = 'S'
    elif pct >= 70: grade = 'A'
    elif pct >= 50: grade = 'B'
    else: grade = 'C'

    # Suggestions
    sugg = []
    for d in dims:
        if d['s'] / d['m'] < 0.5:
            sugg.append({'t': 'fix', 'm': f"{d['n']} low: {d['d']}"})
    if len(sugg) < 2:
        sugg.append({'t': 'good',
                     'm': 'Overall GEO-friendly. Keep publishing similar quality content.'})

    return {
        'title': title,
        'total': total,
        'maxTotal': max_total,
        'pct': pct,
        'grade': grade,
        'dimensions': dims,
        'suggestions': sugg,
        'stats': {
            'textLength': len(ft),
            'paraCount': len(paras),
            'avgParaLen': round(avg_len),
            'dataCount': nm,
        }
    }


def format_output(result: dict) -> str:
    """Human-readable output"""
    r = result
    grade_emoji = {'S': '🏆 Excellent', 'A': '✅ Good', 'B': '⚠️ Needs Work', 'C': '❌ Rewrite'}
    out = []
    out.append("╔══════════════════════════════════╗")
    out.append(f"║  GEO Auditor v{VERSION}              ║")
    out.append("╠══════════════════════════════════╣")
    out.append(f"║  Score: {r['total']}/{r['maxTotal']}  ({r['pct']}%)  Grade: {r['grade']}  ║")
    out.append("╚══════════════════════════════════╝")
    out.append("")
    out.append(f"  {grade_emoji.get(r['grade'], r['grade'])}")
    out.append(f"  Chars: {r['stats']['textLength']}  |  Paras: {r['stats']['paraCount']}  |  "
               f"Avg len: {r['stats']['avgParaLen']}  |  Data pts: {r['stats']['dataCount']}")
    out.append("")
    out.append("  ── Dimensions ──")
    for d in r['dimensions']:
        bar = '█' * round(d['s'] / d['m'] * 20) + '░' * (20 - round(d['s'] / d['m'] * 20))
        out.append(f"  {d['icon']} {d['n']:<15s} {d['s']}/{d['m']}  {bar}  {d['d']}")
    out.append("")
    out.append("  ── Suggestions ──")
    for s in r['suggestions']:
        tag = '[FIX]' if s['t'] == 'fix' else '[TIP]'
        out.append(f"  {tag} {s['m']}")
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(
        description='GEO Auditor — AI Search Content Quality Detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 geo_auditor.py "your content text here..."
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json
  echo "content" | python3 geo_auditor.py --stdin
        """
    )
    parser.add_argument('text', nargs='?', help='Content text to analyze')
    parser.add_argument('--file', '-f', help='Read content from file')
    parser.add_argument('--stdin', action='store_true', help='Read content from stdin')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output (for Agent parsing)')
    parser.add_argument('--version', '-v', action='version', version=f'GEO Auditor v{VERSION}')
    args = parser.parse_args()

    content = None
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.stdin:
        content = sys.stdin.read()
    elif args.text:
        content = args.text
    else:
        parser.print_help()
        sys.exit(1)

    if not content or not content.strip():
        print("Error: empty content", file=sys.stderr)
        sys.exit(1)

    result = detect(content)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == '__main__':
    main()
