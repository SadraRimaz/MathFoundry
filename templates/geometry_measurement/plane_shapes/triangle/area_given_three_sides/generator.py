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

MAX_SAMPLE_ATTEMPTS = 200


class TriangleAreaGivenThreeSidesGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        for _ in range(MAX_SAMPLE_ATTEMPTS):
            side_a = self._sample_discrete(rng, "side_a")
            side_b = self._sample_discrete(rng, "side_b")
            side_c = self._sample_discrete(rng, "side_c")
            if (
                side_a + side_b > side_c
                and side_b + side_c > side_a
                and side_a + side_c > side_b
            ):
                return {"side_a": side_a, "side_b": side_b, "side_c": side_c}

        raise RuntimeError(
            f"Could not sample a valid triangle after {MAX_SAMPLE_ATTEMPTS} attempts"
        )

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        side_a = params["side_a"]
        side_b = params["side_b"]
        side_c = params["side_c"]

        semi_perimeter = (side_a + side_b + side_c) / 2
        area = math.sqrt(
            semi_perimeter
            * (semi_perimeter - side_a)
            * (semi_perimeter - side_b)
            * (semi_perimeter - side_c)
        )
        area = round(area, 2)

        return area, {
            "side_a": side_a,
            "side_b": side_b,
            "side_c": side_c,
            "semi_perimeter": semi_perimeter,
            "area": area,
        }

    def render_problem_text(self, params: dict, template: str) -> str:
        # No placeholders are expected in this template's problem_text
        # (all data is conveyed by the image) — .format is still applied
        # defensively so this stays correct if a future phrasing adds one.
        return template.format(**params)

    def render_image(self, params: dict) -> str | None:
        side_a = params["side_a"]
        side_b = params["side_b"]
        side_c = params["side_c"]

        # A at origin, B along the x-axis (edge A-B has length side_a).
        # C found via the law of cosines using the angle at A, so edge
        # C-A has length side_c and edge B-C has length side_b.
        a_vertex = (0.0, 0.0)
        b_vertex = (float(side_a), 0.0)
        angle_a = math.acos(
            (side_a ** 2 + side_c ** 2 - side_b ** 2) / (2 * side_a * side_c)
        )
        c_vertex = (side_c * math.cos(angle_a), side_c * math.sin(angle_a))

        fig, ax = plt.subplots(figsize=(5, 5))

        triangle = plt.Polygon(
            [a_vertex, b_vertex, c_vertex], closed=True,
            edgecolor="black", facecolor="none", linewidth=2,
        )
        ax.add_patch(triangle)

        def midpoint(p, q):
            return ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)

        # side_a: edge A-B, label below it.
        mid_ab = midpoint(a_vertex, b_vertex)
        ax.annotate(
            f"a = {side_a}",
            xy=mid_ab, xytext=(0, -18), textcoords="offset points",
            ha="center", fontsize=11,
        )

        # side_b: edge B-C, label offset to the right of its midpoint.
        mid_bc = midpoint(b_vertex, c_vertex)
        ax.annotate(
            f"b = {side_b}",
            xy=mid_bc, xytext=(12, 0), textcoords="offset points",
            ha="left", va="center", fontsize=11,
        )

        # side_c: edge C-A, label offset to the left of its midpoint.
        mid_ca = midpoint(c_vertex, a_vertex)
        ax.annotate(
            f"c = {side_c}",
            xy=mid_ca, xytext=(-12, 0), textcoords="offset points",
            ha="right", va="center", fontsize=11,
        )

        xs = [a_vertex[0], b_vertex[0], c_vertex[0]]
        ys = [a_vertex[1], b_vertex[1], c_vertex[1]]
        x_pad = (max(xs) - min(xs)) * 0.25 + 1
        y_pad = (max(ys) - min(ys)) * 0.25 + 1
        ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
        ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)
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
