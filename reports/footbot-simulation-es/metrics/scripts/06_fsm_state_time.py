#!/usr/bin/env python3
"""Chart 6: Time spent per FSM state.

Integrates dwell time from a string FSM state topic such as
``/soccer/reach_goal_fsm_state``.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, bag_time_bounds, read_messages, require_topics, string_data
from common.csv_utils import add_common_args, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_name='06_fsm_state_time.csv')
    parser.add_argument('--fsm-topic', default='/soccer/reach_goal_fsm_state')
    parser.add_argument(
        '--timeline-output',
        default='',
        help='Optional CSV path for the raw FSM timeline: episode,scenario,t_s,state.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.fsm_topic])
        t_start, t_end = bag_time_bounds(args.input)
        messages = [
            (item.timestamp_s, string_data(item.msg))
            for item in read_messages(args.input, [args.fsm_topic])
        ]
        if not messages:
            fail(f'no FSM state messages on {args.fsm_topic}')

        if args.timeline_output:
            timeline_rows = [
                {
                    'episode': args.episode,
                    'scenario': args.scenario,
                    't_s': stamp,
                    'state': state,
                }
                for stamp, state in messages
            ]
            write_csv(
                timeline_rows,
                args.timeline_output,
                columns=['episode', 'scenario', 't_s', 'state'],
            )

        totals = defaultdict(float)
        visits = defaultdict(int)
        previous_state = None
        for index, (stamp, state) in enumerate(messages):
            if state != previous_state:
                visits[state] += 1
                previous_state = state
            next_stamp = messages[index + 1][0] if index + 1 < len(messages) else (t_end or stamp)
            totals[state] += max(next_stamp - stamp, 0.0)

        episode_duration = max((t_end or messages[-1][0]) - (t_start or messages[0][0]), 0.0)
        rows = []
        for state in sorted(totals):
            total = totals[state]
            rows.append({
                'episode': args.episode,
                'state': state,
                'total_time_s': total,
                'pct_of_episode': (100.0 * total / episode_duration) if episode_duration > 0.0 else '',
                'n_visits': visits[state],
            })
        write_csv(rows, args.output)
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

