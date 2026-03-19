from typing import Any

from pydantic import BaseModel, Field


class StepSpec(BaseModel):
    id: str
    name: str
    type: str = "task"
    skill: str
    params: dict[str, Any] = Field(default_factory=dict)
    items: str | list[Any] | None = None  # For map type steps
    depends_on: list[str] = Field(default_factory=list)
    output_key: str | None = None


class FlowSpec(BaseModel):
    id: str
    name: str
    description: str | None = None
    steps: list[StepSpec]


class StepResult(BaseModel):
    step_id: str
    status: str
    output: Any = None
    error: str | None = None


class FlowExecutionResult(BaseModel):
    flow_id: str
    status: str
    step_results: list[StepResult]
    outputs: dict[str, Any] = Field(default_factory=dict)
