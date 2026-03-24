# 场景1全链路说明

**场景1：解析需求 -> 命中已有 Flow -> 用户确认 -> 执行并返回结果**。

---

## 一、场景1的目标与边界

- 场景1优先复用已有 Flow 资产，避免每次重新编排。
- Flow 资产是 Markdown 文件，可读、可审、可版本化。
- 执行器与适配器解耦：同一流程可混合脚本型 skill、LLM 型 skill 与内置转换节点。
- 执行前做契约校验，执行后做结果落盘与回填，保证稳定性与可追溯性。

---

## 二、端到端串联逻辑（前端 -> 后端 -> 前端）

### 1) 用户发起查询

前端 `ui/index.html` 在发送消息时调用：
- `POST /chat/query`
- 请求体：`{ query, topk: 1 }`

后端 `app/api/routes.py` 中 `chat_query` 执行：
1. `IntentRouter.parse(query)`：解析意图、关键词、提取参数（如 `analysis_topic`）。
2. `FlowMatcher.match(intent)`：扫描 `flows/*.md`，用关键词/领域/任务类型打分，返回候选。

返回给前端的数据包括：
- `intent`（结构化意图与提取参数）
- `candidates`（候选 flow_id、name、score、mermaid_code）

### 2) 前端确认卡片

前端拿到候选后：
- 若第一名分数 `>= 0.8`，渲染推荐卡片与 Mermaid 图。
- 用户点击“确认并执行”触发 `executeFlow(flowId)`。

### 3) 执行请求

前端调用：
- `POST /flow/execute`
- 请求体：`{ flow_id, inputs }`

后端在 `flow_execute` 中执行：
1. 通过 `FlowRepository.get_flow(flow_id)` 读取已保存 Flow。
2. 在 `execute_output/<timestamp>/` 创建本次会话目录。
3. 规范化输出路径（防路径穿越，`basename`）。
4. 执行前校验（缺输入/缺来源/前向依赖）。
5. 调用 `FlowExecutor.execute(spec, inputs)` 执行。
6. 将报告落盘并回填 `execution.outputs.context.final_report`。

### 4) 前端展示结果

前端收到 `execution` 后：
- 展示每步状态（success/failed）。
- 从 `execution.outputs.context.final_report` 取最终报告。
- 使用 Markdown 渲染（不可用时自动降级纯文本）。

---

## 三、Flow 文件是如何被读取和解析的

由 `app/storage/flow_repository.py` 负责。

### 1) 列表读取（用于匹配）
- `list_flows()`：扫描 `flow_dir/*.md`。
- `_read_meta()`：读取 frontmatter 中的 `id/name/description/tags`。

### 2) 详情读取（用于执行）
- `get_flow(flow_id)`：按 id 找到文件后读取执行规范。
- `_read_spec()` 优先读取 ```yaml 代码块；没有再读取 ```json 代码块。
- 若 json 是 steps 数组，会自动包装成 `FlowSpec(id,name,steps)`。

---

## 四、底层执行机制（FlowExecutor）

执行器位于 `app/flow_engine/executor.py`，本质是一个顺序 DAG 调度器。

### 1) 上下文模型

执行时维护 `context`：
- `context.inputs`：本次输入
- `context.steps`：每步输出
- `context[step_id]`：便于模板引用
- `context[output_key]`：便于下游按业务键名引用

### 2) 模板渲染

每步执行前先解析 `params` 中模板变量：
- `{{inputs.xxx}}`
- `{{step_id.output_key}}`
- 支持 list/dict 递归解析。

路径查找由 `_lookup_path` 完成，支持：
- 字典路径
- 数组下标
- 含点号 key 的最长匹配（兼容历史 id）。

### 3) 步骤执行

- `task`：执行一次 skill
- `map`：先解析 `items` 为列表，逐项执行 skill，汇总为数组输出

### 4) 出错策略

任一步失败：
- 立即停止后续步骤
- 返回 `status=failed`
- 保留已执行步骤结果用于排障

---

## 五、场景1一条请求的时序

1. UI 输入需求 -> `POST /chat/query`
2. 后端：IntentRouter + FlowMatcher
3. 返回候选 -> UI 渲染推荐卡片
4. 用户点击执行 -> `POST /flow/execute`
5. 后端：FlowRepository 读 spec + 前校验 + FlowExecutor 执行
6. 返回 step_results + final_report
7. UI 渲染步骤状态与 Markdown 报告




