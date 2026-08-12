from string import Formatter

from contracts.instance import Instance
from contracts.template_spec import TemplateFile, TemplateSpec


def validate_instance(data: dict) -> Instance:
    """Validate a raw dict against the Instance contract (Section 1)."""
    return Instance.model_validate(data)


def validate_template_spec(data: dict) -> TemplateSpec:
    """Validate a raw dict against the macro TemplateSpec contract (Section 2)."""
    return TemplateSpec.model_validate(data)


def validate_template_file(data: dict) -> TemplateFile:
    """
    Validate a raw dict against the on-disk spec.yaml contract (Section 3),
    then check that its problem_text_templates placeholders and its
    parameters block agree (spec.md Section 2: placeholders are the source
    of truth for parameter names). Raises ValueError on mismatch.
    """
    template_file = TemplateFile.model_validate(data)

    mismatches = check_placeholders_match_parameters(template_file)
    if mismatches:
        raise ValueError(
            f"spec.yaml placeholder/parameter mismatch: {'; '.join(mismatches)}"
        )

    return template_file


def check_placeholders_match_parameters(template_file: TemplateFile) -> list[str]:
    """
    Compare {name} placeholders used across problem_text_templates against
    the declared parameters. Returns a list of mismatch descriptions
    (empty list means everything agrees).
    """
    placeholder_names: set[str] = set()
    for text in template_file.problem_text_templates:
        for _, field_name, _, _ in Formatter().parse(text):
            if field_name:
                placeholder_names.add(field_name)

    parameter_names = set(template_file.parameters.keys())

    mismatches = []
    for name in sorted(placeholder_names - parameter_names):
        mismatches.append(
            f"placeholder '{name}' used in problem_text_templates but not declared in parameters"
        )
    for name in sorted(parameter_names - placeholder_names):
        mismatches.append(
            f"parameter '{name}' declared but never used in any problem_text_templates"
        )

    return mismatches