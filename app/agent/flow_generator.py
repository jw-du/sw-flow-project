import json
import re
from typing import Any, Dict, List
from pydantic import BaseModel
from app.core.llm import LLMClient
from app.agent.skill_registry import skill_registry

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
4. 返回的仅仅是 JSON 文本。
"""

    def generate(self, user_request: str) -> GeneratedFlow:
        skills_context = skill_registry.get_skills_prompt_context()
        prompt = self.system_prompt.replace("{skills_context}", skills_context)

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"请为以下需求生成执行计划：\n{user_request}"}
        ]

        response = LLMClient.chat_completion(
            messages=messages,
            temperature=0.2 # 降低随机性以保证 JSON 格式正确
        )
        
        content = response.choices[0].message.content.strip()
        
        # 尝试提取 JSON
        json_str = content
        if "```json" in content:
            match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                json_str = match.group(1)
        elif "```" in content:
            match = re.search(r"```\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                json_str = match.group(1)
                
        try:
            flow_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM 未返回合法的 JSON: {e}\nRaw Content:\n{content}")

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

    def _generate_mermaid(self, flow_data: Dict[str, Any]) -> str:
        lines = ["graph TD", "    Start[开始] --> Inputs{输入参数}"]
        
        steps = flow_data.get("steps", [])
        if not steps:
            lines.append("    Inputs --> End[结束]")
            return "\n".join(lines)

        prev_node = "Inputs"
        for i, step in enumerate(steps):
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
