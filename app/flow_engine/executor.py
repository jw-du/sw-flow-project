from __future__ import annotations

import json
import re
from typing import Any

from app.flow_engine.models import FlowExecutionResult, FlowSpec, StepResult
from app.flow_engine.adapters.llm_prompt import LlmPromptAdapter
from app.flow_engine.adapters.python_script import PythonScriptAdapter


class FlowExecutor:
    def execute(self, flow: FlowSpec, user_input: dict[str, Any]) -> FlowExecutionResult:
        context: dict[str, Any] = {"input": user_input, "inputs": user_input, "steps": {}}
        results: list[StepResult] = []
        for step in flow.steps:
            try:
                if step.type == "map" and step.items:
                    items = self._resolve_value(step.items, context)
                    if not isinstance(items, list):
                        items = [items]
                    
                    step_output = []
                    for item in items:
                        iter_context = context.copy()
                        iter_context["item"] = item
                        
                        resolved_params = self._resolve_value(step.params, iter_context)
                        res = self._run_skill(step.skill, resolved_params, iter_context)
                        step_output.append(res)
                    
                    output = step_output
                else:
                    resolved_params = self._resolve_value(step.params, context)
                    output = self._run_skill(step.skill, resolved_params, context)
                
                context["steps"][step.id] = output
                context[step.id] = {"output": output}
                if step.output_key:
                    context[step.output_key] = output
                    context[step.id][step.output_key] = output
                results.append(StepResult(step_id=step.id, status="success", output=output))
                
            except Exception as exc:
                results.append(StepResult(step_id=step.id, status="failed", error=str(exc)))
                return FlowExecutionResult(
                    flow_id=flow.id,
                    status="failed",
                    step_results=results,
                    outputs={"context": context},
                )
        return FlowExecutionResult(
            flow_id=flow.id,
            status="success",
            step_results=results,
            outputs={"context": context},
        )

    def _run_skill(self, skill: str, params: dict[str, Any], context: dict[str, Any]) -> Any:
        if skill.startswith("builtin."):
            return self._run_builtin(skill, params, context)

        py_adapter = PythonScriptAdapter(skill)
        script_path = py_adapter.find_script()
        if script_path:
            return py_adapter.execute(params, context)

        llm_adapter = LlmPromptAdapter(skill)
        if llm_adapter.load_prompt():
            return llm_adapter.execute(params, context)

        raise ValueError(f"unsupported skill: {skill}")

    def _run_builtin(self, skill: str, params: dict[str, Any], context: dict[str, Any]) -> Any:
        if skill == "builtin.echo":
            return {"text": params.get("text", "")}
        if skill == "builtin.collect":
            keys = params.get("keys", [])
            return {k: context.get(k) for k in keys}
        if skill == "builtin.json":
            payload = params.get("payload", {})
            return json.loads(json.dumps(payload, ensure_ascii=False))
        raise ValueError(f"unsupported skill: {skill}")

    def _resolve_value(self, value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, str):
            return self._resolve_template(value, context)
        if isinstance(value, list):
            return [self._resolve_value(v, context) for v in value]
        if isinstance(value, dict):
            return {k: self._resolve_value(v, context) for k, v in value.items()}
        return value

    def _resolve_template(self, text: str, context: dict[str, Any]) -> Any:
        pattern = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
        matches = pattern.findall(text)
        if not matches:
            return text
        if len(matches) == 1 and text.strip() == "{{" + matches[0] + "}}":
            return self._lookup_path(context, matches[0].strip())
        resolved = text
        for match in matches:
            value = self._lookup_path(context, match.strip())
            resolved = resolved.replace(f"{{{{{match}}}}}", str(value))
            resolved = resolved.replace(f"{{{{ {match} }}}}", str(value))
        return resolved

    def _lookup_path(self, data: dict[str, Any], path: str) -> Any:
        cursor: Any = data
        parts = path.split(".")
        for part in parts:
            if isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            elif isinstance(cursor, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(cursor):
                    cursor = cursor[idx]
                else:
                    raise KeyError(f"index out of range: {idx} in path {path}")
            else:
                raise KeyError(f"path not found: {path} at part {part}")
        return cursor
