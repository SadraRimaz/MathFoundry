import unittest

from contracts.template_spec import TemplateFile
from qc.checks import (
    check_exact_duplicates,
    check_answer_diversity,
    check_parameter_range_coverage,
    check_template_distribution,
)


def make_template_file(**overrides) -> TemplateFile:
    data = {
        "template_id": "test-template-v1",
        "domain": "geometry_measurement",
        "name": "test-template",
        "description": "test",
        "has_image": True,
        "answer_type": "numeric",
        "problem_text_templates": ["Template A", "Template B"],
        "parameters": {
            "x": {"type": "int", "min": 0, "max": 100, "step": 1},
        },
    }
    data.update(overrides)
    return TemplateFile.model_validate(data)


class TestCheckExactDuplicates(unittest.TestCase):

    def test_no_duplicates_passes(self):
        template_file = make_template_file(has_image=False)
        instances = [
            {"id": "1", "problem_text": "A", "final_answer": 1, "sampled_params": {}},
            {"id": "2", "problem_text": "B", "final_answer": 2, "sampled_params": {}},
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertTrue(result["passed"])
        self.assertEqual(result["duplicate_count"], 0)

    def test_one_duplicate_pair_fails_no_image(self):
        template_file = make_template_file(has_image=False)
        instances = [
            {"id": "1", "problem_text": "A", "final_answer": 1, "sampled_params": {}},
            {"id": "2", "problem_text": "A", "final_answer": 1, "sampled_params": {}},
            {"id": "3", "problem_text": "B", "final_answer": 2, "sampled_params": {}},
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertFalse(result["passed"])
        self.assertEqual(result["duplicate_count"], 1)
        self.assertIn(["1", "2"], result["duplicate_groups"])

    def test_same_text_different_answer_not_duplicate_no_image(self):
        template_file = make_template_file(has_image=False)
        instances = [
            {"id": "1", "problem_text": "A", "final_answer": 1, "sampled_params": {}},
            {"id": "2", "problem_text": "A", "final_answer": 999, "sampled_params": {}},
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertTrue(result["passed"])

    def test_vector_final_answer_duplicate_detected_no_image(self):
        template_file = make_template_file(has_image=False)
        instances = [
            {"id": "1", "problem_text": "A", "final_answer": [1.0, 2.0], "sampled_params": {}},
            {"id": "2", "problem_text": "A", "final_answer": [1.0, 2.0], "sampled_params": {}},
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertFalse(result["passed"])
        self.assertEqual(result["duplicate_count"], 1)

    def test_has_image_true_keys_on_sampled_params_not_text(self):
        # Same fixed caption text and same final_answer, but genuinely
        # different sampled_params (e.g. different figures) — must NOT be
        # flagged as a duplicate when has_image=True.
        template_file = make_template_file(has_image=True)
        instances = [
            {
                "id": "1", "problem_text": "Find the area shown.",
                "final_answer": 68.0, "sampled_params": {"base": 4, "height": 34},
            },
            {
                "id": "2", "problem_text": "Find the area shown.",
                "final_answer": 68.0, "sampled_params": {"base": 8, "height": 17},
            },
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertTrue(result["passed"])
        self.assertEqual(result["duplicate_count"], 0)

    def test_has_image_true_still_flags_identical_sampled_params(self):
        template_file = make_template_file(has_image=True)
        instances = [
            {
                "id": "1", "problem_text": "Find the area shown.",
                "final_answer": 68.0, "sampled_params": {"base": 4, "height": 34},
            },
            {
                "id": "2", "problem_text": "Find the area shown.",
                "final_answer": 68.0, "sampled_params": {"base": 4, "height": 34},
            },
        ]
        result = check_exact_duplicates(instances, template_file)
        self.assertFalse(result["passed"])
        self.assertEqual(result["duplicate_count"], 1)


class TestCheckAnswerDiversity(unittest.TestCase):

    def test_high_diversity_passes(self):
        instances = [{"final_answer": i} for i in range(10)]
        result = check_answer_diversity(instances, answer_type="numeric")
        self.assertTrue(result["passed"])

    def test_low_diversity_fails(self):
        instances = [{"final_answer": 1} for _ in range(10)]
        result = check_answer_diversity(instances, answer_type="numeric")
        self.assertFalse(result["passed"])
        self.assertEqual(result["unique_count"], 1)

    def test_exactly_at_threshold_passes(self):
        # 3 unique out of 10 = 30%, boundary should pass (>=, not >).
        instances = [{"final_answer": i % 3} for i in range(10)]
        result = check_answer_diversity(instances, answer_type="numeric")
        self.assertEqual(result["unique_fraction"], 0.3)
        self.assertTrue(result["passed"])

    def test_boolean_answer_type_auto_passes(self):
        instances = [{"final_answer": True} for _ in range(10)]
        result = check_answer_diversity(instances, answer_type="boolean")
        self.assertTrue(result["passed"])
        self.assertTrue(result["skipped"])


class TestCheckParameterRangeCoverage(unittest.TestCase):

    def test_full_span_passes(self):
        template_file = make_template_file()
        instances = [
            {"sampled_params": {"x": 0}},
            {"sampled_params": {"x": 100}},
        ]
        result = check_parameter_range_coverage(instances, template_file)
        self.assertTrue(result["passed"])
        self.assertEqual(result["per_parameter"]["x"]["coverage"], 1.0)

    def test_narrow_span_fails(self):
        template_file = make_template_file()
        instances = [
            {"sampled_params": {"x": 40}},
            {"sampled_params": {"x": 50}},
        ]
        result = check_parameter_range_coverage(instances, template_file)
        self.assertFalse(result["passed"])
        self.assertFalse(result["per_parameter"]["x"]["passed"])

    def test_multi_parameter_overall_fails_if_any_parameter_fails(self):
        template_file = make_template_file(
            parameters={
                "good": {"type": "int", "min": 0, "max": 100, "step": 1},
                "bad": {"type": "int", "min": 0, "max": 100, "step": 1},
            }
        )
        instances = [
            {"sampled_params": {"good": 0, "bad": 40}},
            {"sampled_params": {"good": 100, "bad": 50}},
        ]
        result = check_parameter_range_coverage(instances, template_file)
        self.assertFalse(result["passed"])
        self.assertTrue(result["per_parameter"]["good"]["passed"])
        self.assertFalse(result["per_parameter"]["bad"]["passed"])


class TestCheckTemplateDistribution(unittest.TestCase):

    def test_even_split_passes(self):
        instances = (
            [{"problem_text": "Template A"}] * 5
            + [{"problem_text": "Template B"}] * 5
        )
        result = check_template_distribution(instances, make_template_file())
        self.assertTrue(result["passed"])

    def test_skewed_distribution_fails(self):
        instances = (
            [{"problem_text": "Template A"}] * 9
            + [{"problem_text": "Template B"}] * 1
        )
        result = check_template_distribution(instances, make_template_file())
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(result["max_share"], 0.9)

    def test_exactly_at_threshold_passes(self):
        # 80% boundary should pass (<=, not <).
        instances = (
            [{"problem_text": "Template A"}] * 8
            + [{"problem_text": "Template B"}] * 2
        )
        result = check_template_distribution(instances, make_template_file())
        self.assertEqual(result["max_share"], 0.8)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()