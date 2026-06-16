#!/usr/bin/env python3
"""Chart 1: Perception-to-actuation loop latency.

Reads a rosbag2 recording, matches each ``/camera/image_raw`` frame timestamp to
the first subsequent ``/cmd_vel`` command recorded in the bag, and writes one CSV
row per matched frame. A separate summary CSV is also written with aggregate
latency statistics.
"""

from __future__ import annotations

import argparse
import bisect
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, message_stamp_s, read_messages, require_topics
from common.csv_utils import default_csv_path, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='rosbag2 directory.')
    parser.add_argument('--output', default=str(default_csv_path('01_loop_latency.csv')))
    parser.add_argument(
        '--summary-output',
        default=str(default_csv_path('01_loop_latency_summary.csv')),
        help='Summary CSV output path.',
    )
    parser.add_argument('--camera-topic', default='/camera/image_raw')
    parser.add_argument('--cmd-vel-topic', default='/cmd_vel')
    parser.add_argument('--max-latency-ms', type=float, default=1000.0)
    parser.add_argument(
        '--use-image-header-stamp',
        action='store_true',
        help=(
            'Use sensor_msgs/Image.header.stamp for frame_stamp_s. By default '
            'the script uses rosbag receive timestamps so image and /cmd_vel '
            'timestamps share the same clock.'
        ),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.camera_topic, args.cmd_vel_topic])

        frame_stamps = []
        cmd_stamps = []
        for item in read_messages(args.input, [args.camera_topic, args.cmd_vel_topic]):
            if item.topic == args.camera_topic:
                if args.use_image_header_stamp:
                    frame_stamps.append(message_stamp_s(item.msg, item.timestamp_s))
                else:
                    frame_stamps.append(item.timestamp_s)
            elif item.topic == args.cmd_vel_topic:
                cmd_stamps.append(item.timestamp_s)

        if not frame_stamps:
            fail(f'no camera frames found on {args.camera_topic}')
        if not cmd_stamps:
            fail(f'no velocity commands found on {args.cmd_vel_topic}')

        cmd_stamps.sort()
        rows = []
        for frame_stamp in frame_stamps:
            index = bisect.bisect_left(cmd_stamps, frame_stamp)
            if index >= len(cmd_stamps):
                continue
            cmd_stamp = cmd_stamps[index]
            latency_ms = (cmd_stamp - frame_stamp) * 1000.0
            if latency_ms < 0.0 or latency_ms > args.max_latency_ms:
                continue
            rows.append({
                'frame_stamp_s': frame_stamp,
                'cmd_stamp_s': cmd_stamp,
                'latency_ms': latency_ms,
            })

        write_csv(rows, args.output, columns=['frame_stamp_s', 'cmd_stamp_s', 'latency_ms'])

        latencies = np.array([row['latency_ms'] for row in rows], dtype=float)
        if latencies.size:
            summary = [{
                'count': int(latencies.size),
                'mean_ms': float(np.mean(latencies)),
                'median_ms': float(np.median(latencies)),
                'p95_ms': float(np.percentile(latencies, 95)),
                'min_ms': float(np.min(latencies)),
                'max_ms': float(np.max(latencies)),
            }]
        else:
            summary = [{
                'count': 0,
                'mean_ms': '',
                'median_ms': '',
                'p95_ms': '',
                'min_ms': '',
                'max_ms': '',
            }]
        write_csv(summary, args.summary_output)
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()
