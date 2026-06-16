#!/usr/bin/env python3
"""Chart 8: YOLO precision/recall/mAP and optional PR/F1 curve CSVs.

Runs Ultralytics ``model.val()`` for a FootBot soccer-vision dataset and writes
per-class metrics. If the installed Ultralytics version exposes curve arrays,
this script also writes ``pr_curve.csv`` and ``f1_curve.csv``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.csv_utils import default_csv_path, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--weights', required=True, help='YOLO .pt weights.')
    parser.add_argument('--data', required=True, help='YOLO data.yaml path.')
    parser.add_argument('--output', default=str(default_csv_path('08_yolo_eval.csv')))
    parser.add_argument('--pr-output', default=str(default_csv_path('08_pr_curve.csv')))
    parser.add_argument('--f1-output', default=str(default_csv_path('08_f1_curve.csv')))
    parser.add_argument('--split', default='val')
    parser.add_argument('--image-size', type=int, default=640)
    parser.add_argument('--conf', type=float, default=0.001)
    parser.add_argument('--iou', type=float, default=0.6)
    parser.add_argument('--device', default='cpu')
    parser.add_argument(
        '--project',
        default=str(Path(__file__).resolve().parents[4] / 'simulation' / 'ros2_ws' / 'src' / 'footbot_soccer_vision' / 'runs' / 'val'),
        help='Ultralytics validation project directory.',
    )
    parser.add_argument('--name', default='report_metrics')
    return parser.parse_args()


def load_names(data_yaml):
    with Path(data_yaml).expanduser().open('r', encoding='utf-8') as handle:
        data = yaml.safe_load(handle) or {}
    names = data.get('names', {})
    if isinstance(names, dict):
        return [names[index] for index in sorted(names)]
    return list(names)


def array_or_empty(obj, attr):
    value = getattr(obj, attr, None)
    if value is None:
        return np.array([], dtype=float)
    return np.asarray(value, dtype=float)


def metric_rows(results, names):
    box = getattr(results, 'box', results)
    precision = array_or_empty(box, 'p')
    recall = array_or_empty(box, 'r')
    map50 = array_or_empty(box, 'ap50')
    map50_95 = array_or_empty(box, 'ap')

    # Some Ultralytics versions expose only aggregate map/map50 fields.
    aggregate_map50 = getattr(box, 'map50', '')
    aggregate_map = getattr(box, 'map', '')
    n = max(len(names), precision.size, recall.size, map50.size, map50_95.size)
    rows = []
    for index in range(n):
        rows.append({
            'class': names[index] if index < len(names) else str(index),
            'precision': float(precision[index]) if index < precision.size else '',
            'recall': float(recall[index]) if index < recall.size else '',
            'map50': float(map50[index]) if index < map50.size else aggregate_map50,
            'map50_95': float(map50_95[index]) if index < map50_95.size else aggregate_map,
        })
    return rows


def write_curve_csv(results, curve_name, output):
    """Best-effort extraction for Ultralytics curve arrays."""

    rows = []
    box = getattr(results, 'box', results)
    curves_results = getattr(box, 'curves_results', None) or getattr(results, 'curves_results', None)

    if curves_results:
        for curve in curves_results:
            if len(curve) < 4:
                continue
            x_values, y_values, x_label, y_label = curve[:4]
            x_label = str(x_label).lower()
            y_label = str(y_label).lower()
            if curve_name == 'pr' and 'recall' not in x_label:
                continue
            if curve_name == 'f1' and 'f1' not in y_label:
                continue
            y_array = np.asarray(y_values)
            x_array = np.asarray(x_values)
            if y_array.ndim == 1:
                y_array = y_array.reshape(1, -1)
            for class_index, class_values in enumerate(y_array):
                for x, y in zip(x_array, class_values):
                    if curve_name == 'pr':
                        rows.append({'class': class_index, 'recall': float(x), 'precision': float(y)})
                    else:
                        rows.append({'class': class_index, 'conf': float(x), 'f1': float(y)})

    columns = ['class', 'recall', 'precision'] if curve_name == 'pr' else ['class', 'conf', 'f1']
    write_csv(rows, output, columns=columns)
    if not rows:
        print(
            f'warning: this Ultralytics version did not expose {curve_name.upper()} curve arrays; '
            f'wrote header-only CSV: {output}',
            file=sys.stderr,
        )


def main():
    args = parse_args()
    weights = Path(args.weights).expanduser()
    data = Path(args.data).expanduser()
    if not weights.exists():
        fail(f'weights not found: {weights}')
    if not data.exists():
        fail(f'data.yaml not found: {data}')

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit(
            'error: ultralytics is not installed. Install metrics requirements or '
            '`python3 -m pip install --user -r simulation/requirements-yolo.txt`.'
        ) from exc

    model = YOLO(str(weights))
    results = model.val(
        data=str(data),
        split=args.split,
        imgsz=args.image_size,
        conf=args.conf,
        iou=args.iou,
        device=args.device,
        project=str(Path(args.project).expanduser()),
        name=args.name,
        plots=True,
    )
    names = load_names(data)
    write_csv(
        metric_rows(results, names),
        args.output,
        columns=['class', 'precision', 'recall', 'map50', 'map50_95'],
    )
    write_curve_csv(results, 'pr', args.pr_output)
    write_curve_csv(results, 'f1', args.f1_output)


if __name__ == '__main__':
    main()
