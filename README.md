# MathFoundry

A proof-of-concept data pipeline for generating math word problem samples
(text plus optional figure, structured solution trace, final answer) for
LLM/VLM training and evaluation. Built as one concrete instantiation of a
general manufacturing-style architecture for agentic AI content generation:
a contract-bound core, deterministic per-template generators, and a blind
quality-control layer, designed so new problem types can be added without
touching the core.

Full design rationale is in `docs/project.md`, and file formats and
module contracts are defined in `docs/spec.md`.

## Current scope

This build implements and validates three layers, independently of any
agent pipeline:

- **Contracts** (`contracts/`) — Pydantic models for a generated problem
  instance and for a template's spec file, plus validation helpers,
  including a check that a template's text placeholders and declared
  parameters agree with each other.
- **Core** (`core/`) — A fixed `ProblemGenerator` interface every template
  implements, a loader that reads a template's `spec.yaml` and
  `generator.py` from disk, and a generation orchestrator that produces a
  reproducible batch of contract-valid instances from a template path, a
  seed, and a count.
- **QC** (`qc/`) — A blind, batch-level quality gate. It runs a template's
  generator and checks the resulting batch for execution errors, exact
  duplicates, answer diversity, sampled-parameter range coverage, and
  problem-phrasing distribution, without ever reading the generator's
  source code.

The macro agent (problem design), micro agent (generator implementation),
reviewer loop, and human approval gate described in the design docs are
not implemented yet. `pipeline/` and `agents_stub/` contain the intended
call shape as stub functions, so those pieces can be dropped in later
without restructuring the core.

Nine templates have been implemented against this core, covering the
three subdomains in execution scope — see [Templates](#templates) below.

## Templates

Nine hand-authored, fully working templates exist, one per problem idea
within each of the three in-scope subdomains (see `docs/taxonomy.md`).
Each has been run end to end through generation and QC.

**Geometry → Plane Shapes → Triangle** (`has_image: true`, all numeric
data conveyed by the rendered figure, not the problem text):

- `triangle/area_given_base_height/` — area of a triangle given its base
  and height. The reference template: it is the integration test for the
  core and QC modules, and includes a shape-only parameter so
  otherwise-identical base/height pairs still produce visually distinct
  figures.
- `triangle/area_given_three_sides/` — area of a triangle given its three
  side lengths, via Heron's formula.
- `triangle/perimeter_given_three_sides/` — perimeter of a triangle given
  its three side lengths.

**Algebra → Ratios & Proportions → Simple Ratio Word Problems**
(`has_image: false`, numeric answers):

- `simple_ratio_word_problems/divide_quantity_in_ratio/` — split a total
  quantity between three parties according to a stated ratio.
- `simple_ratio_word_problems/equivalent_ratio_unknown_term/` — solve
  `a:b = c:x` for `x` from a real-world equivalent-ratio scenario.
- `simple_ratio_word_problems/recipe_ratio_scaling/` — scale one
  ingredient of a fixed-ratio recipe to match a new amount of another.

**Linear Algebra → Vectors → Dot Product**:

- `dot_product/perpendicular_check/` — determine whether two 2D vectors
  are perpendicular by testing whether their dot product is zero
  (`answer_type: boolean`).
- `dot_product/projection/` — scalar projection of one 2D vector onto
  another (`answer_type: numeric`).
- `dot_product/work_done/` — work done by a constant force over a
  straight-line displacement, `W = F . d` (`answer_type: numeric`).

## Running the tests

```
pip install -r requirements.txt
python tests/run_all.py
```

Tests use Python's standard `unittest`, no external test framework. They
cover contract validation, end-to-end generation against the reference
template, each QC check in isolation, and end-to-end QC runs against both
the healthy reference template and a set of deliberately broken generator
fixtures.

## Layout

```
contracts/    instance and template-spec data models, validation
core/         ProblemGenerator interface, template loader, generation orchestrator
qc/           batch-level QC checks and the run_qc entry point
templates/    one directory per template: spec.yaml + generator.py
tests/        unittest suite for all of the above
pipeline/     pipeline orchestrator (not yet implemented)
agents_stub/  macro/micro agent stub functions (not yet implemented)
output/       destination for generated batches and QC samples at runtime
docs/         design documents and specification
```
