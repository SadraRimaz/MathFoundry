import hashlib
import math
from pathlib import Path
from random import Random
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.problem_generator import ProblemGenerator

IMAGES_DIR = Path(__file__).parent / "_generated_images"

MAX_SAMPLE_ATTEMPTS = 20


class TrianglePerimeterGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        side_c_param = self.template_file.parameters["side_c"]

        for _ in range(MAX_SAMPLE_ATTEMPTS):
            side_a = self._sample_discrete(rng, "side_a")
            side_b = self._sample_discrete(rng, "side_b")

            # side_c has no cross-parameter constraint field in the
            # Parameter contract, so its valid window (strict triangle
            # inequality) is computed here rather than sampled
            # independently via _sample_discrete.
            low = max(side_c_param.min, abs(side_a - side_b) + side_c_param.step)
            high = min(side_c_param.max, side_a + side_b - side_c_param.step)
            if low > high:
                continue

            side_c = rng.randrange(int(low), int(high) + 1)
            return {"side_a": side_a, "side_b": side_b, "side_c": side_c}

        raise RuntimeError(
            "Could not sample a valid (side_a, side_b, side_c) triangle "
            f"after {MAX_SAMPLE_ATTEMPTS} attempts"
        )

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        perimeter = params["side_a"] + params["side_b"] + params["side_c"]
        return perimeter, {"perimeter": perimeter}

    def render_problem_text(self, params: dict, template: str) -> str:
        # No placeholders are expected in this template's problem_text
        # (all data is conveyed by the image) — .format is still applied
        # defensively so this stays correct if a future phrasing adds one.
        return template.format(**params)

    def render_image(self, params: dict) -> str | None:
        side_a = params["side_a"]
        side_b = params["side_b"]
        side_c = params["side_c"]

        # A at origin, B along the x-axis (AB = side_a). C is placed by
        # triangulating from the other two side lengths (AC = side_b,
        # BC = side_c) via the standard two-circle-intersection formula.
        a_pt = (0.0, 0.0)
        b_pt = (float(side_a), 0.0)
        x = (side_b**2 - side_c**2 + side_a**2) / (2 * side_a)
        y = math.sqrt(side_b**2 - x**2)
        c_pt = (x, y)

        fig, ax = plt.subplots(figsize=(5, 5))

        triangle = plt.Polygon(
            [a_pt, b_pt, c_pt], closed=True,
            edgecolor="black", facecolor="none", linewidth=2,
        )
        ax.add_patch(triangle)

        centroid = (
            (a_pt[0] + b_pt[0] + c_pt[0]) / 3,
            (a_pt[1] + b_pt[1] + c_pt[1]) / 3,
        )

        def label_side(p1, p2, text):
            mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            # Offset the label outward, away from the centroid, so labels
            # don't overlap the triangle's edges.
            dx, dy = mid[0] - centroid[0], mid[1] - centroid[1]
            norm = math.hypot(dx, dy) or 1.0
            offset = 16
            ax.annotate(
                text,
                xy=mid,
                xytext=(dx / norm * offset, dy / norm * offset),
                textcoords="offset points",
                ha="center", va="center", fontsize=11,
            )

        label_side(a_pt, b_pt, f"{side_a}")
        label_side(a_pt, c_pt, f"{side_b}")
        label_side(b_pt, c_pt, f"{side_c}")

        xs = [a_pt[0], b_pt[0], c_pt[0]]
        ys = [a_pt[1], b_pt[1], c_pt[1]]
        x_span = max(xs) - min(xs) or 1.0
        y_span = max(ys) - min(ys) or 1.0
        ax.set_xlim(min(xs) - x_span * 0.15, max(xs) + x_span * 0.15)
        ax.set_ylim(min(ys) - y_span * 0.15, max(ys) + y_span * 0.15)
        ax.set_aspect("equal")
        ax.axis("off")

        # Deterministic filename from the sampled params: same params ->
        # same image file. Rendered before the instance's id is assembled
        # (orchestrator calls render_image before building the id), so a
        # param hash is used instead of the id.
        param_key = f"{side_a}-{side_b}-{side_c}"
        filename = hashlib.sha1(param_key.encode()).hexdigest()[:16] + ".png"

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        out_path = IMAGES_DIR / filename
        fig.savefig(out_path, bbox_inches="tight", dpi=100)
        plt.close(fig)

        # Relative to the template's own directory (spec.md Section 7:
        # image_path is relative to the template's output location, not
        # an absolute filesystem path).
        return str(out_path.relative_to(Path(__file__).parent))
