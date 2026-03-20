import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel

class SkillMeta(BaseModel):
    name: str
    description: str
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}
    path: str

class SkillRegistry:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, SkillMeta] = {}
        self.refresh()

    def refresh(self):
        """扫描 skills 目录下的所有 SKILL.md，解析 YAML frontmatter"""
        self.skills.clear()
        if not self.skills_dir.exists():
            return

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md_path = skill_dir / "SKILL.md"
            if not skill_md_path.exists():
                continue

            try:
                content = skill_md_path.read_text(encoding="utf-8")
                if content.startswith("---"):
                    # 提取 YAML frontmatter
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        meta_dict = yaml.safe_load(yaml_content) or {}
                        
                        name = meta_dict.get("name", skill_dir.name)
                        self.skills[name] = SkillMeta(
                            name=name,
                            description=meta_dict.get("description", ""),
                            inputs=meta_dict.get("inputs", {}),
                            outputs=meta_dict.get("outputs", {}),
                            path=str(skill_md_path)
                        )
            except Exception as e:
                print(f"Failed to parse {skill_md_path}: {e}")

    def get_all_skills(self) -> List[SkillMeta]:
        return list(self.skills.values())

    def get_skills_prompt_context(self) -> str:
        """格式化所有 skill 为一段用于注入 LLM prompt 的文本"""
        lines = ["## 可用的底层技能 (Skills) 列表：\n"]
        for skill in self.get_all_skills():
            lines.append(f"### Skill: `{skill.name}`")
            lines.append(f"- **描述**: {skill.description}")
            if skill.inputs:
                lines.append("- **输入参数 (inputs)**:")
                for k, v in skill.inputs.items():
                    req = "必填" if v.get("required") else "可选"
                    desc = v.get("description", "")
                    lines.append(f"  - `{k}` ({v.get('type', 'any')}): {desc} [{req}]")
            if skill.outputs:
                out_desc = skill.outputs.get("description", "")
                lines.append(f"- **输出说明 (outputs)**: {out_desc}")
            lines.append("")
        return "\n".join(lines)

# 全局单例
skill_registry = SkillRegistry()
