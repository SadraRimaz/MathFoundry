# Project Overview

## What this is

A proof-of-concept data pipeline that generates math word problem samples for
LLM/VLM training and evaluation (SFT and RL), built as an application of a
general **manufacturing metaphor for agentic AI generation**:

- A **static, contract-bound core** (fixed interfaces, payloads, deterministic
  I/O) that many structurally diverse "products" are built against.
- A **hierarchical agent pipeline** — macro (planning) agent → optional
  reviewer agent → micro (implementation) agent.
- A **blind Quality Control layer** that validates products without seeing
  their internal implementation code.
- An **optional human-in-the-loop checkpoint**, operable anywhere between full
  oversight and fully delegated (reviewer-agent-assisted) review, with
  automatic escalation to a human if agents can't converge.

The core architectural claim: infinite horizontal scalability (adding new
problem types indefinitely) requires **constraining** agent autonomy via
architectural contracts, not expanding it. This is positioned against
open-loop "vibe coding" pipelines that drift and compound errors at scale.

This project is one concrete instantiation of that architecture, not the
architecture itself. Keep the two separate in discussion: changes made here
for POC simplicity (e.g. skipping the human gate topic, deferring reviewer
convergence mechanics) are scoping decisions for this application, not
changes to the general idea.

## Product = problem template

In this application:

- A **domain** (e.g. geometry, algebra, linear algebra) is a subject area.
- A **template** is the "product" — a standalone problem type (e.g. "find the
  area of a triangle given base and height"). Produced by the macro agent as
  a non-technical spec, then implemented by the micro agent as a generator.
- An **instance** is one manufactured unit of a template — one concrete
  problem with sampled parameter values, a computed answer, and (optionally)
  a rendered image.

One template maps to exactly one generator, always. There is no ambiguity for
the micro agent to resolve independently — all high-level decisions about
what a problem type is belong to the macro agent.

## Scope for this POC

- **Taxonomy**: 3 areas × 3 domains × 3 subdomains = 27 subdomains, fully
  designed (see `taxonomy.md`), but only a small subset is actually run
  end-to-end through the pipeline.
- **Execution scope** (subdomains actually implemented and generated):
  1. Geometry → Plane Shapes (exercises `has_image: true`)
  2. Algebra → Ratios & Proportions (exercises plain numeric, no image)
  3. Linear Algebra → Vectors (exercises `answer_type: vector`)
- **Priority build order**: contracts, core (generation orchestrator +
  `ProblemGenerator` interface), and the QC module, built and testable as
  **decoupled modules** — independent of whether the macro/micro/reviewer
  agents exist yet.
- **Deferred / stubbed for now**: macro agent, micro agent, reviewer agent
  (Checkpoints A and B), and the human gate. These are represented as
  interfaces/stub functions the orchestrator calls, so they can be dropped in
  later without restructuring anything already built.

## Out of scope / explicitly cut for this POC

- Per-sample (instance-level) correctness validation by QC. QC validates a
  **batch** (does the generator run without errors, is the batch diverse) —
  it does not re-derive and check each individual answer. This is a
  deliberate departure from a stricter "blind, per-product QC" design, made
  because the manufacturing metaphor here is "many instances from one
  template," so QC's natural unit is the batch, not the instance.
- Free-text, narrated chain-of-thought. `solution_steps` is a structured list
  of named intermediate variables, not prose reasoning. This is cheaper to
  generate reliably, machine-checkable, and can be templated into prose later
  if needed.
- Difficulty tagging, unit-of-measure as a separate field, and
  structured `variables` as a QC-visible field (all cut from the contract for
  simplicity — see `spec.md`).
- Human gate design (Topic 7) — intentionally skipped in this pass. The
  reviewer loop (Topic 5) is closed only at the outline level; exact
  criteria, iteration semantics, and judge implementation are deferred to be
  handled later via agentic coding, once the core infrastructure exists.
- Generative-model image generation. Images are drawn programmatically
  (matplotlib), not produced by an image-generation model — this keeps
  figures accurate, reproducible, and cheap.

## Downstream use of generated data

Supervised fine-tuning (SFT) first, then RL training. `solution_steps` exists
specifically to support this: a structured, verifiable intermediate-state
trace usable as a CoT scaffold for SFT and as a checkable trajectory for RL,
without requiring free-text reasoning generation.
