from random import Random

from contracts.validate import validate_instance
from core.loader import load_template


def choose_template(templates: list[str], rng: Random) -> str:
    """Pick one problem_text_templates entry using the seeded rng, so
    template-choice randomness is part of the same controlled stream."""
    return rng.choice(templates)


def generate(template_path: str, seed: int, n: int) -> list[dict]:
    """
    Generate n contract-shaped instances from a template on disk.
    Reproducible from (template_id, seed, n): instance i always uses
    seed + i (spec.md Section 4).

    Only depends on load_template (spec.yaml + generator.py on disk) —
    no awareness of macro/micro/reviewer agents.

    Fails loudly: any schema-invalid instance or generator exception
    propagates immediately, rather than being skipped.
    """
    generator = load_template(template_path)
    template_file = generator.template_file

    instances = []
    for i in range(n):
        instance_seed = seed + i
        rng = Random(instance_seed)

        params = generator.sample_parameters(rng)
        final_answer, solution_steps = generator.compute_solution(params)
        template_str = choose_template(template_file.problem_text_templates, rng)
        problem_text = generator.render_problem_text(params, template_str)
        image_path = generator.render_image(params)

        instance = validate_instance({
            "id": f"{template_file.template_id}-{instance_seed}",
            "domain": template_file.domain,
            "problem_text": problem_text,
            "image_path": image_path,
            "final_answer": final_answer,
            "answer_type": template_file.answer_type,
            "solution_steps": solution_steps,
            "sampled_params": params,
        })

        instances.append(instance.model_dump())

    return instances