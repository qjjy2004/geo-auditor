# GEO Auditor · 工业品 AI 搜索内容检测器

不只是 GEO——同时检测「AI 腔」，专为工程/建筑/制造行业，支持 AI Agent 自我进化。

## 三个差异化

### 1. 反向「去 AI 腔」检测

所有 GEO 工具都在帮你讨好 AI。我们反过来——检测你的文章有没有「机器味」：

- 自动识别「值得注意的是」「综上所述」「首先…其次…最后」等 AI 模板词
- 14 个维度中单独设立「去 AI 化」评分项
- **人看着舒服 + AI 愿意引用 = 真正的 GEO**

### 2. Agent 可驱动 · 自我进化

不只是一个网页工具。提供 CLI 版本，Agent 可以直接调用：

```bash
# Hermes / Claude Code / 任何 Agent 工具可直接调用
python3 geo_auditor.py "你的内容文本"
python3 geo_auditor.py --file article.md --json  # JSON 输出供 Agent 解析
```

Agent 使用闭环：

> 检测 → 定位低分维度 → 自动改写 → 再检测 → 对比分数 → 总结规律 → 下次写作直接规避

### 3. 工程行业垂直

不是通用 GEO 检测器。搜索「抗震支架」时，它会：

- 优先识别工程行业关键词（抗震支架、GB50981、验收、锚栓、扭矩…共 18 个行业词）
- 专门检测规范引用（GB/ISO/TCECS 标准编号）
- EEAT 权威度评估——工程行业的经验年数、标准引用、检测报告

## 14 维度检测体系

| # | 维度 | 满分 | 说明 |
|---|------|------|------|
| 1 | 结论前置 | 10 | 第一句是否直接给出核心答案 |
| 2 | 数据锚点 | 10 | 具体数字 + 标准编号引用 |
| 3 | 步骤/结构化 | 8 | 分点分步、编号列表 |
| 4 | 对比结构 | 8 | A vs B 式对比、达标/不达标 |
| 5 | FAQ 模块 | 8 | Q&A 问答格式 |
| 6 | 标题质量 | 8 | 核心词 + 搜索意图词 + 数字 |
| 7 | 关键词密度 | 8 | 行业核心词 3-5 次自然出现 |
| 8 | 段落长度 | 6 | 平均 80-150 字/段 |
| 9 | 引用可追溯 | 6 | 规范编号、检测报告、来源 |
| 10 | CTA 号召 | 4 | 文末行动引导 |
| 11 | 实体信息 | 8 | 地名 + 机构 + 角色 |
| 12 | EEAT 权威度 | 8 | 经验 + 专业 + 权威 |
| 13 | 语义匹配 | 4 | 标题与内容意图一致 |
| 14 | 去 AI 化 | 4 | 零 AI 模板词 |

**满分 100 分。80+ 分内容 AI 高概率引用。**

## 两种使用方式

### 方式一：网页版

打开 `geo-auditor.html` 即可使用。粘贴内容 → 14 维度检测 → 结果+优化建议。历史记录存本地浏览器（localStorage），不上传任何服务器。

### 方式二：CLI 命令行（Agent 友好）

```bash
# 直接输入文本
python3 geo_auditor.py "做了12年抗震支架，验收现场跑了不下200次..."

# 从文件读取
python3 geo_auditor.py --file article.md

# JSON 输出（Agent 程序化解析）
python3 geo_auditor.py --file article.md --json

# Markdown 格式化输出
python3 geo_auditor.py --file article.md --json | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'总分: {d[\"pct\"]}% ({d[\"grade\"]})')
for dim in d['dimensions']:
    print(f'  {dim[\"icon\"]} {dim[\"name\"]}: {dim[\"score\"]}/{dim[\"max\"]}')
"
```

## 安装

```bash
git clone https://github.com/liangjia-tech/geo-auditor.git
cd geo-auditor

# 网页版：直接用浏览器打开 geo-auditor.html

# CLI 版本：无需额外依赖，Python 3.7+ 即可
python3 geo_auditor.py --help
```

## 工程行业适配

检测器内置 18 个工程行业高频关键词，关键词密度检测会优先匹配这些词：

`抗震支架、抗震支吊架、建筑机电、GB50981、验收、安装、锚栓、斜撑、螺栓、扭矩、槽钢、支吊架、机电抗震、施工、监理、甲方`

**可自定义**：编辑 HTML 中的 `INDUSTRY_KW` 数组，替换为自己的行业关键词。

## 与 Hermes AI Agent 协同

这个工具的设计哲学是「对话即界面」——它不是一个孤立的检测器，而是 AI Agent 工作流中的一个环节。配合 Hermes Agent 使用时：

1. Hermes 生成初稿 → 自动调 CLI 检测
2. 分数 < 80 → Agent 改写低分维度 → 再次检测
3. 对比前后分数 → 记录改进规律
4. 下次生成内容时，Agent 直接从规律中规避已知问题

**工具本身在进化——你一个月后用的检测器，判断力跟今天不一样。**

## License

MIT

## 作者

良佳科技 · [zhibi.xyz](https://zhibi.xyz)
