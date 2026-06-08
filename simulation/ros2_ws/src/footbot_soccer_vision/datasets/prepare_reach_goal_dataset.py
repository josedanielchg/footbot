#!/usr/bin/env python3
"""Prepare filtered YOLO datasets for Reach Goal soccer behavior."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from collections import Counter
from pathlib import Path


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--classes', nargs='+', default=['ball', 'goal'])
    parser.add_argument('--copy-images', action='store_true')
    parser.add_argument('--symlink-images', action='store_true')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--train-ratio', type=float, default=0.8)
    parser.add_argument('--val-ratio', type=float, default=0.15)
    parser.add_argument('--test-ratio', type=float, default=0.05)
    parser.add_argument('--overwrite', action='store_true')
    return parser.parse_args()


def normalize_names(value) -> list[str]:
    if isinstance(value, dict):
        return [str(value[index]) for index in sorted(value)]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError('names must be a list or mapping')


def load_yaml_module():
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - validated through CLI message.
        raise ValueError(
            'PyYAML is required. Install dependencies with: '
            'python3 -m pip install --user -r simulation/requirements-yolo.txt'
        ) from exc
    return yaml


def load_class_names(input_dir: Path) -> list[str]:
    yaml = load_yaml_module()
    data_yaml = input_dir / 'data.yaml'
    if data_yaml.exists():
        data = yaml.safe_load(data_yaml.read_text(encoding='utf-8')) or {}
        if 'names' in data:
            return normalize_names(data['names'])

    classes_txt = input_dir / 'classes.txt'
    if classes_txt.exists():
        return [line.strip() for line in classes_txt.read_text(encoding='utf-8').splitlines() if line.strip()]

    raise ValueError(f'Could not find class names in {data_yaml} or {classes_txt}')


def resolve_yaml_path(input_dir: Path, split: str) -> Path | None:
    data_yaml = input_dir / 'data.yaml'
    if not data_yaml.exists():
        return None
    yaml = load_yaml_module()
    data = yaml.safe_load(data_yaml.read_text(encoding='utf-8')) or {}
    raw = data.get(split)
    if raw is None:
        return None
    path = Path(str(raw))
    if path.is_absolute():
        return path
    base = Path(data.get('path', input_dir))
    if not base.is_absolute():
        base = input_dir / base
    return base / path


def infer_label_dir(image_dir: Path, split: str) -> Path:
    parts = list(image_dir.parts)
    if 'images' in parts:
        index = len(parts) - 1 - parts[::-1].index('images')
        parts[index] = 'labels'
        return Path(*parts)
    return image_dir.parent.parent / 'labels' / split


def image_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(
        item for item in path.iterdir()
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS
    )


def discover_pairs(input_dir: Path) -> list[tuple[Path, Path, str]]:
    pairs: list[tuple[Path, Path, str]] = []

    for split in ('train', 'val', 'test'):
        image_dir = resolve_yaml_path(input_dir, split)
        candidates = []
        if image_dir is not None:
            candidates.append(image_dir)
        candidates.extend([
            input_dir / 'images' / split,
            input_dir / split / 'images',
        ])

        for candidate in candidates:
            images = image_files(candidate)
            if not images:
                continue
            label_dir = infer_label_dir(candidate, split)
            for image in images:
                pairs.append((image, label_dir / f'{image.stem}.txt', split))

    if pairs:
        return pairs

    flat_candidates = [input_dir / 'images', input_dir]
    for image_dir in flat_candidates:
        for image in image_files(image_dir):
            label_dir = input_dir / 'labels'
            pairs.append((image, label_dir / f'{image.stem}.txt', 'unsplit'))
    return pairs


def split_pairs(
    pairs: list[tuple[Path, Path, str]],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[tuple[Path, Path]]]:
    if any(split != 'unsplit' for _, _, split in pairs):
        result = {'train': [], 'val': [], 'test': []}
        for image, label, split in pairs:
            if split in result:
                result[split].append((image, label))
        return result

    total_ratio = train_ratio + val_ratio + test_ratio
    if total_ratio <= 0:
        raise ValueError('split ratios must sum to a positive value')
    train_ratio /= total_ratio
    val_ratio /= total_ratio

    shuffled = [(image, label) for image, label, _ in pairs]
    random.Random(seed).shuffle(shuffled)

    train_count = int(len(shuffled) * train_ratio)
    val_count = int(len(shuffled) * val_ratio)
    if len(shuffled) > 1 and val_count == 0:
        val_count = 1
    return {
        'train': shuffled[:train_count],
        'val': shuffled[train_count:train_count + val_count],
        'test': shuffled[train_count + val_count:],
    }


def remap_label_file(
    source: Path,
    destination: Path,
    class_map: dict[int, int],
    class_names: list[str],
    kept_class_names: list[str],
) -> Counter:
    counts = Counter()
    destination.parent.mkdir(parents=True, exist_ok=True)
    output_lines = []

    if source.exists():
        for line in source.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            fields = stripped.split()
            if len(fields) != 5:
                raise ValueError(f'malformed label in {source}: {line}')
            old_id = int(fields[0])
            if old_id < 0 or old_id >= len(class_names):
                raise ValueError(f'invalid class id {old_id} in {source}')
            if old_id not in class_map:
                continue
            new_id = class_map[old_id]
            output_lines.append(' '.join([str(new_id), *fields[1:]]))
            counts[kept_class_names[new_id]] += 1

    destination.write_text('\n'.join(output_lines) + ('\n' if output_lines else ''), encoding='utf-8')
    return counts


def copy_or_link_image(source: Path, destination: Path, symlink: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    if symlink:
        destination.symlink_to(source.resolve())
    else:
        shutil.copy2(source, destination)


def write_data_yaml(output_dir: Path, classes: list[str]) -> None:
    yaml = load_yaml_module()
    data = {
        'path': str(output_dir.resolve()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': classes,
    }
    with (output_dir / 'data.yaml').open('w', encoding='utf-8') as file:
        yaml.safe_dump(data, file, sort_keys=False)


def prepare_dataset(args: argparse.Namespace) -> int:
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.exists():
        raise ValueError(f'input dataset does not exist: {input_dir}')
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise ValueError(f'output directory is not empty; use --overwrite: {output_dir}')
    if args.copy_images and args.symlink_images:
        raise ValueError('choose either --copy-images or --symlink-images, not both')

    if output_dir.exists() and args.overwrite:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_classes = load_class_names(input_dir)
    requested_classes = [item.strip() for item in args.classes if item.strip()]
    missing_classes = [name for name in requested_classes if name not in input_classes]
    if missing_classes:
        raise ValueError(f'requested classes not found in input dataset: {missing_classes}')

    class_map = {
        input_classes.index(name): new_id
        for new_id, name in enumerate(requested_classes)
    }

    pairs = discover_pairs(input_dir)
    if not pairs:
        raise ValueError(f'no images found in {input_dir}')

    split_map = split_pairs(
        pairs,
        args.train_ratio,
        args.val_ratio,
        args.test_ratio,
        args.seed,
    )

    class_counts = Counter()
    image_counts = Counter()
    label_counts = Counter()
    empty_labels = Counter()

    symlink = args.symlink_images and not args.copy_images
    for split, split_pairs_value in split_map.items():
        for image, label in split_pairs_value:
            image_dest = output_dir / 'images' / split / image.name
            label_dest = output_dir / 'labels' / split / f'{image.stem}.txt'
            copy_or_link_image(image, image_dest, symlink)
            counts = remap_label_file(label, label_dest, class_map, input_classes, requested_classes)
            image_counts[split] += 1
            label_counts[split] += sum(counts.values())
            if not counts:
                empty_labels[split] += 1
            class_counts.update(counts)

    write_data_yaml(output_dir, requested_classes)
    report = {
        'input_dir': str(input_dir),
        'output_dir': str(output_dir),
        'classes': requested_classes,
        'input_classes': input_classes,
        'image_counts': dict(image_counts),
        'label_counts': dict(label_counts),
        'empty_label_files': dict(empty_labels),
        'class_counts': dict(class_counts),
        'image_mode': 'symlink' if symlink else 'copy',
        'seed': args.seed,
    }
    (output_dir / 'preparation_report.json').write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding='utf-8',
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main() -> int:
    args = parse_args()
    try:
        return prepare_dataset(args)
    except ValueError as exc:
        print(f'error: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
