import shutil
import unittest
from pathlib import Path

from contracts.validate import validate_instance
from core.orchestrator import generate

TEMPLATE_PATH = "templates/geometry_measurement/plane_shapes/triangle/area_given_base_height"
GENERATED_IMAGES_DIR = Path(TEMPLATE_PATH) / "_generated_images"


class TestOrchestratorTriangleArea(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        # Clean up images produced by running this test class, so repeated
        # runs don't accumulate stale build artifacts in the template dir.
        if GENERATED_IMAGES_DIR.exists():
            shutil.rmtree(GENERATED_IMAGES_DIR)

    def test_returns_exact_count(self):
        instances = generate(TEMPLATE_PATH, seed=42, n=5)
        self.assertEqual(len(instances), 5)

    def test_all_instances_contract_valid(self):
        instances = generate(TEMPLATE_PATH, seed=42, n=5)
        for instance in instances:
            validate_instance(instance)  # raises on failure

    def test_reproducible_with_same_seed(self):
        instances_a = generate(TEMPLATE_PATH, seed=42, n=5)
        instances_b = generate(TEMPLATE_PATH, seed=42, n=5)
        self.assertEqual(instances_a, instances_b)

    def test_different_seed_gives_different_output(self):
        instances_a = generate(TEMPLATE_PATH, seed=42, n=5)
        instances_b = generate(TEMPLATE_PATH, seed=100, n=5)
        params_a = [inst["sampled_params"] for inst in instances_a]
        params_b = [inst["sampled_params"] for inst in instances_b]
        self.assertNotEqual(params_a, params_b)

    def test_has_image_true_is_honored(self):
        instances = generate(TEMPLATE_PATH, seed=42, n=5)
        for instance in instances:
            self.assertIsNotNone(instance["image_path"])
            resolved = Path(TEMPLATE_PATH) / instance["image_path"]
            self.assertTrue(
                resolved.exists(),
                f"image_path {instance['image_path']} does not exist on disk",
            )

    def test_domain_and_answer_type_propagate_from_spec(self):
        instances = generate(TEMPLATE_PATH, seed=42, n=5)
        for instance in instances:
            self.assertEqual(instance["domain"], "geometry_measurement")
            self.assertEqual(instance["answer_type"], "numeric")

    def test_area_matches_base_times_height_formula(self):
        # Spot-check of our one hand-written reference generator's own
        # arithmetic — ordinary unit testing of code we wrote, not
        # per-instance QC validation of production data (that's cut,
        # see project.md).
        instances = generate(TEMPLATE_PATH, seed=42, n=5)
        instance = instances[0]
        base = instance["sampled_params"]["base"]
        height = instance["sampled_params"]["height"]
        self.assertEqual(instance["final_answer"], 0.5 * base * height)


if __name__ == "__main__":
    unittest.main()