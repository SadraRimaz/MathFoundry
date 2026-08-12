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
    """
    One entry in spec.yaml's `parameters` block (spec.md Section 3).

    The sampling space is discrete, not continuous: valid values are
    min, min + step, min + 2*step, ..., up to max (inclusive if it lands
    exactly on a step). e.g. min=1, max=50, step=0.5 for half-step values,
    or step=1 for plain integers.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["int", "float"]
    min: float
    max: float
    step: float


class TemplateFile(TemplateSpec):
    """On-disk spec.yaml: TemplateSpec fields + micro-derived parameters."""

    parameters: dict[str, Parameter]