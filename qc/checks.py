import json
from collections import Counter

from contracts.template_spec import TemplateFile

DUPLICATE_THRESHOLD = 0
DIVERSITY_MIN_FRACTION = 0.30
RANGE_COVERAGE_MIN_FRACTION = 0.70
TEMPLATE_MAX_SHARE = 0.80


def _hashable_key(value) -> str:
    """Hashable JSON key for a value that may be unhashable (list, dict) —
    used for both final_answer (vector/matrix) and sampled_params."""
    return json.dumps(value, sort_keys=True)


def check_exact_duplicates(instances: list[dict], template_file: TemplateFile) -> dict:
    """
    Exact duplicates. Threshold: 0 tolerated (spec.md Section 5).

    Key depends on has_image:
    - has_image=False: (problem_text, final_answer) — text is the actual
      content, exactly as spec.md defines it.
    - has_image=True: (sampled_params, final_answer) instead. The image
      itself is not inspected (out of scope — no image comparison), and
      problem_text is typically fixed/near-fixed caption text carrying no
      discriminating information for these templates, so using it as part
      of the duplicate key would under-detect (or, as observed, flag
      coincidental non-duplicates: different sampled_params that happen to
      share phrasing and final_answer). sampled_params is the actual
      varying content for an image-driven template.
    """
    seen: dict[tuple, list[str]] = {}
    for instance in instances:
        if template_file.has_image:
            content_key = _hashable_key(instance["sampled_params"])
        else:
            content_key = instance["problem_text"]
        key = (content_key, _hashable_key(instance["final_answer"]))
        seen.setdefault(key, []).append(instance["id"])

    duplicate_ids = [ids for ids in seen.values() if len(ids) > 1]
    duplicate_count = sum(len(ids) - 1 for ids in duplicate_ids)

    return {
        "passed": duplicate_count <= DUPLICATE_THRESHOLD,
        "duplicate_count": duplicate_count,
        "duplicate_groups": duplicate_ids,
    }


def check_answer_diversity(instances: list[dict], answer_type: str) -> dict:
    """
    Unique final_answer values as a fraction of N. Threshold: >= 30% of N.
    Skipped (auto-pass) for boolean answer_type, which structurally caps
    at 2 unique values (spec.md Section 5 note).
    """
    if answer_type == "boolean":
        return {
            "passed": True,
            "skipped": True,
            "reason": "boolean answer_type structurally caps unique values at 2",
        }

    n = len(instances)
    unique_count = len({_hashable_key(inst["final_answer"]) for inst in instances})
    unique_fraction = unique_count / n if n else 0.0

    return {
        "passed": unique_fraction >= DIVERSITY_MIN_FRACTION,
        "unique_count": unique_count,
        "unique_fraction": unique_fraction,
    }


def check_parameter_range_coverage(instances: list[dict], template_file: TemplateFile) -> dict:
    """
    Per parameter: (max_sampled - min_sampled) / (declared_max - declared_min)
    >= 0.7. Overall passed = every parameter individually clears the
    threshold (spec.md states the per-parameter rule; "all must pass" is
    this module's choice for how per-parameter results combine).
    """
    per_parameter = {}
    for name, param in template_file.parameters.items():
        sampled_values = [inst["sampled_params"][name] for inst in instances]
        min_sampled = min(sampled_values)
        max_sampled = max(sampled_values)

        declared_span = param.max - param.min
        sampled_span = max_sampled - min_sampled
        coverage = sampled_span / declared_span if declared_span else 1.0

        per_parameter[name] = {
            "passed": coverage >= RANGE_COVERAGE_MIN_FRACTION,
            "coverage": coverage,
            "min_sampled": min_sampled,
            "max_sampled": max_sampled,
            "declared_min": param.min,
            "declared_max": param.max,
        }

    return {
        "passed": all(p["passed"] for p in per_parameter.values()),
        "per_parameter": per_parameter,
    }


def check_template_distribution(instances: list[dict], template_file: TemplateFile) -> dict:
    """
    No single problem_text_templates entry used for > 80% of instances.

    Matches each instance's rendered problem_text back to a declared
    template string by exact equality. This works for templates with no
    placeholders (e.g. the triangle-area reference template, where the
    rendered text IS the template string) but is a real limitation for
    templates with placeholders, where rendered text won't exactly match
    the raw template string — matching against the placeholder-stripped
    pattern would be needed there. Revisit when a placeholder-bearing
    template (e.g. ratios/vectors) is built.
    """
    counts = Counter(instance["problem_text"] for instance in instances)
    n = len(instances)
    max_share = max(counts.values()) / n if n else 0.0

    return {
        "passed": max_share <= TEMPLATE_MAX_SHARE,
        "max_share": max_share,
        "counts": dict(counts),
    }