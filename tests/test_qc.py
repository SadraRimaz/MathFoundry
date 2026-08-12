import shutil
import tempfile
import unittest
from pathlib import Path

from qc.run_qc import run_qc

TRIANGLE_AREA_PATH = "templates/geometry_measurement/plane_shapes/triangle/area_given_base_height"
TRIANGLE_GENERATED_IMAGES_DIR = Path(TRIANGLE_AREA_PATH) / "_generated_images"

BASE_SPEC_YAML = """
template_id: broken-test-template-v1
domain: test
name: broken-test-template
description: test fixture, not a real template
has_image: false
answer_type: numeric
problem_text_templates:
  - "Variant {x}: what is the value?"
  - "Alt phrasing, variant {x}: find the value."
parameters:
  x:
    type: int
    min: 0
    max: 100
    step: 1
"""


def write_broken_template(tmp_dir: str, generator_source: str, spec_yaml: str = BASE_SPEC_YAML) -> str:
    """Write a minimal spec.yaml + generator.py fixture to a temp dir and
    return the template path. These are throwaway QC test fixtures, not
    real templates — kept out of templates/ entirely."""
    template_dir = Path(tmp_dir) / "broken_template"
    template_dir.mkdir()
    (template_dir / "spec.yaml").write_text(spec_yaml)
    (template_dir / "generator.py").write_text(generator_source)
    return str(template_dir)


class TestRunQcHealthyReferenceTemplate(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        if TRIANGLE_GENERATED_IMAGES_DIR.exists():
            shutil.rmtree(TRIANGLE_GENERATED_IMAGES_DIR)

    def test_passes_on_real_triangle_area_template(self):
        result = run_qc(TRIANGLE_AREA_PATH, n=100, seed=0)
        self.assertEqual(result["status"], "pass")
        for check_name, check_result in result["report"].items():
            self.assertTrue(
                check_result["passed"],
                f"expected {check_name} to pass, got {check_result}",
            )


class TestRunQcExecutionFailure(unittest.TestCase):

    GENERATOR_SOURCE = """
from core.problem_generator import ProblemGenerator

class BrokenGenerator(ProblemGenerator):
    def sample_parameters(self, rng):
        return {"x": 1}

    def compute_solution(self, params):
        raise RuntimeError("deliberately broken: compute_solution always raises")

    def render_problem_text(self, params, template):
        return template.format(x=1)
"""

    def test_fails_on_execution_error_with_no_other_checks_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = write_broken_template(tmp_dir, self.GENERATOR_SOURCE)
            result = run_qc(template_path, n=20, seed=0)

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["report"]["execution"]["passed"])
        # short-circuit: no other check keys should be present at all
        self.assertEqual(set(result["report"].keys()), {"execution"})


class TestRunQcDuplicateFailure(unittest.TestCase):

    GENERATOR_SOURCE = """
from core.problem_generator import ProblemGenerator

class BrokenGenerator(ProblemGenerator):
    def sample_parameters(self, rng):
        # ignores rng entirely -> every instance identical
        return {"x": 5}

    def compute_solution(self, params):
        return params["x"], {"x": params["x"]}

    def render_problem_text(self, params, template):
        return template.format(x=params["x"])
"""

    def test_fails_on_duplicates_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = write_broken_template(tmp_dir, self.GENERATOR_SOURCE)
            result = run_qc(template_path, n=20, seed=0)

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["report"]["duplicates"]["passed"])
        # every instance samples identical params, so duplicates should be
        # heavily concentrated (n - (number of distinct template phrasings)
        # groups at most, given 2 phrasings in BASE_SPEC_YAML)
        self.assertGreaterEqual(result["report"]["duplicates"]["duplicate_count"], 15)


class TestRunQcAnswerDiversityFailure(unittest.TestCase):

    GENERATOR_SOURCE = """
from core.problem_generator import ProblemGenerator

class BrokenGenerator(ProblemGenerator):
    def sample_parameters(self, rng):
        # varies x (and therefore problem_text) so the duplicate check
        # doesn't also fire, but compute_solution ignores x entirely ->
        # final_answer never varies.
        return {"x": self._sample_discrete(rng, "x")}

    def compute_solution(self, params):
        return 42, {"answer": 42}

    def render_problem_text(self, params, template):
        return template.format(x=params["x"])
"""

    def test_fails_on_answer_diversity_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = write_broken_template(tmp_dir, self.GENERATOR_SOURCE)
            result = run_qc(template_path, n=50, seed=0)

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["report"]["answer_diversity"]["passed"])
        self.assertEqual(result["report"]["answer_diversity"]["unique_count"], 1)
        # Not asserting duplicates["passed"] here: x varies per instance,
        # but at finite n two instances can coincidentally land on the
        # same x and template phrasing, producing a genuine (unrelated)
        # duplicate. The point of this test is answer_diversity, which is
        # asserted above regardless of what duplicates reports.


class TestRunQcParameterRangeCoverageFailure(unittest.TestCase):

    GENERATOR_SOURCE = """
from random import Random
from core.problem_generator import ProblemGenerator

class BrokenGenerator(ProblemGenerator):
    def sample_parameters(self, rng):
        # ignores the declared [0, 100] range in spec.yaml, always samples
        # from a narrow sub-range -> low coverage.
        return {"x": rng.randint(0, 3)}

    def compute_solution(self, params):
        return params["x"], {"x": params["x"]}

    def render_problem_text(self, params, template):
        return template.format(x=params["x"])
"""

    def test_fails_on_parameter_range_coverage_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = write_broken_template(tmp_dir, self.GENERATOR_SOURCE)
            result = run_qc(template_path, n=20, seed=0)

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["report"]["parameter_range_coverage"]["passed"])
        self.assertFalse(
            result["report"]["parameter_range_coverage"]["per_parameter"]["x"]["passed"]
        )


class TestRunQcTemplateDistributionFailure(unittest.TestCase):

    GENERATOR_SOURCE = """
from core.problem_generator import ProblemGenerator

class BrokenGenerator(ProblemGenerator):
    def sample_parameters(self, rng):
        return {"x": self._sample_discrete(rng, "x")}

    def compute_solution(self, params):
        return params["x"], {"x": params["x"]}

    def render_problem_text(self, params, template):
        # always renders the FIRST template string with a fixed x,
        # regardless of which template orchestrator actually chose or
        # what x was really sampled -> defeats template-string variety
        return "Variant 0: what is the value?"
"""

    def test_fails_on_template_distribution_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            template_path = write_broken_template(tmp_dir, self.GENERATOR_SOURCE)
            result = run_qc(template_path, n=20, seed=0)

        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["report"]["template_distribution"]["passed"])
        self.assertEqual(result["report"]["template_distribution"]["max_share"], 1.0)


if __name__ == "__main__":
    unittest.main()