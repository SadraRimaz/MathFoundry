---
name: plan-problem
description: Proposes three distinct problem ideas for a given MathFoundry area/domain/subdomain, gets human approval, then scaffolds the template directory. Use when the user asks to plan, propose, scope, or design problem(s)/template(s) for a subdomain in taxonomy.md, or asks "what problems should we build for X", before any generator.py or spec.yaml is written.
---

# Plan Problem

Plans new MathFoundry problem templates within a single subdomain, acting as
the human-facing half of the macro agent's role described in `project.md`:
propose non-technical problem specs, get them approved, then hand off a
scaffolded directory for implementation. This skill never writes
`generator.py` or a final `spec.yaml` — those belong to a later
implementation step (the micro agent). This skill's output is a proposal
and, once approved, an empty structural shell for that step to fill in.

Read `docs/project.md` and `docs/taxonomy.md` (or their equivalents at the
repo root) before using this skill if they haven't been read yet this
session — they define the domain names, the execution scope, and what
"template" and "instance" mean in this project. Do not invent domain or
subdomain names; they must come from `taxonomy.md`.

This skill runs in two separate invocations, split by a human approval gate.
Never skip from step 1 to step 4 in one turn — the human must respond in
chat between them.

## Step 1 — Resolve the target subdomain

The user names an area/domain/subdomain (e.g. "Algebra → Ratios &
Proportions", or just "ratios and proportions"). Match it against
`taxonomy.md`. If the match is ambiguous or not found, ask the user to
clarify rather than guessing — do not proceed on a guess.

Derive the two path segments used everywhere below:
- `{domain}`: the existing top-level folder name under `templates/`, e.g.
  `geometry_measurement`, `algebra`, `linear_algebra`. This matches the
  `domain` field used in `contracts/instance.py` and `template_spec.py`,
  not the taxonomy heading text directly — check `templates/` for the
  actual folder name already in use for that area.
- `{subdomain}`: the existing (or to-be-created) folder name under
  `templates/{domain}/`, e.g. `plane_shapes`, `ratios_proportions`,
  `vectors` — snake_case of the taxonomy subdomain name.

If `templates/{domain}/{subdomain}/` doesn't exist yet, that's fine —
step 4 creates it. If it exists and already contains real template
subfolders (i.e. more than a placeholder `README.md`/`.gitkeep`), tell the
user what's already there before proposing more, since the goal is
distinct, non-redundant problems.

## Step 2 — Draft three distinct problem proposals

Write exactly three problem ideas for that subdomain. Each must be prose
only — no `spec.yaml`, no parameter lists, no `problem_text_templates`.
Those are technical decisions for the implementation step, not this one.
Keep each proposal to:

- **Name**: short, matches the style of existing template names (e.g.
  `triangle-area-given-base-height`).
- **One-paragraph description**: what the learner is given and what they
  must find — enough for a human to picture the problem, not enough to
  constrain the implementation.
- **Scope — included**: what variation is intentionally covered (e.g.
  "any triangle orientation", "both radius and diameter given as inputs").
- **Scope — excluded**: what's deliberately left out and why (e.g. "no
  negative coordinates", "no obtuse-only cases", "not a system of
  equations — that's Linear Equations, not this subdomain").
- **`has_image`** and **`answer_type`** only, as a one-line note each (the
  only two contract fields worth flagging this early, since they affect
  whether the idea even fits the subdomain — e.g. don't propose an image
  for a subdomain scoped `has_image: false` in `taxonomy.md`).

The three proposals must be genuinely distinct from each other and from
anything already implemented in that subdomain's folder (per Step 1) — not
three phrasings of the same underlying problem. Prefer proposals that
between them explore different sub-topics already listed under that
subdomain heading in `taxonomy.md`, rather than three variations on the
first bullet point.

## Step 3 — Write the proposal file and stop for approval

Write the three proposals to:

```
templates/{domain}/{subdomain}/_proposal.md
```

The leading underscore is intentional and load-bearing: it marks this as a
planning artifact, not a template, so it's visually distinct from real
template subfolders (which are plain snake_case, no underscore prefix) and
so nothing downstream mistakes it for one. If `templates/{domain}/{subdomain}/`
doesn't exist yet, create it and put only `_proposal.md` in it for now.

Structure the file as three `##`-level sections (`## Option 1: <name>`, etc.)
each containing the fields from Step 2, plus a one-line header stating the
area/domain/subdomain this is for.

After writing the file, **stop and end your turn.** Tell the user the
proposal is ready at that path and ask them to review it and reply with
which option to approve (they may also ask for edits or a fresh round of
three — if so, revise and rewrite `_proposal.md` in place and stop again).
Do not create any template subfolder, `spec.yaml`, or `generator.py` in
this step. Do not guess at approval — wait for an explicit reply.

## Step 4 — On approval, scaffold the structure

Only after the user's next message clearly approves one option (e.g.
"approved", "go with #2", "use the ratio scaling one") continue to
scaffolding. If their reply is ambiguous about which option, ask before
proceeding.

Derive `{template_name}` from the approved option's name (snake_case,
matching the pattern of existing template folder names — e.g.
`triangle-area-given-base-height` as a name maps to a directory segment
consistent with how `templates/geometry_measurement/plane_shapes/triangle/area_given_base_height/`
is nested: check the existing reference template's directory nesting
before deciding how many levels deep the new one goes, since some
subdomains nest one level further by shape/topic and some don't).

Create:

```
templates/{domain}/{subdomain}/{template_name}/
```

with these files as placeholders only (no implementation logic — that is
explicitly out of scope for this skill, per `project.md`'s division between
macro-agent spec authoring and micro-agent implementation):

- `spec.yaml` — populate only the fields this skill has real information
  for: `template_id`, `domain`, `name`, `description`, `has_image`,
  `answer_type`, and `problem_text_templates` as a one-item placeholder
  list (e.g. `["TODO: problem text"]`). Leave `parameters` as an empty
  mapping (`parameters: {}`) with a `# TODO(micro agent): define
  parameters` comment — do not invent parameter ranges, since those are an
  implementation decision this skill has no basis for. Match the exact
  key order and style of the existing reference `spec.yaml` at
  `templates/geometry_measurement/plane_shapes/triangle/area_given_base_height/spec.yaml`
  (also bundled at `examples/reference_spec.yaml` in this skill folder, for
  workspaces where that reference template isn't present yet).
- `generator.py` — do not write one. Its absence is expected; a comment-only
  file is not needed either. Leave it for the implementation step.

Then delete `_proposal.md` from that directory (its content is now
superseded by `spec.yaml`, and its job — getting to an approved decision —
is done) and confirm to the user what was created, listing the exact paths.

If the user asks this skill to also implement the generator, decline within
this skill's scope and say that's a separate implementation step, distinct
from planning — do not write generator logic here even if asked directly,
since this skill's whole value is keeping planning and implementation as
separate, reviewable stages per `project.md`'s macro/micro split.
