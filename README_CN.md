# GEO Auditor · 倒后镜看到的是过去，我们看上的是未来

[![Version](https://img.shields.io/badge/version-v0.6.6-blue)](https://github.com/qjjy2004/geo-auditor/releases)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![Test](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml/badge.svg)](https://github.com/qjjy2004/geo-auditor/actions/workflows/test.yml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](https://github.com/qjjy2004/geo-auditor)

![demo](demo.gif)

**其他 GEO 工具告诉你已经发生了什么。GEO Auditor 在发布之前就告诉你——这篇文章能不能被 AI 引用。**

---

## 核心差异：倒后镜 vs 前照灯

所有 GEO 工具的工作方式都一样：

```
定义 prompt → 批量跑 AI 搜索引擎 → 记录：「你的品牌被提到了吗？」
```

它们回答的是同一个问题：**「AI 有没有提到我的品牌？」** —— 而且是事后才知道。它们是倒后镜，不需要进化，只管记录。

**GEO Auditor 回答的是另一个问题：「我的内容能不能被 AI 引用？」** —— 在发布之前。这是前照灯。它必须进化，因为每次改写都会让检测更准确。

| | 监测工具（竞品） | GEO Auditor |
|---|---|---|
| **时机** | 发布之后 | 发布之前 |
| **检测什么** | 「AI 回答里有没有我的品牌？」 | 「AI 能不能提取并引用这篇内容？」 |
| **比喻** | 倒后镜 | 前照灯 |
| **进化** | 不需要（只做记录） | **核心功能**（越改越聪明） |

**这就是为什么自我进化和 AI 改写建议是核心卖点——不是附加功能。** 监测工具不需要学习，检测工具必须学习。

---

## 为什么用 GEO Auditor

```
AI Agent 写内容 → 检测器打分 → Agent 改写 → 对比前后 →
积累经验 → 进化 → 生成 Agent 提示词 →
Agent 从此在更高的水平线上写作
```

检测器本身在每次改写中变得更聪明。你的 Agent 继承这份智力。

---

## 两种用法

### 1. 作为检测器（CLI + Web）

```bash
python3 geo_auditor.py --file draft.md
python3 geo_auditor.py --file draft.md --json        # Agent API
python3 geo_auditor.py --compare v1.md v2.md          # 改写前后对比
python3 geo_auditor.py --rewrite-prompt               # LLM 改写建议
```

14 个维度 + 6 重去 AI 腔检测，中英双语，零依赖。

**CLI + Web —— 两个入口，一套引擎。** Web 版（`geo-auditor.html`）在浏览器里跑完整检测引擎。CLI 版（`geo_auditor.py`）额外支持进化追踪、Agent 训练和配置注入。

### 2. 作为 Agent 训练器（进化系统）

```bash
# 每次检测自动写入进化日志 ~/.geo-auditor/evolution.jsonl
python3 geo_auditor.py --file article.md     # 自动记录

# 每次对比记录各维度提升
python3 geo_auditor.py --compare old.md new.md  # 自动记录

# 积累 5 次以上改写后，进化分析
python3 geo_auditor.py --evolve               # 验证过的改法 + 无效维度

# 导出为 Agent 系统提示词
python3 geo_auditor.py --agent-prompt > ~/.geo-auditor/writing_rules.txt
# → 加载到你的 Agent 系统提示词里就生效
```

---

## 自我进化：检测器学习，Agent 继承

| 阶段 | 发生了什么 |
|------|-----------|
| **检测** | 每次检测自动写入进化日志 |
| **改写** | 每次 `--compare` 记录各维度提升幅度 |
| **进化** | 积累 5 次以上改写后，分析哪些改法真的有效 |
| **生成提示词** | 把验证过的改法转成 Agent 可加载的写作规则 |

**进化输出示例：**

```
验证有效的改法（自动应用）：
  Conclusion-First（开门见山）：100% 有效，平均提升 +8.0
  → 「开头直接给答案。用『说白了』『一句话总结』开头」

  EEAT（专业权威）：100% 有效，平均提升 +6.0
  → 「提到从业年限 + 资质认证 + 第三方检测报告」

无效维度（别浪费时间）：
  Anti-AI Voice（去AI腔）：0% 有效
  → 这个维度是内容内在特征，改不动。把精力放在别处。
```

---

## 14 维检测 + 6 重去 AI 腔

| 维度 | 满分 | 去 AI 腔信号 | 类型 |
|------|------|------------|------|
| 开门见山 | 10 | A. 禁用句式 | 结构 |
| 数据锚点 | 10 | B. 禁用词汇（50+ 词） | 词汇 |
| 结构层次 | 8 | C. RLHF 语气（7 种模式） | 语域 |
| 对比分析 | 8 | D. 句式波动 + 多样性 | 节奏 |
| FAQ 模块 | 8 | E. 开头重复 | 结构 |
| 标题质量 | 8 | F. 标点指纹 | 书写 |
| 关键词密度 | 8 | | |
| 段落长度 | 6 | | |
| 引用来源 | 6 | | |
| 行动号召 | 4 | | |
| 实体信息 | 8 | | |
| EEAT 权威 | 8 | | |
| 语义匹配 | 4 | | |
| 去AI腔 | 4 | | |

**GEO 友好结构（对比分析、FAQ、编号列表）会被加分，不会被误判为 AI 腔。** 设计边界在源码中有明确注释。

---

## 设计理念

- **零外部依赖** — 纯 Python 规则引擎，离线运行
- **语言无感** — 自动识别中/英文，分别提取主题词
- **Agent 优先** — JSON 输出、配置注入、进化管道、Agent 提示词导出
- **研究支撑** — 去 AI 腔信号对标 GPTZero、GLTR、Binoculars（ICML 2024）、arXiv 2605.19516

---

## 安装

```bash
git clone https://github.com/qjjy2004/geo-auditor.git
cd geo-auditor

# CLI：Python 3.7+，零依赖
python3 geo_auditor.py --help

# Web：直接用浏览器打开 geo-auditor.html
```

## 快速上手

```bash
# 给文件打分
python3 geo_auditor.py --file draft.md

# 直接给文本打分
python3 geo_auditor.py "你的内容" --json

# 改写前后对比（同时训练进化引擎）
python3 geo_auditor.py --compare v1.md v2.md

# 导出写作规则给 AI Agent
python3 geo_auditor.py --agent-prompt
```

## 常见问题

**内容会被传到网上吗？** 不会。零网络调用。一切在本地运行。

**和 GPTZero / Originality.ai 有什么区别？** 它们检测文本是不是 AI 写的。GEO Auditor 检测的是 **AI 搜索引用质量**——得分高的内容更容易被 AI 搜索引擎（Perplexity、ChatGPT Search、Google AI Overviews、Claude）引用。

**和 Semrush GEO / Otterly / KIME 有什么区别？** 它们在发布**之后**监测你的品牌是否出现在 AI 回答里。GEO Auditor 在发布**之前**检测你的内容是否可被 AI 引用。倒后镜 vs 前照灯。

**为什么零依赖？** 任何地方都能跑，不需要 `pip install`。只要 Python 3.7+。

## 路线图

- `v0.7` — 多文件批量分析
- `v0.8` — 浏览器插件（一键检测任意网页）
- `v0.9` — Markdown 导出带行内批注
- `v1.0` — 稳定 API + 插件系统文档

## 许可证

MIT · zhibi · [zhibi.xyz](https://zhibi.xyz)
