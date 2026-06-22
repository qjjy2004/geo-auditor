这是 GEO Auditor v0.6.0，一个开源的 AI 搜索内容质量检测器。请做全面的 Bug Review。

## 项目简介
14 维度检测 + 6 信号去 AI 化 + Agent 驱动的自我进化系统。纯 Python 3.7+，零外部依赖。支持中英双语。

## 请你做的事

### 1. 逻辑 Bug 扫描
- 逐函数阅读 geo_auditor.py，检查 14 个维度的评分逻辑是否有误
- 检查 extract_topic_phrases() 的中文 ngram 提取是否正确
- 检查 generate_rewrite_hint() 的阈值判断
- 检查 evolve_detector() 的数据聚合逻辑
- 检查 generate_agent_prompt() 是否正确映射 dimension_principles

### 2. 边界条件测试
- 空文本、纯空格、单字文本
- 超长文本（>10000 字）
- 纯英文、纯中文、混合文本
- 标题缺失时各维度行为
- evolution.jsonl 为空时各项命令的行为

### 3. 数据流检查
- log_detection() 和 log_compare() 的 JSONL 是否合法
- evolve_detector() 读取 JSONL 时的容错
- --compare、--evolve、--agent-prompt 的输出一致性
- voice_details 中 burstiness 和 sentence_diversity 的计算

### 4. 安全审查
- 文件读写路径（--file、--config）是否有路径遍历风险
- innerHTML 使用是否安全（HTML 版）
- JSON 解析的异常处理

### 5. 代码质量
- 死代码 / 未使用变量
- 函数职责是否单一
- 重复逻辑

## 测试方法
你可以用 Python 执行 geo_auditor.py 来做实际测试。核心文件：
- geo_auditor.py（1675行，核心引擎）
- geo-auditor.html（664行，网页版）
- README.md（设计文档）

请逐项检查，发现的每个问题标注：文件、行号、问题描述、严重程度（严重/中等/轻微）。
