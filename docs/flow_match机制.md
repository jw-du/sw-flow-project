
# Flow意图识别与推荐机制
**会扫描所有的 Flow**。目前的推荐机制（Match）分为两步：

*   **步骤 A：意图提取 (Intent Parsing)**
    *   **机制**：调用 LLM（DeepSeek），把你的自然语言（比如“帮我看看房地产”）提取为结构化特征：
        *   `keywords`: `["房地产", "政策", "利好"]`
        *   `domain`: `industry_research`
        *   `task_type`: `analysis`
    *   代码位置：`app/agent/intent_router.py`

*   **步骤 B：打分排序 (Scoring & Ranking)**
    *   **机制**：加载 `flows/` 目录下**所有**的 `.md` 文件，读取它们的元数据（name, description, tags）。
    *   **打分规则**：
        1.  **关键词命中**：用户关键词出现在 Flow 名称/描述中，每个词 `+1.0` 分（权重最高）。
        2.  **领域匹配**：`domain` 相同（如都是“行业研究”），`+0.8` 分。
        3.  **任务类型匹配**：`task_type` 相同（如都是“分析”），`+0.6` 分。
    *   **结果**：按总分降序排列，取 **Top 3** 返回给你。
    *   代码位置：`app/agent/flow_matcher.py`
