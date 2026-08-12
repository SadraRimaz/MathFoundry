from typing import Any, Literal, Union
from pydantic import BaseModel, ConfigDict

AnswerType = Literal["numeric", "expression", "vector", "matrix", "boolean"]

# Covers all five answer_type variants:
#   numeric    -> int | float
#   expression -> str
#   vector     -> list[float]
#   matrix     -> list[list[float]]
#   boolean    -> bool
# bool is listed before int/float since Python's bool is a subclass of int
# and pydantic (in non-strict mode) would otherwise coerce/match it against
# int first.
FinalAnswer = Union[bool, int, float, str, list]


class Instance(BaseModel):
    """One manufactured problem instance (spec.md Section 1, amended)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    domain: str
    problem_text: str
    image_path: str | None
    final_answer: FinalAnswer
    answer_type: AnswerType
    solution_steps: dict[str, Any]
    sampled_params: dict[str, Any]