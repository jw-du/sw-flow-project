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
    steps: list[dict[str, Any]] | None = None  # for temporary generated flows
    input_schema: dict[str, Any] | None = None


class ExecuteFlowResponse(BaseModel):
    execution: FlowExecutionResult


class GenerateFlowRequest(BaseModel):
    query: str


class GenerateFlowResponse(BaseModel):
    name: str
    description: str
    inputs: dict[str, Any]
    steps: list[dict[str, Any]]
    mermaid_code: str
    raw_json: str


class SaveFlowRequest(BaseModel):
    name: str
    description: str
    inputs: dict[str, Any]
    steps: list[dict[str, Any]]
    mermaid_code: str
