from random import Random
from typing import Any

from core.problem_generator import ProblemGenerator


class DivideQuantityInRatioGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        return {
            "part_a": self._sample_discrete(rng, "part_a"),
            "part_b": self._sample_discrete(rng, "part_b"),
            "part_c": self._sample_discrete(rng, "part_c"),
            "total": self._sample_discrete(rng, "total"),
        }

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        part_a = params["part_a"]
        part_b = params["part_b"]
        part_c = params["part_c"]
        total = params["total"]

        sum_of_parts = part_a + part_b + part_c
        unit_value = total / sum_of_parts
        share_b = round(total * part_b / sum_of_parts, 2)

        solution_steps = {
            "part_a": part_a,
            "part_b": part_b,
            "part_c": part_c,
            "total": total,
            "sum_of_parts": sum_of_parts,
            "unit_value": round(unit_value, 4),
            "share_b": share_b,
        }
        return share_b, solution_steps

    def render_problem_text(self, params: dict, template: str) -> str:
        return template.format(**params)
