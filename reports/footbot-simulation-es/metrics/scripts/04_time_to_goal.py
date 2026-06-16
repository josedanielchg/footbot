#!/usr/bin/env python3
"""Chart 4: Time to score.

Reads ``/soccer/goal_scored`` and reports the first true value relative to the
start of the rosbag episode.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, bag_time_bounds, bool_data, read_messages, require_topics
from common.csv_utils import add_common_args, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_name='04_time_to_goal.csv')
    parser.add_argument('--goal-scored-topic', default='/soccer/goal_scored')
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.goal_scored_topic])
        t_start, _ = bag_time_bounds(args.input)
        t_goal = None
        for item in read_messages(args.input, [args.goal_scored_topic]):
            if t_start is None:
                t_start = item.timestamp_s
            if bool_data(item.msg):
                t_goal = item.timestamp_s
                break
        rows = [{
            'episode': args.episode,
            't_start_s': t_start if t_start is not None else '',
            't_goal_s': t_goal if t_goal is not None else '',
            'dt_s': (t_goal - t_start) if t_goal is not None and t_start is not None else '',
        }]
        write_csv(rows, args.output)
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

