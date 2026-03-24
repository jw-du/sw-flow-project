# 场景2 全链路说明（基于当前代码）

本**场景2：未命中已有 Flow 时，系统动态编排临时 Flow 并执行**。

---

## 一、场景2的目标与触发条件

- 目标：当 `flows/` 中没有高匹配流程时，自动基于技能库临时生成可执行 Flow，保证用户任务不中断。
- 前端触发条件：`/chat/query` 返回候选为空，或第一候选分数 `< 0.8`。
- 典型交互：
  - 用户发问题 -> 系统提示“未找到完全匹配工作流”
  - 用户点击“让 AI 自动生成”
  - 系统返回临时 Flow + Mermaid
  - 用户确认执行，必要时补齐参数
  - 可选“一键保存”沉淀为长期资产

---

## 二、前后端全链路串联

## 1) 用户发起查询

前端调用：
- `POST /chat/query`

后端执行：
1. `IntentRouter.parse` 解析意图
2. `FlowMatcher.match` 计算已有 Flow 匹配分

前端决策：
- `score >= 0.8`：走场景1推荐执行
- `score < 0.8`：进入场景2动态编排

---

## 2) 动态编排

前端调用：
- `POST /flow/generate`
- 请求体：`{ query }`

后端 `routes.py -> flow_generate`：
1. 实例化 `FlowGenerator`
2. 调用 `generate(query)`
3. 返回：
   - `name`
   - `description`
   - `inputs`（输入 contract）
   - `steps`（执行计划）
   - `mermaid_code`
   - `raw_json`

前端行为：
- 渲染“动态生成 Flow”卡片
- Mermaid 渲染（失败则降级展示步骤列表）
- 展示“执行此工作流 / 一键保存 / 取消”按钮

---

## 3) 执行前检查

前端调用：
- `POST /flow/validate`
- 请求体包含：
  - `flow_id: "temp_generated_flow"`
  - `steps`
  - `inputs`
  - `input_schema`

后端校验项（`routes.py`）：
- `missing_inputs`：缺少 `{{inputs.xxx}}`
- `missing_sources`：引用不存在的来源
- `forward_refs`：引用了后续步骤（前向依赖）
- `field_mismatch`：字段与上游输出 contract 不对齐（风险提示）

当前阻断策略：
- `missing_inputs` / `missing_sources` / `forward_refs` 为阻断项
- `field_mismatch` 为风险项（提示但可继续）

---

## 4) 临时 Flow 执行

前端调用：
- `POST /flow/execute`
- `flow_id` 固定为 `temp_generated_flow`
- body 中直接传 `steps`（不依赖本地 flow 文件）

后端 `flow_execute`：
1. 将 `steps` 转成 `FlowSpec`
2. 合并输入默认值（`_merge_inputs_with_schema`）
3. 执行前校验（见上）
4. 创建 `execute_output/<timestamp>/` 会话目录
5. 重定向 `output_path` 到该目录
6. 调用 `FlowExecutor.execute(spec, inputs)`
7. 若有报告文本则落盘
8. 从落盘文件读回 UTF-8 内容回填到 `context.final_report`

返回：
- `execution.status`
- `execution.step_results`
- `execution.outputs.context`
- `saved_report_path`
- `session_dir`

---

## 5) 资产沉淀Flow保存

前端点击“一键保存”调用：
- `POST /flow/save`

后端保存逻辑：
1. 组装 frontmatter（`name/description/inputs/skills`）
2. 组装 Mermaid 代码块和执行步骤 JSON 代码块
3. 清理文件名并写入 `flows/`

结果：
- 临时 Flow 转为长期可复用 `flows/*.md`
- 后续可被场景1直接匹配命中

---

## 三、动态编排器（FlowGenerator）底层机制

文件：`app/agent/flow_generator.py`

### 1) 主路径：LLM 生成 JSON DAG

1. 构建系统提示词（含 Skills Contract）
2. 调用 LLM 生成 Flow JSON
3. 解析代码块中的 JSON
4. 生成 Mermaid

### 2) MVP 稳定性增强（当前重点）

#### a) 白名单技能

`MVP_SAFE_SKILLS` 只允许：
- eastmoney-calendar
- bing_search
- industry-keywords
- industry-news-sentiment
- market-environment

#### b) 安全上下文注入

生成时注入的是 `_build_mvp_skills_context()`，而不是全量技能。

#### c) Step ID 规范化

自动将 step.id 规范为 `[a-zA-Z0-9_]`，并同步重写模板引用，避免含 `.` 的路径解析问题。

#### d) 不安全结果回退

若生成结果包含非白名单 skill、非法 step.id 或 builtin 隐式引用，自动回退到 `_fallback_flow_data()` 的稳定模板。

#### e) 生成失败兜底

LLM 调用异常时直接使用 fallback flow，避免前端空白。

---

## 四、执行层机制（FlowExecutor）在场景2的作用

文件：`app/flow_engine/executor.py`

执行器对场景2与场景1完全一致：
- 支持 `task` / `map`
- 模板解析 `{{...}}`
- 上下文写回 `context.inputs / context.steps / context[output_key]`

技能分发优先级：
1. `builtin.*` -> 内置执行
2. `PythonScriptAdapter` -> 脚本型 skill
3. `LlmPromptAdapter` -> prompt 型 skill

任一步失败即中断并返回 `failed`。


---

## 七、场景2一条请求时序

1. 用户输入需求 -> `/chat/query`
2. 未命中高分 Flow -> 前端展示“让 AI 自动生成”
3. 用户点击生成 -> `/flow/generate`
4. 返回临时 steps + mermaid -> 前端渲染确认卡片
5. 点击执行 -> `/flow/validate`
6. 缺输入则补参，字段风险仅警告
7. `/flow/execute` 执行临时 Flow
8. 返回步骤状态 + final_report 并展示
9. 可选 `/flow/save` 保存为 `flows/*.md`


