from typing import Literal

from pydantic import BaseModel, ConfigDict

from contracts.instance import AnswerType


class TemplateSpec(BaseModel):
    """Macro agent's non-technical template spec (spec.md Section 2)."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    domain: str
    name: str
    description: str
    has_image: bool
    answer_type: AnswerType
    problem_text_templates: list[str]


class Parameter(BaseModel):
    """One entry in spec.yaml's `parameters` block (spec.md Section 3)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["int", "float"]
    min: float
    max: float


class TemplateFile(TemplateSpec):
    """On-disk spec.yaml: TemplateSpec fields + micro-derived parameters."""

    parameters: dict[str, Parameter]