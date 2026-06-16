#!/usr/bin/env python3
"""Chart 9: Ball and robot (x, y) trajectory.

Reads Gazebo pose data bridged as ``tf2_msgs/TFMessage`` and writes the current
ball and robot positions at each observed world-pose timestamp.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.bag_reader import BagReadError, read_messages, require_topics
from common.csv_utils import add_common_args, fail, write_csv


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_name='09_trajectory_xy.csv')
    parser.add_argument('--world-pose-topic', default='/world/footbot_world/pose/info')
    parser.add_argument('--ball-entity', default='reach_goal_ball')
    parser.add_argument('--robot-entity', default='footbot')
    return parser.parse_args()


def yaw_from_quaternion(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def transform_to_pose_tuple(transform):
    translation = transform.transform.translation
    rotation = transform.transform.rotation
    return float(translation.x), float(translation.y), yaw_from_quaternion(rotation)


def main():
    args = parse_args()
    try:
        require_topics(args.input, [args.world_pose_topic])
        latest_ball = None
        latest_robot = None
        rows = []
        for item in read_messages(args.input, [args.world_pose_topic]):
            changed = False
            transforms = getattr(item.msg, 'transforms', [])
            for transform in transforms:
                if transform.child_frame_id == args.ball_entity:
                    x, y, _ = transform_to_pose_tuple(transform)
                    latest_ball = (x, y)
                    changed = True
                elif transform.child_frame_id == args.robot_entity:
                    latest_robot = transform_to_pose_tuple(transform)
                    changed = True

            if changed:
                rows.append({
                    't_s': item.timestamp_s,
                    'ball_x': latest_ball[0] if latest_ball is not None else '',
                    'ball_y': latest_ball[1] if latest_ball is not None else '',
                    'robot_x': latest_robot[0] if latest_robot is not None else '',
                    'robot_y': latest_robot[1] if latest_robot is not None else '',
                    'robot_yaw': latest_robot[2] if latest_robot is not None else '',
                })

        if not rows:
            fail(
                f'no rows produced. Check entity names: '
                f'ball={args.ball_entity}, robot={args.robot_entity}'
            )
        write_csv(
            rows,
            args.output,
            columns=['t_s', 'ball_x', 'ball_y', 'robot_x', 'robot_y', 'robot_yaw'],
        )
    except BagReadError as exc:
        fail(str(exc))


if __name__ == '__main__':
    main()

