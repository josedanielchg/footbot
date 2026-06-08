"""Simulation referee for Reach-goal scoring.

The robot behavior remains perception-driven. This node is a simulation-only
referee: it watches the dynamic ball pose and publishes when the ball has
entered the goal zone so the FSM can stop the episode cleanly.
"""

import time

import rclpy
from footbot_common.topics import SOCCER_GOAL_SCORED, REACH_GOAL_BALL_POSE
from geometry_msgs.msg import Pose
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool
from tf2_msgs.msg import TFMessage


DEFAULT_WORLD_POSE_TOPIC = '/world/footbot_world/pose/info'


def pose_inside_goal_zone(pose, goal_line_x, goal_half_width, max_ball_z):
    return bool(
        float(pose.position.x) >= float(goal_line_x)
        and abs(float(pose.position.y)) <= float(goal_half_width)
        and float(pose.position.z) <= float(max_ball_z)
    )


class ReachGoalScoreMonitor(Node):
    def __init__(self):
        super().__init__('reach_goal_score_monitor')

        self.declare_parameter('ball_pose_topic', REACH_GOAL_BALL_POSE)
        self.declare_parameter('world_pose_topic', DEFAULT_WORLD_POSE_TOPIC)
        self.declare_parameter('ball_entity_name', 'reach_goal_ball')
        self.declare_parameter('goal_scored_topic', SOCCER_GOAL_SCORED)
        self.declare_parameter('goal_line_x', 1.68)
        self.declare_parameter('goal_half_width', 0.38)
        self.declare_parameter('max_ball_z', 0.20)
        self.declare_parameter('score_hold_time_sec', 0.15)
        self.declare_parameter('publish_rate', 20.0)

        self.ball_pose_topic = self.get_parameter('ball_pose_topic').value
        self.world_pose_topic = self.get_parameter('world_pose_topic').value
        self.ball_entity_name = self.get_parameter('ball_entity_name').value
        self.goal_scored_topic = self.get_parameter('goal_scored_topic').value
        self.goal_line_x = float(self.get_parameter('goal_line_x').value)
        self.goal_half_width = float(self.get_parameter('goal_half_width').value)
        self.max_ball_z = float(self.get_parameter('max_ball_z').value)
        self.score_hold_time_sec = float(
            self.get_parameter('score_hold_time_sec').value
        )
        publish_rate = float(self.get_parameter('publish_rate').value)

        self.latest_pose = None
        self.score_candidate_since = None
        self.scored = False

        self.pose_subscription = self.create_subscription(
            Pose,
            self.ball_pose_topic,
            self.on_pose,
            10,
        )
        self.world_pose_subscription = self.create_subscription(
            TFMessage,
            self.world_pose_topic,
            self.on_world_pose,
            10,
        )
        self.score_publisher = self.create_publisher(
            Bool,
            self.goal_scored_topic,
            10,
        )
        self.timer = self.create_timer(
            1.0 / max(publish_rate, 1.0),
            self.publish_score,
        )
        self.get_logger().info(
            f'Reach Goal score monitor watching {self.ball_pose_topic} and '
            f'{self.world_pose_topic} for {self.ball_entity_name}; '
            f'publishing {self.goal_scored_topic}'
        )

    def on_pose(self, message):
        self.latest_pose = message

    def on_world_pose(self, message):
        for transform in message.transforms:
            if transform.child_frame_id != self.ball_entity_name:
                continue
            pose = Pose()
            pose.position.x = transform.transform.translation.x
            pose.position.y = transform.transform.translation.y
            pose.position.z = transform.transform.translation.z
            pose.orientation = transform.transform.rotation
            self.latest_pose = pose
            return

    def update_score(self, now):
        if self.scored:
            return True

        if self.latest_pose is None:
            self.score_candidate_since = None
            return False

        in_goal = pose_inside_goal_zone(
            self.latest_pose,
            self.goal_line_x,
            self.goal_half_width,
            self.max_ball_z,
        )
        if not in_goal:
            self.score_candidate_since = None
            return False

        if self.score_candidate_since is None:
            self.score_candidate_since = now
            return False

        self.scored = now - self.score_candidate_since >= self.score_hold_time_sec
        if self.scored:
            self.get_logger().info('Goal scored. Stopping Reach Goal episode.')
        return self.scored

    def publish_score(self):
        self.score_publisher.publish(Bool(data=self.update_score(time.monotonic())))


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = ReachGoalScoreMonitor()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
