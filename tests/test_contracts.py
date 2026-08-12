import unittest

from pydantic import ValidationError

from contracts.instance import Instance
from contracts.template_spec import TemplateSpec, TemplateFile
from contracts.validate import (
    validate_instance,
    validate_template_spec,
    validate_template_file,
    check_placeholders_match_parameters,
)


def minimal_instance(**overrides) -> dict:
    data = {
        "id": "inst-1",
        "domain": "geometry",
        "problem_text": "A triangle has base 4 and height 5. What is its area?",
        "image_path": None,
        "final_answer": 10.0,
        "answer_type": "numeric",
        "solution_steps": {"area": 10.0},
        "sampled_params": {"base": 4, "height": 5},
    }
    data.update(overrides)
    return data


def minimal_template_spec(**overrides) -> dict:
    data = {
        "template_id": "geometry-triangle-area-v1",
        "domain": "geometry",
        "name": "triangle-area-given-base-height",
        "description": "Find the area of a triangle given base and height.",
        "has_image": True,
        "answer_type": "numeric",
        "problem_text_templates": [
            "A triangle has a base of {base} and height of {height}. What is its area?",
        ],
    }
    data.update(overrides)
    return data


def minimal_template_file(**overrides) -> dict:
    data = minimal_template_spec()
    data["parameters"] = {
        "base": {"type": "int", "min": 1, "max": 50, "step": 1},
        "height": {"type": "int", "min": 1, "max": 50, "step": 1},
    }
    data.update(overrides)
    return data


class TestInstanceContract(unittest.TestCase):

    def test_minimal_valid_instance(self):
        instance = Instance.model_validate(minimal_instance())
        self.assertEqual(instance.final_answer, 10.0)
        self.assertEqual(instance.sampled_params, {"base": 4, "height": 5})

    def test_wrapper_delegates_to_model(self):
        instance = validate_instance(minimal_instance())
        self.assertIsInstance(instance, Instance)

    def test_missing_required_field_raises(self):
        data = minimal_instance()
        del data["final_answer"]
        with self.assertRaises(ValidationError):
            Instance.model_validate(data)

    def test_invalid_answer_type_raises(self):
        data = minimal_instance(answer_type="not-a-real-type")
        with self.assertRaises(ValidationError):
            Instance.model_validate(data)

    def test_extra_field_raises(self):
        # status was removed from the contract; a stray status key must
        # be rejected, confirming extra="forbid" is actually enforced.
        data = minimal_instance(status="qc_passed")
        with self.assertRaises(ValidationError):
            Instance.model_validate(data)

    def test_answer_type_numeric(self):
        data = minimal_instance(answer_type="numeric", final_answer=42)
        Instance.model_validate(data)

    def test_answer_type_expression(self):
        data = minimal_instance(answer_type="expression", final_answer="3x + 2")
        Instance.model_validate(data)

    def test_answer_type_vector(self):
        data = minimal_instance(answer_type="vector", final_answer=[1.0, 2.0, 3.0])
        Instance.model_validate(data)

    def test_answer_type_matrix(self):
        data = minimal_instance(
            answer_type="matrix", final_answer=[[1.0, 0.0], [0.0, 1.0]]
        )
        Instance.model_validate(data)

    def test_answer_type_boolean(self):
        data = minimal_instance(answer_type="boolean", final_answer=True)
        instance = Instance.model_validate(data)
        self.assertIs(instance.final_answer, True)


class TestTemplateSpecContract(unittest.TestCase):

    def test_minimal_valid_template_spec(self):
        spec = TemplateSpec.model_validate(minimal_template_spec())
        self.assertTrue(spec.has_image)

    def test_wrapper_delegates_to_model(self):
        spec = validate_template_spec(minimal_template_spec())
        self.assertIsInstance(spec, TemplateSpec)

    def test_missing_required_field_raises(self):
        data = minimal_template_spec()
        del data["description"]
        with self.assertRaises(ValidationError):
            TemplateSpec.model_validate(data)

    def test_invalid_answer_type_raises(self):
        data = minimal_template_spec(answer_type="not-a-real-type")
        with self.assertRaises(ValidationError):
            TemplateSpec.model_validate(data)


class TestTemplateFileContract(unittest.TestCase):

    def test_valid_template_file_passes(self):
        template_file = validate_template_file(minimal_template_file())
        self.assertIsInstance(template_file, TemplateFile)
        self.assertEqual(set(template_file.parameters.keys()), {"base", "height"})

    def test_placeholder_not_declared_as_parameter_raises(self):
        data = minimal_template_file(
            problem_text_templates=[
                "A triangle has a base of {base}, height of {height}, "
                "and color {color}. What is its area?",
            ]
        )
        with self.assertRaises(ValueError):
            validate_template_file(data)

    def test_parameter_never_referenced_raises(self):
        data = minimal_template_file()
        data["parameters"]["unused_param"] = {"type": "int", "min": 1, "max": 10}
        with self.assertRaises(ValueError):
            validate_template_file(data)

    def test_check_placeholders_match_parameters_directly_ok(self):
        template_file = TemplateFile.model_validate(minimal_template_file())
        mismatches = check_placeholders_match_parameters(template_file)
        self.assertEqual(mismatches, [])

    def test_check_placeholders_match_parameters_directly_mismatch(self):
        data = minimal_template_file()
        data["problem_text_templates"] = ["Base {base} only, no height used."]
        template_file = TemplateFile.model_validate(data)
        mismatches = check_placeholders_match_parameters(template_file)

        # both directions of mismatch should be represented:
        # 'height' declared but unused, and nothing missing from parameters
        # in this direction (base is fine), so just check height is flagged.
        self.assertTrue(any("height" in m for m in mismatches))


if __name__ == "__main__":
    unittest.main()