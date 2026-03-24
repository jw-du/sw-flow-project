**方案名称**
- 场景2自由编排的 Skill IO 对齐治理方案

**问题描述**
- 自动编排需要将多个 Skill 串成可执行 DAG。
- 但现有 Skill 存在两类特性冲突：
  - **描述/指导类 Skill**（MD Prompt 型）输出不稳定、语义化强；
  - **执行类 Skill**（脚本/API 型）要求输入输出字段稳定、可校验。
- 直接混用会导致：
  - 上下游字段名不一致（`results` vs `items`）；
  - 类型不一致（string/list/object）；
  - 缺失输入参数（运行时才报错）；
  - 编排成功但执行失败。

---

**总体思路**
- 采用 **Contract-first（契约优先）**：
  - 编排看 skill contract，不看自由文本；
  - 执行调用真实 skill 内容实现，但必须满足 contract；
  - 执行前做校验，缺参可追问用户；
  - 对不齐时通过“适配节点”做结构转换。

---

**核心设计**

- **Skill 双层模型**
  - **Contract 层（确定性）**：`inputs schema`、`outputs schema`、required/default、可选 alias。
  - **Implementation 层（灵活性）**：`scripts`、`SKILL.md`、`references`、Prompt 逻辑。

- **Skill 分类**
  - **Execution Skill**：可进入执行 DAG 主链路，必须有稳定 output schema。
  - **Planning Skill**：用于生成策略/关键词/分析框架，不直接作为关键执行依赖；必要时后接“结构化节点”。

- **Flow 编排规则**
  - LLM 编排时仅消费“技能 registry + contract 摘要”。
  - Flow 中跨节点引用只能引用 contract 里声明字段。
  - 不允许直接依赖未声明输出字段。

- **执行前校验（Validate）**
  - 校验 `{{inputs.xxx}}` 是否完整；
  - 校验 `{{stepA.xxx}}` 的来源是否存在、是否前向依赖；
  - 基于已注册 skill contract 做字段对齐检查，输出 `field_mismatch` 风险；
  - 返回结构化结果：`missing_inputs` / `missing_sources` / `field_mismatch` / `forward_refs`。

- **适配节点（Adapter Nodes）**
  - 预置高频转换器：`pick`、`rename`、`flatten`、`to_text`、`json`。
  - 编排时优先插入预置转换器对齐上下游。
  - 无合适转换器时，当前 MVP阶段采取回退稳定模板策略，未来改为允许“临时转换节点（LLM 生成）”，跑通后可沉淀为正式 skill。

- **缺参追问用户（Human-in-the-loop）**
  - 对 `missing_inputs` 返回前端追问表单/弹窗；
  - 用户补参后自动重试执行；
  - 后续可加默认值记忆和字段级 UI 组件（date/number/file）。


