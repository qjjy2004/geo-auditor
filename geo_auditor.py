#!/usr/bin/env python3
"""
GEO Auditor CLI — 工业品 AI 搜索内容检测器
14维度检测 + 去AI化 + 工程行业垂直

用法:
  python3 geo_auditor.py "你的内容文本"
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json
  echo "内容" | python3 geo_auditor.py --stdin

Agent 集成:
  python3 geo_auditor.py --file output.md --json 2>/dev/null
  # 返回 JSON: {pct, grade, total, maxTotal, dimensions: [...], suggestions: [...]}
"""

import re
import sys
import json
import argparse
from typing import Optional

VERSION = "1.0.0"

# ══════════════════════════════════════════
# 行业关键词 — 修改这里适配你的行业
# ══════════════════════════════════════════
INDUSTRY_KW = [
    '抗震支架', '抗震支吊架', '建筑机电', 'GB50981', '验收',
    '安装', '锚栓', '斜撑', '螺栓', '扭矩', '槽钢', '支吊架',
    '机电抗震', '抗震', '工程', '施工', '监理', '甲方'
]

ENTITY_PATTERNS = [
    re.compile(r'省|市|区|县|江苏|浙江|广东|北京|上海|深圳|南京|杭州|广州|安徽|山东|河南|河北|湖北|湖南|四川|重庆'),
    re.compile(r'医院|学校|厂房|高铁|地铁|机场|商场|住宅|酒店|办公|停车'),
    re.compile(r'公司|厂|集团|院|局|所|中心|站|队'),
]

AI_FORBIDDEN = [
    re.compile(r'不是.{0,15}而是'),
    re.compile(r'并非.{0,10}而是'),
    re.compile(r'不仅是.{0,10}更是'),
    re.compile(r'与其说.{0,10}不如说'),
]

AI_WASTE = [
    '此外', '而且', '因此', '然而', '综上所述', '可以说', '在某种程度上',
    '往往', '一定的', '值得注意的是', '更为关键的是', '总而言之',
    '众所周知', '不可否认', '毋庸置疑', '总的来看', '总的来讲'
]


def count_pattern(text: str, pattern) -> int:
    """统计正则匹配次数"""
    return len(re.findall(pattern, text))


def count_keyword(text: str, keyword: str) -> int:
    """统计关键词出现次数（转义正则特殊字符）"""
    escaped = re.escape(keyword)
    return len(re.findall(escaped, text))


def detect(text: str) -> dict:
    """核心检测引擎 — 与 HTML 版逻辑完全一致"""
    lines = text.split('\n')
    title = lines[0] if len(lines[0]) < 80 else ''
    body = '\n'.join(lines[1:]) if title else text
    ft = text  # full text

    dims = []
    total = 0
    max_total = 100

    # 1. 结论前置 10
    first_para = (body.strip().split('\n')[0] if body.strip() else '')[:120]
    has_conclusion = bool(re.search(r'答案|结论|核心|关键|说白了|说真的|直接|就是', first_para)) and len(first_para) >= 25
    cf = 10 if has_conclusion else (6 if len(first_para) >= 20 else 2)
    cf_d = '首段结论明确，AI可直接提取' if cf >= 9 else ('有开篇但不够直接，建议第一句给答案' if cf >= 5 else '缺结论——AI偏好第一段直接说答案')
    dims.append({'n': '结论前置', 's': cf, 'm': 10, 'd': cf_d, 'icon': '📍'})
    total += cf

    # 2. 数据锚点 10
    nm = count_pattern(ft, r'\d+\.?\d*\s*(?:亿|万|千|百|元|套|个|次|年|月|日|%|mm|cm|m|kg|t|℃|μm|条|家|N·m|kN)')
    sm = count_pattern(ft, r'GB\s*\d|ISO\s*\d|TCECS|标准|规范|第.*条')
    if nm >= 4 and sm >= 2: da = 10
    elif nm >= 3: da = 7
    elif nm >= 2: da = 5
    elif nm >= 1: da = 2
    else: da = 0
    da_d = f'{nm}个数据+{sm}条规范。{"优秀" if da>=9 else "不错" if da>=5 else "偏少，加具体数字"}'
    dims.append({'n': '数据锚点', 's': da, 'm': 10, 'd': da_d, 'icon': '📊'})
    total += da

    # 3. 步骤/结构化 8
    st = count_pattern(body, r'第[一二三四五六七八九十\d]|步骤|首先|然后|其次|最后|第一|第二|第三|\d+[\.、\)]\s*\S')
    bu = count_pattern(body, r'^[\-\*•]\s')
    total_struct = st + bu
    if total_struct >= 4: ss = 8
    elif total_struct >= 2: ss = 6
    elif total_struct >= 1: ss = 3
    else: ss = 1
    ss_d = f'{st}步骤+{bu}列表。{"结构清晰" if ss>=7 else "有基础" if ss>=4 else "缺分点分步"}'
    dims.append({'n': '步骤/结构化', 's': ss, 'm': 8, 'd': ss_d, 'icon': '🔢'})
    total += ss

    # 4. 对比结构 8
    cm = count_pattern(ft, r'vs|对比|相比|不同于|区别|差异|比.*更|而不是|而非|优于|不如|达标.*翻车|合格.*不合格')
    cs = 8 if cm >= 3 else (5 if cm >= 1 else 2)
    cs_d = f'{cm}处对比。{"充足" if cs>=7 else "有1-2处" if cs>=4 else "缺对比，加A vs B"}'
    dims.append({'n': '对比结构', 's': cs, 'm': 8, 'd': cs_d, 'icon': '⚖️'})
    total += cs

    # 5. FAQ模块 8
    qa = count_pattern(body, r'Q[：:]|问[：:]|A[：:]|答[：:]|Q&A|常见问题|FAQ')
    if qa >= 4: qs = 8
    elif qa >= 2: qs = 6
    elif qa >= 1: qs = 3
    else: qs = 1
    qs_d = f'{qa}个Q&A标记。{"FAQ丰富" if qs>=6 else "有但可补" if qs>=3 else "无FAQ，加2-3个问答匹配AI搜索"}'
    dims.append({'n': 'FAQ模块', 's': qs, 'm': 8, 'd': qs_d, 'icon': '❓'})
    total += qs

    # 6. 标题质量 8
    hk = len(title) > 0
    hi = bool(re.search(r'怎么|如何|什么|哪|为什么|多少|吗|教程|指南|攻略|方法|技巧|案例|实录', title))
    hn = bool(re.search(r'\d', title))
    if hk and hi and hn: tq = 8
    elif hk and hi: tq = 6
    elif hk and hn: tq = 5
    elif hk: tq = 3
    else: tq = 1
    tq_d = '标题含搜索词+数字' if tq>=7 else ('不错，加个数字更佳' if tq>=5 else ('缺搜索意图' if tq>=2 else '无有效标题'))
    dims.append({'n': '标题质量', 's': tq, 'm': 8, 'd': tq_d, 'icon': '📌'})
    total += tq

    # 7. 关键词密度 8 (行业词优先)
    kw_score = 0
    kw_top = ''
    for kw in INDUSTRY_KW:
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
        kw_top = '(无)'
    kw_d = f'核心词"{kw_top}"充分覆盖' if kw_score>=7 else (f'"{kw_top}"出现不足，目标3-5次' if kw_score>=4 else '行业核心词缺失')
    dims.append({'n': '关键词密度', 's': kw_score, 'm': 8, 'd': kw_d, 'icon': '🔑'})
    total += kw_score

    # 8. 段落长度 6
    paras = [p for p in body.split('\n\n') if p.strip()]
    avg_len = sum(len(p) for p in paras) / max(len(paras), 1)
    if 30 <= avg_len <= 150: pl = 6
    elif 15 <= avg_len <= 300: pl = 4
    else: pl = 2
    pl_d = f'平均{round(avg_len)}字/段。{"适中友好" if pl>=5 else "偏长或偏短" if pl>=3 else "段落需调整"}'
    dims.append({'n': '段落长度', 's': pl, 'm': 6, 'd': pl_d, 'icon': '📏'})
    total += pl

    # 9. 引用可追溯 6
    rf = count_pattern(ft, r'GB\s*\d+|ISO\s*\d+|TCECS|第\d+\.\d+\.\d+条|据.*显示|参考|来源|检测报告|型式检验')
    if rf >= 3: rs = 6
    elif rf >= 1: rs = 4
    else: rs = 1
    rs_d = f'{rf}处可验证来源。{"可信度高" if rs>=5 else "有引用可加强" if rs>=3 else "缺规范编号或来源"}'
    dims.append({'n': '引用可追溯', 's': rs, 'm': 6, 'd': rs_d, 'icon': '📖'})
    total += rs

    # 10. CTA号召 4
    ct = count_pattern(ft, r'私信|联系|咨询|关注|扫描|点击|评论|加微信|打电话|聊聊')
    cc = 4 if ct >= 1 else 1
    cc_d = '有引导互动' if ct >= 1 else '缺CTA——文末加一句引导'
    dims.append({'n': 'CTA号召', 's': cc, 'm': 4, 'd': cc_d, 'icon': '🎯'})
    total += cc

    # 11. 实体信息 8
    ent_score = sum(1 for p in ENTITY_PATTERNS if p.search(ft))
    if ent_score >= 3: ent_score = 8
    elif ent_score >= 2: ent_score = 6
    elif ent_score >= 1: ent_score = 3
    else: ent_score = 1
    ent_d = '地名/机构/角色信息丰富' if ent_score>=6 else ('有基础地域信息' if ent_score>=3 else '缺地名和机构信息——AI无法地理匹配')
    dims.append({'n': '实体信息', 's': ent_score, 'm': 8, 'd': ent_d, 'icon': '🏢'})
    total += ent_score

    # 12. EEAT权威度 8
    eeat = 0
    if re.search(r'10年|12年|\d+年.*经验|做过|干过|跑过|做过.*项目', ft):
        eeat += 3
    if re.search(r'GB\s*\d|TCECS|型式检验|检测报告|第三方|规范', ft):
        eeat += 3
    if eeat > 5: eeat = 8
    elif eeat > 2: eeat = 5
    else: eeat = 2
    eeat_d = '经验+专业+权威均衡' if eeat>=7 else ('有经验但缺权威背书' if eeat>=4 else '缺行业经验或规范引用，EEAT弱')
    dims.append({'n': 'EEAT权威度', 's': eeat, 'm': 8, 'd': eeat_d, 'icon': '🛡️'})
    total += eeat

    # 13. 语义匹配 4
    sem = 0
    if re.search(r'为什么|怎么|如何|什么|哪|多少|吗', title):
        sem += 2
    if re.search(r'因为|所以|原因|答案|关键|核心', body[:200]):
        sem += 2
    sem_d = '标题和内容意图一致' if sem>=3 else ('部分匹配，可加强' if sem>=1 else '标题和内容意图脱节')
    dims.append({'n': '语义匹配', 's': sem, 'm': 4, 'd': sem_d, 'icon': '🎯'})
    total += sem

    # 14. 去AI化 4
    ai_hits = 0
    for pat in AI_FORBIDDEN:
        ai_hits += len(pat.findall(ft))
    for w in AI_WASTE:
        ai_hits += count_keyword(ft, w)
    if ai_hits == 0: deai = 4
    elif ai_hits <= 2: deai = 3
    elif ai_hits <= 5: deai = 1
    else: deai = 0
    deai_d = '零AI模板词，纯人声' if ai_hits==0 else (f'{ai_hits}处AI腔，可接受' if ai_hits<=2 else f'{ai_hits}处AI模板词——换口语表达')
    dims.append({'n': '去AI化', 's': deai, 'm': 4, 'd': deai_d, 'icon': '🤖'})
    total += deai

    # 汇总
    pct = round(total / max_total * 100)
    if pct >= 85: grade = 'S'
    elif pct >= 70: grade = 'A'
    elif pct >= 50: grade = 'B'
    else: grade = 'C'

    # 建议
    sugg = []
    for d in dims:
        if d['s'] / d['m'] < 0.5:
            sugg.append({'t': 'fix', 'm': f"{d['n']}得分偏低：{d['d']}"})
    if len(sugg) < 2:
        sugg.append({'t': 'good', 'm': '整体GEO友好度良好，持续发布同类内容可逐步提升AI引用率'})

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
    """格式化输出（人类可读）"""
    r = result
    grade_emoji = {'S': '🏆 完美', 'A': '✅ 优秀', 'B': '⚠️ 可优化', 'C': '❌ 需重写'}
    out = []
    out.append(f"╔══════════════════════════════════╗")
    out.append(f"║  GEO Auditor v{VERSION}              ║")
    out.append(f"╠══════════════════════════════════╣")
    out.append(f"║  总分: {r['total']}/{r['maxTotal']}  ({r['pct']}%)  {r['grade']}级  ║")
    out.append(f"╚══════════════════════════════════╝")
    out.append("")
    out.append(f"  {grade_emoji.get(r['grade'], r['grade'])}")
    out.append(f"  字符数: {r['stats']['textLength']}  |  段落: {r['stats']['paraCount']}  |  均段长: {r['stats']['avgParaLen']}字  |  数据锚点: {r['stats']['dataCount']}")
    out.append("")
    out.append("  ── 逐项评分 ──")
    for d in r['dimensions']:
        bar = '█' * round(d['s'] / d['m'] * 20) + '░' * (20 - round(d['s'] / d['m'] * 20))
        out.append(f"  {d['icon']} {d['n']:<8s} {d['s']}/{d['m']}  {bar}  {d['d']}")
    out.append("")
    out.append("  ── 优化建议 ──")
    for s in r['suggestions']:
        tag = '[修复]' if s['t'] == 'fix' else '[建议]'
        out.append(f"  {tag} {s['m']}")
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(
        description='GEO Auditor — 工业品 AI 搜索内容检测器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 geo_auditor.py "做了12年抗震支架，验收现场跑了不下200次..."
  python3 geo_auditor.py --file article.md
  python3 geo_auditor.py --file article.md --json
  echo "内容文本" | python3 geo_auditor.py --stdin
        """
    )
    parser.add_argument('text', nargs='?', help='要检测的文本内容')
    parser.add_argument('--file', '-f', help='从文件读取内容')
    parser.add_argument('--stdin', action='store_true', help='从标准输入读取内容')
    parser.add_argument('--json', '-j', action='store_true', help='JSON 格式输出（供 Agent 解析）')
    parser.add_argument('--version', '-v', action='version', version=f'GEO Auditor v{VERSION}')
    args = parser.parse_args()

    # 获取内容
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
        print("错误：内容为空", file=sys.stderr)
        sys.exit(1)

    result = detect(content)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_output(result))


if __name__ == '__main__':
    main()
