from abc import ABC, abstractmethod
from decimal import Decimal
from random import Random
from typing import Any

from contracts.template_spec import TemplateFile


class ProblemGenerator(ABC):
    """
    Fixed interface every template's generator.py must implement
    (spec.md Section 3).

    Constructed with the template's own loaded spec.yaml (TemplateFile),
    so sample_parameters can read declared min/max/step from
    self.template_file instead of duplicating ranges as hardcoded
    literals inside the generator.
    """

    def __init__(self, template_file: TemplateFile):
        self.template_file = template_file

    @abstractmethod
    def sample_parameters(self, rng: Random) -> dict:
        """Sample values for each parameter within spec.yaml constraints."""

    @abstractmethod
    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        """Return (final_answer, solution_steps) computed from sampled params."""

    @abstractmethod
    def render_problem_text(self, params: dict, template: str) -> str:
        """Fill the chosen template string with sampled param values."""

    def render_image(self, params: dict) -> str | None:
        """Optional. Return an image path, or None if has_image is False.
        Images are drawn programmatically (e.g. matplotlib), never via a
        generative image model."""
        return None

    def _sample_discrete(self, rng: Random, name: str) -> int | float:
        """
        Sample one value for the named parameter from its discrete space:
        min, min + step, min + 2*step, ..., up to max (inclusive if it
        lands exactly on a step boundary). Concrete helper so every
        generator doesn't reimplement this arithmetic independently.
        """
        param = self.template_file.parameters[name]

        step_count = int(round((param.max - param.min) / param.step))
        chosen_step = rng.randint(0, step_count)
        value = param.min + chosen_step * param.step

        if param.type == "int":
            return int(round(value))
        # Round to the step's decimal precision to avoid float drift
        # (e.g. 0.1 + 0.2 style accumulation) leaking into sampled_params.
        decimals = max(0, -Decimal(str(param.step)).as_tuple().exponent)
        return round(value, decimals)