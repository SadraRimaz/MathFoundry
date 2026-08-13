---
name: problem-implementation
description: Implements a planned MathFoundry template — finalizes spec.yaml and writes generator.py for a template directory produced by the plan-problem skill — after a human-approved implementation plan, then runs QC until it passes. Use when the user asks to implement, build, or code a template/generator that already has an approved proposal or a partial spec.yaml with parameters left as TODO.
---

# Problem Implementation

Implements the single template (product) that `plan-problem` scaffolded:
turns a partial `spec.yaml` (real fields set, `parameters: {}` left as a
TODO, `problem_text_templates` a placeholder) into the two files the
contract actually requires — a finalized `spec.yaml` and a `generator.py`
implementing `ProblemGenerator` — then runs QC until it passes. This is the
micro-agent half of the macro/micro split in `project.md`; it does not
invent new problem scope, only implements the scope already approved by
`plan-problem`.

Read `docs/project.md`, `contracts/template_spec.py`,
`contracts/instance.py`, and `core/problem_generator.py` (or their repo-root
equivalents) before using this skill if they haven't been read yet this
session — they define the exact contract this skill's output must satisfy.
Do not change contract shapes to make implementation easier; if the
contract genuinely can't express the approved proposal, stop and tell the
human rather than working around it silently.

This skill runs in two phases, split by a human approval gate, followed by
an automated QC loop. Never skip from Phase 1 to Phase 2 in one turn — the
human must respond in chat between them.

## Locating the target template

The user names a template, or points at a directory. Resolve to
`templates/{domain}/{subdomain}/{template_name}/`. That directory must
already exist with a partial `spec.yaml` in it (written by `plan-problem`).
If it doesn't exist, or `spec.yaml` is missing, tell the user to run
`plan-problem` first — do not fabricate a spec from scratch here. If
`spec.yaml` looks already-complete (non-empty `parameters` and a non-TODO
`problem_text_templates`) and `generator.py` already exists, tell the user
this template appears already implemented and confirm before overwriting
anything.

## Phase 1 — Draft an implementation plan (no code)

Write a prose/pseudocode plan — not real Python, not final YAML — covering:

- **Parameters**: for each value the generator needs to sample, name it and
  give its type/rough range in prose (e.g. "`base`: int, 1–50" or, for
  non-scalar answer types like `vector`/`matrix` where `contracts/template_spec.py`'s
  `Parameter` model only supports flat numeric ranges, decompose into
  separate scalar components, e.g. `v1_x`, `v1_y`, `v2_x`, `v2_y` rather
  than a single "vector" parameter). Note any parameter relationships or
  constraints that plain min/max/step can't express (e.g. "the triangle
  must be non-degenerate", "second value must differ from the first") and
  how the generator will enforce them — the `Parameter` contract has no
  field for cross-parameter constraints, so this logic lives in
  `sample_parameters`, and the plan should say so explicitly.
- **Solution computation**: the formula/algorithm in prose, and the named
  keys `compute_solution` will put in `solution_steps` (structured
  intermediate values per `project.md`, not prose reasoning).
- **Problem text templates**: at least two distinct phrasings/framings for
  `problem_text_templates`, as they'll actually read (placeholders like
  `{base}` marked), not just "a sentence with the params in it."
- **Image rendering** (only if `has_image: true` in `spec.yaml`): what
  `render_image` draws and with what, in prose (e.g. "matplotlib, draw the
  triangle with base/height labeled, save to `images/{id}.png`"). Per
  `project.md`, images are always programmatic (matplotlib or similar),
  never a generative image model — the plan must not propose one.
- **Edge cases / QC risk**: call out anything likely to trip the four QC
  checks in `qc/checks.py` (duplicates, answer diversity, parameter range
  coverage, template distribution) — e.g. a parameter range too narrow to
  produce enough distinct answers over a batch, or only one
  `problem_text_templates` entry (which alone would suppress template
  distribution variety).

Write this to `templates/{domain}/{subdomain}/{template_name}/_plan.md`.
After writing it, **stop and end your turn.** Tell the user the plan is
ready at that path and ask them to review and approve it, or request
changes. Do not write `generator.py` or finalize `spec.yaml` in this phase.
Do not guess at approval — wait for an explicit reply.

## Phase 2 — On approval, implement and run QC

Only after the user's next message clearly approves the plan (or approves
with named edits — apply those edits to the plan's logic before coding)
continue. If the reply requests substantial changes, revise `_plan.md`,
rewrite it, and stop again for a fresh approval rather than coding against
an unapproved revision.

Once approved:

1. **Finalize `spec.yaml`**: fill in `parameters` (one entry per Phase 1
   parameter, using the `Parameter` shape — `type`/`min`/`max`/`step`; see
   `contracts/template_spec.py`) and replace the placeholder
   `problem_text_templates` with the real phrasings from the plan. Leave
   every other field (`template_id`, `domain`, `name`, `description`,
   `has_image`, `answer_type`) as `plan-problem` set them — this phase
   fills gaps, it doesn't revisit prior decisions. The bundled
   `examples/reference_spec.yaml` in this skill folder shows a complete,
   valid example if the repo's own reference template isn't present.
2. **Write `generator.py`**: implement exactly one `ProblemGenerator`
   subclass (per `core/loader.py`, more or fewer than one class is a hard
   error) with `sample_parameters`, `compute_solution`,
   `render_problem_text`, and — only if `has_image: true` — `render_image`.
   Follow the plan's logic; don't introduce parameters, formulas, or text
   templates the plan didn't cover. The bundled
   `examples/reference_generator.py` shows the interface in use.
3. **Run QC**: call `qc.run_qc.run_qc(template_path)` (or the equivalent
   test/CLI entry point already in this repo, if `run_qc` isn't directly
   invokable in this environment) against the template directory.
   - If `status == "pass"`, report success to the user with the QC summary
     and stop. Implementation is complete.
   - If `status == "fail"`, read `report` to see which check(s) failed and
     why, fix `generator.py` and/or `spec.yaml` accordingly (e.g. widen a
     parameter range for range-coverage failures, add a
     `problem_text_templates` entry for distribution failures, fix a
     sampling bug for a duplicates or execution failure), and re-run QC.
   - **Cap retries at 5 attempts.** If still failing after 5, stop, report
     the final QC report and a summary of what was tried across attempts,
     and hand back to the human rather than continuing to retry
     autonomously.

Then delete `_plan.md` from the template directory (superseded by the
finalized `spec.yaml` + `generator.py`, mirroring `plan-problem`'s deletion
of `_proposal.md`) and confirm to the user what was created/changed, the
final QC status, and the exact paths.

If QC fails in a way that suggests the *approved plan* itself was wrong
(not just the code) — e.g. the parameter ranges as specified genuinely
can't produce a diverse batch no matter how `generator.py` is written —
say so explicitly rather than burning retries on code changes that can't
fix a planning problem, and ask the human whether to revise the plan
(reopening Phase 1) or adjust scope.
