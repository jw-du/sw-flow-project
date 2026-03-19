import json
from pathlib import Path
from typing import Any

from app.flow_engine.adapters.base import SkillAdapter
from app.core.llm import LLMClient


class LlmPromptAdapter(SkillAdapter):
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.skill_dir = Path("skills") / skill_name
        
    def execute(self, params: dict[str, Any], context: dict[str, Any]) -> Any:
        prompt = self.load_prompt()
        if not prompt:
            raise FileNotFoundError(f"No prompt file found for skill {self.skill_name}")
            
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(params, ensure_ascii=False)}
        ]
        
        output_type = params.get("output_type", "text")
        
        response = LLMClient.chat_completion(messages=messages)
        content = response.choices[0].message.content or ""
        
        if output_type == "json_array":
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                return json.loads(content)
            except Exception:
                return content

        output_file = params.get("output_file") or params.get("output_path")
        if isinstance(output_file, str) and output_file.strip():
            Path(output_file.strip()).write_text(content, encoding="utf-8")
        
        return content

    def load_prompt(self) -> str | None:
        p = self.skill_dir / "SKILL.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return None
