#!/usr/bin/env python3
"""Chart 7: RECOVER_BALL / COMMIT_TO_GOAL activation counts.

Counts transitions into selected FSM states and normalizes them per minute of
episode duration.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, bag_time_bounds, read_messages, require_topics, string_data
from common.csv_utils import add_common_args, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_name='07_fsm_event_counts.csv')
    parser.add_argument('--fsm-topic', default='/soccer/reach_goal_fsm_state')
    parser.add_argument('--events', nargs='*', default=['RECOVER_BALL', 'COMMIT_TO_GOAL'])
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.fsm_topic])
        t_start, t_end = bag_time_bounds(args.input)
        events = set(args.events)
        counts = Counter()
        previous_state = None
        for item in read_messages(args.input, [args.fsm_topic]):
            state = string_data(item.msg)
            if state != previous_state and state in events:
                counts[state] += 1
            previous_state = state
        duration_s = max((t_end or 0.0) - (t_start or 0.0), 0.0)
        rows = []
        for event in args.events:
            count = counts[event]
            rows.append({
                'episode': args.episode,
                'event': event,
                'count': count,
                'per_minute': (60.0 * count / duration_s) if duration_s > 0.0 else '',
            })
        write_csv(rows, args.output)
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

