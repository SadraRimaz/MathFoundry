import hashlib
from pathlib import Path
from random import Random
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.problem_generator import ProblemGenerator

IMAGES_DIR = Path(__file__).parent / "_generated_images"


class TriangleAreaGenerator(ProblemGenerator):

    def sample_parameters(self, rng: Random) -> dict:
        return {
            "base": self._sample_discrete(rng, "base"),
            "height": self._sample_discrete(rng, "height"),
            "apex_offset": self._sample_discrete(rng, "apex_offset"),
        }

    def compute_solution(self, params: dict) -> tuple[Any, dict[str, Any]]:
        base = params["base"]
        height = params["height"]
        area = 0.5 * base * height
        return area, {"area": area}

    def render_problem_text(self, params: dict, template: str) -> str:
        # No placeholders are expected in this template's problem_text
        # (all data is conveyed by the image) — .format is still applied
        # defensively so this stays correct if a future phrasing adds one.
        return template.format(**params)

    def render_image(self, params: dict) -> str | None:
        base = params["base"]
        height = params["height"]
        apex_offset = params["apex_offset"]

        # Triangle vertices: base along the x-axis, apex positioned by
        # apex_offset as a fraction of base (0 = above left end,
        # 1 = above right end).
        left = (0, 0)
        right = (base, 0)
        apex = (apex_offset * base, height)
        apex_x, apex_y = apex

        fig, ax = plt.subplots(figsize=(5, 5))

        triangle = plt.Polygon(
            [left, right, apex], closed=True,
            edgecolor="black", facecolor="none", linewidth=2,
        )
        ax.add_patch(triangle)

        # base label
        ax.plot([left[0], right[0]], [left[1], right[1]], color="black")
        ax.annotate(
            f"base = {base}",
            xy=((left[0] + right[0]) / 2, 0),
            xytext=(0, -18), textcoords="offset points",
            ha="center", fontsize=11,
        )

        # height: dashed perpendicular from apex down to the base line
        ax.plot(
            [apex_x, apex_x], [0, apex_y],
            linestyle="--", color="gray", linewidth=1.5,
        )
        ax.annotate(
            f"height = {height}",
            xy=(apex_x, apex_y / 2),
            xytext=(10, 0), textcoords="offset points",
            ha="left", va="center", fontsize=11, color="gray",
        )

        ax.set_xlim(min(0, apex_x) - base * 0.15, max(base, apex_x) + base * 0.15)
        ax.set_ylim(-height * 0.25, height * 1.15)
        ax.set_aspect("equal")
        ax.axis("off")

        # Deterministic filename from the sampled params: same params ->
        # same image file. Rendered before the instance's id is assembled
        # (orchestrator calls render_image before building the id), so a
        # param hash is used instead of the id.
        param_key = f"{base}-{height}-{apex_offset}"
        filename = hashlib.sha1(param_key.encode()).hexdigest()[:16] + ".png"

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        out_path = IMAGES_DIR / filename
        fig.savefig(out_path, bbox_inches="tight", dpi=100)
        plt.close(fig)

        # Relative to the template's own directory (spec.md Section 7:
        # image_path is relative to the template's output location, not
        # an absolute filesystem path).
        return str(out_path.relative_to(Path(__file__).parent))