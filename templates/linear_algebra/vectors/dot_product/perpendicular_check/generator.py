from random import Random
from typing import Any

from core.problem_generator import ProblemGenerator


class DotProductPerpendicularCheckGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        v1_x = self._sample_discrete(rng, "v1_x")
        v1_y = self._sample_discrete(rng, "v1_y")
        while v1_x == 0 and v1_y == 0:
            v1_x = self._sample_discrete(rng, "v1_x")
            v1_y = self._sample_discrete(rng, "v1_y")

        if rng.random() < 0.5:
            # Exact integer-perpendicular identity: for any k,
            # v1 . (-v1_y*k, v1_x*k) == 0. k = +-1 keeps v2's components a
            # sign-flipped permutation of v1's, so they stay in range and
            # inherit v1's coverage without extra clamping.
            k = rng.choice([1, -1])
            v2_x = -v1_y * k
            v2_y = v1_x * k
        else:
            v2_x = self._sample_discrete(rng, "v2_x")
            v2_y = self._sample_discrete(rng, "v2_y")
            while v2_x == 0 and v2_y == 0:
                v2_x = self._sample_discrete(rng, "v2_x")
                v2_y = self._sample_discrete(rng, "v2_y")

        return {"v1_x": v1_x, "v1_y": v1_y, "v2_x": v2_x, "v2_y": v2_y}

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        v1_x, v1_y = params["v1_x"], params["v1_y"]
        v2_x, v2_y = params["v2_x"], params["v2_y"]

        dot_product = v1_x * v2_x + v1_y * v2_y
        is_perpendicular = dot_product == 0

        solution_steps = {
            "v1": [v1_x, v1_y],
            "v2": [v2_x, v2_y],
            "dot_product": dot_product,
            "is_perpendicular": is_perpendicular,
        }
        return is_perpendicular, solution_steps

    def render_problem_text(self, params: dict, template: str) -> str:
        return template.format(**params)
