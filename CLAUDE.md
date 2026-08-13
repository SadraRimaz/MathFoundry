# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A proof-of-concept data pipeline that generates math word problem samples
(text + optional figure + structured solution trace + final answer) for
LLM/VLM training data. It's one concrete instantiation of a general
"manufacturing" architecture for agentic content generation: a static,
contract-bound core; deterministic per-template generators (the "products");
and a blind, batch-level QC gate — designed so new problem types can be
added without ever touching the core.

Design docs (read before making architectural changes):
- `docs/project.md` — why the project exists, the manufacturing metaphor, scope/out-of-scope decisions
- `docs/initial/spec.md` — exact contracts, file formats, module boundaries (source of truth for "what to build")
- `docs/taxonomy.md` — the full problem taxonomy and which subdomains are actually in execution scope
- `docs/initial/claude.md` — original build-process instructions (superseded by this file for day-to-day work, but useful history)

## Commands

```
pip install -r requirements.txt      # pydantic, pyyaml, matplotlib
python tests/run_all.py              # run the full unittest suite
python -m unittest tests.test_orchestrator          # run one test module
python -m unittest tests.test_orchestrator.TestOrchestratorTriangleArea.test_generate_n_instances  # run one test
python scripts/run_generate.py <template_path> [n] [seed]   # generate a production batch to output/<template_id>/
```

There is no build step, linter, or package install target — this is a flat,
uninstalled Python package run from the repo root (scripts add the repo root
to `sys.path` manually rather than relying on an installed package).

## Architecture

Three independently-testable layers, in dependency order:

1. **`contracts/`** — Pydantic models and validators. `instance.py` defines
   the `Instance` shape every generated problem must satisfy (id, domain,
   problem_text, image_path, final_answer, answer_type, solution_steps,
   sampled_params). `template_spec.py` defines `TemplateSpec` (the
   non-technical "macro agent" spec: description, has_image, answer_type,
   phrasings) and `TemplateFile` (the on-disk `spec.yaml` shape, which adds a
   `parameters` block with type/min/max/step per parameter). `validate.py`
   also enforces that `{placeholder}` names in `problem_text_templates`
   exactly match declared `parameters` keys (parameters may exist without a
   placeholder only when `has_image: true`, since the image can carry that
   value instead).

2. **`core/`** — `problem_generator.py` defines the `ProblemGenerator` ABC
   every template implements: `sample_parameters(rng)`,
   `compute_solution(params)`, `render_problem_text(params, template)`, and
   optional `render_image(params)`. `loader.py` reads a template's
   `spec.yaml`, validates it, dynamically imports its `generator.py`, and
   instantiates its single `ProblemGenerator` subclass (zero or more than
   one such class is a hard error). `orchestrator.py`'s `generate(template_path,
   seed, n)` is the core entry point: produces `n` contract-valid instances,
   fully reproducible from `(template_id, seed, n)` — instance `i` always
   uses `Random(seed + i)`. This is the one shared dependency between
   generator testing and QC; it has zero awareness of how a template was
   produced (no macro/micro/reviewer-agent knowledge).

3. **`qc/`** — Blind, batch-level quality gate. `run_qc(template_path, n=100,
   seed=0)` calls `core.orchestrator.generate` and, if it succeeds, runs all
   checks in `checks.py`: exact duplicates (0 tolerated), answer diversity
   (≥30% unique `final_answer`, skipped for `boolean`), per-parameter sampled
   range coverage (≥70% of declared span), and template-phrasing
   distribution (no single phrasing >80% of a batch). QC never reads
   `generator.py` source — it only ever looks at the instances `generate()`
   produced. It validates generator *behavior* over a batch, not any single
   instance's correctness — deliberately not a per-instance judge (see
   "Out of scope" in `docs/project.md`).

**The decoupling rule that must not be violated**: the orchestrator only
depends on `spec.yaml` + `generator.py` on disk; QC only depends on the
orchestrator and a template path, never on generator source. If a change
would make QC read `generator.py` "to make a check easier," that breaks the
architecture's central claim (scale by constraining what each stage can see,
not by expanding it).

### Template layout

Each template is a self-contained directory with exactly two authored files:

```
templates/<domain>/<subdomain>/[<nested.../]<template_name>/
  spec.yaml       # TemplateFile: template_id, domain, name, description,
                  # has_image, answer_type, problem_text_templates, parameters
  generator.py    # exactly one ProblemGenerator subclass
```

The reference, fully-working template — used as the integration test for
core + QC — is
`templates/geometry_measurement/plane_shapes/triangle/area_given_base_height/`:
an image-driven triangle-area problem (problem text carries no numeric
placeholders; all values live in the rendered figure), including a
shape-only parameter so otherwise-identical base/height pairs still render
visually distinct figures.

Execution scope is intentionally limited to three subdomains, chosen to each
stress a different contract configuration (see `docs/taxonomy.md`):
Geometry → Plane Shapes (`has_image: true`), Algebra → Ratios & Proportions
(`has_image: false`), Linear Algebra → Vectors (`answer_type: vector`). The
other 24 taxonomy subdomains are designed on paper only — do not implement
them without being asked.

### Not yet implemented

`pipeline/` (global orchestrator fanning out to multiple templates) and
`agents_stub/` (macro/micro/reviewer agent call shapes) are described in the
spec but do not exist in this build. Do not build the macro agent, micro
agent, reviewer/checkpoint loop, or human approval gate unless explicitly
asked — they're deferred by design, not forgotten.

## Working on templates: use the skills

Two skills under `.agents/skills/` implement the macro/micro split from
`docs/project.md` and are the expected way to add a new template — prefer
invoking them over hand-rolling the equivalent steps:

- **`plan-problem`** — proposes three distinct non-technical problem ideas
  for a taxonomy subdomain, gets human approval, then scaffolds
  `templates/{domain}/{subdomain}/{template_name}/spec.yaml` with
  `parameters: {}` left as a TODO. Never writes `generator.py`.
- **`problem-implementation`** — takes that scaffolded (partial) `spec.yaml`,
  drafts an implementation plan for human approval, then finalizes
  `spec.yaml`'s `parameters` + `problem_text_templates` and writes
  `generator.py`, and loops running `qc.run_qc.run_qc(...)` (capped at 5
  retries) until it passes.

Both skills pause for explicit human approval between their planning phase
and their write phase — never collapse the two phases into one turn even if
asked to move fast.

## Conventions worth knowing before editing

- Per-instance seeding is `master_seed + i` — simple and known-limited
  (reordering/inserting instances shifts all downstream seeds). This is an
  accepted POC tradeoff, not a bug to fix opportunistically.
- `solution_steps` is a structured `dict[str, Any]` of named intermediate
  values, not free-text chain-of-thought reasoning — it's meant to scaffold
  SFT/RL training data, not narrate.
- Images are always drawn programmatically (matplotlib), never via a
  generative image model.
- `Parameter.step` makes the sampling space discrete (`min, min+step,
  min+2*step, ..., max`), not a continuous range — `ProblemGenerator._sample_discrete`
  is the shared helper for this.
- When a design question isn't answered by `docs/project.md` or
  `docs/initial/spec.md`, don't silently expand scope (e.g. adding
  difficulty tags, per-instance correctness QC, or generative image
  rendering — all explicitly cut) — flag it instead.
