# GEO Auditor v0.7.0 开发记录

**日期**：2026-06-24  
**版本**：v0.6.6 → v0.7.0  
**文件**：`geo-auditor.html`（外部版）、`geo_check.html`（内部PM版）、`app.py`（服务端代理）

---

## 一、出发点

v0.6.6 的演化系统存在三个根本问题：

1. **演化只存在于 Python CLI，HTML 版完全没有** — GitHub 标着 Self-Evolving，实际外部版是静态检测器
2. **演化闭环缺改写环节** — 检测→对比→积累→调权，但没有改写，用户得手动拷到 ChatGPT 改完再贴回来
3. **演化主体模糊** — "谁在进化？进化了什么？" 回答不了这个问题，Self-Evolving 就是空话

## 二、核心设计决策

### 2.1 演化主体明确化

**演化的是评分权重，不是检测规则。**

- 14 维检测引擎（正则、计数、阈值）固定不变
- 演化引擎统计每维度改写历史 → 分类（proven/fragile/hard_to_improve/saturated）→ 调整该维度在总分里的乘数
- 大模型只做改写，不参与演化
- 演化引擎是纯数学——统计+分类+调权，不调 API

### 2.2 裸分 vs 加权分分离

**演化 Δ 必须基于裸分计算，不能用加权分。**

原因：如果加权分进入演化，会形成自噬循环——加权分高→Δ小→维度看起来没改善→降权→加权分更高→Δ更小。

`detect()` 现在输出三套数据：
- `rawPct`：裸分（永不被动，演化用这个）
- `adaptivePct`：加权分（展示给用户看）
- `rawDims`：每维裸分数组

### 2.3 对比自动化

**保存即对比，对比即演化。**

改写后保存 → 自动找到上次保存的记录 → 自动对比 → 自动写演化日志 → 自动触发 evolveEngine()。用户不需要知道「对比」这个操作存在。

手动 Compare Tab 保留——跨时间对比或非 AI 改写场景仍需手动选 A/B。

### 2.4 AI 改写定位

**AI 改写是可选快捷键，不是核心能力。**

不接 AI 也能跑完整闭环：自己找任何工具改写→贴回来→检测→保存→自动对比→演化。演化引擎不关心改写从哪来的。

内置改写的唯一价值：省略复制粘贴 + 提示词受控（不点名弱项、含硬约束）。

### 2.5 演化冷启动与安全机制

| 条件 | 行为 |
|------|------|
| < 5 次对比 | 冷启动，不调权，只展示对比 |
| ≥ 5 次对比 | 演化激活，每维度统计 |
| < 8 次改写（单维度） | insufficient_data，保持权重 1.0 |
| 裸分 ≥ 85（单维度） | 饱和锁定，权重 1.0，退出追踪 |
| ≥ 8 次改写 + 改善率≥80% + Δ≥5 | proven，权重 1.15-1.25 |
| 改善率 50-80% | fragile，权重 0.90-1.10 |
| 改善率 < 30% | hard_to_improve，权重 0.85 |
| 连续 3 轮无改善 | 自动重置到 0.95，打破负循环 |

安全约束：±0.05 缓动、0.85 地板、14 维归一化、β 平滑。

### 2.6 提示词设计

**不点名弱项维度 + 含硬约束。**

告诉 AI 哪里弱 → AI 猛攻那里 → 演化数据说那里 proven → 自我实现的预言。

正确做法：
```
你是内容编辑。不告诉你具体弱项，通读全文后自由发挥。
硬约束：
1. 不得新增原文没有的事实、数字、引用、案例
2. 需要数据支撑的地方标注 [需补充数据]，不要编造
3. 不改变品牌、产品、价格、承诺
4. 保持自然人类表达，不要模板化
5. 不要机械堆关键词
```

## 三、代码改动清单

### 3.1 `detect()` 改造

**文件**：`geo_check.html` L460-497、`geo-auditor.html` L550-610

**改动**：
- 函数签名 `detect(text)` → `detect(text, evoWeights)`
- 新增 `rawPct`、`adaptivePct`、`rawDims` 三个输出字段
- 权重只影响 adaptivePct，不影响 rawPct 和 dims[].s

### 3.2 JS 演化引擎（新增 600+ 行）

**文件**：`geo_check.html` L664-795、`geo-auditor.html` L1088-1210

**新增函数**：
- `evolveEngine(includeManual)` — 核心演化逻辑
- `loadLocalEvolutionWeights()` — 读 localStorage 权重
- `EVOLVE_CONFIG` — 所有门槛参数集中管理

**逻辑流程**：
1. 读 `geo_evolution_log`（localStorage）
2. 筛选 ai_rewrite + accepted=true
3. 每维度聚合：改善次数、β改善率、平均Δ、Δ方差、基线裸分
4. 分类判权
5. 归一化到 14
6. 写回 `geo_evolution_state`

### 3.3 AI 改写引擎（新增 180 行）

**文件**：`geo_check.html` L991-1103、`geo-auditor.html` L1180-1221

**新增函数**：
- `REWRITE_SYSTEM_PROMPT` — 提示词常量（含禁止项）
- `buildRewriteUserPrompt(text)` — 组装用户提示
- `aiRewrite()` — 主改写流程（内部版走服务端代理，外部版走 localStorage API Key）

**内部版**：调 `/api/geo/ai-rewrite` → 服务端通过本地 DeepSeek 代理（127.0.0.1:8788）→ DeepSeek API。用户无需填 Key。

**外部版**：用户自配 Key 存 localStorage → 浏览器直连 API。遇 CORS 需配代理地址。

### 3.4 服务端代理端点

**文件**：`app.py` L1103-1155

**路由**：`POST /api/geo/ai-rewrite`

**功能**：接收 text + system_prompt + user_prompt → 通过本地 DeepSeek 代理转发 → 返回 `choices[0].message.content`

**Key 管理**：从 `/opt/pm/deepseek_proxy_config.yaml` 读取（www-data 可读）

### 3.5 自动对比

**文件**：`geo_check.html` L593-650

**新增函数**：
- `autoCompareAfterRewrite(r, content)` — 保存 AI 改写版本后自动对比
- `showAutoCompareResult(before, after, ad, bd)` — 展示对比面板

**触发条件**：`rewriteSource === 'ai_rewrite'` 且上次保存记录在 1 小时内

### 3.6 导入导出

**文件**：`geo-auditor.html` L1003-1053

**新增函数**：
- `exportEvoData()` — 导出演化日志+权重+历史记录为 JSON
- `importEvoData(input)` — 从 JSON 文件导入并合并
- `updateEvoStats()` — 实时显示对比次数和演化状态

**UI**：History Tab 底部显示演化数据面板，含缓存丢失警告 + 导入/导出按钮

### 3.7 中英文 UI 切换

**文件**：`geo-auditor.html` L268-293 + 全文 `data-en`/`data-zh` 属性

**新增函数**：
- `T(en, zh)` — 双语选择函数
- `toggleLang()` — 切换语言
- `applyUILang()` — 遍历所有 `[data-en]` 元素替换文本

**范围**：标题栏、Tab、按钮、提示文案、占位符、Evolution Data 面板、Compare 面板、Footer。检测引擎的维度标签仍自动根据内容语言切换（不受 UI 语言影响）。

### 3.8 对比日志增强

**文件**：`geo_check.html` L896-955

**改动**：
- 日志结构新增 `before_raw`、`after_raw`、`source`、`model`、`accepted` 字段
- `logEvolutionCompare` 双写：服务端 API + localStorage
- 对比后自动触发 `evolveEngine(false)`
- 改写来源追踪：hash 匹配改写内容 → 自动识别 ai_rewrite vs manual_edit

## 四、压测发现并修复的 Bug

### Bug 1 — `L is not defined`（renderResult 崩溃）

**根因**：外部版 `L()` 在 `detect()` 内是局部函数，`renderResult()` 用不到。

**修复**：提取 `_lastIsCN` 全局变量 + `L()` 全局函数（`geo-auditor.html` L372-374）。

### Bug 2 — `_isCN is not defined`（copyResult 崩溃）

**根因**：`copyResult()` 引用了全局 `_isCN`，但外部版从未设置。

**修复**：改为 `_lastIsCN`。

## 五、效果

| 指标 | v0.6.6 | v0.7.0 |
|------|--------|--------|
| 演化能力 | Python CLI only | HTML 全功能 |
| 改写入口 | 手动复制到 ChatGPT | 一键 AI 改写（可选） |
| 对比触发 | 手动四步 | 保存即自动对比 |
| 数据安全 | 清缓存全丢 | 导入/导出 JSON |
| 中文支持 | 仅引擎自适应 | 全 UI 中英切换 |
| 评分体系 | 单一分数 | 裸分+加权分双轨 |

## 六、未解决的问题

1. **浏览器数据丢失** — 外部版 localStorage 清缓存即丢，导入导出是补偿方案，非根治。云端同步可作为 PRO 功能。
2. **演化需要大量对比数据** — 冷启动门槛 5 次，单维度分类门槛 8 次。低频用户可能永远看不到演化效果。
3. **AI 改写 CORS 限制** — 外部版直连大模型 API 可能遇浏览器跨域限制，需用户自配代理。
4. **维度非正交污染** — 改写 Structure 可能附带改善 Readability，统计不绝对干净。v1 不处理。
