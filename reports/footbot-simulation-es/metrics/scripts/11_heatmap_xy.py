#!/usr/bin/env python3
"""Derived chart: Robot and ball XY occupancy heatmap bins.

This script does not draw a plot. It converts ``09_trajectory_xy`` output into a
stable CSV grid that can later be rendered as a heatmap for the robot and the
ball. The dwell-time columns help identify areas where the behavior gets stuck,
for example near the goal mouth.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.csv_utils import default_csv_path, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--input',
        required=True,
        help='Trajectory CSV from 09_trajectory_xy.py or 09_trajectory_xy_trials.csv.',
    )
    parser.add_argument('--output', default=str(default_csv_path('11_heatmap_xy.csv')))
    parser.add_argument('--cell-size', type=float, default=0.10, help='Grid cell size in meters.')
    parser.add_argument('--x-min', type=float, default=None)
    parser.add_argument('--x-max', type=float, default=None)
    parser.add_argument('--y-min', type=float, default=None)
    parser.add_argument('--y-max', type=float, default=None)
    parser.add_argument(
        '--max-delta-sec',
        type=float,
        default=1.0,
        help='Cap dwell time per sample to avoid large gaps between episodes.',
    )
    return parser.parse_args()


def finite_float(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def bin_index(value, minimum, cell_size):
    return math.floor((value - minimum) / cell_size)


def bin_center(index, minimum, cell_size):
    return minimum + (index + 0.5) * cell_size


def add_sample(accumulator, entity, x, y, dt, x_min, y_min, cell_size):
    x_bin = bin_index(x, x_min, cell_size)
    y_bin = bin_index(y, y_min, cell_size)
    key = (entity, x_bin, y_bin)
    item = accumulator[key]
    item['count'] += 1
    item['dwell_time_s'] += max(dt, 0.0)


def main():
    args = parse_args()
    if args.cell_size <= 0.0:
        fail('--cell-size must be positive')
    if args.max_delta_sec < 0.0:
        fail('--max-delta-sec cannot be negative')

    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            'error: pandas is required. Install '
            '`reports/footbot-simulation-es/metrics/requirements.txt`.'
        ) from exc

    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        fail(f'input CSV not found: {input_path}')

    frame = pd.read_csv(input_path)
    required = {'t_s', 'ball_x', 'ball_y', 'robot_x', 'robot_y'}
    missing = sorted(required - set(frame.columns))
    if missing:
        fail(f'input CSV is missing required columns: {", ".join(missing)}')

    frame = frame.sort_values('t_s').reset_index(drop=True)
    points_x = []
    points_y = []
    for _, row in frame.iterrows():
        for prefix in ('ball', 'robot'):
            x = finite_float(row.get(f'{prefix}_x'))
            y = finite_float(row.get(f'{prefix}_y'))
            if x is not None and y is not None:
                points_x.append(x)
                points_y.append(y)

    if not points_x or not points_y:
        fail('trajectory CSV contains no valid ball or robot positions')

    x_min = args.x_min if args.x_min is not None else math.floor(min(points_x) / args.cell_size) * args.cell_size
    x_max = args.x_max if args.x_max is not None else math.ceil(max(points_x) / args.cell_size) * args.cell_size
    y_min = args.y_min if args.y_min is not None else math.floor(min(points_y) / args.cell_size) * args.cell_size
    y_max = args.y_max if args.y_max is not None else math.ceil(max(points_y) / args.cell_size) * args.cell_size

    if x_max <= x_min or y_max <= y_min:
        fail('invalid heatmap bounds')

    timestamps = [finite_float(value) for value in frame['t_s']]
    positive_deltas = [
        timestamps[index + 1] - timestamps[index]
        for index in range(len(timestamps) - 1)
        if timestamps[index] is not None
        and timestamps[index + 1] is not None
        and timestamps[index + 1] > timestamps[index]
    ]
    fallback_dt = min(positive_deltas) if positive_deltas else 0.0

    accumulator = defaultdict(lambda: {'count': 0, 'dwell_time_s': 0.0})
    total_time_by_entity = defaultdict(float)
    skipped_out_of_bounds = 0

    for index, row in frame.iterrows():
        now = finite_float(row.get('t_s'))
        next_t = timestamps[index + 1] if index + 1 < len(timestamps) else None
        if now is not None and next_t is not None and next_t > now:
            dt = next_t - now
        else:
            dt = fallback_dt
        dt = min(dt, args.max_delta_sec)

        for prefix in ('ball', 'robot'):
            x = finite_float(row.get(f'{prefix}_x'))
            y = finite_float(row.get(f'{prefix}_y'))
            if x is None or y is None:
                continue
            if x < x_min or x > x_max or y < y_min or y > y_max:
                skipped_out_of_bounds += 1
                continue
            add_sample(accumulator, prefix, x, y, dt, x_min, y_min, args.cell_size)
            total_time_by_entity[prefix] += max(dt, 0.0)

    rows = []
    for (entity, x_bin, y_bin), item in sorted(accumulator.items()):
        total_time = total_time_by_entity[entity]
        rows.append({
            'entity': entity,
            'x_bin': x_bin,
            'y_bin': y_bin,
            'x_center': bin_center(x_bin, x_min, args.cell_size),
            'y_center': bin_center(y_bin, y_min, args.cell_size),
            'count': item['count'],
            'dwell_time_s': item['dwell_time_s'],
            'pct_time': (100.0 * item['dwell_time_s'] / total_time) if total_time > 0.0 else '',
            'cell_size_m': args.cell_size,
            'x_min': x_min,
            'x_max': x_max,
            'y_min': y_min,
            'y_max': y_max,
            'skipped_out_of_bounds': skipped_out_of_bounds,
        })

    write_csv(
        rows,
        args.output,
        columns=[
            'entity',
            'x_bin',
            'y_bin',
            'x_center',
            'y_center',
            'count',
            'dwell_time_s',
            'pct_time',
            'cell_size_m',
            'x_min',
            'x_max',
            'y_min',
            'y_max',
            'skipped_out_of_bounds',
        ],
    )


if __name__ == '__main__':
    main()

