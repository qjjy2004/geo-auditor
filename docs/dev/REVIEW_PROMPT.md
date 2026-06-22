这是 GEO Auditor v0.6.2，一个开源的 AI 搜索内容质量检测器。请做全面的 Bug Review + 运行逻辑验证。

## 项目简介
14 维度检测 + 6 信号去 AI 化 + Agent 驱动的自我进化系统（--evolve → 动态权重 → detect() 自适应评分）。纯 Python 3.7+，零外部依赖。支持中英双语。MIT 协议开源。

## 核心文件
- geo_auditor.py（1935行，核心引擎）
- geo-auditor.html（779行，网页版界面）
- example_config.json（配置模板）
- README.md（设计文档）

## 请你做的事

### 1. 逻辑 Bug 扫描
- 逐函数阅读 geo_auditor.py，检查 14 个维度的评分逻辑
- extract_topic_phrases() 中文 ngram 提取
- generate_rewrite_hint() 阈值判断
- generate_agent_prompt() 是否正确映射 dimension_principles
- 评分归一化逻辑（各维度 0-100 是否真正可比）

### 2. 运行逻辑验证（重点 — 必须实际跑代码）
这是我最关心的部分。进化闭环的被设计为：
  --evolve → 生成 evolution_state.json（含维度权重 + stale/proven/fragile 标记）
  → detect() 自动读取 → stale 维度中和到60%max，proven 维度托底到70%max

请设计并执行以下验证：

A. 闭环基础验证
   1. 清空 evolution.jsonl，跑 --evolve，确认 evolution_state.json 为空且 detect() 退化到默认权重
   2. 手工构造 3-5 条检测日志到 evolution.jsonl（含明确的高分/低分模式），跑 --evolve
   3. 检查 evolution_state.json 是否正确生成权重，stale/proven/fragile 标记是否合理
   4. 用同一段文本跑 detect()，对比进化前和进化后的评分差异 — 评分应该有变化

B. 权重机制验证
   1. stale 维度：构造日志让某维度长期无信号 → --evolve → 确认标记为 stale → detect() 中该维度是否被中和（不超过60% max权重）
   2. proven 维度：构造日志让某维度持续高分 → --evolve → 确认标记为 proven → detect() 中该维度是否被托底（不低于70% max权重）
   3. fragile 维度：构造日志让某维度波动大 → --evolve → 确认标记为 fragile → detect() 行为

C. 进化方向验证
   1. 跑 3 轮：检测 → 记录日志 → 进化 → 再检测 → 再记录 → 再进化
   2. 检查权重是否收敛（而非发散或震荡）
   3. 检查总评分趋势是否合理

D. 多语言一致性
   1. 中英文同一含义的文本，评分是否接近
   2. 进化后，中英文权重是否一致

### 3. 边界条件
- 空文本、纯空格、单字、超长文本(>10000字)
- 纯英文/纯中文/混合文本
- 标题缺失、evolution.jsonl 为空/只有1条/有损坏行
- 纯标点/emoji

### 4. 数据流
- log_detection() 和 log_compare() JSONL 合法性
- CLI 和 HTML 评分一致性（同一段文本两个入口跑）
- burstiness / sentence_diversity 计算
- --compare 对比模式评分是否合理

### 5. 安全
- --file / --config 路径遍历
- innerHTML 安全（HTML 版）
- JSON 解析异常处理

### 6. 代码质量
- 死代码、重复逻辑、函数职责
- 1935 行单文件是否该拆分

## 测试命令
```
python3 geo_auditor.py --text "测试内容" --title "测试标题"
python3 geo_auditor.py --compare --text "原文" --rewrite "改写"
python3 geo_auditor.py --evolve
python3 geo_auditor.py --agent-prompt
python3 geo_auditor.py --file test.txt
```

每个问题标注：文件、行号、描述、严重程度（严重/中等/轻微）、修复建议。

最重要的输出：闭环是否真的在"进化"（权重是否根据数据调整、评分是否因此变得更准），还是只是看起来在动但实际上没有方向性改进。
