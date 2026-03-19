from fastapi import APIRouter, HTTPException

from app.agent.flow_matcher import FlowMatcher
from app.agent.intent_router import IntentRouter
from app.api.schemas import ChatQueryRequest, ChatQueryResponse, ExecuteFlowRequest, ExecuteFlowResponse
from app.flow_engine.executor import FlowExecutor
from app.storage.flow_repository import FlowRepository


def build_router(repository: FlowRepository) -> APIRouter:
    router = APIRouter()
    intent_router = IntentRouter()
    matcher = FlowMatcher(repository)
    executor = FlowExecutor()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/chat/query", response_model=ChatQueryResponse)
    def chat_query(body: ChatQueryRequest) -> ChatQueryResponse:
        intent = intent_router.parse(body.query)
        candidates = matcher.match(intent, topk=body.topk)
        return ChatQueryResponse(intent=intent, candidates=candidates)

    @router.post("/flow/execute", response_model=ExecuteFlowResponse)
    def flow_execute(body: ExecuteFlowRequest) -> ExecuteFlowResponse:
        try:
            stored = repository.get_flow(body.flow_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        
        # 处理输出路径：创建时间戳文件夹
        import os
        from datetime import datetime
        
        # 基础目录
        base_output_dir = os.path.join(os.getcwd(), "execute_output")
        
        # 生成时间戳子目录 (YYYYMMDDHHMMSS)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_dir = os.path.join(base_output_dir, timestamp)
        
        # 确保目录存在
        os.makedirs(session_dir, exist_ok=True)
        
        # 更新 inputs 中的 output_path
        # 如果原始 inputs 里有 output_path，我们将其重定向到新目录下
        # 如果没有，我们默认创建一个 report.md
        inputs = body.inputs.copy()
        original_filename = inputs.get("output_path", "report.md")
        
        # 确保只取文件名，防止路径穿越
        original_filename = os.path.basename(original_filename)
        
        # 拼接完整绝对路径
        final_output_path = os.path.join(session_dir, original_filename)
        inputs["output_path"] = final_output_path
        
        # 同时将本次会话目录放入 inputs，供 flow 可能需要的其他文件使用
        inputs["_session_dir"] = session_dir
        
        execution = executor.execute(stored.spec, inputs)
        return ExecuteFlowResponse(execution=execution)

    return router
