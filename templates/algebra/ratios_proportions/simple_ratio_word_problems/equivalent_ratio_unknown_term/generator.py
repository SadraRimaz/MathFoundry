from fractions import Fraction
from random import Random
from typing import Any

from core.problem_generator import ProblemGenerator


class EquivalentRatioUnknownTermGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        return {
            "a": self._sample_discrete(rng, "a"),
            "b": self._sample_discrete(rng, "b"),
            "c": self._sample_discrete(rng, "c"),
        }

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        a = params["a"]
        b = params["b"]
        c = params["c"]

        exact = Fraction(c * b, a)
        x = round(float(exact), 2)

        solution_steps = {
            "a": a,
            "b": b,
            "c": c,
            "cross_product": c * b,
            "exact_fraction": f"{exact.numerator}/{exact.denominator}",
            "x": x,
        }
        return x, solution_steps

    def render_problem_text(self, params: dict, template: str) -> str:
        return template.format(**params)
