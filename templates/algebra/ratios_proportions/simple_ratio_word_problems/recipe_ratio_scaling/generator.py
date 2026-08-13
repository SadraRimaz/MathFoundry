from random import Random
from typing import Any

from core.problem_generator import ProblemGenerator


class RecipeRatioScalingGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        return {
            "orig_a": self._sample_discrete(rng, "orig_a"),
            "orig_b": self._sample_discrete(rng, "orig_b"),
            "new_a": self._sample_discrete(rng, "new_a"),
        }

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        orig_a = params["orig_a"]
        orig_b = params["orig_b"]
        new_a = params["new_a"]

        scale_factor = new_a / orig_a
        new_b = round(orig_b * scale_factor, 2)

        return new_b, {
            "scale_factor": round(scale_factor, 4),
            "new_amount_b": new_b,
        }

    def render_problem_text(self, params: dict, template: str) -> str:
        return template.format(**params)
