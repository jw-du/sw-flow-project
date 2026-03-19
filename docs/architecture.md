# SW-flow-project 架构设计

## 1. 设计原则

- 小内核：核心仅保留意图识别、Flow 匹配、Flow 执行
- 可插拔：LLM、检索、工具调用都通过适配器扩展
- 可审阅：Flow 使用 Markdown + Mermaid 存储与展示
- 可交付：默认支持 Docker 化打包试用

## 2. 分层结构

### API 层

- `/chat/query`：接收用户需求，返回候选 Flow
- `/flow/execute`：执行用户确认的 Flow
- `/health`：健康检查

### Agent 层

- `intent_router`：提取需求关键词、领域标签、任务类型
- `flow_matcher`：在本地 Flow 库中检索并排序候选

### 执行层

- `flow_engine.models`：FlowSpec 与 StepSpec
- `flow_engine.executor`：顺序执行节点，管理上下文变量

### 存储层

- `storage.flow_repository`：扫描 `flows/` 目录，读取 metadata

## 3. 场景 1 主链路

1. 用户提问
2. Intent Router 解析意图
3. Flow Matcher 检索 TopK
4. 前端展示候选 Flow 与匹配理由
5. 用户确认 flow_id
6. 执行引擎运行
7. 返回执行摘要与步骤结果

## 4. 目录约定

- `flows/*.md`：Flow 定义文件
- `app/api`：接口定义
- `app/agent`：意图与匹配
- `app/flow_engine`：执行器与模型
- `app/storage`：Flow 仓库读写

## 5. 扩展点

- 语义检索：增加向量索引模块替换 matcher 排序策略
- 工具执行：支持 Python Script / HTTP / MCP 统一适配
- 人机编排：增加可视化编辑与 Flow 回写
