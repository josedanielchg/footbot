#!/usr/bin/env python3
"""Chart 5: Goal success rate across episode bags.

Scans a directory of rosbag2 episodes and writes one row per episode plus a
summary row with the aggregate success rate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, bag_time_bounds, bool_data, discover_bags, read_messages, topic_types
from common.csv_utils import default_csv_path, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Directory containing episode bags.')
    parser.add_argument('--output', default=str(default_csv_path('05_goal_success_rate.csv')))
    parser.add_argument('--goal-scored-topic', default='/soccer/goal_scored')
    return parser.parse_args()


def episode_result(bag_path, goal_topic):
    available = topic_types(bag_path)
    if goal_topic not in available:
        print(f'warning: {bag_path} has no {goal_topic}; treating as not scored', file=sys.stderr)
        t_start, t_end = bag_time_bounds(bag_path)
        return False, max((t_end or 0.0) - (t_start or 0.0), 0.0)

    scored = False
    for item in read_messages(bag_path, [goal_topic]):
        if bool_data(item.msg):
            scored = True
            break
    t_start, t_end = bag_time_bounds(bag_path)
    duration = max((t_end or 0.0) - (t_start or 0.0), 0.0)
    return scored, duration


def main():
    args = parse_args()
    try:
        bags = discover_bags(args.input)
        if not bags:
            fail(f'no rosbag2 metadata.yaml files found under {args.input}')
        rows = []
        successes = 0
        for bag in bags:
            scored, duration = episode_result(bag, args.goal_scored_topic)
            successes += int(scored)
            rows.append({
                'row_type': 'episode',
                'episode': bag.name,
                'scored': scored,
                'duration_s': duration,
                'success_rate_pct': '',
                'n_episodes': '',
            })

        rows.append({
            'row_type': 'summary',
            'episode': '',
            'scored': '',
            'duration_s': '',
            'success_rate_pct': 100.0 * successes / len(bags),
            'n_episodes': len(bags),
        })
        write_csv(
            rows,
            args.output,
            columns=['row_type', 'episode', 'scored', 'duration_s', 'success_rate_pct', 'n_episodes'],
        )
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

