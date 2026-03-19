# 历史新闻分析示例

## 示例 1：重大货币政策（1 分）

**新闻**： "央行宣布下调存款准备金率0.5个百分点，释放长期资金约1万亿元"

**分析**：
- Score: 1.0
- Category: Regulatory/Policy
- Industry: N/A (Market-wide)
- Key Factors:
  - 降准 (RRR cut) - Major monetary policy
  - 释放资金1万亿元 (Release 1 trillion yuan) - Significant liquidity injection
- Impact Assessment:
  - Major positive market impact
  - Banks can lend more, boosting economic activity
  - Immediate market reaction expected
  - Bullish for financial sector and overall market

**输出**：
```
Score: 1.0
Category: Regulatory/Policy
Industry: N/A
Key Factors: 降准, 释放资金1万亿元
Impact Assessment: Major monetary policy easing, significant liquidity injection, bullish for financial sector and overall market
```

## 示例 2：监管打击（0 分）

**新闻**： "监管部门对某互联网平台企业开展反垄断调查，并处以182亿元罚款"

**分析**：
- Score: 0.0
- Category: Regulatory
- Industry: 科技
- Key Factors:
  - 反垄断调查 (antitrust investigation) - Regulatory crackdown
  - 罚款182亿元 (18.2 billion yuan fine) - Major penalty
- Impact Assessment:
  - Negative for tech sector
  - Regulatory tightening signals
  - Short-term pressure on affected companies
  - Long-term compliance costs increase

**输出**：
```
Score: 0.0
Category: Regulatory
Industry: 科技
Key Factors: 反垄断调查, 罚款182亿元
Impact Assessment: Regulatory crackdown on tech sector, major fine signals tightening, negative short-term impact
```

## 示例 3：房地产政策支持（1 分 + 行业）

**新闻**： "多地放松房地产限购政策，降低首付比例至20%，支持刚性和改善性住房需求"

**分析**：
- Score: 1.0 + 房地产
- Category: Regulatory/Policy
- Industry: 房地产
- Key Factors:
  - 放松限购 (relax purchase restrictions) - Policy easing
  - 降低首付至20% (reduce down payment to 20%) - Major support measure
  - 支持住房需求 (support housing demand) - Explicit policy support
- Impact Assessment:
  - Major positive for real estate sector
  - Boosts housing demand
  - Positive for property developers and related industries
  - Higher weight due to industry-specific policy

**输出**：
```
Score: 1.0 + 房地产
Category: Regulatory/Policy
Industry: 房地产
Key Factors: 放松限购, 降低首付至20%, 支持住房需求
Impact Assessment: Major policy easing for real estate, boosts housing demand, bullish for property developers and related sectors
```

## 示例 4：普通公司新闻（0.5 分）

**新闻**： "某科技公司发布第三季度财报，营收同比增长15%，净利润增长8%"

**分析**：
- Score: 0.5
- Category: Corporate
- Industry: 科技
- Key Factors:
  - 财报 (earnings report) - Routine corporate news
  - 营收增长15% (revenue up 15%) - Moderate growth
  - 净利润增长8% (net profit up 8%) - Moderate growth
- Impact Assessment:
  - Moderate positive for the company
  - Routine earnings report
  - No exceptional performance
  - Limited market-wide impact

**输出**：
```
Score: 0.5
Category: Corporate
Industry: 科技
Key Factors: 财报, 营收增长15%, 净利润增长8%
Impact Assessment: Routine earnings report with moderate growth, limited market-wide impact
```

## 示例 5：无相关新闻（0 分）

**新闻**： "某行业协会召开年度工作会议，总结过去一年工作成果，部署下一年度工作计划"

**分析**：
- Score: 0.0
- Category: N/A
- Industry: N/A
- Key Factors:
  - 行业协会会议 (industry association meeting) - Routine administrative
  - 工作总结 (work summary) - Non-market-moving
  - 工作计划 (work plan) - Routine planning
- Impact Assessment:
  - No market impact
  - Routine administrative update
  - No policy changes or market-moving information

**输出**：
```
Score: 0.0
Category: N/A
Industry: N/A
Key Factors: 行业协会会议, 工作总结, 工作计划
Impact Assessment: Routine administrative update, no market-moving information
```

## 示例 6：国家队增持（1 分）

**新闻**： "国家队通过ETF增持A股，单日净买入超过100亿元"

**分析**：
- Score: 1.0
- Category: Regulatory/Policy
- Industry: N/A (Market-wide)
- Key Factors:
  - 国家队增持 (national team purchases) - Government support
  - ETF增持 (ETF purchases) - Market-wide support
  - 净买入100亿元 (net buy 10 billion yuan) - Significant scale
- Impact Assessment:
  - Major positive market signal
  - Government backing for market
  - Immediate market support
  - Bullish for overall market

**输出**：
```
Score: 1.0
Category: Regulatory/Policy
Industry: N/A
Key Factors: 国家队增持, ETF增持, 净买入100亿元
Impact Assessment: Major government support signal, significant market-wide buying, bullish for overall market
```

## 示例 7：相互冲突的信号（0.5 分）

**新闻**： "央行降准释放流动性，但同时强调房地产调控不放松"

**分析**：
- Score: 0.5
- Category: Regulatory/Policy
- Industry: N/A
- Key Factors:
  - 降准 (RRR cut) - Positive (+1)
  - 房地产调控不放松 (real estate regulation not relaxed) - Negative (-0.5)
  - Net impact: Moderate positive
- Impact Assessment:
  - Mixed signals from policy
  - Liquidity easing is positive
  - Real estate regulation continues
  - Net moderate positive impact

**输出**：
```
Score: 0.5
Category: Regulatory/Policy
Industry: N/A
Key Factors: 降准(+1), 房地产调控不放松(-0.5)
Impact Assessment: Mixed policy signals, liquidity easing positive but real estate regulation continues, net moderate positive
```

## 示例 8：多条新闻（聚合）

**新闻条目**：
1. "央行降准0.5个百分点" (1 point)
2. "某科技公司发布新产品" (0.5 point)
3. "监管部门加强互联网金融监管" (0 point)

**分析**：
- Individual Scores: 1.0, 0.5, 0.0
- Weighted by recency (assuming all recent): 1.0 + 0.5 + 0.0 = 1.5
- Cumulative Impact: Positive overall

**输出**：
```
Individual Scores:
- Item 1: 1.0 (降准)
- Item 2: 0.5 (新产品发布)
- Item 3: 0.0 (加强监管)

Aggregated Score: 1.5
Cumulative Impact: Positive overall, major monetary policy outweighs regulatory tightening
```

## 示例 9：传闻 vs 确认消息

**传闻**： "传闻央行即将降准"
- 评分: 0.5（按传闻折扣处理）
- 状态: 未证实

**确认**： "央行正式宣布降准0.5个百分点"
- 评分: 1.0（满分）
- 状态: 已证实

**分析**：
- 传闻按 0.5 倍折扣计分
- 一旦确认，按满分计算
- 务必核验信息来源与确认状态

## 示例 10：行业级重大政策（1 分 + 行业）

**新闻**： "国家发改委发布新能源汽车产业发展规划，到2025年新能源汽车销量占比达到20%"

**分析**：
- Score: 1.0 + 新能源
- Category: Regulatory/Policy
- Industry: 新能源
- Key Factors:
  - 产业发展规划 (industry development plan) - Major policy
  - 新能源汽车 (new energy vehicles) - Industry-specific
  - 销量占比20% (20% market share target) - Specific target
- Impact Assessment:
  - Major positive for new energy sector
  - Clear policy support and targets
  - Long-term structural impact
  - Bullish for EV manufacturers and supply chain

**输出**：
```
Score: 1.0 + 新能源
Category: Regulatory/Policy
Industry: 新能源
Key Factors: 产业发展规划, 新能源汽车, 销量占比20%
Impact Assessment: Major industry policy support, clear targets for EV adoption, long-term bullish for new energy sector
```

## 分析最佳实践

### 1. 始终核验来源
- 官方政府公告：最高可信度
- 主流财经媒体：较高可信度
- 公司公告：较高可信度
- 社交媒体：低可信度，需用官方来源核验

### 2. 考虑市场环境
- 牛市：正面新闻影响被放大
- 熊市：正面新闻更受重视
- 高波动：所有新闻权重更高

### 3. 评估时效
- 突发新闻：即时影响
- 预定公告：可提前计入预期
- 延迟报道：影响减弱

### 4. 评估影响范围
- 全市场：影响最大
- 行业层面：中高影响
- 个股层面：影响较低

### 5. 检查冲突信号
- 同时识别正负信号
- 判断主导信号
- 给出净评分的理由
