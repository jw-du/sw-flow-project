import yaml
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SkillMeta(BaseModel):
    name: str
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    skill_type: str = "execution"
    has_script: bool = False
    path: str

class SkillRegistry:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: Dict[str, SkillMeta] = {}
        self.refresh()

    def refresh(self):
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
                meta_dict = self._parse_frontmatter(content)
                name = meta_dict.get("name", skill_dir.name)
                has_script = any((skill_dir / "scripts").glob("*.py"))
                self.skills[name] = SkillMeta(
                    name=name,
                    description=str(meta_dict.get("description", "")),
                    inputs=meta_dict.get("inputs", {}) if isinstance(meta_dict.get("inputs", {}), dict) else {},
                    outputs=meta_dict.get("outputs", {}) if isinstance(meta_dict.get("outputs", {}), dict) else {},
                    skill_type=str(meta_dict.get("skill_type", "execution")).lower(),
                    has_script=bool(has_script),
                    path=str(skill_md_path)
                )
            except Exception as e:
                print(f"Failed to parse {skill_md_path}: {e}")

    def get_all_skills(self) -> List[SkillMeta]:
        return list(self.skills.values())

    def get_execution_skills(self) -> List[SkillMeta]:
        return [s for s in self.get_all_skills() if s.skill_type != "planning"]

    def get_skill(self, skill_name: str) -> SkillMeta | None:
        return self.skills.get(skill_name)

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        yaml_content = parts[1]
        try:
            parsed = yaml.safe_load(yaml_content) or {}
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            result: dict[str, Any] = {}
            for line in yaml_content.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key in {"name", "description", "skill_type"} and value:
                    result[key] = value
            return result

    def _output_fields(self, outputs: dict[str, Any]) -> list[str]:
        if not isinstance(outputs, dict):
            return []
        fields = outputs.get("fields")
        if isinstance(fields, list):
            return [str(x) for x in fields]
        schema = outputs.get("schema")
        if isinstance(schema, dict):
            props = schema.get("properties")
            if isinstance(props, dict):
                return [str(k) for k in props.keys()]
        return []

    def get_skills_prompt_context(self) -> str:
        lines = ["## 可用技能 Contract 列表：\n"]
        for skill in self.get_execution_skills():
            lines.append(f"### Skill: `{skill.name}`")
            lines.append(f"- **描述**: {skill.description}")
            if skill.inputs:
                lines.append("- **输入参数 (inputs)**:")
                for k, v in skill.inputs.items():
                    if isinstance(v, dict):
                        req = "必填" if v.get("required") else "可选"
                        desc = v.get("description", "")
                        lines.append(f"  - `{k}` ({v.get('type', 'any')}): {desc} [{req}]")
                    else:
                        lines.append(f"  - `{k}` (any): [{v}]")
            if skill.outputs:
                out_desc = skill.outputs.get("description", "") if isinstance(skill.outputs, dict) else ""
                lines.append(f"- **输出说明 (outputs)**: {out_desc}")
                fields = self._output_fields(skill.outputs)
                if fields:
                    lines.append(f"- **可引用输出字段**: {', '.join(fields)}")
            lines.append("")
        return "\n".join(lines)

# 全局单例
skill_registry = SkillRegistry()
