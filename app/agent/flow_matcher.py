import re
from pathlib import Path

from pydantic import BaseModel, Field

from app.agent.intent_router import IntentResult
from app.storage.flow_repository import FlowMeta, FlowRepository


class FlowCandidate(BaseModel):
    flow_id: str
    name: str
    score: float
    reason: str
    tags: list[str] = Field(default_factory=list)
    mermaid_code: str | None = None


class FlowMatcher:
    def __init__(self, repository: FlowRepository):
        self.repository = repository

    def match(self, intent: IntentResult, topk: int = 3) -> list[FlowCandidate]:
        flows = self.repository.list_flows()
        scored = [self._score_flow(intent, flow) for flow in flows]
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:topk]

    def _score_flow(self, intent: IntentResult, flow: FlowMeta) -> FlowCandidate:
        text = f"{flow.name} {flow.description} {' '.join(flow.tags)}".lower()
        score = 0.0
        hits: list[str] = []
        for keyword in intent.keywords:
            if keyword and keyword in text:
                score += 1.0
                hits.append(keyword)
        if intent.domain in text:
            score += 0.8
        if intent.task_type in text:
            score += 0.6
        reason = "关键词命中: " + ", ".join(hits[:4]) if hits else "基于主题与标签弱匹配"
        mermaid_code = None
        try:
            flow_content = Path(flow.path).read_text(encoding="utf-8")
            m = re.search(r"```mermaid\n(.*?)\n```", flow_content, re.DOTALL)
            if m:
                mermaid_code = m.group(1).strip()
        except Exception:
            pass

        return FlowCandidate(
            flow_id=flow.id,
            name=flow.name,
            score=round(score, 2),
            reason=reason,
            tags=flow.tags,
            mermaid_code=mermaid_code,
        )
