# Flow 意图识别与推荐机制（基于当前代码）
系统会扫描 `flows/` 下的所有 Flow。当前推荐机制（Match）分为两步：

* **步骤 A：意图提取 (Intent Parsing)**
  * **机制**：优先调用 LLM 将自然语言提取为结构化特征，失败时回退到本地规则解析。
  * **结构字段**：
    * `keywords`
    * `domain`
    * `task_type`
    * `extracted_params`
  * **代码位置**：`app/agent/intent_router.py`

* **步骤 B：打分排序 (Scoring & Ranking)**
  * **机制**：加载 `flows/` 目录下所有 `.md` 文件，读取元信息（`name/description/tags`）后打分。
  * **打分规则**：
    1. **关键词命中**：关键词命中名称/描述/标签，每个命中 `+1.0`
    2. **领域命中**：`domain` 出现在文本中，`+0.8`
    3. **任务类型命中**：`task_type` 出现在文本中，`+0.6`
  * **结果**：
    * `FlowMatcher.match` 默认 `topk=3`
    * `ChatQueryRequest` 默认 `topk=3`，当前前端调用 `/chat/query` 实际传 `topk=1`
    * 因此前端 UI 只拿第一候选
    * 前端再按阈值判定：`score >= 0.8` 走场景1，否则进入场景2
  * **代码位置**：`app/agent/flow_matcher.py`、`app/api/schemas.py`、`ui/index.html`
