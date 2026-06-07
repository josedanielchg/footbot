#!/usr/bin/env python3
"""Train a YOLO model for FootBot Reach Goal soccer perception."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


DATASETS_DIR = Path(__file__).resolve().parents[1] / 'datasets'
sys.path.insert(0, str(DATASETS_DIR))

from validate_yolo_dataset import validate_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--device', default=None)
    parser.add_argument('--dry-run', action='store_true')
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


def resolve_path(value: str | Path, base: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def load_yaml_module():
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - validated through CLI message.
        raise RuntimeError(
            'PyYAML is required. Install dependencies with: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt'
        ) from exc
    return yaml


def load_config(path: Path) -> dict:
    yaml = load_yaml_module()
    with path.open('r', encoding='utf-8') as file:
        config = yaml.safe_load(file) or {}
    required = [
        'dataset_dir',
        'model',
        'image_size',
        'epochs',
        'batch',
        'patience',
        'device',
        'workers',
        'seed',
        'project',
        'name',
        'target_model_dir',
        'final_weights_name',
    ]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f'training config missing keys: {missing}')
    return config


def validate_from_config(config: dict, base: Path) -> int:
    dataset_dir = resolve_path(config['dataset_dir'], base)
    namespace = argparse.Namespace(
        dataset_dir=dataset_dir,
        min_images=0,
        require_splits=config.get('required_splits', ['train', 'val']),
    )
    return validate_dataset(namespace)


def train(config: dict, base: Path, device_override: str | None, dry_run: bool) -> int:
    validation_result = validate_from_config(config, base)
    if validation_result != 0:
        return validation_result

    dataset_dir = resolve_path(config['dataset_dir'], base)
    project = resolve_path(config['project'], base)
    target_model_dir = resolve_path(config['target_model_dir'], base)
    device = device_override if device_override is not None else str(config['device'])

    if dry_run:
        print('Dry run OK. Training would use:')
        print(f'  dataset: {dataset_dir}')
        print(f'  model: {config["model"]}')
        print(f'  device: {device}')
        print(f'  project: {project}')
        print(f'  run name: {config["name"]}')
        print(f'  target model dir: {target_model_dir}')
        return 0

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            'Ultralytics YOLO is not installed. Install dependencies with: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt'
        ) from exc

    project.mkdir(parents=True, exist_ok=True)
    target_model_dir.mkdir(parents=True, exist_ok=True)

    results = YOLO(str(config['model'])).train(
        data=str(dataset_dir / 'data.yaml'),
        imgsz=int(config['image_size']),
        epochs=int(config['epochs']),
        batch=int(config['batch']),
        patience=int(config['patience']),
        device=device,
        workers=int(config['workers']),
        seed=int(config['seed']),
        project=str(project),
        name=str(config['name']),
        exist_ok=True,
        deterministic=True,
        plots=True,
    )

    run_dir = Path(results.save_dir)
    best_weights = run_dir / 'weights' / 'best.pt'
    if not best_weights.exists():
        raise RuntimeError(f'best.pt not found after training: {best_weights}')

    final_weights = target_model_dir / str(config['final_weights_name'])
    shutil.copy2(best_weights, final_weights)
    print(f'Saved best weights to {final_weights}')
    print(f'Training artifacts remain in {run_dir}')
    return 0


def main() -> int:
    args = parse_args()
    base = repo_root()
    try:
        config = load_config(args.config)
        return train(config, base, args.device, args.dry_run)
    except (RuntimeError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
