# Taxonomy

Full 3 areas × 3 domains × 3 subdomains taxonomy for macro-agent scoping.
Designing the full taxonomy is cheap (naming/organizing); **running the
pipeline end-to-end is not** — only the three subdomains marked
`[EXECUTION SCOPE]` below are actually implemented for this POC. The rest
exist so future work has a ready-made scope to expand into without
redesigning the taxonomy.

Diversity properties this taxonomy is designed to guarantee across the
execution scope: at least one subdomain with `has_image: true` (Geometry),
at least one with a non-`numeric` `answer_type` (Vectors), and a spread of
problem structures generally, so QC's diversity checks are exercised
meaningfully rather than trivially.

---

## Area 1: Geometry & Measurement

Naturally provides `has_image: true` coverage.

### Domain 1.1 — Plane Shapes `[EXECUTION SCOPE]`
- Triangle area/perimeter (given base+height, or given sides)
- Circle area/circumference (given radius or diameter)
- Rectangle/square area & perimeter

### Domain 1.2 — Solid Shapes
- Cube/rectangular prism volume & surface area
- Cylinder volume & surface area
- Sphere volume & surface area

### Domain 1.3 — Coordinate Geometry
- Distance between two points
- Midpoint of a segment
- Slope of a line through two points

---

## Area 2: Algebra

Core numeric coverage, with a natural `boolean` answer_type option.

### Domain 2.1 — Linear Equations
- Solve for x in a one-variable linear equation (word-framed, e.g. age/rate problems)
- Two-variable system of linear equations (e.g. mixture/cost problems)
- Linear rate problems (distance = rate × time)

### Domain 2.2 — Ratios & Proportions `[EXECUTION SCOPE]`
- Simple ratio word problems (e.g. recipe scaling)
- Percentage change (discount, tax, growth)
- Unit rate / unit conversion

### Domain 2.3 — Quadratics
- Solve a quadratic via factoring (projectile motion framing)
- Vertex/max-min word problem (e.g. optimization of area given perimeter)
- Roots via quadratic formula, discriminant-based (real vs. no real solution — natural `boolean` answer_type)

---

## Area 3: Linear Algebra & Discrete Math

Provides `vector`/`matrix` answer_type coverage, plus a lighter discrete-math
angle for structural variety.

### Domain 3.1 — Vectors `[EXECUTION SCOPE]`
- Vector addition/subtraction (e.g. combined displacement/force)
- Dot product (e.g. work done, projection framing)
- Vector magnitude (e.g. resultant speed/distance)

### Domain 3.2 — Matrices
- Matrix addition/scalar multiplication (e.g. combining data tables)
- 2×2 matrix multiplication (e.g. transformation word problem)
- 2×2 determinant (e.g. area scaling factor)

### Domain 3.3 — Counting & Probability
- Basic permutations (arrangements word problem)
- Basic combinations (selection word problem)
- Simple probability (single event; natural `numeric` or `boolean` — e.g. "is it more likely than not")

---

## Execution scope summary

| Subdomain | Contract configuration exercised |
|---|---|
| Geometry → Plane Shapes | `has_image: true`, `answer_type: numeric` |
| Algebra → Ratios & Proportions | `has_image: false`, `answer_type: numeric` |
| Linear Algebra → Vectors | `has_image: false`, `answer_type: vector` |

These three were chosen specifically to each stress a different contract
configuration with minimal redundant engineering, rather than for curriculum
completeness.
