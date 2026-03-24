# SW-flow-project
## 项目介绍
### 投研平台交互流程：从“对话”到“资产”

本流程的核心在于**“逻辑的显性化”**，即不让 AI 成为黑盒，而是让分析师通过 Flow 审阅和编排，掌握逻辑的主导权。

### 1. 意图规划阶段：逻辑的“初稿”生成

* **输入**：分析师输入复杂的投研需求（如：“对比 A 股白酒龙头近三年的现金流质量，并归因其估值波动”）。
* **规划**：意图规划 Agent 进行需求理解和初步拆解
* **匹配**：根据需求，匹配已有的 Flow 模版

若没有匹配到，系统会提示用户“暂无相关 Flow 模版”。
* **编排**：检索skills目录，根据需求，形成新的 Flow
输出：
   1. **文字解释**：说明分析步骤。
   2. **Flow 有向图**：使用 **Markdown + Mermaid** 格式生成流程图，展示数据抓取、财务建模、逻辑对齐等节点。
* **审阅**：流程图实时渲染，分析师可直观看到 AI 的“思考路径”。


### 2. 交互编排阶段：人机协同的逻辑修正
* **反馈修正**：用户通过文字要求调整（如：“不要只看现金流，加入对预收账款的分析”），Agent 实时重新规划flow。
* **升级方案 (GUI 编排)**：
* 系统提供类似 **Coze** 的节点拖拽界面。
* 分析师可以手动连接不同的 **Skill** 节点，或修改节点的输入输出参数。
* **核心意义**：将“对话逻辑”转化为了可复用的**“逻辑模版”**。


### 3. 任务执行阶段：Skill 与 Kit 的联动
一旦 Flow 被采纳，后台将进入自动化执行层：
* **能力映射**：Flow 中的每一个节点被映射到具体的 **Skill**（说明书）上。
* **代码调用**：通过 **Kit**（组件包）执行底层代码，通过MCP连接 Wind、聚源或内部数据库获取数据。

### 4. 内容沉淀阶段：投资笔记载体
* **编辑器链接**：最终生成的分析结论、图表和推演过程存入关联的 **Markdown 编辑器**（类似 Trae、Obsidian）。
* **双向交互**：
* 分析师在编辑器中手动修改一段结论。
* **反向触发**：编辑器中的修改可反馈回系统循环，系统询问：“是否需要基于您的修改更新对应的 Flow 逻辑？”。
* **资产打包**：最终确认的 Flow、Skill 和相关 Kit 被打包成一个 **Plugin**，作为可分发的制品。


## Demo
## 1. 功能概览
轻量投研 Agent Flow 平台，主要实现以下核心环节：

1. 用户自然语言提问
2. 检索并推荐已有 Flow（场景1）
3. 未命中时动态生成临时 Flow（场景2），支持资产化存储
4. 用户确认后执行，输出Markdown 报告并保存至本地

内容包含：
- FastAPI 后端 + 前端 UI（`ui/index.html`）
- Flow 仓库扫描与匹配（`flows/*.md`）
- DAG 执行器（支持 task/map、模板变量解析）
- 多 Skill 适配（Python 脚本 / LLM Prompt / builtin）
- 临时 Flow 一键保存到 `flows/`
- 执行产物落盘到 `execute_output/<timestamp>/`

---

## 2. 本地复现

### 2.1 环境要求
- Python >= 3.10（推荐 3.11）
- 可访问配置的 LLM 服务（默认 DeepSeek OpenAI-compatible）

### 2.2 安装依赖
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -e .
```

### 2.3 配置环境变量
```bash
copy .env.example .env
```
确认以下配置：
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `FLOW_DIR`（默认 `flows`）

`.env.example` 位置：`./.env.example`

### 2.4 启动服务
```bash
uvicorn app.main:app --reload
```
访问常用入口（根路由会自动跳转到 UI）：`http://127.0.0.1:8000`

### 2.5 Prompt示例
```
分析一下房地产的市场情绪。
搜索分析接下来几天是否有重磅会议(如美联储议息等)，以及是否刚发生过重磅冲突，资金避险情况如何?
```

---


## 3. 项目核心文件

### 3.1 后端核心

```text
app/
├─ main.py # 入口层：应用入口、路由注册、UI挂载
├─ api/  # 接口层
│  ├─ routes.py  # 核心API：query/generate/validate/execute/save
│  └─ schemas.py  # 请求/响应数据模型
├─ agent/ # 模型层
│  ├─ intent_router.py  # 用户意图解析，自然语言拆成关键词、任务类型、参数
│  ├─ flow_matcher.py  # 场景1已有Flow匹配策略
│  ├─ flow_generator.py  # 场景2Flow动态编排
│  └─ skill_registry.py  # Skill contract读取与整理
├─ flow_engine/ # 执行层
│  ├─ executor.py  # DAG执行器：模板解析、调用skill（builtin / python 脚本 / prompt）
│  ├─ models.py  # 执行计划模型，定义 FlowStep、执行结果等结构
│  └─ adapters/
│     ├─ python_script.py  # Python脚本型Skill适配
│     └─ llm_prompt.py  # Prompt型Skill适配
├─ storage/  # flow仓库访问层
│  └─ flow_repository.py  # 扫描列出所有flow元信息、读取指定flow、解析frontmatter+代码块（yaml/json）变成可执行结构
└─ core/ # 基础配置层
   ├─ config.py  # 配置中心（.env映射）
   └─ llm.py  # LLM客户端封装
```

### 3.2 前端核心

```text
ui/
└─ index.html  # 单页前端：匹配、生成、校验、执行、保存、结果展示
```

### 3.3 资产与定义

```text
flows/
├─ *.md   # 可复用Flow定义（frontmatter + mermaid + 执行计划）
skills/
├─ <skill_name>/SKILL.md  # 技能说明与contract
└─ <skill_name>/scripts/*.py  # 技能底层实现脚本

docs/
├─ 场景1-匹配已有flow.md  
├─ 场景2-自主编排flow.md  
├─ flow_match机制.md
└─ flow-skill编排对齐方案.md  
```
