"""
Generate N instances from a template and save them to output/<template_id>/,
matching the storage format in docs/spec.md Section 7:

  output/<template_id>/instances.json
  output/<template_id>/images/<instance_id>.png

Usage:
  python scripts/run_generate.py <template_path> [n] [seed]

Example:
  python scripts/run_generate.py templates/geometry_measurement/plane_shapes/triangle/area_given_base_height 100 0
"""

import json
import shutil
import sys
from pathlib import Path

# Allow running this script directly (python scripts/run_generate.py ...)
# by ensuring the repo root is on sys.path, since core/ is a flat package,
# not installed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.orchestrator import generate


def main():
    template_path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    instances = generate(template_path, seed=seed, n=n)

    template_id = instances[0]["id"].rsplit("-", 1)[0] if instances else "unknown"
    out_dir = Path("output") / template_id
    images_out_dir = out_dir / "images"
    images_out_dir.mkdir(parents=True, exist_ok=True)

    # Copy each instance's image (if any) into output/<template_id>/images/
    # and rewrite image_path to be relative to out_dir, per the storage format.
    for instance in instances:
        if instance["image_path"] is not None:
            src = Path(template_path) / instance["image_path"]
            dst_name = f"{instance['id']}.png"
            dst = images_out_dir / dst_name
            shutil.copyfile(src, dst)
            instance["image_path"] = f"images/{dst_name}"

    with open(out_dir / "instances.json", "w") as f:
        json.dump(instances, f, indent=2)

    print(f"Generated {len(instances)} instances -> {out_dir / 'instances.json'}")
    if any(inst["image_path"] for inst in instances):
        print(f"Images -> {images_out_dir}")


if __name__ == "__main__":
    main()
