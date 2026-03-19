# SW-flow-project

Python 轻量 Agent Flow 项目，面向投研场景，优先支持：

1. 用户提需求后检索已有 Flow。
2. 命中后用户确认执行。
3. 执行并返回结构化结果。

## 当前能力

- FastAPI 服务骨架
- 场景 1 检索与执行 API
- 本地 Flow 仓库扫描
- 基础 Flow 执行器
- Docker 打包与 compose 启动

## 快速启动

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -U pip
pip install -e .
uvicorn app.main:app --reload --port 8080
```

首次运行前请准备环境变量：

```bash
copy .env.example .env
```

然后在 `.env` 中填写 `LLM_API_KEY`、`LLM_MODEL`。

打开 `http://localhost:8080/ui/index.html` 使用前端界面。  
打开 `http://localhost:8080/docs` 查看接口文档。

## 环境自检

```bash
python scripts/doctor.py
```

## LLM 连通性测试

```bash
python scripts/test_llm.py
```

## Flow 测试

```bash
python test_flow.py
```

## Docker 启动

```bash
docker compose up --build
```

服务默认运行在 `http://localhost:8080`。

## 项目文档

- 规划文档：`docs/project-plan.md`
- 架构说明：`docs/architecture.md`
