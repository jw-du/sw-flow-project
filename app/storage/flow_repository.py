from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.flow_engine.models import FlowSpec


class FlowMeta(BaseModel):
    id: str
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    path: str


class StoredFlow(BaseModel):
    meta: FlowMeta
    spec: FlowSpec


class FlowRepository:
    def __init__(self, flow_dir: str):
        self.flow_dir = Path(flow_dir)

    def list_flows(self) -> list[FlowMeta]:
        return [self._read_meta(path) for path in sorted(self.flow_dir.glob("*.md"))]

    def get_flow(self, flow_id: str) -> StoredFlow:
        for path in sorted(self.flow_dir.glob("*.md")):
            meta = self._read_meta(path)
            if meta.id == flow_id:
                spec = self._read_spec(path)
                return StoredFlow(meta=meta, spec=spec)
        raise FileNotFoundError(f"flow not found: {flow_id}")

    def _read_meta(self, file_path: Path) -> FlowMeta:
        content = file_path.read_text(encoding="utf-8")
        meta = self._parse_front_matter(content)
        return FlowMeta(
            id=meta.get("id", file_path.stem),
            name=meta.get("name", file_path.stem),
            description=meta.get("description", ""),
            tags=meta.get("tags", []),
            path=str(file_path),
        )

    def _read_spec(self, file_path: Path) -> FlowSpec:
        content = file_path.read_text(encoding="utf-8")
        
        # 优先尝试读取 yaml 块
        yaml_block = self._extract_code_block(content, "yaml")
        if yaml_block:
            spec_data: dict[str, Any] = yaml.safe_load(yaml_block)
            return FlowSpec.model_validate(spec_data)
            
        # 兼容读取 json 块（例如旧的执行计划格式）
        json_block = self._extract_code_block(content, "json")
        if json_block:
            import json
            steps_data = json.loads(json_block)
            # 兼容：如果 json 只包含 steps 数组，需要包装一层
            if isinstance(steps_data, list):
                meta = self._read_meta(file_path)
                spec_data = {
                    "id": meta.id,
                    "name": meta.name,
                    "steps": steps_data
                }
            else:
                spec_data = steps_data
            return FlowSpec.model_validate(spec_data)
            
        raise ValueError(f"flow spec block (yaml or json) not found in {file_path}")

    def _parse_front_matter(self, content: str) -> dict[str, Any]:
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return {}
        data = yaml.safe_load(match.group(1))
        if isinstance(data, dict):
            return data
        return {}

    def _extract_code_block(self, content: str, lang: str) -> str | None:
        pattern = re.compile(rf"```{lang}\n(.*?)\n```", re.DOTALL)
        match = pattern.search(content)
        if not match:
            return None
        return match.group(1)
