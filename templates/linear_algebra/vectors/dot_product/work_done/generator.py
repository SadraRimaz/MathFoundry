from random import Random
from typing import Any

from core.problem_generator import ProblemGenerator


class DotProductWorkDoneGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        force_x = self._sample_discrete(rng, "force_x")
        force_y = self._sample_discrete(rng, "force_y")
        while force_x == 0 and force_y == 0:
            force_x = self._sample_discrete(rng, "force_x")
            force_y = self._sample_discrete(rng, "force_y")

        displacement_x = self._sample_discrete(rng, "displacement_x")
        displacement_y = self._sample_discrete(rng, "displacement_y")
        while displacement_x == 0 and displacement_y == 0:
            displacement_x = self._sample_discrete(rng, "displacement_x")
            displacement_y = self._sample_discrete(rng, "displacement_y")

        return {
            "force_x": force_x,
            "force_y": force_y,
            "displacement_x": displacement_x,
            "displacement_y": displacement_y,
        }

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        force_x = params["force_x"]
        force_y = params["force_y"]
        displacement_x = params["displacement_x"]
        displacement_y = params["displacement_y"]

        term_x = force_x * displacement_x
        term_y = force_y * displacement_y
        work = term_x + term_y

        solution_steps = {
            "force_x": force_x,
            "force_y": force_y,
            "displacement_x": displacement_x,
            "displacement_y": displacement_y,
            "term_x": term_x,
            "term_y": term_y,
            "work": work,
        }
        return work, solution_steps

    def render_problem_text(self, params: dict, template: str) -> str:
        return template.format(**params)
