import importlib.util
import inspect
from pathlib import Path

import yaml

from contracts.template_spec import TemplateFile
from contracts.validate import validate_template_file
from core.problem_generator import ProblemGenerator


def load_template_file(template_path: str) -> TemplateFile:
    """
    Read <template_path>/spec.yaml, validate its shape (Section 3) and
    its placeholder/parameter agreement (Section 2 rule). Raises on any
    failure — no silent fallback.
    """
    spec_yaml_path = Path(template_path) / "spec.yaml"
    with open(spec_yaml_path, "r") as f:
        raw = yaml.safe_load(f)

    return validate_template_file(raw)


def load_generator(template_path: str, template_file: TemplateFile) -> ProblemGenerator:
    """
    Dynamically import <template_path>/generator.py and instantiate the
    single ProblemGenerator subclass it defines. "One template maps to
    exactly one generator, always" (spec.md) is enforced here: zero or
    more than one matching class both raise ValueError.
    """
    generator_py_path = Path(template_path) / "generator.py"

    module_name = f"_mathfoundry_template_{Path(template_path).name}"
    spec = importlib.util.spec_from_file_location(module_name, generator_py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    candidates = [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if issubclass(obj, ProblemGenerator) and obj is not ProblemGenerator
    ]

    if len(candidates) == 0:
        raise ValueError(
            f"{generator_py_path} defines no ProblemGenerator subclass"
        )
    if len(candidates) > 1:
        names = ", ".join(c.__name__ for c in candidates)
        raise ValueError(
            f"{generator_py_path} defines multiple ProblemGenerator subclasses "
            f"({names}) — exactly one generator per template is required"
        )

    generator_class = candidates[0]
    return generator_class(template_file)


def load_template(template_path: str) -> ProblemGenerator:
    """Convenience wrapper: spec.yaml + generator.py -> ready generator instance."""
    template_file = load_template_file(template_path)
    return load_generator(template_path, template_file)