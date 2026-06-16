#!/usr/bin/env python3
"""Chart 2: Topic frequency in Hz.

Computes frequency statistics from an offline rosbag2 recording. This is the
preferred reproducible path for the report; use ``ros2 topic hz`` manually only
for quick live checks.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, read_messages, topic_types
from common.csv_utils import default_csv_path, fail, write_csv


DEFAULT_TOPICS = [
    '/camera/image_raw',
    '/cmd_vel',
    '/ball_detection',
    '/soccer/ball_state',
    '/soccer/detections',
    '/soccer/ball_goal_state',
    '/soccer/reach_goal_fsm_state',
    '/soccer/goal_scored',
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='rosbag2 directory.')
    parser.add_argument('--output', default=str(default_csv_path('02_topic_hz.csv')))
    parser.add_argument('--topics', nargs='*', default=DEFAULT_TOPICS)
    return parser.parse_args()


def topic_row(topic, stamps):
    stamps = sorted(stamps)
    count = len(stamps)
    if count < 2:
        return {
            'topic': topic,
            'count': count,
            'duration_s': 0.0,
            'mean_hz': '',
            'min_hz': '',
            'max_hz': '',
            'std_hz': '',
        }
    deltas = np.diff(np.array(stamps, dtype=float))
    deltas = deltas[deltas > 0.0]
    duration = stamps[-1] - stamps[0]
    if deltas.size == 0 or duration <= 0.0:
        mean_hz = ''
        hz_values = np.array([], dtype=float)
    else:
        mean_hz = float((count - 1) / duration)
        hz_values = 1.0 / deltas
    return {
        'topic': topic,
        'count': count,
        'duration_s': duration,
        'mean_hz': mean_hz,
        'min_hz': float(np.min(hz_values)) if hz_values.size else '',
        'max_hz': float(np.max(hz_values)) if hz_values.size else '',
        'std_hz': float(np.std(hz_values)) if hz_values.size else '',
    }


def main():
    args = parse_args()
    try:
        available = topic_types(args.input)
        selected = [topic for topic in args.topics if topic in available]
        missing = [topic for topic in args.topics if topic not in available]
        for topic in missing:
            print(f'warning: topic not in bag, skipping: {topic}', file=sys.stderr)
        if not selected:
            fail('none of the requested topics exist in the bag')

        stamps_by_topic = defaultdict(list)
        for item in read_messages(args.input, selected):
            stamps_by_topic[item.topic].append(item.timestamp_s)

        rows = [topic_row(topic, stamps_by_topic.get(topic, [])) for topic in selected]
        write_csv(
            rows,
            args.output,
            columns=['topic', 'count', 'duration_s', 'mean_hz', 'min_hz', 'max_hz', 'std_hz'],
        )
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

