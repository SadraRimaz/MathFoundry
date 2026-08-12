from core.loader import load_template_file
from core.orchestrator import generate
from qc.checks import (
    check_exact_duplicates,
    check_answer_diversity,
    check_parameter_range_coverage,
    check_template_distribution,
)


def run_qc(template_path: str, n: int = 100, seed: int = 0) -> dict:
    """
    Blind, batch-level QC (spec.md Section 5). Runs generate() and, if it
    succeeds, all four checks in qc/checks.py. Any exception during
    generation fails QC outright ("0 tolerated" execution errors) with no
    further checks attempted.

    Pure function: no persistence side effects. Persisting qc_sample.json
    (spec.md Section 7) is a pipeline-level concern, not this function's.
    """
    try:
        instances = generate(template_path, seed, n)
    except Exception as e:
        return {
            "status": "fail",
            "report": {
                "execution": {"passed": False, "error": str(e)},
            },
        }

    template_file = load_template_file(template_path)

    duplicates = check_exact_duplicates(instances, template_file)
    answer_diversity = check_answer_diversity(instances, template_file.answer_type)
    parameter_range_coverage = check_parameter_range_coverage(instances, template_file)
    template_distribution = check_template_distribution(instances, template_file)

    report = {
        "execution": {"passed": True, "n": n},
        "duplicates": duplicates,
        "answer_diversity": answer_diversity,
        "parameter_range_coverage": parameter_range_coverage,
        "template_distribution": template_distribution,
    }

    overall_passed = all(
        check["passed"]
        for check in (
            duplicates,
            answer_diversity,
            parameter_range_coverage,
            template_distribution,
        )
    )

    return {
        "status": "pass" if overall_passed else "fail",
        "report": report,
    }