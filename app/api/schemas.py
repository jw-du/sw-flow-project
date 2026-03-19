from typing import Any

from pydantic import BaseModel, Field

from app.agent.flow_matcher import FlowCandidate
from app.agent.intent_router import IntentResult
from app.flow_engine.models import FlowExecutionResult


class ChatQueryRequest(BaseModel):
    query: str
    topk: int = 3


class ChatQueryResponse(BaseModel):
    intent: IntentResult
    candidates: list[FlowCandidate] = Field(default_factory=list)


class ExecuteFlowRequest(BaseModel):
    flow_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)


class ExecuteFlowResponse(BaseModel):
    execution: FlowExecutionResult
