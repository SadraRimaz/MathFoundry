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

## Reference template

`templates/geometry_measurement/plane_shapes/triangle/area_given_base_height/`
is a hand-authored, fully working template: given a rendered figure of a
triangle with its base and height labeled, find the area. It is
image-driven — the problem text carries no numeric placeholders, all
values come from the figure — and includes a shape-only parameter so
otherwise-identical base/height pairs still produce visually distinct
figures. It has been run end to end through generation and QC and is used
as the integration test for the core and QC modules.

Two further template locations exist as placeholders, matching the
project's execution scope, and are not yet implemented:

- `templates/algebra/ratios_proportions/`
- `templates/linear_algebra/vectors/`

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