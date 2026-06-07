#!/usr/bin/env python3
"""Run YOLO predictions on image files for visual inspection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--iou', type=float, default=0.45)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--image-size', type=int, default=640)
    parser.add_argument('--project', type=Path, default=Path('simulation/ros2_ws/src/footbot_soccer_vision/runs/predict'))
    parser.add_argument('--name', default='reach_goal_predictions')
    return parser.parse_args()


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / '.git').exists():
            return parent
    for parent in current.parents:
        if (parent / 'simulation' / 'ros2_ws' / 'src').exists():
            return parent
    return Path.cwd()


def resolve_path(path: Path, base: Path) -> Path:
    return path if path.is_absolute() else (base / path).resolve()


def main() -> int:
    args = parse_args()
    base = repo_root()
    weights = resolve_path(args.weights, base)
    source = resolve_path(args.source, base)
    project = resolve_path(args.project, base)

    if not weights.exists():
        print(f'error: weights not found: {weights}', file=sys.stderr)
        return 1
    if not source.exists():
        print(f'error: source not found: {source}', file=sys.stderr)
        return 1

    try:
        from ultralytics import YOLO
    except ImportError:
        print(
            'error: Ultralytics YOLO is not installed. Run: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt',
            file=sys.stderr,
        )
        return 1

    results = YOLO(str(weights)).predict(
        source=str(source),
        conf=args.conf,
        iou=args.iou,
        imgsz=args.image_size,
        device=args.device,
        project=str(project),
        name=args.name,
        save=True,
        exist_ok=True,
    )
    if results:
        print(f'Predictions saved under {results[0].save_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
