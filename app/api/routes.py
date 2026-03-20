from fastapi import APIRouter, HTTPException

from app.agent.flow_matcher import FlowMatcher
from app.agent.intent_router import IntentRouter
from app.agent.flow_generator import FlowGenerator
from app.api.schemas import (
    ChatQueryRequest, ChatQueryResponse, 
    ExecuteFlowRequest, ExecuteFlowResponse,
    GenerateFlowRequest, GenerateFlowResponse,
    SaveFlowRequest
)
from app.flow_engine.executor import FlowExecutor
from app.flow_engine.models import FlowSpec, StepSpec
from app.storage.flow_repository import FlowRepository
import os
import re
import yaml
from datetime import datetime

def _default_input_value(key: str, schema: dict) -> object:
    if "default" in schema:
        return schema["default"]
    input_type = str(schema.get("type", "")).lower()
    if input_type in {"number", "integer", "float"}:
        return 7 if "day" in key.lower() else 0
    if input_type in {"boolean", "bool"}:
        return False
    if input_type in {"array", "list"}:
        return []
    if input_type in {"object", "dict"}:
        return {}
    return ""

def _merge_inputs_with_schema(inputs: dict, input_schema: dict | None) -> dict:
    merged = dict(inputs or {})
    if not isinstance(input_schema, dict):
        return merged
    for key, schema in input_schema.items():
        if key in merged:
            continue
        if not isinstance(schema, dict):
            merged[key] = ""
            continue
        merged[key] = _default_input_value(key, schema)
    return merged

def _collect_required_input_refs(steps: list[StepSpec]) -> list[str]:
    pattern = re.compile(r"\{\{\s*inputs\.([a-zA-Z0-9_]+)\s*\}\}")
    required: set[str] = set()
    for step in steps:
        payload = {
            "params": step.params,
            "items": step.items,
        }
        text = str(payload)
        for m in pattern.findall(text):
            required.add(m)
    return sorted(required)


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
        if body.flow_id == "temp_generated_flow" and body.steps:
            # 动态生成的临时 Flow
            steps = [StepSpec(**s) for s in body.steps]
            spec = FlowSpec(id="temp_generated_flow", name="临时生成Flow", steps=steps)
        else:
            try:
                stored = repository.get_flow(body.flow_id)
                spec = stored.spec
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
        inputs = _merge_inputs_with_schema(body.inputs, body.input_schema)
        missing_inputs = [k for k in _collect_required_input_refs(spec.steps) if k not in inputs]
        if missing_inputs:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "执行前校验失败：存在缺失输入参数",
                    "missing_inputs": missing_inputs,
                },
            )
        original_filename = inputs.get("output_path", "report.md")
        
        # 确保只取文件名，防止路径穿越
        original_filename = os.path.basename(original_filename)
        
        # 拼接完整绝对路径
        final_output_path = os.path.join(session_dir, original_filename)
        inputs["output_path"] = final_output_path
        
        # 同时将本次会话目录放入 inputs，供 flow 可能需要的其他文件使用
        inputs["_session_dir"] = session_dir
        
        execution = executor.execute(spec, inputs)

        report_text = None
        ctx = execution.outputs.get("context", {}) if isinstance(execution.outputs, dict) else {}
        if isinstance(ctx, dict):
            candidate = ctx.get("final_report")
            if candidate is None and execution.step_results:
                last_ok = next((s for s in reversed(execution.step_results) if s.status == "success"), None)
                if last_ok is not None:
                    step_data = ctx.get("steps", {}).get(last_ok.step_id) if isinstance(ctx.get("steps"), dict) else None
                    candidate = step_data
            if isinstance(candidate, str):
                report_text = candidate
            elif isinstance(candidate, dict):
                if isinstance(candidate.get("text"), str):
                    report_text = candidate.get("text")
                elif isinstance(candidate.get("final_report"), str):
                    report_text = candidate.get("final_report")

        if report_text and not os.path.exists(final_output_path):
            with open(final_output_path, "w", encoding="utf-8") as f:
                f.write(report_text)

        if isinstance(execution.outputs, dict):
            execution.outputs["saved_report_path"] = final_output_path
            execution.outputs["session_dir"] = session_dir

        return ExecuteFlowResponse(execution=execution)

    @router.post("/flow/generate", response_model=GenerateFlowResponse)
    def flow_generate(body: GenerateFlowRequest) -> GenerateFlowResponse:
        generator = FlowGenerator()
        try:
            generated = generator.generate(body.query)
            return GenerateFlowResponse(
                name=generated.name,
                description=generated.description,
                inputs=generated.inputs,
                steps=generated.steps,
                mermaid_code=generated.mermaid_code,
                raw_json=generated.raw_json
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/flow/save")
    def flow_save(body: SaveFlowRequest):
        try:
            # 构建 Markdown 内容
            frontmatter = {
                "name": body.name,
                "description": body.description,
                "inputs": body.inputs,
                "skills": list({s.get("skill") for s in body.steps if s.get("skill")})
            }
            
            yaml_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
            
            import json
            steps_json = json.dumps(body.steps, ensure_ascii=False, indent=2)
            
            md_content = f"---\n{yaml_str}---\n\n# {body.name}\n\n{body.description}\n\n## 流程图 (Visualization)\n\n```mermaid\n{body.mermaid_code}\n```\n\n## 执行步骤 (Execution Plan)\n\n```json\n{steps_json}\n```\n"
            
            # 确保目录存在
            os.makedirs(repository.flow_dir, exist_ok=True)

            # 保存文件 (清理文件名)
            import re
            safe_name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5_-]', '-', body.name).lower()
            if not safe_name:
                safe_name = "untitled-flow"
            filename = f"{safe_name}.md"
            filepath = os.path.join(str(repository.flow_dir), filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md_content)
                
            return {"status": "success", "file": filename}
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail={"message": str(e)})

    return router
