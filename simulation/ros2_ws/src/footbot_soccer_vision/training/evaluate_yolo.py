#!/usr/bin/env python3
"""Evaluate a trained YOLO model on a YOLO data.yaml file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--image-size', type=int, default=640)
    parser.add_argument('--project', type=Path, default=Path('simulation/ros2_ws/src/footbot_soccer_vision/runs/val'))
    parser.add_argument('--name', default='reach_goal_eval')
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
    data = resolve_path(args.data, base)
    project = resolve_path(args.project, base)

    if not weights.exists():
        print(f'error: weights not found: {weights}', file=sys.stderr)
        return 1
    if not data.exists():
        print(f'error: data.yaml not found: {data}', file=sys.stderr)
        return 1

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        print(
            'error: Ultralytics YOLO is not installed. Run: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt',
            file=sys.stderr,
        )
        return 1

    model = YOLO(str(weights))
    model.val(
        data=str(data),
        imgsz=args.image_size,
        device=args.device,
        project=str(project),
        name=args.name,
        plots=True,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
