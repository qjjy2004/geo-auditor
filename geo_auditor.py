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
import math
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
    # ── Research-backed banned vocabulary (GPTZero, HC3, ai-check taxonomy) ──
    'furthermore', 'moreover', 'consequently', 'nevertheless', 'in conclusion',
    'it is worth noting', 'it should be noted', 'as previously mentioned',
    'in summary', 'to summarize', 'as we can see', 'without a doubt',
    'undeniably', 'it is important to', 'one might argue',
    # Research additions (2024-2026 literature)
    'delve', 'leverage', 'utilize', 'robust', 'comprehensive',
    'streamline', 'foster', 'facilitate', 'pivotal', 'nuanced',
    'multifaceted', 'showcase', 'underscore', 'align with', 'garner',
    'notable', 'notably', 'a myriad of', 'a plethora of', 'in the realm of',
    'stands as a testament', 'marks a pivotal', 'evolving landscape',
    'setting the stage for', 'serves as', 'boasts', 'features', 'offers',
    # Chinese
    '此外', '而且', '因此', '然而', '综上所述', '可以说', '在某种程度上',
    '往往', '一定的', '值得注意的是', '更为关键的是', '总而言之',
    '众所周知', '不可否认', '毋庸置疑', '总的来看', '总的来讲',
]

# RLHF / instruction-tuning voice patterns (key 2025-2026 finding)
RLHF_SIGNALS = [
    (re.compile(r"here.{0,5}s how.{0,5}i.{0,5}d think about", re.IGNORECASE),
     'helpful_assistant', '"Here\'s how I\'d think about it" — RLHF scaffold'),
    (re.compile(r"let me walk you through", re.IGNORECASE),
     'walkthrough', '"Let me walk you through" — pedagogical AI voice'),
    (re.compile(r"on one hand.{0,80}on the other", re.IGNORECASE),
     'balanced_tradeoff', '"On one hand X, on the other Y" — balanced framing'),
    (re.compile(r"great question|you.{0,3}re absolutely right", re.IGNORECASE),
     'sycophantic', '"Great question!" / "You\'re absolutely right!" — sycophantic prefix'),
    (re.compile(r"as of my.{0,15}(?:training|knowledge).{0,10}cutoff", re.IGNORECASE),
     'cutoff_disclaimer', '"As of my training cutoff" — knowledge disclaimer'),
    (re.compile(r"while.{0,20}has benefits.{0,30}also presents challenges", re.IGNORECASE),
     'diplomatic_tradeoff', 'Diplomatic framing of obvious tradeoffs'),
    (re.compile(r"happy to jump on a call|let me know if you have any questions|feel free to reach out",
               re.IGNORECASE),
     'templated_closer', 'Templated email/Slack closer'),
]

# ── Reference alternatives for banned vocabulary (offline, zero-API) ──
# "Consider using" — suggestions, not replacement commands. Context-dependent.
AI_ALTERNATIVES = {
    'delve': 'explore / dig into / get into / examine',
    'leverage': 'use / tap into / make the most of / put to work',
    'utilize': 'use / apply / put to use',
    'robust': 'solid / reliable / proven / battle-tested',
    'comprehensive': 'thorough / complete / full / in-depth',
    'streamline': 'simplify / speed up / cut through / make faster',
    'foster': 'build / create / encourage / grow',
    'facilitate': 'help / make possible / enable / ease',
    'pivotal': 'critical / key / central / game-changing',
    'nuanced': 'subtle / layered / complex / fine-grained',
    'multifaceted': 'complex / many-sided / layered',
    'showcase': 'show / display / highlight / put on display',
    'underscore': 'stress / emphasize / highlight / drive home',
    'garner': 'get / earn / win / pick up',
    'notable': 'worth noting / striking / key / important',
    'a myriad of': 'many / countless / dozens of / a range of',
    'a plethora of': 'many / lots of / a wealth of / plenty of',
    'in the realm of': 'in / within / around / about',
    'furthermore': 'also / plus / what\'s more / on top of that',
    'moreover': 'beyond that / and / besides',
    'consequently': 'so / as a result / that means / therefore',
    'nevertheless': 'but / still / even so / that said',
    'in conclusion': 'bottom line / here\'s the thing / to wrap up',
    'it is worth noting': 'note this / keep in mind / here\'s the key',
    'it should be noted': 'remember / the thing is / key point',
    'without a doubt': 'no question / hands down / clearly',
    'undeniably': 'no doubt / for sure / without question',
    'it is important to': 'you need to / don\'t skip this / here\'s why it matters',
    'one might argue': 'some say / you could say / the argument goes',
    '此外': '还有 / 另外 / 顺便说一句',
    '因此': '所以 / 这就导致 / 结果就是',
    '然而': '但是 / 不过 / 实际上',
    '综上所述': '总结一下 / 说穿了 / 一句话',
    '值得注意的是': '关键是 / 重点是 / 你要知道',
    '总而言之': '一句话 / 说到底',
    '众所周知': '大家都知道 / 做这行的都懂',
}

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
        self.rlhf_signals = d.get('rlhf_signals', [])  # Agent-injected RLHF patterns
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
            'instruction': '6-signal check failed. Check: (1) banned vocabulary (delve/robust/furthermore etc.), '
                           '(2) RLHF voice ("Let me walk you through"), (3) burstiness (vary sentence length), '
                           '(4) punctuation (reduce em dashes/semicolons/curly quotes), '
                           '(5) paragraph opener variety, (6) sentence structure diversity.',
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

    # 14. Anti-AI Voice 4 — research-backed multi-signal detection
    # DESIGN BOUNDARY: Does NOT penalize GEO-positive structural features
    # (comparisons, FAQ, numbered lists, conclusion-first openers).
    # Only targets: pure AI vocabulary, RLHF voice, punctuation fingerprints, burstiness deficit.
    ai_hits = 0
    ai_found = []

    # ── Signal A: AI template patterns (forbidden constructions) ──
    for pat in ai_forbidden:
        for m in pat.finditer(ft):
            pos = ft[:m.start()].count('\n')
            ai_found.append({'signal': 'forbidden_pattern', 'word': m.group(), 'para': pos + 1,
                            'detail': 'Structural template — break with conversational variation'})
            ai_hits += 1

    # ── Signal B: Banned vocabulary (research-backed, EN+CN) ──
    for w in ai_waste:
        escaped = re.escape(w)
        for m in re.finditer(escaped, ft, re.IGNORECASE):
            pos = ft[:m.start()].count('\n')
            alt = AI_ALTERNATIVES.get(w.lower(), 'rephrase in natural voice')
            ai_found.append({'signal': 'banned_word', 'word': w, 'para': pos + 1,
                            'detail': f'Consider: {alt}'})
            ai_hits += 1

    # ── Signal C: RLHF / instruction-tuning voice ──
    rlhf_hits = 0
    rlhf_found = []
    for pat, sig_type, desc in RLHF_SIGNALS:
        for m in pat.finditer(ft):
            pos = ft[:m.start()].count('\n')
            rlhf_found.append({'signal': sig_type, 'word': m.group(), 'para': pos + 1, 'detail': desc})
            rlhf_hits += 1
    ai_hits += rlhf_hits
    ai_found.extend(rlhf_found)

    # ── Signal D: Sentence diversity + burstiness ──
    sents = re.split(r'[.!?。！？\n]', body)
    sents = [s.strip() for s in sents if len(s.strip()) > 10]
    sent_lengths = [len(s.split()) for s in sents]  # word counts per sentence

    # Burstiness: std dev of sentence length (humans = high variance, AI = uniform)
    burstiness = 0.0
    if len(sent_lengths) >= 4:
        mean_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((l - mean_len) ** 2 for l in sent_lengths) / len(sent_lengths)
        burstiness = round(math.sqrt(variance), 1)

    # Simple declarative ratio
    simple_decl = sum(1 for s in sents if re.match(r'^.{0,5}(是|is|are|was|were)\b', s))
    sent_diversity = 1.0
    if len(sents) >= 4:
        simple_ratio = simple_decl / len(sents)
        sent_diversity = max(0.3, 1.0 - simple_ratio)

    # ── Signal E: Paragraph opener repetition ──
    para_openers = []
    for p in paras:
        opener = p.strip()[:15].rstrip('，,.。!！?？\n')
        if opener:
            para_openers.append(opener)
    opener_repeats = 0
    if len(para_openers) >= 3:
        oc = Counter(para_openers)
        opener_repeats = sum(c - 1 for c in oc.values() if c > 1)

    # ── Signal F: Punctuation fingerprints (research-validated) ──
    # Em dash density: >2 per 500 chars = AI signal (3-5× human rate)
    em_dash_count = ft.count('—') + ft.count('–')
    em_dash_density = round(em_dash_count / max(len(ft), 1) * 500, 1)
    # Semicolons outside academic context: almost exclusively AI
    semicolon_count = ft.count(';')
    # Curly/smart quotes (ChatGPT signature)
    curly_quotes = ft.count('\u201c') + ft.count('\u201d') + ft.count('\u2018') + ft.count('\u2019')
    punct_score = 1.0  # 1.0 = clean, 0.0 = heavy AI punctuation
    if em_dash_density > 2: punct_score -= 0.3
    if semicolon_count > 3: punct_score -= 0.3
    if curly_quotes > 2: punct_score -= 0.4
    punct_score = max(0.0, punct_score)

    # ── Score synthesis (6 signals) ──
    deai = 4
    if ai_hits > 5: deai -= 2
    elif ai_hits > 2: deai -= 1
    if burstiness < 5 and len(sent_lengths) >= 4: deai -= 1  # SD < 5 words = metronomic
    if sent_diversity < 0.5: deai -= 1
    if opener_repeats > 2: deai -= 1
    if punct_score < 0.4: deai -= 1
    deai = max(0, deai)

    # Diagnosis string
    reasons = []
    if ai_hits > 0: reasons.append(f'{ai_hits} AI-tells')
    if burstiness > 0 and burstiness < 5: reasons.append(f'burstiness={burstiness}(low)')
    if sent_diversity < 0.7: reasons.append(f'diversity={sent_diversity}')
    if opener_repeats > 0: reasons.append(f'{opener_repeats} repeated openers')
    if punct_score < 0.7: reasons.append(f'punct={punct_score}')
    deai_d = ('Clean human voice' if deai >= 4 else
              ('Minor signals: ' + ', '.join(reasons) if deai >= 3 else
               ('Mixed signals: ' + ', '.join(reasons) if deai >= 1 else
                'Heavy AI voice: ' + ', '.join(reasons))))

    voice_details = {
        'ai_word_count': ai_hits,
        'ai_words_found': ai_found[:30],
        'rlhf_signals': rlhf_found,
        'burstiness': burstiness,
        'sentence_diversity': round(sent_diversity, 2),
        'sentence_count': len(sents),
        'simple_declarative_pct': round(simple_decl / max(len(sents), 1) * 100),
        'opener_repeats': opener_repeats,
        'repeated_openers': [o for o, c in Counter(para_openers).items() if c > 1][:5],
        'punctuation': {
            'em_dash_count': em_dash_count,
            'em_dash_per_500_chars': em_dash_density,
            'semicolon_count': semicolon_count,
            'curly_quote_count': curly_quotes,
            'punct_score': round(punct_score, 2),
        },
    }
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
        'voice_details': voice_details,
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
    return analysis


def learn_from_history(results: list) -> dict:
    """Generate executable writing strategy updates from detection history"""
    analysis = analyze_history(results)
    if 'error' in analysis:
        return analysis

    rules = {
        'lock_in': [],
        'fix_first': [],
        'watch': [],
        'template_patch': [],
    }

    for name in analysis['patterns']['always_high']:
        trend = analysis['dimension_trends'][name]
        rules['lock_in'].append({
            'dimension': name,
            'evidence': f'Scored {trend["last"]}/{trend["max"]} consistently',
            'action': f'Keep current approach for {name}',
        })

    gaps = []
    for name in analysis['patterns']['always_low']:
        trend = analysis['dimension_trends'][name]
        avg_score = sum(trend['scores']) / len(trend['scores'])
        gap = trend['max'] - avg_score
        gaps.append((name, gap, trend))
    gaps.sort(key=lambda x: -x[1])

    for name, gap, trend in gaps:
        hint = generate_rewrite_hint(name, trend['last'], trend['max'], '')
        rules['fix_first'].append({
            'dimension': name,
            'avg_score': round(sum(trend['scores']) / len(trend['scores']), 1),
            'gap': round(gap, 1),
            'action': hint['action'],
            'instruction': hint['instruction'],
            'target_section': hint['target_section'],
        })
        if hint['action'] == 'add_qa_section':
            rules['template_patch'].append('Add Q&A block to template footer')
        elif hint['action'] == 'add_cta':
            rules['template_patch'].append('Add CTA line to template footer')
        elif hint['action'] == 'add_numbers':
            rules['template_patch'].append('Add [data + source] placeholder to template body')
        elif hint['action'] == 'add_context':
            rules['template_patch'].append('Add [Location, Org, Year] line to template intro')

    for name in analysis['patterns']['improving']:
        if name not in analysis['patterns']['always_high']:
            trend = analysis['dimension_trends'][name]
            if trend['delta'] <= 2:
                rules['watch'].append({
                    'dimension': name,
                    'trend': f'{trend["first"]}→{trend["last"]}',
                    'note': 'Improving but fragile',
                })

    for name in analysis['patterns']['worsening']:
        trend = analysis['dimension_trends'][name]
        rules['watch'].append({
            'dimension': name,
            'trend': f'{trend["first"]}→{trend["last"]}',
            'note': 'Declining — recent changes may have hurt this',
        })

    return {
        'summary': {
            'checks_analyzed': analysis['results_count'],
            'score_progress': f'{analysis["score_trend"]["first"]}% → {analysis["score_trend"]["last"]}%',
            'lock_in_count': len(rules['lock_in']),
            'fix_first_count': len(rules['fix_first']),
            'template_patches': len(rules['template_patch']),
        },
        'writing_rules': rules,
        'trends': analysis['dimension_trends'],
    }


def format_learn(learn: dict) -> str:
    """Human-readable learning output"""
    out = []
    out.append("╔══════════════════════════════════╗")
    out.append("║  GEO Auditor — Writing Strategy  ║")
    out.append("╠══════════════════════════════════╣")
    s = learn['summary']
    out.append(f"║  {s['score_progress']} over {s['checks_analyzed']} checks          ║")
    out.append("╚══════════════════════════════════╝")
    out.append("")

    r = learn['writing_rules']

    if r['lock_in']:
        out.append("  ✅ LOCK IN — Keep doing these:")
        for item in r['lock_in']:
            out.append(f"     {item['dimension']}: {item['evidence']}")
        out.append("")

    if r['fix_first']:
        out.append("  🔧 FIX FIRST — Before next writing session:")
        for item in r['fix_first']:
            out.append(f"     {item['dimension']}: {item['action']}")
            out.append(f"     → {item['instruction'][:100]}")
        out.append("")

    if r['template_patch']:
        out.append("  📝 TEMPLATE UPDATES — Apply to writing template:")
        for patch in r['template_patch']:
            out.append(f"     • {patch}")
        out.append("")

    if r['watch']:
        out.append("  👀 WATCH — Monitor these:")
        for item in r['watch']:
            out.append(f"     {item['dimension']} {item['trend']}: {item['note']}")

    return '\n'.join(out)
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


def generate_rewrite_prompt(text: str, result: dict) -> str:
    """Generate an LLM-ready prompt asking for 3 rewrite alternatives per flagged sentence.
    Zero-API: paste this into any LLM chat (ChatGPT, DeepSeek, Claude, etc.)"""
    vd = result.get('voice_details', {})
    flagged = vd.get('ai_words_found', [])

    if not flagged:
        return "# No AI-flagged content found. No rewrites needed."

    lines = text.split('\n')
    # Group by paragraph
    by_para = {}
    for f in flagged:
        p = f['para']
        if p not in by_para:
            by_para[p] = []
        by_para[p].append(f)

    prompt = []
    prompt.append("Rewrite the following sentences to remove AI-template language.")
    prompt.append("For each flagged sentence, provide 3 natural alternatives.")
    prompt.append("Keep the original meaning. Vary sentence structure. Use conversational voice.\n")

    for para_num in sorted(by_para.keys()):
        items = by_para[para_num]
        words = ', '.join(set(f['word'] for f in items))
        # Get the paragraph text
        para_text = lines[para_num - 1] if para_num <= len(lines) else '(not found)'
        para_text = para_text[:300]

        prompt.append(f"## Paragraph {para_num}")
        prompt.append(f"Flagged: {words}")
        prompt.append(f"Original: {para_text}")
        prompt.append("")
        prompt.append("Give 3 rewrite alternatives:")
        prompt.append("1. [rewrite 1]")
        prompt.append("2. [rewrite 2]")
        prompt.append("3. [rewrite 3]")
        prompt.append("")

    return '\n'.join(prompt)


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
    parser.add_argument('--learn', action='store_true',
                        help='Like --history but generates executable writing strategy rules')
    parser.add_argument('--rewrite-prompt', action='store_true',
                        help='Generate LLM-ready prompt: suggests 3 rewrites per AI-flagged sentence')
    parser.add_argument('--version', '-v', action='version', version=f'GEO Auditor v{VERSION}')
    args = parser.parse_args()

    # ── History / Agent Learning mode ──
    if args.history or args.learn:
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
        if args.learn:
            analysis = learn_from_history(results)
            if args.json:
                print(json.dumps(analysis, ensure_ascii=False, indent=2))
            else:
                print(format_learn(analysis))
        else:
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

    if args.rewrite_prompt:
        print(generate_rewrite_prompt(content, result))
    elif args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == '__main__':
    main()
