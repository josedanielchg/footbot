#!/usr/bin/env python3
"""Chart 3: Time to first ball control.

Reads the Ball Control FSM state topic and reports the first time the controller
enters a captured/controlling state.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, bag_time_bounds, read_messages, require_topics, string_data
from common.csv_utils import add_common_args, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_name='03_time_to_ball_control.csv')
    parser.add_argument('--fsm-topic', default='/soccer/fsm_state')
    parser.add_argument(
        '--control-states',
        nargs='*',
        default=['CONTROL_BALL', 'ROTATE_WITH_BALL'],
        help='FSM states considered successful ball control.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.fsm_topic])
        t_start, _ = bag_time_bounds(args.input)
        first_control = None
        control_states = set(args.control_states)
        for item in read_messages(args.input, [args.fsm_topic]):
            if t_start is None:
                t_start = item.timestamp_s
            if string_data(item.msg) in control_states:
                first_control = item.timestamp_s
                break

        rows = [{
            'episode': args.episode,
            'scenario': args.scenario,
            't_start_s': t_start if t_start is not None else '',
            't_first_control_s': first_control if first_control is not None else '',
            'dt_s': (first_control - t_start) if first_control is not None and t_start is not None else '',
        }]
        write_csv(rows, args.output)
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

