#!/usr/bin/env python3
"""Validate a YOLO detection dataset before training."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import cv2
except ImportError:  # pragma: no cover - validated through CLI message.
    cv2 = None


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-dir', required=True, type=Path)
    parser.add_argument('--min-images', type=int, default=0)
    parser.add_argument('--require-splits', nargs='+', default=['train', 'val'])
    return parser.parse_args()


def load_yaml_module():
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - validated through CLI message.
        raise ValueError(
            'PyYAML is required. Install dependencies with: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt'
        ) from exc
    return yaml


def read_data_yaml(dataset_dir: Path) -> dict:
    data_yaml = dataset_dir / 'data.yaml'
    if not data_yaml.exists():
        raise ValueError(f'data.yaml not found: {data_yaml}')

    yaml = load_yaml_module()
    with data_yaml.open('r', encoding='utf-8') as file:
        data = yaml.safe_load(file) or {}

    missing = [key for key in ('train', 'val', 'names') if key not in data]
    if missing:
        raise ValueError(f'data.yaml missing required keys: {", ".join(missing)}')

    names = normalize_names(data['names'])
    if not names:
        raise ValueError('data.yaml names is empty')
    data['names'] = names
    return data


def normalize_names(value) -> list[str]:
    if isinstance(value, dict):
        return [str(value[index]) for index in sorted(value)]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError('data.yaml names must be a list or mapping')


def resolve_path(dataset_dir: Path, data: dict, split: str) -> Path:
    raw = data.get(split)
    if raw is None:
        raise ValueError(f'data.yaml missing split path: {split}')
    path = Path(str(raw))
    if path.is_absolute():
        return path

    base = Path(data.get('path', dataset_dir))
    if not base.is_absolute():
        base = dataset_dir / base
    return (base / path).resolve()


def infer_label_dir(image_dir: Path, split: str) -> Path:
    parts = list(image_dir.parts)
    if 'images' in parts:
        index = len(parts) - 1 - parts[::-1].index('images')
        parts[index] = 'labels'
        return Path(*parts)
    return image_dir.parent.parent / 'labels' / split


def list_images(path: Path) -> list[Path]:
    return sorted(
        item for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
    )


def validate_label_file(label_path: Path, class_count: int) -> tuple[list[int], list[str]]:
    class_ids: list[int] = []
    errors: list[str] = []
    if not label_path.exists():
        return class_ids, [f'missing label file: {label_path}']

    lines = label_path.read_text(encoding='utf-8').splitlines()
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        fields = stripped.split()
        if len(fields) != 5:
            errors.append(f'{label_path}:{line_number}: expected 5 fields, got {len(fields)}')
            continue
        try:
            class_id = int(fields[0])
            values = [float(value) for value in fields[1:]]
        except ValueError:
            errors.append(f'{label_path}:{line_number}: non-numeric YOLO label')
            continue
        if class_id < 0 or class_id >= class_count:
            errors.append(f'{label_path}:{line_number}: invalid class id {class_id}')
        for value in values:
            if value < 0.0 or value > 1.0:
                errors.append(f'{label_path}:{line_number}: bbox value out of [0, 1]: {value}')
        if values[2] <= 0.0 or values[3] <= 0.0:
            errors.append(f'{label_path}:{line_number}: bbox width/height must be positive')
        class_ids.append(class_id)
    return class_ids, errors


def image_is_readable(path: Path) -> bool:
    if cv2 is None:
        return True
    return cv2.imread(str(path)) is not None


def validate_dataset(args: argparse.Namespace) -> int:
    dataset_dir = args.dataset_dir.resolve()
    if not dataset_dir.exists():
        raise ValueError(f'dataset directory not found: {dataset_dir}')

    data = read_data_yaml(dataset_dir)
    names = data['names']
    class_counts = Counter()
    image_counts = Counter()
    label_counts = Counter()
    empty_labels = Counter()
    duplicate_stems = defaultdict(list)
    warnings: list[str] = []
    errors: list[str] = []

    for split in args.require_splits:
        image_dir = resolve_path(dataset_dir, data, split)
        label_dir = infer_label_dir(image_dir, split)

        if not image_dir.exists():
            errors.append(f'{split}: image directory missing: {image_dir}')
            continue
        if not label_dir.exists():
            errors.append(f'{split}: label directory missing: {label_dir}')
            continue

        images = list_images(image_dir)
        image_counts[split] = len(images)
        if not images:
            errors.append(f'{split}: no images found in {image_dir}')

        for image in images:
            duplicate_stems[image.stem].append(str(image))
            if not image_is_readable(image):
                errors.append(f'{split}: broken/unreadable image: {image}')

            label_path = label_dir / f'{image.stem}.txt'
            ids, label_errors = validate_label_file(label_path, len(names))
            errors.extend(f'{split}: {error}' for error in label_errors)
            label_counts[split] += len(ids)
            if label_path.exists() and not ids:
                empty_labels[split] += 1
            for class_id in ids:
                class_counts[names[class_id]] += 1

    total_images = sum(image_counts.values())
    if args.min_images and total_images < args.min_images:
        warnings.append(f'dataset has {total_images} images; requested minimum is {args.min_images}')

    for stem, paths in duplicate_stems.items():
        if len(paths) > 1:
            warnings.append(f'duplicate filename stem "{stem}": {paths}')

    if len(class_counts) > 1:
        values = [count for count in class_counts.values() if count > 0]
        if values and min(values) / max(values) < 0.25:
            warnings.append('class imbalance warning: smallest nonzero class has less than 25% of largest class')

    print('YOLO dataset summary')
    print(f'  dataset: {dataset_dir}')
    print(f'  classes: {names}')
    print(f'  images by split: {dict(image_counts)}')
    print(f'  labels by split: {dict(label_counts)}')
    print(f'  empty labels by split: {dict(empty_labels)}')
    print(f'  labels by class: {dict(class_counts)}')

    if warnings:
        print('\nWarnings:')
        for warning in warnings:
            print(f'  - {warning}')

    if errors:
        print('\nErrors:', file=sys.stderr)
        for error in errors:
            print(f'  - {error}', file=sys.stderr)
        return 1
    return 0


def main() -> int:
    args = parse_args()
    try:
        return validate_dataset(args)
    except ValueError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
