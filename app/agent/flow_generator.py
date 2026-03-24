import json
import re
from typing import Any, Dict, List
from pydantic import BaseModel
from app.core.llm import LLMClient
from app.agent.skill_registry import skill_registry

# MVP阶段，支持部分技能
# 后期若需去掉白名单机制，把 skills_context = self._build_mvp_skills_context() 改为 skills_context = skill_registry.get_skills_prompt_context()
# 注释/删除这段：- if not self._is_mvp_safe(flow_data): ...fallback...

MVP_SAFE_SKILLS = {
    "eastmoney-calendar",
    "bing_search",
    "industry-keywords",
    "industry-news-sentiment",
    "market-environment",
}

class GeneratedFlow(BaseModel):
    name: str
    description: str
    inputs: Dict[str, Any]
    steps: List[Dict[str, Any]]
    mermaid_code: str
    raw_json: str

class FlowGenerator:
    def __init__(self):
        self.system_prompt = """你是一个高级工作流（Agentic Flow）编排专家。你的任务是根据用户的需求，利用系统中已有的底层技能（Skills），自动生成一个执行计划（DAG）。

你的输出必须是合法的 JSON 格式，不要包含任何多余的 Markdown 标记（如果使用了 ```json 包装，请确保内容是纯 JSON）。

JSON 结构必须严格遵循以下格式：
{
  "name": "工作流名称（简短，如：国内市场情绪研判）",
  "description": "工作流的一句话描述",
  "inputs": {
    "输入参数的键名 (如 analysis_topic)": {
      "type": "string / number 等",
      "description": "参数说明",
      "required": true
    }
  },
  "steps": [
    {
      "id": "唯一的步骤ID，如 step_1_search",
      "name": "步骤的自然语言描述",
      "type": "task 或 map（如果是对数组循环执行，请使用 map）",
      "skill": "使用的 skill 名称",
      "params": {
        "参数名": "参数值。可以使用 {{inputs.参数名}} 引用全局输入，或使用 {{上一个步骤的id.输出键名}} 引用上游结果。如果是 map 类型，可以用 {{item}} 引用当前循环项。"
      },
      "items": "{{上一个步骤的id.输出键名}}", // 仅当 type 为 map 时需要，指定要循环的数组
      "output_key": "当前步骤输出结果要保存的上下文键名，供后续步骤引用"
    }
  ]
}

以下是系统中可用的 Skills 列表，你只能使用这些 Skills 进行编排：
{skills_context}

请注意：
1. 步骤之间的依赖关系通过 {{}} 模板语法隐式表达。
2. 确保步骤的逻辑连贯，例如先提取关键词 -> 再搜索 -> 再分析。
3. 请尽可能复用系统提供的 Skills。
4. 只允许引用 Skills Contract 中声明的输入与输出字段。
5. 当上下游字段不一致时，优先插入内置适配节点：builtin.pick / builtin.rename / builtin.flatten / builtin.to_text。
6. step.id 只能使用字母、数字、下划线，禁止使用点号 "."。
7. 返回的仅仅是 JSON 文本。
"""

    def generate(self, user_request: str) -> GeneratedFlow:
        try:
            skills_context = self._build_mvp_skills_context()
            prompt = self.system_prompt.replace("{skills_context}", skills_context)

            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请为以下需求生成执行计划：\n{user_request}"}
            ]

            response = LLMClient.chat_completion(
                messages=messages,
                temperature=0.2
            )
            content = (response.choices[0].message.content or "").strip()
            json_str = content
            if "```json" in content:
                match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
                if match:
                    json_str = match.group(1)
            elif "```" in content:
                match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
                if match:
                    json_str = match.group(1)
            flow_data = json.loads(json_str)
        except Exception:
            flow_data = self._fallback_flow_data(user_request)
            json_str = json.dumps(flow_data, ensure_ascii=False)

        flow_data = self._normalize_step_ids(flow_data)
        if not self._is_mvp_safe(flow_data):
            flow_data = self._fallback_flow_data(user_request)
            flow_data = self._normalize_step_ids(flow_data)
        json_str = json.dumps(flow_data, ensure_ascii=False)

        # 生成 Mermaid 图
        mermaid_code = self._generate_mermaid(flow_data)

        return GeneratedFlow(
            name=flow_data.get("name", "未命名 Flow"),
            description=flow_data.get("description", ""),
            inputs=flow_data.get("inputs", {}),
            steps=flow_data.get("steps", []),
            mermaid_code=mermaid_code,
            raw_json=json_str
        )

    def _build_mvp_skills_context(self) -> str:
        lines = ["## 可用技能 Contract 列表：\n"]
        for name in sorted(MVP_SAFE_SKILLS):
            skill = skill_registry.get_skill(name)
            if not skill:
                continue
            lines.append(f"### Skill: `{skill.name}`")
            lines.append(f"- **描述**: {skill.description}")
            if skill.inputs:
                lines.append("- **输入参数 (inputs)**:")
                for k, v in skill.inputs.items():
                    if isinstance(v, dict):
                        req = "必填" if v.get("required") else "可选"
                        desc = v.get("description", "")
                        lines.append(f"  - `{k}` ({v.get('type', 'any')}): {desc} [{req}]")
            if skill.outputs and isinstance(skill.outputs, dict):
                out_desc = skill.outputs.get("description", "")
                if out_desc:
                    lines.append(f"- **输出说明 (outputs)**: {out_desc}")
            lines.append("")
        return "\n".join(lines)

    def _is_mvp_safe(self, flow_data: Dict[str, Any]) -> bool:
        steps = flow_data.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            return False
        for step in steps:
            if not isinstance(step, dict):
                return False
            step_id = str(step.get("id", ""))
            if "." in step_id:
                return False
            skill = str(step.get("skill", ""))
            if skill.startswith("builtin."):
                continue
            if skill not in MVP_SAFE_SKILLS:
                return False
            payload = {"params": step.get("params"), "items": step.get("items")}
            text = json.dumps(payload, ensure_ascii=False)
            if "{{builtin." in text or "{{ builtin." in text:
                return False
        return True

    def _normalize_step_ids(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        steps = flow_data.get("steps", [])
        if not isinstance(steps, list):
            return flow_data
        old_to_new: dict[str, str] = {}
        used: set[str] = set()
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            old_id = str(step.get("id", f"step_{i+1}"))
            base = re.sub(r"[^a-zA-Z0-9_]", "_", old_id)
            if not base:
                base = f"step_{i+1}"
            new_id = base
            idx = 1
            while new_id in used:
                idx += 1
                new_id = f"{base}_{idx}"
            used.add(new_id)
            old_to_new[old_id] = new_id
            step["id"] = new_id
        flow_data["steps"] = [self._rewrite_refs(s, old_to_new) for s in steps]
        return flow_data

    def _rewrite_refs(self, value: Any, id_map: Dict[str, str]) -> Any:
        if isinstance(value, str):
            out = value
            for old_id, new_id in id_map.items():
                out = re.sub(r"\{\{\s*" + re.escape(old_id) + r"(?=\.)", "{{" + new_id, out)
                out = re.sub(r"\{\{\s*" + re.escape(old_id) + r"\s*\}\}", "{{" + new_id + "}}", out)
            return out
        if isinstance(value, list):
            return [self._rewrite_refs(v, id_map) for v in value]
        if isinstance(value, dict):
            return {k: self._rewrite_refs(v, id_map) for k, v in value.items()}
        return value

    def _fallback_flow_data(self, user_request: str) -> Dict[str, Any]:
        return {
            "name": "临时生成-重磅事件与避险分析",
            "description": f"基于日历与新闻对市场避险情况进行研判：{user_request}",
            "inputs": {
                "analysis_topic": {
                    "type": "string",
                    "description": "分析主题",
                    "required": True
                },
                "forward_days": {
                    "type": "number",
                    "description": "未来日历窗口天数",
                    "required": False,
                    "default": 7
                },
                "lookback_days": {
                    "type": "number",
                    "description": "新闻回溯天数",
                    "required": False,
                    "default": 7
                },
                "output_path": {
                    "type": "string",
                    "description": "报告输出路径",
                    "required": False
                }
            },
            "steps": [
                {
                    "id": "step_1_calendar",
                    "name": "获取近期财经日历与会议",
                    "skill": "eastmoney-calendar",
                    "params": {
                        "size": 100
                    },
                    "output_key": "calendar_data"
                },
                {
                    "id": "step_2_search",
                    "name": "检索重磅冲突与避险新闻",
                    "skill": "bing_search",
                    "params": {
                        "_positional": ["{{inputs.analysis_topic}} 重磅会议 冲突 资金避险", 8]
                    },
                    "output_key": "news_results"
                },
                {
                    "id": "step_3_environment",
                    "name": "生成市场环境与避险分析报告",
                    "skill": "market-environment",
                    "params": {
                        "output_path": "{{inputs.output_path}}"
                    },
                    "output_key": "final_report"
                }
            ]
        }

    def _generate_mermaid(self, flow_data: Dict[str, Any]) -> str:
        lines = ["graph TD", "    Start[开始] --> Inputs{输入参数}"]
        
        steps = flow_data.get("steps", [])
        visible_steps = []
        for s in steps:
            skill_name = str(s.get("skill", ""))
            if skill_name.startswith("builtin."):
                continue
            visible_steps.append(s)
        if not visible_steps:
            lines.append("    Inputs --> End[结束]")
            return "\n".join(lines)

        prev_node = "Inputs"
        for i, step in enumerate(visible_steps):
            step_id = step.get("id", f"step_{i}")
            step_name = step.get("name", step_id)
            skill_name = step.get("skill", "unknown")
            node_type = "map" if step.get("type") == "map" else "task"
            
            node_label = f"{step_name} ({skill_name})"
            if node_type == "map":
                node_label = f"{step_name} [Map: {skill_name}]"

            node_key = self._sanitize_node_id(f"N_{step_id}")
            safe_label = self._sanitize_label(node_label)
            lines.append(f'    {prev_node} --> {node_key}["{safe_label}"]')
            prev_node = node_key
            
        lines.append(f"    {prev_node} --> End[结束]")
        return "\n".join(lines)

    def _sanitize_node_id(self, node_id: str) -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", node_id)
        if not sanitized:
            sanitized = "N_step"
        if sanitized[0].isdigit():
            sanitized = f"N_{sanitized}"
        return sanitized

    def _sanitize_label(self, label: str) -> str:
        label = str(label).replace("\n", " ").replace("\r", " ")
        label = label.replace("[", "（").replace("]", "）")
        label = label.replace("{", "（").replace("}", "）")
        label = label.replace('"', "“")
        label = label.replace("\\", "/")
        label = label.replace("|", "｜")
        return label
