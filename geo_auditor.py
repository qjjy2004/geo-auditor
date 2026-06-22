#!/usr/bin/env python3
"""
GEO Auditor — AI Search Content Quality Detector
14-dimension check + anti-AI-voice + Agent-driven self-evolution

Usage:
  python3 geo_auditor.py "your content text"
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json
  python3 geo_auditor.py --file article.md --config industry.json
  python3 geo_auditor.py --compare v1.md v2.md
  echo "content" | python3 geo_auditor.py --stdin

Agent integration:
  python3 geo_auditor.py --file output.md --json 2>/dev/null
  # Returns JSON with actionable 'rewrite_hints' per low dimension

Agent learning loop:
  python3 geo_auditor.py --history < results.jsonl
  # Reads multiple detection results and extracts improvement patterns
"""

import re
import sys
import json
import argparse
from collections import Counter
from typing import Optional

VERSION = "1.2.0"

# ════════════════════════════════════
# Default patterns (can be overridden via --config)
# ════════════════════════════════════
DEFAULT_ENTITY_PATTERNS = [
    re.compile(r'province|city|county|district|state|China|US|UK|Japan|Korea|India|'
               r'Beijing|Shanghai|Shenzhen|Guangzhou|Hangzhou|Nanjing|Tokyo|London|NY|'
               r'省|市|区|县|江苏|浙江|广东|北京|上海|深圳|南京|杭州|广州'),
    re.compile(r'company|corp|inc|ltd|group|university|institute|hospital|school|agency|'
               r'公司|集团|大学|学院|医院|学校|机构|部门|单位|工厂|实验室'),
    re.compile(r'\d{4}年|\d{4}-\d{2}|since\s+\d{4}|for\s+\d+\s+years|'
               r'做了?\d+年|干了?\d+年|\d+年.*经验'),
]

DEFAULT_AI_FORBIDDEN = [
    re.compile(r'not.{0,15}but'),
    re.compile(r"isn't.{0,10}it's"),
    re.compile(r'not only.{0,10}but also'),
    re.compile(r'it.{0,10}goes without saying'),
    re.compile(r'不是.{0,15}而是'),
    re.compile(r'并非.{0,10}而是'),
    re.compile(r'不仅是.{0,10}更是'),
]

DEFAULT_AI_WASTE = [
    'furthermore', 'moreover', 'consequently', 'nevertheless', 'in conclusion',
    'it is worth noting', 'it should be noted', 'as previously mentioned',
    'in summary', 'to summarize', 'as we can see', 'without a doubt',
    'undeniably', 'it is important to', 'one might argue',
    '此外', '而且', '因此', '然而', '综上所述', '可以说', '在某种程度上',
    '往往', '一定的', '值得注意的是', '更为关键的是', '总而言之',
    '众所周知', '不可否认', '毋庸置疑', '总的来看', '总的来讲',
]

DEFAULT_REF_PATTERNS = [
    r'reference|source|citation|according.to|study|survey|'
    r'published|reported|data.from|verified.by|link|'
    r'参考|来源|引用|据.*显示|检测报告|调查|研究表明',
]

DEFAULT_DATA_UNITS = (
    r'billion|million|thousand|hundred|%|USD|EUR|CNY|¥|\$|€|'
    r'kg|km|mm|cm|m|t|℃|°F|years|months|days|hours|times|users|people|'
    r'亿|万|千|百|元|套|个|次|年|月|日|条|家|N·m|kN|MPa|吨'
)


class Config:
    """Agent-injectable detection config"""
    def __init__(self, data: dict = None):
        d = data or {}
        self.keywords = d.get('keywords', [])          # custom topic keywords
        self.entity_patterns = [re.compile(p) for p in d.get('entity_patterns', [])]
        self.ai_forbidden = [re.compile(p) for p in d.get('ai_forbidden', [])]
        self.ai_waste = d.get('ai_waste', [])
        self.ref_patterns = d.get('ref_patterns', [])
        self.data_units = d.get('data_units', '')

    @property
    def has_custom_keywords(self):
        return len(self.keywords) > 0

    @property
    def has_custom_refs(self):
        return len(self.ref_patterns) > 0

    def entity_patterns_or_default(self):
        return self.entity_patterns if self.entity_patterns else DEFAULT_ENTITY_PATTERNS

    def ai_forbidden_or_default(self):
        return self.ai_forbidden if self.ai_forbidden else DEFAULT_AI_FORBIDDEN

    def ai_waste_or_default(self):
        return self.ai_waste if self.ai_waste else DEFAULT_AI_WASTE

    def ref_patterns_or_default(self):
        return self.ref_patterns if self.ref_patterns else DEFAULT_REF_PATTERNS

    def data_units_or_default(self):
        return self.data_units if self.data_units else DEFAULT_DATA_UNITS


def count_pattern(text: str, pattern) -> int:
    return len(re.findall(pattern, text))


def count_keyword(text: str, keyword: str) -> int:
    return len(re.findall(re.escape(keyword), text))


def extract_topic_phrases(text: str, top_n: int = 5) -> list:
    """Auto-extract topic bigrams/trigrams (handles both EN + CN)"""
    clean = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
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
        words = clean.split()
        if len(words) >= 3:
            bigram_counts = Counter()
            for i in range(len(words) - 1):
                if words[i] not in stops and words[i+1] not in stops:
                    bg = f'{words[i]} {words[i+1]}'
                    if len(bg.replace(' ', '')) >= 4:
                        bigram_counts[bg] += 1
            for bg, count in bigram_counts.items():
                if count >= 2:
                    candidates.append((bg, count))

    candidates.sort(key=lambda x: -x[1])
    return [phrase for phrase, count in candidates[:top_n]]


def generate_rewrite_hint(dim_name: str, score: int, max_score: int, detail: str) -> dict:
    """Generate structured, actionable rewrite instruction for Agent"""
    ratio = score / max_score
    base = {'dimension': dim_name, 'current': score, 'max': max_score, 'severity': ratio}

    hints = {
        'Conclusion-First': {
            'action': 'rewrite_opening',
            'instruction': 'Move the core answer/conclusion to the FIRST sentence of the body. '
                           'Use phrases like "Here\'s the thing:" or "The short answer:" or "说白了:". '
                           'Keep it under 40 words.',
            'target_section': 'paragraph_1',
        },
        'Data Anchors': {
            'action': 'add_numbers',
            'instruction': 'Add 2-3 specific numbers (% or counts or amounts) with units. '
                           'Add 1-2 source citations or standard references.',
            'target_section': 'throughout',
        },
        'Structure': {
            'action': 'add_numbered_list',
            'instruction': 'Convert one section into a numbered list (3-5 items). '
                           'Use "1. / 2. / 3." or bullet points.',
            'target_section': 'middle_section',
        },
        'Comparison': {
            'action': 'add_contrast',
            'instruction': 'Add at least one A vs B comparison. '
                           'Use "vs", "compared to", "rather than", or numeric contrast '
                           '("X is 3x more than Y").',
            'target_section': 'any_paragraph',
        },
        'FAQ Module': {
            'action': 'add_qa_section',
            'instruction': 'Add 2-3 Q&A pairs at the end. Format: "Q: [question] A: [answer]". '
                           'Use questions real users would search for.',
            'target_section': 'end_of_content',
        },
        'Title Quality': {
            'action': 'rewrite_title',
            'instruction': 'Add a search-intent word (how/what/why/guide) AND a number to the title.',
            'target_section': 'title',
        },
        'Keyword Density': {
            'action': 'reinforce_topic_words',
            'instruction': 'Identify 2-3 core topic terms and ensure each appears 3-5 times naturally '
                           'throughout the content. Don\'t stuff — spread evenly.',
            'target_section': 'throughout',
        },
        'Paragraph Length': {
            'action': 'adjust_paragraphs',
            'instruction': 'Break long paragraphs (>200 chars) into 2-3 shorter ones. '
                           'Each paragraph should express one complete thought.',
            'target_section': 'long_paragraphs',
        },
        'Sources': {
            'action': 'add_citations',
            'instruction': 'Add at least 2 verifiable references. Mention specific studies, '
                           'standards, reports, or link to source data.',
            'target_section': 'throughout',
        },
        'CTA': {
            'action': 'add_cta',
            'instruction': 'Add one call-to-action at the very end: "Subscribe for more", '
                           '"Contact me", "Try it yourself", etc.',
            'target_section': 'end_of_content',
        },
        'Entity Info': {
            'action': 'add_context',
            'instruction': 'Add a location name (city/province) and an organization/company name. '
                           'Mention a specific time period or year.',
            'target_section': 'early_paragraphs',
        },
        'EEAT': {
            'action': 'add_credibility',
            'instruction': 'Add experience signal ("X years in this field") AND '
                           'a credential or third-party validation reference.',
            'target_section': 'intro_or_body',
        },
        'Semantic Match': {
            'action': 'align_title_body',
            'instruction': 'Make sure the body directly answers the question/claim in the title. '
                           'Use the title keyword in the first paragraph.',
            'target_section': 'title_and_opening',
        },
        'Anti-AI Voice': {
            'action': 'remove_ai_tells',
            'instruction': 'Remove AI-template phrases. Replace "furthermore/in conclusion/it is worth noting" '
                           'with conversational transitions. Read aloud — if it sounds like a robot, rewrite.',
            'target_section': 'throughout',
        },
    }

    h = hints.get(dim_name, {
        'action': 'improve',
        'instruction': detail,
        'target_section': 'throughout',
    })
    h['dimension'] = dim_name
    h['current'] = score
    h['max'] = max_score
    h['severity'] = ratio
    return h


def detect(text: str, config: Config = None) -> dict:
    """Core detection engine — 14 dimensions, 100 points"""
    if config is None:
        config = Config()

    entity_patterns = config.entity_patterns_or_default()
    ai_forbidden = config.ai_forbidden_or_default()
    ai_waste = config.ai_waste_or_default()
    ref_patterns = config.ref_patterns_or_default()
    data_units = config.data_units_or_default()

    lines = text.split('\n')
    title = lines[0] if len(lines[0]) < 80 else ''
    body = '\n'.join(lines[1:]) if title else text
    ft = text

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
    nm = count_pattern(ft, rf'\d+\.?\d*\s*(?:{data_units})')
    sm = sum(count_pattern(ft, p) for p in ref_patterns)
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

    # 7. Keyword Density 8 (custom keywords OR auto-extract)
    kw_score = 0
    kw_top = ''
    if config.has_custom_keywords:
        for kw in config.keywords:
            c = count_keyword(ft, kw)
            if c >= 3:
                kw_score = 8
                kw_top = kw
                break
            elif c >= 1 and kw_score < 5:
                kw_score = 5
                kw_top = kw
        if not kw_score:
            kw_score = 2
            kw_top = '(none matched)'
        kw_d = (f'"{kw_top}" well covered (≥3x)'
                if kw_score >= 7 else (f'"{kw_top}" sparse — aim for 3-5x'
                if kw_score >= 4 else 'Custom keywords not found in text'))
    else:
        topic_phrases = extract_topic_phrases(body)
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

    # 9. Sources 6
    rf = sum(count_pattern(ft, p) for p in ref_patterns)
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
    ent_score = sum(1 for p in entity_patterns if p.search(ft))
    if ent_score >= 3: ent_score = 8
    elif ent_score >= 2: ent_score = 6
    elif ent_score >= 1: ent_score = 3
    else: ent_score = 1
    ent_d = ('Rich location/org/time info'
             if ent_score >= 6 else ('Has basic entity info'
             if ent_score >= 3 else 'Add location and organization names'))
    dims.append({'n': 'Entity Info', 's': ent_score, 'm': 8, 'd': ent_d, 'icon': '🏢'})
    total += ent_score

    # 12. EEAT 8
    eeat = 0
    if re.search(r'\d+[\s\-]*(?:years|年).*(?:experience|经验|in\s|of\s)', ft):
        eeat += 3
    elif re.search(r'(?:做了?|干了?|跑过|从业|入行|从事).{0,15}\d+\s*年|'
                   r'\d+\s*年.{0,15}(?:经验|经历|从业|入行)', ft):
        eeat += 3
    if re.search(r'certified|licensed|PhD|degree|expert|professional|'
                 r'认证|资质|专业|工程师|博士|证书', ft):
        eeat += 3
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
    for pat in ai_forbidden:
        ai_hits += len(pat.findall(ft))
    for w in ai_waste:
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

    # Structured rewrite hints for Agent
    rewrite_hints = []
    for d in dims:
        if d['s'] / d['m'] < 0.5:
            rewrite_hints.append(generate_rewrite_hint(d['n'], d['s'], d['m'], d['d']))

    # Text suggestions (human-readable)
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
        'rewrite_hints': rewrite_hints,
        'stats': {
            'textLength': len(ft),
            'paraCount': len(paras),
            'avgParaLen': round(avg_len),
            'dataCount': nm,
        }
    }


def compare_results(r1: dict, r2: dict) -> dict:
    """Compare two detection results, return delta analysis"""
    delta_pct = r2['pct'] - r1['pct']
    dim_deltas = []
    for d1, d2 in zip(r1['dimensions'], r2['dimensions']):
        d = d2['s'] - d1['s']
        dim_deltas.append({
            'dimension': d1['n'],
            'before': d1['s'],
            'after': d2['s'],
            'max': d1['m'],
            'delta': d,
            'improved': d > 0,
            'worsened': d < 0,
        })

    improved = [d for d in dim_deltas if d['improved']]
    worsened = [d for d in dim_deltas if d['worsened']]
    unchanged = [d for d in dim_deltas if d['delta'] == 0]

    return {
        'before': {'pct': r1['pct'], 'grade': r1['grade'], 'total': r1['total']},
        'after': {'pct': r2['pct'], 'grade': r2['grade'], 'total': r2['total']},
        'delta_pct': delta_pct,
        'dimension_deltas': dim_deltas,
        'summary': {
            'improved_count': len(improved),
            'worsened_count': len(worsened),
            'unchanged_count': len(unchanged),
            'total_gain': sum(d['delta'] for d in improved),
            'total_loss': sum(abs(d['delta']) for d in worsened),
            'net_change': delta_pct,
            'biggest_gain': max(improved, key=lambda d: d['delta']) if improved else None,
            'biggest_loss': min(worsened, key=lambda d: d['delta']) if worsened else None,
        }
    }


def analyze_history(results: list) -> dict:
    """Analyze multiple detection results to extract improvement patterns"""
    if len(results) < 2:
        return {'error': 'Need at least 2 results for pattern analysis'}

    dim_trends = {}
    dim_names = [d['n'] for d in results[0]['dimensions']]
    dim_maxes = {d['n']: d['m'] for d in results[0]['dimensions']}

    for name in dim_names:
        scores = []
        for r in results:
            for d in r['dimensions']:
                if d['n'] == name:
                    scores.append(d['s'])
                    break
        first = scores[0]
        last = scores[-1]
        trend = 'up' if last > first else ('down' if last < first else 'flat')
        dim_trends[name] = {
            'first': first,
            'last': last,
            'delta': last - first,
            'trend': trend,
            'scores': scores,
            'max': dim_maxes.get(name, 8),
        }

    # Identify patterns (using per-dimension max for ratio)
    always_low = [n for n, t in dim_trends.items()
                  if all(s / t['max'] <= 0.5 for s in t['scores'])]
    always_high = [n for n, t in dim_trends.items()
                   if all(s / t['max'] >= 0.8 for s in t['scores'])]
    improving = [n for n, t in dim_trends.items() if t['trend'] == 'up' and t['delta'] >= 1]
    worsening = [n for n, t in dim_trends.items() if t['trend'] == 'down' and t['delta'] <= -1]

    suggestions = []
    if always_low:
        suggestions.append(f"Persistent weakness: {', '.join(always_low)}. "
                           f"Adjust writing template to address these first.")
    if improving:
        suggestions.append(f"Improving dimensions: {', '.join(improving)}. "
                           f"Reinforce the changes that drove these gains.")
    if worsening:
        suggestions.append(f"Declining dimensions: {', '.join(worsening)}. "
                           f"Recent rewrites may have traded one strength for another.")
    if always_high:
        suggestions.append(f"Consistent strengths: {', '.join(always_high)}. "
                           f"Lock these in as writing defaults.")

    return {
        'results_count': len(results),
        'dimension_trends': dim_trends,
        'patterns': {
            'always_low': always_low,
            'always_high': always_high,
            'improving': improving,
            'worsening': worsening,
        },
        'suggestions': suggestions,
        'score_trend': {
            'first': results[0]['pct'],
            'last': results[-1]['pct'],
            'delta': results[-1]['pct'] - results[0]['pct'],
            'scores': [r['pct'] for r in results],
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
    if r.get('rewrite_hints'):
        out.append("")
        out.append("  ── Agent Rewrite Hints ──")
        for h in r['rewrite_hints']:
            out.append(f"  ▶ {h['dimension']}: {h['instruction'][:80]}...")
    return '\n'.join(out)


def format_compare(cmp: dict) -> str:
    """Human-readable comparison output"""
    out = []
    out.append("╔══════════════════════════════════╗")
    out.append("║  GEO Auditor — Compare Mode      ║")
    out.append("╠══════════════════════════════════╣")
    s = cmp['summary']
    delta_str = f"+{cmp['delta_pct']}" if cmp['delta_pct'] >= 0 else str(cmp['delta_pct'])
    out.append(f"║  {cmp['before']['pct']}% → {cmp['after']['pct']}%  ({delta_str}%)  "
               f"{cmp['before']['grade']}→{cmp['after']['grade']}    ║")
    out.append("╚══════════════════════════════════╝")
    out.append("")
    out.append(f"  Improved: {s['improved_count']} dims (+{s['total_gain']} pts)")
    out.append(f"  Worsened: {s['worsened_count']} dims (-{s['total_loss']} pts)")
    out.append(f"  Unchanged: {s['unchanged_count']} dims")
    if s['biggest_gain']:
        out.append(f"  Biggest gain: {s['biggest_gain']['dimension']} "
                   f"({s['biggest_gain']['before']}→{s['biggest_gain']['after']})")
    if s['biggest_loss']:
        out.append(f"  Biggest loss: {s['biggest_loss']['dimension']} "
                   f"({s['biggest_loss']['before']}→{s['biggest_loss']['after']})")
    out.append("")
    out.append("  ── Per Dimension ──")
    for d in cmp['dimension_deltas']:
        arrow = '↑' if d['improved'] else ('↓' if d['worsened'] else '→')
        delta_str = f"+{d['delta']}" if d['delta'] > 0 else str(d['delta'])
        out.append(f"  {arrow} {d['dimension']:<16s} {d['before']}→{d['after']}  ({delta_str})")
    return '\n'.join(out)


def format_history(analysis: dict) -> str:
    """Human-readable history analysis output"""
    out = []
    out.append("╔══════════════════════════════════╗")
    out.append("║  GEO Auditor — Agent Learning    ║")
    out.append("╠══════════════════════════════════╣")
    st = analysis['score_trend']
    delta_str = f"+{st['delta']}" if st['delta'] >= 0 else str(st['delta'])
    out.append(f"║  {st['first']}% → {st['last']}%  ({delta_str}%) over {analysis['results_count']} checks  ║")
    out.append("╚══════════════════════════════════╝")
    out.append("")

    for name, trend in analysis['dimension_trends'].items():
        scores_str = ' → '.join(str(s) for s in trend['scores'])
        arrow = {'up': '📈', 'down': '📉', 'flat': '➡️'}[trend['trend']]
        out.append(f"  {arrow} {name:<16s} {scores_str}")

    out.append("")
    out.append("  ── Patterns ──")
    p = analysis['patterns']
    if p['always_high']:
        out.append(f"  ✅ Consistently strong: {', '.join(p['always_high'])}")
    if p['always_low']:
        out.append(f"  ❌ Consistently weak: {', '.join(p['always_low'])}")
    if p['improving']:
        out.append(f"  📈 Improving: {', '.join(p['improving'])}")
    if p['worsening']:
        out.append(f"  📉 Declining: {', '.join(p['worsening'])}")

    out.append("")
    out.append("  ── Agent Suggestions ──")
    for s in analysis['suggestions']:
        out.append(f"  💡 {s}")
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(
        description='GEO Auditor — AI Search Content Quality Detector (Agent-Ready)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic detection
  python3 geo_auditor.py "your content text here..."
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json

  # Agent config injection (custom keywords + industry patterns)
  python3 geo_auditor.py --file article.md --config seismic_config.json --json

  # Compare before/after rewrite
  python3 geo_auditor.py --compare draft.md revised.md

  # Agent learning: analyze trends from multiple checks
  python3 geo_auditor.py --history < results.jsonl

Config file format (geo_auditor.json):
  {
    "keywords": ["seismic bracing", "GB50981", "inspection"],
    "ref_patterns": ["GB\\\\s*\\\\d+", "JGJ\\\\s*\\\\d+", "CECS"],
    "ai_waste": ["furthermore", "值得注意的是"],
    "ai_forbidden": ["not.{0,15}but"],
    "data_units": "kN|MPa|mm|cm|吨"
  }
        """
    )
    parser.add_argument('text', nargs='?', help='Content text to analyze')
    parser.add_argument('--file', '-f', help='Read content from file')
    parser.add_argument('--stdin', action='store_true', help='Read content from stdin')
    parser.add_argument('--config', '-c', help='JSON config file (Agent-injected keywords/patterns)')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output (for Agent parsing)')
    parser.add_argument('--compare', nargs=2, metavar=('BEFORE', 'AFTER'),
                        help='Compare two files: --compare old.md new.md')
    parser.add_argument('--history', action='store_true',
                        help='Read JSONL results from stdin, analyze improvement patterns')
    parser.add_argument('--version', '-v', action='version', version=f'GEO Auditor v{VERSION}')
    args = parser.parse_args()

    # ── History / Agent Learning mode ──
    if args.history:
        results = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        if len(results) < 2:
            print("Error: need at least 2 JSON results for pattern analysis (via stdin)",
                  file=sys.stderr)
            sys.exit(1)
        analysis = analyze_history(results)
        if args.json:
            print(json.dumps(analysis, ensure_ascii=False, indent=2))
        else:
            print(format_history(analysis))
        return

    # ── Compare mode ──
    if args.compare:
        f1, f2 = args.compare
        with open(f1, 'r', encoding='utf-8') as f:
            c1 = f.read()
        with open(f2, 'r', encoding='utf-8') as f:
            c2 = f.read()
        config = Config()
        if args.config:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = Config(json.load(f))
        r1 = detect(c1, config)
        r2 = detect(c2, config)
        cmp = compare_results(r1, r2)
        if args.json:
            print(json.dumps({'before': r1, 'after': r2, 'compare': cmp},
                             ensure_ascii=False, indent=2))
        else:
            print(format_output(r1))
            print("\n" + "─" * 50 + "\n")
            print(format_output(r2))
            print("\n" + format_compare(cmp))
        return

    # ── Normal detection mode ──
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

    config = Config()
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = Config(json.load(f))

    result = detect(content, config)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == '__main__':
    main()
